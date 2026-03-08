import json, os
from datetime import datetime
from collections import Counter

KB_PATH = "data/kb_notion.json"

def _cargar():
    if not os.path.exists(KB_PATH):
        return {"ideas": [], "patrones": {}}
    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"ideas": [], "patrones": {}}

def _guardar(kb):
    os.makedirs("data", exist_ok=True)
    with open(KB_PATH, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

def _actualizar_patrones(kb):
    ideas = kb.get("ideas", [])
    if not ideas:
        return
    exitosas = [i for i in ideas if i.get("score_total", 0) >= 75]
    verticales = Counter(i.get("vertical", "") for i in exitosas)
    tipos      = Counter(i.get("tipo", "")     for i in exitosas)
    tags       = Counter(t for i in exitosas for t in i.get("tags", []))
    score_por_vertical = {}
    for v in set(i.get("vertical", "") for i in ideas if i.get("vertical")):
        grupo = [i["score_total"] for i in ideas if i.get("vertical") == v and i.get("score_total")]
        if grupo:
            score_por_vertical[v] = round(sum(grupo) / len(grupo), 1)
    scores_todos = [i["score_total"] for i in ideas if i.get("score_total")]
    kb["patrones"] = {
        "mejores_verticales":  [v for v, _ in verticales.most_common(3)],
        "mejores_tipos":       [t for t, _ in tipos.most_common(2)],
        "tags_exitosos":       [t for t, _ in tags.most_common(6)],
        "score_por_vertical":  score_por_vertical,
        "total_analizadas":    len(ideas),
        "total_exitosas":      len(exitosas),
        "score_promedio":      round(sum(scores_todos) / max(len(scores_todos), 1), 1),
        "tasa_exito":          f"{round(len(exitosas) / max(len(ideas), 1) * 100, 1)}%",
        "actualizado":         datetime.now().isoformat(),
    }

def registrar_idea(idea: dict):
    kb = _cargar()
    entrada = {
        "nombre":      idea.get("nombre", ""),
        "vertical":    idea.get("vertical", ""),
        "tipo":        idea.get("tipo", ""),
        "tags":        idea.get("tags", []),
        "score_total": idea.get("scores", {}).get("score_total", 0),
        "scores":      idea.get("scores", {}),
        "fecha":       datetime.now().strftime("%Y-%m-%d"),
    }
    kb["ideas"].append(entrada)
    _actualizar_patrones(kb)
    _guardar(kb)

def get_contexto_para_prompt():
    kb = _cargar()
    patrones = kb.get("patrones", {})
    ideas    = kb.get("ideas", [])
    nombres  = [i.get("nombre", "") for i in ideas[-40:] if i.get("nombre")]
    return {
        "ideas_previas":      ", ".join(nombres) if nombres else "ninguna aún",
        "mejores_verticales": ", ".join(patrones.get("mejores_verticales", ["SaaS", "HealthTech"])),
        "tags_exitosos":      ", ".join(patrones.get("tags_exitosos", [])),
        "score_por_vertical": json.dumps(patrones.get("score_por_vertical", {}), ensure_ascii=False),
        "total_analizadas":   patrones.get("total_analizadas", 0),
        "tasa_exito":         patrones.get("tasa_exito", "N/A"),
    }

def get_top_ideas(n=5):
    kb = _cargar()
    ideas = kb.get("ideas", [])
    return sorted(ideas, key=lambda x: x.get("score_total", 0), reverse=True)[:n]

def get_stats():
    kb = _cargar()
    patrones = kb.get("patrones", {})
    ideas    = kb.get("ideas", [])
    top1     = get_top_ideas(1)
    return {
        "total_ideas":    len(ideas),
        "score_promedio": patrones.get("score_promedio", 0),
        "mejor_score":    top1[0].get("score_total", 0) if top1 else 0,
        "mejor_vertical": (patrones.get("mejores_verticales") or ["N/A"])[0],
        "mejor_tipo":     (patrones.get("mejores_tipos")      or ["N/A"])[0],
        "mejor_idea":     top1[0].get("nombre", "N/A") if top1 else "N/A",
        "tasa_exito":     patrones.get("tasa_exito", "N/A"),
    }

def contar_pendientes():
    try:
        import csv
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta):
            return 0
        with open(ruta, newline="", encoding="utf-8") as f:
            return sum(1 for _ in csv.DictReader(f))
    except:
        return 0
