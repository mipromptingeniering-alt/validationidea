import os
import json
import csv
import requests
from datetime import datetime

NOTION_TOKEN       = os.environ.get("NOTION_TOKEN", "")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
NOTION_VERSION     = "2022-06-28"

# ── Campos EXACTOS de tu BD Notion (detectados automáticamente)
# Name, ScoreViral, Date, Tags, Description, Target
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

def _safe_dict(valor, fallback=None) -> dict:
    """Convierte a dict si es string u otro tipo — protección para ideas antiguas."""
    if isinstance(valor, dict):
        return valor
    return fallback or {}

def _safe_list(valor) -> list:
    """Convierte a list si no lo es."""
    if isinstance(valor, list):
        return valor
    if isinstance(valor, str) and valor:
        return [valor]
    return []

def _build_properties(idea: dict) -> dict:
    """Mapea la idea a los campos EXACTOS de tu BD Notion."""
    scores  = _safe_dict(idea.get("scores", {}))
    score_t = scores.get("score_total", 0)
    titulo  = f"[{score_t}] {idea.get('nombre','SinNombre')} — {idea.get('tagline','')}"
    tags    = _safe_list(idea.get("tags", []))

    props = {
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

    print(f"   Propiedades mapeadas: {list(props.keys())}")
    return props

# ════════════════════════════════════════════════════════
#  BLOQUES DEL CUERPO — con protección total de tipos
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
    scores = _safe_dict(idea.get("scores", {}))
    s_t    = scores.get("score_total", 0)

    # ── Resumen ejecutivo
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

    # ── Problema & Solución
    b.append(_b_h("❓ Problema & Solución", 2))
    b.append(_b_text(f"PROBLEMA: {idea.get('problema','')}"))
    b.append(_b_text(f"SOLUCIÓN: {idea.get('solucion','')}"))
    b.append(_b_text(f"CLIENTE: {idea.get('cliente_objetivo','')}"))
    b.append(_b_text(f"PROPUESTA DE VALOR ÚNICA: {idea.get('propuesta_valor_unica','')}"))
    b.append(_b_sep())

    # ── Mercado
    mercado = _safe_dict(idea.get("mercado", {}))
    if mercado:
        b.append(_b_h("🌍 Mercado", 2))
        b.append(_b_text(f"TAM: {mercado.get('TAM','')}"))
        b.append(_b_text(f"SAM: {mercado.get('SAM','')}"))
        b.append(_b_text(f"SOM: {mercado.get('SOM','')}"))
        b.append(_b_text(f"Ventaja competitiva: {mercado.get('ventaja_competitiva','')}"))
        for c in _safe_list(mercado.get("competidores", [])):
            b.append(_b_bullet(f"Competidor: {c}"))
        b.append(_b_sep())

    # ── Modelo de negocio
    mn = _safe_dict(idea.get("modelo_negocio", {}))
    if mn:
        b.append(_b_h("💰 Modelo de Negocio", 2))
        b.append(_b_text(f"Tipo: {mn.get('tipo','')}  |  Time to revenue: {mn.get('time_to_revenue','')}"))
        b.append(_b_text(f"Pricing: {mn.get('pricing','')}"))
        for canal in _safe_list(mn.get("canales_adquisicion", [])):
            b.append(_b_bullet(str(canal)))
        b.append(_b_sep())

    # ── Estudio económico
    eco = _safe_dict(idea.get("estudio_economico", {}))
    if eco:
        b.append(_b_h("📈 Estudio Económico", 2))
        for esc in ["conservador", "realista", "optimista"]:
            datos = _safe_dict(eco.get(esc, {}))
            if not datos:
                continue
            emoji = {"conservador": "🟡", "realista": "🟢", "optimista": "🚀"}.get(esc, "")
            b.append(_b_h(f"{emoji} Escenario {esc.capitalize()}", 3))
            b.append(_b_text(f"Supuestos: {datos.get('supuestos','')}"))
            m6  = _safe_dict(datos.get("mes6",  {}))
            m12 = _safe_dict(datos.get("mes12", {}))
            m24 = _safe_dict(datos.get("mes24", {}))
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

    # ── DAFO
    dafo = _safe_dict(idea.get("dafo", {}))
    if dafo:
        b.append(_b_h("⚡ DAFO", 2))
        b.append(_b_text("FORTALEZAS:"))
        for f in _safe_list(dafo.get("fortalezas", [])):
            b.append(_b_bullet(f"✅ {f}"))
        b.append(_b_text("DEBILIDADES:"))
        for d in _safe_list(dafo.get("debilidades", [])):
            b.append(_b_bullet(f"⚠️ {d}"))
        b.append(_b_text("OPORTUNIDADES:"))
        for o in _safe_list(dafo.get("oportunidades", [])):
            b.append(_b_bullet(f"🚀 {o}"))
        b.append(_b_text("AMENAZAS:"))
        for a in _safe_list(dafo.get("amenazas", [])):
            b.append(_b_bullet(f"🔴 {a}"))
        b.append(_b_sep())

    # ── MVP
    mvp = _safe_dict(idea.get("mvp", {}))
    if mvp:
        coste = mvp.get("coste_estimado_eur", 0)
        try:
            coste = float(coste)
            if coste > 10000:
                coste = 0
        except:
            coste = 0
        b.append(_b_h("🛠️ MVP", 2))
        b.append(_b_text(f"Stack: {mvp.get('stack_recomendado','')}"))
        b.append(_b_text(f"Tiempo: {mvp.get('tiempo_semanas','?')} semanas  |  Coste estimado: {coste}€"))
        for feat in _safe_list(mvp.get("features_minimas", [])):
            b.append(_b_bullet(str(feat)))
        b.append(_b_sep())

    # ── Estrategia de monetización
    em = _safe_dict(idea.get("estrategia_monetizacion", {}))
    if em:
        b.append(_b_h("💵 Estrategia de Monetización", 2))
        for key, label in [("semana1","Semana 1"),("semana4","Semana 4"),("mes3","Mes 3"),("mes6","Mes 6")]:
            if em.get(key):
                b.append(_b_bullet(f"{label}: {em[key]}"))
        if em.get("precio_optimo_justificado"):
            b.append(_b_text(f"Precio óptimo: {em['precio_optimo_justificado']}"))
        b.append(_b_sep())

    # ── Prompt MVP
    pm = _safe_dict(idea.get("prompt_mvp", {}))
    if pm:
        b.append(_b_h("🤖 PROMPT MVP — Copia en Cursor/Claude", 2))
        b.append(_b_text(f"IA recomendada: {pm.get('ia_recomendada','')}"))
        prompt_txt = str(pm.get("prompt_completo", ""))
        if prompt_txt:
            for chunk in [prompt_txt[i:i+1900] for i in range(0, len(prompt_txt), 1900)]:
                b.append(_b_code(chunk))
        b.append(_b_sep())

    # ── Opinión profesional
    op = idea.get("opinion_profesional", "")
    if op:
        b.append(_b_h("🎯 Opinión Profesional", 2))
        b.append(_b_text(str(op)))

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
    """Crea una página en Notion. Devuelve la URL o '' si falla."""
    nombre = idea.get("nombre", "SinNombre")
    print(f"📤 Sincronizando '{nombre}'...")

    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado")
        return ""

    # 1. Construir propiedades con los campos exactos de la BD
    try:
        properties = _build_properties(idea)
    except Exception as e:
        print(f"⚠️ Error construyendo propiedades: {e}")
        scores  = _safe_dict(idea.get("scores", {}))
        score_t = scores.get("score_total", 0)
        properties = {
            CAMPO_TITULO: {"title": [{"type": "text", "text": {
                "content": f"[{score_t}] {nombre}"
            }}]}
        }

    # 2. Construir bloques del cuerpo
    try:
        bloques = _construir_bloques(idea)[:100]
    except Exception as e:
        print(f"⚠️ Error construyendo bloques: {e}")
        bloques = [_b_text(f"Idea: {nombre} — Error generando contenido detallado: {e}")]

    # 3. Crear la página en Notion
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

            # Reintento solo con título si hay error de propiedades
            if resp.status_code == 400:
                print("🔄 Reintentando solo con título + cuerpo...")
                scores  = _safe_dict(idea.get("scores", {}))
                score_t = scores.get("score_total", 0)
                payload_min = {
                    "parent":     {"database_id": NOTION_DATABASE_ID},
                    "properties": {
                        CAMPO_TITULO: {"title": [{"type": "text", "text": {
                            "content": f"[{score_t}] {nombre} — {idea.get('tagline','')}"
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
