import os
import time
import requests
from dotenv import load_dotenv
from agents.encoding_helper import fix_llm_encoding

load_dotenv()

NOTION_API_KEY     = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY     = os.environ.get("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID   = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_VERSION     = "2022-06-28"

CAMPOS = {
    "Problem":    "Describe el problema principal que resuelve: quién lo sufre, por qué duele, qué pierde si no lo resuelve. Usa datos si es posible. Máximo 3 frases.",
    "Solution":   "Explica cómo funciona exactamente la solución: qué hace, paso a paso. Directo y concreto. Máximo 3 frases.",
    "Description":"Una sola frase que describa el producto como si fuera un tweet de lanzamiento.",
    "Value":      "Propuesta de valor única: por qué elegiría esto el cliente en lugar de la competencia o de no hacer nada.",
    "Target":     "Perfil del cliente ideal: edad, ocupación, dolor específico, dónde pasa el tiempo online, cuánto pagaría.",
    "MVP":        "El producto mínimo viable: qué es lo más pequeño que se puede lanzar en 2 semanas con €0 de inversión.",
    "Marketing":  "3 canales de adquisición concretos con tácticas específicas para los primeros 100 clientes.",
    "Metrics":    "Los 5 KPIs más importantes para medir el éxito en los primeros 90 días, con valores objetivo.",
    "Strengths":  "3-5 ventajas competitivas concretas: por qué esta idea tiene más probabilidades de funcionar.",
    "Weaknesses": "3-5 debilidades reales que hay que superar: mercado, ejecución, competencia, adopción.",
    "Risks":      "Top 3 riesgos críticos: probabilidad de ocurrencia y plan de mitigación para cada uno.",
    "NextSteps":  "Los próximos 5 pasos concretos ordenados por prioridad para validar y lanzar esta semana.",
    "Business":   "Modelo de monetización: precios exactos, márgenes estimados, proyección de ingresos mes 1, mes 6.",
    "Research":   "Tamaño de mercado (TAM/SAM/SOM), tendencia de búsqueda, 2-3 competidores directos con sus precios.",
    "Report":     "Resumen ejecutivo de 5 frases para presentar a un inversor: problema, solución, mercado, modelo, tracción.",
}


def _h():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def telegram(msg: str):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": msg, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


def _groq(prompt: str, max_tokens: int = 400) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={"model": "llama-3.3-70b-versatile",
              "messages": [{"role": "user", "content": prompt}],
              "temperature": 0.6, "max_tokens": max_tokens},
        timeout=60,
    )
    if r.status_code == 429:
        raise RuntimeError("RATE_LIMIT")
    r.raise_for_status()
    return fix_llm_encoding(r.json()["choices"][0]["message"]["content"].strip())


def _gemini(prompt: str, max_tokens: int = 400) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={GEMINI_API_KEY}"
    r = requests.post(url,
        json={"contents": [{"parts": [{"text": prompt}]}],
              "generationConfig": {"maxOutputTokens": max_tokens, "temperature": 0.6}},
        timeout=60,
    )
    r.raise_for_status()
    return fix_llm_encoding(r.json()["candidates"][0]["content"]["parts"][0]["text"].strip())


def ia(prompt: str, max_tokens: int = 400) -> str | None:
    for i in range(3):
        try:
            return _groq(prompt, max_tokens)
        except RuntimeError:
            time.sleep(20 * (i + 1))
        except Exception as e:
            print(f"[Groq] {e}")
            break
    for i in range(3):
        try:
            return _gemini(prompt, max_tokens)
        except Exception as e:
            print(f"[Gemini] {e}")
            time.sleep(30)
    return None


def get_ideas_con_vacios() -> list:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    filtro = {
        "or": [
            {"property": c, "rich_text": {"is_empty": True}}
            for c in ["Problem", "Solution", "Value", "MVP", "Business", "Report"]
        ]
    }
    ideas, cursor = [], None
    while True:
        body = {"page_size": 100, "filter": filtro}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(url, headers=_h(), json=body, timeout=30)
        data = r.json()
        ideas.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        cursor = data.get("next_cursor")
    return ideas


def get_txt(props, key):
    p = props.get(key, {})
    rt = p.get("rich_text") or p.get("title") or []
    return " ".join(t.get("plain_text", "") for t in rt).strip()


def get_num(props, key):
    return props.get(key, {}).get("number")


def patch_texto(pid, campo, valor):
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{pid}", headers=_h(),
        json={"properties": {campo: {"rich_text": [{"type": "text", "text": {"content": valor[:2000]}}]}}},
        timeout=30,
    )
    return r.status_code == 200


def patch_numero(pid, campo, valor):
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{pid}", headers=_h(),
        json={"properties": {campo: {"number": valor}}},
        timeout=30,
    )
    return r.status_code == 200


def patch_tags(pid, tags):
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{pid}", headers=_h(),
        json={"properties": {"Tags": {"multi_select": [{"name": t} for t in tags]}}},
        timeout=30,
    )
    return r.status_code == 200


def generar_campo(campo, instruccion, contexto):
    prompt = f"""Eres experto en negocios digitales. Genera el campo "{campo}" para esta idea.

CONTEXTO DE LA IDEA:
{contexto}

INSTRUCCIÓN:
{instruccion}

REGLAS: máximo 300 palabras, directo y accionable, en español, sin introducciones.
Escribe solo el contenido del campo:"""
    return ia(prompt, 400)


def generar_score(tipo, contexto):
    criterios = {
        "ScoreGen":    "viabilidad general: mercado, monetización, ejecución (1-100)",
        "ScoreViral":  "potencial viral y crecimiento orgánico en redes (1-100)",
        "ScoreCritic": "urgencia del problema: cuánto duele al cliente (1-100)",
    }
    prompt = f"""Evalúa esta idea para: {criterios.get(tipo, tipo)}

{contexto}

Responde SOLO con un número entero entre 1 y 100. Sin texto:"""
    res = ia(prompt, 10)
    if res:
        try:
            return int("".join(c for c in res if c.isdigit())[:3])
        except Exception:
            return None
    return None


def generar_tags(contexto):
    LISTA = "SaaS, IA, Automatizacion, Ecommerce, Marketing, B2B, B2C, Productividad, Educacion, Finanzas, Salud, Herramientas, Freelance, Plugin, PDF, No-Code, API"
    prompt = f"""Elige 2-4 etiquetas para esta idea de negocio.
IDEA: {contexto}
LISTA DE ETIQUETAS: {LISTA}
Responde SOLO con etiquetas separadas por coma. Ejemplo: SaaS, IA, B2B"""
    res = ia(prompt, 30)
    if res:
        return [t.strip() for t in res.split(",") if t.strip()]
    return []


def main():
    print("=" * 50)
    print("completar_campos.py — Rellenando campos vacíos")
    print("=" * 50)

    ideas = get_ideas_con_vacios()
    print(f"Ideas con campos vacíos: {len(ideas)}")
    if not ideas:
        telegram("✅ <b>Completar campos:</b> Todo completo.")
        return

    telegram(f"🔧 <b>Completando {len(ideas)} ideas...</b>")

    for i, page in enumerate(ideas, 1):
        pid   = page["id"]
        props = page.get("properties", {})
        nombre = get_txt(props, "Name") or "Sin nombre"
        print(f"\n[{i}/{len(ideas)}] ➜ {nombre}")

        ctx_parts = [f"Nombre: {nombre}"]
        for c in ["Problem", "Solution", "Value", "Target", "Business", "Description"]:
            v = get_txt(props, c)
            if v:
                ctx_parts.append(f"{c}: {v}")
        ctx = "\n".join(ctx_parts)

        completados = 0

        for campo, instruccion in CAMPOS.items():
            if not get_txt(props, campo):
                print(f"  → Generando {campo}...")
                nuevo = generar_campo(campo, instruccion, ctx)
                if nuevo and patch_texto(pid, campo, nuevo):
                    completados += 1
                    ctx += f"\n{campo}: {nuevo}"
                    print(f"  ✅ {campo}")
                time.sleep(1)

        for score_campo in ["ScoreGen", "ScoreViral", "ScoreCritic"]:
            if get_num(props, score_campo) is None:
                score = generar_score(score_campo, ctx)
                if score and patch_numero(pid, score_campo, score):
                    completados += 1
                    print(f"  ✅ {score_campo}: {score}")
                time.sleep(1)

        if not props.get("Tags", {}).get("multi_select"):
            tags = generar_tags(ctx)
            if tags and patch_tags(pid, tags):
                completados += 1
                print(f"  ✅ Tags: {', '.join(tags)}")

        url_idea = f"https://notion.so/{pid.replace('-', '')}"
        telegram(f"✅ <b>{nombre}</b> — {completados} campos completados\n{url_idea}")
        time.sleep(3)

    telegram(f"🎉 <b>Completar campos finalizado.</b> {len(ideas)} ideas procesadas.")
    print("\n✅ Completar campos finalizado")


if __name__ == "__main__":
    main()
