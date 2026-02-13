import os
from datetime import datetime

def generate_report(idea_data):
    """
    Genera un informe completo en Markdown para desarrolladores
    Incluye TAM/SAM/SOM, roadmap, proyecciones y prompt para IA
    """
    
    slug = idea_data.get('slug', 'idea')
    nombre = idea_data.get('nombre', 'Idea SaaS')
    descripcion = idea_data.get('descripcion', 'Una idea innovadora')
    problema = idea_data.get('problema', 'Problema a resolver')
    solucion = idea_data.get('solucion', 'Nuestra solución')
    tam = idea_data.get('tam', 'N/A')
    sam = idea_data.get('sam', 'N/A')
    som = idea_data.get('som', 'N/A')
    precio_sugerido = idea_data.get('precio_sugerido', '29€/mes')
    score = idea_data.get('score', 0)
    complejidad = idea_data.get('complejidad', 'MEDIA')
    tiempo_estimado = idea_data.get('tiempo_estimado', '20h')
    
    roadmap = """
## 🗓️ Roadmap 6 Semanas

### Semana 1-2: MVP Básico
- [ ] Setup proyecto (Next.js + Tailwind)
- [ ] Diseño UI/UX básico
- [ ] Landing page principal
- [ ] Sistema autenticación (Supabase Auth)
- [ ] Base de datos (Supabase)

### Semana 3-4: Funcionalidad Core
- [ ] Implementar funcionalidad principal
- [ ] Integración APIs necesarias
- [ ] Panel de usuario básico
- [ ] Sistema de pagos (Stripe)

### Semana 5: Testing y Mejoras
- [ ] Testing funcional
- [ ] Optimización rendimiento
- [ ] Fixes bugs críticos
- [ ] Mejoras UX basadas en feedback

### Semana 6: Lanzamiento
- [ ] Deploy producción (Vercel)
- [ ] Configurar analytics
- [ ] Lanzamiento ProductHunt
- [ ] Campaña marketing inicial
"""
    
    stack = """
## 🛠️ Stack Tecnológico Recomendado (100% Gratis hasta $$$)

**Frontend:**
- Next.js 14 (App Router)
- Tailwind CSS
- Shadcn/ui (componentes)

**Backend:**
- Vercel (hosting + serverless functions)
- Supabase (DB + Auth + Storage)

**Pagos:**
- Stripe (pay as you go)

**Analytics:**
- Vercel Analytics (gratis)
- PostHog (gratis hasta 1M eventos)

**Email:**
- Resend (gratis 100 emails/día)

**Deploy:**
- Vercel (100GB/mes gratis)
"""
    
    proyecciones = f"""
## 💰 Proyecciones Financieras

**Precio sugerido:** {precio_sugerido}

### Escenario Conservador (Mes 3)
- Usuarios: 20-50
- MRR: 580€-1,450€
- Churn: 15%

### Escenario Realista (Mes 6)
- Usuarios: 100-200
- MRR: 2,900€-5,800€
- Churn: 10%

### Escenario Optimista (Mes 12)
- Usuarios: 500-1,000
- MRR: 14,500€-29,000€
- Churn: 5%

**Costos mensuales estimados:** 50-200€ (hosting, APIs, tools)
"""
    
    mercado = f"""
## 📊 Análisis de Mercado

**TAM (Total Addressable Market):** {tam}
- Mercado total teórico disponible

**SAM (Serviceable Addressable Market):** {sam}
- Porción del mercado que podemos alcanzar

**SOM (Serviceable Obtainable Market):** {som}
- Porción realista en primeros 12 meses
"""
    
    prompt_ia = f"""
## 🤖 PROMPT PARA CURSOR / V0.DEV / BOLT

Copia y pega esto en tu IA de desarrollo favorita:

---

Quiero construir un SaaS llamado "{nombre}".

**Descripción:**
{descripcion}

**Problema que resuelve:**
{problema}

**Solución:**
{solucion}

**Stack técnico:**
- Frontend: Next.js 14 (App Router) + Tailwind CSS + Shadcn/ui
- Backend: Vercel + Supabase
- Pagos: Stripe
- Auth: Supabase Auth

**Funcionalidades core:**
1. Landing page con formulario registro
2. Sistema de autenticación (email/password y Google)
3. Dashboard de usuario
4. Funcionalidad principal
5. Sistema de suscripciones con Stripe
6. Panel admin básico

**Requisitos:**
- Responsive (mobile-first)
- Dark mode
- SEO optimizado
- TypeScript
- Lighthouse mayor a 90

Por favor, genera el proyecto completo con toda la estructura de carpetas y archivos necesarios.

---
"""
    
    marketing = """
## 📢 Estrategia Marketing (Primeras 2 Semanas)

### Día 1: Lanzamiento
- [ ] Post ProductHunt (prepara upvotes)
- [ ] Tweet anuncio + hilo features
- [ ] Post LinkedIn
- [ ] Subreddits relevantes (3-5)

### Día 2-7: Tracción Inicial
- [ ] Responder todos los comentarios
- [ ] Crear contenido (blog post, video demo)
- [ ] Compartir en comunidades indie hackers
- [ ] Cold outreach (50 emails)

### Día 8-14: Optimización
- [ ] Analizar métricas (conversión, churn)
- [ ] A/B testing landing page
- [ ] Recoger feedback usuarios
- [ ] Iterar producto

### Canales Recomendados:
1. Twitter/X - Audiencia tech, build in public
2. Reddit - Subreddits nicho
3. ProductHunt - Lanzamiento principal
4. LinkedIn - Audiencia B2B
5. IndieHackers - Comunidad makers
"""
    
    report_content = f"""# 📋 INFORME TÉCNICO: {nombre}

**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Score Validación:** {score}/100  
**Complejidad:** {complejidad}  
**Tiempo Estimado:** {tiempo_estimado}

---

## 🎯 Resumen Ejecutivo

{descripcion}

**Problema:**
{problema}

**Solución:**
{solucion}

---

{mercado}

---

{proyecciones}

---

{roadmap}

---

{stack}

---

{marketing}

---

{prompt_ia}

---

## ✅ Checklist Pre-Lanzamiento

### Técnico
- [ ] MVP funcional deployed
- [ ] Testing completo (funcional + user)
- [ ] Performance optimizado (Lighthouse mayor a 90)
- [ ] SEO configurado
- [ ] Analytics instalado
- [ ] Error tracking (Sentry)

### Legal
- [ ] Términos de servicio
- [ ] Política privacidad
- [ ] GDPR compliance (si aplica)
- [ ] Stripe account verificado

### Marketing
- [ ] Landing page optimizada
- [ ] Copy A/B tested
- [ ] Material gráfico (screenshots, video)
- [ ] Estrategia redes sociales
- [ ] Lista comunidades para launch

---

## 🚀 Próximos Pasos

1. Copia el PROMPT PARA IA de arriba
2. Pégalo en Cursor/v0.dev/Bolt
3. Genera el proyecto base
4. Sigue el roadmap 6 semanas
5. Lanza y distribuye según estrategia

---

## 📊 Métricas a Trackear

**Semana 1:**
- Visitas landing
- Signups
- Conversión signup a trial

**Mes 1:**
- Trial a Paid
- Churn rate
- MRR

**Mes 3:**
- CAC (Customer Acquisition Cost)
- LTV (Lifetime Value)
- Product-Market Fit Score

---

**Dudas?** Revisa el roadmap y ajusta según tu contexto específico.

**Buena suerte construyendo!**
"""
    
    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f'{output_dir}/{slug}.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Informe generado: {filename}")
    return filename


def generate_all_reports(ideas_list):
    """
    Genera informes para una lista de ideas
    """
    generated_files = []
    
    for idea in ideas_list:
        try:
            filename = generate_report(idea)
            generated_files.append(filename)
        except Exception as e:
            print(f"❌ Error generando informe para {idea.get('slug', 'unknown')}: {e}")
    
    return generated_files


if __name__ == "__main__":
    test_idea = {
        'slug': 'test-idea',
        'nombre': 'Test SaaS Validator',
        'descripcion': 'Herramienta para validar ideas rápidamente',
        'problema': 'Es difícil saber si una idea SaaS tendrá éxito sin invertir meses de desarrollo',
        'solucion': 'Sistema automatizado que valida ideas en 48 horas con landing pages y métricas reales',
        'tam': '50M€',
        'sam': '5M€',
        'som': '500K€',
        'precio_sugerido': '49€/mes',
        'score': 85,
        'complejidad': 'MEDIA',
        'tiempo_estimado': '30h'
    }
    
    print("🧪 Generando informe de prueba...")
    generate_report(test_idea)
    print("✅ Informe de prueba generado en reports/test-idea.md")
