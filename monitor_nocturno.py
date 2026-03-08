import os
import sys
import json
import time
import logging
import subprocess
import threading
import csv
import requests
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler

import pytz

os.environ["PYTHONUTF8"] = "1"
ZONA = pytz.timezone("Europe/Madrid")

def _configurar_logger():
    os.makedirs(os.path.join("data", "logs"), exist_ok=True)
    log_path = os.path.join("data", "logs", datetime.now(ZONA).strftime("%Y-%m-%d") + ".log")
    logger = logging.getLogger("validationidea")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        fh = TimedRotatingFileHandler(log_path, when="W0", interval=1, backupCount=4, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(ch)
    return logger

_logger = _configurar_logger()

def log(msg):
    _logger.info(msg)

TELEGRAM_TOKEN   = ""
TELEGRAM_CHAT_ID = ""

def _base():
    return f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def enviar_telegram(mensaje):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        resp = requests.post(
            f"{_base()}/sendMessage",
            json={"chat_id": TELEGRAM_CHAT_ID, "text": mensaje, "parse_mode": "HTML"},
            timeout=15
        )
        if resp.status_code == 200:
            log("📱 Telegram enviado")
        else:
            log(f"⚠️ Telegram HTTP {resp.status_code}")
    except Exception as e:
        log(f"❌ Error Telegram: {e}")

def responder(chat_id, mensaje):
    try:
        # Telegram límite 4096 chars
        mensaje = str(mensaje)[:4000]
        requests.post(
            f"{_base()}/sendMessage",
            json={"chat_id": str(chat_id), "text": mensaje, "parse_mode": "HTML"},
            timeout=15
        )
    except Exception as e:
        log(f"❌ Error responder: {e}")

def extraer_resultado_batch(salida: str):
    nombre = score = url = ""
    for linea in salida.split("\n"):
        l = linea.strip()
        if l.startswith("NOTION_URL:"):
            url = l.replace("NOTION_URL:", "").strip()
        elif "✅ Sincronizada:" in l:
            nombre = l.split("✅ Sincronizada:")[-1].strip().replace("│","").strip()
        elif l.startswith("SCORE_FINAL:"):
            score = l.replace("SCORE_FINAL:", "").strip()
        elif "📊 Score:" in l and not score:
            score = l.split("📊 Score:")[-1].strip().split("|")[0].strip().replace("│","").strip()
    return nombre, score, url

# ════════════════════════════════════════════════════════
#  MIGRACIÓN AUTOMÁTICA DE KB AL ARRANCAR
# ════════════════════════════════════════════════════════
def migrar_kb_si_necesario():
    try:
        from agents.knowledge_base import get_stats, registrar_idea
        stats = get_stats()
        if stats.get("total_ideas", 0) > 0:
            log(f"✅ KB ya tiene {stats['total_ideas']} ideas — no necesita migración")
            return

        ruta = "data/ideas.json"
        if not os.path.exists(ruta):
            log("📭 No hay ideas.json que migrar")
            return

        with open(ruta, "r", encoding="utf-8") as f:
            ideas = json.load(f)

        if not ideas:
            return

        log(f"🔄 Migrando {len(ideas)} ideas a KB...")
        migradas = 0
        for idea in ideas:
            try:
                if "scores" not in idea:
                    idea["scores"] = {
                        "critico": 70, "viral": 50, "generador": 70,
                        "monetizacion": 65, "ejecutabilidad": 70, "timing": 65,
                        "score_total": 68.0
                    }
                elif "score_total" not in idea.get("scores", {}):
                    s = idea["scores"]
                    s["score_total"] = round(
                        s.get("critico",70)*0.25 + s.get("generador",70)*0.25 +
                        s.get("ejecutabilidad",70)*0.20 + s.get("monetizacion",65)*0.15 +
                        s.get("timing",65)*0.10 + s.get("viral",50)*0.05, 1
                    )
                registrar_idea(idea)
                migradas += 1
            except Exception as e:
                log(f"⚠️ Error migrando '{idea.get('nombre','?')}': {e}")

        stats2 = get_stats()
        log(f"✅ Migración completada: {migradas} ideas | Score promedio: {stats2['score_promedio']}")
        enviar_telegram(
            f"🔄 <b>KB migrada automáticamente</b>\n"
            f"✅ {migradas} ideas cargadas\n"
            f"📊 Score promedio: {stats2['score_promedio']}/100\n"
            f"⭐ Mejor idea: {stats2['mejor_idea']}"
        )
    except Exception as e:
        log(f"❌ Error en migración KB: {e}")

# ════════════════════════════════════════════════════════
#  COMANDOS DEL BOT
# ════════════════════════════════════════════════════════
def handle_start(chat_id, _=""):
    responder(chat_id,
        "🤖 <b>ValidationIdea Bot v2</b>\n\n"
        "<b>Comandos:</b>\n"
        "💡 /idea [tema] — Genera idea (ej: /idea salud)\n"
        "📊 /status — Estado del sistema\n"
        "🏆 /top — Top 5 mejores ideas\n"
        "📋 /stats — Estadísticas KB\n"
        "🚀 /ranking — Top 5 más ejecutables HOY\n"
        "🛠️ /ejecutar [nombre] — Prompt MVP\n"
        "🔍 /buscar [palabra] — Buscar ideas\n"
        "🌐 /tendencias — Tendencias tech ahora\n"
        "🔄 /cola — Ideas pendientes Notion\n"
        "🐛 /debug — Ver último error del sistema\n\n"
        "<b>O escríbeme directamente:</b>\n"
        "\"genera una idea de fitness\"\n"
        "\"ejecuta CodeGenius\"\n"
        "\"muéstrame el ranking\""
    )

def handle_status(chat_id, _=""):
    try:
        from agents.knowledge_base import get_stats, contar_pendientes
        stats  = get_stats()
        cola_n = contar_pendientes()
        total_local = 0
        try:
            with open("data/ideas.json", "r", encoding="utf-8") as f:
                total_local = len(json.load(f))
        except:
            pass
        responder(chat_id,
            f"📊 <b>Estado del sistema</b>\n"
            f"🕐 {datetime.now(ZONA).strftime('%d/%m/%Y %H:%M')}\n\n"
            f"✅ Monitor: <b>Activo 24/7</b>\n"
            f"✅ Groq: <b>Activo</b>\n"
            f"✅ Notion: <b>Activo</b>\n\n"
            f"💡 Ideas generadas: <b>{total_local}</b>\n"
            f"📚 Ideas en KB: <b>{stats.get('total_ideas', 0)}</b>\n"
            f"📊 Score promedio: <b>{stats.get('score_promedio', 0)}/100</b>\n"
            f"🏆 Mejor score: <b>{stats.get('mejor_score', 0)}/100</b>\n"
            f"🎯 Tasa de éxito: <b>{stats.get('tasa_exito', 'N/A')}</b>\n"
            f"⏳ Cola pendiente: <b>{cola_n}</b>"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_top(chat_id, _=""):
    try:
        from agents.knowledge_base import get_top_ideas
        top = get_top_ideas(5)
        if not top:
            responder(chat_id, "📭 Aún no hay ideas en el TOP.\nUsa /idea para generar la primera.")
            return
        texto = "🏆 <b>TOP 5 MEJORES IDEAS</b>\n\n"
        for i, idea in enumerate(top, 1):
            s = idea.get("score_total", 0)
            e = "💎" if s >= 90 else "⭐" if s >= 85 else "🔥" if s >= 80 else "💡"
            texto += (
                f"{e} <b>{i}. {idea.get('nombre','?')}</b>\n"
                f"   📊 {s}/100 | {idea.get('tipo','?')} | {idea.get('vertical','?')}\n"
                f"   📅 {idea.get('fecha','N/A')}\n\n"
            )
        texto += "Usa /ejecutar [nombre] para obtener el prompt MVP."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_stats(chat_id, _=""):
    try:
        from agents.knowledge_base import get_stats
        stats = get_stats()
        responder(chat_id,
            f"📈 <b>Estadísticas KB</b>\n\n"
            f"💡 Ideas analizadas: <b>{stats.get('total_ideas', 0)}</b>\n"
            f"📊 Score promedio: <b>{stats.get('score_promedio', 0)}/100</b>\n"
            f"🏆 Mejor score: <b>{stats.get('mejor_score', 0)}/100</b>\n"
            f"🌐 Vertical ganadora: <b>{stats.get('mejor_vertical', 'N/A')}</b>\n"
            f"🚀 Tipo ganador: <b>{stats.get('mejor_tipo', 'N/A')}</b>\n"
            f"⭐ Mejor idea: <b>{stats.get('mejor_idea', 'N/A')}</b>\n"
            f"🎯 Tasa de éxito: <b>{stats.get('tasa_exito', 'N/A')}</b>"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_idea(chat_id, tema=""):
    if tema:
        responder(chat_id, f"⏳ <b>Generando idea sobre '{tema}'...</b>\nEspera 45-90 segundos ☕")
    else:
        responder(chat_id, "⏳ <b>Generando idea completa...</b>\nEspera 45-90 segundos ☕\n(DAFO + economía + prompt MVP)")
    try:
        env = os.environ.copy()
        if tema:
            env["IDEA_TOPIC"] = tema
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, timeout=150, env=env
        )
        salida  = resultado.stdout.decode("utf-8", errors="replace")
        errores = resultado.stderr.decode("utf-8", errors="replace")
        nombre, score, url = extraer_resultado_batch(salida)

        if nombre:
            try:
                score_num = float(str(score).split("/")[0].strip())
            except:
                score_num = 0
            emoji = "⭐" if score_num >= 75 else "💡"
            msg = f"{emoji} <b>¡Idea generada!</b>\n\n🚀 <b>{nombre}</b>\n📊 Score: <b>{score}/100</b>\n"
            if url:
                msg += f"\n📋 <b>Informe completo en Notion:</b>\n{url}"
            else:
                msg += "\n📋 Informe disponible en Notion."
            responder(chat_id, msg)
        else:
            # Mostrar error real para diagnóstico
            error_info = ""
            for linea in (salida + errores).split("\n"):
                if any(p in linea for p in ["❌", "Error", "error", "Traceback", "Exception"]):
                    error_info += linea.strip() + "\n"
            error_info = error_info[:600] if error_info else (salida[-400:] if salida else "Sin output")
            responder(chat_id,
                f"❌ <b>Error generando idea</b>\n\n"
                f"<code>{error_info}</code>\n\n"
                f"Usa /debug para ver el log completo."
            )
            # Guardar último error
            try:
                os.makedirs("data", exist_ok=True)
                with open("data/ultimo_error.txt", "w", encoding="utf-8") as f:
                    f.write(f"=== {datetime.now()} ===\n{salida}\n{errores}")
            except:
                pass
    except subprocess.TimeoutExpired:
        responder(chat_id, "⏰ Timeout (>150s) — el sistema lo reintentará en 30 min.")
    except Exception as e:
        responder(chat_id, f"❌ Error inesperado: {e}")

def handle_debug(chat_id, _=""):
    """Muestra el último error del sistema"""
    responder(chat_id, "🔍 Ejecutando diagnóstico completo...")
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, timeout=60, env=os.environ.copy()
        )
        salida  = resultado.stdout.decode("utf-8", errors="replace")[-1500:]
        errores = resultado.stderr.decode("utf-8", errors="replace")[-500:]
        codigo  = resultado.returncode
        responder(chat_id,
            f"🐛 <b>Debug run_batch.py</b>\n"
            f"Return code: {codigo}\n\n"
            f"<b>stdout:</b>\n<code>{salida}</code>\n\n"
            f"<b>stderr:</b>\n<code>{errores[:300]}</code>"
        )
    except subprocess.TimeoutExpired:
        # Si hay último error guardado
        try:
            with open("data/ultimo_error.txt", "r", encoding="utf-8") as f:
                contenido = f.read()[-1500:]
            responder(chat_id, f"📋 <b>Último error guardado:</b>\n<code>{contenido}</code>")
        except:
            responder(chat_id, "⏰ Timeout en diagnóstico — revisa logs de Railway.")
    except Exception as e:
        responder(chat_id, f"❌ Error en debug: {e}")

def handle_cola(chat_id, _=""):
    try:
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta):
            responder(chat_id, "✅ Cola vacía — todo sincronizado con Notion.")
            return
        with open(ruta, newline="", encoding="utf-8") as f:
            pendientes = list(csv.DictReader(f))
        if not pendientes:
            responder(chat_id, "✅ Cola vacía — todo sincronizado con Notion.")
            return
        texto = f"📋 <b>Cola: {len(pendientes)} pendiente(s)</b>\n\n"
        for p in pendientes[:5]:
            texto += f"• {p.get('nombre_idea','?')} (intento {p.get('intentos',1)}/3)\n"
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_ranking(chat_id, _=""):
    try:
        from agents.knowledge_base import _cargar
        kb    = _cargar()
        ideas = kb.get("ideas", [])
        if not ideas:
            responder(chat_id, "📭 Aún no hay ideas. Usa /idea para generar.")
            return
        def score_ejecutable(idea):
            s = idea.get("scores", {})
            return (s.get("ejecutabilidad",0)*0.40 + s.get("generador",0)*0.35 + s.get("timing",0)*0.25)
        top = sorted(ideas, key=score_ejecutable, reverse=True)[:5]
        texto = "🚀 <b>TOP 5 IDEAS MÁS EJECUTABLES AHORA</b>\n\n"
        for i, idea in enumerate(top, 1):
            s = idea.get("scores", {})
            texto += (
                f"<b>{i}. {idea.get('nombre','?')}</b>\n"
                f"   ⚡ Ejecutabilidad: {s.get('ejecutabilidad',0)}/100\n"
                f"   💰 Revenue rápido: {s.get('generador',0)}/100\n"
                f"   ⏰ Timing: {s.get('timing',0)}/100\n"
                f"   📊 Score total: {idea.get('score_total',0)}/100\n\n"
            )
        texto += "Usa /ejecutar [nombre] para el prompt MVP."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def _buscar_idea_por_nombre(nombre_buscado: str):
    try:
        with open("data/ideas.json", "r", encoding="utf-8") as f:
            todas = json.load(f)
        nb = nombre_buscado.lower()
        for idea in reversed(todas):
            if idea.get("nombre", "").lower() == nb:
                return idea
        for idea in reversed(todas):
            if nb in idea.get("nombre", "").lower():
                return idea
    except:
        pass
    return None

def handle_ejecutar(chat_id, nombre_arg=""):
    try:
        idea_target = None
        if nombre_arg:
            idea_target = _buscar_idea_por_nombre(nombre_arg)
            if not idea_target:
                responder(chat_id,
                    f"❌ No encontré ninguna idea con '<b>{nombre_arg}</b>'.\n\n"
                    f"Usa /top o /ranking para ver los nombres disponibles."
                )
                return
        else:
            from agents.knowledge_base import _cargar
            kb    = _cargar()
            ideas = kb.get("ideas", [])
            if not ideas:
                responder(chat_id, "📭 Sin ideas. Usa /idea primero.")
                return
            def score_ejecutable(idea):
                s = idea.get("scores", {})
                return (s.get("ejecutabilidad",0)*0.40 + s.get("generador",0)*0.35 + s.get("timing",0)*0.25)
            top1       = sorted(ideas, key=score_ejecutable, reverse=True)[0]
            idea_target = _buscar_idea_por_nombre(top1.get("nombre", ""))

        if not idea_target:
            responder(chat_id, "⚠️ Datos no encontrados. Genera nuevas ideas con /idea.")
            return

        nombre_final = idea_target.get("nombre", "?")
        pm           = idea_target.get("prompt_mvp", {})
        prompt_texto = pm.get("prompt_completo", "")
        ia_rec       = pm.get("ia_recomendada", "Claude 3.5 Sonnet en Cursor IDE")
        score        = idea_target.get("scores", {}).get("score_total", "?")

        if not prompt_texto:
            responder(chat_id,
                f"⚠️ <b>{nombre_final}</b> fue generada con el sistema antiguo y no tiene prompt MVP.\n"
                f"Usa /idea para generar ideas nuevas con el sistema v2."
            )
            return

        responder(chat_id,
            f"🛠️ <b>EJECUTA HOY: {nombre_final}</b>\n"
            f"📊 Score: {score}/100\n\n"
            f"🤖 <b>IA recomendada:</b>\n{ia_rec}\n\n"
            f"📋 <b>Copia este prompt en Cursor/Claude:</b>\n\n"
            f"{prompt_texto[:3500]}"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_buscar(chat_id, palabra=""):
    if not palabra:
        responder(chat_id, "❓ Escribe qué buscar. Ejemplo: /buscar fintech")
        return
    try:
        with open("data/ideas.json", "r", encoding="utf-8") as f:
            todas = json.load(f)
        pl = palabra.lower()
        encontradas = [
            i for i in todas
            if pl in i.get("nombre","").lower()
            or pl in i.get("vertical","").lower()
            or pl in str(i.get("tags",[])).lower()
            or pl in i.get("tagline","").lower()
        ]
        if not encontradas:
            responder(chat_id, f"🔍 No encontré ideas relacionadas con '<b>{palabra}</b>'.")
            return
        texto = f"🔍 <b>Ideas relacionadas con '{palabra}'</b>\n\n"
        for i, idea in enumerate(encontradas[-5:], 1):
            s = idea.get("scores", {}).get("score_total", 0)
            texto += f"<b>{i}. {idea.get('nombre','?')}</b>\n   {idea.get('tagline','')}\n   📊 Score: {s}/100\n\n"
        texto += "Usa /ejecutar [nombre] para el prompt MVP."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_tendencias(chat_id, _=""):
    try:
        from agents.trend_scout import actualizar_tendencias
        responder(chat_id, "🔄 Consultando HackerNews...")
        tendencias = actualizar_tendencias()
        if not tendencias:
            responder(chat_id, "⚠️ No hay tendencias disponibles ahora.")
            return
        texto = "🌐 <b>TENDENCIAS TECH AHORA</b>\n(fuente: HackerNews)\n\n"
        for i, t in enumerate(tendencias, 1):
            texto += f"{i}. {t}\n"
        texto += "\n💡 La próxima idea usará estas tendencias.\nUsa /idea [tema] para generar sobre alguna."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

# ════════════════════════════════════════════════════════
#  LENGUAJE NATURAL
# ════════════════════════════════════════════════════════
def procesar_lenguaje_natural(chat_id, texto: str):
    t = texto.lower()
    if any(p in t for p in ["genera", "crea", "nueva idea", "idea sobre", "idea de"]):
        for kw in ["sobre ", "de ", "acerca de "]:
            if kw in t:
                tema = t.split(kw)[-1].strip()
                if len(tema) > 2:
                    handle_idea(chat_id, tema)
                    return
        handle_idea(chat_id, "")
        return
    if any(p in t for p in ["estado", "cómo va", "como va", "activo", "funciona"]):
        handle_status(chat_id)
        return
    if any(p in t for p in ["top", "mejores", "mejor idea"]):
        handle_top(chat_id)
        return
    if any(p in t for p in ["ranking", "ejecutable", "cuál ejecuto", "cual ejecuto"]):
        handle_ranking(chat_id)
        return
    if any(p in t for p in ["ejecuta", "construye", "prompt de", "cómo hacer", "como hacer"]):
        partes = texto.split()
        if len(partes) > 1:
            handle_ejecutar(chat_id, " ".join(partes[1:]))
        else:
            handle_ejecutar(chat_id, "")
        return
    if any(p in t for p in ["busca", "buscar", "encuentra"]):
        partes = texto.split()
        if len(partes) > 1:
            handle_buscar(chat_id, " ".join(partes[1:]))
        return
    if any(p in t for p in ["tendencia", "trend", "qué está pasando", "novedades"]):
        handle_tendencias(chat_id)
        return
    if any(p in t for p in ["stats", "estadística", "cuántas", "cuantas"]):
        handle_stats(chat_id)
        return
    if any(p in t for p in ["debug", "error", "fallo", "problema"]):
        handle_debug(chat_id)
        return
    responder(chat_id,
        "🤖 No entendí bien. Prueba con:\n\n"
        "• \"genera una idea de [tema]\"\n"
        "• \"ejecuta [nombre de idea]\"\n"
        "• \"muéstrame el ranking\"\n"
        "• \"busca fintech\"\n\n"
        "O usa /start para ver todos los comandos."
    )

COMANDOS = {
    "/start":      handle_start,
    "/status":     handle_status,
    "/top":        handle_top,
    "/stats":      handle_stats,
    "/idea":       handle_idea,
    "/cola":       handle_cola,
    "/ranking":    handle_ranking,
    "/ejecutar":   handle_ejecutar,
    "/buscar":     handle_buscar,
    "/tendencias": handle_tendencias,
    "/debug":      handle_debug,
}

# ════════════════════════════════════════════════════════
#  LOOP DEL BOT
# ════════════════════════════════════════════════════════
def iniciar_bot():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not TELEGRAM_TOKEN:
        log("⚠️ TELEGRAM_BOT_TOKEN no configurado — bot desactivado")
        return
    try:
        requests.get(f"{_base()}/deleteWebhook?drop_pending_updates=true", timeout=10)
        log("🧹 Webhook eliminado")
    except:
        pass
    log("🤖 ✅ Bot iniciado — polling directo + lenguaje natural")
    offset = 0
    while True:
        try:
            resp = requests.get(
                f"{_base()}/getUpdates",
                params={"timeout": 30, "offset": offset, "allowed_updates": ["message"]},
                timeout=40
            )
            if resp.status_code != 200:
                log(f"⚠️ getUpdates HTTP {resp.status_code}")
                time.sleep(5)
                continue
            updates = resp.json().get("result", [])
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    msg     = update.get("message", {})
                    text    = msg.get("text", "").strip()
                    chat_id = msg.get("chat", {}).get("id")
                    if not text or not chat_id:
                        continue
                    log(f"📩 '{text[:50]}' de {chat_id}")
                    if text.startswith("/"):
                        partes = text.split(maxsplit=1)
                        cmd    = partes[0].lower().split("@")[0]
                        arg    = partes[1].strip() if len(partes) > 1 else ""
                        fn     = COMANDOS.get(cmd)
                        if fn:
                            threading.Thread(target=fn, args=(chat_id, arg), daemon=True).start()
                        else:
                            responder(chat_id, "❓ Comando no reconocido. Escribe /start.")
                    else:
                        threading.Thread(
                            target=procesar_lenguaje_natural,
                            args=(chat_id, text), daemon=True
                        ).start()
                except Exception as e:
                    log(f"❌ Error procesando update: {e}")
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            log(f"❌ Bot loop error: {e}")
            time.sleep(10)

# ════════════════════════════════════════════════════════
#  FUNCIONES DEL MONITOR
# ════════════════════════════════════════════════════════
def ejecutar_script(nombre):
    log(f"▶️  {nombre}...")
    try:
        resultado = subprocess.run([sys.executable, nombre], capture_output=True, timeout=240)
        salida  = resultado.stdout.decode("utf-8", errors="replace").strip()
        errores = resultado.stderr.decode("utf-8", errors="replace").strip()
        if salida:
            for linea in salida.split("\n"):
                if linea.strip():
                    log(f"  │ {linea.strip()}")
        if resultado.returncode != 0 and errores:
            for linea in errores.split("\n")[:5]:
                if linea.strip():
                    log(f"  ⚠️ {linea.strip()}")
        return resultado.returncode == 0, salida
    except subprocess.TimeoutExpired:
        log(f"⏰ Timeout en {nombre}")
        return False, "Timeout"
    except Exception as e:
        log(f"❌ Error ejecutando {nombre}: {e}")
        return False, str(e)

def hc_groq():
    try:
        import groq
        client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"), timeout=10)
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "ok"}],
            max_tokens=3, temperature=0
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)[:200]

def hc_notion():
    try:
        token = os.environ.get("NOTION_TOKEN", "")
        db_id = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
        resp  = requests.get(
            f"https://api.notion.com/v1/databases/{db_id}",
            headers={"Authorization": f"Bearer {token}", "Notion-Version": "2022-06-28"},
            timeout=10
        )
        return (True, "OK") if resp.status_code == 200 else (False, f"HTTP {resp.status_code}")
    except Exception as e:
        return False, str(e)[:200]

def ejecutar_health_check():
    log("🏥 Health check iniciado...")
    checks = {"Groq": hc_groq(), "Notion": hc_notion()}
    fallos = [(srv, msg) for srv, (ok, msg) in checks.items() if not ok]
    if fallos:
        lineas = "\n".join(f"❌ <b>{srv}</b>: {msg}" for srv, msg in fallos)
        enviar_telegram(f"🚨 <b>HEALTH CHECK FALLO</b>\n{lineas}")
        log(f"🚨 Fallos: {[s for s, _ in fallos]}")
    else:
        log("✅ Health check OK — Groq ✅  Notion ✅")

def procesar_cola_csv():
    try:
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta):
            return
        from agents.notion_sync_agent import sync_idea_to_notion
        with open(ruta, newline="", encoding="utf-8") as f:
            pendientes = list(csv.DictReader(f))
        if not pendientes:
            return
        log(f"📋 Cola CSV: {len(pendientes)} pendiente(s)")
        eliminados = []
        for fila in pendientes:
            nombre   = fila.get("nombre_idea", "?")
            intentos = int(fila.get("intentos", 1))
            ts       = fila.get("timestamp", "")
            if intentos > 3:
                eliminados.append(ts)
                continue
            try:
                datos = json.loads(fila.get("datos_json", "{}"))
                url   = sync_idea_to_notion(datos)
                if url:
                    log(f"✅ Reintento exitoso: '{nombre}'")
                    eliminados.append(ts)
                else:
                    fila["intentos"] = str(intentos + 1)
            except Exception as e:
                log(f"❌ Reintento fallido '{nombre}': {e}")
                fila["intentos"] = str(intentos + 1)
        restantes = [f for f in pendientes if f.get("timestamp") not in eliminados]
        with open(ruta, "w", newline="", encoding="utf-8") as f:
            if restantes:
                writer = csv.DictWriter(f, fieldnames=restantes[0].keys())
                writer.writeheader()
                writer.writerows(restantes)
            else:
                f.write("")
    except Exception as e:
        log(f"❌ Error cola CSV: {e}")

def generar_nueva_idea():
    log("🧠 Generando nueva idea automática...")
    exito, salida = ejecutar_script("run_batch.py")
    if exito:
        nombre, score, url = extraer_resultado_batch(salida)
        if nombre:
            try:
                score_num = float(str(score).split("/")[0].strip())
            except:
                score_num = 0
            msg = (f"⭐ <b>IDEA DESTACADA — score {score}/100</b>\n\n🚀 <b>{nombre}</b>\n"
                   if score_num >= 75 else
                   f"💡 <b>Nueva idea generada</b>\n\n🚀 <b>{nombre}</b>\n📊 Score: <b>{score}/100</b>\n")
            if url:
                msg += f"📋 <b>Informe en Notion:</b>\n{url}"
            enviar_telegram(msg)
    else:
        log("⚠️ run_batch.py falló — se reintentará en 30 min")
    return exito

def enviar_resumen_diario():
    log("☀️ Resumen diario (08:00)...")
    try:
        from agents.knowledge_base import get_stats, get_top_ideas, contar_pendientes
        stats  = get_stats()
        top3   = get_top_ideas(3)
        top_txt = ""
        for i, idea in enumerate(top3, 1):
            top_txt += f"\n{i}. <b>{idea.get('nombre','?')}</b> → {idea.get('score_total',0)}pts"
        cola_n   = contar_pendientes()
        cola_txt = f"\n⏳ Cola pendiente: <b>{cola_n}</b>" if cola_n > 0 else ""
        enviar_telegram(
            f"☀️ <b>Resumen diario — ValidationIdea v2</b>\n"
            f"📅 {datetime.now(ZONA).strftime('%d/%m/%Y')}\n\n"
            f"💡 Ideas generadas: <b>{stats.get('total_ideas', 0)}</b>\n"
            f"📊 Score promedio: <b>{stats.get('score_promedio', 0)}/100</b>\n"
            f"🎯 Tasa de éxito: <b>{stats.get('tasa_exito', 'N/A')}</b>\n"
            f"⭐ Mejor idea: <b>{stats.get('mejor_idea', 'N/A')}</b>"
            f"\n\n🏅 <b>TOP 3:</b>{top_txt}{cola_txt}\n\n"
            f"✅ Sistema operativo 24/7"
        )
    except Exception as e:
        log(f"❌ Error resumen: {e}")
        enviar_telegram(f"☀️ Sistema activo — error en resumen: {e}")

# ════════════════════════════════════════════════════════
#  MAIN
# ════════════════════════════════════════════════════════
def main():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

    log("🚀 monitor_nocturno.py iniciado — P1→P10 activos")

    # Migrar KB automáticamente si está vacía
    migrar_kb_si_necesario()

    enviar_telegram(
        "🟢 <b>Monitor ValidationIdea v2 arrancado</b>\n\n"
        "✅ P1–P10 activos\n"
        "✅ Ideas cada 30 min automáticamente\n"
        "✅ Informes: DAFO + economía + prompt MVP\n"
        "✅ Bot con lenguaje natural activado\n\n"
        "📱 Escribe /start para ver comandos\n"
        "🐛 Escribe /debug si algo falla"
    )

    bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
    bot_thread.start()
    log("🤖 Bot arrancado en hilo paralelo")

    ahora_utc        = datetime.now(timezone.utc)
    ultimo_batch     = ahora_utc - timedelta(minutes=31)
    ultimo_informe   = ahora_utc - timedelta(minutes=6)
    ultimo_health    = ahora_utc - timedelta(hours=1, minutes=1)
    ultima_tendencia = ahora_utc - timedelta(hours=3)
    dia_resumen      = -1
    dia_mant         = -1

    while True:
        try:
            ahora_utc   = datetime.now(timezone.utc)
            ahora_local = datetime.now(ZONA)
            hora = ahora_local.hour
            dia  = ahora_local.day

            if (ahora_utc - ultimo_batch).total_seconds() >= 30 * 60:
                generar_nueva_idea()
                ultimo_batch = ahora_utc

            if (ahora_utc - ultimo_informe).total_seconds() >= 5 * 60:
                ejecutar_script("run_monitor.py")
                procesar_cola_csv()
                ultimo_informe = ahora_utc

            if (ahora_utc - ultimo_health).total_seconds() >= 60 * 60:
                ejecutar_health_check()
                ultimo_health = ahora_utc

            if (ahora_utc - ultima_tendencia).total_seconds() >= 3 * 60 * 60:
                try:
                    from agents.trend_scout import actualizar_tendencias
                    actualizar_tendencias()
                    log("🌐 Tendencias actualizadas")
                except Exception as e:
                    log(f"⚠️ Error tendencias: {e}")
                ultima_tendencia = ahora_utc

            if hora == 8 and dia != dia_resumen:
                enviar_resumen_diario()
                dia_resumen = dia

            if hora == 3 and dia != dia_mant:
                ejecutar_script("run_monitor.py")
                dia_mant = dia

        except Exception as e:
            log(f"❌ Error en loop principal: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
