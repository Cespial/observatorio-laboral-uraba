"""
Shared ETL functions for the Observatorio Laboral.
Extracted from 12_sync_empleo_incremental.py for testability and reuse.
"""
import hashlib
import re
import unicodedata

MUNICIPIO_DANE = {
    "apartadó": "05045", "apartado": "05045",
    "turbo": "05837",
    "carepa": "05147",
    "chigorodó": "05172", "chigorodo": "05172",
    "necoclí": "05490", "necocli": "05490",
    "arboletes": "05051",
    "san pedro de urabá": "05665", "san pedro": "05665",
    "san juan de urabá": "05659", "san juan": "05659",
    "mutatá": "05480", "mutata": "05480",
    "murindó": "05475", "murindo": "05475",
    "vigía del fuerte": "05873", "vigia del fuerte": "05873", "vigia": "05873",
    "urabá": None, "uraba": None,
}

SKILL_PATTERNS = [
    (r'\bexcel\b', 'Excel'),
    (r'\bword\b', 'Word'),
    (r'\bsap\b', 'SAP'),
    (r'\bpython\b', 'Python'),
    (r'\bsql\b', 'SQL'),
    (r'\bingl[eé]s\b', 'Inglés'),
    (r'\bcontabilidad\b', 'Contabilidad'),
    (r'\bfacturaci[oó]n\b', 'Facturación'),
    (r'\batenci[oó]n al cliente\b', 'Atención al cliente'),
    (r'\bservicio al cliente\b', 'Servicio al cliente'),
    (r'\bventas\b', 'Ventas'),
    (r'\bliderazgo\b', 'Liderazgo'),
    (r'\btrabajo en equipo\b', 'Trabajo en equipo'),
    (r'\bcomunicaci[oó]n\b', 'Comunicación'),
    (r'\bnegociaci[oó]n\b', 'Negociación'),
    (r'\bmanejo de personal\b', 'Manejo de personal'),
    (r'\blogística\b|\blogistica\b', 'Logística'),
    (r'\bpresupuesto\b', 'Presupuesto'),
    (r'\bmarketing\b|\bmercadeo\b', 'Marketing'),
    (r'\bredes sociales\b|\bsocial media\b', 'Redes sociales'),
    (r'\blicencia\s+(de\s+)?conducci[oó]n\b|\blicencia\s+[bc]\d\b', 'Licencia de conducción'),
    (r'\bmoto\b', 'Moto propia'),
    (r'\bsalud ocupacional\b|\bsst\b|\bseguridad y salud\b', 'SST'),
    (r'\bagricultura\b|\bagrícola\b|\bagricola\b|\bcultivo\b', 'Agricultura'),
    (r'\bbanano\b|\bplátano\b|\bplatano\b', 'Cultivo banano/plátano'),
    (r'\bglobalg\.?a\.?p\.?\b|\brainforest\b', 'Certificaciones agrícolas'),
    (r'\benfermería\b|\benfermeria\b|\benfermero\b', 'Enfermería'),
    (r'\bmedicina\b|\bmédico\b|\bmedico\b', 'Medicina'),
    (r'\bpedagog\b|\beducaci[oó]n\b|\bdocente\b|\bprofesor\b', 'Educación'),
    (r'\bconstrucci[oó]n\b|\bobra\b|\bingeniería civil\b', 'Construcción'),
    (r'\belectricidad\b|\beléctric\b|\belectric\b', 'Electricidad'),
    (r'\bmecánic\b|\bmecanica\b', 'Mecánica'),
    (r'\bsoldadura\b', 'Soldadura'),
    (r'\bpower\s*bi\b', 'Power BI'),
    (r'\btableau\b', 'Tableau'),
    (r'\berp\b', 'ERP'),
    (r'\bcrm\b', 'CRM'),
    (r'\bautocad\b|\bauto\s*cad\b', 'AutoCAD'),
    (r'\bphotoshop\b|\billustrator\b|\bdise[nñ]o\b', 'Diseno grafico'),
    (r'\bsiigo\b|\bworld\s*office\b|\bhelisa\b', 'Software contable'),
    (r'\bplaneaci[oó]n\b|\bplanificaci[oó]n\b', 'Planeacion'),
    (r'\bgesti[oó]n\b', 'Gestion'),
    (r'\binventario\b', 'Inventarios'),
    (r'\bcaja\b|\bmanejo.*efectivo\b', 'Manejo de caja'),
    (r'\bcobranza\b|\bcartera\b', 'Cobranza/Cartera'),
    (r'\bimportaci[oó]n\b|\bexportaci[oó]n\b|\bcomercio\s+exterior\b', 'Comercio exterior'),
    (r'\bcalidad\b|\biso\b|\bnormas?\b', 'Gestion de calidad'),
    (r'\bprimeros\s+auxilios\b|\bbrigad\b', 'Primeros auxilios'),
    (r'\bfitosanitar\b|\bplagas?\b|\bfumig\b', 'Fitosanidad'),
    (r'\bempaque\b|\bembalaje\b|\bempacad\b', 'Empaque'),
    (r'\bcosecha\b|\brecolec\b|\bcorte\b.*\bbanano\b', 'Cosecha'),
    (r'\briego\b|\bdrenaje\b|\bfertirriego\b', 'Riego y drenaje'),
    (r'\bcertific\b.*\borganic\b|\bglobal\s*gap\b', 'Certificacion organica'),
    (r'\bmontacarga\b', 'Montacargas'),
    (r'\bveh[ií]culo\s+propio\b', 'Vehiculo propio'),
    (r'\bcadena\s+de\s+fr[ií]o\b', 'Cadena de frio'),
    (r'\bBPM\b|\bbuenas\s+pr[aá]cticas\b', 'BPM'),
    (r'\bHACCP\b', 'HACCP'),
]

EXPERIENCIA_PATTERNS = [
    (r'sin\s+experiencia|no\s+requiere\s+experiencia|primera\s+vez', 'Sin experiencia'),
    (r'1\s*a[nñ]o|12\s*meses|un\s*\(?\d?\)?\s*a[nñ]o', '1 ano'),
    (r'2\s*a[nñ]os?|24\s*meses', '2 anos'),
    (r'3\s*a[nñ]os?|36\s*meses', '3 anos'),
    (r'[45]\s*a[nñ]os?', '4-5 anos'),
    (r'[6-9]\s*a[nñ]os?|\d{2,}\s*a[nñ]os?|m[aá]s\s+de\s+5', '5+ anos'),
]

CONTRATO_PATTERNS = [
    (r'indefinido|fijo\s+indefinido|planta', 'Indefinido'),
    (r'fijo|t[eé]rmino\s+fijo|temporal', 'Fijo'),
    (r'prestaci[oó]n\s+de\s+servicios|contratista|independiente|freelance', 'Prestacion de servicios'),
    (r'obra\s+o?\s*labor|obra\s+civil|por\s+obra', 'Obra o labor'),
    (r'aprendiz|sena|practicante|pr[aá]ctica', 'Aprendizaje'),
]

EDUCACION_PATTERNS = [
    (r'bachiller|secundaria|11[°º]', 'Bachiller'),
    (r't[eé]cnic[oa]', 'Tecnico'),
    (r'tecn[oó]log[oa]', 'Tecnologo'),
    (r'profesional|universitari[oa]|ingenier[oa]|abogad[oa]|licenciad[oa]', 'Profesional'),
    (r'especializaci[oó]n|especialista|postgrado|posgrado', 'Especializacion'),
    (r'maestr[ií]a|magister|m[aá]ster', 'Maestria'),
]

MODALIDAD_PATTERNS = [
    (r'remoto|teletrabajo|home\s*office|desde\s+casa|virtual', 'Remoto'),
    (r'h[ií]brido|mixto|alterno', 'Hibrido'),
    (r'presencial|en\s+sitio|campo|planta', 'Presencial'),
]

SECTOR_PATTERNS = [
    (r'\bagrícol|\bagricol|\bbanano|\bplátano|\bcultivo|\bagrono|\bfinca\b', 'Agroindustria'),
    (r'\bsalud|\benferm|\bmédic|\bhospital|\bIPS\b|\bEPS\b|\bfarmac', 'Salud'),
    (r'\beduca|\bdocente|\bprofesor|\bcolegio|\binstruct', 'Educación'),
    (r'\bcontabl|\bcontador|\bfinanci|\baudit|\btribut|\bimpuest', 'Contabilidad y Finanzas'),
    (r'\bvend|\bcomercial|\btienda|\bmercad|\bTAT\b', 'Comercio y Ventas'),
    (r'\bconstrucc|\bobra|\bingenier.*civil|\bmaestro.*obra|\barquitect', 'Construcción'),
    (r'\btecnolog|\bsistema|\bdesarroll|\bsoftware|\bIT\b|\bprogramad', 'Tecnología'),
    (r'\btransport|\blogíst|\bconductor|\bchof', 'Transporte y Logística'),
    (r'\bseguridad|\bvigilant|\bcustodia|\bguarda', 'Seguridad'),
    (r'\bturism|\bhotel|\brestaurant|\bcocin|\bchef\b|\bmesero', 'Turismo y Gastronomía'),
    (r'\badministrativ|\bsecretari|\brecepcion|\basistente.*admin', 'Administrativo'),
    (r'\bderecho|\bjuríd|\babogad|\blegal', 'Jurídico'),
    (r'\brecursos humanos|\btalento humano|\bRRHH\b|\bnómin', 'Recursos Humanos'),
    (r'\bmantenimiento|\bmecánic|\belectric|\btécnic', 'Mantenimiento'),
]


def _normalize(text: str) -> str:
    """Normalize text: lowercase and strip accents for comparison."""
    if not text:
        return ""
    text = text.lower().strip()
    nfkd = unicodedata.normalize("NFKD", text)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def compute_dedup_hash(titulo: str, empresa: str, municipio: str) -> str:
    """Compute a deduplication hash based on normalized title + company + municipality."""
    parts = [_normalize(titulo), _normalize(empresa or ""), _normalize(municipio or "")]
    canonical = "|".join(parts)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()[:16]


def extract_skills(titulo, descripcion):
    combined = f"{titulo or ''} {descripcion or ''}".lower()
    seen = set()
    result = []
    for pattern, name in SKILL_PATTERNS:
        if name not in seen and re.search(pattern, combined, re.IGNORECASE):
            seen.add(name)
            result.append(name)
    return result


def classify_sector(titulo, descripcion):
    combined = f"{titulo or ''} {descripcion or ''}".lower()
    for pattern, sector in SECTOR_PATTERNS:
        if re.search(pattern, combined, re.IGNORECASE):
            return sector
    return 'Otro'


def extract_enrichment(titulo, descripcion):
    combined = f"{titulo or ''} {descripcion or ''}".lower()
    result = {}
    for patterns, key in [
        (EXPERIENCIA_PATTERNS, 'nivel_experiencia'),
        (CONTRATO_PATTERNS, 'tipo_contrato'),
        (EDUCACION_PATTERNS, 'nivel_educativo'),
        (MODALIDAD_PATTERNS, 'modalidad'),
    ]:
        for pattern, label in patterns:
            if re.search(pattern, combined, re.IGNORECASE):
                result[key] = label
                break
        else:
            result[key] = None
    return result


def parse_salary(salario_str):
    if not salario_str:
        return None
    cleaned = re.sub(r'[^\d.]', '', salario_str.split('+')[0].split('-')[0].strip())
    parts = cleaned.split('.')
    if len(parts) > 2:
        cleaned = ''.join(parts)
    elif len(parts) == 2 and len(parts[1]) == 3:
        cleaned = ''.join(parts)
    try:
        val = int(cleaned)
        return val if val > 100000 else None
    except (ValueError, OverflowError):
        return None


def get_dane_code(municipio):
    return MUNICIPIO_DANE.get((municipio or '').lower().strip()) if municipio else None
