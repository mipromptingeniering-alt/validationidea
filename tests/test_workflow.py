import os
import sys

sys.path.insert(0, os.path.abspath('.'))


def test_workflow_complete():
    """Test workflow básico"""
    
    print("\n🔍 Verificando estructura...")
    
    # Directorios requeridos
    required_dirs = ['agents', 'config', 'data', 'dashboard']
    
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            print(f"❌ Falta: {dir_name}")
            return False
        print(f"✅ {dir_name}")
    
    # Agentes requeridos
    required_agents = [
        'agents/generator_agent.py',
        'agents/critic_agent.py',
        'agents/dashboard_generator.py'
    ]
    
    for agent in required_agents:
        if not os.path.exists(agent):
            print(f"❌ Falta: {agent}")
            return False
        print(f"✅ {agent}")
    
    # Test imports
    try:
        from agents import generator_agent
        assert hasattr(generator_agent, 'generate')
        assert hasattr(generator_agent, 'load_config')
        print("✅ generator_agent importable")
        
    except Exception as e:
        print(f"❌ Error import: {e}")
        return False
    
    print("\n✅ TODOS LOS TESTS PASADOS\n")
    return True


if __name__ == "__main__":
    success = test_workflow_complete()
    sys.exit(0 if success else 1)
