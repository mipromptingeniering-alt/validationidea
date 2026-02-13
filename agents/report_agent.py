import os
import json
from datetime import datetime

def generate_report(idea, critique):
    """Generar informe completo en Markdown con TODO"""
    nombre = idea.get('nombre', 'Idea sin nombre')
    slug = nombre.lower().replace(' ', '-').replace('/', '-')[:30]
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    os.makedirs('reports', exist_ok=True)
    report_file = f'reports/{slug}.md'
    
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    score_promedio = (score_gen + score_crit) / 2
    
    if score_promedio >= 80:
        viabilidad = "ALTA ⭐⭐⭐"
        recomendacion = "Idea sólida con alto potencial. Vale la pena ejecutar."
        prob_exito = "65-80%"
    elif score_promedio >= 70:
        viabilidad = "MEDIA ⭐⭐"
        recomendacion = "Idea viable con riesgos manejables. Validar antes de invertir mucho tiempo."
        prob_exito = "45-65%"
    else:
        viabilidad = "BAJA ⭐"
        recomendacion = "Idea con riesgos significativos. Solo ejecutar si tienes ventaja única."
        prob_exito = "20-45%"
    
    tam_estimado = """**TAM (Total Addressable Market):** Mercado global total estimado: **$50M - $500M/año**
- Basado en número de usuarios potenciales globales en el nicho
- Crecimiento anual estimado: 15-25%

**SAM (Serviceable Addressable Market):** Mercado que puedes servir realísticamente: **$5M - $50M/año**
- Limitado por idioma, geografía, canales de distribución
- Target inicial: mercados anglófonos + Europa

**SOM (Serviceable Obtainable Market):** Lo que puedes capturar en 12 meses: **$50K - $200K/año**
- Asumiendo 500-2000 usuarios activos
- Penetración del 0.5-2% del SAM en año 1

**Nota:** Cifras conservadoras. Validar con datos reales de competencia y encuestas."""
    
    stack_map = {
        'Next.js 15': '[Next.js 15](https://nextjs.org/)',
        'Next.js': '[Next.js](https://nextjs.org/)',
        'Supabase': '[Supabase](https://supabase.com/)',
        'Vercel': '[Vercel](https://vercel.com/)',
        'Tailwind CSS': '[Tailwind CSS](https://tailwindcss.com/)',
        'Tailwind': '[Tailwind CSS](https://tailwindcss.com/)',
        'TypeScript': '[TypeScript](https://www.typescriptlang.org/)',
        'Stripe': '[Stripe](https://stripe.com/)',
        'Resend': '[Resend](https://resend.com/)',
        'Cloudflare': '[Cloudflare](https://cloudflare.com/)',
        'Astro': '[Astro](https://astro.build/)',
        'React': '[React](https://react.dev/)',
        'PostgreSQL': '[PostgreSQL](https://www.postgresql.org/)',
        'Prisma': '[Prisma](https://www.prisma.io/)',
        'tRPC': '[tRPC](https://trpc.io/)'
    }
    
    tech_stack_links = ""
    for tech in idea.get('tech_stack', []):
        tech_str = tech.strip()
        tech_stack_links += f"- {stack_map.get(tech_str, tech_str)}\n"
    
    roadmap = """### Semana 1: Validación del Problema
- [ ] **Día 1-2:** 10 conversaciones con usuarios objetivo (grabar con permiso)
- [ ] **Día 3:** Analizar patrones en conversaciones → 3 pain points principales
- [ ] **Día 4:** Definir 3 funcionalidades core (no más)
- [ ] **Día 5:** Wireframes en papel/Figma de flujo principal
- [ ] **Día 6-7:** Landing page simple con formulario email (sin producto aún)
- [ ] **Meta:** 50 emails en lista espera

### Semana 2: MVP v0.1 - Lo Mínimo Viable
- [ ] **Día 1:** Setup proyecto: Next.js + Supabase + Vercel
- [ ] **Día 2:** Auth básico (email/password o Google OAuth)
- [ ] **Día 3-4:** Funcionalidad core #1 (la más crítica)
- [ ] **Día 5:** UI mínima pero funcional (Tailwind + shadcn/ui)
- [ ] **Día 6:** Deploy en Vercel + testing manual
- [ ] **Día 7:** 5 beta testers invitados → feedback en 48h
- [ ] **Meta:** 5 usuarios usando el MVP

### Semana 3: Iterar Basado en Feedback Real
- [ ] **Día 1-2:** Analizar feedback de beta testers (bugs + feature requests)
- [ ] **Día 3-4:** Funcionalidad core #2
- [ ] **Día 5:** Mejorar onboarding (primer uso <5 min)
- [ ] **Día 6:** Testing con 10 nuevos usuarios
- [ ] **Día 7:** Ajustes UX basados en observación
- [ ] **Meta:** Retención día 7 > 40%

### Semana 4: Monetización y Lanzamiento Público
- [ ] **Día 1-2:** Pricing page + integración Stripe
- [ ] **Día 3:** Plan gratuito limitado + plan pago ($19-29/mes)
- [ ] **Día 4:** Mejorar landing page con social proof
- [ ] **Día 5:** Preparar lanzamiento: Product Hunt, Reddit, Twitter
- [ ] **Día 6:** Lanzamiento público coordinado
- [ ] **Día 7:** Soporte activo en redes sociales
- [ ] **Meta:** 100 signups, 5 clientes pagando

### Semana 5: Primeros Clientes y Retention
- [ ] **Día 1-3:** Onboarding personalizado a primeros clientes
- [ ] **Día 4-5:** Implementar analytics (PostHog o Mixpanel)
- [ ] **Día 6-7:** Email drip campaign para conversión free → paid
- [ ] **Meta:** 200 usuarios, 10 pagando (€190-290/mes)

### Semana 6: Escala y Growth
- [ ] **Día 1-2:** Content marketing: 2 artículos SEO
- [ ] **Día 3-4:** Funcionalidad core #3 basada en requests
- [ ] **Día 5:** Optimizar conversión (A/B testing pricing)
- [ ] **Día 6-7:** Primeros anuncios pagados (€50 test Facebook/Google)
- [ ] **Meta:** 500 usuarios, 25 pagando (€475-725/mes)"""
    
    monetizacion = idea.get('monetizacion', '').lower()
    if '$19' in monetizacion or '€19' in monetizacion or '19' in monetizacion:
        precio = 19
        ing_m3, ing_m6, ing_m12 = '95', '475', '1,425'
    elif '$29' in monetizacion or '€29' in monetizacion or '29' in monetizacion:
        precio = 29
        ing_m3, ing_m6, ing_m12 = '145', '725', '2,175'
    elif '$49' in monetizacion or '€49' in monetizacion or '49' in monetizacion:
        precio = 49
        ing_m3, ing_m6, ing_m12 = '245', '1,225', '3,675'
    elif '$9' in monetizacion or '€9' in monetizacion or '9' in monetizacion:
        precio = 9
        ing_m3, ing_m6, ing_m12 = '45', '225', '675'
    else:
        precio = 19
        ing_m3, ing_m6, ing_m12 = '100', '500', '1,500'
    
    tech_stack_str = ', '.join(idea.get('tech_stack', ['Next.js 15', 'Supabase', 'Vercel']))
    
    prompt = {
        "proyecto": idea.get('nombre', ''),
        "descripcion": idea.get('descripcion_corta', ''),
        "problema_a_resolver": idea.get('problema', ''),
        "solucion_propuesta": idea.get('solucion', ''),
        "propuesta_valor": idea.get('propuesta_valor', ''),
        "mercado_objetivo": idea.get('mercado_objetivo', ''),
        "tech_stack": tech_stack_str,
        "funcionalidades_core": [
            "Autenticación de usuarios (email/password + OAuth Google)",
            "Dashboard principal con overview del usuario",
            "Funcionalidad principal específica del proyecto",
            "Pricing page con integración Stripe",
            "Sistema de notificaciones (email via Resend)"
        ],
        "requisitos_tecnicos": {
            "framework": "Next.js 15 con App Router",
            "database": "Supabase (PostgreSQL)",
            "auth": "Supabase Auth",
            "styling": "Tailwind CSS + shadcn/ui",
            "deployment": "Vercel",
            "analytics": "PostHog o Mixpanel",
            "payments": "Stripe Checkout + Customer Portal",
            "emails": "Resend con templates React Email"
        },
        "estilo_ui": "Moderno, minimalista, gradientes suaves, micro-interacciones",
        "paleta_colores": {
            "primary": "#667eea",
            "secondary": "#764ba2",
            "accent": "#f093fb",
            "background": "#ffffff",
            "text": "#1a202c"
        },
        "instrucciones_ia": [
            "Genera estructura completa del proyecto con arquitectura escalable",
            "Implementa las 3 funcionalidades core primero",
            "Setup completo de Supabase con Row Level Security (RLS)",
            "Auth funcional con rutas protegidas",
            "Landing page optimizada para conversión",
            "Dashboard con datos reales del usuario",
            "Pricing page con Stripe funcionando",
            "Responsive design (mobile-first)",
            "Loading states y error handling",
            "TypeScript estricto en todo el proyecto"
        ],
        "estructura_carpetas": {
            "app": "Routes y páginas (App Router)",
            "components": "Componentes reutilizables",
            "lib": "Utilidades y configuración",
            "hooks": "Custom React hooks",
            "types": "TypeScript types",
            "public": "Assets estáticos"
        }
    }
    
    prompt_json = json.dumps(prompt, indent=2, ensure_ascii=False)
    
    report_content = f"""# 📊 Informe Completo de Validación: {nombre}

**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Viabilidad General:** {viabilidad}  
**Score Generador IA:** {score_gen}/100  
**Score Crítico IA:** {score_crit}/100  
**Score Promedio:** {score_promedio:.1f}/100  
**Probabilidad de Éxito:** {prob_exito}

---

## 🎯 Resumen Ejecutivo (Elevator Pitch)

{idea.get('descripcion_corta', '')}

### Problema Identificado

{idea.get('problema', '')}

### Solución Propuesta

{idea.get('solucion', '')}

### ¿Por Qué Ahora?

El mercado actual demanda soluciones más ágiles en este espacio. La competencia existente tiene fricciones significativas que esta idea resuelve.

---

## 💡 Propuesta de Valor Única

{idea.get('propuesta_valor', '')}

### Diferenciación Clave vs Competencia

{idea.get('diferenciacion', '')}

**¿Por qué un usuario elegiría esto?**
- Más rápido/simple que alternativas existentes
- Enfoque en un nicho específico desatendido
- Pricing más accesible o modelo más justo
- Mejor UX/experiencia de usuario

---

## 👥 Mercado Objetivo y Personas

**Target Principal:** {idea.get('mercado_objetivo', '')}

### Segmentación Detallada

**Early Adopters (Primeros 100 clientes):**
- Profesionales que ya usan herramientas similares
- Frustrados con soluciones actuales
- Dispuestos a probar nuevas herramientas
- Budget para SaaS ($10-50/mes)

**Mainstream (Escala):**
- Mercado más amplio con mismo pain point
- Necesitan más educación sobre el problema
- Más sensibles al precio

### Análisis de Mercado (TAM/SAM/SOM)

{tam_estimado}

---

## 🏢 Análisis Competitivo

### Competencia Principal

"""
    
    for i, comp in enumerate(idea.get('competencia', []), 1):
        report_content += f"{i}. **{comp}**\n"
    
    report_content += f"""
### Matriz Competitiva

| Factor | {nombre} | Competidor 1 | Competidor 2 |
|--------|----------|--------------|--------------|
| Precio | €{precio}/mes | €29-99/mes | €49+/mes |
| Setup | <5 min | 15-30 min | Complejo |
| Target | Nicho específico | General | Enterprise |
| UX | Moderno | Anticuado | Complejo |

### Análisis SWOT

**Fortalezas (Strengths):**
"""
    
    for f in critique.get('fortalezas', ['Enfoque específico', 'Setup rápido']):
        report_content += f"- {f}\n"
    
    report_content += "\n**Debilidades (Weaknesses):**\n"
    
    for d in critique.g
