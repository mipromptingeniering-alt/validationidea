import os
import json
import hashlib
import csv
import random
import time
from groq import Groq
from difflib import SequenceMatcher

MAX_ATTEMPTS = 5
SIMILARITY_THRESHOLD = 0.20

def load_config():
    """Carga configuración del generador"""
    config_file = 'config/generator_config.json'
    if os.path.exists(config_file):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return {
        'min_score_generador': 70,
        'creativity_boost': 1.2,
        'diversification': True
    }

def load_existing_ideas():
    """Carga ideas existentes"""
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

def load_researcher_insights():
    """Carga insights del agente investigador"""
    insights_file = 'data/research-insights.json'
    
    if os.path.exists(insights_file):
        try:
            with open(insights_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return None

def calculate_fingerprint(nombre, descripcion):
    combined = f"{str(nombre).lower()}|{str(descripcion).lower()}"
    return hashlib.md5(combined.encode()).hexdigest()[:8]

def is_similar(text1, text2):
    if not text1 or not text2 or len(text1) < 3 or len(text2) < 3:
        return False
    ratio = SequenceMatcher(None, str(text1).lower(), str(text2).lower()).ratio()
    return ratio > SIMILARITY_THRESHOLD

def is_duplicate(idea, existing_ideas):
    """Validación duplicados"""
    nombre = str(idea.get('nombre', '')).lower().strip()
    descripcion = str(idea.get('descripcion_corta', '')).lower().strip()
    
    if not nombre or len(nombre) < 3:
        return True
    
    fingerprint = calculate_fingerprint(nombre, descripcion)
    
    for existing in existing_ideas:
        if existing.get('fingerprint') == fingerprint:
            return True
        
        if existing.get('nombre'):
            ratio = SequenceMatcher(None, nombre, existing['nombre']).ratio()
            if ratio > 0.80:
                return True
    
    return False

def get_niche_idea():
    """Alias para compatibilidad - llama a get_monetizable_product"""
    return get_monetizable_product()

def get_monetizable_product():
    """50 productos monetizables diversos"""
    
    products = [
        # TEMPLATES (10)
        {
            "tipo": "Notion Template",
            "nombre_base": "Notion Content OS",
            "vertical": "Creators",
            "problema": "Creators pierden 5h/semana organizando contenido en sistemas caóticos",
            "producto": "Sistema completo Notion: calendario editorial, banco ideas, analytics, CRM clientes",
            "monetizacion": "€29 one-time Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Gumroad + Reddit r/Notion + Twitter",
            "esfuerzo": "20h crear",
            "tool": "Notion API",
            "precio": "29"
        },
        {
            "tipo": "Figma UI Kit",
            "nombre_base": "SaaS UI Kit Pro",
            "vertical": "Designers",
            "problema": "Designers gastan 15h creando components desde cero cada proyecto",
            "producto": "500+ components Figma con variants, auto-layout, design system completo",
            "monetizacion": "€49 Gumroad",
            "revenue_6m": "€2,450 (50 ventas)",
            "como": "Figma Community + Dribbble",
            "esfuerzo": "40h crear",
            "tool": "Figma",
            "precio": "49"
        },
        {
            "tipo": "Spreadsheet",
            "nombre_base": "Freelance Finance Tracker",
            "vertical": "Freelancers",
            "problema": "Freelancers no calculan profit margins ni pricing correcto",
            "producto": "Google Sheets: pricing calculator, profit tracker, tax estimator, invoices",
            "monetizacion": "€19 Gumroad",
            "revenue_6m": "€950 (50 ventas)",
            "como": "Reddit r/freelance + Twitter",
            "esfuerzo": "15h crear",
            "tool": "Google Sheets",
            "precio": "19"
        },
        {
            "tipo": "Canva Templates",
            "nombre_base": "Instagram Growth Pack",
            "vertical": "Instagram Creators",
            "problema": "Creators tardan 3h/semana diseñando posts que no destacan",
            "producto": "100 templates Canva: posts, stories, reels covers editables",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Instagram + Pinterest + Etsy",
            "esfuerzo": "25h crear",
            "tool": "Canva",
            "precio": "29"
        },
        {
            "tipo": "Email Templates",
            "nombre_base": "Cold Email Playbook",
            "vertical": "Sales Teams",
            "problema": "SDRs tienen 2% reply rate con emails genéricos",
            "producto": "50 templates testeados 15%+ reply rate + follow-ups + subject lines",
            "monetizacion": "€39 Gumroad",
            "revenue_6m": "€1,950 (50 ventas)",
            "como": "LinkedIn + Twitter",
            "esfuerzo": "20h crear",
            "tool": "Email",
            "precio": "39"
        },
        {
            "tipo": "Webflow Template",
            "nombre_base": "SaaS Landing Template",
            "vertical": "SaaS Founders",
            "problema": "Founders pagan €500+ por landing page o usan templates feos",
            "producto": "Template Webflow: hero, features, pricing, testimonials, FAQ cloneable",
            "monetizacion": "€49 Webflow Marketplace",
            "revenue_6m": "€2,450 (50 ventas)",
            "como": "Webflow Showcase + Twitter",
            "esfuerzo": "30h crear",
            "tool": "Webflow",
            "precio": "49"
        },
        {
            "tipo": "Framer Template",
            "nombre_base": "Portfolio Pro",
            "vertical": "Designers",
            "problema": "Diseñadores quieren portfolio interactivo pero código intimida",
            "producto": "Template Framer animado: projects grid, case studies, contact form",
            "monetizacion": "€29 Framer Marketplace",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Framer Community + Dribbble",
            "esfuerzo": "25h crear",
            "tool": "Framer",
            "precio": "29"
        },
        {
            "tipo": "Airtable Base",
            "nombre_base": "Content Pipeline",
            "vertical": "Marketing Teams",
            "problema": "Marketing teams pierden ideas de contenido sin sistema organizado",
            "producto": "Base Airtable: idea capture, planning, production, analytics",
            "monetizacion": "€19 Gumroad",
            "revenue_6m": "€950 (50 ventas)",
            "como": "Twitter + Airtable Universe",
            "esfuerzo": "15h crear",
            "tool": "Airtable",
            "precio": "19"
        },
        {
            "tipo": "Pitch Deck",
            "nombre_base": "Investor Pitch Template",
            "vertical": "Startup Founders",
            "problema": "Founders crean pitch decks feos que VCs ignoran",
            "producto": "Google Slides template: 15 slides optimizados para funding rounds",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Twitter + Indie Hackers",
            "esfuerzo": "15h crear",
            "tool": "Google Slides",
            "precio": "29"
        },
        {
            "tipo": "Chrome Extension",
            "nombre_base": "LinkedIn Auto-Connect",
            "vertical": "LinkedIn Users",
            "problema": "Enviar LinkedIn messages personalizados tarda 10 min/persona",
            "producto": "Extension que auto-personaliza con IA usando profile info",
            "monetizacion": "€9/mes",
            "revenue_6m": "€2,700 (50 users × 6 meses)",
            "como": "Chrome Web Store + Reddit",
            "esfuerzo": "40h desarrollar",
            "tool": "Chrome API",
            "precio": "9"
        },
        # Continúa con más variedad...
        {
            "tipo": "eBook",
            "nombre_base": "Side Project Guide",
            "vertical": "Indie Hackers",
            "problema": "Devs no saben monetizar side projects más allá de ads",
            "producto": "150 páginas: pricing, marketing no-code, primeros 100 customers",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€2,900 (100 ventas)",
            "como": "ProductHunt + HackerNews + Twitter",
            "esfuerzo": "60h escribir",
            "tool": "PDF",
            "precio": "29"
        },
        {
            "tipo": "Video Course",
            "nombre_base": "No-Code Masterclass",
            "vertical": "No-code Builders",
            "problema": "Tutorials no-code son superficiales, gente no aprende apps reales",
            "producto": "15 videos 6h: Build 3 apps reales (CRM, Marketplace, SaaS)",
            "monetizacion": "€99 Gumroad",
            "revenue_6m": "€4,950 (50 ventas)",
            "como": "YouTube preview + paid course",
            "esfuerzo": "80h grabar",
            "tool": "Video",
            "precio": "99"
        },
        {
            "tipo": "Newsletter",
            "nombre_base": "Indie Insider Weekly",
            "vertical": "Indie Hackers",
            "problema": "Info indie hacking scattered, need curated digest",
            "producto": "Newsletter: 5 case studies + tool reviews + revenue screenshots",
            "monetizacion": "€9/mes",
            "revenue_6m": "€2,700 (50 subs × 6 meses)",
            "como": "Twitter + Substack",
            "esfuerzo": "8h/semana",
            "tool": "Substack",
            "precio": "9"
        },
        {
            "tipo": "Productized Service",
            "nombre_base": "Idea Validation 48h",
            "vertical": "SaaS Founders",
            "problema": "Founders no saben si idea tiene mercado antes de construir",
            "producto": "20 user interviews + report con insights + go/no-go decision",
            "monetizacion": "€500 por validación",
            "revenue_6m": "€6,000 (12 clientes)",
            "como": "Twitter + Indie Hackers",
            "esfuerzo": "8h por cliente",
            "tool": "Manual",
            "precio": "500"
        },
        {
            "tipo": "Discord Community",
            "nombre_base": "No-Code Club",
            "vertical": "No-code Builders",
            "problema": "No-coders aprenden solos, stuck cuando bloqueados",
            "producto": "Discord: challenges, reviews, job board, templates",
            "monetizacion": "€19/mes",
            "revenue_6m": "€5,700 (50 members × 6 meses)",
            "como": "YouTube + Twitter",
            "esfuerzo": "10h/semana moderar",
            "tool": "Discord",
            "precio": "19"
        }
    ]
    
    return random.choice(products)

def generate():
    """Genera producto monetizable"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    # Cargar insights investigador
    insights = load_researcher_insights()
    extra_context = ""
    
    if insights:
        print("📊 Usando insights del investigador...")
        trends = insights.get('trends', [])
        if trends:
            extra_context = f"\nTrends: {', '.join([t.get('keyword', '') for t in trends[:3]])}"
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        product = get_monetizable_product()
        timestamp = int(time.time())
        variation = random.randint(1000, 9999)
        
        nombre_unico = f"{product['nombre_base']} {variation}"
        slug = f"producto-{variation}"
        
        system_prompt = f"""Genera producto monetizable 2026.

TIPO: {product['tipo']}
VERTICAL: {product['vertical']}
PROBLEMA: {product['problema']}
PRODUCTO: {product['producto']}
MONETIZACIÓN: {product['monetizacion']}
REVENUE 6M: {product['revenue_6m']}
CÓMO: {product['como']}
{extra_context}

Evita: {', '.join([i['nombre'][:15] for i in existing_ideas[-5:] if i.get('nombre')])}

JSON sin markdown:
{{
  "nombre": "{nombre_unico}",
  "slug": "{slug}",
  "tipo_producto": "{product['tipo']}",
  "categoria": "{product['vertical']}",
  "descripcion": "{product['producto'][:150]}",
  "descripcion_corta": "{product['problema'][:100]}",
  "problema": "{product['problema']}",
  "solucion": "{product['producto']}",
  "publico_objetivo": "{product['vertical']}",
  "propuesta_valor": "Ahorra tiempo y genera ingresos",
  "diferenciacion": "Específico y accionable para {product['vertical']}",
  "tam": "50M",
  "sam": "5M",
  "som": "500K",
  "competencia": ["Competidor1", "Competidor2"],
  "ventaja_competitiva": "Nicho específico y validado",
  "precio_sugerido": "{product['precio']}",
  "modelo_monetizacion": "{product['monetizacion']}",
  "features_core": ["Feature 1", "Feature 2", "Feature 3"],
  "roadmap_mvp": ["Semana 1: Setup", "Semana 2: Desarrollo", "Semana 3: Launch"],
  "stack_sugerido": ["Tool1", "Tool2"],
  "integraciones": ["{product['tool']}", "Zapier"],
  "canales_adquisicion": ["Twitter", "ProductHunt"],
  "metricas_clave": ["Ventas", "MRR"],
  "riesgos": ["Competencia"],
  "validacion_inicial": "10 ventas primeras 2 semanas",
  "tiempo_estimado": "{product['esfuerzo']}",
  "inversion_inicial": "0",
  "dificultad": "Media",
  "revenue_6_meses": "{product['revenue_6m']}",
  "como_monetizar": "{product['como']}",
  "score_generador": 88
}}"""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": "JSON:"}
                ],
                temperature=1.2,
                max_tokens=1500
            )
            
            content = str(response.choices[0].message.content).strip()
            
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            idea = json.loads(content)
            
            # Asegurar campos son strings
            for key, value in idea.items():
                if isinstance(value, list):
                    idea[key] = ', '.join(str(x) for x in value)
                elif not isinstance(value, (str, int, float)):
                    idea[key] = str(value)
            
            idea['_fingerprint'] = calculate_fingerprint(
                idea.get('nombre', ''),
                idea.get('descripcion_corta', '')
            )
            
            if not is_duplicate(idea, existing_ideas):
                print(f"✅ ÚNICA - {idea['nombre']}")
                return idea
        
        except json.JSONDecodeError:
            pass
        except Exception as e:
            print(f"⚠️  Error: {e}")
        
        # FALLBACK ROBUSTO
        idea = {
            'nombre': nombre_unico,
            'slug': slug,
            'tipo_producto': product['tipo'],
            'categoria': product['vertical'],
            'descripcion': product['producto'][:200],
            'descripcion_corta': product['problema'][:100],
            'problema': product['problema'],
            'solucion': product['producto'],
            'publico_objetivo': product['vertical'],
            'propuesta_valor': 'Ahorra tiempo y genera ingresos',
            'diferenciacion': f"Específico para {product['vertical']}",
            'tam': '50M',
            'sam': '5M',
            'som': '500K',
            'competencia': 'Competencia existente',
            'ventaja_competitiva': 'Nicho específico',
            'precio_sugerido': product['precio'],
            'modelo_monetizacion': product['monetizacion'],
            'features_core': 'Feature 1, Feature 2, Feature 3',
            'roadmap_mvp': 'Semana 1: Setup, Semana 2: Dev, Semana 3: Launch',
            'stack_sugerido': 'Gumroad, Twitter',
            'integraciones': f"{product['tool']}, Zapier",
            'canales_adquisicion': 'Twitter, ProductHunt',
            'metricas_clave': 'Ventas, MRR',
            'riesgos': 'Competencia',
            'validacion_inicial': '10 ventas en 2 semanas',
            'tiempo_estimado': product['esfuerzo'],
            'inversion_inicial': '0',
            'dificultad': 'Media',
            'revenue_6_meses': product['revenue_6m'],
            'como_monetizar': product['como'],
            'score_generador': 85,
            '_fingerprint': calculate_fingerprint(nombre_unico, product['problema'][:100])
        }
        
        if not is_duplicate(idea, existing_ideas):
            print(f"✅ FALLBACK - {idea['nombre']}")
            return idea
    
    print("❌ No generó idea única")
    return None


if __name__ == "__main__":
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
