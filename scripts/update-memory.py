import json
import os
from datetime import datetime

def update_memory(new_context):
    """Actualiza memoria persistente con nuevo contexto"""
    
    memory_file = 'memory-system/conversation-memory.json'
    
    # Cargar memoria existente
    if os.path.exists(memory_file):
        with open(memory_file, 'r', encoding='utf-8') as f:
            memory = json.load(f)
    else:
        memory = {
            "project": "ValidationIdea",
            "started": datetime.now().strftime('%Y-%m-%d'),
            "conversations": [],
            "pending_tasks": []
        }
    
    # Actualizar timestamp
    memory["last_updated"] = datetime.now().isoformat()
    
    # Añadir nueva conversación
    if "conversation" in new_context:
        memory["conversations"].append({
            "date": datetime.now().strftime('%Y-%m-%d'),
            "time": datetime.now().strftime('%H:%M'),
            "topic": new_context.get("topic", "General"),
            "decisions": new_context.get("decisions", []),
            "files_modified": new_context.get("files", [])
        })
    
    # Actualizar tareas
    if "task_update" in new_context:
        for task in memory["pending_tasks"]:
            if task["id"] == new_context["task_update"]["id"]:
                task["status"] = new_context["task_update"]["status"]
    
    # Guardar
    os.makedirs('memory-system', exist_ok=True)
    with open(memory_file, 'w', encoding='utf-8') as f:
        json.dump(memory, f, indent=2, ensure_ascii=False)
    
    print(f"✅ Memoria actualizada: {memory_file}")
    return memory


def load_memory():
    """Carga memoria para recuperar contexto"""
    memory_file = 'memory-system/conversation-memory.json'
    
    if os.path.exists(memory_file):
        with open(memory_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    return None


if __name__ == "__main__":
    # Ejemplo uso
    update_memory({
        "conversation": True,
        "topic": "Fix dashboard + nuevo agente investigador",
        "decisions": [
            "Dashboard botones ahora usan rutas correctas",
            "Botón descarga CSV añadido",
            "Nuevo agente researcher_agent.py"
        ],
        "files": [
            "agents/dashboard_generator.py",
            "agents/researcher_agent.py",
            "memory-system/conversation-memory.json"
        ]
    })
