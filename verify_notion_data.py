import sys
sys.path.insert(0, 'agents')
from notion_sync_agent import sync_idea_to_notion
import json

with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)

prospectaflow = None
for idea in data['ideas']:
    if 'Prospectaflow' in idea.get('nombre', ''):
        prospectaflow = idea
        break

if prospectaflow:
    print("\n=== DATOS LOCALES ===")
    print(f"fortalezas: {prospectaflow.get('fortalezas')}")
    print(f"debilidades: {prospectaflow.get('debilidades')}")
    
    # Simular exactamente lo que hace notion_sync
    fortalezas = prospectaflow.get("fortalezas", [])
    debilidades = prospectaflow.get("debilidades", [])
    
    if fortalezas:
        strengths = "\n• ".join(fortalezas)
        print(f"\n=== LO QUE SE ENVÍA A NOTION (Strengths) ===")
        print(strengths)
    
    if debilidades:
        weaknesses = "\n• ".join(debilidades)
        print(f"\n=== LO QUE SE ENVÍA A NOTION (Weaknesses) ===")
        print(weaknesses)
