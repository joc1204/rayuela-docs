"""Compara, para varios ISBN, los datos de Rayuela produccion, el servidor de
pruebas y nuestra base.

Uso (cuando Rayuela esta cerrada, para no cargarla):

    python3 comparar_bridge.py --limite 10
    python3 comparar_bridge.py --isbn 9788433998088,9789871307845
    python3 comparar_bridge.py --limite 10 --sin-produccion   # solo pruebas

Lee el articulo por el webservice viejo (/rest/webservice/articulo/<isbn>) en
produccion y en pruebas, y ademas la API v1 de pruebas (token de /etc/rayuela/bridge.env)
para rubro/categoria/stock/precio.

No escribe nada: solo GET.
"""
import argparse
import json
import os
import sqlite3
import time
import urllib.error
import urllib.request

PROD = 'http://rayuela1.serveftp.net:9090/BSGestion'
PRUEBAS = 'http://brd.serveftp.net:10160/BSGestionRayuela'
DB = '/opt/rayuela/demo/catalogo.db'


def token():
    try:
        for linea in open('/etc/rayuela/bridge.env', encoding='utf-8', errors='ignore'):
            if linea.startswith('BRIDGE_TOKEN='):
                return linea.split('=', 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return ''


def get_json(url, clave=None, timeout=30):
    pedido = urllib.request.Request(url)
    if clave:
        pedido.add_header('Authorization', 'Bearer ' + clave)
    try:
        with urllib.request.urlopen(pedido, timeout=timeout) as respuesta:
            return json.loads(respuesta.read().decode('utf-8', 'ignore'))
    except (urllib.error.URLError, ValueError):
        return None


def propiedades(ficha):
    salida = {}
    for p in (ficha or {}).get('propiedades') or []:
        nombre = (p.get('nombre') or '').strip().upper()
        valor = (p.get('valor') or '').strip()
        if nombre and valor:
            salida[nombre] = valor
    return salida


def resumen(ficha):
    if not ficha:
        return None
    props = propiedades(ficha)
    return {
        'descripcion': (ficha.get('descripcion') or '').strip(),
        'detalle': (ficha.get('detalle') or '').strip(),
        'marca': (ficha.get('marca') or '').strip(),
        'precio': ficha.get('precioLista'),
        'stock': ficha.get('stockVenta'),
        'estado': (ficha.get('estado') or '').strip(),
        'categoria': ficha.get('categoria'),
        'fechaMod': ficha.get('fechaMod') or ficha.get('fechaAct'),
        'autor': props.get('AUTOR', ''),
        'tema1': props.get('TEMA1', ''),
        'tema2': props.get('TEMA2', ''),
        'tema3': props.get('TEMA3', ''),
        'coleccion': props.get('COLECCION', ''),
        'paginas': props.get('PAGINAS', ''),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--isbn', default=None, help='lista separada por comas')
    ap.add_argument('--limite', type=int, default=10)
    ap.add_argument('--sin-produccion', action='store_true',
                    help='no consulta produccion (para probar el script)')
    ap.add_argument('--pausa', type=float, default=0.4)
    ap.add_argument('--salida', default='/tmp/comparacion-bridge.json')
    args = ap.parse_args()

    clave = token()
    if args.isbn:
        codigos = [c.strip() for c in args.isbn.split(',') if c.strip()]
    else:
        con = sqlite3.connect('file:%s?mode=ro' % DB, uri=True)
        codigos = [fila[0] for fila in con.execute(
            "select codigo from productos where publicable=1 and oculto=0 and filtro=0 "
            "and coalesce(stock,0) > 0 and detalle is not null and detalle != '' "
            "order by actualizado desc limit ?", (args.limite,))]
        con.close()

    con = sqlite3.connect('file:%s?mode=ro' % DB, uri=True)
    con.row_factory = sqlite3.Row
    informe = []
    for codigo in codigos:
        nuestro = con.execute('select * from productos where codigo = ?',
                             (codigo,)).fetchone()
        pruebas = resumen(get_json('%s/rest/webservice/articulo/%s' % (PRUEBAS, codigo)))
        produccion = None if args.sin_produccion else resumen(
            get_json('%s/rest/webservice/articulo/%s' % (PROD, codigo)))
        api_pruebas = get_json('%s/api/productos?pagina=1&limite=1&busqueda=%s'
                               '&campos=codigo,descripcion,categoria,rubro,stock,precioVenta'
                               % (PRUEBAS, codigo), clave)
        api = ((api_pruebas or {}).get('datos') or [{}])[0] if api_pruebas else {}

        informe.append({
            'codigo': codigo,
            'nuestro': dict(nuestro) if nuestro else None,
            'pruebas': pruebas,
            'produccion': produccion,
            'api_pruebas': api,
        })
        print('  %s · %s' % (codigo, (nuestro['descripcion'] if nuestro else '?')[:45]))
        if produccion and pruebas:
            iguales = sum(1 for k in pruebas if pruebas.get(k) == produccion.get(k))
            print('    pruebas vs produccion: %d/%d campos iguales' % (iguales, len(pruebas)))
            for campo in ('stock', 'precio', 'estado', 'categoria', 'tema1', 'fechaMod'):
                if pruebas.get(campo) != produccion.get(campo):
                    print('    distinto en %s: pruebas=%r produccion=%r'
                          % (campo, pruebas.get(campo), produccion.get(campo)))
        elif args.sin_produccion:
            print('    (sin produccion) stock=%r precio=%r temas=%r'
                  % (pruebas.get('stock') if pruebas else None,
                     pruebas.get('precio') if pruebas else None,
                     (pruebas.get('tema1'), pruebas.get('tema2'), pruebas.get('tema3')) if pruebas else None))
        time.sleep(args.pausa)

    con.close()
    with open(args.salida, 'w', encoding='utf-8') as archivo:
        json.dump(informe, archivo, ensure_ascii=False, indent=1)
    print('  informe: %s' % args.salida)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
