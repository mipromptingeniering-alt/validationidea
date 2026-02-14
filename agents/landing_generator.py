import os
import json
from datetime import datetime

def generate_landing(idea):
    """Genera landing page en estructura correcta slug/index.html"""
    
    print("\n🎨 Generando landing page...")
    
    slug = idea.get('slug', 'idea')
    nombre = idea.get('nombre', 'Sin nombre')
    descripcion = idea.get('descripcion', 'Sin descripción')
    descripcion_corta = idea.get('descripcion_corta', descripcion)[:180]
    problema = idea.get('problema', 'Problema no especificado')
    solucion = idea.get('solucion', 'Solución no especificada')
    precio = idea.get('precio_sugerido', '49')
    publico = idea.get('publico_objetivo', 'Profesionales')
    propuesta_valor = idea.get('propuesta_valor', 'Ahorra tiempo y dinero')
    
    # Features
    features = idea.get('features_core', [])
    if isinstance(features, str):
        features = [features]
    if not features:
        features = ['Automatización inteligente', 'Fácil de usar', 'Integración con herramientas populares']
    
    # HTML landing
    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="{descripcion_corta}">
    <title>{nombre} - Solución SaaS Innovadora</title>
    
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            line-height: 1.6;
            color: #333;
        }}
        
        .hero {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 4rem 2rem;
            text-align: center;
            min-height: 60vh;
            display: flex;
            flex-direction: column;
            justify-content: center;
            align-items: center;
        }}
        
        .hero h1 {{
            font-size: 3rem;
            margin-bottom: 1rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
            animation: fadeInDown 0.8s ease-out;
        }}
        
        .hero p {{
            font-size: 1.3rem;
            margin-bottom: 2rem;
            max-width: 700px;
            opacity: 0.95;
            animation: fadeIn 1s ease-out;
        }}
        
        .cta-button {{
            background: white;
            color: #667eea;
            padding: 1.2rem 3rem;
            border-radius: 50px;
            text-decoration: none;
            font-weight: 700;
            font-size: 1.2rem;
            box-shadow: 0 8px 24px rgba(0,0,0,0.2);
            transition: all 0.3s;
            display: inline-block;
            animation: fadeInUp 1.2s ease-out;
        }}
        
        .cta-button:hover {{
            transform: translateY(-3px);
            box-shadow: 0 12px 32px rgba(0,0,0,0.3);
        }}
        
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            padding: 4rem 2rem;
        }}
        
        .section {{
            margin-bottom: 4rem;
        }}
        
        .section h2 {{
            font-size: 2.5rem;
            color: #667eea;
            margin-bottom: 1.5rem;
            text-align: center;
        }}
        
        .problem-solution {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 2rem;
            margin-top: 3rem;
        }}
        
        .card {{
            background: #f8f9fa;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.08);
            transition: all 0.3s;
        }}
        
        .card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 8px 24px rgba(0,0,0,0.12);
        }}
        
        .card h3 {{
            font-size: 1.8rem;
            margin-bottom: 1rem;
            color: #333;
        }}
        
        .problem-card {{
            border-left: 5px solid #ff6b6b;
        }}
        
        .solution-card {{
            border-left: 5px solid #51cf66;
        }}
        
        .features {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 2rem;
            margin-top: 3rem;
        }}
        
        .feature {{
            background: white;
            padding: 2rem;
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.06);
            text-align: center;
            transition: all 0.3s;
        }}
        
        .feature:hover {{
            transform: scale(1.05);
            box-shadow: 0 8px 24px rgba(102, 126, 234, 0.15);
        }}
        
        .feature-icon {{
            font-size: 3rem;
            margin-bottom: 1rem;
        }}
        
        .feature h4 {{
            font-size: 1.3rem;
            margin-bottom: 0.75rem;
            color: #667eea;
        }}
        
        .pricing {{
            background: linear-gradient(135deg, #f8f9fa, #e9ecef);
            padding: 4rem 2rem;
            text-align: center;
            border-radius: 16px;
        }}
        
        .pricing h2 {{
            margin-bottom: 2rem;
        }}
        
        .price {{
            font-size: 4rem;
            color: #667eea;
            font-weight: bold;
            margin: 1rem 0;
        }}
        
        .price-detail {{
            font-size: 1.2rem;
            color: #666;
            margin-bottom: 2rem;
        }}
        
        .email-form {{
            max-width: 500px;
            margin: 3rem auto;
            background: white;
            padding: 2.5rem;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(0,0,0,0.1);
        }}
        
        .email-form h3 {{
            text-align: center;
            margin-bottom: 1.5rem;
            color: #333;
        }}
        
        .form-group {{
            margin-bottom: 1.5rem;
        }}
        
        .form-group label {{
            display: block;
            margin-bottom: 0.5rem;
            font-weight: 600;
            color: #555;
        }}
        
        .form-group input {{
            width: 100%;
            padding: 1rem;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: all 0.3s;
        }}
        
        .form-group input:focus {{
            outline: none;
            border-color: #667eea;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
        }}
        
        .submit-btn {{
            width: 100%;
            padding: 1.2rem;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 1.1rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .submit-btn:hover {{
            transform: translateY(-2px);
            box-shadow: 0 8px 16px rgba(102, 126, 234, 0.3);
        }}
        
        footer {{
            background: #2c3e50;
            color: white;
            text-align: center;
            padding: 2rem;
            margin-top: 4rem;
        }}
        
        @keyframes fadeInDown {{
            from {{
                opacity: 0;
                transform: translateY(-30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @keyframes fadeIn {{
            from {{ opacity: 0; }}
            to {{ opacity: 1; }}
        }}
        
        @keyframes fadeInUp {{
            from {{
                opacity: 0;
                transform: translateY(30px);
            }}
            to {{
                opacity: 1;
                transform: translateY(0);
            }}
        }}
        
        @media (max-width: 768px) {{
            .hero h1 {{
                font-size: 2rem;
            }}
            
            .problem-solution {{
                grid-template-columns: 1fr;
            }}
            
            .features {{
                grid-template-columns: 1fr;
            }}
        }}
    </style>
</head>
<body>
    <div class="hero">
        <h1>🚀 {nombre}</h1>
        <p>{descripcion_corta}</p>
        <a href="#registro" class="cta-button">Únete a la Lista de Espera</a>
    </div>
    
    <div class="container">
        <div class="section">
            <div class="problem-solution">
                <div class="card problem-card">
                    <h3>❌ El Problema</h3>
                    <p>{problema}</p>
                </div>
                
                <div class="card solution-card">
                    <h3>✅ Nuestra Solución</h3>
                    <p>{solucion}</p>
                </div>
            </div>
        </div>
        
        <div class="section">
            <h2>⚡ Características Principales</h2>
            <div class="features">
"""
    
    # Features dinámicos
    feature_icons = ['🎯', '⚡', '🔥', '💡', '🚀', '✨']
    for idx, feature in enumerate(features[:6]):
        icon = feature_icons[idx] if idx < len(feature_icons) else '⭐'
        html += f"""
                <div class="feature">
                    <div class="feature-icon">{icon}</div>
                    <h4>{feature}</h4>
                </div>
"""
    
    html += f"""
            </div>
        </div>
        
        <div class="pricing">
            <h2>💰 Precio de Lanzamiento</h2>
            <div class="price">€{precio}</div>
            <p class="price-detail">por mes • Cancela cuando quieras</p>
            <p style="color: #666; margin-top: 1rem;">🎁 <strong>50% descuento</strong> para los primeros 100 usuarios</p>
        </div>
        
        <div class="email-form" id="registro">
            <h3>📧 Únete a la Lista de Espera</h3>
            <p style="text-align: center; color: #666; margin-bottom: 1.5rem;">
                Sé el primero en saber cuándo lanzamos
            </p>
            
            <form action="/api/submit-email" method="POST">
                <input type="hidden" name="idea_slug" value="{slug}">
                
                <div class="form-group">
                    <label for="name">Nombre</label>
                    <input type="text" id="name" name="name" required placeholder="Tu nombre">
                </div>
                
                <div class="form-group">
                    <label for="email">Email</label>
                    <input type="email" id="email" name="email" required placeholder="tu@email.com">
                </div>
                
                <button type="submit" class="submit-btn">
                    🚀 ¡Quiero acceso anticipado!
                </button>
            </form>
        </div>
    </div>
    
    <footer>
        <p>🤖 Generado automáticamente por <strong>ValidationIdea</strong></p>
        <p style="margin-top: 0.5rem; opacity: 0.8;">Sistema Multi-Agente IA para Validación de Ideas SaaS</p>
    </footer>
</body>
</html>
"""
    
    # ESTRUCTURA CORRECTA: slug/index.html
    output_dir = f'landing-pages/{slug}'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = f'{output_dir}/index.html'
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"✅ Landing generada: {output_file}")
    
    return output_file


if __name__ == "__main__":
    # Test
    test_idea = {
        "nombre": "TestSaaS Pro",
        "slug": "test-saas-pro",
        "descripcion": "Plataforma revolucionaria para automatizar tu workflow",
        "descripcion_corta": "Automatiza tu workflow en minutos",
        "problema": "Los equipos pierden 10 horas semanales en tareas manuales repetitivas",
        "solucion": "IA que automatiza tareas repetitivas con 1-click, ahorra 80% del tiempo",
        "precio_sugerido": "49",
        "publico_objetivo": "Equipos remotos y startups",
        "features_core": [
            "Automatización con IA",
            "Integraciones ilimitadas",
            "Dashboard en tiempo real"
        ]
    }
    
    generate_landing(test_idea)
