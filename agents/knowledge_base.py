import os
import json
from datetime import datetime

KB_FILE = "data/knowledge_base.json"

# Estructura base garantizada — usada si el archivo no existe o tiene formato antiguo
_ESTRUCTURA_BASE = {
    "total_analizadas": 0,
    "patrones_exitosos": [],
    "stats_tipos": {},
    "stats_verticales": {},
    "ultima_actualizacion": None,
}


def _cargar() -> dict:
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
            # Migración: si faltan claves del formato nuevo, añadirlas
            for clave, valor in _ESTRUCTURA_BASE.items():
                if clave not in datos:
                    datos[clave] = valor
            return datos
        except Exception:
            pass  # Archivo corrupto → empezar de cero
    return dict(_ESTRUCTURA_BASE)


def _guardar(kb: dict):
    os.makedirs("data", exist_ok=True)
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def aprender(idea: dict, score: int):
    """Registra una idea evaluada y actualiza estadísticas de tipos y verticales."""
    kb = _cargar()

    kb["total_analizadas"] = kb.get("total_analizadas", 0) + 1
    kb["ultima_actualizacion"] = datetime.now().isoformat()

    tipo     = str(idea.get("tipo")     or "Desconocido")[:60]
    vertical = str(idea.get("vertical") or "Desconocido")[:60]

    for campo, valor in [("stats_tipos", tipo), ("stats_verticales", vertical)]:
        grupo = kb.get(campo, {})
        if valor not in grupo:
            grupo[valor] = {"total": 0, "suma": 0, "avg": 0}
        grupo[valor]["total"] += 1
        grupo[valor]["suma"]  += score
        grupo[valor]["avg"]    = round(
            grupo[valor]["suma"] / grupo[valor]["total"], 1
        )
        kb[campo] = grupo

    # Guardar solo ideas exitosas (score >= 75) — máximo 30
    if score >= 75:
        patron = {
            "nombre":   str(idea.get("nombre") or "")[:100],
            "tipo":     tipo,
            "vertical": vertical,
            "score":    score,
            "valor":    str(idea.get("propuesta_valor") or "")[:200],
        }
        patrones = kb.get("patrones_exitosos", [])
        patrones.append(patron)
        kb["patrones_exitosos"] = patrones[-30:]

    _guardar(kb)
    print(
        f"[KB] ✅ {idea.get('nombre', '?')} | "
        f"tipo={tipo} | vertical={vertical} | score={score} | "
        f"total={kb['total_analizadas']}"
    )


def get_contexto_para_generador() -> str:
    """Devuelve texto con insights para mejorar el generador de ideas."""
    kb = _cargar()
    if kb.get("total_analizadas", 0) < 5:
        return ""

    lineas = []

    tipos = kb.get("stats_tipos", {})
    if tipos:
        top = sorted(tipos.items(), key=lambda x: x[1].get("avg", 0), reverse=True)
        top3 = [(t, d) for t, d in top if d.get("total", 0) >= 2][:3]
        if top3:
            lineas.append(
                "Tipos más exitosos: " +
                ", ".join(f"{t}({d['avg']:.0f}/100)" for t, d in top3)
            )

    verticales = kb.get("stats_verticales", {})
    if verticales:
        top = sorted(verticales.items(), key=lambda x: x[1].get("avg", 0), reverse=True)
        top3 = [(v, d) for v, d in top if d.get("total", 0) >= 2][:3]
        if top3:
            lineas.append(
                "Verticales más rentables: " +
                ", ".join(f"{v}({d['avg']:.0f}/100)" for v, d in top3)
            )

    patrones = kb.get("patrones_exitosos", [])
    if patrones:
        recientes = patrones[-3:]
        nombres = [p["nombre"] for p in recientes if p.get("nombre")]
        if nombres:
            lineas.append(f"Ideas recientes exitosas: {', '.join(nombres)}")

    return "\n".join(lineas)


def get_stats() -> dict:
    """Retorna estadísticas resumidas. Nunca lanza excepciones."""
    try:
        kb = _cargar()

        mejor_tipo = "N/A"
        tipos = kb.get("stats_tipos", {})
        tipos_validos = {k: v for k, v in tipos.items() if v.get("total", 0) >= 2}
        if tipos_validos:
            mejor_tipo = max(tipos_validos.items(), key=lambda x: x[1].get("avg", 0))[0]

        mejor_vert = "N/A"
        verts = kb.get("stats_verticales", {})
        verts_validos = {k: v for k, v in verts.items() if v.get("total", 0) >= 2}
        if verts_validos:
            mejor_vert = max(verts_validos.items(), key=lambda x: x[1].get("avg", 0))[0]

        return {
            "total":           kb.get("total_analizadas", 0),
            "exitosas":        len(kb.get("patrones_exitosos", [])),
            "mejor_tipo":      mejor_tipo,
            "mejor_vertical":  mejor_vert,
        }
    except Exception:
        return {"total": 0, "exitosas": 0, "mejor_tipo": "N/A", "mejor_vertical": "N/A"}
