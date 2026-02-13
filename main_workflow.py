import os
import sys
import json
from datetime import datetime
from agents import researcher_agent, generator_agent, critic_agent, optimizer_agent, report_agent, landing_generator, dashboard_generator, telegram_notifier

def count_ideas():
    csv_file = 'data/ideas-validadas.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            return len(f.readlines()) - 1
    return 0

def should_research():
    """Investigar cada 5 ideas (antes era cada 10)"""
    return count_ideas() % 5 == 0

def should_optimize():
    return count_ideas() > 0 and count_ideas() % 10 == 0

def save_rejected_idea(idea, critique, reason=""):
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
        'reason': reason,
        'fingerprint': idea.get('_fingerprint', '')
    })
    with open(rejected_file, 'w', encoding='utf-8') as f:
        json.dump(rejected_ideas, f, indent=2, ensure_ascii=False)
    print(f"📝 Rechazada: {idea.get('nombre')} | {reason}")

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
    print(f"✅ Guardada: {nombre} | Gen:{score_gen} Crit:{score_crit}")

def generate_with_feedback(max_iterations=3):
    """Genera con feedback loop hasta conseguir idea buena"""
    config = generator_agent.load_config()
    
    for iteration in range(max_iterations):
        print(f"\n{'='*60}")
        print(f"🔄 ITERACIÓN {iteration + 1}/{max_iterations}")
        print(f"{'='*60}")
        
        print("\n🧠 GENERACIÓN")
        idea = generator_agent.generate()
        
        if not idea:
            print("❌ Error, reintentando...")
            continue
        
        print("\n🎯 CRÍTICA")
        critique = critic_agent.critique(idea)
        
        print("\n📋 DECISIÓN")
        should_publish = critic_agent.decide_publish(idea, critique, config)
        
        if should_publish:
            return idea, critique, True
        else:
            score_gen = idea.get('score_generador', 0)
            score_crit = critique.get('score_critico', 0)
            puntos_debiles = critique.get('puntos_debiles', [])
            reason = f"Gen:{score_gen} Crit:{score_crit}"
            if puntos_debiles:
                reason += f" | {', '.join(puntos_debiles[:2])}"
            
            print(f"❌ RECHAZAR - {reason}")
            
            if iteration < max_iterations - 1:
                print(f"🔄 Mejorando con feedback... ({max_iterations - iteration - 1} restantes)")
            else:
                save_rejected_idea(idea, critique, reason)
                return idea, critique, False
    
    return None, None, False

def main():
    print("=" * 60)
    print("🤖 SISTEMA MULTI-AGENTE VALIDACIÓN IDEAS v2.0")
    print("🎯 MODO: INSISTENTE + APRENDIZAJE CONTINUO")
    print("=" * 60)
    
    try:
        # Fase 1: Research
        if should_research():
            print("\n📊 FASE 1: INVESTIGACIÓN MERCADO")
            researcher_agent.run()
        else:
            print("\n✅ Cache válido (research cada 5 ideas)")
        
        # Fase 2-4: Generar con feedback
        idea, critique, should_publish = generate_with_feedback(max_iterations=3)
        
        if not idea:
            print("\n❌ No se pudo generar idea válida")
            sys.exit(1)
        
        if should_publish:
            print("\n🎉 IDEA APROBADA - PUBLICANDO...")
            
            # Guardar en CSV
            save_idea_to_csv(idea, critique)
            
            # Generar landing
            print("\n🎨 LANDING...")
            landing_file = landing_generator.generate_landing(idea)
            slug = idea.get('slug', 'idea')
            landing_url = f"landing-pages/{slug}.html"
            
            # Generar informe HTML
            print("\n📊 INFORME...")
            report_file = report_agent.generate_report(idea)
            report_url = f"reports/{slug}.html"
            
            # Dashboard
            print("\n🏠 DASHBOARD...")
            dashboard_generator.generate_dashboard()
            
            # Telegram
            print("\n📱 TELEGRAM...")
            telegram_notifier.send_telegram_notification(idea, critique, landing_url, report_url)
            
            # Optimización
            if should_optimize():
                print("\n🚀 OPTIMIZACIÓN")
                optimizer_agent.run()
            
            print("\n" + "=" * 60)
            print(f"✅ ÉXITO: {idea.get('nombre')}")
            print(f"📊 Scores: Gen={idea.get('score_generador')} Crit={critique.get('score_critico')}")
            print(f"🔗 {landing_url}")
            print(f"📄 {report_url}")
            print("=" * 60)
        else:
            print("\n❌ RECHAZADA TRAS 3 ITERACIONES")
            print("💡 Sistema aprenderá de este rechazo")
    
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
