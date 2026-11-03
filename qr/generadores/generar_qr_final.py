"""QR definitivos de las apps de Rayuela: rayuelalaplata.com.ar

    python generar_qr_final.py
"""
import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

import generar_qr as g  # noqa: E402

BASE = 'https://ferias.rayuelalaplata.com.ar'
LECTOR = 'https://lector.rayuelalaplata.com.ar'
SALIDA = os.path.join(BASE_DIR, 'qr', 'final')


def main():
    os.makedirs(SALIDA, exist_ok=True)
    ok = True
    imagenes = {}
    for nombre, texto in (('app', BASE),
                          ('manual', BASE + '/manual'),
                          ('lector', LECTOR),
                          ('lector-vendedor', LECTOR + '/?m=v')):
        formato_ok, datos_ok, vuelta, matriz = g.verificar(texto)
        ok = ok and formato_ok and datos_ok
        print('  %-16s formato=%-3s datos=%-3s (%d caracteres)'
              % (nombre, 'OK' if formato_ok else 'MAL', 'OK' if datos_ok else 'MAL',
                 len(texto)))
        if not datos_ok:
            print('           volvio: %r' % (vuelta or '')[:80])
        imagen = g.dibujar_qr(matriz, escala=12, margen=4)
        imagen.save(os.path.join(SALIDA, 'qr-%s.png' % nombre))
        imagenes[nombre] = imagen

    hojas = (
        ('qr-hoja-A4-app.png', [
            ('Rayuela Ferias', 'Escaneá para vender y cargar stock', '', imagenes['app']),
            ('Manual de la app', 'Escaneá para ver el manual actualizado', '', imagenes['manual']),
        ]),
        ('qr-hoja-A4-lector.png', [
            ('Consultar precio', 'Escaneá y armá tu lista de deseos', '', imagenes['lector']),
            ('Lector de vendedores', 'Escaneá para consultar y armar la lista', '',
             imagenes['lector-vendedor']),
        ]),
    )
    for nombre, bloques in hojas:
        hoja = g.hoja_a4(bloques)
        ruta = os.path.join(SALIDA, nombre)
        hoja.save(ruta, dpi=(300, 300))
        print('  hoja A4  %-26s %d KB' % (nombre, os.path.getsize(ruta) // 1024))

    print('')
    print('TODO OK' if ok else 'HAY ERRORES')
    return 0 if ok else 1


if __name__ == '__main__':
    raise SystemExit(main())
