"""
knowledge_base.py — Base de conocimiento con autoaprendizaje.
"""
import os
import re
import json
from datetime import datetime
from collections import Counter

RUTA_KB = "data/knowledge_base.json"
os.makedirs("data", exist_ok=True)

# ── Persistencia ──────────────────────────────────────────────────────────────

def _cargar() -> dict:
    if os.path.exists(RUTA_KB):
        try:
            with open(RUTA_KB, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"ideas": [], "feedback": {}, "acciones": [], "ciclo_aprendizaje": 0}

def _guardar(kb: dict):
    with open(RUTA_KB, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

# ── Registro de ideas ─────────────────────────────────────────────────────────

def registrar_idea(idea: dict):
    kb    = _cargar()
    ideas = kb.get("ideas", [])

    scores      = idea.get("scores", {})
    if not isinstance(scores, dict): scores = {}
    score_total = scores.get("score_total", 0)

    entrada = {
        "nombre":         idea.get("nombre", "?"),
        "tagline":        idea.get("tagline", ""),
        "problema":       idea.get("problema", "")[:300],
        "solucion":       idea.get("solucion", "")[:300],
        "vertical":       idea.get("vertical", "?"),
        "tipo":           idea.get("tipo", "?"),
        "tags":           idea.get("tags", []) if isinstance(idea.get("tags"), list) else [],
        "herramienta_ia": idea.get("herramienta_ia_clave", ""),
        "scores":         scores,
        "score_total":    score_total,
        "fecha":          datetime.now().strftime("%Y-%m-%d %H:%M"),
        "feedback":       kb.get("feedback", {}).get(idea.get("nombre", "?"), ""),
        "landing_url":    idea.get("landing_url", ""),
    }
    ideas.append(entrada)
    kb["ideas"] = ideas

    _registrar_accion(kb, "idea_generada", {
        "nombre":   entrada["nombre"],
        "score":    score_total,
        "vertical": entrada["vertical"],
    })

    _guardar(kb)

    # Auto-aprendizaje incremental cada 3 ideas (a partir de 5)
    if len(ideas) >= 5 and len(ideas) % 3 == 0:
        _aprendizaje_incremental(kb)

def _registrar_accion(kb: dict, tipo: str, datos: dict):
    acciones = kb.get("acciones", [])
    acciones.append({"tipo": tipo, "datos": datos, "ts": datetime.now().isoformat()})
    kb["acciones"] = acciones[-200:]

# ── Aprendizaje incremental ───────────────────────────────────────────────────

def _aprendizaje_incremental(kb: dict):
    """Aprendizaje ligero cada 3 ideas. Actualiza pesos dinámicos."""
    try:
        ideas    = kb.get("ideas", [])
        feedback = kb.get("feedback", {})
        exitosas = [i for i in ideas if i.get("score_total", 0) >= 75]
        liked    = [i for i in ideas if feedback.get(i.get("nombre", "")) == "like"]
        disliked = [i for i in ideas if feedback.get(i.get("nombre", "")) == "dislike"]

        ruta = "config/prompt_weights.json"
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                pesos = json.load(f)
        except:
            pesos = {}

        # Tags e IA tools de ideas exitosas + liked
        tags_c: Counter = Counter()
        ia_c:   Counter = Counter()
        for i in exitosas + liked:
            for t in (i.get("tags") or []):
                tags_c[t] += 1
            h = i.get("herramienta_ia", "")
            if h: ia_c[h[:60]] += 1

        if tags_c:
            pesos["tags_exitosos"]  = [t for t, _ in tags_c.most_common(8)]
        if ia_c:
            pesos["ia_tools_top"]   = [t for t, _ in ia_c.most_common(5)]

        # Verticales preferidas y penalizadas
        v_liked    = Counter(i.get("vertical", "?") for i in liked)
        v_disliked = Counter(i.get("vertical", "?") for i in disliked)
        v_exitosas = Counter(i.get("vertical", "?") for i in exitosas)

        if v_exitosas or v_liked:
            merged = Counter()
            for v, c in v_exitosas.items(): merged[v] += c
            for v, c in v_liked.items():    merged[v] += c * 2  # liked pesa doble
            pesos["verticales_preferidas"] = [v for v, _ in merged.most_common(5)]

        if v_disliked:
            pesos["verticales_penalizadas"] = [v for v, _ in v_disliked.most_common(4)]

        # Patrones exitosos: vertical + tipo
        pat_c: Counter = Counter()
        for i in exitosas + liked:
            pat = f"{i.get('vertical','?')} + {i.get('tipo','?')}"
            pat_c[pat] += 1
        if pat_c:
            pesos["patrones_exitosos"] = [p for p, _ in pat_c.most_common(4)]

        # Score objetivo: 3% por encima del promedio reciente
        scores_rec = [i.get("score_total", 0) for i in ideas[-20:] if i.get("score_total", 0) > 0]
        if scores_rec:
            promedio = sum(scores_rec) / len(scores_rec)
            pesos["score_objetivo"] = min(90, round(promedio * 1.03, 1))

        # Ajuste temperatura: bajar si muchos duplicados, subir si scores bajos
        scores_tot = [i.get("score_total", 0) for i in ideas[-10:] if i.get("score_total", 0) > 0]
        if scores_tot:
            promedio_10 = sum(scores_tot) / len(scores_tot)
            temp_actual = pesos.get("temperatura_groq", 0.85)
            if promedio_10 < 70:
                pesos["temperatura_groq"] = min(0.95, round(temp_actual + 0.02, 2))
            elif promedio_10 > 82:
                pesos["temperatura_groq"] = max(0.75, round(temp_actual - 0.01, 2))

        pesos["ciclos_completados"]                  = pesos.get("ciclos_completados", 0) + 1
        pesos["ultima_actualizacion_incremental"]    = datetime.now().isoformat()
        pesos["total_ideas_en_momento_aprendizaje"]  = len(ideas)

        os.makedirs("config", exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(pesos, f, ensure_ascii=False, indent=2)

        kb["ciclo_aprendizaje"] = kb.get("ciclo_aprendizaje", 0) + 1
        _guardar(kb)
        print(f"🧠 Aprendizaje incremental #{pesos['ciclos_completados']} completado")

    except Exception as e:
        print(f"⚠️ Aprendizaje incremental: {e}")

# ── Feedback ──────────────────────────────────────────────────────────────────

def registrar_feedback(nombre: str, accion: str):
    kb = _cargar()
    fb = kb.get("feedback", {})
    fb[nombre] = accion
    kb["feedback"] = fb

    for idea in kb.get("ideas", []):
        if idea.get("nombre", "").lower() == nombre.lower():
            idea["feedback"] = accion
            break

    _registrar_accion(kb, f"feedback_{accion}", {"nombre": nombre})
    _guardar(kb)

    # Aprendizaje inmediato tras feedback — señal muy valiosa
    _aprendizaje_incremental(kb)

# ── Anti-duplicados semánticos ────────────────────────────────────────────────

STOP_WORDS = {
    "el","la","los","las","de","que","en","un","una","y","es","se",
    "del","por","con","para","su","sus","al","lo","le","les","una",
    "esta","este","son","hay","como","mas","pero","si","no","ya"
}

def _vectorizar(idea: dict) -> list:
    texto = " ".join([
        idea.get("nombre",   ""),
        idea.get("tagline",  ""),
        idea.get("problema", "")[:200],
        idea.get("vertical", ""),
        idea.get("tipo",     ""),
        " ".join(idea.get("tags", []) if isinstance(idea.get("tags"), list) else []),
    ]).lower()

    palabras = set(re.sub(r"[^a-záéíóúüñ\s]", "", texto).split())
    return list(palabras - STOP_WORDS)

def _similitud(v1: list, v2: list) -> float:
    if not v1 or not v2: return 0.0
    s1, s2 = set(v1), set(v2)
    inter  = len(s1 & s2)
    union  = len(s1 | s2)
    return inter / union if union > 0 else 0.0

def es_duplicado(idea_nueva: dict, umbral: float = 0.38) -> tuple:
    kb    = _cargar()
    ideas = kb.get("ideas", [])
    if not ideas:
        return False, ""

    v_nueva     = _vectorizar(idea_nueva)
    max_sim     = 0.0
    mas_similar = ""

    for idea_existente in ideas[-60:]:
        v_existente = _vectorizar(idea_existente)
        sim = _similitud(v_nueva, v_existente)
        if sim > max_sim:
            max_sim     = sim
            mas_similar = idea_existente.get("nombre", "?")

    print(f"   Anti-dup: similitud={max_sim:.3f} (umbral={umbral}) vs '{mas_similar}'")
    return (max_sim >= umbral, mas_similar)

# ── Contexto para prompt ──────────────────────────────────────────────────────

def get_contexto_para_prompt() -> dict:
    kb    = _cargar()
    ideas = kb.get("ideas", [])

    if not ideas:
        return {
            "ideas_previas": "ninguna aun", "total_analizadas": 0,
            "tasa_exito": "N/A", "score_promedio": 0,
            "verticales_saturadas": "", "verticales_disliked": "",
        }

    ideas_str = []
    for i in ideas[-50:]:
        fb    = " [👍LIKED]" if i.get("feedback") == "like" else " [👎DISLIKED]" if i.get("feedback") == "dislike" else ""
        score = i.get("score_total", 0)
        ideas_str.append(
            f"- {i.get('nombre','?')} ({i.get('vertical','?')}/{i.get('tipo','?')}) "
            f"Score:{score}{fb} | {i.get('tagline','')[:80]}"
        )

    scores_validos = [i.get("score_total", 0) for i in ideas if i.get("score_total", 0) > 0]
    score_promedio = round(sum(scores_validos) / len(scores_validos), 1) if scores_validos else 0
    exitosas       = len([i for i in ideas if i.get("score_total", 0) >= 75])
    tasa_exito     = f"{round(exitosas / len(ideas) * 100)}%" if ideas else "N/A"

    v_count   = Counter(i.get("vertical", "?") for i in ideas)
    saturadas = [v for v, c in v_count.most_common() if c >= 3]

    fb_map   = kb.get("feedback", {})
    disliked = [i for i in ideas if fb_map.get(i.get("nombre", "")) == "dislike"]
    v_dis    = list(set(i.get("vertical", "?") for i in disliked))

    return {
        "ideas_previas":        "\n".join(ideas_str),
        "total_analizadas":     len(ideas),
        "tasa_exito":           tasa_exito,
        "score_promedio":       score_promedio,
        "verticales_saturadas": ", ".join(saturadas[:4]),
        "verticales_disliked":  ", ".join(v_dis[:3]),
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

    fb_map   = kb.get("feedback", {})
    scores   = [i.get("score_total", 0) for i in ideas if i.get("score_total", 0) > 0]
    promedio = round(sum(scores) / len(scores), 1) if scores else 0
    mejor    = max(ideas, key=lambda x: x.get("score_total", 0))
    exitosas = len([i for i in ideas if i.get("score_total", 0) >= 75])

    v_count  = Counter(i.get("vertical", "?") for i in ideas if i.get("score_total", 0) >= 75)
    t_count  = Counter(i.get("tipo",     "?") for i in ideas if i.get("score_total", 0) >= 75)
    ia_count = Counter(i.get("herramienta_ia", "") for i in ideas if i.get("herramienta_ia", ""))
    liked    = [i.get("nombre", "?") for i in ideas if fb_map.get(i.get("nombre", "")) == "like"]

    return {
        "total_ideas":        len(ideas),
        "score_promedio":     promedio,
        "mejor_score":        mejor.get("score_total", 0),
        "mejor_idea":         mejor.get("nombre", "?"),
        "mejor_vertical":     v_count.most_common(1)[0][0] if v_count else "N/A",
        "mejor_tipo":         t_count.most_common(1)[0][0] if t_count else "N/A",
        "tasa_exito":         f"{round(exitosas / len(ideas) * 100)}%" if ideas else "N/A",
        "ia_tools_top":       ia_count.most_common(1)[0][0][:50] if ia_count else "N/A",
        "ideas_liked":        liked,
        "ciclos_aprendizaje": kb.get("ciclo_aprendizaje", 0),
    }

def get_top_ideas(n: int = 5) -> list:
    kb    = _cargar()
    ideas = kb.get("ideas", [])
    fb_map = kb.get("feedback", {})
    for i in ideas:
        i["feedback"] = fb_map.get(i.get("nombre", ""), "")
    return sorted(ideas, key=lambda x: x.get("score_total", 0), reverse=True)[:n]

def contar_pendientes() -> int:
    try:
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta): return 0
        with open(ruta, newline="", encoding="utf-8") as f:
            return max(0, sum(1 for _ in f) - 1)
    except: return 0

# aqui finaliza el codigo de agents/knowledge_base.py
