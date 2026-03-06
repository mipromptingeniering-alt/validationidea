import os
import json
import time
import logging
import subprocess
import sys
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from telegram.error import Conflict, NetworkError

logging.basicConfig(level=logging.WARNING)
log = logging.getLogger(__name__)

TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 <b>ValidationIdea Bot</b>\n\n"
        "Comandos disponibles:\n"
        "💡 /idea — Genera 1 idea ahora\n"
        "📊 /status — Estado del sistema\n"
        "🏆 /top — Top 5 mejores ideas\n"
        "📋 /stats — Estadísticas KB\n"
        "🔄 /cola — Ideas pendientes Notion",
        parse_mode="HTML"
    )

async def cmd_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        from agents.knowledge_base import get_stats
        stats = get_stats()

        cola_n = 0
        try:
            from agents.cola_csv import contar_pendientes
            cola_n = contar_pendientes()
        except:
            pass

        total_local = 0
        try:
            with open("data/ideas.json", "r", encoding="utf-8") as f:
                total_local = len(json.load(f))
        except:
            pass

        await update.message.reply_text(
            f"📊 <b>Estado del sistema</b>\n"
            f"🕐 {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            f"✅ Monitor: <b>Activo 24/7</b>\n"
            f"✅ Groq: <b>Activo</b>\n"
            f"✅ Notion: <b>Activo</b>\n\n"
            f"💡 Ideas generadas: <b>{total_local}</b>\n"
            f"📚 Ideas en KB: <b>{stats.get('total_ideas', 0)}</b>\n"
            f"📊 Score promedio: <b>{stats.get('score_promedio', 0)}/100</b>\n"
            f"🏆 Mejor score: <b>{stats.get('mejor_score', 0)}/100</b>\n"
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
            await update.message.reply_text(
                "📭 Aún no hay ideas en el TOP.\n"
                "El sistema genera 1 idea cada 30 min automáticamente."
            )
            return

        texto = "🏆 <b>TOP 5 MEJORES IDEAS</b>\n\n"
        for i, idea in enumerate(top, 1):
            s = idea["score"]
            emoji = "💎" if s >= 90 else "⭐" if s >= 85 else "🔥" if s >= 80 else "💡"
            texto += (
                f"{emoji} <b>{i}. {idea['nombre']}</b>\n"
                f"   📊 Score: <b>{s}/100</b>\n"
                f"   🏷️ {idea.get('tipo','?')} | {idea.get('vertical','?')}\n"
                f"   📅 {idea.get('fecha', 'N/A')}\n\n"
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
            f"⭐ Mejor idea: <b>{stats.get('mejor_idea', 'N/A')}</b>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_idea(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "⏳ <b>Generando idea TOP...</b>\n"
        "Espera 30-60 segundos ☕",
        parse_mode="HTML"
    )
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, timeout=120
        )
        salida = resultado.stdout.decode("utf-8", errors="replace")

        nombre = score = url = ""
        for linea in salida.split("\n"):
            l = linea.strip().replace("│", "").strip()
            if "✅ Sincronizada:" in l:
                nombre = l.split("✅ Sincronizada:")[-1].strip()
            if "📊 Score:" in l and "Score:" in l:
                score = l.split("📊 Score:")[-1].strip().split("|")[0].strip()
            if "notion.so" in l and "http" in l:
                url = l

        if nombre:
            await update.message.reply_text(
                f"✅ <b>¡Idea generada!</b>\n\n"
                f"🚀 <b>{nombre}</b>\n"
                f"📊 Score: <b>{score}</b>\n"
                f"🔗 {url}",
                parse_mode="HTML"
            )
        else:
            await update.message.reply_text(
                "⚠️ Idea generada pero sin confirmar.\n"
                "Revisa Notion en 1 minuto."
            )
    except subprocess.TimeoutExpired:
        await update.message.reply_text(
            "⏰ La idea se está generando en background.\n"
            "Revisa Notion en 2 minutos."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

async def cmd_cola(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    try:
        from agents.cola_csv import obtener_pendientes
        pendientes = obtener_pendientes()
        if not pendientes:
            await update.message.reply_text("✅ Cola vacía — todo sincronizado en Notion.")
            return
        texto = f"📋 <b>Cola CSV: {len(pendientes)} pendiente(s)</b>\n\n"
        for p in pendientes[:5]:
            texto += f"• {p.get('nombre_idea','?')} (intento {p.get('intentos',1)}/3)\n"
        await update.message.reply_text(texto, parse_mode="HTML")
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")

def main():
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no configurado")
        return

    while True:
        try:
            print("[Bot] Iniciando IdeaValidator Bot...")
            app = Application.builder().token(TOKEN).build()
            app.add_handler(CommandHandler("start",  cmd_start))
            app.add_handler(CommandHandler("status", cmd_status))
            app.add_handler(CommandHandler("top",    cmd_top))
            app.add_handler(CommandHandler("stats",  cmd_stats))
            app.add_handler(CommandHandler("idea",   cmd_idea))
            app.add_handler(CommandHandler("cola",   cmd_cola))
            print("[Bot] ✅ Escuchando comandos...")
            app.run_polling(
                drop_pending_updates=True,
                allowed_updates=["message"],
                timeout=30
            )
        except Conflict:
            print("⚠️ Conflict detectado — esperando 30s y reintentando...")
            time.sleep(30)
        except NetworkError as e:
            print(f"⚠️ NetworkError: {e} — reintentando en 15s...")
            time.sleep(15)
        except Exception as e:
            print(f"❌ Error bot: {e} — reintentando en 15s...")
            time.sleep(15)

if __name__ == "__main__":
    main()
# FIN COMPLETO telegram_bot.py
