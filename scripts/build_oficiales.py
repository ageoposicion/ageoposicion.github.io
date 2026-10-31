"""Construye data/oficiales.json: las preguntas oficiales del INAP útiles para el examen (sin informática, anuladas,
repetidas ni las excluidas por haber cambiado la norma), con la respuesta de la plantilla definitiva."""
import json, os, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ETQ = {('2025', 'mod'): 'Examen 2026 (convocatoria 2025)', ('2025', 'lla'): 'Examen 2026 (convocatoria 2025), llamamiento extraordinario',
       ('2024', 'mod'): 'Convocatoria 2024', ('2024', 'lla'): 'Convocatoria 2024, llamamiento extraordinario',
       ('2021-2022', 'ord'): 'Convocatoria 2021-2022', ('2021-2022', 'lla'): 'Convocatoria 2021-2022, llamamiento extraordinario'}
MIN = re.compile(r'Ministr[oa] de Hacienda y Función Pública|Ministerio de Hacienda y Función Pública|Ministr[oa] de Transportes, Movilidad y Agenda Urbana|Ministerio de Asuntos Económicos y Transformación Digital|Ministr[oa] de Asuntos Económicos')
def main():
    R = json.load(open(os.path.join(ROOT, 'data', 'oficiales', 'revision.json'), encoding='utf-8'))
    D = json.load(open(os.path.join(ROOT, 'data', 'oficiales', 'decisiones.json'), encoding='utf-8'))
    urls = {}
    for ln in open(os.path.join(ROOT, 'data', 'inap', 'registro.txt'), encoding='utf-8'):
        p = ln.rstrip('\n').split('\t')
        if len(p) >= 4 and p[1] == 'DESCARGADO' and p[2].lower().startswith('cuestionario'):
            urls[(p[0], 'lla' if 'extraordinario' in p[2].lower() else ('mod' if 'modelo a' in p[2].lower() else 'ord' if 'modelo' not in p[2].lower() else None))] = p[3]
    out, excl = [], []
    for x in R:
        if x['estado'] == 'informatica_vieja': excl.append((x['id'], x['motivo'])); continue
        if x['estado'] not in ('revisar', 'literal_boe', 'informatica_ok'): continue
        dec = D.get(x['id'])
        if dec and dec[0] == 'excluir': excl.append((x['id'], dec[1])); continue
        if not x.get('tema'): excl.append((x['id'], 'sin tema del programa')); continue
        k = (x['examen'], x['modelo'][:3])
        nota = dec[1] if dec and dec[0] == 'nota' else ''
        if MIN.search(x['q'] + ' '.join(x['o']) + (x['ctx'] or '')):
            nota = (nota + ' ' if nota else '') + 'Los nombres de los ministerios son los de la fecha del examen.'
        out.append({'id': x['id'], 'ex': ETQ[k], 'parte': x['parte'], 'n': x['n'], 'q': x['q'], 'o': x['o'], 'r': 'abcd'.index(x['r']),
                    'ctx': x['ctx'], 'tema': x['tema'], 'bloque': x['tema'].split('.')[0], 'nota': nota, 'url': urls.get(k, ''),
                    'prov': x.get('provisional', False),
                    'comprobada': 'pregunta oficial de informática válida para Windows 11 y Microsoft 365' if x['estado'] == 'informatica_ok' else 'literal en el BOE vigente' if x['estado'] == 'literal_boe' else
                                  ('el artículo citado no ha cambiado desde el examen' if x.get('explicito') and not x.get('cambio') else
                                   'respuesta oficial del INAP; sin cambios normativos detectados')})
    json.dump(out, open(os.path.join(ROOT, 'data', 'oficiales.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(len(out), 'preguntas oficiales;', len(excl), 'excluidas'); [print('  excluida', i, m) for i, m in excl if 'versión' not in m]
    import collections; print(sorted(collections.Counter(o['bloque'] for o in out).items()))
if __name__ == '__main__': main()
