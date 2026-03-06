import os
import sys
import json
import time
import logging
import subprocess
from datetime import datetime, timedelta, timezone
from logging.handlers import TimedRotatingFileHandler

import pytz

os.environ["PYTHONUTF8"] = "1"

ZONA = pytz.timezone("Europe/Madrid")

def _configurar_logger() -> logging.Logger:
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

def log(msg: str):
    _logger.info(msg)

def enviar_telegram(mensaje: str):
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

def ejecutar_script(nombre: str):
    log(f"▶️  {nombre}...")
    try:
        resultado = subprocess.run(
            [sys.executable, nombre],
            capture_output=True,
            timeout=240
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

def hc_gemini():
    try:
        from google import genai
        client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
        client.models.generate_content(model="gemini-2.0-flash", contents="ok")
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
        ok_g, msg_g = hc_gemini()
        if not ok_g:
            log(f"⚠️ Gemini degradado (no crítico): {msg_g}")
    except Exception as eg:
        log(f"⚠️ Gemini no disponible: {eg}")

    checks = {"Groq": hc_groq(), "Notion": hc_notion()}
    fallos = [(srv, msg) for srv, (ok, msg) in checks.items() if not ok]

    if fallos:
        lineas = "\n".join(f"❌ <b>{srv}</b>: {msg}" for srv, msg in fallos)
        enviar_telegram(
            f"🚨 <b>HEALTH CHECK — FALLO</b>\n"
            f"🕐 {datetime.now(ZONA).strftime('%d/%m/%Y %H:%M')}\n\n"
            f"{lineas}\n\n⚙️ Revisa Railway logs."
        )
        log(f"🚨 Servicios fallidos: {[s for s, _ in fallos]}")
    else:
        log("✅ Health check OK — Groq ✅  Notion ✅")

    return len(fallos) == 0

def procesar_cola_csv():
    try:
        from agents.cola_csv import obtener_pendientes, eliminar_de_cola, incrementar_intentos
        from agents.notion_sync_agent import sync_idea_to_notion
        pendientes = obtener_pendientes()
        if not pendientes:
            return
        log(f"📋 Cola CSV: {len(pendientes)} pendiente(s)")
        for fila in pendientes:
            ts       = fila.get("timestamp", "")
            nombre   = fila.get("nombre_idea", "?")
            intentos = int(fila.get("intentos", 1))
            if intentos > 3:
                log(f"⏭️ Descartando '{nombre}' (>3 intentos)")
                eliminar_de_cola(ts)
                continue
            try:
                datos = json.loads(fila.get("datos_json", "{}"))
                resultado = sync_idea_to_notion(datos)
                if resultado:
                    log(f"✅ Reintento exitoso: '{nombre}'")
                    eliminar_de_cola(ts)
                else:
                    raise Exception("sync devolvió None")
            except json.JSONDecodeError:
                log(f"❌ JSON corrupto '{nombre}', eliminando")
                eliminar_de_cola(ts)
            except Exception as e:
                log(f"❌ Reintento fallido '{nombre}': {e}")
                incrementar_intentos(ts)
    except Exception as e:
        log(f"❌ Error cola CSV: {e}")

def generar_nueva_idea():
    log("🧠 Generando nueva idea...")
    exito, salida = ejecutar_script("run_batch.py")

    # 🆕 Notificar Telegram si idea fue generada
    if exito and "✅ Sincronizada:" in salida:
        try:
            nombre = ""
            score  = ""
            url    = ""
            for linea in salida.split("\n"):
                if "✅ Sincronizada:" in linea:
                    nombre = linea.split("✅ Sincronizada:")[-1].strip()
                if "📊 Score:" in linea:
                    score = linea.split("📊 Score:")[-1].strip().split("|")[0].strip()
                if "notion.so" in linea:
                    url = linea.strip()

            enviar_telegram(
                f"💡 <b>Nueva idea generada</b>\n\n"
                f"🚀 <b>{nombre}</b>\n"
                f"📊 Score: <b>{score}</b>\n"
                f"🔗 {url}"
            )
        except Exception as e:
            log(f"⚠️ Error notificando Telegram idea: {e}")
    elif not exito:
        log("❌ Error generando idea")

    return exito

def procesar_informes():
    log("📄 Revisando informes pendientes...")
    exito, _ = ejecutar_script("run_monitor.py")
    return exito

def mantenimiento_nocturno():
    log("🔧 Mantenimiento nocturno (03:00)...")
    ejecutar_script("completar_campos.py")
    ejecutar_script("run_monitor.py")
    log("🔧 Mantenimiento completado")

def enviar_resumen_diario():
    log("☀️ Resumen diario (08:00)...")
    try:
        from agents.knowledge_base import get_stats, get_top_ideas
        stats      = get_stats()
        total      = stats.get("total_ideas", 0)
        score_prom = stats.get("score_promedio", 0)
        mejor_v    = stats.get("mejor_vertical", "N/A")
        mejor_t    = stats.get("mejor_tipo", "N/A")
        mejor_idea = stats.get("mejor_idea", "N/A")

        # Top 3 ideas
        top3 = get_top_ideas(3)
        top_txt = ""
        for i, idea in enumerate(top3, 1):
            top_txt += f"\n{i}. <b>{idea['nombre']}</b> → {idea['score']}pts ({idea['tipo']})"

        cola_txt = ""
        try:
            from agents.cola_csv import contar_pendientes
            n = contar_pendientes()
            if n > 0:
                cola_txt = f"\n⏳ Cola CSV: <b>{n}</b> pendiente(s)"
        except:
            pass

        enviar_telegram(
            f"☀️ <b>Resumen diario — ValidationIdea</b>\n"
            f"📅 {datetime.now(ZONA).strftime('%d/%m/%Y')}\n\n"
            f"💡 Ideas generadas: <b>{total}</b>\n"
            f"📊 Score promedio: <b>{score_prom}/100</b>\n"
            f"🏆 Mejor vertical: <b>{mejor_v}</b>\n"
            f"🚀 Mejor tipo: <b>{mejor_t}</b>\n"
            f"⭐ Mejor idea: <b>{mejor_idea}</b>"
            f"\n\n🏅 <b>TOP 3 IDEAS:</b>{top_txt}"
            f"{cola_txt}\n\n"
            f"✅ Sistema operativo 24/7"
        )
    except Exception as e:
        log(f"❌ Error resumen diario: {e}")
        enviar_telegram(f"☀️ Sistema activo — error en resumen: {e}")

def main():
    log("🚀 monitor_nocturno.py iniciado — P1→P10 activos")
    enviar_telegram(
        "🟢 <b>Monitor ValidationIdea arrancado</b>\n\n"
        "✅ P1–P10 activos\n"
        "✅ Gemini: modo opcional (no bloquea)\n"
        "✅ Groq + Notion: críticos\n"
        "💡 Genera ideas cada 30 min automáticamente"
    )

    ahora_utc      = datetime.now(timezone.utc)
    ultimo_batch   = ahora_utc - timedelta(minutes=31)
    ultimo_informe = ahora_utc - timedelta(minutes=6)
    ultimo_health  = ahora_utc - timedelta(hours=1, minutes=1)
    dia_resumen       = -1
    dia_mantenimiento = -1

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
                procesar_informes()
                procesar_cola_csv()
                ultimo_informe = ahora_utc

            if (ahora_utc - ultimo_health).total_seconds() >= 60 * 60:
                ejecutar_health_check()
                ultimo_health = ahora_utc

            if hora == 8 and dia != dia_resumen:
                enviar_resumen_diario()
                dia_resumen = dia

            if hora == 3 and dia != dia_mantenimiento:
                mantenimiento_nocturno()
                dia_mantenimiento = dia

        except Exception as e:
            log(f"❌ Error en loop principal: {e}")

        time.sleep(60)

if __name__ == "__main__":
    main()
# FIN COMPLETO monitor_nocturno.py
