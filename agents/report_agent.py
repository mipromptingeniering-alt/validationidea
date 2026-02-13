import os
import json
from datetime import datetime

def generate_report(idea, critique):
    """Generar informe completo en Markdown"""
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
    elif score_promedio >= 70:
        viabilidad = "MEDIA ⭐⭐"
        recomendacion = "Idea viable con riesgos manejables. Validar antes de invertir mucho tiempo."
    else:
        viabilidad = "BAJA ⭐"
        recomendacion = "Idea con riesgos significativos. Solo ejecutar si tienes ventaja única."
    tam_estimado = """
**TAM (Total Addressable Market):** Mercado global estimado: **$50M - $500M/año**
**SAM (Serviceable Addressable Market):** Mercado que puedes servir: **$5M - $50M/año**
**SOM (Serviceable Obtainable Market):** Lo que puedes capturar en 12 meses: **$50K - $200K/año**
**Nota:** Estimaciones conservadoras. Valida con datos reales de competencia."""
    stack_map = {'Next.js 15': '[Next.js 15](https://nextjs.org/)', 'Next.js': '[Next.js](https://nextjs.org/)', 'Supabase': '[Supabase](https://supabase.com/)', 'Vercel': '[Vercel](https://vercel.com/)', 'Tailwind CSS': '[Tailwind CSS](https://tailwindcss.com/)', 'Tailwind': '[Tailwind CSS](https://tailwindcss.com/)', 'TypeScript': '[TypeScript](https://www.typescriptlang.org/)', 'Stripe': '[Stripe](https://stripe.com/)', 'Resend': '[Resend](https://resend.com/)', 'Cloudflare': '[Cloudflare](https://cloudflare.com/)', 'Astro': '[Astro](https://astro.build/)'}
    tech_stack_links = ""
    for tech in idea.get('tech_stack', []):
        tech_str = tech.strip()
        tech_stack_links += f"- {stack_map.get(tech_str, tech_str)}\n"
    roadmap = """
### Semana 1: Validación
- [ ] 10 conversaciones con usuarios objetivo
- [ ] Definir 3 funcionalidades core
- [ ] Wireframes en papel/Figma
- [ ] Landing page simple

### Semana 2: MVP v0.1
- [ ] Setup: Next.js + Supabase + Vercel
- [ ] Auth básico
- [ ] 1 funcionalidad core
- [ ] Deploy y 5 beta testers

### Semana 3-4: Iterar
- [ ] Feedback de beta testers
- [ ] Añadir funcionalidad #2
- [ ] Pricing page + Stripe
- [ ] Lanzamiento público

### Semana 5-6: Growth
- [ ] Content marketing
- [ ] SEO básico
- [ ] Primeros 10 clientes pagando
- [ ] Iterar basado en feedback"""
    monetizacion = idea.get('monetizacion', '').lower()
    if '$19' in monetizacion or '19' in monetizacion:
        ing_m3, ing_m6, ing_m12 = '95', '475', '1,425'
    elif '$29' in monetizacion or '29' in monetizacion:
        ing_m3, ing_m6, ing_m12 = '145', '725', '2,175'
    elif '$9' in monetizacion or '9' in monetizacion:
        ing_m3, ing_m6, ing_m12 = '45', '225', '675'
    else:
        ing_m3, ing_m6, ing_m12 = '100', '500', '1,500'
    tech_stack_str = ', '.join(idea.get('tech_stack', ['Next.js 15', 'Supabase', 'Vercel']))
    prompt = {"proyecto": idea.get('nombre', ''), "descripcion": idea.get('descripcion_corta', ''), "problema": idea.get('problema', ''), "solucion": idea.get('solucion', ''), "tech_stack": tech_stack_str, "funcionalidades_core": ["Autenticación de usuarios", "Dashboard principal", "Funcionalidad core específica", "Pricing page + Stripe"], "estilo_ui": "Moderno, minimalista, gradientes suaves", "colores": "Primario: #667eea, Secundario: #764ba2", "instrucciones": ["Genera estructura completa", "Setup Supabase", "Auth y rutas protegidas", "Landing page", "Dashboard funcional"]}
    prompt_json = json.dumps(prompt, indent=2, ensure_ascii=False)
    report_content = f"""# 📊 Informe Completo: {nombre}

**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Viabilidad:** {viabilidad}  
**Score Generador:** {score_gen}/100 | **Score Crítico:** {score_crit}/100

---

## 🎯 Resumen Ejecutivo

{idea.get('descripcion_corta', '')}

**Problema:** {idea.get('problema', '')}

**Solución:** {idea.get('solucion', '')}

---

## 💡 Propuesta de Valor

{idea.get('propuesta_valor', '')}

**Diferenciación clave:** {idea.get('diferenciacion', '')}

---

## 👥 Mercado Objetivo

**Target:** {idea.get('mercado_objetivo', '')}

### Análisis de Mercado (TAM/SAM/SOM)

{tam_estimado}

---

## 🏢 Competencia

"""
    for comp in idea.get('competencia', []):
        report_content += f"- **{comp}**\n"
    report_content += "\n### Análisis Competitivo\n\n**Fortalezas:**\n"
    for f in critique.get('fortalezas', []):
        report_content += f"- {f}\n"
    report_content += "\n**Debilidades:**\n"
    for d in critique.get('debilidades', []):
        report_content += f"- {d}\n"
    report_content += f"""
---

## 💰 Modelo de Negocio

{idea.get('monetizacion', '')}

### Proyección Realista (Año 1)

- **Mes 1-2:** Desarrollo MVP + primeros 10 beta testers (€0)
- **Mes 3:** Lanzamiento público. Meta: 50 usuarios (5 pagando) → €{ing_m3}
- **Mes 6:** Crecimiento orgánico. Meta: 200 usuarios (25 pagando) → €{ing_m6}
- **Mes 12:** Escala. Meta: 500 usuarios (75 pagando) → €{ing_m12}

**Inversión inicial:** €0-500  
**Break-even esperado:** Mes 4-6

---

## 🛠️ Stack Tecnológico 2026

{tech_stack_links}

**Justificación:** Rápido desarrollo, costo €0/mes inicial, escalable, modern DX.

---

## 📅 Roadmap Realista

{roadmap}

---

## 🚨 Riesgos y Mitigación

"""
    for i, riesgo in enumerate(critique.get('riesgos_mayores', []), 1):
        report_content += f"\n### Riesgo #{i}: {riesgo}\n\n**Mitigación:** Validar con 10 usuarios antes de invertir más de 40h.\n"
    report_content += f"""
---

## 🎯 Opinión Profesional

**Veredicto:** {critique.get('veredicto_honesto', 'No disponible')}

**Probabilidad de éxito:** {critique.get('probabilidad_exito', 'N/A')}

### Mi Evaluación

**¿Vale la pena?** {recomendacion}

**Factores críticos:**
1. Validar problema con 10 conversaciones reales
2. MVP super simple: 1 funcionalidad core
3. Go-to-market: canal específico donde están usuarios
4. Pricing: empezar caro ($29 mejor que $9)

**Red flags:**
- Nadie paga después de 50 conversaciones → pivotar
- Competencia lanza feature similar → acelerar
- Churn >10% mensual → problema de PMF

---

## 🤖 Prompt para Desarrollar con IA

```json
{prompt_json}
Uso:

Cursor AI: Pega en chat, dile "genera proyecto completo"

v0.dev: Pega descripción y funcionalidades

Bolt.new: Pega todo el JSON

📈 Métricas Semana 1
20 conversaciones con usuarios

10 email signups

5 demo requests

Willingness to pay validado

Si alcanzas metas → seguir. Si no → pivotar.

Generado por Sistema Multi-Agente • Groq AI + GitHub Actions • $0/mes
"""
with open(report_file, 'w', encoding='utf-8') as f:
f.write(report_content)
print(f"✅ Informe generado: {report_file}")
return slug

if name == "main":
test_idea = {"nombre": "Test", "descripcion_corta": "Test", "problema": "Test", "solucion": "Test", "propuesta_valor": "Test", "mercado_objetivo": "Devs", "competencia": ["C1"], "diferenciacion": "Test", "monetizacion": "$19/mes", "tech_stack": ["Next.js"], "dificultad": "Media", "tiempo_estimado": "4 sem", "score_generador": 75}
test_critique = {"score_critico": 65, "fortalezas": ["F1"], "debilidades": ["D1"], "riesgos_mayores": ["R1"], "veredicto_honesto": "Test", "probabilidad_exito": "50%"}
generate_report(test_idea, test_critique)
