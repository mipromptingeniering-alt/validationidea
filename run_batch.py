"""
Runner batch: 1 idea completa con anÃ¡lisis de competencia y notificaciones
"""
import os
import json
from datetime import datetime
from main_workflow import save_idea
from agents import generator_agent, researcher_agent, critic_agent, notion_sync_agent, telegram_agent

def run_batch():
    print("\n" + "="*80)
    print("ðŸš€ CHET THIS - 1 IDEA COMPLETA")
    print("="*80)
    print(f"ðŸ“… {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

    # 1. Generar
    print("\nðŸŽ¨ Generando idea...")
    idea = generator_agent.generate()
    if not idea:
        print("âŒ Error generando")
        return

    print(f"âœ… {idea.get('nombre', 'Sin nombre')}")

    # 2. Criticar
    print("\nðŸ“Š Evaluando...")
    critique = critic_agent.critique(idea)
    if critique:
        idea['score_critico'] = critique.get('score_critico', 70)
        idea['critique'] = critique
        print(f"   Score: {idea['score_critico']}/100")
    
    # Filtro temporal a 70
    if idea.get('score_critico', 0) < 80:
        print(f"âŒ Descartada (< 70)")
        return

    print("âœ… APROBADA")

    # 3. Research
    print("\nðŸ” Research...")
    try:
        research = researcher_agent.research(idea)
        if research:
            idea['research'] = research
            print("âœ… Research OK")
    except Exception as e:
        print(f"âš ï¸ Research: {e}")

    # 4. Guardar
    save_idea(idea)
    print("âœ… Guardada")

    # 5. Sync Notion (con anÃ¡lisis competencia + estimaciÃ³n)
    print("\nðŸ“¤ Sincronizando a Notion con anÃ¡lisis completo...")
    try:
        page = notion_sync_agent.sync_idea_to_notion(idea)
        if page:
            print(f"âœ… Ver en: {page['url']}")
    except Exception as e:
        print(f"âŒ Notion: {e}")

    # 6. NotificaciÃ³n Telegram
    print("\nðŸ“± Enviando notificaciÃ³n Telegram...")
    try:
        telegram_agent.send_notification(idea)
    except Exception as e:
        print(f"âš ï¸ Telegram: {e}")

    # 7. Learning cada 3
    try:
        with open('data/ideas.json', 'r', encoding='utf-8') as f:
            all_ideas = json.load(f)['ideas']
        
        if len(all_ideas) % 3 == 0 and len(all_ideas) > 0:
            print(f"\nðŸ§  Auto-learning ({len(all_ideas)} ideas)...")
            from agents import learning_agent
            learning_agent.learn_and_improve()
    except:
        pass

    print("\nâœ… COMPLETADO")
    print("="*80 + "\n")

if __name__ == "__main__":
    run_batch()