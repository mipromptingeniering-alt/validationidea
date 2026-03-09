import os
import json
import csv
import requests
from datetime import datetime

NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
NOTION_VERSION     = "2022-06-28"

# Campos exactos de tu BD Notion (detectados en logs)
CAMPO_TITULO      = "Name"
CAMPO_SCORE       = "ScoreViral"
CAMPO_FECHA       = "Date"
CAMPO_TAGS        = "Tags"
CAMPO_DESCRIPCION = "Description"
CAMPO_TARGET      = "Target"

def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def _safe(v, t=dict):
    if isinstance(v, t):
        return v
    return (t)()

def _safe_list(v) -> list:
    if isinstance(v, list):
        return v
    if isinstance(v, str) and v:
        return [v]
    return []

# ════════════════════════════════════════════════════════
#  BARRA DE SCORE VISUAL
# ════════════════════════════════════════════════════════
def _barra(valor: int, max_val: int = 100, largo: int = 10) -> str:
    llenos  = round((valor / max_val) * largo)
    vacios  = largo - llenos
    color   = "🟢" if valor >= 80 else "🟡" if valor >= 65 else "🔴"
    return f"{'█' * llenos}{'░' * vacios} {valor}/100 {color}"

# ════════════════════════════════════════════════════════
#  CONSTRUCTORES DE BLOQUES
# ════════════════════════════════════════════════════════
def _b(txt: str, tipo: str = "paragraph") -> dict:
    return {
        "object": "block", "type": tipo,
        tipo: {"rich_text": [{"type": "text", "text": {"content": str(txt)[:2000]}}]}
    }

def _bh(txt: str, n: int = 2) -> dict:
    t = f"heading_{n}"
    return {
        "object": "block", "type": t,
        t: {"rich_text": [{"type": "text", "text": {"content": str(txt)[:2000]}}]}
    }

def _sep() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}

def _bullet(txt: str) -> dict:
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": str(txt)[:2000]}}]}
    }

def _num(txt: str) -> dict:
    return {
        "object": "block", "type": "numbered_list_item",
        "numbered_list_item": {"rich_text": [{"type": "text", "text": {"content": str(txt)[:2000]}}]}
    }

def _code(txt: str, lang: str = "plain text") -> dict:
    return {
        "object": "block", "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": str(txt)[:2000]}}],
            "language": lang
        }
    }

def _callout(txt: str, emoji: str = "💡") -> dict:
    return {
        "object": "block", "type": "callout",
        "callout": {
            "rich_text": [{"type": "text", "text": {"content": str(txt)[:2000]}}],
            "icon": {"type": "emoji", "emoji": emoji},
            "color": "gray_background"
        }
    }

# ════════════════════════════════════════════════════════
#  PROPIEDADES DE LA TABLA
# ════════════════════════════════════════════════════════
def _build_properties(idea: dict) -> dict:
    scores  = _safe(idea.get("scores", {}))
    score_t = scores.get("score_total", 0)
    tags    = _safe_list(idea.get("tags", []))
    titulo  = f"[{score_t}] {idea.get('nombre','SinNombre')} — {idea.get('tagline','')}"

    return {
        CAMPO_TITULO: {
            "title": [{"type": "text", "text": {"content": titulo[:200]}}]
        },
        CAMPO_SCORE: {
            "number": float(score_t)
        },
        CAMPO_FECHA: {
            "date": {"start": datetime.now().strftime("%Y-%m-%d")}
        },
        CAMPO_TAGS: {
            "multi_select": [{"name": str(t)[:100]} for t in tags[:5]]
        },
        CAMPO_DESCRIPCION: {
            "rich_text": [{"type": "text", "text": {
                "content": idea.get("tagline", "")[:2000]
            }}]
        },
        CAMPO_TARGET: {
            "rich_text": [{"type": "text", "text": {
                "content": idea.get("cliente_objetivo", "")[:2000]
            }}]
        },
    }

# ════════════════════════════════════════════════════════
#  BLOQUES DEL CUERPO — PÁGINA RICA
# ════════════════════════════════════════════════════════
def _construir_bloques(idea: dict) -> list:
    b      = []
    scores = _safe(idea.get("scores", {}))
    s_t    = scores.get("score_total", 0)
    nombre = idea.get("nombre", "?")

    # ── CABECERA
    emoji_rating = "💎" if s_t >= 90 else "⭐" if s_t >= 80 else "🔥" if s_t >= 70 else "💡"
    b.append(_callout(
        f"{emoji_rating} {nombre}  |  Score: {s_t}/100  |  "
        f"{idea.get('vertical','?')} · {idea.get('tipo','?')}  |  "
        f"{datetime.now().strftime('%d/%m/%Y')}",
        emoji_rating
    ))
    b.append(_b(f"\"{idea.get('tagline','')}\"\\n\\n{idea.get('propuesta_valor_unica','')}"))

    # Herramienta IA clave
    herramienta = idea.get("herramienta_ia_clave", "")
    if herramienta:
        b.append(_callout(f"🤖 Herramienta IA que hace posible esta idea HOY:\n{herramienta}", "🤖"))
    b.append(_sep())

    # ── SCORES VISUALES
    b.append(_bh("📊 SCORES DETALLADOS", 2))
    b.append(_b(
        f"Score Total:      {_barra(int(s_t))}\n"
        f"Crítico:          {_barra(scores.get('critico',0))}\n"
        f"Generador $:      {_barra(scores.get('generador',0))}\n"
        f"Ejecutabilidad:   {_barra(scores.get('ejecutabilidad',0))}\n"
        f"Monetización:     {_barra(scores.get('monetizacion',0))}\n"
        f"Timing:           {_barra(scores.get('timing',0))}\n"
        f"Viral:            {_barra(scores.get('viral',0))}"
    ))
    b.append(_sep())

    # ── PROBLEMA & SOLUCIÓN
    b.append(_bh("❓ PROBLEMA & SOLUCIÓN", 2))
    b.append(_callout(idea.get("problema", ""), "🔴"))
    b.append(_callout(idea.get("solucion", ""), "✅"))
    b.append(_b(f"👤 Cliente objetivo: {idea.get('cliente_objetivo','')}"))
    b.append(_sep())

    # ── MERCADO
    mercado = _safe(idea.get("mercado", {}))
    if mercado:
        b.append(_bh("🌍 ANÁLISIS DE MERCADO", 2))
        b.append(_b(
            f"TAM (Total):      {mercado.get('TAM','?')}\n"
            f"SAM (Alcanzable): {mercado.get('SAM','?')}\n"
            f"SOM (Año 1):      {mercado.get('SOM','?')}"
        ))
        b.append(_b(f"🏆 Ventaja competitiva: {mercado.get('ventaja_competitiva','')}"))
        b.append(_b("Competidores y sus debilidades:"))
        for c in _safe_list(mercado.get("competidores", [])):
            b.append(_bullet(str(c)))
        b.append(_sep())

    # ── MODELO DE NEGOCIO
    mn = _safe(idea.get("modelo_negocio", {}))
    if mn:
        b.append(_bh("💰 MODELO DE NEGOCIO", 2))
        b.append(_b(
            f"Tipo: {mn.get('tipo','')}  |  Time to revenue: {mn.get('time_to_revenue','')}\n"
            f"Pricing: {mn.get('pricing','')}"
        ))
        b.append(_b("Canales de adquisición:"))
        for c in _safe_list(mn.get("canales_adquisicion", [])):
            b.append(_bullet(str(c)))
        b.append(_sep())

    # ── PROYECCIONES FINANCIERAS
    eco = _safe(idea.get("estudio_economico", {}))
    if eco:
        b.append(_bh("📈 PROYECCIONES FINANCIERAS", 2))
        for esc, emoji_esc in [("conservador","🟡"), ("realista","🟢"), ("optimista","🚀")]:
            datos = _safe(eco.get(esc, {}))
            if not datos:
                continue
            b.append(_bh(f"{emoji_esc} Escenario {esc.capitalize()}", 3))
            b.append(_b(f"Supuestos: {datos.get('supuestos','')}"))
            m6  = _safe(datos.get("mes6",  {}))
            m12 = _safe(datos.get("mes12", {}))
            m24 = _safe(datos.get("mes24", {}))
            filas = []
            if m6:
                filas.append(
                    f"Mes  6 → MRR {m6.get('mrr_eur','?')}€ | "
                    f"{m6.get('usuarios','?')} usuarios | "
                    f"CAC {m6.get('cac_eur','?')}€ | LTV {m6.get('ltv_eur','?')}€"
                )
            if m12:
                filas.append(
                    f"Mes 12 → MRR {m12.get('mrr_eur','?')}€ | "
                    f"{m12.get('usuarios','?')} usuarios | "
                    f"Margen {m12.get('margen_pct','?')}%"
                )
            if m24:
                filas.append(
                    f"Mes 24 → MRR {m24.get('mrr_eur','?')}€ | "
                    f"ARR {m24.get('arr_eur','?')}€ | "
                    f"Breakeven: {m24.get('breakeven','?')}"
                )
            if filas:
                b.append(_b("\n".join(filas)))
        b.append(_sep())

    # ── DAFO
    dafo = _safe(idea.get("dafo", {}))
    if dafo:
        b.append(_bh("⚡ ANÁLISIS DAFO", 2))
        for label, clave, emoji_d in [
            ("FORTALEZAS",    "fortalezas",    "✅"),
            ("DEBILIDADES",   "debilidades",   "⚠️"),
            ("OPORTUNIDADES", "oportunidades", "🚀"),
            ("AMENAZAS",      "amenazas",      "🔴"),
        ]:
            items = _safe_list(dafo.get(clave, []))
            if items:
                b.append(_b(f"{emoji_d} {label}:"))
                for item in items:
                    b.append(_bullet(str(item)))
        b.append(_sep())

    # ── PLAN DE ACCIÓN (ESTRATEGIA DE MONETIZACIÓN)
    em = _safe(idea.get("estrategia_monetizacion", {}))
    if em:
        b.append(_bh("🗓️ PLAN DE ACCIÓN PASO A PASO", 2))
        pasos = [
            ("semana1", "📅 Semana 1"),
            ("semana4", "📅 Semana 4"),
            ("mes3",    "📅 Mes 3"),
            ("mes6",    "📅 Mes 6"),
        ]
        for key, label in pasos:
            if em.get(key):
                b.append(_num(f"{label}: {em[key]}"))
        if em.get("precio_optimo_justificado"):
            b.append(_callout(f"💵 Precio óptimo: {em['precio_optimo_justificado']}", "💵"))
        b.append(_sep())

    # ── MVP TÉCNICO
    mvp = _safe(idea.get("mvp", {}))
    if mvp:
        coste = mvp.get("coste_estimado_eur", 0)
        try:
            coste = float(coste)
            if coste > 10000:
                coste = 0
        except:
            coste = 0
        b.append(_bh("🛠️ MVP TÉCNICO", 2))
        b.append(_b(
            f"⏱️ Tiempo estimado: {mvp.get('tiempo_semanas','?')} semanas\n"
            f"💶 Coste estimado: {coste}€\n"
            f"🔧 Stack recomendado: {mvp.get('stack_recomendado','')}"
        ))
        b.append(_b("Features mínimas para lanzar:"))
        for feat in _safe_list(mvp.get("features_minimas", [])):
            b.append(_num(str(feat)))
        b.append(_sep())

    # ── PROMPT MVP (bloque más importante)
    pm = _safe(idea.get("prompt_mvp", {}))
    if pm:
        b.append(_bh("🤖 PROMPT PARA CONSTRUIR EL MVP", 2))
        b.append(_callout(
            f"Copia esto en Cursor IDE o Claude.ai y tendrás el MVP completo.\n"
            f"IA recomendada: {pm.get('ia_recomendada','')}",
            "📋"
        ))
        prompt_txt = str(pm.get("prompt_completo", ""))
        if prompt_txt:
            for chunk in [prompt_txt[i:i+1900] for i in range(0, len(prompt_txt), 1900)]:
                b.append(_code(chunk))
        b.append(_sep())

    # ── OPINIÓN PROFESIONAL
    op = idea.get("opinion_profesional", "")
    if op:
        b.append(_bh("🎯 OPINIÓN PROFESIONAL", 2))
        b.append(_callout(str(op), "🎯"))

    return b

# ════════════════════════════════════════════════════════
#  COLA CSV
# ════════════════════════════════════════════════════════
def _guardar_en_cola(idea: dict, error: str):
    try:
        os.makedirs("data", exist_ok=True)
        ruta  = "data/cola_pendientes.csv"
        nuevo = {
            "timestamp":    datetime.now().isoformat(),
            "nombre_idea":  idea.get("nombre", "?"),
            "intentos":     "1",
            "ultimo_error": error[:200],
            "datos_json":   json.dumps(idea, ensure_ascii=False)[:5000],
        }
        existe = os.path.exists(ruta)
        with open(ruta, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=nuevo.keys())
            if not existe:
                writer.writeheader()
            writer.writerow(nuevo)
        print(f"📋 Cola CSV: {idea.get('nombre','?')}")
    except Exception as e:
        print(f"❌ Error cola: {e}")

# ════════════════════════════════════════════════════════
#  SYNC PRINCIPAL
# ════════════════════════════════════════════════════════
def sync_idea_to_notion(idea: dict) -> str:
    nombre = idea.get("nombre", "SinNombre")
    print(f"📤 Sincronizando '{nombre}'...")

    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado")
        return ""

    try:
        properties = _build_properties(idea)
    except Exception as e:
        print(f"⚠️ Error propiedades: {e}")
        scores  = _safe(idea.get("scores", {}))
        score_t = scores.get("score_total", 0)
        properties = {CAMPO_TITULO: {"title": [{"type": "text", "text": {
            "content": f"[{score_t}] {nombre}"
        }}]}}

    try:
        bloques = _construir_bloques(idea)[:100]
    except Exception as e:
        print(f"⚠️ Error bloques: {e}")
        bloques = [_b(f"Idea: {nombre} — error generando contenido: {e}")]

    payload = {
        "parent":     {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children":   bloques
    }

    try:
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=_headers(), json=payload, timeout=30
        )
        if resp.status_code == 200:
            page_id = resp.json().get("id", "").replace("-", "")
            url     = f"https://notion.so/{page_id}"
            print(f"✅ Notion OK: {url}")
            return url
        else:
            error_msg = resp.text[:400]
            print(f"❌ Error {resp.status_code}: {error_msg}")
            # Reintento solo con título
            if resp.status_code == 400:
                print("🔄 Reintentando solo con título...")
                scores  = _safe(idea.get("scores", {}))
                score_t = scores.get("score_total", 0)
                payload2 = {
                    "parent":     {"database_id": NOTION_DATABASE_ID},
                    "properties": {CAMPO_TITULO: {"title": [{"type": "text", "text": {
                        "content": f"[{score_t}] {nombre} — {idea.get('tagline','')}"
                    }}]}},
                    "children": bloques
                }
                r2 = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=_headers(), json=payload2, timeout=30
                )
                if r2.status_code == 200:
                    page_id = r2.json().get("id", "").replace("-", "")
                    url     = f"https://notion.so/{page_id}"
                    print(f"✅ Notion OK (solo título): {url}")
                    return url
            _guardar_en_cola(idea, error_msg)
            return ""
    except Exception as e:
        print(f"❌ Excepción Notion: {e}")
        _guardar_en_cola(idea, str(e))
        return ""

# aqui finaliza el codigo de agents/notion_sync_agent.py
