import os
import json
import requests
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from agents.encoding_helper import fix_llm_encoding

load_dotenv()

TOKEN              = os.environ.get("TELEGRAM_BOT_TOKEN")
CHAT_ID            = os.environ.get("TELEGRAM_CHAT_ID")
NOTION_API_KEY     = os.environ.get("NOTION_TOKEN") or os.environ.get("NOTION_API_KEY")
NOTION_DATABASE_ID = os.environ.get("NOTION_DATABASE_ID")
GROQ_API_KEY       = os.environ.get("GROQ_API_KEY")
NOTION_VERSION     = "2022-06-28"


# ─── Helpers Notion ──────────────────────────────────────────────────────────

def _h():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_VERSION,
    }


def get_ideas(page_size: int = 200) -> list:
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    ideas, cursor = [], None
    while True:
        body = {"page_size": min(page_size, 100)}
        if cursor:
            body["start_cursor"] = cursor
        r = requests.post(url, headers=_h(), json=body, timeout=30)
        data = r.json()
        ideas.extend(data.get("results", []))
        if not data.get("has_more") or len(ideas) >= page_size:
            break
        cursor = data.get("next_cursor")
    return ideas


def get_txt(props, key: str) -> str:
    p  = props.get(key, {})
    rt = p.get("rich_text") or p.get("title") or []
    return " ".join(t.get("plain_text", "") for t in rt).strip()


def get_num(props, key: str):
    return props.get(key, {}).get("number")


def get_score(props) -> int | None:
    """Busca score en ScoreGen (nuevo) y en Score (campo antiguo)."""
    s = get_num(props, "ScoreGen")
    if s is None:
        s = get_num(props, "Score")
    return s


# ─── Helper LLM ──────────────────────────────────────────────────────────────

def llamar_groq(prompt: str, max_tokens: int = 600) -> str:
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers={"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"},
        json={
            "model": "llama-3.3-70b-versatile",
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.8,
            "max_tokens": max_tokens,
        },
        timeout=60,
    )
    if r.status_code == 429:
        raise RuntimeError("RATE_LIMIT")
    r.raise_for_status()
    return fix_llm_encoding(r.json()["choices"][0]["message"]["content"])


def crear_idea_notion(nombre, problema, solucion, descripcion,
                      valor, target, negocio, score: int) -> str:
    def rt(t):
        return [{"type": "text", "text": {"content": str(t)[:2000]}}]

    payload = {
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": {
            "Name":        {"title":     rt(nombre)},
            "Problem":     {"rich_text": rt(problema)},
            "Solution":    {"rich_text": rt(solucion)},
            "Description": {"rich_text": rt(descripcion)},
            "Value":       {"rich_text": rt(valor)},
            "Target":      {"rich_text": rt(target)},
            "Business":    {"rich_text": rt(negocio)},
            "ScoreGen":    {"number":    score},
            "Date":        {"date":      {"start": datetime.now().strftime("%Y-%m-%d")}},
        },
    }
    r = requests.post("https://api.notion.com/v1/pages",
                      headers=_h(), json=payload, timeout=30)
    r.raise_for_status()
    return f"https://notion.so/{r.json()['id'].replace('-', '')}"


def añadir_tag(page_id: str, props: dict, nuevo_tag: str, quitar_tag: str = "") -> bool:
    tags = [t["name"] for t in props.get("Tags", {}).get("multi_select", [])]
    if nuevo_tag not in tags:
        tags.append(nuevo_tag)
    if quitar_tag and quitar_tag in tags:
        tags.remove(quitar_tag)
    r = requests.patch(
        f"https://api.notion.com/v1/pages/{page_id}",
        headers=_h(),
        json={"properties": {"Tags": {"multi_select": [{"name": t} for t in tags]}}},
        timeout=30,
    )
    return r.status_code == 200


# ─── Handlers ────────────────────────────────────────────────────────────────

def solo_mi_chat(update: Update) -> bool:
    return str(update.effective_chat.id) == str(CHAT_ID)


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    await update.message.reply_text(
        "🤖 <b>IdeaValidator Bot</b>\n\n"
        "<b>Comandos:</b>\n"
        "/nueva &lt;tema&gt; — Genera idea sobre ese tema\n"
        "/top5 — Top 5 ideas por ScoreGen\n"
        "/estado — Estadísticas del sistema\n"
        "/insights — Qué tipos de ideas funcionan mejor\n"
        "/aprobar &lt;nombre&gt; — Marca idea como aprobada\n"
        "/rechazar &lt;nombre&gt; — Marca idea como rechazada\n"
        "/ayuda — Esta ayuda",
        parse_mode="HTML",
    )


async def cmd_nueva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    if not context.args:
        await update.message.reply_text("❌ Uso: /nueva &lt;tema&gt;\nEjemplo: /nueva automatización para freelancers", parse_mode="HTML")
        return

    tema = " ".join(context.args)
    await update.message.reply_text(f"🤖 Generando idea sobre: <b>{tema}</b>...", parse_mode="HTML")

    prompt = f"""Genera una idea de negocio digital sobre el tema: "{tema}"

Responde ÚNICAMENTE en JSON exacto (sin markdown ni texto extra):
{{
  "nombre": "Nombre del producto (máx 3 palabras)",
  "problema": "Problema que resuelve en 2 frases con datos",
  "solucion": "Cómo funciona exactamente en 2 frases",
  "descripcion": "Descripción en 1 frase estilo tweet de lanzamiento",
  "valor": "Propuesta de valor única frente a alternativas",
  "target": "Cliente ideal: perfil concreto, edad, ocupación, dolor",
  "negocio": "Precio en euros y modelo de monetización concreto",
  "score": 78
}}"""

    try:
        texto = llamar_groq(prompt, max_tokens=600)
        texto = texto.strip()
        if "```" in texto:
            partes = texto.split("```")
            for parte in partes:
                parte = parte.strip().lstrip("json").strip()
                if parte.startswith("{"):
                    texto = parte
                    break

        data        = json.loads(texto)
        nombre      = data.get("nombre", "Nueva Idea")
        problema    = data.get("problema", "")
        solucion    = data.get("solucion", "")
        descripcion = data.get("descripcion", "")
        valor       = data.get("valor", "")
        target      = data.get("target", "")
        negocio     = data.get("negocio", "")
        score       = int(data.get("score", 70))

        notion_url = crear_idea_notion(
            nombre, problema, solucion, descripcion, valor, target, negocio, score
        )

        # Auto-aprendizaje: registrar en KB
        try:
            from agents.knowledge_base import aprender
            aprender({"nombre": nombre, "tipo": "Nueva", "vertical": target}, score)
        except Exception:
            pass

        await update.message.reply_text(
            f"💡 <b>{nombre}</b>\n\n"
            f"📌 <b>Problema:</b> {problema}\n"
            f"✅ <b>Solución:</b> {solucion}\n"
            f"💰 <b>Modelo:</b> {negocio}\n"
            f"👥 <b>Target:</b> {target}\n"
            f"📊 <b>Score:</b> {score}/100\n\n"
            f'🔗 <a href="{notion_url}">Ver en Notion</a>',
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except json.JSONDecodeError:
        await update.message.reply_text(
            "⚠️ El LLM no devolvió JSON válido. Intenta de nuevo."
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return

    await update.message.reply_text("🔍 Buscando top 5...")

    try:
        ideas = get_ideas(200)
        con_score = []
        for p in ideas:
            s = get_score(p.get("properties", {}))
            if s is not None:
                con_score.append((s, p))

        con_score.sort(key=lambda x: x[0], reverse=True)
        top5 = con_score[:5]

        if not top5:
            await update.message.reply_text("❌ Ninguna idea tiene ScoreGen.")
            return

        msg = "🏆 <b>Top 5 Ideas</b>\n\n"
        medallas = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"]
        for i, (s, p) in enumerate(top5):
            props  = p.get("properties", {})
            nombre = get_txt(props, "Name") or "Sin nombre"
            link   = f"https://notion.so/{p['id'].replace('-', '')}"
            msg   += f"{medallas[i]} <b>{nombre}</b> — {s}/100\n<a href='{link}'>Ver</a>\n\n"

        await update.message.reply_text(
            msg, parse_mode="HTML", disable_web_page_preview=True
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return

    await update.message.reply_text("📊 Consultando...")

    try:
        ideas   = get_ideas(200)
        total   = len(ideas)
        con_inf = 0
        scores  = []

        for p in ideas:
            props = p.get("properties", {})
            if props.get("Informe Completo", {}).get("rich_text"):
                con_inf += 1
            s = get_score(props)
            if s is not None:          # ← FIX: is not None (no "if s:")
                scores.append(s)

        avg         = round(sum(scores) / len(scores), 1) if scores else 0
        sin_informe = total - con_inf

        try:
            from agents.knowledge_base import get_stats
            kb = get_stats()
            kb_txt = (
                f"\n\n🧠 <b>Auto-aprendizaje:</b>\n"
                f"  Analizadas: {kb['total']} | Exitosas: {kb['exitosas']}\n"
                f"  Mejor tipo: {kb['mejor_tipo']}\n"
                f"  Mejor vertical: {kb['mejor_vertical']}\n\n"
                f"<i>Usa /insights para ver detalles</i>"
            )
        except Exception:
            kb_txt = "\n\n<i>KB no disponible. Ejecuta poblar_knowledge_base.py</i>"

        await update.message.reply_text(
            f"📊 <b>Estado del Sistema</b>\n\n"
            f"💡 Ideas totales: <b>{total}</b>\n"
            f"📝 Con informe: <b>{con_inf}</b>\n"
            f"⏳ Sin informe: <b>{sin_informe}</b>\n"
            f"📈 Score promedio: <b>{avg}/100</b>"
            + kb_txt,
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error: {e}")


async def cmd_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return

    try:
        from agents.knowledge_base import get_stats, get_contexto_para_generador
        kb  = get_stats()
        ctx = get_contexto_para_generador()

        if kb["total"] < 5:
            await update.message.reply_text(
                f"🧠 <b>Auto-aprendizaje</b>\n\n"
                f"Ideas analizadas: {kb['total']}/5\n"
                f"⚠️ Necesitas al menos 5 ideas con score.\n\n"
                f"Ejecuta en PowerShell:\n"
                f"<code>python poblar_knowledge_base.py</code>",
                parse_mode="HTML",
            )
            return

        await update.message.reply_text(
            f"🧠 <b>Insights del Sistema</b>\n\n"
            f"📚 Ideas analizadas: <b>{kb['total']}</b>\n"
            f"⭐ Con score alto (>75): <b>{kb['exitosas']}</b>\n"
            f"🏆 Mejor tipo de producto: <b>{kb['mejor_tipo']}</b>\n"
            f"🎯 Mejor vertical/mercado: <b>{kb['mejor_vertical']}</b>\n\n"
            f"<b>Recomendaciones:</b>\n{ctx}",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Error KB: {e}")


async def cmd_aprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    if not context.args:
        await update.message.reply_text("❌ Uso: /aprobar &lt;nombre&gt;", parse_mode="HTML")
        return

    buscar = " ".join(context.args).lower()
    ideas  = get_ideas(200)
    encontrada = next(
        (p for p in ideas if buscar in get_txt(p.get("properties", {}), "Name").lower()),
        None,
    )
    if not encontrada:
        await update.message.reply_text(f"❌ No encontré '{buscar}'")
        return

    props  = encontrada.get("properties", {})
    nombre = get_txt(props, "Name")
    ok     = añadir_tag(encontrada["id"], props, "Aprobada", quitar_tag="Rechazada")
    msg    = f"✅ <b>{nombre}</b> marcada como <b>Aprobada</b>" if ok else "❌ Error al actualizar"
    await update.message.reply_text(msg, parse_mode="HTML")


async def cmd_rechazar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    if not context.args:
        await update.message.reply_text("❌ Uso: /rechazar &lt;nombre&gt;", parse_mode="HTML")
        return

    buscar = " ".join(context.args).lower()
    ideas  = get_ideas(200)
    encontrada = next(
        (p for p in ideas if buscar in get_txt(p.get("properties", {}), "Name").lower()),
        None,
    )
    if not encontrada:
        await update.message.reply_text(f"❌ No encontré '{buscar}'")
        return

    props  = encontrada.get("properties", {})
    nombre = get_txt(props, "Name")
    ok     = añadir_tag(encontrada["id"], props, "Rechazada", quitar_tag="Aprobada")
    msg    = f"🚫 <b>{nombre}</b> marcada como <b>Rechazada</b>" if ok else "❌ Error al actualizar"
    await update.message.reply_text(msg, parse_mode="HTML")


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("[Bot] Iniciando IdeaValidator Bot...")

    # Notificar por Telegram que el bot arrancó
    if TOKEN and CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": "🚀 <b>IdeaValidator Bot iniciado</b>\nUsa /ayuda para ver comandos.",
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
        except Exception:
            pass

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",    cmd_ayuda))
    app.add_handler(CommandHandler("ayuda",    cmd_ayuda))
    app.add_handler(CommandHandler("nueva",    cmd_nueva))
    app.add_handler(CommandHandler("top5",     cmd_top5))
    app.add_handler(CommandHandler("estado",   cmd_estado))
    app.add_handler(CommandHandler("insights", cmd_insights))
    app.add_handler(CommandHandler("aprobar",  cmd_aprobar))
    app.add_handler(CommandHandler("rechazar", cmd_rechazar))

    print("[Bot] ✅ Escuchando comandos...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
