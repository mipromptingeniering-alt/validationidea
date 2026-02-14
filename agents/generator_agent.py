import os
import json
import hashlib
import csv
from groq import Groq
from difflib import SequenceMatcher

MAX_ATTEMPTS = 5
SIMILARITY_THRESHOLD = 0.30

def load_config():
    config_file = 'config/generator_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'min_score_generador': 70}

def load_existing_ideas():
    """Carga ideas de forma segura"""
    csv_file = 'data/ideas-validadas.csv'
    ideas = []
    
    if not os.path.exists(csv_file):
        return ideas
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                nombre = row.get('nombre', '')
                descripcion = row.get('descripcion_corta', '')
                fingerprint = row.get('fingerprint', '')
                
                if isinstance(nombre, list):
                    nombre = ' '.join(str(x) for x in nombre)
                if isinstance(descripcion, list):
                    descripcion = ' '.join(str(x) for x in descripcion)
                
                ideas.append({
                    'nombre': str(nombre).lower().strip(),
                    'descripcion': str(descripcion).lower().strip(),
                    'fingerprint': str(fingerprint).strip()
                })
    except Exception as e:
        print(f"⚠️  Error CSV: {e}")
    
    return ideas

def calculate_fingerprint(nombre, descripcion):
    combined = f"{str(nombre).lower()}|{str(descripcion).lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def normalize_field(field):
    """Convierte cualquier campo a string limpio"""
    if field is None:
        return ""
    if isinstance(field, list):
        return ' '.join(str(x) for x in field)
    return str(field).strip()

def is_similar(text1, text2):
    if not text1 or not text2:
        return False
    ratio = SequenceMatcher(None, str(text1).lower(), str(text2).lower()).ratio()
    return ratio > SIMILARITY_THRESHOLD

def is_duplicate(idea, existing_ideas):
    nombre = normalize_field(idea.get('nombre', '')).lower()
    descripcion = normalize_field(idea.get('descripcion_corta', '')).lower()
    
    if not nombre or not descripcion or len(nombre) < 3:
        return True
    
    fingerprint = calculate_fingerprint(nombre, descripcion)
    
    for existing in existing_ideas:
        if existing['fingerprint'] == fingerprint:
            return True
        if existing['nombre'] and is_similar(nombre, existing['nombre']):
            return True
        if existing['descripcion'] and is_similar(descripcion, existing['descripcion']):
            return True
    
    return False

def get_inspiration_seed():
    """Genera semillas de inspiración rotativas"""
    import random
    
    categories = [
        {
            "name": "IA Creadores",
            "tools": ["Claude API", "GPT-4"],
            "problem": "Creadores pierden 10h/semana"
        },
        {
            "name": "Automatizacion",
            "tools": ["n8n", "Notion API"],
            "problem": "Freelancers pierden 6h admin"
        },
        {
            "name": "Scraping IA",
            "tools": ["Bright Data", "Claude"],
            "problem": "eCommerce necesita monitoreo"
        },
        {
            "name": "Micro SaaS",
            "tools": ["Stripe API", "Notion"],
            "problem": "Usuarios necesitan CRM"
        },
        {
            "name": "NoCode IA",
            "tools": ["Bubble", "OpenAI"],
            "problem": "Nocoders necesitan IA"
        }
    ]
    
    return random.choice(categories)

def generate():
    """Genera idea usando sistema de semillas"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        seed = get_inspiration_seed()
        
        evitar = ', '.join([str(i['nombre'])[:15] for i in existing_ideas[-5:] if i.get('nombre')])
        
        system_prompt = f"""Genera idea SaaS 2026.

Cat: {seed['name']}
Tools: {seed['tools'][0]}, {seed['tools'][1]}
Problema: {seed['problem']}
Evita: {evitar}

Responde SOLO JSON sin explicacion:

{{
  "nombre": "Nombre corto",
  "slug": "nombre-slug",
  "descripcion": "Automatiza X con {seed['tools'][0]} para usuarios Y",
  "descripcion_corta": "Soluciona problema con IA",
  "categoria": "SaaS IA",
  "problema": "Usuarios pierden 5 horas semanales en tarea X",
  "solucion": "IA automatiza proceso con {seed['tools'][0]} en 10 minutos",
  "publico_objetivo": "Profesionales digitales",
  "propuesta_valor": "Ahorra 5 horas semanales",
  "diferenciacion": "Unica integracion {seed['tools'][0]}",
  "tam": "50M",
  "sam": "5M",
  "som": "500K",
  "competencia": ["Tool1", "Tool2"],
  "ventaja_competitiva": "Automatizacion completa",
  "precio_sugerido": "49",
  "modelo_monetizacion": "Subscription",
  "features_core": ["Feature 1", "Feature 2", "Feature 3"],
  "roadmap_mvp": ["Semana 1-2 Setup", "Semana 3-4 APIs", "Semana 5-6 Deploy"],
  "stack_sugerido": ["Next.js", "Supabase", "Stripe"],
  "integraciones": ["{seed['tools'][0]}", "Zapier"],
  "canales_adquisicion": ["Twitter", "ProductHunt"],
  "metricas_clave": ["MRR", "Churn"],
  "riesgos": ["API dependencia"],
  "validacion_inicial": "20 entrevistas",
  "tiempo_estimado": "4-6 semanas",
  "inversion_inicial": "500",
  "dificultad": "Media",
  "score_generador": 85
}}"""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "JSON puro:"}
                ],
                temperature=0.9 + (attempt * 0.1),
                max_tokens=1200
            )
            
            content = str(response.choices[0].message.content).strip()
            
            # Extraer JSON limpio
            if '```json' in content:
                parts = content.split('```json')
                if len(parts) > 1:
                    content = parts[1].split('```').strip()
            elif '```' in content:
                parts = content.split('```')
                if len(parts) > 1:
                    content = parts.split('```')[0].strip()
            
            idea = json.loads(content)
            
            # Normalizar TODOS los campos a strings
            normalized_idea = {}
            for key, value in idea.items():
                if isinstance(value, (dict, list)):
                    normalized_idea[key] = value
                else:
                    normalized_idea[key] = normalize_field(value)
            
            idea = normalized_idea
            
            # Validar campos críticos
            if not idea.get('nombre') or not idea.get('descripcion_corta'):
                print("⚠️  Campos vacíos")
                continue
            
            if len(str(idea.get('nombre', ''))) < 3:
                print("⚠️  Nombre muy corto")
                continue
            
            # Fingerprint
            idea['_fingerprint'] = calculate_fingerprint(
                idea.get('nombre', ''),
                idea.get('descripcion_corta', '')
            )
            
            # Verificar duplicado
            if is_duplicate(idea, existing_ideas):
                print("⚠️  Duplicada, reintentando...")
                continue
            
            print(f"✅ ÚNICA - Score: {idea.get('score_generador', 0)} - {idea['nombre']}")
            return idea
        
        except json.JSONDecodeError as e:
            print(f"⚠️  Error JSON: {e}")
            continue
        except Exception as e:
            print(f"⚠️  Error: {e}")
            continue
    
    print("❌ No se pudo generar idea única")
    return None


if __name__ == "__main__":
    for i in range(3):
        print(f"\n{'='*60}\nTEST {i+1}\n{'='*60}")
        idea = generate()
        if idea:
            print(json.dumps(idea, indent=2, ensure_ascii=False))
