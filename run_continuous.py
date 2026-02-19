# run_continuous.py - SCHEDULER AUTOMATICO CON LOOP INFINITO
# Coloca este archivo en: C:/Users/juanj/Documents/validationidea/
# Ejecutar con: python run_continuous.py

import time
import subprocess
import sys
import os
import json
from datetime import datetime

# ============================================================
# CONFIGURACION — Ajusta estos valores segun necesites
# ============================================================
INTERVAL_MINUTES = 30       # Tiempo entre ideas (minutos)
DAILY_LIMIT = 20            # Maximo ideas por dia
MAX_CONSECUTIVE_ERRORS = 5  # Errores antes de pausa larga
LOG_FILE = "data/system.log"
# ============================================================


def log(message):
    """Registra en consola Y en archivo de log persistente"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_msg = f"[{timestamp}] {message}"
    print(full_msg)
    os.makedirs("data", exist_ok=True)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(full_msg + "\n")


def count_today_ideas():
    """Cuenta cuantas ideas se generaron hoy"""
    try:
        with open("data/ideas.json", "r", encoding="utf-8") as f:
            ideas = json.load(f)
        today = datetime.now().strftime("%Y-%m-%d")
        return len([i for i in ideas if i.get("date", "").startswith(today)])
    except Exception:
        return 0


def seconds_until_tomorrow():
    """Calcula segundos hasta medianoche"""
    now = datetime.now()
    return ((23 - now.hour) * 3600 +
            (59 - now.minute) * 60 +
            (60 - now.second))


def run_batch():
    """Ejecuta run_batch.py — retorna True si exito, False si fallo"""
    try:
        result = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120  # 2 minutos maximo por ejecucion
        )
        if result.returncode == 0:
            log("✅ Idea generada exitosamente")
            # Mostrar ultimas 5 lineas del output
            lines = [l for l in result.stdout.strip().split("\n") if l.strip()]
            for line in lines[-5:]:
                log(f"   {line.strip()}")
            return True
        else:
            error_msg = result.stderr[-300:] if result.stderr else "desconocido"
            log(f"❌ Error en run_batch: {error_msg}")
            return False
    except subprocess.TimeoutExpired:
        log("⚠️  Timeout — la generacion tardo mas de 2 minutos")
        return False
    except Exception as e:
        log(f"❌ Error inesperado al ejecutar run_batch: {e}")
        return False


def main():
    log("=" * 55)
    log("🚀 SISTEMA CONTINUO DE GENERACION DE IDEAS v2.0")
    log(f"⏱️  Intervalo: {INTERVAL_MINUTES} minutos entre ideas")
    log(f"📊 Limite diario: {DAILY_LIMIT} ideas")
    log(f"📝 Log en: {LOG_FILE}")
    log("   Presiona Ctrl+C para detener")
    log("=" * 55)

    consecutive_errors = 0

    while True:
        try:
            # Verificar limite diario
            today_count = count_today_ideas()

            if today_count >= DAILY_LIMIT:
                wait_secs = seconds_until_tomorrow() + 60
                log(f"📊 Limite diario: {today_count}/{DAILY_LIMIT} ideas.")
                log(f"   Esperando {wait_secs // 3600:.1f}h hasta manana...")
                time.sleep(wait_secs)
                continue

            log(f"🎯 Iniciando generacion... (idea #{today_count + 1} de hoy, max {DAILY_LIMIT})")

            success = run_batch()

            if success:
                consecutive_errors = 0
                log(f"⏳ Proxima idea en {INTERVAL_MINUTES} minutos...\n")
                time.sleep(INTERVAL_MINUTES * 60)
            else:
                consecutive_errors += 1
                log(f"⚠️  Error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}")

                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    log(f"🚨 {MAX_CONSECUTIVE_ERRORS} errores consecutivos. Pausa de 1 hora...")
                    consecutive_errors = 0
                    time.sleep(3600)
                else:
                    # Backoff exponencial: 5, 10, 15, 20, 25 minutos
                    wait_min = min(5 * consecutive_errors, 30)
                    log(f"   Reintentando en {wait_min} minutos...\n")
                    time.sleep(wait_min * 60)

        except KeyboardInterrupt:
            log("\n👋 Sistema detenido por el usuario")
            break
        except Exception as e:
            log(f"❌ Error critico en bucle principal: {e}")
            time.sleep(300)  # Esperar 5 minutos y reintentar


if __name__ == "__main__":
    main()
