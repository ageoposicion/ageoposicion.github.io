"""Asigna bloque y tema del programa (data/programa.md) a cada pregunta oficial según la norma o la materia que cita.
Las de informática (bloque VI) se marcan como tales y no se incorporan hasta que la usuaria lo pida."""
import re
INF = re.compile(r'\b(Access|Excel|Word|Windows|Outlook|Microsoft|Office|365|PowerPoint|navegador|teclado|Explorador de archivos|'
                 r'hoja de cálculo|tabla dinámica|celda|fórmula|macro|carpeta|archivo comprimido|correo electrónico de Outlook|'
                 r'página web|web dinámica|Inteligencia Artificial|Copilot|OneDrive|Teams|SharePoint|URL|HTML|Edge|Chrome)\b', re.I)
def art(q, ley_re):
    m = re.search(r'art[íi]culos?\s+(\d+)(?:\.\d+)*[^.]{0,40}?' + ley_re, q, re.I) or re.search(ley_re + r'[^.]{0,80}?art[íi]culo\s+(\d+)', q, re.I)
    return int(m.group(1)) if m else None
REGLAS = [
 (r'responsabilidad patrimonial', lambda q: 'III.6'),
 (r'Oferta de Empleo Público', lambda q: 'IV.2'),
 (r'Delegad\w* del Gobierno|Subdelegad', lambda q: 'I.8'),
 (r'\bCorona\b|\bel Rey\b|regencia', lambda q: 'I.2'),
 (r'Agenda 2030|Objetivos? de Desarrollo Sostenible|ODS\b|Gobierno Abierto', lambda q: 'I.6'),
 (r'Tratado de (la Unión|Funcionamiento)|Unión Europea|Parlamento Europeo|Comisión Europea|Consejo Europeo', lambda q: 'I.11'),
 (r'Ley 19/2013|transparencia', lambda q: 'I.7'),
 (r'Ley 7/1985|Régimen Local|municipio|provincia|Ayuntamiento|alcalde', lambda q: 'I.10'),
 (r'Ley 50/1997|Ley del Gobierno', lambda q: 'I.5'),
 (r'Orgánica 2/1979|Tribunal Constitucional', lambda q: 'I.1'),
 (r'Orgánica 3/1981|Defensor del Pueblo', lambda q: 'I.1'),
 (r'Orgánica 6/1985|Poder Judicial|Tribunal Supremo', lambda q: 'I.4'),
 (r'Real Decreto 951/2005|cartas? de servicios|quejas y sugerencias|Real Decreto 208/1996|atención al ciudadano|información administrativa', lambda q: 'II.1'),
 (r'Orgánica 3/2018|protección de datos|rectificación de datos|Reglamento \(UE\) 2016/679|delegado de protección', lambda q: 'II.4'),
 (r'Real Decreto 203/2021|sede electrónica|identificación electrónica|firma electrónica|sello electrónico|notificaci\w+ electrónica|Punto de Acceso General', lambda q: 'II.3'),
 (r'Real Decreto 1708/2011|archivo', lambda q: 'II.2'),
 (r'Código Civil|jerarquía normativa', lambda q: 'III.1'),
 (r'Ley 29/1998|contencioso', lambda q: 'III.3'),
 (r'Ley 38/2003|subvenci', lambda q: 'V.6'),
 (r'Orgánica 3/2007|Orgánica 1/2004|Ley 15/2022|Ley 4/2023|LGTBI|personas trans|violencia de género|igualdad efectiva|dependencia|discapacidad', lambda q: 'III.7'),
 (r'Real Decreto 1405/1986|Registro Central de Personal', lambda q: 'IV.1'),
 (r'Real Decreto 365/1995|situaci\w+ administrativas?|excedencia|servicios especiales|servicio activo', lambda q: 'IV.4'),
 (r'Ley 53/1984|incompatibilidad|disciplinari|falta (muy )?grave', lambda q: 'IV.6'),
 (r'Legislativo 4/2000|MUFACE|Clases Pasivas|670/1987', lambda q: 'IV.7'),
 (r'Convenio Único|personal laboral|grupo profesional', lambda q: 'IV.8'),
 (r'Legislativo 8/2015|Seguridad Social|jubilación', lambda q: 'IV.9'),
 (r'Real Decreto 640/1987|a justificar|anticipos? de caja fija', lambda q: 'V.5'),
 (r'Orden de 1 de febrero de 1996|1 de febrero de 1996|documento contable|aprobar el gasto|Documento (RC|A|D|AD|O|OK|ADOK|MC)\b|Tribunal de Cuentas|Orgánica 2/1982|fiscalizaci|Intervención', lambda q: 'V.3'),
 (r'retribuci|nómina|trienio|complemento de destino|complemento específico|Ley 30/1984|grado personal|indemnizaciones por razón del servicio', lambda q: 'V.4'),
 (r'Ley 47/2003|Presupuestari|presupuest|crédito|suplemento|transferencias? de crédito|generación de crédito|remanente', lambda q: (
     'V.1' if (art(q, r'Ley 47/2003') or 0) in range(26, 32) else 'V.2')),
 (r'Real Decreto-ley 6/2023|Real Decreto-ley 6/2023|carrera profesional|provisión de puestos|concurso|libre designación|comisión de servicios|permiso|vacaciones|toma de posesión|tomar posesión|jefatura|promoción interna|funcionarios? en prácticas', lambda q: 'IV.5'),
 (r'Legislativo 5/2015|Estatuto Básico del Empleado Público', lambda q: (
     (lambda a: 'IV.2' if a and 55 <= a <= 62 else 'IV.4' if a and (63 <= a <= 68 or 85 <= a <= 92) else 'IV.6' if a and 93 <= a <= 98
      else 'IV.3' if a in (9, 10) else 'V.4' if a and 21 <= a <= 30 else 'IV.5' if a else 'IV.1')(art(q, r'(?:Legislativo 5/2015|Estatuto Básico)')))),
 (r'Ley 40/2015|Régimen Jurídico del Sector Público|convenio', lambda q: (
     (lambda a: 'I.8' if a and 54 <= a <= 80 or not a and re.search(r'Subsecretari|Secretari\w+ de Estado|Directores? Generales|Ministros?\b', q) else 'II.3' if a and 38 <= a <= 46 else 'III.6' if a and 32 <= a <= 37 else 'III.3')(art(q, r'Ley 40/2015')))),
 (r'Ley 39/2015|Procedimiento Administrativo Común|recurso|plazo|notifica|silencio|caducidad|desistid|subsana|lesividad|nulidad|anulab|revis\w+ de oficio', lambda q: (
     (lambda a: 'II.2' if a in (16, 17, 26, 27, 28) else 'III.1' if a and 127 <= a <= 133 else 'III.2' if a and 34 <= a <= 52 else 'III.3')(art(q, r'Ley 39/2015')))),
 (r'Constitución|\bCE\b', lambda q: (
     (lambda a: 'I.2' if a and 56 <= a <= 65 else 'III.1' if a and 81 <= a <= 86 else 'I.11' if a and 93 <= a <= 96 else 'I.3' if a and 66 <= a <= 96
      else 'I.5' if a and 97 <= a <= 116 else 'I.4' if a and 117 <= a <= 127 else 'V.1' if a and 128 <= a <= 136 else 'I.10' if a and 140 <= a <= 142
      else 'I.9' if a and 137 <= a <= 158 else 'I.1')(art(q, r'(?:Constitución|\bCE\b)')))),
 (r'Ley 9/2017|contrat|licitaci|adjudica|perfil del contratante|valor estimado|garantía definitiva', lambda q: 'III.4'),
  (r'decreto-ley|decreto legislativo|potestad reglamentaria|reglamento', lambda q: 'III.1'),
]
NORMA = re.compile(r'\bCE\b|Ley(?: Orgánica)? \d+/\d{4}|Real Decreto(?:[- ]ley| Legislativo)? \d+/\d{4}|Constitución|Código Civil|Tratado|Orden (?:del|de \d)|Convenio Único|Agenda 2030|Estatuto Básico', re.I)
def _pasada(texto, solo_norma):
    for pat, f in REGLAS:
        m = re.search(pat, texto, re.I)
        if m and (not solo_norma or NORMA.search(m.group(0))):
            return f(texto)
def tema(q, opts='', ctx=''):
    """Primero la norma citada en el enunciado; después la materia del enunciado; luego las opciones y el caso."""
    for texto, solo in ((q, True), (q, False), (opts, True), (opts, False), (ctx, False)):
        if texto:
            t = _pasada(texto, solo)
            if t: return t
    return None
def es_informatica(x):
    return x['parte'] == 'primera' and 41 <= x['n'] <= 70 or bool(INF.search(x['q'] + ' ' + ' '.join(x['o'])))
