import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def text_prop(value):
    if not value:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def sync_idea_to_notion(idea):
    try:
        score = idea.get("score_critico", 0) or 0
        viral = idea.get("viral_score", 0) or 0
        gen = idea.get("score_generador", 0) or 0

        if score >= 90:
            emoji = "💎"
        elif score >= 85:
            emoji = "⭐"
        elif score >= 80:
            emoji = "🔥"
        else:
            emoji = "💡"

        nombre = idea.get("nombre", "Sin titulo")
        print(f"📤 Sincronizando '{nombre}' a Notion...")

        fortalezas = idea.get("fortalezas", idea.get("puntos_fuertes", []))
        debilidades = idea.get("debilidades", idea.get("puntos_debiles", []))

        if isinstance(fortalezas, str):
            fortalezas = [fortalezas]
        if isinstance(debilidades, str):
            debilidades = [debilidades]

        fortalezas_text = "\n• ".join(fortalezas) if fortalezas else ""
        debilidades_text = "\n• ".join(debilidades) if debilidades else ""

        report_lines = [
            f"📊 ANALISIS - {nombre}",
            f"🎯 Score Critico: {score}/100",
            f"🚀 Score Viral: {viral}/100",
            f"⚙️  Score Generador: {gen}/100",
            "",
            "✅ FORTALEZAS:",
        ]
        for f in fortalezas[:3]:
            report_lines.append(f"  • {f}")
        report_lines.append("")
        report_lines.append("⚠️ DEBILIDADES:")
        for d in debilidades[:3]:
            report_lines.append(f"  • {d}")

        tags = []
        if score >= 90:
            tags.append({"name": "💎 Excepcional"})
        elif score >= 85:
            tags.append({"name": "⭐ Premium"})
        elif score >= 80:
            tags.append({"name": "🔥 Calidad"})
        if viral >= 85:
            tags.append({"name": "🚀 Viral"})

        properties = {
            "Name": {
                "title": [{"text": {"content": f"{emoji} {nombre[:95]}"}}]
            },
            "Description": text_prop(idea.get("descripcion")),
            "Problem": text_prop(idea.get("problema")),
            "Solution": text_prop(idea.get("solucion")),
            "Value": text_prop(idea.get("propuesta_valor")),
            "Target": text_prop(idea.get("vertical")),
            "Business": text_prop(idea.get("monetizacion")),
            "MVP": text_prop(idea.get("esfuerzo")),
            "Marketing": text_prop(idea.get("como")),
            "Strengths": text_prop(fortalezas_text),
            "Weaknesses": text_prop(debilidades_text),
            "Report": text_prop("\n".join(report_lines)),
            "ScoreGen": {"number": int(gen)},
            "ScoreCritic": {"number": int(score)},
            "ScoreViral": {"number": int(viral)},
            "Date": {"date": {"start": idea.get("fecha") or datetime.now().isoformat()}},
        }

        if tags:
            properties["Tags"] = {"multi_select": tags}

        payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": properties,
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )

        if response.status_code == 200 or response.status_code == 201:
            page = response.json()
            url = page.get("url", "")
            print(f"✅ Sincronizado: {url}")
            return page
        else:
            print(f"❌ Error Notion {response.status_code}: {response.text[:300]}")
            return None

    except Exception as e:
        print(f"❌ Error Notion: {e}")
        import traceback
        traceback.print_exc()
        return None
