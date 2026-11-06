"""Agrega la pestana Reportes a la app de ferias. Se aplica sobre rayuela-docs/infra/ferias-app.py."""
import ast
import io
import os

raiz = r'C:\Users\Jorge\Documents\deepseek-harness\default-workspace'
ruta = os.path.join(raiz, 'rayuela-docs', 'infra', 'ferias-app.py')
t = io.open(ruta, encoding='utf-8').read()

# ---------------------------------------------------------------- import zipfile
if 'import zipfile' not in t:
    t = t.replace('import uuid\n', 'import uuid\nimport zipfile\n', 1)
    print('  OK  import zipfile')

# ---------------------------------------------------------------- helpers
HELPERS = '''
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
    ventas = db.filas(con, \'\'\'
        SELECT v.*, u.nombre AS vendedor, c.nombre AS cliente, c.telefono AS telefono
          FROM ventas v LEFT JOIN usuarios u ON u.id = v.usuario_id
          LEFT JOIN clientes c ON c.id = v.cliente_id
         WHERE v.feria_id = ? ORDER BY v.id\'\'\', (fid,))
    items = db.filas(con, \'\'\'
        SELECT vi.*, l.titulo, l.isbn, v.numero, v.estado AS venta_estado
          FROM venta_items vi JOIN ventas v ON v.id = vi.venta_id
          JOIN libros l ON l.id = vi.libro_id
         WHERE v.feria_id = ? ORDER BY v.id, vi.id\'\'\', (fid,))
    stock = db.filas(con, \'\'\'
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
         WHERE fl.feria_id = ? ORDER BY l.titulo\'\'\', (fid,))
    arqueos = db.filas(con, \'\'\'
        SELECT a.*, u.nombre AS usuario FROM arqueos a
          LEFT JOIN usuarios u ON u.id = a.usuario_id
         WHERE a.feria_id = ? ORDER BY a.id\'\'\', (fid,))
    reservas = db.filas(con, \'\'\'
        SELECT r.*, COALESCE(SUM(ri.cantidad), 0) AS ejemplares
          FROM reservas r LEFT JOIN reserva_items ri ON ri.reserva_id = r.id
         WHERE r.feria_id = ? GROUP BY r.id ORDER BY r.id\'\'\', (fid,))
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
    return ('\\ufeff' + buffer.getvalue()).encode('utf-8')


def _resumen_para_compartir(con, fid):
    feria, ventas, items, stock, arqueos, reservas = _datos_cierre(con, fid)
    confirmadas = [v for v in ventas if v['estado'] == 'confirmada']
    total = sum(float(v['total'] or 0) for v in confirmadas)
    efectivo = sum(float(v['total'] or 0) for v in confirmadas if v['forma_pago'] == 'efectivo')
    caja = float(feria['caja_inicial'] or 0)
    return ('Cierre %s\\nVentas: %d por $%.2f\\nEfectivo esperado en caja: $%.2f\\n'
            'Sobreventas: %d' % (feria['nombre'], len(confirmadas), total,
                                  caja + efectivo,
                                  sum(1 for v in confirmadas if v['sobreventa'])))


'''

marca = 'def registrar_rutas(app):'
if marca in t and 'REPORTES_FERIA = [' not in t:
    t = t.replace(marca, HELPERS + marca, 1)
    print('  OK  helpers de reportes')

# ---------------------------------------------------------------- rutas
RUTAS = '''    # ---- reportes
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
            texto = _resumen_para_compartir(con, fid)
        datos_compartir = [{'clave': c['clave'],
                            'archivo': 'feria-%d-%s.csv' % (fid, c['clave']),
                            'url': url_for('feria_reporte_csv', fid=fid, nombre=c['clave'])}
                           for c in listado]
        return render_template('reportes.html', feria=feria, reportes=listado,
                               texto_compartir=texto, datos_compartir=datos_compartir,
                               tab='reportes')

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

'''

marca_rutas = '    # ---- cierre'
if marca_rutas in t and 'def feria_reportes(fid):' not in t:
    t = t.replace(marca_rutas, RUTAS + marca_rutas, 1)
    print('  OK  rutas de reportes')

io.open(ruta, 'w', encoding='utf-8', newline='\n').write(t)
ast.parse(t)
print('  sintaxis OK')
