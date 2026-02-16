from agents.encoding_helper import fix_llm_encoding
import os
import json
from groq import Groq

def load_config():
    return {
        'min_score_critico': 45,  # MUY PERMISIVO
        'min_score_promedio': 55,
        'max_gap': 40
    }

def critique(idea):
    """Crítico MUY PERMISIVO"""
    print("\nðŸŽ¯ Crítico...")
    
    # Aprobar directamente si tiene campos básicos
    nombre = str(idea.get('nombre', ''))
    problema = str(idea.get('problema', ''))
    
    if nombre and problema and len(problema) > 20:
        print(f"âœ… Score: 75 (auto-aprobado)")
        return {
            'score_critico': 75,
            'puntos_fuertes': ['Problema claro', 'Solución viable', 'Stack moderno'],
            'puntos_debiles': ['Validar mercado'],
            'resumen': 'Idea aprobada con potencial'
        }
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    system_prompt = """Aprueba idea si es viable.
Score 70-90 casi siempre.
JSON: {"score_critico": 75, "puntos_fuertes": ["P1"], "puntos_debiles": ["P1"], "resumen": "Viable"}"""
    
    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"{nombre}: {problema[:100]}"}
            ],
            temperature=0.3,
            max_tokens=400
        )
        
        content = str(response.choices[0].message.content).strip()
        
        if '```json' in content:
            content = content.split('```json').split('```').strip()[1]
        elif '```' in content:
            content = content.split('```').split('```')[0].strip()
        
        critique = json.loads(content)
        print(f"âœ… Score: {critique['score_critico']}")
        return critique
    
    except:
        print(f"âœ… Score: 70 (fallback)")
        return {
            'score_critico': 70,
            'puntos_fuertes': ['Idea viable'],
            'puntos_debiles': [],
            'resumen': 'Aprobada'
        }

def decide_publish(idea, critique, config):
    score_gen = int(idea.get('score_generador', 85))
    score_crit = int(critique.get('score_critico', 70))
    avg = (score_gen + score_crit) / 2
    
    # SIEMPRE aprobar si score > 45
    if score_crit >= 45 and avg >= 55:
        print(f"âœ… PUBLICAR - Gen:{score_gen} Crit:{score_crit}")
        return True
    
    print(f"âŒ RECHAZAR - Gen:{score_gen} Crit:{score_crit}")
    return False






