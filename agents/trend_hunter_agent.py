import os
import json
import requests
import time
from datetime import datetime, timedelta
from groq import Groq

TRENDS_FILE = 'data/viral-trends.json'
CACHE_HOURS = 6

# ============ FUENTE 1: AnswerThePublic (Apify) ============
def fetch_answerthepublic(keyword, apify_token):
    """Obtiene preguntas reales de AnswerThePublic vía Apify"""
    
    url = "https://api.apify.com/v2/acts/deadlyaccurate~answer-the-public/run-sync-get-dataset-items"
    
    payload = {
        "keywords": [keyword],
        "language": "es",
        "region": "es"
    }
    
    headers = {
        "Authorization": f"Bearer {apify_token}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers, timeout=120)
        
        if response.status_code == 200:
            data = response.json()
            
            if data and len(data) > 0:
                item = data[0]
                
                # Extraer preguntas de todas las categorías
                questions = []
                
                if 'data' in item:
                    for category, content in item['data'].items():
                        if isinstance(content, dict) and 'results' in content:
                            results = content['results']
                            if isinstance(results, dict) and 'data' in results:
                                for q in results['data'][:10]:  # Top 10 por categoría
                                    if isinstance(q, dict) and 'text' in q:
                                        questions.append(q['text'])
                
                return {
                    "keyword": keyword,
                    "questions": questions[:30],  # Top 30 total
                    "search_volume": item.get('data', {}).get('max_search_volume', 'N/A'),
                    "timestamp": datetime.now().isoformat(),
                    "source": "answerthepublic"
                }
        
        print(f"⚠️ AnswerThePublic error: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"⚠️ Error AnswerThePublic: {e}")
        return None

# ============ FUENTE 2: Google Trends (Scraping) ============
def fetch_google_trends_realtime():
    """Simula búsquedas explosivas de Google Trends"""
    
    # En producción: usar pytrends o scraping con proxies rotatorios
    trending_now = [
        {
            "keyword": "IA agentes autónomos",
            "category": "Tecnología",
            "volume": "450K",
            "growth": "+420%",
            "hours_ago": 8,
            "related": ["agentes IA", "automatización no-code", "workflow automation"]
        },
        {
            "keyword": "ingresos pasivos 2026",
            "category": "Negocios",
            "volume": "780K",
            "growth": "+350%",
            "hours_ago": 12,
            "related": ["side hustle", "productos digitales", "negocio online"]
        },
        {
            "keyword": "plantillas Notion productividad",
            "category": "Productividad",
            "volume": "320K",
            "growth": "+280%",
            "hours_ago": 6,
            "related": ["Notion templates", "sistema productividad", "second brain"]
        }
    ]
    
    for trend in trending_now:
        trend['timestamp'] = datetime.now().isoformat()
        trend['source'] = 'google_trends'
    
    return trending_now

# ============ FUENTE 3: Reddit Viral Posts ============
def fetch_reddit_viral(subreddits=['SaaS', 'Entrepreneur', 'passive_income']):
    """Obtiene posts virales de Reddit últimas 24h"""
    
    # En producción: usar SociaVault API o PRAW
    viral_posts = [
        {
            "subreddit": "r/SaaS",
            "title": "Hice €8K en 2 semanas con extensión Chrome",
            "upvotes": 2800,
            "comments": 420,
            "hours_ago": 9,
            "url": "reddit.com/r/SaaS/...",
            "pain_point": "Gente busca ganancias rápidas con bajo esfuerzo",
            "extracted_keyword": "chrome extension"
        },
        {
            "subreddit": "r/Entrepreneur",
            "title": "€12K primer mes vendiendo plantillas Notion",
            "upvotes": 3100,
            "comments": 580,
            "hours_ago": 14,
            "url": "reddit.com/r/Entrepreneur/...",
            "pain_point": "Creadores necesitan organización sin herramientas complejas",
            "extracted_keyword": "notion templates"
        }
    ]
    
    for post in viral_posts:
        post['timestamp'] = datetime.now().isoformat()
        post['source'] = 'reddit'
    
    return viral_posts

# ============ FUENTE 4: ProductHunt Today ============
def fetch_producthunt_today():
    """Productos lanzados HOY en ProductHunt con tracción"""
    
    # En producción: scraping de hunted.space o API no oficial
    launched_today = [
        {
            "name": "QuickPrompts AI Pro",
            "tagline": "2000+ prompts ChatGPT organizados por categoría",
            "upvotes": 520,
            "comments": 95,
            "category": "IA",
            "pricing": "€29 pago único",
            "hours_ago": 5,
            "insight": "Colecciones curadas de prompts se venden muy bien"
        },
        {
            "name": "NotionOS Business",
            "tagline": "Sistema operativo completo para solopreneurs",
            "upvotes": 440,
            "comments": 78,
            "category": "Productividad",
            "pricing": "€49 pago único",
            "hours_ago": 7,
            "insight": "Workspaces todo-en-uno son muy populares"
        }
    ]
    
    for product in launched_today:
        product['timestamp'] = datetime.now().isoformat()
        product['source'] = 'producthunt'
    
    return launched_today

# ============ FUENTE 5: Twitter/X Trends ============
def fetch_twitter_trends(woeid=23424950):  # España
    """Obtiene trending topics de Twitter/X"""
    
    # En producción: usar Twitter API v1.1 con autenticación
    # GET https://api.x.com/1.1/trends/place.json?id=23424950
    
    trends = [
        {
            "name": "#IAGenerativa",
            "tweet_volume": 45800,
            "rank": 3,
            "hours_ago": 2,
            "category": "Tecnología"
        },
        {
            "name": "#ProductividadDigital",
            "tweet_volume": 28500,
            "rank": 7,
            "hours_ago": 4,
            "category": "Negocios"
        }
    ]
    
    for trend in trends:
        trend['timestamp'] = datetime.now().isoformat()
        trend['source'] = 'twitter'
    
    return trends

# ============ SCORING SYSTEM ============
def calculate_viral_score(trend_data):
    """Calcula score viral + urgencia + ventana de oportunidad"""
    
    growth = str(trend_data.get('growth', '0%'))
    volume = str(trend_data.get('volume', trend_data.get('upvotes', trend_data.get('tweet_volume', '0'))))
    hours_ago = trend_data.get('hours_ago', 999)
    
    # Score de crecimiento
    growth_pct = 0
    try:
        growth_pct = int(growth.replace('%', '').replace('+', ''))
    except:
        pass
    
    growth_score = min(40, growth_pct / 10)
    
    # Score de volumen
    volume_str = str(volume).upper()
    if 'M' in volume_str:
        volume_score = 40
    elif 'K' in volume_str:
        k_value = float(volume_str.replace('K', ''))
        volume_score = min(40, k_value / 10)
    else:
        try:
            num_volume = int(volume_str)
            volume_score = min(40, num_volume / 100)
        except:
            volume_score = 10
    
    # Score de frescura
    if hours_ago < 6:
        freshness_score = 20
    elif hours_ago < 12:
        freshness_score = 18
    elif hours_ago < 24:
        freshness_score = 15
    elif hours_ago < 48:
        freshness_score = 10
    else:
        freshness_score = 5
    
    total_score = int(growth_score + volume_score + freshness_score)
    
    # Determinar urgencia y ventana
    if total_score >= 85:
        urgency = "🔴 CRÍTICA"
        window = "24-48h"
        action = "ACTUAR YA"
    elif total_score >= 70:
        urgency = "🟠 ALTA"
        window = "2-4 días"
        action = "Actuar esta semana"
    elif total_score >= 55:
        urgency = "🟡 MEDIA"
        window = "1-2 semanas"
        action = "Planificar"
    else:
        urgency = "🟢 BAJA"
        window = "2-4 semanas"
        action = "Evaluar"
    
    return {
        "viral_score": total_score,
        "urgency": urgency,
        "window": window,
        "action": action,
        "breakdown": {
            "volume": int(volume_score),
            "growth": int(growth_score),
            "freshness": int(freshness_score)
        }
    }

# ============ IDEA GENERATOR ============
def generate_quick_win_ideas(trend, client):
    """Genera productos rápidos (24-48h) para capitalizar tendencia"""
    
    print(f"\n🔥 Generando ideas para: {trend.get('keyword', trend.get('name', trend.get('title', 'trend')))}")
    
    viral_metrics = calculate_viral_score(trend)
    
    source = trend.get('source', 'unknown')
    
    # Construir contexto según fuente
    if source == 'answerthepublic':
        context = f"""TENDENCIA DETECTADA EN ANSWERTHEPUBLIC:
Keyword: {trend['keyword']}
Volumen búsquedas: {trend.get('search_volume', 'N/A')}
Preguntas top que hace la gente:
{chr(10).join(['• ' + q for q in trend.get('questions', [])[:5]])}"""
    
    elif source == 'reddit':
        context = f"""POST VIRAL EN REDDIT:
Subreddit: {trend['subreddit']}
Título: {trend['title']}
Engagement: {trend['upvotes']} upvotes, {trend['comments']} comentarios
Pain Point: {trend['pain_point']}"""
    
    elif source == 'producthunt':
        context = f"""PRODUCTO EXITOSO EN PRODUCTHUNT HOY:
Nombre: {trend['name']}
Tagline: {trend['tagline']}
Tracción: {trend['upvotes']} upvotes en {trend['hours_ago']}h
Insight: {trend['insight']}"""
    
    elif source == 'google_trends':
        context = f"""BÚSQUEDA EXPLOSIVA EN GOOGLE TRENDS:
Keyword: {trend['keyword']}
Volumen: {trend['volume']}
Crecimiento: {trend['growth']} en últimas {trend['hours_ago']}h
Related: {', '.join(trend.get('related', []))}"""
    
    elif source == 'twitter':
        context = f"""TRENDING TOPIC EN TWITTER/X:
Hashtag: {trend['name']}
Volumen: {trend.get('tweet_volume', 'N/A')} tweets
Rank: #{trend.get('rank', 'N/A')}
Horas trending: {trend['hours_ago']}h"""
    
    else:
        context = f"Tendencia: {str(trend)[:200]}"
    
    prompt = f"""{context}

MÉTRICAS VIRALES:
• Score: {viral_metrics['viral_score']}/100
• Urgencia: {viral_metrics['urgency']}
• Ventana de oportunidad: {viral_metrics['window']}
• Acción: {viral_metrics['action']}

Genera 3 productos digitales que se pueden crear y lanzar en MÁXIMO 48 HORAS:

CRITERIOS OBLIGATORIOS:
✓ Tiempo de creación: <48h realista
✓ No requiere programación compleja
✓ Monetizable de inmediato (Gumroad, Chrome Web Store, etc.)
✓ Aprovecha el timing perfecto (tendencia está creciendo AHORA)
✓ Precio entre €9-€49

Responde SOLO con JSON (sin markdown):
[
  {{
    "nombre": "Nombre específico y atractivo",
    "tipo": "Template/Guía/Extension/Tool/Service",
    "descripcion_corta": "1 frase - qué es",
    "problema": "Pain point exacto que resuelve",
    "solucion": "Cómo lo resuelve",
    "tiempo_creacion": "X horas",
    "precio_sugerido": "€X",
    "plataforma": "Gumroad/ChromeStore/Figma/Notion/etc",
    "revenue_estimado_2_semanas": "€X conservador",
    "pasos_rapidos": ["Paso 1", "Paso 2", "Paso 3"],
    "porque_funciona_ahora": "Por qué este timing es perfecto (2 frases)"
  }}
]"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres experto en trend-jacking: crear productos rápidos que capitalizan tendencias virales. Solo sugieres productos REALISTAS que alguien puede crear en 48h máximo."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=2000
        )
        
        content = response.choices[0].message.content.strip()
        
        # Limpiar markdown si existe
        if '```json' in content:
            content = content.split('```json').split('```').strip()[1]
        elif '```' in content:
            content = content.split('```').split('```')[0].strip()
        
        ideas = json.loads(content)
        
        # Enriquecer con metadata
        for idea in ideas:
            idea['trend_source'] = trend.get('keyword', trend.get('name', trend.get('title', 'Unknown')))
            idea['source_type'] = source
            idea['viral_score'] = viral_metrics['viral_score']
            idea['urgency'] = viral_metrics['urgency']
            idea['window'] = viral_metrics['window']
            idea['detected_at'] = datetime.now().isoformat()
        
        return ideas
    
    except Exception as e:
        print(f"⚠️ Error generando ideas: {e}")
        return []

# ============ MAIN HUNTER ============
def hunt_viral_opportunities():
    """CAZA COMPLETA de oportunidades virales multi-fuente"""
    
    print("\n" + "="*80)
    print("🔥 TREND HUNTER AGENT - Cazando Tendencias Virales en Tiempo Real")
    print("="*80)
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    all_opportunities = []
    
    # 1. AnswerThePublic
    print("\n🔍 [1/5] AnswerThePublic - Preguntas reales...")
    apify_token = os.environ.get("APIFY_TOKEN")
    
    if apify_token:
        keywords = ["agentes ia", "plantillas notion", "ingresos pasivos"]
        
        for keyword in keywords:
            print(f"   Analizando: {keyword}")
            atp_data = fetch_answerthepublic(keyword, apify_token)
            
            if atp_data:
                ideas = generate_quick_win_ideas(atp_data, client)
                all_opportunities.extend(ideas)
                time.sleep(2)
    else:
        print("   ⚠️ APIFY_TOKEN no configurado - saltando")
    
    # 2. Google Trends
    print("\n📊 [2/5] Google Trends - Búsquedas explosivas...")
    google_trends = fetch_google_trends_realtime()
    
    for trend in google_trends[:2]:
        print(f"   {trend['keyword']} ({trend['growth']})")
        ideas = generate_quick_win_ideas(trend, client)
        all_opportunities.extend(ideas)
        time.sleep(2)
    
    # 3. Reddit Viral
    print("\n🔥 [3/5] Reddit - Posts virales 24h...")
    reddit_posts = fetch_reddit_viral()
    
    for post in reddit_posts[:2]:
        print(f"   {post['subreddit']}: {post['title'][:50]}...")
        ideas = generate_quick_win_ideas(post, client)
        all_opportunities.extend(ideas)
        time.sleep(2)
    
    # 4. ProductHunt
    print("\n🚀 [4/5] ProductHunt - Lanzados hoy...")
    ph_today = fetch_producthunt_today()
    
    for product in ph_today:
        print(f"   {product['name']}: {product['upvotes']} upvotes")
        ideas = generate_quick_win_ideas(product, client)
        all_opportunities.extend(ideas)
        time.sleep(2)
    
    # 5. Twitter Trends
    print("\n🐦 [5/5] Twitter/X - Trending topics...")
    twitter_trends = fetch_twitter_trends()
    
    for trend in twitter_trends[:1]:
        print(f"   {trend['name']}: {trend.get('tweet_volume', 'N/A')} tweets")
        ideas = generate_quick_win_ideas(trend, client)
        all_opportunities.extend(ideas)
        time.sleep(2)
    
    # Ordenar por viral_score
    all_opportunities.sort(key=lambda x: x.get('viral_score', 0), reverse=True)
    
    # Guardar resultados
    trends_output = {
        "last_update": datetime.now().isoformat(),
        "next_update": (datetime.now() + timedelta(hours=CACHE_HOURS)).isoformat(),
        "total_opportunities": len(all_opportunities),
        "sources_used": {
            "answerthepublic": bool(apify_token),
            "google_trends": True,
            "reddit": True,
            "producthunt": True,
            "twitter": True
        },
        "top_10_opportunities": all_opportunities[:10],
        "all_opportunities": all_opportunities
    }
    
    os.makedirs('data', exist_ok=True)
    with open(TRENDS_FILE, 'w', encoding='utf-8') as f:
        json.dump(trends_output, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ {len(all_opportunities)} oportunidades detectadas")
    print(f"📁 Guardado en: {TRENDS_FILE}")
    
    # Mostrar Top 3
    print("\n" + "="*80)
    print("🏆 TOP 3 OPORTUNIDADES MÁS URGENTES:")
    print("="*80)
    
    for idx, opp in enumerate(all_opportunities[:3], 1):
        print(f"\n#{idx} {opp['nombre']}")
        print(f"   📊 Score: {opp['viral_score']}/100")
        print(f"   {opp['urgency']} - Ventana: {opp['window']}")
        print(f"   ⏱️ Crear en: {opp['tiempo_creacion']}")
        print(f"   💰 Revenue estimado: {opp['revenue_estimado_2_semanas']}")
        print(f"   🎯 {opp['porque_funciona_ahora'][:80]}...")
    
    return trends_output

def is_cache_valid():
    """Verifica si cache es válido (<6h)"""
    
    if not os.path.exists(TRENDS_FILE):
        return False
    
    try:
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            last_update = datetime.fromisoformat(data['last_update'])
            return datetime.now() - last_update < timedelta(hours=CACHE_HOURS)
    except:
        return False

def get_best_viral_opportunity():
    """Obtiene la MEJOR oportunidad viral (score más alto)"""
    
    if not is_cache_valid():
        print("⚠️ Cache expirado - ejecutando hunt...")
        hunt_viral_opportunities()
    
    try:
        with open(TRENDS_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            opportunities = data.get('all_opportunities', [])
            return opportunities[0] if opportunities else None
    except:
        return None

if __name__ == "__main__":
    hunt_viral_opportunities()
