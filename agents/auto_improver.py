"""
auto_improver.py - El sistema se repara y mejora solo via git push
Ciclo: detecta error → Groq genera fix → git commit → Railway redeploya
"""
import os, sys, json, subprocess, time, re
from datetime import datetime

GROQ_API_KEY    = os.environ.get("GROQ_API_KEY", "")
REPO_DIR        = os.environ.get("REPO_DIR", "/app")
MEJORAS_FILE    = "data/mejoras_aplicadas.json"
MAX_MEJORAS_DIA = 3

SISTEMA_AUTO_MEJORA = (
    "Eres un ingeniero senior de Python con 20 años de experiencia. "
    "Analizas errores de produccion y generas fixes exactos y completos. "
    "REGLA ABSOLUTA: responde UNICAMENTE con JSON valido. Sin texto extra."
)

def _cargar_historial():
    try:
        with open(MEJORAS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"mejoras": [], "total_hoy": 0, "ultimo_dia": "", "rollbacks": 0}

def _guardar_historial(h):
    os.makedirs("data", exist_ok=True)
    with open(MEJORAS_FILE, "w", encoding="utf-8") as f:
        json.dump(h, f, ensure_ascii=False, indent=2)

def _limite_alcanzado():
    h   = _cargar_historial()
    hoy = datetime.now().strftime("%Y-%m-%d")
    if h.get("ultimo_dia") != hoy:
        h["total_hoy"]  = 0
        h["ultimo_dia"] = hoy
        _guardar_historial(h)
        return False
    return h.get("total_hoy", 0) >= MAX_MEJORAS_DIA

def _run_git(args, cwd=REPO_DIR):
    try:
        r = subprocess.run(
            ["git"] + args, cwd=cwd,
            capture_output=True, text=True, timeout=30
        )
        return r.returncode == 0, (r.stdout + r.stderr).strip()
    except Exception as e:
        return False, str(e)

def _leer_archivo(ruta):
    try:
        with open(os.path.join(REPO_DIR, ruta), "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"ERROR LEYENDO: {e}"

def _escribir_archivo(ruta, contenido):
    try:
        ruta_completa = os.path.join(REPO_DIR, ruta)
        os.makedirs(os.path.dirname(ruta_completa), exist_ok=True)
        with open(ruta_completa, "w", encoding="utf-8") as f:
            f.write(contenido)
        return True
    except Exception as e:
        print(f"Error escribiendo {ruta}: {e}")
        return False

def _llamar_groq(prompt):
    try:
        import groq
        client = groq.Groq(api_key=GROQ_API_KEY, timeout=60)
        resp   = client.chat.completions.create(
            model       = "meta-llama/llama-4-scout-17b-16e-instruct",
            messages    = [
                {"role": "system", "content": SISTEMA_AUTO_MEJORA},
                {"role": "user",   "content": prompt},
            ],
            max_tokens  = 4000,
            temperature = 0.2,
        )
        content = resp.choices[0].message.content if resp.choices else ""
        if isinstance(content, list):
            content = " ".join(
                str(b.get("text", b.get("content", ""))) if isinstance(b, dict) else str(b)
                for b in content
            )
        c=content; return (c if isinstance(c,str) else ''.join(str(getattr(b,'text',b)) for b in c) if isinstance(c,list) else str(c or '')).strip()
    except Exception as e:
        print(f"Groq auto_improver: {e}")
        return ""

def _limpiar_json_respuesta(texto):
    if not isinstance(texto, str):
        return "{}"
    if "```json" in texto:
        texto = texto.split("```json")[1].split("```")[0].strip()
    elif "```" in texto:
        texto = texto.split("```")[1].split("```")[0].strip()
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1:
        return texto[inicio:fin+1]
    return texto

def analizar_error_y_generar_fix(error_log, archivo_afectado="run_batch.py"):
    codigo_actual = _leer_archivo(archivo_afectado)[:3000]
    prompt = (
        f"Analiza este error de produccion en Python en Railway:\n\n"
        f"ERROR LOG:\n{error_log[:800]}\n\n"
        f"CODIGO ACTUAL ({archivo_afectado}, primeros 3000 chars):\n{codigo_actual}\n\n"
        f"Genera el fix exacto. Responde con:\n"
        + '{"archivo":"run_batch.py",'
        + '"descripcion":"que hace el fix en 1 linea",'
        + '"tipo_error":"rate_limit/json_invalido/import_error/timeout/otro",'
        + '"confianza":85,'
        + '"codigo_completo_nuevo":"CODIGO PYTHON COMPLETO CORREGIDO",'
        + '"rollback_seguro":true}'
    )
    respuesta = _llamar_groq(prompt)
    if not respuesta:
        return None
    try:
        data = json.loads(_limpiar_json_respuesta(respuesta))
        if not data.get("codigo_completo_nuevo"):
            return None
        if data.get("confianza", 0) < 70:
            print(f"⚠️ Confianza baja ({data.get('confianza')}%) — fix descartado")
            return None
        return data
    except Exception as e:
        print(f"Fix JSON invalido: {e}")
        return None

def aplicar_fix(fix_data, telegram_fn=None, chat_id=None):
    if _limite_alcanzado():
        print(f"⚠️ Limite {MAX_MEJORAS_DIA} auto-mejoras/dia alcanzado")
        return False

    archivo     = fix_data.get("archivo", "run_batch.py")
    codigo      = fix_data.get("codigo_completo_nuevo", "")
    descripcion = fix_data.get("descripcion", "auto-fix")
    confianza   = fix_data.get("confianza", 0)

    if not codigo or len(codigo) < 100:
        print("❌ Codigo vacio — fix abortado")
        return False

    ok, commit_actual = _run_git(["rev-parse", "HEAD"])
    commit_antes      = commit_actual.strip() if ok else ""
    codigo_original   = _leer_archivo(archivo)

    print(f"🔧 Aplicando fix: {descripcion} (confianza {confianza}%)")

    if not _escribir_archivo(archivo, codigo):
        print("❌ No se pudo escribir el archivo")
        return False

    ok_add,    _ = _run_git(["add", archivo])
    ok_commit, _ = _run_git(["commit", "-m",
        f"auto-fix: {descripcion[:60]} [conf={confianza}%] [{datetime.now().strftime('%H:%M')}]"
    ])
    ok_push, out_push = _run_git(["push"])

    if not (ok_add and ok_commit and ok_push):
        print(f"❌ Git push fallido ({out_push}) — revirtiendo localmente")
        _escribir_archivo(archivo, codigo_original)
        return False

    h = _cargar_historial()
    h["mejoras"].append({
        "timestamp":    datetime.now().isoformat(),
        "archivo":      archivo,
        "descripcion":  descripcion,
        "confianza":    confianza,
        "commit_antes": commit_antes,
        "tipo_error":   fix_data.get("tipo_error", "?"),
    })
    h["total_hoy"]  = h.get("total_hoy", 0) + 1
    h["ultimo_dia"] = datetime.now().strftime("%Y-%m-%d")
    _guardar_historial(h)

    msg = (
        f"🔧 <b>Auto-mejora aplicada</b>\n\n"
        f"Fix: {descripcion}\n"
        f"Archivo: {archivo}\n"
        f"Confianza: {confianza}%\n"
        f"Tipo: {fix_data.get('tipo_error','?')}\n"
        f"Mejoras hoy: {h['total_hoy']}/{MAX_MEJORAS_DIA}\n\n"
        f"⏳ Railway redesplegando en ~2 min"
    )
    print(msg.replace("<b>","").replace("</b>",""))
    if telegram_fn and chat_id:
        try: telegram_fn(chat_id, msg)
        except: pass

    return True

def rollback_ultimo_fix(telegram_fn=None, chat_id=None):
    h = _cargar_historial()
    if not h.get("mejoras"):
        print("Sin mejoras que revertir")
        return False

    ultima       = h["mejoras"][-1]
    commit_antes = ultima.get("commit_antes", "")
    if not commit_antes:
        print("Sin commit de referencia")
        return False

    print(f"⏪ Rollback al commit {commit_antes[:8]}...")
    ok_reset, _ = _run_git(["reset", "--hard", commit_antes])
    ok_push,  _ = _run_git(["push", "--force"])

    if ok_reset and ok_push:
        h["rollbacks"] = h.get("rollbacks", 0) + 1
        h["mejoras"].pop()
        _guardar_historial(h)
        msg = (
            f"⏪ <b>Rollback completado</b>\n\n"
            f"Revertido: {ultima.get('descripcion','?')}\n"
            f"Commit restaurado: {commit_antes[:8]}\n"
            f"Total rollbacks: {h['rollbacks']}"
        )
        if telegram_fn and chat_id:
            try: telegram_fn(chat_id, msg)
            except: pass
        return True

    print("❌ Rollback fallido")
    return False

def generar_mejora_proactiva(metricas):
    prompt = (
        f"Eres el arquitecto de este sistema de generacion de ideas con IA. "
        f"Analiza estas metricas y propone UNA mejora de codigo especifica y aplicable:\n\n"
        f"METRICAS:\n{json.dumps(metricas, indent=2)}\n\n"
        f"ARCHIVOS: run_batch.py, monitor_nocturno.py, agents/watchdog.py, "
        f"agents/verticales_rotacion.py, agents/notion_sync_agent.py\n\n"
        f"Prioriza: reducir timeouts > mejorar calidad ideas > diversidad > velocidad\n\n"
        + '{"archivo":"run_batch.py",'
        + '"descripcion":"mejora en 1 linea",'
        + '"tipo_mejora":"rendimiento/calidad/diversidad/estabilidad",'
        + '"impacto_esperado":"descripcion del impacto real",'
        + '"confianza":80,'
        + '"codigo_completo_nuevo":"CODIGO COMPLETO DEL ARCHIVO MEJORADO"}'
    )
    return _llamar_groq(prompt)

def ciclo_auto_mejora(error_log="", metricas=None, telegram_fn=None, chat_id=None):
    if _limite_alcanzado():
        print(f"⚠️ Limite diario de auto-mejoras alcanzado")
        return False

    print(f"🤖 Ciclo auto-mejora ({datetime.now().strftime('%H:%M')})")

    if error_log:
        print("  Modo: REACTIVO")
        archivo = "run_batch.py"
        if "notion_sync_agent" in error_log:
            archivo = "agents/notion_sync_agent.py"
        elif "monitor_nocturno" in error_log:
            archivo = "monitor_nocturno.py"
        elif "watchdog" in error_log:
            archivo = "agents/watchdog.py"
        fix = analizar_error_y_generar_fix(error_log, archivo)
        if fix:
            return aplicar_fix(fix, telegram_fn=telegram_fn, chat_id=chat_id)
        print("  No se genero fix con confianza suficiente")
        return False
    else:
        print("  Modo: PROACTIVO")
        if not metricas:
            try:
                from agents.knowledge_base import get_stats
                from agents.watchdog import get_diagnostico
                s        = get_stats()
                d        = get_diagnostico()
                metricas = {
                    "score_promedio":        s.get("score_promedio", 0),
                    "total_ideas":           s.get("total_ideas", 0),
                    "timeouts_consecutivos": d.get("consecutive_timeouts", 0),
                    "ciclos_reparacion":     d.get("ciclo_reparacion", 0),
                    "ultimo_exito":          d.get("last_success", "nunca"),
                    "ok_hoy":                d.get("total_ok_24h", 0),
                }
            except:
                metricas = {}
        respuesta = generar_mejora_proactiva(metricas)
        if not respuesta:
            return False
        try:
            fix = json.loads(_limpiar_json_respuesta(respuesta))
            if fix.get("confianza", 0) >= 75:
                return aplicar_fix(fix, telegram_fn=telegram_fn, chat_id=chat_id)
        except Exception as e:
            print(f"  Mejora proactiva JSON invalido: {e}")
        return False

def get_historial_mejoras():
    h = _cargar_historial()
    return {
        "total_mejoras": len(h.get("mejoras", [])),
        "total_hoy":     h.get("total_hoy", 0),
        "limite_dia":    MAX_MEJORAS_DIA,
        "rollbacks":     h.get("rollbacks", 0),
        "ultimas_5":     h.get("mejoras", [])[-5:],
    }

# fin agents/auto_improver.py
