import os
import time
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")

def send_telegram(message):
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": message,
            "parse_mode": "HTML"
        }
        requests.post(url, data=data, timeout=10)
    except Exception as e:
        logger.error(f"Error Telegram: {e}")

def generar_y_sincronizar():
    from agents.generator_agent import generate
    from agents.notion_sync_agent import sync_idea_to_notion
    logger.info("Generando 2 ideas automaticas...")
    for i in range(2):
        try:
            idea = generate()
            if idea:
                resultado = sync_idea_to_notion(idea)
                nombre = idea.get('name', 'Sin nombre')
                page_id = ''
                if resultado and isinstance(resultado, dict):
                    page_id = resultado.get('id', '')
                if page_id:
                    url_n = f"https://notion.so/{page_id.replace('-', '')}"
                else:
                    url_n = "Notion"
                send_telegram(f"Nueva idea generada:\n{nombre}\n{url_n}")
                logger.info(f"Idea {i+1} creada: {nombre}")
                time.sleep(3)
        except Exception as e:
            logger.error(f"Error idea {i+1}: {e}")
            send_telegram(f"Error generando idea: {e}")

def proceso_nocturno():
    import run_monitor
    logger.info("Proceso nocturno 03:00")
    send_telegram("Proceso nocturno iniciado")
    try:
        run_monitor.main()
        send_telegram("Proceso nocturno completado OK")
    except Exception as e:
        logger.error(f"Error nocturno: {e}")
        send_telegram(f"Error nocturno: {e}")

def resumen_diario():
    logger.info("Resumen diario 08:00")
    send_telegram("Buenos dias! El monitor lleva 24h activo generando ideas.")

def detectar_sin_informe():
    try:
        import run_monitor
        run_monitor.main()
    except Exception as e:
        logger.error(f"Error detectando informes: {e}")

def main():
    logger.info("Monitor nocturno iniciado")
    send_telegram("Monitor 24/7 activo y funcionando")
    ultimo_2h = 0
    ultimo_5min = 0
    nocturno_fecha = None
    resumen_fecha = None
    while True:
        ahora = time.time()
        dt = datetime.now()
        h = dt.hour
        m = dt.minute
        if ahora - ultimo_2h >= 7200:
            generar_y_sincronizar()
            ultimo_2h = ahora
        if ahora - ultimo_5min >= 300:
            detectar_sin_informe()
            ultimo_5min = ahora
        if h == 3 and m == 0:
            hoy = dt.date()
            if nocturno_fecha != hoy:
                proceso_nocturno()
                nocturno_fecha = hoy
        if h == 8 and m == 0:
            hoy = dt.date()
            if resumen_fecha != hoy:
                resumen_diario()
                resumen_fecha = hoy
        time.sleep(30)

if __name__ == "__main__":
    main()
