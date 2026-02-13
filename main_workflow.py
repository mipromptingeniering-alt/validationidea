import os
import sys
import json
from datetime import datetime

# Importar agentes
from agents import researcher_agent, generator_agent, critic_agent, optimizer_agent

def count_ideas():
    """Contar ideas publicadas"""
    csv_file = 'data/ideas-validadas.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            return len(f.readlines()) - 1  # -1 por el header
    return 0

def should_research():
    """Verificar si toca investigar (cada 10 ideas)"""
    return count_ideas() % 10 == 0

def should_optimize():
    """Verificar si toca optimizar (cada 10 ideas)"""
    return count_ideas() > 0 and count_ideas() % 10 == 0

def save_rejected_idea(idea, critique):
    """Guardar idea rechazada CON fingerprint"""
    os.makedirs('data', exist_ok=True)
    rejected_file = 'data/rejected_ideas.json'
    
    rejected_ideas = []
    if os.path.exists(rejected_file):
        with open(rejected_file, 'r', encoding='utf-8') as f:
            rejected_ideas = json.load(f)
    
    rejected_ideas.append({
        'timestamp': datetime.now().isoformat(),
        'idea': idea,
        'critique': critique,
        'fingerprint': idea.get('_fingerprint', '')
    })
    
    with open(rejected_file, 'w', encoding='utf-8') as f:
        json.dump(rejected_ideas, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Idea rechazada guardada: {idea.get('nombre')}")

def save_idea_to_csv(idea, critique):
    """Guardar idea en CSV CON fingerprint"""
    os.makedirs('data', exist_ok=True)
    csv_file = 'data/ideas-validadas.csv'
    
    # Crear header si no existe
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('timestamp,nombre,descripcion_corta,score_generador,score_critico,tipo,dificultad,fingerprint\n')
    
    # Añadir idea
    with open(csv_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().isoformat()
        nombre = idea.get('nombre', '').replace(',', ';')
        descripcion = idea.get('descripcion_corta', '').replace(',', ';')
        score_gen = idea.get('score_generador', 0)
        score_crit = critique.get('score_critico', 0)
        tipo = 'SaaS'
        dificultad = idea.get('dificultad', 'Media')
        fingerprint = idea.get('_fingerprint', '')
        
        f.write(f'{timestamp},{nombre},{descripcion},{score_gen},{score_crit},{tipo},{dificultad},{fingerprint}\n')
    
    print(f"✅ Idea guardada en CSV: {nombre}")

def create_simple_landing_page(idea, critique):
    """Crear landing page simple"""
    os.makedirs('landing-pages', exist_ok=True)
    
    slug = idea.get('nombre', 'idea').lower().replace(' ', '-').replace('/', '-')[:30]
    # Limpiar caracteres especiales
    slug = ''.join(c for c in slug if c.isalnum() or c == '-')
    html_file = f'landing-pages/{slug}.html'
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{idea.get('nombre', 'Idea')}</title>
    <style>
        body {{ 
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 800px; 
            margin: 50px auto; 
            padding: 20px;
            line-height: 1.6;
        }}
        h1 {{ color: #667eea; margin-bottom: 10px; }}
        .meta {{ color: #999; margin-bottom: 30px; }}
        .score {{ 
            background: #f3f4f6; 
            padding: 15px; 
            border-radius: 10px; 
            margin: 20px 0;
        }}
        .score-item {{
            display: inline-block;
            margin-right: 20px;
            font-weight: bold;
        }}
        .section {{ margin: 30px 0; }}
        .section h2 {{ color: #333; border-bottom: 2px solid #667eea; padding-bottom: 5px; }}
        ul {{ padding-left: 20px; }}
        li {{ margin: 8px 0; }}
    </style>
</head>
<body>
    <h1>{idea.get('nombre', 'Idea')}</h1>
    <div class="meta">
        📅 Generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}
    </div>
    
    <p><strong>{idea.get('descripcion_corta', '')}</strong></p>
    
    <div class="score">
        <span class="score-item">🤖 Score Generador: {idea.get('score_generador', 0)}/100</span>
        <span class="score-item">🎯 Score Crítico: {critique.get('score_critico', 0)}/100</span>
    </div>
    
    <div class="secti
