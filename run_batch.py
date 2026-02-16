"""
Orquestador principal del sistema de validación de ideas
"""
from agents import generator_agent, critic_agent, notion_sync_agent, field_mapper, knowledge_base
import json
import os

def save_idea(idea):
    """Guarda la idea en el archivo JSON"""
    ideas_file = 'data/ideas.json'
    
    if os.path.exists(ideas_file):
        with open(ideas_file, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    else:
        data = {'ideas': []}
    
    data['ideas'].append(idea)
    
    with open(ideas_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    print('Iniciando generación de idea...')
    
    # Generar idea
    idea = generator_agent.generate()
    
    # Mapear campos al formato Notion
    if idea:
        idea = field_mapper.map_idea_fields(idea)
    
    if not idea:
        print('Error: No se pudo generar idea')
        return
    
    print(f'Idea generada: {idea.get("nombre", "Sin nombre")}')
    
    # Criticar y evaluar
    critic_result = critic_agent.critique(idea)
    idea.update(critic_result)
    
    print(f'Score crítico: {idea.get("score_critico", 0)}')
    
    # Guardar en local
    save_idea(idea)
    print('Idea guardada localmente')
    
    # Analizar idea para aprendizaje
    try:
        kb = knowledge_base.KnowledgeBase()
        kb.analyze_idea(idea)
        print('Idea analizada para auto-aprendizaje')
    except Exception as e:
        print(f'Advertencia en análisis: {e}')
    
    # Sincronizar con Notion
    try:
        notion_sync_agent.sync_to_notion(idea)
        print('Idea sincronizada con Notion')
    except Exception as e:
        print(f'Error en Notion sync: {e}')
    
    print('Proceso completado')

if __name__ == '__main__':
    main()

