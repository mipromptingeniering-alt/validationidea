import os
import json
import hashlib
from groq import Groq
from difflib import SequenceMatcher

# Configuración
MAX_ATTEMPTS = 5
SIMILARITY_THRESHOLD = 0.40  # Bajado de 0.60 a 0.40 (más permisivo)

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
    csv_file = 'data/ideas-validadas.csv'
    ideas = []
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 8:
                    ideas.append({
                        'nombre': parts[1].lower(),
                        'descripcion': parts[2].lower(),
                        'fingerprint': parts[7]
                    })
    return ideas

def calculate_fingerprint(nombre, descripcion):
    combined = f"{nombre.lower()}|{descripcion.lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def is_similar(text1, text2):
    ratio = SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    return ratio > SIMILARITY_THRESHOLD

def is_duplicate(idea, existing_ideas):
    nombre = idea['nombre'].lower()
    descripcion = idea['descripcion_corta'].lower()
    fingerprint = calculate_fingerprint(nombre, descripcion)
    
    for existing in existing_ideas:
        if existing['fingerprint'] == fingerprint:
            print(f"❌ Fingerprint duplicado: {fingerprint}")
            return True
        
        if is_similar(nombre, existing['nombre']):
            print(f"⚠️  Nombre similar: '{nombre}' ≈ '{existing['nombre']}'")
            return True
        
        if is_similar(descripcion, existing['descripcion']):
            similarity = SequenceMatcher(None, descripcion, existing['descripcion']).ratio()
            print(f"⚠️  Descripción similar ({int(similarity*100)}%)")
            return True
    
    return False

def generate():
    """
    Genera idea SaaS INNOVADORA usando tendencias 2026 + IA
    """
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    config = load_config()
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    # PROMPT MEJORADO con tendencias 2026
    system_prompt = """Eres un experto generador de ideas SaaS INNOVADORAS para 2026.

🔥 TENDENCIAS OBLIGATORIAS 2026:
- IA Generativa (Claude 3.5, GPT-4, Gemini, Midjourney)
- Agentes IA autónomos
- Automatización con n8n, Make, Zapier
- APIs modernas (Stripe, Notion, Airtable, Supabase)
- No-code/Low-code tools
- Micro-SaaS (nichos específicos)
- Web scraping + IA
- Análisis de datos con IA
- Asistentes personalizados
- Workflows inteligentes

🎯 NICHOS RENTABLES:
- Creadores de contenido (YouTube, TikTok, LinkedIn)
- Freelancers y solopreneurs
- Equipos de marketing
- Desarrolladores indie
- Emprendedores
- Consultores
- Coaches
- eCommerce
- Real Estate
- Fitness/Health

💡 CARACTERÍSTICAS CLAVE:
1. **Problema ESPECÍFICO** (no genérico)
2. **Combina 2-3 herramientas** (Ej: Notion API + Claude + Stripe)
3. **Automatización clara** (ahorra X horas/semana)
4. **Monetización simple** (precio 19-99€/mes)
5. **MVP en 4-6 semanas**
6. **Stack moderno** (Next.js, Supabase, Vercel, Stripe)

🚫 EVITAR:
- Ideas genéricas ("CRM para pymes")
- Sin automatización
- Mercados saturados sin diferenciación
- Problemas vagos

📊 FORMATO JSON:
Genera UNA idea siguiendo EXACTAMENTE este formato. Solo el JSON, sin texto adicional.

{
  "nombre": "Nombre corto y pegadizo",
  "slug": "nombre-en-minusculas-con-guiones",
  "descripcion": "Descripción completa (2-3 frases). Debe mencionar ESPECÍFICAMENTE qué herramientas usa y qué automatiza.",
  "descripcion_corta": "Descripción de 1 frase ultra-específica",
  "categoria": "categoria",
  "problema": "Problema específico y medible. Ej: 'Los creadores de LinkedIn pierden 8h/semana escribiendo posts manualmente'",
  "solucion": "Solución técnica específica. Menciona APIs y herramientas. Ej: 'IA (Claude API) analiza tus mejores posts y genera 30 nuevos en tu estilo en 5 minutos'",
  "publico_objetivo": "Nicho ultra-específico",
  "propuesta_valor": "Ahorra X horas/semana o genera Y€ extra",
  "diferenciacion": "Qué hace único vs competencia. Menciona integración específica.",
  "tam": "Tamaño mercado en €",
  "sam": "Mercado alcanzable",
  "som": "Objetivo año 1",
  "competencia": ["Competidor 1", "Competidor 2", "Competidor 3"],
  "ventaja_competitiva": "Por qué ganamos",
  "precio_sugerido": "49€/mes",
  "modelo_monetizacion": "Freemium / Subscription / One-time",
  "features_core": [
    "Feature 1: Descripción técnica (API usada)",
    "Feature 2: Descripción técnica",
    "Feature 3: Descripción técnica"
  ],
  "roadmap_mvp": [
    "Semana 1-2: Setup Next.js + Supabase + Auth",
    "Semana 3-4: Integración APIs (especificar cuáles)",
    "Semana 5-6: UI + Stripe + Deploy"
  ],
  "stack_sugerido": ["Next.js 14", "Supabase", "Stripe", "Vercel", "API específica"],
  "integraciones": ["API 1", "API 2", "API 3"],
  "canales_adquisicion": ["Twitter", "ProductHunt", "Reddit /r/nicho"],
  "metricas_clave": ["MRR", "Churn", "CAC"],
  "riesgos": ["Riesgo 1", "Riesgo 2"],
  "validacion_inicial": "Cómo validar antes de construir",
  "tiempo_estimado": "4-6 semanas",
  "inversion_inicial": "0-500€",
  "dificultad": "Baja/Media/Alta",
  "score_generador": 85
}

🎲 EJEMPLOS DE IDEAS BUENAS:

1. **LinkedInBoost AI**
- Problema: Creadores LinkedIn escriben 8h/semana posts
- Solución: Claude API analiza tus 20 mejores posts, aprende tu estilo, genera 30 nuevos posts + carruseles en 5 minutos
- Stack: Next.js + Claude API + LinkedIn API + Supabase
- Precio: 39€/mes
- Diferenciación: Analiza engagement real vía LinkedIn API para aprender qué funciona

2. **NotionCRM Sync**
- Problema: Freelancers pierden clientes porque Notion no tiene CRM integrado
- Solución: Sincronización bidireccional automática entre Notion y Pipedrive/HubSpot vía APIs. Actualización en tiempo real.
- Stack: Next.js + Notion API + Pipedrive API + Webhooks
- Precio: 29€/mes
- Diferenciación: Única solución con sincronización bidireccional en tiempo real

3. **VideoScripter AI**
- Problema: YouTubers tardan 3h escribiendo scripts de vídeos
- Solución: GPT-4 analiza tus vídeos con mejor rendimiento, extrae patrón, genera scripts optimizados para CTR + timestamps + B-roll suggestions
- Stack: Next.js + OpenAI API + YouTube API + Supabase
- Precio: 49€/mes
- Diferenciación: Análisis de métricas YouTube reales (CTR, retention) para optimizar scripts

Genera UNA idea COMPLETAMENTE NUEVA siguiendo estos principios."""

    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Genera una idea SaaS INNOVADORA para 2026. Debe usar APIs modernas y resolver un problema específico. Ideas existentes a EVITAR: {[i['nombre'] for i in existing_ideas[-10:]]}"}
                ],
                temperature=1.1 + (attempt * 0.1),  # Más creatividad en cada intento
                max_tokens=2000
            )
            
            content = response.choices[0].message.content.strip()
            
            # Extraer JSON
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            idea = json.loads(content)
            
            # Añadir fingerprint
            idea['_fingerprint'] = calculate_fingerprint(idea['nombre'], idea['descripcion_corta'])
            
            # Validar unicidad
            if is_duplicate(idea, existing_ideas):
                print("⚠️  Duplicada/similar, reintentando...")
                continue
            
            print(f"✅ Idea ÚNICA - Score: {idea.get('score_generador', 0)} - FP: {idea['_fingerprint']}")
            print(f"✅ {idea['nombre']}")
            return idea
        
        except Exception as e:
            print(f"⚠️  Error en intento {attempt}: {e}")
            continue
    
    print("❌ No se pudo generar idea única tras 5 intentos")
    return None


if __name__ == "__main__":
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
