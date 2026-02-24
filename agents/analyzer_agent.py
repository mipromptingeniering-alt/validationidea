import os
import time
import requests
from agents.encoding_helper import fix_llm_encoding

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")

# ── 15 secciones obligatorias ─────────────────────────────────────────────────
SECCIONES = [
    "IDEA Y PROPUESTA DE VALOR",
    "ANALISIS DE MERCADO",
    "CLIENTE IDEAL (BUYER PERSONA)",
    "ANALISIS DE LA COMPETENCIA",
    "MODELO DE NEGOCIO",
    "VALIDACION DEL NEGOCIO",
    "PLAN FINANCIERO",
    "ESTRATEGIA DE MARKETING DIGITAL",
    "TECNOLOGIA Y HERRAMIENTAS",
    "METRICAS Y KPIs",
    "ASPECTOS LEGALES Y FISCALES",
    "OPERACIONES Y GESTION",
    "MARCA Y CONFIANZA",
    "RIESGOS Y PLAN B",
    "MENTALIDAD Y ESTRATEGIA PERSONAL",
]

FRASES_RELLENO = [
    "en desarrollo", "próximamente", "no disponible",
    "no especificado", "pendiente", "por definir",
    "a determinar", "tbd", "n/a", "este apartado",
    "en construcción", "será definido",
]


# ── LLM helpers ───────────────────────────────────────────────────────────────

def _groq(prompt: str, max_tokens: int = 4096) -> str:
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    }
    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.7,
        "max_tokens": max_tokens,
    }
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers, json=body, timeout=120
    )
    if r.status_code == 429:
        raise RuntimeError("RATE_LIMIT_GROQ")
    r.raise_for_status()
    return fix_llm_encoding(r.json()["choices"][0]["message"]["content"])


def _gemini(prompt: str, max_tokens: int = 4096) -> str:
    url = (
        "https://generativelanguage.googleapis.com/v1beta/models/"
        f"gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    )
    body = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.7},
    }
    r = requests.post(url, json=body, timeout=120)
    if r.status_code == 429:
        raise RuntimeError("RATE_LIMIT_GEMINI")
    r.raise_for_status()
    return fix_llm_encoding(
        r.json()["candidates"][0]["content"]["parts"][0]["text"]
    )


def llamar_ia(prompt: str, max_tokens: int = 4096) -> str | None:
    for intento in range(3):
        try:
            return _groq(prompt, max_tokens)
        except RuntimeError as e:
            if "RATE_LIMIT" in str(e):
                espera = 30 * (2 ** intento)
                print(f"[Groq] Rate limit. Esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"[Groq] Error: {e}")
                break
        except Exception as e:
            print(f"[Groq] Error inesperado: {e}")
            break

    for intento in range(3):
        try:
            print("[Gemini] Usando fallback...")
            return _gemini(prompt, max_tokens)
        except RuntimeError as e:
            if "RATE_LIMIT" in str(e):
                espera = 45 * (2 ** intento)
                print(f"[Gemini] Rate limit. Esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"[Gemini] Error: {e}")
                break
        except Exception as e:
            print(f"[Gemini] Error: {e}")
            time.sleep(30)
    return None


# ── P4: Validador de calidad ──────────────────────────────────────────────────

def _extraer_secciones(informe: str) -> dict:
    """Devuelve dict {NOMBRE_SECCION: contenido} extrayendo bloques ## del informe."""
    secciones = {}
    partes = informe.split("## ")
    for parte in partes[1:]:
        lineas = parte.strip().split("\n", 1)
        nombre = lineas[0].strip().upper()
        contenido = lineas[1].strip() if len(lineas) > 1 else ""
        secciones[nombre] = contenido
    return secciones


def _seccion_valida(contenido: str) -> tuple:
    """Retorna (True/False, motivo). False si hay poco contenido o relleno."""
    palabras = len(contenido.split())
    if palabras < 100:
        return False, f"solo {palabras} palabras (mínimo 100)"
    for frase in FRASES_RELLENO:
        if frase in contenido.lower():
            return False, f"contiene frase de relleno: '{frase}'"
    return True, ""


def _regenerar_seccion(nombre: str, idea: dict, resumen_idea: str) -> str:
    """Regenera una sola sección con prompt específico y detallado."""
    nombre_idea = idea.get("nombre", "la idea")
    prompt = (
        f"Eres un experto analista de negocios con 20 años de experiencia en startups digitales.\n"
        f"Escribe ÚNICAMENTE la sección '{nombre}' para el informe de negocio de '{nombre_idea}'.\n\n"
        f"Contexto de la idea:\n{resumen_idea}\n\n"
        f"REGLAS ESTRICTAS:\n"
        f"- Mínimo 200 palabras\n"
        f"- Incluye datos numéricos reales (precios, TAM/SAM, porcentajes)\n"
        f"- Pasos accionables y concretos\n"
        f"- Sin frases genéricas ni de relleno\n"
        f"- Responde SOLO con el contenido, sin escribir el título\n\n"
        f"Escribe ahora la sección {nombre}:"
    )
    resultado = llamar_ia(prompt, max_tokens=800)
    return resultado or ""


def _validar_y_mejorar(informe: str, idea: dict) -> str:
    """Recorre las 15 secciones, regenera las que no superan el umbral de calidad."""
    secciones_actuales = _extraer_secciones(informe)
    informe_final = informe
    mejoras = 0

    # Resumen de la idea para el prompt de regeneración
    resumen = (
        f"Nombre: {idea.get('nombre', 'N/A')}\n"
        f"Problema: {idea.get('problema', idea.get('Problem', 'N/A'))}\n"
        f"Solución: {idea.get('solucion', idea.get('Solution', 'N/A'))}\n"
        f"Modelo de negocio: {idea.get('modelo_negocio', idea.get('Business', 'N/A'))}"
    )

    for seccion in SECCIONES:
        # Buscar sección (tolerante a variaciones menores)
        contenido = None
        clave_encontrada = None
        for k, v in secciones_actuales.items():
            if seccion in k or k in seccion:
                contenido = v
                clave_encontrada = k
                break

        # Sección ausente — añadir al final
        if contenido is None:
            print(f"[Validator] ⚠️  Sección ausente: {seccion} — regenerando...")
            nuevo = _regenerar_seccion(seccion, idea, resumen)
            if nuevo:
                informe_final += f"\n\n## {seccion}\n{nuevo}"
                mejoras += 1
            continue

        # Sección presente pero insuficiente
        valida, motivo = _seccion_valida(contenido)
        if not valida:
            print(f"[Validator] 🔄 '{seccion}' — {motivo} — regenerando...")
            nuevo = _regenerar_seccion(seccion, idea, resumen)
            if nuevo and len(nuevo.split()) >= 80:
                titulo = f"## {clave_encontrada if clave_encontrada else seccion}"
                pos = informe_final.upper().find(titulo.upper())
                if pos >= 0:
                    sig = informe_final.find("\n## ", pos + len(titulo))
                    bloque = titulo + "\n" + nuevo + "\n"
                    if sig >= 0:
                        informe_final = informe_final[:pos] + bloque + informe_final[sig:]
                    else:
                        informe_final = informe_final[:pos] + bloque
                mejoras += 1

    total_palabras = len(informe_final.split())
    if mejoras > 0:
        print(f"[Validator] ✅ {mejoras} sección(es) mejorada(s) — {total_palabras} palabras totales")
    else:
        print(f"[Validator] ✅ Todas las secciones OK — {total_palabras} palabras")

    return informe_final


# ── Función principal ─────────────────────────────────────────────────────────

def generate_complete_report(idea: dict) -> str | None:
    def get(key, *fallbacks):
        for k in [key] + list(fallbacks):
            v = idea.get(k)
            if v:
                return str(v)
        return "No especificado"

    nombre      = get("nombre",         "Name")
    problema    = get("problema",        "Problem")
    solucion    = get("solucion",        "Solution")
    valor       = get("propuesta_valor", "Value")
    target      = get("target",          "Target")
    mvp         = get("mvp",             "MVP")
    marketing   = get("marketing",       "Marketing")
    negocio     = get("modelo_negocio",  "Business")
    fortalezas  = get("fortalezas",      "Strengths")
    debilidades = get("debilidades",     "Weaknesses")
    riesgos     = get("riesgos",         "Risks")
    sg          = get("score_generador", "ScoreGen",   "score_gen")
    sv          = get("viral_score",     "ScoreViral", "score_viral")
    sc          = get("score_critico",   "ScoreCritic")

    prompt = f"""Eres un experto analista de negocios con 20 años de experiencia en startups digitales, SaaS y productos bootstrapped. Redacta un INFORME DE NEGOCIO COMPLETO Y DETALLADO en español.

=== DATOS DE LA IDEA ===
Nombre: {nombre}
Problema que resuelve: {problema}
Solución propuesta: {solucion}
Propuesta de valor: {valor}
Cliente objetivo: {target}
MVP: {mvp}
Estrategia de marketing: {marketing}
Modelo de negocio: {negocio}
Fortalezas: {fortalezas}
Debilidades: {debilidades}
Riesgos: {riesgos}
Score general: {sg}/100 | Score viral: {sv}/100 | Score crítico: {sc}/100

=== ESTRUCTURA OBLIGATORIA ===
Escribe EXACTAMENTE los 15 apartados con "## " como prefijo. Mínimo 200 palabras por apartado. Incluye datos numéricos reales (TAM/SAM, precios, porcentajes, ejemplos concretos).

## IDEA Y PROPUESTA DE VALOR
## ANALISIS DE MERCADO
## CLIENTE IDEAL (BUYER PERSONA)
## ANALISIS DE LA COMPETENCIA
## MODELO DE NEGOCIO
## VALIDACION DEL NEGOCIO
## PLAN FINANCIERO
## ESTRATEGIA DE MARKETING DIGITAL
## TECNOLOGIA Y HERRAMIENTAS
## METRICAS Y KPIs
## ASPECTOS LEGALES Y FISCALES
## OPERACIONES Y GESTION
## MARCA Y CONFIANZA
## RIESGOS Y PLAN B
## MENTALIDAD Y ESTRATEGIA PERSONAL

REGLAS ESTRICTAS:
- Mínimo 2500 palabras en total
- Datos y cifras reales, no genéricas
- Usa "- " para listas
- Pasos accionables en cada sección
- Cero frases de relleno

Escribe el informe completo ahora:"""

    print(f"[Analyzer] Generando informe: {nombre}...")
    resultado = llamar_ia(prompt, max_tokens=4096)

    if not resultado:
        print(f"[Analyzer] ❌ No se pudo generar el informe para {nombre}")
        return None

    palabras_raw = len(resultado.split())
    print(f"[Analyzer] 📝 Borrador: {palabras_raw} palabras — validando calidad...")

    # P4: Validar y mejorar sección a sección
    resultado = _validar_y_mejorar(resultado, idea)

    return resultado
