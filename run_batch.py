import os, sys, json, time, re
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch v10 iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

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
]

# ── Conversion segura ─────────────────────────────────────────────────────────

def _content_to_str(content):
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, (list, tuple)):
        partes = []
        for bloque in content:
            if isinstance(bloque, str):
                partes.append(bloque)
            elif isinstance(bloque, dict):
                partes.append(str(bloque.get("text", bloque.get("content", ""))))
            elif hasattr(bloque, "text"):
                partes.append(str(bloque.text))
            elif hasattr(bloque, "content"):
                partes.append(str(bloque.content))
            else:
                partes.append(str(bloque))
        return "".join(partes)
    if isinstance(content, dict):
        return str(content.get("text", content.get("content", str(content))))
    if hasattr(content, "text"):
        return str(content.text)
    if hasattr(content, "content"):
        return str(content.content)
    return str(content)

def limpiar_json(texto):
    if not isinstance(texto, str):
        texto = _content_to_str(texto)
    texto = texto.strip()
    if not texto:
        return "{}"
    if "```json" in texto:
        partes = texto.split("```json")
        if len(partes) > 1:
            texto = partes[1].split("```")[0].strip()
    elif "```" in texto:
        for parte in texto.split("```"):
            parte = parte.strip()
            if parte.startswith("{"):
                texto = parte
                break
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1 and fin > inicio:
        return texto[inicio:fin+1]
    return texto

# ── Extraccion exhaustiva del choice ─────────────────────────────────────────

def _extraer_content_de_choice(choice, modelo=""):
    """
    Intenta extraer content de UN choice usando TODOS los metodos posibles.
    Imprime debug para saber que estructura tiene.
    Nunca lanza excepciones.
    """
    # --- DEBUG: mostrar tipo y atributos ---
    tipo_choice = type(choice).__name__
    attrs = []
    try:
        if hasattr(choice, "__dict__"):
            attrs = list(choice.__dict__.keys())[:15]
        elif hasattr(choice, "__slots__"):
            attrs = list(choice.__slots__)[:15]
    except: pass
    print(f"   [DEBUG] choice type={tipo_choice} attrs={attrs}")

    content = None

    # Metodo 1: choice.message.content (estandar SDK)
    if hasattr(choice, "message"):
        msg = choice.message
        print(f"   [DEBUG] message type={type(msg).__name__}")
        if hasattr(msg, "content"):
            content = _content_to_str(msg.content)
            print(f"   [DEBUG] via message.content: {len(content)} chars")
        elif isinstance(msg, dict):
            content = _content_to_str(msg.get("content", ""))
        elif isinstance(msg, (list, str)):
            content = _content_to_str(msg)
        if content:
            return content

    # Metodo 2: choice es dict
    if isinstance(choice, dict):
        msg = choice.get("message", {})
        if isinstance(msg, dict):
            content = _content_to_str(msg.get("content", ""))
        elif msg:
            content = _content_to_str(msg)
        if not content:
            content = _content_to_str(choice.get("content", choice.get("text", "")))
        if content:
            print(f"   [DEBUG] via dict: {len(content)} chars")
            return content

    # Metodo 3: choice.text o choice.content directo
    if hasattr(choice, "text") and choice.text:
        content = _content_to_str(choice.text)
        if content:
            print(f"   [DEBUG] via choice.text: {len(content)} chars")
            return content

    if hasattr(choice, "content") and choice.content:
        content = _content_to_str(choice.content)
        if content:
            print(f"   [DEBUG] via choice.content: {len(content)} chars")
            return content

    # Metodo 4: delta (respuesta streaming accidental)
    if hasattr(choice, "delta"):
        delta = choice.delta
        if hasattr(delta, "content") and delta.content:
            content = _content_to_str(delta.content)
            if content:
                print(f"   [DEBUG] via delta.content: {len(content)} chars")
                return content

    # Metodo 5: choice es lista
    if isinstance(choice, (list, tuple)):
        content = _content_to_str(choice)
        if content:
            print(f"   [DEBUG] via choice-as-list: {len(content)} chars")
            return content

    # Metodo 6: stringify completo y buscar JSON
    try:
        raw = str(choice)
        print(f"   [DEBUG] choice str: {raw[:200]}")
        if "{" in raw:
            # Puede contener el JSON directamente
            inicio = raw.find("{")
            fin    = raw.rfind("}")
            if inicio != -1 and fin > inicio:
                content = raw[inicio:fin+1]
                print(f"   [DEBUG] via stringify+JSON: {len(content)} chars")
                return content
        return raw if raw and raw != "None" else None
    except:
        return None

def _extraer_content_respuesta(resp, modelo=""):
    """
    Extrae content de la respuesta completa del SDK.
    Maneja resp con .choices, resp como lista, resp como dict.
    """
    # Debug de la respuesta completa
    tipo_resp = type(resp).__name__
    print(f"   [DEBUG] resp type={tipo_resp}")

    choices = None

    if hasattr(resp, "choices"):
        choices = resp.choices
    elif isinstance(resp, dict):
        choices = resp.get("choices", [])
    elif isinstance(resp, (list, tuple)):
        # resp directamente es la lista de choices
        choices = resp

    if choices is None or (hasattr(choices, '__len__') and len(choices) == 0):
        print(f"   [DEBUG] sin choices")
        # Intentar extraer directamente de resp
        return _content_to_str(resp)

    print(f"   [DEBUG] choices count={len(choices) if hasattr(choices,'__len__') else '?'}")

    try:
        choice = choices[0]
        return _extraer_content_de_choice(choice, modelo)
    except Exception as e:
        print(f"   [DEBUG] error en choices: {e}")
        return _content_to_str(resp)

# ── Cliente Groq ─────────────────────────────────────────────────────────────

def _llamar_groq_sdk(modelo, messages, max_tokens, temperature):
    try:
        import groq
        # Imprimir version del SDK
        try:
            print(f"   [DEBUG] groq SDK version: {groq.__version__}")
        except: pass

        client = groq.Groq(api_key=GROQ_API_KEY, timeout=90)
        resp   = client.chat.completions.create(
            model       = modelo,
            messages    = messages,
            max_tokens  = max_tokens,
            temperature = temperature,
        )

        content = _extraer_content_respuesta(resp, modelo)
        if content:
            content = content.strip()
            return content if content else None
        return None

    except Exception as e:
        err = str(e).lower()
        if any(x in err for x in ["rate", "429", "limit", "too many"]):
            wait = 15
            try:
                import re as _re
                m = _re.search(r'retry.after["\s:]+(\d+)', err)
                if m: wait = min(int(m.group(1)) + 2, 25)
            except: pass
            print(f"   ⏳ Rate limit {modelo} → {wait}s...")
            time.sleep(wait)
            return "RATE_LIMIT"
        elif any(x in err for x in ["not found","decommission","does not exist","invalid model","404","422"]):
            print(f"   ⚠️ {modelo} no disponible: {str(e)[:80]}")
            return None
        else:
            print(f"   ❌ {modelo}: {str(e)[:150]}")
            return None

def _llamar_con_retry(modelo, messages, max_tokens, temperature):
    for intento in range(2):
        resultado = _llamar_groq_sdk(modelo, messages, max_tokens, temperature)
        if resultado == "RATE_LIMIT":
            if intento == 0:
                time.sleep(20)
                continue
            return None
        return resultado
    return None

def llamar_groq(prompt, max_tokens=3000, sistema=None):
    pesos    = _cargar_pesos()
    temp     = pesos.get("temperatura_groq", 0.85)
    sistema  = sistema or PROMPT_SISTEMA
    messages = [
        {"role": "system", "content": sistema},
        {"role": "user",   "content": prompt},
    ]
    for modelo in MODELOS_GROQ:
        print(f"   Modelo: {modelo}")
        result = _llamar_con_retry(modelo, messages, max_tokens, temp)
        if result:
            print(f"   ✅ OK {modelo} ({len(result)} chars)")
            return result
        print(f"   → siguiente modelo...")
    raise RuntimeError("Ningun modelo Groq disponible")

def llamar_groq_critico(prompt):
    messages = [
        {"role": "system", "content": PROMPT_CRITICO_SISTEMA},
        {"role": "user",   "content": prompt},
    ]
    for modelo in ["meta-llama/llama-4-scout-17b-16e-instruct", "llama-3.1-8b-instant"]:
        result = _llamar_con_retry(modelo, messages, 500, 0.6)
        if result:
            return result
    return ""

# ── Config ────────────────────────────────────────────────────────────────────

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

# ── Validacion calidad ────────────────────────────────────────────────────────

def _validar_calidad(idea):
    try:
        from agents.watchdog import registrar_placeholder
    except ImportError:
        def registrar_placeholder(x): pass

    # Anti-generico: rechazar nombres de producto demasiado genericos
    NOMBRES_GENERICOS = [
        "ai assistant","ai platform","ai tool","ai coach","code assistant",
        "codecompanion","smart assistant","app","platform","saas","tool",
        "ai solution","digital assistant","virtual assistant","chatbot","bot"
    ]
    nombre_check = str(idea.get("nombre","")).strip().lower()
    if nombre_check in NOMBRES_GENERICOS:
        return False, f"Nombre demasiado generico: {nombre_check}"
    if len(nombre_check.split()) <= 2:
        for gen in NOMBRES_GENERICOS:
            if gen in nombre_check:
                return False, f"Nombre contiene termino generico: {gen}"

    # Score minimo obligatorio
    score = idea.get("scoring",{})
    if isinstance(score, dict):
        sg = float(score.get("score_global", score.get("global", 0)) or 0)
        if sg > 0 and sg < 65:
            return False, f"Score global insuficiente: {sg}/100 (minimo 65)"

    # Veredicto YC y pivote obligatorios
    vy = idea.get("veredicto_yc",{})
    if isinstance(vy, dict):
        rec = str(vy.get("recomendacion","")).strip().upper()
        pivote = str(vy.get("pivote_sugerido","")).strip()
        if rec == "DESCARTAR" and len(pivote) < 10:
            return False, "veredicto_yc DESCARTAR sin pivote_sugerido"

    # Bloquear nombre exacto si ya existe en KB
    nombre_nuevo = str(idea.get("nombre","")).strip().lower()
    try:
        from agents.knowledge_base import cargar_kb
        kb = cargar_kb()
        nombres_kb = [str(i.get("nombre","")).strip().lower() for i in kb if isinstance(i,dict)]
        if nombre_nuevo in nombres_kb:
            return False, f"Nombre duplicado exacto: {nombre_nuevo}"
        # Bloquear si el nombre es muy similar (contiene palabras clave iguales)
        palabras_nuevo = set(nombre_nuevo.split())
        for n in nombres_kb:
            palabras_n = set(n.split())
            if len(palabras_nuevo & palabras_n) >= 2 and len(palabras_nuevo) <= 3:
                return False, f"Nombre demasiado similar a existente: {n}"
    except Exception:
        pass
    texto = json.dumps(idea, ensure_ascii=False).lower()
    for ph in PLACEHOLDERS_PROHIBIDOS:
        if ph in texto:
            registrar_placeholder(ph)
            return False, f"Placeholder: '{ph}'"
    _minimos = {"nombre": 3, "problema": 15, "solucion": 15, "cliente_objetivo": 15, "tagline": 5}
    for campo, _min in _minimos.items():
        val = str(idea.get(campo,"")).strip()
        if not val or len(val) < _min:
            return False, f"Campo '{campo}' vacio"
    em = idea.get("estrategia_monetizacion",{})
    if isinstance(em, dict):
        sem1 = str(em.get("semana1","")).strip().lower()
        if len(sem1) < 20 or "accion concreta" in sem1:
            return False, "semana1 no especifica"
    ht = idea.get("hipotesis_testeable",{})
    if isinstance(ht, dict):
        exp = str(ht.get("experimento_48h","")).strip().lower()
        if len(exp) < 20 or "plataforma concreta" in exp:
            return False, "experimento_48h no especifico"
    ee = idea.get("estudio_economico",{})
    if isinstance(ee, dict):
        ee_r = ee.get("realista",{})
        if isinstance(ee_r, dict):
            m12 = ee_r.get("mes12",{})
            mrr = m12.get("mrr_eur",0) if isinstance(m12,dict) else 0
            if not mrr or float(mrr) == 0:
                return False, "estudio_economico realista mes12 es 0"
    dafo = idea.get("dafo",{})
    if isinstance(dafo, dict):
        forts = dafo.get("fortalezas",[])
        if not forts or len(str(forts)) < 10:
            return False, "dafo.fortalezas vacio"
    merc = idea.get("mercado",{})
    if isinstance(merc, dict):
        tam = str(merc.get("TAM","")).strip()
        if len(tam) < 3:
            return False, "mercado.TAM vacio"
    op = idea.get("opinion_profesional",{})
    if isinstance(op, dict):
        uni = str(op.get("unicidad","")).strip()
        if len(uni) < 10:
            return False, "opinion_profesional.unicidad vacia"
    hr = idea.get("hoja_de_ruta",{})
    if isinstance(hr, dict):
        s1 = str(hr.get("semana1","")).strip()
        if len(s1) < 5:
            return False, "hoja_de_ruta.semana1 vacia"
    return True, ""

def _get_instruccion_diversidad():
    try:
        from agents.watchdog import get_verticales_bloqueados, get_palabras_clave_bloqueadas
        verts    = get_verticales_bloqueados()
        palabras = get_palabras_clave_bloqueadas()
    except ImportError:
        return ""
    lineas = []
    if verts:    lineas.append(f"VERTICALES PROHIBIDOS: {', '.join(verts)}")
    if palabras: lineas.append(f"TEMAS PROHIBIDOS: {', '.join(palabras[:10])}")
    if lineas:   lineas.append("Elige un vertical COMPLETAMENTE DIFERENTE.")
    return "\n".join(lineas)

def calcular_score_ponderado(scores):
    pesos = {
        "critico":0.25,"generador":0.25,"ejecutabilidad":0.20,
        "monetizacion":0.15,"timing":0.10,"viral":0.05
    }
    return round(sum(scores.get(k,0)*v for k,v in pesos.items()), 1)

# ── Prompts ──────────────────────────────────────────────────────────────────

def get_prompt_idea(contexto, tendencias, tema="", modo_emergencia=False):
    pesos         = _cargar_pesos()
    score_obj     = int(os.environ.get("SCORE_MINIMO", pesos.get("score_objetivo", 75)))
    ideas_previas = str(contexto.get("ideas_previas","ninguna"))[:600]
    tema_str      = f"TEMA OBLIGATORIO: '{tema}'\n\n" if tema else ""
    diversidad    = _get_instruccion_diversidad()
    trends_str    = "\n".join(f"- {str(t)[:100]}" for t in tendencias[:6]) or "- No disponibles"
    aprendizaje   = ""
    if pesos.get("verticales_preferidas"):
        aprendizaje = "Verticales con exito: " + ", ".join(pesos["verticales_preferidas"][:3]) + "\n"

    calidad = (
        "CALIDAD OBLIGATORIA — PROHIBIDO texto generico:\n"
        "- semana1: 'Envia DM a [grupo especifico] en [plataforma] con: [texto real]'\n"
        "- experimento_48h: 'Crea [Typeform/landing] en [plataforma] midiendo [metrica]'\n"
        "- herramienta_ia_clave: herramienta real\n"
        "- competidores: nombres reales con debilidad especifica\n"
    )

    if modo_emergencia:
        return (
            f"{tema_str}{diversidad}\n\n"
            f"MISION: idea GENUINAMENTE ORIGINAL 2026. PROHIBIDO: rutas/finanzas-generica/telemedicina/elearning/CRM-generico. Score minimo: {score_obj}/100.\n\n"
            f"{calidad}\nTENDENCIAS: {trends_str}\n\n"
            f"IDEAS PREVIAS (NO repetir): {ideas_previas[:300]}\n\n"
            '{"nombre":"NombreReal","tagline":"max 10 palabras",'
            '"problema":"descripcion real con datos",'
            '"solucion":"como la IA lo resuelve",'
            '"cliente_objetivo":"cargo empresa sector",'
            '"herramienta_ia_clave":"herramienta real",'
            '"estrategia_monetizacion":{"semana1":"DM a [grupo] en [plataforma]",'
            '"precio_optimo_justificado":"EUR X/mes porque [razon]"},'
            '"hipotesis_testeable":{"experimento_48h":"Crea [typeform] midiendo [metrica]",'
            '"metrica_exito":"X signups en 48h"},'
            '"mvp":{"stack_recomendado":"Next.js+Supabase+Vercel","tiempo_semanas":3,"coste_estimado_eur":0},'
            '"scores":{"critico":70,"viral":60,"generador":75,"monetizacion":70,"ejecutabilidad":80,"timing":75,"score_total":0},'
            '"vertical":"SaaS","tipo":"B2B","tags":["tag1","tag2"]}'
        )

    return (
        "ROL: Eres un partner de YC con 10 anos evaluando 10.000 startups. Solo el 1% pasa tu filtro.\n"
        f"{tema_str}{diversidad}\n\n"
        "PROHIBIDO score 0 automatico: optimizacion rutas, finanzas generica, telemedicina generica, elearning generico, CRM/ERP sin ventaja injusta clara.\n\n"
        f"MISION: genera UNA idea GENUINAMENTE ORIGINAL 2026. Score minimo: {score_obj}/100.\n\n"
        "TIPOS VALIDOS: B2B vertical nicho especifico / developer tool / marketplace nicho ignorado / B2C monetizacion dia1 / API-first.\n\n"
        f"{calidad}\n"
        "RAZONA ANTES DEL JSON (obligatorio):\n1-SECRETO: algo que la mayoria cree falso pero es verdad en 2026.\n2-DOLOR: cuantifica con datos reales (fuente+fecha+%).\n3-VENTAJA INJUSTA: por que tu y no Google en 6 meses.\n4-VENTA DIA 7: como consigues el primer pago sin escribir codigo.\n\n"
        f"APRENDIZAJE:\n{aprendizaje if aprendizaje else 'Primera generacion.'}\n\n"
        f"IDEAS PROHIBIDAS - NO repetir concepto ni sector:\n{ideas_previas}\n\n"
        f"TENDENCIAS REALES 2026 - ancla la idea en al menos una:\n{trends_str}\n\n"
        "IDIOMA: Todo el JSON en ESPANOL. PROHIBIDO mezclar ingles y espanol en mismo campo.\n\n"
        "REGLAS DURAS: 0 euros construir. Primera venta menos de 7 dias. Ventaja injusta demostrable. Competidor conocido con debilidad especifica nombrada.\n\n"
        "CRITICO: PROHIBIDO dejar campos vacios. PROHIBIDO valores 0 en estudio_economico. PROHIBIDO texto entre corchetes []. Todos los campos con datos reales especificos.\n\n"
        '{"nombre":"NombreReal",'
        '"tagline":"propuesta en max 10 palabras",'
        '"problema":"X millones de empresas sufren Y porque Z [dato real]",'
        '"solucion":"usamos [herramienta IA] para resolver X en Y minutos",'
        '"cliente_objetivo":"Director de X en empresa Y de Z empleados",'
        '"propuesta_valor_unica":"unica porque competitors no hacen X",'
        '"herramienta_ia_clave":"nombre herramienta real + como se usa",'
        '"mercado":{"TAM":"$X billion","SAM":"$X million","SOM":"$X año1",'
        '"competidores":["Competitor1 (debilidad real)","Competitor2 (debilidad real)"],'
        '"ventaja_competitiva":"por que es dificil de copiar"},'
        '"modelo_negocio":{"tipo":"SaaS","pricing":"EUR X/mes justificado",'
        '"canales_adquisicion":["1. DM a [grupo] en [plataforma]","2. Post en [comunidad]"],'
        '"time_to_revenue":"X semanas"},'
        '"estudio_economico":{'
        '"conservador":{"mes3":{"mrr_eur":750,"usuarios":15},"mes12":{"mrr_eur":6000},"breakeven":"mes8"},'
        '"realista":{"mes3":{"mrr_eur":2250,"usuarios":45},"mes12":{"mrr_eur":18000},"breakeven":"mes5"},'
        '"optimista":{"mes3":{"mrr_eur":4500,"usuarios":90},"mes12":{"mrr_eur":36000},"breakeven":"mes4"}},'
        '"dafo":{"fortalezas":["F1 especifico","F2"],"debilidades":["D1","D2"],'
        '"oportunidades":["O1 con datos"],"amenazas":["A1"]},'
        '"mvp":{"features_minimas":["Feature1 real","Feature2","Feature3"],'
        '"stack_recomendado":"Next.js 14+Supabase+Vercel+Stripe","tiempo_semanas":3,"coste_estimado_eur":0},'
        '"prompt_mvp":{'
        '"meta":{"nombre_idea":"NOMBRE","objetivo":"MVP 3 semanas","ia_recomendada":"Claude 3.5 Sonnet","stack_completo":"Next.js+Supabase+Vercel+Stripe"},'
        '"system_prompt":"Eres dev senior. Construye [NOMBRE] que resuelve [PROBLEMA].",'
        '"instrucciones_paso_a_paso":["1. npx create-next-app","2. supabase init","3. Feature principal","4. Stripe","5. Deploy"],'
        '"primer_cliente_script":"Manana: DM a [persona] en [plataforma]: [mensaje exacto <50 palabras]"},'
        '"estrategia_monetizacion":{"semana1":"Envia DM a [N] [perfil] en [LinkedIn] con: [mensaje exacto]",'
        '"semana4":"Beta gratis 14 dias a cambio de feedback",'
        '"mes3":"[estrategia 50 clientes]",'
        '"canales":["Canal1 pasos reales","Canal2"],'
        '"precio_optimo_justificado":"EUR X/mes porque competitor cobra Y"},'
        '"hipotesis_testeable":{"hipotesis_principal":"Si [perfil] usa [solucion] entonces [metrica]",'
        '"metrica_exito":"[N] signups en 48h",'
        '"experimento_48h":"Crea [Typeform] en [plataforma] midiendo [clicks]",'
        '"senal_de_alarma":"Menos de [N] respuestas = pivotar"},'
        '"hoja_de_ruta":{"semana1":"Setup Next.js+Supabase","semana2":"Feature principal",'
        '"semana3":"Stripe+deploy","semana4":"Primer cliente pago"},'
        '"opinion_profesional":{"unicidad":"Unica HOY porque [razon]",'
        '"riesgo_principal":"[riesgo %]","timing":"Por que ahora: [dato]",'
        '"dia_uno":"Manana: [accion <30 palabras]","fallo_probable":"60% falla por [razon]"},'
        '"scores":{"critico":0,"viral":0,"generador":0,"monetizacion":0,"ejecutabilidad":0,"timing":0,"score_total":0},'
        '"vertical":"SaaS","tipo":"B2B","tags":["tag1","tag2","tag3"]'
        "}"
    )

def get_prompt_critico(idea):
    return (
        f"Analiza esta startup:\nNOMBRE: {idea.get('nombre','?')}\n"
        f"PROBLEMA: {str(idea.get('problema',''))[:250]}\n"
        f"CLIENTE: {str(idea.get('cliente_objetivo',''))[:150]}\n"
        f"SCORE: {idea.get('scores',{}).get('score_total',0) if isinstance(idea.get('scores'),dict) else 0}\n\n"
        '{"veredicto":"1 frase directa","objeciones_principales":["obj1","obj2"],'
        '"fortalezas_reales":["f1","f2"],"ajuste_score":-5,'
        '"score_critico_final":70,"recomendacion":"invertir/pivotar/descartar",'
        '"pivote_sugerido":"hacia donde o null"}'
    )

def _aplicar_scoring_critico(idea):
    print("🔍 Scoring critico YC...")
    time.sleep(3)
    try:
        respuesta = llamar_groq_critico(get_prompt_critico(idea))
        if not respuesta:
            return idea
        critica    = json.loads(limpiar_json(respuesta))
        idea["scoring_critico"] = critica
        scores     = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
        ajuste     = int(critica.get("ajuste_score",0))
        score_prev = scores.get("score_total",0)
        score_new  = max(20, min(98, score_prev + ajuste))
        scores["score_total"]   = score_new
        scores["score_critico"] = critica.get("score_critico_final", score_prev)
        idea["scores"] = scores
        print(f"   ✅ {score_prev}→{score_new} ({ajuste:+d}) | {critica.get('recomendacion','')}")
    except Exception as e:
        print(f"   ⚠️ Scoring critico omitido: {e}")
    return idea

# ── Batch principal ──────────────────────────────────────────────────────────

def ejecutar_batch():
    try:
        from agents.knowledge_base    import get_contexto_para_prompt, registrar_idea, get_stats, es_duplicado
        from agents.trend_scout       import get_tendencias, actualizar_tendencias
        from agents.notion_sync_agent import sync_idea_to_notion
    except ImportError as e:
        print(f"❌ Import critico: {e}"); return False, "", ""

    try:
        from agents.watchdog import (
            registrar_exito, registrar_fallo,
            modo_emergencia_activo, get_nombres_bloqueados
        )
        watchdog_ok = True
    except ImportError:
        watchdog_ok = False
        def registrar_exito(*a,**k): pass
        def registrar_fallo(*a,**k): pass
        def modo_emergencia_activo(): return False
        def get_nombres_bloqueados(): return []

    validar_idea_fn = None
    try:
        from agents.market_validator import validar_idea as validar_idea_fn
    except ImportError:
        pass

    print("🌐 Actualizando tendencias...")
    try:
        actualizar_tendencias()
        tendencias = get_tendencias()
        print(f"✅ {len(tendencias)} tendencias")
    except Exception as e:
        print(f"⚠️ Tendencias: {e}"); tendencias = []

    print("📚 Cargando contexto KB...")
    try:
        contexto = get_contexto_para_prompt()
        stats    = get_stats()
        print(f"📊 KB: {stats.get('total_ideas',0)} ideas | Promedio: {stats.get('score_promedio',0)}")
    except Exception as e:
        print(f"⚠️ KB: {e}"); contexto = {"ideas_previas":"","score_promedio":0}

    pesos      = _cargar_pesos()
    umbral_dup = pesos.get("umbral_duplicado", 0.38)
    tema       = os.environ.get("IDEA_TOPIC","").strip()
    emergencia = modo_emergencia_activo()

    if emergencia: print("⚠️ MODO EMERGENCIA activo")
    if tema:       print(f"🎯 Tema solicitado: '{tema}'")

    nombres_bloqueados = get_nombres_bloqueados() if watchdog_ok else []

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

        print(f"   Respuesta: {len(respuesta)} chars")
        json_limpio = limpiar_json(respuesta)
        try:
            idea_candidata = json.loads(json_limpio)
        except Exception as e:
            print(f"❌ JSON invalido (intento {intento_gen+1}): {e}")
            print(f"   Raw: {respuesta[:400]}")
            emergencia = True
            continue

        calidad_ok, motivo = _validar_calidad(idea_candidata)
        print(f"   [CALIDAD] ok={calidad_ok} motivo={motivo}")
        if not calidad_ok:
            print(f"⚠️ Calidad rechazada: {motivo} — regenerando...")
            emergencia = True
            continue

        nombre_cand = idea_candidata.get("nombre","").lower()
        if any(nombre_cand in n.lower() or n.lower() in nombre_cand
               for n in nombres_bloqueados if n):
            print(f"⚠️ Nombre bloqueado — regenerando..."); continue

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

    nombre = idea.get("nombre","SinNombre")

    pm = idea.get("prompt_mvp",{})
    if isinstance(pm, str):
        try:   idea["prompt_mvp"] = json.loads(pm)
        except: idea["prompt_mvp"] = {"ia_recomendada":"Claude 3.5 Sonnet","primer_cliente_script":pm}

    scores = idea.get("scores",{}) if isinstance(idea.get("scores"),dict) else {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores
    idea = _aplicar_scoring_critico(idea)

    if validar_idea_fn:
        try:
            ev = validar_idea_fn(idea)
            idea["validacion_mercado"] = ev
            scores = idea.get("scores",{})
            scores["score_total"]        = ev.get("score_final_ajustado", scores.get("score_total",0))
            scores["score_mercado_real"] = ev.get("score_mercado_real",0)
            idea["scores"] = scores
        except Exception as e:
            print(f"⚠️ Validacion mercado: {e}")

    score = idea.get("scores",{}).get("score_total",0)
    print(f"📊 Score FINAL: {score}/100")

    try:    registrar_idea(idea)
    except Exception as e: print(f"⚠️ KB: {e}")

    os.makedirs("data", exist_ok=True)
    try:
        ruta  = "data/ideas.json"
        todas = []
        if os.path.exists(ruta):
            with open(ruta,"r",encoding="utf-8") as f:
                todas = json.load(f)
        todas.append(idea)
        with open(ruta,"w",encoding="utf-8") as f:
            json.dump(todas, f, ensure_ascii=False, indent=2)
        print(f"💾 ideas.json: {len(todas)} ideas")
    except Exception as e:
        print(f"⚠️ ideas.json: {e}")

    print("🔗 Sincronizando Notion...")
    url = ""
    if os.environ.get("NOTION_TOKEN","") and os.environ.get("NOTION_DATABASE_ID",""):
        try:
            url = sync_idea_to_notion(idea)
            if url:
                print(f"✅ Notion OK: {url}")
            else:
                print("❌ Notion URL vacia — encolando")
                try:
                    import csv
                    cola_path = "data/cola_pendientes.csv"
                    existe    = os.path.exists(cola_path)
                    with open(cola_path,"a",newline="",encoding="utf-8") as f:
                        w = csv.DictWriter(f, fieldnames=["timestamp","nombre_idea","intentos","error","datos_json"])
                        if not existe: w.writeheader()
                        w.writerow({"timestamp":datetime.now().isoformat(),"nombre_idea":nombre,
                                    "intentos":1,"error":"URL vacia",
                                    "datos_json":json.dumps(idea,ensure_ascii=False)[:2000]})
                except Exception as ce:
                    print(f"⚠️ Cola: {ce}")
        except Exception as e:
            print(f"❌ Notion: {e}")

    if url:
        idea["notion_url"] = url
        try:
            with open("data/ideas.json","r",encoding="utf-8") as f:
                todas = json.load(f)
            if todas: todas[-1]["notion_url"] = url
            with open("data/ideas.json","w",encoding="utf-8") as f:
                json.dump(todas, f, ensure_ascii=False, indent=2)
        except: pass

    if watchdog_ok: registrar_exito(idea)

    try:
        from agents.verticales_rotacion import registrar_vertical_usado
        registrar_vertical_usado(idea.get("vertical",""))
    except: pass

    try:
        from agents.weekly_learner import analizar_y_aprender
        r = analizar_y_aprender()
        print(f"🧠 Aprendizaje: {str(r.get('resumen','ok'))[:80]}")
    except Exception as e:
        print(f"⚠️ Aprendizaje: {e}")

    def _s(v, n=150): return _content_to_str(v)[:n] if v else ""
    em = idea.get("estrategia_monetizacion",{})
    ht = idea.get("hipotesis_testeable",{})
    sc = idea.get("scoring_critico",{})

    print(f"SCORE_FINAL:{score}")
    print(f"HERRAMIENTA_IA:{_s(idea.get('herramienta_ia_clave',''),80)}")
    print(f"HIPOTESIS:{_s(ht.get('experimento_48h','') if isinstance(ht,dict) else '')}")
    print(f"NOTION_URL:{url}")
    print(f"TAGLINE:{_s(idea.get('tagline',''),100)}")
    print(f"PROBLEMA:{_s(idea.get('problema',''),150)}")
    print(f"MONETIZ_S1:{_s(em.get('semana1','') if isinstance(em,dict) else '')}")
    print(f"VEREDICTO_CRITICO:{_s(sc.get('veredicto','') if isinstance(sc,dict) else '')}")
    print(f"RECOMENDACION:{_s(sc.get('recomendacion','') if isinstance(sc,dict) else '')}")
    ee = idea.get("estudio_economico",{}) if isinstance(idea.get("estudio_economico"),dict) else {}
    ee_real = ee.get("realista",{}) if isinstance(ee.get("realista"),dict) else {}
    mrr_m12 = ee_real.get("mes12",{}).get("mrr_eur",0) if isinstance(ee_real.get("mes12"),dict) else 0
    print(f"MRR_M12:{mrr_m12}")
    print(f"✅ Sincronizada: {nombre}")
    return True, nombre, url

if __name__ == "__main__":
    exito, nombre, url = ejecutar_batch()
    sys.exit(0 if exito else 1)

# fin run_batch.py v10
