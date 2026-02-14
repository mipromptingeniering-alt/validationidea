import os
import csv
from datetime import datetime

def generate_dashboard():
    """Genera dashboard con vista lista, ideas nuevas arriba"""
    
    print("\n📊 Generando dashboard...")
    
    # Cargar ideas
    ideas = []
    csv_file = 'data/ideas-validadas.csv'
    
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                ideas.append(row)
    
    # ORDENAR POR TIMESTAMP DESC (más nuevas primero)
    ideas.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    # Estadísticas
    total_ideas = len(ideas)
    
    # Ideas hoy
    today = datetime.now().strftime('%Y-%m-%d')
    today_count = sum(1 for idea in ideas if idea.get('timestamp', '').startswith(today))
    
    # Score promedio
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
            max-width: 1200px;
            margin: 0 auto;
        }}
        
        .header {{
            text-align: center;
            color: white;
            margin-bottom: 2rem;
            animation: fadeIn 0.6s ease-in;
        }}
        
        .header h1 {{
            font-size: 3rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        }}
        
        .header p {{
            font-size: 1.1rem;
            opacity: 0.9;
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
            letter-spacing: 1px;
        }}
        
        .stat-card .number {{
            font-size: 2.5rem;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }}
        
        .download-section {{
            text-align: center;
            margin-bottom: 2rem;
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
            transition: all 0.3s;
            box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
        }}
        
        .download-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(40, 167, 69, 0.4);
        }}
        
        .ideas-container {{
            background: white;
            border-radius: 16px;
            padding: 2rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.15);
        }}
        
        .ideas-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.5rem;
            padding-bottom: 1rem;
            border-bottom: 2px solid #f0f0f0;
        }}
        
        .ideas-header h2 {{
            color: #667eea;
            font-size: 1.5rem;
        }}
        
        .ideas-count {{
            color: #888;
            font-size: 0.95rem;
        }}
        
        .idea-item {{
            display: flex;
            align-items: center;
            padding: 1.5rem;
            margin-bottom: 1rem;
            background: #f8f9fa;
            border-radius: 12px;
            border-left: 4px solid #667eea;
            transition: all 0.3s;
            position: relative;
        }}
        
        .idea-item:hover {{
            transform: translateX(5px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
            background: #fff;
        }}
        
        .idea-number {{
            flex-shrink: 0;
            width: 40px;
            height: 40px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            font-size: 1.1rem;
            margin-right: 1.5rem;
        }}
        
        .idea-content {{
            flex: 1;
            min-width: 0;
        }}
        
        .idea-title {{
            font-size: 1.3rem;
            color: #333;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }}
        
        .idea-meta {{
            display: flex;
            gap: 1.5rem;
            margin-bottom: 0.75rem;
            flex-wrap: wrap;
        }}
        
        .meta-item {{
            display: flex;
            align-items: center;
            gap: 0.3rem;
            font-size: 0.9rem;
            color: #666;
        }}
        
        .score {{
            font-weight: bold;
            color: #28a745;
            font-size: 1rem;
        }}
        
        .category {{
            background: linear-gradient(135deg, #e3f2fd, #bbdefb);
            color: #1976d2;
            padding: 0.3rem 0.8rem;
            border-radius: 15px;
            font-size: 0.85rem;
            font-weight: 600;
        }}
        
        .timestamp {{
            color: #999;
            font-size: 0.85rem;
        }}
        
        .new-badge {{
            background: #ff6b6b;
            color: white;
            padding: 0.2rem 0.6rem;
            border-radius: 10px;
            font-size: 0.75rem;
            font-weight: bold;
            text-transform: uppercase;
            animation: pulse 2s infinite;
        }}
        
        .idea-description {{
            color: #666;
            line-height: 1.6;
            margin-bottom: 1rem;
            font-size: 0.95rem;
        }}
        
        .idea-actions {{
            display: flex;
            gap: 0.75rem;
        }}
        
        .btn {{
            padding: 0.6rem 1.2rem;
            border-radius: 8px;
            text-decoration: none;
            font-weight: 600;
            font-size: 0.9rem;
            transition: all 0.3s;
            display: inline-flex;
            align-items: center;
            gap: 0.4rem;
        }}
        
        .btn-primary {{
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
        }}
        
        .btn-primary:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }}
        
        .btn-secondary {{
            background: #f0f0f0;
            color: #333;
        }}
        
        .btn-secondary:hover {{
            background: #e0e0e0;
        }}
        
        .empty-state {{
            text-align: center;
            padding: 4rem 2rem;
            color: #999;
        }}
        
        .empty-state h3 {{
            font-size: 1.5rem;
            margin-bottom: 0.5rem;
            color: #666;
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes pulse {{
            0%, 100% {{ opacity: 1; }}
            50% {{ opacity: 0.6; }}
        }}
        
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 2rem;
            }}
            
            .idea-item {{
                flex-direction: column;
                align-items: flex-start;
            }}
            
            .idea-number {{
                margin-bottom: 1rem;
            }}
            
            .idea-actions {{
                width: 100%;
                flex-direction: column;
            }}
            
            .btn {{
                width: 100%;
                justify-content: center;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🚀 ValidationIdea</h1>
            <p>Sistema Multi-Agente IA - Generación Automática de Ideas SaaS</p>
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
        
        <div class="download-section">
            <a href="../data/ideas-validadas.csv" download class="download-btn">
                📥 Descargar CSV Completo
            </a>
        </div>
        
        <div class="ideas-container">
            <div class="ideas-header">
                <h2>📋 Ideas Validadas</h2>
                <span class="ideas-count">{total_ideas} ideas • Ordenadas por fecha</span>
            </div>
"""
    
    if not ideas:
        html += """
            <div class="empty-state">
                <h3>🎯 Aún no hay ideas generadas</h3>
                <p>El sistema generará la primera idea en breve...</p>
            </div>
"""
    else:
        for idx, idea in enumerate(ideas, 1):
            slug = idea.get('slug', 'idea')
            nombre = idea.get('nombre', 'Sin nombre')
            descripcion = idea.get('descripcion_corta', 'Sin descripción')[:200]
            categoria = idea.get('categoria', 'SaaS')
            
            # Score seguro
            try:
                score = int(float(idea.get('score_promedio', 70)))
            except:
                score = 70
            
            timestamp = idea.get('timestamp', '')
            
            # Detectar si es de hoy (nueva)
            is_new = timestamp.startswith(today) if timestamp else False
            new_badge = '<span class="new-badge">Nuevo</span>' if is_new else ''
            
            # Formatear fecha
            try:
                dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                formatted_date = dt.strftime('%d/%m/%Y %H:%M')
            except:
                formatted_date = timestamp[:16] if timestamp else 'N/A'
            
            # URLs corregidas
            landing_url = f"../landing-pages/{slug}/index.html"
            informe_url = f"../informes/{slug}/informe-{slug}.md"
            
            html += f"""
            <div class="idea-item">
                <div class="idea-number">{idx}</div>
                
                <div class="idea-content">
                    <div class="idea-title">{nombre} {new_badge}</div>
                    
                    <div class="idea-meta">
                        <span class="meta-item">📊 Score: <span class="score">{score}</span></span>
                        <span class="category">{categoria}</span>
                        <span class="meta-item timestamp">🕐 {formatted_date}</span>
                    </div>
                    
                    <p class="idea-description">{descripcion}...</p>
                    
                    <div class="idea-actions">
                        <a href="{landing_url}" class="btn btn-primary" target="_blank">
                            🌐 Ver Landing
                        </a>
                        <a href="{informe_url}" class="btn btn-secondary" target="_blank">
                            📊 Ver Informe
                        </a>
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
