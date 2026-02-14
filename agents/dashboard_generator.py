import os
import csv
from datetime import datetime

def generate_dashboard():
    """Genera dashboard con links correctos"""
    
    print("\n📊 Generando dashboard...")
    
    # Cargar ideas
    ideas = []
    csv_file = 'data/ideas-validadas.csv'
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ideas.append(row)
    
    # Ordenar por fecha (más nuevas primero)
    ideas.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Estadísticas
    total_ideas = len(ideas)
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for idea in ideas if idea.get('timestamp', '').startswith(today))
    
    scores = []
    for idea in ideas:
        try:
            score = float(idea.get('score_promedio', 0))
            if score > 0:
                scores.append(score)
        except:
            pass
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    
    # HTML
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ValidationIdea - Dashboard</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 2rem;
        }}
        .container {{ max-width: 1200px; margin: 0 auto; }}
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 2rem;
        }}
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1rem;
            margin-bottom: 2rem;
        }}
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            text-align: center;
        }}
        .stat-card h3 {{
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 0.5rem;
            text-transform: uppercase;
        }}
        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        .download-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.5rem;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 1rem 2rem;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            margin-bottom: 2rem;
        }}
        .ideas-container {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }}
        .idea-item {{
            display: flex;
            align-items: center;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #667eea;
        }}
        .idea-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            background: #fff;
        }}
        .idea-number {{
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            margin-right: 1.5rem;
        }}
        .idea-content {{ flex: 1; }}
        .idea-title {{
            font-size: 1.3rem;
            color: #333;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        .idea-meta {{
            display: flex;
            gap: 1rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }}
        .score {{ font-weight: bold; color: #28a745; }}
        .btn {{
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
            margin-right: 0.5rem;
        }}
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }}
        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ValidationIdea</h1>
            <p>Sistema Multi-Agente IA - Productos Monetizables</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>💡 Total Ideas</h3>
                <div class="number">{total_ideas}</div>
            </div>
            <div class="stat-card">
                <h3>📅 Hoy</h3>
                <div class="number">{today_count}</div>
            </div>
            <div class="stat-card">
                <h3>⭐ Score Medio</h3>
                <div class="number">{avg_score}</div>
            </div>
        </div>
        
        <div style="text-align: center; margin-bottom: 2rem;">
            <a href="../data/ideas-validadas.csv" download class="download-btn">
                📥 Descargar CSV
            </a>
        </div>
        
        <div class="ideas-container">
"""
    
    if not ideas:
        html += '<p style="text-align:center;padding:2rem;color:#999;">Aún no hay ideas generadas</p>'
    else:
        for idx, idea in enumerate(ideas, 1):
            slug = idea.get('slug', 'idea')
            nombre = idea.get('nombre', 'Sin nombre')
            descripcion = idea.get('descripcion_corta', '')[:150]
            
            try:
                score = int(float(idea.get('score_promedio', 70)))
            except:
                score = 70
            
            timestamp = idea.get('timestamp', '')
            
            # URLS CORREGIDAS
            landing_url = f"../landing-pages/{slug}/index.html"
            informe_url = f"../informes/{slug}/informe-{slug}.md"  # ← CORRECTO AHORA
            
            html += f"""
            <div class="idea-item">
                <div class="idea-number">{idx}</div>
                <div class="idea-content">
                    <div class="idea-title">{nombre}</div>
                    <div class="idea-meta">
                        <span>Score: <span class="score">{score}</span></span>
                        <span style="color:#999;">{timestamp[:16]}</span>
                    </div>
                    <p style="color:#666;margin-bottom:1rem;">{descripcion}</p>
                    <div>
                        <a href="{landing_url}" class="btn btn-primary" target="_blank">🌐 Landing</a>
                        <a href="{informe_url}" class="btn btn-secondary" target="_blank">📊 Informe</a>
                    </div>
                </div>
            </div>
"""
    
    html += """
        </div>
    </div>
</body>
</html>
"""
    
    # Guardar
    output_file = 'dashboard/index.html'
    os.makedirs('dashboard', exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Dashboard generado: {output_file}")
    print(f"📊 {len(ideas)} ideas (más nuevas primero)")
    
    return output_file


if __name__ == "__main__":
    generate_dashboard()
