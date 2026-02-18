import sys
import traceback
sys.path.insert(0, 'agents')

try:
    from generator_agent import generate
    print("Generando idea...")
    idea = generate()
    if idea:
        print(f"\n✅ ÉXITO: {idea.get('nombre')}")
    else:
        print("\n❌ No se generó idea")
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\nTRACEBACK COMPLETO:")
    traceback.print_exc()
