import sys
sys.path.insert(0, 'agents')
from knowledge_base import KnowledgeBase
import json

kb = KnowledgeBase()

# Cargar ideas existentes
with open('data/ideas.json', encoding='utf-8') as f:
    ideas = json.load(f)['ideas']

print(f'Analizando {len(ideas)} ideas existentes...\n')

for idea in ideas:
    kb.analyze_idea(idea)
    print(f'  ✓ {idea.get(\"nombre\", \"Sin nombre\")} (Score: {idea.get(\"score_critico\", 0)})')

insights = kb.get_insights()
print(f'\n📊 INSIGHTS ACTUALIZADOS:')
print(f'  • Total analizado: {insights[\"total_analyzed\"]}')
print(f'  • Tasa de éxito: {insights[\"success_rate\"]:.1f}%')
print(f'  • Top categorías: {list(insights[\"top_categories\"].keys())[:3]}')

recommendations = kb.get_prompt_recommendations()
print(f'\n💡 RECOMENDACIONES PARA PRÓXIMA GENERACIÓN:')
for rec in recommendations:
    print(f'  • {rec}')
