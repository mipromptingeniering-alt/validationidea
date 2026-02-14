import json
import os
from datetime import datetime

CONTEXT_FILE = 'memory-system/FULL-CONTEXT.json'

def track_interaction(topic, decisions=None, files=None):
    """Registra cada interacción automáticamente"""
    
    if not os.path.exists(CONTEXT_FILE):
        print("⚠️  Inicializando contexto...")
        initialize_context()
    
    with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
        context = json.load(f)
    
    # Incrementar contador
    context['meta']['interaction_count'] += 1
    count = context['meta']['interaction_count']
    
    # Registrar interacción
    interaction = {
        "count": count,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "time": datetime.now().strftime('%H:%M'),
        "topic": topic,
        "decisions": decisions or [],
        "files": files or []
    }
    
    context['interaction_history'].append(interaction)
    context['meta']['last_updated'] = datetime.now().isoformat()
    
    # Auto-update cada 5
    if count % 5 == 0:
        print(f"\n{'='*60}")
        print(f"🔄 AUTO-UPDATE #{count} TRIGGERED")
        print(f"{'='*60}\n")
        context = perform_auto_update(context)
    
    # Guardar
    with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Interacción #{count} registrada: {topic}")
    
    return count

def perform_auto_update(context):
    """Realiza actualización completa cada 5 interacciones"""
    
    print("📊 Actualizando métricas...")
    
    # Actualizar ideas generadas
    csv_file = 'data/ideas-validadas.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r') as f:
            context['metrics']['ideas_generated'] = len(f.readlines()) - 1
    
    # Calcular token usage
    context['metrics']['daily_token_usage'] = context['metrics']['ideas_generated'] * 300
    context['metrics']['token_budget_remaining'] = 100000 - context['metrics']['daily_token_usage']
    
    # Comprimir historial si >20 interacciones
    if len(context['interaction_history']) > 20:
        print("🗜️  Comprimiendo historial antiguo...")
        recent = context['interaction_history'][-20:]
        old = context['interaction_history'][:-20]
        
        summary = {
            "compressed": True,
            "total": len(old),
            "range": f"{old[0]['date']} - {old[-1]['date']}",
            "topics": list(set([i['topic'] for i in old]))[:10]
        }
        
        context['interaction_history'] = [summary] + recent
    
    # Generar resumen
    print("📝 Generando resumen progreso...")
    context['summary'] = {
        "generated_at": datetime.now().isoformat(),
        "total_interactions": context['meta']['interaction_count'],
        "ideas_generated": context['metrics']['ideas_generated'],
        "approval_rate": context['metrics']['approval_rate'],
        "status": "✅ On track" if context['metrics']['approval_rate'] > 0.5 else "⚠️ Needs improvement"
    }
    
    print("✅ Auto-update completado\n")
    
    return context

def initialize_context():
    """Inicializa contexto si no existe"""
    # Si no existe FULL-CONTEXT.json, lo crea con estructura básica
    context = {
        "meta": {
            "interaction_count": 0,
            "last_updated": datetime.now().isoformat()
        },
        "interaction_history": [],
        "metrics": {
            "ideas_generated": 0,
            "approval_rate": 0.6,
            "daily_token_usage": 0,
            "token_budget_remaining": 100000
        }
    }
    
    os.makedirs('memory-system', exist_ok=True)
    with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2)

# Registrar esta interacción (#7)
if __name__ == "__main__":
    track_interaction(
        topic="Continuando desarrollo - Implementando prompts templates + checkpoint system",
        decisions=[
            "Sistema tracking interacciones automático",
            "Prompts reutilizables para tareas comunes",
            "Checkpoint system para rollback",
            "Smart diff para cambios específicos"
        ],
        files=[
            "scripts/interaction-tracker.py",
            "prompts/templates.json",
            "scripts/checkpoint-manager.py",
            "scripts/smart-diff.py"
        ]
    )
