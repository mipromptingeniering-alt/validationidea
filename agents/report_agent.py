import os
import json
from datetime import datetime

def generate_report(idea, critique):
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
        recomendacion = "Idea sólida. Ejecutar YA."
    elif score_promedio >= 70:
        viabilidad = "MEDIA ⭐⭐"
        recomendacion = "Viable. Validar antes de invertir 40h."
    else:
        viabilidad = "BAJA ⭐"
        recomendacion = "Riesgos altos. Solo si tienes ventaja única."
    monetizacion = idea.get('monetizacion', '').lower()
    if '29' in monetizacion:
        precio = 29
        ing_m3, ing_m6, ing_m12 = '145', '725', '2,175'
    elif '19' in monetizacion:
        precio = 19
        ing_m3, ing_m6, ing_m12 = '95', '475', '1,425'
    elif '49' in monetizacion:
        precio = 49
        ing_m3, ing_m6, ing_m12 = '245', '1,225', '3,675'
    else:
        precio = 19
        ing_m3, ing_m6, ing_m12 = '100', '500', '1,500'
    tech_str = ', '.join(idea.get('tech_stack', ['Next.js']))
    prompt = {"proyecto": idea.get('nombre', ''), "descripcion": idea.get('descripcion_corta', ''), "problema": idea.get('problema', ''), "solucion": idea.get('solucion', ''), "tech_stack": tech_str, "funcionalidades": ["Auth", "Dashboard", "Feature core", "Stripe"], "instrucciones": ["Proyecto completo", "TypeScript", "Responsive"]}
    prompt_json = json.dumps(prompt, indent=2, ensure_ascii=False)
    comp_str = '\n'.join([f"- {c}" for c in idea.get('competencia', [])])
    fort_str = '\n'.join([f"- {f}" for f in critique.get('fortalezas', [])])
    deb_str = '\n'.join([f"- {d}" for d in critique.get('debilidades', [])])
    riesg_str = '\n'.join([f"{i}. {r}" for i, r in enumerate(critique.get('riesgos_mayores', []), 1)])
    report_content = f"""# 📊 Informe Completo: {nombre}

**Fecha:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Viabilidad:** {viabilidad}  
**Scores:** Gen {score_gen}/100 | Crit {score_crit}/100 | Promedio {score_promedio:.0f}/100

## 🎯 Resumen

{idea.get('descripcion_corta', '')}

**Problema:** {idea.get('problema', '')}  
**Solución:** {idea.get('solucion', '')}

## 💡 Propuesta de Valor

{idea.get('propuesta_valor', '')}

**Recomendación:** {recomendacion}

## 👥 Mercado: {idea.get('mercado_objetivo', '')}

### TAM/SAM/SOM

**TAM:** $50M-500M/año (mercado global)  
**SAM:** $5M-50M/año (mercado servible)  
**SOM:** $50K-200K/año (capturable en 12 meses)

## 🏢 Competencia

{comp_str}

**Fortalezas:** {fort_str}

**Debilidades:** {deb_str}

## 💰 Monetización

{idea.get('monetizacion', '')}

**Proyecciones:** Mes 3: €{ing_m3} | Mes 6: €{ing_m6} | Mes 12: €{ing_m12}

## 📅 Roadmap 6 Semanas

**S1:** Validación - 10 conversaciones, wireframes, 50 emails  
**S2:** MVP v0.1 - Setup stack, auth, feature #1, 5 beta testers  
**S3:** Iterar - Feedback, feature #2, onboarding <5min  
**S4:** Monetización - Stripe, pricing €{precio}/mes, lanzamiento  
**S5:** Clientes - Onboarding, analytics, 10 pagando  
**S6:** Growth - Content, feature #3, ads test, 25 pagando

## 🚨 Riesgos

{riesg_str}

**Mitigación:** Validar antes de programar. Métricas claras. Si nadie paga tras 50 conversaciones → pivotar.

## 🎯 Veredicto

{critique.get('veredicto_honesto', 'Validar con usuarios reales')}

## 🤖 Prompt IA

```json
{prompt_json}
Instrucciones: Genera proyecto Next.js 15 + Supabase + Stripe. TypeScript estricto. Responsive. Simplicidad sobre complejidad.

📈 Métricas Semana 1
20 conversaciones usuarios

10 email signups

5 demo requests

Willingness to pay >50%

Decisión: ✅ Continuar si alcanzas | ❌ Pivotar si no

Sistema Multi-Agente • Groq AI • €0/mes
"""
with open(report_file, 'w', encoding='utf-8') as f:
f.write(report_content)
print(f"✅ Informe completo: {report_file}")
return slug

if name == "main":
test_idea = {"nombre": "Test", "descripcion_corta": "Test", "problema": "Test", "solucion": "Test", "propuesta_valor": "Test", "mercado_objetivo": "Devs", "competencia": ["C1"], "monetizacion": "$19/mes", "tech_stack": ["Next.js"], "score_generador": 75}
test_critique = {"score_critico": 65, "fortalezas": ["F1"], "debilidades": ["D1"], "riesgos_mayores": ["R1"], "veredicto_honesto": "Test"}
generate_report(test_idea, test_critique)
