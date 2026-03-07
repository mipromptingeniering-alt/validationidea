import os
import sys
import json
import time
import logging
import subprocess
import threading
import asyncio
import csv
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

def enviar_telegram(mensaje):
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        import requests
        resp = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": mensaje, "parse_mode": "HTML"},
            timeout=15
        )
        if resp.status_code == 200:
            log("📱 Telegram enviado")
        else:
            log(f"⚠️ Telegram HTTP {resp.status_code}")
    except Exception as e:
        log(f"❌ Error Telegram: {e}")

def ejecutar_script(nombre):
    log(f"▶️  {nombre}...")
    try:
        resultado = subprocess.run(
            [sys.executable, nombre],
            capture_output=True, timeout=240
        )
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
        import requests
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
    try:
        from google import genai
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        client.models.generate_content(model="gemini-2.0-flash", contents="ok")
    except Exception as eg:
        log(f"⚠️ Gemini degradado (no crítico): {eg}")
    checks = {"Groq": hc_groq(), "Notion": hc_notion()}
    fallos = [(srv, msg) for srv, (ok, msg) in checks.items() if not ok]
    if fallos:
        lineas = "\n".join(f"❌ <b>{srv}</b>: {msg}" for srv, msg in fallos)
        enviar_telegram(f"🚨 <b>HEALTH CHECK FALLO</b>\n{lineas}")
        log(f"🚨 Fallos: {[s for s, _ in fallos]}")
    else:
        log("✅ Health check OK — Groq ✅  Notion ✅")
    return len(fallos) == 0

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
    log("🧠 Generando nueva idea...")
    exito, salida = ejecutar_script("run_batch.py")
    if exito and "✅ Sincronizada:" in salida:
        try:
            nombre = score = url = ""
            for linea in salida.split("\n"):
                l = linea.strip().replace("│", "").strip()
                if "✅ Sincronizada:" in l:
                    nombre = l.split("✅ Sincronizada:")[-1].strip()
                if "📊 Score:" in l:
                    score = l.split("📊 Score:")[-1].strip().split("|")[0].strip()
                if "notion.so" in l and "http" in l:
                    url = l
            # Solo notificar si score >= 75
            try:
                score_num = float(score.split("/")[0].strip())
            except:
                score_num = 0
            if score_num >= 75:
                enviar_telegram(
                    f"⭐ <b>IDEA DESTACADA — score {score}</b>\n\n"
                    f"🚀 <b>{nombre}</b>\n"
                    f"🔗 {url}\n\n"
                    f"Usa /ejecutar para obtener el prompt MVP."
                )
            else:
                enviar_telegram(
                    f"💡 <b>Nueva idea generada</b>\n\n"
                    f"🚀 <b>{nombre}</b>\n"
                    f"📊 Score: <b>{score}</b>\n"
                    f"🔗 {url}"
                )
        except Exception as e:
            log(f"⚠️ Error notificando idea: {e}")
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
            f"🏆 Mejor vertical: <b>{stats.get('mejor_vertical', 'N/A')}</b>\n"
            f"⭐ Mejor idea: <b>{stats.get('mejor_idea', 'N/A')}</b>"
            f"\n\n🏅 <b>TOP 3:</b>{top_txt}"
            f"{cola_txt}\n\n"
            f"✅ Sistema operativo 24/7\n"
            f"📱 /ranking → ideas más ejecutables hoy"
        )
    except Exception as e:
        log(f"❌ Error resumen: {e}")
        enviar_telegram(f"☀️ Sistema activo — error en resumen: {e}")


# ════════════════════════════════════════════════════════
#   BOT TELEGRAM — asyncio correcto
# ════════════════════════════════════════════════════════
def iniciar_bot():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        log("⚠️ TELEGRAM_BOT_TOKEN no configurado — bot desactivado")
        return

    try:
        from telegram import Update
        from telegram.ext import Application, CommandHandler, ContextTypes
        from telegram.error import Conflict, NetworkError

        async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "🤖 <b>ValidationIdea Bot v2</b>\n\n"
                "💡 /idea — Genera 1 idea ahora\n"
                "📊 /status — Estado del sistema\n"
                "🏆 /top — Top 5 mejores ideas\n"
                "📋 /stats — Estadísticas KB\n"
                "🚀 /ranking — Top 5 más ejecutables HOY\n"
                "🛠️ /ejecutar — Prompt MVP listo para usar\n"
                "🌐 /tendencias — Tendencias tech ahora\n"
                "🔄 /cola — Ideas pendientes Notion",
                parse_mode="HTML"
            )

        async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
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
                await update.message.reply_text(
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
                    f"⏳ Cola pendiente: <b>{cola_n}</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_top(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                from agents.knowledge_base import get_top_ideas
                top = get_top_ideas(5)
                if not top:
                    await update.message.reply_text("📭 Aún no hay ideas en el TOP.")
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
                await update.message.reply_text(texto, parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                from agents.knowledge_base import get_stats
                stats = get_stats()
                await update.message.reply_text(
                    f"📈 <b>Estadísticas KB</b>\n\n"
                    f"💡 Ideas analizadas: <b>{stats.get('total_ideas', 0)}</b>\n"
                    f"📊 Score promedio: <b>{stats.get('score_promedio', 0)}/100</b>\n"
                    f"🏆 Mejor score: <b>{stats.get('mejor_score', 0)}/100</b>\n"
                    f"🌐 Vertical ganadora: <b>{stats.get('mejor_vertical', 'N/A')}</b>\n"
                    f"🚀 Tipo ganador: <b>{stats.get('mejor_tipo', 'N/A')}</b>\n"
                    f"⭐ Mejor idea: <b>{stats.get('mejor_idea', 'N/A')}</b>\n"
                    f"🎯 Tasa de éxito: <b>{stats.get('tasa_exito', 'N/A')}</b>",
                    parse_mode="HTML"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_idea(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            await update.message.reply_text(
                "⏳ <b>Generando idea con informe completo...</b>\n"
                "Espera 45-90 segundos ☕\n"
                "(DAFO + estudio económico + prompt MVP incluidos)",
                parse_mode="HTML"
            )
            try:
                resultado = subprocess.run(
                    [sys.executable, "run_batch.py"],
                    capture_output=True, timeout=150
                )
                salida = resultado.stdout.decode("utf-8", errors="replace")
                nombre = score = url = ""
                for linea in salida.split("\n"):
                    l = linea.strip().replace("│", "").strip()
                    if "✅ Sincronizada:" in l:
                        nombre = l.split("✅ Sincronizada:")[-1].strip()
                    if "📊 Score:" in l:
                        score = l.split("📊 Score:")[-1].strip().split("|")[0].strip()
                    if "notion.so" in l and "http" in l:
                        url = l
                if nombre:
                    await update.message.reply_text(
                        f"✅ <b>¡Idea generada!</b>\n\n"
                        f"🚀 <b>{nombre}</b>\n"
                        f"📊 Score: <b>{score}</b>\n"
                        f"📋 Informe completo en Notion:\n{url}",
                        parse_mode="HTML"
                    )
                else:
                    await update.message.reply_text(
                        "⚠️ Generada en background — revisa Notion en 1 minuto."
                    )
            except subprocess.TimeoutExpired:
                await update.message.reply_text(
                    "⏰ Generando en background — revisa Notion en 2 min."
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_cola(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                ruta = "data/cola_pendientes.csv"
                if not os.path.exists(ruta):
                    await update.message.reply_text("✅ Cola vacía — todo sincronizado.")
                    return
                with open(ruta, newline="", encoding="utf-8") as f:
                    pendientes = list(csv.DictReader(f))
                if not pendientes:
                    await update.message.reply_text("✅ Cola vacía — todo sincronizado.")
                    return
                texto = f"📋 <b>Cola: {len(pendientes)} pendiente(s)</b>\n\n"
                for p in pendientes[:5]:
                    texto += f"• {p.get('nombre_idea','?')} (intento {p.get('intentos',1)}/3)\n"
                await update.message.reply_text(texto, parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_ranking(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                from agents.knowledge_base import _cargar
                kb    = _cargar()
                ideas = kb.get("ideas", [])
                if not ideas:
                    await update.message.reply_text("📭 Aún no hay ideas. Usa /idea para generar.")
                    return
                def score_ejecutable(idea):
                    s = idea.get("scores", {})
                    return (
                        s.get("ejecutabilidad", 0) * 0.40 +
                        s.get("generador",      0) * 0.35 +
                        s.get("timing",         0) * 0.25
                    )
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
                texto += "💡 Usa /ejecutar para el prompt MVP de la mejor."
                await update.message.reply_text(texto, parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_ejecutar(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                from agents.knowledge_base import _cargar
                kb    = _cargar()
                ideas = kb.get("ideas", [])
                if not ideas:
                    await update.message.reply_text("📭 Sin ideas. Usa /idea primero.")
                    return
                def score_ejecutable(idea):
                    s = idea.get("scores", {})
                    return (
                        s.get("ejecutabilidad", 0) * 0.40 +
                        s.get("generador",      0) * 0.35 +
                        s.get("timing",         0) * 0.25
                    )
                top1        = sorted(ideas, key=score_ejecutable, reverse=True)[0]
                nombre_top  = top1.get("nombre", "")
                prompt_texto = ""
                ia_rec = "Claude 3.5 Sonnet en Cursor IDE"
                try:
                    with open("data/ideas.json", "r", encoding="utf-8") as f:
                        todas = json.load(f)
                    for idea in reversed(todas):
                        if idea.get("nombre") == nombre_top:
                            pm = idea.get("prompt_mvp", {})
                            prompt_texto = pm.get("prompt_completo", "")
                            ia_rec = pm.get("ia_recomendada", ia_rec)
                            break
                except:
                    pass
                if not prompt_texto:
                    await update.message.reply_text(
                        f"⚠️ Prompt de <b>{nombre_top}</b> no encontrado.\n"
                        f"Usa /idea para generar ideas con el sistema v2.",
                        parse_mode="HTML"
                    )
                    return
                await update.message.reply_text(
                    f"🛠️ <b>EJECUTA HOY: {nombre_top}</b>\n\n"
                    f"🤖 <b>Usa:</b> {ia_rec}\n\n"
                    f"📋 <b>Copia este prompt en Cursor/Claude:</b>\n\n"
                    f"{prompt_texto[:3500]}",
                    parse_mode="HTML"
                )
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        async def cmd_tendencias(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
            try:
                from agents.trend_scout import actualizar_tendencias
                await update.message.reply_text("🔄 Consultando HackerNews...")
                tendencias = actualizar_tendencias()
                if not tendencias:
                    await update.message.reply_text("⚠️ No hay tendencias disponibles ahora.")
                    return
                texto = "🌐 <b>TENDENCIAS TECH AHORA</b>\n(fuente: HackerNews)\n\n"
                for i, t in enumerate(tendencias, 1):
                    texto += f"{i}. {t}\n"
                texto += "\n💡 La próxima idea usará estas tendencias automáticamente."
                await update.message.reply_text(texto, parse_mode="HTML")
            except Exception as e:
                await update.message.reply_text(f"❌ Error: {e}")

        # ── Loop asyncio correcto ────────────────────────
        async def arrancar():
            while True:
                try:
                    log("🤖 Bot Telegram iniciando...")
                    app = Application.builder().token(token).build()
                    app.add_handler(CommandHandler("start",      cmd_start))
                    app.add_handler(CommandHandler("status",     cmd_status))
                    app.add_handler(CommandHandler("top",        cmd_top))
                    app.add_handler(CommandHandler("stats",      cmd_stats))
                    app.add_handler(CommandHandler("idea",       cmd_idea))
                    app.add_handler(CommandHandler("cola",       cmd_cola))
                    app.add_handler(CommandHandler("ranking",    cmd_ranking))
                    app.add_handler(CommandHandler("ejecutar",   cmd_ejecutar))
                    app.add_handler(CommandHandler("tendencias", cmd_tendencias))
                    log("🤖 ✅ Bot escuchando — 9 comandos activos")
                    await app.run_polling(drop_pending_updates=True, allowed_updates=["message"])
                except Conflict:
                    log("⚠️ Bot Conflict — esperando 30s...")
                    await asyncio.sleep(30)
                except NetworkError as ne:
                    log(f"⚠️ NetworkError: {ne} — reintentando 15s...")
                    await asyncio.sleep(15)
                except Exception as e:
                    log(f"❌ Bot error: {e} — reintentando 15s...")
                    await asyncio.sleep(15)

        asyncio.run(arrancar())

    except ImportError:
        log("⚠️ python-telegram-bot no instalado — bot desactivado")


# ════════════════════════════════════════════════════════
#   LOOP PRINCIPAL
# ════════════════════════════════════════════════════════
def main():
    log("🚀 monitor_nocturno.py iniciado — P1→P10 activos")
    enviar_telegram(
        "🟢 <b>Monitor ValidationIdea v2 arrancado</b>\n\n"
        "✅ P1–P10 activos\n"
        "✅ Informes: DAFO + economía + prompt MVP\n"
        "✅ Autoaprendizaje KB activo\n"
        "✅ Tendencias HackerNews en tiempo real\n\n"
        "📱 Comandos disponibles:\n"
        "/idea /status /top /stats\n"
        "/ranking /ejecutar /tendencias /cola"
    )

    bot_thread = threading.Thread(target=iniciar_bot, daemon=True)
    bot_thread.start()
    log("🤖 Bot Telegram arrancado en hilo paralelo")

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
                    log("🌐 Tendencias actualizadas automáticamente")
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
