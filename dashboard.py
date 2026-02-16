"""
Dashboard - Visualiza la evolución del sistema
"""
import sys
sys.path.insert(0, 'agents')
from knowledge_base import KnowledgeBase
from prompt_optimizer import PromptOptimizer
import json
from datetime import datetime

def show_dashboard():
    kb = KnowledgeBase()
    insights = kb.get_insights()
    
    print('='*80)
    print('📊 CHET THIS - DASHBOARD DE EVOLUCIÓN')
    print('='*80)
    print(f'\n📅 {datetime.now().strftime(\"%Y-%m-%d %H:%M\")}')
    
    print('\n🧠 MEMORIA DEL SISTEMA:')
    print(f'  • Ideas analizadas: {insights[\"total_analyzed\"]}')
    print(f'  • Tasa de éxito: {insights[\"success_rate\"]:.1f}%')
    
    print('\n🎯 PATRONES DETECTADOS:')
    if insights['top_keywords']:
        print('  • Keywords exitosos:')
        for kw, count in list(insights['top_keywords'].items())[:5]:
            print(f'    - {kw}: {count} veces')
    
    if insights['top_categories']:
        print('  • Categorías exitosas:')
        for cat, count in list(insights['top_categories'].items())[:3]:
            avg_score = insights['avg_scores_by_category'].get(cat, 0)
            print(f'    - {cat}: {count} ideas (avg score: {avg_score:.1f})')
    
    if insights['top_stacks']:
        print('  • Stacks preferidos:')
        for stack, count in list(insights['top_stacks'].items())[:5]:
            print(f'    - {stack}: {count} veces')
    
    print('\n💡 RECOMENDACIONES ACTUALES:')
    for rec in kb.get_prompt_recommendations():
        print(f'  • {rec}')
    
    # Evolución del prompt
    try:
        optimizer = PromptOptimizer(kb)
        stats = optimizer.get_evolution_stats()
        if stats:
            print('\n📈 EVOLUCIÓN DE PROMPTS:')
            print(f'  • Versiones generadas: {stats[\"total_versions\"]}')
            print(f'  • Mejora total: {stats[\"improvement\"]:.1f}%')
            print(f'  • Tasa inicial: {stats[\"first_success_rate\"]:.1f}%')
            print(f'  • Tasa actual: {stats[\"current_success_rate\"]:.1f}%')
    except:
        pass
    
    print('\n' + '='*80)
    print('✅ Sistema auto-evolutivo operativo')
    print('='*80 + '\n')

if __name__ == '__main__':
    show_dashboard()
