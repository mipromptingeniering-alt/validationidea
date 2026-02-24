import os
import json
from datetime import datetime

KB_FILE = "data/knowledge_base.json"

_ESTRUCTURA_BASE = {
    "total_analizadas": 0,
    "patrones_exitosos": [],
    "stats_tipos": {},
    "stats_verticales": {},
    "ultima_actualizacion": None,
}

# Umbral P6: vertical saturada si tiene más ideas que esto
UMBRAL_SATURACION = 10
# Umbral P6: vertical a explorar si tiene menos ideas que esto
UMBRAL_EXPLORACION = 3


def _cargar() -> dict:
    if os.path.exists(KB_FILE):
        try:
            with open(KB_FILE, "r", encoding="utf-8") as f:
                datos = json.load(f)
            for clave, valor in _ESTRUCTURA_BASE.items():
                if clave not in datos:
                    datos[clave] = valor
            return datos
        except Exception:
            pass
    return dict(_ESTRUCTURA_BASE)


def _guardar(kb: dict):
    os.makedirs("data", exist_ok=True)
    with open(KB_FILE, "w", encoding="utf-8") as f:
        json.dump(kb, f, ensure_ascii=False, indent=2)


def aprender(idea: dict, score: int):
    """Registra una idea evaluada y actualiza estadísticas de tipos y verticales."""
    kb = _cargar()

    kb["total_analizadas"]      = kb.get("total_analizadas", 0) + 1
    kb["ultima_actualizacion"]  = datetime.now().isoformat()

    tipo     = str(idea.get("tipo")     or "Desconocido")[:60]
    vertical = str(idea.get("vertical") or "Desconocido")[:60]

    for campo, valor in [("stats_tipos", tipo), ("stats_verticales", vertical)]:
        grupo = kb.get(campo, {})
        if valor not in grupo:
            grupo[valor] = {"total": 0, "suma": 0, "avg": 0}
        grupo[valor]["total"] += 1
        grupo[valor]["suma"]  += score
        grupo[valor]["avg"]    = round(grupo[valor]["suma"] / grupo[valor]["total"], 1)
        kb[campo] = grupo

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
    """
    Devuelve texto con insights para mejorar el generador de ideas.
    Incluye P6: verticales saturadas a evitar y verticales a explorar.
    """
    kb = _cargar()
    if kb.get("total_analizadas", 0) < 5:
        return ""

    lineas = []

    # ── Tipos más exitosos ────────────────────────────────────────────────────
    tipos = kb.get("stats_tipos", {})
    if tipos:
        top = sorted(tipos.items(), key=lambda x: x[1].get("avg", 0), reverse=True)
        top3 = [(t, d) for t, d in top if d.get("total", 0) >= 2][:3]
        if top3:
            lineas.append(
                "Tipos más exitosos: " +
                ", ".join(f"{t}({d['avg']:.0f}/100)" for t, d in top3)
            )

    # ── Verticales más rentables ──────────────────────────────────────────────
    verticales = kb.get("stats_verticales", {})
    if verticales:
        top = sorted(verticales.items(), key=lambda x: x[1].get("avg", 0), reverse=True)
        top3 = [(v, d) for v, d in top if d.get("total", 0) >= 2][:3]
        if top3:
            lineas.append(
                "Verticales más rentables: " +
                ", ".join(f"{v}({d['avg']:.0f}/100)" for v, d in top3)
            )

    # ── P6: Anti-saturación de verticales ─────────────────────────────────────
    if verticales:
        saturadas = [
            v for v, d in verticales.items()
            if d.get("total", 0) > UMBRAL_SATURACION
        ]
        a_explorar = [
            v for v, d in verticales.items()
            if d.get("total", 0) < UMBRAL_EXPLORACION
        ]
        todas_las_verticales = set(verticales.keys())

        # Verticales nunca exploradas (no aparecen en KB)
        verticales_conocidas = {
            "SaaS", "App móvil", "Marketplace", "IA", "Hardware",
            "Servicio", "E-commerce", "Educación", "Salud", "Fintech",
            "Legal Tech", "Sostenibilidad", "Productividad", "Recursos Humanos",
            "Logística", "Turismo", "Inmobiliaria", "Deportes", "Alimentación"
        }
        sin_explorar = sorted(verticales_conocidas - todas_las_verticales)

        if saturadas:
            lineas.append(
                "VERTICALES SATURADAS — evitar repetir: " +
                ", ".join(saturadas)
            )
        if a_explorar or sin_explorar:
            explorar = list(a_explorar) + sin_explorar[:3]
            lineas.append(
                "VERTICALES A EXPLORAR — priorizar estas: " +
                ", ".join(explorar[:6])
            )

    # ── Ideas recientes exitosas ──────────────────────────────────────────────
    patrones = kb.get("patrones_exitosos", [])
    if patrones:
        recientes = patrones[-3:]
        nombres = [p["nombre"] for p in recientes if p.get("nombre")]
        if nombres:
            lineas.append(f"Ideas recientes exitosas (no repetir): {', '.join(nombres)}")

    return "\n".join(lineas)


def get_stats() -> dict:
    """
    Retorna estadísticas resumidas.
    Devuelve total_ideas, score_promedio, mejor_tipo, mejor_vertical.
    Nunca lanza excepciones.
    """
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

        # Calcular score promedio global
        todos_los_scores = [
            v.get("avg", 0) * v.get("total", 0)
            for v in verts.values() if v.get("total", 0) > 0
        ]
        total_ideas_con_score = sum(v.get("total", 0) for v in verts.values())
        score_promedio = (
            round(sum(todos_los_scores) / total_ideas_con_score, 1)
            if total_ideas_con_score > 0 else 0
        )

        total = kb.get("total_analizadas", 0)

        return {
            "total":          total,
            "total_ideas":    total,           # alias para monitor_nocturno
            "exitosas":       len(kb.get("patrones_exitosos", [])),
            "mejor_tipo":     mejor_tipo,
            "mejor_vertical": mejor_vert,
            "score_promedio": score_promedio,  # para resumen diario Telegram
        }
    except Exception:
        return {
            "total": 0, "total_ideas": 0, "exitosas": 0,
            "mejor_tipo": "N/A", "mejor_vertical": "N/A", "score_promedio": 0
        }
