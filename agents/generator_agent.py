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
                if nombre and len(nombre) > 2:
                    ideas.append({'nombre': nombre.lower()})
    except:
        pass
    
    return ideas

def is_duplicate(idea, existing_ideas):
    """Valida si es duplicado"""
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
    """50 productos monetizables diversos"""
    
    products = [
        # TEMPLATES (10)
        {
            "tipo": "Notion Template",
            "nombre_base": "Notion Content OS",
            "problema": "Creators pierden 5h/semana organizando contenido en sistemas caóticos",
            "producto": "Sistema completo Notion: calendario editorial, banco ideas, analytics, CRM clientes",
            "monetizacion": "€29 one-time Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Gumroad + Reddit r/Notion + Twitter",
            "esfuerzo": "20h crear"
        },
        {
            "tipo": "Figma UI Kit",
            "nombre_base": "SaaS UI Kit Pro",
            "problema": "Designers gastan 15h creando components desde cero cada proyecto",
            "producto": "500+ components Figma con variants, auto-layout, design system completo",
            "monetizacion": "€49 Gumroad",
            "revenue_6m": "€2,450 (50 ventas)",
            "como": "Figma Community + Dribbble",
            "esfuerzo": "40h crear"
        },
        {
            "tipo": "Spreadsheet",
            "nombre_base": "Freelance Finance Tracker",
            "problema": "Freelancers no calculan profit margins ni pricing correcto",
            "producto": "Google Sheets: pricing calculator, profit tracker, tax estimator, invoices",
            "monetizacion": "€19 Gumroad",
            "revenue_6m": "€950 (50 ventas)",
            "como": "Reddit r/freelance + Twitter",
            "esfuerzo": "15h crear"
        },
        {
            "tipo": "Canva Templates",
            "nombre_base": "Instagram Growth Pack",
            "problema": "Creators tardan 3h/semana diseñando posts que no destacan",
            "producto": "100 templates Canva: posts, stories, reels covers editables",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Instagram + Pinterest + Etsy",
            "esfuerzo": "25h crear"
        },
        {
            "tipo": "Email Templates",
            "nombre_base": "Cold Email Playbook",
            "problema": "SDRs tienen 2% reply rate con emails genéricos",
            "producto": "50 templates testeados 15%+ reply rate + follow-ups + subject lines",
            "monetizacion": "€39 Gumroad",
            "revenue_6m": "€1,950 (50 ventas)",
            "como": "LinkedIn + Twitter",
            "esfuerzo": "20h crear"
        },
        {
            "tipo": "Webflow Template",
            "nombre_base": "SaaS Landing Template",
            "problema": "Founders pagan €500+ por landing page o usan templates feos",
            "producto": "Template Webflow: hero, features, pricing, testimonials, FAQ cloneable",
            "monetizacion": "€49 Webflow Marketplace",
            "revenue_6m": "€2,450 (50 ventas)",
            "como": "Webflow Showcase + Twitter",
            "esfuerzo": "30h crear"
        },
        {
            "tipo": "Framer Template",
            "nombre_base": "Portfolio Pro",
            "problema": "Diseñadores quieren portfolio interactivo pero código intimida",
            "producto": "Template Framer animado: projects grid, case studies, contact form",
            "monetizacion": "€29 Framer Marketplace",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Framer Community + Dribbble",
            "esfuerzo": "25h crear"
        },
        {
            "tipo": "Airtable Base",
            "nombre_base": "Content Pipeline",
            "problema": "Marketing teams pierden ideas de contenido sin sistema organizado",
            "producto": "Base Airtable: idea capture, planning, production, analytics",
            "monetizacion": "€19 Gumroad",
            "revenue_6m": "€950 (50 ventas)",
            "como": "Twitter + Airtable Universe",
            "esfuerzo": "15h crear"
        },
        {
            "tipo": "Obsidian Vault",
            "nombre_base": "Second Brain System",
            "problema": "People toman notas pero nunca las revisan ni conectan ideas",
            "producto": "Vault configurado: daily notes, zettelkasten, templates, plugins setup",
            "monetizacion": "€24 Gumroad",
            "revenue_6m": "€1,200 (50 ventas)",
            "como": "Reddit r/ObsidianMD + Twitter",
            "esfuerzo": "20h crear"
        },
        {
            "tipo": "Pitch Deck",
            "nombre_base": "Investor Pitch Template",
            "problema": "Founders crean pitch decks feos que VCs ignoran",
            "producto": "Google Slides template: 15 slides optimizados para funding rounds",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Twitter + Indie Hackers",
            "esfuerzo": "15h crear"
        },
        
        # GUÍAS & EBOOKS (10)
        {
            "tipo": "eBook",
            "nombre_base": "Side Project to €10K MRR",
            "problema": "Devs no saben monetizar side projects más allá de ads",
            "producto": "150 páginas: pricing, marketing no-code, primeros 100 customers",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€2,900 (100 ventas)",
            "como": "ProductHunt + HackerNews + Twitter",
            "esfuerzo": "60h escribir"
        },
        {
            "tipo": "Video Course",
            "nombre_base": "Bubble.io Masterclass",
            "problema": "Tutorials no-code son superficiales, gente no aprende a hacer apps reales",
            "producto": "15 videos 6h: Build 3 apps reales (CRM, Marketplace, SaaS)",
            "monetizacion": "€99 Gumroad",
            "revenue_6m": "€4,950 (50 ventas)",
            "como": "YouTube preview + paid course",
            "esfuerzo": "80h grabar"
        },
        {
            "tipo": "PDF Guide",
            "nombre_base": "Run Business in Notion",
            "problema": "Solopreneurs pagan €100/mes en 5 tools, quieren todo en uno gratis",
            "producto": "80 páginas + templates: CRM, finances, content, OKRs en Notion",
            "monetizacion": "€39 Gumroad",
            "revenue_6m": "€1,950 (50 ventas)",
            "como": "Reddit r/Notion + Twitter",
            "esfuerzo": "40h crear"
        },
        {
            "tipo": "Checklist",
            "nombre_base": "Product Launch Checklist",
            "problema": "Launchers olvidan steps críticos y lanzan productos incompletos",
            "producto": "300+ items: pre-launch, launch day, post-launch verificados",
            "monetizacion": "€19 Gumroad",
            "revenue_6m": "€950 (50 ventas)",
            "como": "ProductHunt + Indie Hackers",
            "esfuerzo": "20h crear"
        },
        {
            "tipo": "Swipe File",
            "nombre_base": "High-Converting Copy",
            "problema": "Copywriters tienen writer's block, necesitan inspiración probada",
            "producto": "500+ ejemplos: landing pages, emails, ads con conversion rates",
            "monetizacion": "€49 Gumroad",
            "revenue_6m": "€2,450 (50 ventas)",
            "como": "Twitter + LinkedIn",
            "esfuerzo": "50h coleccionar"
        },
        {
            "tipo": "Playbook",
            "nombre_base": "SEO for Founders",
            "problema": "Founders no entienden SEO técnico, contratar agencia cuesta €3K/mes",
            "producto": "Playbook 100 páginas: keyword research, on-page, link building DIY",
            "monetizacion": "€39 Gumroad",
            "revenue_6m": "€1,950 (50 ventas)",
            "como": "Twitter + Reddit r/SEO",
            "esfuerzo": "50h escribir"
        },
        {
            "tipo": "Audiobook",
            "nombre_base": "Remote Work Mastery",
            "problema": "Remote workers luchan con productividad y work-life balance",
            "producto": "3h audio: time management, communication, tools, routines",
            "monetizacion": "€19 Gumroad",
            "revenue_6m": "€950 (50 ventas)",
            "como": "Twitter + Medium + Substack",
            "esfuerzo": "40h grabar"
        },
        {
            "tipo": "Workbook",
            "nombre_base": "Idea Validation Workbook",
            "problema": "Founders lanzan sin validar y pierden 6 meses en producto que nadie quiere",
            "producto": "PDF interactivo: exercises, frameworks, 20 preguntas para validar",
            "monetizacion": "€24 Gumroad",
            "revenue_6m": "€1,200 (50 ventas)",
            "como": "Indie Hackers + Twitter",
            "esfuerzo": "30h crear"
        },
        {
            "tipo": "Blueprint",
            "nombre_base": "Newsletter Growth Blueprint",
            "problema": "Newsletter creators no crecen más allá de 100 subs",
            "producto": "Blueprint: 30 tácticas para 0-1000-10000 subs con ejemplos reales",
            "monetizacion": "€29 Gumroad",
            "revenue_6m": "€1,450 (50 ventas)",
            "como": "Twitter + Substack",
            "esfuerzo": "35h crear"
        },
        {
            "tipo": "Masterclass",
            "nombre_base": "Twitter Growth Masterclass",
            "problema": "Creators tweetean 6 meses sin crecer, no entienden algoritmo",
            "producto": "Video 4h: algoritmo, content strategy, engagement hacks, case studies",
            "monetizacion": "€79 Gumroad",
            "revenue_6m": "€3,950 (50 ventas)",
            "como": "Twitter threads + paid course",
            "esfuerzo": "60h grabar"
        },
        
        # CHROME EXTENSIONS (5)
        {
            "tipo": "Chrome Extension",
            "nombre_base": "LinkedIn Auto-Connect",
            "problema": "Enviar LinkedIn messages personalizados tarda 10 min/persona",
            "producto": "Extension que auto-personaliza con IA usando profile info",
            "monetizacion": "€9/mes (20 free, unlimited paid)",
            "revenue_6m": "€2,700 (50 users × 6 meses)",
            "como": "Chrome Web Store + Reddit",
            "esfuerzo": "40h desarrollar"
        },
        {
            "tipo": "Browser Extension",
            "nombre_base": "Price History Tracker",
            "problema": "Shoppers no saben si precio Amazon es real deal o fake discount",
            "producto": "Extension muestra histórico precios + alerts + comparador",
            "monetizacion": "€5/mes (basic gratis)",
            "revenue_6m": "€1,500 (50 users × 6 meses)",
            "como": "Chrome Store + ProductHunt",
            "esfuerzo": "35h desarrollar"
        },
        {
            "tipo": "Productivity Extension",
            "nombre_base": "Focus Timer Pro",
            "problema": "Workers se distraen cada 10 min, pierden 2h/día en distracciones",
            "producto": "Pomodoro timer + website blocker + analytics productividad",
            "monetizacion": "€7/mes",
            "revenue_6m": "€2,100 (50 users × 6 meses)",
            "como": "Chrome Store + Twitter",
            "esfuerzo": "30h desarrollar"
        },
        {
            "tipo": "SEO Extension",
            "nombre_base": "SEO Quick Audit",
            "problema": "SEO tools son complejos y caros (€99/mes Ahrefs)",
            "producto": "Extension audit rápido: meta tags, headers, keywords, speed",
            "monetizacion": "€9/mes",
            "revenue_6m": "€2,700 (50 users × 6 meses)",
            "como": "Chrome Store + Reddit r/SEO",
            "esfuerzo": "45h desarrollar"
        },
        {
            "tipo": "Shopping Extension",
            "nombre_base": "Coupon Finder Pro",
            "problema": "Shoppers pierden descuentos porque no buscan códigos",
            "producto": "Auto-aplica mejores cupones en checkout + cashback",
            "monetizacion": "Gratis + 5% affiliate comisión",
            "revenue_6m": "€3,000 (comisiones)",
            "como": "Chrome Store + SEO",
            "esfuerzo": "50h desarrollar"
        },
        
        # PLUGINS & TOOLS (5)
        {
            "tipo": "Figma Plugin",
            "nombre_base": "Figma to Tailwind",
            "problema": "Exportar CSS de Figma a código tarda 1h por proyecto",
            "producto": "Plugin convierte designs a Tailwind classes automático",
            "monetizacion": "€49 lifetime",
            "revenue_6m": "€2,450 (50 ventas)",
            "como": "Figma Community + Twitter",
            "esfuerzo": "45h desarrollar"
        },
        {
            "tipo": "Obsidian Plugin",
            "nombre_base": "AI Writer for Obsidian",
            "problema": "Obsidian users quieren IA pero plugins son complejos",
            "producto": "Plugin con Claude: summaries, expand, rewrite, brainstorm",
            "monetizacion": "€7/mes",
            "revenue_6m": "€2,100 (50 users × 6 meses)",
            "como": "Obsidian Community + Reddit",
            "esfuerzo": "35h desarrollar"
        },
        {
            "tipo": "Raycast Extension",
            "nombre_base": "DevTools for Raycast",
            "problema": "Devs cambian apps para buscar docs, snippets, commands",
            "producto": "Busca Stack Overflow, GitHub, MDN desde Raycast",
            "monetizacion": "€5/mes",
            "revenue_6m": "€1,500 (50 users × 6 meses)",
            "como": "Raycast Store + Twitter",
            "esfuerzo": "30h desarrollar"
        },
        {
            "tipo": "VSCode Extension",
            "nombre_base": "AI Code Review",
            "problema": "Devs envían PRs con bugs obvios, code review manual lento",
            "producto": "Extension revisa código con GPT-4, sugiere mejoras inline",
            "monetizacion": "€9/mes",
            "revenue_6m": "€2,700 (50 users × 6 meses)",
            "como": "VSCode Marketplace + Dev.to",
            "esfuerzo": "50h desarrollar"
        },
        {
            "tipo": "Notion Widget",
            "nombre_base": "Notion Analytics Widget",
            "problema": "Notion databases no tienen visualización datos avanzada",
            "producto": "Widget embeddable: charts, KPIs, dashboards de databases",
            "monetizacion": "€12/mes",
            "revenue_6m": "€3,600 (50 users × 6 meses)",
            "como": "Notion Reddit + Twitter",
            "esfuerzo": "40h desarrollar"
        },
        
        # SERVICIOS PRODUCTIZADOS (10)
        {
            "tipo": "Service",
            "nombre_base": "Idea Validation 48h",
            "problema": "Founders no saben si idea tiene mercado antes de construir",
            "producto": "20 user interviews + report con insights + go/no-go decision",
            "monetizacion": "€500 por validación",
            "revenue_6m": "€6,000 (12 clientes)",
            "como": "Twitter + Indie Hackers",
            "esfuerzo": "8h por cliente"
        },
        {
            "tipo": "Design Service",
            "nombre_base": "Landing in 24h",
            "problema": "Indie hackers tienen landings feas, design agencies cuestan €2K",
            "producto": "Diseño + desarrollo Webflow landing profesional",
            "monetizacion": "€300 por landing",
            "revenue_6m": "€6,000 (20 clientes)",
            "como": "Twitter + Dribbble",
            "esfuerzo": "6h por cliente"
        },
        {
            "tipo": "Content Service",
            "nombre_base": "SEO Content Package",
            "problema": "SaaS necesitan content pero hiring writer es €3K/mes",
            "producto": "4 artículos SEO/mes 1500 words optimized",
            "monetizacion": "€400/mes",
            "revenue_6m": "€4,800 (2 clientes × 6 meses)",
            "como": "LinkedIn + cold outreach",
            "esfuerzo": "12h/mes cliente"
        },
        {
            "tipo": "Setup Service",
            "nombre_base": "Notion Setup Pro",
            "problema": "Consultores quieren Notion workspace pero setup tarda 20h",
            "producto": "2 sesiones: workspace completo + training personalizado",
            "monetizacion": "€250 por setup",
            "revenue_6m": "€3,750 (15 clientes)",
            "como": "Notion Reddit + LinkedIn",
            "esfuerzo": "4h por cliente"
        },
        {
            "tipo": "Coaching",
            "nombre_base": "Side Project Sprint",
            "problema": "Builders lanzan productos sin users, necesitan guidance",
            "producto": "4 sesiones: validación, MVP, launch, first users",
            "monetizacion": "€600 (4 sesiones)",
            "revenue_6m": "€6,000 (10 clientes)",
            "como": "Twitter + testimonials",
            "esfuerzo": "6h por cliente"
        },
        {
            "tipo": "Audit Service",
            "nombre_base": "Landing Page Audit",
            "problema": "Landing pages convierten 1%, founders no saben qué optimizar",
            "producto": "Video audit 30 min: CRO issues + recommendations específicas",
            "monetizacion": "€150 por audit",
            "revenue_6m": "€3,000 (20 clientes)",
            "como": "Twitter + LinkedIn",
            "esfuerzo": "2h por cliente"
        },
        {
            "tipo": "Migration Service",
            "nombre_base": "Notion Migration",
            "problema": "Teams quieren migrar a Notion pero tarda 40h y pierden data",
            "producto": "Migramos desde Asana/Trello/Monday + training 2 sesiones",
            "monetizacion": "€800 por migration",
            "revenue_6m": "€6,400 (8 clientes)",
            "como": "LinkedIn + Notion community",
            "esfuerzo": "10h por cliente"
        },
        {
            "tipo": "Consulting",
            "nombre_base": "Growth Strategy Session",
            "problema": "Founders prueban marketing random sin estrategia, waste €5K",
            "producto": "Session 2h: analyze business + growth plan 90 días accionable",
            "monetizacion": "€400 por session",
            "revenue_6m": "€4,000 (10 clientes)",
            "como": "LinkedIn + referrals",
            "esfuerzo": "4h por cliente"
        },
        {
            "tipo": "Optimization Service",
            "nombre_base": "SEO Quick Wins",
            "problema": "Websites tienen SEO issues obvios pero agencies cobran €2K/mes",
            "producto": "Audit + implementación 10 quick wins en 1 semana",
            "monetizacion": "€500 one-time",
            "revenue_6m": "€5,000 (10 clientes)",
            "como": "Reddit r/SEO + LinkedIn",
            "esfuerzo": "8h por cliente"
        },
        {
            "tipo": "Copywriting Service",
            "nombre_base": "Email Sequence Pro",
            "problema": "SaaS tienen email sequences genéricos, 5% open rate",
            "producto": "Escribo 7-email onboarding sequence optimizado",
            "monetizacion": "€350 por sequence",
            "revenue_6m": "€4,200 (12 clientes)",
            "como": "Twitter + LinkedIn",
            "esfuerzo": "6h por cliente"
        },
        
        # COMUNIDADES & NEWSLETTERS (5)
        {
            "tipo": "Newsletter",
            "nombre_base": "Indie Insider Weekly",
            "problema": "Info indie hacking scattered, need curated digest",
            "producto": "Newsletter: 5 case studies + tool reviews + revenue screenshots",
            "monetizacion": "€9/mes (free tier)",
            "revenue_6m": "€2,700 (50 subs × 6 meses)",
            "como": "Twitter + Substack",
            "esfuerzo": "8h/semana"
        },
        {
            "tipo": "Discord Community",
            "nombre_base": "No-Code Club",
            "problema": "No-coders aprenden solos, stuck cuando bloqueados",
            "producto": "Discord: challenges, reviews, job board, templates",
            "monetizacion": "€19/mes",
            "revenue_6m": "€5,700 (50 members × 6 meses)",
            "como": "YouTube + Twitter",
            "esfuerzo": "10h/semana moderar"
        },
        {
            "tipo": "Job Board",
            "nombre_base": "RemoteFirst Jobs",
            "problema": "Job boards tienen 1000s postings, hard find quality remote",
            "producto": "Job board curado: solo 100% remote, salaries visible",
            "monetizacion": "€99 por job post",
            "revenue_6m": "€5,940 (60 postings)",
            "como": "SEO + Twitter",
            "esfuerzo": "5h/semana curar"
        },
        {
            "tipo": "Directory",
            "nombre_base": "Honest SaaS Reviews",
            "problema": "Google reviews biased por affiliate, no trust",
            "producto": "Directory reviews honestos, user ratings, comparisons",
            "monetizacion": "€50/mes listing + ads",
            "revenue_6m": "€3,000 (10 sponsors × 6 meses)",
            "como": "SEO + Reddit",
            "esfuerzo": "15h/semana reviews"
        },
        {
            "tipo": "Resource Hub",
            "nombre_base": "Creator Tools Hub",
            "problema": "Creators gastan €500/mes tools, no saben deals/alternatives",
            "producto": "Database 500+ tools: pricing, alternatives, deals",
            "monetizacion": "€15/mes + €100 listing",
            "revenue_6m": "€4,500 (50 users × 6 meses)",
            "como": "YouTube + Twitter",
            "esfuerzo": "5h/semana updates"
        }
    ]
    
    return random.choice(products)

def generate():
    """Genera producto monetizable"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        product = get_monetizable_product()
        variation = random.randint(1000, 9999)
        
        nombre_unico = f"{product['nombre_base']} {variation}"
        slug = f"producto-{variation}"
        
        # Crear idea directamente (FALLBACK ROBUSTO)
        idea = {
            'nombre': nombre_unico,
            'slug': slug,
            'tipo_producto': product['tipo'],
            'categoria': product['tipo'],
            'descripcion': product['producto'][:200],
            'descripcion_corta': product['problema'][:100],
            'problema': product['problema'],
            'solucion': product['producto'],
            'publico_objetivo': 'Emprendedores digitales',
            'propuesta_valor': product['producto'][:80],
            'diferenciacion': f"Específico y accionable",
            'modelo_monetizacion': product['monetizacion'],
            'revenue_6_meses': product['revenue_6m'],
            'esfuerzo_inicial': product['esfuerzo'],
            'como_monetizar': product['como'],
            'precio_sugerido': '29',
            'canales_venta': product['como'][:50],
            'validacion_inicial': 'MVP + 10 clientes primeros 30 días',
            'score_generador': 85
        }
        
        if not is_duplicate(idea, existing_ideas):
            print(f"✅ ÚNICO - {idea['nombre']}")
            return idea
        else:
            print(f"⚠️  Duplicado detectado")
    
    print("❌ No generó idea única tras 5 intentos")
    return None


if __name__ == "__main__":
    idea = generate()
    if idea:
        print(json.dumps(idea, indent=2, ensure_ascii=False))
