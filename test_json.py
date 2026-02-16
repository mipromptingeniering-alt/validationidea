import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    if data['ideas']:
        idea = data['ideas'][-1]
        print("="*60)
        print("ÚLTIMA IDEA EN JSON LOCAL:")
        print("="*60)
        print(f"Nombre: {idea.get('nombre', 'N/A')}")
        print(f"Fortalezas: {idea.get('fortalezas', 'N/A')[:200] if idea.get('fortalezas') else 'VACÍO'}")
        print(f"Debilidades: {idea.get('debilidades', 'N/A')[:200] if idea.get('debilidades') else 'VACÍO'}")
        print(f"Problema: {idea.get('problema', 'N/A')[:200]}")
        print(f"\nTodos los campos: {list(idea.keys())}")
