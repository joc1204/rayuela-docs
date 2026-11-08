"""Compara datos de Rayuela contra la autoconsulta y nuestra base.

La autoconsulta es el endpoint que usa el local:
    http://rayuela1.serveftp.net:9090/BSGestion/BuscadorProductosAction.do
        ?method=buscarArticulo&buscarPorDescripcion=false&id=<ISBN>

Trae datos actuales de Rayuela (titulo, precio, descripcion, autor, TEMA1-3).
NO trae stock. El stock de la demo viene de la API v1 (/api/productos, campo stock)
y no se puede contrastar aca.

No usa el webservice v0 (/rest/webservice): fue retirado.

    python3 comparar_bridge.py --isbn 9789876918732,9780194442312
    python3 comparar_bridge.py --limite 10
"""
import argparse
import json
import re
import sqlite3
import time
import unicodedata
import urllib.parse
import urllib.request

AUTOCONSULTA = ('http://rayuela1.serveftp.net:9090/BSGestion/'
                'BuscadorProductosAction.do')
DB = '/opt/rayuela/demo/catalogo.db'


def precio_a_numero(crudo):
    s = re.sub(r'[^\d,.\-]', '', str(crudo or ''))
    if not s:
        return 0.0
    if ',' in s and '.' in s:
        s = s.replace('.', '').replace(',', '.')
    elif ',' in s:
        s = s.replace(',', '.')
    try:
        return round(float(s), 2)
    except ValueError:
        return 0.0


def normalizar(texto):
    texto = unicodedata.normalize('NFD', texto or '')
    texto = ''.join(c for c in texto if unicodedata.category(c) != 'Mn')
    return ' '.join(texto.lower().split())


def autoconsultar(isbn):
    """Devuelve los datos actuales de Rayuela para un ISBN, sin stock."""
    url = (AUTOCONSULTA + '?method=buscarArticulo&buscarPorDescripcion=false&id='
           + urllib.parse.quote(str(isbn)))
    with urllib.request.urlopen(url, timeout=20) as respuesta:
        crudo = respuesta.read().decode('utf-8', 'replace')
    datos = json.loads(crudo)
    if not isinstance(datos, list) or len(datos) < 5:
        return None
    attrs = {}
    for par in datos[5:]:
        if isinstance(par, list) and len(par) == 2:
            attrs[str(par[0]).upper()] = str(par[1])
    temas = [str(attrs.get('TEMA%d' % i) or '').strip() for i in (1, 2, 3)]
    return {
        'id': datos[0],
        'titulo': str(datos[1] or '').strip(),
        'precio': precio_a_numero(datos[2]),
        'isbn': str(datos[3] or '').strip(),
        'detalle': str(datos[4] or '').strip(),
        'autor': str(attrs.get('AUTOR') or '').strip(),
        'editorial': str(attrs.get('EDITORIAL') or '').strip(),
        'coleccion': str(attrs.get('COLECCION') or '').strip(),
        'temas': ' | '.join(t for t in temas if t),
        'agotado': str(attrs.get('AGOTADO DESDE') or '').strip(),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--isbn', default=None, help='lista separada por comas')
    ap.add_argument('--limite', type=int, default=5)
    ap.add_argument('--pausa', type=float, default=0.3)
    args = ap.parse_args()

    if args.isbn:
        codigos = [c.strip() for c in args.isbn.split(',') if c.strip()]
    else:
        con = sqlite3.connect('file:%s?mode=ro' % DB, uri=True)
        codigos = [fila[0] for fila in con.execute(
            "select codigo from productos where publicable=1 and oculto=0 and filtro=0 "
            "and coalesce(stock,0) > 0 and actualizado >= '2026-11-08' "
            "order by actualizado desc limit ?", (args.limite,))]
        con.close()

    con = sqlite3.connect('file:%s?mode=ro' % DB, uri=True)
    con.row_factory = sqlite3.Row
    print('  ISBN · titulo · precio (base / Rayuela) · autor · temas')
    for codigo in codigos:
        nuestro = con.execute('select * from productos where codigo = ?', (codigo,)).fetchone()
        if not nuestro:
            print('  %s · no esta en nuestra base' % codigo)
            continue
        try:
            vivo = autoconsultar(codigo)
        except Exception as error:
            print('  %s · error en autoconsulta: %s' % (codigo, str(error)[:80]))
            continue
        if not vivo:
            print('  %s · la autoconsulta no devolvio datos' % codigo)
            continue
        precio_ok = abs(float(nuestro['precio'] or 0) - vivo['precio']) < 0.5
        autor_ok = normalizar(nuestro['autor'] or '') == normalizar(vivo['autor'])
        temas_ok = normalizar(nuestro['temas'] or '') == normalizar(vivo['temas'])
        print('  %s · %-30s · %s / %s %s · autor %s · temas %s'
              % (codigo, (nuestro['descripcion'] or '')[:30],
                 nuestro['precio'], vivo['precio'], 'OK' if precio_ok else 'DISTINTO',
                 'OK' if autor_ok else 'DISTINTO',
                 'OK' if temas_ok else 'DISTINTO'))
        if vivo['detalle']:
            print('    Rayuela detalle: %d caracteres · nuestro detalle: %d'
                  % (len(vivo['detalle']), len(nuestro['detalle'] or '')))
        time.sleep(args.pausa)
    con.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
