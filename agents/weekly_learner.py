"""
weekly_learner.py
Analiza el histórico de ideas cada lunes, identifica patrones de éxito
y actualiza config/prompt_weights.json para que el prompt mejore solo.
"""
import os
import json
from datetime import datetime
from collections import Counter, defaultdict

RUTA_WEIGHTS = "config/prompt_weights.json"
os.makedirs("config", exist_ok=True)

def _cargar_pesos() -> dict:
    if os.path.exists(RUTA_WEIGHTS):
        try:
            with open(RUTA_WEIGHTS, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "verticales_preferidas":   [],
        "verticales_penalizadas":  [],
        "tipos_preferidos":        [],
        "tags_exitosos":           [],
        "ia_tools_top":            [],
        "temperatura_groq":        0.9,
        "umbral_duplicado":        0.42,
        "num_ideas_contexto":      40,
        "ultima_actualizacion":    "",
        "ciclos_completados":      0,
        "score_objetivo":          75,
        "patrones_exitosos":       [],
    }

def analizar_y_aprender() -> dict:
    """
    Lee todas las ideas, detecta patrones de exito y actualiza los pesos.
    Retorna resumen del aprendizaje.
    """
    try:
        from agents.knowledge_base import _cargar
        kb    = _cargar()
        ideas = kb.get("ideas", [])
    except Exception as e:
        return {"error": str(e)}

    if len(ideas) < 5:
        return {"mensaje": f"Solo {len(ideas)} ideas — aprendizaje requiere minimo 5"}

    pesos    = _cargar_pesos()
    exitosas = [i for i in ideas if i.get("score_total", 0) >= 75]
    malas    = [i for i in ideas if i.get("score_total", 0) < 60]
    liked    = [i for i in ideas if i.get("feedback") == "like"]
    disliked = [i for i in ideas if i.get("feedback") == "dislike"]

    # Verticales: puntaje combinado score + feedback
    v_exito:   Counter = Counter(i.get("vertical","?") for i in exitosas)
    v_liked:   Counter = Counter(i.get("vertical","?") for i in liked)
    v_dislike: Counter = Counter(i.get("vertical","?") for i in disliked)
    v_malas:   Counter = Counter(i.get("vertical","?") for i in malas)

    puntaje_v: dict = defaultdict(float)
    for v, c in v_exito.items():  puntaje_v[v] += c * 2.0
    for v, c in v_liked.items():  puntaje_v[v] += c * 3.0
    for v, c in v_dislike.items():puntaje_v[v] -= c * 2.5
    for v, c in v_malas.items():  puntaje_v[v] -= c * 1.0

    v_preferidas  = [v for v,p in sorted(puntaje_v.items(), key=lambda x:-x[1]) if p > 0][:5]
    v_penalizadas = [v for v,p in sorted(puntaje_v.items(), key=lambda x:x[1])  if p < 0][:5]

    # Tipos con mejor promedio
    t_exito: Counter = Counter(i.get("tipo","?") for i in exitosas + liked)
    tipos_pref = [t for t,_ in t_exito.most_common(3)]

    # Tags en ideas exitosas
    tags_c: Counter = Counter()
    for i in exitosas + liked:
        for t in (i.get("tags") or []):
            tags_c[t] += 1
    tags_exitosos = [t for t,_ in tags_c.most_common(8)]

    # Herramientas IA en ideas exitosas
    ia_c: Counter = Counter()
    for i in exitosas + liked:
        h = i.get("herramienta_ia","")
        if h:
            ia_c[h[:50]] += 1
    ia_tools_top = [t for t,_ in ia_c.most_common(5)]

    # Patrones vertical+tipo exitosos
    pat_c: Counter = Counter()
    for i in exitosas:
        pat = f"{i.get('vertical','?')}/{i.get('tipo','?')}"
        pat_c[pat] += 1
    patrones = [p for p,_ in pat_c.most_common(5)]

    # Score objetivo: 5% por encima del promedio actual
    scores_todos = [i.get("score_total",0) for i in ideas if i.get("score_total",0) > 0]
    promedio = round(sum(scores_todos)/len(scores_todos), 1) if scores_todos else 70
    score_objetivo = min(90, round(promedio * 1.05, 1))

    # Temperatura: sube si va bien, baja si va mal
    temperatura = pesos.get("temperatura_groq", 0.9)
    if promedio >= 80:
        temperatura = min(0.95, round(temperatura + 0.02, 2))
    elif promedio < 65:
        temperatura = max(0.75, round(temperatura - 0.03, 2))

    # Umbral anti-duplicado: mas estricto con mas ideas
    umbral = 0.42
    if len(ideas) > 100: umbral = 0.30
    elif len(ideas) > 50:  umbral = 0.35

    pesos_nuevos = {
        "verticales_preferidas":   v_preferidas,
        "verticales_penalizadas":  v_penalizadas,
        "tipos_preferidos":        tipos_pref,
        "tags_exitosos":           tags_exitosos,
        "ia_tools_top":            ia_tools_top,
        "temperatura_groq":        temperatura,
        "umbral_duplicado":        umbral,
        "num_ideas_contexto":      min(60, max(30, len(ideas))),
        "ultima_actualizacion":    datetime.now().isoformat(),
        "ciclos_completados":      pesos.get("ciclos_completados", 0) + 1,
        "score_objetivo":          score_objetivo,
        "patrones_exitosos":       patrones,
        "stats": {
            "total_ideas":     len(ideas),
            "exitosas_pct":    round(len(exitosas)/len(ideas)*100) if ideas else 0,
            "liked":           len(liked),
            "disliked":        len(disliked),
            "score_promedio":  promedio,
            "score_objetivo":  score_objetivo,
        }
    }

    os.makedirs("config", exist_ok=True)
    with open(RUTA_WEIGHTS, "w", encoding="utf-8") as f:
        json.dump(pesos_nuevos, f, ensure_ascii=False, indent=2)

    resumen = (
        f"Ciclo {pesos_nuevos['ciclos_completados']} completado\n"
        f"{len(ideas)} ideas | {len(exitosas)} exitosas ({pesos_nuevos['stats']['exitosas_pct']}%)\n"
        f"Score promedio: {promedio} -> Objetivo nuevo: {score_objetivo}\n"
        f"Verticales TOP: {', '.join(v_preferidas[:3]) or 'N/A'}\n"
        f"Verticales penalizadas: {', '.join(v_penalizadas[:3]) or 'ninguna'}\n"
        f"Tags exitosos: {', '.join(tags_exitosos[:5]) or 'N/A'}\n"
        f"IA tools top: {', '.join(ia_tools_top[:3]) or 'N/A'}\n"
        f"Temperatura: {temperatura} | Umbral dup: {umbral}"
    )
    print(resumen)
    return {"resumen": resumen, "pesos": pesos_nuevos}

def get_pesos() -> dict:
    return _cargar_pesos()

# aqui finaliza el codigo de agents/weekly_learner.py
