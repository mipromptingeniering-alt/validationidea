# agents/knowledge_base.py — versión v2

import json, os
from datetime import datetime
from collections import Counter

KB_PATH = "data/kb.json"

def _cargar():
    if not os.path.exists(KB_PATH):
        return {"ideas": [], "patrones": {}, "tendencias": []}
    with open(KB_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def _guardar(kb):
    os.makedirs("data", exist_ok=True)
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

def registrar_idea(idea: dict):
    kb = _cargar()
    
    # Guardar idea con timestamp
    idea["_registrada"] = datetime.now().isoformat()
    kb["ideas"].append(idea)
    
    # Actualizar patrones automáticamente
    _actualizar_patrones(kb)
    _guardar(kb)

def _actualizar_patrones(kb):
    """Aprende qué funciona: extrae patrones de ideas con score alto"""
    ideas = kb["ideas"]
    if not ideas:
        return
    
    # Ideas exitosas = score > 75
    exitosas = [i for i in ideas if i.get("scores", {}).get("score_total", 0) >= 75]
    
    # Patrones de verticales exitosas
    verticales = Counter(i.get("vertical", "") for i in exitosas)
    tipos = Counter(i.get("tipo", "") for i in exitosas)
    tags = Counter(t for i in exitosas for t in i.get("tags", []))
    
    # Score promedio por vertical
    score_por_vertical = {}
    for v in set(i.get("vertical", "") for i in ideas):
        grupo = [i["scores"]["score_total"] for i in ideas 
                 if i.get("vertical") == v and "scores" in i]
        if grupo:
            score_por_vertical[v] = round(sum(grupo)/len(grupo), 1)
    
    kb["patrones"] = {
        "mejores_verticales": [v for v, _ in verticales.most_common(3)],
        "mejores_tipos": [t for t, _ in tipos.most_common(2)],
        "tags_exitosos": [t for t, _ in tags.most_common(5)],
        "score_por_vertical": score_por_vertical,
        "total_analizadas": len(ideas),
        "total_exitosas": len(exitosas),
        "tasa_exito": f"{round(len(exitosas)/max(len(ideas),1)*100,1)}%",
        "actualizado": datetime.now().isoformat()
    }

def get_contexto_para_prompt():
    """Devuelve contexto rico para mejorar el siguiente prompt"""
    kb = _cargar()
    patrones = kb.get("patrones", {})
    ideas = kb.get("ideas", [])
    
    nombres_previos = [i.get("nombre", "") for i in ideas[-30:]]  # últimas 30
    
    return {
        "ideas_previas": ", ".join(nombres_previos),
        "mejores_verticales": ", ".join(patrones.get("mejores_verticales", [])),
        "tags_exitosos": ", ".join(patrones.get("tags_exitosos", [])),
        "score_por_vertical": json.dumps(patrones.get("score_por_vertical", {})),
        "tasa_exito": patrones.get("tasa_exito", "N/A"),
        "total_analizadas": patrones.get("total_analizadas", 0)
    }

def get_top_ideas(n=5):
    kb = _cargar()
    ideas = kb.get("ideas", [])
    ordenadas = sorted(ideas, 
                       key=lambda x: x.get("scores", {}).get("score_total", 0), 
                       reverse=True)
    return ordenadas[:n]

def get_stats():
    kb = _cargar()
    patrones = kb.get("patrones", {})
    ideas = kb.get("ideas", [])
    scores = [i.get("scores", {}).get("score_total", 0) for i in ideas if "scores" in i]
    return {
        "total_ideas": len(ideas),
        "score_promedio": round(sum(scores)/max(len(scores),1), 1),
        "mejor_score": max(scores) if scores else 0,
        "mejor_vertical": patrones.get("mejores_verticales", ["N/A"])[0] if patrones.get("mejores_verticales") else "N/A",
        "mejor_tipo": patrones.get("mejores_tipos", ["N/A"])[0] if patrones.get("mejores_tipos") else "N/A",
        "mejor_idea": get_top_ideas(1)[0].get("nombre", "N/A") if get_top_ideas(1) else "N/A",
        "tasa_exito": patrones.get("tasa_exito", "N/A")
    }
