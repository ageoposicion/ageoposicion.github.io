"""Cambia el bloque o retira preguntas en una especificación scripts/lotes/lote-NNN.py sin renumerar.
Uso (desde Python): editar(ruta, fn) donde fn(n, entrada) devuelve la entrada (tupla) o una cadena 'RETIRADA: motivo'."""
import ast, sys
sys.dont_write_bytecode = True

def editar(ruta, fn):
    src = open(ruta, encoding='utf-8').read()
    arbol = ast.parse(src)
    ns = {}; exec(compile(src, ruta, 'exec'), ns)
    lista = next(n.value for n in arbol.body if isinstance(n, ast.Assign) and any(getattr(t, 'id', None) == 'PREGUNTAS' for t in n.targets))
    lineas = src.split('\n')
    cambios = []
    for k, el in enumerate(lista.elts):
        n = ns['INICIO'] + k
        ent = ns['PREGUNTAS'][k]
        nueva = fn(n, ent)
        if nueva == ent: continue
        a = sum(len(x) + 1 for x in lineas[:el.lineno - 1]) + len(lineas[el.lineno - 1].encode('utf-8')[:el.col_offset].decode('utf-8'))
        b = sum(len(x) + 1 for x in lineas[:el.end_lineno - 1]) + len(lineas[el.end_lineno - 1].encode('utf-8')[:el.end_col_offset].decode('utf-8'))
        if isinstance(nueva, str): txt = repr(nueva)
        else:
            viejo = src[a:b]
            assert viejo.startswith("('%s'," % ent[0]), viejo[:30]
            txt = "('%s'," % nueva[0] + viejo[len("('%s'," % ent[0]):]
            assert tuple(nueva[1:]) == tuple(ent[1:]), 'solo se admite cambiar el bloque'
        cambios.append((a, b, txt))
    for a, b, txt in sorted(cambios, reverse=True): src = src[:a] + txt + src[b:]
    open(ruta, 'w', encoding='utf-8').write(src)
    return len(cambios)
