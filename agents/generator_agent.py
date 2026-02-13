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
        "umbral_minimo": 75,
        "umbral_critico": 55,
        "max_intentos": 5,
        "aprender_de_rechazos": True
    }

def analyze_rejected_patterns():
    """
    Analiza ideas rechazadas para aprender patrones
    """
    rejected_file = 'data/rejected_ideas.json'
    if not os.path.exists(rejected_file):
        return []
    
    with open(rejected_file, 'r', encoding='utf-8') as f:
        rejected = json.load(f)
    
    # Últimas 10 rechazadas
    recent = rejected[-10:] if len(rejected) > 10 else rejected
    
    patterns = []
    for item in recent:
        idea = item.get('idea', {})
        reason = item.get('reason', '')
        patterns.append({
            'nombre': idea.get('nombre', ''),
            'categoria': extract_category(idea.get('nombre', '')),
            'reason': reason
        })
    
    return patterns

def extract_category(nombre):
    """Extrae categoría de la idea"""
    keywords = {
        'documentacion': ['doc', 'documentation', 'documentacion'],
        'dashboard': ['dashboard', 'panel', 'analytics'],
        'automatizacion': ['auto', 'automation', 'automatiza'],
        'gestion': ['gestor', 'management', 'manager']
    }
    
    nombre_lower = nombre.lower()
    for categoria, words in keywords.items():
        for word in words:
            if word in nombre_lower:
                return categoria
    return 'otra'

def load_existing_ideas():
    """Carga ideas existentes"""
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
    text = f"{idea_dict.get('nombre', '')}{idea_dict.get('descripcion_corta', '')}".lower()
    text = ''.join(e for e in text if e.isalnum() or e.isspace())
    return hashlib.md5(text.encode()).hexdigest()[:8]

def is_similar_semantic(new_idea, existing_ideas):
    banned_keywords = ['documentacion', 'documentation', 'dashboard', 'panel', 'analytics', 'analitica', 'gestor', 'management', 'manager', 'automatiza', 'automation', 'automate']
    
    new_name = new_idea.get('nombre', '').lower()
    new_desc = new_idea.get('descripcion_corta', '').lower()
    new_text = f"{new_name} {new_desc}"
    
    for keyword in banned_keywords:
        count = sum(1 for ex in existing_ideas if keyword in ex['nombre'].lower() or keyword in ex['descripcion'].lower())
        if count >= 2 and keyword in new_text:
            print(f"⚠️  Categoría saturada: '{keyword}' ({count} existentes)")
            return True
    
    for existing in existing_ideas:
        ex_name = existing['nombre'].lower()
        ex_desc = existing['descripcion'].lower()
        
        if new_name in ex_name or ex_name in new_name:
            print(f"⚠️  Nombre similar: '{new_name}' ≈ '{ex_name}'")
            return True
        
        new_words = set(new_desc.split())
        ex_words = set(ex_desc.split())
        if len(new_words) > 0:
            similarity = len(new_words & ex_words) / len(new_words)
            if similarity > 0.5:
                print(f"⚠️  Descripción similar ({int(similarity*100)}%)")
                return True
    
    return False

def is_duplicate(new_idea, existing_ideas):
    new_fp = calculate_fingerprint(new_idea)
    for existing in existing_ideas:
        if existing['fingerprint'] == new_fp:
            print(f"❌ Fingerprint duplicado: {new_fp}")
            return True
    
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
    rejected_patterns = analyze_rejected_patterns()
    
    tendencias_text = ", ".join(tendencias[:3]) if tendencias else "IA generativa, automatización inteligente, herramientas no-code"
    problemas_text = ", ".join(problemas[:3]) if problemas else "pérdida de tiempo en tareas manuales, falta integración entre herramientas"
    
    # Analizar rechazos
    rechazos_texto = ""
    if rejected_patterns:
        categorias_rechazadas = [p['categoria'] for p in rejected_patterns]
        razones_comunes = [p['reason'] for p in rejected_patterns]
        rechazos_texto = f"\n⚠️ EVITA ESTAS CATEGORÍAS (rechazadas recientemente): {', '.join(set(categorias_rechazadas))}\n⚠️ RAZONES DE RECHAZO COMUNES: {', '.join(set(razones_comunes[:3]))}"
    
    categorias_saturadas = []
    keyword_count = {}
    for idea in existing_ideas:
        texto = f"{idea['nombre']} {idea['descripcion']}".lower()
        for word in ['documentacion', 'dashboard', 'analytics', 'gestor', 'automatiza', 'panel', 'management']:
            if word in texto:
                keyword_count[word] = keyword_count.get(word, 0) + 1
    
    for word, count in keyword_count.items():
        if count >= 2:
            categorias_saturadas.append(f"{word}({count})")
    
    categorias_text = ", ".join(categorias_saturadas) if categorias_saturadas else "ninguna"
    
    max_attempts = config.get('max_intentos', 5)
    
    for attempt in range(max_attempts):
        print(f"📝 Intento {attempt + 1}/{max_attempts}...")
        
        prompt = f"""Eres un GENIO generando ideas SaaS ÚNICAS y RENTABLES.

CONTEXTO MERCADO:
- Tendencias HOT: {tendencias_text}
- Pain Points detectados: {problemas_text}

❌ CATEGORÍAS SATURADAS (NO TOCAR): {categorias_text}
{rechazos_texto}

GENERA UNA IDEA SaaS REVOLUCIONARIA:

REQUISITOS ESTRICTOS:
1. ✅ Problema ESPECÍFICO con datos (ej: "Restaurantes pierden 3.2K€/mes en inventario caducado")
2. ✅ Público NICHO (ej: "Dueños franquicias comida rápida 5-20 locales España", NO "restaurantes")
3. ✅ TAM mínimo 15M€ (mercados pequeños = rechazo automático)
4. ✅ Diferenciación RADICAL (no "mejor UX" o "más rápido", algo que nadie hace)
5. ✅ Precio 20-100€/mes (nada de 5€/mes ni 500€/mes)
6. ✅ INNOVADORA: combina 2+ conceptos únicos

INSPIRACIÓN (NO COPIES, INSPÍRATE):
- "SaaS para clínicas veterinarias que predice enfermedades con IA análisis heces"
- "Marketplace B2B verificado de proveedores sostenibles para retailers >1M€ facturación"
- "Compliance GDPR automatizado para e-commerce Shopify con auditorías AI mensuales"

JSON EXACTO (sin markdown):
{{
  "nombre": "Nombre pegadizo único (2-3 palabras)",
  "slug": "url-friendly",
  "descripcion_corta": "Valor único 1 frase (max 70 caracteres)",
  "descripcion": "Qué hace específicamente con detalles técnicos (3-4 frases)",
  "problema": "Problema específico con datos cuantitativos y urgencia",
  "solucion": "Cómo resuelve técnicamente (algoritmos, procesos únicos)",
  "publico_objetivo": "Nicho híper-específico con tamaño mercado",
  "tam": "Mercado total € (mínimo 15M€, máximo 500M€)",
  "sam": "10% TAM",
  "som": "5% SAM",
  "competencia": ["Competidor real 1", "Competidor 2", "Alternativa actual"],
  "diferenciacion": "Ventaja competitiva ÚNICA que nadie más tiene (no genérica)",
  "precio_sugerido": "Entre 20-100€/mes",
  "canales_adquisicion": ["Canal específico 1", "Canal 2", "Canal 3"],
  "score_generador": 82,
  "dificultad": "Media",
  "tiempo_estimado": "4-6 semanas",
  "stack_sugerido": ["Next.js", "Supabase", "Stripe", "Herramienta específica"],
  "features_core": ["Feature técnica específica 1", "Feature 2", "Feature 3"]
}}"""

        try:
            chat_completion = client.chat.completions.create(
                messages=[
                    {
                        "role": "system",
                        "content": "Eres un GENIO en startups SaaS. Generas ideas que nadie ha pensado. Respondes SOLO JSON válido sin markdown. Tus ideas son específicas, únicas y rentables."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model="llama-3.3-70b-versatile",
                temperature=0.95,
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
                print(f"✅ Idea ÚNICA - Score: {score} - FP: {fingerprint}")
                print(f"✅ {idea.get('nombre')}")
                return idea
            else:
                print(f"⚠️  Duplicada/similar, reintentando...")
        
        except json.JSONDecodeError as e:
            print(f"❌ JSON inválido: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"❌ No se pudo generar idea única tras {max_attempts} intentos")
    return None

if __name__ == "__main__":
    print("🧪 Probando generador mejorado...")
    idea = generate()
    if idea:
        print("\n" + "="*60)
        print(json.dumps(idea, indent=2, ensure_ascii=False))
        print("="*60)
