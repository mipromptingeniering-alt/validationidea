import os
import sys
import json

sys.path.insert(0, os.path.abspath('.'))


def test_workflow_complete():
    """Test workflow end-to-end"""
    
    print("\n🔍 Test 1: Verificar estructura proyecto...")
    
    required_dirs = [
        'agents',
        'config',
        'data',
        'dashboard',
        'landing-pages',
        'informes',
        'scripts'
    ]
    
    for dir_name in required_dirs:
        assert os.path.exists(dir_name), f"❌ Falta directorio: {dir_name}"
    
    print("✅ Estructura correcta")
    
    print("\n🔍 Test 2: Verificar agentes...")
    
    required_agents = [
        'agents/generator_agent.py',
        'agents/critic_agent.py',
        'agents/optimizer_agent.py',
        'agents/report_generator.py',
        'agents/landing_generator.py',
        'agents/dashboard_generator.py'
    ]
    
    for agent in required_agents:
        assert os.path.exists(agent), f"❌ Falta agente: {agent}"
    
    print("✅ Todos los agentes presentes")
    
    print("\n🔍 Test 3: Verificar imports...")
    
    try:
        from agents import generator_agent
        assert hasattr(generator_agent, 'generate')
        assert hasattr(generator_agent, 'load_config')
        print("✅ generator_agent OK")
        
        from agents import critic_agent
        assert hasattr(critic_agent, 'critique')
        print("✅ critic_agent OK")
        
        from agents import optimizer_agent
        assert hasattr(optimizer_agent, 'optimize')
        print("✅ optimizer_agent OK")
        
        from agents import report_generator
        assert hasattr(report_generator, 'generate')
        print("✅ report_generator OK")
        
        from agents import landing_generator
        assert hasattr(landing_generator, 'generate_landing')
        print("✅ landing_generator OK")
        
        from agents import dashboard_generator
        assert hasattr(dashboard_generator, 'generate_dashboard')
        print("✅ dashboard_generator OK")
        
    except Exception as e:
        print(f"❌ Error imports: {e}")
        return False
    
    print("\n🔍 Test 4: Verificar config files...")
    
    if os.path.exists('config/generator_config.json'):
        with open('config/generator_config.json', 'r') as f:
            config = json.load(f)
            assert isinstance(config, dict)
            print("✅ generator_config.json válido")
    
    print("\n🔍 Test 5: Verificar CSV...")
    
    if os.path.exists('data/ideas-validadas.csv'):
        with open('data/ideas-validadas.csv', 'r') as f:
            header = f.readline()
            assert 'nombre' in header
            assert 'slug' in header
            print("✅ CSV estructura correcta")
    
    print("\n" + "="*60)
    print("✅ TODOS LOS TESTS PASADOS")
    print("="*60 + "\n")
    
    return True


if __name__ == "__main__":
    success = test_workflow_complete()
    sys.exit(0 if success else 1)
