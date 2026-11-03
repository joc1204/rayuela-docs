"""Genera la guia de uso de la app Novedades (DOCX -> PDF).

    python construir_guia.py
"""
import os

from docx import Document
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

BASE = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(BASE)
QR = os.path.join(RAIZ, 'qr', 'qr-novedades.png')
SALIDA = os.path.join(BASE, 'Guia-Novedades.docx')

VERDE = RGBColor(0x1F, 0x4D, 0x3D)
GRIS = RGBColor(0x4C, 0x59, 0x64)
VERDE_CLARO = 'E3F3E9'
NARANJA = 'FDEBD3'

ANCHO = Cm(17.0)          # util con margenes de 2 cm en A4


def color_fondo(celda, hex_color):
    tcPr = celda._tc.get_or_add_tcPr()
    sombra = OxmlElement('w:shd')
    sombra.set(qn('w:val'), 'clear')
    sombra.set(qn('w:color'), 'auto')
    sombra.set(qn('w:fill'), hex_color)
    tcPr.append(sombra)


def margenes_celda(celda, arriba=60, abajo=60, izq=100, der=100):
    tcPr = celda._tc.get_or_add_tcPr()
    mar = OxmlElement('w:tcMar')
    for nombre, valor in (('top', arriba), ('bottom', abajo),
                          ('left', izq), ('right', der)):
        nodo = OxmlElement('w:%s' % nombre)
        nodo.set(qn('w:w'), str(valor))
        nodo.set(qn('w:type'), 'dxa')
        mar.append(nodo)
    tcPr.append(mar)


def numeracion_pagina(seccion):
    pie = seccion.footer.paragraphs[0]
    pie.alignment = WD_ALIGN_PARAGRAPH.CENTER

    corrida = pie.add_run()
    inicio = OxmlElement('w:fldChar')
    inicio.set(qn('w:fldCharType'), 'begin')
    instruccion = OxmlElement('w:instrText')
    instruccion.set(qn('xml:space'), 'preserve')
    instruccion.text = ' PAGE '
    separador = OxmlElement('w:fldChar')
    separador.set(qn('w:fldCharType'), 'separate')
    valor = OxmlElement('w:t')
    valor.text = '1'
    fin = OxmlElement('w:fldChar')
    fin.set(qn('w:fldCharType'), 'end')
    for nodo in (inicio, instruccion, separador, valor, fin):
        corrida._r.append(nodo)

    pie.add_run('  ·  Novedades · Rayuela')
    for r in pie.runs:
        r.font.size = Pt(8)
        r.font.color.rgb = RGBColor(0x9A, 0xA5, 0xAE)


def configurar(doc):
    seccion = doc.sections[0]
    seccion.page_width = Cm(21.0)
    seccion.page_height = Cm(29.7)
    seccion.top_margin = Cm(2.0)
    seccion.bottom_margin = Cm(1.8)
    seccion.left_margin = Cm(2.0)
    seccion.right_margin = Cm(2.0)
    seccion.different_first_page_header_footer = True
    numeracion_pagina(seccion)

    normal = doc.styles['Normal']
    normal.font.name = 'Calibri'
    normal.font.size = Pt(10.5)
    normal.font.color.rgb = RGBColor(0x16, 0x20, 0x2A)
    normal.paragraph_format.space_after = Pt(6)
    normal.paragraph_format.line_spacing = 1.12

    for nivel, tam in ((1, 17), (2, 12.5)):
        estilo = doc.styles['Heading %d' % nivel]
        estilo.font.name = 'Calibri'
        estilo.font.size = Pt(tam)
        estilo.font.bold = True
        estilo.font.color.rgb = VERDE if nivel == 1 else RGBColor(0x2F, 0x5D, 0x4C)
        estilo.paragraph_format.space_before = Pt(16 if nivel == 1 else 12)
        estilo.paragraph_format.space_after = Pt(6)
        estilo.paragraph_format.keep_with_next = True


def titulo_pagina(doc, texto, subtitulo=None):
    p = doc.add_paragraph(style='Heading 1')
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(texto)
    r.font.size = Pt(19)
    r.font.bold = True
    r.font.color.rgb = VERDE
    borde = OxmlElement('w:pBdr')
    linea = OxmlElement('w:bottom')
    linea.set(qn('w:val'), 'single')
    linea.set(qn('w:sz'), '10')
    linea.set(qn('w:space'), '4')
    linea.set(qn('w:color'), '1F4D3D')
    borde.append(linea)
    p._p.get_or_add_pPr().append(borde)
    if subtitulo:
        s = doc.add_paragraph()
        s.paragraph_format.space_after = Pt(12)
        rs = s.add_run(subtitulo)
        rs.font.size = Pt(10)
        rs.font.color.rgb = GRIS


def parrafo(doc, texto, tam=10.5, espacio=6):
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(espacio)
    p.add_run(texto).font.size = Pt(tam)
    return p


def vinetas(doc, items, tam=10.5):
    for item in items:
        p = doc.add_paragraph(style='List Bullet')
        p.paragraph_format.space_after = Pt(3)
        if isinstance(item, tuple):
            r = p.add_run(item[0])
            r.bold = True
            r.font.size = Pt(tam)
            p.add_run(' ' + item[1]).font.size = Pt(tam)
        else:
            p.add_run(item).font.size = Pt(tam)


def lista_numerada(doc, items, tam=10.5):
    for item in items:
        p = doc.add_paragraph(style='List Number')
        p.paragraph_format.space_after = Pt(3)
        p.add_run(item).font.size = Pt(tam)


def tabla(doc, encabezados, filas, anchos, tam=9.5):
    t = doc.add_table(rows=1, cols=len(encabezados))
    t.style = 'Table Grid'
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False

    trPr = t.rows[0]._tr.get_or_add_trPr()
    repetir = OxmlElement('w:tblHeader')
    repetir.set(qn('w:val'), 'true')
    trPr.append(repetir)

    for i, texto in enumerate(encabezados):
        celda = t.rows[0].cells[i]
        celda.width = anchos[i]
        color_fondo(celda, '1F4D3D')
        margenes_celda(celda)
        p = celda.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        r = p.add_run(texto)
        r.bold = True
        r.font.size = Pt(tam)
        r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
    for numero, fila in enumerate(filas):
        fila_tabla = t.add_row()
        no_partir = OxmlElement('w:cantSplit')
        fila_tabla._tr.get_or_add_trPr().append(no_partir)
        celdas = fila_tabla.cells
        for i, valor in enumerate(fila):
            celdas[i].width = anchos[i]
            margenes_celda(celdas[i])
            if numero % 2 == 1:
                color_fondo(celdas[i], 'F4F7F9')
            p = celdas[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(0)
            r = p.add_run(str(valor))
            r.font.size = Pt(tam)
            if i == 0:
                r.bold = True
    return t


def caja(doc, titulo, texto, fondo=VERDE_CLARO):
    t = doc.add_table(rows=1, cols=1)
    t.autofit = False
    celda = t.rows[0].cells[0]
    celda.width = ANCHO
    color_fondo(celda, fondo)
    margenes_celda(celda, arriba=120, abajo=120, izq=160, der=160)
    p = celda.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    r = p.add_run(titulo + ' ')
    r.bold = True
    r.font.size = Pt(10.5)
    p.add_run(texto).font.size = Pt(10.5)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


# --------------------------------------------------------------------- paginas
def portada(doc):
    for _ in range(3):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Novedades')
    r.font.size = Pt(40)
    r.bold = True
    r.font.color.rgb = VERDE

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Guía de uso y significado de cada columna')
    r.font.size = Pt(15)
    r.font.color.rgb = GRIS

    doc.add_paragraph()
    if os.path.exists(QR):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(QR, width=Cm(6.4))

    for _ in range(5):
        doc.add_paragraph()
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run('Rayuela Libros  ·  versión 1.0  ·  octubre 2026')
    r.font.size = Pt(10)
    r.font.color.rgb = GRIS
    doc.add_page_break()


def que_hace(doc):
    titulo_pagina(doc, '1 · Qué hace')
    parrafo(doc, 'Novedades toma una lista de ISBN y busca cada libro en las páginas web de '
                 'tres librerías: SBS, Yenny (El Ateneo) y Zivals.')
    parrafo(doc, 'De cada libro devuelve el título, el autor, la editorial, el tema, el año de '
                 'edición, la encuadernación, el idioma, el precio de tapa, la sinopsis y la '
                 'tapa, todo junto en una planilla.')

    doc.add_paragraph()
    doc.add_paragraph('El circuito completo', style='Heading 2')
    lista_numerada(doc, [
        'Se escanean los ISBN con el celular (o se escriben a mano).',
        'Se elige a qué casilla de correo mandarlo.',
        'La app consulta las tres librerías, libro por libro.',
        'Llega un mail con la planilla y las tapas.',
    ])
    doc.add_paragraph()
    caja(doc, 'Tiempo típico:',
         'menos de un minuto para cinco libros, alrededor de dos minutos para cuarenta.',
         fondo=NARANJA)
    caja(doc, 'Si un libro no aparece:',
         'puede ser que ninguna de las tres librerías lo tenga. La fila queda marcada como '
         '"no está" y el libro se carga a mano.')


def antes_de_empezar(doc):
    titulo_pagina(doc, '2 · Antes de empezar')
    tabla(doc, ['Qué', 'Detalle'], [
        ['Un celular con internet', 'Datos móviles o wifi. La cámara tiene que poder abrirse.'],
        ['El PIN', 'Es una clave corta que se pide una sola vez por sesión.'],
        ['Una casilla de destino', 'La casilla a la que se quiere que llegue el resultado.'],
    ], [Cm(4.6), Cm(12.4)])
    doc.add_paragraph()
    parrafo(doc, 'No hace falta instalar nada: la app se abre desde el navegador del celular, '
                 'como una página más.', tam=10)
    doc.add_paragraph()
    caja(doc, 'Si el celular es compartido:',
         'tocá "Salir" al terminar. El nombre y la casilla se borran al cerrar la pestaña, pero '
         'si la dejás abierta quedan a la vista del que la use después.', fondo=NARANJA)


def como_entrar(doc):
    titulo_pagina(doc, '3 · Cómo entrar')
    pasos = [
        ('Abrí la app', 'Con la cámara del celular, escaneá el código de la portada de esta guía.'),
        ('Poné el PIN', 'Se pide una sola vez por sesión. Acepta letras y números.'),
        ('Escribí tu nombre', 'Va en el asunto del mail, así se sabe quién lo mandó. '
                              'Ejemplo: "Verónica".'),
    ]
    for i, (titulo, texto) in enumerate(pasos, start=1):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        r = p.add_run('Paso %d · %s' % (i, titulo))
        r.bold = True
        r.font.size = Pt(11)
        r.font.color.rgb = VERDE
        parrafo(doc, texto, espacio=2)
    doc.add_paragraph()
    caja(doc, 'Si no tenés el PIN:', 'pedíselo a Verónica.')
    caja(doc, 'El botón "Salir"',
         'está arriba a la derecha. Cierra la sesión y borra el nombre y la casilla que hayas '
         'escrito. Usalo siempre en un celular compartido.')


def cargar_isbn(doc):
    titulo_pagina(doc, '4 · Cargar los ISBN', 'Escanear o escribir a mano')
    doc.add_paragraph('Con la cámara', style='Heading 2')
    vinetas(doc, [
        ('Tocá "Cargar ISBN".', 'Se abre la cámara en la parte de arriba de la pantalla.'),
        ('Apuntá al código de barras.', 'No hace falta apretar nada más: lee solo.'),
        ('Escaneá uno tras otro.', 'Cada lectura agrega el libro a la lista de abajo.'),
        ('Mirá el cartel verde "✔ Leído".', 'Aparece encima de la cámara con el ISBN y el '
         'celular vibra. Es la confirmación de que tomó el código.'),
        ('Terminá con "⏹ Terminar de escanear".', 'La cámara se cierra y queda la lista.'),
    ])
    doc.add_paragraph()
    doc.add_paragraph('Con el teclado', style='Heading 2')
    parrafo(doc, 'Si el código está roto, tapado o la cámara no abre, escribí los trece números '
                 'en el campo "o escribí el ISBN" y tocá "Agregar". Funciona igual.')
    doc.add_paragraph()
    doc.add_paragraph('La lista', style='Heading 2')
    vinetas(doc, [
        ('Contador', 'arriba de la lista dice cuántos ISBN hay cargados.'),
        ('✕', 'borra un ISBN mal escaneado antes de enviar.'),
        ('Repetidos', 'si el mismo libro se escanea dos veces, se busca una sola vez.'),
        ('Códigos inválidos', 'si un código no es un ISBN válido, no se envía: la app avisa '
         'cuántos quedaron afuera y sigue con los buenos.'),
    ])


def enviar(doc):
    titulo_pagina(doc, '5 · Enviar y recibir')
    doc.add_paragraph('Elegir la casilla', style='Heading 2')
    parrafo(doc, 'En el campo "Enviar a" se escribe la casilla de destino.')
    parrafo(doc, 'Si las casillas ya están guardadas, aparecen como botones debajo del campo: '
                 'un toque y queda puesta. Si alguien quiere mandarlo a una casilla personal, la '
                 'escribe a mano y no usa los botones: no queda guardada.')
    doc.add_paragraph()
    doc.add_paragraph('Administrar casillas', style='Heading 2')
    vinetas(doc, [
        ('Dónde está', 'abajo del botón "Enviar", en el apartado "Administrar casillas".'),
        ('Agregar', 'nombre (ej. Administración) y la casilla. Con eso aparece como botón para '
         'todos.'),
        ('Borrar', 'con la ✕ al lado de cada una.'),
        ('Quién puede', 'cualquiera que haya entrado con el PIN.'),
    ])
    doc.add_paragraph()
    doc.add_paragraph('El envío', style='Heading 2')
    vinetas(doc, [
        ('Tocá "Enviar".', 'La pantalla dice "Enviado: N ISBN. Te llega el mail en un minuto".'),
        ('Seguí el progreso.', '"Buscando los libros: 2 de 5…" avanza a medida que termina.'),
        ('Al terminar', 'dice "Listo: mail enviado a <casilla>".'),
        ('Si falla', 'dice el motivo. Se puede volver a enviar: los libros ya buscados quedan en '
         'memoria por 24 horas y la segunda vez es instantánea.'),
        ('Descarga directa', 'mientras el mail viaja, se pueden bajar la planilla y el ZIP desde '
         'la misma pantalla.'),
    ])


def que_llega(doc):
    titulo_pagina(doc, '6 · Qué te llega por mail')
    parrafo(doc, 'Un mail con dos adjuntos:')
    tabla(doc, ['Adjunto', 'Qué contiene'], [
        ['novedades.xlsx', 'La planilla, una fila por libro, con la tapa de cada uno incrustada '
                           'en la fila. Se abre con Excel.'],
        ['tapas.zip', 'Las tapas sueltas, con el nombre del ISBN.'],
    ], [Cm(4.6), Cm(12.4)])
    doc.add_paragraph()
    parrafo(doc, 'También viene un resumen en el cuerpo del mail: cuántos se encontraron, cuántos '
                 'no, y la lista de los que hay que buscar a mano.')
    doc.add_paragraph()
    caja(doc, 'Si el mail no llega:',
         'mirá en Spam y fijate que la casilla de destino esté bien escrita. Si sigue sin '
         'aparecer, avisale a Verónica.', fondo=NARANJA)
    caja(doc, 'Las tapas:',
         'se achican a 600 píxeles y se guardan en JPG, para que pesen poco y se vean bien.')


def columnas(doc):
    titulo_pagina(doc, '7 · Qué significa cada columna',
                  'Las 24 columnas de la planilla, una por una')

    doc.add_paragraph('Identificación y control', style='Heading 2')
    tabla(doc, ['Columna', 'Qué es y qué hacer'], [
        ['isbn', 'El código de 13 números del libro.'],
        ['estado', 'Cómo terminó la búsqueda de ese ISBN: ok, no_esta, error_red o roto. Si dice '
                   'ok, los datos están completos. Ver la sección 8.'],
        ['sitios_ok', 'Qué librerías lo encontraron (ej. "yenny, sbs"). Sirve para saber de '
                      'dónde salieron los datos.'],
        ['sitios_rotos', 'Librerías que respondieron con una página que la app no pudo leer: '
                         'habría que avisar para revisar esa librería.'],
        ['sitios_error', 'Librerías que no respondieron por un problema de red. Suele '
                         'arreglarse solo al reenviar.'],
        ['revisar_autor', 'Dice "SI" cuando las librerías informan autores que no comparten '
                          'ninguna palabra: hay que mirar el autor a mano. Si está vacío, los '
                          'tres coinciden (aunque esté escrito distinto).'],
        ['precio_difiere', 'Dice "SI" cuando las librerías informan precios distintos. Por la '
                           'ley de precio único no debería pasar: si aparece, conviene '
                           'confirmarlo.'],
    ], [Cm(3.6), Cm(13.4)])

    doc.add_paragraph('Datos del libro', style='Heading 2')
    tabla(doc, ['Columna', 'Qué es y qué hacer'], [
        ['titulo', 'El título del libro, como lo publica la librería.'],
        ['autor', 'El autor o autores. Si en "revisar_autor" dice SI, este campo puede estar mal: '
                  'contrastalo con la contratapa.'],
        ['editorial', 'La editorial.'],
        ['tema', 'El rubro o categoría. Cada librería lo clasifica a su manera: es el dato que '
                 'más varía entre una y otra.'],
        ['anio', 'El año de edición (a veces viene como mes/año: 06/2019).'],
        ['encuadernacion', 'Tapa blanda, tapa dura, cartoné… Siempre traducido al castellano.'],
        ['idioma', 'El idioma de la edición (normalmente "Español").'],
        ['precio', 'El precio de tapa que informa la librería.'],
        ['sinopsis', 'El texto de contratapa. Se toma la versión más completa de las tres '
                     'librerías.'],
    ], [Cm(3.6), Cm(13.4)])

    doc.add_paragraph('Tapas', style='Heading 2')
    tabla(doc, ['Columna', 'Qué es y qué hacer'], [
        ['tapa_url', 'El link a la imagen original en la librería. No hace falta abrirlo: la '
                     'tapa ya viene incrustada en la planilla.'],
        ['tapa_archivo', 'El nombre del archivo de la tapa dentro del ZIP (ej. '
                         '9789871374991.jpg), para encontrarla rápido.'],
    ], [Cm(3.6), Cm(13.4)])

    doc.add_paragraph('De dónde salió cada dato', style='Heading 2')
    parrafo(doc, 'Las columnas que terminan en _origen dicen qué librería aportó ese dato. No se '
                 'usan todos los días, pero sirven para entender una diferencia entre librerías:')
    tabla(doc, ['Columna', 'Qué indica'], [
        ['titulo_origen', 'de dónde salió el título (normalmente Yenny)'],
        ['autor_origen', 'de dónde salió el autor (normalmente Zivals)'],
        ['editorial_origen', 'de dónde salió la editorial (normalmente SBS)'],
        ['tema_origen', 'de dónde salió el rubro (normalmente Zivals)'],
        ['precio_origen', 'de dónde salió el precio (normalmente SBS)'],
        ['sinopsis_origen', 'de dónde salió la sinopsis más completa'],
    ], [Cm(4.2), Cm(12.8)])


def estados(doc):
    titulo_pagina(doc, '8 · Los estados', 'Qué significa cada estado de la columna estado')
    tabla(doc, ['Estado', 'Qué significa', 'Qué hacer'], [
        ['ok', 'Se encontró el libro y los datos están completos.', ''],
        ['no_esta', 'Ninguna de las tres librerías lo tiene.', ''],
        ['error_red', 'Una librería no respondió cuando se consultó.', ''],
        ['roto', 'La librería respondió, pero la app no pudo leer la página: cambió el sitio.',
         'Avisarle a Verónica con el ISBN para que lo revisen.'],
    ], [Cm(2.6), Cm(8.0), Cm(6.4)])


def problemas(doc):
    titulo_pagina(doc, '9 · Problemas frecuentes')
    tabla(doc, ['Situación', 'Qué hacer'], [
        ['El mail no llega', 'Mirar Spam. Verificar que la casilla de destino esté bien escrita.'],
        ['La cámara no abre', 'Darle permiso de cámara al navegador. Si sigue, cargar los ISBN a '
                              'mano con el teclado.'],
        ['No lee un código', 'Acercar o alejar el celular, buscar luz, limpiar la contratapa. Si '
                             'el código está dañado, escribirlo a mano.'],
        ['Dice "no_esta" pero el libro existe', 'Puede ser un libro que ninguna de las tres '
                                                'librerías tiene.'],
        ['"Sigue en cola" y no avanza', 'Puede haber otro envío procesándose. Esperar un minuto '
                                        'y mirar la pantalla de nuevo.'],
        ['Aparece el nombre de otra persona', 'Tocar "Salir" y volver a entrar. El nombre y la '
                                              'casilla se borran al salir.'],
        ['Un ISBN no entra en la lista', 'No es un ISBN válido (13 números con dígito '
                                         'verificador). Revisar el código.'],
        ['La app no abre o da error', 'Avisarle a Verónica con la hora y lo que decía la '
                                      'pantalla.'],
    ], [Cm(4.6), Cm(12.4)])


def main():
    doc = Document()
    configurar(doc)
    portada(doc)
    que_hace(doc)
    antes_de_empezar(doc)
    como_entrar(doc)
    cargar_isbn(doc)
    enviar(doc)
    que_llega(doc)
    columnas(doc)
    estados(doc)
    problemas(doc)
    doc.save(SALIDA)
    print('  guardado: %s (%d KB)' % (SALIDA, os.path.getsize(SALIDA) // 1024))


if __name__ == '__main__':
    main()
