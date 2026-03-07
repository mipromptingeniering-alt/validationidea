import os, json, requests
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
DATABASE_ID  = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")

HEADERS = {
    "Authorization":  f"Bearer {NOTION_TOKEN}",
    "Content-Type":   "application/json",
    "Notion-Version": "2022-06-28",
}

def _bloque_titulo(texto: str) -> dict:
    return {
        "object": "block", "type": "heading_2",
        "heading_2": {"rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]}
    }

def _bloque_parrafo(texto: str) -> dict:
    return {
        "object": "block", "type": "paragraph",
        "paragraph": {"rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]}
    }

def _bloque_separador() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}

def _bloque_callout(texto: str, emoji: str = "💡") -> dict:
    return {
        "object": "block", "type": "callout",
        "callout": {
            "icon": {"type": "emoji", "emoji": emoji},
            "rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]
        }
    }

def _bloque_bullet(items: list) -> list:
    bloques = []
    for item in items:
        bloques.append({
            "object": "block", "type": "bulleted_list_item",
            "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": str(item)[:2000]}}]}
        })
    return bloques

def construir_bloques(idea: dict) -> list:
    bloques = []
    scores = idea.get("scores", {})
    mercado = idea.get("mercado", {})
    modelo  = idea.get("modelo_negocio", {})
    eco     = idea.get("estudio_economico", {})
    dafo    = idea.get("dafo", {})
    mvp     = idea.get("mvp", {})
    prompt_mvp    = idea.get("prompt_mvp", {})
    monetizacion  = idea.get("estrategia_monetizacion", {})
    opinion       = idea.get("opinion_profesional", "")

    # ── RESUMEN EJECUTIVO ────────────────────────────
    bloques.append(_bloque_titulo("📋 RESUMEN EJECUTIVO"))
    bloques.append(_bloque_callout(f"🎯 {idea.get('tagline', '')}", "🎯"))
    bloques.append(_bloque_parrafo(f"🔴 Problema: {idea.get('problema', '')}"))
    bloques.append(_bloque_parrafo(f"✅ Solución: {idea.get('solucion', '')}"))
    bloques.append(_bloque_parrafo(f"👤 Cliente: {idea.get('cliente_objetivo', '')}"))
    bloques.append(_bloque_parrafo(f"⚡ Ventaja única: {idea.get('propuesta_valor_unica', '')}"))
    bloques.append(_bloque_separador())

    # ── SCORING ──────────────────────────────────────
    bloques.append(_bloque_titulo("📊 SCORING DETALLADO"))
    bloques.append(_bloque_parrafo(
        f"TOTAL: {scores.get('score_total', 0)}/100\n"
        f"🔴 Crítico (dolor real): {scores.get('critico', 0)}/100\n"
        f"💰 Generador de revenue: {scores.get('generador', 0)}/100\n"
        f"⚡ Ejecutabilidad solo: {scores.get('ejecutabilidad', 0)}/100\n"
        f"💎 Monetización: {scores.get('monetizacion', 0)}/100\n"
        f"⏰ Timing de mercado: {scores.get('timing', 0)}/100\n"
        f"📣 Potencial viral: {scores.get('viral', 0)}/100"
    ))
    bloques.append(_bloque_separador())

    # ── MERCADO ──────────────────────────────────────
    bloques.append(_bloque_titulo("🌍 ANÁLISIS DE MERCADO"))
    bloques.append(_bloque_parrafo(
        f"TAM: {mercado.get('TAM', 'N/A')}\n"
        f"SAM: {mercado.get('SAM', 'N/A')}\n"
        f"SOM (año 1): {mercado.get('SOM', 'N/A')}"
    ))
    bloques.append(_bloque_parrafo(f"🏆 Ventaja competitiva: {mercado.get('ventaja_competitiva', '')}"))
    competidores = mercado.get("competidores", [])
    if competidores:
        bloques.append(_bloque_parrafo("Competidores principales:"))
        bloques += _bloque_bullet(competidores)
    bloques.append(_bloque_separador())

    # ── MODELO DE NEGOCIO ────────────────────────────
    bloques.append(_bloque_titulo("💼 MODELO DE NEGOCIO"))
    bloques.append(_bloque_parrafo(
        f"Tipo: {modelo.get('tipo', 'N/A')}\n"
        f"💰 Pricing: {modelo.get('pricing', 'N/A')}\n"
        f"⚡ Time to revenue: {modelo.get('time_to_revenue', 'N/A')}"
    ))
    canales = modelo.get("canales_adquisicion", [])
    if canales:
        bloques.append(_bloque_parrafo("Canales de adquisición:"))
        bloques += _bloque_bullet(canales)
    bloques.append(_bloque_separador())

    # ── ESTUDIO ECONÓMICO ────────────────────────────
    bloques.append(_bloque_titulo("📈 ESTUDIO ECONÓMICO — 3 ESCENARIOS"))
    for escenario, emoji in [("conservador", "🐢"), ("realista", "📊"), ("optimista", "🚀")]:
        datos = eco.get(escenario, {})
        if datos:
            m6  = datos.get("mes6", {})
            m12 = datos.get("mes12", {})
            m24 = datos.get("mes24", {})
            bloques.append(_bloque_parrafo(
                f"{emoji} ESCENARIO {escenario.upper()}\n"
                f"Supuestos: {datos.get('supuestos', '')}\n"
                f"Mes 6:  MRR {m6.get('mrr_eur', 0)}€ | Usuarios {m6.get('usuarios', 0)} | CAC {m6.get('cac_eur', 0)}€ | LTV {m6.get('ltv_eur', 0)}€\n"
                f"Mes 12: MRR {m12.get('mrr_eur', 0)}€ | Usuarios {m12.get('usuarios', 0)} | Margen {m12.get('margen_pct', 0)}%\n"
                f"Mes 24: MRR {m24.get('mrr_eur', 0)}€ | ARR {m24.get('arr_eur', 0)}€ | Break-even: {m24.get('breakeven', 'N/A')}"
            ))
    bloques.append(_bloque_separador())

    # ── DAFO ─────────────────────────────────────────
    bloques.append(_bloque_titulo("🔲 ANÁLISIS DAFO"))
    for seccion, emoji in [("fortalezas","💪"),("debilidades","⚠️"),("oportunidades","🌟"),("amenazas","🚨")]:
        items = dafo.get(seccion, [])
        if items:
            bloques.append(_bloque_parrafo(f"{emoji} {seccion.upper()}:"))
            bloques += _bloque_bullet(items)
    bloques.append(_bloque_separador())

    # ── MVP ──────────────────────────────────────────
    bloques.append(_bloque_titulo("🛠️ PLAN MVP"))
    features = mvp.get("features_minimas", [])
    if features:
        bloques.append(_bloque_parrafo("Features mínimas indispensables:"))
        bloques += _bloque_bullet(features)
    bloques.append(_bloque_parrafo(
        f"Stack: {mvp.get('stack_recomendado', 'N/A')}\n"
        f"Tiempo: {mvp.get('tiempo_semanas', 'N/A')} semanas\n"
        f"Coste estimado: {mvp.get('coste_estimado_eur', 0)}€"
    ))
    bloques.append(_bloque_separador())

    # ── ESTRATEGIA MONETIZACIÓN ──────────────────────
    bloques.append(_bloque_titulo("💰 ESTRATEGIA DE MONETIZACIÓN RÁPIDA"))
    bloques.append(_bloque_parrafo(
        f"Semana 1: {monetizacion.get('semana1', '')}\n"
        f"Semana 4: {monetizacion.get('semana4', '')}\n"
        f"Mes 3: {monetizacion.get('mes3', '')}\n"
        f"Mes 6: {monetizacion.get('mes6', '')}"
    ))
    bloques.append(_bloque_parrafo(f"💲 Precio óptimo: {monetizacion.get('precio_optimo_justificado', '')}"))
    canales_m = monetizacion.get("canales", [])
    if canales_m:
        bloques.append(_bloque_parrafo("Canales con mayor ROI:"))
        bloques += _bloque_bullet(canales_m)
    bloques.append(_bloque_separador())

    # ── PROMPT MVP ───────────────────────────────────
    bloques.append(_bloque_titulo("🤖 PROMPT PARA CONSTRUIR EL MVP CON IA"))
    bloques.append(_bloque_callout(
        f"IA recomendada: {prompt_mvp.get('ia_recomendada', 'Claude 3.5 Sonnet en Cursor IDE')}",
        "🤖"
    ))
    prompt_texto = prompt_mvp.get("prompt_completo", "")
    if prompt_texto:
        # Dividir en chunks de 2000 chars para Notion
        for i in range(0, len(prompt_texto), 1900):
            bloques.append(_bloque_parrafo(prompt_texto[i:i+1900]))
    bloques.append(_bloque_separador())

    # ── OPINIÓN PROFESIONAL ──────────────────────────
    if opinion:
        bloques.append(_bloque_titulo("🎯 OPINIÓN PROFESIONAL"))
        bloques.append(_bloque_callout(str(opinion)[:2000], "🎯"))

    return bloques

def sync_idea_to_notion(idea: dict) -> str:
    """Sincroniza idea completa a Notion. Devuelve URL o None."""
    global HEADERS
    HEADERS["Authorization"] = f"Bearer {os.environ.get('NOTION_TOKEN', NOTION_TOKEN)}"

    nombre    = idea.get("nombre", "Sin nombre")
    scores    = idea.get("scores", {})
    score     = scores.get("score_total", 0)
    vertical  = idea.get("vertical", "General")
    tipo      = idea.get("tipo", "B2B")
    modelo    = idea.get("modelo_negocio", {})
    ttr       = modelo.get("time_to_revenue", "N/A")
    mercado   = idea.get("mercado", {})
    sam       = mercado.get("SOM", "N/A")

    print(f"📤 Sincronizando '{nombre}'...")

    # Propiedades de la página
    propiedades = {
        "Nombre": {"title": [{"text": {"content": nombre}}]},
        "Score":  {"number": float(score)},
    }

    # Propiedades opcionales (si existen en la BD)
    try:
        propiedades["Vertical"] = {"select": {"name": str(vertical)[:100]}}
    except: pass
    try:
        propiedades["Tipo"] = {"select": {"name": str(tipo)[:100]}}
    except: pass

    # Crear página
    payload = {
        "parent": {"database_id": DATABASE_ID},
        "icon":   {"type": "emoji", "emoji": "💡"},
        "properties": propiedades,
    }

    resp = requests.post(
        "https://api.notion.com/v1/pages",
        headers=HEADERS, json=payload, timeout=20
    )

    if resp.status_code not in (200, 201):
        print(f"❌ Error {resp.status_code}: {resp.text[:200]}")
        return None

    page_id  = resp.json().get("id", "")
    page_url = resp.json().get("url", "")
    print(f"✅ Sincronizado: {page_url}")

    # Añadir bloques de contenido
    bloques = construir_bloques(idea)
    for i in range(0, len(bloques), 90):  # Notion límite 100 bloques/request
        chunk = bloques[i:i+90]
        r2 = requests.patch(
            f"https://api.notion.com/v1/blocks/{page_id}/children",
            headers=HEADERS,
            json={"children": chunk},
            timeout=30
        )
        if r2.status_code not in (200, 201):
            print(f"⚠️ Error bloques chunk {i}: {r2.status_code}")

    print(f"📄 Informe COMPLETO escrito en la página")
    return page_url
