import json
with open('data/ideas.json', 'r', encoding='utf-8-sig') as f:
    data = json.load(f)
    idea = data['ideas'][-1]
    
print("="*70)
print(f"IDEA: {idea.get('nombre')}")
print("="*70)

# Verificar ambos formatos
pf = idea.get('puntos_fuertes', 'NO EXISTE')
pd = idea.get('puntos_debiles', 'NO EXISTE')
fort = idea.get('fortalezas', 'NO EXISTE')
debil = idea.get('debilidades', 'NO EXISTE')

print(f"\npuntos_fuertes: {pf}")
print(f"puntos_debiles: {pd}")
print(f"\nfortalezas: {fort}")
print(f"debilidades: {debil}")

if fort != 'NO EXISTE' and debil != 'NO EXISTE':
    print("\n✅ MAPEO EXITOSO - Fortalezas y debilidades existen")
else:
    print("\n❌ MAPEO FALLÓ")
print("="*70)
