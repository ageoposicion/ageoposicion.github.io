"""Pasa a Plazómetro las preguntas del banco (data/bank.json) que aún no tiene, y cambia el tema de las que lo necesiten.
Uso: python scripts/plazometro/fusion.py <html publicado de Plazómetro> <html de salida> <primer número de pregunta a considerar>
Las anteriores ya se revisaron en fusiones previas (las repetidas se descartaron entonces a mano).
Solo toca el banco (const BANK = …); el código de la app no se modifica."""
import glob, importlib.util, json, os, re, sys, unicodedata
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
sys.dont_write_bytecode = True
def strip(s): return ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
def toks(s): return set(w for w in re.findall(r'[a-z0-9]+', strip(s)) if len(w) > 3)
# anclas de cada pregunta (la frase que se resalta en la cita)
ANC = {}
for f in sorted(glob.glob(os.path.join(ROOT, 'scripts', 'lotes', 'lote-*.py'))):
    sp = importlib.util.spec_from_file_location('m', f); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m)
    for k, e in enumerate(m.PREGUNTAS):
        if isinstance(e, tuple): ANC[m.INICIO + k] = e[6]
UN = {'uno':1,'dos':2,'tres':3,'cuatro':4,'cinco':5,'seis':6,'siete':7,'ocho':8,'nueve':9,'diez':10,'once':11,'doce':12,'trece':13,'catorce':14,'quince':15,
      'dieciseis':16,'diecisiete':17,'dieciocho':18,'diecinueve':19,'veinte':20,'treinta':30,'cuarenta':40,'cincuenta':50,'sesenta':60,'setenta':70,'ochenta':80,'noventa':90,'cien':100,'ciento':100,
      'primero':1,'segundo':2,'tercero':3,'cuarto':4,'quinto':5}
def artnum(a):
    m = re.match(r'Disposición (adicional|transitoria|final) (.+)$', a)
    if m: return {'adicional': 'DA', 'transitoria': 'DT', 'final': 'DF'}[m.group(1)] + ' ' + m.group(2)
    s = strip(a).replace('articulo', '').strip(); bis = ''
    m = re.search(r'\b(bis|ter|quater|quinquies|sexies)$', s)
    if m: bis = ' ' + m.group(1); s = s[:m.start()].strip()
    if re.fullmatch(r'\d+', s): return s + bis
    return str(sum(UN[w] for w in s.replace(' y ', ' ').split())) + bis
def tema(ley, art, defecto):
    m = re.match(r'(\d+)', art); n = int(m.group(1)) if m else 0
    if ley == 'CE':
        if 56 <= n <= 65: return 'I.2'
        if 81 <= n <= 86: return 'III.1'
        if 93 <= n <= 96: return 'I.11'
        if 66 <= n <= 96: return 'I.3'
        if 97 <= n <= 116: return 'I.5'
        if 117 <= n <= 127: return 'I.4'
        if 128 <= n <= 136: return 'V.1'
        if 140 <= n <= 142: return 'I.10'
        if 137 <= n <= 158: return 'I.9'
        return 'I.1'
    if ley == 'LGP': return 'V.1' if 26 <= n <= 31 else 'V.2' if 32 <= n <= 72 else 'V.5' if 78 <= n <= 79 else 'V.3'
    if ley == 'TREBEP':
        if 8 <= n <= 12: return 'IV.3'
        if 55 <= n <= 62: return 'IV.2'
        if 63 <= n <= 68 or 85 <= n <= 92: return 'IV.4'
        if 93 <= n <= 98: return 'IV.6'
        if 14 <= n <= 20 or 31 <= n <= 54 or 78 <= n <= 84: return 'IV.5'
        return 'IV.1'
    if ley == 'L39': return 'II.2' if n in (16, 17, 26, 27, 28) else 'III.1' if 127 <= n <= 133 else 'III.2' if 34 <= n <= 52 else 'III.3'
    if ley == 'L40': return 'III.6' if 32 <= n <= 37 else 'II.3' if 38 <= n <= 46 else 'I.8' if 54 <= n <= 80 else 'III.3'
    if ley == 'LCSP' and (284 <= n <= 297 or n == 312): return 'III.5'
    return defecto
# repetidas revisadas a mano (la comparación automática no las ve: cifras en letra frente a número, etc.)
YA_ESTAN = {'AGE-43001': 'AGE-10028', 'AGE-50024': 'CONV-005'}
NUEVAS = {  # normas que Plazómetro aún no tiene: código, nombre corto, bloque, tema, orden
    'BOE-A-2019-7414': ('CONV', 'IV Convenio único (personal laboral AGE)', 'IV', 'IV.8', 8)}
def main(src, dst, desde):
    h = open(src, encoding='utf-8').read()
    if '<body>\n' in h: h = h[h.index('<body>\n') + 7:]
    if '</body></html>' in h: h = h[:h.rindex('</body></html>')].rstrip() + '\n'
    a = h.index('const BANK = ') + len('const BANK = ')
    bank, end = json.JSONDecoder().raw_decode(h[a:])
    L = bank['laws']; have = {i['id'] for i in bank['items']}
    boe2code = {v['boe']: k for k, v in L.items() if v.get('boe') and not v.get('alias') and not v.get('oficial')}
    alias = {(v['alias'], v['bloque']): k for k, v in L.items() if v.get('alias')}
    porley = {}
    for it in bank['items']: porley.setdefault(it['ley'], []).append(it)
    A = json.load(open(os.path.join(ROOT, 'data', 'bank.json'), encoding='utf-8'))
    nuevas, dup = [], []
    for q in A:
        iid = 'AGE-%d' % q['n']
        if iid in have or q['n'] < desde: continue
        boe = q['u'].split('id=')[1].split('#')[0]
        base = boe2code.get(boe)
        if not base:
            c, corto, bl, tm, orden = NUEVAS[boe]
            if c not in L:
                titulo = next(json.load(open(f, encoding='utf-8'))['titulo'] for f in glob.glob(os.path.join(ROOT, 'data', 'boe', '*.json'))
                              if json.load(open(f, encoding='utf-8')).get('id') == boe)
                L[c] = {'boe': boe, 'corto': corto, 'bloque': bl, 'tema': tm, 'orden': orden, 'nombre': titulo.rstrip('.'), 'titulo': titulo.rstrip('.')}
            base = c
        code = base if L[base]['bloque'] == q['b'] else alias.get((base, q['b']))
        if not code: raise SystemExit('falta un alias para %s en el bloque %s' % (base, q['b']))
        art = artnum(q['a']); r = q['o'][q['c']]
        tq = toks(q['q'])
        tr = toks(r)
        def igual(y):   # mismo enunciado (casi) y misma respuesta (casi): ya la tiene
            ya = toks(str(y.get('t') or y.get('v') or ''))
            jq = len(tq & toks(y['q'])) / max(1, len(tq | toks(y['q'])))
            ja = len(tr & ya) / max(1, len(tr | ya)) if ya and tr else (1 if str(y.get('v')) in r else 0)
            return jq > 0.6 and ja >= 0.5
        rep = next((y for y in porley.get(base, []) + porley.get(code, []) if igual(y)), None) or ({'id': YA_ESTAN[iid]} if iid in YA_ESTAN else None)
        if rep: dup.append((iid, rep['id'])); continue
        hl = ANC.get(q['n'], '')
        if hl.startswith('re:') or hl not in q['cita']: hl = q['cita'][:120]
        it = {'id': iid, 'ley': code, 'art': art, 'q': q['q'], 'cita': q['cita'], 'hl': hl, 'url': q['u'], 'src': 'age',
              'tema': tema(base, art, L[code].get('tema') or L[base].get('tema')), 't': r, 'o': [o for i, o in enumerate(q['o']) if i != q['c']]}
        if q['t'] != 'plazo': it['k'] = 'tst'
        bank['items'].append(it); nuevas.append(it)
    # temas corregidos: TREBEP 8-12 es el tema IV.3 (funcionarios de carrera e interinos)
    ret = 0
    for it in bank['items']:
        if it['ley'] == 'TREBEP' and re.match(r'(8|9|10|11|12)\b', it['art'] or '') and it.get('tema') != 'IV.3': it['tema'] = 'IV.3'; ret += 1
    js = json.dumps(bank, ensure_ascii=False, separators=(',', ':')).replace('</', '<\\/')
    open(dst, 'w', encoding='utf-8').write(h[:a] + js + h[a + end:])
    print(len(nuevas), 'nuevas;', len(dup), 'ya estaban;', ret, 'cambiadas al tema IV.3; total', len(bank['items']))
    for i, y in dup: print('  ya estaba', i, '→', y)
if __name__ == '__main__': main(sys.argv[1], sys.argv[2], int(sys.argv[3]))
