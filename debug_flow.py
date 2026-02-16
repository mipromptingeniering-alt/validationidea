import json
import sys
sys.path.insert(0, 'agents')
from field_mapper import map_idea_fields

# Simular lo que hace run_batch.py
print("\n" + "="*80)
print("SIMULACIÓN DEL FLUJO ACTUAL")
print("="*80)

# 1. Idea después de generator (SIN puntos_fuertes)
idea_from_generator = {
    'nombre': 'Test',
    'descripcion': 'Test desc',
    'problema': 'Test problem'
}

print("\n1. IDEA DESPUÉS DE GENERATOR (sin puntos_fuertes):")
print(f"   Tiene puntos_fuertes: {'puntos_fuertes' in idea_from_generator}")
print(f"   Tiene fortalezas: {'fortalezas' in idea_from_generator}")

# 2. Mapear ANTES de critic (como hace ahora)
idea_after_mapper = map_idea_fields(idea_from_generator)

print("\n2. IDEA DESPUÉS DE FIELD_MAPPER:")
print(f"   Tiene puntos_fuertes: {'puntos_fuertes' in idea_after_mapper}")
print(f"   Tiene fortalezas: {'fortalezas' in idea_after_mapper}")
print(f"   fortalezas = {idea_after_mapper.get('fortalezas', 'NO EXISTE')}")

# 3. Simular critic_agent
critic_result = {
    'score_critico': 75,
    'puntos_fuertes': ['Fortaleza 1', 'Fortaleza 2'],
    'puntos_debiles': ['Debilidad 1']
}

idea_after_mapper.update(critic_result)

print("\n3. IDEA DESPUÉS DE CRITIC + UPDATE:")
print(f"   puntos_fuertes = {idea_after_mapper.get('puntos_fuertes')}")
print(f"   fortalezas = {idea_after_mapper.get('fortalezas')}")

print("\n" + "="*80)
print("CONCLUSIÓN:")
if idea_after_mapper.get('fortalezas') == idea_after_mapper.get('fortalezas', []):
    print("❌ fortalezas NO se actualiza porque ya existe como []")
    print("❌ El problema es el ORDEN + que update() no sobrescribe []")
print("="*80)
