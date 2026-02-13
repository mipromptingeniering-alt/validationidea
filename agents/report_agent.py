import os
import json
from datetime import datetime

def generate_report(idea_data):
    """
    Genera informe técnico COMPLETO como HTML responsive
    """
    
    slug = idea_data.get('slug', 'idea')
    nombre = idea_data.get('nombre', 'Idea SaaS')
    descripcion = idea_data.get('descripcion', 'Una idea innovadora')
    descripcion_corta = idea_data.get('descripcion_corta', descripcion)
    problema = idea_data.get('problema', 'Problema a resolver')
    solucion = idea_data.get('solucion', 'Nuestra solución')
    publico = idea_data.get('publico_objetivo', 'profesionales')
    tam = idea_data.get('tam', '50M€')
    sam = idea_data.get('sam', '5M€')
    som = idea_data.get('som', '500K€')
    precio = idea_data.get('precio_sugerido', '29€/mes')
    score = idea_data.get('score_generador', 75)
    dificultad = idea_data.get('dificultad', 'Media')
    tiempo = idea_data.get('tiempo_estimado', '4-6 semanas')
    competencia = idea_data.get('competencia', ['Competidor 1', 'Competidor 2'])
    diferenciacion = idea_data.get('diferenciacion', 'Propuesta única de valor')
    features = idea_data.get('features_core', ['Feature 1', 'Feature 2', 'Feature 3'])
    stack = idea_data.get('stack_sugerido', ['Next.js', 'Supabase', 'Stripe'])
    canales = idea_data.get('canales_adquisicion', ['Twitter', 'ProductHunt', 'Reddit'])
    
    # Crear JSON estructurado
    prompt_json = {
        "project_name": nombre,
        "description": descripcion,
        "target_audience": publico,
        "problem": problema,
        "solution": solucion,
        "tech_stack": {
            "frontend": "Next.js 14 (App Router)",
            "styling": "Tailwind CSS + Shadcn/ui",
            "backend": "Vercel Serverless Functions",
            "database": "Supabase (PostgreSQL)",
            "auth": "Supabase Auth",
            "payments": "Stripe",
            "email": "Resend",
            "analytics": "Vercel Analytics + PostHog"
        },
        "core_features": features,
        "pricing": precio
    }
    
    prompt_json_str = json.dumps(prompt_json, indent=2, ensure_ascii=False)
    
    # Escapar caracteres especiales para JSON
    prompt_json_str_escaped = prompt_json_str.replace('{', '{{').replace('}', '}}')
    
    # Listas HTML
    competencia_html = ''.join([f'<li>{comp}</li>' for comp in competencia])
    features_html = ''.join([f'<li>{feat}</li>' for feat in features])
    stack_html = ''.join([f'<li>{tech}</li>' for tech in stack])
    canales_html = ''.join([f'<li>{canal}</li>' for canal in canales])
    
    # Generar HTML
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Informe Técnico: {nombre}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 0;
        }}
        
        .container {{
            max-width: 900px;
            margin: 0 auto;
            background: white;
            box-shadow: 0 0 20px rgba(0,0,0,0.1);
        }}
        
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            text-align: center;
        }}
        
        .header h1 {{
            font-size: 2rem;
            margin-bottom: 0.5rem;
        }}
        
        .header .meta {{
            font-size: 0.9rem;
            opacity: 0.9;
        }}
        
        .score-badge {{
            display: inline-block;
            background: rgba(255,255,255,0.2);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            margin: 0.5rem;
            font-weight: bold;
        }}
        
        .content {{
            padding: 2rem;
        }}
        
        h2 {{
            color: #667eea;
            margin: 2rem 0 1rem 0;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #667eea;
            font-size: 1.5rem;
        }}
        
        h3 {{
            color: #764ba2;
            margin: 1.5rem 0 0.5rem 0;
            font-size: 1.2rem;
        }}
        
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 1rem 0;
            font-size: 0.95rem;
        }}
        
        th, td {{
            padding: 0.75rem;
            text-align: left;
            border-bottom: 1px solid #ddd;
        }}
        
        th {{
            background: #f8f9fa;
            font-weight: 600;
            color: #667eea;
        }}
        
        tr:hover {{
            background: #f8f9fa;
        }}
        
        ul, ol {{
            margin: 1rem 0 1rem 2rem;
        }}
        
        li {{
            margin: 0.5rem 0;
        }}
        
        .alert {{
            padding: 1rem;
            border-radius: 8px;
            margin: 1rem 0;
        }}
        
        .alert-success {{
            background: #d4edda;
            border-left: 4px solid #28a745;
        }}
        
        .alert-warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }}
        
        .alert-danger {{
            background: #f8d7da;
            border-left: 4px solid #dc3545;
        }}
        
        .alert-info {{
            background: #d1ecf1;
            border-left: 4px solid #17a2b8;
        }}
        
        .json-container {{
            background: #1e1e1e;
            color: #d4d4d4;
            padding: 1.5rem;
            border-radius: 8px;
            overflow-x: auto;
            margin: 1rem 0;
            max-height: 400px;
            overflow-y: auto;
        }}
        
        .json-container pre {{
            margin: 0;
            font-family: 'Courier New', monospace;
            font-size: 0.85rem;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        
        .collapsible {{
            background: #667eea;
            color: white;
            cursor: pointer;
            padding: 1rem;
            width: 100%;
            border: none;
            text-align: left;
            outline: none;
            font-size: 1rem;
            font-weight: bold;
            border-radius: 8px;
            margin: 1rem 0;
            transition: 0.3s;
        }}
        
        .collapsible:hover {{
            background: #5568d3;
        }}
        
        .collapsible:after {{
            content: '▼';
            float: right;
            transition: 0.3s;
        }}
        
        .collapsible.active:after {{
            content: '▲';
        }}
        
        .collapsible-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease-out;
        }}
        
        /* RESPONSIVE */
        @media (max-width: 768px) {{
            .header h1 {{
                font-size: 1.5rem;
            }}
            
            .content {{
                padding: 1rem;
            }}
            
            h2 {{
                font-size: 1.3rem;
            }}
            
            h3 {{
                font-size: 1.1rem;
            }}
            
            table {{
                font-size: 0.85rem;
                display: block;
                overflow-x: auto;
                white-space: nowrap;
            }}
            
            th, td {{
                padding: 0.5rem;
            }}
            
            .json-container {{
                padding: 1rem;
                font-size: 0.75rem;
            }}
            
            .score-badge {{
                display: block;
                margin: 0.5rem 0;
            }}
        }}
        
        @media (max-width: 480px) {{
            body {{
                font-size: 0.9rem;
            }}
            
            .header {{
                padding: 1.5rem 1rem;
            }}
            
            .header h1 {{
                font-size: 1.3rem;
            }}
            
            table {{
                font-size: 0.75rem;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📋 {nombre}</h1>
            <p class="meta">Informe Técnico Completo - {datetime.now().strftime('%d/%m/%Y')}</p>
            <div class="score-badge">Score: {score}/100</div>
            <div class="score-badge">Dificultad: {dificultad}</div>
            <div class="score-badge">Tiempo: {tiempo}</div>
        </div>
        
        <div class="content">
            <h2>🎯 Resumen Ejecutivo</h2>
            <p><strong>Descripción:</strong> {descripcion}</p>
            <p><strong>Público objetivo:</strong> {publico}</p>
            
            <div class="alert alert-danger">
                <strong>❌ Problema:</strong><br>
                {problema}
            </div>
            
            <div class="alert alert-success">
                <strong>✅ Solución:</strong><br>
                {solucion}
            </div>
            
            <div class="alert alert-info">
                <strong>💎 Diferenciación:</strong><br>
                {diferenciacion}
            </div>
            
            <h2>📊 Validación de Mercado</h2>
            <table>
                <tr>
                    <th>Métrica</th>
                    <th>Valor</th>
                    <th>Descripción</th>
                </tr>
                <tr>
                    <td><strong>TAM</strong></td>
                    <td>{tam}</td>
                    <td>Mercado total disponible</td>
                </tr>
                <tr>
                    <td><strong>SAM</strong></td>
                    <td>{sam}</td>
                    <td>Mercado alcanzable</td>
                </tr>
                <tr>
                    <td><strong>SOM</strong></td>
                    <td>{som}</td>
                    <td>Objetivo año 1</td>
                </tr>
            </table>
            
            <h3>Competencia Principal</h3>
            <ul>
                {competencia_html}
            </ul>
            <p><strong>Tu ventaja:</strong> {diferenciacion}</p>
            
            <h2>💰 Modelo de Negocio</h2>
            <p><strong>Precio sugerido:</strong> {precio}</p>
            
            <h3>Proyecciones Financieras</h3>
            <table>
                <tr>
                    <th>Período</th>
                    <th>Usuarios</th>
                    <th>MRR</th>
                    <th>ARR</th>
                    <th>Churn</th>
                </tr>
                <tr>
                    <td>Mes 3</td>
                    <td>20-50</td>
                    <td>580-1,450€</td>
                    <td>7K-17K€</td>
                    <td>15%</td>
                </tr>
                <tr>
                    <td>Mes 6</td>
                    <td>100-200</td>
                    <td>2,900-5,800€</td>
                    <td>35K-70K€</td>
                    <td>10%</td>
                </tr>
                <tr>
                    <td>Año 1</td>
                    <td>500-1,000</td>
                    <td>14,500-29,000€</td>
                    <td>174K-348K€</td>
                    <td>5%</td>
                </tr>
            </table>
            
            <h2>🛠️ Stack Tecnológico</h2>
            <ul>
                {stack_html}
            </ul>
            <p><strong>Justificación:</strong> Stack gratuito hasta primeros ingresos, escalable hasta 10K usuarios.</p>
            
            <h2>🚀 Funcionalidades Core</h2>
            <ul>
                {features_html}
            </ul>
            
            <h2>📢 Estrategia de Marketing</h2>
            <h3>Canales de Adquisición</h3>
            <ul>
                {canales_html}
            </ul>
            
            <h2>🤖 Prompt para Cursor/Bolt/v0</h2>
            <button class="collapsible">📋 Ver JSON Completo (Click para expandir)</button>
            <div class="collapsible-content">
                <div class="json-container">
                    <pre>{prompt_json_str}</pre>
                </div>
            </div>
            
            <h2>⚠️ Riesgos y Mitigación</h2>
            <table>
                <tr>
                    <th>Riesgo</th>
                    <th>Probabilidad</th>
                    <th>Impacto</th>
                    <th>Mitigación</th>
                </tr>
                <tr>
                    <td>No encontrar product-market fit</td>
                    <td>Alta</td>
                    <td>Alto</td>
                    <td>Validar con 20+ entrevistas pre-build</td>
                </tr>
                <tr>
                    <td>Competencia fuerte</td>
                    <td>Media</td>
                    <td>Medio</td>
                    <td>Diferenciación clara + nicho específico</td>
                </tr>
                <tr>
                    <td>Costos inesperados</td>
                    <td>Baja</td>
                    <td>Bajo</td>
                    <td>Usar tier gratis, monitorizar uso</td>
                </tr>
            </table>
            
            <div class="alert alert-info" style="margin-top: 3rem; text-align: center;">
                <p><strong>¿Listo para construir? 🚀</strong></p>
                <p>Copia el JSON, pégalo en Cursor/Bolt/v0 y empieza HOY.</p>
            </div>
        </div>
    </div>
    
    <script>
        // Collapsible JSON
        const coll = document.getElementsByClassName("collapsible");
        for (let i = 0; i < coll.length; i++) {{
            coll[i].addEventListener("click", function() {{
                this.classList.toggle("active");
                const content = this.nextElementSibling;
                if (content.style.maxHeight) {{
                    content.style.maxHeight = null;
                }} else {{
                    content.style.maxHeight = content.scrollHeight + "px";
                }}
            }});
        }}
    </script>
</body>
</html>"""
    
    # Guardar como HTML
    output_dir = 'reports'
    os.makedirs(output_dir, exist_ok=True)
    
    filename = f'{output_dir}/{slug}.html'
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Informe HTML generado: {filename}")
    return filename


if __name__ == "__main__":
    test_idea = {
        'slug': 'testmaster-pro',
        'nombre': 'TestMaster Pro',
        'descripcion': 'Plataforma de testing automatizado con IA',
        'descripcion_corta': 'Tests automáticos con IA',
        'problema': 'Desarrolladores pierden 15h/semana escribiendo tests',
        'solucion': 'IA analiza código y genera tests en tiempo real',
        'publico_objetivo': 'Equipos de desarrollo',
        'tam': '150M€',
        'sam': '15M€',
        'som': '750K€',
        'precio_sugerido': '49€/mes',
        'score_generador': 82,
        'dificultad': 'Media',
        'tiempo_estimado': '4-6 semanas',
        'competencia': ['Jest', 'Cypress', 'Playwright'],
        'diferenciacion': 'Generación automática con IA',
        'features_core': ['Tests Automáticos', 'Cobertura 100%', 'CI/CD'],
        'stack_sugerido': ['Next.js', 'Supabase', 'Stripe'],
        'canales_adquisicion': ['Twitter', 'ProductHunt', 'Dev.to']
    }
    
    print("🧪 Generando informe de prueba...")
    generate_report(test_idea)
