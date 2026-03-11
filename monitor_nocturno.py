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

# ── Helpers ──────────────────────────────────────────────────────────────────

def _limpiar_tema(texto):
    texto = texto.strip().lower()
    for quitar in ["/idea", "genera una idea sobre", "genera una idea de",
                   "genera idea sobre", "genera idea de", "dame una idea sobre",
                   "dame una idea de", "idea sobre", "idea de", "genera", "idea"]:
        if texto.startswith(quitar):
            texto = texto[len(quitar):].strip()
    return texto.strip()

def _botones_feedback(idea_nombre):
    safe = idea_nombre.replace(" ", "_")[:40]
    return {"inline_keyboard": [[
        {"text": "👍 Buena",   "callback_data": f"like_{safe}"},
        {"text": "👎 Mala",    "callback_data": f"dislike_{safe}"},
        {"text": "🔖 Guardar", "callback_data": f"save_{safe}"},
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
        f"❗ <b>Problema:</b> {d.get('problema', '')[:220]}",
    ]
    if d.get("herramienta_ia"):
        lineas.append(f"🤖 <b>IA clave:</b> {d['herramienta_ia'][:160]}")
    if d.get("monetiz_s1"):
        lineas.append(f"💰 <b>Semana 1:</b> {d['monetiz_s1'][:220]}")
    if d.get("hipotesis"):
        lineas.append(f"🧪 <b>Test 48h:</b> {d['hipotesis'][:220]}")
    if d.get("veredicto_critico"):
        lineas.append(f"✅ <b>Veredicto YC:</b> {d['veredicto_critico'][:180]}")
    if d.get("recomendacion"):
        lineas.append(f"🏷 <b>Recomendacion:</b> {d['recomendacion'].upper()}")
    if d.get("notion_url"):
        lineas.append(f"\n📋 <a href=\"{d['notion_url']}\">Ver informe completo en Notion</a>")
    else:
        lineas.append("\n⚠️ Notion: en cola de reintento automático")
    return "\n".join(lineas)

# ── Notion retry queue ───────────────────────────────────────────────────────

def _notion_retry_loop():
    while True:
        time.sleep(600)
        try:
            cola_path = "data/cola_pendientes.csv"
            if not os.path.exists(cola_path):
                continue
            import csv
            with open(cola_path, "r", encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            if not rows:
                continue

            from agents.notion_sync_agent import sync_idea_to_notion
            pendientes_nuevos = []
            exitos = 0
            for row in rows:
                if int(row.get("intentos", 1)) > 5:
                    continue
                try:
                    idea = json.loads(row.get("datos_json", "{}"))
                    url  = sync_idea_to_notion(idea)
                    if url:
                        exitos += 1
                        if TELEGRAM_CHAT:
                            enviar(TELEGRAM_CHAT,
                                f"✅ Notion retry OK: {row.get('nombre_idea','?')}\n"
                                f"📋 <a href=\"{url}\">Ver en Notion</a>"
                            )
                    else:
                        row["intentos"] = int(row.get("intentos", 1)) + 1
                        pendientes_nuevos.append(row)
                except Exception:
                    row["intentos"] = int(row.get("intentos", 1)) + 1
                    pendientes_nuevos.append(row)

            with open(cola_path, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["timestamp","nombre_idea","intentos","error","datos_json"])
                writer.writeheader()
                writer.writerows(pendientes_nuevos)

            if exitos > 0:
                print(f"✅ Notion retry: {exitos} ideas subidas")
        except Exception as e:
            print(f"Notion retry: {e}")

# ── Ejecucion batch ──────────────────────────────────────────────────────────

def ejecutar_idea(tema="", chat_id=None):
    if not chat_id:
        chat_id = TELEGRAM_CHAT
    env = os.environ.copy()

    if not tema:
        try:
            from agents.verticales_rotacion import get_vertical_siguiente
            from agents.watchdog import get_verticales_bloqueados
            bloqueados = get_verticales_bloqueados()
            vertical   = get_vertical_siguiente(verticales_bloqueados_extra=bloqueados)
            env["IDEA_TOPIC"] = vertical
            print(f"🎯 Vertical rotativo: {vertical}")
        except Exception as e:
            print(f"⚠️ Rotacion vertical: {e}")
            env["IDEA_TOPIC"] = ""
    else:
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

    try:
        from agents.watchdog import registrar_timeout, registrar_fallo, necesita_reparacion, auto_reparar
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
            enviar(chat_id, f"⚠️ Generada pero sin datos extraibles.\n{salida[-400:]}")
            return False

        try:
            from agents.verticales_rotacion import registrar_vertical_usado
            registrar_vertical_usado(env.get("IDEA_TOPIC", ""))
        except: pass

        msg  = _fmt_mensaje_idea(d)
        msg += f"\n\n⏱ <i>Generada en {elapsed}s</i>"
        mkup = _botones_feedback(d["nombre"])
        enviar(chat_id, msg, reply_markup=mkup)

        if d.get("score", 0) >= 85:
            enviar(chat_id,
                f"🚨 <b>ALERTA IDEA TOP — {d['score']}/100</b>\n"
                f"Usa /ejecutar {d['nombre']} para el prompt MVP completo."
            )
        return True

    else:
        if "TIMEOUT" in salida:
            n_timeouts = registrar_timeout() if wd_ok else 0
            enviar(chat_id,
                f"⏰ Timeout (>{elapsed}s) — reintento en {INTERVALO_MIN} min. "
                f"[{n_timeouts} consecutivos]"
            )
            if necesita_reparacion():
                auto_reparar(telegram_fn=enviar, chat_id=chat_id)
                try:
                    from agents.auto_improver import ciclo_auto_mejora
                    threading.Thread(
                        target=ciclo_auto_mejora,
                        kwargs={"error_log": salida[-600:], "telegram_fn": enviar, "chat_id": chat_id},
                        daemon=True
                    ).start()
                except Exception as e:
                    print(f"Auto-improver: {e}")
                def _reintentar():
                    time.sleep(120)
                    ejecutar_idea(tema=tema, chat_id=chat_id)
                threading.Thread(target=_reintentar, daemon=True).start()
        else:
            if wd_ok: registrar_fallo(salida[-100:])
            error_lines = [l for l in salida.split("\n")
                           if "❌" in l or "error" in l.lower() or "Error" in l]
            error_msg = error_lines[-1][:250] if error_lines else salida[-300:]
            enviar(chat_id, f"❌ Error\n\n{error_msg}\n\nUsa /debug.")
            # Auto-mejora reactiva
            if wd_ok and necesita_reparacion():
                try:
                    from agents.auto_improver import ciclo_auto_mejora
                    threading.Thread(
                        target=ciclo_auto_mejora,
                        kwargs={"error_log": salida[-600:], "telegram_fn": enviar, "chat_id": chat_id},
                        daemon=True
                    ).start()
                except Exception as e:
                    print(f"Auto-improver reactivo: {e}")
        return False

# ── Debug ────────────────────────────────────────────────────────────────────

def ejecutar_debug(chat_id):
    enviar(chat_id, "🔍 Ejecutando diagnostico — espera 60s...")

    try:
        from agents.watchdog import get_diagnostico
        d = get_diagnostico()
        enviar(chat_id,
            f"📊 <b>Estado Watchdog</b>\n"
            f"Timeouts consecutivos: {d['consecutive_timeouts']}\n"
            f"Ultimo exito: {d['last_success']}\n"
            f"OK hoy: {d['total_ok_24h']}\n"
            f"Modo emergencia: {'⚠️ SI' if d['modo_emergencia'] else '✅ NO'}\n"
            f"Ciclo reparacion: {d['ciclo_reparacion']}\n"
            f"Ultimas ideas: {', '.join(d['ultimas_ideas'][-3:]) or 'ninguna'}\n"
            f"Verticales saturados: {', '.join(d['verticales_saturados']) or 'ninguno'}\n"
            f"Errores recientes:\n" + "\n".join(f"  • {e}" for e in d["errores_recientes"][-4:])
        )
    except Exception as e:
        enviar(chat_id, f"⚠️ Watchdog: {e}")

    try:
        from agents.verticales_rotacion import get_stats_rotacion
        r = get_stats_rotacion()
        enviar(chat_id,
            f"🎯 <b>Rotacion Vertical</b>\n"
            f"Ciclo: {r['ciclo_actual']} | "
            f"Disponibles: {r['disponibles_restantes']}/{r['total_disponibles']}\n"
            f"Ultimos 5: {', '.join(r['ultimos_5']) or 'ninguno'}"
        )
    except Exception as e:
        enviar(chat_id, f"⚠️ Rotacion: {e}")

    try:
        from agents.auto_improver import get_historial_mejoras
        h = get_historial_mejoras()
        enviar(chat_id,
            f"🔧 <b>Auto-mejoras</b>\n"
            f"Total: {h['total_mejoras']} | Hoy: {h['total_hoy']}/{h['limite_dia']}\n"
            f"Rollbacks: {h['rollbacks']}"
        )
    except Exception as e:
        enviar(chat_id, f"⚠️ Auto-improver: {e}")

    vars_lineas = []
    for v in ["GROQ_API_KEY","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","NOTION_TOKEN","NOTION_DATABASE_ID"]:
        val    = os.environ.get(v, "")
        estado = "✅ OK" if val else "❌ NO CONFIGURADA"
        vars_lineas.append(f"{v}: {estado}")
    enviar(chat_id, "🔧 <b>Variables Railway</b>\n" + "\n".join(vars_lineas))

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

    datos   = _extraer_datos_salida(salida)
    ok_str  = "✅ 0" if ok else "❌ 1"
    nom_str = f"✅ {datos['nombre']}"          if datos["nombre"]            else "❌ No encontrada"
    sco_str = f"✅ {datos['score']}"           if datos["score"]             else "❌"
    not_str = f"✅ {datos['notion_url'][:50]}" if datos["notion_url"]        else "❌ Sin URL"
    ver_str = f"✅ {datos['veredicto_critico'][:60]}" if datos["veredicto_critico"] else "❌"
    output  = salida[-1500:] if len(salida) > 1500 else salida

    enviar(chat_id,
        f"🐛 <b>Debug run_batch.py</b>\n"
        f"Codigo: {ok_str}\n"
        f"Idea: {nom_str}\n"
        f"Score: {sco_str}\n"
        f"Veredicto: {ver_str}\n"
        f"Notion: {not_str}\n\n"
        f"Output:\n{'='*35}\n{output}"[:4096]
    )

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
            s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            n = idea.get("nombre","?")
            t = idea.get("tagline","")[:80]
            lineas.append(f"{i}. <b>{n}</b> — {s}/100\n   <i>{t}</i>")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_stats(chat_id):
    try:
        from agents.knowledge_base import get_stats
        s = get_stats()
        rot_txt = ""
        try:
            from agents.verticales_rotacion import get_stats_rotacion
            r = get_stats_rotacion()
            rot_txt = f"\nRotacion vertical: ciclo {r['ciclo_actual']} | {r['disponibles_restantes']} disponibles"
        except: pass
        enviar(chat_id,
            f"📊 <b>Estadisticas KB</b>\n\n"
            f"Total ideas: {s.get('total_ideas',0)}\n"
            f"Score promedio: {s.get('score_promedio',0)}/100\n"
            f"Mejor idea: {s.get('mejor_idea','?')} ({s.get('mejor_score',0)}/100)\n"
            f"Ideas esta semana: {s.get('ideas_semana',0)}\n"
            f"Verticales top: {', '.join(s.get('verticales_top',[])[:3]) or 'N/A'}"
            + rot_txt
        )
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
            scores = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
            ej   = scores.get("ejecutabilidad",0)
            sc   = scores.get("score_total",0)
            n    = idea.get("nombre","?")
            em   = idea.get("estrategia_monetizacion",{})
            sem1 = str(em.get("semana1",""))[:130] if isinstance(em,dict) else ""
            herr = idea.get("herramienta_ia_clave","")[:80]
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
        pm = idea.get("prompt_mvp",{})
        if isinstance(pm, str):
            try:   pm = json.loads(pm)
            except: pm = {}
        if isinstance(pm, dict):
            meta       = pm.get("meta",{}) if isinstance(pm.get("meta"),dict) else {}
            ia_rec     = meta.get("ia_recomendada","Claude 3.5 Sonnet en Cursor")
            sys_p      = pm.get("system_prompt","")[:400]
            script_cli = pm.get("primer_cliente_script","")[:300]
            pasos      = pm.get("instrucciones_paso_a_paso",[])[:5]
            pasos_str  = "\n".join(f"  {p}" for p in pasos)
            enviar(chat_id,
                f"🛠️ <b>Prompt MVP: {idea.get('nombre','')}</b>\n\n"
                f"🤖 IA: {ia_rec}\n\n"
                f"📝 System prompt:\n<code>{sys_p}</code>\n\n"
                f"🚀 Pasos:\n{pasos_str}\n\n"
                f"💰 Primer cliente:\n{script_cli}"[:4096]
            )
        else:
            enviar(chat_id, f"Sin prompt MVP para '{nombre_idea}'")
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_comparar(chat_id, texto):
    partes = re.split(r"\s+vs\.?\s+", texto, flags=re.IGNORECASE)
    if len(partes) < 2:
        enviar(chat_id, "❓ Uso: /comparar NombreA vs NombreB")
        return
    try:
        ruta = "data/ideas.json"
        if not os.path.exists(ruta):
            enviar(chat_id, "📭 Sin ideas aun.")
            return
        with open(ruta,"r",encoding="utf-8") as f:
            todas = json.load(f)

        def _buscar(nombre):
            n = nombre.strip().lower()
            for idea in todas:
                if n in idea.get("nombre","").lower():
                    return idea
            return None

        a = _buscar(partes[0])
        b = _buscar(partes[1])
        if not a:
            enviar(chat_id, f"❌ No encontre '{partes[0]}'"); return
        if not b:
            enviar(chat_id, f"❌ No encontre '{partes[1]}'"); return

        def _sc(idea):
            return idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
        def _em(idea):
            e = idea.get("estrategia_monetizacion",{})
            return e if isinstance(e,dict) else {}

        lineas = [f"⚔️ <b>{a['nombre']} vs {b['nombre']}</b>\n"]
        for label, va, vb in [
            ("Score total",    _sc(a).get("score_total",0),    _sc(b).get("score_total",0)),
            ("Ejecutabilidad", _sc(a).get("ejecutabilidad",0), _sc(b).get("ejecutabilidad",0)),
            ("Monetizacion",   _sc(a).get("monetizacion",0),   _sc(b).get("monetizacion",0)),
            ("Viral",          _sc(a).get("viral",0),          _sc(b).get("viral",0)),
            ("Timing",         _sc(a).get("timing",0),         _sc(b).get("timing",0)),
        ]:
            w = "⬅️" if va > vb else "➡️" if vb > va else "🤝"
            lineas.append(f"{w} <b>{label}:</b> {va} vs {vb}")

        lineas.append(f"\n💰 <b>Pricing A:</b> {_em(a).get('precio_optimo_justificado','?')[:80]}")
        lineas.append(f"💰 <b>Pricing B:</b> {_em(b).get('precio_optimo_justificado','?')[:80]}")

        sc_a = _sc(a).get("score_total",0)
        sc_b = _sc(b).get("score_total",0)
        if sc_a > sc_b:
            lineas.append(f"\n🏆 Ganadora: <b>{a['nombre']}</b> (+{sc_a-sc_b} pts)")
        elif sc_b > sc_a:
            lineas.append(f"\n🏆 Ganadora: <b>{b['nombre']}</b> (+{sc_b-sc_a} pts)")
        else:
            lineas.append("\n🤝 Empate — decide por ejecutabilidad")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_buscar(chat_id, query):
    try:
        ruta = "data/ideas.json"
        if not os.path.exists(ruta):
            enviar(chat_id, "📭 Sin ideas aun.")
            return
        with open(ruta,"r",encoding="utf-8") as f:
            todas = json.load(f)
        q     = query.lower()
        found = [idea for idea in todas if q in json.dumps(idea, ensure_ascii=False).lower()]
        if not found:
            enviar(chat_id, f"🔍 Sin resultados para '{query}'")
            return
        lineas = [f"🔍 <b>Resultados '{query}'</b>\n"]
        for idea in found[-5:]:
            s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            n = idea.get("nombre","?")
            t = idea.get("tagline","")[:80]
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
        with open(ruta,"r",encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            enviar(chat_id, "✅ Cola vacia.")
            return
        lineas = [f"🔄 <b>Cola pendientes Notion: {len(rows)}</b>\n"]
        for r in rows[-5:]:
            lineas.append(f"• {r.get('nombre_idea','?')} (intento {r.get('intentos','1')}) — {r.get('error','?')[:50]}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

def cmd_aprender(chat_id):
    enviar(chat_id, "🧠 Ejecutando aprendizaje ahora...")
    try:
        from agents.weekly_learner import analizar_y_aprender
        r     = analizar_y_aprender()
        pesos = r.get("nuevos_pesos",{})
        enviar(chat_id,
            f"✅ <b>Aprendizaje completado</b>\n\n"
            f"Ciclo {r.get('ciclo',0)} | {r.get('total_ideas',0)} ideas | "
            f"{r.get('ideas_exitosas',0)} exitosas ({r.get('pct_exito',0)}%)\n"
            f"Score: {r.get('score_anterior',0)} → Objetivo: {r.get('score_objetivo',0)}\n"
            f"Verticales TOP: {', '.join(pesos.get('verticales_preferidas',[])[:3]) or 'N/A'}\n"
            f"Penalizadas: {', '.join(pesos.get('verticales_penalizadas',[])[:3]) or 'ninguna'}\n"
            f"Tags: {', '.join(pesos.get('tags_exitosos',[])[:5]) or 'N/A'}\n"
            f"Temperatura: {pesos.get('temperatura_groq',0.85)} | "
            f"Umbral dup: {pesos.get('umbral_duplicado',0.38)}"
        )
    except Exception as e:
        enviar(chat_id, f"❌ Aprendizaje: {e}")

def cmd_mejoras(chat_id):
    try:
        from agents.auto_improver import get_historial_mejoras
        h = get_historial_mejoras()
        lineas = [
            f"🔧 <b>Auto-mejoras aplicadas</b>\n",
            f"Total: {h['total_mejoras']} | Hoy: {h['total_hoy']}/{h['limite_dia']}",
            f"Rollbacks: {h['rollbacks']}\n",
            "<b>Ultimas mejoras:</b>",
        ]
        for m in reversed(h["ultimas_5"]):
            ts   = m.get("timestamp","")[:16].replace("T"," ")
            desc = m.get("descripcion","?")[:60]
            conf = m.get("confianza",0)
            tipo = m.get("tipo_error","?")
            lineas.append(f"• [{ts}] {desc}\n  Confianza: {conf}% | Tipo: {tipo}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"❌ {e}")

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
            f"Timeouts: {d['consecutive_timeouts']} | OK hoy: {d['total_ok_24h']}\n"
            f"Ultimo exito: {d['last_success']}\n"
            f"Emergencia: {'⚠️ SI' if d['modo_emergencia'] else '✅ NO'} | "
            f"Ciclo rep: {d['ciclo_reparacion']}"
        )
    except: pass
    rot_txt = ""
    try:
        from agents.verticales_rotacion import get_stats_rotacion
        r = get_stats_rotacion()
        rot_txt = f"\n🎯 Vertical ciclo {r['ciclo_actual']} | {r['disponibles_restantes']} disponibles"
    except: pass
    ai_txt = ""
    try:
        from agents.auto_improver import get_historial_mejoras
        h = get_historial_mejoras()
        ai_txt = f"\n🤖 Auto-mejoras: {h['total_mejoras']} total | {h['total_hoy']}/{h['limite_dia']} hoy"
    except: pass
    notion_ok = "✅" if os.environ.get("NOTION_TOKEN","") else "❌ Sin token"
    groq_ok   = "✅" if os.environ.get("GROQ_API_KEY","") else "❌ Sin key"
    enviar(chat_id,
        f"📊 <b>Estado ValidationIdea v6</b>\n"
        f"{datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
        f"KB: {s.get('total_ideas',0)} ideas | Promedio: {s.get('score_promedio',0)}/100\n"
        f"Mejor: {s.get('mejor_idea','?')} ({s.get('mejor_score',0)}/100)\n\n"
        f"Groq: {groq_ok} | Notion: {notion_ok}\n"
        f"Monitor: ✅ activo — ideas cada {INTERVALO_MIN} min"
        + wd_txt + rot_txt + ai_txt
    )

# ── Feedback ──────────────────────────────────────────────────────────────────

def procesar_feedback(callback_data, cb_id):
    try:
        from agents.knowledge_base import registrar_feedback
    except ImportError:
        return
    try:
        if callback_data.startswith("like_"):
            nombre = callback_data[5:].replace("_"," ")
            registrar_feedback(nombre, True)
            _post("answerCallbackQuery",{"callback_query_id":cb_id,"text":"👍 Registrado"})
        elif callback_data.startswith("dislike_"):
            nombre = callback_data[8:].replace("_"," ")
            registrar_feedback(nombre, False)
            _post("answerCallbackQuery",{"callback_query_id":cb_id,"text":"👎 Registrado"})
        elif callback_data.startswith("save_"):
            nombre = callback_data[5:].replace("_"," ")
            registrar_feedback(nombre, True)
            _post("answerCallbackQuery",{"callback_query_id":cb_id,"text":"🔖 Guardada"})
    except Exception as e:
        print(f"Feedback: {e}")

# ── Hilos periodicos ──────────────────────────────────────────────────────────

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
            pesos = r.get("nuevos_pesos",{})
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT,
                    f"🧠 Aprendizaje automatico completado\n"
                    f"Ciclo {r.get('ciclo',0)} | {r.get('total_ideas',0)} ideas\n"
                    f"Score objetivo: {r.get('score_objetivo',75)}\n"
                    f"Verticales TOP: {', '.join(pesos.get('verticales_preferidas',[])[:3]) or 'N/A'}"
                )
        except Exception as e:
            print(f"Aprendizaje diario: {e}")
        # Mejora proactiva justo despues del aprendizaje
        try:
            from agents.auto_improver import ciclo_auto_mejora
            ciclo_auto_mejora(telegram_fn=enviar, chat_id=TELEGRAM_CHAT)
        except Exception as e:
            print(f"Mejora proactiva diaria: {e}")

def log_diario():
    while True:
        ahora   = datetime.now()
        proxima = ahora.replace(hour=9, minute=0, second=0, microsecond=0)
        if ahora >= proxima:
            proxima += timedelta(days=1)
        time.sleep((proxima - ahora).total_seconds())
        try:
            from agents.knowledge_base import get_stats
            s = get_stats()
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT,
                    f"☀️ <b>Resumen diario</b> — {datetime.now().strftime('%d/%m/%Y')}\n\n"
                    f"📊 Total ideas: {s.get('total_ideas',0)}\n"
                    f"🏆 Score promedio: {s.get('score_promedio',0)}/100\n"
                    f"⭐ Mejor: {s.get('mejor_idea','?')} ({s.get('mejor_score',0)}/100)\n\n"
                    f"Usa /top para ver las mejores."
                )
        except Exception as e:
            print(f"Log diario: {e}")

def monitor_watchdog():
    while True:
        time.sleep(INTERVALO_MIN * 60 * 3)
        try:
            from agents.watchdog import necesita_reparacion, auto_reparar, get_diagnostico
            if necesita_reparacion():
                diag = get_diagnostico()
                print(f"🔧 Watchdog: {diag['consecutive_timeouts']} timeouts — reparando...")
                auto_reparar(telegram_fn=enviar, chat_id=TELEGRAM_CHAT)
        except Exception as e:
            print(f"Monitor watchdog: {e}")

# ── Bot loop ──────────────────────────────────────────────────────────────────

def bot_loop():
    offset = 0
    print("🤖 Bot arrancado")
    while True:
        try:
            data = get_updates(offset)
            for upd in data.get("result", []):
                offset = upd["update_id"] + 1

                if "callback_query" in upd:
                    cq = upd["callback_query"]
                    procesar_feedback(cq.get("data",""), cq.get("id",""))
                    continue

                msg  = upd.get("message", {})
                text = msg.get("text","").strip()
                chat = str(msg.get("chat",{}).get("id",""))
                if not text or not chat:
                    continue

                tl = text.lower().strip()

                if tl in ("/start", "/help"):
                    enviar(chat,
                        "🤖 <b>ValidationIdea Bot v6</b>\n\n"
                        "💡 /idea [tema] — Genera idea\n"
                        "📊 /status — Estado del sistema\n"
                        "🏆 /top — Top 5 mejores ideas\n"
                        "📋 /stats — Estadisticas KB\n"
                        "🚀 /ranking — Top 5 más ejecutables\n"
                        "🛠️ /ejecutar [nombre] — Prompt MVP\n"
                        "⚔️ /comparar [A] vs [B] — Compara ideas\n"
                        "🔍 /buscar [palabra] — Buscar ideas\n"
                        "🌐 /tendencias — Tendencias tech\n"
                        "🔄 /cola — Cola Notion pendiente\n"
                        "🧠 /aprender — Aprendizaje manual\n"
                        "🔧 /mejoras — Historial auto-mejoras\n"
                        "⏪ /rollback — Revertir ultima mejora\n"
                        "🤖 /mejorar — Forzar auto-mejora ahora\n"
                        "🐛 /debug — Diagnostico completo\n\n"
                        "Feedback: 👍 👎 🔖 en cada idea\n"
                        "Auto-reparacion activa 24/7"
                    )

                elif tl.startswith("/idea"):
                    raw  = text[5:].strip()
                    tema = _limpiar_tema(raw) if raw else ""
                    if not tema:
                        enviar(chat, "💡 Ejemplo: /idea salud\n/idea mascotas\n/idea fintech")
                    else:
                        enviar(chat, f"⏳ Generando idea sobre '{tema}'...\nEspera 60-120s ☕")
                        threading.Thread(target=ejecutar_idea, args=(tema, chat), daemon=True).start()

                elif tl == "/debug":
                    threading.Thread(target=ejecutar_debug, args=(chat,), daemon=True).start()

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

                elif tl.startswith("/comparar"):
                    txt_cmp = text[9:].strip()
                    if not txt_cmp:
                        enviar(chat, "❓ Uso: /comparar Idea1 vs Idea2")
                    else:
                        cmd_comparar(chat, txt_cmp)

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
                    threading.Thread(target=cmd_aprender, args=(chat,), daemon=True).start()

                elif tl == "/mejoras":
                    cmd_mejoras(chat)

                elif tl == "/rollback":
                    try:
                        from agents.auto_improver import rollback_ultimo_fix
                        threading.Thread(
                            target=rollback_ultimo_fix,
                            kwargs={"telegram_fn": enviar, "chat_id": chat},
                            daemon=True
                        ).start()
                        enviar(chat, "⏪ Ejecutando rollback...")
                    except Exception as e:
                        enviar(chat, f"❌ {e}")

                elif tl == "/mejorar":
                    enviar(chat, "🤖 Iniciando ciclo de auto-mejora proactiva...")
                    def _mejora():
                        try:
                            from agents.auto_improver import ciclo_auto_mejora
                            ok = ciclo_auto_mejora(telegram_fn=enviar, chat_id=chat)
                            if not ok:
                                enviar(chat, "ℹ️ Sin mejora con confianza suficiente ahora.")
                        except Exception as e:
                            enviar(chat, f"❌ {e}")
                    threading.Thread(target=_mejora, daemon=True).start()

                else:
                    tema_nlp = ""
                    if any(x in tl for x in ["genera","idea","dame"]):
                        tema_nlp = _limpiar_tema(tl)
                    elif any(x in tl for x in ["ranking","ejecutable"]):
                        cmd_ranking(chat); continue
                    elif any(x in tl for x in ["top","mejor"]):
                        cmd_top(chat); continue
                    elif any(x in tl for x in ["busca","buscar"]):
                        q = re.sub(r"busca[r]?\s*","",tl).strip()
                        cmd_buscar(chat,q) if q else enviar(chat,"❓ /buscar fintech")
                        continue
                    elif "tendencia" in tl:
                        cmd_tendencias(chat); continue
                    elif "stats" in tl or "estadistic" in tl:
                        cmd_stats(chat); continue
                    elif "status" in tl or "estado" in tl:
                        cmd_status(chat); continue

                    if tema_nlp and len(tema_nlp) > 2:
                        enviar(chat, f"⏳ Generando idea sobre '{tema_nlp}'...\nEspera 60-120s ☕")
                        threading.Thread(target=ejecutar_idea, args=(tema_nlp, chat), daemon=True).start()
                    else:
                        enviar(chat,
                            "🤖 No entendi. Prueba:\n"
                            "• /idea [tema]\n"
                            "• /ranking\n"
                            "• /comparar A vs B\n"
                            "O usa /start."
                        )

        except Exception as e:
            print(f"Bot loop: {e}")
            time.sleep(5)

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    try:
        from agents.health_server import iniciar_health_server
        iniciar_health_server()
    except Exception as e:
        print(f"Health server: {e}")

    try:
        from agents.knowledge_base import migrar_si_necesario, get_stats
        migrar_si_necesario()
        stats = get_stats()
        if TELEGRAM_CHAT:
            enviar(TELEGRAM_CHAT,
                f"🔄 KB migrada\n"
                f"✅ {stats.get('total_ideas',0)} ideas | "
                f"Promedio: {stats.get('score_promedio',0)}/100\n"
                f"⭐ Mejor: {stats.get('mejor_idea','?')}"
            )
    except Exception as e:
        print(f"Migracion KB: {e}")

    if TELEGRAM_CHAT:
        enviar(TELEGRAM_CHAT,
            f"🟢 <b>Monitor ValidationIdea v6 arrancado</b>\n\n"
            f"✅ Ideas cada {INTERVALO_MIN} min — verticales rotativos\n"
            f"✅ Anti-placeholders + calidad garantizada\n"
            f"✅ Watchdog + auto-reparacion\n"
            f"✅ Auto-mejora via Groq + git push\n"
            f"✅ Notion retry automatico cada 10 min\n"
            f"✅ Alerta especial ideas +85 puntos\n"
            f"✅ /comparar, /mejoras, /rollback, /mejorar\n"
            f"✅ Health check HTTP activo\n"
            f"✅ Log 09:00 + Aprendizaje 08:00\n\n"
            f"📱 /start para ver todos los comandos"
        )

    threading.Thread(target=bot_loop,           daemon=True).start()
    threading.Thread(target=aprendizaje_diario,  daemon=True).start()
    threading.Thread(target=log_diario,           daemon=True).start()
    threading.Thread(target=monitor_watchdog,     daemon=True).start()
    threading.Thread(target=_notion_retry_loop,   daemon=True).start()

    print(f"✅ Loop principal: ideas cada {INTERVALO_MIN} min")
    while True:
        try:
            print(f"\n⏰ {datetime.now().strftime('%H:%M')} — ciclo automatico")
            ejecutar_idea(tema="", chat_id=TELEGRAM_CHAT)
        except Exception as e:
            print(f"Loop principal: {e}")
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT, f"⚠️ Error loop: {str(e)[:100]}")
        time.sleep(INTERVALO_MIN * 60)

if __name__ == "__main__":
    main()

# fin monitor_nocturno.py v6
