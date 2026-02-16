import os
import json
import time
import random
import hashlib
from datetime import datetime
from groq import Groq
from agents.prompt_optimizer import PromptOptimizer
from agents.knowledge_base import KnowledgeBase

# ============ TREND HUNTER INTEGRATION ============
try:
    from agents import trend_hunter_agent
    TRENDS_ENABLED = True
except ImportError:
    TRENDS_ENABLED = False
    print("âš ï¸ Trend Hunter no disponible - continuando sin detecciÃ³n viral")

# ============ CONFIGURACIÃ“N ============
IDEAS_FILE = 'data/ideas.json'
MAX_ATTEMPTS = 5

# ============ HELPER FUNCTIONS ============
def load_existing_ideas():
    """Carga ideas existentes desde JSON"""
    if os.path.exists(IDEAS_FILE):
        try:
            with open(IDEAS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('ideas', [])
        except:
            return []
    return []

def calculate_fingerprint(nombre, descripcion):
    """Calcula huella Ãºnica de la idea"""
    text = f"{nombre.lower()}{descripcion[:100].lower()}"
    return hashlib.md5(text.encode()).hexdigest()

def is_duplicate(new_idea, existing_ideas):
    """Verifica si la idea es duplicada"""
    new_fp = new_idea['_fingerprint']
    
    for idea in existing_ideas:
        if idea.get('_fingerprint') == new_fp:
            return True
        
        # Verificar similitud en nombre
        if idea['nombre'].lower() == new_idea['nombre'].lower():
            return True
    
    return False

def get_monetizable_product():
    """Retorna producto monetizable aleatorio"""
    
    productos = [
        {
            "tipo": "Notion Template",
            "vertical": "Creadores de contenido",
            "nombre_base": "Content Calendar Pro",
            "problema": "Creadores no saben quÃ© publicar ni cuÃ¡ndo",
            "producto": "Sistema completo de planificaciÃ³n de contenido con calendario editorial, ideas de posts, tracking de mÃ©tricas",
            "precio": "29",
            "monetizacion": "â‚¬29 pago Ãºnico en Gumroad",
            "tool": "Notion",
            "esfuerzo": "8-12h",
            "revenue_6m": "â‚¬2,500",
            "como": "Vender en Gumroad + promociÃ³n Twitter"
        },
        {
            "tipo": "Chrome Extension",
            "vertical": "Marketers",
            "nombre_base": "LinkedIn Auto-Commenter",
            "problema": "Engagement en LinkedIn requiere tiempo manual",
            "producto": "ExtensiÃ³n que genera comentarios contextuales inteligentes con un clic usando IA",
            "precio": "19",
            "monetizacion": "â‚¬19/mes suscripciÃ³n",
            "tool": "Chrome Extension",
            "esfuerzo": "20-30h",
            "revenue_6m": "â‚¬4,800",
            "como": "Chrome Web Store + LinkedIn outreach"
        },
        {
            "tipo": "GuÃ­a PDF",
            "vertical": "Freelancers",
            "nombre_base": "Cold Email Templates Pack",
            "problema": "Freelancers no saben cÃ³mo prospectar clientes por email",
            "producto": "50 plantillas de cold emails probadas con anÃ¡lisis de por quÃ© funcionan",
            "precio": "15",
            "monetizacion": "â‚¬15 pago Ãºnico",
            "tool": "Canva + Gumroad",
            "esfuerzo": "6-10h",
            "revenue_6m": "â‚¬1,800",
            "como": "Vender en Gumroad + Twitter + ProductHunt"
        },
        {
            "tipo": "Figma Plugin",
            "vertical": "DiseÃ±adores",
            "nombre_base": "AI Color Palette Generator",
            "problema": "Crear paletas de colores coherentes toma mucho tiempo",
            "producto": "Plugin que genera paletas profesionales con IA basadas en mood/industria",
            "precio": "12",
            "monetizacion": "â‚¬12 pago Ãºnico",
            "tool": "Figma Plugin",
            "esfuerzo": "15-25h",
            "revenue_6m": "â‚¬3,200",
            "como": "Figma Community + Twitter + Reddit r/FigmaDesign"
        },
        {
            "tipo": "Google Sheets Template",
            "vertical": "Ecommerce",
            "nombre_base": "Profit Calculator Dashboard",
            "problema": "Tiendas online no trackean mÃ¡rgenes reales correctamente",
            "producto": "Dashboard automatizado que calcula costos, mÃ¡rgenes, break-even por producto",
            "precio": "24",
            "monetizacion": "â‚¬24 pago Ãºnico",
            "tool": "Google Sheets",
            "esfuerzo": "10-15h",
            "revenue_6m": "â‚¬2,100",
            "como": "Gumroad + comunidades ecommerce"
        },
        {
            "tipo": "Micro-SaaS",
            "vertical": "Agencias",
            "nombre_base": "Client Report Generator",
            "problema": "Crear reportes mensuales para clientes es tedioso",
            "producto": "Herramienta que conecta Google Analytics/Ads y genera reportes automÃ¡ticos en PDF",
            "precio": "49",
            "monetizacion": "â‚¬49/mes",
            "tool": "No-code (Bubble/Softr)",
            "esfuerzo": "40-60h",
            "revenue_6m": "â‚¬8,400",
            "como": "SEO + cold email a agencias"
        },
        {
            "tipo": "Curso Email",
            "vertical": "Developers",
            "nombre_base": "7-Day API Integration Course",
            "problema": "Developers junior no saben integrar APIs de terceros",
            "producto": "7 emails con ejemplos prÃ¡cticos de integrar Stripe, Mailchimp, etc.",
            "precio": "39",
            "monetizacion": "â‚¬39 pago Ãºnico",
            "tool": "ConvertKit + Notion",
            "esfuerzo": "12-20h",
            "revenue_6m": "â‚¬3,500",
            "como": "Lanzar en ProductHunt + Dev.to + Twitter"
        },
        {
            "tipo": "Plantilla Airtable",
            "vertical": "Recruiters",
            "nombre_base": "ATS Lite - Candidate Tracker",
            "problema": "Recruiters pequeÃ±os no pueden pagar ATS caros",
            "producto": "Base Airtable con pipelines, automatizaciones, email templates integrados",
            "precio": "35",
            "monetizacion": "â‚¬35 pago Ãºnico",
            "tool": "Airtable",
            "esfuerzo": "12-18h",
            "revenue_6m": "â‚¬2,800",
            "como": "Gumroad + LinkedIn + Reddit r/recruiting"
        },
        {
            "tipo": "Webflow Template",
            "vertical": "SaaS Founders",
            "nombre_base": "SaaS Landing Page Template",
            "problema": "Founders tÃ©cnicos no saben diseÃ±ar landing pages que conviertan",
            "producto": "Template Webflow con 5 secciones probadas + animaciones + responsive",
            "precio": "79",
            "monetizacion": "â‚¬79 pago Ãºnico",
            "tool": "Webflow",
            "esfuerzo": "25-35h",
            "revenue_6m": "â‚¬5,900",
            "como": "Webflow Marketplace + Twitter + Indie Hackers"
        },
        {
            "tipo": "Automation Service",
            "vertical": "Small Business",
            "nombre_base": "Zapier Automation Setup Service",
            "problema": "PequeÃ±os negocios quieren automatizar pero no saben usar Zapier",
            "producto": "Servicio: configuro 5 automatizaciones personalizadas en 48h",
            "precio": "299",
            "monetizacion": "â‚¬299 por proyecto",
            "tool": "Zapier + Make",
            "esfuerzo": "4-6h por cliente",
            "revenue_6m": "â‚¬7,200",
            "como": "Cold email + Upwork + LinkedIn"
        }
    ]
    
    return random.choice(productos)

# ============ GENERADOR PRINCIPAL ============
def generate():
    """Genera producto monetizable (prioriza virales si existen)"""
    print("\nðŸ§  Agente Generador iniciado...")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    existing_ideas = load_existing_ideas()
    
    print(f"ðŸ“‹ Ideas existentes en sistema: {len(existing_ideas)}")
    
    # ============ ðŸ”¥ PRIORIDAD 1: OPORTUNIDAD VIRAL ============
    viral_opportunity = None
    
    if TRENDS_ENABLED:
        try:
            print("\nðŸ”¥ Verificando oportunidades virales en cache...")
            
            if trend_hunter_agent.is_cache_valid():
                viral_opportunity = trend_hunter_agent.get_best_viral_opportunity()
                
                if viral_opportunity and viral_opportunity.get('viral_score', 0) >= 70:
                    print(f"\nâš¡ OPORTUNIDAD VIRAL DETECTADA:")
                    print(f"   ðŸ“¦ {viral_opportunity['nombre']}")
                    print(f"   {viral_opportunity.get('urgency', 'ALTA')}")
                    print(f"   â±ï¸  Ventana: {viral_opportunity.get('window', 'N/A')}")
                    print(f"   ðŸŽ¯ Score: {viral_opportunity.get('viral_score', 0)}/100")
                    print(f"   ðŸ“ Fuente: {viral_opportunity.get('source_type', 'unknown')}")
                else:
                    print("   â„¹ï¸  No hay oportunidades virales urgentes (score < 70)")
                    viral_opportunity = None
            else:
                print("   âš ï¸  Cache de trends expirado (se actualizarÃ¡ en prÃ³xima ejecuciÃ³n)")
        
        except Exception as e:
            print(f"   âš ï¸  Error verificando trends: {e}")
            viral_opportunity = None
    else:
        print("   â„¹ï¸  Trend Hunter deshabilitado - usando generaciÃ³n normal")
    
    # ============ INTENTOS DE GENERACIÃ“N ============
    for attempt in range(1, MAX_ATTEMPTS + 1):
        print(f"\nðŸ“ Intento {attempt}/{MAX_ATTEMPTS}...")
        
        # ============ ATTEMPT 1: USAR VIRAL SI EXISTE ============
        if attempt == 1 and viral_opportunity:
            print("   ðŸ”¥ Usando oportunidad viral...")
            
            variation = random.randint(1000, 9999)
            slug = f"viral-{variation}"
            
            idea = {
                'nombre': viral_opportunity['nombre'],
                'slug': slug,
                'tipo_producto': viral_opportunity.get('tipo', 'Digital Product'),
                'categoria': 'Viral Trend',
                'descripcion': viral_opportunity.get('solucion', viral_opportunity.get('descripcion_corta', ''))[:200],
                'descripcion_corta': viral_opportunity.get('problema', '')[:100],
                'problema': viral_opportunity.get('problema', ''),
                'solucion': viral_opportunity.get('solucion', ''),
                'publico_objetivo': 'Early adopters que siguen tendencias',
                'propuesta_valor': viral_opportunity.get('porque_funciona_ahora', 'Timing perfecto para capitalizar tendencia')[:100],
                'diferenciacion': f"Capitaliza trend viral de {viral_opportunity.get('trend_source', 'fuente desconocida')}",
                'tam': '1M+',
                'sam': '100K',
                'som': '10K',
                'competencia': 'Baja (trend reciente)',
                'ventaja_competitiva': 'First mover advantage - timing perfecto',
                'precio_sugerido': viral_opportunity.get('precio_sugerido', 'â‚¬29').replace('â‚¬', '').strip(),
                'modelo_monetizacion': f"{viral_opportunity.get('precio_sugerido', 'â‚¬29')} pago Ãºnico en {viral_opportunity.get('plataforma', 'Gumroad')}",
                'features_core': ', '.join(viral_opportunity.get('pasos_rapidos', ['Feature 1', 'Feature 2', 'Feature 3'])[:3]),
                'roadmap_mvp': f"Crear en {viral_opportunity.get('tiempo_creacion', '48h')} â†’ Lanzar en ProductHunt â†’ Iterar segÃºn feedback",
                'stack_sugerido': viral_opportunity.get('plataforma', 'Gumroad') + ', Twitter, Reddit',
                'integraciones': 'Standalone (sin integraciones complejas)',
                'canales_adquisicion': 'ProductHunt, Twitter, Reddit, comunidades nicho',
                'metricas_clave': 'Ventas primeras 48h, tasa conversiÃ³n, viralidad',
                'riesgos': 'Trend puede morir rÃ¡pido si no se capitaliza a tiempo',
                'validacion_inicial': viral_opportunity.get('revenue_estimado_2_semanas', 'â‚¬500-â‚¬1000'),
                'tiempo_estimado': viral_opportunity.get('tiempo_creacion', '24-48h'),
                'inversion_inicial': 'â‚¬0 (o mÃ­nima para herramientas)',
                'dificultad': 'Baja-Media',
                'revenue_6_meses': viral_opportunity.get('revenue_estimado_2_semanas', 'â‚¬1,000').replace('â‚¬', '').strip(),
                'como_monetizar': f"Lanzar en {viral_opportunity.get('plataforma', 'Gumroad')} + marketing viral en redes sociales + aprovechar trend",
                
                # Metadata viral
                'urgency': viral_opportunity.get('urgency', 'ALTA'),
                'viral_score': viral_opportunity.get('viral_score', 85),
                'window': viral_opportunity.get('window', '48h'),
                'trend_source': viral_opportunity.get('trend_source', 'Unknown'),
                'source_type': viral_opportunity.get('source_type', 'Unknown'),
                'detected_at': viral_opportunity.get('detected_at', datetime.now().isoformat()),
                
                'score_generador': viral_opportunity.get('viral_score', 85),
                '_fingerprint': calculate_fingerprint(viral_opportunity['nombre'], viral_opportunity.get('problema', ''))
            }
            
            # Verificar si es Ãºnica
            if not is_duplicate(idea, existing_ideas):
                print(f"âœ… IDEA VIRAL ÃšNICA - {idea['nombre']}")
                return idea
            else:
                print("   âš ï¸  Idea viral duplicada - usando fallback normal...")
        
        # ============ ATTEMPTS 2-5: PRODUCTOS NORMALES ============
        print("   ðŸŽ² Generando producto normal...")
        
        product = get_monetizable_product()
        timestamp = int(time.time())
        variation = random.randint(1000, 9999)
        
        nombre_unico = f"{product['nombre_base']} {variation}"
        slug = f"producto-{variation}"
        
        prompt = f"""Producto base: {product['producto']}
Vertical: {product['vertical']}
Problema: {product['problema']}

Genera variaciÃ³n ÃšNICA y ESPECÃFICA. No copies el producto base tal cual.

JSON sin markdown:
{{
  "nombre": "[Nombre especÃ­fico diferente]",
  "descripcion": "[DescripciÃ³n Ãºnica 150 chars]",
  "propuesta_valor": "[Por quÃ© es mejor que alternativas]",
  "features_core": "[3-5 features concretas separadas por comas]",
  "diferenciacion": "[QuÃ© lo hace Ãºnico]",
  "tam": "[TamaÃ±o mercado total]",
  "sam": "[Mercado alcanzable]",
  "som": "[Mercado objetivo primer aÃ±o]"
}}"""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Eres experto en productos digitales monetizables. Generas variaciones Ãºnicas y especÃ­ficas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=800
            )
            
            content = response.choices[0].message.content.strip().encode('latin-1').decode('utf-8')
            
            # Limpiar markdown
            if '```json' in content:
                content = content.split('```json').split('```').strip()[1]
            elif '```' in content:
                content = content.split('```').split('```')[0].strip()
            
            enrichment = json.loads(content)
            
            idea = {
                'nombre': enrichment.get('nombre', nombre_unico),
                'slug': slug,
                'tipo_producto': product['tipo'],
                'categoria': product['vertical'],
                'descripcion': enrichment.get('descripcion', product['producto'][:200]),
                'descripcion_corta': product['problema'][:100],
                'problema': product['problema'],
                'solucion': product['producto'],
                'publico_objetivo': product['vertical'],
                'propuesta_valor': enrichment.get('propuesta_valor', 'SoluciÃ³n efectiva y rÃ¡pida'),
                'diferenciacion': enrichment.get('diferenciacion', f"EspecÃ­fico para {product['vertical']}"),
                'tam': enrichment.get('tam', '50M'),
                'sam': enrichment.get('sam', '5M'),
                'som': enrichment.get('som', '500K'),
                'competencia': 'Competencia moderada en el nicho',
                'ventaja_competitiva': 'EspecializaciÃ³n y ejecuciÃ³n rÃ¡pida',
                'precio_sugerido': product['precio'],
                'modelo_monetizacion': product['monetizacion'],
                'features_core': enrichment.get('features_core', 'Feature 1, Feature 2, Feature 3'),
                'roadmap_mvp': 'Semana 1: Setup y diseÃ±o, Semana 2: Desarrollo, Semana 3: Testing y lanzamiento',
                'stack_sugerido': f"{product['tool']}, Gumroad, Twitter",
                'integraciones': f"{product['tool']}, Zapier, webhooks",
                'canales_adquisicion': 'Twitter, ProductHunt, Reddit, comunidades especializadas',
                'metricas_clave': 'MRR, tasa conversiÃ³n, CAC, LTV',
                'riesgos': 'Competencia puede copiar, dependencia de plataforma',
                'validacion_inicial': '10 ventas en primeras 2 semanas',
                'tiempo_estimado': product['esfuerzo'],
                'inversion_inicial': 'â‚¬0-â‚¬50',
                'dificultad': 'Media',
                'revenue_6_meses': product['revenue_6m'],
                'como_monetizar': product['como'],
                'score_generador': 75,
                '_fingerprint': calculate_fingerprint(enrichment.get('nombre', nombre_unico), product['problema'][:100])
            }
            
            # Verificar duplicados
            if not is_duplicate(idea, existing_ideas):
                print(f"âœ… IDEA NORMAL ÃšNICA - {idea['nombre']}")
                return idea
            else:
                print(f"   âš ï¸  Idea duplicada (attempt {attempt})")
        
        except Exception as e:
            print(f"   âš ï¸  Error en generaciÃ³n: {e}")
            continue
    
    # Si llegamos aquÃ­, no se pudo generar idea Ãºnica
    print("\nâŒ No se pudo generar idea Ãºnica despuÃ©s de 5 intentos")
    return None

# ============ MAIN ============
if __name__ == "__main__":
    idea = generate()
    
    if idea:
        print("\n" + "="*80)
        print("âœ… IDEA GENERADA:")
        print("="*80)
        print(json.dumps(idea, indent=2, ensure_ascii=False))
    else:
        print("\nâŒ No se generÃ³ idea")



