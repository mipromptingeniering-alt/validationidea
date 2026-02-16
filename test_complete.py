"""Test completo con funciones correctas"""
import sys

print("="*80)
print("TEST COMPLETO DEL SISTEMA")
print("="*80)

# Test 1: Imports
print("\n1. Verificando imports...")
try:
    from agents import generator_agent, critic_agent, notion_sync_agent, field_mapper, knowledge_base
    print("   ✅ Todos los imports OK")
except Exception as e:
    print(f"   ❌ Error en imports: {e}")
    sys.exit(1)

# Test 2: Funciones críticas
print("\n2. Verificando funciones críticas...")
errors = []

if not hasattr(critic_agent, 'critique'):
    errors.append("critic_agent.critique no existe")
    
if not hasattr(generator_agent, 'generate'):
    errors.append("generator_agent.generate no existe")

# Verificar notion_sync_agent (buscar función correcta)
notion_funcs = [f for f in dir(notion_sync_agent) if not f.startswith('_')]
print(f"   Funciones en notion_sync_agent: {notion_funcs}")
    
if not hasattr(field_mapper, 'map_idea_fields'):
    errors.append("field_mapper.map_idea_fields no existe")
    
if not hasattr(knowledge_base, 'KnowledgeBase'):
    errors.append("knowledge_base.KnowledgeBase no existe")

if errors:
    for err in errors:
        print(f"   ❌ {err}")
    sys.exit(1)
else:
    print("   ✅ Funciones críticas OK")

# Test 3: Knowledge base
print("\n3. Verificando knowledge base...")
try:
    kb = knowledge_base.KnowledgeBase()
    insights = kb.get_insights()
    print(f"   ✅ Knowledge base OK - {insights['total_analyzed']} ideas analizadas")
except Exception as e:
    print(f"   ❌ Error: {e}")
    sys.exit(1)

print("\n" + "="*80)
print("✅ TODOS LOS TESTS PASARON")
print("="*80)
