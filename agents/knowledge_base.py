import os
import json
from datetime import datetime
from collections import Counter

RUTA_KB = "data/kb_notion.json"
os.makedirs("data", exist_ok=True)

def _cargar() -> dict:
    if os.path.exists(RUTA_KB):
        try:
            with open(RUTA_KB, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"ideas": [], "stats": {}, "version": 2}

def _guardar(kb: dict):
    with open(RUTA_KB, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)

def _palabras_clave(idea: dict) -> set:
    texto = " ".join([
        idea.get("nombre", ""),
        idea.get("tagline", ""),
        str(idea.get("problema", ""))[:120],
        idea.get("vertical", ""),
        idea.get("tipo", ""),
        str(idea.get("tags", [])),
    ]).lower()
    stopwords = {"de","la","el","en","y","a","para","con","que","una","un","los","las","por","del","se","su","es","al","lo"}
    return set(w for w in texto.split() if len(w) > 3 and w not in stopwords)

def es_duplicado(idea_nueva: dict, umbral: float = 0.42) -> tuple:
    """
    Devuelve (True, nombre_similar) si la idea supera el umbral de similitud.
    También penaliza si comparten vertical+tipo exactos.
    """
    kb = _cargar()
    palabras_nueva   = _palabras_clave(idea_nueva)
    vertical_nueva   = idea_nueva.get("vertical", "").lower()
    tipo_nuevo       = idea_nueva.get("tipo", "").lower()
    if not palabras_nueva:
        return False, ""
    for idea in kb.get("ideas", []):
        palabras = _palabras_clave(idea)
        if not palabras:
            continue
        union = palabras_nueva | palabras
        interseccion = palabras_nueva & palabras
        sim = len(interseccion) / len(union) if union else 0
        # Penalizar si mismo vertical + tipo
        if idea.get("vertical","").lower() == vertical_nueva and idea.get("tipo","").lower() == tipo_nuevo:
            sim *= 1.35
        if sim >= umbral:
            return True, idea.get("nombre", "?")
    return False, ""

def registrar_idea(idea: dict):
    kb    = _cargar()
    ideas = kb.get("ideas", [])
    scores = idea.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    ideas.append({
        "nombre":         idea.get("nombre", "SinNombre"),
        "tagline":        idea.get("tagline", ""),
        "vertical":       idea.get("vertical", ""),
        "tipo":           idea.get("tipo", ""),
        "tags":           idea.get("tags", []) if isinstance(idea.get("tags"), list) else [],
        "score_total":    scores.get("score_total", 0),
        "scores":         scores,
        "feedback":       None,
        "herramienta_ia": idea.get("herramienta_ia_clave", ""),
        "fecha":          datetime.now().strftime("%Y-%m-%d"),
    })
    kb["ideas"] = ideas
    kb["stats"] = _calcular_stats(ideas)
    _guardar(kb)

def registrar_feedback(nombre: str, feedback: str):
    """Registra like/dislike para que el sistema aprenda preferencias."""
    kb    = _cargar()
    ideas = kb.get("ideas", [])
    for idea in ideas:
        if idea.get("nombre", "").lower() == nombre.lower():
            idea["feedback"] = feedback
            break
    kb["ideas"] = ideas
    kb["stats"] = _calcular_stats(ideas)
    _guardar(kb)

def _calcular_stats(ideas: list) -> dict:
    if not ideas:
        return {}
    scores = [i.get("score_total", 0) for i in ideas if i.get("score_total", 0) > 0]

    # Verticales con promedio de score
    verticales: dict = {}
    for i in ideas:
        v = i.get("vertical", "?")
        verticales.setdefault(v, []).append(i.get("score_total", 0))
    mejores_v = sorted(verticales.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:3]

    # Tags en ideas con score >= 75
    tags_exito: Counter = Counter()
    for i in ideas:
        if i.get("score_total", 0) >= 75:
            for t in (i.get("tags") or []):
                tags_exito[t] += 1

    # Herramientas IA más usadas en ideas buenas
    ia_tools: Counter = Counter()
    for i in ideas:
        if i.get("score_total", 0) >= 75 and i.get("herramienta_ia"):
            ia_tools[i["herramienta_ia"][:40]] += 1

    exitosas  = [i for i in ideas if i.get("score_total", 0) >= 75]
    liked     = [i.get("nombre") for i in ideas if i.get("feedback") == "like"]
    disliked  = [i.get("nombre") for i in ideas if i.get("feedback") == "dislike"]
    mejor     = max(ideas, key=lambda x: x.get("score_total", 0)) if ideas else {}

    # Mejor tipo por score promedio
    tipos: dict = {}
    for i in ideas:
        t = i.get("tipo", "?")
        tipos.setdefault(t, []).append(i.get("score_total", 0))
    mejor_tipo = max(tipos.items(), key=lambda x: sum(x[1])/len(x[1]) if x[1] else 0)[0] if tipos else "N/A"

    return {
        "total_ideas":         len(ideas),
        "score_promedio":      round(sum(scores)/len(scores), 1) if scores else 0,
        "mejor_score":         max(scores) if scores else 0,
        "mejor_idea":          mejor.get("nombre", "N/A"),
        "mejor_vertical":      mejores_v[0][0] if mejores_v else "N/A",
        "mejor_tipo":          mejor_tipo,
        "mejores_verticales":  ", ".join(f"{v}({round(sum(s)/len(s),0):.0f}pt)" for v,s in mejores_v),
        "tags_exitosos":       ", ".join(t for t,_ in tags_exito.most_common(5)),
        "ia_tools_top":        ", ".join(t for t,_ in ia_tools.most_common(3)),
        "tasa_exito":          f"{len(exitosas)}/{len(ideas)} ({round(len(exitosas)/len(ideas)*100) if ideas else 0}%)",
        "ideas_liked":         liked,
        "ideas_disliked":      disliked,
    }

def get_stats() -> dict:
    kb = _cargar()
    return kb.get("stats", _calcular_stats(kb.get("ideas", [])))

def get_top_ideas(n: int = 5) -> list:
    kb = _cargar()
    return sorted(kb.get("ideas", []), key=lambda x: x.get("score_total", 0), reverse=True)[:n]

def contar_pendientes() -> int:
    try:
        import csv
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta):
            return 0
        with open(ruta, newline="", encoding="utf-8") as f:
            return sum(1 for _ in csv.DictReader(f))
    except:
        return 0

def get_contexto_para_prompt() -> dict:
    kb    = _cargar()
    ideas = kb.get("ideas", [])
    stats = kb.get("stats", {})

    # Últimas 40 ideas con toda la info para anti-duplicados
    ideas_previas = "\n".join(
        f"- {i.get('nombre','?')} [{i.get('vertical','?')}/{i.get('tipo','?')}] "
        f"'{i.get('tagline','')}' tags:[{','.join(i.get('tags') or [])}]"
        for i in ideas[-40:]
    ) or "ninguna aún"

    # Verticales saturadas en las últimas 15 ideas
    recientes = ideas[-15:] if len(ideas) >= 15 else ideas
    v_count   = Counter(i.get("vertical","") for i in recientes)
    saturadas = [v for v, c in v_count.most_common() if c >= 3]

    # Verticales de ideas con dislike — evitarlas
    disliked_verticals = list(set(
        i.get("vertical","") for i in ideas if i.get("feedback") == "dislike"
    ))

    return {
        "ideas_previas":         ideas_previas,
        "mejores_verticales":    stats.get("mejores_verticales", "N/A"),
        "tags_exitosos":         stats.get("tags_exitosos", "N/A"),
        "ia_tools_top":          stats.get("ia_tools_top", "N/A"),
        "score_promedio":        stats.get("score_promedio", 0),
        "tasa_exito":            stats.get("tasa_exito", "N/A"),
        "total_analizadas":      stats.get("total_ideas", 0),
        "verticales_saturadas":  ", ".join(saturadas) if saturadas else "ninguna",
        "verticales_disliked":   ", ".join(disliked_verticals) if disliked_verticals else "ninguna",
    }

# aqui finaliza el codigo de agents/knowledge_base.py
