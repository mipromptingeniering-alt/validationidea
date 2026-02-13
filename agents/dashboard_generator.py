import os
import json
from datetime import datetime

def load_ideas_data():
    """Carga todas las ideas desde CSV"""
    csv_file = 'data/ideas-validadas.csv'
    ideas = []
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()[1:]  # Skip header
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) >= 8:
                    ideas.append({
                        'timestamp': parts[0],
                        'nombre': parts[1],
                        'descripcion': parts[2],
                        'score_gen': int(parts[3]),
                        'score_crit': int(parts[4]),
                        'tipo': parts[5],
                        'dificultad': parts[6],
                        'fingerprint': parts[7]
                    })
    
    return ideas

def load_rejected_ideas():
    """Carga ideas rechazadas"""
    rejected_file = 'data/rejected_ideas.json'
    if os.path.exists(rejected_file):
        with open(rejected_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def calculate_stats(ideas, rejected):
    """Calcula estadísticas para gráficas"""
    total_ideas = len(ideas)
    total_rejected = len(rejected)
    total_generated = total_ideas + total_rejected
    
    # Score promedio
    avg_score_gen = sum(i['score_gen'] for i in ideas) / total_ideas if total_ideas > 0 else 0
    avg_score_crit = sum(i['score_crit'] for i in ideas) / total_ideas if total_ideas > 0 else 0
    
    # Tasa aprobación
    approval_rate = (total_ideas / total_generated * 100) if total_generated > 0 else 0
    
    # Ideas por día (últimos 7 días)
    from collections import defaultdict
    ideas_per_day = defaultdict(int)
    for idea in ideas:
        date = idea['timestamp'][:10]  # YYYY-MM-DD
        ideas_per_day[date] += 1
    
    # Últimas 7 fechas
    dates = sorted(ideas_per_day.keys())[-7:]
    counts = [ideas_per_day[d] for d in dates]
    
    # Scores evolución (últimas 10 ideas)
    recent_ideas = ideas[-10:] if len(ideas) >= 10 else ideas
    scores_gen = [i['score_gen'] for i in recent_ideas]
    scores_crit = [i['score_crit'] for i in recent_ideas]
    nombres = [i['nombre'] for i in recent_ideas]
    
    return {
        'total_ideas': total_ideas,
        'total_rejected': total_rejected,
        'total_generated': total_generated,
        'avg_score_gen': round(avg_score_gen, 1),
        'avg_score_crit': round(avg_score_crit, 1),
        'approval_rate': round(approval_rate, 1),
        'dates': dates,
        'counts': counts,
        'scores_gen': scores_gen,
        'scores_crit': scores_crit,
        'nombres': nombres
    }

def generate_dashboard():
    """Genera dashboard HTML con gráficas interactivas"""
    
    ideas = load_ideas_data()
    rejected = load_rejected_ideas()
    stats = calculate_stats(ideas, rejected)
    
    # Preparar datos para gráficas
    dates_json = json.dumps(stats['dates'])
    counts_json = json.dumps(stats['counts'])
    scores_gen_json = json.dumps(stats['scores_gen'])
    scores_crit_json = json.dumps(stats['scores_crit'])
    nombres_json = json.dumps(stats['nombres'])
    
    # Cards HTML de ideas
    ideas_html = ""
    for idea in reversed(ideas[-6:]):  # Últimas 6
        slug = idea['nombre'].lower().replace(' ', '-')
        ideas_html += f"""
        <div class="idea-card">
            <h3>{idea['nombre']}</h3>
            <p>{idea['descripcion'][:100]}...</p>
            <div class="badges">
                <span class="badge badge-gen">Gen: {idea['score_gen']}</span>
                <span class="badge badge-crit">Crit: {idea['score_crit']}</span>
                <span class="badge badge-diff">{idea['dificultad']}</span>
            </div>
            <div class="actions">
                <a href="{slug}.html" class="btn btn-primary">Ver Landing</a>
                <a href="../reports/{slug}.html" class="btn btn-secondary">Informe</a>
            </div>
        </div>
        """
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dashboard - Ideas Validadas</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        
        .container {{
            max-width: 1400px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 3rem;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 3rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            text-align: center;
        }}
        
        .stat-card h3 {{
            color: #667eea;
            font-size: 1rem;
            margin-bottom: 1rem;
        }}
        
        .stat-card .value {{
            font-size: 3rem;
            font-weight: bold;
            color: #333;
        }}
        
        .stat-card .label {{
            color: #666;
            font-size: 0.9rem;
            margin-top: 0.5rem;
        }}
        
        .charts-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
            gap: 2rem;
            margin-bottom: 3rem;
        }}
        
        .chart-card {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        
        .chart-card h3 {{
            color: #667eea;
            margin-bottom: 1.5rem;
            font-size: 1.3rem;
        }}
        
        .ideas-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 1.5rem;
        }}
        
        .idea-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .idea-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0,0,0,0.15);
        }}
        
        .idea-card h3 {{
            color: #667eea;
            margin-bottom: 0.5rem;
            font-size: 1.3rem;
        }}
        
        .idea-card p {{
            color: #666;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}
        
        .badges {{
            display: flex;
            gap: 0.5rem;
            margin-bottom: 1rem;
            flex-wrap: wrap;
        }}
        
        .badge {{
            padding: 0.3rem 0.8rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .badge-gen {{
            background: #d4edda;
            color: #155724;
        }}
        
        .badge-crit {{
            background: #d1ecf1;
            color: #0c5460;
        }}
        
        .badge-diff {{
            background: #fff3cd;
            color: #856404;
        }}
        
        .actions {{
            display: flex;
            gap: 0.5rem;
        }}
        
        .btn {{
            flex: 1;
            padding: 0.7rem;
            border-radius: 8px;
            text-decoration: none;
            text-align: center;
            font-weight: 600;
            transition: 0.3s;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
        }}
        
        .btn-secondary {{
            background: #f8f9fa;
            color: #667eea;
            border: 2px solid #667eea;
        }}
        
        .btn-secondary:hover {{
            background: #667eea;
            color: white;
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .charts-grid {{
                grid-template-columns: 1fr;
            }}
            
            .ideas-grid {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 Dashboard Ideas Validadas</h1>
            <p>Sistema Multi-Agente de Generación y Validación</p>
            <p style="font-size: 0.9rem; margin-top: 0.5rem;">Actualizado: {datetime.now().strftime('%d/%m/%Y %H:%M')}</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <h3>Ideas Publicadas</h3>
                <div class="value">{stats['total_ideas']}</div>
                <div class="label">Aprobadas y validadas</div>
            </div>
            
            <div class="stat-card">
                <h3>Ideas Rechazadas</h3>
                <div class="value">{stats['total_rejected']}</div>
                <div class="label">No superaron validación</div>
            </div>
            
            <div class="stat-card">
                <h3>Tasa Aprobación</h3>
                <div class="value">{stats['approval_rate']}%</div>
                <div class="label">De {stats['total_generated']} generadas</div>
            </div>
            
            <div class="stat-card">
                <h3>Score Promedio</h3>
                <div class="value">{int((stats['avg_score_gen'] + stats['avg_score_crit'])/2)}</div>
                <div class="label">Gen: {stats['avg_score_gen']} | Crit: {stats['avg_score_crit']}</div>
            </div>
        </div>
        
        <div class="charts-grid">
            <div class="chart-card">
                <h3>📊 Ideas por Día (Últimos 7 días)</h3>
                <canvas id="ideasPerDay"></canvas>
            </div>
            
            <div class="chart-card">
                <h3>📈 Evolución Scores (Últimas 10 ideas)</h3>
                <canvas id="scoresEvolution"></canvas>
            </div>
        </div>
        
        <h2 style="color: white; margin-bottom: 2rem; font-size: 2rem;">💡 Últimas Ideas Publicadas</h2>
        
        <div class="ideas-grid">
            {ideas_html}
        </div>
    </div>
    
    <script>
        // Gráfica 1: Ideas por día
        new Chart(document.getElementById('ideasPerDay'), {{
            type: 'bar',
            data: {{
                labels: {dates_json},
                datasets: [{{
                    label: 'Ideas Publicadas',
                    data: {counts_json},
                    backgroundColor: 'rgba(102, 126, 234, 0.8)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2
                }}]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        ticks: {{
                            stepSize: 1
                        }}
                    }}
                }}
            }}
        }});
        
        // Gráfica 2: Evolución scores
        new Chart(document.getElementById('scoresEvolution'), {{
            type: 'line',
            data: {{
                labels: {nombres_json},
                datasets: [
                    {{
                        label: 'Score Generador',
                        data: {scores_gen_json},
                        borderColor: 'rgba(40, 167, 69, 1)',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4
                    }},
                    {{
                        label: 'Score Crítico',
                        data: {scores_crit_json},
                        borderColor: 'rgba(0, 123, 255, 1)',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        tension: 0.4
                    }}
                ]
            }},
            options: {{
                responsive: true,
                scales: {{
                    y: {{
                        beginAtZero: true,
                        max: 100
                    }}
                }}
            }}
        }});
    </script>
</body>
</html>"""
    
    # Guardar
    output_dir = 'landing-pages'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f'{output_dir}/index.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Dashboard con gráficas generado: {filename}")
    return filename


if __name__ == "__main__":
    generate_dashboard()
