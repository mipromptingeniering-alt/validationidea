"""
Script de una sola ejecución para poblar la Knowledge Base
con las ideas existentes en Notion.
Ejecutar: python poblar_knowledge_base.py
"""
import os
import requests
from dotenv import load_dotenv
from agents.knowledge_base import aprender, get_stats

load_dotenv()

NOTION_API_KEY     = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
NOTION_VERSION     = "2022-06-28"


def _h():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def get_todas() -> list:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    ideas, cursor = [], None
    while True:
        body = {"page_size": 100}
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
    p  = props.get(key, {})
    rt = p.get("rich_text") or p.get("title") or []
    return " ".join(t.get("plain_text", "") for t in rt).strip()


def get_num(props, key):
    return props.get(key, {}).get("number")


def main():
    print("=" * 50)
    print("poblar_knowledge_base.py")
    print("Importando ideas de Notion a la KB local...")
    print("=" * 50)

    ideas     = get_todas()
    procesadas = 0
    sin_score  = 0

    for page in ideas:
        props  = page.get("properties", {})
        nombre = get_txt(props, "Name") or "Sin nombre"

        # Buscar score en ScoreGen primero, luego en Score (campo antiguo)
        score = get_num(props, "ScoreGen")
        if score is None:
            score = get_num(props, "Score")

        if score is None:
            sin_score += 1
            print(f"  ⏭️  {nombre}: sin score, saltando")
            continue

        # Construir objeto idea para la KB
        tipo     = get_txt(props, "Type")     or get_txt(props, "Tags") or "SaaS"
        vertical = get_txt(props, "Target")   or get_txt(props, "Vertical") or "General"
        valor    = get_txt(props, "Value")    or ""

        idea = {
            "nombre":          nombre,
            "tipo":            tipo[:50] if tipo else "SaaS",
            "vertical":        vertical[:50] if vertical else "General",
            "propuesta_valor": valor,
        }

        aprender(idea, int(score))
        print(f"  ✅ {nombre}: score={int(score)}")
        procesadas += 1

    print("\n" + "=" * 50)
    print(f"Procesadas: {procesadas} | Sin score: {sin_score}")

    # Mostrar estadísticas finales
    kb = get_stats()
    print(f"\n📊 Knowledge Base actualizada:")
    print(f"  Total analizadas: {kb['total']}")
    print(f"  Exitosas (>75):   {kb['exitosas']}")
    print(f"  Mejor tipo:       {kb['mejor_tipo']}")
    print(f"  Mejor vertical:   {kb['mejor_vertical']}")
    print(f"\nArchivo: data/knowledge_base.json")


if __name__ == "__main__":
    main()
