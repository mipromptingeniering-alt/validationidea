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


# â”€â”€ Helpers Notion â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
        r    = requests.post(url, headers=_h(), json=body, timeout=30)
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
    s = get_num(props, "ScoreGen")
    if s is None:
        s = get_num(props, "Score")
    return s


# â”€â”€ Helper LLM â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

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
            "ScoreGen":    {"number": score},
            "Date":        {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
        },
    }
    r = requests.post("https://api.notion.com/v1/pages",
                      headers=_h(), json=payload, timeout=30)
    r.raise_for_status()
    return f"https://notion.so/{r.json()['id'].replace('-', '')}"


def aÃ±adir_tag(page_id: str, props: dict, nuevo_tag: str, quitar_tag: str = "") -> bool:
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


# â”€â”€ Handlers â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def solo_mi_chat(update: Update) -> bool:
    return str(update.effective_chat.id) == str(CHAT_ID)


async def cmd_ayuda(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    await update.message.reply_text(
        "ðŸ¤– <b>IdeaValidator Bot</b>\n\n"
        "<b>Comandos:</b>\n"
        "/nueva &lt;tema&gt; â€” Genera idea sobre ese tema\n"
        "/top5 â€” Top 5 ideas por ScoreGen\n"
        "/top5money â€” Top 5 ideas por ScoreMoney ðŸ’°\n"
        "/estado â€” EstadÃ­sticas del sistema\n"
        "/insights â€” QuÃ© tipos de ideas funcionan mejor\n"
        "/logs â€” Ãšltimas 20 lÃ­neas del log de hoy ðŸ“‹\n"
        "/exportar â€” Newsletter top 10 ideas en Markdown ðŸ“°\n"
        "/aprobar &lt;nombre&gt; â€” Marca idea como aprobada\n"
        "/rechazar &lt;nombre&gt; â€” Marca idea como rechazada\n"
        "/ayuda â€” Esta ayuda",
        parse_mode="HTML",
    )


async def cmd_nueva(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    if not context.args:
        await update.message.reply_text(
            "âŒ Uso: /nueva &lt;tema&gt;\nEjemplo: /nueva automatizaciÃ³n para freelancers",
            parse_mode="HTML"
        )
        return

    tema = " ".join(context.args)
    await update.message.reply_text(f"ðŸ¤– Generando idea sobre: <b>{tema}</b>...", parse_mode="HTML")

    prompt = f"""Genera una idea de negocio digital sobre el tema: "{tema}"

Responde ÃšNICAMENTE en JSON exacto (sin markdown ni texto extra):
{{
  "nombre": "Nombre del producto (mÃ¡x 3 palabras)",
  "problema": "Problema que resuelve en 2 frases con datos",
  "solucion": "CÃ³mo funciona exactamente en 2 frases",
  "descripcion": "DescripciÃ³n en 1 frase estilo tweet de lanzamiento",
  "valor": "Propuesta de valor Ãºnica frente a alternativas",
  "target": "Cliente ideal: perfil concreto, edad, ocupaciÃ³n, dolor",
  "negocio": "Precio en euros y modelo de monetizaciÃ³n concreto",
  "score": 78
}}"""

    try:
        texto = llamar_groq(prompt, max_tokens=600)
        texto = texto.strip()
        if "```" in texto:
            for parte in texto.split("```"):
                parte = parte.strip().lstrip("json").strip()
                if parte.startswith("{"):
                    texto = parte
                    break

        data        = json.loads(texto)
        nombre      = data.get("nombre",      "Nueva Idea")
        problema    = data.get("problema",    "")
        solucion    = data.get("solucion",    "")
        descripcion = data.get("descripcion", "")
        valor       = data.get("valor",       "")
        target      = data.get("target",      "")
        negocio     = data.get("negocio",     "")
        score       = int(data.get("score",   70))

        notion_url = crear_idea_notion(
            nombre, problema, solucion, descripcion, valor, target, negocio, score
        )

        try:
            from agents.knowledge_base import aprender
            aprender({"nombre": nombre, "tipo": "Nueva", "vertical": target}, score)
        except Exception:
            pass

        await update.message.reply_text(
            f"ðŸ’¡ <b>{nombre}</b>\n\n"
            f"ðŸ“Œ <b>Problema:</b> {problema}\n"
            f"âœ… <b>SoluciÃ³n:</b> {solucion}\n"
            f"ðŸ’° <b>Modelo:</b> {negocio}\n"
            f"ðŸ‘¥ <b>Target:</b> {target}\n"
            f"ðŸ“Š <b>Score:</b> {score}/100\n\n"
            f'ðŸ”— <a href="{notion_url}">Ver en Notion</a>',
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    except json.JSONDecodeError:
        await update.message.reply_text("âš ï¸ El LLM no devolviÃ³ JSON vÃ¡lido. Intenta de nuevo.")
    except Exception as e:
        await update.message.reply_text(f"âŒ Error: {e}")


async def cmd_top5(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    await update.message.reply_text("ðŸ” Buscando top 5 por ScoreGen...")
    try:
        ideas     = get_ideas(200)
        con_score = []
        for p in ideas:
            s = get_score(p.get("properties", {}))
            if s is not None:
                con_score.append((s, p))
        con_score.sort(key=lambda x: x[0], reverse=True)
        top5 = con_score[:5]
        if not top5:
            await update.message.reply_text("âŒ Ninguna idea tiene ScoreGen.")
            return
        msg      = "ðŸ† <b>Top 5 â€” ScoreGen</b>\n\n"
        medallas = ["ðŸ¥‡", "ðŸ¥ˆ", "ðŸ¥‰", "4ï¸âƒ£", "5ï¸âƒ£"]
        for i, (s, p) in enumerate(top5):
            props     = p.get("properties", {})
            nombre    = get_txt(props, "Name") or "Sin nombre"
            money     = get_num(props, "ScoreMoney")
            money_txt = f" | ðŸ’°{money}" if money is not None else ""
            link      = f"https://notion.so/{p['id'].replace('-', '')}"
            msg      += f"{medallas[i]} <b>{nombre}</b> â€” {s}/100{money_txt}\n<a href='{link}'>Ver</a>\n\n"
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"âŒ Error: {e}")


async def cmd_top5money(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    await update.message.reply_text("ðŸ’° Buscando top 5 por ScoreMoney...")
    try:
        ideas     = get_ideas(200)
        con_money = []
        for p in ideas:
            props = p.get("properties", {})
            m = get_num(props, "ScoreMoney")
            if m is not None:
                con_money.append((m, p))
        con_money.sort(key=lambda x: x[0], reverse=True)
        top5 = con_money[:5]
        if not top5:
            await update.message.reply_text(
                "âŒ Ninguna idea tiene ScoreMoney aÃºn.\n"
                "Las prÃ³ximas ideas generadas ya incluirÃ¡n este score."
            )
            return
        msg      = "ðŸ’° <b>Top 5 â€” ScoreMoney</b>\n\n"
        medallas = ["ðŸ¥‡", "ðŸ¥ˆ", "ðŸ¥‰", "4ï¸âƒ£", "5ï¸âƒ£"]
        for i, (m, p) in enumerate(top5):
            props   = p.get("properties", {})
            nombre  = get_txt(props, "Name") or "Sin nombre"
            gen     = get_score(props)
            gen_txt = f" | ðŸ“Š{gen}" if gen is not None else ""
            link    = f"https://notion.so/{p['id'].replace('-', '')}"
            msg    += f"{medallas[i]} <b>{nombre}</b> â€” ðŸ’°{m}/100{gen_txt}\n<a href='{link}'>Ver</a>\n\n"
        await update.message.reply_text(msg, parse_mode="HTML", disable_web_page_preview=True)
    except Exception as e:
        await update.message.reply_text(f"âŒ Error: {e}")


async def cmd_estado(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    await update.message.reply_text("ðŸ“Š Consultando...")
    try:
        ideas   = get_ideas(200)
        total   = len(ideas)
        con_inf = 0
        scores  = []
        moneys  = []
        for p in ideas:
            props = p.get("properties", {})
            if props.get("Informe Completo", {}).get("rich_text"):
                con_inf += 1
            s = get_score(props)
            if s is not None:
                scores.append(s)
            m = get_num(props, "ScoreMoney")
            if m is not None:
                moneys.append(m)

        avg       = round(sum(scores) / len(scores), 1) if scores else 0
        avg_money = round(sum(moneys) / len(moneys), 1) if moneys else 0

        try:
            from agents.knowledge_base import get_stats
            kb     = get_stats()
            kb_txt = (
                f"\n\nðŸ§  <b>Auto-aprendizaje:</b>\n"
                f"  Analizadas: {kb['total']} | Exitosas: {kb['exitosas']}\n"
                f"  Mejor tipo: {kb['mejor_tipo']}\n"
                f"  Mejor vertical: {kb['mejor_vertical']}\n\n"
                f"<i>Usa /insights para ver detalles</i>"
            )
        except Exception:
            kb_txt = "\n\n<i>KB no disponible</i>"

        money_txt = f"\nðŸ’° ScoreMoney promedio: <b>{avg_money}/100</b>" if moneys else ""

        await update.message.reply_text(
            f"ðŸ“Š <b>Estado del Sistema</b>\n\n"
            f"ðŸ’¡ Ideas totales: <b>{total}</b>\n"
            f"ðŸ“ Con informe: <b>{con_inf}</b>\n"
            f"â³ Sin informe: <b>{total - con_inf}</b>\n"
            f"ðŸ“ˆ ScoreGen promedio: <b>{avg}/100</b>"
            f"{money_txt}"
            + kb_txt,
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"âŒ Error: {e}")


async def cmd_insights(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    try:
        from agents.knowledge_base import get_stats, get_contexto_para_generador
        kb  = get_stats()
        ctx = get_contexto_para_generador()
        if kb["total"] < 5:
            await update.message.reply_text(
                f"ðŸ§  <b>Auto-aprendizaje</b>\n\nIdeas analizadas: {kb['total']}/5\n"
                f"âš ï¸ Necesitas al menos 5 ideas con score.",
                parse_mode="HTML",
            )
            return
        await update.message.reply_text(
            f"ðŸ§  <b>Insights del Sistema</b>\n\n"
            f"ðŸ“š Ideas analizadas: <b>{kb['total']}</b>\n"
            f"â­ Con score alto (>75): <b>{kb['exitosas']}</b>\n"
            f"ðŸ† Mejor tipo: <b>{kb['mejor_tipo']}</b>\n"
            f"ðŸŽ¯ Mejor vertical: <b>{kb['mejor_vertical']}</b>\n\n"
            f"<b>Recomendaciones P6:</b>\n{ctx}",
            parse_mode="HTML",
        )
    except Exception as e:
        await update.message.reply_text(f"âŒ Error KB: {e}")


async def cmd_logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    try:
        import pytz
        zona     = pytz.timezone("Europe/Madrid")
        hoy      = datetime.now(zona).strftime("%Y-%m-%d")
        log_path = os.path.join("data", "logs", f"{hoy}.log")

        if not os.path.exists(log_path):
            await update.message.reply_text(
                f"ðŸ“‹ No hay log para hoy ({hoy}).\n"
                f"Se crearÃ¡ cuando el monitor genere la prÃ³xima idea."
            )
            return

        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            lineas = f.readlines()

        ultimas = lineas[-20:]
        if not ultimas:
            await update.message.reply_text("ðŸ“‹ Log vacÃ­o por ahora.")
            return

        texto = "".join(ultimas).strip()
        if len(texto) > 3800:
            texto = "...\n" + texto[-3800:]

        await update.message.reply_text(
            f"ðŸ“‹ <b>Log {hoy} â€” Ãºltimas {len(ultimas)} lÃ­neas</b>\n\n"
            f"<pre>{texto}</pre>",
            parse_mode="HTML"
        )
    except Exception as e:
        await update.message.reply_text(f"âŒ Error leyendo logs: {e}")


async def cmd_exportar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """P8 â€” Genera newsletter Markdown con top 10 ideas y la envÃ­a como archivo."""
    if not solo_mi_chat(update):
        return

    await update.message.reply_text("ðŸ“° Generando newsletter con top 10 ideas...")

    try:
        import pytz
        zona   = pytz.timezone("Europe/Madrid")
        ahora  = datetime.now(zona)
        semana = ahora.strftime("%Y-semana%W")
        fecha  = ahora.strftime("%d/%m/%Y")

        # Obtener todas las ideas y ordenar por ScoreGen
        ideas     = get_ideas(200)
        con_score = []
        for p in ideas:
            props = p.get("properties", {})
            s = get_score(props)
            if s is not None:
                con_score.append((s, p))
        con_score.sort(key=lambda x: x[0], reverse=True)
        top10 = con_score[:10]

        if not top10:
            await update.message.reply_text("âŒ No hay ideas con score para exportar.")
            return

        # Construir contenido Markdown
        lineas = [
            f"# ðŸ’¡ ValidationIdea â€” Newsletter {semana}",
            f"",
            f"**Fecha:** {fecha}  ",
            f"**Ideas analizadas esta semana:** {len(ideas)}  ",
            f"**Top 10 por ScoreGen**",
            f"",
            f"---",
            f"",
        ]

        medallas = ["ðŸ¥‡", "ðŸ¥ˆ", "ðŸ¥‰", "4ï¸âƒ£", "5ï¸âƒ£", "6ï¸âƒ£", "7ï¸âƒ£", "8ï¸âƒ£", "9ï¸âƒ£", "ðŸ”Ÿ"]

        for i, (score, p) in enumerate(top10):
            props       = p.get("properties", {})
            nombre      = get_txt(props, "Name")  or "Sin nombre"
            problema    = get_txt(props, "Problem")   or "â€”"
            solucion    = get_txt(props, "Solution")  or "â€”"
            negocio     = get_txt(props, "Business")  or "â€”"
            target      = get_txt(props, "Target")    or "â€”"
            score_viral = get_num(props, "ScoreViral")
            score_money = get_num(props, "ScoreMoney")
            link        = f"https://notion.so/{p['id'].replace('-', '')}"

            score_extra = ""
            if score_viral is not None:
                score_extra += f" | ðŸš€ Viral: {score_viral}"
            if score_money is not None:
                score_extra += f" | ðŸ’° Money: {score_money}"

            lineas += [
                f"## {medallas[i]} {nombre}",
                f"",
                f"**Score:** {score}/100{score_extra}  ",
                f"**Problema:** {problema[:300]}  ",
                f"**SoluciÃ³n:** {solucion[:300]}  ",
                f"**Modelo de negocio:** {negocio[:200]}  ",
                f"**Cliente objetivo:** {target[:200]}  ",
                f"**Ver informe completo:** [{nombre}]({link})",
                f"",
                f"---",
                f"",
            ]

        # Pie de pÃ¡gina
        lineas += [
            f"*Generado automÃ¡ticamente por ValidationIdea â€” sistema autÃ³nomo de ideas de negocio*",
            f"",
            f"*Â¿Quieres recibir esto cada semana? SuscrÃ­bete por 9â‚¬/mes.*",
        ]

        contenido = "\n".join(lineas)

        # Guardar en data/exports/
        os.makedirs(os.path.join("data", "exports"), exist_ok=True)
        ruta = os.path.join("data", "exports", f"{semana}.md")
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(contenido)

        # Enviar archivo por Telegram
        with open(ruta, "rb") as f:
            await update.message.reply_document(
                document=f,
                filename=f"validationidea-{semana}.md",
                caption=(
                    f"ðŸ“° <b>Newsletter {semana}</b>\n"
                    f"Top {len(top10)} ideas Â· {fecha}\n\n"
                    f"Archivo Markdown listo para publicar o enviar a suscriptores."
                ),
                parse_mode="HTML"
            )

    except Exception as e:
        await update.message.reply_text(f"âŒ Error generando newsletter: {e}")


async def cmd_aprobar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    if not context.args:
        await update.message.reply_text("âŒ Uso: /aprobar &lt;nombre&gt;", parse_mode="HTML")
        return
    buscar     = " ".join(context.args).lower()
    ideas      = get_ideas(200)
    encontrada = next(
        (p for p in ideas if buscar in get_txt(p.get("properties", {}), "Name").lower()), None
    )
    if not encontrada:
        await update.message.reply_text(f"âŒ No encontrÃ© '{buscar}'")
        return
    props  = encontrada.get("properties", {})
    nombre = get_txt(props, "Name")
    ok     = aÃ±adir_tag(encontrada["id"], props, "Aprobada", quitar_tag="Rechazada")
    await update.message.reply_text(
        f"âœ… <b>{nombre}</b> marcada como <b>Aprobada</b>" if ok else "âŒ Error al actualizar",
        parse_mode="HTML"
    )


async def cmd_rechazar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not solo_mi_chat(update):
        return
    if not context.args:
        await update.message.reply_text("âŒ Uso: /rechazar &lt;nombre&gt;", parse_mode="HTML")
        return
    buscar     = " ".join(context.args).lower()
    ideas      = get_ideas(200)
    encontrada = next(
        (p for p in ideas if buscar in get_txt(p.get("properties", {}), "Name").lower()), None
    )
    if not encontrada:
        await update.message.reply_text(f"âŒ No encontrÃ© '{buscar}'")
        return
    props  = encontrada.get("properties", {})
    nombre = get_txt(props, "Name")
    ok     = aÃ±adir_tag(encontrada["id"], props, "Rechazada", quitar_tag="Aprobada")
    await update.message.reply_text(
        f"ðŸš« <b>{nombre}</b> marcada como <b>Rechazada</b>" if ok else "âŒ Error al actualizar",
        parse_mode="HTML"
    )


# â”€â”€ Main â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€

def main():
    print("[Bot] Iniciando IdeaValidator Bot...")

    if TOKEN and CHAT_ID:
        try:
            requests.post(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                json={
                    "chat_id": CHAT_ID,
                    "text": "ðŸš€ <b>IdeaValidator Bot iniciado</b>\nUsa /ayuda para ver comandos.",
                    "parse_mode": "HTML",
                },
                timeout=10,
            )
        except Exception:
            pass

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start",     cmd_ayuda))
    app.add_handler(CommandHandler("ayuda",     cmd_ayuda))
    app.add_handler(CommandHandler("nueva",     cmd_nueva))
    app.add_handler(CommandHandler("top5",      cmd_top5))
    app.add_handler(CommandHandler("top5money", cmd_top5money))
    app.add_handler(CommandHandler("estado",    cmd_estado))
    app.add_handler(CommandHandler("insights",  cmd_insights))
    app.add_handler(CommandHandler("logs",      cmd_logs))
    app.add_handler(CommandHandler("exportar",  cmd_exportar))
    app.add_handler(CommandHandler("aprobar",   cmd_aprobar))
    app.add_handler(CommandHandler("rechazar",  cmd_rechazar))

    print("[Bot] âœ… Escuchando comandos...")
    app.run_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
