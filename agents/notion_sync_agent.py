"""
Notion Sync Agent - Sincroniza ideas.json con Notion Dashboard
"""
import os
import json
from datetime import datetime
import requests

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = "308313aca133809cb9fde119be25681d"

def _parse_revenue(value):
    """Extrae el número de revenue del campo (puede ser '1,500 conservador')"""
    try:
        if isinstance(value, (int, float)):
            return int(value)
        # Si es string, extraer solo los dígitos
        clean = str(value).replace(',', '').replace('€', '').strip()
        # Tomar solo la primera palabra (el número)
        number_str = clean.split()[0] if clean else '0'
        return int(number_str)
    except:
        return 0

def sync_idea_to_notion(idea):
    """Sincroniza una idea al dashboard de Notion"""
    
    headers = {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }
    
    # Construir propiedades de Notion (NOMBRES EXACTOS de tu database)
    properties = {
        "nombre": {"title": [{"text": {"content": idea.get('nombre', 'Sin nombre')}}]},
        "Score Generador": {"number": idea.get('score_generador', 0)},
        "Score Crítico": {"number": idea.get('score_critico', 0)},
        "Revenue Estimado (€/mes)": {"number": _parse_revenue(idea.get('revenue_6_meses', 0))},
        "Estado": {"select": {"name": "🆕 Nueva"}},
        "Prioridad": {"select": {"name": "🔥 Alta" if idea.get('viral_score', 0) > 80 else "⚡ Media"}},
        "Tags": {"multi_select": [{"name": "IA"}, {"name": "SaaS"}, {"name": "Viral"}]}
    }
    
    # Añadir URLs si existen
    if 'landing_url' in idea:
        properties["Landing Page"] = {"url": idea['landing_url']}
    if 'report_url' in idea:
        properties["Report Técnico"] = {"url": idea['report_url']}
    
    # Crear página en Notion
    data = {
        "parent": {"database_id": DATABASE_ID},
        "properties": properties
    }
    
    response = requests.post(
        "https://api.notion.com/v1/pages",
        headers=headers,
        json=data
    )
    
    if response.status_code == 200:
        print(f"✅ Idea '{idea.get('nombre')}' sincronizada a Notion")
        return response.json()
    else:
        print(f"❌ Error sincronizando a Notion: {response.text}")
        return None

def sync_all_ideas():
    """Sincroniza todas las ideas de ideas.json a Notion"""
    
    if not NOTION_TOKEN:
        print("⚠️ NOTION_TOKEN no configurado - saltando sync")
        return
    
    try:
        with open('data/ideas.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            ideas = data.get('ideas', [])
        
        print(f"\n📊 Sincronizando {len(ideas)} ideas a Notion...")
        
        for idea in ideas:
            sync_idea_to_notion(idea)
        
        print(f"✅ {len(ideas)} ideas sincronizadas")
        
    except Exception as e:
        print(f"❌ Error en sync: {str(e)}")

if __name__ == "__main__":
    sync_all_ideas()