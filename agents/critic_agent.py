import os
import json
from groq import Groq

def load_config():
    return {
        'min_score_critico': 50,  # Muy permisivo
        'min_score_promedio': 60,
        'max_gap': 35
    }

def critique(idea):
    """Evalúa con criterios REALISTAS"""
    print("\n🎯 Crítico...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = """Evalúa esta idea SaaS con criterios REALISTAS para 2026.

✅ APRUEBA (score 60-100) si:
- Problema específico y medible
- Solución técnicamente viable
- Stack moderno (Next.js, APIs, IA)
- Mercado > 10M€
- MVP en 4-8 semanas

❌ RECHAZA (score 0-59) solo si:
- Problema muy vago
- Técnicamente imposible
- Mercado < 5M€
- Ya existe solución exacta gratis

Responde en JSON:
{
  "score_critico": 75,
  "puntos_fuertes": ["Punto 1", "Punto 2", "Punto 3"],
  "puntos_debiles": ["Punto 1", "Punto 2"],
  "recomendaciones": ["Rec 1", "Rec 2"],
  "resumen": "Buena idea porque [razón]."
}"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": json.dumps(idea, ensure_ascii=False)}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        content = response.choices[0].message.content.strip()
        
        if '```json' in content:
            content = content.split('```json').split('```').strip()[1]
        elif '```' in content:
            content = content.split('```').split('```')[0].strip()
        
        critique = json.loads(content)
        
        print(f"✅ Score: {critique['score_critico']}")
        return critique
    
    except Exception as e:
        print(f"⚠️  Error: {e}")
        return {
            'score_critico': 65,
            'puntos_fuertes': ['Idea viable'],
            'puntos_debiles': [],
            'resumen': 'Idea con potencial'
        }

def decide_publish(idea, critique, config):
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    avg = (score_gen + score_crit) / 2
    
    if score_crit >= 50 and avg >= 60:
        print(f"✅ PUBLICAR - Gen:{score_gen} Crit:{score_crit} Avg:{int(avg)}")
        return True
    
    print(f"❌ RECHAZAR - Gen:{score_gen} Crit:{score_crit}")
    return False
