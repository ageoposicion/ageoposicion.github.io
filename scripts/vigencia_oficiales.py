"""Une las preguntas oficiales (data/oficiales/*.json), quita las de informática (bloque VI), las anuladas y las repetidas,
asigna tema y comprueba la respuesta oficial contra el texto VIGENTE del BOE (data/boe) cuando la pregunta cita una norma
descargada. Escribe data/oficiales/revision.json con lo que hay que revisar a mano."""
import glob, json, os, re, sys, unicodedata
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from clasifica_oficiales import tema, es_informatica
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
LEYES = [(r'Constituci[óo]n|\bCE\b', 'CE'), (r'Ley 39/2015', 'L39'), (r'Ley 40/2015', 'L40'), (r'Legislativo 5/2015|Estatuto B[áa]sico', 'TREBEP'),
 (r'Ley 9/2017|Contratos del Sector P', 'LCSP'), (r'Ley 19/2013', 'L19'), (r'Ley 47/2003|General Presupuestaria', 'LGP'), (r'Org[áa]nica 3/2018', 'LOPDGDD'),
 (r'Ley 38/2003|General de Subvenciones', 'LGS'), (r'Ley 7/1985', 'LBRL'), (r'Ley 50/1997|Ley del Gobierno', 'LGOB'), (r'Ley 29/1998', 'LJCA'),
 (r'Org[áa]nica 3/2007', 'LOI'), (r'Org[áa]nica 1/2004', 'LOVG'), (r'Ley 15/2022', 'LIGT'), (r'Ley 4/2023', 'LTRANS'), (r'Ley 39/2006', 'LDEP'),
 (r'Ley 53/1984', 'LINC'), (r'Legislativo 4/2000', 'MUFACE'), (r'Legislativo 670/1987', 'LCLP'), (r'Legislativo 8/2015', 'LGSS'),
 (r'Org[áa]nica 6/1985', 'LOPJ'), (r'Org[áa]nica 2/1979', 'LOTC'), (r'Org[áa]nica 3/1981', 'LODP'), (r'Org[áa]nica 4/1981', 'LOAES'),
 (r'Real Decreto 203/2021', 'RDAE'), (r'Real Decreto 208/1996', 'RDINF'), (r'Real Decreto 1708/2011', 'RDARCH')]
def norm(s):
    s = ''.join(c for c in unicodedata.normalize('NFD', s.lower()) if unicodedata.category(c) != 'Mn')
    return re.sub(r'[^a-z0-9]+', ' ', s).strip()
BOE = {}
def texto(k):
    if k not in BOE:
        d = json.load(open(os.path.join(ROOT, 'data', 'boe', k + '.json'), encoding='utf-8'))['articulos']
        BOE[k] = norm(' '.join(v['texto'] for v in d.values()))
    return BOE[k]
def main():
    todas, vistos = [], {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'data', 'oficiales', '20*.json'))):
        for x in json.load(open(f, encoding='utf-8')):
            x['id'] = 'OF-%s-%s-%s-%d' % (x['examen'], x['modelo'][:3], re.sub(r'[^a-zI]+', '', x['parte']), x['n'])
            todas.append(x)
    out, stats = [], {}
    for x in todas:
        if x['r'] == 'ANULADA': est = 'anulada'
        elif es_informatica(x): est = 'informatica'
        else:
            clave = norm(x['q'] + ' ' + x['o']['abcd'.index(x['r'])])
            if clave in vistos and not x['ctx']: est = 'repetida'; x['igual_a'] = vistos[clave]
            else:
                vistos.setdefault(clave, x['id'])
                x['tema'] = tema(x['q'], ' '.join(x['o']), x['ctx'] or '')
                ley = next((k for p, k in LEYES if re.search(p, x['q'])), None)
                resp = norm(x['o']['abcd'.index(x['r'])])
                if ley:
                    x['ley'] = ley
                    est = 'literal_boe' if len(resp) > 12 and resp in texto(ley) else 'revisar'
                else: est = 'revisar'
        x['estado'] = est; stats[est] = stats.get(est, 0) + 1
        out.append(x)
    json.dump(out, open(os.path.join(ROOT, 'data', 'oficiales', 'revision.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(stats)
if __name__ == '__main__': main()
