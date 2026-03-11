import os, sys, json, time, subprocess, threading, re
from datetime import datetime, timedelta

os.environ["PYTHONUTF8"] = "1"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "")
INTERVALO_MIN  = int(os.environ.get("INTERVALO_MINUTOS", "30"))

# ── Telegram helpers ────────────────────────────────────────────────────────

def _post(endpoint, payload, timeout=15):
    import urllib.request
    url  = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"Telegram {endpoint}: {e}")
        return {}

def enviar(chat_id, texto, reply_markup=None):
    texto = str(texto)[:4096]
    payload = {"chat_id": chat_id, "text": texto, "parse_mode": "HTML"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _post("sendMessage", payload)

def get_updates(offset=0):
    return _post("getUpdates", {"offset": offset, "timeout": 10, "limit": 5}, timeout=15)

# ── Helpers ─────────────────────────────────────────────────────────────────

def _botones_feedback(idea_nombre):
    safe = idea_nombre.replace(" ", "_")[:40]
    return {"inline_keyboard": [[
        {"text": "👍 Buena", "callback_data": f"like_{safe}"},
        {"text": "👎 Mala",  "callback_data": f"dislike_{safe}"},
    ]]}

def _extraer_datos_salida(salida):
    def _get(tag):
        m = re.search(rf"^{tag}:(.+)$", salida, re.MULTILINE)
        return m.group(1).strip() if m else ""
    score_str = _get("SCORE_FINAL")
    try:   score = float(score_str)
    except: score = 0
    m = re.search(r"✅ Sincronizada: (.+)$", salida, re.MULTILINE)
    nombre = m.group(1).strip() if m else ""
    return {
        "nombre":            nombre,
        "score":             score,
        "notion_url":        _get("NOTION_URL"),
        "tagline":           _get("TAGLINE"),
        "herramienta_ia":    _get("HERRAMIENTA_IA"),
        "hipotesis":         _get("HIPOTESIS"),
        "monetiz_s1":        _get("MONETIZ_S1"),
        "problema":          _get("PROBLEMA"),
        "veredicto_critico": _get("VEREDICTO_CRITICO"),
        "recomendacion":     _get("RECOMENDACION"),
    }

def _fmt_mensaje_idea(d):
    score  = d.get("score", 0)
    nombre = d.get("nombre", "?")
    if   score >= 90: emoji = "💎"
    elif score >= 85: emoji = "⭐"
    elif score >= 80: emoji = "🔥"
    elif score >= 75: emoji = "✅"
    else:             emoji = "💡"

    lineas = [
        f"{emoji} <b>{nombre} — {score}/100</b>",
        f"<i>\"{d.get('tagline', '')}\"</i>",
        "",
        f"❗ <b>Problema:</b> {d.get('problema', '')[:200]}",
    ]
    if d.get("herramienta_ia"):
        lineas.append(f"🤖 <b>IA clave:</b> {d['herramienta_ia'][:150]}")
    if d.get("monetiz_s1"):
        lineas.append(f"💰 <b>Semana 1:</b> {d['monetiz_s1'][:200]}")
    if d.get("hipotesis"):
        lineas.append(f"🧪 <b>Test 48h:</b> {d['hipotesis'][:200]}")
    if d.get("veredicto_critico"):
        lineas.append(f"✅ <b>Veredicto YC:</b> {d['veredicto_critico'][:150]}")
    if d.get("recomendacion"):
        lineas.append(f"🏷 <b>Recomendacion:</b> {d['recomendacion'].upper()}")
    if d.get("notion_url"):
        lineas.append(f"\n📋 <a href=\"{d['notion_url']}\">Ver informe completo en Notion</a>")
    return "\n".join(lineas)

# ── Ejecucion batch ──────────────────────────────────────────────────────────

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

    elapsed = round(time.time() - t0)

    # Watchdog imports
    try:
        from agents.watchdog import (
            registrar_timeout, registrar_fallo,
            necesita_reparacion, auto_reparar
        )
        wd_ok = True
    except ImportError:
        wd_ok = False
        def registrar_timeout(): return 0
        def registrar_fallo(e): pass
        def necesita_reparacion(): return False
        def auto_reparar(**k): return ""

    if ok:
        d = _extraer_datos_salida(salida)
        if not d.get("nombre"):
            enviar(chat_id, f"⚠️ Idea generada pero sin datos. Output:\n{salida[-500:]}")
            return False

        msg  = _fmt_mensaje_idea(d)
        msg += f"\n\n⏱ <i>Generada en {elapsed}s</i>"
        mkup = _botones_feedback(d["nombre"])
        enviar(chat_id, msg, reply_markup=mkup)

        # Avisar si falta Notion
        if not d.get("notion_url"):
            if not os.environ.get("NOTION_TOKEN", ""):
                enviar(chat_id,
                    "⚠️ <b>Sin link Notion</b> — NOTION_TOKEN no configurado en Railway.\n"
                    "Ve a Railway → Variables → Añade NOTION_TOKEN y NOTION_DATABASE_ID"
                )
            else:
                enviar(chat_id, "⚠️ Notion no devolvio URL — revisa NOTION_DATABASE_ID en Railway.")

    else:
        if "TIMEOUT" in salida:
            n_timeouts = registrar_timeout() if wd_ok else 0
            enviar(chat_id,
                f"⏰ Timeout (>{elapsed}s) — reintento en 30 min. [{n_timeouts} consecutivos]"
            )
            if necesita_reparacion():
                auto_reparar(telegram_fn=enviar, chat_id=chat_id)
                def _reintentar():
                    time.sleep(120)
                    ejecutar_idea(tema=tema, chat_id=chat_id)
                threading.Thread(target=_reintentar, daemon=True).start()
        else:
            if wd_ok: registrar_fallo(salida[-100:])
            error_lines = [l for l in salida.split("\n") if "❌" in l or "error" in l.lower()]
            error_msg   = error_lines[-1][:250] if error_lines else salida[-300:]
            enviar(chat_id, f"❌ Error generando idea\n\n{error_msg}\n\nUsa /debug.")

    return ok

# ── Debug ────────────────────────────────────────────────────────────────────

def ejecutar_debug(chat_id):
    enviar(chat_id, "🔍 Ejecutando diagnostico — espera 60s...")

    # Estado watchdog
    try:
        from agents.watchdog import get_diagnostico
        diag = get_diagnostico()
        enviar(chat_id,
            f"📊 <b>Estado Watchdog</b>\n"
            f"Timeouts consecutivos: {diag['consecutive_timeouts']}\n"
            f"Ultimo exito: {diag['last_success']}\n"
            f"OK hoy: {diag['total_ok_24h']}\n"
            f"Modo emergencia: {'⚠️ SI' if diag['modo_emergencia'] else '✅ NO'}\n"
            f"Ciclo reparacion: {diag['ciclo_reparacion']}\n"
            f"Ultimas ideas: {', '.join(diag['ultimas_ideas'][-3:]) or 'ninguna'}\n"
            f"Verticales saturados: {', '.join(diag['verticales_saturados']) or 'ninguno'}\n"
            f"Errores recientes:\n" + "\n".join(f"  • {e}" for e in diag["errores_recientes"][-4:])
        )
    except Exception as e:
        enviar(chat_id, f"⚠️ Watchdog: {e}")

    # Variables de entorno
    vars_lineas = []
    for v in ["GROQ_API_KEY", "TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID", "NOTION_TOKEN", "NOTION_DATABASE_ID"]:
        val    = os.environ.get(v, "")
        estado = "✅ OK" if val else "❌ NO CONFIGURADA"
        vars_lineas.append(f"{v}: {estado}")
    enviar(chat_id, "🔧 <b>Variables Railway</b>\n" + "\n".join(vars_lineas))

    # Test run_batch
    env = os.environ.copy()
    env["IDEA_TOPIC"] = "fintech"
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
        salida = "TIMEOUT >420s"
        ok     = False
    except Exception as e:
        salida = str(e)
        ok     = False

    d       = _extraer_datos_salida(salida)
    ok_str  = "✅ 0" if ok else "❌ 1"
    nom_str = f"✅ {d['nombre']}" if d["nombre"] else "❌ No encontrada"
    sco_str = f"✅ {d['score']}" if d["score"] else "❌"
    not_str = f"✅ {d['notion_url'][:60]}" if d["notion_url"] else "❌ Sin URL"
    ver_str = f"✅ {d['veredicto_critico'][:60]}" if d["veredicto_critico"] else "❌"

    output_truncado = salida[-1500:] if len(salida) > 1500 else salida
    msg = (
        f"🐛 <b>Debug run_batch.py</b>\n"
        f"Codigo: {ok_str}\n"
        f"Idea: {nom_str}\n"
        f"Score: {sco_str}\n"
        f"Veredicto: {ver_str}\n"
        f"Notion: {not_str}\n\n"
        f"Output:\n{'='*40}\n{output_truncado}"
    )
    enviar(chat_id, msg[:4096])

# ── Comandos ─────────────────────────────────────────────────────────────────

def cmd_top(chat_id):
    try:
        from agents.knowledge_base import get_top_ideas
        ideas = get_top_ideas(5)
        if not ideas:
            enviar(chat_id, "📭 No hay ideas. Usa /idea [tema]")
            return
        lineas = ["🏆 <b>Top 5 mejores ideas</b>\n"]
        for i, idea in enumerate(ideas, 1):
            s = idea.get("scores", {}).get("score_total", 0) if isinstance(idea.get("scores"), dict) else 0
            n = idea.get("nombre", "?")
            t = idea.get("tagline", "")[:80]
            lineas.append(f"{i}. <b>{n}</b> — {s}/100\n   <i>{t}</i>")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_stats(chat_id):
    try:
        from agents.knowledge_base import get_stats
        s   = get_stats()
        msg = (
            f"📊 <b>Estadisticas KB</b>\n\n"
            f"Total ideas: {s.get('total_ideas', 0)}\n"
            f"Score promedio: {s.get('score_promedio', 0)}/100\n"
            f"Mejor idea: {s.get('mejor_idea', '?')} ({s.get('mejor_score', 0)}/100)\n"
            f"Ideas esta semana: {s.get('ideas_semana', 0)}\n"
            f"Verticales top: {', '.join(s.get('verticales_top', [])[:3]) or 'N/A'}"
        )
        enviar(chat_id, msg)
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_ranking(chat_id):
    try:
        from agents.knowledge_base import get_top_ejecutables
        ideas = get_top_ejecutables(5)
        if not ideas:
            enviar(chat_id, "📭 No hay ideas.")
            return
        lineas = ["🚀 <b>Top 5 más ejecutables HOY</b>\n"]
        for i, idea in enumerate(ideas, 1):
            scores = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
            ej  = scores.get("ejecutabilidad", 0)
            sc  = scores.get("score_total", 0)
            n   = idea.get("nombre", "?")
            em  = idea.get("estrategia_monetizacion", {})
            sem1 = str(em.get("semana1", ""))[:120] if isinstance(em, dict) else ""
            herr = idea.get("herramienta_ia_clave", "")[:80]
            lineas.append(f"{i}. <b>{n}</b> — Ejec: {ej}/100 | Score: {sc}/100")
            if herr: lineas.append(f"   🤖 {herr}")
            if sem1: lineas.append(f"   💰 {sem1}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

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
            meta       = pm.get("meta", {}) if isinstance(pm.get("meta"), dict) else {}
            ia_rec     = meta.get("ia_recomendada", "Claude 3.5 Sonnet en Cursor")
            sys_p      = pm.get("system_prompt", "")[:400]
            script_cli = pm.get("primer_cliente_script", "")[:300]
            pasos      = pm.get("instrucciones_paso_a_paso", [])[:5]
            pasos_str  = "\n".join(f"  {p}" for p in pasos)
            msg = (
                f"🛠️ <b>Prompt MVP: {idea.get('nombre', '')}</b>\n\n"
                f"🤖 IA: {ia_rec}\n\n"
                f"📝 System prompt:\n<code>{sys_p}</code>\n\n"
                f"🚀 Pasos:\n{pasos_str}\n\n"
                f"💰 Primer cliente:\n{script_cli}"
            )
        else:
            msg = f"Sin prompt MVP para '{nombre_idea}'"
        enviar(chat_id, msg[:4096])
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_buscar(chat_id, query):
    try:
        ruta = "data/ideas.json"
        if not os.path.exists(ruta):
            enviar(chat_id, "📭 Sin ideas aun.")
            return
        with open(ruta, "r", encoding="utf-8") as f:
            todas = json.load(f)
        q     = query.lower()
        found = [idea for idea in todas if q in json.dumps(idea, ensure_ascii=False).lower()]
        if not found:
            enviar(chat_id, f"🔍 Sin resultados para '{query}'")
            return
        lineas = [f"🔍 <b>Resultados '{query}'</b>\n"]
        for idea in found[-5:]:
            s = idea.get("scores", {}).get("score_total", 0) if isinstance(idea.get("scores"), dict) else 0
            n = idea.get("nombre", "?")
            t = idea.get("tagline", "")[:80]
            lineas.append(f"• <b>{n}</b> — {s}/100\n  <i>{t}</i>")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_tendencias(chat_id):
    try:
        from agents.trend_scout import get_tendencias, actualizar_tendencias
        actualizar_tendencias()
        trends = get_tendencias()[:12]
        if not trends:
            enviar(chat_id, "📭 Sin tendencias.")
            return
        lineas = ["🌐 <b>Tendencias tech ahora</b>\n"]
        for t in trends:
            lineas.append(f"• {str(t)[:100]}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_cola(chat_id):
    ruta = "data/cola_pendientes.csv"
    if not os.path.exists(ruta):
        enviar(chat_id, "✅ Cola vacia.")
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
            lineas.append(f"• {r.get('nombre_idea', '?')} — {r.get('error', '?')[:60]}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_aprender(chat_id):
    enviar(chat_id, "🧠 Ejecutando aprendizaje ahora...")
    try:
        from agents.weekly_learner import analizar_y_aprender
        r     = analizar_y_aprender()
        pesos = r.get("nuevos_pesos", {})
        msg = (
            f"✅ <b>Aprendizaje completado</b>\n\n"
            f"Ciclo {r.get('ciclo', 0)} completado\n"
            f"{r.get('total_ideas', 0)} ideas | {r.get('ideas_exitosas', 0)} exitosas ({r.get('pct_exito', 0)}%)\n"
            f"Score promedio: {r.get('score_anterior', 0)} → Objetivo: {r.get('score_objetivo', 0)}\n"
            f"Verticales TOP: {', '.join(pesos.get('verticales_preferidas', [])[:3]) or 'N/A'}\n"
            f"Penalizadas: {', '.join(pesos.get('verticales_penalizadas', [])[:3]) or 'ninguna'}\n"
            f"Tags exitosos: {', '.join(pesos.get('tags_exitosos', [])[:5]) or 'N/A'}\n"
            f"Temperatura: {pesos.get('temperatura_groq', 0.85)} | Umbral dup: {pesos.get('umbral_duplicado', 0.38)}"
        )
        enviar(chat_id, msg)
    except Exception as e:
        enviar(chat_id, f"❌ Aprendizaje: {e}")

def cmd_status(chat_id):
    try:
        from agents.knowledge_base import get_stats
        s = get_stats()
    except:
        s = {}
    wd_txt = ""
    try:
        from agents.watchdog import get_diagnostico
        d = get_diagnostico()
        wd_txt = (
            f"\n\n🔧 <b>Watchdog</b>\n"
            f"Timeouts consecutivos: {d['consecutive_timeouts']}\n"
            f"Ultimo exito: {d['last_success']}\n"
            f"Modo emergencia: {'⚠️ SI' if d['modo_emergencia'] else '✅ NO'}\n"
            f"Ciclo reparacion: {d['ciclo_reparacion']}"
        )
    except:
        pass
    notion_ok = "✅" if os.environ.get("NOTION_TOKEN", "") else "❌ Sin NOTION_TOKEN"
    groq_ok   = "✅" if os.environ.get("GROQ_API_KEY", "") else "❌ Sin GROQ_API_KEY"
    msg = (
        f"📊 <b>Estado ValidationIdea v5</b>\n"
        f"Hora: {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"KB: {s.get('total_ideas', 0)} ideas | Promedio: {s.get('score_promedio', 0)}/100\n"
        f"Mejor: {s.get('mejor_idea', '?')} ({s.get('mejor_score', 0)}/100)\n\n"
        f"Groq: {groq_ok}\n"
        f"Notion: {notion_ok}\n"
        f"Monitor: ✅ activo — ideas cada {INTERVALO_MIN} min"
        + wd_txt
    )
    enviar(chat_id, msg)

# ── Feedback ──────────────────────────────────────────────────────────────────

def procesar_feedback(callback_data, from_id, cb_id):
    try:
        from agents.knowledge_base import registrar_feedback
    except ImportError:
        return
    try:
        if callback_data.startswith("like_"):
            nombre = callback_data[5:].replace("_", " ")
            registrar_feedback(nombre, True)
            _post("answerCallbackQuery", {"callback_query_id": cb_id, "text": "👍 Registrado"})
        elif callback_data.startswith("dislike_"):
            nombre = callback_data[8:].replace("_", " ")
            registrar_feedback(nombre, False)
            _post("answerCallbackQuery", {"callback_query_id": cb_id, "text": "👎 Registrado"})
    except Exception as e:
        print(f"Feedback error: {e}")

# ── Bot loop ──────────────────────────────────────────────────────────────────

def bot_loop():
    offset = 0
    print("🤖 Bot Telegram arrancado")
    while True:
        try:
            data = get_updates(offset)
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1

                # Callback (feedback)
                if "callback_query" in upd:
                    cq = upd["callback_query"]
                    procesar_feedback(
                        cq.get("data", ""),
                        str(cq["from"]["id"]),
                        cq.get("id", ""),
                    )
                    continue

                msg  = upd.get("message", {})
                text = msg.get("text", "").strip()
                chat = str(msg.get("chat", {}).get("id", ""))
                if not text or not chat:
                    continue

                tl = text.lower()

                if tl in ("/start", "/help"):
                    enviar(chat,
                        "🤖 ValidationIdea Bot v5\n\n"
                        "Comandos:\n"
                        "💡 /idea [tema] — Genera idea (ej: /idea salud)\n"
                        "📊 /status — Estado del sistema\n"
                        "🏆 /top — Top 5 mejores ideas\n"
                        "📋 /stats — Estadisticas KB\n"
                        "🚀 /ranking — Top 5 más ejecutables HOY\n"
                        "🛠️ /ejecutar [nombre] — Prompt MVP completo\n"
                        "🔍 /buscar [palabra] — Buscar ideas\n"
                        "🌐 /tendencias — Tendencias tech ahora\n"
                        "🔄 /cola — Ideas pendientes Notion\n"
                        "🧠 /aprender — Ejecutar aprendizaje ahora\n"
                        "🐛 /debug — Diagnostico del sistema\n\n"
                        "Feedback en cada idea: 👍 / 👎\n"
                        "Sistema aprende cada dia a las 08:00."
                    )

                elif tl.startswith("/idea"):
                    tema = text[5:].strip()
                    if not tema:
                        enviar(chat, "💡 Ejemplo: /idea salud\n/idea fintech\n/idea mascotas")
                    else:
                        enviar(chat, f"⏳ Generando idea sobre '{tema}'...\nEspera 60-120s ☕")
                        threading.Thread(
                            target=ejecutar_idea, args=(tema, chat), daemon=True
                        ).start()

                elif tl == "/debug":
                    threading.Thread(
                        target=ejecutar_debug, args=(chat,), daemon=True
                    ).start()

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
                    threading.Thread(
                        target=cmd_aprender, args=(chat,), daemon=True
                    ).start()

                else:
                    # NLP basico
                    if any(x in tl for x in ["genera", "idea de", "idea sobre", "dame una idea"]):
                        for kw in ["dame una idea sobre", "dame una idea de", "genera idea sobre",
                                   "genera idea de", "idea sobre", "idea de", "genera"]:
                            if kw in tl:
                                tema = tl.split(kw)[-1].strip()
                                if tema and len(tema) > 2:
                                    enviar(chat, f"⏳ Generando idea sobre '{tema}'...\nEspera 60-120s ☕")
                                    threading.Thread(
                                        target=ejecutar_idea, args=(tema, chat), daemon=True
                                    ).start()
                                    break
                    elif any(x in tl for x in ["ranking", "ejecutable"]):
                        cmd_ranking(chat)
                    elif any(x in tl for x in ["top", "mejor"]):
                        cmd_top(chat)
                    elif any(x in tl for x in ["busca", "buscar"]):
                        q = re.sub(r"busca[r]?\s*", "", tl).strip()
                        if q:
                            cmd_buscar(chat, q)
                        else:
                            enviar(chat, "❓ Ejemplo: /buscar fintech")
                    elif "tendencia" in tl:
                        cmd_tendencias(chat)
                    elif "stats" in tl or "estadistic" in tl:
                        cmd_stats(chat)
                    elif "status" in tl or "estado" in tl:
                        cmd_status(chat)
                    else:
                        enviar(chat,
                            "🤖 No entendi. Prueba:\n"
                            "• /idea [tema]\n"
                            "• /ranking\n"
                            "• /top\n"
                            "• /buscar [palabra]\n"
                            "O usa /start."
                        )

        except Exception as e:
            print(f"Bot loop error: {e}")
            time.sleep(5)

# ── Aprendizaje diario ────────────────────────────────────────────────────────

def aprendizaje_diario():
    while True:
        ahora   = datetime.now()
        proxima = ahora.replace(hour=8, minute=0, second=0, microsecond=0)
        if ahora >= proxima:
            proxima += timedelta(days=1)
        time.sleep((proxima - ahora).total_seconds())
        try:
            from agents.weekly_learner import analizar_y_aprender
            r     = analizar_y_aprender()
            pesos = r.get("nuevos_pesos", {})
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT,
                    f"🧠 Aprendizaje automatico completado\n"
                    f"Ciclo {r.get('ciclo', 0)} | {r.get('total_ideas', 0)} ideas\n"
                    f"Score objetivo: {r.get('score_objetivo', 75)}\n"
                    f"Verticales TOP: {', '.join(pesos.get('verticales_preferidas', [])[:3]) or 'N/A'}"
                )
        except Exception as e:
            print(f"Aprendizaje diario error: {e}")

# ── Monitor watchdog: detecta fallos en bucle principal ───────────────────────

def monitor_watchdog():
    """Hilo independiente: si llevamos 3+ ciclos sin exito, auto-repara."""
    while True:
        time.sleep(INTERVALO_MIN * 60 * 3)  # Comprueba cada 3 ciclos
        try:
            from agents.watchdog import necesita_reparacion, auto_reparar, get_diagnostico
            if necesita_reparacion():
                diag = get_diagnostico()
                print(f"🔧 Watchdog: {diag['consecutive_timeouts']} timeouts — auto-reparando...")
                auto_reparar(telegram_fn=enviar, chat_id=TELEGRAM_CHAT)
        except Exception as e:
            print(f"Monitor watchdog error: {e}")

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    # Migrar KB
    try:
        from agents.knowledge_base import migrar_si_necesario, get_stats
        migrar_si_necesario()
        stats = get_stats()
        if TELEGRAM_CHAT:
            enviar(TELEGRAM_CHAT,
                f"🔄 KB migrada automaticamente\n"
                f"✅ {stats.get('total_ideas', 0)} ideas cargadas\n"
                f"📊 Score promedio: {stats.get('score_promedio', 0)}/100\n"
                f"⭐ Mejor idea: {stats.get('mejor_idea', '?')}"
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
            f"✅ Anti-placeholders: informacion real garantizada\n"
            f"✅ Watchdog: auto-reparacion si falla 3 veces\n"
            f"✅ Diversidad forzada: no repite temas\n"
            f"✅ Aprendizaje automatico DIARIO a las 08:00\n"
            f"✅ Link Notion en cada notificacion\n\n"
            f"📱 /start para ver comandos"
        )

    # Hilos daemon
    threading.Thread(target=bot_loop,          daemon=True).start()
    threading.Thread(target=aprendizaje_diario, daemon=True).start()
    threading.Thread(target=monitor_watchdog,   daemon=True).start()

    print(f"✅ Loop principal: ideas cada {INTERVALO_MIN} min")

    # Loop principal
    while True:
        try:
            print(f"\n⏰ {datetime.now().strftime('%H:%M')} — Generando idea automatica...")
            ejecutar_idea(tema="", chat_id=TELEGRAM_CHAT)
        except Exception as e:
            print(f"Loop principal error: {e}")
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT, f"⚠️ Error loop: {str(e)[:100]}")
        time.sleep(INTERVALO_MIN * 60)

if __name__ == "__main__":
    main()

# fin monitor_nocturno.py
