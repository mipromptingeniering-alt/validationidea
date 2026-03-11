"""
watchdog.py - Monitor de salud del sistema, auto-reparacion y aprendizaje de errores
"""
import os, json, time
from datetime import datetime, timedelta

WATCHDOG_FILE = "data/watchdog_state.json"

def _load():
    try:
        with open(WATCHDOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "consecutive_timeouts":  0,
            "consecutive_failures":  0,
            "last_success":          None,
            "last_failure":          None,
            "total_ok_24h":          0,
            "total_fail_24h":        0,
            "modo_emergencia":       False,
            "ciclo_reparacion":      0,
            "ultimas_ideas":         [],
            "verticales_saturados":  [],
            "palabras_clave_bloqueadas": [],
            "nombres_bloqueados":    [],
            "errores_recientes":     [],
            "placeholders_vistos":   [],
            "historial_ok":          [],
            "historial_fail":        [],
        }

def _save(d):
    os.makedirs("data", exist_ok=True)
    with open(WATCHDOG_FILE, "w", encoding="utf-8") as f:
        json.dump(d, f, ensure_ascii=False, indent=2)

def _ahora_str():
    return datetime.now().strftime("%d/%m %H:%M")

# ── Registro de eventos ──────────────────────────────────────────────────────

def registrar_exito(idea=None):
    d = _load()
    d["consecutive_timeouts"]  = 0
    d["consecutive_failures"]  = 0
    d["modo_emergencia"]       = False
    d["last_success"]          = _ahora_str()
    d["total_ok_24h"]          = d.get("total_ok_24h", 0) + 1

    if isinstance(idea, dict):
        nombre   = idea.get("nombre", "")
        vertical = str(idea.get("vertical", "")).lower()
        if nombre:
            ideas = d.get("ultimas_ideas", [])
            ideas.append(nombre)
            d["ultimas_ideas"] = ideas[-20:]
        if vertical:
            # Desbloquear vertical si estaba saturado
            saturados = d.get("verticales_saturados", [])
            if vertical in saturados:
                saturados.remove(vertical)
            d["verticales_saturados"] = saturados

    # Historial limpio de las ultimas 24h
    ahora = datetime.now()
    hok   = d.get("historial_ok", [])
    hok.append(ahora.isoformat())
    d["historial_ok"] = [t for t in hok
                         if datetime.fromisoformat(t) > ahora - timedelta(hours=24)][-50:]
    _save(d)

def registrar_fallo(motivo=""):
    d = _load()
    d["consecutive_failures"] = d.get("consecutive_failures", 0) + 1
    d["last_failure"]         = _ahora_str()
    d["total_fail_24h"]       = d.get("total_fail_24h", 0) + 1

    errores = d.get("errores_recientes", [])
    errores.append(f"{_ahora_str()} {str(motivo)[:80]}")
    d["errores_recientes"] = errores[-10:]

    if d["consecutive_failures"] >= 3:
        d["modo_emergencia"] = True

    ahora = datetime.now()
    hfail = d.get("historial_fail", [])
    hfail.append(ahora.isoformat())
    d["historial_fail"] = [t for t in hfail
                           if datetime.fromisoformat(t) > ahora - timedelta(hours=24)][-50:]
    _save(d)

def registrar_timeout():
    d = _load()
    d["consecutive_timeouts"] = d.get("consecutive_timeouts", 0) + 1
    d["last_failure"]         = _ahora_str()

    errores = d.get("errores_recientes", [])
    errores.append(f"{_ahora_str()} TIMEOUT #{d['consecutive_timeouts']}")
    d["errores_recientes"] = errores[-10:]

    if d["consecutive_timeouts"] >= 3:
        d["modo_emergencia"] = True

    _save(d)
    return d["consecutive_timeouts"]

def registrar_placeholder(placeholder):
    d = _load()
    vistos = d.get("placeholders_vistos", [])
    if placeholder not in vistos:
        vistos.append(placeholder)
    d["placeholders_vistos"] = vistos[-20:]
    _save(d)

# ── Consultas de estado ──────────────────────────────────────────────────────

def necesita_reparacion():
    d = _load()
    return (
        d.get("consecutive_timeouts", 0) >= 3 or
        d.get("consecutive_failures", 0) >= 3 or
        d.get("modo_emergencia", False)
    )

def modo_emergencia_activo():
    return _load().get("modo_emergencia", False)

def get_verticales_bloqueados():
    return _load().get("verticales_saturados", [])

def get_palabras_clave_bloqueadas():
    return _load().get("palabras_clave_bloqueadas", [])

def get_nombres_bloqueados():
    return _load().get("nombres_bloqueados", [])

def get_diagnostico():
    d = _load()
    return {
        "consecutive_timeouts": d.get("consecutive_timeouts", 0),
        "consecutive_failures": d.get("consecutive_failures", 0),
        "last_success":         d.get("last_success", "nunca"),
        "last_failure":         d.get("last_failure", "nunca"),
        "total_ok_24h":         d.get("total_ok_24h", 0),
        "total_fail_24h":       d.get("total_fail_24h", 0),
        "modo_emergencia":      d.get("modo_emergencia", False),
        "ciclo_reparacion":     d.get("ciclo_reparacion", 0),
        "ultimas_ideas":        d.get("ultimas_ideas", []),
        "verticales_saturados": d.get("verticales_saturados", []),
        "errores_recientes":    d.get("errores_recientes", []),
        "placeholders_vistos":  d.get("placeholders_vistos", []),
    }

# ── Auto-reparacion ──────────────────────────────────────────────────────────

def auto_reparar(telegram_fn=None, chat_id=None):
    d = _load()
    d["ciclo_reparacion"] = d.get("ciclo_reparacion", 0) + 1
    ciclo = d["ciclo_reparacion"]

    acciones = []

    # Limpiar estado critico
    d["consecutive_timeouts"] = 0
    d["consecutive_failures"] = 0
    d["modo_emergencia"]      = False

    if ciclo == 1:
        # Bloquear vertical actual, forzar diversidad
        ideas_recientes = d.get("ultimas_ideas", [])[-3:]
        if ideas_recientes:
            acciones.append(f"Bloqueando verticales de: {', '.join(ideas_recientes)}")
        d["modo_emergencia"] = False

    elif ciclo == 2:
        # Reducir temperatura en config
        acciones.append("Reduciendo temperatura Groq a 0.6")
        try:
            os.makedirs("config", exist_ok=True)
            cfg_path = "config/prompt_weights.json"
            cfg = {}
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["temperatura_groq"] = 0.6
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception as e:
            acciones.append(f"Error config: {e}")

    elif ciclo >= 3:
        # Reset completo
        acciones.append("Reset completo de estado watchdog")
        d["consecutive_timeouts"] = 0
        d["consecutive_failures"] = 0
        d["verticales_saturados"] = []
        d["palabras_clave_bloqueadas"] = []
        d["ciclo_reparacion"]    = 0
        d["modo_emergencia"]     = False
        # Restaurar temperatura
        try:
            cfg_path = "config/prompt_weights.json"
            cfg = {}
            if os.path.exists(cfg_path):
                with open(cfg_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["temperatura_groq"] = 0.85
            with open(cfg_path, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except: pass

    _save(d)

    msg = (
        f"🔧 <b>Auto-reparacion ciclo {ciclo}</b>\n\n"
        + "\n".join(f"• {a}" for a in acciones)
        + f"\n\nTimeouts reseteados. Reintentando en 2 min."
    )
    print(msg.replace("<b>","").replace("</b>",""))
    if telegram_fn and chat_id:
        try: telegram_fn(chat_id, msg)
        except: pass

    return msg

def bloquear_vertical(vertical):
    d = _load()
    saturados = d.get("verticales_saturados", [])
    v = str(vertical).lower()
    if v not in saturados:
        saturados.append(v)
    d["verticales_saturados"] = saturados[-10:]
    _save(d)

def bloquear_nombre(nombre):
    d = _load()
    nombres = d.get("nombres_bloqueados", [])
    if nombre not in nombres:
        nombres.append(nombre)
    d["nombres_bloqueados"] = nombres[-30:]
    _save(d)

def reset_estado():
    d = _load()
    d["consecutive_timeouts"] = 0
    d["consecutive_failures"] = 0
    d["modo_emergencia"]      = False
    d["ciclo_reparacion"]     = 0
    _save(d)

# fin agents/watchdog.py
