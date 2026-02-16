import os
import json
import time
import random
import hashlib
from datetime import datetime
from groq import Groq
from agents.prompt_optimizer import PromptOptimizer
from agents.knowledge_base import KnowledgeBase
from agents.encoding_helper import fix_llm_encoding

# ============ TREND HUNTER INTEGRATION ============
try:
    from agents import trend_hunter_agent
    TRENDS_ENABLED = True
except ImportError:
    TRENDS_ENABLED = False
    print("âš ï¸ Trend Hunter no disponible - continuando sin detección viral")

# ============ CONFIGURACIí“N ============
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
    """Calcula huella única de la idea"""
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
            "problema": "Creadores no saben qué publicar ni cuándo",
            "producto": "Sistema completo de planificación de contenido con calendario editorial, ideas de posts, tracking de métricas",
            "precio": "29",
            "monetizacion": "€29 pago único en Gumroad",
            "tool": "Notion",
            "esfuerzo": "8-12h",
            "revenue_6m": "€2,500",
            "como": "Vender en Gumroad + promoción Twitter"
        },
        {
            "tipo": "Chrome Extension",
            "vertical": "Marketers",
            "nombre_base": "LinkedIn Auto-Commenter",
            "problema": "Engagement en LinkedIn requiere tiempo manual",
            "producto": "Extensión que genera comentarios contextuales inteligentes con un clic usando IA",
            "precio": "19",
            "monetizacion": "€19/mes suscripción",
            "tool": "Chrome Extension",
            "esfuerzo": "20-30h",
            "revenue_6m": "€4,800",
            "como": "Chrome Web Store + LinkedIn outreach"
        },
        {
            "tipo": "Guía PDF",
            "vertical": "Freelancers",
            "nombre_base": "Cold Email Templates Pack",
            "problema": "Freelancers no saben cómo prospectar clientes por email",
            "producto": "50 plantillas de cold emails probadas con análisis de por qué funcionan",
            "precio": "15",
            "monetizacion": "€15 pago único",
            "tool": "Canva + Gumroad",
            "esfuerzo": "6-10h",
            "revenue_6m": "€1,800",
            "como": "Vender en Gumroad + Twitter + ProductHunt"
        },
        {
            "tipo": "Figma Plugin",
            "vertical": "Diseñadores",
            "nombre_base": "AI Color Palette Generator",
            "problema": "Crear paletas de colores coherentes toma mucho tiempo",
            "producto": "Plugin que genera paletas profesionales con IA basadas en mood/industria",
            "precio": "12",
            "monetizacion": "€12 pago único",
            "tool": "Figma Plugin",
            "esfuerzo": "15-25h",
            "revenue_6m": "€3,200",
            "como": "Figma Community + Twitter + Reddit r/FigmaDesign"
        },
        {
            "tipo": "Google Sheets Template",
            "vertical": "Ecommerce",
            "nombre_base": "Profit Calculator Dashboard",
            "problema": "Tiendas online no trackean márgenes reales correctamente",
            "producto": "Dashboard automatizado que calcula costos, márgenes, break-even por producto",
            "precio": "24",
            "monetizacion": "€24 pago único",
            "tool": "Google Sheets",
            "esfuerzo": "10-15h",
            "revenue_6m": "€2,100",
            "como": "Gumroad + comunidades ecommerce"
        },
        {
            "tipo": "Micro-SaaS",
            "vertical": "Agencias",
            "nombre_base": "Client Report Generator",
            "problema": "Crear reportes mensuales para clientes es tedioso",
            "producto": "Herramienta que conecta Google Analytics/Ads y genera reportes automáticos en PDF",
            "precio": "49",
            "monetizacion": "€49/mes",
            "tool": "No-code (Bubble/Softr)",
            "esfuerzo": "40-60h",
            "revenue_6m": "€8,400",
            "como": "SEO + cold email a agencias"
        },
        {
            "tipo": "Curso Email",
            "vertical": "Developers",
            "nombre_base": "7-Day API Integration Course",
            "problema": "Developers junior no saben integrar APIs de terceros",
            "producto": "7 emails con ejemplos prácticos de integrar Stripe, Mailchimp, etc.",
            "precio": "39",
            "monetizacion": "€39 pago único",
            "tool": "ConvertKit + Notion",
            "esfuerzo": "12-20h",
            "revenue_6m": "€3,500",
            "como": "Lanzar en ProductHunt + Dev.to + Twitter"
        },
        {
            "tipo": "Plantilla Airtable",
            "vertical": "Recruiters",
            "nombre_base": "ATS Lite - Candidate Tracker",
            "problema": "Recruiters pequeños no pueden pagar ATS caros",
            "producto": "Base Airtable con pipelines, automatizaciones, email templates integrados",
            "precio": "35",
            "monetizacion": "€35 pago único",
            "tool": "Airtable",
            "esfuerzo": "12-18h",
            "revenue_6m": "€2,800",
            "como": "Gumroad + LinkedIn + Reddit r/recruiting"
        },
        {
            "tipo": "Webflow Template",
            "vertical": "SaaS Founders",
            "nombre_base": "SaaS Landing Page Template",
            "problema": "Founders técnicos no saben diseñar landing pages que conviertan",
            "producto": "Template Webflow con 5 secciones probadas + animaciones + responsive",
            "precio": "79",
            "monetizacion": "€79 pago único",
            "tool": "Webflow",
            "esfuerzo": "25-35h",
            "revenue_6m": "€5,900",
            "como": "Webflow Marketplace + Twitter + Indie Hackers"
        },
        {
            "tipo": "Automation Service",
            "vertical": "Small Business",
            "nombre_base": "Zapier Automation Setup Service",
            "problema": "Pequeños negocios quieren automatizar pero no saben usar Zapier",
            "producto": "Servicio: configuro 5 automatizaciones personalizadas en 48h",
            "precio": "299",
            "monetizacion": "€299 por proyecto",
            "tool": "Zapier + Make",
            "esfuerzo": "4-6h por cliente",
            "revenue_6m": "€7,200",
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
                print("   âš ï¸  Cache de trends expirado (se actualizará en próxima ejecución)")
        
        except Exception as e:
            print(f"   âš ï¸  Error verificando trends: {e}")
            viral_opportunity = None
    else:
        print("   â„¹ï¸  Trend Hunter deshabilitado - usando generación normal")
    
    # ============ INTENTOS DE GENERACIí“N ============
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
                'precio_sugerido': viral_opportunity.get('precio_sugerido', '€29').replace('€', '').strip(),
                'modelo_monetizacion': f"{viral_opportunity.get('precio_sugerido', '€29')} pago único en {viral_opportunity.get('plataforma', 'Gumroad')}",
                'features_core': ', '.join(viral_opportunity.get('pasos_rapidos', ['Feature 1', 'Feature 2', 'Feature 3'])[:3]),
                'roadmap_mvp': f"Crear en {viral_opportunity.get('tiempo_creacion', '48h')} â†’ Lanzar en ProductHunt â†’ Iterar según feedback",
                'stack_sugerido': viral_opportunity.get('plataforma', 'Gumroad') + ', Twitter, Reddit',
                'integraciones': 'Standalone (sin integraciones complejas)',
                'canales_adquisicion': 'ProductHunt, Twitter, Reddit, comunidades nicho',
                'metricas_clave': 'Ventas primeras 48h, tasa conversión, viralidad',
                'riesgos': 'Trend puede morir rápido si no se capitaliza a tiempo',
                'validacion_inicial': viral_opportunity.get('revenue_estimado_2_semanas', '€500-€1000'),
                'tiempo_estimado': viral_opportunity.get('tiempo_creacion', '24-48h'),
                'inversion_inicial': '€0 (o mínima para herramientas)',
                'dificultad': 'Baja-Media',
                'revenue_6_meses': viral_opportunity.get('revenue_estimado_2_semanas', '€1,000').replace('€', '').strip(),
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
            
            # Verificar si es única
            if not is_duplicate(idea, existing_ideas):
                print(f"âœ… IDEA VIRAL íšNICA - {idea['nombre']}")
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

Genera variación íšNICA y ESPECíFICA. No copies el producto base tal cual.

JSON sin markdown:
{{
  "nombre": "[Nombre específico diferente]",
  "descripcion": "[Descripción única 150 chars]",
  "propuesta_valor": "[Por qué es mejor que alternativas]",
  "features_core": "[3-5 features concretas separadas por comas]",
  "diferenciacion": "[Qué lo hace único]",
  "tam": "[Tamaño mercado total]",
  "sam": "[Mercado alcanzable]",
  "som": "[Mercado objetivo primer año]"
}}"""

        try:
            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "Eres experto en productos digitales monetizables. Generas variaciones únicas y específicas."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.9,
                max_tokens=800
            )
            
            content = fix_llm_encoding(response.choices[0].message.content.strip())
            
            # Limpiar markdown
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0].strip()
            elif '```' in content:
                content = content.split('```')[1].split('```')[0].strip()
            
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
                'propuesta_valor': enrichment.get('propuesta_valor', 'Solución efectiva y rápida'),
                'diferenciacion': enrichment.get('diferenciacion', f"Específico para {product['vertical']}"),
                'tam': enrichment.get('tam', '50M'),
                'sam': enrichment.get('sam', '5M'),
                'som': enrichment.get('som', '500K'),
                'competencia': 'Competencia moderada en el nicho',
                'ventaja_competitiva': 'Especialización y ejecución rápida',
                'precio_sugerido': product['precio'],
                'modelo_monetizacion': product['monetizacion'],
                'features_core': enrichment.get('features_core', 'Feature 1, Feature 2, Feature 3'),
                'roadmap_mvp': 'Semana 1: Setup y diseño, Semana 2: Desarrollo, Semana 3: Testing y lanzamiento',
                'stack_sugerido': f"{product['tool']}, Gumroad, Twitter",
                'integraciones': f"{product['tool']}, Zapier, webhooks",
                'canales_adquisicion': 'Twitter, ProductHunt, Reddit, comunidades especializadas',
                'metricas_clave': 'MRR, tasa conversión, CAC, LTV',
                'riesgos': 'Competencia puede copiar, dependencia de plataforma',
                'validacion_inicial': '10 ventas en primeras 2 semanas',
                'tiempo_estimado': product['esfuerzo'],
                'inversion_inicial': '€0-€50',
                'dificultad': 'Media',
                'revenue_6_meses': product['revenue_6m'],
                'como_monetizar': product['como'],
                'score_generador': 75,
                '_fingerprint': calculate_fingerprint(enrichment.get('nombre', nombre_unico), product['problema'][:100])
            }
            
            # Verificar duplicados
            if not is_duplicate(idea, existing_ideas):
                print(f"âœ… IDEA NORMAL íšNICA - {idea['nombre']}")
                return idea
            else:
                print(f"   âš ï¸  Idea duplicada (attempt {attempt})")
        
        except Exception as e:
            print(f"   âš ï¸  Error en generación: {e}")
            continue
    
    # Si llegamos aquí, no se pudo generar idea única
    print("\nâŒ No se pudo generar idea única después de 5 intentos")
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
        print("\nâŒ No se generó idea")





