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
    elif score_promedio >= 70:
        viabilidad = "MEDIA ⭐⭐"
        recomendacion = "Idea viable con riesgos manejables. Validar antes de invertir mucho tiempo."
    else:
        viabilidad = "BAJA ⭐"
        recomendacion = "Idea con riesgos significativos. Solo ejecutar si tienes ventaja única."
    
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

**¿Vale la pena?** {recomendacion}

---

**Generado por Sistema Multi-Agente**
"""
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    print(f"✅ Informe generado: {report_file}")
    return slug

if __name__ == "__main__":
    test_idea = {"nombre": "Test", "descripcion_corta": "Test", "problema": "Test", "solucion": "Test", "propuesta_valor": "Test", "mercado_objetivo": "Devs", "competencia": ["C1"], "diferenciacion": "Test", "monetizacion": "$19/mes", "tech_stack": ["Next.js"], "dificultad": "Media", "tiempo_estimado": "4 sem", "score_generador": 75}
    test_critique = {"score_critico": 65, "fortalezas": ["F1"], "debilidades": ["D1"], "riesgos_mayores": ["R1"], "veredicto_honesto": "Test", "probabilidad_exito": "50%"}
    generate_report(test_idea, test_critique)
