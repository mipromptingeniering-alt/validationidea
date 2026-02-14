import os
import csv
from datetime import datetime
import json

def load_published_ideas():
    """Carga ideas publicadas desde CSV de forma segura"""
    ideas = []
    csv_file = 'data/ideas-validadas.csv'
    
    if not os.path.exists(csv_file):
        return ideas
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    # Convertir scores a float primero, luego a int
                    score_gen = row.get('score_generador', '0')
                    score_crit = row.get('score_critico', '0')
                    score_prom = row.get('score_promedio', '0')
                    
                    # Limpiar y convertir de forma segura
                    score_gen = int(float(str(score_gen).strip())) if score_gen else 0
                    score_crit = int(float(str(score_crit).strip())) if score_crit else 0
                    score_prom = int(float(str(score_prom).strip())) if score_prom else 0
                    
                    ideas.append({
                        'nombre': str(row.get('nombre', '')).strip(),
                        'score_gen': score_gen,
                        'score_crit': score_crit,
                        'score_promedio': score_prom,
                        'timestamp': str(row.get('timestamp', '')).strip()
                    })
                except (ValueError, TypeError) as e:
                    print(f"⚠️  Error parseando fila: {e}")
                    continue
    
    except Exception as e:
        print(f"⚠️  Error leyendo CSV: {e}")
    
    return ideas

def analyze_performance():
    """Analiza rendimiento del sistema"""
    published = load_published_ideas()
    
    if not published:
        return {
            'total': 0,
            'avg_score': 0,
            'approval_rate': 0,
            'top_performers': []
        }
    
    total = len(published)
    
    # Calcular score promedio de forma segura
    scores = [idea['score_promedio'] for idea in published if idea['score_promedio'] > 0]
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    
    # Tasa aprobación (score > 60)
    approved = sum(1 for idea in published if idea['score_promedio'] > 60)
    approval_rate = (approved / total * 100) if total > 0 else 0
    
    # Top performers
    top_performers = sorted(
        published,
        key=lambda x: x['score_promedio'],
        reverse=True
    )[:5]
    
    stats = {
        'total': total,
        'avg_score': avg_score,
        'approval_rate': round(approval_rate, 1),
        'top_performers': [
            {
                'nombre': idea['nombre'],
                'score': idea['score_promedio']
            }
            for idea in top_performers
        ]
    }
    
    return stats

def suggest_improvements(stats):
    """Sugiere mejoras basadas en estadísticas"""
    suggestions = []
    
    avg_score = stats.get('avg_score', 0)
    approval_rate = stats.get('approval_rate', 0)
    
    # Análisis score promedio
    if avg_score < 60:
        suggestions.append({
            'tipo': 'CRITICAL',
            'area': 'Generador',
            'sugerencia': 'Score promedio muy bajo (<60). Necesita ajustar temperatura o prompts.',
            'accion': 'Revisar config/generator_config.json - aumentar creativity_boost'
        })
    elif avg_score < 70:
        suggestions.append({
            'tipo': 'WARNING',
            'area': 'Generador',
            'sugerencia': 'Score promedio bajo (60-70). Ideas funcionan pero pueden mejorar.',
            'accion': 'Añadir más nichos específicos o refinar prompts'
        })
    else:
        suggestions.append({
            'tipo': 'SUCCESS',
            'area': 'Generador',
            'sugerencia': f'Score promedio excelente ({avg_score}). Sistema funciona bien.',
            'accion': 'Mantener estrategia actual'
        })
    
    # Análisis tasa aprobación
    if approval_rate < 50:
        suggestions.append({
            'tipo': 'CRITICAL',
            'area': 'Crítico',
            'sugerencia': f'Tasa aprobación baja ({approval_rate}%). Rechaza demasiado.',
            'accion': 'Reducir score_minimo en config/critic_config.json'
        })
    elif approval_rate < 70:
        suggestions.append({
            'tipo': 'WARNING',
            'area': 'Crítico',
            'sugerencia': f'Tasa aprobación media ({approval_rate}%).',
            'accion': 'Revisar criterios de evaluación'
        })
    else:
        suggestions.append({
            'tipo': 'SUCCESS',
            'area': 'Crítico',
            'sugerencia': f'Tasa aprobación óptima ({approval_rate}%).',
            'accion': 'Criterios bien calibrados'
        })
    
    # Análisis total ideas
    total = stats.get('total', 0)
    if total < 10:
        suggestions.append({
            'tipo': 'INFO',
            'area': 'Sistema',
            'sugerencia': f'Solo {total} ideas generadas. Necesita más datos para análisis.',
            'accion': 'Dejar ejecutar más iteraciones (objetivo: 50+ ideas)'
        })
    
    return suggestions

def generate_optimization_report(stats, suggestions):
    """Genera reporte de optimización"""
    
    report = f"""# 🚀 REPORTE DE OPTIMIZACIÓN

**Generado:** {datetime.now().strftime('%Y-%m-%d %H:%M')}

---

## 📊 MÉTRICAS ACTUALES

- **Total Ideas:** {stats['total']}
- **Score Promedio:** {stats['avg_score']}/100
- **Tasa Aprobación:** {stats['approval_rate']}%

---

## 🏆 TOP 5 IDEAS

"""
    
    for i, idea in enumerate(stats['top_performers'], 1):
        report += f"{i}. **{idea['nombre']}** - Score: {idea['score']}\n"
    
    report += "\n---\n\n## 💡 SUGERENCIAS DE MEJORA\n\n"
    
    for sugg in suggestions:
        emoji = {
            'CRITICAL': '🔴',
            'WARNING': '⚠️',
            'SUCCESS': '✅',
            'INFO': 'ℹ️'
        }.get(sugg['tipo'], '•')
        
        report += f"""### {emoji} {sugg['tipo']} - {sugg['area']}

**{sugg['sugerencia']}**

**Acción:** {sugg['accion']}

---

"""
    
    # Guardar reporte
    os.makedirs('reports', exist_ok=True)
    report_file = f"reports/optimization-{datetime.now().strftime('%Y%m%d-%H%M')}.md"
    
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"✅ Reporte guardado: {report_file}")
    
    return report_file

def run():
    """Función principal del optimizador"""
    print("\n🚀 Ejecutando análisis de optimización...")
    
    try:
        # Analizar rendimiento
        stats = analyze_performance()
        
        print(f"\n📊 Estadísticas:")
        print(f"   Total ideas: {stats['total']}")
        print(f"   Score promedio: {stats['avg_score']}")
        print(f"   Tasa aprobación: {stats['approval_rate']}%")
        
        # Generar sugerencias
        suggestions = suggest_improvements(stats)
        
        print(f"\n💡 Sugerencias generadas: {len(suggestions)}")
        
        # Generar reporte
        report_file = generate_optimization_report(stats, suggestions)
        
        print(f"✅ Optimización completada\n")
        
        return {
            'stats': stats,
            'suggestions': suggestions,
            'report': report_file
        }
    
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    result = run()
    if result:
        print(json.dumps(result['stats'], indent=2))
