"""Para cada pregunta oficial a revisar, localiza el artículo del BOE en que se apoya y compara la fecha de su última
modificación con la del examen: si el artículo cambió después del examen, la pregunta se revisa a mano."""
import glob, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from vigencia_oficiales import LEYES, norm
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
# fecha a partir de la cual pudo celebrarse cada examen (cota prudente: si el artículo cambió después, se revisa)
EXAMEN = {('2025', 'mod'): '20260523', ('2025', 'lla'): '20260601', ('2024', 'mod'): '20250101', ('2024', 'lla'): '20250101',
          ('2021-2022', 'ord'): '20230101', ('2021-2022', 'lla'): '20230101'}
STOP = set('para como sera seran esta este estos estas cuando sobre entre desde hasta donde todo toda todos todas otro otra otros otras puede podra podran debera deberan dicho dicha caso casos tendra tendran cual cuales sino solo tanto mismo misma'.split())
ART = {}
for f in glob.glob(os.path.join(ROOT, 'data', 'boe', '*.json')):
    k = os.path.basename(f)[:-5]
    for a, v in json.load(open(f, encoding='utf-8'))['articulos'].items():
        m = re.match(r'Artículo (\d+)', v['titulo'])
        ART.setdefault(k, []).append((a, int(m.group(1)) if m else None, v['titulo'], v.get('vigencia') or '', set(norm(v['texto']).split())))
def main():
    d = json.load(open(os.path.join(ROOT, 'data', 'oficiales', 'revision.json'), encoding='utf-8'))
    for x in d:
        if x['estado'] not in ('revisar', 'literal_boe'): continue
        ex = EXAMEN[(x['examen'], x['modelo'][:3])]
        texto = x['q'] + ' ' + ' '.join(x['o'])
        leyes = [k for p, k in LEYES if re.search(p, x['q'] + ' ' + (x['ctx'] or ''))] or list(ART)
        m = re.search(r'art[íi]culos?\s+(\d+)', x['q'])
        tk = [w for w in norm(texto).split() if (len(w) > 3 or w.isdigit()) and w not in STOP]
        cands = []
        for k in leyes:
            for a, n, tit, vig, toks in ART.get(k, []):
                if m and n is not None and n == int(m.group(1)) and k == leyes[0]: cands.append((10**6, k, a, tit, vig)); continue
                cands.append((sum(w in toks for w in tk), k, a, tit, vig))
        cands.sort(reverse=True)
        sc, k, a, tit, vig = cands[0]
        x['apoyo'] = '%s %s' % (k, tit); x['vig_art'] = vig; x['fecha_examen'] = ex
        x['cambio'] = bool(vig and vig > ex); x['explicito'] = sc == 10**6
    json.dump(d, open(os.path.join(ROOT, 'data', 'oficiales', 'revision.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    r = [x for x in d if x['estado'] in ('revisar', 'literal_boe')]
    print(len(r), 'a comprobar;', sum(x['cambio'] for x in r), 'con el artículo modificado después del examen')
if __name__ == '__main__': main()
