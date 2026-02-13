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
            
            print("\n🎨 FASE 5: GENERANDO LANDING PAGE MARKETING...")
            slug = landing_generator.generate_marketing_landing(idea, critique)
            landing_url = f"landing-pages/{slug}.html"
            
            print("\n📊 FASE 6: GENERANDO INFORME COMPLETO...")
            report_agent.generate_report(idea, critique)
            report_url = f"reports/{slug}.md"
            
            print("\n🏠 FASE 7: ACTUALIZANDO DASHBOARD...")
            dashboard_generator.generate_dashboard()
            
            print("\n📱 FASE 8: ENVIANDO NOTIFICACIÓN TELEGRAM...")
            telegram_notifier.send_telegram_notification(idea, critique, landing_url, report_url)
            
            if should_optimize():
                print("\n🚀 FASE 9: OPTIMIZACIÓN")
                optimizer_agent.run()
            
            print("\n" + "=" * 60)
            print(f"🎉 ÉXITO: {idea.get('nombre', 'Idea')} publicada")
            print(f"🔗 Landing: {landing_url}")
            print(f"📊 Informe: {report_url}")
            print(f"🏠 Dashboard: landing-pages/index.html")
            print(f"📱 Notificación Telegram enviada")
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
