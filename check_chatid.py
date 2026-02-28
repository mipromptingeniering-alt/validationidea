from dotenv import load_dotenv
import os, requests
load_dotenv()
token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
chat_id_env = os.environ.get("TELEGRAM_CHAT_ID", "")
print("CHAT_ID en .env: [" + chat_id_env + "]")
r = requests.get("https://api.telegram.org/bot" + token + "/getUpdates?limit=10&offset=0")
updates = r.json().get("result", [])
if updates:
    for u in updates:
        msg = u.get("message", {})
        cid = str(msg.get("chat", {}).get("id", "?"))
        txt = msg.get("text", "")
        print("chat_id real: " + cid + "  |  texto: " + txt)
else:
    print("Sin updates - manda /start al bot en Telegram y repite")
