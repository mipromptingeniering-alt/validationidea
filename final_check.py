import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    idea = data['ideas'][-1]

print("\n" + "="*80)
print(f"ÚLTIMA IDEA: {idea.get('nombre')}")
print("="*80)
print(f"✓ puntos_fuertes: {idea.get('puntos_fuertes')}")
print(f"✓ fortalezas: {idea.get('fortalezas')}")
print(f"\n✓ puntos_debiles: {idea.get('puntos_debiles')}")
print(f"✓ debilidades: {idea.get('debilidades')}")

# Validación
success = (
    idea.get('fortalezas') and 
    len(idea.get('fortalezas', [])) > 0 and
    idea.get('fortalezas') == idea.get('puntos_fuertes')
)

if success:
    print("\n✅✅✅ ÉXITO TOTAL - Mapeo perfecto")
else:
    print("\n❌ Aún hay problema")
print("="*80)
