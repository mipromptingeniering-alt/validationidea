"""
knowledge_base.py - Base de conocimiento persistente de ideas
"""
import os, json, re
from datetime import datetime, timedelta

KB_FILE   = "data/knowledge_base.json"
IDEAS_FILE = "data/ideas.json"

def _load_kb():
    try:
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"ideas": [], "version": 2, "ultimo_aprendizaje": ""}

def _save_kb(d):
    os.makedirs("data", exist_ok=True)
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _load_ideas():
    try:
        with open(IDEAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return []

def migrar_si_necesario():
    """Migra ideas.json a knowledge_base.json si es necesario."""
    kb    = _load_kb()
    ideas = _load_ideas()
    if not ideas:
        return
    nombres_kb = {i.get("nombre","") for i in kb.get("ideas",[])}
    nuevas = [i for i in ideas if i.get("nombre","") not in nombres_kb]
    if nuevas:
        kb["ideas"].extend(nuevas)
        _save_kb(kb)
        print(f"✅ KB migrada: {len(nuevas)} ideas nuevas")

def registrar_idea(idea):
    if not isinstance(idea, dict):
        return
    kb     = _load_kb()
    nombre = idea.get("nombre","")
    # Actualizar si existe, insertar si no
    for i, existente in enumerate(kb["ideas"]):
        if existente.get("nombre","") == nombre:
            kb["ideas"][i] = idea
            _save_kb(kb)
            return
    kb["ideas"].append(idea)
    _save_kb(kb)
    # Tambien guardar en ideas.json
    try:
        todas = _load_ideas()
        nombres_existentes = {i.get("nombre","") for i in todas}
        if nombre not in nombres_existentes:
            todas.append(idea)
            with open(IDEAS_FILE, "w", encoding="utf-8") as f:
                json.dump(todas, f, ensure_ascii=False, indent=2)
    except: pass

def registrar_feedback(nombre_idea, positivo: bool):
    kb = _load_kb()
    for idea in kb["ideas"]:
        if nombre_idea.lower() in idea.get("nombre","").lower():
            fb = idea.get("feedback", {"likes":0,"dislikes":0})
            if positivo:
                fb["likes"]    = fb.get("likes",0) + 1
            else:
                fb["dislikes"] = fb.get("dislikes",0) + 1
            idea["feedback"] = fb
            break
    _save_kb(kb)

def es_duplicado(idea_nueva, umbral=0.38):
    """Deteccion semantica simple de duplicados por palabras clave."""
    if not isinstance(idea_nueva, dict):
        return False, ""
    kb     = _load_kb()
    ideas  = kb.get("ideas", [])
    if not ideas:
        return False, ""

    nombre_nuevo   = idea_nueva.get("nombre","").lower()
    problema_nuevo = idea_nueva.get("problema","").lower()
    vertical_nuevo = idea_nueva.get("vertical","").lower()

    def _palabras(texto):
        return set(re.findall(r'\b\w{4,}\b', str(texto).lower()))

    palabras_nuevas = _palabras(nombre_nuevo + " " + problema_nuevo)

    for idea in ideas[-50:]:  # Solo comparar con las 50 ultimas
        nombre_viejo   = idea.get("nombre","").lower()
        problema_viejo = idea.get("problema","").lower()
        vertical_viejo = idea.get("vertical","").lower()

        # Match exacto de nombre
        if nombre_nuevo and nombre_nuevo == nombre_viejo:
            return True, idea.get("nombre","")

        # Match de vertical + palabras clave
        if vertical_nuevo and vertical_nuevo == vertical_viejo:
            palabras_viejas = _palabras(nombre_viejo + " " + problema_viejo)
            if palabras_nuevas and palabras_viejas:
                interseccion = palabras_nuevas & palabras_viejas
                union        = palabras_nuevas | palabras_viejas
                jaccard      = len(interseccion) / len(union) if union else 0
                if jaccard > umbral:
                    return True, idea.get("nombre","")

    return False, ""

def get_contexto_para_prompt():
    """Devuelve contexto para el prompt de generacion."""
    kb    = _load_kb()
    ideas = kb.get("ideas", [])
    if not ideas:
        return {"ideas_previas": "ninguna", "score_promedio": 0}

    nombres = [i.get("nombre","?") for i in ideas[-15:]]
    scores  = [
        i.get("scores",{}).get("score_total",0)
        for i in ideas
        if isinstance(i.get("scores"),dict) and i["scores"].get("score_total",0) > 0
    ]
    promedio = round(sum(scores)/len(scores), 1) if scores else 0

    verticales_usados = list({str(i.get("vertical","")).lower() for i in ideas[-8:] if i.get("vertical")})

    return {
        "ideas_previas":     ", ".join(nombres),
        "score_promedio":    promedio,
        "verticales_usados": verticales_usados,
        "total_ideas":       len(ideas),
    }

def get_stats():
    kb    = _load_kb()
    ideas = kb.get("ideas", [])
    if not ideas:
        return {
            "total_ideas": 0, "score_promedio": 0,
            "mejor_idea": "ninguna", "mejor_score": 0,
            "ideas_semana": 0, "ideas_hoy": 0,
            "verticales_top": [],
        }

    scores = [
        (i.get("nombre","?"),
         i.get("scores",{}).get("score_total",0) if isinstance(i.get("scores"),dict) else 0)
        for i in ideas
    ]
    scores_validos = [(n,s) for n,s in scores if s > 0]
    promedio       = round(sum(s for _,s in scores_validos)/len(scores_validos),1) if scores_validos else 0
    mejor          = max(scores_validos, key=lambda x:x[1], default=("ninguna",0))

    ahora    = datetime.now()
    semana   = ahora - timedelta(days=7)
    hoy      = ahora - timedelta(hours=24)

    ideas_semana = 0
    ideas_hoy    = 0
    for idea in ideas:
        ts_str = idea.get("timestamp","") or idea.get("fecha","")
        if ts_str:
            try:
                ts = datetime.fromisoformat(ts_str[:19])
                if ts > semana: ideas_semana += 1
                if ts > hoy:    ideas_hoy    += 1
            except: pass

    from collections import Counter
    verticales = [str(i.get("vertical","")).lower() for i in ideas if i.get("vertical")]
    top_verts  = [v for v,_ in Counter(verticales).most_common(3)]

    return {
        "total_ideas":    len(ideas),
        "score_promedio": promedio,
        "mejor_idea":     mejor[0],
        "mejor_score":    mejor[1],
        "ideas_semana":   ideas_semana,
        "ideas_hoy":      ideas_hoy,
        "verticales_top": top_verts,
    }

def get_top_ideas(n=5):
    kb    = _load_kb()
    ideas = kb.get("ideas", [])
    def _score(i):
        return i.get("scores",{}).get("score_total",0) if isinstance(i.get("scores"),dict) else 0
    return sorted(ideas, key=_score, reverse=True)[:n]

def get_top_ejecutables(n=5):
    kb    = _load_kb()
    ideas = kb.get("ideas", [])
    def _ejec(i):
        return i.get("scores",{}).get("ejecutabilidad",0) if isinstance(i.get("scores"),dict) else 0
    return sorted(ideas, key=_ejec, reverse=True)[:n]

def buscar_idea(nombre):
    kb    = _load_kb()
    ideas = kb.get("ideas", [])
    n     = nombre.strip().lower()
    for idea in reversed(ideas):
        if n in idea.get("nombre","").lower():
            return idea
    return None

def get_ideas_con_feedback_positivo():
    kb    = _load_kb()
    ideas = kb.get("ideas", [])
    return [
        i for i in ideas
        if isinstance(i.get("feedback"),dict) and i["feedback"].get("likes",0) > 0
    ]

# fin agents/knowledge_base.py


def registrar_rechazo(idea: dict, motivo: str):
    """Guarda rechazos para que el prompt aprenda a evitarlos."""
    import json, datetime, os
    ruta = pathlib.Path(__file__).parent.parent / "data" / "rechazos.jsonl"
    ruta.parent.mkdir(parents=True, exist_ok=True)
    entry = {
        "ts": datetime.datetime.utcnow().isoformat(),
        "nombre": idea.get("nombre",""),
        "motivo": motivo,
        "sector": idea.get("sector",""),
    }
    with open(ruta, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(entry, ensure_ascii=False) + "\n")


def es_similar(idea: dict, umbral: float = 0.55):
    """Devuelve (True, motivo) si la idea es demasiado similar a una anterior."""
    import json, pathlib as _p
    nombre_nuevo = str(idea.get("nombre", "")).strip().lower()
    problema_nuevo = str(idea.get("problema", "")).strip().lower()

    ruta_kb = _p.Path(__file__).parent.parent / "data" / "ideas.jsonl"
    if not ruta_kb.exists():
        return False, ""

    palabras_n = set(nombre_nuevo.split())
    palabras_p = set(problema_nuevo.split())

    with open(ruta_kb, encoding="utf-8") as fh:
        for linea in fh:
            try:
                prev = json.loads(linea)
            except Exception:
                continue
            n_prev = str(prev.get("nombre", "")).strip().lower()
            p_prev = str(prev.get("problema", "")).strip().lower()

            # Nombre identico
            if nombre_nuevo and nombre_nuevo == n_prev:
                return True, f"Nombre identico: {n_prev}"

            # Nombre muy similar (Jaccard sobre palabras)
            palabras_prev = set(n_prev.split())
            if palabras_n and palabras_prev:
                union = palabras_n | palabras_prev
                inter = palabras_n & palabras_prev
                if len(union) > 0 and len(inter) / len(union) >= umbral:
                    return True, f"Nombre similar ({int(len(inter)/len(union)*100)}%): {n_prev}"

            # Problema muy similar
            palabras_pp = set(p_prev.split())
            if len(palabras_p) > 5 and palabras_pp:
                union_p = palabras_p | palabras_pp
                inter_p = palabras_p & palabras_pp
                if len(union_p) > 0 and len(inter_p) / len(union_p) >= 0.65:
                    return True, f"Problema similar a: {n_prev}"

    return False, ""
