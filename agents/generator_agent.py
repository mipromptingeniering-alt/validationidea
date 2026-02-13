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
        "max_intentos": 5
    }

def load_existing_ideas():
    """Carga ideas existentes con más información para comparación"""
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
                        'descripcion': parts[2],
                        'fingerprint': parts[7]
                    })
    
    # También cargar rechazadas para evitar repetir
    rejected_file = 'data/rejected_ideas.json'
    if os.path.exists(rejected_file):
        with open(rejected_file, 'r', encoding='utf-8') as f:
            rejected = json.load(f)
            for item in rejected:
                idea = item.get('idea', {})
                existing.append({
                    'nombre': idea.get('nombre', ''),
                    'descripcion': idea.get('descripcion_corta', ''),
                    'fingerprint': idea.get('_fingerprint', '')
                })
    
    print(f"📋 Ideas existentes: {len(existing)}")
    return existing

def calculate_fingerprint(idea_dict):
    """Fingerprint más robusto"""
    text = f"{idea_dict.get('nombre', '')}{idea_dict.get('descripcion_corta', '')}".lower()
    # Limpiar caracteres especiales
    text = ''.join(e for e in text if e.isalnum() or e.isspace())
    return hashlib.md5(text.encode()).hexdigest()[:8]

def is_similar_semantic(new_idea, existing_ideas):
    """Detecta similitud semántica usando palabras clave"""
    
    # Categorías prohibidas (muy repetidas)
    banned_keywords = [
        'documentacion', 'documentation', 'dashboard', 'panel',
        'analytics', 'analitica', 'gestor', 'management', 'manager',
        'automatiza', 'automation', 'automate'
    ]
    
    new_name = new_idea.get('nombre', '').lower()
    new_desc = new_idea.get('descripcion_corta', '').lower()
    new_text = f"{new_name} {new_desc}"
    
    # Verificar palabras prohibidas
    for keyword in banned_keywords:
        count = sum(1 for ex in existing_ideas if keyword in ex['nombre'].lower() or keyword in ex['descripcion'].lower())
        if count >= 2 and keyword in new_text:
            print(f"⚠️  Categoría saturada detectada: '{keyword}' (ya hay {count} ideas similares)")
            return True
    
    # Comparar con existentes
    for existing in existing_ideas:
        ex_name = existing['nombre'].lower()
        ex_desc = existing['descripcion'].lower()
        
        # Nombre exacto o muy similar
        if new_name in ex_name or ex_name in new_name:
            print(f"⚠️  Nombre similar detectado: '{new_name}' ≈ '{ex_name}'")
            return True
        
        # Descripción muy similar (más de 50% palabras compartidas)
        new_words = set(new_desc.split())
        ex_words = set(ex_desc.split())
        if len(new_words) > 0:
            similarity = len(new_words & ex_words) / len(new_words)
            if similarity > 0.5:
                print(f"⚠️  Descripción similar ({int(similarity*100)}%): '{new_desc[:50]}...' ≈ '{ex_desc[:50]}...'")
                return True
    
    return False

def is_duplicate(new_idea, existing_ideas):
    """Verificación completa de duplicados"""
    
    # 1. Fingerprint exacto
    new_fp = calculate_fingerprint(new_idea)
    for existing in existing_ideas:
        if existing['fingerprint'] == new_fp:
            print(f"❌ Fingerprint duplicado: {new_fp}")
            return True
    
    # 2. Similitud semántica
    if is_similar_semantic(new_idea, existing_ideas):
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
    
    tendencias_text = ", ".join(tendencias[:3]) if tendencias else "IA, automatización, productividad"
    problemas_text = ", ".join(problemas[:3]) if problemas else "pérdida de tiempo en tareas repetitivas"
    
    # Construir lista de categorías saturadas
    categorias_saturadas = []
    keyword_count = {}
    for idea in existing_ideas:
        texto = f"{idea['nombre']} {idea['descripcion']}".lower()
        for word in ['documentacion', 'dashboard', 'analytics', 'gestor', 'automatiza']:
            if word in texto:
                keyword_count[word] = keyword_count.get(word, 0) + 1
    
    for word, count in keyword_count.items():
        if count >= 2:
            categorias_saturadas.append(word)
    
    categorias_text = ", ".join(categorias_saturadas) if categorias_saturadas else "ninguna"
    
    max_attempts = config.get('max_intentos', 5)
    
    for attempt in range(max_attempts):
        print(f"📝 Intento {attempt + 1}/{max_attempts}...")
        
        prompt = f"""Eres un experto en generar ideas SaaS innovadoras y ÚNICAS.

CONTEXTO ACTUAL DEL MERCADO:
- Tendencias: {tendencias_text}
- Problemas detectados: {problemas_text}

⚠️ CATEGORÍAS SATURADAS (NO GENERAR): {categorias_text}
⚠️ EVITA ideas genéricas de: documentación automática, dashboards, gestión básica, analytics simples

GENERA UNA IDEA SAAS COMPLETAMENTE ÚNICA que cumpla:
1. Resuelve un problema ESPECÍFICO y NICHO (no genérico)
2. Tiene mercado definido con números realistas
3. Monetizable desde día 1
4. Implementable en 4-6 semanas
5. Diferente a todo lo anterior
6. INNOVADORA (combina 2+ conceptos únicos)

EJEMPLOS DE BUENAS IDEAS (únicas y específicas):
- "SaaS para restaurantes que predice rotación de inventario con IA visual"
- "Marketplace B2B de freelancers pre-vetados para startups de criptomonedas"
- "Herramienta de compliance GDPR automatizado para e-commerce Shopify"

RESPONDE EN JSON EXACTO (sin markdown):
{{
  "nombre": "Nombre corto único (max 3 palabras, evita genéricos)",
  "slug": "nombre-url-friendly",
  "descripcion_corta": "Valor único en 1 línea (max 80 caracteres)",
  "descripcion": "Qué hace específicamente (2-3 frases con detalles)",
  "problema": "Problema MUY específico con datos (ej: 'Restaurantes pierden 3K€/mes en inventario caducado')",
  "solucion": "Cómo lo resuelve de forma única (tecnología/proceso específico)",
  "publico_objetivo": "Nicho MUY específico (ej: 'Dueños de franquicias de comida rápida 5-20 locales en España')",
  "tam": "Mercado total en € (realista, ej: '120M€')",
  "sam": "Mercado alcanzable en € (10% TAM, ej: '12M€')",
  "som": "Mercado objetivo año 1 en € (5% SAM, ej: '600K€')",
  "competencia": ["Competidor 1 específico", "Competidor 2 específico", "Alternativa actual"],
  "diferenciacion": "Qué te hace RADICALMENTE diferente (no 'mejor UX' o 'más rápido')",
  "precio_sugerido": "Precio mensual realista (ej: '79€/mes' para B2B, '19€/mes' para B2C)",
  "canales_adquisicion": ["Canal específico 1", "Canal 2", "Canal 3"],
  "score_generador": 78,
  "dificultad": "Media",
  "tiempo_estimado": "4-6 semanas",
  "stack_sugerido": ["Next.js", "Supabase", "Stripe"],
  "features_core": ["Feature específica 1", "Feature 2", "Feature 3"]
}}"""

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un experto en startups SaaS innovadoras. Respondes SOLO con JSON válido, sin markdown. Generas ideas ÚNICAS que nadie ha visto antes."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.9,  # Mayor creatividad
                max_tokens=2000
            )
            
            response_text = chat_completion.choices[0].message.content.strip()
            
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            idea = json.loads(response_text)
            
            # Validar que no sea duplicado
            if not is_duplicate(idea, existing_ideas):
                fingerprint = calculate_fingerprint(idea)
                idea['_fingerprint'] = fingerprint
                idea['_timestamp'] = datetime.now().isoformat()
                
                score = idea.get('score_generador', 0)
                print(f"✅ Idea ÚNICA validada - Score: {score} - Fingerprint: {fingerprint}")
                print(f"✅ Idea generada: {idea.get('nombre')}")
                return idea
            else:
                print(f"⚠️  Idea duplicada/similar, reintentando...")
        
        except json.JSONDecodeError as e:
            print(f"❌ Error parseando JSON: {e}")
            print(f"Respuesta recibida: {response_text[:200]}")
        except Exception as e:
            print(f"❌ Error generando idea: {e}")
    
    print(f"❌ No se pudo generar idea única tras {max_attempts} intentos")
    return None

if __name__ == "__main__":
    print("🧪 Probando generador con anti-duplicación mejorado...")
    idea = generate()
    if idea:
        print("\n" + "="*60)
        print(json.dumps(idea, indent=2, ensure_ascii=False))
        print("="*60)
