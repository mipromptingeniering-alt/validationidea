"""
weekly_learner.py - Aprende de las ideas generadas y ajusta pesos del sistema
"""
import os, json
from datetime import datetime
from collections import Counter

WEIGHTS_FILE  = "config/prompt_weights.json"
KB_FILE       = "data/knowledge_base.json"
LEARNER_FILE  = "data/learner_state.json"

def _load_kb():
    try:
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"ideas": []}

def _load_weights():
    try:
        with open(WEIGHTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "temperatura_groq":       0.85,
            "umbral_duplicado":       0.38,
            "verticales_preferidas":  [],
            "verticales_penalizadas": [],
            "tags_exitosos":          [],
            "score_objetivo":         75,
        }

def _save_weights(w):
    os.makedirs("config", exist_ok=True)
    with open(WEIGHTS_FILE, "w", encoding="utf-8") as f:
        json.dump(w, f, ensure_ascii=False, indent=2)

def _load_state():
    try:
        with open(LEARNER_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"ciclo": 0, "ultimo_aprendizaje": ""}

def _save_state(s):
    os.makedirs("data", exist_ok=True)
    with open(LEARNER_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)

def analizar_y_aprender():
    """
    Analiza todas las ideas, detecta patrones y ajusta pesos.
    Devuelve dict con resultados del aprendizaje.
    """
    kb     = _load_kb()
    ideas  = kb.get("ideas", [])
    state  = _load_state()
    pesos  = _load_weights()

    ciclo = state.get("ciclo", 0) + 1
    state["ciclo"] = ciclo
    state["ultimo_aprendizaje"] = datetime.now().isoformat()

    if not ideas:
        _save_state(state)
        return {
            "ciclo": ciclo, "total_ideas": 0, "ideas_exitosas": 0,
            "pct_exito": 0, "score_anterior": 0, "score_objetivo": 75,
            "nuevos_pesos": pesos, "resumen": "Sin ideas para aprender",
        }

    # Clasificar ideas
    UMBRAL_EXITO = 75
    exitosas  = []
    fallidas  = []
    for idea in ideas:
        s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
        fb = idea.get("feedback",{}) if isinstance(idea.get("feedback"),dict) else {}
        # Exito = score >= umbral O tiene likes
        if s >= UMBRAL_EXITO or fb.get("likes",0) > 0:
            exitosas.append(idea)
        elif s > 0:
            fallidas.append(idea)

    total    = len(ideas)
    n_exit   = len(exitosas)
    pct      = round(n_exit / total * 100, 1) if total > 0 else 0

    scores_todos = [
        i.get("scores",{}).get("score_total",0)
        for i in ideas
        if isinstance(i.get("scores"),dict) and i["scores"].get("score_total",0) > 0
    ]
    score_prom = round(sum(scores_todos)/len(scores_todos),1) if scores_todos else 0

    # Verticales exitosos
    verts_exit = [str(i.get("vertical","")).lower() for i in exitosas if i.get("vertical")]
    verts_fail = [str(i.get("vertical","")).lower() for i in fallidas if i.get("vertical")]
    top_verts  = [v for v,_ in Counter(verts_exit).most_common(5) if v]
    bad_verts  = [v for v,_ in Counter(verts_fail).most_common(3)
                  if v and v not in top_verts]

    # Tags exitosos
    tags_exit = []
    for i in exitosas:
        t = i.get("tags",[])
        if isinstance(t, list):
            tags_exit.extend([str(x).lower() for x in t])
    top_tags = [t for t,_ in Counter(tags_exit).most_common(10) if t]

    # Ajustar temperatura
    temperatura = pesos.get("temperatura_groq", 0.85)
    if pct >= 70:
        temperatura = min(0.95, temperatura + 0.02)
    elif pct < 40:
        temperatura = max(0.60, temperatura - 0.05)

    # Ajustar umbral duplicado
    umbral = pesos.get("umbral_duplicado", 0.38)
    if total > 30:
        umbral = min(0.45, umbral + 0.01)

    # Nuevo score objetivo
    score_obj = max(70, min(88, round(score_prom * 1.05)))

    # Actualizar pesos
    pesos.update({
        "temperatura_groq":       round(temperatura, 2),
        "umbral_duplicado":       round(umbral, 2),
        "verticales_preferidas":  top_verts[:5],
        "verticales_penalizadas": bad_verts[:3],
        "tags_exitosos":          top_tags[:10],
        "score_objetivo":         score_obj,
        "ultimo_ciclo":           ciclo,
        "ultimo_aprendizaje":     datetime.now().isoformat(),
        "estadisticas": {
            "total_ideas":    total,
            "ideas_exitosas": n_exit,
            "pct_exito":      pct,
            "score_promedio": score_prom,
        }
    })
    _save_weights(pesos)
    _save_state(state)

    print(
        f"🧠 Aprendizaje ciclo {ciclo}: "
        f"{total} ideas | {n_exit} exitosas ({pct}%) | "
        f"Score prom: {score_prom} | Obj: {score_obj} | "
        f"Temp: {temperatura:.2f}"
    )

    return {
        "ciclo":           ciclo,
        "total_ideas":     total,
        "ideas_exitosas":  n_exit,
        "pct_exito":       pct,
        "score_anterior":  score_prom,
        "score_objetivo":  score_obj,
        "nuevos_pesos":    pesos,
        "resumen":         f"{n_exit}/{total} exitosas, temp={temperatura:.2f}",
    }

# fin agents/weekly_learner.py
