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
    """Guardar idea rechazada"""
    os.makedirs('data', exist_ok=True)
    rejected_file = 'data/rejected_ideas.json'
    
    rejected_ideas = []
    if os.path.exists(rejected_file):
        with open(rejected_file, 'r', encoding='utf-8') as f:
            rejected_ideas = json.load(f)
    
    rejected_ideas.append({
        'timestamp': datetime.now().isoformat(),
        'idea': idea,
        'critique': critique
    })
    
    with open(rejected_file, 'w', encoding='utf-8') as f:
        json.dump(rejected_ideas, f, indent=2, ensure_ascii=False)
    
    print(f"📝 Idea rechazada guardada en {rejected_file}")

def save_idea_to_csv(idea, critique):
    """Guardar idea en CSV"""
    os.makedirs('data', exist_ok=True)
    csv_file = 'data/ideas-validadas.csv'
    
    # Crear header si no existe
    if not os.path.exists(csv_file):
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('timestamp,nombre,descripcion_corta,score_generador,score_critico,tipo,dificultad\n')
    
    # Añadir idea
    with open(csv_file, 'a', encoding='utf-8') as f:
        timestamp = datetime.now().isoformat()
        nombre = idea.get('nombre', '').replace(',', ';')
        descripcion = idea.get('descripcion_corta', '').replace(',', ';')
        score_gen = idea.get('score_generador', 0)
        score_crit = critique.get('score_critico', 0)
        tipo = 'SaaS'  # Default
        dificultad = idea.get('dificultad', 'Media')
        
        f.write(f'{timestamp},{nombre},{descripcion},{score_gen},{score_crit},{tipo},{dificultad}\n')
    
    print(f"✅ Idea guardada en CSV: {nombre}")

def create_simple_landing_page(idea, critique):
    """Crear landing page simple"""
    os.makedirs('landing-pages', exist_ok=True)
    
    slug = idea.get('nombre', 'idea').lower().replace(' ', '-')[:30]
    html_file = f'landing-pages/{slug}.html'
    
    html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{idea.get('nombre', 'Idea')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }}
        h1 {{ color: #6366f1; }}
        .score {{ background: #f0f0f0; padding: 10px; border-radius: 5px; }}
    </style>
</head>
<body>
    <h1>{idea.get('nombre', 'Idea')}</h1>
    <p><strong>Descripción:</strong> {idea.get('descripcion_corta', '')}</p>
    
    <h2>Problema</h2>
    <p>{idea.get('problema', '')}</p>
    
    <h2>Solución</h2>
    <p>{idea.get('solucion', '')}</p>
    
    <h2>Propuesta de Valor</h2>
    <p>{idea.get('propuesta_valor', '')}</p>
    
    <h2>Mercado Objetivo</h2>
    <p>{idea.get('mercado_objetivo', '')}</p>
    
    <h2>Competencia</h2>
    <ul>
        {''.join([f'<li>{comp}</li>' for comp in idea.get('competencia', [])])}
    </ul>
    
    <h2>Diferenciación</h2>
    <p>{idea.get('diferenciacion', '')}</p>
    
    <h2>Monetización</h2>
    <p>{idea.get('monetizacion', '')}</p>
    
    <div class="score">
        <p><strong>Score Generador:</strong> {idea.get('score_generador', 0)}/100</p>
        <p><strong>Score Crítico:</strong> {critique.get('score_critico', 0)}/100</p>
    </div>
    
    <h2>Veredicto del Crítico</h2>
    <p>{critique.get('veredicto_honesto', '')}</p>
</body>
</html>"""
    
    with open(html_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"✅ Landing page creada: {html_file}")

def main():
    """Workflow principal"""
    print("=" * 60)
    print("🤖 SISTEMA MULTI-AGENTE DE VALIDACIÓN DE IDEAS")
    print("=" * 60)
    
    try:
        # 1. Investigar si toca
        if should_research():
            print("\n📊 FASE 1: INVESTIGACIÓN")
            researcher_agent.run()
        else:
            print("\n✅ Cache de investigación válido, saltando...")
        
        # 2. Generar idea
        print("\n🧠 FASE 2: GENERACIÓN DE IDEA")
        idea = generator_agent.generate()
        
        # 3. Criticar idea
        print("\n🎯 FASE 3: CRÍTICA DE IDEA")
        critique = critic_agent.critique(idea)
        
        # 4. Decidir publicación
        print("\n📋 FASE 4: DECISIÓN")
        should_publish = critic_agent.decide_publish(idea, critique, generator_agent.load_config())
        
        if should_publish:
            print("\n✅ IDEA APROBADA - PUBLICANDO...")
            
            # Guardar en CSV
            save_idea_to_csv(idea, critique)
            
            # Crear landing page
            create_simple_landing_page(idea, critique)
            
            # Optimizar si toca
            if should_optimize():
                print("\n🚀 FASE 5: OPTIMIZACIÓN")
                optimizer_agent.run()
            
            print("\n" + "=" * 60)
            print(f"🎉 ÉXITO: {idea.get('nombre', 'Idea')} publicada")
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
