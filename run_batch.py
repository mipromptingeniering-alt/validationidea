import os, sys, json, time, re
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

MODELOS_GROQ = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]

PROMPT_SISTEMA = (
    "Eres un analista de startups con 20 años en YC y a16z. "
    "Generas ideas con datos REALES y especificos. "
    "PROHIBIDO usar texto generico o de ejemplo. "
    "REGLA ABSOLUTA: responde UNICAMENTE con JSON valido. Sin texto extra."
)

PROMPT_CRITICO_SISTEMA = (
    "Eres socio de YC con 15 años rechazando el 99% de startups. "
    "REGLA ABSOLUTA: responde UNICAMENTE con JSON valido. Sin texto extra."
)

PLACEHOLDERS_PROHIBIDOS = [
    "accion concreta canal mensaje",
    "test sin codigo plataforma concreta",
    "nombre real", "problema real", "propuesta real",
    "cliente real", "pricing real", "canal1", "canal2",
    "f1 detalle tecnico", "tag1", "tag2", "rival1", "rival2",
    "hito", "descripcion extensa",
]

def _cargar_pesos():
    try:
        with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "temperatura_groq": 0.85,
            "umbral_duplicado": 0.38,
            "verticales_preferidas": [],
            "verticales_penalizadas": [],
            "tags_exitosos": [],
            "score_objetivo": 75,
        }

def _validar_calidad(idea):
    try:
        from agents.watchdog import registrar_placeholder
    except ImportError:
        registrar_placeholder = lambda x: None

    texto_completo = json.dumps(idea, ensure_ascii=False).lower()
    for ph in PLACEHOLDERS_PROHIBIDOS:
        if ph in texto_completo:
            registrar_placeholder(ph)
            return False, f"Placeholder: '{ph}'"

    for campo in ["nombre", "problema", "solucion", "cliente_objetivo", "tagline"]:
        val = str(idea.get(campo, "")).strip()
        if not val or len(val) < 15:
            return False, f"Campo '{campo}' vacio"

    em = idea.get("estrategia_monetizacion", {})
    if isinstance(em, dict):
        sem1 = str(em.get("semana1", "")).strip().lower()
        if len(sem1) < 20 or "accion concreta" in sem1:
            return False, "semana1 no especifica"

    ht = idea.get("hipotesis_testeable", {})
    if isinstance(ht, dict):
        exp = str(ht.get("experimento_48h", "")).strip().lower()
        if len(exp) < 20 or "plataforma concreta" in exp:
            return False, "experimento_48h no especifico"

    return True, ""

def _get_instruccion_diversidad():
    try:
        from agents.watchdog import get_verticales_bloqueados, get_palabras_clave_bloqueadas
        verts    = get_verticales_bloqueados()
        palabras = get_palabras_clave_bloqueadas()
    except ImportError:
        return ""
    lineas = []
    if verts:
        lineas.append(f"VERTICALES PROHIBIDOS: {', '.join(verts)}")
    if palabras:
        lineas.append(f"TEMAS PROHIBIDOS: {', '.join(palabras[:10])}")
    if lineas:
        lineas.append("Elige un vertical COMPLETAMENTE DIFERENTE.")
    return "\n".join(lineas)

def get_prompt_idea(contexto, tendencias, tema="", modo_emergencia=False):
    pesos         = _cargar_pesos()
    score_obj     = pesos.get("score_objetivo", 75)
    ideas_previas = str(contexto.get("ideas_previas", "ninguna"))[:600]
    tema_str      = f"TEMA OBLIGATORIO: '{tema}'\n\n" if tema else ""
    diversidad    = _get_instruccion_diversidad()
    trends_str    = "\n".join(f"- {str(t)[:100]}" for t in tendencias[:6]) or "- No disponibles"

    aprendizaje = ""
    if pesos.get("verticales_preferidas"):
        aprendizaje += "Verticales con exito: " + ", ".join(pesos["verticales_preferidas"][:3]) + "\n"

    instrucciones_calidad = (
        "CALIDAD OBLIGATORIA — PROHIBIDO texto generico:\n"
        "- semana1: 'Envia DM a [grupo especifico] en [plataforma] con: [texto real]'\n"
        "- experimento_48h: 'Crea [Typeform/landing] en [plataforma] sobre [tema] y mide [metrica]'\n"
        "- herramienta_ia_clave: herramienta real de las tendencias\n"
        "- competidores: nombres reales (Notion, Linear, etc.) con debilidad especifica\n"
    )

    if modo_emergencia:
        return (
            f"{tema_str}{diversidad}\n\n"
            f"Genera UNA idea de startup SaaS B2B ORIGINAL 2026. Score minimo: {score_obj}/100.\n\n"
            f"{instrucciones_calidad}\n"
            f"TENDENCIAS: {trends_str}\n\n"
            f"IDEAS PREVIAS (NO repetir): {ideas_previas[:300]}\n\n"
            + '{"nombre":"string","tagline":"max 10 palabras",'
            + '"problema":"descripcion real con datos",'
            + '"solucion":"como la IA lo resuelve",'
            + '"cliente_objetivo":"cargo empresa sector dolor",'
            + '"herramienta_ia_clave":"herramienta real de tendencias",'
            + '"estrategia_monetizacion":{"semana1":"DM a [grupo] en [plataforma] ofreciendo [X]",'
            + '"precio_optimo_justificado":"EUR X/mes porque [razon]"},'
            + '"hipotesis_testeable":{"experimento_48h":"Crea [typeform] en [plataforma] midiendo [metrica]",'
            + '"metrica_exito":"X signups en 48h"},'
            + '"mvp":{"stack_recomendado":"Next.js+Supabase+Vercel","tiempo_semanas":3,"coste_estimado_eur":0},'
            + '"scores":{"critico":70,"viral":60,"generador":75,"monetizacion":70,"ejecutabilidad":80,"timing":75,"score_total":0},'
            + '"vertical":"SaaS","tipo":"B2B","tags":["tag_real_1","tag_real_2"]}'
        )

    return (
        f"{tema_str}{diversidad}\n\n"
        f"Genera UNA idea de startup ORIGINAL para 2026. Score minimo: {score_obj}/100.\n\n"
        f"{instrucciones_calidad}\n"
        f"APRENDIZAJE:\n{aprendizaje if aprendizaje else 'Primera generacion.'}\n\n"
        f"IDEAS PREVIAS (NO repetir):\n{ideas_previas}\n\n"
        f"TENDENCIAS (usa al menos una):\n{trends_str}\n\n"
        f"REGLAS: 0 euros para construir, primera venta en menos de 4 semanas.\n\n"
        + "{"
        + '"nombre":"NombreReal",'
        + '"tagline":"propuesta en max 10 palabras",'
        + '"problema":"X millones de empresas sufren Y porque Z [dato real]",'
        + '"solucion":"usamos [herramienta IA] para resolver X en Y minutos",'
        + '"cliente_objetivo":"Director de X en empresa Y de Z empleados que sufre W",'
        + '"propuesta_valor_unica":"unica porque competitors no hacen X por razon tecnica",'
        + '"herramienta_ia_clave":"nombre herramienta real + como se usa exactamente",'
        + '"mercado":{"TAM":"$X billion","SAM":"$X million","SOM":"$X año1",'
        + '"competidores":["Competitor1 (debilidad real)","Competitor2 (debilidad real)"],'
        + '"ventaja_competitiva":"por que es dificil de copiar"},'
        + '"modelo_negocio":{"tipo":"SaaS","pricing":"EUR X/mes justificado",'
        + '"canales_adquisicion":["1. DM a [grupo] en [plataforma]","2. Post en [comunidad]"],'
        + '"time_to_revenue":"X semanas"},'
        + '"estudio_economico":{'
        + '"conservador":{"supuestos":"5 clientes/mes","mes3":{"mrr_eur":750,"usuarios":15,"cac_eur":50},"mes6":{"mrr_eur":2250,"usuarios":45},"mes12":{"mrr_eur":6000,"margen_pct":70},"mes24":{"mrr_eur":15000,"arr_eur":180000,"breakeven":"mes8"}},'
        + '"realista":{"supuestos":"15 clientes/mes","mes3":{"mrr_eur":2250,"usuarios":45,"cac_eur":30},"mes6":{"mrr_eur":6750,"usuarios":135},"mes12":{"mrr_eur":18000,"margen_pct":75},"mes24":{"mrr_eur":45000,"arr_eur":540000,"breakeven":"mes5"}},'
        + '"optimista":{"supuestos":"30 clientes/mes","mes3":{"mrr_eur":4500,"usuarios":90,"cac_eur":20},"mes6":{"mrr_eur":13500,"usuarios":270},"mes12":{"mrr_eur":36000,"margen_pct":80},"mes24":{"mrr_eur":90000,"arr_eur":1080000,"breakeven":"mes4"}}},'
        + '"dafo":{"fortalezas":["F1 especifico","F2 especifico"],"debilidades":["D1 real","D2 real"],"oportunidades":["O1 con datos","O2"],"amenazas":["A1","A2"]},'
        + '"mvp":{"features_minimas":["Feature1 descripcion tecnica real","Feature2","Feature3"],'
        + '"stack_recomendado":"Next.js 14+Supabase+Vercel+Stripe","tiempo_semanas":3,"coste_estimado_eur":0},'
        + '"prompt_mvp":{'
        + '"meta":{"nombre_idea":"NOMBRE_REAL","objetivo":"MVP 3 semanas 0 euros","ia_recomendada":"Claude 3.5 Sonnet en Cursor","stack_completo":"Next.js+Supabase+Vercel+Stripe"},'
        + '"system_prompt":"Eres dev senior. Construye [NOMBRE] que resuelve [PROBLEMA]. Stack: Next.js 14+Supabase+Stripe+Tailwind.",'
        + '"contexto_negocio":{"problema_resuelto":"[PROBLEMA ESPECIFICO]","propuesta_valor":"[PROPUESTA]","usuario_objetivo":"[CLIENTE]","modelo_monetizacion":"EUR X/mes Stripe"},'
        + '"arquitectura_tecnica":{"base_datos":"tabla users, tabla [entidad](id,user_id,[campos])","auth":"Supabase Auth","frontend":"Next.js 14+Tailwind+shadcn","backend":"Edge Functions","pagos":"Stripe Checkout","deploy":"Vercel"},'
        + '"instrucciones_paso_a_paso":["1. npx create-next-app","2. supabase init","3. Feature principal","4. Stripe","5. Deploy"],'
        + '"features_mvp":[{"nombre":"Feature1","descripcion":"detalle tecnico real","prioridad":"P0"}],'
        + '"primer_cliente_script":"Manana: DM a [persona] en [plataforma]: [mensaje exacto <50 palabras]"},'
        + '"estrategia_monetizacion":{"semana1":"Envia DM a [N] [perfil] en [LinkedIn/Slack] con: [mensaje exacto]",'
        + '"semana4":"Beta gratis 14 dias en [comunidad] a cambio de feedback",'
        + '"mes3":"[estrategia 50 clientes canal especifico]",'
        + '"mes6":"[palanca: afiliados/SEO/integraciones]",'
        + '"canales":["Canal1 pasos reales","Canal2 pasos reales"],'
        + '"precio_optimo_justificado":"EUR X/mes porque competitor cobra Y y ahorramos Z horas"},'
        + '"hipotesis_testeable":{"hipotesis_principal":"Si [perfil] usa [solucion] entonces [metrica] en [tiempo]",'
        + '"metrica_exito":"[N] signups en 48h = validado",'
        + '"experimento_48h":"Crea [Typeform/landing] en [plataforma] sobre [angulo] midiendo [clicks/signups]",'
        + '"senal_de_alarma":"Menos de [N] respuestas en 48h = pivotar"},'
        + '"hoja_de_ruta":{"semana1":"Setup Next.js+Supabase","semana2":"Feature principal","semana3":"Stripe+deploy","semana4":"Primer cliente pago","mes3":"[objetivo numero]","mes6":"[objetivo numero]"},'
        + '"opinion_profesional":{"unicidad":"Unica HOY porque [razon ligada a tendencia]",'
        + '"riesgo_principal":"[riesgo con probabilidad %]",'
        + '"timing":"Por que ahora: [dato mercado especifico]",'
        + '"dia_uno":"Manana: [accion especifica <30 palabras]",'
        + '"fallo_probable":"60% falla por [razon especifica]"},'
        + '"scores":{"critico":0,"viral":0,"generador":0,"monetizacion":0,"ejecutabilidad":0,"timing":0,"score_total":0},'
        + '"vertical":"SaaS","tipo":"B2B","tags":["tag1","tag2","tag3"]'
        + "}"
    )

def get_prompt_critico(idea):
    return (
        f"Analiza esta startup:\n"
        f"NOMBRE: {idea.get('nombre','?')}\n"
        f"PROBLEMA: {str(idea.get('problema',''))[:250]}\n"
        f"CLIENTE: {str(idea.get('cliente_objetivo',''))[:150]}\n"
        f"PRICING: {idea.get('modelo_negocio',{}).get('pricing','?') if isinstance(idea.get('modelo_negocio'),dict) else '?'}\n"
        f"SCORE: {idea.get('scores',{}).get('score_total',0) if isinstance(idea.get('scores'),dict) else 0}\n\n"
        + 'Responde SOLO con: {"veredicto":"1 frase directa sobre ESTA idea",'
        + '"objeciones_principales":["obj1","obj2","obj3"],'
        + '"fortalezas_reales":["f1","f2"],'
        + '"ajuste_score":-5,'
        + '"score_critico_final":70,'
        + '"recomendacion":"invertir/pivotar/descartar",'
        + '"pivote_sugerido":"hacia donde o null"}'
    )

def calcular_score_ponderado(scores):
    pesos = {
        "critico":0.25,"generador":0.25,"ejecutabilidad":0.20,
        "monetizacion":0.15,"timing":0.10,"viral":0.05
    }
    return round(sum(scores.get(k,0)*v for k,v in pesos.items()), 1)

def _groq_client():
    import groq
    return groq.Groq(api_key=GROQ_API_KEY, timeout=90)

def _content_to_str(content):
    """Convierte content de Groq a string — maneja str, list y dict."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        partes = []
        for bloque in content:
            if isinstance(bloque, dict):
                partes.append(str(bloque.get("text", bloque.get("content", ""))))
            else:
                partes.append(str(bloque))
        return " ".join(partes)
    if isinstance(content, dict):
        return str(content.get("text", content.get("content", str(content))))
    return str(content)

def _llamar_con_retry(client, modelo, messages, max_tokens, temperature):
    for intento in range(2):
        try:
            resp = client.chat.completions.create(
                model=modelo,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            if not resp.choices:
                return None
            content = resp.choices[0].message.content
            text    = _content_to_str(content).strip()
            if text:
                return text
            return None
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err or "limit" in err:
                wait = 12 + (intento * 3)
                try:
                    raw = getattr(e, "response", None)
                    if raw:
                        ra = raw.headers.get("retry-after", "")
                        if ra:
                            wait = min(int(float(str(ra))) + 2, 20)
                except: pass
                print(f"   ⏳ Rate limit {modelo} → {wait}s...")
                time.sleep(wait)
            elif any(x in err for x in ["not found","decommission","does not exist","invalid model","404"]):
                print(f"   ⚠️ {modelo} no disponible")
                return None
            else:
                print(f"   ❌ {modelo}: {str(e)[:100]}")
                return None
    return None

def limpiar_json(texto):
    """Limpia y extrae JSON de la respuesta — maneja str, list, dict y None."""
    if texto is None:
        return "{}"
    if isinstance(texto, dict):
        return json.dumps(texto, ensure_ascii=False)
    if isinstance(texto, list):
        for item in texto:
            if isinstance(item, str) and "{" in item:
                texto = item
                break
            elif isinstance(item, dict):
                return json.dumps(item, ensure_ascii=False)
        else:
            return json.dumps(texto[0] if texto else {}, ensure_ascii=False)
    if not isinstance(texto, str):
        texto = str(texto)
    texto = texto.strip()
    if "```json" in texto:
        texto = texto.split("```json").split("```").strip()[1]
    elif "```" in texto:
        texto = texto.split("```").split("```")[0].strip()
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1:
        texto = texto[inicio:fin+1]
    return texto

def llamar_groq(prompt, max_tokens=3000):
    pesos    = _cargar_pesos()
    temp     = pesos.get("temperatura_groq", 0.85)
    client   = _groq_client()
    messages = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user",   "content": prompt},
    ]
    for modelo in MODELOS_GROQ:
        print(f"   Modelo: {modelo}")
        result = _llamar_con_retry(client, modelo, messages, max_tokens, temp)
        if result:
            print(f"   ✅ OK {modelo} ({len(result)} chars)")
            return result
        print(f"   → siguiente modelo...")
    raise RuntimeError("Ningun modelo Groq disponible")

def llamar_groq_critico(prompt):
    client   = _groq_client()
    messages = [
        {"role": "system", "content": PROMPT_CRITICO_SISTEMA},
        {"role": "user",   "content": prompt},
    ]
    for modelo in ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]:
        result = _llamar_con_retry(client, modelo, messages, 500, 0.6)
        if result:
            return result
    return ""

def _aplicar_scoring_critico(idea):
    print("🔍 Scoring critico YC...")
    time.sleep(4)
    try:
        respuesta = llamar_groq_critico(get_prompt_critico(idea))
        if not respuesta:
            return idea
        critica = json.loads(limpiar_json(respuesta))
        idea["scoring_critico"] = critica
        scores      = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
        ajuste      = int(critica.get("ajuste_score", 0))
        score_prev  = scores.get("score_total", 0)
        score_nuevo = max(20, min(98, score_prev + ajuste))
        scores["score_total"]   = score_nuevo
        scores["score_critico"] = critica.get("score_critico_final", score_prev)
        idea["scores"] = scores
        print(f"   ✅ {score_prev}→{score_nuevo} ({ajuste:+d}) | {critica.get('recomendacion','')}")
    except Exception as e:
        print(f"   ⚠️ Scoring critico omitido: {e}")
    return idea

def ejecutar_batch():
    try:
        from agents.knowledge_base    import get_contexto_para_prompt, registrar_idea, get_stats, es_duplicado
        from agents.trend_scout       import get_tendencias, actualizar_tendencias
        from agents.notion_sync_agent import sync_idea_to_notion
    except ImportError as e:
        print(f"❌ Import critico: {e}")
        return False, "", ""

    try:
        from agents.watchdog import (
            registrar_exito, registrar_fallo,
            modo_emergencia_activo, get_nombres_bloqueados
        )
        watchdog_ok = True
    except ImportError:
        watchdog_ok = False
        registrar_exito = lambda *a, **k: None
        registrar_fallo = lambda *a, **k: None
        modo_emergencia_activo = lambda: False
        get_nombres_bloqueados = lambda: []

    validar_idea_fn    = None
    generar_landing_fn = None
    try:
        from agents.market_validator  import validar_idea    as validar_idea_fn
        from agents.landing_generator import generar_landing as generar_landing_fn
    except ImportError:
        pass

    print("🌐 Actualizando tendencias...")
    try:
        actualizar_tendencias()
        tendencias = get_tendencias()
        print(f"✅ {len(tendencias)} tendencias")
    except Exception as e:
        print(f"⚠️ Tendencias: {e}")
        tendencias = []

    print("📚 Cargando contexto KB...")
    try:
        contexto = get_contexto_para_prompt()
        stats    = get_stats()
        print(f"📊 KB: {stats.get('total_ideas',0)} ideas | Promedio: {stats.get('score_promedio',0)}")
    except Exception as e:
        print(f"⚠️ KB: {e}")
        contexto = {"ideas_previas": "", "score_promedio": 0}

    pesos      = _cargar_pesos()
    umbral_dup = pesos.get("umbral_duplicado", 0.38)
    tema       = os.environ.get("IDEA_TOPIC", "")
    emergencia = modo_emergencia_activo()

    if emergencia:
        print("⚠️ MODO EMERGENCIA activo")
    if tema:
        print(f"🎯 Tema: '{tema}'")

    nombres_bloqueados = get_nombres_bloqueados()

    idea = None
    for intento_gen in range(4):
        print(f"🧠 Generando idea (intento {intento_gen+1}/4)...")
        prompt = get_prompt_idea(contexto, tendencias, tema, modo_emergencia=emergencia)
        print(f"   Prompt: {len(prompt)} chars")

        try:
            respuesta = llamar_groq(prompt, max_tokens=3000)
        except Exception as e:
            print(f"❌ Error Groq: {e}")
            if watchdog_ok: registrar_fallo(str(e))
            return False, "", ""

        try:
            idea_candidata = json.loads(limpiar_json(respuesta))
        except Exception as e:
            print(f"❌ JSON invalido (intento {intento_gen+1}): {e}")
            print(f"   Raw: {str(respuesta)[:300]}")
            emergencia = True
            continue

        calidad_ok, motivo = _validar_calidad(idea_candidata)
        if not calidad_ok:
            print(f"⚠️ Calidad rechazada: {motivo} — regenerando...")
            emergencia = True
            continue

        nombre_cand = idea_candidata.get("nombre", "").lower()
        if any(nombre_cand in n.lower() or n.lower() in nombre_cand
               for n in nombres_bloqueados if n):
            print(f"⚠️ Nombre bloqueado por watchdog — regenerando...")
            continue

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado de '{dup_nombre}' — regenerando...")
                contexto["ideas_previas"] += f"\n- DESCARTADA: '{idea_candidata.get('nombre','?')}'"
                continue
        except Exception as e:
            print(f"⚠️ Anti-dup: {e}")

        idea = idea_candidata
        print(f"✅ Idea valida: {idea.get('nombre','?')}")
        break

    if not idea:
        print("❌ No se genero idea valida en 4 intentos")
        if watchdog_ok: registrar_fallo("4 intentos fallidos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")

    pm = idea.get("prompt_mvp", {})
    if isinstance(pm, str):
        try:   idea["prompt_mvp"] = json.loads(pm)
        except: idea["prompt_mvp"] = {"ia_recomendada": "Claude 3.5 Sonnet", "primer_cliente_script": pm}

    scores = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores

    idea = _aplicar_scoring_critico(idea)

    if validar_idea_fn:
        try:
            ev = validar_idea_fn(idea)
            idea["validacion_mercado"] = ev
            scores = idea.get("scores", {})
            scores["score_total"]        = ev.get("score_final_ajustado", scores.get("score_total", 0))
            scores["score_mercado_real"] = ev.get("score_mercado_real", 0)
            idea["scores"] = scores
        except Exception as e:
            print(f"⚠️ Validacion mercado: {e}")

    score = idea.get("scores", {}).get("score_total", 0)
    print(f"📊 Score FINAL: {score}/100")

    try:
        registrar_idea(idea)
    except Exception as e:
        print(f"⚠️ KB registrar: {e}")

    os.makedirs("data", exist_ok=True)
    try:
        ruta  = "data/ideas.json"
        todas = []
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                todas = json.load(f)
        todas.append(idea)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(todas, f, ensure_ascii=False, indent=2)
        print(f"💾 ideas.json: {len(todas)} total")
    except Exception as e:
        print(f"⚠️ ideas.json: {e}")

    # Notion sync
    print("🔗 Sincronizando Notion...")
    url = ""
    notion_token = os.environ.get("NOTION_TOKEN", "")
    notion_db    = os.environ.get("NOTION_DATABASE_ID", "")
    if not notion_token:
        print("⚠️ NOTION_TOKEN no configurado")
    elif not notion_db:
        print("⚠️ NOTION_DATABASE_ID no configurado")
    else:
        try:
            url = sync_idea_to_notion(idea)
            if url:
                print(f"✅ Notion OK: {url}")
            else:
                print("❌ Notion devolvio URL vacia")
        except Exception as e:
            print(f"❌ Notion: {e}")

    if url:
        idea["notion_url"] = url
        try:
            with open("data/ideas.json", "r", encoding="utf-8") as f:
                todas = json.load(f)
            if todas:
                todas[-1]["notion_url"] = url
            with open("data/ideas.json", "w", encoding="utf-8") as f:
                json.dump(todas, f, ensure_ascii=False, indent=2)
        except: pass

    if watchdog_ok:
        registrar_exito(idea)

    try:
        from agents.verticales_rotacion import registrar_vertical_usado
        registrar_vertical_usado(idea.get("vertical", ""))
    except: pass

    try:
        from agents.weekly_learner import analizar_y_aprender
        r = analizar_y_aprender()
        print(f"🧠 Aprendizaje: {str(r.get('resumen',''))[:80]}")
    except Exception as e:
        print(f"⚠️ Aprendizaje: {e}")

    herramienta = str(idea.get("herramienta_ia_clave", ""))[:80]
    tagline     = str(idea.get("tagline", ""))[:100]
    problema    = str(idea.get("problema", ""))[:150]
    monetiz     = ""
    if isinstance(idea.get("estrategia_monetizacion"), dict):
        monetiz = str(idea["estrategia_monetizacion"].get("semana1", ""))[:150]
    hipotesis = ""
    if isinstance(idea.get("hipotesis_testeable"), dict):
        hipotesis = str(idea["hipotesis_testeable"].get("experimento_48h", ""))[:150]
    veredicto = recomendacion = ""
    if isinstance(idea.get("scoring_critico"), dict):
        veredicto     = str(idea["scoring_critico"].get("veredicto", ""))[:150]
        recomendacion = str(idea["scoring_critico"].get("recomendacion", ""))

    print(f"SCORE_FINAL:{score}")
    print(f"HERRAMIENTA_IA:{herramienta}")
    print(f"HIPOTESIS:{hipotesis}")
    print(f"NOTION_URL:{url}")
    print(f"TAGLINE:{tagline}")
    print(f"PROBLEMA:{problema}")
    print(f"MONETIZ_S1:{monetiz}")
    print(f"VEREDICTO_CRITICO:{veredicto}")
    print(f"RECOMENDACION:{recomendacion}")
    print(f"✅ Sincronizada: {nombre}")
    return True, nombre, url

if __name__ == "__main__":
    exito, nombre, url = ejecutar_batch()
    sys.exit(0 if exito else 1)

# fin run_batch.py
