import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    idea = data['ideas'][-1]

print("\n" + "="*70)
print(f"ÚLTIMA IDEA: {idea.get('nombre')}")
print("="*70)
print(f"puntos_fuertes: {idea.get('puntos_fuertes')}")
print(f"fortalezas: {idea.get('fortalezas')}")
print(f"\npuntos_debiles: {idea.get('puntos_debiles')}")
print(f"debilidades: {idea.get('debilidades')}")

if idea.get('fortalezas') and len(idea.get('fortalezas', [])) > 0:
    print("\n✅ ÉXITO - Fortalezas mapeadas correctamente")
else:
    print("\n❌ FALLÓ - Fortalezas vacías")
print("="*70)
