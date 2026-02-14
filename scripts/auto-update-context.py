import json
import os
from datetime import datetime

CONTEXT_FILE = 'memory-system/FULL-CONTEXT.json'
META_ROADMAP_FILE = 'memory-system/META-ROADMAP.json'
UPDATE_INTERVAL = 5

def load_context():
    """Carga contexto actual"""
    if os.path.exists(CONTEXT_FILE):
        with open(CONTEXT_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return None

def save_context(context):
    """Guarda contexto actualizado"""
    os.makedirs('memory-system', exist_ok=True)
    with open(CONTEXT_FILE, 'w', encoding='utf-8') as f:
        json.dump(context, f, indent=2, ensure_ascii=False)
    print(f"✅ Contexto guardado: {CONTEXT_FILE}")

def increment_interaction():
    """Incrementa contador interacciones"""
    context = load_context()
    
    if not context:
        print("⚠️  Contexto no existe, creando nuevo...")
        return
    
    # Incrementar contador
    context['meta']['interaction_count'] += 1
    count = context['meta']['interaction_count']
    
    print(f"📊 Interacción #{count}")
    
    # Actualizar timestamp
    context['meta']['last_updated'] = datetime.now().isoformat()
    
    # Si llegamos a múltiplo de 5, hacer actualización completa
    if count % UPDATE_INTERVAL == 0:
        print(f"🔄 AUTO-UPDATE #{count} - Actualizando contexto completo...")
        
        # Actualizar métricas
        context = update_metrics(context)
        
        # Comprimir historial antiguo
        context = compress_history(context)
        
        # Generar resumen
        context = generate_summary(context)
        
        print("✅ Actualización completa realizada")
    
    # Guardar
    save_context(context)
    
    return context

def update_metrics(context):
    """Actualiza métricas del proyecto"""
    
    # Leer CSV ideas
    csv_file = 'data/ideas-validadas.csv'
    if os.path.exists(csv_file):
        with open(csv_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            context['metrics']['ideas_generated'] = len(lines) - 1  # Sin header
    
    # Calcular token usage
    ideas_today = context['metrics']['ideas_generated']
    context['metrics']['daily_token_usage'] = ideas_today * 300
    context['metrics']['token_budget_remaining'] = 100000 - context['metrics']['daily_token_usage']
    
    return context

def compress_history(context):
    """Comprime historial antiguo (mantiene últimas 20 interacciones)"""
    
    if len(context['interaction_history']) > 20:
        # Guardar últimas 20
        recent = context['interaction_history'][-20:]
        
        # Crear resumen de las antiguas
        old = context['interaction_history'][:-20]
        summary = {
            "compressed": True,
            "total_interactions": len(old),
            "date_range": f"{old[0]['date']} to {old[-1]['date']}",
            "main_topics": list(set([i['topic'] for i in old]))
        }
        
        # Reemplazar
        context['interaction_history'] = [summary] + recent
    
    return context

def generate_summary(context):
    """Genera resumen de progreso"""
    
    count = context['meta']['interaction_count']
    
    summary = {
        "generated_at": datetime.now().isoformat(),
        "total_interactions": count,
        "ideas_generated": context['metrics']['ideas_generated'],
        "issues_fixed": len(context['current_issues_fixed']),
        "pending_critical": len(context['pending_critical']),
        "token_usage_efficiency": f"{context['metrics']['token_usage_per_idea']} tokens/idea",
        "status": "On track" if context['metrics']['approval_rate'] > 0.5 else "Needs improvement"
    }
    
    context['summary'] = summary
    
    return context

def add_interaction(topic, decisions=None, files=None):
    """Añade nueva interacción al historial"""
    
    context = load_context()
    
    if not context:
        print("⚠️  Contexto no existe")
        return
    
    interaction = {
        "count": context['meta']['interaction_count'] + 1,
        "date": datetime.now().strftime('%Y-%m-%d'),
        "time": datetime.now().strftime('%H:%M'),
        "topic": topic,
        "decisions": decisions or [],
        "files": files or []
    }
    
    context['interaction_history'].append(interaction)
    context['meta']['interaction_count'] += 1
    context['meta']['last_updated'] = datetime.now().isoformat()
    
    # Verificar si toca auto-update
    if context['meta']['interaction_count'] % UPDATE_INTERVAL == 0:
        print(f"🔄 AUTO-UPDATE triggered at interaction #{context['meta']['interaction_count']}")
        context = update_metrics(context)
        context = compress_history(context)
        context = generate_summary(context)
    
    save_context(context)
    
    print(f"✅ Interacción #{context['meta']['interaction_count']} registrada: {topic}")


if __name__ == "__main__":
    # Ejemplo uso
    add_interaction(
        topic="Separar roadmap meta-desarrollo + auto-update cada 5",
        decisions=[
            "META-ROADMAP.json para mejorar proceso IA-humano",
            "FULL-CONTEXT.json con TODO el contexto",
            "Auto-update cada 5 interacciones"
        ],
        files=[
            "memory-system/META-ROADMAP.json",
            "memory-system/FULL-CONTEXT.json",
            "scripts/auto-update-context.py"
        ]
    )
