import os
import json
import hashlib
from datetime import datetime
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def load_config():
    config_file = 'config/generator_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        "umbral_minimo": 65,
        "umbral_critico": 45,
        "max_intentos": 3
    }

def load_existing_ideas():
    csv_file = 'data/ideas-validadas.csv'
    existing = []
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 8:
                    existing.append({
                        'nombre': parts[1],
                        'fingerprint': parts[7]
                    })
    print(f"📋 Ideas existentes: {len(existing)}")
    return existing

def calculate_fingerprint(idea_dict):
    text = f"{idea_dict.get('nombre', '')}{idea_dict.get('descripcion_corta', '')}".lower()
    return hashlib.md5(text.encode()).hexdigest()[:8]

def is_duplicate(new_idea, existing_ideas):
    new_fp = calculate_fingerprint(new_idea)
    for existing in existing_ideas:
        if existing['fingerprint'] == new_fp:
            return True
        nombre_similar = new_idea.get('nombre', '').lower()
        nombre_existing = existing['nombre'].lower()
        if nombre_similar in nombre_existing or nombre_existing in nombre_similar:
            return True
    return False

def load_research_cache():
    cache_file = 'data/research_cache.json'
    if os.path.exists(cache_file):
        with open(cache_file, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            tendencias = cache.get('trending_tools', [])
            problemas = cache.get('pain_points', [])
            return tendencias[:5], problemas[:5]
    return [], []

def generate():
    print("🧠 Agente Generador iniciado...")
    
    existing_ideas = load_existing_ideas()
    config = load_config()
    tendencias, problemas = load_research_cache()
    
    tendencias_text = ", ".join(tendencias[:3]) if tendencias else "IA, automatización, no-code"
    problemas_text = ", ".join(problemas[:3]) if problemas else "pérdida de tiempo en tareas repetitivas"
    
    max_attempts = config.get('max_intentos', 3)
    
    for attempt in range(max_attempts):
        print(f"📝 Intento {attempt + 1}/{max_attempts}...")
        
        prompt = f"""Eres un experto en generar ideas SaaS innovadoras y viables.

CONTEXTO ACTUAL DEL MERCADO:
- Tendencias: {tendencias_text}
- Problemas detectados: {problemas_text}

GENERA UNA IDEA SAAS ÚNICA que cumpla estos criterios:
1. Resuelve un problema real y específico
2. Tiene mercado definido (TAM/SAM/SOM calculables)
3. Monetizable desde día 1
4. Implementable en 4-6 semanas
5. Diferente a ideas genéricas de documentación, dashboards o gestión básica

RESPONDE EN JSON EXACTO (sin markdown, sin explicaciones):
{{
  "nombre": "Nombre corto y pegadizo (max 3 palabras)",
  "slug": "nombre-url-friendly",
  "descripcion_corta": "Descripción de 1 línea (max 100 caracteres)",
  "descripcion": "Descripción completa (2-3 frases explicando qué hace)",
  "problema": "Problema específico que resuelve (con datos si es posible: ej. 'pierden 10h/semana')",
  "solucion": "Cómo lo resuelve específicamente",
  "publico_objetivo": "Quién lo usará (muy específico: ej. 'Freelancers de diseño con equipos remotos')",
  "tam": "Mercado total en € (ej. '150M€')",
  "sam": "Mercado alcanzable en € (ej. '15M€')",
  "som": "Mercado objetivo primer año en € (ej. '750K€')",
  "competencia": ["Competidor 1", "Competidor 2", "Competidor 3"],
  "diferenciacion": "Qué te hace único vs competencia",
  "precio_sugerido": "Precio mensual (ej. '49€/mes')",
  "canales_adquisicion": ["Canal 1", "Canal 2", "Canal 3"],
  "score_generador": 75,
  "dificultad": "Media",
  "tiempo_estimado": "4-6 semanas",
  "stack_sugerido": ["Next.js", "Supabase", "Stripe"],
  "features_core": ["Feature 1", "Feature 2", "Feature 3"]
}}"""

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en startups SaaS. Respondes SOLO con JSON válido, sin markdown ni explicaciones."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.8,
                max_tokens=2000
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            idea = json.loads(response_text)
            
            if not is_duplicate(idea, existing_ideas):
                fingerprint = calculate_fingerprint(idea)
                idea['_fingerprint'] = fingerprint
                idea['_timestamp'] = datetime.now().isoformat()
                
                score = idea.get('score_generador', 0)
                print(f"✅ Idea válida - Score: {score} - Fingerprint: {fingerprint}")
                print(f"✅ Idea generada: {idea.get('nombre')}")
                return idea
            else:
                print(f"⚠️  Idea duplicada, reintentando...")
        
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"Respuesta recibida: {response_text[:200]}")
        except Exception as e:
            print(f"❌ Error generando idea: {e}")
    
    print(f"❌ No se pudo generar idea única tras {max_attempts} intentos")
    return None

if __name__ == "__main__":
    print("🧪 Probando generador...")
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
