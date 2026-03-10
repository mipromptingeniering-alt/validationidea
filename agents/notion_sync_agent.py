"""
notion_sync_agent.py — Informes profesionales en Notion
Crea páginas ricas con todas las secciones detalladas.
"""
import os
import json
import csv
import requests
from datetime import datetime, timezone

NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
HEADERS = {
    "Authorization":  f"Bearer {NOTION_TOKEN}",
    "Content-Type":   "application/json",
    "Notion-Version": "2022-06-28",
}

# ── Helpers de bloques Notion ────────────────────────────────────────────────

def _h1(text: str) -> dict:
    return {"object":"block","type":"heading_1","heading_1":{"rich_text":[{"type":"text","text":{"content":text[:100]}}]}}

def _h2(text: str) -> dict:
    return {"object":"block","type":"heading_2","heading_2":{"rich_text":[{"type":"text","text":{"content":text[:100]}}]}}

def _h3(text: str) -> dict:
    return {"object":"block","type":"heading_3","heading_3":{"rich_text":[{"type":"text","text":{"content":text[:100]}}]}}

def _p(text: str, bold: bool = False) -> dict:
    rt = {"type":"text","text":{"content":str(text)[:2000]}}
    if bold:
        rt["annotations"] = {"bold": True}
    return {"object":"block","type":"paragraph","paragraph":{"rich_text":[rt]}}

def _p_rich(partes: list) -> dict:
    """partes = [(texto, bold, color)]"""
    rt = []
    for texto, bold, color in partes:
        item = {"type":"text","text":{"content":str(texto)[:500]}}
        ann  = {}
        if bold:  ann["bold"]  = True
        if color: ann["color"] = color
        if ann:   item["annotations"] = ann
        rt.append(item)
    return {"object":"block","type":"paragraph","paragraph":{"rich_text":rt}}

def _b(text: str) -> dict:
    return {"object":"block","type":"bulleted_list_item","bulleted_list_item":{"rich_text":[{"type":"text","text":{"content":str(text)[:2000]}}]}}

def _nb(text: str) -> dict:
    return {"object":"block","type":"numbered_list_item","numbered_list_item":{"rich_text":[{"type":"text","text":{"content":str(text)[:2000]}}]}}

def _quote(text: str) -> dict:
    return {"object":"block","type":"quote","quote":{"rich_text":[{"type":"text","text":{"content":str(text)[:2000]}}]}}

def _callout(text: str, emoji: str = "💡") -> dict:
    return {
        "object":"block","type":"callout",
        "callout":{
            "rich_text":[{"type":"text","text":{"content":str(text)[:2000]}}],
            "icon":{"type":"emoji","emoji":emoji}
        }
    }

def _divider() -> dict:
    return {"object":"block","type":"divider","divider":{}}

def _code(text: str, language: str = "json") -> dict:
    return {
        "object":"block","type":"code",
        "code":{
            "rich_text":[{"type":"text","text":{"content":str(text)[:4000]}}],
            "language": language
        }
    }

def _toggle(title: str, children: list) -> dict:
    return {
        "object":"block","type":"toggle",
        "toggle":{
            "rich_text":[{"type":"text","text":{"content":title[:100]}}],
            "children": children[:100]
        }
    }

def _safe(d, *keys, default="N/A"):
    """Acceso seguro a diccionario anidado."""
    val = d
    for k in keys:
        if not isinstance(val, dict): return default
        val = val.get(k, default)
    return val if val not in (None, "", {}, []) else default

def _score_bar(score: float) -> str:
    """Genera barra visual de score."""
    filled = int(score / 10)
    empty  = 10 - filled
    bar    = "█" * filled + "░" * empty
    emoji  = "💎" if score >= 90 else "⭐" if score >= 85 else "🔥" if score >= 80 else "✅" if score >= 75 else "💡"
    return f"{emoji} {bar} {score}/100"

# ── Constructor de bloques ────────────────────────────────────────────────────

def _construir_bloques(idea: dict) -> list:
    bloques = []
    scores  = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
    score   = scores.get("score_total", 0)
    nombre  = idea.get("nombre", "Sin nombre")
    tagline = idea.get("tagline", "")
    fecha   = datetime.now().strftime("%d/%m/%Y %H:%M")

    # ── CABECERA ─────────────────────────────────────────────────────────────
    bloques.append(_callout(
        f"{_score_bar(score)} | {idea.get('vertical','?')} · {idea.get('tipo','?')} | {fecha}",
        emoji="🚀"
    ))
    bloques.append(_p(f""{tagline}"", bold=True))
    bloques.append(_divider())

    # ── RESUMEN EJECUTIVO ─────────────────────────────────────────────────────
    bloques.append(_h2("📋 Resumen Ejecutivo"))
    bloques.append(_p(idea.get("problema", ""), bold=False))
    bloques.append(_p(""))
    bloques.append(_p_rich([
        ("✅ Solución: ", True, "green"),
        (idea.get("solucion",""), False, "")
    ]))
    bloques.append(_p_rich([
        ("🎯 Cliente: ", True, "blue"),
        (idea.get("cliente_objetivo",""), False, "")
    ]))
    bloques.append(_p_rich([
        ("💡 Propuesta única: ", True, "purple"),
        (idea.get("propuesta_valor_unica",""), False, "")
    ]))
    bloques.append(_p_rich([
        ("🤖 IA clave: ", True, "orange"),
        (idea.get("herramienta_ia_clave",""), False, "")
    ]))
    bloques.append(_divider())

    # ── SCORES ───────────────────────────────────────────────────────────────
    bloques.append(_h2("📊 Análisis de Scores"))
    score_items = [
        ("critico",        "🔍 Análisis crítico",     "Rigor del análisis"),
        ("generador",      "💰 Generador ingresos",   "Potencial de revenue"),
        ("ejecutabilidad", "⚡ Ejecutabilidad",        "Facilidad de construir"),
        ("monetizacion",   "💳 Monetización",          "Velocidad de cobrar"),
        ("timing",         "⏰ Timing de mercado",     "Momento de entrada"),
        ("viral",          "📢 Potencial viral",       "Crecimiento orgánico"),
    ]
    for key, label, desc in score_items:
        val = scores.get(key, 0)
        bar = "█" * int(val/10) + "░" * (10-int(val/10))
        bloques.append(_b(f"{label}: {bar} {val}/100 — {desc}"))
    bloques.append(_callout(f"SCORE TOTAL PONDERADO: {score}/100", emoji="🏆"))
    bloques.append(_divider())

    # ── MERCADO ───────────────────────────────────────────────────────────────
    bloques.append(_h2("🌐 Análisis de Mercado"))
    mercado = idea.get("mercado", {}) if isinstance(idea.get("mercado"), dict) else {}
    bloques.append(_b(f"TAM (Mercado total): {_safe(mercado, 'TAM')}"))
    bloques.append(_b(f"SAM (Mercado alcanzable): {_safe(mercado, 'SAM')}"))
    bloques.append(_b(f"SOM (Objetivo año 1): {_safe(mercado, 'SOM')}"))
    bloques.append(_p(""))
    bloques.append(_h3("Competidores y debilidades explotables"))
    competidores = mercado.get("competidores", [])
    if isinstance(competidores, list):
        for c in competidores:
            bloques.append(_b(str(c)))
    bloques.append(_p(""))
    bloques.append(_p_rich([
        ("🛡️ Ventaja competitiva (moat): ", True, "green"),
        (_safe(mercado, "ventaja_competitiva"), False, "")
    ]))
    bloques.append(_divider())

    # ── MODELO DE NEGOCIO ─────────────────────────────────────────────────────
    bloques.append(_h2("💼 Modelo de Negocio"))
    mn = idea.get("modelo_negocio", {}) if isinstance(idea.get("modelo_negocio"), dict) else {}
    bloques.append(_b(f"Tipo: {_safe(mn, 'tipo')}"))
    bloques.append(_b(f"Pricing: {_safe(mn, 'pricing')}"))
    bloques.append(_b(f"Time to revenue: {_safe(mn, 'time_to_revenue')}"))
    bloques.append(_h3("Canales de adquisición gratuitos"))
    canales = mn.get("canales_adquisicion", [])
    if isinstance(canales, list):
        for i, c in enumerate(canales, 1):
            bloques.append(_nb(str(c)))
    bloques.append(_divider())

    # ── PROYECCIONES ECONÓMICAS ───────────────────────────────────────────────
    bloques.append(_h2("📈 Proyecciones Económicas"))
    eco = idea.get("estudio_economico", {}) if isinstance(idea.get("estudio_economico"), dict) else {}

    for escenario, emoji_esc in [("conservador","🐢"), ("realista","🎯"), ("optimista","🚀")]:
        esc = eco.get(escenario, {}) if isinstance(eco.get(escenario), dict) else {}
        supuestos = esc.get("supuestos", "")
        m6  = esc.get("mes6",  {}) if isinstance(esc.get("mes6"),  dict) else {}
        m12 = esc.get("mes12", {}) if isinstance(esc.get("mes12"), dict) else {}
        m24 = esc.get("mes24", {}) if isinstance(esc.get("mes24"), dict) else {}
        bloques.append(_h3(f"{emoji_esc} Escenario {escenario.capitalize()}"))
        bloques.append(_p(f"Supuestos: {supuestos}"))
        bloques.append(_b(f"Mes 6  → MRR: €{m6.get('mrr_eur','?')} | Usuarios: {m6.get('usuarios','?')} | CAC: €{m6.get('cac_eur','?')} | LTV: €{m6.get('ltv_eur','?')}"))
        bloques.append(_b(f"Mes 12 → MRR: €{m12.get('mrr_eur','?')} | Usuarios: {m12.get('usuarios','?')} | Margen: {m12.get('margen_pct','?')}%"))
        bloques.append(_b(f"Mes 24 → MRR: €{m24.get('mrr_eur','?')} | ARR: €{m24.get('arr_eur','?')} | Breakeven: {m24.get('breakeven','?')}"))
    bloques.append(_divider())

    # ── DAFO ─────────────────────────────────────────────────────────────────
    bloques.append(_h2("🔄 Análisis DAFO"))
    dafo = idea.get("dafo", {}) if isinstance(idea.get("dafo"), dict) else {}
    for key, label, emoji_d in [
        ("fortalezas","Fortalezas","💪"),
        ("debilidades","Debilidades","⚠️"),
        ("oportunidades","Oportunidades","🌟"),
        ("amenazas","Amenazas","🚨")
    ]:
        items = dafo.get(key, [])
        if isinstance(items, list) and items:
            bloques.append(_h3(f"{emoji_d} {label}"))
            for item in items:
                bloques.append(_b(str(item)))
    bloques.append(_divider())

    # ── MVP ───────────────────────────────────────────────────────────────────
    bloques.append(_h2("🛠️ Plan MVP"))
    mvp = idea.get("mvp", {}) if isinstance(idea.get("mvp"), dict) else {}
    bloques.append(_callout(
        f"⏱️ Tiempo: {_safe(mvp,'tiempo_semanas')} semanas | 💰 Coste: €{_safe(mvp,'coste_estimado_eur')} | Stack: {_safe(mvp,'stack_recomendado')}",
        emoji="⚡"
    ))
    bloques.append(_h3("Features mínimas (P0)"))
    features = mvp.get("features_minimas", [])
    if isinstance(features, list):
        for i, f in enumerate(features, 1):
            bloques.append(_nb(str(f)))
    bloques.append(_divider())

    # ── HOJA DE RUTA ──────────────────────────────────────────────────────────
    hoja = idea.get("hoja_de_ruta", {}) if isinstance(idea.get("hoja_de_ruta"), dict) else {}
    if hoja:
        bloques.append(_h2("🗓️ Hoja de Ruta"))
        for hito, desc in hoja.items():
            bloques.append(_b(f"{hito.replace('_',' ').title()}: {desc}"))
        bloques.append(_divider())

    # ── PROMPT MVP (JSON) ─────────────────────────────────────────────────────
    bloques.append(_h2("🤖 Prompt MVP — Listo para Cursor/Claude"))
    pm = idea.get("prompt_mvp", {})
    if isinstance(pm, str):
        try:   pm = json.loads(pm)
        except: pm = {"prompt_completo": pm}
    if isinstance(pm, dict):
        ia_rec = pm.get("ia_recomendada", "Claude 3.5 Sonnet en Cursor IDE")
        bloques.append(_callout(f"IA recomendada: {ia_rec}", emoji="🎯"))
        bloques.append(_p("Copia el JSON completo en Cursor o Claude para construir el MVP:", bold=True))
        prompt_json = json.dumps(pm, ensure_ascii=False, indent=2)
        # Dividir en chunks de 4000 chars si es muy largo
        chunk_size = 3800
        for i in range(0, len(prompt_json), chunk_size):
            chunk = prompt_json[i:i+chunk_size]
            bloques.append(_code(chunk, "json"))
    bloques.append(_divider())

    # ── ESTRATEGIA DE MONETIZACIÓN ────────────────────────────────────────────
    bloques.append(_h2("💰 Estrategia de Monetización Paso a Paso"))
    em = idea.get("estrategia_monetizacion", {}) if isinstance(idea.get("estrategia_monetizacion"), dict) else {}
    for key, label in [
        ("semana1","Semana 1 — Primeros 5 usuarios"),
        ("semana4","Semana 4 — Primera venta real"),
        ("mes3",   "Mes 3 — 50 clientes"),
        ("mes6",   "Mes 6 — Crecimiento sostenido"),
    ]:
        val = em.get(key)
        if val:
            bloques.append(_h3(f"📅 {label}"))
            bloques.append(_p(str(val)))
    canales_m = em.get("canales", [])
    if isinstance(canales_m, list) and canales_m:
        bloques.append(_h3("📡 Canales de captación gratuitos"))
        for c in canales_m:
            bloques.append(_nb(str(c)))
    precio = em.get("precio_optimo_justificado")
    if precio:
        bloques.append(_callout(f"💳 Precio óptimo: {precio}", emoji="💡"))
    bloques.append(_divider())

    # ── HIPÓTESIS TESTEABLE ───────────────────────────────────────────────────
    bloques.append(_h2("🧪 Hipótesis Testeable"))
    ht = idea.get("hipotesis_testeable", {}) if isinstance(idea.get("hipotesis_testeable"), dict) else {}
    if isinstance(ht, dict):
        if ht.get("hipotesis_principal"):
            bloques.append(_quote(ht["hipotesis_principal"]))
        if ht.get("experimento_48h"):
            bloques.append(_callout(f"⚡ Experimento 48h (sin código): {ht['experimento_48h']}", emoji="🧪"))
        if ht.get("metrica_exito"):
            bloques.append(_b(f"✅ Métrica de éxito: {ht['metrica_exito']}"))
        if ht.get("senal_de_alarma"):
            bloques.append(_b(f"🚨 Señal de alarma: {ht['senal_de_alarma']}"))
    bloques.append(_divider())

    # ── OPINIÓN PROFESIONAL ───────────────────────────────────────────────────
    bloques.append(_h2("🎯 Opinión Profesional"))
    op = idea.get("opinion_profesional", "")
    if isinstance(op, dict):
        if op.get("unicidad"):
            bloques.append(_p_rich([("🌟 Unicidad HOY: ", True, "green"), (op["unicidad"], False, "")]))
        if op.get("riesgo_principal"):
            bloques.append(_p_rich([("⚠️ Riesgo principal: ", True, "red"), (op["riesgo_principal"], False, "")]))
        if op.get("timing"):
            bloques.append(_p_rich([("⏰ Timing: ", True, "orange"), (op["timing"], False, "")]))
        if op.get("dia_uno"):
            bloques.append(_p_rich([("🚀 Día 1: ", True, "blue"), (op["dia_uno"], False, "")]))
        if op.get("fallo_probable"):
            bloques.append(_p_rich([("💀 Posible fallo: ", True, "gray"), (op["fallo_probable"], False, "")]))
    elif isinstance(op, str) and op:
        bloques.append(_quote(op))
    bloques.append(_divider())

    # ── VALIDACIÓN REAL DE MERCADO ────────────────────────────────────────────
    vm = idea.get("validacion_mercado", {}) if isinstance(idea.get("validacion_mercado"), dict) else {}
    if vm:
        bloques.append(_h2("📡 Validación con Datos Reales"))
        reddit = vm.get("reddit", {}) if isinstance(vm.get("reddit"), dict) else {}
        github = vm.get("github", {}) if isinstance(vm.get("github"), dict) else {}
        gt     = vm.get("google_trends", {}) if isinstance(vm.get("google_trends"), dict) else {}
        if reddit.get("posts", 0) > 0:
            bloques.append(_b(f"Reddit: {reddit.get('posts',0)} posts | {reddit.get('upvotes_total',0)} upvotes | Subreddits: {', '.join(reddit.get('subreddits',[])[:3])}"))
            if reddit.get("top_post"):
                bloques.append(_b(f"Top post: \"{reddit['top_post'][:120]}\""))
        if github.get("repos", 0) > 0:
            bloques.append(_b(f"GitHub: {github.get('repos',0)} repos | Top: {github.get('top_repo','')} ⭐{github.get('top_repo_stars',0)} | Señal: {github.get('señal','')}"))
        if gt and "error" not in gt:
            trend_vals = {k:v for k,v in gt.items() if isinstance(v,(int,float))}
            if trend_vals:
                bloques.append(_b(f"Google Trends: {', '.join(f'{k}={v}' for k,v in list(trend_vals.items())[:3])}"))
        bloques.append(_callout(
            f"Score mercado real: {vm.get('score_mercado_real',0)}/100 | "
            f"Score IA original: {vm.get('score_ia_original',0)} | "
            f"Ajuste aplicado: {vm.get('ajuste_aplicado',0):+.1f} | "
            f"Score final: {vm.get('score_final_ajustado',0)}/100",
            emoji="📊"
        ))
        bloques.append(_divider())

    # ── FOOTER ────────────────────────────────────────────────────────────────
    bloques.append(_callout(
        f"Generado por ValidationIdea v4 | {fecha} | "
        f"Tags: {', '.join(idea.get('tags',[]) if isinstance(idea.get('tags'),list) else [])}",
        emoji="🤖"
    ))

    return bloques

# ── Sync principal ────────────────────────────────────────────────────────────

def sync_idea_to_notion(idea: dict) -> str:
    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado")
        return ""

    scores  = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
    score   = scores.get("score_total", 0)
    nombre  = idea.get("nombre", "Sin nombre")
    tagline = idea.get("tagline", "")
    vertical= idea.get("vertical", "SaaS")
    tipo    = idea.get("tipo", "B2B")
    tags    = idea.get("tags", []) if isinstance(idea.get("tags"), list) else []
    fecha   = datetime.now(timezone.utc).isoformat()

    emoji_score = "💎" if score >= 90 else "⭐" if score >= 85 else "🔥" if score >= 80 else "✅" if score >= 75 else "💡"

    # Propiedades de la base de datos
    propiedades = {
        "Nombre": {"title": [{"text": {"content": f"{emoji_score} {nombre}"}}]},
        "Score":  {"number": float(score)},
        "Vertical": {"select": {"name": str(vertical)[:100]}},
        "Tipo": {"select": {"name": str(tipo)[:100]}},
        "Fecha": {"date": {"start": fecha}},
    }
    # Tags como multi-select (max 5)
    if tags:
        propiedades["Tags"] = {"multi_select": [{"name": str(t)[:100]} for t in tags[:5]]}
    # Tagline como rich text si existe la propiedad
    if tagline:
        propiedades["Tagline"] = {"rich_text": [{"text": {"content": str(tagline)[:2000]}}]}

    # Bloques de contenido
    bloques = _construir_bloques(idea)
    # Notion acepta max 100 bloques por request — dividir si es necesario
    bloques_paginados = bloques[:100]

    payload = {
        "parent":     {"database_id": NOTION_DATABASE_ID},
        "properties": propiedades,
        "children":   bloques_paginados,
    }

    try:
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )
        if resp.status_code in (200, 201):
            page_id = resp.json().get("id","").replace("-","")
            url     = f"https://notion.so/{page_id}"
            print(f"✅ Sincronizada: {nombre} | {url}")

            # Si hay más de 100 bloques, añadir el resto
            if len(bloques) > 100:
                _añadir_bloques_extra(resp.json()["id"], bloques[100:])

            return url
        else:
            print(f"❌ Notion HTTP {resp.status_code}: {resp.text[:300]}")
            _guardar_en_cola(idea, resp.status_code)
            return ""
    except Exception as e:
        print(f"❌ Notion error: {e}")
        _guardar_en_cola(idea, str(e))
        return ""

def _añadir_bloques_extra(page_id: str, bloques: list):
    """Añade bloques adicionales en lotes de 100."""
    try:
        for i in range(0, len(bloques), 100):
            lote = bloques[i:i+100]
            requests.patch(
                f"https://api.notion.com/v1/blocks/{page_id}/children",
                headers=HEADERS,
                json={"children": lote},
                timeout=20,
            )
    except Exception as e:
        print(f"⚠️ Error añadiendo bloques extra: {e}")

def _guardar_en_cola(idea: dict, error):
    """Guarda en CSV para reintento posterior."""
    try:
        os.makedirs("data", exist_ok=True)
        ruta = "data/cola_pendientes.csv"
        existe = os.path.exists(ruta)
        with open(ruta, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=["timestamp","nombre_idea","intentos","error","datos_json"])
            if not existe:
                writer.writeheader()
            writer.writerow({
                "timestamp":   datetime.now().isoformat(),
                "nombre_idea": idea.get("nombre","?"),
                "intentos":    1,
                "error":       str(error)[:200],
                "datos_json":  json.dumps(idea, ensure_ascii=False)[:5000],
            })
    except Exception as e:
        print(f"⚠️ Error guardando en cola: {e}")

# aqui finaliza el codigo de agents/notion_sync_agent.py
