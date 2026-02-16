import sys
sys.path.insert(0, 'agents')
from critic_agent import critique

test_idea = {
    'nombre': 'Test Idea',
    'descripcion': 'Test',
    'problema': 'Test problem',
    'solucion': 'Test solution'
}

print("\n" + "="*80)
print("RESULTADO DE critic_agent.critique():")
print("="*80)
result = critique(test_idea)
print(f"Keys: {list(result.keys())}")
print(f"puntos_fuertes: {result.get('puntos_fuertes')}")
print(f"puntos_debiles: {result.get('puntos_debiles')}")
print("="*80)
