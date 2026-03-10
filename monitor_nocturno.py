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
        fh = TimedRotatingFileHandler(log_path, when="midnight", interval=1, backupCount=30, encoding="utf-8")
        fh.setFormatter(logging.Formatter("%(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(fh)
        ch = logging.StreamHandler(sys.stdout)
        ch.setFormatter(logging.Formatter("[%(asctime)s] %(message)s", "%Y-%m-%d %H:%M:%S"))
        logger.addHandler(ch)
    return logger

_logger = _configurar_logger()
def log(msg): _logger.info(msg)

TELEGRAM_TOKEN   = ""
TELEGRAM_CHAT_ID = ""

def _base():
    return f"https://api.telegram.org/bot{TELEGRAM_TOKEN}"

def enviar_telegram(mensaje, reply_markup=None):
    if not TELEGRAM_TOKEN or not TELEGRAM_CHAT_ID:
        return
    try:
        payload = {"chat_id": TELEGRAM_CHAT_ID, "text": str(mensaje)[:4000], "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        resp = requests.post(f"{_base()}/sendMessage", json=payload, timeout=15)
        if resp.status_code == 200:
            log("📱 Telegram enviado")
        else:
            log(f"⚠️ Telegram HTTP {resp.status_code}")
    except Exception as e:
        log(f"❌ Error Telegram: {e}")

def responder(chat_id, mensaje, reply_markup=None):
    try:
        payload = {"chat_id": str(chat_id), "text": str(mensaje)[:4000], "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        requests.post(f"{_base()}/sendMessage", json=payload, timeout=15)
    except Exception as e:
        log(f"❌ Error responder: {e}")

def _teclado_feedback(nombre_idea: str) -> dict:
    nombre_safe = nombre_idea[:30]
    return {
        "inline_keyboard": [[
            {"text": "👍 Buena idea", "callback_data": f"like:{nombre_safe}"},
            {"text": "👎 Descartar",  "callback_data": f"dislike:{nombre_safe}"},
        ]]
    }

def extraer_resultado_batch(salida: str):
    nombre = score = url = herramienta = hipotesis = landing_url = ""
    tagline = problema = monetiz = veredicto_critico = recomendacion = ""
    for linea in salida.split("\n"):
        l = linea.strip()
        if   l.startswith("NOTION_URL:"):          url               = l.replace("NOTION_URL:",         "").strip()
        elif l.startswith("SCORE_FINAL:"):          score             = l.replace("SCORE_FINAL:",         "").strip()
        elif l.startswith("HERRAMIENTA_IA:"):       herramienta       = l.replace("HERRAMIENTA_IA:",      "").strip()
        elif l.startswith("HIPOTESIS:"):            hipotesis         = l.replace("HIPOTESIS:",           "").strip()
        elif l.startswith("LANDING_URL:"):          landing_url       = l.replace("LANDING_URL:",         "").strip()
        elif l.startswith("TAGLINE:"):              tagline           = l.replace("TAGLINE:",             "").strip()
        elif l.startswith("PROBLEMA:"):             problema          = l.replace("PROBLEMA:",            "").strip()
        elif l.startswith("MONETIZ_S1:"):           monetiz           = l.replace("MONETIZ_S1:",          "").strip()
        elif l.startswith("VEREDICTO_CRITICO:"):    veredicto_critico = l.replace("VEREDICTO_CRITICO:",   "").strip()
        elif l.startswith("RECOMENDACION:"):        recomendacion     = l.replace("RECOMENDACION:",       "").strip()
        elif "✅ Sincronizada:" in l:               nombre            = l.split("✅ Sincronizada:")[-1].strip()
    return nombre, score, url, herramienta, hipotesis, landing_url, tagline, problema, monetiz, veredicto_critico, recomendacion

def migrar_kb_si_necesario():
    try:
        from agents.knowledge_base import get_stats, registrar_idea
        stats = get_stats()
        if stats.get("total_ideas", 0) > 0:
            log(f"✅ KB ya tiene {stats['total_ideas']} ideas")
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
                if "scores" not in idea or not isinstance(idea["scores"], dict):
                    idea["scores"] = {
                        "critico": 70, "viral": 50, "generador": 70,
                        "monetizacion": 65, "ejecutabilidad": 70, "timing": 65,
                        "score_total": 68.0
                    }
                elif "score_total" not in idea["scores"]:
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
        log(f"✅ Migracion: {migradas} ideas | Promedio: {stats2['score_promedio']}")
        enviar_telegram(
            f"🔄 <b>KB migrada automaticamente</b>\n"
            f"✅ {migradas} ideas cargadas\n"
            f"📊 Score promedio: {stats2['score_promedio']}/100\n"
            f"⭐ Mejor idea: {stats2['mejor_idea']}"
        )
    except Exception as e:
        log(f"❌ Error migracion KB: {e}")

# ── Handlers de comandos ──────────────────────────────────────────────────────

def handle_start(chat_id, _=""):
    responder(chat_id,
        "🤖 <b>ValidationIdea Bot v5</b>\n\n"
        "<b>Comandos:</b>\n"
        "💡 /idea [tema] — Genera idea (ej: /idea salud)\n"
        "📊 /status — Estado del sistema\n"
        "🏆 /top — Top 5 mejores ideas\n"
        "📋 /stats — Estadísticas KB\n"
        "🚀 /ranking — Top 5 más ejecutables HOY\n"
        "🛠️ /ejecutar [nombre] — Prompt MVP completo\n"
        "🔍 /buscar [palabra] — Buscar ideas\n"
        "🌐 /tendencias — Tendencias tech ahora\n"
        "🔄 /cola — Ideas pendientes Notion\n"
        "🧠 /aprender — Ejecutar aprendizaje ahora\n"
        "🐛 /debug — Diagnóstico del sistema\n\n"
        "<b>Feedback en cada idea:</b> 👍 / 👎\n"
        "El sistema aprende cada dia a las 08:00 y tras cada idea."
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
        except: pass
        pesos_ciclo = 0
        try:
            with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
                pw = json.load(f)
                pesos_ciclo = pw.get("ciclos_completados", 0)
        except: pass
        liked = len(stats.get("ideas_liked", []))
        responder(chat_id,
            f"📊 <b>Estado del sistema</b>\n"
            f"🕐 {datetime.now(ZONA).strftime('%d/%m/%Y %H:%M')}\n\n"
            f"✅ Monitor: <b>Activo 24/7</b>\n"
            f"✅ Fuentes: <b>HN + GitHub + Reddit + PH + IA curada</b>\n"
            f"✅ Scoring: <b>IA generadora + IA critica YC</b>\n\n"
            f"💡 Ideas generadas: <b>{total_local}</b>\n"
            f"📚 Ideas en KB: <b>{stats.get('total_ideas',0)}</b>\n"
            f"📊 Score promedio: <b>{stats.get('score_promedio',0)}/100</b>\n"
            f"🏆 Mejor score: <b>{stats.get('mejor_score',0)}/100</b>\n"
            f"🎯 Tasa exito (>75): <b>{stats.get('tasa_exito','N/A')}</b>\n"
            f"🧠 Ciclos de aprendizaje: <b>{pesos_ciclo}</b>\n"
            f"👍 Ideas con like: <b>{liked}</b>\n"
            f"⏳ Cola pendiente: <b>{cola_n}</b>\n\n"
            f"⏱️ Nueva idea cada 30 min\n"
            f"🧠 Aprendizaje diario a las 08:00"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_top(chat_id, _=""):
    try:
        from agents.knowledge_base import get_top_ideas
        top = get_top_ideas(5)
        if not top:
            responder(chat_id, "📭 Aun no hay ideas. Usa /idea.")
            return
        texto = "🏆 <b>TOP 5 MEJORES IDEAS</b>\n\n"
        for i, idea in enumerate(top, 1):
            s      = idea.get("score_total", 0)
            e      = "💎" if s>=90 else "⭐" if s>=85 else "🔥" if s>=80 else "💡"
            fb     = " 👍" if idea.get("feedback")=="like" else " 👎" if idea.get("feedback")=="dislike" else ""
            ia     = f"\n   🤖 {idea.get('herramienta_ia','')[:60]}" if idea.get("herramienta_ia") else ""
            tagline = idea.get("tagline","")[:80]
            texto += (
                f"{e} <b>{i}. {idea.get('nombre','?')}</b>{fb}\n"
                f"   <i>{tagline}</i>\n"
                f"   📊 {s}/100 | {idea.get('tipo','?')} | {idea.get('vertical','?')}\n"
                f"   📅 {idea.get('fecha','N/A')}{ia}\n\n"
            )
        texto += "Usa /ejecutar [nombre] para el prompt MVP."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_stats(chat_id, _=""):
    try:
        from agents.knowledge_base import get_stats
        stats = get_stats()
        pesos_info = ""
        try:
            with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
                pw = json.load(f)
            v_pref = ", ".join(pw.get("verticales_preferidas",[])[:3]) or "N/A"
            v_pen  = ", ".join(pw.get("verticales_penalizadas",[])[:3]) or "N/A"
            tags   = ", ".join(pw.get("tags_exitosos",[])[:5]) or "N/A"
            pesos_info = (
                f"\n\n🧠 <b>Aprendizaje automatico</b>\n"
                f"   Ciclos: <b>{pw.get('ciclos_completados',0)}</b>\n"
                f"   Verticales TOP: <b>{v_pref}</b>\n"
                f"   Verticales evitadas: <b>{v_pen}</b>\n"
                f"   Tags ganadores: <b>{tags}</b>\n"
                f"   Score objetivo: <b>{pw.get('score_objetivo',75)}/100</b>\n"
                f"   Temperatura IA: <b>{pw.get('temperatura_groq',0.85)}</b>"
            )
        except: pass
        responder(chat_id,
            f"📈 <b>Estadisticas KB</b>\n\n"
            f"💡 Ideas analizadas: <b>{stats.get('total_ideas',0)}</b>\n"
            f"📊 Score promedio: <b>{stats.get('score_promedio',0)}/100</b>\n"
            f"🏆 Mejor score: <b>{stats.get('mejor_score',0)}/100</b>\n"
            f"🌐 Vertical ganadora: <b>{stats.get('mejor_vertical','N/A')}</b>\n"
            f"🚀 Tipo ganador: <b>{stats.get('mejor_tipo','N/A')}</b>\n"
            f"⭐ Mejor idea: <b>{stats.get('mejor_idea','N/A')}</b>\n"
            f"🎯 Tasa de exito: <b>{stats.get('tasa_exito','N/A')}</b>\n"
            f"👍 Ideas con like: <b>{len(stats.get('ideas_liked',[]))}</b>"
            f"{pesos_info}"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_aprender(chat_id, _=""):
    responder(chat_id, "🧠 Ejecutando aprendizaje ahora...")
    try:
        from agents.weekly_learner import analizar_y_aprender
        resultado = analizar_y_aprender()
        responder(chat_id,
            f"✅ <b>Aprendizaje completado</b>\n\n"
            f"<code>{resultado.get('resumen','Sin resumen')}</code>"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error aprendizaje: {e}")

def handle_idea(chat_id, tema=""):
    msg = f"⏳ <b>Generando idea sobre '{tema}'...</b>\nEspera 60-120s ☕" if tema else "⏳ <b>Generando idea...</b>\nEspera 60-120s ☕"
    responder(chat_id, msg)
    try:
        env = os.environ.copy()
        if tema:
            env["IDEA_TOPIC"] = tema
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, timeout=240, env=env
        )
        salida  = resultado.stdout.decode("utf-8", errors="replace")
        errores = resultado.stderr.decode("utf-8", errors="replace")

        nombre, score, url, herramienta, hipotesis, landing_url, tagline, problema, monetiz, veredicto_critico, recomendacion = extraer_resultado_batch(salida)

        if nombre:
            try:    score_num = float(str(score).split("/")[0].strip())
            except: score_num = 0
            emoji = "💎" if score_num >= 90 else "⭐" if score_num >= 75 else "💡"

            msg = (
                f"{emoji} <b>{nombre}</b>  —  {score}/100\n"
                f"<i>{tagline}</i>\n\n"
            )
            if problema:
                msg += f"❗ <b>Problema:</b> {problema[:120]}\n\n"
            if herramienta:
                msg += f"🤖 <b>IA clave:</b> {herramienta[:100]}\n"
            if monetiz:
                msg += f"💰 <b>Semana 1:</b> {monetiz[:120]}\n"
            if hipotesis:
                msg += f"\n🧪 <b>Test 48h:</b> {hipotesis[:150]}\n"
            if veredicto_critico:
                rec_emoji = "✅" if recomendacion == "invertir" else "⚠️" if recomendacion == "pivotar" else "❌"
                msg += f"\n{rec_emoji} <b>Veredicto YC:</b> {veredicto_critico[:120]}\n"
            if url:
                msg += f"\n📋 <a href='{url}'>Ver informe completo en Notion</a>"
            if landing_url:
                msg += f"\n🌐 <a href='{landing_url}'>Landing page</a>"

            responder(chat_id, msg, reply_markup=_teclado_feedback(nombre))
        else:
            error_lines = [
                l.strip() for l in (salida + errores).split("\n")
                if any(p in l for p in ["❌","Error","error","Traceback","Exception","SyntaxError","IndentationError"])
            ]
            responder(chat_id,
                f"❌ <b>Error generando idea</b>\n\n"
                f"<code>{chr(10).join(error_lines[:6])}</code>\n\nUsa /debug."
            )
    except subprocess.TimeoutExpired:
        responder(chat_id, "⏰ Timeout (>240s) — se reintentara automaticamente en 30 min.")
    except Exception as e:
        responder(chat_id, f"❌ Error inesperado: {e}")

def handle_debug(chat_id, _=""):
    responder(chat_id, "🔍 Ejecutando diagnostico — espera 60s...")
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, timeout=180, env=os.environ.copy()
        )
        salida  = resultado.stdout.decode("utf-8", errors="replace")
        errores = resultado.stderr.decode("utf-8", errors="replace")
        codigo  = resultado.returncode

        nombre, score, url, herramienta, hipotesis, landing_url, tagline, problema, monetiz, veredicto_critico, recomendacion = extraer_resultado_batch(salida)

        resumen = (
            f"🐛 <b>Debug run_batch.py</b>\n"
            f"Codigo salida: {'✅ OK' if codigo==0 else f'❌ {codigo}'}\n"
            f"Idea: {nombre or '❌ No encontrada'}\n"
            f"Score: {score or '❌'}\n"
            f"Veredicto: {veredicto_critico[:80] if veredicto_critico else '❌'}\n"
            f"Notion: {'✅ '+url[:50] if url else '❌'}\n\n"
            f"<b>Output completo:</b>\n<code>{salida[-1500:]}</code>"
        )
        if errores.strip():
            resumen += f"\n\n<b>Errores:</b>\n<code>{errores[-400:]}</code>"
        responder(chat_id, resumen)
    except subprocess.TimeoutExpired:
        responder(chat_id, "⏰ Timeout — revisa Railway Deploy Logs.")
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_cola(chat_id, _=""):
    try:
        ruta = "data/cola_pendientes.csv"
        if not os.path.exists(ruta):
            responder(chat_id, "✅ Cola vacia — todo sincronizado.")
            return
        with open(ruta, newline="", encoding="utf-8") as f:
            pendientes = list(csv.DictReader(f))
        if not pendientes:
            responder(chat_id, "✅ Cola vacia — todo sincronizado.")
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
            responder(chat_id, "📭 Sin ideas. Usa /idea para generar.")
            return
        def score_ej(idea):
            s = idea.get("scores", {})
            if not isinstance(s, dict): s = {}
            return s.get("ejecutabilidad",0)*0.40 + s.get("generador",0)*0.35 + s.get("timing",0)*0.25
        top   = sorted(ideas, key=score_ej, reverse=True)[:5]
        texto = "🚀 <b>TOP 5 MAS EJECUTABLES AHORA</b>\n\n"
        for i, idea in enumerate(top, 1):
            s   = idea.get("scores", {})
            if not isinstance(s, dict): s = {}
            ia  = f"\n   🤖 {idea.get('herramienta_ia','')[:60]}" if idea.get("herramienta_ia") else ""
            tgl = idea.get("tagline","")[:70]
            texto += (
                f"<b>{i}. {idea.get('nombre','?')}</b>\n"
                f"   <i>{tgl}</i>\n"
                f"   ⚡ Ejecutabilidad: {s.get('ejecutabilidad',0)}/100\n"
                f"   💰 Revenue rapido: {s.get('generador',0)}/100\n"
                f"   ⏰ Timing: {s.get('timing',0)}/100\n"
                f"   📊 Score total: {idea.get('score_total',0)}/100"
                f"{ia}\n\n"
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
            if idea.get("nombre","").lower() == nb:
                return idea
        for idea in reversed(todas):
            if nb in idea.get("nombre","").lower():
                return idea
    except: pass
    return None

def handle_ejecutar(chat_id, nombre_arg=""):
    try:
        idea_target = None
        if nombre_arg:
            idea_target = _buscar_idea_por_nombre(nombre_arg)
            if not idea_target:
                responder(chat_id, f"❌ No encontre '<b>{nombre_arg}</b>'.\nUsa /top o /ranking.")
                return
        else:
            from agents.knowledge_base import _cargar
            kb    = _cargar()
            ideas = kb.get("ideas", [])
            if not ideas:
                responder(chat_id, "📭 Sin ideas. Usa /idea primero.")
                return
            def score_ej(idea):
                s = idea.get("scores", {})
                if not isinstance(s, dict): s = {}
                return s.get("ejecutabilidad",0)*0.40 + s.get("generador",0)*0.35 + s.get("timing",0)*0.25
            top1        = sorted(ideas, key=score_ej, reverse=True)[0]
            idea_target = _buscar_idea_por_nombre(top1.get("nombre",""))

        if not idea_target:
            responder(chat_id, "⚠️ Datos no encontrados. Genera nuevas ideas.")
            return

        nombre_final = idea_target.get("nombre","?")
        pm           = idea_target.get("prompt_mvp", {})
        if not isinstance(pm, dict): pm = {}
        scores       = idea_target.get("scores",{})
        score        = scores.get("score_total","?") if isinstance(scores, dict) else "?"

        # Meta del prompt
        meta   = pm.get("meta", {}) if isinstance(pm.get("meta"), dict) else {}
        ia_rec = meta.get("ia_recomendada", pm.get("ia_recomendada","Claude 3.5 Sonnet en Cursor IDE"))
        stack  = meta.get("stack_completo", "Next.js + Supabase + Vercel + Stripe")

        prompt_json = json.dumps(pm, ensure_ascii=False, indent=2)
        if not prompt_json or prompt_json == "{}":
            responder(chat_id, f"⚠️ <b>{nombre_final}</b> no tiene prompt MVP.\nUsa /idea para generar nuevas.")
            return

        responder(chat_id,
            f"🛠️ <b>EJECUTA HOY: {nombre_final}</b>\n"
            f"📊 Score: {score}/100\n"
            f"🤖 IA: {ia_rec}\n"
            f"📦 Stack: {stack}\n\n"
            f"📋 <b>Copia en Cursor o Claude:</b>\n\n"
            f"<code>{prompt_json[:3200]}</code>"
        )
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_buscar(chat_id, palabra=""):
    if not palabra:
        responder(chat_id, "❓ Ejemplo: /buscar fintech")
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
            or pl in i.get("problema","").lower()
        ]
        if not encontradas:
            responder(chat_id, f"🔍 No encontre ideas con '<b>{palabra}</b>'.")
            return
        texto = f"🔍 <b>Ideas con '{palabra}'</b>\n\n"
        for i, idea in enumerate(encontradas[-5:], 1):
            s   = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            ia  = f"\n   🤖 {idea.get('herramienta_ia_clave','')[:60]}" if idea.get("herramienta_ia_clave") else ""
            tgl = idea.get("tagline","")[:70]
            texto += (
                f"<b>{i}. {idea.get('nombre','?')}</b>\n"
                f"   <i>{tgl}</i>\n"
                f"   📊 {s}/100{ia}\n\n"
            )
        texto += "Usa /ejecutar [nombre] para el prompt MVP."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def handle_tendencias(chat_id, _=""):
    try:
        from agents.trend_scout import actualizar_tendencias
        responder(chat_id, "🔄 Consultando 5 fuentes...")
        tendencias = actualizar_tendencias()
        if not tendencias:
            responder(chat_id, "⚠️ No hay tendencias disponibles.")
            return
        texto = "🌐 <b>TENDENCIAS TECH AHORA</b>\n(HN + GitHub + Reddit + PH + IA curada)\n\n"
        for i, t in enumerate(tendencias[:20], 1):
            texto += f"{i}. {t[:120]}\n"
        texto += "\n💡 La proxima idea usara estas señales."
        responder(chat_id, texto)
    except Exception as e:
        responder(chat_id, f"❌ Error: {e}")

def procesar_lenguaje_natural(chat_id, texto: str):
    t = texto.lower()
    if any(p in t for p in ["genera","crea","nueva idea","idea sobre","idea de","dame una idea"]):
        for kw in ["sobre ","de ","acerca de "]:
            if kw in t:
                tema = t.split(kw)[-1].strip()
                if len(tema) > 2:
                    handle_idea(chat_id, tema)
                    return
        handle_idea(chat_id, "")
        return
    if any(p in t for p in ["estado","como va","activo","funciona"]):
        handle_status(chat_id); return
    if any(p in t for p in ["top","mejores","mejor idea"]):
        handle_top(chat_id); return
    if any(p in t for p in ["ranking","ejecutable","cual ejecuto"]):
        handle_ranking(chat_id); return
    if any(p in t for p in ["ejecuta","construye","prompt de","como hacer"]):
        partes = texto.split()
        handle_ejecutar(chat_id, " ".join(partes[1:]) if len(partes) > 1 else "")
        return
    if any(p in t for p in ["busca","buscar","encuentra"]):
        partes = texto.split()
        if len(partes) > 1:
            handle_buscar(chat_id, " ".join(partes[1:]))
        return
    if any(p in t for p in ["tendencia","trend","novedades"]):
        handle_tendencias(chat_id); return
    if any(p in t for p in ["stats","estadistica","cuantas"]):
        handle_stats(chat_id); return
    if any(p in t for p in ["aprende","aprendizaje","mejora"]):
        handle_aprender(chat_id); return
    if any(p in t for p in ["debug","error","fallo","problema"]):
        handle_debug(chat_id); return
    responder(chat_id,
        "🤖 No entendi. Prueba:\n"
        "• \"genera una idea de [tema]\"\n"
        "• \"ejecuta [nombre]\"\n"
        "• \"ranking\"\n"
        "• \"busca fintech\"\n"
        "O usa /start."
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
    "/aprender":   handle_aprender,
    "/debug":      handle_debug,
}

def procesar_callback(update: dict):
    try:
        cq      = update.get("callback_query", {})
        cq_id   = cq.get("id","")
        chat_id = cq.get("message",{}).get("chat",{}).get("id","")
        data    = cq.get("data","")
        try:
            requests.post(f"{_base()}/answerCallbackQuery",
                          json={"callback_query_id": cq_id}, timeout=5)
        except: pass
        if not data or ":" not in data:
            return
        accion, nombre = data.split(":", 1)
        nombre = nombre.strip()
        from agents.knowledge_base import registrar_feedback
        registrar_feedback(nombre, accion)
        if accion == "like":
            log(f"👍 LIKE: {nombre}")
            responder(chat_id, f"👍 <b>{nombre}</b> marcada como buena idea.\nEl sistema la priorizara en proximas generaciones.")
        elif accion == "dislike":
            log(f"👎 DISLIKE: {nombre}")
            responder(chat_id, f"👎 <b>{nombre}</b> descartada.\nEl sistema evitara este tipo de ideas.")
    except Exception as e:
        log(f"❌ Error callback: {e}")

def iniciar_bot():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN","")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID","")
    if not TELEGRAM_TOKEN:
        log("⚠️ TELEGRAM_BOT_TOKEN no configurado — bot desactivado")
        return
    try:
        requests.get(f"{_base()}/deleteWebhook?drop_pending_updates=true", timeout=10)
        log("🧹 Webhook eliminado")
    except: pass
    log("🤖 ✅ Bot v5 iniciado — polling activo")
    offset = 0
    while True:
        try:
            resp = requests.get(
                f"{_base()}/getUpdates",
                params={"timeout":30,"offset":offset,"allowed_updates":["message","callback_query"]},
                timeout=40
            )
            if resp.status_code != 200:
                time.sleep(5)
                continue
            updates = resp.json().get("result",[])
            for update in updates:
                offset = update["update_id"] + 1
                try:
                    if "callback_query" in update:
                        threading.Thread(target=procesar_callback, args=(update,), daemon=True).start()
                        continue
                    msg     = update.get("message",{})
                    text    = msg.get("text","").strip()
                    chat_id = msg.get("chat",{}).get("id")
                    if not text or not chat_id:
                        continue
                    log(f"📩 '{text[:50]}' de {chat_id}")
                    if text.startswith("/"):
                        partes = text.split(maxsplit=1)
                        cmd    = partes[0].lower().split("@")[0]
                        arg    = partes[1].strip() if len(partes) > 1 else ""
                        fn     = COMANDOS.get(cmd)
                        if fn:
                            threading.Thread(target=fn, args=(chat_id,arg), daemon=True).start()
                        else:
                            responder(chat_id, "❓ Comando no reconocido. /start")
                    else:
                        threading.Thread(
                            target=procesar_lenguaje_natural, args=(chat_id,text), daemon=True
                        ).start()
                except Exception as e:
                    log(f"❌ Error procesando update: {e}")
        except requests.exceptions.Timeout:
            pass
        except Exception as e:
            log(f"❌ Bot loop error: {e}")
            time.sleep(10)

def ejecutar_script(nombre):
    log(f"▶️  {nombre}...")
    try:
        resultado = subprocess.run([sys.executable, nombre], capture_output=True, timeout=240)
        salida    = resultado.stdout.decode("utf-8", errors="replace").strip()
        errores   = resultado.stderr.decode("utf-8", errors="replace").strip()
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
        log(f"❌ Error {nombre}: {e}")
        return False, str(e)

def hc_groq():
    try:
        import groq
        client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"), timeout=10)
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role":"user","content":"ok"}],
            max_tokens=3, temperature=0
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)[:200]

def hc_notion():
    try:
        token = os.environ.get("NOTION_TOKEN","")
        db_id = os.environ.get("NOTION_DATABASE_ID","308313aca133800981cfc48f32c52146")
        resp  = requests.get(
            f"https://api.notion.com/v1/databases/{db_id}",
            headers={"Authorization":f"Bearer {token}","Notion-Version":"2022-06-28"},
            timeout=10
        )
        return (True,"OK") if resp.status_code==200 else (False,f"HTTP {resp.status_code}")
    except Exception as e:
        return False, str(e)[:200]

def ejecutar_health_check():
    log("🏥 Health check...")
    checks = {"Groq": hc_groq(), "Notion": hc_notion()}
    fallos = [(s,m) for s,(ok,m) in checks.items() if not ok]
    if fallos:
        lineas = "\n".join(f"❌ <b>{s}</b>: {m}" for s,m in fallos)
        enviar_telegram(f"🚨 <b>HEALTH CHECK FALLO</b>\n{lineas}")
    else:
        log("✅ Health check OK")

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
        log(f"📋 Cola: {len(pendientes)} pendiente(s)")
        eliminados = []
        for fila in pendientes:
            nombre   = fila.get("nombre_idea","?")
            intentos = int(fila.get("intentos",1))
            ts       = fila.get("timestamp","")
            if intentos > 3:
                eliminados.append(ts)
                continue
            try:
                datos = json.loads(fila.get("datos_json","{}"))
                url   = sync_idea_to_notion(datos)
                if url:
                    log(f"✅ Reintento OK: {nombre}")
                    eliminados.append(ts)
                else:
                    fila["intentos"] = str(intentos+1)
            except Exception as e:
                log(f"❌ Reintento fallido {nombre}: {e}")
                fila["intentos"] = str(intentos+1)
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
    log("🧠 Generando nueva idea automatica...")
    exito, salida = ejecutar_script("run_batch.py")
    if exito:
        nombre, score, url, herramienta, hipotesis, landing_url, tagline, problema, monetiz, veredicto_critico, recomendacion = extraer_resultado_batch(salida)
        if nombre:
            try:    score_num = float(str(score).split("/")[0].strip())
            except: score_num = 0
            emoji = "💎" if score_num >= 90 else "⭐" if score_num >= 75 else "💡"

            msg = (
                f"{emoji} <b>{nombre}</b>  —  {score}/100\n"
                f"<i>{tagline}</i>\n\n"
            )
            if problema:
                msg += f"❗ <b>Problema:</b> {problema[:120]}\n\n"
            if herramienta:
                msg += f"🤖 <b>IA clave:</b> {herramienta[:100]}\n"
            if monetiz:
                msg += f"💰 <b>Semana 1:</b> {monetiz[:120]}\n"
            if hipotesis:
                msg += f"\n🧪 <b>Test 48h:</b> {hipotesis[:150]}\n"
            if veredicto_critico:
                rec_emoji = "✅" if recomendacion == "invertir" else "⚠️" if recomendacion == "pivotar" else "❌"
                msg += f"\n{rec_emoji} <b>Veredicto YC:</b> {veredicto_critico[:120]}\n"
            if url:
                msg += f"\n📋 <a href='{url}'>Ver informe completo en Notion</a>"
            if landing_url:
                msg += f"\n🌐 <a href='{landing_url}'>Landing page</a>"

            enviar_telegram(msg, reply_markup=_teclado_feedback(nombre))
            log(f"✅ {nombre} | {score} | {url or 'sin URL'}")
    else:
        log("⚠️ run_batch.py fallo — reintento en 30 min")
    return exito

def ejecutar_aprendizaje_diario():
    try:
        from agents.weekly_learner import analizar_y_aprender
        resultado = analizar_y_aprender()
        enviar_telegram(
            f"🧠 <b>Aprendizaje diario completado</b>\n\n"
            f"<code>{resultado.get('resumen','')}</code>"
        )
        log("✅ Aprendizaje diario ejecutado")
    except Exception as e:
        log(f"⚠️ Aprendizaje diario: {e}")

def main():
    global TELEGRAM_TOKEN, TELEGRAM_CHAT_ID
    TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN","")
    TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID","")

    log("🚀 monitor_nocturno.py v5 iniciado")
    migrar_kb_si_necesario()

    enviar_telegram(
        "🟢 <b>Monitor ValidationIdea v5 arrancado</b>\n\n"
        "✅ Ideas automaticas cada 30 minutos\n"
        "✅ 5 fuentes: HN + GitHub + Reddit + PH + IA\n"
        "✅ Scoring doble: IA generadora + IA critica YC\n"
        "✅ Anti-duplicados semantico activo\n"
        "✅ Feedback 👍👎 con aprendizaje inmediato\n"
        "✅ Aprendizaje automatico DIARIO a las 08:00\n"
        "✅ Link Notion en cada notificacion\n\n"
        "📱 /start para ver comandos"
    )

    bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
    bot_thread.start()
    log("🤖 Bot arrancado en hilo paralelo")

    ahora_utc        = datetime.now(timezone.utc)
    ultimo_batch     = ahora_utc - timedelta(minutes=31)
    ultimo_informe   = ahora_utc - timedelta(minutes=6)
    ultimo_health    = ahora_utc - timedelta(hours=1, minutes=1)
    ultima_tendencia = ahora_utc - timedelta(hours=3)
    dia_mant         = -1

    while True:
        try:
            ahora_utc   = datetime.now(timezone.utc)
            ahora_local = datetime.now(ZONA)
            hora        = ahora_local.hour
            dia         = ahora_local.day

            # Ideas automaticas cada 30 min
            if (ahora_utc - ultimo_batch).total_seconds() >= 30 * 60:
                generar_nueva_idea()
                ultimo_batch = ahora_utc

            # Monitor + cola cada 5 min
            if (ahora_utc - ultimo_informe).total_seconds() >= 5 * 60:
                try: ejecutar_script("run_monitor.py")
                except: pass
                procesar_cola_csv()
                ultimo_informe = ahora_utc

            # Health check cada hora
            if (ahora_utc - ultimo_health).total_seconds() >= 60 * 60:
                ejecutar_health_check()
                ultimo_health = ahora_utc

            # Tendencias cada 3 horas
            if (ahora_utc - ultima_tendencia).total_seconds() >= 3 * 60 * 60:
                try:
                    from agents.trend_scout import actualizar_tendencias
                    actualizar_tendencias()
                    log("🌐 Tendencias actualizadas")
                except Exception as e:
                    log(f"⚠️ Tendencias: {e}")
                ultima_tendencia = ahora_utc

            # Aprendizaje DIARIO a las 08:00
            if hora == 8 and dia != dia_mant:
                ejecutar_aprendizaje_diario()
                dia_mant = dia

        except Exception as e:
            log(f"❌ Error loop principal: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()

# aqui finaliza el codigo de monitor_nocturno.py
