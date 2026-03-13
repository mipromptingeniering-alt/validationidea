import os, sys, json, time, subprocess, threading, re
from datetime import datetime, timedelta

os.environ["PYTHONUTF8"] = "1"

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT  = os.environ.get("TELEGRAM_CHAT_ID", "")
INTERVALO_MIN  = int(os.environ.get("INTERVALO_MINUTOS", "30"))

# ── Telegram helpers ─────────────────────────────────────────────────────────

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

def _safe_str(valor):
    """Convierte cualquier tipo a string de forma segura."""
    if valor is None:
        return ""
    if isinstance(valor, str):
        return valor
    if isinstance(valor, list):
        return " ".join(str(v) for v in valor)
    return str(valor)

def _limpiar_tema(texto):
    texto = _safe_str(texto).strip().lower()
    for quitar in ["/idea", "genera una idea sobre", "genera una idea de",
                   "genera idea sobre", "genera idea de", "dame una idea sobre",
                   "dame una idea de", "idea sobre", "idea de", "genera", "idea"]:
        if texto.startswith(quitar):
            texto = texto[len(quitar):].strip()
    return texto.strip()

def _botones_feedback(idea_nombre):
    safe = _safe_str(idea_nombre).replace(" ", "_")[:40]
    return {"inline_keyboard": [[
        {"text": "👍 Buena",   "callback_data": f"like_{safe}"},
        {"text": "👎 Mala",    "callback_data": f"dislike_{safe}"},
        {"text": "🔖 Guardar", "callback_data": f"save_{safe}"},
    ]]}

def _extraer_datos_salida(salida):
    salida = _safe_str(salida)
    def _get(tag):
        m = re.search(rf"^{tag}:(.+)$", salida, re.MULTILINE)
        return _safe_str(m.group(1)).strip() if m else ""
    score_str = _get("SCORE_FINAL")
    try:   score = float(score_str)
    except: score = 0
    m = re.search(r"Sincronizada: (.+)$", salida, re.MULTILINE)
    nombre = _safe_str(m.group(1)).strip() if m else ""
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
        "mrr_m12": _get("MRR_M12"),
        "mrr_m12":           _get("MRR_M12"),
    }

def _fmt_mensaje_idea(d):
    score  = d.get("score", 0)
    nombre = _safe_str(d.get("nombre", "?"))
    if   score >= 90: emoji = "💎"
    elif score >= 85: emoji = "⭐"
    elif score >= 80: emoji = "🔥"
    elif score >= 75: emoji = "✅"
    else:             emoji = "💡"

    lineas = [
        f"{emoji} <b>{nombre} — {score}/100</b>",
        f"<i>\"{_safe_str(d.get('tagline', ''))}\"</i>",
        "",
        f"❗ <b>Problema:</b> {_safe_str(d.get('problema', ''))[:220]}",
    ]
    if d.get("herramienta_ia"):
        lineas.append(f"🤖 <b>IA clave:</b> {_safe_str(d['herramienta_ia'])[:160]}")
    if d.get("monetiz_s1"):
        lineas.append(f"💰 <b>Semana 1:</b> {_safe_str(d['monetiz_s1'])[:220]}")
    if d.get("hipotesis"):
        lineas.append(f"🧪 <b>Test 48h:</b> {_safe_str(d['hipotesis'])[:220]}")
    if d.get("veredicto_critico"):
    if d.get("mrr_m12") and d.get("mrr_m12") != "0":
        lineas.append(f"💹 <b>MRR mes12:</b> {d[chr(109)+chr(114)+chr(114)+chr(95)+chr(109)+chr(49)+chr(50)]}EUR")
        lineas.append(f"✅ <b>Veredicto YC:</b> {_safe_str(d['veredicto_critico'])[:180]}")
    if d.get("recomendacion"):
        lineas.append(f"🏷 <b>Recomendacion:</b> {_safe_str(d['recomendacion']).upper()}")
    if d.get("notion_url"):
    if d.get("mrr_m12") and d.get("mrr_m12","0") != "0":
        lineas.append(f"💹 <b>MRR mes12:</b> {_safe_str(d["mrr_m12"])}EUR")
        lineas.append(f"\n📋 <a href=\"{d['notion_url']}\">Ver informe completo en Notion</a>")
    else:
        lineas.append("\n⚠️ Notion: en cola de reintento automatico")
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
                                f"Notion retry OK: {row.get('nombre_idea','?')}\n"
                                f"<a href=\"{url}\">Ver en Notion</a>"
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
                print(f"Notion retry: {exitos} ideas subidas")
        except Exception as e:
            print(f"Notion retry loop: {e}")

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
            # SIEMPRE convertir a string antes de strip
            if not isinstance(vertical, str):
                vertical = str(vertical[0]) if isinstance(vertical, list) and vertical else str(vertical or "")
            vertical = vertical.strip()
            env["IDEA_TOPIC"] = vertical
            print(f"Vertical rotativo: {vertical}")
        except Exception as e:
            print(f"Rotacion vertical: {e}")
            env["IDEA_TOPIC"] = ""
    else:
        tema = _safe_str(tema).strip()
        env["IDEA_TOPIC"] = tema

    t0 = time.time()
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, text=True,
            timeout=420, env=env,
            encoding="utf-8", errors="replace",
        )
        salida = _safe_str(resultado.stdout) + _safe_str(resultado.stderr)
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
            enviar(chat_id, f"Generada pero sin datos extraibles.\n{salida[-400:]}")
            return False
        try:
            from agents.verticales_rotacion import registrar_vertical_usado
            registrar_vertical_usado(_safe_str(env.get("IDEA_TOPIC", "")))
        except: pass

        msg  = _fmt_mensaje_idea(d)
        msg += f"\n\n<i>Generada en {elapsed}s</i>"
        mkup = _botones_feedback(d["nombre"])
        enviar(chat_id, msg, reply_markup=mkup)

        if d.get("score", 0) >= 85:
            enviar(chat_id,
                f"ALERTA IDEA TOP — {d['score']}/100\n"
                f"Usa /ejecutar {d['nombre']} para el prompt MVP completo."
            )
        return True
    else:
        if "TIMEOUT" in salida:
            n_timeouts = registrar_timeout() if wd_ok else 0
            enviar(chat_id,
                f"Timeout (>{elapsed}s) — reintento en {INTERVALO_MIN} min. "
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
                           if "Error" in l or "error" in l.lower()]
            error_msg = error_lines[-1][:250] if error_lines else salida[-300:]
            enviar(chat_id, f"❌ Error\n\n{error_msg}\n\nUsa /debug.")
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
    enviar(chat_id, "Ejecutando diagnostico completo — espera 60s...")

    try:
        from agents.watchdog import get_diagnostico
        d = get_diagnostico()
        enviar(chat_id,
            f"<b>Estado Watchdog</b>\n"
            f"Timeouts consecutivos: {d['consecutive_timeouts']}\n"
            f"Ultimo exito: {d['last_success']}\n"
            f"OK hoy: {d['total_ok_24h']}\n"
            f"Modo emergencia: {'SI' if d['modo_emergencia'] else 'NO'}\n"
            f"Ciclo reparacion: {d['ciclo_reparacion']}\n"
            f"Ultimas ideas: {', '.join(d['ultimas_ideas'][-3:]) or 'ninguna'}\n"
            f"Verticales saturados: {', '.join(d['verticales_saturados']) or 'ninguno'}\n"
            f"Errores recientes:\n" + "\n".join(f"  {e}" for e in d["errores_recientes"][-4:])
        )
    except Exception as e:
        enviar(chat_id, f"Watchdog: {e}")

    try:
        from agents.verticales_rotacion import get_stats_rotacion
        r = get_stats_rotacion()
        enviar(chat_id,
            f"<b>Rotacion Vertical</b>\n"
            f"Ciclo: {r['ciclo_actual']} | "
            f"Disponibles: {r['disponibles_restantes']}/{r['total_disponibles']}\n"
            f"Ultimos 5: {', '.join(r['ultimos_5']) or 'ninguno'}"
        )
    except Exception as e:
        enviar(chat_id, f"Rotacion: {e}")

    try:
        from agents.auto_improver import get_historial_mejoras
        h = get_historial_mejoras()
        enviar(chat_id,
            f"<b>Auto-mejoras</b>\n"
            f"Total: {h['total_mejoras']} | Hoy: {h['total_hoy']}/{h['limite_dia']}\n"
            f"Rollbacks: {h['rollbacks']}"
        )
    except Exception as e:
        enviar(chat_id, f"Auto-improver: {e}")

    vars_lineas = []
    for v in ["GROQ_API_KEY","TELEGRAM_BOT_TOKEN","TELEGRAM_CHAT_ID","NOTION_TOKEN","NOTION_DATABASE_ID"]:
        val    = os.environ.get(v, "")
        estado = "OK" if val else "NO CONFIGURADA"
        vars_lineas.append(f"{v}: {estado}")
    enviar(chat_id, "<b>Variables Railway</b>\n" + "\n".join(vars_lineas))

    env = os.environ.copy()
    env["IDEA_TOPIC"] = "fintech"
    try:
        resultado = subprocess.run(
            [sys.executable, "run_batch.py"],
            capture_output=True, text=True,
            timeout=420, env=env,
            encoding="utf-8", errors="replace",
        )
        salida = _safe_str(resultado.stdout) + _safe_str(resultado.stderr)
        ok     = resultado.returncode == 0
    except subprocess.TimeoutExpired:
        salida = "TIMEOUT >420s"
        ok     = False
    except Exception as e:
        salida = str(e)
        ok     = False

    datos   = _extraer_datos_salida(salida)
    ok_str  = "OK 0" if ok else "ERROR 1"
    nom_str = datos["nombre"] if datos["nombre"] else "No encontrada"
    sco_str = str(datos["score"]) if datos["score"] else "sin score"
    not_str = datos["notion_url"][:50] if datos["notion_url"] else "Sin URL"
    ver_str = datos["veredicto_critico"][:60] if datos["veredicto_critico"] else "sin veredicto"
    output  = salida[-2000:] if len(salida) > 2000 else salida

    enviar(chat_id,
        f"<b>Debug run_batch.py</b>\n"
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
            enviar(chat_id, "No hay ideas. Usa /idea [tema]")
            return
        lineas = ["<b>Top 5 mejores ideas</b>\n"]
        for i, idea in enumerate(ideas, 1):
            s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            n = _safe_str(idea.get("nombre","?"))
            t = _safe_str(idea.get("tagline",""))[:80]
            lineas.append(f"{i}. <b>{n}</b> — {s}/100\n   <i>{t}</i>")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

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
            f"<b>Estadisticas KB</b>\n\n"
            f"Total ideas: {s.get('total_ideas',0)}\n"
            f"Score promedio: {s.get('score_promedio',0)}/100\n"
            f"Mejor idea: {s.get('mejor_idea','?')} ({s.get('mejor_score',0)}/100)\n"
            f"Ideas esta semana: {s.get('ideas_semana',0)}\n"
            f"Verticales top: {', '.join(s.get('verticales_top',[])[:3]) or 'N/A'}"
            + rot_txt
        )
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_ranking(chat_id):
    try:
        from agents.knowledge_base import get_top_ejecutables
        ideas = get_top_ejecutables(5)
        if not ideas:
            enviar(chat_id, "No hay ideas.")
            return
        lineas = ["<b>Top 5 mas ejecutables HOY</b>\n"]
        for i, idea in enumerate(ideas, 1):
            scores = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
            ej   = scores.get("ejecutabilidad",0)
            sc   = scores.get("score_total",0)
            n    = _safe_str(idea.get("nombre","?"))
            em   = idea.get("estrategia_monetizacion",{})
            sem1 = _safe_str(em.get("semana1","") if isinstance(em,dict) else "")[:130]
            herr = _safe_str(idea.get("herramienta_ia_clave",""))[:80]
            lineas.append(f"{i}. <b>{n}</b> — Ejec: {ej}/100 | Score: {sc}/100")
            if herr: lineas.append(f"   {herr}")
            if sem1: lineas.append(f"   {sem1}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_ejecutar(chat_id, nombre_idea):
    try:
        from agents.knowledge_base import buscar_idea
        idea = buscar_idea(nombre_idea)
        if not idea:
            enviar(chat_id, f"No encontre '{nombre_idea}'. Usa /buscar [palabra]")
            return
        pm = idea.get("prompt_mvp",{})
        if isinstance(pm, str):
            try:   pm = json.loads(pm)
            except: pm = {}
        if isinstance(pm, dict):
            meta       = pm.get("meta",{}) if isinstance(pm.get("meta"),dict) else {}
            ia_rec     = _safe_str(meta.get("ia_recomendada","Claude 3.5 Sonnet en Cursor"))
            sys_p      = _safe_str(pm.get("system_prompt",""))[:400]
            script_cli = _safe_str(pm.get("primer_cliente_script",""))[:300]
            pasos      = pm.get("instrucciones_paso_a_paso",[])[:5]
            pasos_str  = "\n".join(f"  {_safe_str(p)}" for p in pasos)
            enviar(chat_id,
                f"<b>Prompt MVP: {_safe_str(idea.get('nombre',''))}</b>\n\n"
                f"IA: {ia_rec}\n\n"
                f"System prompt:\n<code>{sys_p}</code>\n\n"
                f"Pasos:\n{pasos_str}\n\n"
                f"Primer cliente:\n{script_cli}"[:4096]
            )
        else:
            enviar(chat_id, f"Sin prompt MVP para '{nombre_idea}'")
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_comparar(chat_id, texto):
    partes = re.split(r"\s+vs\.?\s+", texto, flags=re.IGNORECASE)
    if len(partes) < 2:
        enviar(chat_id, "Uso: /comparar NombreA vs NombreB")
        return
    try:
        ruta = "data/ideas.json"
        if not os.path.exists(ruta):
            enviar(chat_id, "Sin ideas aun.")
            return
        with open(ruta,"r",encoding="utf-8") as f:
            todas = json.load(f)

        def _buscar(nombre):
            n = _safe_str(nombre).strip().lower()
            for idea in todas:
                if n in _safe_str(idea.get("nombre","")).lower():
                    return idea
            return None

        a = _buscar(partes[0])
        b = _buscar(partes[1])
        if not a:
            enviar(chat_id, f"No encontre '{partes[0]}'"); return
        if not b:
            enviar(chat_id, f"No encontre '{partes[1]}'"); return

        def _sc(idea):
            return idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
        def _em(idea):
            e = idea.get("estrategia_monetizacion",{})
            return e if isinstance(e,dict) else {}

        lineas = [f"<b>{_safe_str(a['nombre'])} vs {_safe_str(b['nombre'])}</b>\n"]
        for label, va, vb in [
            ("Score total",    _sc(a).get("score_total",0),    _sc(b).get("score_total",0)),
            ("Ejecutabilidad", _sc(a).get("ejecutabilidad",0), _sc(b).get("ejecutabilidad",0)),
            ("Monetizacion",   _sc(a).get("monetizacion",0),   _sc(b).get("monetizacion",0)),
            ("Viral",          _sc(a).get("viral",0),          _sc(b).get("viral",0)),
            ("Timing",         _sc(a).get("timing",0),         _sc(b).get("timing",0)),
        ]:
            w = "izq" if va > vb else "der" if vb > va else "empate"
            lineas.append(f"<b>{label}:</b> {va} vs {vb} [{w}]")

        lineas.append(f"\n<b>Pricing A:</b> {_safe_str(_em(a).get('precio_optimo_justificado','?'))[:80]}")
        lineas.append(f"<b>Pricing B:</b> {_safe_str(_em(b).get('precio_optimo_justificado','?'))[:80]}")

        sc_a = _sc(a).get("score_total",0)
        sc_b = _sc(b).get("score_total",0)
        if sc_a > sc_b:
            lineas.append(f"\nGanadora: <b>{_safe_str(a['nombre'])}</b> (+{sc_a-sc_b} pts)")
        elif sc_b > sc_a:
            lineas.append(f"\nGanadora: <b>{_safe_str(b['nombre'])}</b> (+{sc_b-sc_a} pts)")
        else:
            lineas.append("\nEmpate — decide por ejecutabilidad")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_buscar(chat_id, palabra):
    try:
        ruta = "data/ideas.json"
        if not os.path.exists(ruta):
            enviar(chat_id, "Sin ideas aun."); return
        with open(ruta,"r",encoding="utf-8") as f:
            todas = json.load(f)
        p = _safe_str(palabra).strip().lower()
        encontradas = [
            i for i in todas
            if p in _safe_str(i.get("nombre","")).lower()
            or p in _safe_str(i.get("problema","")).lower()
            or p in _safe_str(i.get("vertical","")).lower()
        ]
        if not encontradas:
            enviar(chat_id, f"Sin resultados para '{palabra}'"); return
        lineas = [f"<b>Resultados para '{palabra}'</b>\n"]
        for idea in encontradas[-5:]:
            s = idea.get("scores",{}).get("score_total",0) if isinstance(idea.get("scores"),dict) else 0
            lineas.append(f"- <b>{_safe_str(idea.get('nombre','?'))}</b> ({s}/100)")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_tendencias(chat_id):
    try:
        from agents.trend_scout import get_tendencias
        tends = get_tendencias()
        lineas = ["<b>Tendencias tech actuales</b>\n"]
        for t in tends[:10]:
            lineas.append(f"- {_safe_str(t)[:100]}")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_cola(chat_id):
    try:
        cola_path = "data/cola_pendientes.csv"
        if not os.path.exists(cola_path):
            enviar(chat_id, "Cola Notion vacia."); return
        import csv
        with open(cola_path,"r",encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            enviar(chat_id, "Cola Notion vacia."); return
        lineas = [f"<b>Cola Notion: {len(rows)} pendientes</b>\n"]
        for row in rows[-5:]:
            lineas.append(
                f"- {_safe_str(row.get('nombre_idea','?'))} "
                f"(intentos: {row.get('intentos','?')})"
            )
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_aprender(chat_id):
    enviar(chat_id, "Ejecutando aprendizaje ahora...")
    try:
        from agents.weekly_learner import analizar_y_aprender
        r = analizar_y_aprender()
        enviar(chat_id,
            f"<b>Aprendizaje completado</b>\n\n"
            f"Ciclo {r['ciclo']} | {r['total_ideas']} ideas | "
            f"{r['ideas_exitosas']} exitosas ({r['pct_exito']}%)\n"
            f"Score: {r['score_anterior']} -> Objetivo: {r['score_objetivo']}\n"
            f"Verticales TOP: {', '.join(r['nuevos_pesos'].get('verticales_preferidas',[])[:3]) or 'N/A'}\n"
            f"Penalizadas: {', '.join(r['nuevos_pesos'].get('verticales_penalizadas',[])[:3]) or 'ninguna'}\n"
            f"Tags: {', '.join(r['nuevos_pesos'].get('tags_exitosos',[])[:5]) or 'N/A'}\n"
            f"Temperatura: {r['nuevos_pesos'].get('temperatura_groq',0.85)} | "
            f"Umbral dup: {r['nuevos_pesos'].get('umbral_duplicado',0.38)}"
        )
    except Exception as e:
        enviar(chat_id, f"Error aprendizaje: {e}")

def cmd_mejoras(chat_id):
    try:
        from agents.auto_improver import get_historial_mejoras
        h = get_historial_mejoras()
        lineas = [
            f"<b>Auto-mejoras aplicadas</b>\n",
            f"Total: {h['total_mejoras']} | Hoy: {h['total_hoy']}/{h['limite_dia']}",
            f"Rollbacks: {h['rollbacks']}",
            "\nUltimas mejoras:",
        ]
        for m in h.get("ultimas_5",[]):
            lineas.append(
                f"- {_safe_str(m.get('descripcion','?'))[:60]} "
                f"({m.get('confianza','?')}%)"
            )
        if not h.get("ultimas_5"):
            lineas.append("(ninguna aun)")
        enviar(chat_id, "\n".join(lineas))
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_rollback(chat_id):
    enviar(chat_id, "Ejecutando rollback de la ultima mejora...")
    try:
        from agents.auto_improver import rollback_ultimo_fix
        ok = rollback_ultimo_fix(telegram_fn=enviar, chat_id=chat_id)
        if not ok:
            enviar(chat_id, "No se pudo hacer rollback o no hay mejoras previas.")
    except Exception as e:
        enviar(chat_id, f"Error rollback: {e}")

def cmd_mejorar(chat_id):
    enviar(chat_id, "Forzando ciclo de auto-mejora proactiva...")
    try:
        from agents.auto_improver import ciclo_auto_mejora
        threading.Thread(
            target=ciclo_auto_mejora,
            kwargs={"telegram_fn": enviar, "chat_id": chat_id},
            daemon=True
        ).start()
    except Exception as e:
        enviar(chat_id, f"Error: {e}")

def cmd_status(chat_id):
    try:
        from agents.watchdog import get_diagnostico
        from agents.knowledge_base import get_stats
        d = get_diagnostico()
        s = get_stats()
        modo = "EMERGENCIA" if d["modo_emergencia"] else "NORMAL"
        enviar(chat_id,
            f"<b>Estado del sistema</b>\n\n"
            f"Modo: {modo}\n"
            f"OK hoy: {d['total_ok_24h']} | Fallos: {d['total_fail_24h']}\n"
            f"Ultimo exito: {d['last_success']}\n"
            f"Total ideas KB: {s.get('total_ideas',0)}\n"
            f"Score promedio: {s.get('score_promedio',0)}/100\n"
            f"Timeouts: {d['consecutive_timeouts']} | Fallos: {d['consecutive_failures']}\n"
            f"Proximo ciclo: en {INTERVALO_MIN} min"
        )
    except Exception as e:
        enviar(chat_id, f"Error status: {e}")

# ── Loop Telegram ─────────────────────────────────────────────────────────────

def _procesar_callback(callback, chat_id):
    data  = _safe_str(callback.get("data",""))
    msg_id = callback.get("message",{}).get("message_id")
    if data.startswith("like_"):
        nombre = data[5:].replace("_"," ")
        try:
            from agents.knowledge_base import registrar_feedback
            registrar_feedback(nombre, positivo=True)
        except: pass
        enviar(chat_id, f"Feedback positivo registrado para '{nombre}'")
    elif data.startswith("dislike_"):
        nombre = data[8:].replace("_"," ")
        try:
            from agents.knowledge_base import registrar_feedback
            registrar_feedback(nombre, positivo=False)
            from agents.watchdog import bloquear_nombre
            bloquear_nombre(nombre)
        except: pass
        enviar(chat_id, f"Feedback negativo registrado. '{nombre}' bloqueada.")
    elif data.startswith("save_"):
        nombre = data[5:].replace("_"," ")
        enviar(chat_id, f"Idea '{nombre}' guardada como favorita.")
    try:
        _post("answerCallbackQuery", {"callback_query_id": callback["id"]})
    except: pass


def cmd_resubir(chat_id):
    enviar(chat_id, "Resubiendo ideas pendientes a Notion...")
    try:
        import csv
        from agents.notion_sync_agent import sync_idea_to_notion
        cola_path = "data/cola_pendientes.csv"
        ruta_ideas = "data/ideas.json"
        exitos = 0
        # Reintentar cola
        if os.path.exists(cola_path):
            with open(cola_path,"r",encoding="utf-8") as f:
                rows = list(csv.DictReader(f))
            pendientes = []
            for row in rows:
                try:
                    idea = json.loads(row.get("datos_json","{}"))
                    url = sync_idea_to_notion(idea)
                    if url:
                        exitos += 1
                    else:
                        pendientes.append(row)
                except:
                    pendientes.append(row)
            with open(cola_path,"w",newline="",encoding="utf-8") as f:
                w = csv.DictWriter(f,fieldnames=["timestamp","nombre_idea","intentos","error","datos_json"])
                w.writeheader(); w.writerows(pendientes)
        # Reintentar ultimas 5 ideas sin URL
        if os.path.exists(ruta_ideas):
            with open(ruta_ideas,"r",encoding="utf-8") as f:
                todas = json.load(f)
            for idea in todas[-5:]:
                if not idea.get("notion_url"):
                    url = sync_idea_to_notion(idea)
                    if url:
                        idea["notion_url"] = url
                        exitos += 1
            with open(ruta_ideas,"w",encoding="utf-8") as f:
                json.dump(todas, f, ensure_ascii=False, indent=2)
        enviar(chat_id, f"Resubida completada: {exitos} ideas subidas a Notion.")
    except Exception as e:
        enviar(chat_id, f"Error resubir: {e}")

def _loop_telegram():
    offset = 0
    print("Escuchando comandos Telegram...")
    while True:
        try:
            resp    = get_updates(offset)
            updates = resp.get("result", [])
            for upd in updates:
                offset = upd["update_id"] + 1
                if "callback_query" in upd:
                    cb      = upd["callback_query"]
                    chat_id = str(cb.get("message",{}).get("chat",{}).get("id",""))
                    _procesar_callback(cb, chat_id)
                    continue
                msg     = upd.get("message", {})
                chat_id = str(msg.get("chat",{}).get("id",""))
                texto   = _safe_str(msg.get("text","")).strip()
                if not texto or not chat_id:
                    continue

                texto_lower = texto.lower()

                if texto_lower == "/start":
                    enviar(chat_id,
                        "<b>ValidationIdea Bot v6</b>\n\n"
                        "Comandos:\n"
                        "💡 /idea [tema] — Genera idea\n"
                        "📊 /status — Estado del sistema\n"
                        "🏆 /top — Top 5 mejores ideas\n"
                        "📋 /stats — Estadisticas KB\n"
                        "🚀 /ranking — Top 5 mas ejecutables\n"
                        "🛠️ /ejecutar [nombre] — Prompt MVP\n"
                        "⚔️ /comparar [A] vs [B] — Compara 2 ideas\n"
                        "🔍 /buscar [palabra] — Buscar ideas\n"
                        "🌐 /tendencias — Tendencias tech\n"
                        "🔄 /cola — Ideas pendientes Notion\n"
                        "🧠 /aprender — Aprendizaje manual\n"
                        "🔧 /mejoras — Historial auto-mejoras\n"
                        "⏪ /rollback — Revertir ultima mejora\n"
                        "🤖 /mejorar — Forzar auto-mejora ahora\n"
                        "🐛 /debug — Diagnostico completo\n\n"
                        "Feedback: 👍 / 👎 / 🔖\n"
                        "Auto-reparacion activa 24/7"
                    )
                elif texto_lower.startswith("/idea"):
                    tema = _limpiar_tema(texto[5:].strip())
                    enviar(chat_id,
                        f"Generando idea{' sobre ' + repr(tema) if tema else ''}...\n"
                        f"Espera 60-120s"
                    )
                    threading.Thread(
                        target=ejecutar_idea,
                        kwargs={"tema": tema, "chat_id": chat_id},
                        daemon=True
                    ).start()
                elif texto_lower.startswith("idea ") or texto_lower.startswith("genera "):
                    tema = _limpiar_tema(texto)
                    enviar(chat_id,
                        f"Generando idea sobre '{tema}'...\nEspera 60-120s"
                    )
                    threading.Thread(
                        target=ejecutar_idea,
                        kwargs={"tema": tema, "chat_id": chat_id},
                        daemon=True
                    ).start()
                elif texto_lower == "/debug":
                    threading.Thread(target=ejecutar_debug, args=(chat_id,), daemon=True).start()
                elif texto_lower == "/status":
                    cmd_status(chat_id)
                elif texto_lower == "/top":
                    cmd_top(chat_id)
                elif texto_lower == "/stats":
                    cmd_stats(chat_id)
                elif texto_lower == "/ranking":
                    cmd_ranking(chat_id)
                elif texto_lower.startswith("/ejecutar"):
                    nombre = texto[9:].strip()
                    if nombre:
                        cmd_ejecutar(chat_id, nombre)
                    else:
                        enviar(chat_id, "Uso: /ejecutar NombreIdea")
                elif texto_lower.startswith("/comparar"):
                    contenido = texto[9:].strip()
                    if contenido:
                        cmd_comparar(chat_id, contenido)
                    else:
                        enviar(chat_id, "Uso: /comparar NombreA vs NombreB")
                elif texto_lower.startswith("/buscar"):
                    palabra = texto[7:].strip()
                    if palabra:
                        cmd_buscar(chat_id, palabra)
                    else:
                        enviar(chat_id, "Uso: /buscar palabra")
                elif texto_lower == "/tendencias":
                    cmd_tendencias(chat_id)
                elif texto_lower == "/cola":
                    cmd_cola(chat_id)
                elif texto_lower == "/resubir":
                    threading.Thread(target=cmd_resubir, args=(chat_id,), daemon=True).start()
                elif texto_lower == "/aprender":
                    threading.Thread(target=cmd_aprender, args=(chat_id,), daemon=True).start()
                elif texto_lower == "/mejoras":
                    cmd_mejoras(chat_id)
                elif texto_lower == "/rollback":
                    threading.Thread(target=cmd_rollback, args=(chat_id,), daemon=True).start()
                elif texto_lower == "/mejorar":
                    cmd_mejorar(chat_id)
                else:
                    # Texto libre — intentar como tema de idea
                    if len(texto) > 3 and not texto.startswith("/"):
                        tema = _limpiar_tema(texto)
                        if tema:
                            enviar(chat_id,
                                f"Generando idea sobre '{tema}'...\nEspera 60-120s"
                            )
                            threading.Thread(
                                target=ejecutar_idea,
                                kwargs={"tema": tema, "chat_id": chat_id},
                                daemon=True
                            ).start()
        except Exception as e:
            print(f"Loop Telegram: {e}")
            time.sleep(5)

# ── Health check HTTP ─────────────────────────────────────────────────────────

def _health_server():
    try:
        from http.server import HTTPServer, BaseHTTPRequestHandler
        class H(BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"OK")
            def log_message(self, *a): pass
        port = int(os.environ.get("PORT", 8080))
        HTTPServer(("0.0.0.0", port), H).serve_forever()
    except Exception as e:
        print(f"Health server: {e}")

# ── Log diario ────────────────────────────────────────────────────────────────

def _log_diario():
    while True:
        ahora = datetime.now()
        proxima = ahora.replace(hour=9, minute=0, second=0, microsecond=0)
        if ahora >= proxima:
            proxima += timedelta(days=1)
        time.sleep((proxima - ahora).total_seconds())
        try:
            from agents.knowledge_base import get_stats
            s = get_stats()
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT,
                    f"<b>Resumen diario — {datetime.now().strftime('%d/%m/%Y')}</b>\n\n"
                    f"Total ideas: {s.get('total_ideas',0)}\n"
                    f"Score promedio: {s.get('score_promedio',0)}/100\n"
                    f"Mejor: {s.get('mejor_idea','ninguna')} ({s.get('mejor_score',0)}/100)\n\n"
                    f"Usa /top para ver las mejores."
                )
        except Exception as e:
            print(f"Log diario: {e}")

# ── Aprendizaje automatico ────────────────────────────────────────────────────

def _aprendizaje_automatico():
    while True:
        ahora = datetime.now()
        proxima = ahora.replace(hour=8, minute=0, second=0, microsecond=0)
        if ahora >= proxima:
            proxima += timedelta(days=1)
        time.sleep((proxima - ahora).total_seconds())
        try:
            from agents.weekly_learner import analizar_y_aprender
            r = analizar_y_aprender()
            if TELEGRAM_CHAT:
                enviar(TELEGRAM_CHAT,
                    f"<b>Aprendizaje automatico completado</b>\n"
                    f"Ciclo {r['ciclo']} | {r['total_ideas']} ideas\n"
                    f"Score objetivo: {r['score_objetivo']}\n"
                    f"Verticales TOP: {', '.join(r['nuevos_pesos'].get('verticales_preferidas',[])[:3]) or 'N/A'}"
                )
        except Exception as e:
            print(f"Aprendizaje auto: {e}")

# ── Ciclo principal de generacion ─────────────────────────────────────────────

def _ciclo_generacion():
    while True:
        time.sleep(INTERVALO_MIN * 60)
        print(f"Ciclo automatico: {datetime.now().strftime('%H:%M')}")
        ejecutar_idea()

# ── Migracion KB ──────────────────────────────────────────────────────────────

def _migrar_kb():
    try:
        from agents.knowledge_base import migrar_si_necesario, get_stats
        migrar_si_necesario()
        s = get_stats()
        if TELEGRAM_CHAT:
            mejor = s.get("mejor_idea","ninguna")
            score = s.get("mejor_score",0)
            enviar(TELEGRAM_CHAT,
                f"KB migrada\n"
                f"{s.get('total_ideas',0)} ideas | Promedio: {s.get('score_promedio',0)}/100\n"
                f"Mejor: {mejor}"
            )
    except Exception as e:
        print(f"Migracion KB: {e}")

# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    _migrar_kb()

    if TELEGRAM_CHAT:
        enviar(TELEGRAM_CHAT,
            "<b>Monitor ValidationIdea v6 arrancado</b>\n\n"
            "Ideas cada 30 min — verticales rotativos\n"
            "Anti-placeholders + calidad garantizada\n"
            "Watchdog + auto-reparacion\n"
            "Auto-mejora via Groq + git push\n"
            "Notion retry automatico cada 10 min\n"
            "Alerta especial ideas +85 puntos\n"
            "/comparar, /mejoras, /rollback, /mejorar, /resubir\n"
            "Health check HTTP activo\n"
            "Log 09:00 + Aprendizaje 08:00\n\n"
            "/start para ver todos los comandos"
        )

    # Threads en background
    threading.Thread(target=_health_server,          daemon=True).start()
    threading.Thread(target=_notion_retry_loop,      daemon=True).start()
    threading.Thread(target=_log_diario,             daemon=True).start()
    threading.Thread(target=_aprendizaje_automatico, daemon=True).start()
    threading.Thread(target=_ciclo_generacion,       daemon=True).start()

    # Primera idea inmediata al arrancar
    threading.Thread(target=ejecutar_idea, daemon=True).start()

    # Loop principal Telegram (no daemon — mantiene el proceso vivo)
    _loop_telegram()

if __name__ == "__main__":
    main()

# fin monitor_nocturno.py
