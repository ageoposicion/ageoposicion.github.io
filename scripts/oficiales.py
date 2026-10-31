"""Extrae las preguntas de los exámenes oficiales del INAP (data/inap/<conv>/cuestionario-*.txt) con la respuesta de la
plantilla DEFINITIVA, y comprueba que cada enunciado y cada opción están literalmente en el cuestionario oficial.
Uso: python scripts/oficiales.py   →  data/oficiales/<examen>.json"""
import glob, json, os, re, sys, unicodedata
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
PIE = re.compile(r'^\s*\d{4}\s*-\s*ADVO.*Página \d+ de \d+\s*$|^\s*Página \d+ de \d+\s*$')
def norm(s):
    s = unicodedata.normalize('NFKC', s).lower().replace('“', '"').replace('”', '"').replace('’', "'")
    return re.sub(r'\s+', '', s)
def secciones(txt):
    """Divide el cuestionario en bloques: primera parte, reserva, supuesto I (+reserva), supuesto II (+reserva)."""
    out, cur, nom = [], [], 'primera'
    ctx = {}
    for ln in txt.splitlines():
        if PIE.match(ln): continue
        s = ln.strip()
        if s == 'PRIMERA PARTE': nom = 'primera'; continue
        if re.fullmatch(r'Preguntas de reserva', s, re.I):
            out.append((nom, cur)); cur = []; nom = nom + '-reserva'; continue
        m = re.fullmatch(r'SUPUESTO (I+|\d+)', s)
        if m:
            out.append((nom, cur)); cur = []; nom = 'supuesto ' + m.group(1); continue
        cur.append(ln)
    out.append((nom, cur))
    return [(n, c) for n, c in out if any(x.strip() for x in c)]
QN = re.compile(r'^\s{0,8}(\d{1,2})\.\s+(\S.*)$')
OPT = re.compile(r'(?:(?<=^)|(?<=\s))([a-d])\)\s*')
def preguntas(lines):
    qs, cur, intro = [], None, []
    for ln in lines:
        if not ln.strip(): continue
        m = QN.match(ln)
        # una pregunta empieza por 1 y luego va en orden (evita líneas del caso que empiezan por «16. …»)
        if m and (cur is None and m.group(1) == '1' or cur is not None and len(cur['o']) == 4 and int(m.group(1)) == cur['n'] + 1):
            cur = {'n': int(m.group(1)), 'q': m.group(2).strip(), 'o': {}, 'last': None}; qs.append(cur); continue
        if cur is None: intro.append(ln.strip()); continue
        segs = [(mm.group(1), mm.start(), mm.end()) for mm in OPT.finditer(ln)]
        # una letra de opción solo cuenta si es la siguiente que falta (evita «a)» dentro de un texto)
        val = []
        for L, s0, e0 in segs:
            esperada = 'abcd'[len(cur['o']) + len(val)] if len(cur['o']) + len(val) < 4 else None
            if L == esperada: val.append((L, s0, e0))
        if val:
            for k, (L, s0, e0) in enumerate(val):
                fin = val[k + 1][1] if k + 1 < len(val) else len(ln)
                cur['o'][L] = ln[e0:fin].strip(); cur['last'] = L
        elif cur['last']: cur['o'][cur['last']] += ' ' + ln.strip()
        else: cur['q'] += ' ' + ln.strip()
    return intro, qs
def plantilla(txt):
    """Columna izquierda: primera parte. Columna derecha, por orden: reserva, Supuesto I, reserva, Supuesto II, reserva."""
    izq, der = {}, []
    sec = None
    for ln in txt.splitlines():
        partes = re.split(r'\s{3,}', ln.strip())
        for p in partes:
            m = re.fullmatch(r'(\d{1,2})\.\s+([a-d]|ANULADA)', p.strip())
            if m:
                if sec is None and int(m.group(1)) not in izq and (not der or len(der[-1][1]) == 0 or p is partes[0] and len(partes) > 1):
                    pass
            # se procesa abajo
        cols = [(n, 'ANULADA' if r.lower()=='anulada' else r.lower()) for n, r in re.findall(r'(\d{1,2})\.\s+([a-dA-D]|ANULADA|Anulada|anulada)\b', ln)]
        heads = re.findall(r'Preguntas de reserva|Supuesto I+|Supuesto \d', ln)
        if len(cols) == 2:
            izq[int(cols[0][0])] = cols[0][1]; der[-1][1][int(cols[1][0])] = cols[1][1]
        elif len(cols) == 1:
            pos = ln.index(cols[0][0] + '.')
            if pos < 20: izq[int(cols[0][0])] = cols[0][1]
            else: der[-1][1][int(cols[0][0])] = cols[0][1]
        for h in heads:
            if h.startswith('Preguntas'): der.append(('reserva', {}))
            else: der.append((h, {}))
    secs = {'primera': izq}
    prev = 'primera'
    for h, d in der:
        if h == 'reserva': secs[prev + '-reserva'] = d
        else: prev = 'supuesto ' + h.split()[1]; secs[prev] = d
    return secs
def main():
    errores = 0
    for cuest in sorted(glob.glob(os.path.join(ROOT, 'data', 'inap', '*', 'cuestionario*.txt'))):
        d = os.path.dirname(cuest); conv = os.path.basename(d)
        if conv < '2021': continue   # solo las tres últimas convocatorias
        mod = os.path.basename(cuest)[len('cuestionario'):-4].split('__')[0].strip('-') or 'ordinario'
        if mod == 'modelo-b': continue   # mismas preguntas que el modelo A en otro orden
        ext = 'extraordinario' in mod
        def cabecera(p): return ' '.join(open(p, encoding='utf-8').read().split()[:30]).upper()
        def casa(p):
            # la plantilla se reconoce por su título interno (y por su nombre): extraordinario sí/no y modelo
            b = os.path.basename(p).lower(); h = cabecera(p)
            es_ext = 'extraordinari' in b or 'EXTRAORDINARIO' in h
            if es_ext != ext: return False
            if mod.startswith('modelo'):
                return ('MODELO ' + mod[-1].upper()) in h
            return 'MODELO' not in h
        pl = [p for p in glob.glob(os.path.join(d, 'plantilla-definitiva*.txt')) if casa(p)]
        prov = [p for p in glob.glob(os.path.join(d, 'plantilla-provisional*.txt')) if casa(p)]
        provisional = False
        if not pl:   # si el INAP no ha publicado la definitiva, la provisional (se marca como tal)
            pl = prov; provisional = True
        if len(pl) != 1: print('sin plantilla única para', cuest, pl); errores += 1; continue
        if not provisional and len(prov) == 1:
            # control: la definitiva solo corrige unas pocas respuestas de la provisional
            A, B = plantilla(open(pl[0], encoding='utf-8').read()), plantilla(open(prov[0], encoding='utf-8').read())
            tot = dif = 0
            for sec in A:
                for n, r in A[sec].items():
                    if n in B.get(sec, {}): tot += 1; dif += (B[sec][n] != r and r != 'ANULADA')
            if not tot or dif > 0.1 * tot: print('ERROR plantillas definitiva y provisional no casan', cuest, dif, tot); errores += 1; continue
        txt = open(cuest, encoding='utf-8').read(); P = plantilla(open(pl[0], encoding='utf-8').read())
        out, ctxs = [], {}
        for nom, lines in secciones(txt):
            intro, qs = preguntas(lines)
            if nom.startswith('supuesto') and not nom.endswith('reserva'): ctxs[nom] = ' '.join(intro).strip()
            ctx = ctxs.get(nom.replace('-reserva', '')) if nom.startswith('supuesto') else None   # las de reserva usan el mismo caso
            for q in qs:
                r = P.get(nom, {}).get(q['n'])
                ok = len(q['o']) == 4 and r is not None
                if not ok:
                    print('ERROR', conv, mod, nom, q['n'], 'opciones', list(q['o']), 'resp', r); errores += 1; continue
                for t in [q['q']] + list(q['o'].values()):
                    if norm(t) not in norm(txt): print('ERROR texto no literal', conv, mod, nom, q['n'], t[:60]); errores += 1
                out.append({'examen': conv, 'modelo': mod, 'parte': nom, 'n': q['n'], 'q': q['q'],
                            'o': [q['o'][L] for L in 'abcd'], 'r': r, 'ctx': ctx, 'provisional': provisional})
            for n in P.get(nom, {}):
                if n not in {q['n'] for q in qs}: print('ERROR falta en cuestionario', conv, mod, nom, n); errores += 1
        fn = os.path.join(ROOT, 'data', 'oficiales', '%s-%s.json' % (conv, mod))
        json.dump(out, open(fn, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
        print(conv, mod, len(out), 'preguntas', {k: sum(1 for x in out if x['parte'] == k) for k in dict.fromkeys(x['parte'] for x in out)})
    if errores: print(errores, 'errores'); sys.exit(1)
if __name__ == '__main__': main()
