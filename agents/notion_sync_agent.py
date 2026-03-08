import os
import json
import csv
import requests
from datetime import datetime

NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
NOTION_VERSION     = "2022-06-28"

def _headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }

def _get_schema() -> dict:
    """Devuelve el esquema completo de la BD: {nombre_prop: tipo}"""
    try:
        resp = requests.get(
            f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}",
            headers=_headers(), timeout=10
        )
        if resp.status_code == 200:
            return resp.json().get("properties", {})
    except Exception as e:
        print(f"⚠️ Error consultando esquema: {e}")
    return {}

def _find_prop(schema: dict, candidatos: list, tipo: str = None) -> str:
    """
    Busca en el esquema el primer nombre de propiedad que coincida
    con alguno de los candidatos (case-insensitive) y opcionalmente del tipo indicado.
    """
    schema_lower = {k.lower(): (k, v) for k, v in schema.items()}
    for candidato in candidatos:
        key, data = schema_lower.get(candidato.lower(), (None, None))
        if key:
            if tipo is None or data.get("type") == tipo:
                return key
    # Si no hay coincidencia exacta, buscar por tipo
    if tipo:
        for name, data in schema.items():
            if data.get("type") == tipo:
                return name
    return ""

def _build_properties(idea: dict, schema: dict) -> dict:
    """
    Construye el dict de propiedades Notion rellenando
    todos los campos que existan en el esquema de la BD.
    """
    scores  = idea.get("scores", {})
    score_t = scores.get("score_total", 0)
    props   = {}

    # ── TÍTULO (obligatorio)
    title_prop = _find_prop(schema, ["Name","Nombre","Title","Título","name","nombre"], "title")
    if not title_prop:
        for k, v in schema.items():
            if v.get("type") == "title":
                title_prop = k
                break
    if title_prop:
        titulo = f"[{score_t}] {idea.get('nombre','SinNombre')} — {idea.get('tagline','')}"
        props[title_prop] = {"title": [{"type": "text", "text": {"content": titulo[:200]}}]}

    # ── SCORE (number)
    score_prop = _find_prop(schema, ["Score","Puntuación","Puntuacion","score","Rating"], "number")
    if score_prop:
        props[score_prop] = {"number": float(score_t)}

    # ── VERTICAL (select)
    vertical_prop = _find_prop(schema, ["Vertical","vertical","Sector","sector","Categoría","Categoria"], "select")
    if vertical_prop:
        props[vertical_prop] = {"select": {"name": idea.get("vertical", "SaaS")[:100]}}

    # ── TIPO (select)
    tipo_prop = _find_prop(schema, ["Tipo","tipo","Type","type","Modelo","modelo"], "select")
    if tipo_prop:
        props[tipo_prop] = {"select": {"name": idea.get("tipo", "B2B")[:100]}}

    # ── FECHA (date)
    fecha_prop = _find_prop(schema, ["Fecha","fecha","Date","date","Created","Creado"], "date")
    if fecha_prop:
        props[fecha_prop] = {"date": {"start": datetime.now().strftime("%Y-%m-%d")}}

    # ── TAGS (multi_select)
    tags_prop = _find_prop(schema, ["Tags","tags","Etiquetas","etiquetas","Labels"], "multi_select")
    if tags_prop:
        tags = idea.get("tags", [])[:5]  # Notion limita multi_select
        props[tags_prop] = {"multi_select": [{"name": str(t)[:100]} for t in tags]}

    # ── TAGLINE / DESCRIPCIÓN (rich_text)
    desc_prop = _find_prop(schema, ["Tagline","tagline","Descripción","Descripcion",
                                     "Description","Resumen","resumen","Summary"], "rich_text")
    if desc_prop:
        props[desc_prop] = {"rich_text": [{"type": "text", "text": {
            "content": idea.get("tagline", "")[:2000]
        }}]}

    # ── EJECUTABILIDAD (number)
    ejec_prop = _find_prop(schema, ["Ejecutabilidad","ejecutabilidad","Ejecutable"], "number")
    if ejec_prop:
        props[ejec_prop] = {"number": float(scores.get("ejecutabilidad", 0))}

    # ── CLIENTE (rich_text)
    cliente_prop = _find_prop(schema, ["Cliente","cliente","Customer","Target"], "rich_text")
    if cliente_prop:
        props[cliente_prop] = {"rich_text": [{"type": "text", "text": {
            "content": idea.get("cliente_objetivo", "")[:2000]
        }}]}

    # ── STATUS (select) — marcar como "Generada"
    status_prop = _find_prop(schema, ["Status","status","Estado","estado","Stage"], "select")
    if status_prop:
        props[status_prop] = {"select": {"name": "Generada"}}

    print(f"   Propiedades mapeadas: {list(props.keys())}")
    return props

# ════════════════════════════════════════════════════════
#  BLOQUES DEL CUERPO DE LA PÁGINA
# ════════════════════════════════════════════════════════
def _b_text(texto: str, tipo: str = "paragraph") -> dict:
    return {
        "object": "block", "type": tipo,
        tipo: {"rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]}
    }

def _b_h(texto: str, nivel: int = 2) -> dict:
    t = f"heading_{nivel}"
    return {
        "object": "block", "type": t,
        t: {"rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]}
    }

def _b_sep() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}

def _b_bullet(texto: str) -> dict:
    return {
        "object": "block", "type": "bulleted_list_item",
        "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]}
    }

def _b_code(texto: str) -> dict:
    return {
        "object": "block", "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}],
            "language": "plain text"
        }
    }

def _construir_bloques(idea: dict) -> list:
    b      = []
    scores = idea.get("scores", {})
    s_t    = scores.get("score_total", 0)

    # Resumen
    b.append(_b_h("📊 RESUMEN EJECUTIVO", 1))
    b.append(_b_text(
        f"Vertical: {idea.get('vertical','N/A')}  |  Tipo: {idea.get('tipo','N/A')}  |  Score total: {s_t}/100\n"
        f"Tagline: {idea.get('tagline','')}"
    ))
    b.append(_b_text(
        f"Scores — Crítico: {scores.get('critico',0)} | Viral: {scores.get('viral',0)} | "
        f"Generador: {scores.get('generador',0)} | Monetización: {scores.get('monetizacion',0)} | "
        f"Ejecutabilidad: {scores.get('ejecutabilidad',0)} | Timing: {scores.get('timing',0)}"
    ))
    b.append(_b_sep())

    # Problema y solución
    b.append(_b_h("❓ Problema & Solución", 2))
    b.append(_b_text(f"PROBLEMA: {idea.get('problema','')}"))
    b.append(_b_text(f"SOLUCIÓN: {idea.get('solucion','')}"))
    b.append(_b_text(f"CLIENTE: {idea.get('cliente_objetivo','')}"))
    b.append(_b_text(f"PROPUESTA DE VALOR ÚNICA: {idea.get('propuesta_valor_unica','')}"))
    b.append(_b_sep())

    # Mercado
    mercado = idea.get("mercado", {})
    if mercado:
        b.append(_b_h("🌍 Mercado", 2))
        b.append(_b_text(f"TAM: {mercado.get('TAM','')}"))
        b.append(_b_text(f"SAM: {mercado.get('SAM','')}"))
        b.append(_b_text(f"SOM: {mercado.get('SOM','')}"))
        b.append(_b_text(f"Ventaja competitiva: {mercado.get('ventaja_competitiva','')}"))
        for c in mercado.get("competidores", []):
            b.append(_b_bullet(f"Competidor: {c}"))
        b.append(_b_sep())

    # Modelo de negocio
    mn = idea.get("modelo_negocio", {})
    if mn:
        b.append(_b_h("💰 Modelo de Negocio", 2))
        b.append(_b_text(f"Tipo: {mn.get('tipo','')}  |  Time to revenue: {mn.get('time_to_revenue','')}"))
        b.append(_b_text(f"Pricing: {mn.get('pricing','')}"))
        for canal in mn.get("canales_adquisicion", []):
            b.append(_b_bullet(canal))
        b.append(_b_sep())

    # Estudio económico
    eco = idea.get("estudio_economico", {})
    if eco:
        b.append(_b_h("📈 Estudio Económico", 2))
        for esc in ["conservador", "realista", "optimista"]:
            datos = eco.get(esc, {})
            if not datos:
                continue
            emoji = {"conservador": "🟡", "realista": "🟢", "optimista": "🚀"}.get(esc, "")
            b.append(_b_h(f"{emoji} Escenario {esc.capitalize()}", 3))
            b.append(_b_text(f"Supuestos: {datos.get('supuestos','')}"))
            m6  = datos.get("mes6",  {})
            m12 = datos.get("mes12", {})
            m24 = datos.get("mes24", {})
            if m6:
                b.append(_b_text(
                    f"Mes 6 → MRR: {m6.get('mrr_eur','?')}€ | "
                    f"Usuarios: {m6.get('usuarios','?')} | "
                    f"CAC: {m6.get('cac_eur','?')}€ | LTV: {m6.get('ltv_eur','?')}€"
                ))
            if m12:
                b.append(_b_text(
                    f"Mes 12 → MRR: {m12.get('mrr_eur','?')}€ | "
                    f"Usuarios: {m12.get('usuarios','?')} | Margen: {m12.get('margen_pct','?')}%"
                ))
            if m24:
                b.append(_b_text(
                    f"Mes 24 → MRR: {m24.get('mrr_eur','?')}€ | "
                    f"ARR: {m24.get('arr_eur','?')}€ | Breakeven: {m24.get('breakeven','?')}"
                ))
        b.append(_b_sep())

    # DAFO
    dafo = idea.get("dafo", {})
    if dafo:
        b.append(_b_h("⚡ DAFO", 2))
        b.append(_b_text("FORTALEZAS:"))
        for f in dafo.get("fortalezas", []):
            b.append(_b_bullet(f"✅ {f}"))
        b.append(_b_text("DEBILIDADES:"))
        for d in dafo.get("debilidades", []):
            b.append(_b_bullet(f"⚠️ {d}"))
        b.append(_b_text("OPORTUNIDADES:"))
        for o in dafo.get("oportunidades", []):
            b.append(_b_bullet(f"🚀 {o}"))
        b.append(_b_text("AMENAZAS:"))
        for a in dafo.get("amenazas", []):
            b.append(_b_bullet(f"🔴 {a}"))
        b.append(_b_sep())

    # MVP — forzar coste a 0 si la IA puso algo absurdo
    mvp = idea.get("mvp", {})
    if mvp:
        coste = mvp.get("coste_estimado_eur", 0)
        if isinstance(coste, (int, float)) and coste > 10000:
            coste = 0  # la IA a veces inventa costes, forzamos 0
        b.append(_b_h("🛠️ MVP", 2))
        b.append(_b_text(f"Stack: {mvp.get('stack_recomendado','')}"))
        b.append(_b_text(f"Tiempo: {mvp.get('tiempo_semanas','?')} semanas  |  Coste estimado: {coste}€"))
        for feat in mvp.get("features_minimas", []):
            b.append(_b_bullet(feat))
        b.append(_b_sep())

    # Estrategia de monetización
    em = idea.get("estrategia_monetizacion", {})
    if em:
        b.append(_b_h("💵 Estrategia de Monetización", 2))
        for key, label in [("semana1","Semana 1"),("semana4","Semana 4"),("mes3","Mes 3"),("mes6","Mes 6")]:
            if em.get(key):
                b.append(_b_bullet(f"{label}: {em[key]}"))
        if em.get("precio_optimo_justificado"):
            b.append(_b_text(f"Precio óptimo: {em['precio_optimo_justificado']}"))
        b.append(_b_sep())

    # Prompt MVP
    pm = idea.get("prompt_mvp", {})
    if pm:
        b.append(_b_h("🤖 PROMPT MVP — Copia en Cursor/Claude", 2))
        b.append(_b_text(f"IA recomendada: {pm.get('ia_recomendada','')}"))
        prompt_txt = pm.get("prompt_completo", "")
        if prompt_txt:
            for chunk in [prompt_txt[i:i+1900] for i in range(0, len(prompt_txt), 1900)]:
                b.append(_b_code(chunk))
        b.append(_b_sep())

    # Opinión profesional
    op = idea.get("opinion_profesional", "")
    if op:
        b.append(_b_h("🎯 Opinión Profesional", 2))
        b.append(_b_text(op))

    return b

# ════════════════════════════════════════════════════════
#  COLA CSV — fallback si Notion falla
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
        print(f"📋 Guardado en cola CSV: {idea.get('nombre','?')}")
    except Exception as e:
        print(f"❌ Error guardando cola: {e}")

# ════════════════════════════════════════════════════════
#  SYNC PRINCIPAL
# ════════════════════════════════════════════════════════
def sync_idea_to_notion(idea: dict) -> str:
    nombre = idea.get("nombre", "SinNombre")
    print(f"📤 Sincronizando '{nombre}'...")

    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado")
        return ""

    # 1. Obtener esquema real de la BD
    schema = _get_schema()
    if not schema:
        print("⚠️ No se pudo obtener el esquema de Notion")

    # 2. Construir propiedades dinámicamente según el esquema
    try:
        properties = _build_properties(idea, schema)
    except Exception as e:
        print(f"⚠️ Error construyendo propiedades: {e}")
        # Fallback mínimo: solo título
        title_prop = "Name"
        for k, v in schema.items():
            if v.get("type") == "title":
                title_prop = k
                break
        properties = {
            title_prop: {"title": [{"type": "text", "text": {
                "content": f"{idea.get('nombre','?')} — {idea.get('tagline','')}"
            }}]}
        }

    # 3. Construir bloques del cuerpo
    try:
        bloques = _construir_bloques(idea)[:100]  # Notion limita a 100 bloques por request
    except Exception as e:
        print(f"⚠️ Error construyendo bloques: {e}")
        bloques = [_b_text(f"Error generando contenido: {e}")]

    # 4. Crear la página
    payload = {
        "parent":     {"database_id": NOTION_DATABASE_ID},
        "properties": properties,
        "children":   bloques
    }

    try:
        resp = requests.post(
            "https://api.notion.com/v1/pages",
            headers=_headers(),
            json=payload,
            timeout=30
        )
        if resp.status_code == 200:
            page_id = resp.json().get("id", "").replace("-", "")
            url     = f"https://notion.so/{page_id}"
            print(f"✅ Notion OK: {url}")
            return url
        else:
            error_msg = resp.text[:400]
            print(f"❌ Error {resp.status_code}: {error_msg}")

            # Si el error es de propiedades, reintentar solo con título
            if "not a property" in error_msg.lower() or "validation_error" in error_msg.lower():
                print("🔄 Reintentando solo con título...")
                title_prop = "Name"
                for k, v in schema.items():
                    if v.get("type") == "title":
                        title_prop = k
                        break
                payload_min = {
                    "parent":     {"database_id": NOTION_DATABASE_ID},
                    "properties": {
                        title_prop: {"title": [{"type": "text", "text": {
                            "content": f"[{idea.get('scores',{}).get('score_total',0)}] {nombre} — {idea.get('tagline','')}",
                        }}]}
                    },
                    "children": bloques
                }
                resp2 = requests.post(
                    "https://api.notion.com/v1/pages",
                    headers=_headers(),
                    json=payload_min,
                    timeout=30
                )
                if resp2.status_code == 200:
                    page_id = resp2.json().get("id", "").replace("-", "")
                    url     = f"https://notion.so/{page_id}"
                    print(f"✅ Notion OK (solo título): {url}")
                    print("⚠️ Tu BD de Notion no tiene columnas Score/Vertical/Tipo — añádelas para ver datos en la tabla")
                    return url
                else:
                    print(f"❌ Reintento fallido: {resp2.text[:200]}")

            _guardar_en_cola(idea, error_msg)
            return ""
    except Exception as e:
        print(f"❌ Excepción Notion: {e}")
        _guardar_en_cola(idea, str(e))
        return ""

# aqui finaliza el codigo de agents/notion_sync_agent.py
