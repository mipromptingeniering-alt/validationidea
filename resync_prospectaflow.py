import sys
sys.path.insert(0, 'agents')
from notion_sync_agent import sync_idea_to_notion
import json

# Cargar Prospectaflow del JSON
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

prospectaflow = None
for idea in data['ideas']:
    if 'Prospectaflow' in idea.get('nombre', ''):
        prospectaflow = idea
        break

if prospectaflow:
    print(f"Datos locales de Prospectaflow:")
    print(f"  fortalezas: {prospectaflow.get('fortalezas')}")
    print(f"  debilidades: {prospectaflow.get('debilidades')}")
    print("\nSincronizando...")
    sync_idea_to_notion(prospectaflow)
else:
    print("❌ No se encontró Prospectaflow")
