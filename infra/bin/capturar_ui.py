"""Saca capturas de un HTML en varios anchos, para revisar la UI antes de publicar.

    python3 capturar_ui.py --html /tmp/pantalla.html --salida /tmp/capturas \
        --nombre catalogo --anchos 1280,1024,390

Requiere playwright y chromium instalados (venv en /opt/rayuela/capturas/venv).
"""
import argparse
import os
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--html', required=True)
    ap.add_argument('--salida', default='/tmp/capturas')
    ap.add_argument('--nombre', default='pantalla')
    ap.add_argument('--anchos', default='1280,1024,390')
    ap.add_argument('--alto', type=int, default=900)
    ap.add_argument('--completo', action='store_true', help='captura toda la pagina, no solo la ventana')
    args = ap.parse_args()

    from playwright.sync_api import sync_playwright

    html = Path(args.html).resolve()
    salida = Path(args.salida)
    salida.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        navegador = p.chromium.launch(args=['--no-sandbox'])
        for ancho in [int(x) for x in args.anchos.split(',') if x.strip()]:
            pagina = navegador.new_page(viewport={'width': ancho, 'height': args.alto})
            pagina.goto('file://' + str(html))
            pagina.wait_for_timeout(250)
            destino = salida / ('%s-%d.png' % (args.nombre, ancho))
            pagina.screenshot(path=str(destino), full_page=args.completo)
            print('  captura: %s' % destino)
            pagina.close()
        navegador.close()


if __name__ == '__main__':
    main()
