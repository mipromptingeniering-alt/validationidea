import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Test 1: Todos los imports funcionan"""
    print("🧪 TEST 1: Imports")
    
    try:
        from agents import generator_agent
        print("   ✅ generator_agent")
    except Exception as e:
        print(f"   ❌ generator_agent: {e}")
        return False
    
    try:
        from agents import critic_agent
        print("   ✅ critic_agent")
    except Exception as e:
        print(f"   ❌ critic_agent: {e}")
        return False
    
    try:
        from agents import researcher_agent
        print("   ✅ researcher_agent")
    except Exception as e:
        print(f"   ❌ researcher_agent: {e}")
        return False
    
    try:
        from agents import report_generator
        print("   ✅ report_generator")
    except Exception as e:
        print(f"   ❌ report_generator: {e}")
        return False
    
    try:
        from agents import landing_generator
        print("   ✅ landing_generator")
    except Exception as e:
        print(f"   ❌ landing_generator: {e}")
        return False
    
    return True

def test_functions_exist():
    """Test 2: Funciones necesarias existen"""
    print("\n🧪 TEST 2: Funciones")
    
    from agents import generator_agent, critic_agent, researcher_agent
    
    functions = [
        (generator_agent, 'generate'),
        (generator_agent, 'load_config'),
        (critic_agent, 'critique'),
        (critic_agent, 'decide_publish'),
        (researcher_agent, 'run'),
        (researcher_agent, 'research_trends')
    ]
    
    all_ok = True
    
    for module, func_name in functions:
        if hasattr(module, func_name):
            print(f"   ✅ {module.__name__}.{func_name}")
        else:
            print(f"   ❌ {module.__name__}.{func_name} NO EXISTE")
            all_ok = False
    
    return all_ok

def test_researcher_agent():
    """Test 3: Researcher agent funciona"""
    print("\n🧪 TEST 3: Researcher Agent")
    
    try:
        from agents import researcher_agent
        
        print("   Ejecutando researcher_agent.run()...")
        result = researcher_agent.run()
        
        if result and isinstance(result, dict):
            print(f"   ✅ Retorna dict con {len(result.keys())} keys")
            
            required_keys = ['trends', 'problems', 'tools', 'niches']
            for key in required_keys:
                if key in result:
                    print(f"   ✅ Key '{key}' presente")
                else:
                    print(f"   ❌ Key '{key}' faltante")
                    return False
            
            return True
        else:
            print("   ❌ No retorna dict válido")
            return False
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_generator_agent():
    """Test 4: Generator agent funciona"""
    print("\n🧪 TEST 4: Generator Agent")
    
    try:
        from agents import generator_agent
        
        print("   Cargando config...")
        config = generator_agent.load_config()
        
        if config:
            print(f"   ✅ Config cargado: {list(config.keys())}")
        else:
            print("   ⚠️  Config vacío (usando defaults)")
        
        print("   Cargando ideas existentes...")
        ideas = generator_agent.load_existing_ideas()
        print(f"   ✅ {len(ideas)} ideas cargadas")
        
        return True
    
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return False

def test_file_structure():
    """Test 5: Estructura archivos necesaria"""
    print("\n🧪 TEST 5: Estructura Archivos")
    
    required_dirs = [
        'agents',
        'config',
        'data',
        'memory-system',
        'scripts'
    ]
    
    required_files = [
        'agents/generator_agent.py',
        'agents/critic_agent.py',
        'agents/researcher_agent.py',
        'main_workflow.py',
        '.github/workflows/generate-ideas.yml'
    ]
    
    all_ok = True
    
    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}/")
        else:
            print(f"   ❌ {dir_path}/ NO EXISTE")
            all_ok = False
    
    for file_path in required_files:
        if os.path.exists(file_path):
            print(f"   ✅ {file_path}")
        else:
            print(f"   ❌ {file_path} NO EXISTE")
            all_ok = False
    
    return all_ok

def test_env_variables():
    """Test 6: Variables entorno necesarias"""
    print("\n🧪 TEST 6: Variables Entorno")
    
    required_vars = [
        'GROQ_API_KEY'
    ]
    
    optional_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    all_ok = True
    
    for var in required_vars:
        if os.environ.get(var):
            print(f"   ✅ {var} (configurado)")
        else:
            print(f"   ❌ {var} NO CONFIGURADO")
            all_ok = False
    
    for var in optional_vars:
        if os.environ.get(var):
            print(f"   ✅ {var} (configurado)")
        else:
            print(f"   ⚠️  {var} no configurado (opcional)")
    
    return all_ok


def run_all_tests():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("🧪 TESTING SUITE - ValidationIdea")
    print("="*60 + "\n")
    
    tests = [
        ("Imports", test_imports),
        ("Funciones", test_functions_exist),
        ("Researcher Agent", test_researcher_agent),
        ("Generator Agent", test_generator_agent),
        ("Estructura Archivos", test_file_structure),
        ("Variables Entorno", test_env_variables)
    ]
    
    results = []
    
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ Test '{name}' falló con error: {e}")
            results.append((name, False))
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN")
    print("="*60 + "\n")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\n{passed}/{total} tests pasados")
    
    if passed == total:
        print("\n🎉 TODOS LOS TESTS PASARON - Sistema listo para deploy")
        return True
    else:
        print("\n⚠️  HAY TESTS FALLANDO - Revisar antes de deploy")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
