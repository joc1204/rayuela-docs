"""Genera los QR de la app de ferias y del lector, sin dependencias externas.

Implementa QR version 4, nivel de correccion M, mascara 0 (byte mode).
Alcanza para URL de hasta 62 caracteres.

Uso:
    python generar_qr.py
"""
import os

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover
    raise SystemExit('Hace falta Pillow para dibujar los QR.')

BASE = os.path.dirname(os.path.abspath(__file__))
SALIDA = os.path.join(BASE, 'qr')

URL_FERIAS = 'https://net-casa.tailfb7a36.ts.net/ferias/'
URL_LECTOR = 'https://net-casa.tailfb7a36.ts.net/ferias/rayuela'
URL_MANUAL = 'https://net-casa.tailfb7a36.ts.net/ferias/manual'
URL_NOVEDADES = 'https://net-casa.tailfb7a36.ts.net/novedades'
URL_LECTOR_VENDEDOR = 'https://net-casa.tailfb7a36.ts.net/ferias/rayuela?m=v'

# --- parametros fijos de la version 4 / nivel M ---
VERSION = 4
SIZE = 17 + 4 * VERSION     # 33 modulos
DATA_CW = 64                # codewords de datos (2 bloques x 32)
EC_CW = 18                  # codewords de correccion por bloque
BLOQUES = 2
MASK = 0
EC_BITS = 0b00              # M = 00

# ---------------------------------------------------------------- GF(256)
EXP = [0] * 512
LOG = [0] * 256
_x = 1
for _i in range(255):
    EXP[_i] = _x
    LOG[_x] = _i
    _x <<= 1
    if _x & 0x100:
        _x ^= 0x11D
for _i in range(255, 512):
    EXP[_i] = EXP[_i - 255]


def mul(a, b):
    if a == 0 or b == 0:
        return 0
    return EXP[LOG[a] + LOG[b]]


def poly_mul(p, q):
    r = [0] * (len(p) + len(q) - 1)
    for i, a in enumerate(p):
        for j, b in enumerate(q):
            r[i + j] ^= mul(a, b)
    return r


def generador(n):
    g = [1]
    for i in range(n):
        g = poly_mul(g, [1, EXP[i]])
    return g


def reed_solomon(datos, n):
    g = generador(n)
    res = list(datos) + [0] * n
    for i in range(len(datos)):
        coef = res[i]
        if coef:
            for j in range(len(g)):
                res[i + j] ^= mul(g[j], coef)
    return res[-n:]


# ---------------------------------------------------------------- datos
def codewords_de_datos(texto):
    datos = texto.encode('utf-8')
    if len(datos) > 62:
        raise ValueError('El texto es muy largo para la version 4.')

    bits = []

    def poner(valor, n):
        for i in range(n - 1, -1, -1):
            bits.append((valor >> i) & 1)

    poner(0b0100, 4)          # modo byte
    poner(len(datos), 8)      # cantidad (8 bits en versiones 1 a 9)
    for b in datos:
        poner(b, 8)

    capacidad = DATA_CW * 8
    poner(0, min(4, capacidad - len(bits)))     # terminador
    while len(bits) % 8:
        bits.append(0)

    cws = []
    for i in range(0, len(bits), 8):
        v = 0
        for bit in bits[i:i + 8]:
            v = (v << 1) | bit
        cws.append(v)

    while len(cws) < DATA_CW:
        cws.append(0xEC)
        if len(cws) < DATA_CW:
            cws.append(0x11)
    return cws


def codewords_finales(texto):
    datos = codewords_de_datos(texto)
    bloque = DATA_CW // BLOQUES
    bloques = [datos[i * bloque:(i + 1) * bloque] for i in range(BLOQUES)]
    correcciones = [reed_solomon(b, EC_CW) for b in bloques]

    final = []
    for i in range(bloque):
        for b in bloques:
            final.append(b[i])
    for i in range(EC_CW):
        for c in correcciones:
            final.append(c[i])
    return final


# ---------------------------------------------------------------- matriz
def mascara(fila, col):
    return (fila + col) % 2 == 0


def bch_formato(datos):
    g = 0b10100110111
    v = datos << 10
    for i in range(4, -1, -1):
        if v & (1 << (i + 10)):
            v ^= g << i
    return ((datos << 10) | (v & 0x3FF)) ^ 0b101010000010010


def matriz(texto):
    codewords = codewords_finales(texto)
    m = [[None] * SIZE for _ in range(SIZE)]
    func = [[False] * SIZE for _ in range(SIZE)]

    def marcar(fila, col, valor):
        m[fila][col] = valor
        func[fila][col] = True

    def finder(fila, col):
        for r in range(-1, 8):
            for c in range(-1, 8):
                rr, cc = fila + r, col + c
                if not (0 <= rr < SIZE and 0 <= cc < SIZE):
                    continue
                dentro = 0 <= r <= 6 and 0 <= c <= 6
                borde = dentro and (r in (0, 6) or c in (0, 6))
                centro = 2 <= r <= 4 and 2 <= c <= 4
                marcar(rr, cc, 1 if (borde or centro) else 0)

    finder(0, 0)
    finder(0, SIZE - 7)
    finder(SIZE - 7, 0)

    for i in range(8, SIZE - 8):
        marcar(6, i, 1 if i % 2 == 0 else 0)
        marcar(i, 6, 1 if i % 2 == 0 else 0)

    for r in range(-2, 3):
        for c in range(-2, 3):
            marcar(26 + r, 26 + c, 1 if max(abs(r), abs(c)) != 1 else 0)

    for i in range(9):
        marcar(8, i, 0)
        marcar(i, 8, 0)
    for i in range(8):
        marcar(8, SIZE - 1 - i, 0)
        marcar(SIZE - 1 - i, 8, 0)

    # datos en zigzag
    fila = SIZE - 1
    inc = -1
    indice_byte = 0
    indice_bit = 7
    for col in range(SIZE - 1, 0, -2):
        if col <= 6:
            col -= 1
        while True:
            for c in range(2):
                if m[fila][col - c] is None:
                    if indice_byte < len(codewords):
                        oscuro = ((codewords[indice_byte] >> indice_bit) & 1) == 1
                    else:
                        oscuro = False
                    if mascara(fila, col - c):
                        oscuro = not oscuro
                    m[fila][col - c] = 1 if oscuro else 0
                    indice_bit -= 1
                    if indice_bit == -1:
                        indice_byte += 1
                        indice_bit = 7
            fila += inc
            if fila < 0 or fila >= SIZE:
                fila -= inc
                inc = -inc
                break

    # info de formato (dos copias) + modulo oscuro
    fmt = bch_formato((EC_BITS << 3) | MASK)
    for i in range(15):
        bit = 1 if ((fmt >> i) & 1) else 0
        if i < 6:
            m[i][8] = bit
        elif i < 8:
            m[i + 1][8] = bit
        else:
            m[SIZE - 15 + i][8] = bit
    for i in range(15):
        bit = 1 if ((fmt >> i) & 1) else 0
        if i < 8:
            m[8][SIZE - i - 1] = bit
        elif i < 9:
            m[8][15 - i] = bit
        else:
            m[8][15 - i - 1] = bit
    m[SIZE - 8][8] = 1
    return m, func


# ---------------------------------------------------------------- verificacion
def leer_formato(m):
    bits = []
    for i in range(15):
        if i < 8:
            bits.append(m[8][SIZE - i - 1])
        elif i < 9:
            bits.append(m[8][15 - i])
        else:
            bits.append(m[8][15 - i - 1])
    valor = 0
    for i, bit in enumerate(bits):
        valor |= (bit & 1) << i
    return any(valor == bch_formato((ec << 3) | MASK) for ec in range(4))


def leer_datos(m, func):
    """Deshace mascara y zigzag; devuelve los codewords intercalados."""
    cw = []
    byte = 0
    bit_i = 7
    fila = SIZE - 1
    inc = -1
    for col in range(SIZE - 1, 0, -2):
        if col <= 6:
            col -= 1
        while True:
            for c in range(2):
                if not func[fila][col - c]:
                    bit = m[fila][col - c] & 1
                    if mascara(fila, col - c):
                        bit ^= 1
                    byte = (byte << 1) | bit
                    bit_i -= 1
                    if bit_i == -1:
                        cw.append(byte)
                        byte = 0
                        bit_i = 7
            fila += inc
            if fila < 0 or fila >= SIZE:
                fila -= inc
                inc = -inc
                break
    return cw


def texto_desde_codewords(intercalados):
    # de-intercalar: primero el bloque 0 completo, despues el bloque 1
    datos = []
    for i in range(32):
        datos.append(intercalados[2 * i])
    for i in range(32):
        datos.append(intercalados[2 * i + 1])

    bits = []
    for c in datos:
        for k in range(7, -1, -1):
            bits.append((c >> k) & 1)

    def leer(desde, n):
        v = 0
        for bit in bits[desde:desde + n]:
            v = (v << 1) | bit
        return v

    modo = leer(0, 4)
    largo = leer(4, 8)
    if modo != 0b0100 or largo > 62:
        return None
    salida = bytearray()
    pos = 12
    for _ in range(largo):
        salida.append(leer(pos, 8))
        pos += 8
    return salida.decode('utf-8', 'replace')


def verificar(texto):
    m, func = matriz(texto)
    formato_ok = leer_formato(m)
    cw = leer_datos(m, func)
    vuelta = texto_desde_codewords(cw)
    return formato_ok, vuelta == texto, vuelta, m


# ---------------------------------------------------------------- dibujo
def dibujar_qr(m, escala=12, margen=4):
    lado = (SIZE + margen * 2) * escala
    img = Image.new('RGB', (lado, lado), (255, 255, 255))
    d = ImageDraw.Draw(img)
    for f in range(SIZE):
        for c in range(SIZE):
            if m[f][c]:
                x0 = (c + margen) * escala
                y0 = (f + margen) * escala
                d.rectangle([x0, y0, x0 + escala - 1, y0 + escala - 1], fill=(0, 0, 0))
    return img


def fuente(tamano):
    for nombre in ('arial.ttf', 'segoeui.ttf', 'calibri.ttf'):
        ruta = os.path.join(os.environ.get('WINDIR', r'C:\Windows'), 'Fonts', nombre)
        if os.path.exists(ruta):
            try:
                return ImageFont.truetype(ruta, tamano)
            except OSError:
                continue
    return ImageFont.load_default()


def hoja_a4(bloques):
    """bloques: [(titulo, subtitulo, url, imagen_qr), ...] — reparte la hoja parejo."""
    ancho, alto = 2480, 3508        # A4 a 300 dpi
    hoja = Image.new('RGB', (ancho, alto), (255, 255, 255))
    d = ImageDraw.Draw(hoja)
    f_titulo = fuente(86)
    f_sub = fuente(48)
    f_url = fuente(32)

    n = len(bloques)
    alto_bloque = alto // n
    lado = 900 if n <= 2 else 760
    alto_contenido = 120 + lado + 170
    for i, (titulo, subtitulo, url, imagen) in enumerate(bloques):
        y = i * alto_bloque + max(40, (alto_bloque - alto_contenido) // 2)
        d.text((ancho // 2, y), titulo, font=f_titulo, fill=(20, 20, 20), anchor='ma')
        im = imagen.resize((lado, lado), Image.NEAREST)
        hoja.paste(im, ((ancho - lado) // 2, y + 120))
        d.text((ancho // 2, y + 120 + lado + 45), subtitulo, font=f_sub,
               fill=(70, 70, 70), anchor='ma')
        d.text((ancho // 2, y + 120 + lado + 112), url, font=f_url,
               fill=(130, 130, 130), anchor='ma')
        if i < n - 1:
            yy = (i + 1) * alto_bloque - 45
            d.line([(260, yy), (ancho - 260, yy)], fill=(210, 210, 210), width=3)
    return hoja


def main():
    os.makedirs(SALIDA, exist_ok=True)
    ok_total = True

    for nombre, texto, titulo in (('qr-lector', URL_LECTOR, 'lector'),
                                  ('qr-ferias', URL_FERIAS, 'ferias'),
                                  ('qr-manual', URL_MANUAL, 'manual'),
                                  ('qr-novedades', URL_NOVEDADES, 'novedades'),
                                  ('qr-lector-vendedor', URL_LECTOR_VENDEDOR, 'vendedor')):
        formato_ok, datos_ok, vuelta, m = verificar(texto)
        ok_total = ok_total and formato_ok and datos_ok
        print('  %-8s formato=%-3s datos=%-3s (%d caracteres)'
              % (titulo, 'OK' if formato_ok else 'MAL',
                 'OK' if datos_ok else 'MAL', len(texto)))
        if not datos_ok:
            print('           volvio: %r' % (vuelta or '')[:80])
        img = dibujar_qr(m, escala=12, margen=4)
        ruta = os.path.join(SALIDA, nombre + '.png')
        img.save(ruta)
        print('           %s (%d bytes)' % (os.path.basename(ruta), os.path.getsize(ruta)))

    mf, _ = matriz(URL_FERIAS)
    ml, _ = matriz(URL_LECTOR)
    mm, _ = matriz(URL_MANUAL)
    mn, _ = matriz(URL_NOVEDADES)
    qr_f = dibujar_qr(mf, escala=10, margen=4)
    qr_l = dibujar_qr(ml, escala=10, margen=4)
    qr_m = dibujar_qr(mm, escala=10, margen=4)
    qr_n = dibujar_qr(mn, escala=10, margen=4)
    mv, _ = matriz(URL_LECTOR_VENDEDOR)
    qr_v = dibujar_qr(mv, escala=10, margen=4)

    hojas = (
        ('qr-hoja-A4-ferias-manual.png', [
            ('Rayuela Ferias', 'Escaneá para vender y controlar stock', URL_FERIAS, qr_f),
            ('Manual de la app', 'Escaneá para ver el manual actualizado', URL_MANUAL, qr_m),
        ]),
        ('qr-hoja-A4-lector-novedades.png', [
            ('Lector de precios', 'Escaneá para consultar un precio', URL_LECTOR, qr_l),
            ('Novedades', 'Escaneá para cargar ISBN y recibirlos por mail', URL_NOVEDADES, qr_n),
        ]),
        ('qr-hoja-A4-lector.png', [
            ('Consultar precio', 'Escaneá y armá tu lista de deseos', '', qr_l),
            ('Lector de vendedores', 'Escaneá para consultar y armar la lista', '', qr_v),
        ]),
    )
    for nombre, bloques in hojas:
        hoja = hoja_a4(bloques)
        ruta = os.path.join(SALIDA, nombre)
        hoja.save(ruta, dpi=(300, 300))
        print('  hoja A4  %s (%d bytes)' % (nombre, os.path.getsize(ruta)))
    print('  ' + ('TODO OK' if ok_total else 'HAY ERRORES'))


if __name__ == '__main__':
    main()
