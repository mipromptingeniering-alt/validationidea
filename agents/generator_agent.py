import os
import json
import hashlib
import httpx
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
        'groq_model': 'llama-3.3-70b-versatile'
    }

def load_prompts():
    """Cargar prompts del sistema"""
    prompts_file = 'config/prompts.json'
    
    if os.path.exists(prompts_file):
        with open(prompts_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return {
        'generator_system': "Eres un Product Manager experto. Genera ideas innovadoras y viables."
    }

def get_idea_fingerprint(idea):
    """Crear huella digital única de la idea"""
    key_parts = [
        idea.get('nombre', '').lower().strip(),
        idea.get('problema', '').lower().strip()[:100],
        idea.get('mercado_objetivo', '').lower().strip()[:50]
    ]
    combined = '|'.join(key_parts)
    return hashlib.md5(combined.encode()).hexdigest()

def load_existing_ideas():
    """Cargar ideas existentes para evitar duplicados"""
    existing_fingerprints = set()
    existing_names = []
    
    # Cargar publicadas
    csv_file = 'data/ideas-validadas.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.split(',')
                if len(parts) >= 2:
                    name = parts[1].strip()
                    existing_names.append(name.lower())
    
    # Cargar rechazadas
    rejected_file = 'data/rejected_ideas.json'
    if os.path.exists(rejected_file):
        with open(rejected_file, 'r', encoding='utf-8') as f:
            rejected = json.load(f)
            for item in rejected:
                idea = item.get('idea', {})
                fp = item.get('fingerprint')
                if fp:
                    existing_fingerprints.add(fp)
                name = idea.get('nombre', '').lower().strip()
                if name:
                    existing_names.append(name)
    
    return existing_fingerprints, existing_names

def generate_with_groq(research_data, prompts, config, existing_names):
    """Generar idea usando Groq API"""
    
    api_key = os.environ.get('GROQ_API_KEY')
    if not api_key:
        raise ValueError("GROQ_API_KEY no configurada")
    
    client = Groq(
        api_key=api_key,
        http_client=httpx.Client()
    )
    
    system_prompt = prompts.get('generator_system', '')
    
    # Lista de ideas recientes para evitar
    recent_names = ', '.join(existing_names[-30:]) if existing_names else 'ninguna'
    
    user_prompt = f"""Genera UNA idea de producto digital COMPLETAMENTE NUEVA E INNOVADORA.

CONTEXTO 2026:
- Tech Stack: {', '.join(research_data.get('tech_stack_2026', []))}
- Tendencias HN: {', '.join(research_data.get('hacker_news_top', [])[:5])}
- GitHub Hot: {', '.join(research_data.get('github_trending', [])[:5])}

❌ NO REPETIR ESTAS IDEAS (ya generadas):
{recent_names}

REQUISITOS CRÍTICOS:
1. PROBLEMA MUY ESPECÍFICO: Dolor real, cuantificable, con urgencia
2. SOLUCIÓN 10X MEJOR: No "un poco mejor", sino radicalmente diferente
3. DIFERENCIACIÓN CLARA: 1 ventaja defendible (moat técnico o de red)
4. GO-TO-MARKET CONCRETO: Cómo conseguir primeros 100 usuarios SIN publicidad
5. MONETIZACIÓN CON NÚMEROS: Precio específico, por qué pagarán ese precio
6. VIABLE PARA 1 PERSONA: MVP en 2-6 semanas, sin equipo
7. CREATIVIDAD: Evita clichés tipo "AI assistant for X", "Notion for Y"

NICHOS PROMETEDORES 2026:
- Herramientas para solopreneurs/makers
- Automatización de tareas manuales tediosas
- Developer tools de nicho específico
- B2B micro-SaaS con ROI claro
- Productividad con IA pero NO chatbots genéricos

RESPONDE EN JSON VÁLIDO (sin markdown, sin comentarios):
{{
  "nombre": "Nombre único (máx 4 palabras)",
  "descripcion_corta": "Resumen en 1-2 frases (máx 50 palabras)",
  "problema": "Problema específico con dolor cuantificado (ej: 'pierden 5h/semana en X')",
  "solucion": "Cómo lo resuelve de forma innovadora",
  "propuesta_valor": "Por qué es 10X mejor que alternativas",
  "mercado_objetivo": "Persona específica + contexto (ej: 'Freelance designers que cobran >$100/h')",
  "competencia": ["Competidor real 1", "Competidor real 2", "Competidor real 3"],
  "diferenciacion": "1 ventaja clara y defendible vs competencia",
  "monetizacion": "Modelo + precio exacto (ej: 'Freemium $19/mes, pagan porque ROI es $200/mes')",
  "tech_stack": ["Next.js 15", "Supabase", "Vercel"],
  "dificultad": "Baja|Media",
  "tiempo_estimado": "2-6 semanas",
  "score_generador": 75
}}

SCORING:
- 90-95: Innovación radical + moat claro + go-to-market obvio
- 80-89: Idea sólida, buen mercado, diferenciación buena
- 70-79: Idea decente pero competencia fuerte o diferenciación débil
- <70: Rechazar

Sé CRÍTICO. Si no es realmente innovadora, baja el score."""

    try:
        completion = client.chat.completions.create(
            model=config.get('groq_model', 'llama-3.3-70b-versatile'),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.9,  # Más creatividad
            max_tokens=2048,
            response_format={"type": "json_object"}
        )
        
        idea_text = completion.choices[0].message.content
        idea = json.loads(idea_text)
        
        return idea
        
    except Exception as e:
        print(f"❌ Error generando con Groq: {e}")
        raise

def validate_idea(idea, config, existing_fingerprints):
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
    
    # Validar score
    score = idea.get('score_generador', 0)
    score_minimo = config.get('score_minimo_generador', 70)
    
    if score < score_minimo:
        print(f"❌ Score muy bajo: {score} < {score_minimo}")
        return False
    
    # Validar duplicado
    fingerprint = get_idea_fingerprint(idea)
    if fingerprint in existing_fingerprints:
        print(f"🔁 Idea duplicada (fingerprint match): {idea.get('nombre')}")
        return False
    
    print(f"✅ Idea válida - Score: {score} - Fingerprint: {fingerprint[:8]}")
    return True

def generate(max_retries=3):
    """Generar idea con reintentos"""
    
    print("🧠 Agente Generador iniciado...")
    
    research_data = load_research_cache()
    config = load_config()
    prompts = load_prompts()
    existing_fingerprints, existing_names = load_existing_ideas()
    
    print(f"📋 Ideas existentes: {len(existing_names)}")
    
    for attempt in range(1, max_retries + 1):
        print(f"📝 Intento {attempt}/{max_retries}...")
        
        try:
            idea = generate_with_groq(research_data, prompts, config, existing_names)
            
            if validate_idea(idea, config, existing_fingerprints):
                # Añadir fingerprint a la idea
                idea['_fingerprint'] = get_idea_fingerprint(idea)
                print(f"✅ Idea generada: {idea.get('nombre', 'Sin nombre')}")
                return idea
            
        except Exception as e:
            print(f"❌ Error en intento {attempt}: {e}")
    
    raise Exception("No se pudo generar idea válida después de 3 intentos")

if __name__ == "__main__":
    idea = generate()
    print(json.dumps(idea, indent=2, ensure_ascii=False))
