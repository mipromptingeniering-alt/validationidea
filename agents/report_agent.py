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
    else:
        precio = 19
        ing_m3, ing_m6, ing_m12 = '100', '500', '1,500'
    
    tech_stack_str = ', '.join(idea.get('tech_stack', ['Next.js 15', 'Supabase', 'Vercel']))
    prompt = {"proyecto": idea.get('nombre', ''), "tech_stack": tech_stack_str, "problema": idea.get('problema', ''), "solucion": idea.get('solucion', '')}
    prompt_json = json.dumps(prompt, indent=2, ensure_ascii=False)
    
    report_content = f"""# 📊 Informe: {nombre}

**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}  
**Viabilidad:** {viabilidad}  
**Scores:** Gen {score_gen}/100 | Crit {score_crit}/100 | Promedio {score_promedio:.0f}/100

---

## 🎯 Resumen

{idea.get('descripcion_corta', '')}

**Problema:** {idea.get('problema', '')}

**Solución:** {idea.get('solucion', '')}

---

## 💡 Propuesta de Valor

{idea.get('propuesta_valor', '')}

**Recomendación:** {recomendacion}

---

## 👥 Mercado: {idea.get('mercado_objetivo', '')}

## 🏢 Competencia

"""
    for comp in idea.get('competencia', []):
        report_content += f"- {comp}\n"
    
    report_content += f"""
**Fortalezas:**
"""
    for f in critique.get('fortalezas', []):
        report_content += f"- {f}\n"
    
    report_content += f"""
**Debilidades:**
"""
    for d in critique.get('debilidades', []):
        report_content += f"- {d}\n"
    
    report_content += f"""
---

## 💰 Monetización

{idea.get('monetizacion', '')}

**Proyecciones:**
- Mes 3: €{ing_m3}
- Mes 6: €{ing_m6}
- Mes 12: €{ing_m12}

---

## 🚨 Riesgos

"""
    for i, riesgo in enumerate(critique.get('riesgos_mayores', []), 1):
        report_content += f"{i}. {riesgo}\n"
    
    report_content += f"""
---

## 🎯 Veredicto

{critique.get('veredicto_honesto', 'Validar con usuarios reales')}

**Probabilidad éxito:** {prob_exito}

---

## 🤖 Prompt IA

```json
{prompt_json}
Usa en Cursor AI / v0.dev / Bolt.new

Sistema Multi-Agente • €0/mes
"""

text
with open(report_file, 'w', encoding='utf-8') as f:
    f.write(report_content)

print(f"✅ Informe: {report_file}")
return slug
if name == "main":
test_idea = {"nombre": "Test", "descripcion_corta": "Test", "problema": "Test", "solucion": "Test", "propuesta_valor": "Test", "mercado_objetivo": "Devs", "competencia": ["C1"], "diferenciacion": "Test", "monetizacion": "$19/mes", "tech_stack": ["Next.js"], "score_generador": 75}
test_critique = {"score_critico": 65, "fortalezas": ["F1"], "debilidades": ["D1"], "riesgos_mayores": ["R1"], "veredicto_honesto": "Test", "probabilidad_exito": "50%"}
generate_report(test_idea, test_critique)
