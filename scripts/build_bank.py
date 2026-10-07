"""Valida cada pregunta de data/questions/*.json contra el texto del BOE y genera data/bank.json.
Una pregunta solo entra si su 'cita' aparece literalmente en el artículo indicado."""
import glob, json, os, re, unicodedata
ROOT = os.path.join(os.path.dirname(__file__), '..')
def norm(s):
    s = unicodedata.normalize('NFKC', s or '').lower()
    s = s.replace('“', '"').replace('”', '"').replace('«', '"').replace('»', '"').replace('’', "'").replace('–', '-').replace('—', '-')
    return re.sub(r'\s+', ' ', s).strip()
def main():
    norms = json.load(open(os.path.join(ROOT, 'norms.json'), encoding='utf-8'))
    boe = {}
    for k in norms:
        p = os.path.join(ROOT, 'data', 'boe', k + '.json')
        if os.path.exists(p): boe[k] = json.load(open(p, encoding='utf-8'))
    bank, rej, seen = [], [], set()
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'questions', '*.json'))):
        for q in json.load(open(f, encoding='utf-8')):
            why = None; n = q.get('n')
            try:
                o = q['opciones']
                if not isinstance(n, int) or n < 1000 or n in seen: why = 'n inválido o repetido (usa enteros únicos >= 1000)'
                elif q['bloque'] not in ('I', 'II', 'III', 'IV', 'V', 'VI'): why = 'bloque inválido'
                elif q['tipo'] not in ('test', 'plazo'): why = 'tipo inválido'
                elif len(o) != 4 or len(set(o)) != 4 or q['correcta'] not in range(4): why = 'opciones inválidas'
                elif q['norma'] not in boe: why = 'norma sin texto descargado'
                elif q['articulo'] not in boe[q['norma']]['articulos']: why = 'artículo inexistente en la norma'
                else:
                    a = boe[q['norma']]['articulos'][q['articulo']]
                    c = norm(q['cita'])
                    if len(c) < 25: why = 'cita demasiado corta'
                    elif c not in norm(a['texto']): why = 'la cita NO aparece literalmente en el artículo vigente'
            except KeyError as e: why = 'falta el campo %s' % e
            seen.add(n)
            if why: rej.append((os.path.basename(f), n, why)); continue
            a = boe[q['norma']]['articulos'][q['articulo']]
            bank.append({'n': n, 'b': q['bloque'], 't': q['tipo'], 'l': boe[q['norma']]['nombre'], 'a': a['titulo'].split('.')[0],
                         'q': q['pregunta'], 'o': q['opciones'], 'c': q['correcta'], 'cita': q['cita'],
                         'u': 'https://www.boe.es/buscar/act.php?id=%s#%s' % (boe[q['norma']]['id'], q['articulo']),
                         'f': boe[q['norma']].get('actualizacion', '')})
    json.dump(bank, open(os.path.join(ROOT, 'data', 'bank.json'), 'w', encoding='utf-8'), ensure_ascii=False)
    cnt = {}
    for b in bank: cnt[b['b']] = cnt.get(b['b'], 0) + 1
    L = ['Preguntas verificadas: %d' % len(bank), 'Por bloque: %s' % cnt, 'Rechazadas: %d' % len(rej)] + ['  %s #%s: %s' % r for r in rej]
    open(os.path.join(ROOT, 'data', 'informe.txt'), 'w', encoding='utf-8').write('\n'.join(L))
    print('\n'.join(L))
if __name__ == '__main__': main()
