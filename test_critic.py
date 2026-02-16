import sys
sys.path.insert(0, 'agents')
from critic_agent import critique

test_idea = {
    "nombre": "Test App",
    "descripcion": "Una app de prueba",
    "problema": "Problema de prueba",
    "solucion": "Solucion de prueba",
    "target_audience": "Developers"
}

print("\n" + "="*60)
print("TEST CRITIC_AGENT:")
print("="*60)

result = critique(test_idea)
print(f"Campos retornados: {list(result.keys())}")

if 'fortalezas' in result:
    print(f"\nFortalezas existe: {bool(result['fortalezas'])}")
    if result['fortalezas']:
        print(f"Fortalezas (primeros 200 chars): {result['fortalezas'][:200]}")
else:
    print("\n❌ 'fortalezas' NO existe en resultado")

if 'debilidades' in result:
    print(f"\nDebilidades existe: {bool(result['debilidades'])}")
    if result['debilidades']:
        print(f"Debilidades (primeros 200 chars): {result['debilidades'][:200]}")
else:
    print("\n❌ 'debilidades' NO existe en resultado")
