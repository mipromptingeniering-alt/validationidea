import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    idea = data['ideas'][-1]
    
print("\n=== CAMPOS CLAVE ===")
print(f"puntos_fuertes: {idea.get('puntos_fuertes')}")
print(f"puntos_debiles: {idea.get('puntos_debiles')}")
print(f"fortalezas: {idea.get('fortalezas')}")
print(f"debilidades: {idea.get('debilidades')}")
