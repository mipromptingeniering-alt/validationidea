"""
verticales_rotacion.py - Fuerza diversidad de verticales en cada generacion
"""
import os, json, random
from datetime import datetime

ROTACION_FILE = "data/verticales_rotacion.json"

VERTICALES_DISPONIBLES = [
    # B2B SaaS
    "legal-tech", "hr-tech", "fintech-b2b", "real-estate-tech", "supply-chain",
    "construction-tech", "agriculture-tech", "insurance-tech", "logistics-tech",
    "accounting-automation", "sales-intelligence", "customer-success",
    # B2C / Consumer
    "salud-mental", "fitness-personalizado", "mascotas", "educacion-adultos",
    "finanzas-personales", "viajes-nicho", "sostenibilidad-consumidor",
    # Infraestructura IA
    "ai-tools-developers", "data-labeling", "model-monitoring",
    "vector-databases", "ai-compliance",
    # Vertical nicho
    "veterinaria-digital", "farmacia-online", "telemedicina-especialistas",
    "ecommerce-b2b", "marketplace-servicios-locales",
]

def _load():
    try:
        with open(ROTACION_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "ultimos_verticales_usados": [],
            "ciclo_actual": 0,
            "ultimo_reset": datetime.now().isoformat(),
        }

def _save(d):
    os.makedirs("data", exist_ok=True)
    with open(ROTACION_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def get_vertical_siguiente(verticales_bloqueados_extra=None):
    """Devuelve el siguiente vertical que NO se ha usado recientemente."""
    d = _load()
    usados = set(d.get("ultimos_verticales_usados", [])[-8:])
    if verticales_bloqueados_extra:
        usados.update(v.lower() for v in verticales_bloqueados_extra)

    disponibles = [v for v in VERTICALES_DISPONIBLES if v not in usados]
    if not disponibles:
        # Reset si hemos agotado todos
        d["ultimos_verticales_usados"] = []
        disponibles = VERTICALES_DISPONIBLES[:]
        print("🔄 Rotacion vertical: reset completo")

    elegido = random.choice(disponibles)
    d["ultimos_verticales_usados"].append(elegido)
    d["ultimos_verticales_usados"] = d["ultimos_verticales_usados"][-12:]
    d["ciclo_actual"] += 1
    _save(d)
    return elegido

def registrar_vertical_usado(vertical):
    if not vertical:
        return
    d = _load()
    d["ultimos_verticales_usados"].append(str(vertical).lower())
    d["ultimos_verticales_usados"] = d["ultimos_verticales_usados"][-12:]
    _save(d)

def get_verticales_prohibidos():
    d = _load()
    return list(set(d.get("ultimos_verticales_usados", [])[-5:]))

def get_stats_rotacion():
    d = _load()
    usados = d.get("ultimos_verticales_usados", [])
    return {
        "ciclo_actual":          d.get("ciclo_actual", 0),
        "ultimo_reset":          d.get("ultimo_reset", ""),
        "ultimos_5":             usados[-5:],
        "total_disponibles":     len(VERTICALES_DISPONIBLES),
        "disponibles_restantes": len([v for v in VERTICALES_DISPONIBLES if v not in set(usados[-8:])]),
    }

# fin agents/verticales_rotacion.py
