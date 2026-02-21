import os
import time
import threading
import datetime
import requests
import pytz
from dotenv import load_dotenv

load_dotenv()

TOKEN  = os.environ.get('TELEGRAM_BOT_TOKEN', '')
CHAT   = os.environ.get('TELEGRAM_CHAT_ID', '')
NKEY   = os.environ.get('NOTION_API_KEY', '')
DB_ID  = os.environ.get('NOTION_DATABASE_ID', '')

HEADERS_N = {
    'Authorization': 'Bearer ' + NKEY,
    'Notion-Version': '2022-06-28',
    'Content-Type': 'application/json'
}

TZ = pytz.timezone('Europe/Madrid')

def tg(msg):
    if not TOKEN or not CHAT:
        return
    try:
        requests.post(
            f'https://api.telegram.org/bot{TOKEN}/sendMessage',
            json={'chat_id': CHAT, 'text': msg, 'parse_mode': 'HTML'},
            timeout=10
        )
    except Exception as e:
        print(f'[TG ERROR] {e}')

def get_ideas():
    try:
        r = requests.post(
            f'https://api.notion.com/v1/databases/{DB_ID}/query',
            headers=HEADERS_N, json={}, timeout=15
        )
        r.raise_for_status()
        return {p['id']: p for p in r.json().get('results', [])}
    except Exception as e:
        print(f'[NOTION ERROR] {e}')
        return {}

def contar_informes(ideas):
    total = len(ideas)
    def txt(props, c):
        try: return props[c]['rich_text'][0]['text']['content']
        except: return ''
    con = sum(1 for p in ideas.values() if txt(p['properties'], 'Informe Completo'))
    return total, con

def procesar_informes():
    try:
        print('[MONITOR] Lanzando generacion de informes...')
        from run_monitor import main as run_main
        run_main()
        print('[MONITOR] Informes completados.')
    except Exception as e:
        print(f'[MONITOR ERROR] {e}')
        tg(f'Error generando informes: {str(e)[:120]}')

def lanzar_informes_async():
    threading.Thread(target=procesar_informes, daemon=True).start()

def main():
    print('[MONITOR] Monitor nocturno iniciado.')
    tg('Monitor nocturno activo. Revisa Notion cada 5 min.')

    ideas_conocidas = get_ideas()
    ahora = datetime.datetime.now(TZ)
    ultimo_proceso = ahora - datetime.timedelta(hours=2)
    ultimo_resumen = ahora - datetime.timedelta(hours=2)

    while True:
        try:
            ahora = datetime.datetime.now(TZ)
            ideas_actuales = get_ideas()

            nuevas = [nid for nid in ideas_actuales if nid not in ideas_conocidas]
            for nid in nuevas:
                page = ideas_actuales[nid]
                props = page.get('properties', {})
                try:
                    nombre = props['Name']['title'][0]['text']['content']
                except Exception:
                    nombre = 'Nueva idea'
                url = page.get('url', '')
                tg(f'Nueva idea: {nombre} - {url}')
                print(f'[MONITOR] Nueva idea: {nombre}')
                lanzar_informes_async()

            ideas_conocidas = ideas_actuales

            if ahora.hour == 8 and ahora.minute < 5:
                if (ahora - ultimo_resumen).total_seconds() > 3600:
                    total, con = contar_informes(ideas_actuales)
                    tg(f'Buenos dias! Ideas: {total} | Con informe: {con} | Pendientes: {total-con}')
                    ultimo_resumen = ahora

            if ahora.hour == 3 and ahora.minute < 5:
                if (ahora - ultimo_proceso).total_seconds() > 3600:
                    tg('Proceso nocturno iniciado...')
                    print('[MONITOR] Iniciando proceso nocturno...')
                    procesar_informes()
                    ultimo_proceso = ahora
                    total, con = contar_informes(get_ideas())
                    tg(f'Proceso nocturno completado. Ideas: {total} | Con informe: {con}')

            time.sleep(300)

        except Exception as e:
            print(f'[LOOP ERROR] {str(e)[:100]}')
            time.sleep(60)

if __name__ == '__main__':
    main()
