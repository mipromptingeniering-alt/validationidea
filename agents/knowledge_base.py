"""
Knowledge Base - Memoria persistente del sistema
Aprende de cada idea generada y detecta patrones de éxito
"""
import json
import os
from datetime import datetime
from collections import Counter, defaultdict

KNOWLEDGE_FILE = 'data/knowledge_base.json'

class KnowledgeBase:
    def __init__(self):
        self.data = self._load()
    
    def _load(self):
        """Carga base de conocimiento"""
        if os.path.exists(KNOWLEDGE_FILE):
            try:
                with open(KNOWLEDGE_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                    # Convertir dicts a Counter
                    data['patterns']['successful_keywords'] = Counter(data['patterns'].get('successful_keywords', {}))
                    data['patterns']['successful_categories'] = Counter(data['patterns'].get('successful_categories', {}))
                    data['patterns']['successful_stacks'] = Counter(data['patterns'].get('successful_stacks', {}))
                    data['patterns']['best_monetization_models'] = Counter(data['patterns'].get('best_monetization_models', {}))
                    
                    return data
            except Exception as e:
                print(f"⚠️ Error cargando knowledge base: {e}")
        
        return {
            'version': '2.0',
            'created_at': datetime.now().isoformat(),
            'total_ideas_analyzed': 0,
            'patterns': {
                'successful_keywords': Counter(),
                'successful_categories': Counter(),
                'successful_problems': [],
                'successful_stacks': Counter(),
                'avg_score_by_category': {},
                'best_monetization_models': Counter()
            },
            'learnings': {
                'what_works': [],
                'what_fails': [],
                'prompt_improvements': []
            },
            'evolution_history': [],
            'last_update': None
        }
    
    def _save(self):
        """Guarda base de conocimiento"""
        os.makedirs('data', exist_ok=True)
        self.data['last_update'] = datetime.now().isoformat()
        
        # Convertir Counter a dict para JSON
        save_data = self.data.copy()
        save_data['patterns'] = self.data['patterns'].copy()
        save_data['patterns']['successful_keywords'] = dict(self.data['patterns']['successful_keywords'])
        save_data['patterns']['successful_categories'] = dict(self.data['patterns']['successful_categories'])
        save_data['patterns']['successful_stacks'] = dict(self.data['patterns']['successful_stacks'])
        save_data['patterns']['best_monetization_models'] = dict(self.data['patterns']['best_monetization_models'])
        
        with open(KNOWLEDGE_FILE, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, indent=2, ensure_ascii=False)
    
    def analyze_idea(self, idea):
        """Analiza una idea y extrae patrones"""
        score = idea.get('score_critico', 0)
        
        self.data['total_ideas_analyzed'] += 1
        
        # Ideas exitosas (score >= 85)
        if score >= 85:
            # Keywords en nombre/descripción
            text = f"{idea.get('nombre', '')} {idea.get('descripcion', '')}".lower()
            words = [w for w in text.split() if len(w) > 4]
            for word in words[:10]:
                self.data['patterns']['successful_keywords'][word] += 1
            
            # Categoría exitosa
            categoria = idea.get('categoria', idea.get('tipo_producto', 'Unknown'))
            self.data['patterns']['successful_categories'][categoria] += 1
            
            # Problemas exitosos
            problema = idea.get('problema', '')[:200]
            if problema and problema not in self.data['patterns']['successful_problems']:
                self.data['patterns']['successful_problems'].append(problema)
            
            # Stack exitoso
            stack = idea.get('stack_sugerido', '')
            if stack:
                for tech in stack.split(','):
                    tech = tech.strip()
                    if tech:
                        self.data['patterns']['successful_stacks'][tech] += 1
            
            # Modelo de monetización
            monetizacion = idea.get('modelo_monetizacion', '')
            if 'suscripción' in monetizacion.lower() or 'subscription' in monetizacion.lower():
                self.data['patterns']['best_monetization_models']['subscription'] += 1
            elif 'pago único' in monetizacion.lower() or 'one-time' in monetizacion.lower():
                self.data['patterns']['best_monetization_models']['one-time'] += 1
            
            # Learning positivo
            learning = f"✅ Score {score}: {idea.get('nombre', 'Sin nombre')} - {categoria}"
            if learning not in self.data['learnings']['what_works']:
                self.data['learnings']['what_works'].append(learning)
        
        # Ideas fallidas (score < 70)
        elif score < 70:
            learning = f"❌ Score {score}: {idea.get('nombre', 'Sin nombre')} - Problema: {idea.get('problema', '')[:50]}"
            if learning not in self.data['learnings']['what_fails']:
                self.data['learnings']['what_fails'].append(learning)
        
        # Score promedio por categoría
        categoria = idea.get('categoria', idea.get('tipo_producto', 'Unknown'))
        if categoria not in self.data['patterns']['avg_score_by_category']:
            self.data['patterns']['avg_score_by_category'][categoria] = []
        self.data['patterns']['avg_score_by_category'][categoria].append(score)
        
        self._save()
    
    def get_insights(self):
        """Retorna insights del sistema"""
        insights = {
            'total_analyzed': self.data['total_ideas_analyzed'],
            'top_keywords': dict(self.data['patterns']['successful_keywords'].most_common(10)),
            'top_categories': dict(self.data['patterns']['successful_categories'].most_common(5)),
            'top_stacks': dict(self.data['patterns']['successful_stacks'].most_common(5)),
            'best_monetization': dict(self.data['patterns']['best_monetization_models'].most_common(3)),
            'avg_scores_by_category': {
                cat: sum(scores) / len(scores) if scores else 0
                for cat, scores in self.data['patterns']['avg_score_by_category'].items()
            },
            'success_rate': self._calculate_success_rate()
        }
        
        return insights
    
    def _calculate_success_rate(self):
        """Calcula tasa de éxito (ideas con score >= 80)"""
        total_scores = []
        for scores in self.data['patterns']['avg_score_by_category'].values():
            total_scores.extend(scores)
        
        if not total_scores:
            return 0
        
        successful = sum(1 for s in total_scores if s >= 80)
        return (successful / len(total_scores)) * 100
    
    def get_prompt_recommendations(self):
        """Genera recomendaciones para mejorar el prompt"""
        recommendations = []
        
        # Recomendar keywords exitosos
        top_keywords = self.data['patterns']['successful_keywords'].most_common(5)
        if top_keywords:
            keywords = ', '.join([k for k, _ in top_keywords])
            recommendations.append(f"Incorporar estos conceptos: {keywords}")
        
        # Recomendar categorías exitosas
        top_cats = self.data['patterns']['successful_categories'].most_common(3)
        if top_cats:
            cats = ', '.join([k for k, _ in top_cats])
            recommendations.append(f"Priorizar estas categorías: {cats}")
        
        # Recomendar stacks exitosos
        top_stacks = self.data['patterns']['successful_stacks'].most_common(3)
        if top_stacks:
            stacks = ', '.join([k for k, _ in top_stacks])
            recommendations.append(f"Usar estos stacks: {stacks}")
        
        return recommendations

if __name__ == '__main__':
    # Test
    kb = KnowledgeBase()
    
    # Simular análisis
    test_idea = {
        'nombre': 'Test SaaS',
        'descripcion': 'Herramienta de automatización',
        'categoria': 'SaaS',
        'problema': 'Problema de automatización',
        'score_critico': 88,
        'stack_sugerido': 'Python, React, AWS',
        'modelo_monetizacion': 'Suscripción mensual'
    }
    
    kb.analyze_idea(test_idea)
    insights = kb.get_insights()
    
    print('📊 INSIGHTS:')
    print(json.dumps(insights, indent=2, ensure_ascii=False))
    
    print('\n💡 RECOMENDACIONES:')
    for rec in kb.get_prompt_recommendations():
        print(f'  • {rec}')
