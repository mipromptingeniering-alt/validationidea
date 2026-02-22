import os
import json
from datetime import datetime

KB_FILE = "data/knowledge_base.json"


def _cargar() -> dict:
    if os.path.exists(KB_FILE):
        with open(KB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "total_analizadas": 0,
        "patrones_exitosos": [],
        "stats_tipos": {},
        "stats_verticales": {},
        "ultima_actualizacion": None,
    }


def _guardar(kb: dict):
    os.makedirs("data", exist_ok=True)
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def aprender(idea: dict, score: int):
    """Registra una idea evaluada y actualiza estadísticas."""
    kb = _cargar()
    kb["total_analizadas"] += 1
    kb["ultima_actualizacion"] = datetime.now().isoformat()

    tipo     = str(idea.get("tipo") or idea.get("Type") or "Desconocido")
    vertical = str(idea.get("vertical") or idea.get("Vertical") or "Desconocido")

    for campo, valor in [("stats_tipos", tipo), ("stats_verticales", vertical)]:
        if valor not in kb[campo]:
            kb[campo][valor] = {"total": 0, "suma": 0, "avg": 0}
        kb[campo][valor]["total"] += 1
        kb[campo][valor]["suma"]  += score
        kb[campo][valor]["avg"]    = round(
            kb[campo][valor]["suma"] / kb[campo][valor]["total"], 1
        )

    if score >= 75:
        patron = {
            "nombre":   str(idea.get("nombre") or idea.get("Name", "")),
            "tipo":     tipo,
            "vertical": vertical,
            "score":    score,
            "valor":    str(idea.get("propuesta_valor") or idea.get("Value", ""))[:200],
        }
        kb["patrones_exitosos"].append(patron)
        kb["patrones_exitosos"] = kb["patrones_exitosos"][-30:]

    _guardar(kb)
    print(f"[KB] Aprendido: {tipo}/{vertical} score={score} | Total={kb['total_analizadas']}")


def get_contexto_para_generador() -> str:
    """Devuelve texto con insights para mejorar el generador de ideas."""
    kb = _cargar()
    if kb["total_analizadas"] < 5:
        return ""

    lineas = ["\n=== INSIGHTS DEL SISTEMA (aprende de ideas previas) ==="]

    if kb["stats_tipos"]:
        top = sorted(kb["stats_tipos"].items(), key=lambda x: x[1]["avg"], reverse=True)
        top3 = [(t, d) for t, d in top if d["total"] >= 2][:3]
        if top3:
            lineas.append("Tipos de producto más exitosos: " +
                          ", ".join(f"{t}({d['avg']:.0f}/100)" for t, d in top3))

    if kb["stats_verticales"]:
        top = sorted(kb["stats_verticales"].items(), key=lambda x: x[1]["avg"], reverse=True)
        top3 = [(v, d) for v, d in top if d["total"] >= 2][:3]
        if top3:
            lineas.append("Verticales más rentables: " +
                          ", ".join(f"{v}({d['avg']:.0f}/100)" for v, d in top3))

    if kb["patrones_exitosos"]:
        recientes = kb["patrones_exitosos"][-3:]
        nombres = [p["nombre"] for p in recientes if p.get("nombre")]
        if nombres:
            lineas.append(f"Ideas recientes exitosas (score>75): {', '.join(nombres)}")

    lineas.append("Usa estos patrones para generar ideas similares a las exitosas.\n")
    return "\n".join(lineas)


def get_stats() -> dict:
    kb = _cargar()
    mejor_tipo = "N/A"
    mejor_vert = "N/A"
    if kb["stats_tipos"]:
        tipos_con_datos = {k: v for k, v in kb["stats_tipos"].items() if v["total"] >= 2}
        if tipos_con_datos:
            mejor_tipo = max(tipos_con_datos.items(), key=lambda x: x[1]["avg"])[0]
    if kb["stats_verticales"]:
        verts_con_datos = {k: v for k, v in kb["stats_verticales"].items() if v["total"] >= 2}
        if verts_con_datos:
            mejor_vert = max(verts_con_datos.items(), key=lambda x: x[1]["avg"])[0]
    return {
        "total": kb["total_analizadas"],
        "exitosas": len(kb["patrones_exitosos"]),
        "mejor_tipo": mejor_tipo,
        "mejor_vertical": mejor_vert,
    }
