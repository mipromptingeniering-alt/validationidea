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
    return {"rich_text": [{"text": {"content": str(value)[:1990]}}]}

def sync_idea_to_notion(idea):
    try:
        score   = idea.get("score_critico", 0)
        viral   = idea.get("viral_score", 0)
        gen     = idea.get("score_generador", 0)
        money   = idea.get("score_money", 0)
        general = idea.get("score_general", 0)
        nombre  = idea.get("nombre", "Sin titulo")

        emoji = "💎" if score >= 90 else "⭐" if score >= 85 else "🔥" if score >= 80 else "💡"
        print(f"📤 Sincronizando '{nombre}'...")

        # Leer esquema real de Notion
        db_resp = requests.get(
            f"https://api.notion.com/v1/databases/{DATABASE_ID}",
            headers=HEADERS, timeout=10
        )
        props_db = db_resp.json().get("properties", {}) if db_resp.status_code == 200 else {}

        # Propiedades base (siempre existen)
        properties = {
            "Name":       {"title": [{"text": {"content": f"{emoji} {nombre[:90]}"}}]},
            "ScoreCritic": {"number": int(score)},
            "ScoreGen":    {"number": int(gen)},
            "ScoreViral":  {"number": int(viral)},
            "Date":        {"date": {"start": datetime.now().isoformat()}},
        }

        # Propiedades opcionales (solo si existen en tu DB)
        opcionales = {
            "Description": idea.get("descripcion", ""),
            "Problem":     idea.get("problema", ""),
            "Solution":    idea.get("solucion", ""),
            "Value":       idea.get("propuesta_valor", ""),
            "Target":      idea.get("vertical", ""),
            "Business":    idea.get("monetizacion", ""),
            "MVP":         idea.get("mvp", idea.get("esfuerzo", "")),
            "Marketing":   idea.get("marketing", idea.get("como", "")),
            "Strengths":   "\n".join([f"• {f}" for f in idea.get("puntos_fuertes", [])[:4]]),
            "Weaknesses":  "\n".join([f"• {d}" for d in idea.get("puntos_debiles", [])[:4]]),
            "Report":      "📄 Informe creado",
        }

        for campo, valor in opcionales.items():
            if campo in props_db:
                properties[campo] = text_prop(valor)

        if "ScoreMoney" in props_db:
            properties["ScoreMoney"] = {"number": int(money)}

        if "Tags" in props_db:
            tags = []
            if score >= 90: tags.append({"name": "💎 Excepcional"})
            elif score >= 85: tags.append({"name": "⭐ Premium"})
            elif score >= 80: tags.append({"name": "🔥 Alta calidad"})
            if viral >= 80: tags.append({"name": "🚀 Viral"})
            if tags:
                properties["Tags"] = {"multi_select": tags}

        # Construir bloques del informe (aparecen DENTRO de la página)
        fortalezas = idea.get("puntos_fuertes", [])[:4]
        debilidades = idea.get("puntos_debiles", [])[:4]

        bloques_informe = [
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "heading_1", "heading_1": {
                "rich_text": [{"type": "text", "text": {"content": f"📊 INFORME COMPLETO — {nombre.upper()}"}}]
            }},
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📋 Resumen ejecutivo"}}]
            }},
            {"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": idea.get("descripcion", "")[:400]}}]
            }},
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "📈 Scores"}}]
            }},
            {"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content":
                    f"🏆 General: {general:.1f}/100  |  🎯 Crítico: {score}  |  🚀 Viral: {viral}  |  ⚙️ Generador: {gen}  |  💰 Money: {money}"
                }}]
            }},
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "🎯 DAFO"}}]
            }},
            {"object": "block", "type": "heading_3", "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "✅ Fortalezas"}}]
            }},
        ]

        for f in fortalezas:
            bloques_informe.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": f}}]}
            })

        bloques_informe.append({
            "object": "block", "type": "heading_3", "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "⚠️ Debilidades"}}]
            }
        })

        for d in debilidades:
            bloques_informe.append({
                "object": "block", "type": "bulleted_list_item",
                "bulleted_list_item": {"rich_text": [{"type": "text", "text": {"content": d}}]}
            })

        bloques_informe.extend([
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "🏗️ Cómo construir el MVP (30 días)"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Días 1-7: Landing page + formulario de leads"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": f"Días 8-20: {idea.get('solucion','Core del producto')[:100]}"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Días 21-30: 100 usuarios beta + iteración"}}]
            }},
            {"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": "💻 Stack recomendado: Next.js + Supabase + Vercel (~20€/mes)"}}]
            }},
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "💰 Modelo de negocio y previsión"}}]
            }},
            {"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"Modelo: {idea.get('monetizacion', 'SaaS por suscripción')}"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Plan Free: 0€ — captación"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Plan Pro: 9,99€/mes — funciones completas"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Plan Team: 29€/mes — equipos"}}]
            }},
            {"object": "block", "type": "heading_3", "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "📊 Previsión económica año 1"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Mes 1-3: Validación, 0€ (invertir tiempo)"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Mes 4-6: 100 usuarios Pro → ~1.000€/mes"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Mes 7-12: 500 usuarios → ~5.000€/mes"}}]
            }},
            {"object": "block", "type": "bulleted_list_item", "bulleted_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Break-even estimado: mes 5"}}]
            }},
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "🗺️ Roadmap 90 días"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Sprint 1 (30d): MVP + 100 beta"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Sprint 2 (60d): 500 usuarios + plan Pro activo"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Sprint 3 (90d): 2.000 usuarios + plan Team"}}]
            }},
            {"object": "block", "type": "heading_2", "heading_2": {
                "rich_text": [{"type": "text", "text": {"content": "👨‍💼 Mi opinión profesional"}}]
            }},
            {"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content":
                    f"{idea.get('resumen', 'Idea con potencial real.')} "
                    f"Con un score de {general:.1f}/100, "
                    f"{'recomiendo lanzar YA.' if general >= 85 else 'recomiendo validar con 50 entrevistas antes de construir.' if general >= 75 else 'necesita más investigación de mercado.'}"
                }}]
            }},
            {"object": "block", "type": "heading_3", "heading_3": {
                "rich_text": [{"type": "text", "text": {"content": "✅ Próximos pasos inmediatos"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Crear landing page en 48 horas (Carrd o Webflow)"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Hacer 50 entrevistas a posibles clientes (1 semana)"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Construir MVP v1 en 3 semanas"}}]
            }},
            {"object": "block", "type": "numbered_list_item", "numbered_list_item": {
                "rich_text": [{"type": "text", "text": {"content": "Conseguir 10 primeros clientes pagando"}}]
            }},
            {"object": "block", "type": "divider", "divider": {}},
            {"object": "block", "type": "paragraph", "paragraph": {
                "rich_text": [{"type": "text", "text": {"content":
                    f"🤖 Generado por validationidea AI — {datetime.now().strftime('%d/%m/%Y %H:%M')}"
                }, "annotations": {"italic": True, "color": "gray"}}]
            }},
        ])

        # Crear página en Notion con bloques dentro
        payload = {
            "parent": {"database_id": DATABASE_ID},
            "properties": properties,
            "children": bloques_informe,
        }

        response = requests.post(
            "https://api.notion.com/v1/pages",
            headers=HEADERS, json=payload, timeout=30
        )

        if response.status_code in (200, 201):
            page = response.json()
            print(f"✅ Sincronizado: {page.get('url')}")
            print(f"📄 Informe COMPLETO escrito en la página")
            return page
        else:
            print(f"❌ Error {response.status_code}: {response.text[:300]}")
            return None

    except Exception as e:
        print(f"❌ Error notion_sync: {e}")
        return None
