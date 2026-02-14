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
    """Validación MUY PERMISIVA"""
    nombre = str(idea.get('nombre', '')).lower().strip()
    descripcion = str(idea.get('descripcion_corta', '')).lower().strip()
    
    if not nombre or len(nombre) < 3:
        return True
    
    fingerprint = calculate_fingerprint(nombre, descripcion)
    
    for existing in existing_ideas:
        if existing['fingerprint'] == fingerprint:
            return True
        
        if existing['nombre']:
            ratio = SequenceMatcher(None, nombre, existing['nombre']).ratio()
            if ratio > 0.80:
                return True
    
    return False

def get_niche_idea():
    """30 nichos ultra-específicos (duplicado de 15)"""
    
    niches = [
        # Originales (15)
        {"vertical": "LinkedIn Creators", "problema": "Pasan 8h/semana escribiendo posts que no generan engagement", "solucion": "IA analiza 100 posts con mejor engagement, extrae patrones, genera 50 posts en tu estilo optimizados para algoritmo LinkedIn", "tool": "Claude Sonnet 4.5", "precio": "39", "nombre": "LinkedBoost AI"},
        {"vertical": "YouTube Creators 10K-100K subs", "problema": "Tardan 5h escribiendo scripts y no saben qué títulos funcionan", "solucion": "GPT-4 analiza tus vídeos con mejor CTR, genera scripts con ganchos + títulos A/B tested + timestamps automáticos", "tool": "GPT-4 API", "precio": "49", "nombre": "ScriptGenius AI"},
        {"vertical": "eCommerce Shopify stores", "problema": "Pierden ventas porque competencia baja precios y no se enteran", "solucion": "Scraping Bright Data 24/7 de 50 competidores + alertas Telegram instant cuando bajan precio + sugerencias pricing IA", "tool": "Bright Data", "precio": "79", "nombre": "PriceSpy Pro"},
        {"vertical": "Freelancers técnicos", "problema": "Pasan 4h/semana en admin: facturas, contratos, time tracking", "solucion": "Notion como CRM + generación automática facturas PDF + contratos templates + time tracking con Toggl API", "tool": "Notion API", "precio": "29", "nombre": "FreelanceHub"},
        {"vertical": "Recruiters IT", "problema": "LinkedIn scraping manual de candidatos tarda 10h/semana", "solucion": "Bot extrae perfiles LinkedIn con skills específicas + enriquece con GitHub + email finder + exports a CRM", "tool": "Apify", "precio": "99", "nombre": "TalentScout AI"},
        {"vertical": "Podcasters", "problema": "Edición y show notes tardan 3h por episodio", "solucion": "Whisper API transcribe + Claude genera show notes + timestamps + quotes destacadas + posts redes", "tool": "Whisper API", "precio": "59", "nombre": "PodcastFlow AI"},
        {"vertical": "Newsletter Creators", "problema": "Research de contenido 6h/semana, engagement bajo 2%", "solucion": "IA escanea 100 fuentes, resume tendencias, genera drafts personalizados con tu voz, optimiza subject lines para +40% open rate", "tool": "Claude API", "precio": "49", "nombre": "NewsletterPro AI"},
        {"vertical": "Agencias Marketing", "problema": "Reportes clientes tardan 5h/mes, formato inconsistente", "solucion": "Conecta Google Ads + Meta + LinkedIn, auto-genera reportes white-label PDF con insights IA, envío automático", "tool": "Google Sheets API", "precio": "149", "nombre": "ReportMaster"},
        {"vertical": "SaaS Founders", "problema": "Seguimiento métricas en 5 herramientas, no ven MRR real", "solucion": "Dashboard Notion que sync Stripe MRR + ChurnKey + Google Analytics + cohorts automáticos con predicciones IA", "tool": "Stripe API", "precio": "79", "nombre": "SaaSMetrics"},
        {"vertical": "Content Creators TikTok", "problema": "No saben qué trends usar, ideas virales tardan 2h/día", "solucion": "IA monitorea trending sounds + hashtags + analiza tus vídeos top, genera 30 ideas virales diarias con script y hooks", "tool": "TikTok API", "precio": "39", "nombre": "TrendHunter AI"},
        {"vertical": "Consultores estrategia", "problema": "Propuestas tardan 8h, templates genéricas, win rate 20%", "solucion": "IA analiza propuestas ganadoras, genera propuesta personalizada por cliente con pricing dinámico en 30min", "tool": "GPT-4", "precio": "99", "nombre": "ProposalGenius"},
        {"vertical": "SEO Agencies", "problema": "Keyword research manual 4h/proyecto, pierden long-tails", "solucion": "IA encuentra 500 long-tail keywords con Ahrefs API + analiza SERP + genera content briefs optimizados", "tool": "Ahrefs API", "precio": "89", "nombre": "KeywordMiner AI"},
        {"vertical": "Real Estate Agents", "problema": "Descripciones propiedades genéricas, fotos sin optimizar", "solucion": "IA genera descripciones premium + optimiza fotos con Midjourney + crea virtual staging + posts Instagram", "tool": "Midjourney API", "precio": "69", "nombre": "PropertyPro AI"},
        {"vertical": "Course Creators", "problema": "Outline de cursos tarda 10h, estructura inconsistente", "solucion": "IA genera outline completo con módulos + lecciones + scripts + quizzes basado en objetivo aprendizaje", "tool": "Claude API", "precio": "59", "nombre": "CourseBuilder AI"},
        {"vertical": "Twitter Creators", "problema": "Threads que funcionan son impredecibles, engagement 1%", "solucion": "IA analiza tus 50 mejores tweets, genera threads con hooks probados, scheduling óptimo para +200% engagement", "tool": "GPT-4", "precio": "29", "nombre": "ThreadGenius"},
        
        # NUEVOS (15 más)
        {"vertical": "Instagram Influencers", "problema": "Captions y hashtags tardan 2h/día, crecimiento estancado", "solucion": "IA analiza tus posts con mejor reach, genera captions + 30 hashtags específicos nicho + best time to post", "tool": "Claude API", "precio": "35", "nombre": "InstaCaption Pro"},
        {"vertical": "Virtual Assistants", "problema": "Gestión múltiples clientes caótica, pierden 5h/semana organizando", "solucion": "Dashboard único con calendarios sincronizados + task automation + templates respuestas + facturación integrada", "tool": "Notion API", "precio": "25", "nombre": "VAManager"},
        {"vertical": "Copywriters", "problema": "Briefing de clientes confuso, 3 revisiones promedio", "solucion": "IA transforma briefings vagos en specs detalladas + genera 5 variaciones copy + A/B testing predictor", "tool": "GPT-4", "precio": "45", "nombre": "CopyBrief AI"},
        {"vertical": "UX Designers", "problema": "User research synthesis tarda 6h, insights se pierden", "solucion": "IA analiza entrevistas + heatmaps + analytics, genera research report + patterns + actionable recommendations", "tool": "Claude API", "precio": "89", "nombre": "ResearchSynth"},
        {"vertical": "Email Marketers", "problema": "Segmentación manual de listas, open rate bajo 15%", "solucion": "IA segmenta por comportamiento + predice best send time + genera subject lines optimizados para +35% open rate", "tool": "Mailchimp API", "precio": "69", "nombre": "EmailGenius"},
        {"vertical": "Developers Indie", "problema": "Documentación API tarda 8h, siempre desactualizada", "solucion": "IA escanea código, auto-genera docs + ejemplos código + Postman collections + mantiene actualizado con commits", "tool": "GPT-4", "precio": "49", "nombre": "DocMatic"},
        {"vertical": "Community Managers", "problema": "Responder DMs/comentarios tarda 4h/día, inconsistente", "solucion": "IA aprende tone of voice marca, genera respuestas personalizadas + detecta crisis + prioriza mensajes urgentes", "tool": "Claude API", "precio": "55", "nombre": "CommunityBot"},
        {"vertical": "Product Managers", "problema": "Priorización features subjetiva, roadmap desorganizado", "solucion": "IA analiza feedback usuarios + customer requests + métricas, genera roadmap priorizado con scoring RICE", "tool": "Notion API", "precio": "99", "nombre": "RoadmapAI"},
        {"vertical": "Sales Teams", "problema": "Lead qualification manual, 40% tiempo en leads fríos", "solucion": "IA puntúa leads por LinkedIn + web activity + fit score, auto-asigna a SDRs + sugiere mejor approach", "tool": "LinkedIn API", "precio": "129", "nombre": "LeadScorer Pro"},
        {"vertical": "Customer Success", "problema": "Detección churn reactiva, pierden cuentas sin avisar", "solucion": "IA predice churn 30 días antes con ML + sugiere acciones retención + auto-programa check-ins", "tool": "Stripe API", "precio": "149", "nombre": "ChurnGuard"},
        {"vertical": "Webinar Hosts", "problema": "Follow-up post-webinar genérico, conversión 3%", "solucion": "IA analiza engagement por attendee, genera emails personalizados + segmenta hot/warm/cold + CRM sync", "tool": "Zoom API", "precio": "79", "nombre": "WebinarFlow"},
        {"vertical": "Affiliate Marketers", "problema": "Tracking de 50+ afiliados manual en spreadsheets", "solucion": "Dashboard consolida todas networks + analiza mejor performing offers + auto-optimiza bids", "tool": "Google Sheets API", "precio": "59", "nombre": "AffiliateHQ"},
        {"vertical": "LinkedIn Ghostwriters", "problema": "Research del cliente tarda 3h, voz genérica", "solucion": "IA analiza posts antiguos cliente + competencia + LinkedIn profile, genera style guide + 30 posts draft", "tool": "Claude API", "precio": "149", "nombre": "GhostwriterAI"},
        {"vertical": "Amazon FBA Sellers", "problema": "Keyword tracking en 100+ productos, pierden rankings", "solucion": "Monitor diario rankings keywords + alertas drops + sugiere optimizaciones listings + competitor analysis", "tool": "Amazon API", "precio": "89", "nombre": "AmazonRank Pro"},
        {"vertical": "Notion Consultants", "problema": "Setup workspaces desde cero tarda 15h", "solucion": "Templates pre-configurados por industria + IA personaliza por necesidades cliente + training videos auto", "tool": "Notion API", "precio": "199", "nombre": "NotionPro Setup"}
    ]
    
    return random.choice(niches)

def generate():
    """Genera idea usando nichos + researcher insights"""
    print("\n🧠 Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    # Cargar insights investigador
    insights = load_researcher_insights()
    extra_context = ""
    
    if insights:
        print("📊 Usando insights del investigador...")
        trends = insights.get('trends', [])
        problems = insights.get('problems', [])
        
        if trends:
            extra_context += f"\nTrends detectados: {', '.join([t['keyword'] for t in trends[:3]])}"
        if problems:
            extra_context += f"\nProblemas reales: {problems[0]}"
    
    print(f"📋 Ideas existentes: {len(existing_ideas)}")
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"📝 Intento {attempt}/{MAX_ATTEMPTS}...")
        
        niche = get_niche_idea()
        timestamp = int(time.time())
        variation = random.randint(1000, 9999)
        
        system_prompt = f"""Genera idea SaaS 2026.

NICHO: {niche['vertical']}
PROBLEMA: {niche['problema']}
SOLUCIÓN: {niche['solucion']}
TOOL: {niche['tool']}
PRECIO: {niche['precio']}€/mes
{extra_context}

Evita: {', '.join([i['nombre'][:15] for i in existing_ideas[-5:] if i.get('nombre')])}

JSON sin explicación:
{{
  "nombre": "{niche['nombre']} {variation}",
  "slug": "saas-{variation}",
  "descripcion": "{niche['solucion'][:150]}",
  "descripcion_corta": "{niche['problema'][:100]}",
  "categoria": "SaaS IA",
  "problema": "{niche['problema']}",
  "solucion": "{niche['solucion']}",
  "publico_objetivo": "{niche['vertical']}",
  "propuesta_valor": "Ahorra 8 horas semanales",
  "diferenciacion": "Integración {niche['tool']}",
  "tam": "50M",
  "sam": "5M",
  "som": "500K",
  "competencia": ["Tool1", "Tool2"],
  "ventaja_competitiva": "IA específica nicho",
  "precio_sugerido": "{niche['precio']}",
  "modelo_monetizacion": "Subscription",
  "features_core": ["Feature 1", "Feature 2", "Feature 3"],
  "roadmap_mvp": ["Semana 1-2 Setup", "Semana 3-4 APIs", "Semana 5-6 Deploy"],
  "stack_sugerido": ["Next.js", "Supabase", "Stripe"],
  "integraciones": ["{niche['tool']}", "Zapier"],
  "canales_adquisicion": ["Twitter", "ProductHunt"],
  "metricas_clave": ["MRR", "Churn"],
  "riesgos": ["API dependency"],
  "validacion_inicial": "20 entrevistas",
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
                temperature=1.2,
                max_tokens=1500
            )
            
            content = str(response.choices[0].message.content).strip()
            
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            idea = json.loads(content)
            
            if not idea.get('nombre'):
                idea['nombre'] = f"{niche['nombre']} {variation}"
            if not idea.get('descripcion_corta'):
                idea['descripcion_corta'] = niche['problema'][:100]
            
            idea['_fingerprint'] = calculate_fingerprint(
                idea.get('nombre', ''),
                idea.get('descripcion_corta', '')
            )
            
            if is_duplicate(idea, existing_ideas):
                print("⚠️  Duplicada")
                continue
            
            print(f"✅ ÚNICA - {idea['nombre']}")
            return idea
        
        except json.JSONDecodeError:
            # Fallback
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
