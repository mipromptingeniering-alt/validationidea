import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT = os.environ.get("TELEGRAM_CHAT_ID")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def telegram_send(texto):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT:
        return
    try:
        requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT, "text": texto, "parse_mode": "HTML"},
            timeout=10,
        )
    except Exception:
        pass


def get_ideas_sin_informe():
    """Consulta Notion y devuelve ideas sin 'Informe Completo'."""
    url = f"https://api.notion.com/v1/databases/{NOTION_DB}/query"
    payload = {
        "filter": {
            "property": "Informe Completo",
            "rich_text": {"is_empty": True},
        },
        "page_size": 20,
    }
    r = requests.post(url, headers=HEADERS, json=payload, timeout=15)
    if r.status_code != 200:
        print(f"❌ Error consultando Notion: {r.status_code} {r.text[:200]}")
        return []
    return r.json().get("results", [])


def extraer_campos_idea(page):
    """Extrae todos los campos de una página de Notion."""
    props = page.get("properties", {})

    def get_text(prop_name):
        prop = props.get(prop_name, {})
        texts = prop.get("rich_text", prop.get("title", []))
        if texts:
            return texts[0].get("plain_text", texts[0].get("text", {}).get("content", ""))
        return ""

    def get_number(prop_name):
        return props.get(prop_name, {}).get("number", 0) or 0

    return {
        "page_id": page["id"],
        "nombre": get_text("Name"),
        "problema": get_text("Problem"),
        "solucion": get_text("Solution"),
        "descripcion": get_text("Description"),
        "propuesta_valor": get_text("Value"),
        "vertical": get_text("Target"),
        "monetizacion": get_text("Business"),
        "esfuerzo": get_text("MVP"),
        "como": get_text("Marketing"),
        "fortalezas": get_text("Strengths"),
        "debilidades": get_text("Weaknesses"),
        "score_critico": get_number("ScoreCritic"),
        "viral_score": get_number("ScoreViral"),
        "score_generador": get_number("ScoreGen"),
        "url": page.get("url", ""),
    }


def main():
    print("=" * 60)
    print("📊 RUN MONITOR — Generador de Informes Completos")
    print("=" * 60)

    from agents.analyzer_agent import generate_complete_report
    from agents.notion_updater_agent import write_report_to_notion

    ideas = get_ideas_sin_informe()

    if not ideas:
        print("✅ Todas las ideas tienen informe completo. Nada que hacer.")
        return

    print(f"📋 Ideas sin informe: {len(ideas)}")
    telegram_send(f"🔄 <b>Generando informes</b>\n📋 Ideas pendientes: {len(ideas)}")

    ok = 0
    errores = 0

    for i, page in enumerate(ideas, 1):
        idea = extraer_campos_idea(page)
        nombre = idea.get("nombre", "Sin nombre")
        page_id = idea.get("page_id")

        print(f"\n[{i}/{len(ideas)}] Procesando: {nombre}")

        if not nombre or nombre == "Sin nombre":
            print("   ⚠️  Sin nombre, saltando...")
            continue

        informe = generate_complete_report(idea)

        if not informe:
            print(f"   ❌ No se pudo generar informe para {nombre}")
            errores += 1
            time.sleep(10)
            continue

        exito = write_report_to_notion(page_id, informe)

        if exito:
            ok += 1
            url = idea.get("url", "")
            telegram_send(
                f"✅ <b>Informe completado</b>\n"
                f"💡 {nombre}\n"
                f"📝 ~{len(informe.split())} palabras\n"
                f"🔗 <a href='{url}'>Ver en Notion</a>"
            )
        else:
            errores += 1

        if i < len(ideas):
            print("   ⏳ Esperando 15s antes de la siguiente idea...")
            time.sleep(15)

    print(f"\n{'='*60}")
    print(f"✅ Completados: {ok} | ❌ Errores: {errores}")
    print(f"{'='*60}")
    telegram_send(
        f"🏁 <b>Monitor completado</b>\n"
        f"✅ Informes generados: {ok}\n"
        f"❌ Errores: {errores}"
    )


if __name__ == "__main__":
    main()

