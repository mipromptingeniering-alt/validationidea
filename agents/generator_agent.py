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
                
                # Convertir a string si son listas
                if isinstance(nombre, list):
                    nombre = ' '.join(nombre)
                if isinstance(descripcion, list):
                    descripcion = ' '.join(descripcion)
                
                ideas.append({
                    'nombre': str(nombre).lower().strip(),
                    'descripcion': str(descripcion).lower().strip(),
                    'fingerprint': str(fingerprint).strip()
                })
    except Exception as e:
        print(f"⚠️  Error CSV: {e}")
    
    return ideas

def calculate_fingerprint(nombre, descripcion):
    combined = f"{nombre.lower()}|{descripcion.lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def normalize_field(field):
    """Convierte cualquier campo a string limpio"""
    if isinstance(field, list):
        return ' '.join([str(x) for x in field])
    return str(field).strip()

def is_similar(text1, text2):
    if not text1 or not text2:
        return False
    ratio = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
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
            "name": "IA + Creadores de Contenido",
            "tools": ["Claude API", "GPT-4", "Midjourney API", "ElevenLabs"],
            "problems": [
                "Creadores LinkedIn pierden 10h/semana escribiendo posts",
                "YouTubers tardan 4h escribiendo scripts de vídeos",
                "Podcasters necesitan show notes automáticos",
                "TikTokers necesitan ideas virales basadas en tendencias"
            ]
        },
        {
            "name": "Automatización + Freelancers",
            "tools": ["n8n", "Make", "Zapier", "Airtable API", "Notion API"],
            "problems": [
                "Freelancers pierden 6h/semana en admin",
                "Consultores necesitan CRM + facturación integrado",
                "Diseñadores necesitan contratos automatizados",
                "Developers necesitan time tracking automático"
            ]
        },
        {
            "name": "Scraping + IA + Análisis",
            "tools": ["Bright Data", "Apify", "Claude API", "Supabase"],
            "problems": [
                "eCommerce necesita monitoreo precios competencia 24/7",
                "Marketers necesitan análisis tendencias Twitter en tiempo real",
                "Recruiters necesitan perfiles LinkedIn actualizados",
                "Investors necesitan análisis startups fundraising"
            ]
        },
        {
            "name": "Micro-SaaS + APIs Públicas",
            "tools": ["Stripe API", "Notion API", "Google Sheets API", "Telegram API"],
            "problems": [
                "Usuarios Notion necesitan CRM dentro de Notion",
                "Equipos necesitan notificaciones Stripe en Telegram",
                "Freelancers necesitan invoicing desde Google Sheets",
                "Startups necesitan métricas en Notion dashboard"
            ]
        },
        {
            "name": "No-Code + IA",
            "tools": ["Bubble", "Webflow", "Airtable", "OpenAI API"],
            "problems": [
                "No-coders necesitan IA integrada en sus apps Bubble",
                "Webflow users necesitan chatbots personalizados",
                "Airtable users necesitan auto-categorización con IA",
                "Notion users necesitan búsqueda semántica inteligente"
            ]
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
        
        # Obtener semilla de inspiración
        seed = get_inspiration_seed()
        
        system_prompt = f"""Eres un experto en Micro-SaaS innovadores para 2026.

🎯 CATEGORÍA FOCUS: {seed['name']}
🛠️ HERRAMIENTAS SUGERIDAS: {', '.join(seed['tools'])}
❌ PROBLEMAS EJEMPLO: {seed['problems'][0]}

INSTRUCCIONES:
1. Genera UNA idea SaaS específica para esta categoría
2. DEBE usar al menos 2 de las herramientas sugeridas
3. DEBE resolver un problema ultra-específico (con números)
4. Precio: 19-79€/mes
5. MVP: 4-6 semanas

⚠️ EVITA estas ideas ya creadas: {', '.join([i['nombre'] for i in existing_ideas[-10:] if i['nombre']])}

📊 FORMATO JSON (solo JSON, sin texto extra):

{{
  "nombre": "Nombre pegadizo (2-3 palabras)",
  "slug": "nombre-en-minusculas",
  "descripcion": "3 frases. Línea 1: Qué hace. Línea 2: Cómo (menciona herramientas específicas). Línea 3: Resultado medible.",
  "descripcion_corta": "Resuelve [problema específico] con [tecnología] para [nicho]",
  "categoria": "{seed['name']}",
  "problema": "Problema ESPECÍFICO con números. Ej: 'Creadores LinkedIn pierden 12h/semana escribiendo posts manualmente'",
  "solucion": "IA [herramienta específica] analiza X, aprende Y, genera Z en N minutos. Integración con [API].",
  "publico_objetivo": "Nicho ultra-específico (Ej: 'YouTubers con 10K-100K suscriptores')",
  "propuesta_valor": "Ahorra [número] horas/semana o genera [número] euros extra al mes",
  "diferenciacion": "Única solución que [integración específica]. Competencia no tiene [feature único].",
  "tam": "50M€",
  "sam": "5M€",
  "som": "500K€",
  "competencia": ["Herramienta1", "Herramienta2", "Herramienta3"],
  "ventaja_competitiva": "Integración [API específica] + [característica única]",
  "precio_sugerido": "49€/mes",
  "modelo_monetizacion": "Freemium",
  "features_core": [
    "Integración [API específica] para [función]",
    "Dashboard personalizable con [métricas]",
    "Exportación automática a [herramienta]"
  ],
  "roadmap_mvp": [
    "Semana 1-2: Setup Next.js + Supabase + Auth",
    "Semana 3-4: Integración APIs {seed['tools'][0]}",
    "Semana 5-6: Dashboard + Stripe + Deploy Vercel"
  ],
  "stack_sugerido": ["Next.js 14", "Supabase", "Stripe", "Vercel", "{seed['tools'][0]}"],
  "integraciones": ["{seed['tools'][0]}", "{seed['tools'][1] if len(seed['tools']) > 1 else 'Zapier'}"],
  "canales_adquisicion": ["Twitter", "ProductHunt", "Reddit r/nicho"],
  "metricas_clave": ["MRR", "Churn %", "CAC"],
  "riesgos": ["Dependencia API externa", "Competencia copie feature"],
  "validacion_inicial": "Entrevistar 20 usuarios del nicho + landing con emails",
  "tiempo_estimado": "4-6 semanas",
  "inversion_inicial": "0-500€",
  "dificultad": "Media",
  "score_generador": 85
}}

EJEMPLOS EXITOSOS:

**PostGen AI** (LinkedIn creators): Claude API analiza 30 posts con mejor engagement, aprende patrones, genera 50 posts personalizados. Integración LinkedIn API para métricas. 39€/mes.

**ShopSpy** (eCommerce): Bright Data scraping + Claude análisis competencia 24/7. Alertas Telegram precio drops. Dashboard Notion. 59€/mes.

**ScriptFlow** (YouTubers): GPT-4 analiza tus vídeos top, genera scripts optimizados + timestamps + B-roll. YouTube Analytics API. 49€/mes.

Genera UNA idea NUEVA para la categoría {seed['name']}."""

        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "Genera la idea en JSON puro, sin texto adicional."}
                ],
                temperature=0.9 + (attempt * 0.1),
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Limpiar JSON
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            idea = json.loads(content)
            
            # NORMALIZAR todos los campos
            for key in idea.keys():
                if not isinstance(idea[key], (dict, list)):
                    idea[key] = normalize_field(idea[key])
            
            # Validar campos críticos
            if not idea.get('nombre') or not idea.get('descripcion_corta'):
                print("⚠️  Campos vacíos")
                continue
            
            if len(str(idea.get('nombre', ''))) < 3:
                print("⚠️  Nombre muy corto")
                continue
            
            # Fingerprint
            idea['_fingerprint'] = calculate_fingerprint(
                normalize_field(idea.get('nombre', '')),
                normalize_field(idea.get('descripcion_corta', ''))
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
