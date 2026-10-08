"""Genera data/questions/lote-NNN.json a partir de una especificación en scripts/lotes/lote-NNN.py.
La 'cita' NO se escribe a mano: se extrae del texto del BOE (data/boe) buscando, en el artículo
indicado, la expresión de cada pregunta y ampliándola hasta la frase completa.
Uso: python scripts/make_lote.py scripts/lotes/lote-002.py"""
import glob, importlib.util, json, os, random, re, sys, unicodedata
sys.dont_write_bytecode = True
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
NOTA = re.compile(r'Se modifica|Se añade|Se suprime|Se deroga|Redactado|Téngase en cuenta|Ref\. BOE')
INICIO = re.compile(r'(?:[.;]) (?=[A-ZÁÉÍÓÚÑ¿«"0-9]|[a-z]\) )')   # comienzo de frase, apartado o letra
FIN = re.compile(r'[.;](?= [A-ZÁÉÍÓÚÑ¿«"0-9]| [a-z]\) |$)')
MAX = 320
RA = re.compile(r'Redacción anterior')
def norm(s):  # misma normalización que build_bank.py
    s = unicodedata.normalize('NFKC', s or '').lower()
    s = s.replace('“', '"').replace('”', '"').replace('«', '"').replace('»', '"').replace('’', "'").replace('–', '-').replace('—', '-')
    return re.sub(r'\s+', ' ', s).strip()
def patron(a):
    if a.startswith('re:'): return re.compile(a[3:])
    return re.compile(r'\s+'.join(re.escape(w) for w in a.split()))
def cita(txt, ancla):
    p = patron(ancla); ms = list(p.finditer(txt))
    if not ms: raise ValueError('ancla no encontrada: %r' % ancla)
    if len(ms) > 1:
        # Si las demás apariciones están dentro de una «Redacción anterior» (texto ya no vigente que el BOE
        # reproduce tras el vigente), vale la primera; en otro caso la ancla es ambigua.
        ra = [m.start() for m in RA.finditer(txt)]
        if not (ra and ms[0].end() <= ra[0] and all(m.start() >= ra[0] for m in ms[1:])):
            raise ValueError('ancla ambigua (%d apariciones): %r' % (len(ms), ancla))
        ms = ms[:1]
    i, j = ms[0].span()
    ss = [m.end() for m in INICIO.finditer(txt) if m.end() <= i]
    s = ss[-1] if ss else 0
    m = FIN.search(txt, j); e = m.end() if m else len(txt)
    if e - s > MAX:  # frase muy larga: la coincidencia más un poco de contexto, cortando en espacios
        s2, e2 = max(s, i - 100), min(e, j + 100)
        if s2 > s: s2 = txt.index(' ', s2) + 1 if ' ' in txt[s2:i] else i
        if e2 < e: e2 = txt.rindex(' ', j, e2) if ' ' in txt[j:e2] else j
        s, e = s2, e2
    c = re.sub(r'^Artículo \S+ ', '', txt[s:e].strip())
    if NOTA.search(c): raise ValueError('la cita incluye una nota del BOE: %r' % c)
    if len(norm(c)) < 25: raise ValueError('cita demasiado corta: %r' % c)
    assert norm(c) in norm(txt)
    return c
def main(spec_path):
    sp = importlib.util.spec_from_file_location('spec', spec_path); S = importlib.util.module_from_spec(sp); sp.loader.exec_module(S)
    boe = json.load(open(os.path.join(ROOT, 'data', 'boe', S.NORMA + '.json'), encoding='utf-8'))['articulos']
    out_path = os.path.join(ROOT, 'data', 'questions', S.LOTE + '.json')
    previas = {}
    for f in glob.glob(os.path.join(ROOT, 'data', 'questions', '*.json')):
        if os.path.abspath(f) == os.path.abspath(out_path): continue
        for q in json.load(open(f, encoding='utf-8')): previas[norm(q['pregunta'])] = os.path.basename(f)
    res, errores, vistos = [], [], set()
    for k, entrada in enumerate(S.PREGUNTAS):
        n = S.INICIO + k
        if isinstance(entrada, str): continue   # pregunta retirada: se conserva su hueco para no renumerar
        bloque, tipo, art, preg, ok, malas, ancla = entrada
        try:
            if art not in boe: raise ValueError('artículo inexistente: ' + art)
            if len(malas) != 3: raise ValueError('hacen falta 3 distractores')
            if len({norm(x) for x in [ok] + malas}) != 4: raise ValueError('opciones repetidas')
            if norm(preg) in previas or norm(preg) in vistos: raise ValueError('pregunta repetida (%s)' % previas.get(norm(preg), S.LOTE))
            vistos.add(norm(preg))
            c = cita(boe[art]['texto'], ancla)
        except ValueError as e:
            errores.append('#%d %s: %s' % (n, art, e)); continue
        r = random.Random(n); o = list(malas); r.shuffle(o); pos = r.randrange(4); o.insert(pos, ok)
        res.append({'n': n, 'bloque': bloque, 'tipo': tipo, 'norma': S.NORMA, 'articulo': art, 'pregunta': preg,
                    'opciones': o, 'correcta': pos, 'cita': c})
    if errores:
        print('\n'.join(errores)); print(len(errores), 'errores: no se ha escrito el lote'); sys.exit(1)
    json.dump(res, open(out_path, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    for q in res:
        print('#%d [%s/%s] %s | %s\n   ✔ %s\n   ✘ %s\n   « %s »' % (q['n'], q['bloque'], q['tipo'], q['articulo'], q['pregunta'],
              q['opciones'][q['correcta']], ' | '.join(x for i, x in enumerate(q['opciones']) if i != q['correcta']), q['cita']))
    print(len(res), 'preguntas escritas en', os.path.relpath(out_path, ROOT))
if __name__ == '__main__': main(sys.argv[1])
