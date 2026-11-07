"""Indexa que titulos tienen tapa y ficha, para poder filtrar por SQL.

Uso: python3 indexar_archivos.py [--base /opt/rayuela/demo]

Lee los archivos de tapas/ y fichas/ y deja la tabla `archivos` con una fila por
(codigo, tipo). Se puede correr las veces que haga falta: borra y rehace.
"""
import argparse
import os
import sqlite3
import sys


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--base', default='/opt/rayuela/demo')
    args = ap.parse_args()

    bd = os.path.join(args.base, 'catalogo.db')
    tapas = os.path.join(args.base, 'tapas')
    fichas = os.path.join(args.base, 'fichas')
    if not os.path.exists(bd):
        sys.exit('no existe %s' % bd)

    def codigos(carpeta, sufijo):
        salida = []
        if not os.path.isdir(carpeta):
            return salida
        for nombre in os.listdir(carpeta):
            if nombre.lower().endswith(sufijo):
                salida.append(nombre[:-len(sufijo)])
        return salida

    lista_tapas = codigos(tapas, '.jpg') + codigos(tapas, '.png') + codigos(tapas, '.jpeg')
    lista_fichas = codigos(fichas, '.json')

    con = sqlite3.connect(bd, timeout=60)
    con.execute("""
        CREATE TABLE IF NOT EXISTS archivos (
            codigo TEXT NOT NULL,
            tipo TEXT NOT NULL,
            PRIMARY KEY (codigo, tipo))""")
    con.execute('delete from archivos')
    con.executemany('insert or ignore into archivos (codigo, tipo) values (?, ?)',
                    [(c, 'tapa') for c in lista_tapas])
    con.executemany('insert or ignore into archivos (codigo, tipo) values (?, ?)',
                    [(c, 'ficha') for c in lista_fichas])
    con.commit()
    total = con.execute('select count(*) from archivos').fetchone()[0]
    print('  indexado: %d tapas · %d fichas · %d filas' %
          (len(set(lista_tapas)), len(set(lista_fichas)), total))
    con.close()


if __name__ == '__main__':
    main()
