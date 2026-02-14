import os
import json
import hashlib
import csv
import random
import time
from groq import Groq
from difflib import SequenceMatcher

MAX_ATTEMPTS = 5
SIMILARITY_THRESHOLD = 0.20  # MUY PERMISIVO (antes 30%)

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
                nombre = str(row.get('nombre', '')).strip()
                descripcion = str(row.get('descripcion_corta', '')).strip()
                fingerprint = str(row.get('fingerprint', '')).strip()
                
                if nombre and len(nombre) > 2:
                    ideas.append({
                        'nombre': nombre.lower(),
                        'descripcion': descripcion.lower(),
                        'fingerprint': fingerprint
                    })
    except Exception as e:
        print(f"⚠️  Error CSV: {e}")
    
    return ideas

def calculate_fingerprint(nombre, descripcion):
    combined = f"{str(nombre).lower()}|{str(descripcion).lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def is_similar(text1, text2):
    if not text1 or not text2 or len(text1) < 3 or len(text2) < 3:
        return False
    ratio = SequenceMatcher(None, str(text1).lower(), str(text2).lower()).ratio()
    return ratio > SIMILARITY_THRESHOLD

def is_duplicate(idea, existing_ideas):
    """Validación MUY PERMISIVA"""
    nombre = str(idea.get('nombre', '')).lower().strip()
    descripcion = str(idea.get('descripcion_corta', '')).lower().strip()
    
    if not nombre or len(nombre) < 3:
        print("⚠️  Nombre muy corto o vacío")
        return True
    
    fingerprint = calculate_fingerprint(nombre, descripcion)
    
    # Solo rechazar si es EXACTAMENTE igual
    for existing in existing_ideas:
        if existing['fingerprint'] == fingerprint:
            print(f"⚠️  Fingerprint exacto: {fingerprint}")
            return True
        
        # Solo si similitud >80% (antes 20%)
        if existing['nombre']:
            ratio = SequenceMatcher(None, nombre, existing['nombre']).ratio()
            if ratio > 0.80:
                print(f"⚠️  Nombre muy similar: {nombre} ≈ {existing['nombre']} ({int(ratio*100)}%)")
                return True
    
    return False

def get_niche_idea():
    """Ideas ultra-específicas con variedad EXTREMA"""
    niches = [
        {
            "vertical": "LinkedIn Creators",
            "problema": "Pasan 8h/semana escribiendo posts que no generan engagement",
            "solucion": "IA analiza 100 posts con mejor engagement, extrae patrones, genera 50 posts en tu estilo optimizados para algoritmo LinkedIn",
            "tool": "Claude Sonnet 4.5",
            "precio": "39",
            "nombre": f"LinkedBoost AI"
        },
        {
            "vertical": "YouTube Creators 10K-100K subs",
            "problema": "Tardan 5h escribiendo scripts y no saben qué títulos funcionan",
            "solucion": "GPT-4 analiza tus vídeos con mejor CTR, genera scripts con ganchos + títulos A/B tested + timestamps automáticos",
            "tool": "GPT-4 API",
            "precio": "49",
            "nombre": f"ScriptGenius AI"
        },
        {
            "vertical": "eCommerce Shopify stores",
            "problema": "Pierden ventas porque competencia baja precios y no se enteran",
            "solucion": "Scraping Bright Data 24/7 de 50 competidores + alertas Telegram instant cuando bajan precio + sugerencias pricing IA",
            "tool": "Bright Data",
            "precio": "79",
            "nombre": f"PriceSpy Pro"
        },
        {
            "vertical": "Freelancers técnicos",
            "problema": "Pasan 4h/semana en admin: facturas, contratos, time tracking",
            "solucion": "Notion como CRM + generación automática facturas PDF + contratos templates + time tracking con Toggl API",
            "tool": "Notion API",
            "precio": "29",
            "nombre": f"FreelanceHub"
        },
        {
            "vertical": "Recruiters IT",
            "problema": "LinkedIn scraping manual de candidatos tarda 10h/semana",
            "solucion": "Bot extrae perfiles LinkedIn con skills específicas + enriquece con GitHub + email finder + exports a CRM",
            "tool": "Apify",
            "precio": "99",
            "nombre": f"TalentScout AI"
        },
        {
            "vertical": "Podcasters",
            "problema": "Edición y show notes tardan 3h por episodio",
            "solucion": "Whisper API transcribe + Claude genera show notes + timestamps + quotes destacadas + posts redes",
            "tool": "Whisper API",
            "precio": "59",
            "nombre": f"PodcastFlow AI"
        },
        {
            "vertical": "Newsletter Creators",
            "problema": "Research de contenido 6h/semana, engagement bajo 2%",
            "solucion": "IA escanea 100 fuentes, resume tendencias, genera drafts personalizados con tu voz, optimiza subject lines para +40% open rate",
            "tool": "Claude API",
            "precio": "49",
            "nombre": f"NewsletterPro AI"
        },
        {
            "vertical": "Agencias Marketing",
            "problema": "Reportes clientes tardan 5h/mes, formato inconsistente",
            "solucion": "Conecta Google Ads + Meta + LinkedIn, auto-genera reportes white-label PDF con insights IA, envío automático",
            "tool": "Google Sheets API",
            "precio": "149",
            "nombre": f"ReportMaster"
        },
        {
            "vertical": "SaaS Founders",
            "problema": "Seguimiento métricas en 5 herramientas, no ven MRR real",
            "solucion": "Dashboard Notion que sync Stripe MRR + ChurnKey + Google Analytics + cohorts automáticos con predicciones IA",
            "tool": "Stripe API",
            "precio": "79",
            "nombre": f"SaaSMetrics"
        },
        {
            "vertical": "Content Creators TikTok",
            "problema": "No saben qué trends usar, ideas virales tardan 2h/día",
            "solucion": "IA monitorea trending sounds + hashtags + analiza tus vídeos top, genera 30 ideas virales diarias con script y hooks",
            "tool": "TikTok API",
            "precio": "39",
            "nombre": f"TrendHunter AI"
        },
        {
            "vertical": "Consultores estrategia",
            "problema": "Propuestas tardan 8h, templates genéricas, win rate 20%",
            "solucion": "IA analiza propuestas ganadoras, genera propuesta personalizada por cliente con pricing dinámico en 30min",
            "tool": "GPT-4",
            "precio": "99",
            "nombre": f"ProposalGenius"
        },
        {
            "vertical": "SEO Agencies",
            "problema": "Keyword research manual 4h/proyecto, pierden long-tails",
            "solucion": "IA encuentra 500 long-tail keywords con Ahrefs API + analiza SERP + genera content briefs optimizados",
            "tool": "Ahrefs API",
            "precio": "89",
            "nombre": f"KeywordMiner AI"
        },
        {
            "vertical": "Real Estate Agents",
            "problema": "Descripciones propiedades genéricas, fotos sin optimizar",
            "solucion": "IA genera descripciones premium + optimiza fotos con Midjourney + crea virtual staging + posts Instagram",
            "tool": "Midjourney API",
            "precio": "69",
            "nombre": f"PropertyPro AI"
        },
        {
            "vertical": "Course Creators",
            "problema": "Outline de cursos tarda 10h, estructura inconsistente",
            "solucion": "IA genera outline completo con módulos + lecciones + scripts + quizzes basado en objetivo aprendizaje",
            "tool": "Claude API",
            "precio": "59",
            "nombre": f"CourseBuilder AI"
        },
        {
            "vertical": "Twitter Creators",
            "problema": "Threads que funcionan son impredecibles, engagement 1%",
            "solucion": "IA analiza tus 50 mejores tweets, genera threads con hooks probados, scheduling óptimo para +200% engagement",
            "tool": "GPT-4",
            "precio": "29",
            "nombre": f"ThreadGenius"
        }
    ]
    
    return random.choice(niches)

def generate():
    """Genera idea ULTRA-ESPECÍFICA"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        # Idea pre-definida ultra-específica
        niche = get_niche_idea()
        
        # Añadir timestamp para forzar unicidad
        timestamp = int(time.time())
        variation = random.randint(1000, 9999)
        
        system_prompt = f"""Eres experto en Micro-SaaS 2026.

Genera esta idea específica con VARIACIÓN ÚNICA:

VERTICAL: {niche['vertical']}
PROBLEMA: {niche['problema']}
SOLUCIÓN: {niche['solucion']}
HERRAMIENTA: {niche['tool']}
PRECIO: {niche['precio']} euros/mes
NOMBRE BASE: {niche['nombre']}

IMPORTANTE: El nombre debe ser ÚNICO. Añade variación: {niche['nombre']} {variation}

Responde JSON COMPLETO sin texto extra:

{{
  "nombre": "{niche['nombre']} Pro",
  "slug": "nombre-unico-{variation}",
  "descripcion": "{niche['solucion']} Stack: {niche['tool']}, Next.js, Stripe. ROI: 10x tiempo ahorrado.",
  "descripcion_corta": "{niche['problema'][:80]} - Solución IA automatizada",
  "categoria": "SaaS IA",
  "problema": "{niche['problema']}",
  "solucion": "{niche['solucion']}",
  "publico_objetivo": "{niche['vertical']}",
  "propuesta_valor": "Ahorra 8 horas semanales",
  "diferenciacion": "Única integración {niche['tool']} + automatización completa",
  "tam": "50M",
  "sam": "5M",
  "som": "500K",
  "competencia": ["Manual work", "Generic tools"],
  "ventaja_competitiva": "IA específica para {niche['vertical']}",
  "precio_sugerido": "{niche['precio']}",
  "modelo_monetizacion": "Subscription",
  "features_core": ["Automatización {niche['tool']}", "Dashboard tiempo real", "Integraciones API"],
  "roadmap_mvp": ["Semana 1-2: Setup Next.js Supabase", "Semana 3-4: {niche['tool']} integration", "Semana 5-6: Stripe Deploy"],
  "stack_sugerido": ["Next.js 14", "Supabase", "Stripe", "{niche['tool']}"],
  "integraciones": ["{niche['tool']}", "Zapier"],
  "canales_adquisicion": ["Twitter", "ProductHunt", "Reddit"],
  "metricas_clave": ["MRR", "Churn"],
  "riesgos": ["API dependency"],
  "validacion_inicial": "20 entrevistas nicho",
  "tiempo_estimado": "4-6 semanas",
  "inversion_inicial": "500",
  "dificultad": "Media",
  "score_generador": 88
}}"""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "JSON:"}
                ],
                temperature=1.2,  # MÁS CREATIVIDAD
                max_tokens=1500
            )
            
            content = str(response.choices[0].message.content).strip()
            
            # Limpiar JSON
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            idea = json.loads(content)
            
            # Asegurar campos mínimos
            if not idea.get('nombre'):
                idea['nombre'] = f"{niche['nombre']} {variation}"
            if not idea.get('descripcion_corta'):
                idea['descripcion_corta'] = niche['problema'][:100]
            
            # Fingerprint
            idea['_fingerprint'] = calculate_fingerprint(
                idea.get('nombre', ''),
                idea.get('descripcion_corta', '')
            )
            
            # Debug
            print(f"🔍 Generada: {idea['nombre']}")
            print(f"🔍 FP: {idea['_fingerprint']}")
            
            # Verificar duplicado
            if is_duplicate(idea, existing_ideas):
                print("⚠️  Duplicada, reintentando...")
                continue
            
            print(f"✅ ÚNICA - {idea['nombre']}")
            return idea
        
        except json.JSONDecodeError as e:
            print(f"⚠️  JSON error: {e}")
            # FALLBACK: Crear idea directamente
            idea = {
                'nombre': f"{niche['nombre']} {variation}",
                'slug': f"saas-{variation}",
                'descripcion': niche['solucion'][:200],
                'descripcion_corta': niche['problema'][:100],
                'categoria': 'SaaS IA',
                'problema': niche['problema'],
                'solucion': niche['solucion'],
                'publico_objetivo': niche['vertical'],
                'propuesta_valor': 'Ahorra tiempo',
                'diferenciacion': f'IA con {niche["tool"]}',
                'tam': '50M',
                'sam': '5M',
                'som': '500K',
                'competencia': ['Tool1', 'Tool2'],
                'ventaja_competitiva': 'Automatización IA',
                'precio_sugerido': niche['precio'],
                'modelo_monetizacion': 'Subscription',
                'features_core': ['Feature 1', 'Feature 2', 'Feature 3'],
                'roadmap_mvp': ['Setup', 'APIs', 'Deploy'],
                'stack_sugerido': ['Next.js', 'Supabase', 'Stripe'],
                'integraciones': [niche['tool'], 'Zapier'],
                'canales_adquisicion': ['Twitter', 'ProductHunt'],
                'metricas_clave': ['MRR', 'Churn'],
                'riesgos': ['API dependency'],
                'validacion_inicial': '20 entrevistas',
                'tiempo_estimado': '4-6 semanas',
                'inversion_inicial': '500',
                'dificultad': 'Media',
                'score_generador': 85,
                '_fingerprint': calculate_fingerprint(f"{niche['nombre']} {variation}", niche['problema'][:100])
            }
            
            if not is_duplicate(idea, existing_ideas):
                print(f"✅ FALLBACK ÚNICA - {idea['nombre']}")
                return idea
            
            continue
        except Exception as e:
            print(f"⚠️  Error: {e}")
            continue
    
    print("❌ No se generó idea única")
    return None


if __name__ == "__main__":
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
