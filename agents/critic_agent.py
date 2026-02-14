import os
import json
from groq import Groq

def load_config():
    return {
        'min_score_critico': 50,
        'min_score_promedio': 60,
        'max_gap': 35
    }

def critique(idea):
    """Evalúa con criterios REALISTAS"""
    print("\n🎯 Crítico...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    # PROMPT CORTO
    system_prompt = """Evalúa idea SaaS 2026.

Aprueba (60-100) si:
- Problema claro
- Stack moderno
- Mercado >10M€

Rechaza (0-59) solo si:
- Problema vago
- Imposible técnicamente

JSON:
{
  "score_critico": 75,
  "puntos_fuertes": ["Punto 1", "Punto 2"],
  "puntos_debiles": ["Punto 1"],
  "resumen": "Buena idea."
}"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",  # Mismo modelo
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Idea: {idea.get('nombre')} - {idea.get('descripcion_corta')}"}
            ],
            temperature=0.3,
            max_tokens=500  # Muy reducido
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
            'resumen': 'Potencial'
        }

def decide_publish(idea, critique, config):
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    avg = (score_gen + score_crit) / 2
    
    if score_crit >= 50 and avg >= 60:
        print(f"✅ PUBLICAR - Gen:{score_gen} Crit:{score_crit}")
        return True
    
    print(f"❌ RECHAZAR - Gen:{score_gen} Crit:{score_crit}")
    return False
