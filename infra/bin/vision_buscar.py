"""Busca tapas por descripcion en castellano usando los vectores de vision_indexar.py.

    /opt/rayuela/vision/venv/bin/python vision_buscar.py "una foca y un elefante"
    /opt/rayuela/vision/venv/bin/python vision_buscar.py "tres chicos corriendo" --html /tmp/busqueda.html

No modifica nada: solo lee el .npz y la base.
"""
import argparse
import html
import os
import shutil
import sqlite3

import numpy as np
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('texto')
    ap.add_argument('--base', default='/opt/rayuela/demo')
    ap.add_argument('--indice', default='/opt/rayuela/vision/tapas.npz')
    ap.add_argument('--cantidad', type=int, default=6)
    ap.add_argument('--html', default=None)
    args = ap.parse_args()

    import open_clip

    torch.set_num_threads(1)
    datos = np.load(args.indice, allow_pickle=True)
    codigos = datos['codigos']
    vectores = datos['vectores']
    if len(codigos) == 0:
        print('  el indice esta vacio')
        return 1

    modelo, _, _ = open_clip.create_model_and_transforms(
        str(datos['modelo']), pretrained=str(datos['pretrained']), device='cpu')
    modelo.eval()
    with torch.no_grad():
        tokens = open_clip.tokenize([args.texto])
        consulta = modelo.encode_text(tokens)
        consulta = consulta / consulta.norm(dim=-1, keepdim=True)
        parecidos = (vectores @ consulta.cpu().numpy().T).ravel()

    orden = parecidos.argsort()[::-1][:args.cantidad]
    db = os.path.join(args.base, 'catalogo.db')
    con = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
    resultados = []
    for posicion in orden:
        codigo = str(codigos[posicion])
        fila = con.execute('select descripcion, autor from productos where codigo = ?',
                           (codigo,)).fetchone()
        resultados.append((codigo, fila[0] if fila else '', fila[1] if fila else '',
                           float(parecidos[posicion])))
    con.close()

    print('  busqueda: %r' % args.texto)
    for codigo, descripcion, autor, puntaje in resultados:
        print('    %.3f  %-14s %s — %s' % (puntaje, codigo, descripcion[:55], autor[:30]))

    if args.html:
        carpeta = os.path.splitext(args.html)[0] + '-tapas'
        os.makedirs(carpeta, exist_ok=True)
        partes = ['<meta charset="utf-8"><body style="font-family:sans-serif;background:#faf6f0">',
                  '<h2>%s</h2><div style="display:flex;flex-wrap:wrap;gap:16px">' % html.escape(args.texto)]
        for codigo, descripcion, autor, puntaje in resultados:
            origen = os.path.join(args.base, 'tapas', codigo + '.jpg')
            destino = os.path.join(carpeta, codigo + '.jpg')
            if os.path.exists(origen):
                shutil.copy(origen, destino)
            partes.append(
                '<div style="width:180px;background:#fff;padding:8px;border:1px solid #ddd">'
                '<img src="%s" style="width:100%%"><div style="font-size:12px">%.3f · %s<br>%s</div></div>'
                % (html.escape(os.path.basename(carpeta) + '/' + os.path.basename(destino)), puntaje,
                   html.escape(descripcion[:40]), html.escape(autor[:25])))
        partes.append('</div>')
        with open(args.html, 'w', encoding='utf-8') as archivo:
            archivo.write('\n'.join(partes))
        print('  galeria: %s' % args.html)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
