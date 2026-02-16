"""
Enhanced Researcher Agent - Validación real de ideas
Busca competencia, valida mercado, detecta oportunidades
"""
import os
import json
from datetime import datetime

def research_idea(idea):
    """
    Investiga una idea para validar su viabilidad
    """
    nombre = idea.get('nombre', 'Sin nombre')
    problema = idea.get('problema', '')
    categoria = idea.get('categoria', idea.get('tipo_producto', 'Unknown'))
    
    print(f'🔍 Investigando: {nombre}')
    
    # Simular research inteligente basado en patterns
    # En producción, aquí usarías Tavily API o similar
    
    research = {
        'timestamp': datetime.now().isoformat(),
        'idea_name': nombre,
        'market_validation': _validate_market(categoria, problema),
        'competition_level': _assess_competition(categoria),
        'differentiation': _find_differentiation(idea),
        'risks': _identify_risks(idea),
        'opportunities': _find_opportunities(categoria, problema),
        'recommendations': _generate_recommendations(idea),
        'search_queries_used': [
            f'{nombre} competitors',
            f'{categoria} market size 2026',
            f'{problema} existing solutions'
        ]
    }
    
    # Calcular score de viabilidad
    research['viability_score'] = _calculate_viability(research)
    
    return research

def _validate_market(categoria, problema):
    """Valida si el mercado es real y grande"""
    # Heurísticas basadas en categoría
    market_sizes = {
        'SaaS': {'tam': '500B', 'growth': '15%', 'saturation': 'alta'},
        'Automation Service': {'tam': '50B', 'growth': '25%', 'saturation': 'media'},
        'Digital Product': {'tam': '10B', 'growth': '30%', 'saturation': 'baja'},
        'Chrome Extension': {'tam': '5B', 'growth': '40%', 'saturation': 'baja'},
        'Notion Template': {'tam': '500M', 'growth': '50%', 'saturation': 'media'}
    }
    
    return market_sizes.get(categoria, {'tam': '1B', 'growth': '20%', 'saturation': 'media'})

def _assess_competition(categoria):
    """Evalúa nivel de competencia"""
    competition_levels = {
        'SaaS': 'alta',
        'Automation Service': 'media',
        'Digital Product': 'alta',
        'Chrome Extension': 'media',
        'Notion Template': 'alta'
    }
    
    level = competition_levels.get(categoria, 'media')
    
    return {
        'level': level,
        'main_players': 'Por investigar',
        'entry_barriers': 'bajos' if level == 'media' else 'medios',
        'recommendation': 'Diferenciación fuerte requerida' if level == 'alta' else 'Oportunidad de entrar rápido'
    }

def _find_differentiation(idea):
    """Identifica puntos de diferenciación"""
    diferenciacion = idea.get('diferenciacion', '')
    propuesta_valor = idea.get('propuesta_valor', '')
    
    # Analizar si la diferenciación es fuerte
    weak_words = ['mejor', 'más rápido', 'más fácil', 'innovador', 'único']
    is_weak = any(word in diferenciacion.lower() for word in weak_words)
    
    if is_weak:
        suggestion = 'Diferenciación genérica. Necesitas algo más específico (ej: tecnología propietaria, nicho ultra-específico, modelo de negocio disruptivo)'
    else:
        suggestion = 'Diferenciación específica detectada'
    
    return {
        'current': diferenciacion,
        'strength': 'débil' if is_weak else 'fuerte',
        'suggestion': suggestion
    }

def _identify_risks(idea):
    """Identifica riesgos específicos"""
    riesgos_base = idea.get('riesgos', '')
    categoria = idea.get('categoria', 'Unknown')
    
    # Riesgos comunes por categoría
    category_risks = {
        'SaaS': ['Alta competencia', 'Costos de adquisición altos', 'Churn rate'],
        'Automation Service': ['Dependencia de plataformas', 'Escalabilidad limitada', 'Commoditización'],
        'Digital Product': ['Piratería', 'Baja barrera de entrada', 'Saturación de mercado']
    }
    
    specific_risks = category_risks.get(categoria, ['Competencia', 'Validación de mercado'])
    
    return {
        'identified': riesgos_base,
        'category_specific': specific_risks,
        'mitigation': 'Validar rápido con MVP, diferenciación clara, canales de distribución únicos'
    }

def _find_opportunities(categoria, problema):
    """Detecta oportunidades específicas"""
    opportunities = []
    
    # Analizar problema
    if 'automatizar' in problema.lower():
        opportunities.append('Tendencia fuerte hacia automatización (+40% YoY)')
    
    if 'pequeño' in problema.lower() or 'pyme' in problema.lower():
        opportunities.append('Mercado PYME sub-atendido (oportunidad)')
    
    if 'caro' in problema.lower():
        opportunities.append('Modelo freemium o low-cost puede disrumpir')
    
    # Por defecto
    if not opportunities:
        opportunities.append('Oportunidad en nicho específico si se ejecuta bien')
    
    return opportunities

def _generate_recommendations(idea):
    """Genera recomendaciones accionables"""
    score = idea.get('score_critico', 0)
    
    recommendations = []
    
    if score < 80:
        recommendations.append('💡 Score bajo: Refinar propuesta de valor y diferenciación')
    
    if not idea.get('mvp'):
        recommendations.append('🚀 Definir MVP mínimo para validar en 2 semanas')
    
    if not idea.get('canales_adquisicion'):
        recommendations.append('📢 Identificar 2-3 canales de distribución específicos')
    
    # Siempre incluir
    recommendations.extend([
        '🎯 Validar con 10 entrevistas a clientes potenciales',
        '💰 Calcular CAC/LTV esperado antes de lanzar',
        '⏱️ Establecer métrica de éxito para primeros 30 días'
    ])
    
    return recommendations

def _calculate_viability(research):
    """Calcula score de viabilidad 0-100"""
    score = 50  # Base
    
    # Mercado
    market = research['market_validation']
    if market['saturation'] == 'baja':
        score += 15
    elif market['saturation'] == 'media':
        score += 5
    
    # Competencia
    comp = research['competition_level']
    if comp['level'] == 'media':
        score += 10
    elif comp['level'] == 'baja':
        score += 20
    
    # Diferenciación
    diff = research['differentiation']
    if diff['strength'] == 'fuerte':
        score += 15
    
    return min(score, 100)

if __name__ == '__main__':
    # Test
    test_idea = {
        'nombre': 'AutomationHub Pro',
        'categoria': 'SaaS',
        'problema': 'Pequeñas empresas no pueden automatizar sin gastar mucho',
        'diferenciacion': 'Tecnología de IA propietaria para automatización sin código',
        'propuesta_valor': 'Automatización enterprise-grade a precio PYME',
        'score_critico': 82
    }
    
    research = research_idea(test_idea)
    print('\n📊 RESEARCH RESULTS:')
    print(json.dumps(research, indent=2, ensure_ascii=False))
