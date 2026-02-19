import os
import json
import time
import threading
import traceback
import requests
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID = str(os.environ.get("TELEGRAM_CHAT_ID", ""))
NOTION_TOKEN_VAL = os.environ.get("NOTION_TOKEN")
NOTION_DB = os.environ.get("NOTION_DATABASE_ID")
BASE = f"https://api.telegram.org/bot{TOKEN}"
NOTION_HEADERS = {
    "Authorization": f"Bearer {NOTION_TOKEN_VAL}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}


def send(chat_id, text, parse_mode="HTML"):
    if not TOKEN:
        return
    try:
        for i in range(0, len(text), 4000):
            chunk = text[i:i+4000]
            requests.post(
                f"{BASE}/sendMessage",
                json={"chat_id": chat_id, "text": chunk, "parse_mode": parse_mode},
                timeout=10,
            )
            time.sleep(0.3)
    except Exception as e:
        print(f"Send error: {e}")


def notify(text):
    send(CHAT_ID, text)


def get_updates(offset=0):
    try:
        r = requests.get(
            f"{BASE}/getUpdates",
            params={"offset": offset, "timeout": 30},
            timeout=35,
        )
        return r.json().get("result", [])
    except Exception:
        return []


def notion_query(filtro=None, sorts=None, page_size=10):
    url = f"https://api.notion.com/v1/databases/{NOTION_DB}/query"
    payload = {"page_size": page_size}
    if filtro:
        payload["filter"] = filtro
    if sorts:
        payload["sorts"] = sorts
    try:
        r = requests.post(url, headers=NOTION_HEADERS, json=payload, timeout=15)
        r.raise_for_status()
        return r.json().get("results", [])
    except Exception as e:
        print(f"Notion error: {e}")
        return []


def notion_update_page(page_id, properties):
    url = f"https://api.notion.com/v1/pages/{page_id}"
    try:
        r = requests.patch(url, headers=NOTION_HEADERS, json={"properties": properties}, timeout=15)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"Notion update error: {e}")
        return None


def get_nombre(props):
    tlist = props.get("Name", {}).get("title", [])
    item = next(iter(tlist), None)
    if item:
        return item.get("text", {}).get("content", "Sin nombre")
    return "Sin nombre"


def extraer_json(content):
    content = content.strip()
    if "```json" in content:
        try:
            interior = content.split("```json")[1]
            return interior.split("```").strip()
        except Exception:
            pass
    if "```" in content:
        try:
            partes = content.split("```")
            if len(partes) >= 2:
                return partes.strip()[1]
        except Exception:
            pass
    inicio = content.find("{")
    fin = content.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        return content[inicio:fin+1]
    return content


def cmd_ayuda(chat_id):
    send(chat_id, (
        "🤖 <b>ValidationIdea Bot</b>\n\n"
        "<b>Comandos:</b>\n\n"
        "/nueva <i>tema</i> — Genera idea sobre ese tema\n"
        "Ejemplo: <code>/nueva herramientas para abogados</code>\n\n"
        "/top5 — Las 5 mejores ideas por score\n"
        "/estado — Estadisticas del sistema\n"
        "/aprobar <i>nombre</i> — Aniade tag Aprobada\n"
        "/rechazar <i>nombre</i> — Aniade tag Rechazada\n"
        "/ayuda — Muestra este mensaje"
    ))


def cmd_nueva(chat_id, tema):
    send(chat_id, f"⚙️ Generando idea sobre: <b>{tema}</b>...")
    try:
        from groq import Groq
        from agents.encoding_helper import fix_llm_encoding

        client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

        prompt = (
            "Genera UNA idea de negocio digital especifica sobre el tema: " + tema + "\n\n"
            "Responde SOLO con el JSON, sin texto adicional, sin markdown:\n"
            "{\n"
            '  \"nombre\": \"Nombre del producto\",\n'
            '  \"problema\": \"Problema especifico que resuelve\",\n'
            '  \"solucion\": \"Como lo resuelve\",\n'
            '  \"descripcion\": \"Descripcion en 2-3 frases\",\n'
            '  \"propuesta_valor\": \"Por que es mejor que alternativas\",\n'
            '  \"tipo\": \"SaaS o PDF o Plugin o Tool o Agencia\",\n'
            '  \"vertical\": \"Mercado objetivo especifico\",\n'
            '  \"precio\": \"Precio en euros\",\n'
            '  \"monetizacion\": \"Modelo de monetizacion\",\n'
            '  \"tool\": \"Stack tecnologico\",\n'
            '  \"esfuerzo\": \"Horas para MVP\",\n'
            '  \"revenue_6m\": \"Ingresos estimados 6 meses en euros\",\n'
            '  \"como\": \"3 pasos concretos para lanzar\"\n'
            "}"
        )

        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.85,
            max_tokens=900,
        )

        choices = response.choices
        if not choices:
            send(chat_id, "❌ El LLM no devolvio respuesta. Intenta de nuevo.")
            return

        first_choice = next(iter(choices))
        content = first_choice.message.content

        if not content:
            send(chat_id, "❌ Respuesta vacia del LLM.")
            return

        content = content.strip()
        content = fix_llm_encoding(content)
        content = extraer_json(content)
        print(f"DEBUG: {content[:200]}")

        idea = json.loads(content)

        score = 70
        viral = 55
        fortalezas = []

        try:
            from agents.critic_agent import critique
            evaluation = critique(idea)
            if evaluation and isinstance(evaluation, dict):
                score = int(evaluation.get("score_critico", 70))
                viral = int(evaluation.get("viral_score", 55))
                fortalezas = evaluation.get("puntos_fuertes", [])
                idea.update(evaluation)
        except Exception as e_crit:
            print(f"Critic error: {e_crit}")

        idea["fortalezas"] = fortalezas if isinstance(fortalezas, list) else []
        idea["fecha"] = datetime.now().isoformat()
        idea["date"] = idea["fecha"]

        notion_url = ""
        try:
            from agents.notion_sync_agent import sync_idea_to_notion
            result = sync_idea_to_notion(idea)
            if result and isinstance(result, dict):
                notion_url = result.get("url", "")
        except Exception as e_notion:
            print(f"Notion error: {e_notion}")

        ftext = "\n".join([f"  • {f}" for f in idea["fortalezas"][:3]])
        if not ftext:
            ftext = "  • En evaluacion"

        nlink = f'\n\n🔗 <a href="{notion_url}">Ver en Notion</a>' if notion_url else ""

        send(chat_id, (
            f"💡 <b>{idea.get('nombre', 'Nueva idea')}</b>\n\n"
            f"📌 <b>Problema:</b> {idea.get('problema', '')}\n"
            f"✅ <b>Solucion:</b> {idea.get('solucion', '')}\n"
            f"💰 <b>Modelo:</b> {idea.get('monetizacion', '')} — {idea.get('precio', '')}€\n"
            f"👥 <b>Target:</b> {idea.get('vertical', '')}\n"
            f"📊 Score: <b>{score}/100</b> | 🚀 Viral: <b>{viral}/100</b>\n\n"
            f"💪 <b>Fortalezas:</b>\n{ftext}"
            f"{nlink}"
        ))

    except json.JSONDecodeError as e:
        traceback.print_exc()
        send(chat_id, "❌ Error parseando JSON del LLM. Intenta de nuevo.")
    except Exception as e:
        traceback.print_exc()
        send(chat_id, f"❌ Error: {e}")


def cmd_top5(chat_id):
    send(chat_id, "⏳ Consultando top 5...")
    try:
        if not NOTION_DB:
            send(chat_id, "❌ NOTION_DATABASE_ID no configurado")
            return
        pages = notion_query(
            sorts=[{"property": "ScoreCritic", "direction": "descending"}],
            page_size=5,
        )
        if not pages:
            send(chat_id, "No hay ideas aun.")
            return
        text = "🏆 <b>Top 5 Ideas</b>\n\n"
        for i, page in enumerate(pages, 1):
            props = page.get("properties", {})
            nombre = get_nombre(props)
            score = props.get("ScoreCritic", {}).get("number", 0) or 0
            viral = props.get("ScoreViral", {}).get("number", 0) or 0
            url = page.get("url", "")
            text += f"{i}. <b>{nombre}</b>\n   📊 {score}/100 | 🚀 {viral}/100\n   🔗 <a href=\"{url}\">Notion</a>\n\n"
        send(chat_id, text)
    except Exception as e:
        traceback.print_exc()
        send(chat_id, f"❌ Error: {e}")


def cmd_estado(chat_id):
    try:
        from agents.knowledge_base import KnowledgeBase
        kb = KnowledgeBase()
        summary = kb.get_summary()
        todas = notion_query(page_size=100)
        total = len(todas)
        con_rep = notion_query(
            filtro={"property": "Informe Completo", "rich_text": {"is_not_empty": True}},
            page_size=100,
        )
        con_informe = len(con_rep)
        insights = "\n".join([f"  {ins}" for ins in summary.get("insights", [])[:4]])
        send(chat_id, (
            "📊 <b>Estado del Sistema</b>\n\n"
            f"💡 Ideas totales: <b>{total}</b>\n"
            f"📝 Con informe: <b>{con_informe}</b>\n"
            f"⏳ Sin informe: <b>{total - con_informe}</b>\n"
            f"📈 Score promedio: <b>{summary.get('avg_score', 0)}</b>\n\n"
            f"🔥 <b>Insights:</b>\n{insights if insights else '  Sin datos aun'}"
        ))
    except Exception as e:
        traceback.print_exc()
        send(chat_id, f"❌ Error: {e}")


def tag_idea(chat_id, nombre_buscar, tag):
    try:
        if not NOTION_DB:
            send(chat_id, "❌ NOTION_DATABASE_ID no configurado")
            return
        pages = notion_query(
            filtro={"property": "Name", "title": {"contains": nombre_buscar}},
            page_size=5,
        )
        if not pages:
            send(chat_id, f"❌ No encontre idea con '{nombre_buscar}'")
            return
        page = next(iter(pages))
        page_id = page["id"]
        current = page["properties"].get("Tags", {}).get("multi_select", [])
        notion_update_page(page_id, {"Tags": {"multi_select": current + [{"name": tag}]}})
        nombre = get_nombre(page["properties"])
        send(chat_id, f"✅ Tag '{tag}' aniadido a: <b>{nombre}</b>")
    except Exception as e:
        traceback.print_exc()
        send(chat_id, f"❌ Error: {e}")


def process_update(update):
    msg = update.get("message", {})
    chat_id = str(msg.get("chat", {}).get("id", ""))
    text = msg.get("text", "").strip()
    if not text:
        return
    if CHAT_ID and chat_id != CHAT_ID:
        send(chat_id, "No autorizado.")
        return
    lower = text.lower()
    if lower in ["/start", "/ayuda", "/help"]:
        cmd_ayuda(chat_id)
    elif lower.startswith("/nueva"):
        partes = text.split(maxsplit=1)
        if len(partes) < 2:
            send(chat_id, "⚠️ Uso: <code>/nueva tema aqui</code>")
        else:
            tema = partes[-1]
            threading.Thread(target=cmd_nueva, args=(chat_id, tema), daemon=True).start()
    elif lower == "/top5":
        threading.Thread(target=cmd_top5, args=(chat_id,), daemon=True).start()
    elif lower == "/estado":
        threading.Thread(target=cmd_estado, args=(chat_id,), daemon=True).start()
    elif lower.startswith("/aprobar"):
        partes = text.split(maxsplit=1)
        if len(partes) < 2:
            send(chat_id, "⚠️ Uso: <code>/aprobar nombre</code>")
        else:
            threading.Thread(target=tag_idea, args=(chat_id, partes[-1], "Aprobada"), daemon=True).start()
    elif lower.startswith("/rechazar"):
        partes = text.split(maxsplit=1)
        if len(partes) < 2:
            send(chat_id, "⚠️ Uso: <code>/rechazar nombre</code>")
        else:
            threading.Thread(target=tag_idea, args=(chat_id, partes[-1], "Rechazada"), daemon=True).start()
    else:
        send(chat_id, "❓ Comando no reconocido. Usa /ayuda")


def main():
    print("🤖 Bot iniciado...")
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN no encontrado en .env")
        return
    if not CHAT_ID:
        print("❌ TELEGRAM_CHAT_ID no encontrado en .env")
        return
    print(f"✅ Token: ...{TOKEN[-10:]}")
    print(f"✅ Chat ID: {CHAT_ID}")
    print(f"✅ Notion DB: {NOTION_DB or 'NO CONFIGURADO'}")
    notify("🚀 <b>ValidationIdea Bot iniciado</b>\nUsa /ayuda para ver comandos.")
    offset = 0
    while True:
        try:
            updates = get_updates(offset)
            for u in updates:
                offset = u["update_id"] + 1
                process_update(u)
        except KeyboardInterrupt:
            print("👋 Bot detenido")
            break
        except Exception as e:
            print(f"❌ Error loop: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()