"""Genera el HTML de una pantalla del panel con el CSS embebido, listo para capturar.

    CATALOGO_DB=/opt/rayuela/demo/catalogo.db DEMO_CLAVE=... \
    python3 vista_previa.py --ruta /admin/catalogo --salida /tmp/pantalla.html

Se usa junto con capturar_ui.py. No escribe nada en la base.
"""
import argparse
import io
import os
import re
import sys

BASE = os.environ.get('RAYUELA_BASE') or '/opt/rayuela/demo'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--ruta', default='/admin/catalogo')
    ap.add_argument('--salida', default='/tmp/pantalla.html')
    ap.add_argument('--css', default=None, help='CSS alternativo para probar sin publicar')
    ap.add_argument('--sin-barras', action='store_true',
                    help='oculta las barras de navegacion para ver solo el contenido')
    args = ap.parse_args()

    os.chdir(BASE)
    sys.path.insert(0, BASE)
    import app as A

    cliente = A.app.test_client()
    with cliente.session_transaction() as ses:
        ses['equipo'] = True
    respuesta = cliente.get(args.ruta)
    if respuesta.status_code != 200:
        sys.exit('la ruta devolvio HTTP %d' % respuesta.status_code)
    html = respuesta.get_data(as_text=True)

    ruta_css = args.css or os.path.join(BASE, 'static', 'estilo.css')
    css = io.open(ruta_css, encoding='utf-8').read()
    html = re.sub(r'<link[^>]+estilo\.css[^>]*>', '<style>' + css + '</style>', html)
    html = re.sub(r'<link[^>]+favicon[^>]*>', '', html)
    html = html.replace('"/static/', '"file://' + BASE + '/static/')
    html = html.replace("'/static/", "'file://" + BASE + "/static/")
    # las tapas las sirve nginx; en la vista previa se leen del disco
    html = html.replace('"/tapas/', '"file://' + BASE + '/tapas/')
    html = html.replace('"/tapas-externas/', '"file:///opt/rayuela/tapas_externas/tapas/')

    extra = ''
    if args.sin_barras:
        extra = ('<style>.barra-admin,.barra-volver,.barra-acciones-catalogo{display:none !important}'
                 'body{padding-top:18px !important}</style>')
    html = html.replace('</head>', extra + '</head>')

    io.open(args.salida, 'w', encoding='utf-8').write(html)
    print('  html: %s (%d KB)' % (args.salida, len(html) // 1024))


if __name__ == '__main__':
    main()
