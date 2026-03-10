import os, sys, json, time, re
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# Modelos ordenados por TPM disponible en free tier 2026
# llama-3.3-70b-versatile: 12K TPM
# llama-4-scout:           30K TPM  ← mejor fallback
# llama-3.1-8b-instant:    6K TPM   ← último recurso (rápido)
MODELOS_GROQ = [
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "llama-3.1-8b-instant",
]

PROMPT_SISTEMA = (
    "Eres un analista de startups de clase mundial con 20 años en Silicon Valley. "
    "Generas ideas ORIGINALES con datos reales y monetizacion probada. "
    "REGLA ABSOLUTA: responde UNICAMENTE con JSON valido. Sin texto extra. Sin markdown."
)

PROMPT_CRITICO_SISTEMA = (
    "Eres un socio de YC con 15 años rechazando el 99% de startups. "
    "Eres brutalmente honesto. "
    "REGLA ABSOLUTA: responde UNICAMENTE con JSON valido. Sin texto extra."
)

def _cargar_pesos():
    try:
        with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "temperatura_groq": 0.85, "umbral_duplicado": 0.38,
            "verticales_preferidas": [], "verticales_penalizadas": [],
            "tags_exitosos": [], "ia_tools_top": [],
            "score_objetivo": 75, "patrones_exitosos": [],
        }

def get_prompt_idea(contexto, tendencias, tema=""):
    pesos         = _cargar_pesos()
    score_obj     = pesos.get("score_objetivo", 75)
    ideas_previas = str(contexto.get("ideas_previas", "ninguna"))[:800]
    tema_str      = f"TEMA OBLIGATORIO: '{tema}'\n\n" if tema else ""

    # Solo las 8 tendencias mas relevantes para no exceder tokens
    top_trends = tendencias[:8]
    trends_str = "\n".join(f"- {t[:100]}" for t in top_trends) if top_trends else "- No disponibles"

    aprendizaje = ""
    if pesos.get("verticales_preferidas"):
        aprendizaje += "Verticales TOP: " + ", ".join(pesos["verticales_preferidas"][:3]) + "\n"
    if pesos.get("verticales_penalizadas"):
        aprendizaje += "Evitar: " + ", ".join(pesos["verticales_penalizadas"][:3]) + "\n"
    if pesos.get("tags_exitosos"):
        aprendizaje += "Tags ganadores: " + ", ".join(pesos["tags_exitosos"][:5]) + "\n"
    if contexto.get("score_promedio", 0) > 0:
        aprendizaje += f"Score promedio actual: {contexto['score_promedio']} — supera este\n"

    # Prompt compacto ~1200 tokens — describe campos sin template completo
    return (
        f"{tema_str}"
        f"Genera UNA idea de startup ORIGINAL para 2026. Score minimo: {score_obj}/100.\n\n"
        f"APRENDIZAJE:\n{aprendizaje if aprendizaje else 'Primera generacion.'}\n\n"
        f"IDEAS PREVIAS (NO repetir):\n{ideas_previas}\n\n"
        f"TENDENCIAS ACTUALES (usa al menos una):\n{trends_str}\n\n"
        f"REGLAS: 0 euros para construir, primera venta en <4 semanas, nicho especifico.\n\n"
        f"Responde SOLO con este JSON (todos los campos con datos REALES, no ejemplos):\n"
        + "{"
        + '"nombre":"string",'
        + '"tagline":"max 10 palabras",'
        + '"problema":"descripcion extensa del problema real con datos",'
        + '"solucion":"como la IA lo resuelve mejor que alternativas",'
        + '"cliente_objetivo":"cargo sector empresa tamaño dolor especifico",'
        + '"propuesta_valor_unica":"ventaja injusta dificil de copiar",'
        + '"herramienta_ia_clave":"herramienta IA de las tendencias que lo hace posible HOY",'
        + '"mercado":{"TAM":"$ calculado","SAM":"$ calculado","SOM":"$ año1","competidores":["Rival1 debilidad","Rival2 debilidad"],"ventaja_competitiva":"moat real"},'
        + '"modelo_negocio":{"tipo":"SaaS","pricing":"precio exacto justificado","canales_adquisicion":["canal1 paso a paso","canal2"],"time_to_revenue":"X semanas"},'
        + '"estudio_economico":{'
        + '"conservador":{"supuestos":"texto","mes3":{"mrr_eur":0,"usuarios":0,"cac_eur":0},"mes6":{"mrr_eur":0,"usuarios":0},"mes12":{"mrr_eur":0,"margen_pct":0},"mes24":{"mrr_eur":0,"arr_eur":0,"breakeven":"mesX"}},'
        + '"realista":{"supuestos":"texto","mes3":{"mrr_eur":0,"usuarios":0,"cac_eur":0},"mes6":{"mrr_eur":0,"usuarios":0},"mes12":{"mrr_eur":0,"margen_pct":0},"mes24":{"mrr_eur":0,"arr_eur":0,"breakeven":"mesX"}},'
        + '"optimista":{"supuestos":"texto","mes3":{"mrr_eur":0,"usuarios":0,"cac_eur":0},"mes6":{"mrr_eur":0,"usuarios":0},"mes12":{"mrr_eur":0,"margen_pct":0},"mes24":{"mrr_eur":0,"arr_eur":0,"breakeven":"mesX"}}},'
        + '"dafo":{"fortalezas":["F1","F2"],"debilidades":["D1","D2"],"oportunidades":["O1","O2"],"amenazas":["A1","A2"]},'
        + '"mvp":{"features_minimas":["F1 detalle tecnico","F2","F3"],"stack_recomendado":"Next.js+Supabase+Vercel+Stripe","tiempo_semanas":3,"coste_estimado_eur":0},'
        + '"prompt_mvp":{'
        + '"meta":{"nombre_idea":"NOMBRE REAL","objetivo":"MVP en 3 semanas 0 euros","ia_recomendada":"Claude 3.5 Sonnet en Cursor","stack_completo":"Next.js+Supabase+Vercel+Stripe"},'
        + '"system_prompt":"Eres desarrollador senior. Construye NOMBRE_REAL desde cero. DESCRIPCION_REAL_DEL_PRODUCTO.",'
        + '"contexto_negocio":{"problema_resuelto":"PROBLEMA REAL","propuesta_valor":"PROPUESTA REAL","usuario_objetivo":"CLIENTE REAL","modelo_monetizacion":"PRICING REAL"},'
        + '"arquitectura_tecnica":{"base_datos":"Schema Supabase real con tablas de esta idea","auth":"Supabase Auth","frontend":"Next.js 14+Tailwind+shadcn","backend":"Edge Functions","pagos":"Stripe Checkout+webhook","deploy":"Vercel free"},'
        + '"instrucciones_paso_a_paso":["1. npx create-next-app","2. Supabase setup","3. Feature principal","4. Stripe","5. Deploy"],'
        + '"features_mvp":[{"nombre":"F1_REAL","descripcion":"detalle tecnico","prioridad":"P0"}],'
        + '"primer_cliente_script":"accion exacta para primer cliente en 48h"},'
        + '"estrategia_monetizacion":{"semana1":"accion concreta canal mensaje","semana4":"primera venta plataforma","mes3":"50 clientes estrategia","mes6":"palanca crecimiento","canales":["canal1","canal2"],"precio_optimo_justificado":"precio y razon"},'
        + '"hipotesis_testeable":{"hipotesis_principal":"Si X usa Y entonces Z en T","metrica_exito":"numero y fecha","experimento_48h":"test sin codigo plataforma concreta","senal_de_alarma":"metrica que indica no hay mercado"},'
        + '"hoja_de_ruta":{"semana1":"hito","semana2":"hito","semana3":"MVP listo","semana4":"primer cliente","mes3":"objetivo","mes6":"objetivo"},'
        + '"opinion_profesional":{"unicidad":"unica HOY citando tendencia","riesgo_principal":"riesgo con probabilidad %","timing":"por que ahora exactamente","dia_uno":"primera accion manana","fallo_probable":"fallo honesto"},'
        + '"scores":{"critico":75,"viral":55,"generador":80,"monetizacion":72,"ejecutabilidad":85,"timing":78,"score_total":0},'
        + '"vertical":"SaaS","tipo":"B2B","tags":["tag1","tag2","tag3"]'
        + "}"
    )

def get_prompt_critico(idea):
    return (
        f"Analiza esta startup como socio de YC:\n"
        f"NOMBRE: {idea.get('nombre','?')}\n"
        f"PROBLEMA: {str(idea.get('problema',''))[:200]}\n"
        f"CLIENTE: {str(idea.get('cliente_objetivo',''))[:150]}\n"
        f"PRICING: {idea.get('modelo_negocio',{}).get('pricing','?') if isinstance(idea.get('modelo_negocio'),dict) else '?'}\n"
        f"SCORE IA: {idea.get('scores',{}).get('score_total',0) if isinstance(idea.get('scores'),dict) else 0}\n\n"
        + "Responde SOLO con: "
        + '{"veredicto":"1 frase directa",'
        + '"objeciones_principales":["obj1","obj2","obj3"],'
        + '"fortalezas_reales":["f1","f2"],'
        + '"ajuste_score":-5,'
        + '"score_critico_final":70,'
        + '"recomendacion":"invertir/pivotar/descartar",'
        + '"pivote_sugerido":"hacia donde o null}'
        + '"}'
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

def _llamar_con_retry(client, modelo, messages, max_tokens, temperature):
    """Llama a Groq leyendo el header retry-after real."""
    for intento in range(3):
        try:
            resp = client.chat.completions.create(
                model=modelo,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
            )
            n = len(resp.choices) if resp.choices else 0
            if n == 0:
                print(f"   ⚠️ choices=0 en {modelo}")
                return None
            content = resp.choices[0].message.content
            if content and content.strip():
                return content.strip()
            return None
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err or "limit" in err:
                # Leer retry-after de los headers si está disponible
                wait = 30 + (intento * 30)
                try:
                    raw = getattr(e, "response", None)
                    if raw:
                        ra = raw.headers.get("retry-after", "")
                        if ra:
                            wait = int(float(str(ra))) + 5
                except: pass
                print(f"   ⏳ Rate limit {modelo} → espera {wait}s (intento {intento+1}/3)...")
                time.sleep(wait)
            elif any(x in err for x in ["not found","decommission","does not exist","invalid model","404"]):
                print(f"   ⚠️ {modelo} no disponible — saltando")
                return None
            else:
                print(f"   ❌ {modelo}: {str(e)[:100]}")
                return None
    return None

def llamar_groq(prompt, max_tokens=3500):
    pesos  = _cargar_pesos()
    temp   = pesos.get("temperatura_groq", 0.85)
    client = _groq_client()
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
    client = _groq_client()
    messages = [
        {"role": "system", "content": PROMPT_CRITICO_SISTEMA},
        {"role": "user",   "content": prompt},
    ]
    # Para el critico usamos llama-4-scout primero (30K TPM) y llama-3.1-8b como fallback
    modelos_critico = [
        "meta-llama/llama-4-scout-17b-16e-instruct",
        "llama-3.1-8b-instant",
    ]
    for modelo in modelos_critico:
        result = _llamar_con_retry(client, modelo, messages, 600, 0.6)
        if result:
            return result
    return ""

def limpiar_json(texto):
    if not isinstance(texto, str):
        return json.dumps(texto, ensure_ascii=False)
    texto = texto.strip()
    if "```json" in texto:
        texto = texto.split("```json").split("```").strip()[1]
    elif "```" in texto:
        texto = texto.split("```")[2].split("```")[0].strip()
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1:
        texto = texto[inicio:fin+1]
    return texto

def _aplicar_scoring_critico(idea):
    print("🔍 Aplicando scoring critico (IA YC)...")
    # Pausa de 5s entre llamadas para no saturar TPM
    time.sleep(5)
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
        print(f"   ✅ Score: {score_prev} → {score_nuevo} ({ajuste:+d}) | {critica.get('recomendacion','')}")
    except Exception as e:
        print(f"   ⚠️ Scoring critico omitido: {e}")
    return idea

def _auto_aprender():
    try:
        from agents.weekly_learner import analizar_y_aprender
        r = analizar_y_aprender()
        print(f"🧠 Auto-aprendizaje: {str(r.get('resumen',''))[:100]}")
    except Exception as e:
        print(f"⚠️ Auto-aprendizaje: {e}")

def ejecutar_batch():
    try:
        from agents.knowledge_base    import get_contexto_para_prompt, registrar_idea, get_stats, es_duplicado
        from agents.trend_scout       import get_tendencias, actualizar_tendencias
        from agents.notion_sync_agent import sync_idea_to_notion
    except ImportError as e:
        print(f"❌ Import critico: {e}")
        return False, "", ""

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
        print(f"✅ {len(tendencias)} tendencias frescas")
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
        contexto = {"ideas_previas":"","score_promedio":0}

    pesos      = _cargar_pesos()
    umbral_dup = pesos.get("umbral_duplicado", 0.38)
    tema       = os.environ.get("IDEA_TOPIC", "")
    if tema:
        print(f"🎯 Tema: '{tema}'")

    idea = None
    for intento_gen in range(4):
        print(f"🧠 Generando idea (intento {intento_gen+1}/4)...")
        prompt = get_prompt_idea(contexto, tendencias, tema)
        print(f"   Prompt: {len(prompt)} chars")
        try:
            respuesta = llamar_groq(prompt, max_tokens=3500)
        except Exception as e:
            print(f"❌ Error Groq: {e}")
            return False, "", ""

        try:
            idea_candidata = json.loads(limpiar_json(respuesta))
        except Exception as e:
            print(f"❌ JSON invalido: {e} | Raw: {str(respuesta)[:200]}")
            continue

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado de '{dup_nombre}' — regenerando...")
                contexto["ideas_previas"] += f"\n- DESCARTADA: '{idea_candidata.get('nombre','?')}' similar a '{dup_nombre}'"
                continue
        except Exception as e:
            print(f"⚠️ Anti-dup: {e}")

        idea = idea_candidata
        break

    if not idea:
        print("❌ No se genero idea unica en 4 intentos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea: {nombre}")

    # Normalizar prompt_mvp
    pm = idea.get("prompt_mvp", {})
    if isinstance(pm, str):
        try:   idea["prompt_mvp"] = json.loads(pm)
        except: idea["prompt_mvp"] = {"ia_recomendada":"Claude 3.5 Sonnet","primer_cliente_script":pm}

    # Score inicial
    scores = idea.get("scores", {}) if isinstance(idea.get("scores"), dict) else {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores

    # Scoring critico con pausa entre llamadas
    idea = _aplicar_scoring_critico(idea)

    # Validacion de mercado
    if validar_idea_fn:
        try:
            ev = validar_idea_fn(idea)
            idea["validacion_mercado"] = ev
            scores = idea.get("scores", {})
            scores["score_total"]        = ev.get("score_final_ajustado", scores.get("score_total",0))
            scores["score_mercado_real"] = ev.get("score_mercado_real", 0)
            idea["scores"] = scores
        except Exception as e:
            print(f"⚠️ Validacion: {e}")

    score = idea.get("scores", {}).get("score_total", 0)
    print(f"📊 Score FINAL: {score}/100")

    try:
        registrar_idea(idea)
    except Exception as e:
        print(f"⚠️ KB: {e}")

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

    landing_url = ""
    if generar_landing_fn:
        try:
            l = generar_landing_fn(idea)
            landing_url = l.get("url_publica","")
        except Exception as e:
            print(f"⚠️ Landing: {e}")

    print("🔗 Sincronizando Notion...")
    url = ""
    try:
        url = sync_idea_to_notion(idea)
        if url:
            print(f"NOTION_URL:{url}")
    except Exception as e:
        print(f"❌ Notion: {e}")

    _auto_aprender()

    herramienta       = str(idea.get("herramienta_ia_clave",""))
    hipotesis         = ""
    if isinstance(idea.get("hipotesis_testeable"), dict):
        hipotesis = str(idea["hipotesis_testeable"].get("experimento_48h",""))
    tagline           = str(idea.get("tagline",""))
    problema          = str(idea.get("problema",""))[:150]
    monetiz           = ""
    if isinstance(idea.get("estrategia_monetizacion"), dict):
        monetiz = str(idea["estrategia_monetizacion"].get("semana1",""))[:120]
    veredicto_critico = ""
    recomendacion     = ""
    if isinstance(idea.get("scoring_critico"), dict):
        veredicto_critico = str(idea["scoring_critico"].get("veredicto",""))[:120]
        recomendacion     = str(idea["scoring_critico"].get("recomendacion",""))

    print(f"SCORE_FINAL:{score}")
    print(f"HERRAMIENTA_IA:{herramienta[:80]}")
    print(f"HIPOTESIS:{hipotesis[:120]}")
    print(f"LANDING_URL:{landing_url}")
    print(f"TAGLINE:{tagline[:100]}")
    print(f"PROBLEMA:{problema}")
    print(f"MONETIZ_S1:{monetiz}")
    print(f"VEREDICTO_CRITICO:{veredicto_critico}")
    print(f"RECOMENDACION:{recomendacion}")
    print(f"✅ Sincronizada: {nombre}")
    return True, nombre, url

if __name__ == "__main__":
    exito, nombre, url = ejecutar_batch()
    sys.exit(0 if exito else 1)

# aqui finaliza run_batch.py
