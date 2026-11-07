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
    ap.add_argument('--scroll', action='store_true', help='recorre la pagina para cargar imagenes con lazy')
    ap.add_argument('--selector', default=None, help='captura solo ese elemento css')
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
            pagina.wait_for_timeout(300)
            if args.scroll:
                pagina.evaluate('''async () => {
                    for (let y = 0; y < document.body.scrollHeight; y += 600) {
                        window.scrollTo(0, y);
                        await new Promise(r => setTimeout(r, 60));
                    }
                    window.scrollTo(0, 0);
                }''')
                pagina.wait_for_timeout(400)
            destino = salida / ('%s-%d.png' % (args.nombre, ancho))
            if args.selector:
                elemento = pagina.locator(args.selector).first
                elemento.scroll_into_view_if_needed()
                pagina.wait_for_timeout(250)
                elemento.screenshot(path=str(destino))
            else:
                pagina.screenshot(path=str(destino), full_page=args.completo)
            print('  captura: %s' % destino)
            pagina.close()
        navegador.close()


if __name__ == '__main__':
    main()
