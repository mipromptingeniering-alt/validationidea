import os
import csv
from datetime import datetime

def generate_dashboard():
    """Genera dashboard con botones funcionando correctamente"""
    
    print("\n📊 Generando dashboard...")
    
    # Cargar ideas
    ideas = []
    csv_file = 'data/ideas-validadas.csv'
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ideas.append(row)
    
    # Estadísticas
    total_ideas = len(ideas)
    
    # Calcular ideas esta semana
    today = datetime.now()
    this_week = sum(1 for idea in ideas if idea.get('timestamp', '').startswith(today.strftime('%Y-%m-%d')))
    
    # Score promedio
    scores = [int(idea.get('score_promedio', 70)) for idea in ideas if idea.get('score_promedio')]
    avg_score = int(sum(scores) / len(scores)) if scores else 0
    
    # HTML completo
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
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
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
            animation: fadeIn 0.6s ease-in;
        }}
        
        .header h1 {{
            font-size: 3.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.2rem;
            opacity: 0.9;
        }}
        
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 1.5rem;
            margin-bottom: 2rem;
        }}
        
        .stat-card {{
            background: white;
            padding: 2rem;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
            transition: transform 0.3s, box-shadow 0.3s;
            animation: slideUp 0.6s ease-out;
        }}
        
        .stat-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.2);
        }}
        
        .stat-card h3 {{
            font-size: 0.95rem;
            color: #666;
            margin-bottom: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        
        .stat-card .number {{
            font-size: 3rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
        }}
        
        .download-section {{
            text-align: center;
            margin-bottom: 2rem;
        }}
        
        .download-btn {{
            display: inline-flex;
            align-items: center;
            gap: 0.75rem;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            padding: 1.25rem 2.5rem;
            border-radius: 12px;
            text-decoration: none;
            font-weight: 600;
            font-size: 1.1rem;
            transition: all 0.3s;
            box-shadow: 0 4px 16px rgba(40, 167, 69, 0.3);
        }}
        
        .download-btn:hover {{
            transform: translateY(-3px);
            box-shadow: 0 8px 24px rgba(40, 167, 69, 0.4);
        }}
        
        .ideas-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(380px, 1fr));
            gap: 2rem;
            animation: fadeIn 0.8s ease-in;
        }}
        
        .idea-card {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
            transition: all 0.3s;
            position: relative;
            overflow: hidden;
        }}
        
        .idea-card::before {{
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            height: 4px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }}
        
        .idea-card:hover {{
            transform: translateY(-8px);
            box-shadow: 0 16px 40px rgba(0,0,0,0.2);
        }}
        
        .idea-header {{
            margin-bottom: 1.25rem;
        }}
        
        .idea-name {{
            font-size: 1.65rem;
            color: #667eea;
            margin-bottom: 0.75rem;
            font-weight: 700;
            line-height: 1.3;
        }}
        
        .idea-category {{
            display: inline-block;
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            color: #1976d2;
            padding: 0.4rem 1rem;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .idea-description {{
            color: #555;
            margin: 1.25rem 0;
            line-height: 1.7;
            font-size: 0.95rem;
        }}
        
        .idea-meta {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding: 0.75rem;
            background: #f8f9fa;
            border-radius: 8px;
            font-size: 0.9rem;
        }}
        
        .score {{
            font-weight: bold;
            font-size: 1.1rem;
            color: #28a745;
        }}
        
        .date {{
            color: #888;
        }}
        
        .actions {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 0.75rem;
        }}
        
        .btn {{
            padding: 0.9rem 1.25rem;
            border: none;
            border-radius: 10px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s;
            text-decoration: none;
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.5rem;
            font-size: 0.95rem;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #e0e0e0;
            transform: translateY(-2px);
        }}
        
        .empty-state {{
            text-align: center;
            color: white;
            padding: 4rem 2rem;
        }}
        
        .empty-state h2 {{
            font-size: 2rem;
            margin-bottom: 1rem;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes slideUp {{
            from {{
                opacity: 0;
                transform: translateY(20px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @media (max-width: 768px) {{
            .ideas-grid {{
                grid-template-columns: 1fr;
            }}
            
            .header h1 {{
                font-size: 2.5rem;
            }}
            
            .actions {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ValidationIdea</h1>
            <p>Sistema Multi-Agente IA para Validación de Ideas SaaS</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <h3>💡 Total Ideas</h3>
                <div class="number">{total_ideas}</div>
            </div>
            <div class="stat-card">
                <h3>📅 Esta Semana</h3>
                <div class="number">{this_week}</div>
            </div>
            <div class="stat-card">
                <h3>⭐ Score Promedio</h3>
                <div class="number">{avg_score}</div>
            </div>
        </div>
        
        <div class="download-section">
            <a href="../data/ideas-validadas.csv" download="ideas-validadas.csv" class="download-btn">
                📥 Descargar CSV Completo
            </a>
        </div>
        
        <div class="ideas-grid">
"""
    
    # Cards de ideas
    if not ideas:
        html += """
            <div class="empty-state">
                <h2>🎯 Aún no hay ideas generadas</h2>
                <p>El sistema está trabajando en generar las primeras ideas...</p>
            </div>
"""
    else:
        for idea in ideas:
            slug = idea.get('slug', 'idea')
            nombre = idea.get('nombre', 'Sin nombre')
            descripcion = idea.get('descripcion_corta', 'Sin descripción')[:180]
            categoria = idea.get('categoria', 'SaaS')
            score = idea.get('score_promedio', '70')
            timestamp = idea.get('timestamp', datetime.now().strftime('%Y-%m-%d'))
            
            # Rutas CORREGIDAS
            landing_url = f"../landing-pages/{slug}/index.html"
            informe_url = f"../informes/{slug}/informe-{slug}.md"
            
            html += f"""
            <div class="idea-card">
                <div class="idea-header">
                    <h2 class="idea-name">{nombre}</h2>
                    <span class="idea-category">{categoria}</span>
                </div>
                
                <p class="idea-description">{descripcion}...</p>
                
                <div class="idea-meta">
                    <span>Score: <span class="score">{score}</span></span>
                    <span class="date">{timestamp}</span>
                </div>
                
                <div class="actions">
                    <a href="{landing_url}" class="btn btn-primary" target="_blank">
                        🌐 Ver Landing
                    </a>
                    <a href="{informe_url}" class="btn btn-secondary" target="_blank">
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
    print(f"📊 {len(ideas)} ideas mostradas")
    
    return output_file


if __name__ == "__main__":
    generate_dashboard()
