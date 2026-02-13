import os
import json
from datetime import datetime

def generate_report(idea_data):
    """
    Genera informe técnico COMPLETO para desarrolladores
    Incluye PROMPT JSON estructurado para Cursor/Bolt/v0
    """
    
    slug = idea_data.get('slug', 'idea')
    nombre = idea_data.get('nombre', 'Idea SaaS')
    descripcion = idea_data.get('descripcion', 'Una idea innovadora')
    descripcion_corta = idea_data.get('descripcion_corta', descripcion)
    problema = idea_data.get('problema', 'Problema a resolver')
    solucion = idea_data.get('solucion', 'Nuestra solución')
    publico = idea_data.get('publico_objetivo', 'profesionales')
    tam = idea_data.get('tam', '50M€')
    sam = idea_data.get('sam', '5M€')
    som = idea_data.get('som', '500K€')
    precio = idea_data.get('precio_sugerido', '29€/mes')
    score = idea_data.get('score_generador', 75)
    dificultad = idea_data.get('dificultad', 'Media')
    tiempo = idea_data.get('tiempo_estimado', '4-6 semanas')
    competencia = idea_data.get('competencia', ['Competidor 1', 'Competidor 2'])
    diferenciacion = idea_data.get('diferenciacion', 'Propuesta única de valor')
    features = idea_data.get('features_core', ['Feature 1', 'Feature 2', 'Feature 3'])
    stack = idea_data.get('stack_sugerido', ['Next.js', 'Supabase', 'Stripe'])
    canales = idea_data.get('canales_adquisicion', ['Twitter', 'ProductHunt', 'Reddit'])
    
    # Crear JSON estructurado para Cursor/Bolt
    prompt_json = {
        "project_name": nombre,
        "description": descripcion,
        "target_audience": publico,
        "problem": problema,
        "solution": solucion,
        "tech_stack": {
            "frontend": "Next.js 14 (App Router)",
            "styling": "Tailwind CSS + Shadcn/ui",
            "backend": "Vercel Serverless Functions",
            "database": "Supabase (PostgreSQL)",
            "auth": "Supabase Auth",
            "payments": "Stripe",
            "email": "Resend",
            "analytics": "Vercel Analytics + PostHog"
        },
        "core_features": features,
        "pages": [
            {
                "route": "/",
                "name": "Landing Page",
                "sections": [
                    "Hero con CTA principal",
                    "Problema (pain points)",
                    "Solución (features con iconos)",
                    "Testimonios (3-6 usuarios)",
                    "Pricing (plan único simple)",
                    "FAQ (4-6 preguntas)",
                    "CTA final + formulario email"
                ]
            },
            {
                "route": "/dashboard",
                "name": "Dashboard Usuario",
                "sections": [
                    "Sidebar navegación",
                    "Stats cards (métricas principales)",
                    "Tabla/lista items principales",
                    "Acciones rápidas",
                    "Configuración cuenta"
                ]
            },
            {
                "route": "/auth/login",
                "name": "Login",
                "features": ["Email/password", "Google OAuth", "Magic link"]
            },
            {
                "route": "/auth/register",
                "name": "Registro",
                "features": ["Email/password", "Google OAuth", "Verificación email"]
            },
            {
                "route": "/pricing",
                "name": "Pricing",
                "features": ["Plan único", "Checkout Stripe", "Trial 7 días"]
            },
            {
                "route": "/admin",
                "name": "Panel Admin",
                "sections": [
                    "Lista usuarios",
                    "Métricas MRR/Churn",
                    "Logs actividad"
                ]
            }
        ],
        "database_schema": {
            "users": {
                "id": "uuid primary key",
                "email": "text unique",
                "name": "text",
                "avatar_url": "text",
                "subscription_status": "text (active/cancelled/trial)",
                "subscription_id": "text",
                "trial_ends_at": "timestamp",
                "created_at": "timestamp"
            },
            "items": {
                "id": "uuid primary key",
                "user_id": "uuid references users",
                "title": "text",
                "description": "text",
                "status": "text",
                "created_at": "timestamp",
                "updated_at": "timestamp"
            }
        },
        "stripe_products": [
            {
                "name": f"{nombre} Pro",
                "price": precio,
                "features": features,
                "trial_days": 7
            }
        ],
        "env_variables": {
            "NEXT_PUBLIC_SUPABASE_URL": "tu_supabase_url",
            "NEXT_PUBLIC_SUPABASE_ANON_KEY": "tu_supabase_anon_key",
            "SUPABASE_SERVICE_ROLE_KEY": "tu_service_role_key",
            "STRIPE_SECRET_KEY": "sk_test_xxx",
            "STRIPE_WEBHOOK_SECRET": "whsec_xxx",
            "NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY": "pk_test_xxx",
            "RESEND_API_KEY": "re_xxx"
        },
        "project_structure": {
            "/app": {
                "page.tsx": "Landing page",
                "/dashboard": {
                    "page.tsx": "Dashboard principal",
                    "layout.tsx": "Layout con sidebar"
                },
                "/auth": {
                    "/login/page.tsx": "Login",
                    "/register/page.tsx": "Registro",
                    "/callback/route.ts": "OAuth callback"
                },
                "/api": {
                    "/stripe/webhook/route.ts": "Webhook Stripe",
                    "/users/route.ts": "API usuarios"
                },
                "/pricing/page.tsx": "Pricing",
                "/admin/page.tsx": "Admin panel"
            },
            "/components": {
                "/ui": "Shadcn components",
                "/landing": "Landing sections",
                "/dashboard": "Dashboard components",
                "Navbar.tsx": "Navigation",
                "Footer.tsx": "Footer"
            },
            "/lib": {
                "supabase.ts": "Supabase client",
                "stripe.ts": "Stripe client",
                "utils.ts": "Utilities"
            }
        },
        "deployment": {
            "platform": "Vercel",
            "steps": [
                "Conectar repo GitHub",
                "Configurar env variables",
                "Deploy automático en main",
                "Configurar dominio custom (opcional)"
            ]
        },
        "requirements": [
            "TypeScript strict mode",
            "Responsive mobile-first",
            "Dark mode toggle",
            "SEO optimizado (meta tags, og:image)",
            "Loading states en todas las acciones",
            "Error handling completo",
            "Lighthouse score > 90"
        ]
    }
    
    prompt_json_str = json.dumps(prompt_json, indent=2, ensure_ascii=False)
    
    # Competencia en lista
    competencia_html = "\\n".join([f"{i+1}. **{comp}**" for i, comp in enumerate(competencia)])
    
    # Features en lista
    features_html = "\\n".join([f"- {feat}" for feat in features])
    
    # Stack en lista
    stack_html = "\\n".join([f"- {tech}" for tech in stack])
    
    # Canales en lista
    canales_html = "\\n".join([f"- {canal}" for canal in canales])
    
    report_content = f"""# 📋 INFORME TÉCNICO: {nombre}

**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Score Validación:** {score}/100  
**Complejidad:** {dificultad}  
**Tiempo Estimado:** {tiempo}

---

## 🎯 Resumen Ejecutivo

**Descripción:** {descripcion}

**Público objetivo:** {publico}

**Problema:**  
{problema}

**Solución:**  
{solucion}

**Diferenciación:**  
{diferenciacion}

---

## 📊 Validación de Mercado

### Tamaño del Mercado

| Métrica | Valor | Descripción |
|---------|-------|-------------|
| **TAM** | {tam} | Total Addressable Market (mercado total disponible) |
| **SAM** | {sam} | Serviceable Addressable Market (alcanzable) |
| **SOM** | {som} | Serviceable Obtainable Market (objetivo año 1) |

### Competencia Principal

{competencia_html}

**Tu ventaja competitiva:** {diferenciacion}

---

## 💰 Modelo de Negocio

### Pricing

**Precio:** {precio}

**Estrategia:**
- Trial gratuito 7 días (sin tarjeta)
- Descuento early bird 30% primeros 100 usuarios
- Suscripción mensual sin permanencia
- Upgrade/downgrade inmediato

### Proyecciones Financieras

| Período | Usuarios | MRR | ARR | Churn |
|---------|----------|-----|-----|-------|
| **Mes 3** | 20-50 | 580-1,450€ | 7K-17K€ | 15% |
| **Mes 6** | 100-200 | 2,900-5,800€ | 35K-70K€ | 10% |
| **Año 1** | 500-1,000 | 14,500-29,000€ | 174K-348K€ | 5% |

**Costos mensuales estimados:** 50-200€
- Vercel: 0-20€ (gratis hasta límite)
- Supabase: 0-25€ (gratis hasta 500MB)
- Stripe: 1.5% + 0.25€ por transacción
- Resend: 0-20€ (gratis 3K emails/mes)
- Dominio: 1€/mes

---

## 🛠️ Stack Tecnológico

{stack_html}

**Justificación:**
- ✅ **100% gratuito** hasta primeros ingresos
- ✅ **Escalable** hasta 10K usuarios sin cambios
- ✅ **Developer-friendly** (rápido de implementar)
- ✅ **Bien documentado** (gran comunidad)

---

## 🗓️ Roadmap de Desarrollo (6 Semanas)

### **Semana 1-2: Setup + MVP Core**
- [ ] Configurar proyecto Next.js 14 + Tailwind
- [ ] Integrar Supabase (DB + Auth)
- [ ] Landing page completa (hero, features, FAQ, CTA)
- [ ] Sistema autenticación (email/pass + Google OAuth)
- [ ] Página registro/login funcional

**Entregable:** Landing desplegada + Auth funcionando

---

### **Semana 3-4: Funcionalidad Principal**
- [ ] Dashboard usuario con sidebar
- [ ] CRUD funcionalidad core (crear/leer/actualizar/borrar)
- [ ] Integrar Stripe (checkout + webhooks)
- [ ] Página pricing con Stripe Checkout
- [ ] Sistema suscripciones (trial 7 días)

**Entregable:** Producto funcional end-to-end

---

### **Semana 5: Polish + Testing**
- [ ] Panel admin básico (usuarios, métricas)
- [ ] Email transaccionales (welcome, trial ending)
- [ ] Dark mode toggle
- [ ] Responsive mobile (test todos los breakpoints)
- [ ] Performance optimization (Lighthouse > 90)
- [ ] SEO (meta tags, sitemap, robots.txt)

**Entregable:** Producto production-ready

---

### **Semana 6: Lanzamiento**
- [ ] Testing completo (funcional + user)
- [ ] Deploy producción Vercel
- [ ] Configurar analytics (Vercel + PostHog)
- [ ] Términos servicio + Privacidad + GDPR
- [ ] Material marketing (screenshots, video demo)
- [ ] Lanzamiento ProductHunt + redes sociales

**Entregable:** Producto público lanzado

---

## 🚀 Funcionalidades Core

{features_html}

---

## 📢 Estrategia de Marketing

### Canales de Adquisición (Primeros 3 Meses)

{canales_html}

### Plan de Lanzamiento (Día a Día)

**Día 1: Launch ProductHunt**
- Post a las 00:01 PT (mejor horario)
- Conseguir 10-15 upvotes primeras 2h (amigos/comunidad)
- Responder TODOS los comentarios en <30min
- Compartir en Twitter con hilo 5-7 tweets
- Post LinkedIn (storytelling del problema)

**Día 2-7: Amplificación**
- 3 posts Reddit (subreddits nicho, NO spam)
- 50 emails cold outreach personalizados
- 2-3 posts IndieHackers (build in public)
- Crear contenido (blog post, video demo YouTube)
- Responder en foros Quora/Stack Overflow

**Semana 2-4: Iteración**
- Analizar métricas (Google Analytics + PostHog)
- Hablar con usuarios (Calendly 1:1 calls)
- A/B testing landing (headline, CTA, pricing)
- Crear caso de uso real (testimonios video)
- Guest posting blogs nicho

**Mes 2-3: Escalado**
- Paid ads pequeño presupuesto (50-100€/mes)
- Partnerships con complementarios
- Programa de afiliados (20% comisión)
- Content marketing SEO (2-4 posts/mes)

---

## 🤖 PROMPT COMPLETO PARA CURSOR / BOLT / V0.DEV

**Copia este JSON y pégalo en tu IA de desarrollo:**

\`\`\`json
{prompt_json_str}
\`\`\`

### Instrucciones para la IA:

> Genera un proyecto SaaS completo basado en el JSON anterior. Incluye:
> 
> 1. Estructura completa de carpetas según `project_structure`
> 2. Todos los componentes necesarios (landing, dashboard, auth)
> 3. Integración Supabase para DB y autenticación
> 4. Integración Stripe para pagos con webhooks
> 5. Schema de base de datos según `database_schema`
> 6. Emails transaccionales con Resend
> 7. Dark mode funcional
> 8. Responsive mobile-first
> 9. TypeScript strict
> 10. Optimizado SEO (meta tags, Open Graph)
> 
> Usa Shadcn/ui para componentes. Prioriza código limpio y bien documentado.

---

## ✅ Checklist Pre-Lanzamiento

### Técnico
- [ ] MVP funcional deployed en producción
- [ ] Testing completo (unit + integration + e2e)
- [ ] Performance optimizado (Lighthouse > 90)
- [ ] SEO configurado (meta, sitemap, robots.txt)
- [ ] Analytics instalado (Vercel + PostHog)
- [ ] Error tracking (Sentry o LogRocket)
- [ ] Backups DB automatizados
- [ ] SSL configurado (HTTPS)

### Legal & Compliance
- [ ] Términos de servicio (usar termsfeed.com)
- [ ] Política privacidad (incluir GDPR)
- [ ] GDPR compliance (banner cookies)
- [ ] Stripe account verificado (KYC)
- [ ] Email confirmación opt-in (doble opt-in)

### Marketing
- [ ] Landing page optimizada (conversión > 2%)
- [ ] Copy A/B tested (mínimo 2 variantes headline)
- [ ] Material gráfico (3 screenshots + video demo)
- [ ] Estrategia redes sociales (calendario 2 semanas)
- [ ] Lista 20 comunidades para distribución
- [ ] Email bienvenida + secuencia onboarding

### Financiero
- [ ] Cuenta bancaria business (Stripe Connect)
- [ ] Herramienta contabilidad (Holded o Stripe Tax)
- [ ] Presupuesto marketing definido (100-500€)

---

## 📊 Métricas Clave (KPIs)

### Semana 1 Post-Launch
- **Visitas landing:** 500-1,000
- **Signups:** 50-100 (5-10% conversión)
- **Trial activations:** 20-30 (40% de signups)

### Mes 1
- **Trial → Paid:** 10-15 (30-50% conversión)
- **MRR:** 300-500€
- **Churn:** <20%

### Mes 3
- **MRR:** 1,000-2,000€
- **CAC:** <50€ (Customer Acquisition Cost)
- **LTV:** >150€ (Lifetime Value)
- **Churn:** <15%

**Objetivo mínimo viabilidad:** 500€ MRR en 3 meses (cubre costos + tiempo invertido)

---

## 🎓 Recursos Útiles

### Desarrollo
- [Next.js Docs](https://nextjs.org/docs)
- [Supabase Docs](https://supabase.com/docs)
- [Stripe Docs](https://stripe.com/docs)
- [Shadcn/ui](https://ui.shadcn.com)

### Marketing
- [ProductHunt Launch Guide](https://www.producthunt.com/launch)
- [IndieHackers](https://www.indiehackers.com)
- [Startup School YC](https://www.startupschool.org)

### Legal
- [TermsFeed](https://www.termsfeed.com) (generador gratis)
- [GDPR Checklist](https://gdprchecklist.io)

---

## 🚀 Próximos Pasos (Action Plan)

1. **HOY:**
   - [ ] Copia el PROMPT JSON completo
   - [ ] Pégalo en Cursor/Bolt/v0.dev
   - [ ] Genera proyecto base

2. **ESTA SEMANA:**
   - [ ] Configura Supabase + Stripe (cuentas gratis)
   - [ ] Implementa landing + auth
   - [ ] Deploy en Vercel

3. **PRÓXIMAS 2 SEMANAS:**
   - [ ] Desarrolla funcionalidad core
   - [ ] Testing con 5-10 beta users
   - [ ] Pulir UX según feedback

4. **SEMANA 6:**
   - [ ] Launch ProductHunt
   - [ ] Distribución en canales
   - [ ] Primeros clientes de pago

---

## ⚠️ Riesgos y Mitigación

| Riesgo | Probabilidad | Impacto | Mitigación |
|--------|--------------|---------|------------|
| No encontrar product-market fit | Alta | Alto | Validar con 20+ entrevistas pre-build |
| Competencia fuerte | Media | Medio | Diferenciación clara + nicho específico |
| Costos inesperados | Baja | Bajo | Usar tier gratis, monitorizar uso |
| Problemas técnicos | Media | Medio | Testing exhaustivo, error tracking |
| Baja conversión | Alta | Alto | A/B testing continuo, analizar métricas |

---

## 💬 Dudas Frecuentes (para Emprendedores)

**¿Necesito saber programar?**  
Idealmente sí (básico). Si no, contrata freelancer (~500-1,500€) o usa no-code.

**¿Cuánto dinero necesito para empezar?**  
0-50€ (dominio). Todo lo demás es gratis hasta tener ingresos.

**¿Cuánto tiempo hasta primeros ingresos?**  
Con este plan: 6-8 semanas hasta primer cliente de pago.

**¿Y si nadie me compra?**  
Normal primeros días. Da 3 meses mínimo. Si tras 100 conversaciones nadie paga, pivota.

---

**¿Listo para construir?** 🚀  
Copia el JSON, genera el proyecto y empieza HOY. Suerte! 💪

---

*Informe generado automáticamente por [Idea Validator](https://github.com/mipromptingeniering-alt/validationidea)*
"""
    
    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f'{output_dir}/{slug}.md'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Informe generado: {filename}")
    return filename


def generate_all_reports(ideas_list):
    """Genera informes para una lista de ideas"""
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
        'slug': 'testmaster-pro',
        'nombre': 'TestMaster Pro',
        'descripcion': 'Plataforma de testing automatizado con IA que genera tests desde código',
        'descripcion_corta': 'Tests automáticos con IA',
        'problema': 'Desarrolladores pierden 15h/semana escribiendo tests manuales',
        'solucion': 'IA analiza el código y genera tests automatizados en tiempo real',
        'publico_objetivo': 'Equipos de desarrollo y freelancers tech',
        'tam': '150M€',
        'sam': '15M€',
        'som': '750K€',
        'precio_sugerido': '49€/mes',
        'score_generador': 82,
        'dificultad': 'Media',
        'tiempo_estimado': '4-6 semanas',
        'competencia': ['Jest', 'Cypress', 'Playwright'],
        'diferenciacion': 'Generación automática con IA vs manual',
        'features_core': ['Tests Automáticos', 'Cobertura 100%', 'CI/CD Integrado'],
        'stack_sugerido': ['Next.js', 'Supabase', 'Stripe'],
        'canales_adquisicion': ['Twitter', 'ProductHunt', 'Dev.to']
    }
    
    print("🧪 Generando informe de prueba...")
    generate_report(test_idea)
    print("✅ Informe generado en reports/testmaster-pro.md")
