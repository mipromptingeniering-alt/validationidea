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

def _get_title_property_name() -> str:
    """Consulta el esquema real de la BD y devuelve el nombre del campo título."""
    try:
        resp = requests.get(
            f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}",
            headers=_headers(), timeout=10
        )
        if resp.status_code == 200:
            props = resp.json().get("properties", {})
            for name, prop in props.items():
                if prop.get("type") == "title":
                    return name
    except Exception as e:
        print(f"⚠️ Error consultando esquema Notion: {e}")
    return "Name"  # fallback universal

def _bloque_texto(texto: str, tipo: str = "paragraph") -> dict:
    return {
        "object": "block",
        "type": tipo,
        tipo: {
            "rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]
        }
    }

def _bloque_heading(texto: str, nivel: int = 2) -> dict:
    tipo = f"heading_{nivel}"
    return {
        "object": "block",
        "type": tipo,
        tipo: {
            "rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]
        }
    }

def _bloque_separador() -> dict:
    return {"object": "block", "type": "divider", "divider": {}}

def _bullet(texto: str) -> dict:
    return {
        "object": "block",
        "type": "bulleted_list_item",
        "bulleted_list_item": {
            "rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}]
        }
    }

def _codigo(texto: str) -> dict:
    return {
        "object": "block",
        "type": "code",
        "code": {
            "rich_text": [{"type": "text", "text": {"content": str(texto)[:2000]}}],
            "language": "plain text"
        }
    }

def _construir_bloques(idea: dict) -> list:
    bloques = []
    scores  = idea.get("scores", {})
    score_t = scores.get("score_total", 0)

    # — Resumen ejecutivo
    bloques.append(_bloque_heading("📊 RESUMEN EJECUTIVO", 1))
    bloques.append(_bloque_texto(
        f"Vertical: {idea.get('vertical','N/A')}  |  Tipo: {idea.get('tipo','N/A')}  |  Score total: {score_t}/100\n"
        f"Tagline: {idea.get('tagline','')}"
    ))
    bloques.append(_bloque_texto(
        f"Scores detalle — "
        f"Crítico: {scores.get('critico',0)} | "
        f"Viral: {scores.get('viral',0)} | "
        f"Generador: {scores.get('generador',0)} | "
        f"Monetización: {scores.get('monetizacion',0)} | "
        f"Ejecutabilidad: {scores.get('ejecutabilidad',0)} | "
        f"Timing: {scores.get('timing',0)}"
    ))
    bloques.append(_bloque_separador())

    # — Problema y solución
    bloques.append(_bloque_heading("❓ Problema & Solución", 2))
    bloques.append(_bloque_texto(f"PROBLEMA: {idea.get('problema','')}"))
    bloques.append(_bloque_texto(f"SOLUCIÓN: {idea.get('solucion','')}"))
    bloques.append(_bloque_texto(f"CLIENTE: {idea.get('cliente_objetivo','')}"))
    bloques.append(_bloque_texto(f"PROPUESTA DE VALOR ÚNICA: {idea.get('propuesta_valor_unica','')}"))
    bloques.append(_bloque_separador())

    # — Mercado
    mercado = idea.get("mercado", {})
    if mercado:
        bloques.append(_bloque_heading("🌍 Mercado", 2))
        bloques.append(_bloque_texto(f"TAM: {mercado.get('TAM','')}"))
        bloques.append(_bloque_texto(f"SAM: {mercado.get('SAM','')}"))
        bloques.append(_bloque_texto(f"SOM: {mercado.get('SOM','')}"))
        bloques.append(_bloque_texto(f"Ventaja competitiva: {mercado.get('ventaja_competitiva','')}"))
        for c in mercado.get("competidores", []):
            bloques.append(_bullet(f"Competidor: {c}"))
        bloques.append(_bloque_separador())

    # — Modelo de negocio
    mn = idea.get("modelo_negocio", {})
    if mn:
        bloques.append(_bloque_heading("💰 Modelo de Negocio", 2))
        bloques.append(_bloque_texto(f"Tipo: {mn.get('tipo','')}  |  Time to revenue: {mn.get('time_to_revenue','')}"))
        bloques.append(_bloque_texto(f"Pricing: {mn.get('pricing','')}"))
        for canal in mn.get("canales_adquisicion", []):
            bloques.append(_bullet(canal))
        bloques.append(_bloque_separador())

    # — Estudio económico
    eco = idea.get("estudio_economico", {})
    if eco:
        bloques.append(_bloque_heading("📈 Estudio Económico", 2))
        for escenario in ["conservador", "realista", "optimista"]:
            datos = eco.get(escenario, {})
            if datos:
                emoji = {"conservador": "🟡", "realista": "🟢", "optimista": "🚀"}.get(escenario, "")
                bloques.append(_bloque_heading(f"{emoji} Escenario {escenario.capitalize()}", 3))
                bloques.append(_bloque_texto(f"Supuestos: {datos.get('supuestos','')}"))
                mes6  = datos.get("mes6",  {})
                mes12 = datos.get("mes12", {})
                mes24 = datos.get("mes24", {})
                if mes6:
                    bloques.append(_bloque_texto(
                        f"Mes 6 → MRR: {mes6.get('mrr_eur','?')}€ | "
                        f"Usuarios: {mes6.get('usuarios','?')} | "
                        f"CAC: {mes6.get('cac_eur','?')}€ | "
                        f"LTV: {mes6.get('ltv_eur','?')}€"
                    ))
                if mes12:
                    bloques.append(_bloque_texto(
                        f"Mes 12 → MRR: {mes12.get('mrr_eur','?')}€ | "
                        f"Usuarios: {mes12.get('usuarios','?')} | "
                        f"Margen: {mes12.get('margen_pct','?')}%"
                    ))
                if mes24:
                    bloques.append(_bloque_texto(
                        f"Mes 24 → MRR: {mes24.get('mrr_eur','?')}€ | "
                        f"ARR: {mes24.get('arr_eur','?')}€ | "
                        f"Breakeven: {mes24.get('breakeven','?')}"
                    ))
        bloques.append(_bloque_separador())

    # — DAFO
    dafo = idea.get("dafo", {})
    if dafo:
        bloques.append(_bloque_heading("⚡ DAFO", 2))
        bloques.append(_bloque_texto("FORTALEZAS:"))
        for f in dafo.get("fortalezas", []):
            bloques.append(_bullet(f"✅ {f}"))
        bloques.append(_bloque_texto("DEBILIDADES:"))
        for d in dafo.get("debilidades", []):
            bloques.append(_bullet(f"⚠️ {d}"))
        bloques.append(_bloque_texto("OPORTUNIDADES:"))
        for o in dafo.get("oportunidades", []):
            bloques.append(_bullet(f"🚀 {o}"))
        bloques.append(_bloque_texto("AMENAZAS:"))
        for a in dafo.get("amenazas", []):
            bloques.append(_bullet(f"🔴 {a}"))
        bloques.append(_bloque_separador())

    # — MVP
    mvp = idea.get("mvp", {})
    if mvp:
        bloques.append(_bloque_heading("🛠️ MVP", 2))
        bloques.append(_bloque_texto(f"Stack: {mvp.get('stack_recomendado','')}"))
        bloques.append(_bloque_texto(f"Tiempo: {mvp.get('tiempo_semanas','?')} semanas  |  Coste: {mvp.get('coste_estimado_eur','?')}€"))
        for feat in mvp.get("features_minimas", []):
            bloques.append(_bullet(feat))
        bloques.append(_bloque_separador())

    # — Estrategia de monetización
    em = idea.get("estrategia_monetizacion", {})
    if em:
        bloques.append(_bloque_heading("💵 Estrategia de Monetización", 2))
        for key, label in [("semana1","Semana 1"),("semana4","Semana 4"),("mes3","Mes 3"),("mes6","Mes 6")]:
            if em.get(key):
                bloques.append(_bullet(f"{label}: {em[key]}"))
        if em.get("precio_optimo_justificado"):
            bloques.append(_bloque_texto(f"Precio óptimo: {em['precio_optimo_justificado']}"))
        bloques.append(_bloque_separador())

    # — Prompt MVP (el más importante para ejecutar)
    pm = idea.get("prompt_mvp", {})
    if pm:
        bloques.append(_bloque_heading("🤖 PROMPT MVP — Copia en Cursor/Claude", 2))
        bloques.append(_bloque_texto(f"IA recomendada: {pm.get('ia_recomendada','')}"))
        prompt_txt = pm.get("prompt_completo", "")
        if prompt_txt:
            # Dividir en chunks de 2000 chars para respetar el límite de Notion
            chunks = [prompt_txt[i:i+1900] for i in range(0, len(prompt_txt), 1900)]
            for chunk in chunks:
                bloques.append(_codigo(chunk))
        bloques.append(_bloque_separador())

    # — Opinión profesional
    op = idea.get("opinion_profesional", "")
    if op:
        bloques.append(_bloque_heading("🎯 Opinión Profesional", 2))
        bloques.append(_bloque_texto(op))

    return bloques

def _guardar_en_cola(idea: dict, error: str):
    """Guarda en CSV local si Notion falla para reintentar después."""
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
        print(f"❌ Error guardando cola CSV: {e}")

def sync_idea_to_notion(idea: dict) -> str:
    """Crea una página en Notion con todo el contenido. Devuelve la URL o '' si falla."""
    nombre = idea.get("nombre", "SinNombre")
    print(f"📤 Sincronizando '{nombre}'...")

    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado")
        return ""

    # 1. Obtener nombre real del campo título en esta BD
    title_prop = _get_title_property_name()
    print(f"   Campo título detectado: '{title_prop}'")

    # 2. Construir los bloques del cuerpo
    try:
        bloques = _construir_bloques(idea)
    except Exception as e:
        print(f"⚠️ Error construyendo bloques: {e}")
        bloques = [_bloque_texto(f"Error generando contenido: {e}")]

    # Notion permite máx 100 bloques por request
    bloques_trunc = bloques[:100]

    # 3. Crear la página
    scores  = idea.get("scores", {})
    score_t = scores.get("score_total", 0)
    titulo  = f"[{score_t}] {nombre} — {idea.get('tagline', '')}"

    payload = {
        "parent":     {"database_id": NOTION_DATABASE_ID},
        "properties": {
            title_prop: {
                "title": [{"type": "text", "text": {"content": titulo[:200]}}]
            }
        },
        "children": bloques_trunc
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
            error_msg = resp.text[:300]
            print(f"❌ Error {resp.status_code}: {error_msg}")
            _guardar_en_cola(idea, error_msg)
            return ""
    except Exception as e:
        print(f"❌ Excepción Notion: {e}")
        _guardar_en_cola(idea, str(e))
        return ""

# aqui finaliza el codigo de agents/notion_sync_agent.py
