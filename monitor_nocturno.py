import os
import sys
import json
import time
import subprocess
from datetime import datetime, timedelta

import pytz

os.environ["PYTHONUTF8"] = "1"

ZONA = pytz.timezone("Europe/Madrid")


# ── Logging ───────────────────────────────────────────────────────────────────

def log(msg):
    ts = datetime.now(ZONA).strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ── Telegram via requests (sin bot async) ─────────────────────────────────────

def enviar_telegram(mensaje):
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        log("⚠️ Variables Telegram no configuradas")
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


# ── Subprocess seguro (bytes + decode, sin text=True) ─────────────────────────

def ejecutar_script(nombre):
    log(f"▶️  {nombre}...")
    try:
        resultado = subprocess.run(
            [sys.executable, nombre],
            capture_output=True,
            timeout=300
        )
        salida = resultado.stdout.decode("utf-8", errors="replace")
        errores = resultado.stderr.decode("utf-8", errors="replace")
        exito = resultado.returncode == 0
        if not exito and errores:
            log(f"STDERR {nombre}: {errores[:300]}")
        return exito, salida
    except subprocess.TimeoutExpired:
        log(f"⏰ Timeout en {nombre}")
        return False, "Timeout"
    except Exception as e:
        log(f"❌ Error ejecutando {nombre}: {e}")
        return False, str(e)


# ── P3: HEALTH CHECK ──────────────────────────────────────────────────────────

def hc_groq():
    try:
        import groq
        client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"), timeout=10)
        client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": "ok"}],
            max_tokens=3,
            temperature=0
        )
        return True, "OK"
    except Exception as e:
        return False, str(e)[:200]


def hc_gemini():
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash")
        model.generate_content("ok", generation_config={"max_output_tokens": 3})
        return True, "OK"
    except Exception as e:
        return False, str(e)[:200]


def hc_notion():
    try:
        import requests
        token = os.environ.get("NOTION_TOKEN", "")
        db_id = os.environ.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")
        resp = requests.get(
            f"https://api.notion.com/v1/databases/{db_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "Notion-Version": "2022-06-28"
            },
            timeout=10
        )
        if resp.status_code == 200:
            return True, "OK"
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)[:200]


def ejecutar_health_check():
    log("🏥 Health check iniciado...")
    ahora_str = datetime.now(ZONA).strftime("%d/%m/%Y %H:%M:%S")

    checks = {
        "Groq": hc_groq(),
        "Gemini": hc_gemini(),
        "Notion": hc_notion()
    }

    fallos = [(srv, msg) for srv, (ok, msg) in checks.items() if not ok]

    if fallos:
        lineas = "\n".join(f"❌ <b>{srv}</b>: {msg}" for srv, msg in fallos)
        enviar_telegram(
            f"🚨 <b>HEALTH CHECK — FALLO</b>\n"
            f"🕐 {ahora_str}\n\n"
            f"{lineas}\n\n"
            f"⚙️ Revisa Railway logs para detalles."
        )
        log(f"🚨 Servicios fallidos: {[s for s, _ in fallos]}")
    else:
        log("✅ Health check OK — Groq ✅  Gemini ✅  Notion ✅")

    return len(fallos) == 0


# ── P2: REINTENTOS COLA CSV ───────────────────────────────────────────────────

def procesar_cola_csv():
    try:
        from agents.cola_csv import (
            obtener_pendientes, eliminar_de_cola, incrementar_intentos
        )
        from agents.notion_sync_agent import sync_idea_to_notion

        pendientes = obtener_pendientes()
        if not pendientes:
            return

        log(f"📋 Cola CSV: {len(pendientes)} pendiente(s)")

        for fila in pendientes:
            ts = fila.get("timestamp", "")
            nombre = fila.get("nombre_idea", "?")
            intentos = int(fila.get("intentos", 1))
            log(f"🔄 Reintento {intentos}/3 — '{nombre}'")
            try:
                datos = json.loads(fila.get("datos_json", "{}"))
                resultado = sync_idea_to_notion(datos)
                if resultado:
                    log(f"✅ Reintento exitoso: '{nombre}'")
                    eliminar_de_cola(ts)
                else:
                    raise Exception("sync devolvió None/False")
            except json.JSONDecodeError:
                log(f"❌ JSON corrupto para '{nombre}', eliminando de cola")
                eliminar_de_cola(ts)
            except Exception as e:
                log(f"❌ Reintento fallido para '{nombre}': {e}")
                incrementar_intentos(ts)

    except Exception as e:
        log(f"❌ Error procesando cola CSV: {e}")


# ── TAREAS PROGRAMADAS ────────────────────────────────────────────────────────

def generar_nueva_idea():
    log("🧠 Generando nueva idea (con KB context)...")
    exito, _ = ejecutar_script("run_batch.py")
    if not exito:
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
        from agents.knowledge_base import get_stats
        stats = get_stats()
        total = stats.get("total_ideas", 0)
        score_prom = stats.get("score_promedio", 0)
        mejor_v = stats.get("mejor_vertical", "N/A")
        mejor_t = stats.get("mejor_tipo", "N/A")

        cola_txt = ""
        try:
            from agents.cola_csv import contar_pendientes
            n = contar_pendientes()
            if n > 0:
                cola_txt = f"\n⏳ Ideas en cola CSV: <b>{n}</b> (se reintentarán)"
        except Exception:
            pass

        enviar_telegram(
            f"☀️ <b>Resumen diario — ValidationIdea</b>\n"
            f"📅 {datetime.now(ZONA).strftime('%d/%m/%Y')}\n\n"
            f"💡 Ideas en KB: <b>{total}</b>\n"
            f"📊 Score promedio: <b>{score_prom:.1f}/100</b>\n"
            f"🏆 Mejor vertical: <b>{mejor_v}</b>\n"
            f"🚀 Mejor tipo: <b>{mejor_t}</b>"
            f"{cola_txt}\n\n"
            f"Sistema operativo 24/7 ✅"
        )
    except Exception as e:
        log(f"❌ Error resumen diario: {e}")
        enviar_telegram(f"☀️ Sistema activo — error generando resumen: {e}")


# ── LOOP PRINCIPAL ────────────────────────────────────────────────────────────

def main():
    log("🚀 monitor_nocturno.py iniciado — P1+P2+P3 activos")
    enviar_telegram(
        "🟢 <b>Monitor ValidationIdea arrancado</b>\n\n"
        "✅ P1: Prompt evolutivo con KB\n"
        "✅ P2: Cola CSV reintentos automáticos\n"
        "✅ P3: Health check cada hora"
    )

    ahora_utc = datetime.utcnow()
    ultimo_batch = ahora_utc - timedelta(minutes=31)    # ejecutar pronto al iniciar
    ultimo_informe = ahora_utc - timedelta(minutes=6)   # ejecutar pronto al iniciar
    ultimo_health = ahora_utc - timedelta(hours=1, minutes=1)  # ejecutar pronto

    dia_resumen = -1
    dia_mantenimiento = -1

    while True:
        try:
            ahora_utc = datetime.utcnow()
            ahora_local = datetime.now(ZONA)
            hora = ahora_local.hour
            dia = ahora_local.day

            # Cada 30 min — generar idea nueva
            if (ahora_utc - ultimo_batch).total_seconds() >= 30 * 60:
                generar_nueva_idea()
                ultimo_batch = ahora_utc

            # Cada 5 min — informes + cola CSV (P2)
            if (ahora_utc - ultimo_informe).total_seconds() >= 5 * 60:
                procesar_informes()
                procesar_cola_csv()
                ultimo_informe = ahora_utc

            # Cada 60 min — health check (P3)
            if (ahora_utc - ultimo_health).total_seconds() >= 60 * 60:
                ejecutar_health_check()
                ultimo_health = ahora_utc

            # A las 08:00 — resumen diario
            if hora == 8 and dia != dia_resumen:
                enviar_resumen_diario()
                dia_resumen = dia

            # A las 03:00 — mantenimiento nocturno
            if hora == 3 and dia != dia_mantenimiento:
                mantenimiento_nocturno()
                dia_mantenimiento = dia

        except Exception as e:
            log(f"❌ Error en loop principal: {e}")

        time.sleep(60)


if __name__ == "__main__":
    main()
