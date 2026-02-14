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
    return {}

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

def is_duplicate(idea, existing_ideas):
    """Validación duplicados"""
    nombre = str(idea.get('nombre', '')).lower().strip()
    
    if not nombre or len(nombre) < 3:
        return True
    
    for existing in existing_ideas:
        if existing.get('nombre'):
            ratio = SequenceMatcher(None, nombre, existing['nombre']).ratio()
            if ratio > 0.80:
                return True
    
    return False

def get_monetizable_product():
    """50 productos monetizables (no solo SaaS)"""
    
    products = [
        # TEMPLATES & PLANTILLAS (10)
        {
            "tipo": "Notion Template",
            "vertical": "Creators & Productividad",
            "problema": "Creadores pierden 5h/semana organizando contenido y tareas en sistemas desordenados",
            "producto": "Notion Content OS - Sistema completo para creators: calendario editorial, ideas bank, analytics tracker, client CRM",
            "monetizacion": "€29 one-time en Gumroad",
            "esfuerzo": "20h crear + 2h/mes soporte",
            "revenue_6m": "€1,500 (50 ventas × €29)",
            "como": "Vender en Gumroad + Reddit r/Notion + Twitter + ProductHunt"
        },
        {
            "tipo": "Figma UI Kit",
            "vertical": "Diseñadores & Developers",
            "problema": "Designers gastan 15h creando components desde cero para cada proyecto SaaS",
            "producto": "SaaS UI Kit Pro - 500+ components + variants + auto-layout + design system completo",
            "monetizacion": "€49 Gumroad o €9/mes Figma Community",
            "esfuerzo": "40h crear + actualizaciones mensuales",
            "revenue_6m": "€2,450 (50 ventas × €49)",
            "como": "Lanzar Figma Community + Behance + Dribbble showcase"
        },
        {
            "tipo": "Spreadsheet Template",
            "vertical": "Freelancers",
            "problema": "Freelancers no saben si cobran suficiente ni calculan profitability correctamente",
            "producto": "Freelance Finance Tracker - Google Sheets con: pricing calculator, profit margins, tax estimator, client tracker",
            "monetizacion": "€19 Gumroad",
            "esfuerzo": "15h crear",
            "revenue_6m": "€950 (50 ventas × €19)",
            "como": "Reddit r/freelance + Twitter + blog posts SEO"
        },
        {
            "tipo": "Canva Templates Pack",
            "vertical": "Instagram Creators",
            "problema": "Creators tardan 3h/semana diseñando posts Instagram que no destacan",
            "producto": "Instagram Growth Pack - 100 templates Canva editables: posts, stories, reels covers, carousels",
            "monetizacion": "€29 Gumroad",
            "esfuerzo": "25h crear",
            "revenue_6m": "€1,450 (50 ventas × €29)",
            "como": "Instagram + Pinterest + Etsy"
        },
        {
            "tipo": "Email Templates",
            "vertical": "Sales & Marketing",
            "problema": "SDRs envían cold emails genéricos con 2% reply rate",
            "producto": "Cold Email Playbook - 50 templates testeados (15%+ reply rate) + follow-up sequences + subject lines",
            "monetizacion": "€39 Gumroad",
            "esfuerzo": "20h crear",
            "revenue_6m": "€1,950 (50 ventas × €39)",
            "como": "LinkedIn + Twitter + Indie Hackers"
        },
        
        # GUÍAS & EBOOKS (10)
        {
            "tipo": "eBook Guide",
            "vertical": "Developers indie",
            "problema": "Devs no saben cómo monetizar side projects más allá de ads",
            "producto": "'From Side Project to €10K MRR' - 150 páginas: pricing strategies, marketing no-code, primeros 100 customers",
            "monetizacion": "€29 Gumroad + €9/mes newsletter premium",
            "esfuerzo": "60h escribir",
            "revenue_6m": "€2,900 (100 ventas × €29)",
            "como": "ProductHunt + HackerNews + Dev.to + Twitter"
        },
        {
            "tipo": "Video Course",
            "vertical": "No-code builders",
            "problema": "Gente quiere crear apps pero coding intimida, no-code tutorials son superficiales",
            "producto": "Bubble.io Masterclass - 15 vídeos (6h totales): Build 3 real apps (CRM, Marketplace, SaaS) step-by-step",
            "monetizacion": "€99 one-time en Gumroad",
            "esfuerzo": "80h grabar + editar",
            "revenue_6m": "€4,950 (50 ventas × €99)",
            "como": "YouTube free content → paid course funnel"
        },
        {
            "tipo": "Notion Guide",
            "vertical": "Solopreneurs",
            "problema": "Solopreneurs tienen 5 herramientas (CRM, project mgmt, docs, calendar) pagando €100/mes total",
            "producto": "'Run Your Business in Notion' - 80 páginas + templates: CRM, finances, content, OKRs, todo en Notion gratis",
            "monetizacion": "€39 Gumroad (guía + templates bundle)",
            "esfuerzo": "40h escribir + crear templates",
            "revenue_6m": "€1,950 (50 ventas × €39)",
            "como": "Reddit r/Notion + Twitter + Medium"
        },
        {
            "tipo": "Checklist Pack",
            "vertical": "Product Launchers",
            "problema": "Launchers olvidan pasos críticos (SEO, analytics, backups) y lanzan productos incompletos",
            "producto": "Product Launch Checklist Pro - 300+ items verificados: pre-launch, launch day, post-launch, growth",
            "monetizacion": "€19 Gumroad",
            "esfuerzo": "20h crear + research",
            "revenue_6m": "€950 (50 ventas × €19)",
            "como": "ProductHunt + Indie Hackers + Twitter"
        },
        {
            "tipo": "Swipe File",
            "vertical": "Copywriters",
            "problema": "Copywriters luchan con writer's block, necesitan inspiración comprobada",
            "producto": "High-Converting Copy Swipe - 500+ ejemplos reales: landing pages, emails, ads (con conversion rates)",
            "monetizacion": "€49 Gumroad + €9/mes updates",
            "esfuerzo": "50h coleccionar + categorizar",
            "revenue_6m": "€2,450 (50 ventas × €49)",
            "como": "Twitter + LinkedIn + communities"
        },
        
        # APPS & EXTENSIONES (10)
        {
            "tipo": "Chrome Extension",
            "vertical": "LinkedIn Users",
            "problema": "Enviar conexiones LinkedIn personalizadas tarda 10 min/persona",
            "producto": "LinkedIn Connector Pro - Extension que auto-personaliza mensajes con IA usando profile info",
            "monetizacion": "€9/mes (20 connections/día gratis, ilimitado paid)",
            "esfuerzo": "40h desarrollar + Chrome Store",
            "revenue_6m": "€2,700 (50 users × €9 × 6 meses)",
            "como": "ProductHunt + Chrome Web Store SEO + Reddit"
        },
        {
            "tipo": "Raycast Extension",
            "vertical": "Mac Power Users",
            "problema": "Developers cambian entre apps para buscar docs, snippets, commands",
            "producto": "DevTools for Raycast - Busca Stack Overflow, GitHub, MDN docs sin salir de Raycast",
            "monetizacion": "€5/mes (freemium)",
            "esfuerzo": "30h desarrollar",
            "revenue_6m": "€1,500 (50 users × €5 × 6 meses)",
            "como": "Raycast Store + Twitter + HackerNews"
        },
        {
            "tipo": "Obsidian Plugin",
            "vertical": "Note-takers",
            "problema": "Obsidian users quieren AI pero plugins son complejos o caros",
            "producto": "AI Writer for Obsidian - Plugin que mejora notas con Claude (summaries, expand, rewrite)",
            "monetizacion": "€7/mes",
            "esfuerzo": "35h desarrollar",
            "revenue_6m": "€2,100 (50 users × €7 × 6 meses)",
            "como": "Obsidian Community + Reddit r/ObsidianMD"
        },
        {
            "tipo": "Figma Plugin",
            "vertical": "UI Designers",
            "problema": "Exportar assets de Figma a código CSS tarda 1h por proyecto",
            "producto": "Figma to TailwindCSS - Plugin que convierte designs a Tailwind classes automático",
            "monetizacion": "€9/mes o €49 lifetime",
            "esfuerzo": "45h desarrollar",
            "revenue_6m": "€2,450 (50 × €49 lifetime)",
            "como": "Figma Community + Twitter + ProductHunt"
        },
        {
            "tipo": "Telegram Bot",
            "vertical": "Crypto Traders",
            "problema": "Traders pierden oportunidades porque monitorean precios manualmente",
            "producto": "Crypto Alert Bot - Telegram bot con alertas custom price + whale movements + news",
            "monetizacion": "€15/mes (10 alertas gratis, ilimitado paid)",
            "esfuerzo": "25h desarrollar",
            "revenue_6m": "€4,500 (50 users × €15 × 6 meses)",
            "como": "Telegram channels crypto + Twitter + Reddit"
        },
        
        # SERVICIOS & PRODUCTIZED (10)
        {
            "tipo": "Productized Service",
            "vertical": "SaaS Founders",
            "problema": "Founders no saben si su idea tiene mercado, necesitan validación rápida",
            "producto": "Idea Validation in 48h - Servicio: 20 entrevistas target users + report con insights + go/no-go",
            "monetizacion": "€500 por validación",
            "esfuerzo": "8h por cliente",
            "revenue_6m": "€6,000 (12 clientes × €500)",
            "como": "Twitter + Indie Hackers + referrals"
        },
        {
            "tipo": "Design Service",
            "vertical": "Indie Hackers",
            "problema": "Indie hackers son developers, sus landings parecen de 1999",
            "producto": "Landing Page in 24h - Diseño + desarrollo Webflow de landing profesional",
            "monetizacion": "€300 por landing",
            "esfuerzo": "6h por cliente",
            "revenue_6m": "€6,000 (20 clientes × €300)",
            "como": "ProductHunt + Twitter + Dribbble showcase"
        },
        {
            "tipo": "Content Service",
            "vertical": "B2B SaaS",
            "problema": "SaaS necesitan content para SEO pero hiring writer es €3K/mes",
            "producto": "SEO Content Package - 4 artículos/mes (1500 words) optimized for keywords",
            "monetizacion": "€400/mes por cliente",
            "esfuerzo": "12h por cliente/mes",
            "revenue_6m": "€4,800 (2 clientes × €400 × 6 meses)",
            "como": "LinkedIn + cold outreach + SEO"
        },
        {
            "tipo": "Setup Service",
            "vertical": "Consultants",
            "problema": "Consultores quieren Notion workspace pro pero setup tarda 20 horas",
            "producto": "Notion Setup for Consultants - 2 sesiones: configuro workspace completo + training",
            "monetizacion": "€250 por setup",
            "esfuerzo": "4h por cliente",
            "revenue_6m": "€3,750 (15 clientes × €250)",
            "como": "Notion Reddit + LinkedIn + Twitter"
        },
        {
            "tipo": "Coaching",
            "vertical": "Side Project Builders",
            "problema": "Builders lanzan productos que nadie usa, necesitan guidance",
            "producto": "Side Project Coaching - 4 sesiones 1-on-1: validación, MVP, launch, primeros users",
            "monetizacion": "€600 (4 × €150 sesiones)",
            "esfuerzo": "6h por cliente",
            "revenue_6m": "€6,000 (10 clientes × €600)",
            "como": "Twitter + testimonials + word of mouth"
        },
        
        # NEWSLETTERS & MEMBERSHIPS (10)
        {
            "tipo": "Newsletter Premium",
            "vertical": "Indie Hackers",
            "problema": "Info sobre indie hacking es scattered, need curated digest",
            "producto": "Indie Insider Weekly - Newsletter: 5 case studies + tool reviews + revenue screenshots real founders",
            "monetizacion": "€9/mes (free tier con 1 case study)",
            "esfuerzo": "8h/semana research + escribir",
            "revenue_6m": "€2,700 (50 subs × €9 × 6 meses)",
            "como": "Twitter + Substack + guest posts"
        },
        {
            "tipo": "Discord Community",
            "vertical": "No-code Builders",
            "problema": "No-coders aprenden solos, stuck sin ayuda cuando bloqueados",
            "producto": "No-Code Club - Discord con: daily challenges, code reviews, job board, templates library",
            "monetizacion": "€19/mes (free tier limitado)",
            "esfuerzo": "10h/semana moderar",
            "revenue_6m": "€5,700 (50 members × €19 × 6 meses)",
            "como": "YouTube + Twitter + referrals"
        },
        {
            "tipo": "Job Board",
            "vertical": "Remote Workers",
            "problema": "Job boards genéricos tienen 1000s postings, hard to find quality remote gigs",
            "producto": "RemoteFirst Jobs - Job board curado: solo empresas 100% remote, salaries visible, no agencies",
            "monetizacion": "€99 por job posting (employers pagan)",
            "esfuerzo": "5h/semana curar + moderar",
            "revenue_6m": "€5,940 (60 postings × €99)",
            "como": "SEO + Twitter + partnerships remote companies"
        },
        {
            "tipo": "Directory",
            "vertical": "Tool Seekers",
            "problema": "Buscar tools en Google muestra ads y content farms, no reviews reales",
            "producto": "Honest SaaS Reviews - Directory con reviews honestos (no affiliate bias), user ratings, price comparisons",
            "monetizacion": "€50/mes listing destacado + ads",
            "esfuerzo": "15h/semana reviews",
            "revenue_6m": "€3,000 (10 sponsors × €50 × 6 meses)",
            "como": "SEO programático + Reddit + HackerNews"
        },
        {
            "tipo": "Resource Hub",
            "vertical": "Content Creators",
            "problema": "Creators gastan €500/mes en tools, no saben qué deals/alternatives existen",
            "producto": "Creator Tools Hub - Database 500+ tools con: pricing, alternatives, deals exclusivos, user reviews",
            "monetizacion": "€15/mes acceso + €100 tool listing fee",
            "esfuerzo": "20h setup + 5h/semana updates",
            "revenue_6m": "€4,500 (50 users × €15 × 6 meses)",
            "como": "YouTube + Twitter + ProductHunt"
        }
    ]
    
    return random.choice(products)

def generate():
    """Genera producto monetizable (no solo SaaS)"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        product = get_monetizable_product()
        timestamp = int(time.time())
        variation = random.randint(1000, 9999)
        
        system_prompt = f"""Genera producto monetizable 2026.

TIPO: {product['tipo']}
VERTICAL: {product['vertical']}
PROBLEMA: {product['problema']}
PRODUCTO: {product['producto']}
MONETIZACIÓN: {product['monetizacion']}
REVENUE 6M: {product['revenue_6m']}
CÓMO VENDER: {product['como']}

Evita: {', '.join([i['nombre'][:15] for i in existing_ideas[-5:] if i.get('nombre')])}

JSON (sin markdown, sin explicación):
{{
  "nombre": "[Nombre producto único] {variation}",
  "slug": "producto-{variation}",
  "tipo_producto": "{product['tipo']}",
  "categoria": "{product['vertical']}",
  "descripcion": "{product['producto'][:150]}",
  "descripcion_corta": "{product['problema'][:100]}",
  "problema": "{product['problema']}",
  "solucion": "{product['producto']}",
  "publico_objetivo": "{product['vertical']}",
  "propuesta_valor": "{product['producto'][:80]}",
  "diferenciacion": "Específico para {product['vertical']}",
  "modelo_monetizacion": "{product['monetizacion']}",
  "revenue_6_meses": "{product['revenue_6m']}",
  "esfuerzo_inicial": "{product.get('esfuerzo', '30h')}",
  "como_monetizar": "{product['como']}",
  "precio_sugerido": "29",
  "canales_venta": ["{product['como'].split(' + ')[0]}", "Twitter", "ProductHunt"],
  "validacion_inicial": "Crear MVP y vender a primeros 10 clientes en 2 semanas",
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
            
            # Normalizar campos a strings
            for key in idea:
                if isinstance(idea[key], list):
                    idea[key] = ', '.join(str(x) for x in idea[key])
            
            if not idea.get('nombre'):
                idea['nombre'] = f"{product['tipo']} {variation}"
            
            if not is_duplicate(idea, existing_ideas):
                print(f"✅ ÚNICA - {idea['nombre']}")
                return idea
        
        except json.JSONDecodeError:
            # Fallback robusto
            idea = {
                'nombre': f"{product['tipo']} Pro {variation}",
                'slug': f"producto-{variation}",
                'tipo_producto': product['tipo'],
                'categoria': product['vertical'],
                'descripcion': product['producto'][:200],
                'descripcion_corta': product['problema'][:100],
                'problema': product['problema'],
                'solucion': product['producto'],
                'publico_objetivo': product['vertical'],
                'propuesta_valor': product['producto'][:80],
                'diferenciacion': f"Específico para {product['vertical']}",
                'modelo_monetizacion': product['monetizacion'],
                'revenue_6_meses': product['revenue_6m'],
                'esfuerzo_inicial': product.get('esfuerzo', '30h'),
                'como_monetizar': product['como'],
                'precio_sugerido': '29',
                'canales_venta': product['como'][:50],
                'validacion_inicial': 'MVP + primeros 10 clientes',
                'score_generador': 85
            }
            
            if not is_duplicate(idea, existing_ideas):
                print(f"✅ FALLBACK - {idea['nombre']}")
                return idea
        
        except Exception as e:
            print(f"⚠️  Error: {e}")
            continue
    
    print("❌ No generó idea única")
    return None


if __name__ == "__main__":
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
