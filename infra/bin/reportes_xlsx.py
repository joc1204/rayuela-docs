"""Arma el Excel de cierre a partir de los CSV del reporte. No toca ninguna base."""
import csv
import os

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

raiz = r'C:\Users\Jorge\Documents\deepseek-harness\default-workspace'
carpeta = os.path.join(raiz, 'reportes')
destino = os.path.join(carpeta, 'Cierre-Colegio-York-2026-11-06.xlsx')

HOJAS = [
    ('01-resumen.csv', 'Resumen'),
    ('02-ventas.csv', 'Ventas'),
    ('03-ventas-detalle.csv', 'Detalle por venta'),
    ('04-vendidos-para-rayuela.csv', 'Vendidos (Rayuela)'),
    ('05-stock-final.csv', 'Stock final'),
    ('06-sobreventas.csv', 'Sobreventas'),
    ('07-reservas.csv', 'Reservas'),
    ('08-caja.csv', 'Caja'),
]

COLUMNAS_DINERO = {'Valor', 'Total', 'Precio', 'Precio unitario', 'Descuento', 'Subtotal',
                   'Importe', 'Esperado', 'Contado', 'Diferencia'}
COLUMNAS_ANCHO_ESPECIAL = {'Titulo': 46, 'Autor': 24, 'Editorial': 20, 'Nota': 30,
                           'Concepto': 30, 'Detalle': 28}

encabezado_fondo = PatternFill('solid', fgColor='F0E4D0')
encabezado_fuente = Font(bold=True)


def leer(nombre):
    ruta = os.path.join(carpeta, nombre)
    with open(ruta, encoding='utf-8-sig', newline='') as archivo:
        return [fila for fila in csv.reader(archivo, delimiter=';')]


libro = Workbook()
libro.remove(libro.active)

# ---------------------------------------------------------------- hoja "cómo usar"
guia = libro.create_sheet('Cómo usar')
filas_guia = [
    ('Cierre de la feria Colegio York', ''),
    ('Generado', '06/11/2026'),
    ('', ''),
    ('Hoja', 'Para qué sirve'),
    ('Resumen', 'Los números del cierre: ventas, caja y controles.'),
    ('Ventas', 'Una fila por ticket, con vendedor y forma de pago.'),
    ('Detalle por venta', 'Qué libros lleva cada ticket.'),
    ('Vendidos (Rayuela)', 'Un ISBN por fila con la cantidad vendida: es la lista para dar de baja/reservar en Bridge.'),
    ('Stock final', 'Llevados, repuestos, vendidos, reservados, perdidos y devueltos por título.'),
    ('Sobreventas', 'Libros que se vendieron sin estar cargados (o de más): hay que corregir el stock.'),
    ('Reservas', 'Reservas cargadas y su estado.'),
    ('Caja', 'Totales por forma de pago, caja inicial, efectivo esperado y arqueos.'),
    ('', ''),
    ('Antes de dar de baja en Bridge', 'Revisar "Sobreventas" y "Stock final": lo que no cierre, corregirlo primero.'),
]
for fila in filas_guia:
    guia.append(fila)
guia['A1'].font = Font(bold=True, size=14)
guia['A4'].font = encabezado_fuente
guia['B4'].font = encabezado_fuente
for celda in ('A4', 'B4'):
    guia[celda].fill = encabezado_fondo
guia.column_dimensions['A'].width = 26
guia.column_dimensions['B'].width = 95
for fila in guia.iter_rows(min_row=5, max_row=guia.max_row, min_col=2, max_col=2):
    for celda in fila:
        celda.alignment = Alignment(wrap_text=True, vertical='top')

# ---------------------------------------------------------------- resto de hojas
for archivo, nombre_hoja in HOJAS:
    filas = leer(archivo)
    hoja = libro.create_sheet(nombre_hoja)
    for fila in filas:
        hoja.append([celda if celda != '' else None for celda in fila])
    if not filas:
        hoja.append(['(sin datos)'])

    encabezados = filas[0] if filas else []
    for columna, titulo in enumerate(encabezados, start=1):
        celda = hoja.cell(row=1, column=columna)
        celda.font = encabezado_fuente
        celda.fill = encabezado_fondo
        ancho = COLUMNAS_ANCHO_ESPECIAL.get(titulo, max(10, min(40, len(titulo) + 4)))
        hoja.column_dimensions[get_column_letter(columna)].width = ancho
        if titulo in COLUMNAS_DINERO:
            for fila in range(2, hoja.max_row + 1):
                hoja.cell(row=fila, column=columna).number_format = '#,##0.00'
    # convertir numeros: los importes y cantidades como numero (no como texto)
    NUMERICAS = COLUMNAS_DINERO | {'Operaciones', 'Cantidad', 'Llevados', 'Repuestos',
                                   'Vendidos', 'Reservados', 'Perdidos', 'Devueltos',
                                   'Cargados', 'Faltante', 'Ejemplares', 'Cantidad vendida'}
    for columna, titulo in enumerate(encabezados, start=1):
        for fila in range(2, hoja.max_row + 1):
            celda = hoja.cell(row=fila, column=columna)
            if not isinstance(celda.value, str):
                continue
            texto = celda.value.strip().replace(',', '.')
            try:
                numero = float(texto)
            except ValueError:
                continue
            if titulo == 'Valor' or titulo in NUMERICAS:
                celda.value = int(numero) if numero.is_integer() and titulo not in COLUMNAS_DINERO else numero

    hoja.freeze_panes = 'A2'
    if hoja.max_row > 1:
        hoja.auto_filter.ref = 'A1:%s%d' % (get_column_letter(len(encabezados)), hoja.max_row)

libro.save(destino)
print('  guardado:', destino, '·', round(os.path.getsize(destino) / 1024, 1), 'KB')
print('  hojas:', ', '.join(libro.sheetnames))
