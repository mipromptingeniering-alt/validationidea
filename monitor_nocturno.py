import os, sys, json, time, subprocess, threading, re
from datetime import datetime, timedelta

os.environ["PYTHONUTF8"] = "1"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID",   "")
INTERVALO_MIN  = int(os.environ.get("INTERVALO_MINUTOS", "30"))

# ── Telegram helpers ────────────────────────────────────────────────────────

def _post(endpoint, payload, timeout=15):
    import urllib.request
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"Telegram error {endpoint}: {e}")
        return {}

def enviar(chat_id, texto, reply_markup=None):
    texto = str(texto)[:4096]
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _post("sendMessage", payload)

def get_updates(offset=0):
    return _post("getUpdates", {"offset": offset, "timeout": 10, "limit": 5}, timeout=15)

# ── Formateador de idea ─────────────────────────────────────────────────────

def _fmt_idea(idea):
    scores  = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
    score   = scores.get("score_total", 0)
    nombre  = idea.get("nombre", "?")
    tagline = idea.get("tagline", "")

    if   score >= 90: emoji = "💎"
    elif score >= 85: emoji = "⭐"
    elif score >= 80: emoji = "🔥"
    elif score >= 75: emoji = "✅"
    else:             emoji = "💡"

    problema  = str(idea.get("problema", ""))[:120]
    herr      = str(idea.get("herramienta_ia_clave", ""))[:80]
    monetiz   = ""
    if isinstance(idea.get("estrategia_monetizacion"), dict):
        monetiz = str(idea["estrategia_monetizacion"].get("semana1",""))[:120]
    hipotesis = ""
    if isinstance(idea.get("hipotesis_testeable"), dict):
        hipotesis = str(idea["hipotesis_testeable"].get("experimento_48h",""))[:120]

    veredicto = ""
    recom     = ""
    if isinstance(idea.get("scoring_critico"), dict):
        veredicto = str(idea["scoring_critico"].get("veredicto",""))[:120]
        recom     = str(idea["scoring_critico"].get("recomendacion","")).upper()

    notion_url = idea.get("notion_url","")

    lineas = [
        f"{emoji} <b>{nombre} — {score}/100</b>",
        f"<i>\"{tagline}\"</i>",
        "",
        f"❗ <b>Problema:</b> {problema}",
        f"🤖 <b>IA clave:</b> {herr}",
    ]
    if monetiz:
        lineas.append(f"💰 <b>Semana 1:</b> {monetiz}")
    if hipotesis:
        lineas.append(f"🧪 <b>Test 48h:</b> {hipotesis}")
    if veredicto:
        lineas.append(f"✅ <b>Veredicto YC:</b> {veredicto}")
    if recom:
        lineas.append(f"🏷 <b>Recomendacion:</b> {recom}")
    if notion_url:
        lineas.append(f"\n📋 <a href=\"{notion_url}\">Ver informe completo en Notion</a>")

    return "\n".join(lineas)

def _botones_feedback(idea_nombre):
    safe = idea_nombre.replace(" ","_")[:40]
    return {
        "inline_keyboard": [[
            {"text": "👍 Buena idea", "callback_data": f"like_{safe}"},
            {"text": "👎 Mala idea",  "callback_data": f"dislike_{safe}"},
        ]]
    }

# ── Ejecucion de batch ──────────────────────────────────────────────────────

def ejecutar_idea(tema="", chat_id=None):
    if not chat_id:
        chat_id = TELEGRAM_CHAT
    env = os.environ.copy()
    env["IDEA_TOPIC"] = tema
    t0 = time.time()
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, text=True,
            timeout=420,           # 7 minutos — cubre 3 modelos * 2 reintentos * 20s + generacion
            env=env,
            encoding="utf-8", errors="replace",
        )
        salida = (resultado.stdout or "") + (resultado.stderr or "")
        ok     = resultado.returncode == 0
    except subprocess.TimeoutExpired:
        salida = "TIMEOUT"
        ok     = False
    except Exception as e:
        salida = str(e)
        ok     = False

    elapsed = round(time.time() - t0)

    if ok:
        idea_data = _extraer_datos_salida(salida)
        nombre    = idea_data.get("nombre", "Nueva idea")
        score     = idea_data.get("score",  0)
        notion    = idea_data.get("notion_url", "")
        tagline   = idea_data.get("tagline", "")
        herr      = idea_data.get("herramienta_ia", "")
        hipotesis = idea_data.get("hipotesis", "")
        monetiz   = idea_data.get("monetiz_s1", "")
        veredicto = idea_data.get("veredicto_critico", "")
        recom     = idea_data.get("recomendacion", "").upper()

        if   score >= 90: emoji = "💎"
        elif score >= 85: emoji = "⭐"
        elif score >= 80: emoji = "🔥"
        elif score >= 75: emoji = "✅"
        else:             emoji = "💡"

        lineas = [
            f"{emoji} <b>{nombre} — {score}/100</b>",
            f"<i>\"{tagline}\"</i>",
            "",
        ]
        if herr:      lineas.append(f"🤖 <b>IA clave:</b> {herr}")
        if monetiz:   lineas.append(f"💰 <b>Semana 1:</b> {monetiz}")
        if hipotesis: lineas.append(f"🧪 <b>Test 48h:</b> {hipotesis}")
        if veredicto: lineas.append(f"✅ <b>Veredicto YC:</b> {veredicto}")
        if recom:     lineas.append(f"🏷 <b>Recomendacion:</b> {recom}")
        if notion:    lineas.append(f"\n📋 <a href=\"{notion}\">Ver informe completo en Notion</a>")
        lineas.append(f"\n⏱ Generada en {elapsed}s")

        msg  = "\n".join(lineas)
        mkup = _botones_feedback(nombre)
        enviar(chat_id, msg, reply_markup=mkup)
    else:
        if "TIMEOUT" in salida:
            enviar(chat_id, f"⏰ Timeout (>{elapsed}s) — se reintentara automaticamente en 30 min.")
        else:
            # Extraer linea de error relevante
            error_lines = [l for l in salida.split("\n") if "❌" in l or "Error" in l or "error" in l.lower()]
            error_msg   = error_lines[-1][:200] if error_lines else salida[-200:]
            enviar(chat_id, f"❌ Error generando idea\n\n{error_msg}\n\nUsa /debug.")

    return ok

def _extraer_datos_salida(salida):
    def _get(tag):
        m = re.search(rf"^{tag}:(.+)$", salida, re.MULTILINE)
        return m.group(1).strip() if m else ""
    score_str = _get("SCORE_FINAL")
    try:   score = float(score_str)
    except: score = 0
    m_nombre = re.search(r"✅ Sincronizada: (.+)$", salida, re.MULTILINE)
    nombre   = m_nombre.group(1).strip() if m_nombre else ""
    m_notion = re.search(r"NOTION_URL:(.+)$", salida, re.MULTILINE)
    notion   = m_notion.group(1).strip() if m_notion else ""
    return {
        "nombre":           nombre,
        "score":            score,
        "notion_url":       notion,
        "tagline":          _get("TAGLINE"),
        "herramienta_ia":   _get("HERRAMIENTA_IA"),
        "hipotesis":        _get("HIPOTESIS"),
        "monetiz_s1":       _get("MONETIZ_S1"),
        "veredicto_critico":_get("VEREDICTO_CRITICO"),
        "recomendacion":    _get("RECOMENDACION"),
    }

# ── Debug ───────────────────────────────────────────────────────────────────

def ejecutar_debug(chat_id):
    enviar(chat_id, "🔍 Ejecutando diagnóstico — espera 60s...")
    env = os.environ.copy()
    env["IDEA_TOPIC"] = "debug_test"
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, text=True,
            timeout=420, env=env,
            encoding="utf-8", errors="replace",
        )
        salida = (resultado.stdout or "") + (resultado.stderr or "")
        ok     = resultado.returncode == 0
    except subprocess.TimeoutExpired:
        salida = "TIMEOUT"
        ok     = False
    except Exception as e:
        salida = str(e)
        ok     = False

    datos    = _extraer_datos_salida(salida)
    nombre   = datos.get("nombre","")
    score    = datos.get("score",0)
    notion   = datos.get("notion_url","")
    veredicto= datos.get("veredicto_critico","")

    ok_str   = "✅ 0" if ok else "❌ 1"
    nom_str  = f"✅ {nombre}" if nombre else "❌ No encontrada"
    sco_str  = f"✅ {score}" if score else "❌"
    ver_str  = f"✅ {veredicto[:60]}" if veredicto else "❌"
    not_str  = f"✅ {notion[:60]}" if notion else "❌"

    output_truncado = salida[-1200:] if len(salida) > 1200 else salida

    msg = (
        f"🐛 Debug run_batch.py\n"
        f"Codigo salida: {ok_str}\n"
        f"Idea: {nom_str}\n"
        f"Score: {sco_str}\n"
        f"Veredicto: {ver_str}\n"
        f"Notion: {not_str}\n\n"
        f"Output completo:\n"
        f"{'='*50}\n"
        f"{output_truncado}"
    )
    enviar(chat_id, msg[:4096])

# ── Comandos KB ─────────────────────────────────────────────────────────────

def cmd_top(chat_id):
    try:
        from agents.knowledge_base import get_top_ideas
        ideas = get_top_ideas(5)
        if not ideas:
            enviar(chat_id, "📭 No hay ideas aun. Usa /idea [tema]")
            return
        lineas = ["🏆 <b>Top 5 mejores ideas</b>\n"]
        for i, idea in enumerate(ideas, 1):
            s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            n = idea.get("nombre","?")
            t = idea.get("tagline","")[:60]
            lineas.append(f"{i}. <b>{n}</b> — {s}/100\n   <i>{t}</i>")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_stats(chat_id):
    try:
        from agents.knowledge_base import get_stats
        s = get_stats()
        msg = (
            f"📊 <b>Estadísticas KB</b>\n\n"
            f"Total ideas: {s.get('total_ideas',0)}\n"
            f"Score promedio: {s.get('score_promedio',0)}/100\n"
            f"Mejor idea: {s.get('mejor_idea','?')} ({s.get('mejor_score',0)}/100)\n"
            f"Ideas esta semana: {s.get('ideas_semana',0)}\n"
            f"Verticales top: {', '.join(s.get('verticales_top',[])[:3]) or 'N/A'}"
        )
        enviar(chat_id, msg)
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_ranking(chat_id):
    try:
        from agents.knowledge_base import get_top_ejecutables
        ideas = get_top_ejecutables(5)
        if not ideas:
            enviar(chat_id, "📭 No hay ideas. Usa /idea [tema]")
            return
        lineas = ["🚀 <b>Top 5 más ejecutables HOY</b>\n"]
        for i, idea in enumerate(ideas, 1):
            scores = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
            ej     = scores.get("ejecutabilidad", 0)
            sc     = scores.get("score_total", 0)
            n      = idea.get("nombre","?")
            herr   = idea.get("herramienta_ia_clave","")[:40]
            sem1   = ""
            if isinstance(idea.get("estrategia_monetizacion"),dict):
                sem1 = str(idea["estrategia_monetizacion"].get("semana1",""))[:80]
            lineas.append(f"{i}. <b>{n}</b> — Ejecutabilidad: {ej}/100 | Score: {sc}/100")
            if herr: lineas.append(f"   🤖 {herr}")
            if sem1: lineas.append(f"   💰 {sem1}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_ejecutar(chat_id, nombre_idea):
    try:
        from agents.knowledge_base import buscar_idea
        idea = buscar_idea(nombre_idea)
        if not idea:
            enviar(chat_id, f"❌ No encontre '{nombre_idea}'. Usa /buscar [palabra]")
            return
        pm = idea.get("prompt_mvp", {})
        if isinstance(pm, str):
            try:   pm = json.loads(pm)
            except: pm = {}
        if isinstance(pm, dict):
            meta        = pm.get("meta",{}) if isinstance(pm.get("meta"),dict) else {}
            ia_rec      = meta.get("ia_recomendada","Claude 3.5 Sonnet en Cursor")
            sys_prompt  = pm.get("system_prompt","")[:400]
            script_cli  = pm.get("primer_cliente_script","")[:200]
            pasos       = pm.get("instrucciones_paso_a_paso",[])[:5]
            pasos_str   = "\n".join(f"  {p}" for p in pasos)
            msg = (
                f"🛠️ <b>Prompt MVP: {idea.get('nombre','')}</b>\n\n"
                f"🤖 IA: {ia_rec}\n\n"
                f"📝 System prompt:\n<code>{sys_prompt}</code>\n\n"
                f"🚀 Pasos:\n{pasos_str}\n\n"
                f"💰 Primer cliente:\n{script_cli}"
            )
        else:
            msg = f"🛠️ {idea.get('nombre','')}: Sin prompt MVP generado aun."
        enviar(chat_id, msg[:4096])
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_buscar(chat_id, query):
    try:
        from agents.knowledge_base import buscar_ideas
        ideas = buscar_ideas(query, limit=5)
        if not ideas:
            enviar(chat_id, f"🔍 No encontre ideas con '{query}'")
            return
        lineas = [f"🔍 <b>Resultados para '{query}'</b>\n"]
        for idea in ideas:
            s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            n = idea.get("nombre","?")
            t = idea.get("tagline","")[:60]
            lineas.append(f"• <b>{n}</b> — {s}/100\n  <i>{t}</i>")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_tendencias(chat_id):
    try:
        from agents.trend_scout import get_tendencias, actualizar_tendencias
        actualizar_tendencias()
        trends = get_tendencias()[:12]
        if not trends:
            enviar(chat_id, "📭 No hay tendencias disponibles.")
            return
        lineas = ["🌐 <b>Tendencias tech ahora</b>\n"]
        for t in trends:
            lineas.append(f"• {str(t)[:100]}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_cola(chat_id):
    ruta = "data/cola_pendientes.csv"
    if not os.path.exists(ruta):
        enviar(chat_id, "✅ Cola vacia — todas las ideas en Notion.")
        return
    try:
        import csv
        with open(ruta, "r", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            enviar(chat_id, "✅ Cola vacia.")
            return
        lineas = [f"🔄 <b>Cola pendientes Notion: {len(rows)}</b>\n"]
        for r in rows[-5:]:
            lineas.append(f"• {r.get('nombre_idea','?')} — {r.get('error','?')[:60]}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

def cmd_aprender(chat_id):
    enviar(chat_id, "🧠 Ejecutando aprendizaje ahora...")
    try:
        from agents.weekly_learner import analizar_y_aprender
        r = analizar_y_aprender()
        pesos = r.get("nuevos_pesos", {})
        msg = (
            f"✅ Aprendizaje completado\n\n"
            f"Ciclo {r.get('ciclo',0)} completado\n"
            f"{r.get('total_ideas',0)} ideas | {r.get('ideas_exitosas',0)} exitosas ({r.get('pct_exito',0)}%)\n"
            f"Score promedio: {r.get('score_anterior',0)} -> Objetivo nuevo: {r.get('score_objetivo',0)}\n"
            f"Verticales TOP: {', '.join(pesos.get('verticales_preferidas',[])[:3]) or 'N/A'}\n"
            f"Verticales penalizadas: {', '.join(pesos.get('verticales_penalizadas',[])[:3]) or 'ninguna'}\n"
            f"Tags exitosos: {', '.join(pesos.get('tags_exitosos',[])[:5]) or 'N/A'}\n"
            f"IA tools top: {', '.join(pesos.get('ia_tools_top',[])[:3]) or 'N/A'}\n"
            f"Temperatura: {pesos.get('temperatura_groq',0.85)} | Umbral dup: {pesos.get('umbral_duplicado',0.38)}"
        )
        enviar(chat_id, msg)
    except Exception as e:
        enviar(chat_id, f"❌ Error aprendizaje: {e}")

def cmd_status(chat_id):
    try:
        from agents.knowledge_base import get_stats
        s = get_stats()
        ahora = datetime.now().strftime("%d/%m/%Y %H:%M")
        msg = (
            f"📊 <b>Estado ValidationIdea v5</b>\n"
            f"Hora: {ahora}\n\n"
            f"KB: {s.get('total_ideas',0)} ideas | Promedio: {s.get('score_promedio',0)}/100\n"
            f"Mejor: {s.get('mejor_idea','?')} ({s.get('mejor_score',0)}/100)\n\n"
            f"✅ Monitor activo — ideas cada {INTERVALO_MIN} min\n"
            f"✅ Groq modelos: llama-3.3-70b + llama-4-scout + llama-3.1-8b\n"
            f"✅ Notion: {'configurado' if os.environ.get('NOTION_TOKEN') else '❌ sin token'}\n"
            f"✅ Scoring doble: generador + critico YC"
        )
        enviar(chat_id, msg)
    except Exception as e:
        enviar(chat_id, f"❌ Error: {e}")

# ── Feedback ─────────────────────────────────────────────────────────────────

def procesar_feedback(callback_data, chat_id, mensaje_id):
    try:
        from agents.knowledge_base import registrar_feedback
    except ImportError:
        return
    try:
        if callback_data.startswith("like_"):
            nombre = callback_data[5:].replace("_"," ")
            registrar_feedback(nombre, True)
            _post("answerCallbackQuery", {"callback_query_id": mensaje_id, "text": "👍 Feedback registrado"})
        elif callback_data.startswith("dislike_"):
            nombre = callback_data[8:].replace("_"," ")
            registrar_feedback(nombre, False)
            _post("answerCallbackQuery", {"callback_query_id": mensaje_id, "text": "👎 Feedback registrado"})
    except Exception as e:
        print(f"Feedback error: {e}")

# ── Bot loop ─────────────────────────────────────────────────────────────────

def bot_loop():
    offset  = 0
    print("🤖 Bot Telegram arrancado")
    while True:
        try:
            data = get_updates(offset)
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1

                # Callback (feedback 👍👎)
                if "callback_query" in upd:
                    cq      = upd["callback_query"]
                    cb_data = cq.get("data","")
                    cb_id   = cq.get("id","")
                    cb_chat = str(cq["from"]["id"])
                    procesar_feedback(cb_data, cb_chat, cb_id)
                    continue

                msg  = upd.get("message", {})
                text = msg.get("text", "").strip()
                chat = str(msg.get("chat", {}).get("id", ""))
                if not text or not chat:
                    continue

                tl = text.lower()

                if tl in ("/start", "/help"):
                    enviar(chat, (
                        "🤖 ValidationIdea Bot v5\n\n"
                        "Comandos:\n"
                        "💡 /idea [tema] — Genera idea (ej: /idea salud)\n"
                        "📊 /status — Estado del sistema\n"
                        "🏆 /top — Top 5 mejores ideas\n"
                        "📋 /stats — Estadísticas KB\n"
                        "🚀 /ranking — Top 5 más ejecutables HOY\n"
                        "🛠️ /ejecutar [nombre] — Prompt MVP completo\n"
                        "🔍 /buscar [palabra] — Buscar ideas\n"
                        "🌐 /tendencias — Tendencias tech ahora\n"
                        "🔄 /cola — Ideas pendientes Notion\n"
                        "🧠 /aprender — Ejecutar aprendizaje ahora\n"
                        "🐛 /debug — Diagnóstico del sistema\n\n"
                        "Feedback en cada idea: 👍 / 👎\n"
                        "El sistema aprende cada dia a las 08:00 y tras cada idea."
                    ))

                elif tl.startswith("/idea"):
                    tema = text[5:].strip()
                    if not tema:
                        enviar(chat, "💡 Ejemplo: /idea salud\n/idea fintech\n/idea mascotas")
                    else:
                        enviar(chat, f"⏳ Generando idea sobre '{tema}'...\nEspera 60-120s ☕")
                        t = threading.Thread(target=ejecutar_idea, args=(tema, chat), daemon=True)
                        t.start()

                elif tl == "/debug":
                    t = threading.Thread(target=ejecutar_debug, args=(chat,), daemon=True)
                    t.start()

                elif tl == "/top":
                    cmd_top(chat)

                elif tl == "/stats":
                    cmd_stats(chat)

                elif tl == "/status":
                    cmd_status(chat)

                elif tl == "/ranking":
                    cmd_ranking(chat)

                elif tl.startswith("/ejecutar"):
                    nombre = text[9:].strip()
                    if not nombre:
                        enviar(chat, "🛠️ Ejemplo: /ejecutar PetScanAI")
                    else:
                        cmd_ejecutar(chat, nombre)

                elif tl.startswith("/buscar"):
                    q = text[7:].strip()
                    if not q:
                        enviar(chat, "❓ Ejemplo: /buscar fintech")
                    else:
                        cmd_buscar(chat, q)

                elif tl == "/tendencias":
                    cmd_tendencias(chat)

                elif tl == "/cola":
                    cmd_cola(chat)

                elif tl == "/aprender":
                    t = threading.Thread(target=cmd_aprender, args=(chat,), daemon=True)
                    t.start()

                else:
                    # NLP basico
                    if any(x in tl for x in ["genera","idea de","idea sobre"]):
                        for kw in ["genera","idea de","idea sobre","dame una idea"]:
                            if kw in tl:
                                tema = tl.split(kw)[-1].strip()
                                if tema:
                                    enviar(chat, f"⏳ Generando idea sobre '{tema}'...\nEspera 60-120s ☕")
                                    t = threading.Thread(target=ejecutar_idea, args=(tema, chat), daemon=True)
                                    t.start()
                                    break
                    elif any(x in tl for x in ["ranking","ejecutables"]):
                        cmd_ranking(chat)
                    elif any(x in tl for x in ["top","mejores"]):
                        cmd_top(chat)
                    elif any(x in tl for x in ["busca","buscar"]):
                        q = tl.replace("busca","").replace("buscar","").strip()
                        cmd_buscar(chat, q) if q else enviar(chat, "❓ Ejemplo: /buscar fintech")
                    else:
                        enviar(chat, (
                            "🤖 No entendi. Prueba:\n"
                            "• /idea [tema]\n"
                            "• /ranking\n"
                            "• /top\n"
                            "• /buscar [palabra]\n"
                            "O usa /start."
                        ))

        except Exception as e:
            print(f"Bot loop error: {e}")
            time.sleep(5)

# ── Monitor principal ────────────────────────────────────────────────────────

def aprendizaje_diario():
    """Ejecuta aprendizaje todos los dias a las 08:00."""
    while True:
        ahora   = datetime.now()
        proxima = ahora.replace(hour=8, minute=0, second=0, microsecond=0)
        if ahora >= proxima:
            proxima += timedelta(days=1)
        secs = (proxima - ahora).total_seconds()
        time.sleep(secs)
        try:
            from agents.weekly_learner import analizar_y_aprender
            r = analizar_y_aprender()
            if TELEGRAM_CHAT:
                pesos = r.get("nuevos_pesos", {})
                enviar(TELEGRAM_CHAT,
                    f"🧠 Aprendizaje automatico completado\n"
                    f"Ciclo {r.get('ciclo',0)} | {r.get('total_ideas',0)} ideas\n"
                    f"Score objetivo: {r.get('score_objetivo',75)}\n"
                    f"Verticales TOP: {', '.join(pesos.get('verticales_preferidas',[])[:3]) or 'N/A'}"
                )
        except Exception as e:
            print(f"Aprendizaje diario error: {e}")

def main():
    # Migrar KB si es necesario
    try:
        from agents.knowledge_base import migrar_si_necesario, get_stats
        migrar_si_necesario()
        stats = get_stats()
        if TELEGRAM_CHAT:
            enviar(TELEGRAM_CHAT,
                f"🔄 KB migrada automaticamente\n"
                f"✅ {stats.get('total_ideas',0)} ideas cargadas\n"
                f"📊 Score promedio: {stats.get('score_promedio',0)}/100\n"
                f"⭐ Mejor idea: {stats.get('mejor_idea','?')}"
            )
    except Exception as e:
        print(f"Migracion KB: {e}")

    if TELEGRAM_CHAT:
        enviar(TELEGRAM_CHAT,
            f"🟢 Monitor ValidationIdea v5 arrancado\n\n"
            f"✅ Ideas automaticas cada {INTERVALO_MIN} minutos\n"
            f"✅ 5 fuentes: HN + GitHub + Reddit + PH + IA\n"
            f"✅ Scoring doble: IA generadora + IA critica YC\n"
            f"✅ Anti-duplicados semantico activo\n"
            f"✅ Feedback 👍👎 con aprendizaje inmediato\n"
            f"✅ Aprendizaje automatico DIARIO a las 08:00\n"
            f"✅ Link Notion en cada notificacion\n\n"
            f"📱 /start para ver comandos"
        )

    # Hilo bot Telegram
    bot_t = threading.Thread(target=bot_loop, daemon=True)
    bot_t.start()

    # Hilo aprendizaje diario
    learn_t = threading.Thread(target=aprendizaje_diario, daemon=True)
    learn_t.start()

    # Loop principal — genera idea automatica cada INTERVALO_MIN minutos
    print(f"✅ Loop principal: ideas cada {INTERVALO_MIN} min")
    while True:
        try:
            print(f"\n⏰ {datetime.now().strftime('%H:%M')} — Generando idea automatica...")
            ejecutar_idea(tema="", chat_id=TELEGRAM_CHAT)
        except Exception as e:
            print(f"Loop error: {e}")
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT, f"⚠️ Error en loop: {str(e)[:100]}")
        time.sleep(INTERVALO_MIN * 60)

if __name__ == "__main__":
    main()

# fin monitor_nocturno.py
