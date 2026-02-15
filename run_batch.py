"""
Runner batch: 1 idea completa con reporte técnico en Notion.
"""
import os
import json
from datetime import datetime
from main_workflow import save_idea
from agents import generator_agent, researcher_agent, critic_agent, notion_sync_agent

def run_batch():
    print("\n" + "="*80)
    print("🚀 CHET THIS - 1 IDEA COMPLETA")
    print("="*80)
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Generar
    print("\n🎨 Generando idea...")
    idea = generator_agent.generate()
    if not idea:
        print("❌ Error generando")
        return

    print(f"✅ {idea.get('nombre', 'Sin nombre')}")

    # 2. Criticar
    print("\n📊 Evaluando...")
    critique = critic_agent.critique(idea)
    if critique:
        idea['score_critico'] = critique.get('score_critico', 70)
        idea['critique'] = critique
        print(f"   Score: {idea['score_critico']}/100")
    
    # Filtro
    if idea.get('score_critico', 0) < 80:
        print(f"❌ Descartada (< 80)")
        return

    print("✅ APROBADA")

    # 3. Research
    print("\n🔍 Research...")
    try:
        research = researcher_agent.research(idea)
        if research:
            idea['research'] = research
            print("✅ Research OK")
    except Exception as e:
        print(f"⚠️ Research: {e}")

    # 4. Guardar
    save_idea(idea)
    print("✅ Guardada")

    # 5. Sync Notion
    print("\n📤 Sincronizando a Notion...")
    try:
        page = notion_sync_agent.sync_idea_to_notion(idea)
        if page:
            print(f"✅ Ver en: {page['url']}")
    except Exception as e:
        print(f"❌ Notion: {e}")

    # 6. Learning cada 3
    try:
        with open('data/ideas.json', 'r', encoding='utf-8') as f:
            all_ideas = json.load(f)['ideas']
        
        if len(all_ideas) % 3 == 0 and len(all_ideas) > 0:
            print(f"\n🧠 Auto-learning ({len(all_ideas)} ideas)...")
            from agents import learning_agent
            learning_agent.learn_and_improve()
    except:
        pass

    print("\n✅ COMPLETADO")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_batch()
