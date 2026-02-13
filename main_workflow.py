import os
import sys
import json
from datetime import datetime

from agents import researcher_agent, generator_agent, critic_agent, optimizer_agent, report_agent

def count_ideas():
    csv_file = 'data/ideas-validadas.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            return len(f.readlines()) - 1
    return 0

def should_research():
    return count_ideas() % 10 == 0

def should_optimize():
    return count_ideas() > 0 and count_ideas() % 10 == 0

def save_rejected_idea(idea, critique):
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
    os.makedirs('data', exist_ok=True)
    csv_file = 'data/ideas-validadas.csv'
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('timestamp,nombre,descripcion_corta,score_generador,score_critico,tipo,dificultad,fingerprint\n')
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
    os.makedirs('landing-pages', exist_ok=True)
    slug = idea.get('nombre', 'idea').lower().replace(' ', '-').replace('/', '-')[:30]
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
            max-width: 900px; 
            margin: 50px auto; 
            padding: 30px;
            line-height: 1.7;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        }}
        .container {{
            background: white;
            padding: 50px;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
        }}
        h1 {{ color: #667eea; margin-bottom: 15px; font-size: 2.5em; }}
        .meta {{ color: #999; margin-bottom: 30px; font-size: 0.95em; }}
        .score {{ 
            background: linear-gradient(135deg, #f3f4f6 0%, #e5e7eb 100%);
            padding: 20px; 
            border-radius: 15px; 
            margin: 25px 0;
            display: flex;
            gap: 30px;
            justify-content: center;
        }}
        .score-item {{ font-weight: 700; font-size: 1.1em; }}
        .section {{ margin: 35px 0; }}
        .section h2 {{ 
            color: #333; 
            border-bottom: 3px solid #667eea; 
            padding-bottom: 8px;
            margin-bottom: 15px;
        }}
        ul {{ padding-left: 25px; }}
        li {{ margin: 10px 0; }}
        .btn-report {{
            display: inline-block;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px 30px;
            border-radius: 10px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 20px;
            box-shadow: 0 4px 15px rgba(102,126,234,0.4);
        }}
        .btn-report:hover {{
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102,126,234,0.6);
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>{idea.get('nombre', 'Idea')}</h1>
        <div class="meta">📅 Generada el {datetime.now().strftime('%d/%m/%Y %H:%M')}</div>
        <p style="font-size: 1.15em; color: #374151;"><strong>{idea.get('descripcion_corta', '')}</strong></p>
        <div class="score">
            <span class="score-item">🤖 Score Generador: {idea.get('score_generador', 0)}/100</span>
            <span class="score-item">🎯 Score Crítico: {critique.get('score_critico', 0)}/100</span>
        </div>
        <a href="../reports/{slug}.md" class="btn-report" target="_blank">📊 Ver Informe Completo</a>
        <div class="section">
            <h2>💡 Problema</h2>
            <p>{idea.get('problema', '')}</p>
        </div>
        <div class="section">
            <h2>✨ Solución</h2>
            <p>{idea.get('solucion', '')}</p>
        </div>
        <div class="section">
            <h2>🎯 Propuesta de Valor</h2>
            <p>{idea.get('propuesta_valor', '')}</p>
        </div>
        <div class="section">
            <h2>👥 Mercado Objetivo</h2>
            <p>{idea.get('mercado_objetivo', '')}</p>
        </div>
        <div class="section">
            <h2>🏢 Competencia</h2>
            <ul>{''.join([f'<li>{comp}</li>' for comp in idea.get('competencia', [])])}</ul>
        </div>
        <div class="section">
            <h2>⚡ Diferenciación</h2>
            <p>{idea.get('diferenciacion', '')}</p>
        </div>
        <div class="section">
            <h2>💰 Monetización</h2>
            <p>{idea.get('monetizacion', '')}</p>
        </div>
        <div class="section">
            <h2>🛠️ Tech Stack</h2>
            <ul>{''.join([f'<li>{tech}</li>' for tech in idea.get('tech_stack', [])])}</ul>
        </div>
        <div class="section">
            <h2>📊 Detalles</h2>
            <p><strong>Dificultad:</strong> {idea.get('dificultad', 'Media')}</p>
            <p><strong>Tiempo estimado:</strong> {idea.get('tiempo_estimado', '4 semanas')}</p>
        </div>
        <div class="section">
            <h2>🎯 Evaluación del Crítico</h2>
            <p><strong>Veredicto:</strong> {critique.get('veredicto_honesto', '')}</p>
            <p><strong>Probabilidad de éxito:</strong> {critique.get('probabilidad_exito', 'N/A')}</p>
            <h3>✅ Fortalezas</h3>
            <ul>{''.join([f'<li>{f}</li>' for f in critique.get('fortalezas', [])])}</ul>
            <h3>⚠️ Debilidades</h3>
            <ul>{''.join([f'<li>{d}</li>' for d in critique.get('debilidades', [])])}</ul>
            <h3>🚨 Riesgos Mayores</h3>
            <ul>{''.join([f'<li>{r}</li>' for r in critique.get('riesgos_mayores', [])])}</ul>
        </div>
        <a href="../reports/{slug}.md" class="btn-report" target="_blank">📊 Ver Informe Completo con Roadmap y Prompt IA</a>
    </div>
</body>
</html>"""
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    print(f"✅ Landing page creada: {html_file}")
    return slug

def main():
    print("=" * 60)
    print("🤖 SISTEMA MULTI-AGENTE DE VALIDACIÓN DE IDEAS")
    print("=" * 60)
    try:
        if should_research():
            print("\n📊 FASE 1: INVESTIGACIÓN")
            researcher_agent.run()
        else:
            print("\n✅ Cache de investigación válido, saltando...")
        print("\n🧠 FASE 2: GENERACIÓN DE IDEA")
        idea = generator_agent.generate()
        print("\n🎯 FASE 3: CRÍTICA DE IDEA")
        critique = critic_agent.critique(idea)
        print("\n📋 FASE 4: DECISIÓN")
        should_publish = critic_agent.decide_publish(idea, critique, generator_agent.load_config())
        if should_publish:
            print("\n✅ IDEA APROBADA - PUBLICANDO...")
            save_idea_to_csv(idea, critique)
            slug = create_simple_landing_page(idea, critique)
            print("\n📊 FASE 5: GENERANDO INFORME COMPLETO...")
            report_agent.generate_report(idea, critique)
            if should_optimize():
                print("\n🚀 FASE 6: OPTIMIZACIÓN")
                optimizer_agent.run()
            print("\n" + "=" * 60)
            print(f"🎉 ÉXITO: {idea.get('nombre', 'Idea')} publicada")
            print(f"🔗 Landing: landing-pages/{slug}.html")
            print(f"📊 Informe: reports/{slug}.md")
            print("=" * 60)
        else:
            print("\n❌ IDEA RECHAZADA")
            save_rejected_idea(idea, critique)
            print("\n" + "=" * 60)
            print("💡 Idea rechazada, se generará otra en el próximo ciclo")
            print("=" * 60)
    except Exception as e:
        print(f"\n❌ ERROR EN EL SISTEMA: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
