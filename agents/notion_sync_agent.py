cd C:\Users\juanj\Documents\validationidea

@"
import os
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
DATABASE_ID  = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")

HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def text_prop(value):
    if not value:
        return {"rich_text": []}
    return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}


def _get_db_properties():
    """Obtiene las propiedades existentes en la DB de Notion."""
    try:
        r = requests.get(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}",
            headers=HEADERS, timeout=10
        )
        if r.status_code == 200:
            return set(r.json().get("properties", {}).keys())
    except Exception:
        pass
    return set()


def sync_idea_to_notion(idea):
    try:
        score = idea.get("score_critico",   0) or 0
        viral = idea.get("viral_score",     0) or 0
        gen   = idea.get("score_generador", 0) or 0
        money = idea.get("score_money",     0) or 0

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

        fortalezas  = idea.get("fortalezas",  idea.get("puntos_fuertes",  []))
        debilidades = idea.get("debilidades", idea.get("puntos_debiles", []))
        if isinstance(fortalezas,  str): fortalezas  = [fortalezas]
        if isinstance(debilidades, str): debilidades = [debilidades]

        fortalezas_text  = "\n• ".join(fortalezas)  if fortalezas  else ""
        debilidades_text = "\n• ".join(debilidades) if debilidades else ""

        report_lines = [
            f"📊 ANALISIS - {nombre}",
            f"🎯 Score Critico:   {score}/100",
            f"🚀 Score Viral:     {viral}/100",
            f"⚙️  Score Generador: {gen}/100",
            f"💰 Score Money:     {money}/100",
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
        if money >= 85:
            tags.append({"name": "💰 Alto Money"})

        # Propiedades base — siempre existen
        properties = {
            "Name":        {"title": [{"text": {"content": f"{emoji} {nombre[:95]}"}}]},
            "Description": text_prop(idea.get("descripcion")),
            "Problem":     text_prop(idea.get("problema")),
            "Solution":    text_prop(idea.get("solucion")),
            "Value":       text_prop(idea.get("propuesta_valor")),
            "Target":      text_prop(idea.get("vertical")),
            "Business":    text_prop(idea.get("monetizacion") or idea.get("modelo_negocio")),
            "MVP":         text_prop(idea.get("esfuerzo") or idea.get("mvp")),
            "Marketing":   text_prop(idea.get("como") or idea.get("marketing")),
            "Strengths":   text_prop(fortalezas_text),
            "Weaknesses":  text_prop(debilidades_text),
            "Report":      text_prop("\n".join(report_lines)),
            "ScoreGen":    {"number": int(gen)},
            "ScoreCritic": {"number": int(score)},
            "ScoreViral":  {"number": int(viral)},
            "Date":        {"date": {"start": idea.get("fecha") or datetime.now().isoformat()}},
        }

        if tags:
            properties["Tags"] = {"multi_select": tags}

        # ScoreMoney: solo añadir si existe en la DB de Notion
        db_props = _get_db_properties()
        if "ScoreMoney" in db_props:
            properties["ScoreMoney"] = {"number": int(money)}
        else:
            print("⚠️ ScoreMoney no existe en Notion DB — omitido (crear campo manualmente)")

        payload = {
            "parent":     {"database_id": DATABASE_ID},
            "properties": properties,
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS,
            json=payload,
            timeout=30,
        )

        if response.status_code in (200, 201):
            page = response.json()
            url  = page.get("url", "")
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
"@ | Set-Content agents\notion_sync_agent.py -Encoding UTF8

# Quitar BOM
$c = Get-Content agents\notion_sync_agent.py -Raw
$c = $c.TrimStart([char]0xFEFF)
[System.IO.File]::WriteAllText((Resolve-Path agents\notion_sync_agent.py), $c, [System.Text.UTF8Encoding]::new($false))

python -c "import ast; ast.parse(open('agents/notion_sync_agent.py', encoding='utf-8').read()); print('Sintaxis OK')"
