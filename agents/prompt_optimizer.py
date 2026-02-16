"""
Prompt Optimizer - Auto-refina prompts basándose en resultados
"""
import json
import os
from datetime import datetime

class PromptOptimizer:
    def __init__(self, knowledge_base):
        self.kb = knowledge_base
        self.history_file = 'data/prompt_evolution.json'
        self.history = self._load_history()
    
    def _load_history(self):
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        return {
            'version': 1,
            'prompts': [],
            'performance': [],
            'created_at': datetime.now().isoformat()
        }
    
    def _save_history(self):
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, indent=2, ensure_ascii=False)
    
    def get_optimized_prompt(self, base_product):
        insights = self.kb.get_insights()
        recommendations = self.kb.get_prompt_recommendations()
        
        top_keywords = list(insights.get('top_keywords', {}).keys())[:5]
        keywords_hint = ', '.join(top_keywords) if top_keywords else 'innovación, automatización'
        
        top_categories = list(insights.get('top_categories', {}).keys())[:3]
        category_hint = top_categories[0] if top_categories else 'SaaS'
        
        top_stacks = list(insights.get('top_stacks', {}).keys())[:3]
        stack_hint = ', '.join(top_stacks) if top_stacks else 'Python, React'
        
        success_rate = insights.get('success_rate', 0)
        
        if success_rate >= 80:
            temperature = 0.8
            creativity_hint = "Mantén el enfoque en lo que está funcionando"
        elif success_rate >= 60:
            temperature = 0.9
            creativity_hint = "Combina patrones exitosos con nuevas ideas"
        else:
            temperature = 1.0
            creativity_hint = "Sé más creativo y explora nuevos enfoques"
        
        prompt = f"""Producto base: {base_product['producto']}
Vertical: {base_product['vertical']}
Problema: {base_product['problema']}

🧠 INSIGHTS DEL SISTEMA (aprendidos de {insights.get('total_analyzed', 0)} ideas):
- Keywords exitosos: {keywords_hint}
- Categoría sugerida: {category_hint}
- Stack recomendado: {stack_hint}
- Tasa éxito actual: {success_rate:.1f}%

💡 DIRECTIVA: {creativity_hint}

GENERA variación ÚNICA que incorpore estos aprendizajes.

REGLAS CRÍTICAS:
1. Usa keywords exitosos naturalmente en descripción
2. Stack técnico debe incluir tecnologías probadas
3. Problema debe ser específico y validable
4. Monetización clara desde día 1
5. Diferenciación REAL, no genérica

JSON sin markdown:
{{
  "nombre": "[Nombre específico que incorpore {keywords_hint}]",
  "descripcion": "[Descripción única 150 chars usando keywords exitosos]",
  "propuesta_valor": "[Por qué es 10x mejor usando aprendizajes]",
  "features_core": "[3-5 features concretas inspiradas en patrones exitosos]",
  "diferenciacion": "[Qué lo hace único basado en {category_hint}]",
  "tam": "[Tamaño mercado total]",
  "sam": "[Mercado alcanzable]",
  "som": "[Mercado objetivo primer año]"
}}"""
        
        self.history['prompts'].append({
            'timestamp': datetime.now().isoformat(),
            'version': len(self.history['prompts']) + 1,
            'temperature': temperature,
            'success_rate': success_rate,
            'keywords_used': keywords_hint,
            'recommendations': recommendations
        })
        
        self._save_history()
        
        return prompt, temperature
    
    def get_evolution_stats(self):
        if not self.history['prompts']:
            return None
        
        versions = len(self.history['prompts'])
        first = self.history['prompts'][0]
        last = self.history['prompts'][-1]
        
        return {
            'total_versions': versions,
            'first_success_rate': first.get('success_rate', 0),
            'current_success_rate': last.get('success_rate', 0),
            'improvement': last.get('success_rate', 0) - first.get('success_rate', 0),
            'keywords_evolution': [p.get('keywords_used', '') for p in self.history['prompts'][-5:]]
        }

if __name__ == '__main__':
    from knowledge_base import KnowledgeBase
    
    kb = KnowledgeBase()
    optimizer = PromptOptimizer(kb)
    
    test_product = {
        'producto': 'Herramienta de automatización',
        'vertical': 'SaaS',
        'problema': 'Procesos manuales lentos'
    }
    
    prompt, temp = optimizer.get_optimized_prompt(test_product)
    
    print('🎯 PROMPT OPTIMIZADO:')
    print('='*80)
    print(prompt)
    print('='*80)
    print(f'\n🌡️ Temperatura: {temp}')
    
    stats = optimizer.get_evolution_stats()
    if stats:
        print('\n📊 EVOLUCIÓN:')
        print(f'  • Versiones: {stats["total_versions"]}')
        print(f'  • Mejora: {stats["improvement"]:.1f}%')
