"""Reportes de cierre de una feria. Solo lectura: no modifica nada.

Uso:
    python3 reportes_feria.py --feria 1 --salida /tmp/reportes-feria
    python3 reportes_feria.py --feria 1 --salida /tmp/reportes-feria --base /opt/rayuela/ferias/ferias.db

Genera CSV separados por punto y coma (se abren en Excel directamente).
"""
import argparse
import csv
import os
import sqlite3
from datetime import datetime


def conectar(base):
    return sqlite3.connect('file:%s?mode=ro' % base, uri=True)


def centavos(valor):
    return round(float(valor or 0), 2)


def escribir(salida, nombre, encabezados, filas):
    ruta = os.path.join(salida, nombre)
    with open(ruta, 'w', encoding='utf-8-sig', newline='') as archivo:
        escritor = csv.writer(archivo, delimiter=';')
        escritor.writerow(encabezados)
        escritor.writerows(filas)
    print('  %-32s %4d filas' % (nombre, len(filas)))


def main():
    analizador = argparse.ArgumentParser()
    analizador.add_argument('--feria', type=int, required=True)
    analizador.add_argument('--salida', required=True)
    analizador.add_argument('--base', default='/opt/rayuela/ferias/ferias.db')
    args = analizador.parse_args()

    os.makedirs(args.salida, exist_ok=True)
    con = conectar(args.base)
    con.row_factory = sqlite3.Row
    fid = args.feria

    feria = con.execute('SELECT * FROM ferias WHERE id = ?', (fid,)).fetchone()
    if not feria:
        raise SystemExit('No existe la feria %s' % fid)

    ventas = con.execute('''
        SELECT v.*, u.nombre AS vendedor, c.nombre AS cliente, c.telefono AS telefono,
               c.email AS email
          FROM ventas v
          LEFT JOIN usuarios u ON u.id = v.usuario_id
          LEFT JOIN clientes c ON c.id = v.cliente_id
         WHERE v.feria_id = ? ORDER BY v.id''', (fid,)).fetchall()

    items = con.execute('''
        SELECT vi.*, l.titulo, l.isbn, v.numero, v.estado AS venta_estado, v.forma_pago
          FROM venta_items vi
          JOIN ventas v ON v.id = vi.venta_id
          JOIN libros l ON l.id = vi.libro_id
         WHERE v.feria_id = ? ORDER BY v.id, vi.id''', (fid,)).fetchall()

    stock = con.execute('''
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
         WHERE fl.feria_id = ? ORDER BY l.titulo''', (fid,)).fetchall()

    arqueos = con.execute('''
        SELECT a.*, u.nombre AS usuario FROM arqueos a
          LEFT JOIN usuarios u ON u.id = a.usuario_id
         WHERE a.feria_id = ? ORDER BY a.id''', (fid,)).fetchall()

    reservas = con.execute("""
        SELECT r.*, COUNT(ri.id) AS libros, COALESCE(SUM(ri.cantidad), 0) AS ejemplares
          FROM reservas r LEFT JOIN reserva_items ri ON ri.reserva_id = r.id
         WHERE r.feria_id = ? GROUP BY r.id ORDER BY r.id""", (fid,)).fetchall()

    confirmadas = [v for v in ventas if v['estado'] == 'confirmada']
    anuladas = [v for v in ventas if v['estado'] == 'anulada']
    pendientes = [v for v in ventas if v['estado'] == 'pendiente']
    total = sum(centavos(v['total']) for v in confirmadas)

    por_forma = {}
    for v in confirmadas:
        clave = v['forma_pago'] or '(sin forma)'
        datos = por_forma.setdefault(clave, {'operaciones': 0, 'total': 0.0})
        datos['operaciones'] += 1
        datos['total'] += centavos(v['total'])

    efectivo = por_forma.get('efectivo', {}).get('total', 0.0)
    caja_inicial = centavos(feria['caja_inicial'])
    libros_ok = [it for it in items if it['venta_estado'] == 'confirmada']

    # ------------------------------------------------------------------ 1. resumen
    filas = [
        ['Feria', feria['nombre']],
        ['Lugar', feria['lugar'] or ''],
        ['Organizador', feria['organizador'] or ''],
        ['Desde', feria['desde'] or ''],
        ['Hasta', feria['hasta'] or ''],
        ['Estado', feria['estado']],
        ['Generado', datetime.now().strftime('%d/%m/%Y %H:%M')],
        [],
        ['Caja inicial', caja_inicial],
        ['Efectivo cobrado', centavos(efectivo)],
        ['Efectivo esperado en caja', centavos(caja_inicial + efectivo)],
        [],
        ['Ventas confirmadas', len(confirmadas)],
        ['Ventas anuladas', len(anuladas)],
        ['Ventas pendientes de pago', len(pendientes)],
        ['Total cobrado', centavos(total)],
        ['Ticket promedio', centavos(total / len(confirmadas)) if confirmadas else 0],
        ['Ejemplares vendidos', sum(int(it['cantidad']) for it in libros_ok)],
        ['Titulos distintos vendidos', len({it['libro_id'] for it in libros_ok})],
        [],
        ['Ventas con sobreventa', sum(1 for v in confirmadas if v['sobreventa'])],
        ['Items vendidos sin cargar', sum(1 for it in libros_ok if it['sin_cargar'])],
        ['Reservas activas', sum(1 for r in reservas if r['estado'] == 'activa')],
        [],
        ['Forma de pago', 'Operaciones', 'Total'],
    ]
    for clave in sorted(por_forma, key=lambda k: -por_forma[k]['total']):
        filas.append([clave, por_forma[clave]['operaciones'], centavos(por_forma[clave]['total'])])
    escribir(args.salida, '01-resumen.csv', ['Concepto', 'Valor', ''], filas)

    # ------------------------------------------------------------------ 2. ventas
    escribir(args.salida, '02-ventas.csv',
             ['Ticket', 'Fecha', 'Hora', 'Vendedor', 'Forma de pago', 'Cliente',
              'Telefono', 'Total', 'Descuento', 'Estado', 'Sobreventa', 'Factura'],
             [[v['numero'], (v['cuando'] or '')[:10], (v['cuando'] or '')[11:19],
               v['vendedor'] or '', v['forma_pago'], v['cliente'] or '', v['telefono'] or '',
               centavos(v['total']), centavos(v['descuento']), v['estado'],
               'SI' if v['sobreventa'] else 'NO', 'SI' if v['pide_factura'] else 'NO']
              for v in ventas])

    # ------------------------------------------------------------------ 3. detalle
    escribir(args.salida, '03-ventas-detalle.csv',
             ['Ticket', 'ISBN', 'Titulo', 'Cantidad', 'Precio unitario', 'Descuento',
              'Subtotal', 'Estado venta', 'Vendido sin cargar'],
             [[it['numero'], it['isbn'], it['titulo'], it['cantidad'],
               centavos(it['precio']), centavos(it['descuento']),
               centavos(int(it['cantidad']) * centavos(it['precio']) - centavos(it['descuento'])),
               it['venta_estado'], 'SI' if it['sin_cargar'] else 'NO']
              for it in items])

    # ------------------------------------- 4. vendidos agregados (baja en Rayuela)
    agregado = {}
    for it in libros_ok:
        datos = agregado.setdefault((it['isbn'] or '', it['titulo']), {'cantidad': 0, 'total': 0.0})
        datos['cantidad'] += int(it['cantidad'])
        datos['total'] += int(it['cantidad']) * centavos(it['precio']) - centavos(it['descuento'])
    escribir(args.salida, '04-vendidos-para-rayuela.csv',
             ['ISBN', 'Titulo', 'Cantidad vendida', 'Importe'],
             [[isbn, titulo, datos['cantidad'], centavos(datos['total'])]
              for (isbn, titulo), datos in sorted(agregado.items(), key=lambda p: p[1]['cantidad'], reverse=True)])

    # ------------------------------------------------------------------ 5. stock final
    filas_stock = []
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
        filas_stock.append([s['isbn'], s['titulo'], s['autor'] or '', s['editorial'] or '',
                            centavos(s['precio']), s['llevados'], s['repuestos'],
                            s['vendidos'], s['reservado'], s['perdidos'], devueltos, situacion])
    escribir(args.salida, '05-stock-final.csv',
             ['ISBN', 'Titulo', 'Autor', 'Editorial', 'Precio', 'Llevados', 'Repuestos',
              'Vendidos', 'Reservados', 'Perdidos', 'Devueltos', 'Situacion'],
             filas_stock)

    # ------------------------------------------------------------------ 6. sobreventas
    tickets_por_libro = {}
    for it in libros_ok:
        if it['sin_cargar']:
            tickets_por_libro.setdefault(it['libro_id'], []).append(it['numero'])
    filas_sobre = []
    for s in stock:
        if not (s['sin_cargar_n'] or s['vendidos'] > s['llevados'] + s['repuestos']):
            continue
        cargados = s['llevados'] + s['repuestos']
        filas_sobre.append([s['isbn'], s['titulo'], cargados, s['vendidos'],
                            max(0, s['vendidos'] - cargados),
                            ', '.join(tickets_por_libro.get(s['libro_id'], [])) if 'libro_id' in s.keys() else ''])
    escribir(args.salida, '06-sobreventas.csv',
             ['ISBN', 'Titulo', 'Cargados', 'Vendidos', 'Faltante', 'Tickets'],
             filas_sobre)

    # ------------------------------------------------------------------ 7. reservas
    filas_reservas = []
    for r in reservas:
        filas_reservas.append([r['id'], r['nombre'], r['telefono'], r['nota'] or '',
                               r['estado'], r['ejemplares']])
    escribir(args.salida, '07-reservas.csv',
             ['Reserva', 'Nombre', 'Telefono', 'Nota', 'Estado', 'Ejemplares'],
             filas_reservas)

    # ------------------------------------------------------------------ 8. caja
    filas_caja = []
    for clave in sorted(por_forma, key=lambda k: -por_forma[k]['total']):
        filas_caja.append([clave + ' (cobrado)', por_forma[clave]['operaciones'],
                           centavos(por_forma[clave]['total']), '', '', ''])
    filas_caja.append(['caja inicial', '', caja_inicial, '', '', ''])
    filas_caja.append(['efectivo esperado en caja', '', centavos(caja_inicial + efectivo), '', '', ''])
    for a in arqueos:
        filas_caja.append(['arqueo ' + (a['forma_pago'] or ''),
                           '', centavos(a['esperado']), centavos(a['contado']),
                           centavos(a['diferencia']), a['usuario'] or ''])
    escribir(args.salida, '08-caja.csv',
             ['Detalle', 'Operaciones', 'Esperado', 'Contado', 'Diferencia', 'Usuario'],
             filas_caja)

    print('  listo: %s' % args.salida)


if __name__ == '__main__':
    main()
