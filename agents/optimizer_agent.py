import os
import json
from datetime import datetime

def load_published_ideas():
    csv_file = 'data/ideas-validadas.csv'
    if not os.path.exists(csv_file):
        return []
    ideas = []
    with open(csv_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()[1:]
        for line in lines:
            parts = line.strip().split(',')
            if len(parts) >= 5:
                ideas.append({
                    'nombre': parts[1],
                    'score_gen': int(parts[3]),
                    'score_crit': int(parts[4])
                })
    return ideas

def load_rejected_ideas():
    rejected_file = 'data/rejected_ideas.json'
    if not os.path.exists(rejected_file):
        return []
    with open(rejected_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_performance():
    published = load_published_ideas()
    rejected = load_rejected_ideas()
    total = len(published) + len(rejected)
    if total == 0:
        return None
    approval_rate = (len(published) / total) * 100
    avg_score_gen = sum([i['score_gen'] for i in published]) / len(published) if published else 0
    avg_score_crit = sum([i['score_crit'] for i in published]) / len(published) if published else 0
    return {
        'total_ideas': total,
        'published': len(published),
        'rejected': len(rejected),
        'approval_rate': approval_rate,
        'avg_score_gen': avg_score_gen,
        'avg_score_crit': avg_score_crit
    }

def get_optimization_insights(stats):
    insights = []
    if stats['approval_rate'] < 30:
        insights.append("⚠️ Tasa de aprobación baja (<30%). Considera ajustar umbrales o mejorar prompts del generador.")
    elif stats['approval_rate'] > 70:
        insights.append("✅ Tasa de aprobación alta (>70%). El sistema funciona bien.")
    if stats['avg_score_gen'] < 70:
        insights.append("🔧 Score promedio del generador bajo. Revisa prompt de generator_agent.")
    if stats['avg_score_crit'] < 70:
        insights.append("🔧 Score promedio del crítico bajo. Ideas publicadas tienen baja calidad según crítico.")
    if abs(stats['avg_score_gen'] - stats['avg_score_crit']) > 15:
        insights.append("⚖️ Gran diferencia entre scores. Generador y crítico no están alineados.")
    if not insights:
        insights.append("🎯 Sistema optimizado. Todo funcionando correctamente.")
    return insights

def generate_optimization_report(stats):
    os.makedirs('reports', exist_ok=True)
    report_file = 'reports/optimization-report.md'
    insights = get_optimization_insights(stats)
    content = f"""# 🚀 Informe de Optimización del Sistema

**Generado:** {datetime.now().strftime('%d/%m/%Y %H:%M')}

---

## 📊 Estadísticas Generales

- **Total de ideas evaluadas:** {stats['total_ideas']}
- **Ideas publicadas:** {stats['published']}
- **Ideas rechazadas:** {stats['rejected']}
- **Tasa de aprobación:** {stats['approval_rate']:.1f}%

---

## 🎯 Calidad Promedio (Ideas Publicadas)

- **Score Generador:** {stats['avg_score_gen']:.1f}/100
- **Score Crítico:** {stats['avg_score_crit']:.1f}/100
- **Score Promedio:** {(stats['avg_score_gen'] + stats['avg_score_crit']) / 2:.1f}/100

---

## 💡 Insights y Recomendaciones

"""
    for insight in insights:
        content += f"- {insight}\n"
    content += f"""
---

## 🔧 Acciones Sugeridas

1. **Si tasa de aprobación <30%:**
   - Bajar threshold en `critic_agent.py` (línea ~50)
   - Mejorar creatividad en prompt de `generator_agent.py`

2. **Si scores bajos (<70):**
   - Revisar prompt del generador
   - Añadir más contexto de investigación

3. **Si diferencia de scores >15 puntos:**
   - Alinear criterios entre generador y crítico
   - Revisar lógica de scoring

4. **Optimización continua:**
   - Analizar `rejected_ideas.json` para patrones
   - Ajustar research topics en `researcher_agent.py`

---

**Sistema:** Multi-Agente de Validación de Ideas  
**Modelo:** Groq Llama 3.3 70B (Gratis)  
**Costo:** $0/mes
"""
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Informe de optimización generado: {report_file}")

def run():
    print("\n🚀 Ejecutando análisis de optimización...")
    stats = analyze_performance()
    if not stats:
        print("⚠️ No hay suficientes datos para optimizar (mínimo 1 idea)")
        return
    print(f"\n📊 Estadísticas:")
    print(f"   - Total evaluadas: {stats['total_ideas']}")
    print(f"   - Publicadas: {stats['published']}")
    print(f"   - Rechazadas: {stats['rejected']}")
    print(f"   - Tasa aprobación: {stats['approval_rate']:.1f}%")
    print(f"   - Score promedio: {(stats['avg_score_gen'] + stats['avg_score_crit']) / 2:.1f}/100")
    generate_optimization_report(stats)
    insights = get_optimization_insights(stats)
    print("\n💡 Insights:")
    for insight in insights:
        print(f"   {insight}")

if __name__ == "__main__":
    run()
