import os
import json
import hashlib
import csv
from groq import Groq
from difflib import SequenceMatcher

MAX_ATTEMPTS = 5
SIMILARITY_THRESHOLD = 0.35  # Más permisivo (antes 0.40)

def load_config():
    config_file = 'config/generator_config.json'
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'min_score_generador': 70,
        'creativity_boost': 1.2,
        'diversification': True
    }

def load_existing_ideas():
    """Carga ideas usando CSV reader (maneja comas correctamente)"""
    csv_file = 'data/ideas-validadas.csv'
    ideas = []
    
    if os.path.exists(csv_file):
        try:
            with open(csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ideas.append({
                        'nombre': str(row.get('nombre', '')).lower().strip(),
                        'descripcion': str(row.get('descripcion_corta', '')).lower().strip(),
                        'fingerprint': str(row.get('fingerprint', '')).strip()
                    })
        except Exception as e:
            print(f"⚠️  Error leyendo CSV: {e}")
            # Fallback a parsing manual simple
            with open(csv_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[1:]
                for line in lines:
                    parts = line.strip().split(',')
                    if len(parts) >= 2:
                        ideas.append({
                            'nombre': parts[1].lower().strip(),
                            'descripcion': parts[2].lower().strip() if len(parts) > 2 else '',
                            'fingerprint': parts[7].strip() if len(parts) > 7 else ''
                        })
    
    return ideas

def calculate_fingerprint(nombre, descripcion):
    combined = f"{nombre.lower()}|{descripcion.lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def is_similar(text1, text2):
    """Compara similitud entre textos"""
    if not text1 or not text2:
        return False
    ratio = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    return ratio > SIMILARITY_THRESHOLD

def is_duplicate(idea, existing_ideas):
    """Verifica si la idea es duplicada o muy similar"""
    nombre = str(idea.get('nombre', '')).lower().strip()
    descripcion = str(idea.get('descripcion_corta', '')).lower().strip()
    
    if not nombre or not descripcion:
        return True
    
    fingerprint = calculate_fingerprint(nombre, descripcion)
    
    for existing in existing_ideas:
        # Verificar fingerprint
        if existing['fingerprint'] == fingerprint:
            print(f"❌ Fingerprint duplicado: {fingerprint}")
            return True
        
        # Verificar nombre similar
        if existing['nombre'] and is_similar(nombre, existing['nombre']):
            print(f"⚠️  Nombre similar: '{nombre}' ≈ '{existing['nombre']}'")
            return True
        
        # Verificar descripción similar
        if existing['descripcion'] and is_similar(descripcion, existing['descripcion']):
            similarity = SequenceMatcher(None, descripcion, existing['descripcion']).ratio()
            print(f"⚠️  Descripción similar ({int(similarity*100)}%)")
            return True
    
    return False

def generate():
    """Genera idea SaaS INNOVADORA"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    config = load_config()
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    system_prompt = """Eres un experto en ideas SaaS INNOVADORAS para 2026.

🔥 TENDENCIAS 2026:
- IA Generativa (Claude, GPT-4, Gemini, Midjourney)
- Agentes IA autónomos
- Automatización (n8n, Make, Zapier)
- APIs modernas (Stripe, Notion, Airtable, Supabase)
- No-code tools
- Micro-SaaS nichos específicos

🎯 NICHOS RENTABLES:
- Creadores contenido (YouTube, TikTok, LinkedIn)
- Freelancers
- Marketing teams
- Developers
- Emprendedores
- Consultores
- eCommerce

💡 CARACTERÍSTICAS:
1. Problema ESPECÍFICO
2. Combina 2-3 herramientas
3. Automatización clara
4. Precio 19-99€/mes
5. MVP 4-6 semanas
6. Stack: Next.js, Supabase, Stripe

🚫 EVITAR:
- Ideas genéricas
- Sin automatización
- Problemas vagos

📊 Genera JSON con esta estructura EXACTA:

{
  "nombre": "Nombre pegadizo",
  "slug": "nombre-en-minusculas",
  "descripcion": "2-3 frases. Menciona herramientas específicas y qué automatiza.",
  "descripcion_corta": "1 frase ultra-específica",
  "categoria": "categoria",
  "problema": "Problema específico medible con números",
  "solucion": "Solución técnica. Menciona APIs concretas.",
  "publico_objetivo": "Nicho específico",
  "propuesta_valor": "Ahorra X horas o genera Y euros",
  "diferenciacion": "Qué hace único. Integración específica.",
  "tam": "50M€",
  "sam": "5M€",
  "som": "500K€",
  "competencia": ["Comp1", "Comp2", "Comp3"],
  "ventaja_competitiva": "Por qué ganamos",
  "precio_sugerido": "49€/mes",
  "modelo_monetizacion": "Subscription",
  "features_core": [
    "Feature 1 con API específica",
    "Feature 2 con tecnología",
    "Feature 3 con integración"
  ],
  "roadmap_mvp": [
    "Semana 1-2: Setup",
    "Semana 3-4: APIs",
    "Semana 5-6: Deploy"
  ],
  "stack_sugerido": ["Next.js", "Supabase", "Stripe", "Vercel"],
  "integraciones": ["API1", "API2"],
  "canales_adquisicion": ["Twitter", "ProductHunt", "Reddit"],
  "metricas_clave": ["MRR", "Churn"],
  "riesgos": ["Riesgo1", "Riesgo2"],
  "validacion_inicial": "Cómo validar",
  "tiempo_estimado": "4-6 semanas",
  "inversion_inicial": "0-500€",
  "dificultad": "Media",
  "score_generador": 85
}

EJEMPLOS BUENOS:

**SocialBoost AI** - Claude API analiza 50 posts LinkedIn, aprende tu estilo, genera 30 posts optimizados en 5min. Diferenciación: Análisis engagement real vía LinkedIn API.

**ScraperFlow** - Scraping automatizado con Bright Data + IA que limpia datos + exporta a Google Sheets. Para agencias marketing. 59€/mes.

**VideoScripts AI** - GPT-4 analiza tus mejores vídeos YouTube, genera scripts con timestamps y B-roll suggestions. Para YouTubers. 39€/mes.

Genera UNA idea COMPLETAMENTE NUEVA."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Genera una idea SaaS innovadora. Evita estas ya existentes: {', '.join([i['nombre'] for i in existing_ideas[-10:] if i['nombre']])}"}
                ],
                temperature=1.0 + (attempt * 0.15),
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extraer JSON
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            idea = json.loads(content)
            
            # Validar campos requeridos
            if not idea.get('nombre') or not idea.get('descripcion_corta'):
                print("⚠️  Faltan campos requeridos")
                continue
            
            # Añadir fingerprint
            idea['_fingerprint'] = calculate_fingerprint(
                str(idea.get('nombre', '')), 
                str(idea.get('descripcion_corta', ''))
            )
            
            # Validar unicidad
            if is_duplicate(idea, existing_ideas):
                print("⚠️  Duplicada/similar, reintentando...")
                continue
            
            print(f"✅ Idea ÚNICA - Score: {idea.get('score_generador', 0)} - FP: {idea['_fingerprint']}")
            print(f"✅ {idea['nombre']}")
            return idea
        
        except json.JSONDecodeError as e:
            print(f"⚠️  Error JSON en intento {attempt}: {e}")
            continue
        except Exception as e:
            print(f"⚠️  Error en intento {attempt}: {e}")
            continue
    
    print("❌ No se pudo generar idea única tras 5 intentos")
    return None


if __name__ == "__main__":
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
