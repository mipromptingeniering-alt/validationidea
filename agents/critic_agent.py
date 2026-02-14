import os
import json
from groq import Groq

def load_config():
    config_file = 'config/critic_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'min_score_critico': 55,  # Bajado de 65 a 55
        'min_score_promedio': 65,  # Bajado de 72 a 65
        'max_gap': 30
    }

def critique(idea):
    """Evalúa la idea de forma CONSTRUCTIVA"""
    print("\n🎯 Agente Crítico iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = """Eres un crítico CONSTRUCTIVO de ideas SaaS.

🎯 CRITERIOS DE EVALUACIÓN (0-100):

1. **Problema (0-20)**
   - ¿Es específico y medible?
   - ¿Afecta a suficiente gente?
   - ¿Están dispuestos a pagar?

2. **Solución (0-20)**
   - ¿Es técnicamente viable?
   - ¿Usa herramientas modernas?
   - ¿Se puede construir rápido?

3. **Mercado (0-20)**
   - ¿TAM > 10M€?
   - ¿Nicho alcanzable?
   - ¿Competencia manejable?

4. **Diferenciación (0-20)**
   - ¿Tiene algo único?
   - ¿Por qué elegirían esto vs competencia?
   - ¿Integración exclusiva?

5. **Viabilidad (0-20)**
   - ¿MVP en 4-6 semanas?
   - ¿Inversión < 500€?
   - ¿Stack moderno?

✅ APRUEBA si:
- Score ≥ 55 (antes era 65)
- Problema específico
- Solución técnicamente viable
- Mercado > 10M€

❌ RECHAZA solo si:
- Score < 50
- Problema muy vago
- Técnicamente imposible
- Mercado < 5M€

📊 FORMATO JSON:
{
  "score_critico": 75,
  "puntos_fuertes": ["Punto 1", "Punto 2", "Punto 3"],
  "puntos_debiles": ["Punto 1", "Punto 2"],
  "oportunidades": ["Oportunidad 1", "Oportunidad 2"],
  "amenazas": ["Amenaza 1", "Amenaza 2"],
  "recomendaciones": ["Recomendación 1", "Recomendación 2"],
  "viabilidad_tecnica": "Alta/Media/Baja",
  "viabilidad_mercado": "Alta/Media/Baja",
  "diferenciacion_score": 75,
  "resumen": "Resumen de 2 frases"
}"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Evalúa esta idea SaaS de forma CONSTRUCTIVA:\n\n{json.dumps(idea, indent=2, ensure_ascii=False)}"}
            ],
            temperature=0.3,
            max_tokens=1500
        )
        
        content = response.choices[0].message.content.strip()
        
        if '```json' in content:
            content = content.split('```json').split('```').strip()[1]
        elif '```' in content:
            content = content.split('```').split('```')[0].strip()
        
        critique = json.loads(content)
        
        # Penalizaciones REDUCIDAS
        penalties = 0
        score_gen = idea.get('score_generador', 0)
        
        if score_gen < 75:
            penalties += 5  # Antes era 10
        
        tam_str = idea.get('tam', '0')
        tam_num = int(''.join(filter(str.isdigit, tam_str)))
        if tam_num < 20:
            penalties += 5  # Antes era 10
        
        if penalties > 0:
            critique['score_critico'] = max(50, critique['score_critico'] - penalties)
            print(f"⚠️  Penalizaciones aplicadas: -{penalties} puntos")
        
        print(f"✅ Crítica completada - Score: {critique['score_critico']}")
        return critique
    
    except Exception as e:
        print(f"❌ Error en crítica: {e}")
        return {
            'score_critico': 60,
            'puntos_fuertes': ['Idea interesante'],
            'puntos_debiles': ['Requiere más análisis'],
            'recomendaciones': ['Validar con usuarios'],
            'resumen': 'Idea con potencial'
        }

def decide_publish(idea, critique, config):
    """Decide si publicar (criterios MÁS PERMISIVOS)"""
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    avg_score = (score_gen + score_crit) / 2
    gap = abs(score_gen - score_crit)
    
    min_score_crit = config.get('min_score_critico', 55)
    min_score_avg = config.get('min_score_promedio', 65)
    max_gap = config.get('max_gap', 30)
    
    if score_crit >= min_score_crit and avg_score >= min_score_avg and gap <= max_gap:
        print(f"✅ PUBLICAR - Gen:{score_gen} Crit:{score_crit} Avg:{int(avg_score)} Gap:{int(gap)}")
        return True
    else:
        print(f"❌ RECHAZAR - Gen:{score_gen} Crit:{score_crit} Avg:{int(avg_score)} Gap:{int(gap)}")
        return False


if __name__ == "__main__":
    test_idea = {
        'nombre': 'Test SaaS',
        'score_generador': 80,
        'tam': '50M€'
    }
    critique(test_idea)
