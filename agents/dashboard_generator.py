import os
import json
from datetime import datetime
import csv

def generate_dashboard():
    """Genera dashboard con botones funcionando + descarga CSV"""
    
    # Cargar ideas
    ideas = []
    csv_file = 'data/ideas-validadas.csv'
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ideas.append(row)
    
    # HTML
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ValidationIdea - Dashboard</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
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
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 1.5rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }}
        
        .stat-card h3 {{
            font-size: 0.9rem;
            color: #666;
            margin-bottom: 0.5rem;
        }}
        
        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: bold;
            color: #667eea;
        }}
        
        .download-btn {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 1rem 2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: bold;
            font-size: 1.1rem;
            margin-bottom: 2rem;
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
        }}
        
        .download-btn:hover {{
            background: #218838;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
        }}
        
        .ideas-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 2rem;
        }}
        
        .idea-card {{
            background: white;
            border-radius: 12px;
            padding: 1.5rem;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            transition: transform 0.3s;
        }}
        
        .idea-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(0,0,0,0.15);
        }}
        
        .idea-header {{
            margin-bottom: 1rem;
        }}
        
        .idea-name {{
            font-size: 1.5rem;
            color: #667eea;
            margin-bottom: 0.5rem;
        }}
        
        .idea-category {{
            display: inline-block;
            background: #e3f2fd;
            color: #1976d2;
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .idea-description {{
            color: #666;
            margin-bottom: 1rem;
            line-height: 1.5;
        }}
        
        .idea-meta {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 1rem;
            font-size: 0.9rem;
            color: #999;
        }}
        
        .score {{
            font-weight: bold;
            color: #28a745;
        }}
        
        .actions {{
            display: flex;
            gap: 0.5rem;
        }}
        
        .btn {{
            flex: 1;
            padding: 0.75rem;
            border: none;
            border-radius: 8px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: inline-block;
            text-align: center;
        }}
        
        .btn-primary {{
            background: #667eea;
            color: white;
        }}
        
        .btn-primary:hover {{
            background: #5568d3;
        }}
        
        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #e0e0e0;
        }}
        
        @media (max-width: 768px) {{
            .ideas-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ValidationIdea</h1>
            <p>Dashboard de Ideas SaaS Validadas con IA</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>Total Ideas</h3>
                <div class="number">{len(ideas)}</div>
            </div>
            <div class="stat-card">
                <h3>Esta Semana</h3>
                <div class="number">{len([i for i in ideas if 'timestamp' in i])}</div>
            </div>
            <div class="stat-card">
                <h3>Score Promedio</h3>
                <div class="number">{int(sum([int(i.get('score_promedio', 70)) for i in ideas]) / len(ideas)) if ideas else 0}</div>
            </div>
        </div>
        
        <a href="data/ideas-validadas.csv" download="ideas-validadas.csv" class="download-btn">
            📥 Descargar CSV Completo
        </a>
        
        <div class="ideas-grid">
"""
    
    # Cards de ideas
    for idea in ideas:
        slug = idea.get('slug', 'idea')
        nombre = idea.get('nombre', 'Sin nombre')
        descripcion = idea.get('descripcion_corta', 'Sin descripción')[:150]
        categoria = idea.get('categoria', 'SaaS')
        score = idea.get('score_promedio', '70')
        timestamp = idea.get('timestamp', datetime.now().strftime('%Y-%m-%d'))
        
        # Rutas correctas
        landing_path = f"landing-pages/{slug}/index.html"
        informe_path = f"informes/{slug}/informe-{slug}.md"
        
        html += f"""
            <div class="idea-card">
                <div class="idea-header">
                    <h2 class="idea-name">{nombre}</h2>
                    <span class="idea-category">{categoria}</span>
                </div>
                
                <p class="idea-description">{descripcion}...</p>
                
                <div class="idea-meta">
                    <span>Score: <span class="score">{score}</span></span>
                    <span>{timestamp}</span>
                </div>
                
                <div class="actions">
                    <a href="{landing_path}" class="btn btn-primary" target="_blank">
                        🌐 Ver Landing
                    </a>
                    <a href="{informe_path}" class="btn btn-secondary" target="_blank">
                        📊 Ver Informe
                    </a>
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
    return output_file


if __name__ == "__main__":
    generate_dashboard()
