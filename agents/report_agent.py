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
        viabilidad = "ALTA"
    elif score_promedio >= 70:
        viabilidad = "MEDIA"
    else:
        viabilidad = "BAJA"
    tech_stack_str = ', '.join(idea.get('tech_stack', ['Next.js']))
    prompt = {"proyecto": idea.get('nombre', ''), "tech_stack": tech_stack_str}
    prompt_json = json.dumps(prompt, indent=2, ensure_ascii=False)
    report_content = f"""# Informe: {nombre}

Viabilidad: {viabilidad}
Scores: Gen {score_gen} Crit {score_crit} Promedio {score_promedio:.0f}

Resumen: {idea.get('descripcion_corta', '')}

Problema: {idea.get('problema', '')}

Solucion: {idea.get('solucion', '')}

Prompt IA:
{prompt_json}
"""
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report_content)
    print(f"Informe: {report_file}")
    return slug

if __name__ == "__main__":
    test_idea = {"nombre": "Test", "descripcion_corta": "Test", "problema": "Test", "solucion": "Test", "tech_stack": ["Next.js"], "score_generador": 75}
    test_critique = {"score_critico": 65}
    generate_report(test_idea, test_critique)
