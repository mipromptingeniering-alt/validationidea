import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    
# Buscar Prospectaflow
prospectaflow = None
for idea in data['ideas']:
    if 'Prospectaflow' in idea.get('nombre', ''):
        prospectaflow = idea
        break

if prospectaflow:
    print("\n" + "="*80)
    print("PROSPECTAFLOW EN JSON LOCAL:")
    print("="*80)
    print(f"puntos_fuertes: {prospectaflow.get('puntos_fuertes')}")
    print(f"fortalezas: {prospectaflow.get('fortalezas')}")
    print(f"puntos_debiles: {prospectaflow.get('puntos_debiles')}")
    print(f"debilidades: {prospectaflow.get('debilidades')}")
    print("="*80)
else:
    print("❌ No se encontró Prospectaflow")
