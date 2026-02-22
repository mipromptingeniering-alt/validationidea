import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

from agents.analyzer_agent import generate_complete_report
from agents.notion_updater_agent import write_report_to_notion

NOTION_API_KEY     = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
NOTION_VERSION     = "2022-06-28"


def _h():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def get_ideas_sin_informe() -> list:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    ideas, cursor = [], None
    while True:
        body = {
            "page_size": 100,
            "filter": {
                "property": "Informe Completo",
                "rich_text": {"is_empty": True}
            }
        }
        if cursor:
            body["start_cursor"] = cursor
        try:
            r = requests.post(url, headers=_h(), json=body, timeout=30)
            data = r.json()
            ideas.extend(data.get("results", []))
            if not data.get("has_more"):
                break
            cursor = data.get("next_cursor")
        except Exception as e:
            print(f"[Monitor] Error consultando Notion: {e}")
            break
    return ideas


def extraer_idea(page: dict) -> dict:
    props = page.get("properties", {})

    def txt(k):
        p = props.get(k, {})
        rt = p.get("rich_text") or p.get("title") or []
        return " ".join(t.get("plain_text", "") for t in rt).strip()

    def num(k):
        return props.get(k, {}).get("number")

    return {
        "nombre":          txt("Name"),
        "problema":        txt("Problem"),
        "solucion":        txt("Solution"),
        "propuesta_valor": txt("Value"),
        "target":          txt("Target"),
        "mvp":             txt("MVP"),
        "marketing":       txt("Marketing"),
        "negocio":         txt("Business"),
        "fortalezas":      txt("Strengths"),
        "debilidades":     txt("Weaknesses"),
        "riesgos":         txt("Risks"),
        "score_gen":       num("ScoreGen"),
        "score_viral":     num("ScoreViral"),
        "score_critico":   num("ScoreCritic"),
    }


def main():
    print("=" * 50)
    print("run_monitor.py — Generador de informes completos")
    print("=" * 50)

    ideas = get_ideas_sin_informe()
    total = len(ideas)
    print(f"Ideas sin informe: {total}")

    if not total:
        print("✅ Nada que procesar.")
        return

    exito = 0
    for i, page in enumerate(ideas, 1):
        idea = extraer_idea(page)
        nombre = idea["nombre"] or "Sin nombre"
        print(f"\n[{i}/{total}] ➜ {nombre}")

        try:
            informe = generate_complete_report(idea)
            if informe:
                write_report_to_notion(page["id"], informe)
                exito += 1
                print(f"  ✅ Informe listo")
            else:
                print(f"  ⚠️  LLM no respondió para '{nombre}'")
        except Exception as e:
            print(f"  ❌ Error: {e}")

        if i < total:
            time.sleep(5)

    print(f"\n{'='*50}")
    print(f"✅ {exito}/{total} informes generados")


if __name__ == "__main__":
    main()
