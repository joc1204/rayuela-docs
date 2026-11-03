"""Arma el manual de uso de Rayuela Ferias en Word.

Uso:
    python construir_manual.py
"""
import os

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE)
LOGO = os.path.join(RAIZ, 'ferias_app', 'static', 'icono-ferias-1024.png')
QR = os.path.join(RAIZ, 'qr', 'qr-ferias.png')
QR_MANUAL = os.path.join(RAIZ, 'qr', 'qr-manual.png')
SALIDA = os.path.join(BASE, 'Manual-Rayuela-Ferias.docx')

NARANJA = RGBColor(0xC2, 0x41, 0x0C)
GRIS = RGBColor(0x44, 0x4C, 0x55)
GRIS_CLARO = RGBColor(0x77, 0x7F, 0x88)
TITULO = RGBColor(0x1F, 0x25, 0x2B)

ENLACE = 'https://net-casa.tailfb7a36.ts.net/ferias/'
ENLACE_MANUAL = 'https://net-casa.tailfb7a36.ts.net/ferias/manual'


# ------------------------------------------------------------------ ayudas
def fuente_corrida(corrida, tamano=None, color=None, negrita=None):
    if tamano:
        corrida.font.size = Pt(tamano)
    if color is not None:
        corrida.font.color.rgb = color
    if negrita is not None:
        corrida.font.bold = negrita


def parrafo(doc, texto='', estilo=None, tamano=None, color=None, negrita=None,
            espacio_despues=6, alineacion=None):
    p = doc.add_paragraph(style=estilo)
    if texto:
        c = p.add_run(texto)
        fuente_corrida(c, tamano, color, negrita)
    p.paragraph_format.space_after = Pt(espacio_despues)
    if alineacion is not None:
        p.alignment = alineacion
    return p


def titulo_seccion(doc, numero, texto):
    p = doc.add_paragraph()
    c = p.add_run('%s. ' % numero)
    fuente_corrida(c, 17, NARANJA, True)
    c2 = p.add_run(texto)
    fuente_corrida(c2, 17, TITULO, True)
    p.paragraph_format.space_before = Pt(16)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    return p


def subtitulo(doc, texto):
    p = doc.add_paragraph()
    c = p.add_run(texto)
    fuente_corrida(c, 12.5, TITULO, True)
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    return p


def vinetas(doc, items):
    for item in items:
        p = doc.add_paragraph(style='List Bullet')
        if isinstance(item, tuple):
            c = p.add_run(item[0])
            fuente_corrida(c, 11, TITULO, True)
            c2 = p.add_run(item[1])
            fuente_corrida(c2, 11, GRIS)
        else:
            c = p.add_run(item)
            fuente_corrida(c, 11, GRIS)
        p.paragraph_format.space_after = Pt(3)


def tabla(doc, encabezados, filas, anchos=None):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = 'Table Grid'
    t.autofit = False
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, texto in enumerate(encabezados):
        celda = t.rows[0].cells[i]
        celda.text = ''
        p = celda.paragraphs[0]
        c = p.add_run(texto)
        fuente_corrida(c, 10, RGBColor(0xFF, 0xFF, 0xFF), True)
        sombrear(celda, 'C2410C')
    for fila in filas:
        celdas = t.add_row().cells
        for i, valor in enumerate(fila):
            celdas[i].text = ''
            p = celdas[i].paragraphs[0]
            c = p.add_run(str(valor))
            fuente_corrida(c, 10, GRIS)
    if anchos:
        for i, ancho in enumerate(anchos):
            t.columns[i].width = Cm(ancho)
            for fila in t.rows:
                fila.cells[i].width = Cm(ancho)
    # que el encabezado se repita si la tabla sigue en la pagina siguiente
    trPr = t.rows[0]._tr.get_or_add_trPr()
    hdr = OxmlElement('w:tblHeader')
    hdr.set(qn('w:val'), 'true')
    trPr.append(hdr)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


def sombrear(celda, hex_color):
    tcPr = celda._tc.get_or_add_tcPr()
    shd = OxmlElement('w:shd')
    shd.set(qn('w:val'), 'clear')
    shd.set(qn('w:fill'), hex_color)
    tcPr.append(shd)


def numero_de_pagina(pie):
    p = pie.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Rayuela Ferias  ·  Manual de uso  ·  pagina ')
    fuente_corrida(c, 8.5, GRIS_CLARO)
    run = p.add_run()
    fuente_corrida(run, 8.5, GRIS_CLARO)
    iniciar = OxmlElement('w:fldChar')
    iniciar.set(qn('w:fldCharType'), 'begin')
    instruccion = OxmlElement('w:instrText')
    instruccion.set(qn('xml:space'), 'preserve')
    instruccion.text = 'PAGE'
    cerrar = OxmlElement('w:fldChar')
    cerrar.set(qn('w:fldCharType'), 'end')
    run._r.append(iniciar)
    run._r.append(instruccion)
    run._r.append(cerrar)


# ------------------------------------------------------------------ documento
def main():
    doc = Document()
    seccion = doc.sections[0]
    seccion.page_width = Cm(21)
    seccion.page_height = Cm(29.7)
    seccion.top_margin = Cm(2.2)
    seccion.bottom_margin = Cm(2.0)
    seccion.left_margin = Cm(2.3)
    seccion.right_margin = Cm(2.3)

    normal = doc.styles['Normal']
    normal.font.name = 'Segoe UI'
    normal.font.size = Pt(11)
    normal.font.color.rgb = GRIS
    normal.paragraph_format.line_spacing = 1.15
    numero_de_pagina(seccion.footer)

    # ------------------------------------------------------------ portada
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_before = Pt(10)
    p.add_run().add_picture(LOGO, width=Cm(5.2))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Rayuela Ferias')
    fuente_corrida(c, 34, TITULO, True)
    p.paragraph_format.space_after = Pt(2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Manual de uso')
    fuente_corrida(c, 17, NARANJA, True)
    p.paragraph_format.space_after = Pt(2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Para vender y controlar el stock en ferias')
    fuente_corrida(c, 11.5, GRIS_CLARO)
    p.paragraph_format.space_after = Pt(18)

    # separador
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('_' * 46)
    fuente_corrida(c, 9, RGBColor(0xE2, 0xD5, 0xC3))
    p.paragraph_format.space_after = Pt(18)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(2)
    p.add_run().add_picture(QR, width=Cm(6.4))

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Escaneá este código para abrir la app')
    fuente_corrida(c, 11, TITULO, True)
    p.paragraph_format.space_after = Pt(2)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run(ENLACE)
    fuente_corrida(c, 9.5, NARANJA)
    p.paragraph_format.space_after = Pt(24)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Versión 3.0  ·  Octubre 2026')
    fuente_corrida(c, 9, GRIS_CLARO)

    doc.add_page_break()

    # ------------------------------------------------------------ 1
    titulo_seccion(doc, 1, 'Qué es')
    parrafo(doc, 'Rayuela Ferias es una aplicación web para usar desde el celular durante las '
                 'ferias de libros. Sirve para vender más rápido, no perder ventas y saber '
                 'exactamente qué se llevó, qué se vendió y qué volvió.')
    vinetas(doc, [
        ('Escanear y saber. ', 'Con la cámara del celular se lee el código de barras y aparece '
                               'el título, el autor y el precio.'),
        ('Armar la venta. ', 'Se cargan varios títulos, se ajustan cantidades y se aplican '
                             'descuentos por libro o sobre el total.'),
        ('Cobrar. ', 'Efectivo, transferencia, QR o tarjeta: cada forma de pago se contabiliza '
                     'por separado.'),
        ('Controlar. ', 'Stock, caja y cierre, con un registro de quién hizo cada cosa.'),
    ])
    parrafo(doc, 'Se usa desde el navegador. No hay que instalar nada: se abre el link y, si se '
                 'quiere, se agrega a la pantalla de inicio para que quede como una app más del '
                 'teléfono.')

    # ------------------------------------------------------------ 2
    titulo_seccion(doc, 2, 'Antes de la feria')
    subtitulo(doc, 'Usuarios y roles')
    parrafo(doc, 'Cada persona entra con su propio usuario y contraseña. El rol define qué puede '
                 'hacer. Se administran desde Usuarios (solo el administrador).')
    tabla(doc, ['Rol', 'Puede', 'No puede'], [
        ['Administrador', 'Todo: crear ferias, cargar y reponer stock, vender, abrir y cerrar, '
                          'anular ventas, reservar, actualizar precios, usuarios y movimientos',
         '—'],
        ['Vendedor', 'Vender, reservar, cargar y reponer stock, ver stock, caja, ventas y cierre',
         'Anular ventas, cerrar la feria, borrar libros, administrar usuarios'],
        ['Repositor', 'Ingresar y reponer stock, ver stock, caja, ventas y cierre',
         'Vender, reservar, anular ventas, cerrar la feria'],
    ], anchos=[3.0, 8.2, 5.0])

    parrafo(doc, 'Al dar de alta cada usuario se completan tres datos: usuario es con lo que entra '
                 'al sistema (corto, sin espacios; por ejemplo "veronica"); nombre es como va a '
                 'figurar en los registros (por ejemplo "Verónica Gómez", un apodo o lo que se '
                 'quiera) y clave es la contraseña. El usuario no se puede repetir; el nombre sí.')
    vinetas(doc, [
        ('Un usuario por persona. ', 'Si comparten la clave, el registro dice el nombre de quien '
                                     'sea y deja de servir para saber quién hizo qué.'),
        ('Desactivar no es eliminar. ', 'Al que deja el trabajo se lo desactiva: no puede entrar, '
                                        'pero queda su historial. Eliminar solo se puede si nunca '
                                        'hizo nada.'),
        ('La clave se puede cambiar. ', 'El administrador puede cambiársela a cualquiera, sin verla.'),
        ('La sesión dura 7 días. ', 'El celular queda adentro; si es un equipo compartido, conviene '
                                    'tocar Salir.'),
        ('El rol se puede cambiar después. ', 'No hace falta borrar el usuario y crearlo de nuevo: '
                                              'desde Usuarios, el administrador le cambia el rol y '
                                              'rige en el acto, sin que la persona tenga que salir y '
                                              'volver a entrar.'),
        ('Los roles que se tocan a sí mismos están protegidos. ', 'Nadie puede cambiarse su propio '
                                                                  'rol ni desactivarse, y no se '
                                                                  'puede dejar a la app sin ningún '
                                                                  'administrador.'),
    ])

    subtitulo(doc, 'Crear la feria')
    parrafo(doc, 'En la pantalla principal, desplegar "Dar de alta una feria" y completar el '
                 'nombre, el lugar, las fechas y la caja inicial (la plata con la que se arranca). '
                 'La feria queda en estado preparación.')
    subtitulo(doc, 'Ingresar el stock')
    parrafo(doc, 'En la pestaña Stock hay que buscar el libro: se escanea el código con la cámara o '
                 'se escribe parte del título, del autor o los números del código. Mientras se '
                 'escribe, la app muestra los títulos que coinciden; se toca el que corresponde y '
                 'aparece el precio con la cantidad en 1.')
    vinetas(doc, [
        ('Los botones + y − ', 'ajustan cuántos ejemplares se ingresan. El número del medio también '
                               'se puede escribir.'),
        ('Ingresar ', 'suma esos ejemplares a la feria y los deja en la lista de abajo.'),
        ('Descartar ', 'cierra el panel sin ingresar nada.'),
        ('La ✕ (solo administrador) ', 'saca el libro de la feria. No se puede si ya tiene ventas: '
                                       'en ese caso se ajustan las cantidades.'),
    ])
    parrafo(doc, 'Si el mismo libro se escanea dos veces, suma un ejemplar más: no duplica la fila.')
    parrafo(doc, 'La lista de abajo muestra, por título: cuántos se llevaron, cuántos se repusieron, '
                 'cuántos se vendieron y cuántos quedan disponibles. Los precios no se cargan a mano: '
                 'vienen del sistema y se mantienen actualizados (ver "Precios actualizados").')
    parrafo(doc, 'Si el disponible de un título aparece en negativo (por ejemplo −1), no es un error '
                 'de cuentas: significa que hay más ejemplares comprometidos que cargados. Pasa '
                 'cuando se reservaron o se vendieron más copias de las que se ingresaron. Se corrige '
                 'ingresando los ejemplares que falten o cancelando la reserva que se pasó de '
                 'cantidad.')
    subtitulo(doc, 'Copiar el link del mapa')
    parrafo(doc, 'En la tarjeta de la feria (pestaña Stock) está el botón "Copiar link del mapa": '
                 'toma la ubicación del celular y copia un link de Google Maps. Aparece un cartel '
                 'grande con el link copiado, listo para pegar en WhatsApp, Instagram o en una '
                 'publicación. Si el teléfono no deja copiar, el cartel muestra el link para '
                 'escribirlo a mano.')
    subtitulo(doc, 'Abrir la feria')
    parrafo(doc, 'El botón "Abrir la feria" la deja lista para vender. Se puede abrir aunque '
                 'todavía no haya libros cargados: el stock puede llegar después.')

    # ------------------------------------------------------------ 3
    titulo_seccion(doc, 3, 'En la feria: vender')
    parrafo(doc, 'Desde la pantalla principal, tocar Vender en la feria abierta.')
    subtitulo(doc, 'Escanear y confirmar')
    vinetas(doc, [
        'Tocar Escanear y apuntar al código: la cámara se cierra sola al leerlo.',
        'Aparece el libro con su precio y la cantidad en 1.',
        'Tocar "Agregar a la venta", o Descartar si no era ese.',
        'Si el código no está en la feria, avisa y deja agregarlo igual: queda marcado como '
        '"sin cargar" para revisarlo en el cierre.',
        'Si el libro tiene reservas, el panel lo avisa ("Este libro tiene 2 reservados, a nombre '
        'de..."). Se puede vender igual: la app solo avisa, la decisión la toma quien vende.',
    ])
    subtitulo(doc, 'Armar la venta')
    parrafo(doc, 'En "En esta venta" cada título se puede sumar con +, restar con -, o sacar con '
                 'la x. El campo de descuento al lado de cada libro descuenta sobre ese título.')
    subtitulo(doc, 'El pie de la venta: qué hace cada cosa')
    parrafo(doc, 'Abajo de todo está siempre a la vista el resumen: Subtotal, Descuentos por título, '
                 'el campo del descuento sobre el total, y el TOTAL. El descuento se aplica mientras '
                 'se escribe. Debajo hay tres botones:')
    tabla(doc, ['Botón', 'Qué hace'], [
        ['Forma de pago ▾', 'Abre la lista de formas de pago. La elegida queda escrita en el botón. '
                            'No viene ninguna elegida: hay que elegirla en cada venta, para que '
                            'ninguna quede con un dato equivocado.'],
        ['Cliente', 'Abre los datos del cliente: nombre, teléfono, mail, DNI y CUIT. Son opcionales; '
                    'solo hacen falta si pide factura (ahí el nombre y un contacto pasan a ser '
                    'obligatorios). En una transferencia, nombre y teléfono son obligatorios.'],
        ['Cobrar', 'Registra la venta. Si no se eligió forma de pago, avisa "Elegí la forma de pago '
                   'antes de cobrar", abre la lista y no cobra.'],
    ], anchos=[3.6, 12.6])
    subtitulo(doc, 'Cobrar')
    parrafo(doc, 'El botón Cobrar registra la venta y muestra el número asignado. Con ese número '
                 'se encuentra la venta en la pestaña Ventas. La venta queda registrada al instante.')
    parrafo(doc, 'El número se lee así: F01-C2-0007 es la feria 1, el celular 2 y la venta número 7.')
    parrafo(doc, 'Antes de confirmar, la app verifica los precios vigentes. Si alguno cambió desde '
                 'que se armó la venta, avisa y no cobra: se puede poner un descuento por libro para '
                 'respetar el precio que se le dijo al cliente y tocar Cobrar de nuevo.')
    parrafo(doc, 'Dos celulares pueden vender el mismo libro. La app no lo bloquea: lo marca como '
                 'sobreventa para revisarlo en el cierre.')
    subtitulo(doc, 'Cobrar por transferencia: la venta queda pendiente de pago')
    parrafo(doc, 'Cuando la forma de pago elegida es una de tipo transferencia, la venta no se '
                 'cobra en el momento: queda como PENDIENTE DE PAGO. El libro ya queda descontado '
                 'del stock, pero la plata no cuenta en la caja hasta que se confirma.')
    vinetas(doc, [
        ('La app pide nombre y teléfono. ', 'Si no están cargados, los pide antes de cobrar: sin '
                                            'contacto no se puede saber a quién reclamarle.'),
        ('Al tocar Cobrar aparece el mensaje para el comprador, ', 'con el detalle de los libros, '
                                                                   'el total, la referencia y los datos '
                                                                   'de la cuenta.'),
        ('Los botones son: ', 'Copiar texto, WhatsApp, Mostrar al cliente, Ver pendientes y Seguir '
                              'vendiendo.'),
        ('El vendedor sigue atendiendo, ', 'no se queda esperando la transferencia.'),
    ])
    parrafo(doc, 'El mensaje pide el comprobante y aclara que la factura se envía luego por mail. '
                 'La referencia (por ejemplo "Ref. A7K3F2") es la que el comprador puede escribir '
                 'en la transferencia, para cruzar el pago con la venta.')
    subtitulo(doc, 'Si se corta la conexión o se refresca la pantalla')
    parrafo(doc, 'La venta en curso se guarda en el propio teléfono. Si la pantalla se refresca o '
                 'la app se cierra sin querer, al volver aparece la venta como estaba, con un aviso '
                 'y la hora en que se guardó. Pasados 20 minutos sin actividad se descarta sola, '
                 'para que no quede una venta vieja dando vueltas.')

    # ------------------------------------------------------------ 4
    titulo_seccion(doc, 4, 'Reservas: apartar libros para alguien')
    parrafo(doc, 'Se usa cuando alguien elige un libro y lo va a buscar o lo va a pagar más tarde '
                 '(por ejemplo, en una feria en una escuela: el chico elige y después viene el padre '
                 'a pagar). El libro queda apartado, deja de ofrecerse como disponible, y queda '
                 'anotado el contacto de quien lo reservó.')
    subtitulo(doc, 'La pestaña Reservas y el número al lado')
    parrafo(doc, 'En la barra de pestañas aparece "Reservas" y, entre paréntesis, cuántas reservas '
                 'activas hay: si dice (3), hay tres reservas sin resolver. Así se ve de un vistazo '
                 'que hay libros apartados, sin tener que entrar al listado. El número cuenta '
                 'reservas, no libros.')
    subtitulo(doc, 'Crear una reserva, paso a paso')
    vinetas(doc, [
        ('1. Buscar el libro. ', 'En "Código o título" se escanea el código o se escribe parte del '
                                 'título o del autor. Mientras se escribe, la app muestra los '
                                 'títulos que coinciden; se toca el que corresponde.'),
        ('2. Ajustar la cantidad. ', 'Cada libro agregado tiene + y −. La ✕ lo saca de la reserva.'),
        ('3. Nombre. ', 'Obligatorio: es la persona a cuyo nombre queda el libro.'),
        ('4. Teléfono. ', 'Obligatorio: es el contacto para avisarle.'),
        ('5. Nota. ', 'Opcional. Sirve para cualquier aclaración: quién lo retira, para qué fecha, '
                      'etc.'),
        ('6. Reservar. ', 'Guarda la reserva y descuenta los ejemplares de los disponibles.'),
    ])
    parrafo(doc, 'Si faltan el nombre, el teléfono o los libros, la app no guarda y avisa qué falta.')
    subtitulo(doc, 'Qué pasa con el stock')
    parrafo(doc, 'Los ejemplares reservados dejan de estar disponibles: el cálculo de la pestaña '
                 'Stock los descuenta. No se mueven de donde están; solo quedan comprometidos. Si la '
                 'reserva se cancela, vuelven a estar disponibles.')
    subtitulo(doc, 'Vender un libro que tiene reservas')
    parrafo(doc, 'La app avisa en el panel ("Este libro tiene 2 reservados, a nombre de Ana") pero '
                 'deja vender igual. Es a propósito: puede ser que la reserva sea para mañana y '
                 'convenga venderlo y pedir reposición. La decisión la toma quien vende.')
    subtitulo(doc, 'Entregar una reserva')
    parrafo(doc, 'El botón Entregar lleva a la pantalla de venta con los libros de la reserva ya '
                 'cargados. Ahí se elige forma de pago, descuentos y datos del cliente igual que en '
                 'cualquier venta. Al cobrar, la venta queda registrada y la reserva pasa a '
                 'entregada. Si se descarta la venta, la reserva sigue activa.')
    subtitulo(doc, 'Cancelar una reserva')
    parrafo(doc, 'El botón Cancelar pide confirmación y devuelve los ejemplares a los disponibles. '
                 'Queda registrado quién la canceló y cuándo.')
    subtitulo(doc, 'Reservas y cierre de la feria')
    parrafo(doc, 'Con reservas activas la feria no se puede cerrar: la app avisa y lleva a la '
                 'pestaña Reservas para que primero se entreguen o se cancelen. Es para que no queden '
                 'libros apartados de una feria que ya terminó.')
    parrafo(doc, 'Las reservas entregadas y canceladas quedan en un bloque plegable, con su fecha y '
                 'quién las hizo.')
    subtitulo(doc, 'Quién puede usar reservas')
    parrafo(doc, 'El administrador y el vendedor. El repositor no: su tarea es cargar y reponer '
                 'stock.')

    # ------------------------------------------------------------ 5
    titulo_seccion(doc, 5, 'Pagos pendientes: confirmar o anular')
    parrafo(doc, 'Las ventas cobradas por transferencia quedan aparte hasta que se confirma que la '
                 'plata llegó. Viven en la pestaña Pendientes, con la cantidad entre paréntesis: '
                 'Pendientes (2) son dos ventas esperando.')
    subtitulo(doc, 'Qué muestra cada venta pendiente')
    vinetas(doc, [
        ('La referencia y la fecha. ', 'Es la que el comprador puede escribir en la transferencia, '
                                       'para cruzarla con el comprobante.'),
        ('El cliente y su teléfono. ', 'Para avisarle si hace falta.'),
        ('Los libros y el total. ', 'Lo mismo que se le pasó en el mensaje.'),
    ])
    subtitulo(doc, 'Confirmar el pago')
    parrafo(doc, 'Cuando llega el comprobante se toca "Confirmar pago": la venta pasa a confirmada, '
                 'cuenta en la caja y queda registrada en Movimientos. Si venía de una reserva, la '
                 'reserva queda entregada.')
    subtitulo(doc, 'Anular una venta pendiente')
    parrafo(doc, 'Si la transferencia no llegó o el comprador se arrepiente, se toca "Anular": los '
                 'libros vuelven al stock y, si venía de una reserva, la reserva sigue activa. '
                 'Puede hacerlo el vendedor. Una venta ya confirmada, en cambio, solo la anula el '
                 'administrador.')
    subtitulo(doc, 'Cómo se ve en la caja y en el cierre')
    parrafo(doc, 'En Caja aparece un renglón aparte: "N ventas pendientes de pago: $X", aclarando '
                 'que no se cuentan hasta confirmar. Ese dinero no se suma al efectivo ni a los '
                 'totales por forma de pago.')
    parrafo(doc, 'Con ventas pendientes la feria no se puede cerrar: la app avisa y lleva a la '
                 'pestaña para que primero se confirmen o se anulen, igual que con las reservas.')
    subtitulo(doc, 'Configurar una cuenta para transferencias (administrador)')
    parrafo(doc, 'En Administración → Formas de pago se agrega una forma de tipo "Transferencia" y '
                 'se completan en el momento el banco, el titular, el CUIT y el CBU o CVU. Sin esos '
                 'datos no se puede crear, y al cobrar la app no deja usar una transferencia sin '
                 'cuenta.')
    parrafo(doc, 'Cada forma de pago se edita con el botón Editar (el formulario está plegado para '
                 'no llenar la pantalla), se puede activar o desactivar, y se puede eliminar si '
                 'ninguna venta la usó. Las inactivas se ven con la etiqueta roja INACTIVA y borde '
                 'punteado, y no aparecen al cobrar.')

    # ------------------------------------------------------------ 6
    titulo_seccion(doc, 6, 'Control y reposición')
    subtitulo(doc, 'Caja')
    parrafo(doc, 'Muestra los totales por forma de pago, el efectivo que debería haber en la caja '
                 '(incluyendo la caja inicial) y las ventas anuladas. El administrador puede '
                 'registrar un arqueo: escribe lo que contó y el sistema calcula la diferencia. '
                 'No cierra la feria, así que en una feria de varios días se puede controlar cada '
                 'noche.')
    subtitulo(doc, 'Reponer stock')
    parrafo(doc, 'Con la feria abierta, en la pestaña Stock se ingresan más ejemplares. Queda '
                 'registrado como reposición, con quién y cuándo.')
    subtitulo(doc, 'Precios actualizados')
    parrafo(doc, 'El administrador decide cada cuántas horas la app trae los precios vigentes del '
                 'sistema (1, 2, 3, 6 horas…) y desde qué hora empieza el ciclo. Además se '
                 'actualizan al abrir la feria, y hay un botón para forzarlo en el momento.')
    parrafo(doc, 'Cada cambio queda registrado con la hora, el precio anterior y el nuevo. Cuando '
                 'hay alguno, en Vender y en Stock aparece un aviso del tipo "Cambiaron 3 precios" '
                 'con el detalle de cada uno.')
    subtitulo(doc, 'Movimientos')
    parrafo(doc, 'En la pestaña Cierre, el administrador puede desplegar "Movimientos: quién cambió '
                 'qué". Ahí figura cada ingreso de stock, cambio de cantidad o precio, anulación de '
                 'venta, apertura y cierre, con el usuario y la hora.')

    # ------------------------------------------------------------ 7
    titulo_seccion(doc, 7, 'Cierre y reportes')
    parrafo(doc, 'Al volver de la feria, en la pestaña Cierre se revisa el conteo: por cada título '
                 'figura lo que se llevó, lo que se repuso, lo que se vendió y lo que vuelve. Si '
                 'falta algún ejemplar, se anota en "perdidos" y el sistema recalcula los devueltos.')
    parrafo(doc, 'El botón "Cerrar feria" deja la feria cerrada: ya no admite ventas ni cambios, '
                 'pero queda todo el historial.')
    parrafo(doc, 'No se puede quitar un libro que ya tiene ventas: en ese caso se ajustan las '
                 'cantidades. Si un libro se vendió sin haber estado cargado, el cierre lo marca '
                 'como "vendido sin cargar"; y si se vendió más que lo cargado, como "vendido de más".')
    subtitulo(doc, 'Los archivos para descargar')
    tabla(doc, ['Archivo', 'Qué trae', 'Para qué sirve'], [
        ['Llevados', 'Una fila por título: precio, llevados, repuestos, vendidos, perdidos, '
                     'devueltos', 'Reconciliar el stock contra lo que volvió'],
        ['Vendidos', 'Una fila por libro vendido: venta, fecha, cliente, forma de pago, título, '
                     'cantidad, precio, descuento, total', 'Facturar en el sistema y enviar los '
                                                            'mails o el marketing'],
        ['Resumen', 'Totales por forma de pago y totales de ejemplares', 'Cerrar el balance de la '
                                                                         'feria'],
    ], anchos=[2.6, 8.0, 5.6])

    # ------------------------------------------------------------ 8
    titulo_seccion(doc, 8, 'Guía rápida: cada botón, para qué sirve')
    parrafo(doc, 'Para no tener dudas, acá está todo lo que se puede tocar, en el orden en que '
                 'aparece en pantalla.')
    tabla(doc, ['Dónde', 'Botón', 'Qué hace'], [
        ['Arriba', '◀ Volver', 'Vuelve a la lista de ferias (en la lista principal no aparece).'],
        ['Lista de ferias', 'Salir de la app', 'Cierra la sesión de este celular.'],
        ['Lista de ferias', 'Dar de alta una feria', 'Crea una feria (solo administrador).'],
        ['Lista de ferias', 'Vender', 'Abre la pantalla de venta de esa feria.'],
        ['Lista de ferias', 'Preparar la feria', 'Abre el Stock de una feria en preparación.'],
        ['Lista de ferias', 'Ver la feria', 'Abre una feria cerrada, para consultarla.'],
        ['Administración', 'Usuarios', 'Crear usuarios, cambiar el rol, cambiar claves.'],
        ['Administración', 'Formas de pago', 'Agregar, editar, activar o eliminar medios de cobro.'],
        ['Administración', 'Actualización de precios', 'Frecuencia de precios y actualizar ahora.'],
        ['Pestañas (‹ ›)', 'Vender', 'Escáner y venta (administrador y vendedor).'],
        ['Pestañas (‹ ›)', 'Stock', 'Cargar y reponer ejemplares.'],
        ['Pestañas (‹ ›)', 'Reservas (N)', 'Libros apartados; el número son las reservas activas.'],
        ['Pestañas (‹ ›)', 'Pendientes (N)', 'Ventas esperando el pago; el número son las que faltan.'],
        ['Pestañas (‹ ›)', 'Caja', 'Totales por forma de pago, efectivo esperado y arqueo.'],
        ['Pestañas (‹ ›)', 'Ventas', 'Listado de ventas y anulaciones.'],
        ['Pestañas (‹ ›)', 'Cierre', 'Conteo final, perdidos, movimientos y archivos.'],
        ['Stock', 'Escanear', 'Abre la cámara para leer el código.'],
        ['Stock', 'Ingresar', 'Suma los ejemplares con la cantidad elegida.'],
        ['Stock', 'Descartar', 'Cierra el panel sin ingresar nada.'],
        ['Stock', 'Copiar link del mapa', 'Copia un link de Google Maps con la ubicación.'],
        ['Stock', 'Abrir la feria', 'La deja lista para vender (administrador).'],
        ['Vender', 'Escanear', 'Abre la cámara para leer el código.'],
        ['Vender', 'Agregar a la venta', 'Suma el libro leído a la venta.'],
        ['Vender', 'Descartar', 'Cierra el panel del libro leído sin agregarlo.'],
        ['Vender', 'Forma de pago ▾', 'Elige cómo se cobra. No viene elegida.'],
        ['Vender', 'Cliente', 'Abre los datos del cliente (opcionales).'],
        ['Vender', 'Cobrar', 'Registra la venta (o la deja pendiente, si es transferencia).'],
        ['Transferencia', 'Copiar texto', 'Copia el mensaje para pegarlo donde quieras.'],
        ['Transferencia', 'WhatsApp', 'Abre WhatsApp con el mensaje y el número del comprador.'],
        ['Transferencia', 'Mostrar al cliente', 'Muestra el mensaje en grande, para que lo lea.'],
        ['Transferencia', 'Ver pendientes', 'Va a la lista de ventas esperando el pago.'],
        ['Transferencia', 'Seguir vendiendo', 'Vuelve a vender, con el carrito vacío.'],
        ['Pendientes', 'Confirmar pago', 'El pago llegó: cuenta en la caja.'],
        ['Pendientes', 'Anular', 'El pago no llegó: los libros vuelven al stock.'],
        ['Reservas', 'Agregar', 'Busca un libro y lo suma a la reserva.'],
        ['Reservas', 'Reservar', 'Guarda la reserva.'],
        ['Reservas', 'Entregar', 'Lleva los libros a la pantalla de venta.'],
        ['Reservas', 'Cancelar', 'Devuelve los libros a los disponibles.'],
        ['Formas de pago', 'Editar', 'Abre el formulario de esa forma de pago.'],
        ['Formas de pago', 'Activar / Desactivar', 'La muestra u oculta al cobrar.'],
        ['Formas de pago', 'Eliminar', 'La borra, solo si ninguna venta la usó.'],
        ['Cierre', 'Cerrar feria', 'Cierra la feria (administrador).'],
        ['Cierre', 'Reabrir feria', 'Vuelve a abrir una feria cerrada (administrador).'],
    ], anchos=[3.2, 4.8, 8.2])

    # ------------------------------------------------------------ 9
    titulo_seccion(doc, 9, 'Por qué es confiable')
    vinetas(doc, [
        ('Los datos quedan en un servidor propio de Rayuela. ',
         'No se alojan en servicios de terceros.'),
        ('Toda la conexión va con candado. ',
         'La dirección empieza con https, igual que un homebanking.'),
        ('Cada uno ve solo lo suyo. ',
         'Cada usuario entra con su clave y su rol limita lo que puede hacer.'),
        ('Todo cambio queda registrado. ',
         'Quién, cuándo y qué se tocó. Un descuadre no se puede tapar sin dejar rastro.'),
        ('La venta en curso vive en el teléfono. ',
         'Si se corta la señal o se refresca la pantalla, no se pierde lo que se estaba cobrando.'),
        ('Las ventas no se duplican. ',
         'Si el teléfono no recibe la confirmación y se reintenta, el servidor reconoce la '
         'operación y no la registra dos veces.'),
        ('Hay protecciones en las cosas delicadas. ',
         'No se puede borrar un libro que ya tiene ventas, un usuario que hizo movimientos, ni una '
         'feria abierta.'),
    ])

    # ------------------------------------------------------------ 10
    titulo_seccion(doc, 10, 'Preguntas frecuentes')
    preguntas = [
        ('No lee el código, ¿qué hago?',
         'Acercar un poco más el teléfono y evitar el reflejo. Si el código está impreso en blanco '
         'sobre un fondo de color, conviene escribir los 13 números a mano: la app los acepta.'),
        ('¿Puedo vender un libro que no está cargado?',
         'Sí. La app avisa y deja agregarlo igual. Queda marcado como "sin cargar" y se ve en el '
         'cierre.'),
        ('Se cortó la señal en medio de una venta, ¿la perdí?',
         'No. La venta queda guardada en el teléfono y se recupera al volver. Si al cobrar la '
         'confirmación no llegó, reintentar no duplica la venta.'),
        ('¿Puedo cobrar dos veces el mismo libro?',
         'Se puede, pero la app lo marca como sobreventa para que se revise en el cierre. Nunca '
         'bloquea una venta.'),
        ('¿Cómo confirmo que la caja está bien?',
         'En Caja, el administrador registra un arqueo con lo que contó. El sistema muestra la '
         'diferencia y la guarda.'),
        ('¿Qué pasa si alguien borra un libro por error?',
         'No se puede borrar si ya tiene ventas. Si no tiene, se vuelve a escanear y queda '
         'registrado el cambio en Movimientos.'),
        ('¿Dónde veo quién vendió qué?',
         'En Ventas aparece cada operación con su número, y en Cierre el registro de movimientos '
         'muestra quién hizo cada cambio.'),
        ('¿Puedo cambiar mi clave?',
         'Sí, o se la pedís al administrador (que puede cambiarla sin verla). La sesión dura 7 días; '
         'en un celular compartido conviene usar Salir.'),
        ('¿Se puede reabrir una feria cerrada?',
         'Sí, solo el administrador, y queda registrado en Movimientos.'),
        ('¿Para qué sirve reservar?',
         'Para apartar libros de alguien que los va a buscar o pagar después. El libro deja de estar '
         'disponible, se anota el nombre y el teléfono, y en la pestaña Reservas aparece cuántas hay '
         'sin resolver.'),
        ('¿Puedo vender un libro que alguien reservó?',
         'Sí. La app avisa cuántos hay reservados y a nombre de quién, pero no lo impide: a veces '
         'conviene vender y pedir reposición.'),
        ('¿Un libro quedó con el disponible en negativo, qué hago?',
         'Significa que hay más comprometido que cargado. Ingresá los ejemplares que faltan o '
         'cancelá la reserva que se pasó de cantidad. El cierre también lo marca como "vendido de '
         'más".'),
        ('¿Puedo reservar un libro que no está cargado en la feria?',
         'No. La reserva se hace sobre libros que ya están en la feria. Primero se cargan en Stock y '
         'después se reservan.'),
        ('¿Un repositor puede vender o reservar?',
         'No. Carga y repone stock, y consulta caja, ventas y cierre.'),
        ('¿Cómo sé si un precio cambió?',
         'La app verifica los precios antes de cobrar y, si alguno cambió, avisa y no cobra. Además '
         'aparece un cartel ("Cambiaron 3 precios") en Vender y en Stock.'),
        ('¿Qué es una venta pendiente de pago?',
         'Es una venta cobrada por transferencia: los libros ya quedaron descontados del stock, pero '
         'la plata no cuenta en la caja hasta confirmar que llegó. Aparece en la pestaña Pendientes.'),
        ('¿Qué hago cuando llega el comprobante?',
         'Pendientes → Confirmar pago. La venta pasa a confirmada y cuenta en la caja.'),
        ('¿Y si la transferencia nunca llega?',
         'Pendientes → Anular. Los libros vuelven al stock y, si venía de una reserva, la reserva '
         'sigue activa.'),
        ('¿Puedo cerrar la feria con ventas pendientes?',
         'No: igual que con las reservas, primero hay que confirmarlas o anularlas.'),
        ('El mensaje de la transferencia, ¿lo manda la app sola?',
         'No. La app arma el mensaje y abre WhatsApp con el número del comprador: el último toque '
         'para enviarlo lo da el vendedor.'),
        ('¿Por qué la forma de pago no viene elegida?',
         'Para que ninguna venta quede con un medio equivocado. Si se toca Cobrar sin elegir, la app '
         'avisa y no cobra.'),
    ]
    for pregunta, respuesta in preguntas:
        p = doc.add_paragraph()
        c = p.add_run(pregunta)
        fuente_corrida(c, 11, TITULO, True)
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(1)
        parrafo(doc, respuesta, espacio_despues=2)

    # ------------------------------------------------------------ cierre
    parrafo(doc, '')
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run().add_picture(QR_MANUAL, width=Cm(3.4))
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Este manual, siempre actualizado')
    fuente_corrida(c, 10.5, TITULO, True)
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run(ENLACE_MANUAL)
    fuente_corrida(c, 9, GRIS_CLARO)
    parrafo(doc, '')
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c = p.add_run('Ante cualquier duda, consultar con el administrador de Rayuela.')
    fuente_corrida(c, 9.5, GRIS_CLARO)

    doc.save(SALIDA)
    print('  guardado: %s (%d bytes)' % (os.path.basename(SALIDA), os.path.getsize(SALIDA)))


if __name__ == '__main__':
    main()
