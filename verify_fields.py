import json

with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    idea = data['ideas'][-1]
    
print("="*70)
print(f"IDEA: {idea.get('nombre')}")
print("="*70)

print(f"\nFortalezas:\n{idea.get('fortalezas', 'VACÍO')}")
print(f"\nDebilidades:\n{idea.get('debilidades', 'VACÍO')}")

print("\n" + "="*70)
if idea.get('fortalezas') and idea.get('debilidades'):
    print("✅ Ambos campos existen en JSON local")
else:
    print("❌ Campos aún vacíos")
print("="*70)
