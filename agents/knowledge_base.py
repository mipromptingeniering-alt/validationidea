"""
knowledge_base.py
Base de conocimiento con autoaprendizaje después de cada acción.
"""
import os
import json
import math
from datetime import datetime
from collections import Counter

RUTA_KB = "data/knowledge_base.json"
os.makedirs("data", exist_ok=True)

# ── Persistencia ─────────────────────────────────────────────────────────────

def _cargar() -> dict:
    if os.path.exists(RUTA_KB):
        try:
            with open(RUTA_KB, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "ideas":            [],
        "feedback":         {},
        "acciones":         [],
        "ciclo_aprendizaje": 0,
    }

def _guardar(kb: dict):
    with open(RUTA_KB, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

# ── Registro de ideas ─────────────────────────────────────────────────────────

def registrar_idea(idea: dict):
    kb    = _cargar()
    ideas = kb.get("ideas", [])

    scores = idea.get("scores", {})
    if not isinstance(scores, dict): scores = {}
    score_total = scores.get("score_total", 0)

    entrada = {
        "nombre":          idea.get("nombre","?"),
        "tagline":         idea.get("tagline",""),
        "problema":        idea.get("problema","")[:300],
        "solucion":        idea.get("solucion","")[:300],
        "vertical":        idea.get("vertical","?"),
        "tipo":            idea.get("tipo","?"),
        "tags":            idea.get("tags", []),
        "herramienta_ia":  idea.get("herramienta_ia_clave",""),
        "scores":          scores,
        "score_total":     score_total,
        "fecha":           datetime.now().strftime("%Y-%m-%d %H:%M"),
        "feedback":        kb.get("feedback",{}).get(idea.get("nombre","?"), ""),
        "landing_url":     idea.get("landing_url",""),
    }
    ideas.append(entrada)
    kb["ideas"] = ideas

    # Registrar accion
    _registrar_accion(kb, "idea_generada", {
        "nombre":    entrada["nombre"],
        "score":     score_total,
        "vertical":  entrada["vertical"],
    })

    _guardar(kb)

    # Auto-aprendizaje incremental tras cada idea (>=5 ideas)
    if len(ideas) >= 5 and len(ideas) % 3 == 0:
        _aprendizaje_incremental(kb)

def _registrar_accion(kb: dict, tipo: str, datos: dict):
    acciones = kb.get("acciones", [])
    acciones.append({
        "tipo":  tipo,
        "datos": datos,
        "ts":    datetime.now().isoformat(),
    })
    # Mantener solo las últimas 200 acciones
    kb["acciones"] = acciones[-200:]

# ── Auto-aprendizaje incremental ──────────────────────────────────────────────

def _aprendizaje_incremental(kb: dict):
    """
    Aprendizaje ligero que se ejecuta cada 3 ideas.
    Actualiza solo los campos más dinámicos de prompt_weights.json.
    """
    try:
        ideas    = kb.get("ideas", [])
        feedback = kb.get("feedback", {})
        exitosas = [i for i in ideas if i.get("score_total", 0) >= 75]
        liked    = [i for i in ideas if feedback.get(i.get("nombre","")) == "like"]

        if not exitosas and not liked:
            return

        ruta = "config/prompt_weights.json"
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                pesos = json.load(f)
        except:
            pesos = {}

        # Actualizar solo tags y herramientas IA (cambios rápidos)
        tags_c: Counter = Counter()
        ia_c:   Counter = Counter()
        for i in exitosas + liked:
            for t in (i.get("tags") or []):
                tags_c[t] += 1
            h = i.get("herramienta_ia","")
            if h: ia_c[h[:50]] += 1

        if tags_c:
            pesos["tags_exitosos"] = [t for t,_ in tags_c.most_common(8)]
        if ia_c:
            pesos["ia_tools_top"]  = [t for t,_ in ia_c.most_common(5)]

        # Score objetivo: siempre apuntar 3% por encima del promedio reciente
        scores_recientes = [i.get("score_total",0) for i in ideas[-20:] if i.get("score_total",0) > 0]
        if scores_recientes:
            promedio_reciente = sum(scores_recientes) / len(scores_recientes)
            pesos["score_objetivo"] = min(90, round(promedio_reciente * 1.03, 1))

        pesos["ultima_actualizacion_incremental"] = datetime.now().isoformat()
        os.makedirs("config", exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(pesos, f, ensure_ascii=False, indent=2)

        kb["ciclo_aprendizaje"] = kb.get("ciclo_aprendizaje", 0) + 1
        _guardar(kb)

    except Exception as e:
        print(f"⚠️ Aprendizaje incremental: {e}")

# ── Feedback ─────────────────────────────────────────────────────────────────

def registrar_feedback(nombre: str, accion: str):
    kb = _cargar()
    fb = kb.get("feedback", {})
    fb[nombre] = accion
    kb["feedback"] = fb

    # Actualizar feedback en la idea dentro de kb
    for idea in kb.get("ideas", []):
        if idea.get("nombre","").lower() == nombre.lower():
            idea["feedback"] = accion
            break

    _registrar_accion(kb, f"feedback_{accion}", {"nombre": nombre})
    _guardar(kb)

    # Aprendizaje inmediato tras feedback (señal muy valiosa)
    _aprendizaje_incremental(kb)

# ── Anti-duplicados semánticos ────────────────────────────────────────────────

def _vectorizar(idea: dict) -> list:
    texto = " ".join([
        idea.get("nombre",""),
        idea.get("tagline",""),
        idea.get("problema","")[:200],
        idea.get("vertical",""),
        idea.get("tipo",""),
        " ".join(idea.get("tags",[]) if isinstance(idea.get("tags"),list) else []),
    ]).lower()

    palabras = set(re.sub(r"[^a-záéíóúüñ\s]", "", texto).split()) if texto else set()
    STOP = {"el","la","los","las","de","que","en","un","una","y","es","se","del","por","con","para","su","sus","al"}
    return list(palabras - STOP)

def _similitud(v1: list, v2: list) -> float:
    if not v1 or not v2: return 0.0
    s1, s2 = set(v1), set(v2)
    inter  = len(s1 & s2)
    union  = len(s1 | s2)
    return inter / union if union > 0 else 0.0

def es_duplicado(idea_nueva: dict, umbral: float = 0.38) -> tuple:
    import re as _re
    global re
    re = _re

    kb    = _cargar()
    ideas = kb.get("ideas", [])
    if not ideas:
        return False, ""

    v_nueva = _vectorizar(idea_nueva)
    max_sim  = 0.0
    mas_similar = ""

    for idea_existente in ideas[-60:]:  # solo las últimas 60 para eficiencia
        v_existente = _vectorizar(idea_existente)
        sim = _similitud(v_nueva, v_existente)
        if sim > max_sim:
            max_sim     = sim
            mas_similar = idea_existente.get("nombre","?")

    print(f"   Anti-dup: max_similitud={max_sim:.3f} (umbral={umbral}) vs '{mas_similar}'")
    return (max_sim >= umbral, mas_similar)

# ── Contexto para prompt ──────────────────────────────────────────────────────

def get_contexto_para_prompt() -> dict:
    kb    = _cargar()
    ideas = kb.get("ideas", [])

    if not ideas:
        return {
            "ideas_previas": "ninguna aun",
            "total_analizadas": 0,
            "tasa_exito": "N/A",
            "score_promedio": 0,
            "verticales_saturadas": "",
            "verticales_disliked": "",
        }

    # Ideas previas: nombre + problema resumido para contexto rico
    ideas_str_parts = []
    for i in ideas[-50:]:
        fb    = " [👍LIKED]" if i.get("feedback") == "like" else " [👎DISLIKED]" if i.get("feedback") == "dislike" else ""
        score = i.get("score_total", 0)
        ideas_str_parts.append(
            f"- {i.get('nombre','?')} ({i.get('vertical','?')}/{i.get('tipo','?')}) "
            f"Score:{score}{fb} | {i.get('tagline','')[:80]}"
        )
    ideas_previas = "\n".join(ideas_str_parts)

    scores_validos = [i.get("score_total",0) for i in ideas if i.get("score_total",0) > 0]
    score_promedio = round(sum(scores_validos)/len(scores_validos),1) if scores_validos else 0
    exitosas       = len([i for i in ideas if i.get("score_total",0) >= 75])
    tasa_exito     = f"{round(exitosas/len(ideas)*100)}%" if ideas else "N/A"

    # Verticales más repetidas (saturadas)
    v_count = Counter(i.get("vertical","?") for i in ideas)
    saturadas = [v for v,c in v_count.most_common() if c >= 3]

    # Verticales de ideas disliked
    fb_map = kb.get("feedback", {})
    disliked = [i for i in ideas if fb_map.get(i.get("nombre","")) == "dislike"]
    v_disliked = list(set(i.get("vertical","?") for i in disliked))

    return {
        "ideas_previas":       ideas_previas,
        "total_analizadas":    len(ideas),
        "tasa_exito":          tasa_exito,
        "score_promedio":      score_promedio,
        "verticales_saturadas": ", ".join(saturadas[:4]),
        "verticales_disliked":  ", ".join(v_disliked[:3]),
    }

# ── Stats ─────────────────────────────────────────────────────────────────────

def get_stats() -> dict:
    kb    = _cargar()
    ideas = kb.get("ideas", [])
    if not ideas:
        return {
            "total_ideas": 0, "score_promedio": 0, "mejor_score": 0,
            "mejor_idea": "N/A", "mejor_vertical": "N/A", "mejor_tipo": "N/A",
            "tasa_exito": "N/A", "ia_tools_top": "N/A", "ideas_liked": [],
            "ciclos_aprendizaje": 0,
        }

    fb_map     = kb.get("feedback", {})
    scores     = [i.get("score_total",0) for i in ideas if i.get("score_total",0) > 0]
    promedio   = round(sum(scores)/len(scores),1) if scores else 0
    mejor      = max(ideas, key=lambda x: x.get("score_total",0))
    exitosas   = len([i for i in ideas if i.get("score_total",0) >= 75])

    v_count = Counter(i.get("vertical","?") for i in ideas if i.get("score_total",0) >= 75)
    t_count = Counter(i.get("tipo","?")     for i in ideas if i.get("score_total",0) >= 75)
    ia_count= Counter(i.get("herramienta_ia","") for i in ideas if i.get("herramienta_ia",""))

    liked = [i.get("nombre","?") for i in ideas if fb_map.get(i.get("nombre","")) == "like"]

    return {
        "total_ideas":          len(ideas),
        "score_promedio":       promedio,
        "mejor_score":          mejor.get("score_total",0),
        "mejor_idea":           mejor.get("nombre","?"),
        "mejor_vertical":       v_count.most_common(1)[0][0] if v_count else "N/A",
        "mejor_tipo":           t_count.most_common(1)[0][0] if t_count else "N/A",
        "tasa_exito":           f"{round(exitosas/len(ideas)*100)}%" if ideas else "N/A",
        "ia_tools_top":         ia_count.most_common(1)[0][0][:50] if ia_count else "N/A",
        "ideas_liked":          liked,
        "ciclos_aprendizaje":   kb.get("ciclo_aprendizaje", 0),
    }

def get_top_ideas(n: int = 5) -> list:
    kb = _cargar()
    ideas = kb.get("ideas", [])
    fb_map = kb.get("feedback", {})
    for i in ideas:
        i["feedback"] = fb_map.get(i.get("nombre",""), "")
    return sorted(ideas, key=lambda x: x.get("score_total",0), reverse=True)[:n]

def contar_pendientes() -> int:
    try:
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta): return 0
        with open(ruta, newline="", encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)
    except: return 0

# aqui finaliza el codigo de agents/knowledge_base.py
