"""Descarga el texto consolidado de las normas de norms.json desde la API oficial del BOE.
Fuente de los datos: Agencia Estatal Boletín Oficial del Estado."""
import json, os, re, sys, time, urllib.request
import xml.etree.ElementTree as ET
BASE = 'https://www.boe.es/datosabiertos/api/legislacion-consolidada/id/'
OUT = os.path.join(os.path.dirname(__file__), '..', 'data', 'boe')
def local(t): return t.split('}')[-1]
def get(url):
    err = None
    for i in range(4):
        try:
            rq = urllib.request.Request(url, headers={'Accept': 'application/xml', 'User-Agent': 'AgeOposicion-sync'})
            with urllib.request.urlopen(rq, timeout=60) as r: return r.read()
        except Exception as e:
            err = e; time.sleep(2 * (i + 1))
    raise err
def first(root, name):
    for e in root.iter():
        if local(e.tag) == name and (e.text or '').strip(): return e.text.strip()
def clean(s): return re.sub(r'\s+', ' ', s or '').strip()
def parse_index(data):
    root = ET.fromstring(data); out = []
    for e in root.iter():
        if local(e.tag) != 'bloque': continue
        bid = e.get('id'); tit = e.get('titulo')
        for c in e:
            if local(c.tag) == 'id' and not bid: bid = (c.text or '').strip()
            if local(c.tag) == 'titulo' and not tit: tit = (c.text or '').strip()
        if bid: out.append((bid, clean(tit)))
    return out
def parse_block(data):
    root = ET.fromstring(data)
    vs = [e for e in root.iter() if local(e.tag) == 'version']
    node = vs[-1] if vs else root  # la última versión es la vigente
    ps = [clean(' '.join(p.itertext())) for p in node.iter() if local(p.tag) == 'p']
    txt = clean(' '.join(x for x in ps if x)) or clean(' '.join(node.itertext()))
    return txt, (vs[-1].get('fecha_vigencia') if vs else None)
def main():
    norms = json.load(open(os.path.join(os.path.dirname(__file__), '..', 'norms.json'), encoding='utf-8'))
    os.makedirs(OUT, exist_ok=True); bad = 0
    for key, n in norms.items():
        nid = n['id']; path = os.path.join(OUT, key + '.json')
        try:
            meta = ET.fromstring(get(BASE + nid + '/metadatos'))
            upd = first(meta, 'fecha_actualizacion') or ''; titulo = first(meta, 'titulo') or ''
            old = json.load(open(path, encoding='utf-8')) if os.path.exists(path) else {}
            if old.get('actualizacion') == upd and old.get('articulos') and upd:
                print(key, 'sin cambios'); continue
            try: idx = parse_index(get(BASE + nid + '/texto/indice'))
            except Exception: idx = parse_index(get(BASE + nid + '/texto/%C3%ADndice'))
            arts = {}
            for bid, tit in idx:
                txt, vig = parse_block(get(BASE + nid + '/texto/bloque/' + bid))
                arts[bid] = {'titulo': tit, 'texto': txt, 'vigencia': vig}; time.sleep(0.25)
            json.dump({'clave': key, 'id': nid, 'nombre': n['nombre'], 'titulo': titulo, 'actualizacion': upd, 'articulos': arts},
                      open(path, 'w', encoding='utf-8'), ensure_ascii=False)
            print(key, len(arts), 'bloques', titulo[:70])
        except Exception as e:
            bad += 1; print('ERROR', key, nid, e, file=sys.stderr)
    if bad: print(bad, 'normas con error (revisa el registro)')
if __name__ == '__main__': main()
