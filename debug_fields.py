import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    idea = data['ideas'][-1]
    
print("="*70)
print("CAMPOS CRÍTICOS:")
print("="*70)
print(f"puntos_fuertes: {idea.get('puntos_fuertes', 'NO EXISTE')[:200]}")
print(f"puntos_debiles: {idea.get('puntos_debiles', 'NO EXISTE')[:200]}")
print(f"fortalezas: {idea.get('fortalezas', 'NO EXISTE')[:200]}")
print(f"debilidades: {idea.get('debilidades', 'NO EXISTE')[:200]}")
