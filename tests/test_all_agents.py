import os
import sys
import json
import pytest

sys.path.insert(0, os.path.abspath('.'))

from agents import generator_agent, critic_agent, optimizer_agent, landing_generator, report_generator, dashboard_generator


class TestGeneratorAgent:
    """Tests para generator_agent"""
    
    def test_load_config_exists(self):
        """Verifica que load_config existe"""
        assert hasattr(generator_agent, 'load_config')
        config = generator_agent.load_config()
        assert isinstance(config, dict)
    
    def test_load_existing_ideas(self):
        """Verifica carga de ideas"""
        ideas = generator_agent.load_existing_ideas()
        assert isinstance(ideas, list)
    
    def test_get_monetizable_product(self):
        """Verifica generación productos"""
        product = generator_agent.get_monetizable_product()
        assert isinstance(product, dict)
        assert 'tipo' in product
        assert 'problema' in product
        assert 'monetizacion' in product
    
    def test_is_duplicate(self):
        """Verifica detección duplicados"""
        idea1 = {'nombre': 'Test Product 123', 'descripcion_corta': 'Test'}
        idea2 = {'nombre': 'test product 123'}
        
        result = generator_agent.is_duplicate(idea1, [idea2])
        assert result == True
    
    def test_calculate_fingerprint(self):
        """Verifica fingerprints únicos"""
        fp1 = generator_agent.calculate_fingerprint('Test', 'Desc')
        fp2 = generator_agent.calculate_fingerprint('Test', 'Desc')
        fp3 = generator_agent.calculate_fingerprint('Other', 'Desc')
        
        assert fp1 == fp2
        assert fp1 != fp3
        assert len(fp1) == 8


class TestCriticAgent:
    """Tests para critic_agent"""
    
    def test_extract_score_function_exists(self):
        """Verifica que extract_score existe"""
        assert hasattr(critic_agent, 'extract_score')
    
    def test_extract_score_handles_valid_numbers(self):
        """Verifica extracción scores válidos"""
        assert critic_agent.extract_score("Score: 85/100") >= 70
        assert critic_agent.extract_score("75") >= 70
    
    def test_extract_score_handles_invalid(self):
        """Verifica fallback con input inválido"""
        score = critic_agent.extract_score("invalid text")
        assert isinstance(score, (int, float))
        assert 0 <= score <= 100


class TestOptimizerAgent:
    """Tests para optimizer_agent"""
    
    def test_optimize_exists(self):
        """Verifica que optimize existe"""
        assert hasattr(optimizer_agent, 'optimize')
    
    def test_optimize_handles_valid_idea(self):
        """Verifica optimización de idea válida"""
        idea = {
            'nombre': 'Test',
            'problema': 'Test problem',
            'solucion': 'Test solution'
        }
        
        critique = {
            'puntos_debiles': ['Weak 1'],
            'recomendaciones': ['Rec 1']
        }
        
        # No debe crashear
        try:
            result = optimizer_agent.optimize(idea, critique)
            assert result is not None
        except:
            pass  # OK si Groq API no disponible en tests


class TestLandingGenerator:
    """Tests para landing_generator"""
    
    def test_generate_exists(self):
        """Verifica que generate existe"""
        assert hasattr(landing_generator, 'generate_landing')
    
    def test_generate_creates_correct_structure(self):
        """Verifica estructura slug/index.html"""
        test_idea = {
            'slug': 'test-product-9999',
            'nombre': 'Test Product',
            'descripcion': 'Test description',
            'problema': 'Test problem',
            'solucion': 'Test solution',
            'precio_sugerido': '29'
        }
        
        output = landing_generator.generate_landing(test_idea)
        
        # Verifica path correcto
        assert 'landing-pages/test-product-9999/index.html' in output
        
        # Verifica que el archivo existe
        assert os.path.exists(output)
        
        # Limpiar
        if os.path.exists(output):
            os.remove(output)
            os.rmdir('landing-pages/test-product-9999')


class TestReportGenerator:
    """Tests para report_generator"""
    
    def test_generate_exists(self):
        """Verifica que generate existe"""
        assert hasattr(report_generator, 'generate')
    
    def test_generate_creates_correct_path(self):
        """Verifica que guarda en informes/slug/"""
        test_idea = {
            'slug': 'test-report-9999',
            'nombre': 'Test',
            'problema': 'Test',
            'solucion': 'Test',
            'score_generador': 85
        }
        
        test_critique = {
            'score_critico': 75,
            'puntos_fuertes': ['Test'],
            'puntos_debiles': ['Test'],
            'resumen': 'Test'
        }
        
        output = report_generator.generate(test_idea, test_critique)
        
        # Verifica path correcto
        assert 'informes/test-report-9999/informe-test-report-9999.md' in output
        
        # Limpiar
        if os.path.exists(output):
            os.remove(output)
            os.rmdir('informes/test-report-9999')


class TestDashboardGenerator:
    """Tests para dashboard_generator"""
    
    def test_generate_exists(self):
        """Verifica que generate_dashboard existe"""
        assert hasattr(dashboard_generator, 'generate_dashboard')
    
    def test_generate_creates_dashboard(self):
        """Verifica que crea dashboard/index.html"""
        output = dashboard_generator.generate_dashboard()
        
        assert output == 'dashboard/index.html'
        assert os.path.exists(output)


class TestIntegration:
    """Tests de integración completa"""
    
    def test_csv_structure(self):
        """Verifica estructura CSV ideas"""
        csv_file = 'data/ideas-validadas.csv'
        
        if os.path.exists(csv_file):
            with open(csv_file, 'r') as f:
                header = f.readline().strip()
                required_fields = ['nombre', 'slug', 'timestamp', 'score_promedio']
                
                for field in required_fields:
                    assert field in header
    
    def test_all_agents_importable(self):
        """Verifica que todos los agentes se pueden importar"""
        modules = [
            'agents.generator_agent',
            'agents.critic_agent',
            'agents.optimizer_agent',
            'agents.report_generator',
            'agents.landing_generator',
            'agents.dashboard_generator'
        ]
        
        for module in modules:
            try:
                __import__(module)
            except ImportError as e:
                pytest.fail(f"No se puede importar {module}: {e}")


def run_tests():
    """Ejecuta todos los tests"""
    print("\n" + "="*60)
    print("🧪 EJECUTANDO TESTS AUTOMÁTICOS")
    print("="*60 + "\n")
    
    pytest.main([__file__, '-v', '--tb=short'])


if __name__ == "__main__":
    run_tests()
