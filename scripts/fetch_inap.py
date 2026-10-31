"""Descarga del INAP (sede.inap.gob.es) los cuestionarios y plantillas oficiales de los exámenes del Cuerpo General
Administrativo (C1), ingreso libre, de las convocatorias de data/inap/fuentes.json. Guarda cada PDF y su texto en
data/inap/<convocatoria>/ y un registro de todos los enlaces vistos en data/inap/registro.txt."""
import html, json, os, re, subprocess, sys, time, urllib.parse, urllib.request
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
OUT = os.path.join(ROOT, 'data', 'inap')
UA = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36',
      'Accept-Language': 'es-ES,es;q=0.9'}
CLAVE = re.compile(r'cuestionario|plantilla|ejercicio|examen|modelo|respuesta|supuesto', re.I)
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
def nombre(txt, url):
    n = re.sub(r'[^a-z0-9]+', '-', (txt or os.path.basename(urllib.parse.urlparse(url).path)).lower()).strip('-')
    return (n or 'documento')[:80]
def main():
    F = json.load(open(os.path.join(OUT, 'fuentes.json'), encoding='utf-8'))
    log, bad = [], 0
    for conv, page in F['paginas'].items():
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
                es_doc = re.search(r'\.pdf($|\?)|/documents/|/documentos/|download', u, re.I)
                if es_doc and CLAVE.search(t + ' ' + u): docs.setdefault(u, t)
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
