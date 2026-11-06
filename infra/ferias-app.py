"""App de ferias: venta y control de stock en ferias de la libreria.

Configuracion por variables de entorno (para poder migrar a hosting sin tocar codigo):
  FERIAS_PUERTO    puerto (default 5050)
  FERIAS_PREFIJO   prefijo publico, ej /ferias (default vacio)
  FERIAS_DB        ruta del archivo SQLite (default <carpeta>/ferias.db)
  FERIAS_SECRETO   clave de sesion (default archivo secreto.key)
  FERIAS_SECURE    1 si se sirve por HTTPS (cookie Secure)
  FERIAS_RAYUELA   URL del endpoint de consulta de Rayuela
"""
import csv
import io
import os
import re
import secrets
import unicodedata
import uuid
import zipfile
import threading
import time
from datetime import datetime, timedelta
from functools import wraps

from flask import (Flask, Response, abort, flash, g, jsonify, redirect,
                   render_template, request, send_file, session, url_for)
from werkzeug.security import check_password_hash, generate_password_hash

import db
import rayuela

BASE = os.path.dirname(os.path.abspath(__file__))
PREFIJO = (os.environ.get('FERIAS_PREFIJO') or '').rstrip('/')
PUERTO = int(os.environ.get('FERIAS_PUERTO') or 5050)
# pausa entre consultas de la actualizacion de precios (en tests se pone 0)
PAUSA_PRECIOS = float(os.environ.get('FERIAS_PRECIOS_PAUSA') or 2)
FORMAS_PAGO = [('efectivo', 'Efectivo'), ('transferencia', 'Transferencia'),
               ('qr', 'QR'), ('tarjeta', 'Tarjeta')]
FORMAS = [f for f, _ in FORMAS_PAGO]

# ---- freno de intentos de login (fuerza bruta)
CLAVE_MINIMA = 8              # caracteres minimos para una clave nueva
MAX_INTENTOS = 10             # fallas permitidas por IP
VENTANA_INTENTOS = 15 * 60    # en esta ventana (segundos)
BLOQUEO_INTENTOS = 15 * 60    # cuanto dura el bloqueo (segundos)

_intentos = {}                # ip -> [marcas de tiempo de las fallas]
_bloqueos = {}                # ip -> hasta cuando esta bloqueada
_candado_intentos = threading.Lock()


def ip_cliente():
    """La IP real, teniendo en cuenta que nginx esta adelante."""
    return (request.headers.get('X-Real-IP') or request.remote_addr or '').strip()


def login_bloqueado(ip):
    """Devuelve los segundos que le quedan de bloqueo (0 si puede probar)."""
    with _candado_intentos:
        hasta = _bloqueos.get(ip)
        if not hasta:
            return 0
        if time.time() >= hasta:
            _bloqueos.pop(ip, None)
            return 0
        return int(hasta - time.time()) + 1


def login_fallo(ip):
    with _candado_intentos:
        ahora = time.time()
        marcas = [t for t in _intentos.get(ip, []) if ahora - t < VENTANA_INTENTOS]
        marcas.append(ahora)
        if len(marcas) >= MAX_INTENTOS:
            _bloqueos[ip] = ahora + BLOQUEO_INTENTOS
            _intentos[ip] = []
        else:
            _intentos[ip] = marcas


def login_ok(ip):
    with _candado_intentos:
        _intentos.pop(ip, None)
        _bloqueos.pop(ip, None)


def clave_valida(clave):
    """Clave nueva: al menos 8 caracteres y que no sea el usuario."""
    return len((clave or '').strip()) >= CLAVE_MINIMA


def clave_desde(nombre):
    """'QR Mercado Pago' -> 'qr_mercado_pago' (la clave no cambia al renombrar)."""
    base = unicodedata.normalize('NFKD', str(nombre or '')).encode('ascii', 'ignore').decode()
    base = re.sub(r'[^a-zA-Z0-9]+', '_', base).strip('_').lower()
    return base[:24] or 'forma'


def formas_pago_todas(con):
    return [(f['clave'], f['nombre']) for f in db.filas(
        con, 'SELECT clave, nombre FROM formas_pago ORDER BY orden, clave')]


def formas_pago_activas(con):
    return db.filas(con, '''SELECT clave, nombre, tipo, banco, titular, cuit, cbu, alias, nota,
                                   qr_imagen
                              FROM formas_pago WHERE activo = 1 ORDER BY orden, clave''')


TIPOS_PAGO = ('simple', 'transferencia', 'qr')


def guardar_qr(archivo, clave):
    """Guarda la imagen del QR de una forma de pago y devuelve la ruta relativa."""
    if not archivo or not archivo.filename:
        return None
    extension = os.path.splitext(archivo.filename)[1].lower()
    if extension not in ('.png', '.jpg', '.jpeg', '.webp'):
        return False
    carpeta = os.path.join(BASE, 'static', 'cobros')
    if not os.path.isdir(carpeta):
        os.makedirs(carpeta)
    base = 'qr_' + re.sub(r'[^a-z0-9_]', '_', clave)[:40]
    nombre = base + extension
    # si cambia la extension, se borra la imagen anterior
    for vieja in os.listdir(carpeta):
        if vieja.startswith(base + '.') and vieja != nombre:
            try:
                os.remove(os.path.join(carpeta, vieja))
            except OSError:
                pass
    archivo.save(os.path.join(carpeta, nombre))
    return 'cobros/' + nombre


def generar_ref():
    """Referencia corta para que el comprador escriba en la transferencia."""
    alfabeto = 'ABCDEFGHJKLMNPQRSTUVWXYZ23456789'   # sin 0/O/I/1
    return ''.join(secrets.choice(alfabeto) for _ in range(6))


def claves_pago(con, solo_activas=True):
    sql = 'SELECT clave FROM formas_pago'
    if solo_activas:
        sql += ' WHERE activo = 1'
    return {f['clave'] for f in db.filas(con, sql)}


class PrefijoProxy:
    """Detras del tunel el prefijo se recorta: se lo devolvemos a Flask para
    que url_for() genere las rutas completas."""

    def __init__(self, wsgi_app, prefijo):
        self.wsgi_app = wsgi_app
        self.prefijo = prefijo

    def __call__(self, environ, start_response):
        if self.prefijo:
            environ['SCRIPT_NAME'] = self.prefijo
        return self.wsgi_app(environ, start_response)


# ------------------------------------------------------------------ utilidades
def marcar_valor(texto):
    return str(texto or '').strip()


def a_entero(valor, por_defecto=0):
    try:
        return int(str(valor).strip())
    except (TypeError, ValueError):
        return por_defecto


def a_decimal(valor, por_defecto=0.0):
    try:
        return round(float(str(valor).replace(',', '.').strip()), 2)
    except (TypeError, ValueError):
        return por_defecto


def reservado_de(fila):
    """Cuantos ejemplares de la fila estan reservados (si la consulta lo trae)."""
    try:
        return int(fila['reservado'] or 0)
    except (KeyError, IndexError, TypeError):
        return 0


def disponible(fila):
    return (fila['llevados'] + fila['repuestos'] - fila['vendidos'] - fila['perdidos']
            - reservado_de(fila))


def sin_acentos(texto):
    """Minusculas y sin acentos, para comparar titulos."""
    texto = unicodedata.normalize('NFD', str(texto or ''))
    return ''.join(c for c in texto if unicodedata.category(c) != 'Mn').lower()


def usuario_id_actual():
    """id del usuario logueado, o None si el codigo corre en segundo plano."""
    try:
        return (g.get('usuario') or {}).get('id')
    except RuntimeError:
        return None


def registrar_movimiento(con, feria_id, accion, detalle='', libro_id=None):
    """Deja constancia de quien cambio que. Si falla, no rompe la accion principal."""
    try:
        con.execute('''INSERT INTO movimientos
            (feria_id, cuando, usuario_id, accion, libro_id, detalle)
            VALUES (?, ?, ?, ?, ?, ?)''',
                    (feria_id, db.ahora(), usuario_id_actual(),
                     accion, libro_id, detalle))
    except Exception:
        pass


def sumar_stock(con, feria, libro_id, cantidad):
    """Suma ejemplares a la feria y devuelve (fila, error).

    Si la feria se esta preparando cuenta como carga inicial (llevados);
    si ya abrio cuenta como reposicion (repuestos) y queda el registro.
    """
    libro = db.fila(con, 'SELECT * FROM libros WHERE id = ?', (libro_id,))
    if not libro:
        return None, 'Ese libro no esta en el sistema.'
    campo = 'llevados' if feria['estado'] == 'preparacion' else 'repuestos'
    fl = db.fila(con, 'SELECT * FROM feria_libros WHERE feria_id = ? AND libro_id = ?',
                 (feria['id'], libro_id))
    if fl:
        con.execute('UPDATE feria_libros SET %s = %s + ? WHERE id = ?' % (campo, campo),
                    (cantidad, fl['id']))
    else:
        con.execute('''INSERT INTO feria_libros
            (feria_id, libro_id, precio, llevados, repuestos, vendidos, perdidos)
            VALUES (?, ?, ?, ?, ?, 0, 0)''',
                    (feria['id'], libro_id, libro['precio_sis'],
                     cantidad if campo == 'llevados' else 0,
                     cantidad if campo == 'repuestos' else 0))
    if campo == 'repuestos':
        con.execute('''INSERT INTO reposiciones
            (feria_id, libro_id, cantidad, cuando, usuario_id)
            VALUES (?, ?, ?, ?, ?)''',
                    (feria['id'], libro_id, cantidad, db.ahora(),
                     usuario_id_actual()))
    registrar_movimiento(con, feria['id'], 'ingresar',
                         '%s +%d' % (campo, cantidad), libro_id)
    fila = db.fila(con, '''SELECT fl.id AS fl_id, fl.*, l.id AS libro_id,
                                  l.isbn, l.titulo, l.autor,
                                  COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                             JOIN reservas r ON r.id = ri.reserva_id
                                            WHERE r.feria_id = fl.feria_id
                                              AND r.estado = 'activa'
                                              AND ri.libro_id = fl.libro_id), 0) AS reservado
                             FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                            WHERE fl.feria_id = ? AND fl.libro_id = ?''',
                   (feria['id'], libro_id))
    if fila:
        fila['disponible'] = disponible(fila)
    return fila, None


# ---------------------------------------------------- precios automaticos
def leer_ajustes(con):
    fila = db.fila(con, 'SELECT * FROM ajustes WHERE id = 1')
    if not fila:
        fila = {'precios_activo': 1, 'precios_desde': '09:00',
                'precios_cada_horas': 2, 'precios_ultimo': None}
    return fila


def _hora_hhmm(texto, por_defecto=(9, 0)):
    try:
        hh, mm = [int(x) for x in str(texto or '').split(':')[:2]]
        if 0 <= hh <= 23 and 0 <= mm <= 59:
            return hh, mm
    except (TypeError, ValueError):
        pass
    return por_defecto


def ultimo_turno(desde, cada_horas, ahora=None):
    """Momento del ultimo turno programado que ya paso."""
    ahora = ahora or datetime.now()
    hh, mm = _hora_hhmm(desde)
    cada = max(1, int(cada_horas or 2))
    inicio = ahora.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if inicio > ahora:
        inicio -= timedelta(days=1)
    pasos = int((ahora - inicio).total_seconds() // (cada * 3600))
    return inicio + timedelta(hours=cada * pasos)


def reclamar_turno_precios():
    """Toma el turno (asi no actualizan dos procesos a la vez)."""
    with db.conexion() as con:
        aj = leer_ajustes(con)
        if not aj['precios_activo']:
            return False
        if not db.valor(con, "SELECT COUNT(*) FROM ferias WHERE estado = 'abierta'"):
            return False
        turno = ultimo_turno(aj['precios_desde'], aj['precios_cada_horas'])
        ultimo = aj['precios_ultimo']
        if ultimo and ultimo >= turno.strftime('%Y-%m-%d %H:%M:%S'):
            return False
        con.execute('UPDATE ajustes SET precios_ultimo = ? WHERE id = 1',
                    (datetime.now().strftime('%Y-%m-%d %H:%M:%S'),))
        return True


def sincronizar_precios(fid=None, pausa=None):
    """Actualiza el precio de los libros de ferias abiertas contra Rayuela."""
    pausa = PAUSA_PRECIOS if pausa is None else pausa
    resumen = {'revisados': 0, 'cambiados': 0, 'errores': 0, 'cortado': False}
    with db.conexion() as con:
        if fid:
            ferias_ = db.filas(con, "SELECT id FROM ferias WHERE id = ? "
                                    "AND estado = 'abierta'", (fid,))
        else:
            ferias_ = db.filas(con, "SELECT id FROM ferias WHERE estado = 'abierta'")
        if not ferias_:
            return resumen
        marcas = ','.join('?' * len(ferias_))
        libros = db.filas(con, '''SELECT fl.id AS fl_id, fl.feria_id, fl.precio,
                                          l.isbn, l.id AS libro_id
                                     FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                                    WHERE fl.feria_id IN (%s)''' % marcas,
                          tuple(f['id'] for f in ferias_))
    fallos = 0
    for libro in libros:
        try:
            info = rayuela.consultar(libro['isbn'])
        except rayuela.ErrorRayuela:
            resumen['errores'] += 1
            fallos += 1
            if fallos >= 5:
                resumen['cortado'] = True
                break
            continue
        fallos = 0
        resumen['revisados'] += 1
        nuevo = float(info.get('precio') or 0)
        viejo = float(libro['precio'] or 0)
        if nuevo > 0 and abs(nuevo - viejo) > 0.001:
            with db.conexion() as con:
                con.execute('UPDATE feria_libros SET precio = ? WHERE id = ?',
                            (nuevo, libro['fl_id']))
                registrar_movimiento(con, libro['feria_id'], 'precio',
                                     '%.2f -> %.2f' % (viejo, nuevo), libro['libro_id'])
            resumen['cambiados'] += 1
        if pausa:
            time.sleep(pausa)
    return resumen


def hilo_precios():
    """Revisa cada minuto si toca actualizar precios y lo hace."""
    while True:
        try:
            if reclamar_turno_precios():
                sincronizar_precios()
        except Exception:
            pass
        time.sleep(60)


def asegurar_tabla_vistos(con):
    """Cada usuario tiene su marca de 'hasta aca vi los cambios de precio'."""
    con.execute('''CREATE TABLE IF NOT EXISTS precios_vistos (
                    usuario_id INTEGER NOT NULL,
                    feria_id   INTEGER NOT NULL,
                    hasta      TEXT    NOT NULL,
                    PRIMARY KEY (usuario_id, feria_id))''')


def cambios_de_precio(con, feria_id, horas=24, usuario_id=None):
    """Cambios de precio de las ultimas horas, para el aviso en pantalla.

    Si se pasa usuario_id, se muestra solo lo posterior a su marca: cada uno
    cierra el aviso cuando lo vio y no afecta a los demas.
    """
    desde = (datetime.now() - timedelta(hours=horas)).strftime('%Y-%m-%d %H:%M:%S')
    sql = '''SELECT m.cuando, m.detalle, l.titulo
               FROM movimientos m LEFT JOIN libros l ON l.id = m.libro_id
              WHERE m.feria_id = ? AND m.accion = 'precio'
                AND m.cuando >= ?'''
    parametros = [feria_id, desde]
    if usuario_id:
        asegurar_tabla_vistos(con)
        visto = db.fila(con, 'SELECT hasta FROM precios_vistos '
                             'WHERE usuario_id = ? AND feria_id = ?',
                        (usuario_id, feria_id))
        if visto and visto['hasta']:
            sql += ' AND m.cuando > ?'
            parametros.append(visto['hasta'])
    sql += ' ORDER BY m.id DESC'
    filas = db.filas(con, sql, tuple(parametros))
    for f in filas:
        partes = (f['detalle'] or '').split('->')
        f['antes'] = a_decimal(partes[0]) if len(partes) == 2 else 0
        f['despues'] = a_decimal(partes[1]) if len(partes) == 2 else 0
    return filas


def texto_lector(info):
    """Arma el texto que muestra el lector de precios (dos bloques)."""
    principal = ['\U0001F4D8 ' + (info.get('titulo') or '')]
    if info.get('autor'):
        principal.append('\u270D\uFE0F ' + info['autor'])
    precio = info.get('precio_texto') or ''
    if precio:
        principal.append('\U0001F4B0 ' + precio)
    ficha = []
    if info.get('isbn'):
        ficha.append('\U0001F516 ' + info['isbn'])
    if info.get('coleccion'):
        ficha.append('\U0001F4DA ' + info['coleccion'])
    if info.get('editorial'):
        ficha.append('\U0001F3E2 ' + info['editorial'])
    if info.get('temas'):
        ficha.append('\U0001F3F7\uFE0F ' + info['temas'])
    if info.get('agotado'):
        ficha.append('\u23F3 Agotado desde: ' + info['agotado'])
    salida = '\n'.join(principal)
    if ficha:
        salida += '\n\n' + '\u2500' * 16 + '\n' + '\n'.join(ficha)
    return salida


# ---------------------------------------------------------------------- auth
def usuario_actual():
    uid = session.get('usuario_id')
    if not uid:
        return None
    with db.conexion() as con:
        u = db.fila(con, 'SELECT id, usuario, nombre, rol, activo FROM usuarios WHERE id = ?', (uid,))
    if not u or not u['activo']:
        session.clear()
        return None
    return u


def requiere_login(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not g.usuario:
            destino = request.script_root + request.path
            return redirect(url_for('ingresar', siguiente=destino))
        return vista(*args, **kwargs)
    return envoltura


def requiere_admin(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not g.usuario:
            return redirect(url_for('ingresar'))
        if g.usuario['rol'] != 'admin':
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


def requiere_vendedor(vista):
    """Admin o vendedor: los que venden."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not g.usuario:
            return redirect(url_for('ingresar'))
        if g.usuario['rol'] not in ('admin', 'vendedor'):
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


def requiere_repositor(vista):
    """Admin o repositor: los que manejan stock (cargar y reponer)."""
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not g.usuario:
            return redirect(url_for('ingresar'))
        if g.usuario['rol'] not in ('admin', 'repositor'):
            abort(403)
        return vista(*args, **kwargs)
    return envoltura


# -------------------------------------------------------------------- rutas

REPORTES_FERIA = [
    ('resumen', 'Resumen de la feria', 'Ventas, caja y controles del cierre.'),
    ('ventas', 'Ventas', 'Una fila por ticket, con vendedor y forma de pago.'),
    ('detalle', 'Detalle por venta', 'Que libros lleva cada ticket.'),
    ('vendidos', 'Vendidos para Rayuela', 'Un ISBN por fila con la cantidad vendida.'),
    ('stock', 'Stock final', 'Llevados, repuestos, vendidos, reservados, perdidos y devueltos.'),
    ('sobreventas', 'Sobreventas', 'Libros vendidos sin cargar o de mas.'),
    ('reservas', 'Reservas', 'Reservas cargadas y su estado.'),
    ('caja', 'Caja', 'Totales por forma de pago, caja inicial y arqueos.'),
]


def _datos_cierre(con, fid):
    """Todo lo que necesitan los reportes, leido una sola vez."""
    feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
    if not feria:
        raise ValueError('feria inexistente')
    ventas = db.filas(con, '''
        SELECT v.*, u.nombre AS vendedor, c.nombre AS cliente, c.telefono AS telefono
          FROM ventas v LEFT JOIN usuarios u ON u.id = v.usuario_id
          LEFT JOIN clientes c ON c.id = v.cliente_id
         WHERE v.feria_id = ? ORDER BY v.id''', (fid,))
    items = db.filas(con, '''
        SELECT vi.*, l.titulo, l.isbn, v.numero, v.estado AS venta_estado
          FROM venta_items vi JOIN ventas v ON v.id = vi.venta_id
          JOIN libros l ON l.id = vi.libro_id
         WHERE v.feria_id = ? ORDER BY v.id, vi.id''', (fid,))
    stock = db.filas(con, '''
        SELECT fl.libro_id, l.isbn, l.titulo, l.autor, l.editorial, fl.precio,
               fl.llevados, fl.repuestos, fl.vendidos, fl.perdidos,
               (SELECT COUNT(*) FROM venta_items vi
                  JOIN ventas v ON v.id = vi.venta_id
                 WHERE vi.libro_id = fl.libro_id AND v.feria_id = fl.feria_id
                   AND v.estado = 'confirmada' AND vi.sin_cargar = 1) AS sin_cargar_n,
               COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                          JOIN reservas r ON r.id = ri.reserva_id
                         WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                           AND ri.libro_id = fl.libro_id), 0) AS reservado
          FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
         WHERE fl.feria_id = ? ORDER BY l.titulo''', (fid,))
    arqueos = db.filas(con, '''
        SELECT a.*, u.nombre AS usuario FROM arqueos a
          LEFT JOIN usuarios u ON u.id = a.usuario_id
         WHERE a.feria_id = ? ORDER BY a.id''', (fid,))
    reservas = db.filas(con, '''
        SELECT r.*, COALESCE(SUM(ri.cantidad), 0) AS ejemplares
          FROM reservas r LEFT JOIN reserva_items ri ON ri.reserva_id = r.id
         WHERE r.feria_id = ? GROUP BY r.id ORDER BY r.id''', (fid,))
    return feria, ventas, items, stock, arqueos, reservas


def _reporte_feria(con, fid, nombre):
    """Encabezados y filas del reporte pedido. Solo lectura."""
    feria, ventas, items, stock, arqueos, reservas = _datos_cierre(con, fid)
    confirmadas = [v for v in ventas if v['estado'] == 'confirmada']
    libros_ok = [it for it in items if it['venta_estado'] == 'confirmada']
    por_forma = {}
    for v in confirmadas:
        clave = v['forma_pago'] or '(sin forma)'
        datos = por_forma.setdefault(clave, {'operaciones': 0, 'total': 0.0})
        datos['operaciones'] += 1
        datos['total'] += float(v['total'] or 0)
    efectivo = por_forma.get('efectivo', {}).get('total', 0.0)
    caja_inicial = float(feria['caja_inicial'] or 0)
    total = sum(float(v['total'] or 0) for v in confirmadas)

    if nombre == 'resumen':
        filas = [
            ['Feria', feria['nombre']], ['Lugar', feria['lugar'] or ''],
            ['Desde', feria['desde'] or ''], ['Hasta', feria['hasta'] or ''],
            ['Estado', feria['estado']],
            ['Generado', datetime.now().strftime('%d/%m/%Y %H:%M')], [],
            ['Caja inicial', round(caja_inicial, 2)],
            ['Efectivo cobrado', round(efectivo, 2)],
            ['Efectivo esperado en caja', round(caja_inicial + efectivo, 2)], [],
            ['Ventas confirmadas', len(confirmadas)],
            ['Ventas anuladas', sum(1 for v in ventas if v['estado'] == 'anulada')],
            ['Ventas pendientes de pago', sum(1 for v in ventas if v['estado'] == 'pendiente')],
            ['Total cobrado', round(total, 2)],
            ['Ticket promedio', round(total / len(confirmadas), 2) if confirmadas else 0],
            ['Ejemplares vendidos', sum(int(it['cantidad']) for it in libros_ok)],
            ['Titulos distintos vendidos', len({it['libro_id'] for it in libros_ok})], [],
            ['Ventas con sobreventa', sum(1 for v in confirmadas if v['sobreventa'])],
            ['Items vendidos sin cargar', sum(1 for it in libros_ok if it['sin_cargar'])],
            ['Reservas activas', sum(1 for r in reservas if r['estado'] == 'activa')], [],
            ['Forma de pago', 'Operaciones', 'Total'],
        ]
        for clave in sorted(por_forma, key=lambda k: -por_forma[k]['total']):
            filas.append([clave, por_forma[clave]['operaciones'], round(por_forma[clave]['total'], 2)])
        return ['Concepto', 'Valor', ''], filas

    if nombre == 'ventas':
        return (['Ticket', 'Fecha', 'Hora', 'Vendedor', 'Forma de pago', 'Cliente',
                 'Telefono', 'Total', 'Descuento', 'Estado', 'Sobreventa', 'Factura'],
                [[v['numero'], (v['cuando'] or '')[:10], (v['cuando'] or '')[11:19],
                  v['vendedor'] or '', v['forma_pago'], v['cliente'] or '', v['telefono'] or '',
                  round(float(v['total'] or 0), 2), round(float(v['descuento'] or 0), 2),
                  v['estado'], 'SI' if v['sobreventa'] else 'NO',
                  'SI' if v['pide_factura'] else 'NO'] for v in ventas])

    if nombre == 'detalle':
        filas = []
        for it in items:
            cantidad = int(it['cantidad'])
            precio = float(it['precio'] or 0)
            descuento = float(it['descuento'] or 0)
            filas.append([it['numero'], it['isbn'], it['titulo'], cantidad,
                          round(precio, 2), round(descuento, 2),
                          round(cantidad * precio - descuento, 2),
                          it['venta_estado'], 'SI' if it['sin_cargar'] else 'NO'])
        return (['Ticket', 'ISBN', 'Titulo', 'Cantidad', 'Precio unitario', 'Descuento',
                 'Subtotal', 'Estado venta', 'Vendido sin cargar'], filas)

    if nombre == 'vendidos':
        agregado = {}
        for it in libros_ok:
            clave = (it['isbn'] or '', it['titulo'])
            datos = agregado.setdefault(clave, {'cantidad': 0, 'total': 0.0})
            datos['cantidad'] += int(it['cantidad'])
            datos['total'] += int(it['cantidad']) * float(it['precio'] or 0) - float(it['descuento'] or 0)
        filas = [[isbn, titulo, datos['cantidad'], round(datos['total'], 2)]
                 for (isbn, titulo), datos in sorted(agregado.items(),
                                                     key=lambda p: -p[1]['cantidad'])]
        return ['ISBN', 'Titulo', 'Cantidad vendida', 'Importe'], filas

    if nombre == 'stock':
        filas = []
        for s in stock:
            devueltos = max(0, s['llevados'] + s['repuestos'] - s['vendidos'] - s['perdidos'])
            if s['sin_cargar_n']:
                situacion = 'vendido sin cargar'
            elif s['vendidos'] > s['llevados'] + s['repuestos']:
                situacion = 'vendido de mas'
            elif s['perdidos'] > 0:
                situacion = 'con perdidos'
            else:
                situacion = 'ok'
            filas.append([s['isbn'], s['titulo'], s['autor'] or '', s['editorial'] or '',
                          round(float(s['precio'] or 0), 2), s['llevados'], s['repuestos'],
                          s['vendidos'], s['reservado'], s['perdidos'], devueltos, situacion])
        return (['ISBN', 'Titulo', 'Autor', 'Editorial', 'Precio', 'Llevados', 'Repuestos',
                 'Vendidos', 'Reservados', 'Perdidos', 'Devueltos', 'Situacion'], filas)

    if nombre == 'sobreventas':
        tickets = {}
        for it in libros_ok:
            if it['sin_cargar']:
                tickets.setdefault(it['libro_id'], []).append(it['numero'])
        filas = []
        for s in stock:
            if not (s['sin_cargar_n'] or s['vendidos'] > s['llevados'] + s['repuestos']):
                continue
            cargados = s['llevados'] + s['repuestos']
            filas.append([s['isbn'], s['titulo'], cargados, s['vendidos'],
                          max(0, s['vendidos'] - cargados),
                          ', '.join(tickets.get(s['libro_id'], []))])
        return (['ISBN', 'Titulo', 'Cargados', 'Vendidos', 'Faltante', 'Tickets'], filas)

    if nombre == 'reservas':
        return (['Reserva', 'Nombre', 'Telefono', 'Nota', 'Estado', 'Ejemplares'],
                [[r['id'], r['nombre'], r['telefono'], r['nota'] or '', r['estado'],
                  r['ejemplares']] for r in reservas])

    if nombre == 'caja':
        filas = []
        for clave in sorted(por_forma, key=lambda k: -por_forma[k]['total']):
            filas.append([clave + ' (cobrado)', por_forma[clave]['operaciones'],
                          round(por_forma[clave]['total'], 2), '', '', ''])
        filas.append(['caja inicial', '', round(caja_inicial, 2), '', '', ''])
        filas.append(['efectivo esperado en caja', '', round(caja_inicial + efectivo, 2), '', '', ''])
        for a in arqueos:
            filas.append(['arqueo ' + (a['forma_pago'] or ''), '',
                          round(float(a['esperado'] or 0), 2), round(float(a['contado'] or 0), 2),
                          round(float(a['diferencia'] or 0), 2), a['usuario'] or ''])
        return (['Detalle', 'Operaciones', 'Esperado', 'Contado', 'Diferencia', 'Usuario'], filas)

    raise ValueError('reporte desconocido')


def _csv_reporte(encabezados, filas):
    buffer = io.StringIO()
    escritor = csv.writer(buffer, delimiter=';')
    escritor.writerow(encabezados)
    escritor.writerows(filas)
    return ('\ufeff' + buffer.getvalue()).encode('utf-8')


def _resumen_para_compartir(con, fid):
    feria, ventas, items, stock, arqueos, reservas = _datos_cierre(con, fid)
    confirmadas = [v for v in ventas if v['estado'] == 'confirmada']
    total = sum(float(v['total'] or 0) for v in confirmadas)
    efectivo = sum(float(v['total'] or 0) for v in confirmadas if v['forma_pago'] == 'efectivo')
    caja = float(feria['caja_inicial'] or 0)
    return ('Cierre %s\nVentas: %d por $%.2f\nEfectivo esperado en caja: $%.2f\n'
            'Sobreventas: %d' % (feria['nombre'], len(confirmadas), total,
                                  caja + efectivo,
                                  sum(1 for v in confirmadas if v['sobreventa'])))


def registrar_rutas(app):

    @app.before_request
    def cargar_usuario():
        g.usuario = usuario_actual()

    @app.context_processor
    def variables_comunes():
        try:
            with db.conexion() as con:
                formas = formas_pago_todas(con)
        except Exception:
            formas = FORMAS_PAGO
        return {'usuario': g.get('usuario'), 'formas_pago': formas,
                'prefijo': PREFIJO}

    # ---- salud / inicio
    @app.get('/salud')
    def salud():
        return jsonify(ok=True, app='ferias')

    @app.get('/robots.txt')
    def robots():
        # que no lo indexen los buscadores: el subdominio no tiene por que aparecer
        return Response('User-agent: *\nDisallow: /\n', mimetype='text/plain')

    # ---- lector de precios (publico, sin login)
    @app.get('/rayuela')
    def lector():
        vendedor = (request.args.get('modo') == 'vendedor'
                    or request.args.get('m') == 'v')
        return render_template('lector.html', modo='vendedor' if vendedor else 'cliente')

    # ---- manual de uso (publico): siempre la ultima version
    @app.get('/manual')
    def manual():
        ruta = os.path.join(BASE, 'static', 'manual.pdf')
        if not os.path.exists(ruta):
            abort(404)
        return send_file(ruta, mimetype='application/pdf', max_age=0)

    @app.post('/api/rayuela-consulta')
    def api_lector():
        datos = request.get_json(silent=True) or {}
        codigo = (request.form.get('codigo') or datos.get('codigo')
                  or datos.get('texto') or '')
        codigo = str(codigo).strip()
        if not codigo:
            return jsonify(ok=False, error='Falta el codigo.'), 400
        try:
            info = rayuela.consultar(codigo)
        except rayuela.ErrorRayuela as e:
            return jsonify(ok=False, error=str(e)), 400
        libro = {
            'isbn': info.get('isbn') or codigo,
            'titulo': info.get('titulo') or '',
            'autor': info.get('autor') or '',
            'precio': info.get('precio'),
            'precio_texto': info.get('precio_texto') or '',
            'editorial': info.get('editorial') or '',
            'coleccion': info.get('coleccion') or '',
            'temas': info.get('temas') or '',
            'agotado': info.get('agotado') or '',
        }
        return jsonify(ok=True, respuesta=texto_lector(info), libro=libro)

    @app.get('/')
    @requiere_login
    def inicio():
        with db.conexion() as con:
            ferias = db.filas(con, '''
                SELECT f.*,
                       (SELECT COUNT(*) FROM feria_libros fl WHERE fl.feria_id = f.id) AS titulos,
                       (SELECT COALESCE(SUM(fl.llevados + fl.repuestos), 0)
                          FROM feria_libros fl WHERE fl.feria_id = f.id) AS ejemplares,
                       (SELECT COALESCE(SUM(fl.vendidos), 0)
                          FROM feria_libros fl WHERE fl.feria_id = f.id) AS vendidos
                  FROM ferias f
              ORDER BY CASE f.estado WHEN 'abierta' THEN 0 WHEN 'preparacion' THEN 1 ELSE 2 END,
                       f.id DESC''')
        return render_template('ferias.html', ferias=ferias)

    # ---- ingresar / salir
    @app.route('/ingresar', methods=['GET', 'POST'])
    def ingresar():
        if g.usuario:
            return redirect(url_for('inicio'))
        error = None
        if request.method == 'POST':
            ip = ip_cliente()
            espera = login_bloqueado(ip)
            if espera:
                minutos = max(1, espera // 60)
                return render_template(
                    'ingresar.html',
                    error='Demasiados intentos fallidos. Probá de nuevo en %d minuto%s.'
                          % (minutos, 's' if minutos > 1 else '')), 429
            usuario = marcar_valor(request.form.get('usuario')).lower()
            clave = request.form.get('clave') or ''
            with db.conexion() as con:
                u = db.fila(con, 'SELECT * FROM usuarios WHERE usuario = ?', (usuario,))
            if not u or not u['activo'] or not check_password_hash(u['clave_hash'], clave):
                login_fallo(ip)
                error = 'Usuario o clave incorrectos.'
            else:
                login_ok(ip)
                session.clear()
                session['usuario_id'] = u['id']
                session.permanent = True
                destino = request.args.get('siguiente') or url_for('inicio')
                if not destino.startswith('/'):
                    destino = url_for('inicio')
                return redirect(destino)
        return render_template('ingresar.html', error=error)

    @app.post('/salir')
    def salir():
        session.clear()
        return redirect(url_for('ingresar'))

    # ---- ferias
    @app.post('/ferias/nueva')
    @requiere_admin
    def feria_nueva():
        nombre = marcar_valor(request.form.get('nombre'))
        if not nombre:
            flash('La feria necesita un nombre.', 'error')
            return redirect(url_for('inicio'))
        with db.conexion() as con:
            cur = con.execute('''
                INSERT INTO ferias (nombre, lugar, organizador, desde, hasta,
                                    observaciones, estado, caja_inicial, creada_por, creada)
                VALUES (?, ?, ?, ?, ?, ?, 'preparacion', ?, ?, ?)''', (
                nombre,
                marcar_valor(request.form.get('lugar')),
                marcar_valor(request.form.get('organizador')),
                marcar_valor(request.form.get('desde')),
                marcar_valor(request.form.get('hasta')),
                marcar_valor(request.form.get('observaciones')),
                a_decimal(request.form.get('caja_inicial')),
                g.usuario['id'], db.ahora()))
            fid = cur.lastrowid
        return redirect(url_for('feria_detalle', fid=fid))

    @app.get('/ferias/<int:fid>')
    @requiere_login
    def feria_detalle(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            filtro = marcar_valor(request.args.get('q')) or ''
            libros = db.filas(con, '''
                SELECT fl.*, l.isbn, l.titulo, l.autor, l.editorial, l.coleccion, l.temas,
                       COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                  JOIN reservas r ON r.id = ri.reserva_id
                                 WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                                   AND ri.libro_id = fl.libro_id), 0) AS reservado
                  FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ? ORDER BY l.titulo''', (fid,))
            for l in libros:
                l['disponible'] = disponible(l)
            resumen = {
                'titulos': len(libros),
                'ejemplares': sum(l['llevados'] + l['repuestos'] for l in libros),
                'vendidos': sum(l['vendidos'] for l in libros),
                'disponibles': sum(l['disponible'] for l in libros),
            }
            # filtro de control de stock: titulo, autor, editorial o ISBN
            if filtro:
                clave = sin_acentos(filtro)
                solo_digitos = ''.join(c for c in filtro if c.isdigit())
                libros = [l for l in libros
                          if clave in sin_acentos(l['titulo'])
                          or clave in sin_acentos(l['autor'])
                          or clave in sin_acentos(l['editorial'])
                          or (solo_digitos and str(l['isbn'] or '').startswith(solo_digitos))]
            ventas = db.filas(con, '''
                SELECT v.*, c.nombre AS cliente_nombre
                  FROM ventas v LEFT JOIN clientes c ON c.id = v.cliente_id
                 WHERE v.feria_id = ? AND v.estado = 'confirmada'
                 ORDER BY v.id DESC LIMIT 15''', (fid,))
            cambios = cambios_de_precio(con, fid,
                                        usuario_id=g.usuario['id'] if g.usuario else None)
        return render_template('feria.html', feria=feria, libros=libros,
                               resumen=resumen, ventas=ventas, cambios=cambios,
                               filtro=filtro, encontrados=len(libros))

    @app.post('/ferias/<int:fid>/datos')
    @requiere_admin
    def feria_datos(fid):
        with db.conexion() as con:
            previa = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not previa:
                abort(404)
            nuevo_nombre = marcar_valor(request.form.get('nombre'))
            nueva_caja = a_decimal(request.form.get('caja_inicial'))
            con.execute('''UPDATE ferias SET nombre = ?, lugar = ?, organizador = ?,
                              desde = ?, hasta = ?, observaciones = ?,
                              caja_inicial = ? WHERE id = ?''', (
                nuevo_nombre,
                marcar_valor(request.form.get('lugar')),
                marcar_valor(request.form.get('organizador')),
                marcar_valor(request.form.get('desde')),
                marcar_valor(request.form.get('hasta')),
                marcar_valor(request.form.get('observaciones')),
                nueva_caja,
                fid))
            cambios = []
            if (previa['nombre'] or '') != (nuevo_nombre or ''):
                cambios.append('nombre: %s -> %s' % (previa['nombre'], nuevo_nombre))
            if abs((previa['caja_inicial'] or 0) - nueva_caja) > 0.001:
                cambios.append('caja inicial: %.2f -> %.2f' % (previa['caja_inicial'], nueva_caja))
            if cambios:
                registrar_movimiento(con, fid, 'datos', '; '.join(cambios))
        flash('Datos de la feria actualizados.', 'ok')
        return redirect(url_for('feria_detalle', fid=fid))

    @app.post('/ferias/<int:fid>/abrir')
    @requiere_admin
    def feria_abrir(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            if feria['estado'] != 'preparacion':
                flash('Solo se puede abrir una feria en preparacion.', 'error')
                return redirect(url_for('feria_detalle', fid=fid))
            con.execute("UPDATE ferias SET estado = 'abierta' WHERE id = ?", (fid,))
            registrar_movimiento(con, fid, 'abrir', 'feria abierta para vender')
        # al abrir, se traen los precios frescos en segundo plano
        threading.Thread(target=sincronizar_precios, args=(fid,), daemon=True).start()
        flash('Feria abierta. Ya se puede vender.', 'ok')
        return redirect(url_for('feria_detalle', fid=fid))

    # ---- libros de la feria
    @app.post('/api/ferias/<int:fid>/agregar')
    @requiere_login
    def api_agregar(fid):
        datos = request.get_json(silent=True) or {}
        codigo = marcar_valor(datos.get('codigo'))
        cantidad = max(1, a_entero(datos.get('cantidad'), 1))
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                return jsonify(ok=False, error='Feria inexistente.'), 404
            if feria['estado'] == 'cerrada':
                return jsonify(ok=False, error='La feria esta cerrada.'), 409
        try:
            info = rayuela.consultar(codigo)
        except rayuela.ErrorRayuela as e:
            return jsonify(ok=False, error=str(e)), 400

        with db.conexion() as con:
            libro = db.fila(con, 'SELECT * FROM libros WHERE isbn = ?', (info['isbn'],))
            if libro:
                con.execute('''UPDATE libros SET titulo = ?, autor = ?, editorial = ?,
                               coleccion = ?, temas = ?, precio_sis = ?, actualizado = ?
                               WHERE id = ?''', (
                    info['titulo'] or libro['titulo'], info['autor'] or libro['autor'],
                    info['editorial'] or libro['editorial'],
                    info['coleccion'] or libro['coleccion'],
                    info['temas'] or libro['temas'],
                    info['precio'] or libro['precio_sis'], db.ahora(), libro['id']))
                libro_id = libro['id']
            else:
                cur = con.execute('''INSERT INTO libros
                    (isbn, titulo, autor, editorial, coleccion, temas, precio_sis, actualizado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                    info['isbn'], info['titulo'], info['autor'], info['editorial'],
                    info['coleccion'], info['temas'], info['precio'], db.ahora()))
                libro_id = cur.lastrowid

            fila, error = sumar_stock(con, feria, libro_id, cantidad)
        if error:
            return jsonify(ok=False, error=error), 404
        return jsonify(ok=True, libro=fila, cantidad=cantidad)

    @app.post('/api/ferias/<int:fid>/ingresar')
    @requiere_login
    def api_ingresar(fid):
        """Ingreso de stock por libro ya identificado (la pantalla Stock)."""
        datos = request.get_json(silent=True) or {}
        libro_id = a_entero(datos.get('libro_id'))
        cantidad = a_entero(datos.get('cantidad'))
        if not libro_id or cantidad <= 0 or cantidad > 999:
            return jsonify(ok=False, error='Cantidad invalida.'), 400
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                return jsonify(ok=False, error='Feria inexistente.'), 404
            if feria['estado'] == 'cerrada':
                return jsonify(ok=False, error='La feria esta cerrada.'), 409
            fila, error = sumar_stock(con, feria, libro_id, cantidad)
        if error:
            return jsonify(ok=False, error=error), 404
        return jsonify(ok=True, libro=fila, cantidad=cantidad)

    @app.post('/api/ferias/<int:fid>/consultar')
    @requiere_login
    def api_consultar(fid):
        """Devuelve los datos del libro SIN cargarlo: la pantalla confirma primero."""
        datos = request.get_json(silent=True) or {}
        codigo = marcar_valor(datos.get('codigo'))
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                return jsonify(ok=False, error='Feria inexistente.'), 404
            if feria['estado'] == 'cerrada':
                return jsonify(ok=False, error='La feria esta cerrada.'), 409
        try:
            info = rayuela.consultar(codigo)
        except rayuela.ErrorRayuela as e:
            return jsonify(ok=False, error=str(e)), 400
        with db.conexion() as con:
            libro = db.fila(con, 'SELECT * FROM libros WHERE isbn = ?', (info['isbn'],))
            if libro:
                con.execute('''UPDATE libros SET titulo = ?, autor = ?, editorial = ?,
                               coleccion = ?, temas = ?, precio_sis = ?, actualizado = ?
                               WHERE id = ?''', (
                    info['titulo'] or libro['titulo'], info['autor'] or libro['autor'],
                    info['editorial'] or libro['editorial'],
                    info['coleccion'] or libro['coleccion'],
                    info['temas'] or libro['temas'],
                    info['precio'] or libro['precio_sis'], db.ahora(), libro['id']))
                libro_id = libro['id']
            else:
                cur = con.execute('''INSERT INTO libros
                    (isbn, titulo, autor, editorial, coleccion, temas, precio_sis, actualizado)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                    info['isbn'], info['titulo'], info['autor'], info['editorial'],
                    info['coleccion'], info['temas'], info['precio'], db.ahora()))
                libro_id = cur.lastrowid
            fresco = db.fila(con, 'SELECT * FROM libros WHERE id = ?', (libro_id,))
            fl = db.fila(con, 'SELECT llevados FROM feria_libros '
                              'WHERE feria_id = ? AND libro_id = ?', (fid, libro_id))
            lleva = fl['llevados'] if fl else 0
        info['libro_id'] = libro_id
        info['precio'] = fresco['precio_sis'] or info['precio']
        info['ya_en_feria'] = lleva > 0
        info['lleva'] = lleva
        return jsonify(ok=True, libro=info)

    @app.post('/api/feria_libros/<int:flid>/editar')
    @requiere_admin
    def api_editar_fl(flid):
        datos = request.get_json(silent=True) or {}
        with db.conexion() as con:
            fl = db.fila(con, 'SELECT * FROM feria_libros WHERE id = ?', (flid,))
            if not fl:
                return jsonify(ok=False, error='No existe.'), 404
            feria = db.fila(con, 'SELECT estado FROM ferias WHERE id = ?', (fl['feria_id'],))
            if feria['estado'] == 'cerrada':
                return jsonify(ok=False, error='La feria esta cerrada.'), 409
            campos = {}
            for clave in ('precio', 'llevados', 'repuestos', 'perdidos'):
                if clave in datos:
                    campos[clave] = a_decimal(datos[clave]) if clave == 'precio' else a_entero(datos[clave])
            if not campos:
                return jsonify(ok=False, error='Nada para cambiar.'), 400
            if 'llevados' in campos and campos['llevados'] < 0:
                return jsonify(ok=False, error='La cantidad no puede ser negativa.'), 400
            cambios = []
            for clave, valor in campos.items():
                antes = fl[clave] or 0
                if clave == 'precio':
                    if abs(float(antes) - float(valor)) > 0.001:
                        cambios.append('precio: %.2f -> %.2f' % (antes, valor))
                elif int(antes) != int(valor):
                    cambios.append('%s: %s -> %s' % (clave, antes, valor))
            sets = ', '.join('%s = ?' % k for k in campos)
            con.execute('UPDATE feria_libros SET %s WHERE id = ?' % sets,
                        list(campos.values()) + [flid])
            if cambios:
                registrar_movimiento(con, fl['feria_id'], 'editar', '; '.join(cambios),
                                     fl['libro_id'])
            fila = db.fila(con, '''SELECT fl.id AS fl_id, fl.*, l.id AS libro_id,
                                          l.isbn, l.titulo, l.autor,
                                          COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                                     JOIN reservas r ON r.id = ri.reserva_id
                                                    WHERE r.feria_id = fl.feria_id
                                                      AND r.estado = 'activa'
                                                      AND ri.libro_id = fl.libro_id), 0) AS reservado
                                     FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                                    WHERE fl.id = ?''', (flid,))
            fila['disponible'] = disponible(fila)
        return jsonify(ok=True, libro=fila)

    @app.post('/api/feria_libros/<int:flid>/quitar')
    @requiere_admin
    def api_quitar_fl(flid):
        with db.conexion() as con:
            fl = db.fila(con, 'SELECT * FROM feria_libros WHERE id = ?', (flid,))
            if not fl:
                return jsonify(ok=False, error='No existe.'), 404
            if fl['vendidos'] > 0:
                return jsonify(ok=False,
                               error='Ese libro ya tiene ventas registradas: no se puede quitar. '
                                     'Ajusta las cantidades en vez de quitarlo.'), 409
            con.execute('DELETE FROM feria_libros WHERE id = ?', (flid,))
            registrar_movimiento(con, fl['feria_id'], 'quitar',
                                 'quitado con %d ejemplar(es) cargado(s)' % fl['llevados'],
                                 fl['libro_id'])
        return jsonify(ok=True)

    @app.get('/api/ferias/<int:fid>/catalogo')
    @requiere_login
    def api_catalogo(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                return jsonify(ok=False, error='Feria inexistente.'), 404
            libros = db.filas(con, '''
                SELECT fl.id AS fl_id, fl.precio, fl.llevados, fl.repuestos,
                       fl.vendidos, fl.perdidos, l.id AS libro_id, l.isbn,
                       l.titulo, l.autor, l.editorial, l.coleccion, l.temas,
                       COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                  JOIN reservas r ON r.id = ri.reserva_id
                                 WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                                   AND ri.libro_id = fl.libro_id), 0) AS reservado,
                       (SELECT r.nombre FROM reserva_items ri
                          JOIN reservas r ON r.id = ri.reserva_id
                         WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                           AND ri.libro_id = fl.libro_id ORDER BY r.id LIMIT 1) AS reserva_nombre
                  FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ? ORDER BY l.titulo''', (fid,))
            for l in libros:
                l['disponible'] = disponible(l)
            items = db.filas(con, '''
                SELECT vi.venta_id, vi.cantidad, vi.precio, vi.descuento, l.titulo, l.isbn
                  FROM venta_items vi
                  JOIN ventas v ON v.id = vi.venta_id
                  JOIN libros l ON l.id = vi.libro_id
                 WHERE v.feria_id = ? AND v.estado = 'confirmada' ''', (fid,))
            formas = formas_pago_activas(con)
        # el permiso lo dice el servidor: el celular no puede quedar con una pantalla vieja
        puede_editar = bool(g.usuario and g.usuario['rol'] == 'admin'
                            and feria['estado'] != 'cerrada')
        return jsonify(ok=True, feria=feria, libros=libros, items=items,
                       formas_pago=formas, puede_editar=puede_editar)

    # ---- ventas
    @app.get('/ferias/<int:fid>/vender')
    @requiere_vendedor
    def vender(fid):
        reserva = None
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            formas = formas_pago_activas(con)
            cambios = cambios_de_precio(con, fid,
                                        usuario_id=g.usuario['id'] if g.usuario else None)
            rid = a_entero(request.args.get('reserva'))
            if rid:
                reserva = db.fila(con, "SELECT * FROM reservas WHERE id = ? AND feria_id = ? "
                                       "AND estado = 'activa'", (rid, fid))
        return render_template('vender.html', feria=feria, formas_pago=formas,
                               cambios=cambios, reserva=reserva)

    @app.get('/api/ferias/<int:fid>/precios')
    @requiere_login
    def api_precios_fair(fid):
        """Cambios de precio desde una marca de tiempo (para el aviso en vivo)."""
        desde = marcar_valor(request.args.get('desde'))
        with db.conexion() as con:
            sql = '''SELECT m.cuando, m.detalle, m.libro_id, l.titulo, l.isbn
                       FROM movimientos m LEFT JOIN libros l ON l.id = m.libro_id
                      WHERE m.feria_id = ? AND m.accion = 'precio' '''
            params = [fid]
            if desde:
                sql += ' AND m.cuando > ?'
                params.append(desde)
            sql += ' ORDER BY m.id DESC LIMIT 50'
            filas = db.filas(con, sql, tuple(params))
            ahora = db.ahora()
        for f in filas:
            partes = (f['detalle'] or '').split('->')
            f['antes'] = a_decimal(partes[0]) if len(partes) == 2 else 0
            f['despues'] = a_decimal(partes[1]) if len(partes) == 2 else 0
        return jsonify(ok=True, cambios=filas, ahora=ahora)

    @app.post('/api/ferias/<int:fid>/precios/visto')
    @requiere_login
    def api_precios_visto(fid):
        """Marca para este usuario que ya vio los cambios hasta ahora."""
        with db.conexion() as con:
            asegurar_tabla_vistos(con)
            con.execute('''INSERT INTO precios_vistos (usuario_id, feria_id, hasta)
                           VALUES (?, ?, ?)
                           ON CONFLICT(usuario_id, feria_id)
                           DO UPDATE SET hasta = excluded.hasta''',
                        (g.usuario['id'], fid, db.ahora()))
        return jsonify(ok=True)

    @app.post('/api/ferias/<int:fid>/precio_actual')
    @requiere_login
    def api_precio_actual(fid):
        """Precio vigente de los libros que estan en la venta (se consulta antes de cobrar)."""
        datos = request.get_json(silent=True) or {}
        ids = datos.get('libro_ids') or []
        if not isinstance(ids, list) or not ids or len(ids) > 200:
            return jsonify(ok=False, error='Faltan los libros.'), 400
        limpios = [a_entero(x) for x in ids if a_entero(x)]
        if not limpios:
            return jsonify(ok=False, error='Faltan los libros.'), 400
        marcas = ','.join('?' * len(limpios))
        with db.conexion() as con:
            filas = db.filas(con, '''SELECT libro_id, precio FROM feria_libros
                                      WHERE feria_id = ? AND libro_id IN (%s)''' % marcas,
                             tuple([fid] + limpios))
        return jsonify(ok=True, precios={f['libro_id']: f['precio'] for f in filas})

    @app.post('/api/ferias/<int:fid>/venta')
    @requiere_vendedor
    def api_venta(fid):
        datos = request.get_json(silent=True) or {}
        idem = marcar_valor(datos.get('idem'))
        if not idem or len(idem) > 64:
            return jsonify(ok=False, error='Falta el identificador de la operacion.'), 400
        forma = marcar_valor(datos.get('forma_pago')) or 'efectivo'
        dispositivo = marcar_valor(datos.get('dispositivo')) or 'C1'
        pedido = datos.get('items') or []
        if not isinstance(pedido, list) or not pedido:
            return jsonify(ok=False, error='La venta no tiene items.'), 400
        if len(pedido) > 200:
            return jsonify(ok=False, error='Demasiados items.'), 400

        descuento_total = max(0.0, a_decimal(datos.get('descuento')))
        pide_factura = 1 if datos.get('pide_factura') else 0
        pendiente = 1 if datos.get('pendiente') else 0
        cli = datos.get('cliente') or {}
        nombre_cli = marcar_valor(cli.get('nombre'))
        telefono_cli = marcar_valor(cli.get('telefono'))
        email_cli = marcar_valor(cli.get('email'))
        dni_cli = marcar_valor(cli.get('dni'))
        cuit_cli = marcar_valor(cli.get('cuit'))
        notas_cli = marcar_valor(cli.get('notas'))

        if pide_factura and (not nombre_cli or not (telefono_cli or email_cli)):
            return jsonify(ok=False,
                           error='Para facturar hacen falta nombre y telefono o mail.'), 400
        if pendiente and (not nombre_cli or not telefono_cli):
            return jsonify(ok=False,
                           error='Para dejar la venta pendiente hacen falta nombre y '
                                 'telefono.'), 400

        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                return jsonify(ok=False, error='Feria inexistente.'), 404
            if feria['estado'] != 'abierta':
                return jsonify(ok=False, error='La feria no esta abierta.'), 409
            if forma not in claves_pago(con):
                return jsonify(ok=False, error='Forma de pago invalida.'), 400
            if pendiente:
                datos_forma = db.fila(con, 'SELECT * FROM formas_pago WHERE clave = ?',
                                      (forma,))
                if not datos_forma or not (datos_forma.get('banco') or datos_forma.get('cbu')
                                           or datos_forma.get('alias')):
                    return jsonify(ok=False, error='Esa forma de pago no tiene cargados los '
                                                   'datos de la cuenta. Pedile al admin que '
                                                   'la complete.'), 400

            repetida = db.fila(con, 'SELECT * FROM ventas WHERE idem = ?', (idem,))
            if repetida:
                return jsonify(ok=True, numero=repetida['numero'],
                               total=repetida['total'], repetida=True)

            # Normalizar items contra el catalogo de la feria (el precio manda el servidor)
            items = {}
            for it in pedido:
                lib_id = a_entero(it.get('libro_id'))
                cant = a_entero(it.get('cantidad'))
                if not lib_id or cant <= 0 or cant > 9999:
                    return jsonify(ok=False, error='Item invalido.'), 400
                desc = max(0.0, a_decimal(it.get('descuento')))
                if lib_id in items:
                    items[lib_id]['cantidad'] += cant
                    items[lib_id]['descuento'] += desc
                else:
                    items[lib_id] = {'cantidad': cant, 'descuento': desc}

            catalogo = {r['libro_id']: r for r in db.filas(con, '''
                SELECT fl.*, l.titulo FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ?''', (fid,))}
            sin_cargar = set()
            for lib_id in items:
                if lib_id in catalogo:
                    continue
                libro = db.fila(con, 'SELECT * FROM libros WHERE id = ?', (lib_id,))
                if not libro:
                    return jsonify(ok=False, error='Ese libro no esta en el sistema.'), 400
                # no estaba cargado en la feria: se agrega sin stock y la venta queda marcada
                con.execute('''INSERT OR IGNORE INTO feria_libros
                    (feria_id, libro_id, precio, llevados, repuestos, vendidos, perdidos)
                    VALUES (?, ?, ?, 0, 0, 0, 0)''', (fid, lib_id, libro['precio_sis']))
                nuevo = db.fila(con, '''SELECT fl.*, l.titulo
                                          FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                                         WHERE fl.feria_id = ? AND fl.libro_id = ?''',
                                (fid, lib_id))
                nuevo['libro_id'] = lib_id
                catalogo[lib_id] = nuevo
                sin_cargar.add(lib_id)

            subtotal = 0.0
            desc_items = 0.0
            sobreventa = 0
            for lib_id, it in items.items():
                c = catalogo[lib_id]
                it['precio'] = c['precio']
                it['titulo'] = c['titulo']
                it['descuento'] = min(it['descuento'], c['precio'] * it['cantidad'])
                subtotal += c['precio'] * it['cantidad']
                desc_items += it['descuento']
                if c['vendidos'] + it['cantidad'] > c['llevados'] + c['repuestos']:
                    sobreventa = 1

            subtotal = round(subtotal, 2)
            desc_items = round(desc_items, 2)
            descuento_total = min(descuento_total, max(0.0, subtotal - desc_items))
            total = round(max(0.0, subtotal - desc_items - descuento_total), 2)

            cliente_id = None
            if nombre_cli or telefono_cli or email_cli or dni_cli or cuit_cli:
                cur = con.execute('''INSERT INTO clientes
                    (nombre, telefono, email, dni, cuit, notas, creado)
                    VALUES (?, ?, ?, ?, ?, ?, ?)''',
                    (nombre_cli, telefono_cli, email_cli, dni_cli, cuit_cli,
                     notas_cli, db.ahora()))
                cliente_id = cur.lastrowid

            # Numeracion F03-C2-0017
            cont = db.fila(con, 'SELECT ultimo FROM contadores WHERE feria_id = ? AND dispositivo = ?',
                           (fid, dispositivo))
            ultimo = (cont['ultimo'] if cont else 0) + 1
            if cont:
                con.execute('UPDATE contadores SET ultimo = ? WHERE feria_id = ? AND dispositivo = ?',
                            (ultimo, fid, dispositivo))
            else:
                con.execute('INSERT INTO contadores (feria_id, dispositivo, ultimo) VALUES (?, ?, ?)',
                            (fid, dispositivo, ultimo))
            numero = 'F%02d-%s-%04d' % (fid, dispositivo, ultimo)

            estado_venta = 'pendiente' if pendiente else 'confirmada'
            ref = generar_ref() if pendiente else None
            cur = con.execute('''INSERT INTO ventas
                (feria_id, numero, dispositivo, cuando, cliente_id, pide_factura,
                 forma_pago, subtotal, descuento, total, estado, sobreventa, idem, usuario_id,
                 ref)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''', (
                fid, numero, dispositivo, db.ahora(), cliente_id, pide_factura,
                forma, subtotal, round(desc_items + descuento_total, 2), total,
                estado_venta, sobreventa, idem, g.usuario['id'], ref))
            venta_id = cur.lastrowid

            for lib_id, it in items.items():
                con.execute('''INSERT INTO venta_items
                    (venta_id, libro_id, cantidad, precio, descuento, sin_cargar)
                    VALUES (?, ?, ?, ?, ?, ?)''',
                    (venta_id, lib_id, it['cantidad'], it['precio'], round(it['descuento'], 2),
                     1 if lib_id in sin_cargar else 0))
                con.execute('UPDATE feria_libros SET vendidos = vendidos + ? '
                            'WHERE feria_id = ? AND libro_id = ?',
                            (it['cantidad'], fid, lib_id))

            # si la venta viene de una reserva, queda entregada (salvo que quede pendiente)
            reserva_id = a_entero(datos.get('reserva_id'))
            if reserva_id:
                res = db.fila(con, 'SELECT * FROM reservas WHERE id = ? AND feria_id = ?',
                              (reserva_id, fid))
                if res and res['estado'] == 'activa':
                    if estado_venta == 'confirmada':
                        con.execute("UPDATE reservas SET estado = 'entregada', venta_id = ? "
                                    'WHERE id = ?', (venta_id, reserva_id))
                        registrar_movimiento(con, fid, 'reserva',
                                             'entregada a %s' % (res['nombre'] or 'sin nombre'))
                    else:
                        con.execute('UPDATE reservas SET venta_id = ? WHERE id = ?',
                                    (venta_id, reserva_id))
                        registrar_movimiento(con, fid, 'reserva',
                                             'esperando el pago de %s'
                                             % (res['nombre'] or 'sin nombre'))

        return jsonify(ok=True, numero=numero, total=total, venta_id=venta_id,
                       sobreventa=bool(sobreventa), pendiente=bool(pendiente), ref=ref,
                       forma=forma)

    @app.post('/api/ventas/<int:vid>/anular')
    @requiere_login
    def api_anular(vid):
        datos = request.get_json(silent=True) or {}
        motivo = marcar_valor(datos.get('motivo') or request.form.get('motivo')) or 'Sin motivo'
        with db.conexion() as con:
            v = db.fila(con, 'SELECT * FROM ventas WHERE id = ?', (vid,))
            if not v:
                if request.is_json:
                    return jsonify(ok=False, error='No existe.'), 404
                flash('Esa venta no existe.', 'error')
                return redirect(url_for('inicio'))
            if v['estado'] == 'anulada':
                if request.is_json:
                    return jsonify(ok=True, ya=True)
                flash('La venta ya estaba anulada.', 'error')
                return redirect(url_for('ferias_ventas', fid=v['feria_id']))
            rol = (g.usuario or {}).get('rol')
            if v['estado'] == 'pendiente':
                if rol not in ('admin', 'vendedor'):
                    abort(403)
            elif rol != 'admin':
                abort(403)
            con.execute("UPDATE ventas SET estado = 'anulada' WHERE id = ?", (vid,))
            for it in db.filas(con, 'SELECT * FROM venta_items WHERE venta_id = ?', (vid,)):
                con.execute('UPDATE feria_libros SET vendidos = vendidos - ? '
                            'WHERE feria_id = ? AND libro_id = ?',
                            (it['cantidad'], v['feria_id'], it['libro_id']))
            # si venia de una reserva, la reserva sigue activa
            con.execute("UPDATE reservas SET venta_id = NULL WHERE venta_id = ? "
                        "AND estado = 'activa'", (vid,))
            registrar_movimiento(con, v['feria_id'], 'anular',
                                 'venta %s anulada: %s (total %.2f)'
                                 % (v['numero'], motivo, v['total'] or 0))
        if request.is_json:
            return jsonify(ok=True)
        era_pendiente = (v['estado'] == 'pendiente')
        flash('Venta %s anulada.' % v['numero'], 'ok')
        if era_pendiente:
            # se vuelve a la lista de pendientes: es donde estaba el usuario
            return redirect(url_for('feria_pendientes', fid=v['feria_id']))
        return redirect(url_for('ferias_ventas', fid=v['feria_id']))

    @app.post('/api/ventas/<int:vid>/confirmar')
    @requiere_vendedor
    def api_venta_confirmar(vid):
        """Confirma el pago de una venta pendiente (transferencia verificada)."""
        with db.conexion() as con:
            v = db.fila(con, 'SELECT * FROM ventas WHERE id = ?', (vid,))
            if not v:
                if request.is_json:
                    return jsonify(ok=False, error='No existe.'), 404
                flash('Esa venta no existe.', 'error')
                return redirect(url_for('inicio'))
            if v['estado'] == 'confirmada':
                if request.is_json:
                    return jsonify(ok=True, ya=True)
                flash('La venta ya estaba confirmada.', 'error')
                return redirect(url_for('feria_pendientes', fid=v['feria_id']))
            if v['estado'] == 'anulada':
                if request.is_json:
                    return jsonify(ok=False, error='La venta esta anulada.'), 409
                flash('La venta esta anulada.', 'error')
                return redirect(url_for('feria_pendientes', fid=v['feria_id']))
            con.execute("UPDATE ventas SET estado = 'confirmada' WHERE id = ?", (vid,))
            registrar_movimiento(con, v['feria_id'], 'cobrar',
                                 'pago confirmado de %s (Ref. %s)'
                                 % (v['numero'], v['ref'] or ''))
            res = db.fila(con, "SELECT * FROM reservas WHERE venta_id = ? "
                               "AND estado = 'activa'", (vid,))
            if res:
                con.execute("UPDATE reservas SET estado = 'entregada' WHERE id = ?",
                            (res['id'],))
                registrar_movimiento(con, v['feria_id'], 'reserva',
                                     'entregada a %s' % (res['nombre'] or ''))
        if request.is_json:
            return jsonify(ok=True)
        flash('Pago confirmado: ya cuenta en la caja.', 'ok')
        return redirect(url_for('feria_pendientes', fid=v['feria_id']))

    @app.get('/ferias/<int:fid>/pendientes')
    @requiere_vendedor
    def feria_pendientes(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            ventas = db.filas(con, '''
                SELECT v.*, c.nombre AS cliente_nombre, c.telefono AS cliente_telefono,
                       c.email AS cliente_email
                  FROM ventas v LEFT JOIN clientes c ON c.id = v.cliente_id
                 WHERE v.feria_id = ? AND v.estado = 'pendiente'
                 ORDER BY v.id''', (fid,))
            items = db.filas(con, '''
                SELECT vi.*, l.titulo, l.isbn
                  FROM venta_items vi JOIN libros l ON l.id = vi.libro_id
                 WHERE vi.venta_id IN (SELECT id FROM ventas WHERE feria_id = ?
                                        AND estado = 'pendiente')''', (fid,))
        por_venta = {}
        for it in items:
            por_venta.setdefault(it['venta_id'], []).append(it)
        for v in ventas:
            v['libros'] = por_venta.get(v['id'], [])
        return render_template('pendientes.html', feria=feria, ventas=ventas,
                               tab='pendientes')

    @app.get('/ferias/<int:fid>/ventas')
    @requiere_login
    def ferias_ventas(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            ventas = db.filas(con, '''
                SELECT v.*, c.nombre AS cliente_nombre, c.telefono AS cliente_telefono,
                       c.email AS cliente_email
                  FROM ventas v LEFT JOIN clientes c ON c.id = v.cliente_id
                 WHERE v.feria_id = ? ORDER BY v.id DESC''', (fid,))
            items = db.filas(con, '''
                SELECT vi.*, l.titulo, l.isbn
                  FROM venta_items vi JOIN libros l ON l.id = vi.libro_id
                 WHERE vi.venta_id IN (SELECT id FROM ventas WHERE feria_id = ?)
                 ORDER BY vi.venta_id DESC''', (fid,))
        agrupados = {}
        for it in items:
            agrupados.setdefault(it['venta_id'], []).append(it)
        return render_template('ventas.html', feria=feria, ventas=ventas,
                               items=agrupados)

    # ---- caja
    @app.get('/ferias/<int:fid>/caja')
    @requiere_login
    def feria_caja(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            por_forma = {}
            for r in db.filas(con, '''
                    SELECT forma_pago, COALESCE(SUM(total), 0) AS total,
                           COUNT(*) AS operaciones
                      FROM ventas WHERE feria_id = ? AND estado = 'confirmada'
                     GROUP BY forma_pago''', (fid,)):
                por_forma[r['forma_pago']] = {'total': r['total'], 'operaciones': r['operaciones']}
            # las formas que no tuvieron ventas se muestran en cero
            for clave, _nombre in formas_pago_todas(con):
                por_forma.setdefault(clave, {'total': 0.0, 'operaciones': 0})
            nombres = dict(formas_pago_todas(con))
            ventas_ok = db.fila(con, '''
                SELECT COUNT(*) AS n, COALESCE(SUM(total), 0) AS total,
                       COALESCE(SUM(descuento), 0) AS descuento
                  FROM ventas WHERE feria_id = ? AND estado = 'confirmada' ''', (fid,))
            anuladas = db.valor(con, "SELECT COUNT(*) FROM ventas WHERE feria_id = ? AND estado = 'anulada'", (fid,))
            arqueos = db.filas(con, '''
                SELECT a.*, u.nombre AS usuario_nombre
                  FROM arqueos a LEFT JOIN usuarios u ON u.id = a.usuario_id
                 WHERE a.feria_id = ? ORDER BY a.id DESC''', (fid,))
            sobreventas = db.valor(con, 'SELECT COUNT(*) FROM ventas WHERE feria_id = ? AND sobreventa = 1', (fid,))
            pendientes = db.fila(con, '''
                SELECT COUNT(*) AS n, COALESCE(SUM(total), 0) AS total
                  FROM ventas WHERE feria_id = ? AND estado = 'pendiente' ''', (fid,))
        en_caja = feria['caja_inicial'] + (por_forma['efectivo']['total'] if 'efectivo' in por_forma else 0)
        total = (ventas_ok['total'] if ventas_ok else 0) or 0
        return render_template('caja.html', feria=feria, por_forma=por_forma,
                               nombres=nombres,
                               ventas_ok=ventas_ok, anuladas=anuladas,
                               arqueos=arqueos, en_caja=round(en_caja, 2),
                               sobreventas=sobreventas, pendientes=pendientes)

    @app.post('/ferias/<int:fid>/arqueo')
    @requiere_admin
    def feria_arqueo(fid):
        forma = marcar_valor(request.form.get('forma_pago'))
        contado = a_decimal(request.form.get('contado'))
        nota = marcar_valor(request.form.get('nota'))
        with db.conexion() as con:
            if forma not in claves_pago(con, solo_activas=False):
                flash('Forma de pago invalida.', 'error')
                return redirect(url_for('feria_caja', fid=fid))
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            esperado = db.valor(con, '''
                SELECT COALESCE(SUM(total), 0) FROM ventas
                 WHERE feria_id = ? AND estado = 'confirmada' AND forma_pago = ?''',
                                (fid, forma)) or 0
            if forma == 'efectivo':
                esperado += feria['caja_inicial']
            con.execute('''INSERT INTO arqueos
                (feria_id, cuando, forma_pago, esperado, contado, diferencia, nota, usuario_id)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', (
                fid, db.ahora(), forma, round(esperado, 2), contado,
                round(contado - esperado, 2), nota, g.usuario['id']))
        flash('Arqueo registrado.', 'ok')
        return redirect(url_for('feria_caja', fid=fid))

    @app.get('/api/ferias/<int:fid>/buscar')
    @requiere_login
    def api_buscar_libros(fid):
        """Busca libros de la feria por titulo, autor o ISBN (sin acentos)."""
        q = marcar_valor(request.args.get('q')) or ''
        if len(q) < 2:
            return jsonify(ok=True, libros=[])
        with db.conexion() as con:
            libros = db.filas(con, '''
                SELECT fl.id AS fl_id, fl.precio, fl.llevados, fl.repuestos, fl.vendidos,
                       fl.perdidos, l.id AS libro_id, l.isbn, l.titulo, l.autor,
                       COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                  JOIN reservas r ON r.id = ri.reserva_id
                                 WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                                   AND ri.libro_id = fl.libro_id), 0) AS reservado
                  FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ?''', (fid,))
        clave = sin_acentos(q)
        salida = []
        for l in libros:
            if (clave in sin_acentos(l['titulo'])
                    or clave in sin_acentos(l['autor'])
                    or str(l['isbn'] or '').startswith(q)):
                l['id'] = l['libro_id']
                l['disponible'] = disponible(l)
                salida.append(l)
        salida.sort(key=lambda x: (x['titulo'] or '').lower())
        return jsonify(ok=True, libros=salida[:20])

    # ---- reservas (vendedor y admin)
    @app.get('/ferias/<int:fid>/reservas')
    @requiere_vendedor
    def feria_reservas(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            reservas = db.filas(con, '''
                SELECT r.*, u.nombre AS usuario_nombre
                  FROM reservas r LEFT JOIN usuarios u ON u.id = r.usuario_id
                 WHERE r.feria_id = ? ORDER BY r.id DESC''', (fid,))
            items = db.filas(con, '''
                SELECT ri.*, l.titulo, l.isbn
                  FROM reserva_items ri JOIN libros l ON l.id = ri.libro_id
                 WHERE ri.reserva_id IN (SELECT id FROM reservas WHERE feria_id = ?)''',
                             (fid,))
        por_reserva = {}
        for it in items:
            por_reserva.setdefault(it['reserva_id'], []).append(it)
        for r in reservas:
            r['items'] = por_reserva.get(r['id'], [])
            r['total'] = sum((i['precio'] or 0) * i['cantidad'] for i in r['items'])
        activas = [r for r in reservas if r['estado'] == 'activa']
        cerradas = [r for r in reservas if r['estado'] != 'activa']
        return render_template('reservas.html', feria=feria, activas=activas,
                               cerradas=cerradas, tab='reservas')

    @app.post('/api/ferias/<int:fid>/reservas')
    @requiere_vendedor
    def api_reserva_crear(fid):
        datos = request.get_json(silent=True) or {}
        nombre = marcar_valor(datos.get('nombre'))
        telefono = marcar_valor(datos.get('telefono'))
        nota = marcar_valor(datos.get('nota'))
        pedido = datos.get('items') or []
        if not nombre:
            return jsonify(ok=False, error='Falta el nombre de quien reserva.'), 400
        if not telefono:
            return jsonify(ok=False, error='Falta el telefono de contacto.'), 400
        if not isinstance(pedido, list) or not pedido or len(pedido) > 100:
            return jsonify(ok=False, error='La reserva no tiene libros.'), 400
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                return jsonify(ok=False, error='Feria inexistente.'), 404
            if feria['estado'] == 'cerrada':
                return jsonify(ok=False, error='La feria esta cerrada.'), 409
            cur = con.execute('''INSERT INTO reservas
                (feria_id, nombre, telefono, nota, estado, creada, usuario_id)
                VALUES (?, ?, ?, ?, 'activa', ?, ?)''',
                (fid, nombre, telefono, nota, db.ahora(), g.usuario['id']))
            rid = cur.lastrowid
            for it in pedido:
                lib_id = a_entero(it.get('libro_id'))
                cant = a_entero(it.get('cantidad'))
                if not lib_id or cant <= 0 or cant > 999:
                    con.execute('DELETE FROM reservas WHERE id = ?', (rid,))
                    return jsonify(ok=False, error='Libro o cantidad invalida.'), 400
                fl = db.fila(con, 'SELECT * FROM feria_libros WHERE feria_id = ? '
                                  'AND libro_id = ?', (fid, lib_id))
                if not fl:
                    con.execute('DELETE FROM reservas WHERE id = ?', (rid,))
                    return jsonify(ok=False, error='Ese libro no esta cargado en la feria.'), 400
                con.execute('''INSERT INTO reserva_items (reserva_id, libro_id, cantidad, precio)
                               VALUES (?, ?, ?, ?)''', (rid, lib_id, cant, fl['precio']))
            registrar_movimiento(con, fid, 'reserva', 'reserva de %s' % nombre)
        return jsonify(ok=True, reserva_id=rid)

    @app.get('/api/reservas/<int:rid>')
    @requiere_vendedor
    def api_reserva_ver(rid):
        with db.conexion() as con:
            r = db.fila(con, 'SELECT * FROM reservas WHERE id = ?', (rid,))
            if not r:
                return jsonify(ok=False, error='No existe.'), 404
            items = db.filas(con, '''
                SELECT ri.*, l.titulo, l.isbn
                  FROM reserva_items ri JOIN libros l ON l.id = ri.libro_id
                 WHERE ri.reserva_id = ?''', (rid,))
        return jsonify(ok=True, reserva=dict(r), items=items)

    @app.post('/api/reservas/<int:rid>/cancelar')
    @requiere_vendedor
    def api_reserva_cancelar(rid):
        with db.conexion() as con:
            r = db.fila(con, 'SELECT * FROM reservas WHERE id = ?', (rid,))
            if not r:
                return jsonify(ok=False, error='No existe.'), 404
            if r['estado'] != 'activa':
                return jsonify(ok=True, ya=True)
            con.execute("UPDATE reservas SET estado = 'cancelada' WHERE id = ?", (rid,))
            registrar_movimiento(con, r['feria_id'], 'reserva',
                                 'cancelada: %s' % (r['nombre'] or ''))
        return jsonify(ok=True)

    @app.get('/ferias/<int:fid>/reservas/<int:rid>/entregar')
    @requiere_vendedor
    def feria_reserva_entregar(fid, rid):
        return redirect(url_for('vender', fid=fid, reserva=rid))

    # ---- reportes
    @app.get('/ferias/<int:fid>/reportes')
    @requiere_admin
    def feria_reportes(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            listado = []
            for clave, titulo, descripcion in REPORTES_FERIA:
                encabezados, filas = _reporte_feria(con, fid, clave)
                listado.append({'clave': clave, 'titulo': titulo, 'descripcion': descripcion,
                                'filas': len(filas)})
            arqueos = db.valor(con, 'SELECT COUNT(*) FROM arqueos WHERE feria_id = ?',
                               (fid,)) or 0
            texto = _resumen_para_compartir(con, fid)
            if feria['estado'] != 'cerrada':
                texto += '\nCierre: pendiente (la feria sigue abierta)'
            elif not arqueos:
                texto += '\nCierre: falta el arqueo de caja'
        if feria['estado'] != 'cerrada':
            estado_cierre = 'abierta'
        elif not arqueos:
            estado_cierre = 'sin arqueo'
        else:
            estado_cierre = 'completo'
        datos_compartir = [{'clave': c['clave'],
                            'archivo': 'feria-%d-%s.csv' % (fid, c['clave']),
                            'url': url_for('feria_reporte_csv', fid=fid, nombre=c['clave'])}
                           for c in listado]
        return render_template('reportes.html', feria=feria, reportes=listado,
                               texto_compartir=texto, datos_compartir=datos_compartir,
                               estado_cierre=estado_cierre, tab='reportes')

    @app.get('/ferias/<int:fid>/reportes/<nombre>.csv')
    @requiere_admin
    def feria_reporte_csv(fid, nombre):
        with db.conexion() as con:
            if nombre not in [c for c, _, _ in REPORTES_FERIA]:
                abort(404)
            try:
                encabezados, filas = _reporte_feria(con, fid, nombre)
            except ValueError:
                abort(404)
        contenido = _csv_reporte(encabezados, filas)
        nombre_archivo = 'feria-%d-%s.csv' % (fid, nombre)
        return Response(contenido, mimetype='text/csv; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename="%s"'
                                 % nombre_archivo})

    @app.get('/ferias/<int:fid>/reportes/paquete.zip')
    @requiere_admin
    def feria_reporte_zip(fid):
        memoria = io.BytesIO()
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            with zipfile.ZipFile(memoria, 'w', zipfile.ZIP_DEFLATED) as paquete:
                for clave, _titulo, _descripcion in REPORTES_FERIA:
                    try:
                        encabezados, filas = _reporte_feria(con, fid, clave)
                    except ValueError:
                        continue
                    paquete.writestr('feria-%d-%s.csv' % (fid, clave),
                                     _csv_reporte(encabezados, filas))
        respuesta = Response(memoria.getvalue(), mimetype='application/zip')
        respuesta.headers['Content-Disposition'] = (
            'attachment; filename="feria-%d-reportes.zip"' % fid)
        return respuesta

    # ---- cierre
    @app.get('/ferias/<int:fid>/cerrar')
    @requiere_login
    def feria_cerrar_vista(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            libros = db.filas(con, '''
                SELECT fl.*, l.isbn, l.titulo, l.autor,
                       (SELECT COUNT(*) FROM venta_items vi
                          JOIN ventas v ON v.id = vi.venta_id
                         WHERE vi.libro_id = fl.libro_id AND v.feria_id = fl.feria_id
                           AND v.estado = 'confirmada' AND vi.sin_cargar = 1) AS sin_cargar_n,
                       COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                  JOIN reservas r ON r.id = ri.reserva_id
                                 WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                                   AND ri.libro_id = fl.libro_id), 0) AS reservado
                  FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ? ORDER BY l.titulo''', (fid,))
            for l in libros:
                l['disponible'] = disponible(l)
                l['sin_cargar'] = 1 if l['sin_cargar_n'] else 0
                # los reservados vuelven a la feria al cerrar: se cuentan como devueltos
                l['devueltos'] = max(0, l['llevados'] + l['repuestos']
                                     - l['vendidos'] - l['perdidos'])
                l['vendido_de_mas'] = 1 if l['vendidos'] > l['llevados'] + l['repuestos'] else 0
            movimientos = db.filas(con, '''
                SELECT m.*, l.titulo, u.nombre AS usuario_nombre
                  FROM movimientos m
                  LEFT JOIN libros l ON l.id = m.libro_id
                  LEFT JOIN usuarios u ON u.id = m.usuario_id
                 WHERE m.feria_id = ? ORDER BY m.id DESC LIMIT 300''', (fid,))
        return render_template('cerrar.html', feria=feria, libros=libros,
                               movimientos=movimientos)

    @app.post('/ferias/<int:fid>/cerrar')
    @requiere_admin
    def feria_cerrar(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            if feria['estado'] == 'cerrada':
                flash('La feria ya estaba cerrada.', 'error')
                return redirect(url_for('feria_detalle', fid=fid))
            activas = db.valor(con, "SELECT COUNT(*) FROM reservas "
                                     "WHERE feria_id = ? AND estado = 'activa'", (fid,)) or 0
            if activas:
                flash('Hay %d reserva%s sin resolver. Entregalas o cancelalas antes de '
                      'cerrar la feria.' % (activas, 's' if activas > 1 else ''), 'error')
                return redirect(url_for('feria_reservas', fid=fid))
            impagas = db.valor(con, "SELECT COUNT(*) FROM ventas "
                                    "WHERE feria_id = ? AND estado = 'pendiente'", (fid,)) or 0
            if impagas:
                flash('Hay %d venta%s pendiente%s de pago. Confirmá el pago o anulalas antes '
                      'de cerrar.' % (impagas, 's' if impagas > 1 else '',
                                      's' if impagas > 1 else ''), 'error')
                return redirect(url_for('feria_pendientes', fid=fid))
            for fl in db.filas(con, 'SELECT * FROM feria_libros WHERE feria_id = ?', (fid,)):
                perdidos = a_entero(request.form.get('perdidos_%d' % fl['id']), 0)
                if perdidos < 0:
                    perdidos = 0
                if perdidos != (fl['perdidos'] or 0):
                    registrar_movimiento(con, fid, 'perdidos',
                                         'perdidos: %s -> %s' % (fl['perdidos'], perdidos),
                                         fl['libro_id'])
                con.execute('UPDATE feria_libros SET perdidos = ? WHERE id = ?',
                            (perdidos, fl['id']))
            con.execute("UPDATE ferias SET estado = 'cerrada', cerrada = ? WHERE id = ?",
                        (db.ahora(), fid))
            registrar_movimiento(con, fid, 'cerrar', 'feria cerrada')
        flash('Feria cerrada. Ya no admite ventas.', 'ok')
        return redirect(url_for('feria_detalle', fid=fid))

    @app.post('/ferias/<int:fid>/eliminar')
    @requiere_admin
    def feria_eliminar(fid):
        """Borra una feria con todo lo suyo. Solo si no esta abierta."""
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            if feria['estado'] == 'abierta':
                flash('Cerra la feria antes de eliminarla.', 'error')
                return redirect(url_for('inicio'))
            if request.form.get('nombre') != feria['nombre']:
                flash('Para eliminar hay que escribir el nombre de la feria.', 'error')
                return redirect(url_for('inicio'))
            con.execute('DELETE FROM venta_items WHERE venta_id IN '
                        '(SELECT id FROM ventas WHERE feria_id = ?)', (fid,))
            con.execute('DELETE FROM ventas WHERE feria_id = ?', (fid,))
            for tabla in ('reposiciones', 'arqueos', 'movimientos',
                          'feria_libros', 'dispositivos', 'contadores'):
                con.execute('DELETE FROM %s WHERE feria_id = ?' % tabla, (fid,))
            con.execute('DELETE FROM clientes WHERE id NOT IN '
                        '(SELECT cliente_id FROM ventas WHERE cliente_id IS NOT NULL)')
            con.execute('DELETE FROM ferias WHERE id = ?', (fid,))
        flash('Feria eliminada.', 'ok')
        return redirect(url_for('inicio'))

    @app.post('/ferias/<int:fid>/reabrir')
    @requiere_admin
    def feria_reabrir(fid):
        with db.conexion() as con:
            con.execute("UPDATE ferias SET estado = 'abierta', cerrada = NULL WHERE id = ?", (fid,))
            registrar_movimiento(con, fid, 'reabrir', 'feria reabierta')
        flash('Feria reabierta.', 'ok')
        return redirect(url_for('feria_detalle', fid=fid))

    # ---- exportaciones
    def _csv(nombre, encabezados, filas_):
        salida = io.StringIO()
        w = csv.writer(salida, delimiter=';', lineterminator='\n')
        w.writerow(encabezados)
        for f in filas_:
            w.writerow(f)
        datos = salida.getvalue()
        return Response('\ufeff' + datos, mimetype='text/csv; charset=utf-8',
                        headers={'Content-Disposition': 'attachment; filename=%s' % nombre})

    @app.get('/ferias/<int:fid>/export/llevados.csv')
    @requiere_login
    def export_llevados(fid):
        with db.conexion() as con:
            filas_ = db.filas(con, '''
                SELECT l.isbn, l.titulo, l.autor, l.editorial, fl.precio,
                       fl.llevados, fl.repuestos, fl.vendidos, fl.perdidos,
                       (SELECT COUNT(*) FROM venta_items vi
                          JOIN ventas v ON v.id = vi.venta_id
                         WHERE vi.libro_id = fl.libro_id AND v.feria_id = fl.feria_id
                           AND v.estado = 'confirmada' AND vi.sin_cargar = 1) AS sin_cargar_n,
                       COALESCE((SELECT SUM(ri.cantidad) FROM reserva_items ri
                                  JOIN reservas r ON r.id = ri.reserva_id
                                 WHERE r.feria_id = fl.feria_id AND r.estado = 'activa'
                                   AND ri.libro_id = fl.libro_id), 0) AS reservado
                  FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ? ORDER BY l.titulo''', (fid,))
        datos = []
        for f in filas_:
            devueltos = max(0, f['llevados'] + f['repuestos'] - f['vendidos'] - f['perdidos'])
            datos.append([f['isbn'], f['titulo'], f['autor'], f['editorial'],
                          '%.2f' % f['precio'], f['llevados'], f['repuestos'],
                          f['vendidos'], f['perdidos'], devueltos, f['reservado'],
                          'SI' if f['sin_cargar_n'] else 'NO'])
        return _csv('feria_%d_llevados.csv' % fid,
                    ['ISBN', 'Titulo', 'Autor', 'Editorial', 'Precio', 'Llevados',
                     'Repuestos', 'Vendidos', 'Perdidos', 'Devueltos', 'Reservados',
                     'Sin cargar'], datos)

    @app.get('/ferias/<int:fid>/export/vendidos.csv')
    @requiere_login
    def export_vendidos(fid):
        with db.conexion() as con:
            ventas = db.filas(con, '''
                SELECT v.*, c.nombre AS cliente_nombre, c.telefono AS cliente_telefono,
                       c.email AS cliente_email, c.dni AS cliente_dni, c.cuit AS cliente_cuit
                  FROM ventas v LEFT JOIN clientes c ON c.id = v.cliente_id
                 WHERE v.feria_id = ? AND v.estado = 'confirmada' ORDER BY v.id''', (fid,))
            items = db.filas(con, '''
                SELECT vi.*, l.titulo, l.isbn
                  FROM venta_items vi JOIN libros l ON l.id = vi.libro_id
                 WHERE vi.venta_id IN (SELECT id FROM ventas WHERE feria_id = ?)
                 ORDER BY vi.id''', (fid,))
        agrupados = {}
        for it in items:
            agrupados.setdefault(it['venta_id'], []).append(it)
        datos = []
        for v in ventas:
            for it in agrupados.get(v['id'], []):
                datos.append([
                    v['numero'], v['cuando'], v['dispositivo'],
                    v['cliente_nombre'] or '', v['cliente_telefono'] or '',
                    v['cliente_email'] or '', v['cliente_dni'] or '', v['cliente_cuit'] or '',
                    'SI' if v['pide_factura'] else 'NO',
                    v['forma_pago'], it['isbn'], it['titulo'], it['cantidad'],
                    '%.2f' % it['precio'], '%.2f' % it['descuento'],
                    'SI' if it.get('sin_cargar') else 'NO',
                    '%.2f' % v['total']])
        return _csv('feria_%d_vendidos.csv' % fid,
                    ['Venta', 'Fecha', 'Dispositivo', 'Cliente', 'Telefono', 'Email',
                     'DNI', 'CUIT', 'Pide factura', 'Forma de pago', 'ISBN', 'Titulo',
                     'Cantidad', 'Precio', 'Descuento', 'Sin cargar', 'Total venta'], datos)

    @app.get('/ferias/<int:fid>/export/resumen.csv')
    @requiere_login
    def export_resumen(fid):
        with db.conexion() as con:
            feria = db.fila(con, 'SELECT * FROM ferias WHERE id = ?', (fid,))
            if not feria:
                abort(404)
            totales = db.filas(con, '''
                SELECT forma_pago, COUNT(*) AS n, COALESCE(SUM(total), 0) AS total
                  FROM ventas WHERE feria_id = ? AND estado = 'confirmada'
                 GROUP BY forma_pago''', (fid,))
            libros = db.filas(con, '''
                SELECT l.titulo, fl.llevados, fl.repuestos, fl.vendidos, fl.perdidos
                  FROM feria_libros fl JOIN libros l ON l.id = fl.libro_id
                 WHERE fl.feria_id = ?''', (fid,))
        datos = [['Feria', feria['nombre']], ['Lugar', feria['lugar']],
                 ['Desde', feria['desde']], ['Hasta', feria['hasta']],
                 ['Estado', feria['estado']], ['Caja inicial', '%.2f' % feria['caja_inicial']],
                 []]
        datos.append(['Forma de pago', 'Operaciones', 'Total'])
        gran_total = 0.0
        operaciones = 0
        for t in totales:
            datos.append([t['forma_pago'], t['n'], '%.2f' % t['total']])
            gran_total += t['total']
            operaciones += t['n']
        datos.append(['TOTAL', operaciones, '%.2f' % gran_total])
        datos.append([])
        llevados = sum(l['llevados'] + l['repuestos'] for l in libros)
        vendidos = sum(l['vendidos'] for l in libros)
        perdidos = sum(l['perdidos'] for l in libros)
        datos.append(['Ejemplares llevados', llevados])
        datos.append(['Ejemplares vendidos', vendidos])
        datos.append(['Ejemplares perdidos', perdidos])
        datos.append(['Ejemplares devueltos', llevados - vendidos - perdidos])
        if llevados:
            datos.append(['Sell-through', '%.1f%%' % (100.0 * vendidos / llevados)])
        return _csv('feria_%d_resumen.csv' % fid, [], datos)

    # ---- formas de pago (admin)
    @app.get('/formas-pago')
    @requiere_admin
    def formas_pago_vista():
        with db.conexion() as con:
            lista = db.filas(con, 'SELECT * FROM formas_pago ORDER BY orden, clave')
        return render_template('formas_pago.html', formas=lista)

    @app.post('/formas-pago/nueva')
    @requiere_admin
    def forma_pago_nueva():
        nombre = marcar_valor(request.form.get('nombre'))
        tipo = marcar_valor(request.form.get('tipo')) or 'simple'
        if tipo not in TIPOS_PAGO:
            tipo = 'simple'
        datos = {c: (marcar_valor(request.form.get(c)) or '')
                 for c in ('banco', 'titular', 'cuit', 'cbu', 'alias', 'nota')}
        if not nombre:
            flash('Poné un nombre para la forma de pago.', 'error')
            return redirect(url_for('formas_pago_vista'))
        if tipo == 'transferencia':
            if not datos['banco'] or not datos['titular'] or not datos['cbu']:
                flash('Para una transferencia hacen falta el banco, el titular y el CBU o CVU.',
                      'error')
                return redirect(url_for('formas_pago_vista'))
        clave = clave_desde(nombre)
        with db.conexion() as con:
            if db.fila(con, 'SELECT clave FROM formas_pago WHERE clave = ?', (clave,)):
                flash('Ya existe una forma de pago parecida. Cambiale el nombre.', 'error')
                return redirect(url_for('formas_pago_vista'))
            orden = (db.valor(con, 'SELECT MAX(orden) FROM formas_pago') or 0) + 1
            con.execute('''INSERT INTO formas_pago
                (clave, nombre, activo, orden, tipo, banco, titular, cuit, cbu, alias, nota)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (clave, nombre, orden, tipo, datos['banco'], datos['titular'],
                         datos['cuit'], datos['cbu'], datos['alias'], datos['nota']))
        if tipo == 'qr':
            subido = guardar_qr(request.files.get('qr'), clave)
            if subido:
                with db.conexion() as con:
                    con.execute('UPDATE formas_pago SET qr_imagen = ? WHERE clave = ?',
                                (subido, clave))
                flash('Forma de pago agregada con su QR.', 'ok')
                return redirect(url_for('formas_pago_vista'))
            if subido is False:
                flash('Forma de pago agregada, pero la imagen no es PNG, JPG ni WEBP. '
                      'Subila desde la tarjeta.', 'error')
                return redirect(url_for('formas_pago_vista'))
            flash('Forma de pago agregada. Falta subir la imagen del QR.', 'ok')
            return redirect(url_for('formas_pago_vista'))
        flash('Forma de pago agregada.', 'ok')
        return redirect(url_for('formas_pago_vista'))

    @app.post('/formas-pago/<clave>/datos')
    @requiere_admin
    def forma_pago_datos(clave):
        nombre = marcar_valor(request.form.get('nombre'))
        if not nombre:
            flash('El nombre no puede quedar vacío.', 'error')
            return redirect(url_for('formas_pago_vista'))
        tipo = marcar_valor(request.form.get('tipo')) or 'simple'
        if tipo not in TIPOS_PAGO:
            tipo = 'simple'
        datos = {c: (marcar_valor(request.form.get(c)) or '')
                 for c in ('banco', 'titular', 'cuit', 'cbu', 'alias', 'nota')}
        if tipo == 'transferencia' and (not datos['banco'] or not datos['titular']
                                        or not datos['cbu']):
            flash('Una transferencia necesita banco, titular y CBU o CVU.', 'error')
            return redirect(url_for('formas_pago_vista'))
        with db.conexion() as con:
            if not db.fila(con, 'SELECT clave FROM formas_pago WHERE clave = ?', (clave,)):
                abort(404)
            con.execute('''UPDATE formas_pago SET nombre = ?, tipo = ?, banco = ?, titular = ?,
                           cuit = ?, cbu = ?, alias = ?, nota = ? WHERE clave = ?''',
                        (nombre, tipo, datos['banco'], datos['titular'], datos['cuit'],
                         datos['cbu'], datos['alias'], datos['nota'], clave))
        if tipo == 'qr':
            subido = guardar_qr(request.files.get('qr'), clave)
            if subido:
                with db.conexion() as con:
                    con.execute('UPDATE formas_pago SET qr_imagen = ? WHERE clave = ?',
                                (subido, clave))
            elif subido is False:
                flash('La imagen tiene que ser PNG, JPG o WEBP.', 'error')
                return redirect(url_for('formas_pago_vista'))
        flash('Forma de pago actualizada.', 'ok')
        return redirect(url_for('formas_pago_vista'))

    @app.post('/formas-pago/<clave>/qr/borrar')
    @requiere_admin
    def forma_pago_qr_borrar(clave):
        with db.conexion() as con:
            f = db.fila(con, 'SELECT * FROM formas_pago WHERE clave = ?', (clave,))
            if not f:
                abort(404)
            ruta = f['qr_imagen'] or ''
            if ruta:
                try:
                    os.remove(os.path.join(BASE, 'static', ruta))
                except OSError:
                    pass
            con.execute("UPDATE formas_pago SET qr_imagen = '' WHERE clave = ?", (clave,))
        flash('Imagen del QR eliminada.', 'ok')
        return redirect(url_for('formas_pago_vista'))

    @app.post('/formas-pago/<clave>/renombrar')
    @requiere_admin
    def forma_pago_renombrar(clave):
        nombre = marcar_valor(request.form.get('nombre'))
        if not nombre:
            flash('El nombre no puede quedar vacío.', 'error')
            return redirect(url_for('formas_pago_vista'))
        with db.conexion() as con:
            con.execute('UPDATE formas_pago SET nombre = ? WHERE clave = ?', (nombre, clave))
        flash('Nombre actualizado.', 'ok')
        return redirect(url_for('formas_pago_vista'))

    @app.post('/formas-pago/<clave>/eliminar')
    @requiere_admin
    def forma_pago_eliminar(clave):
        with db.conexion() as con:
            f = db.fila(con, 'SELECT * FROM formas_pago WHERE clave = ?', (clave,))
            if not f:
                abort(404)
            usos = db.valor(con, 'SELECT COUNT(*) FROM ventas WHERE forma_pago = ?',
                            (clave,)) or 0
            if usos:
                flash('No se puede eliminar: hay %d venta%s con esa forma de pago. '
                      'Desactivala para que no aparezca al cobrar.'
                      % (usos, 's' if usos > 1 else ''), 'error')
                return redirect(url_for('formas_pago_vista'))
            activas = db.valor(con, 'SELECT COUNT(*) FROM formas_pago WHERE activo = 1') or 0
            if f['activo'] and activas <= 1:
                flash('Tiene que quedar al menos una forma de pago activa.', 'error')
                return redirect(url_for('formas_pago_vista'))
            con.execute('DELETE FROM formas_pago WHERE clave = ?', (clave,))
        flash('Forma de pago eliminada.', 'ok')
        return redirect(url_for('formas_pago_vista'))

    @app.post('/formas-pago/<clave>/alternar')
    @requiere_admin
    def forma_pago_alternar(clave):
        with db.conexion() as con:
            fila = db.fila(con, 'SELECT * FROM formas_pago WHERE clave = ?', (clave,))
            if not fila:
                abort(404)
            if fila['activo']:
                activas = db.valor(con, 'SELECT COUNT(*) FROM formas_pago WHERE activo = 1') or 0
                if activas <= 1:
                    flash('Tiene que quedar al menos una forma de pago activa.', 'error')
                    return redirect(url_for('formas_pago_vista'))
            con.execute('UPDATE formas_pago SET activo = 1 - activo WHERE clave = ?', (clave,))
        flash('Forma de pago actualizada.', 'ok')
        return redirect(url_for('formas_pago_vista'))

    # ---- actualizacion de precios (admin)
    @app.get('/precios')
    @requiere_admin
    def precios_vista():
        with db.conexion() as con:
            ajustes = leer_ajustes(con)
            ultimos = db.filas(con, '''
                SELECT m.cuando, m.detalle, l.titulo, f.nombre AS feria
                  FROM movimientos m
                  LEFT JOIN libros l ON l.id = m.libro_id
                  LEFT JOIN ferias f ON f.id = m.feria_id
                 WHERE m.accion = 'precio'
                 ORDER BY m.id DESC LIMIT 50''')
        return render_template('precios.html', ajustes=ajustes, ultimos=ultimos)

    @app.post('/precios/guardar')
    @requiere_admin
    def precios_guardar():
        activo = 1 if request.form.get('activo') else 0
        desde = marcar_valor(request.form.get('desde')) or '09:00'
        hh, mm = _hora_hhmm(desde)
        desde = '%02d:%02d' % (hh, mm)
        cada = a_entero(request.form.get('cada'), 2)
        if cada not in (1, 2, 3, 4, 6, 8, 12, 24):
            cada = 2
        with db.conexion() as con:
            con.execute('''UPDATE ajustes SET precios_activo = ?, precios_desde = ?,
                           precios_cada_horas = ? WHERE id = 1''', (activo, desde, cada))
        flash('Configuracion de precios guardada.', 'ok')
        return redirect(url_for('precios_vista'))

    @app.post('/precios/ahora')
    @requiere_admin
    def precios_ahora():
        threading.Thread(target=sincronizar_precios, daemon=True).start()
        flash('Actualizando precios en segundo plano. Puede tardar unos minutos.', 'ok')
        return redirect(url_for('precios_vista'))

    # ---- usuarios (admin)
    @app.get('/usuarios')
    @requiere_admin
    def usuarios():
        with db.conexion() as con:
            lista = db.filas(con, 'SELECT id, usuario, nombre, rol, activo, creado FROM usuarios ORDER BY id')
        return render_template('usuarios.html', usuarios=lista)

    @app.post('/usuarios/nuevo')
    @requiere_admin
    def usuario_nuevo():
        usuario = marcar_valor(request.form.get('usuario')).lower()
        nombre = marcar_valor(request.form.get('nombre'))
        rol = marcar_valor(request.form.get('rol')) or 'vendedor'
        clave = request.form.get('clave') or ''
        if not usuario or not nombre or not clave_valida(clave):
            flash('Usuario, nombre y una clave de %d o mas caracteres.' % CLAVE_MINIMA,
                  'error')
            return redirect(url_for('usuarios'))
        if rol not in ('admin', 'vendedor', 'repositor'):
            rol = 'vendedor'
        with db.conexion() as con:
            if db.fila(con, 'SELECT id FROM usuarios WHERE usuario = ?', (usuario,)):
                flash('Ese usuario ya existe.', 'error')
                return redirect(url_for('usuarios'))
            con.execute('''INSERT INTO usuarios (usuario, nombre, clave_hash, rol, activo, creado)
                           VALUES (?, ?, ?, ?, 1, ?)''',
                        (usuario, nombre, generate_password_hash(clave), rol, db.ahora()))
        flash('Usuario creado.', 'ok')
        return redirect(url_for('usuarios'))

    @app.post('/usuarios/<int:uid>/clave')
    @requiere_admin
    def usuario_clave(uid):
        clave = request.form.get('clave') or ''
        if not clave_valida(clave):
            flash('La clave tiene que tener %d o mas caracteres.' % CLAVE_MINIMA, 'error')
            return redirect(url_for('usuarios'))
        with db.conexion() as con:
            con.execute('UPDATE usuarios SET clave_hash = ? WHERE id = ?',
                        (generate_password_hash(clave), uid))
        flash('Clave actualizada.', 'ok')
        return redirect(url_for('usuarios'))

    @app.post('/usuarios/<int:uid>/rol')
    @requiere_admin
    def usuario_rol(uid):
        rol = marcar_valor(request.form.get('rol')) or ''
        if rol not in ('admin', 'vendedor', 'repositor'):
            flash('Rol invalido.', 'error')
            return redirect(url_for('usuarios'))
        if uid == g.usuario['id']:
            flash('No te podes cambiar tu propio rol: pedile a otro administrador.', 'error')
            return redirect(url_for('usuarios'))
        with db.conexion() as con:
            u = db.fila(con, 'SELECT * FROM usuarios WHERE id = ?', (uid,))
            if not u:
                abort(404)
            if u['rol'] == 'admin' and rol != 'admin':
                admins = db.valor(
                    con, "SELECT COUNT(*) FROM usuarios WHERE rol = 'admin' AND activo = 1") or 0
                if admins <= 1:
                    flash('Tiene que quedar al menos un administrador activo.', 'error')
                    return redirect(url_for('usuarios'))
            con.execute('UPDATE usuarios SET rol = ? WHERE id = ?', (rol, uid))
        flash('Rol de %s cambiado a %s. Se aplica en el acto.' % (u['usuario'], rol), 'ok')
        return redirect(url_for('usuarios'))

    @app.post('/usuarios/<int:uid>/alternar')
    @requiere_admin
    def usuario_alternar(uid):
        if uid == g.usuario['id']:
            flash('No te podes desactivar a vos mismo.', 'error')
            return redirect(url_for('usuarios'))
        with db.conexion() as con:
            con.execute('UPDATE usuarios SET activo = 1 - activo WHERE id = ?', (uid,))
        flash('Usuario actualizado.', 'ok')
        return redirect(url_for('usuarios'))


    @app.post('/usuarios/<int:uid>/eliminar')
    @requiere_admin
    def usuario_eliminar(uid):
        if uid == g.usuario['id']:
            flash('No te podes eliminar a vos mismo.', 'error')
            return redirect(url_for('usuarios'))
        with db.conexion() as con:
            u = db.fila(con, 'SELECT * FROM usuarios WHERE id = ?', (uid,))
            if not u:
                abort(404)
            usos = []
            for tabla, columna in (('ventas', 'usuario_id'), ('movimientos', 'usuario_id'),
                                   ('arqueos', 'usuario_id'), ('reposiciones', 'usuario_id'),
                                   ('ferias', 'creada_por')):
                if db.valor(con, 'SELECT COUNT(*) FROM %s WHERE %s = ?' % (tabla, columna), (uid,)):
                    usos.append(tabla)
            if usos:
                flash('No se puede eliminar: tiene %s. Desactivalo en vez de borrarlo.'
                      % ', '.join(usos), 'error')
                return redirect(url_for('usuarios'))
            con.execute('DELETE FROM usuarios WHERE id = ?', (uid,))
        flash('Usuario eliminado.', 'ok')
        return redirect(url_for('usuarios'))


def crear_app():
    app = Flask(__name__)
    secreto = os.environ.get('FERIAS_SECRETO')
    if not secreto:
        ruta = os.path.join(BASE, 'secreto.key')
        if os.path.exists(ruta):
            with open(ruta, encoding='utf-8') as f:
                secreto = f.read().strip()
        else:
            secreto = secrets.token_hex(32)
            with open(ruta, 'w', encoding='utf-8') as f:
                f.write(secreto)
    app.secret_key = secreto
    app.permanent_session_lifetime = timedelta(days=7)
    app.config.update(
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE='Lax',
        SESSION_COOKIE_SECURE=(os.environ.get('FERIAS_SECURE') == '1'),
        MAX_CONTENT_LENGTH=2 * 1024 * 1024,
        JSON_AS_ASCII=False,
    )
    db.inicializar()
    registrar_rutas(app)

    @app.context_processor
    def contexto_reservas():
        """Numeros al lado de las pestanas: reservas activas y ventas sin cobrar."""
        n = 0
        pend = 0
        try:
            fid = (request.view_args or {}).get('fid')
            if fid and g.get('usuario'):
                with db.conexion() as con:
                    n = db.valor(con, "SELECT COUNT(*) FROM reservas WHERE feria_id = ? "
                                      "AND estado = 'activa'", (fid,)) or 0
                    pend = db.valor(con, "SELECT COUNT(*) FROM ventas WHERE feria_id = ? "
                                         "AND estado = 'pendiente'", (fid,)) or 0
        except Exception:
            n = 0
            pend = 0
        return {'n_reservas': n, 'n_pendientes': pend}

    app.wsgi_app = PrefijoProxy(app.wsgi_app, PREFIJO)
    # actualizacion automatica de precios en segundo plano (se apaga en las pruebas)
    if os.environ.get('FERIAS_PRECIOS_HILO', '1') != '0':
        threading.Thread(target=hilo_precios, daemon=True).start()
    return app


app = crear_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=PUERTO, debug=False)
