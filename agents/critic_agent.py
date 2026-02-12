import os
import json
from groq import Groq

def load_config():
    """Cargar configuración"""
    config_file = 'config/system_config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        'score_minimo_critico': 60,
        'groq_model': 'llama-3.1-70b-versatile'
    }

def load_prompts():
    """Cargar prompts"""
    prompts_file = 'config/prompts.json'
    
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        'critic_system': "Eres un inversor VC escéptico de Sequoia Capital. Has visto 10,000 pitches y solo invertiste en 50. Sé brutalmente honesto."
    }

def critique_with_groq(idea, prompts, config):
    """Criticar idea usando Groq API"""
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY no configurada")
    
    from groq import Groq
import httpx

client = Groq(
    api_key=api_key,
    http_client=httpx.Client()
)

    
    system_prompt = prompts.get('critic_system', '')
    
    user_prompt = f"""IDEA A EVALUAR:

Nombre: {idea.get('nombre')}
Problema: {idea.get('problema')}
Solución: {idea.get('solucion')}
Mercado: {idea.get('mercado_objetivo')}
Competencia: {', '.join(idea.get('competencia', []))}
Diferenciación: {idea.get('diferenciacion')}
Monetización: {idea.get('monetizacion')}

EVALÚA CRÍTICAMENTE:
1. ¿Es realmente innovadora o una copia?
2. ¿Mercado grande? (TAM > $50M)
3. ¿Diferenciación real vs competencia?
4. ¿Viable técnicamente para 1 persona?
5. ¿Riesgos no mencionados?
6. ¿El problema realmente duele?
7. ¿Monetización realista?

RESPONDE EN JSON:
{{
  "score_critico": 65,
  "fortalezas": ["Fortaleza real 1", "Fortaleza real 2", "Fortaleza real 3"],
  "debilidades": ["Debilidad honesta 1", "Debilidad honesta 2", "Debilidad honesta 3"],
  "riesgos_mayores": ["Riesgo 1", "Riesgo 2"],
  "competencia_real": ["Competidor no mencionado 1", "Competidor no mencionado 2"],
  "veredicto_honesto": "Tu veredicto sin filtros en 2-3 frases",
  "probabilidad_exito": "25%",
  "recomendacion": "Publicar"
}}

Score debe ser honesto (40-90). Sé duro pero justo."""

    try:
        completion = client.chat.completions.create(
            model=config.get('groq_model', 'llama-3.1-70b-versatile'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        critique_text = completion.choices[0].message.content
        critique = json.loads(critique_text)
        
        return critique
        
    except Exception as e:
        print(f"❌ Error criticando con Groq: {e}")
        raise

def decide_publish(idea, critique, config):
    """Decidir si publicar la idea"""
    
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    
    score_min_gen = config.get('score_minimo_generador', 70)
    score_min_crit = config.get('score_minimo_critico', 60)
    
    if score_gen >= score_min_gen and score_crit >= score_min_crit:
        print(f"✅ PUBLICAR - Gen:{score_gen} Crit:{score_crit}")
        return True
    else:
        print(f"❌ RECHAZAR - Gen:{score_gen} Crit:{score_crit}")
        return False

def critique(idea):
    """Criticar idea principal"""
    
    print("🎯 Agente Crítico iniciado...")
    
    config = load_config()
    prompts = load_prompts()
    
    try:
        critique_result = critique_with_groq(idea, prompts, config)
        
        score = critique_result.get('score_critico', 0)
        print(f"✅ Crítica completada - Score: {score}")
        
        return critique_result
        
    except Exception as e:
        print(f"❌ Error en crítica: {e}")
        raise

if __name__ == "__main__":
    test_idea = {
        "nombre": "Test Idea",
        "problema": "Test problem",
        "solucion": "Test solution",
        "mercado_objetivo": "Developers",
        "competencia": ["Comp1"],
        "diferenciacion": "Unique",
        "monetizacion": "Freemium",
        "score_generador": 75
    }
    
    result = critique(test_idea)
    print(json.dumps(result, indent=2, ensure_ascii=False))
