"""
Notion Sync Agent: sincroniza ideas completas
"""
import os
import json
from notion_client import Client
from datetime import datetime

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = "308313ac-a133-8009-81cf-c48f32c52146"

def sync_idea_to_notion(idea):
    """Sincroniza idea completa a Notion"""
    
    print(f"📤 Sincronizando '{idea.get('nombre', 'Sin nombre')}' a Notion...")
    
    # Reporte técnico
    report = f"""# TECHNICAL REPORT

Score: {idea.get('score_critico', 0)}/100 | Viral: {idea.get('viral_score', 0)}/100

## DESCRIPTION
{idea.get('descripcion', 'N/A')}

## ANALYSIS
Problem: {idea.get('problema', 'N/A')}
Solution: {idea.get('solucion', 'N/A')}
Target: {idea.get('publico_objetivo', 'N/A')}

## BUSINESS
Model: {idea.get('modelo_negocio', 'N/A')}
Value: {idea.get('propuesta_valor', 'N/A')}

## EXECUTION
MVP: {idea.get('mvp', 'N/A')}
KPIs: {idea.get('metricas_clave', 'N/A')}
Marketing: {idea.get('canales_marketing', 'N/A')}
Next 30d: {idea.get('proximos_pasos', 'N/A')}

## RISKS
{idea.get('riesgos', 'N/A')}
"""
    
    # Propiedades con nombres EN INGLÉS
    properties = {
        "Name": {"title": [{"text": {"content": idea.get("nombre", "Untitled")[:100]}}]},
    }
    
    def add_text(key, value):
        if value:
            properties[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
    
    add_text("Description", idea.get("descripcion"))
    add_text("Problem", idea.get("problema"))
    add_text("Solution", idea.get("solucion"))
    add_text("Target", idea.get("publico_objetivo"))
    add_text("Business", idea.get("modelo_negocio"))
    add_text("MVP", idea.get("mvp"))
    add_text("Value", idea.get("propuesta_valor"))
    add_text("Metrics", idea.get("metricas_clave"))
    add_text("Risks", idea.get("riesgos"))
    add_text("Marketing", idea.get("canales_marketing"))
    add_text("NextSteps", idea.get("proximos_pasos"))
    add_text("Report", report)
    
    # Números
    properties["ScoreGen"] = {"number": idea.get("score_generador", 0)}
    properties["ScoreCritic"] = {"number": idea.get("score_critico", 0)}
    properties["ScoreViral"] = {"number": idea.get("viral_score", 0)}
    
    # Crítica
    critique = idea.get("critique", {})
    if critique.get("puntos_fuertes"):
        add_text("Strengths", "\n• ".join(critique["puntos_fuertes"]))
    if critique.get("puntos_debiles"):
        add_text("Weaknesses", "\n• ".join(critique["puntos_debiles"]))
    
    # Research
    if idea.get("research"):
        add_text("Research", json.dumps(idea["research"], indent=2, ensure_ascii=False))
    
    # Fecha
    properties["Date"] = {"date": {"start": datetime.now().isoformat()}}
    
    # Tags
    tags = []
    if idea.get("viral_score", 0) >= 85:
        tags.append({"name": "Viral"})
    if idea.get("score_critico", 0) >= 85:
        tags.append({"name": "Quality"})
    
    if tags:
        properties["Tags"] = {"multi_select": tags}
    
    # Crear página
    try:
        page = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
        print(f"✅ Sincronizado: {page['url']}")
        return page
    except Exception as e:
        print(f"❌ Error: {e}")
        return None