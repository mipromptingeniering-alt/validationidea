"""
notion_sync_agent.py - Sincroniza ideas con Notion Database
"""
import os, json, urllib.request, urllib.error
from datetime import datetime

NOTION_TOKEN  = os.environ.get("NOTION_TOKEN", "")
NOTION_DB_ID  = os.environ.get("NOTION_DATABASE_ID", "")
NOTION_API    = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

def _headers():
    return {
        "Authorization":  f"Bearer {NOTION_TOKEN}",
        "Content-Type":   "application/json",
        "Notion-Version": NOTION_VERSION,
    }

def _post(endpoint, payload, timeout=20):
    url  = f"{NOTION_API}{endpoint}"
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers=_headers(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Notion HTTP {e.code}: {body[:300]}")
    except Exception as e:
        raise RuntimeError(f"Notion: {e}")

def _truncar(texto, max_len=2000):
    texto = str(texto) if texto else ""
    return texto[:max_len]

def _rich_text(texto):
    return [{"type": "text", "text": {"content": _truncar(texto, 2000)}}]

def _safe_str(valor, max_len=200):
    if isinstance(valor, list):
        return _truncar(", ".join(str(v) for v in valor), max_len)
    if isinstance(valor, dict):
        return _truncar(json.dumps(valor, ensure_ascii=False), max_len)
    return _truncar(str(valor) if valor else "", max_len)

def sync_idea_to_notion(idea):
    """
    Sube una idea a Notion y devuelve la URL de la pagina creada.
    Devuelve "" si falla.
    """
    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado")
        return ""
    if not NOTION_DB_ID:
        print("⚠️ NOTION_DATABASE_ID no configurado")
        return ""
    if not isinstance(idea, dict):
        return ""

    nombre   = _safe_str(idea.get("nombre","SinNombre"), 100)
    tagline  = _safe_str(idea.get("tagline",""), 200)
    problema = _safe_str(idea.get("problema",""), 500)
    solucion = _safe_str(idea.get("solucion",""), 500)
    cliente  = _safe_str(idea.get("cliente_objetivo",""), 300)
    vertical = _safe_str(idea.get("vertical","SaaS"), 100)
    tipo     = _safe_str(idea.get("tipo","B2B"), 50)

    scores   = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
    score    = scores.get("score_total",0)
    ejec     = scores.get("ejecutabilidad",0)
    viral    = scores.get("viral",0)
    timing_s = scores.get("timing",0)

    em       = idea.get("estrategia_monetizacion",{}) if isinstance(idea.get("estrategia_monetizacion"),dict) else {}
    sem1     = _safe_str(em.get("semana1",""), 400)
    precio   = _safe_str(em.get("precio_optimo_justificado",""), 200)

    ht       = idea.get("hipotesis_testeable",{}) if isinstance(idea.get("hipotesis_testeable"),dict) else {}
    exp_48h  = _safe_str(ht.get("experimento_48h",""), 300)

    herr_ia  = _safe_str(idea.get("herramienta_ia_clave",""), 200)

    critico  = idea.get("scoring_critico",{}) if isinstance(idea.get("scoring_critico"),dict) else {}
    veredicto    = _safe_str(critico.get("veredicto",""), 300)
    recomendacion = _safe_str(critico.get("recomendacion",""), 50)

    tags     = idea.get("tags",[])
    if not isinstance(tags, list):
        tags = []
    tags_str = ", ".join(str(t) for t in tags[:5])

    mvp      = idea.get("mvp",{}) if isinstance(idea.get("mvp"),dict) else {}
    stack    = _safe_str(mvp.get("stack_recomendado",""), 200)
    semanas  = mvp.get("tiempo_semanas", 3)

    dafo     = idea.get("dafo",{}) if isinstance(idea.get("dafo"),dict) else {}
    fortalezas = _safe_str(dafo.get("fortalezas",[]), 300)
    amenazas   = _safe_str(dafo.get("amenazas",[]), 300)

    mercado  = idea.get("mercado",{}) if isinstance(idea.get("mercado"),dict) else {}
    tam      = _safe_str(mercado.get("TAM",""), 100)
    ventaja  = _safe_str(mercado.get("ventaja_competitiva",""), 300)

    # Emoji por score
    if   score >= 90: emoji = "💎"
    elif score >= 85: emoji = "⭐"
    elif score >= 80: emoji = "🔥"
    elif score >= 75: emoji = "✅"
    else:             emoji = "💡"

    title = f"{emoji} {nombre} — {score}/100"

    properties = {
        "Name": {
            "title": _rich_text(title)
        },
        "Score": {
            "number": float(score)
        },
        "Tagline": {
            "rich_text": _rich_text(tagline)
        },
        "Vertical": {
            "select": {"name": vertical[:100]}
        },
        "Tipo": {
            "select": {"name": tipo[:50]}
        },
        "Recomendacion": {
            "select": {"name": recomendacion[:50] if recomendacion else "pivotar"}
        },
        "Ejecutabilidad": {
            "number": float(ejec)
        },
        "Stack": {
            "rich_text": _rich_text(stack)
        },
        "Tags": {
            "rich_text": _rich_text(tags_str)
        },
        "Fecha": {
            "date": {"start": datetime.now().strftime("%Y-%m-%d")}
        },
    }

    # Contenido de la pagina (bloques)
    children = [
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("🚀 Resumen ejecutivo")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"📌 {tagline}")}
        },
        {
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": _rich_text("❗ Problema")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(problema)}
        },
        {
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": _rich_text("💡 Solución")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(solucion)}
        },
        {
            "object": "block", "type": "heading_3",
            "heading_3": {"rich_text": _rich_text("👤 Cliente objetivo")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(cliente)}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("📊 Scoring")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(
                f"Score total: {score}/100 | Ejecutabilidad: {ejec} | Viral: {viral} | Timing: {timing_s}"
            )}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("💰 Estrategia de monetización")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"Semana 1: {sem1}")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"Precio: {precio}")}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("🧪 Hipótesis testeable")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"Experimento 48h: {exp_48h}")}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("🤖 Herramienta IA clave")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(herr_ia)}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("🛠️ MVP")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"Stack: {stack} | Tiempo: {semanas} semanas | Coste: 0€")}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("📈 Mercado")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"TAM: {tam}\nVentaja: {ventaja}")}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("⚔️ DAFO")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"Fortalezas: {fortalezas}\nAmenazas: {amenazas}")}
        },
        {
            "object": "block", "type": "heading_2",
            "heading_2": {"rich_text": _rich_text("✅ Veredicto YC")}
        },
        {
            "object": "block", "type": "paragraph",
            "paragraph": {"rich_text": _rich_text(f"{veredicto}\nRecomendacion: {recomendacion.upper()}")}
        },
    ]

    payload = {
        "parent":     {"database_id": NOTION_DB_ID},
        "properties": properties,
        "children":   children[:50],  # Notion limita a 100 bloques por request
    }

    try:
        result = _post("/pages", payload)
        page_id  = result.get("id","").replace("-","")
        page_url = result.get("url","")
        if not page_url and page_id:
            page_url = f"https://notion.so/{page_id}"
        print(f"✅ Notion: {page_url}")
        return page_url
    except Exception as e:
        print(f"❌ Notion sync: {e}")
        return ""

# fin agents/notion_sync_agent.py
