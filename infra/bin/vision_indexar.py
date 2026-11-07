"""Indexa tapas de libros con CLIP para buscarlas por descripcion en castellano.

    /opt/rayuela/vision/venv/bin/python vision_indexar.py --limite 100

Guarda un .npz con los codigos y los vectores. No toca la base de la tienda.
Pensado para correr de a poco: --limite y --desde permiten procesar por tandas.
"""
import argparse
import os
import resource
import sqlite3
import time

import numpy as np
import torch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='/opt/rayuela/demo')
    ap.add_argument('--db', default=None)
    ap.add_argument('--limite', type=int, default=100)
    ap.add_argument('--desde', type=int, default=0)
    ap.add_argument('--modelo', default='MobileCLIP2-S0')
    ap.add_argument('--pretrained', default='dfndr2b')
    ap.add_argument('--salida', default='/opt/rayuela/vision/tapas.npz')
    ap.add_argument('--imagenes', default=None)
    args = ap.parse_args()

    import open_clip
    from PIL import Image

    torch.set_num_threads(1)
    base = args.base
    imagenes = args.imagenes or os.path.join(base, 'tapas')
    db = args.db or os.path.join(base, 'catalogo.db')

    print('  cargando modelo %s (%s)' % (args.modelo, args.pretrained), flush=True)
    modelo, _, preprocesar = open_clip.create_model_and_transforms(
        args.modelo, pretrained=args.pretrained, device='cpu')
    modelo.eval()
    print('  modelo listo · memoria %.0f MB' % (resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024), flush=True)

    con = sqlite3.connect('file:%s?mode=ro' % db, uri=True)
    filas = con.execute(
        "select a.codigo, p.descripcion, p.autor from archivos a "
        "left join productos p on p.codigo = a.codigo "
        "where a.tipo = 'tapa' order by a.codigo limit ? offset ?",
        (args.limite, args.desde)).fetchall()
    con.close()

    codigos, textos = [], []
    vectores = []
    inicio = time.time()
    with torch.no_grad():
        lote = []
        for codigo, descripcion, autor in filas:
            ruta = os.path.join(imagenes, codigo + '.jpg')
            if not os.path.exists(ruta):
                continue
            try:
                imagen = Image.open(ruta).convert('RGB')
            except Exception:
                continue
            lote.append((codigo, descripcion or '', autor or '', preprocesar(imagen)))
            if len(lote) >= 8:
                vectores.append(_vector(modelo, [x[3] for x in lote]))
                for c, d, a, _ in lote:
                    codigos.append(c)
                    textos.append((d, a))
                lote = []
                print('  %d/%d · %.2f tapas por segundo' % (
                    len(codigos), len(filas), len(codigos) / max(1, time.time() - inicio)),
                    flush=True)
        if lote:
            vectores.append(_vector(modelo, [x[3] for x in lote]))
            for c, d, a, _ in lote:
                codigos.append(c)
                textos.append((d, a))

    matriz = np.vstack(vectores).astype('float32') if vectores else np.zeros((0, 512), 'float32')
    np.savez_compressed(args.salida,
                        codigos=np.array(codigos),
                        vectores=matriz,
                        modelo=args.modelo,
                        pretrained=args.pretrained)
    memoria = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024
    print('  listo: %d tapas en %.1f s · %.2f s por tapa · memoria pico %.0f MB'
          % (len(codigos), time.time() - inicio,
             (time.time() - inicio) / max(1, len(codigos)), memoria))


def _vector(modelo, imagenes):
    import open_clip
    lote = torch.stack(imagenes)
    with torch.no_grad():
        vectores = modelo.encode_image(lote)
        vectores = vectores / vectores.norm(dim=-1, keepdim=True)
    return vectores.cpu().numpy()


if __name__ == '__main__':
    main()
