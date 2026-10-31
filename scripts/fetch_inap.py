"""Descarga del INAP (sede.inap.gob.es) los cuestionarios y plantillas oficiales de los exámenes del Cuerpo General
Administrativo (C1), ingreso libre, de las convocatorias de data/inap/fuentes.json. Guarda cada PDF y su texto en
data/inap/<convocatoria>/ y un registro de todos los enlaces vistos en data/inap/registro.txt."""
import html, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'data', 'inap')
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
      'Accept-Language': 'es-ES,es;q=0.9'}
CLAVE = re.compile(r'cuestionario|plantilla|respuestas', re.I)
DOC = re.compile(r'\.pdf($|\?)|/documents/|/documentos/|download|/files/', re.I)
def get(url):
    err = None
    for i in range(3):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read(), r.headers.get('Content-Type', '')
        except Exception as e:
            err = e; time.sleep(3 * (i + 1))
    raise err
def enlaces(base, data):
    s = data.decode('utf-8', 'replace')
    for m in re.finditer(r'<a\b[^>]*href="([^"#]+)"[^>]*>(.*?)</a>', s, re.S | re.I):
        txt = re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', m.group(2)))).strip()
        yield urllib.parse.urljoin(base, html.unescape(m.group(1))), txt
def slug(t): return re.sub(r'[^a-z0-9]+', '-', t.lower()).strip('-')
def nombre(txt, url):
    # el texto del enlace y el nombre del archivo en el INAP: dos enlaces con el mismo texto no se pisan
    base = os.path.splitext(urllib.parse.unquote(os.path.basename(urllib.parse.urlparse(url).path.rstrip('/'))))[0]
    if re.fullmatch(r'[0-9a-f-]{30,}', base):   # enlaces /documents/…/<archivo>.pdf/<uuid>
        base = os.path.splitext(urllib.parse.unquote(urllib.parse.urlparse(url).path.rstrip('/').split('/')[-2]))[0]
    return ((slug(txt)[:60] or 'documento') + '__' + slug(base)[:50]).strip('-')
def main():
    F = json.load(open(os.path.join(OUT, 'fuentes.json'), encoding='utf-8'))
    log, bad = [], 0
    trabajos = list(F['paginas'].items())
    # índices generales del cuerpo: subpáginas de convocatorias de ingreso libre (no promoción interna)
    for nom, idx in F.get('indices', {}).items():
        try:
            d0, _ = get(idx)
        except Exception as e:
            log.append('%s\tERROR índice\t%s\t%s' % (nom, idx, e)); bad += 1; continue
        nivel = [(idx, d0)]
        vistos = {idx}
        for prof in range(2):
            sig = []
            for base, d in nivel:
                for u, t in enlaces(base, d):
                    log.append('%s\tíndice\t%s\t%s' % (nom, t, u))
                    host = urllib.parse.urlparse(u).netloc
                    if u in vistos or not host.endswith('inap.es') and not host.endswith('inap.gob.es'): continue
                    if DOC.search(u): continue
                    lu = (u + ' ' + t).lower()
                    if 'administrativo' in lu and 'promoci' not in lu and ('libre' in lu or 'convocatoria' in lu or 'oep' in lu):
                        vistos.add(u)
                        try: sig.append((u, get(u)[0]))
                        except Exception as e: log.append('%s\tERROR subpágina\t%s\t%s' % (nom, u, e))
            for u, _ in sig:
                m = re.findall(r'(20\d\d)', u)
                trabajos.append(((m[-1] if m else 'otros') + '-' + nom, u))
            nivel = sig
    hechos = set(u for _, u in F['paginas'].items())
    for conv, page in trabajos:
        if conv in F['paginas'] and page != F['paginas'][conv]: continue
        if page in hechos and conv not in F['paginas']: continue
        hechos.add(page)
        try:
            data, _ = get(page)
        except Exception as e:
            log.append('%s\tERROR página\t%s\t%s' % (conv, page, e)); bad += 1; continue
        os.makedirs(os.path.join(OUT, conv), exist_ok=True)
        vistos = set()
        # la página y, un nivel más, las subpáginas del mismo proceso (p. ej. «ejercicio único»)
        cola = [(page, data)]
        for u, t in list(enlaces(page, data)):
            if u.startswith(page) and u != page and u not in vistos:
                vistos.add(u)
                try: cola.append((u, get(u)[0]))
                except Exception as e: log.append('%s\tERROR subpágina\t%s\t%s' % (conv, u, e))
        docs = {}
        for base, d in cola:
            for u, t in enlaces(base, d):
                log.append('%s\tenlace\t%s\t%s' % (conv, t, u))
                if DOC.search(u) and CLAVE.search(t + ' ' + os.path.basename(u)): docs.setdefault(u, t)
        for u, t in docs.items():
            try:
                pdf, ct = get(u)
                if not pdf.startswith(b'%PDF'):
                    log.append('%s\tno es PDF\t%s\t%s' % (conv, t, u)); continue
                fn = os.path.join(OUT, conv, nombre(t, u))
                open(fn + '.pdf', 'wb').write(pdf)
                subprocess.run(['pdftotext', '-layout', fn + '.pdf', fn + '.txt'], check=False)
                log.append('%s\tDESCARGADO\t%s\t%s\t%d bytes' % (conv, t, u, len(pdf)))
                time.sleep(1)
            except Exception as e:
                log.append('%s\tERROR documento\t%s\t%s\t%s' % (conv, t, u, e)); bad += 1
    open(os.path.join(OUT, 'registro.txt'), 'w', encoding='utf-8').write('\n'.join(log) + '\n')
    print('\n'.join(l for l in log if 'DESCARGADO' in l or 'ERROR' in l))
    if bad: print(bad, 'errores (ver data/inap/registro.txt)', file=sys.stderr)
if __name__ == '__main__': main()
