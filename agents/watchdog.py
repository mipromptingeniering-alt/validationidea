"""
watchdog.py - Auto-diagnóstico, auto-reparación y diversidad de temas
"""
import os, json, re
from datetime import datetime

HEALTH_FILE = "data/health.json"

def _load():
    try:
        with open(HEALTH_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "consecutive_timeouts": 0,
            "consecutive_failures": 0,
            "total_ok_24h": 0,
            "last_success": None,
            "ultimas_ideas": [],
            "ultimos_verticales": [],
            "ultimas_palabras_clave": [],
            "errores_recientes": [],
            "ciclo_reparacion": 0,
            "modo_emergencia": False,
        }

def _save(h):
    os.makedirs("data", exist_ok=True)
    with open(HEALTH_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

def registrar_exito(idea):
    h = _load()
    h["consecutive_timeouts"] = 0
    h["consecutive_failures"]  = 0
    h["total_ok_24h"]         += 1
    h["last_success"]          = datetime.now().isoformat()
    h["modo_emergencia"]       = False

    nombre   = str(idea.get("nombre", ""))
    vertical = str(idea.get("vertical", "")).lower()
    tagline  = str(idea.get("tagline", "")).lower()
    problema = str(idea.get("problema", "")).lower()

    if nombre:
        h["ultimas_ideas"].append(nombre)
        h["ultimas_ideas"] = h["ultimas_ideas"][-25:]

    if vertical:
        h["ultimos_verticales"].append(vertical)
        h["ultimos_verticales"] = h["ultimos_verticales"][-10:]

    # Extraer palabras clave del tema para evitar repeticiones
    texto = tagline + " " + problema
    palabras = re.findall(r'\b[a-záéíóúñ]{5,}\b', texto)
    frecuentes = list(set(palabras))[:6]
    h["ultimas_palabras_clave"].extend(frecuentes)
    h["ultimas_palabras_clave"] = list(set(h["ultimas_palabras_clave"]))[-40:]

    _save(h)

def registrar_timeout():
    h = _load()
    h["consecutive_timeouts"] += 1
    h["consecutive_failures"]  += 1
    ts = datetime.now().strftime("%H:%M")
    h["errores_recientes"].append(f"{ts} TIMEOUT")
    h["errores_recientes"] = h["errores_recientes"][-8:]
    _save(h)
    return h["consecutive_timeouts"]

def registrar_fallo(error_str):
    h = _load()
    h["consecutive_failures"] += 1
    ts = datetime.now().strftime("%H:%M")
    h["errores_recientes"].append(f"{ts} {str(error_str)[:80]}")
    h["errores_recientes"] = h["errores_recientes"][-8:]
    _save(h)

def registrar_placeholder(campo):
    """Registra cuando la IA devuelve texto genérico sin rellenar."""
    h = _load()
    ts = datetime.now().strftime("%H:%M")
    h["errores_recientes"].append(f"{ts} PLACEHOLDER en {campo}")
    h["errores_recientes"] = h["errores_recientes"][-8:]
    _save(h)

def necesita_reparacion():
    return _load().get("consecutive_timeouts", 0) >= 3

def get_nombres_bloqueados():
    return _load().get("ultimas_ideas", [])

def get_verticales_bloqueados():
    """Últimos 5 verticales para forzar diversidad."""
    return list(set(_load().get("ultimos_verticales", [])[-5:]))

def get_palabras_clave_bloqueadas():
    """Palabras temáticas recientes para evitar repetición de tema."""
    h = _load()
    # Palabras que aparecen en las últimas 5 ideas = temas saturados
    recientes = h.get("ultimas_palabras_clave", [])
    return recientes[-20:]

def modo_emergencia_activo():
    return _load().get("modo_emergencia", False)

def get_diagnostico():
    h = _load()
    return {
        "consecutive_timeouts": h.get("consecutive_timeouts", 0),
        "consecutive_failures": h.get("consecutive_failures", 0),
        "last_success":         h.get("last_success", "nunca"),
        "total_ok_24h":         h.get("total_ok_24h", 0),
        "errores_recientes":    h.get("errores_recientes", []),
        "ultimas_ideas":        h.get("ultimas_ideas", [])[-5:],
        "verticales_saturados": get_verticales_bloqueados(),
        "modo_emergencia":      h.get("modo_emergencia", False),
        "ciclo_reparacion":     h.get("ciclo_reparacion", 0),
    }

def auto_reparar(telegram_fn=None, chat_id=None):
    h    = _load()
    diag = get_diagnostico()

    acciones = [
        "Modo prompt reducido activado",
        "Contador de timeouts reseteado",
        "Temas saturados limpiados (forzar diversidad)",
        "Proxima idea en 2 minutos",
    ]

    msg = (
        f"🔧 <b>Auto-reparacion activada — Ciclo {h.get('ciclo_reparacion',0)+1}</b>\n\n"
        f"Timeouts consecutivos: {diag['consecutive_timeouts']}\n"
        f"Ultimo exito: {diag['last_success']}\n"
        f"OK hoy: {diag['total_ok_24h']}\n\n"
        f"Errores recientes:\n"
        + "\n".join(f"  • {e}" for e in diag["errores_recientes"][-4:])
        + f"\n\nTemas saturados limpiados: {', '.join(diag['verticales_saturados']) or 'ninguno'}\n\n"
        + "Acciones:\n"
        + "\n".join(f"✅ {a}" for a in acciones)
    )

    if telegram_fn and chat_id:
        try:
            telegram_fn(chat_id, msg)
        except: pass

    # Reset y modo emergencia
    h["consecutive_timeouts"]     = 0
    h["consecutive_failures"]      = 0
    h["modo_emergencia"]           = True
    h["ultimos_verticales"]        = []
    h["ultimas_palabras_clave"]    = []
    h["ciclo_reparacion"]         += 1
    _save(h)
    print(f"🔧 Auto-reparacion ciclo {h['ciclo_reparacion']}")
    return msg

# fin agents/watchdog.py
