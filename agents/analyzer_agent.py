import os
import time
import requests
from agents.encoding_helper import fix_llm_encoding

GROQ_API_KEY  = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")


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


def generate_complete_report(idea: dict) -> str | None:
    def get(key, *fallbacks):
        for k in [key] + list(fallbacks):
            v = idea.get(k)
            if v:
                return str(v)
        return "No especificado"

    nombre     = get("nombre", "Name")
    problema   = get("problema", "Problem")
    solucion   = get("solucion", "Solution")
    valor      = get("propuesta_valor", "Value")
    target     = get("target", "Target")
    mvp        = get("mvp", "MVP")
    marketing  = get("marketing", "Marketing")
    negocio    = get("negocio", "Business")
    fortalezas = get("fortalezas", "Strengths")
    debilidades= get("debilidades", "Weaknesses")
    riesgos    = get("riesgos", "Risks")
    sg         = get("score_gen", "ScoreGen")
    sv         = get("score_viral", "ScoreViral")
    sc         = get("score_critico", "ScoreCritic")

    prompt = f"""Eres un experto analista de negocios online con 20 años de experiencia en startups digitales, SaaS y productos bootstrapped. Redacta un INFORME DE NEGOCIO COMPLETO Y DETALLADO en español.

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
    if resultado:
        palabras = len(resultado.split())
        print(f"[Analyzer] ✅ Informe generado: {palabras} palabras")
    return resultado
