import os
import json
from groq import Groq

def load_research_cache():
    """Cargar cache de investigación"""
    cache_file = 'data/research_cache.json'
    
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        'tech_stack_2026': ['Next.js 15', 'Supabase', 'Vercel', 'Tailwind CSS'],
        'hacker_news_top': [],
        'github_trending': []
    }

def load_config():
    """Cargar configuración"""
    config_file = 'config/system_config.json'
    
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        'score_minimo_generador': 70,
        'groq_model': 'llama-3.1-70b-versatile'
    }

def load_prompts():
    """Cargar prompts del sistema"""
    prompts_file = 'config/prompts.json'
    
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        'generator_system': "Eres un Product Manager experto con 15 años de experiencia. Genera ideas de productos digitales innovadoras y viables que resuelvan problemas reales."
    }

def generate_with_groq(research_data, prompts, config):
    """Generar idea usando Groq API"""
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY no configurada")
    
    client = Groq(api_key=api_key)
    
    system_prompt = prompts.get('generator_system', '')
    
    user_prompt = f"""Genera una idea de producto digital innovadora.

CONTEXTO DE TENDENCIAS 2026:
- Tecnologías: {', '.join(research_data.get('tech_stack_2026', []))}
- Trending en HN: {', '.join(research_data.get('hacker_news_top', [])[:3])}

REQUISITOS:
1. Debe resolver un problema real y doloroso
2. Mercado grande (TAM > $50M)
3. Técnicamente viable para 1 persona
4. Usar tecnologías modernas 2026

RESPONDE EN JSON CON ESTA ESTRUCTURA EXACTA:
{{
  "nombre": "Nombre del producto (max 4 palabras)",
  "descripcion_corta": "Descripción en 1-2 frases (max 50 palabras)",
  "problema": "Problema específico que resuelve",
  "solucion": "Cómo lo resuelve",
  "propuesta_valor": "Por qué es mejor que alternativas",
  "mercado_objetivo": "Quién lo usaría",
  "competencia": ["Competidor 1", "Competidor 2", "Competidor 3"],
  "diferenciacion": "Qué te hace único",
  "monetizacion": "Modelo de negocio (ej: Freemium $9-29/mes)",
  "tech_stack": ["Next.js 15", "Supabase", "Vercel"],
  "dificultad": "Baja",
  "tiempo_estimado": "4 semanas",
  "score_generador": 85
}}

El score_generador debe ser realista (70-95). No seas optimista, sé crítico."""

    try:
        completion = client.chat.completions.create(
            model=config.get('groq_model', 'llama-3.1-70b-versatile'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.8,
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        idea_text = completion.choices[0].message.content
        idea = json.loads(idea_text)
        
        return idea
        
    except Exception as e:
        print(f"❌ Error generando con Groq: {e}")
        raise

def validate_idea(idea, config):
    """Validar que la idea cumple requisitos mínimos"""
    
    required_fields = [
        'nombre', 'descripcion_corta', 'problema', 'solucion',
        'propuesta_valor', 'mercado_objetivo', 'competencia',
        'diferenciacion', 'monetizacion', 'tech_stack',
        'dificultad', 'tiempo_estimado', 'score_generador'
    ]
    
    for field in required_fields:
        if field not in idea:
            print(f"❌ Falta campo: {field}")
            return False
    
    score = idea.get('score_generador', 0)
    score_minimo = config.get('score_minimo_generador', 70)
    
    if score < score_minimo:
        print(f"❌ Score muy bajo: {score} < {score_minimo}")
        return False
    
    print(f"✅ Idea válida - Score: {score}")
    return True

def generate(max_retries=3):
    """Generar idea con reintentos"""
    
    print("🧠 Agente Generador iniciado...")
    
    research_data = load_research_cache()
    config = load_config()
    prompts = load_prompts()
    
    for attempt in range(1, max_retries + 1):
        print(f"📝 Intento {attempt}/{max_retries}...")
        
        try:
            idea = generate_with_groq(research_data, prompts, config)
            
            if validate_idea(idea, config):
                print(f"✅ Idea generada: {idea.get('nombre', 'Sin nombre')}")
                return idea
            
        except Exception as e:
            print(f"❌ Error en intento {attempt}: {e}")
    
    raise Exception("No se pudo generar idea válida después de 3 intentos")

if __name__ == "__main__":
    idea = generate()
    print(json.dumps(idea, indent=2, ensure_ascii=False))
