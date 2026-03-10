import os, sys, json, time, re
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PROMPT_SISTEMA = (
    "Eres un analista de startups de clase mundial con 20 años en Silicon Valley. "
    "Generas ideas ORIGINALES con datos reales y monetizacion probada. "
    "REGLA ABSOLUTA: responde UNICAMENTE con un objeto JSON valido. "
    "Sin texto antes. Sin texto despues. Sin markdown. Solo JSON puro."
)

PROMPT_CRITICO = (
    "Eres un socio de YC con 15 años rechazando el 99% de las startups. "
    "Eres brutalmente honesto, no te gustan las ideas vagas ni los mercados saturados. "
    "REGLA ABSOLUTA: responde UNICAMENTE con un objeto JSON valido. Sin texto extra."
)

def _cargar_pesos() -> dict:
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

def get_prompt_idea(contexto: dict, tendencias: list, tema: str = "") -> str:
    pesos         = _cargar_pesos()
    score_obj     = pesos.get("score_objetivo", 75)
    ideas_previas = contexto.get("ideas_previas", "ninguna aun")[:1500]
    tema_str      = f"TEMA OBLIGATORIO: '{tema}'. Toda la idea DEBE girar en torno a este tema.\n\n" if tema else ""

    hn  = [t for t in tendencias if "[HN]"     in t][:5]
    gh  = [t for t in tendencias if "[GitHub"  in t][:4]
    rd  = [t for t in tendencias if "[Reddit]" in t][:3]
    ph  = [t for t in tendencias if "[PH]"     in t][:3]
    cur = [t for t in tendencias if not any(x in t for x in ["[HN]","[GitHub","[Reddit]","[PH]"])][:3]
    def fmt(lst): return "\n".join(f"  - {t}" for t in lst) if lst else "  - N/A"

    aprendizaje = ""
    if pesos.get("verticales_preferidas"):
        aprendizaje += f"Verticales con mejor historico (priorizar): {', '.join(pesos['verticales_preferidas'][:4])}\n"
    if pesos.get("verticales_penalizadas"):
        aprendizaje += f"Verticales a evitar: {', '.join(pesos['verticales_penalizadas'][:4])}\n"
    if pesos.get("patrones_exitosos"):
        aprendizaje += f"Patrones exitosos probados: {', '.join(pesos['patrones_exitosos'][:3])}\n"
    if pesos.get("tags_exitosos"):
        aprendizaje += f"Tags ganadores: {', '.join(pesos['tags_exitosos'][:6])}\n"
    if contexto.get("score_promedio", 0) > 0:
        aprendizaje += f"Score promedio actual {contexto['score_promedio']} — supera este numero\n"

    template_json = """{
  "nombre": "NombreProducto",
  "tagline": "Que hace en menos de 10 palabras",
  "problema": "Descripcion extensa del problema real con datos y persona concreta",
  "solucion": "Como la IA lo resuelve de forma unica y mejor que alternativas",
  "cliente_objetivo": "Persona exacta: cargo, sector, empresa, tamaño, dolor especifico",
  "propuesta_valor_unica": "Ventaja injusta dificil de copiar en 6 meses",
  "herramienta_ia_clave": "Herramienta IA especifica de GitHub trending que hace esto posible HOY",
  "mercado": {
    "TAM": "$ con calculo justificado",
    "SAM": "$ con calculo justificado",
    "SOM": "objetivo anio 1 $",
    "competidores": ["Competidor1 — debilidad explotable", "Competidor2 — debilidad"],
    "ventaja_competitiva": "Moat real y especifico"
  },
  "modelo_negocio": {
    "tipo": "SaaS",
    "pricing": "Precio exacto con justificacion psicologica",
    "canales_adquisicion": ["Canal 1 con tactica concreta paso a paso", "Canal 2"],
    "time_to_revenue": "X semanas"
  },
  "estudio_economico": {
    "conservador": {
      "supuestos": "1 fundador, crecimiento lento",
      "mes3":  {"mrr_eur": 300,   "usuarios": 5,   "cac_eur": 80,  "ltv_eur": 360},
      "mes6":  {"mrr_eur": 800,   "usuarios": 15,  "cac_eur": 60,  "ltv_eur": 450},
      "mes12": {"mrr_eur": 3000,  "usuarios": 55,  "margen_pct": 62},
      "mes24": {"mrr_eur": 8000,  "arr_eur": 96000, "breakeven": "mes 16"}
    },
    "realista": {
      "supuestos": "Product-market fit mes 3",
      "mes3":  {"mrr_eur": 1200,  "usuarios": 22,  "cac_eur": 55,  "ltv_eur": 650},
      "mes6":  {"mrr_eur": 4000,  "usuarios": 70,  "cac_eur": 45,  "ltv_eur": 700},
      "mes12": {"mrr_eur": 14000, "usuarios": 200, "margen_pct": 67},
      "mes24": {"mrr_eur": 40000, "arr_eur": 480000, "breakeven": "mes 9"}
    },
    "optimista": {
      "supuestos": "Viral en nicho, equipo 2",
      "mes3":  {"mrr_eur": 5000,  "usuarios": 80,  "cac_eur": 30,  "ltv_eur": 1000},
      "mes6":  {"mrr_eur": 12000, "usuarios": 180, "cac_eur": 30,  "ltv_eur": 1100},
      "mes12": {"mrr_eur": 50000, "usuarios": 600, "margen_pct": 72},
      "mes24": {"mrr_eur": 150000,"arr_eur": 1800000,"breakeven": "mes 5"}
    }
  },
  "dafo": {
    "fortalezas":    ["F1 especifica", "F2", "F3"],
    "debilidades":   ["D1 honesta con datos", "D2"],
    "oportunidades": ["O1 basada en tendencia real de arriba", "O2", "O3"],
    "amenazas":      ["A1 con nombre de empresa concreta", "A2"]
  },
  "mvp": {
    "features_minimas": ["Feature 1 con detalle tecnico", "Feature 2", "Feature 3"],
    "stack_recomendado": "Next.js + Supabase free + Vercel free + Stripe",
    "tiempo_semanas": 3,
    "coste_estimado_eur": 0
  },
  "prompt_mvp": {
    "meta": {
      "nombre_idea": "NOMBRE REAL DE LA IDEA",
      "objetivo": "MVP funcional en 3 semanas con 0 euros",
      "ia_recomendada": "Claude 3.5 Sonnet en Cursor IDE",
      "stack_completo": "Next.js 14 + Supabase + Vercel + Stripe"
    },
    "system_prompt": "Eres desarrollador senior full-stack. Construye [NOMBRE_REAL] desde cero. [DESCRIPCION_REAL]",
    "contexto_negocio": {
      "problema_resuelto": "EL PROBLEMA REAL DE ESTA IDEA",
      "propuesta_valor":   "LA PROPUESTA REAL DE ESTA IDEA",
      "usuario_objetivo":  "EL CLIENTE REAL DE ESTA IDEA",
      "modelo_monetizacion": "EL PRICING REAL DE ESTA IDEA"
    },
    "arquitectura_tecnica": {
      "base_datos": "Schema Supabase real con tablas de esta idea concreta",
      "auth":       "Supabase Auth email/password + magic link",
      "frontend":   "Next.js 14 App Router + Tailwind + shadcn/ui",
      "backend":    "Supabase Edge Functions o Next.js API Routes",
      "pagos":      "Stripe Checkout + webhook activar suscripcion",
      "deploy":     "Vercel free tier"
    },
    "instrucciones_paso_a_paso": [
      "1. npx create-next-app@latest [nombre] --typescript --tailwind",
      "2. Configura Supabase: crea proyecto, SQL schema real, .env.local",
      "3. Implementa [FEATURE_1_REAL] con detalle tecnico",
      "4. Implementa [FEATURE_2_REAL] con detalle tecnico",
      "5. Integra Stripe: producto, webhook, checkout",
      "6. Deploy Vercel: repo, env vars, deploy"
    ],
    "features_mvp": [
      {"nombre": "FEATURE_1_REAL", "descripcion": "Detalle tecnico completo", "prioridad": "P0"},
      {"nombre": "FEATURE_2_REAL", "descripcion": "Detalle tecnico completo", "prioridad": "P0"},
      {"nombre": "FEATURE_3_REAL", "descripcion": "Detalle tecnico completo", "prioridad": "P1"}
    ],
    "output_esperado": [
      "Estructura de carpetas completa",
      "Schema SQL Supabase ejecutable",
      "Componentes React funcionales",
      "API routes implementadas",
      "Stripe completo con webhook",
      ".env.example con todas las variables",
      "README con instrucciones deploy"
    ],
    "primer_cliente_script": "Accion exacta para conseguir primer cliente en 48h"
  },
  "estrategia_monetizacion": {
    "semana1": "Accion concreta con canal y mensaje exacto para 5 usuarios",
    "semana4": "Como cerrar primera venta con plataforma concreta",
    "mes3":    "50 clientes — estrategia detallada con metricas",
    "mes6":    "Palanca de crecimiento principal con numero",
    "canales": ["Canal 1 paso a paso gratuito", "Canal 2 paso a paso gratuito"],
    "precio_optimo_justificado": "Precio y por que maximiza conversion y LTV"
  },
  "hipotesis_testeable": {
    "hipotesis_principal": "Si [cliente exacto] usa [producto] entonces [resultado medible] en [tiempo]",
    "metrica_exito":       "Numero concreto y fecha que confirma exito",
    "experimento_48h":     "Test sin codigo para validar en 48h con plataforma concreta",
    "senal_de_alarma":     "Metrica que indicaria que no tiene mercado"
  },
  "hoja_de_ruta": {
    "semana1": "Hito concreto",
    "semana2": "Hito concreto",
    "semana3": "MVP listo y funcional",
    "semana4": "Primer cliente de pago",
    "mes3": "Objetivo con numero",
    "mes6": "Objetivo con numero"
  },
  "opinion_profesional": {
    "unicidad":        "Que la hace unica HOY en el mercado citando tendencia",
    "riesgo_principal":"Mayor riesgo con probabilidad estimada en %",
    "timing":          "Por que ahora es el momento exacto citando tendencia real",
    "dia_uno":         "Primera accion concreta si la ejecutaras manana",
    "fallo_probable":  "En que podria fallar siendo honesto"
  },
  "scores": {
    "critico": 75, "viral": 55, "generador": 80,
    "monetizacion": 72, "ejecutabilidad": 85, "timing": 78, "score_total": 0
  },
  "vertical": "SaaS",
  "tipo": "B2B",
  "tags": ["tag1", "tag2", "tag3", "tag4"]
}"""

    return (
        f"{tema_str}"
        f"MISION: Genera UNA idea de startup COMPLETAMENTE ORIGINAL para 2026.\n\n"
        f"APRENDIZAJE DEL SISTEMA (ajusta tu idea a estos patrones):\n"
        f"{aprendizaje if aprendizaje else 'Sistema en fase inicial — genera idea de maxima calidad.'}\n\n"
        f"IDEAS YA GENERADAS (PROHIBIDO repetir nombre, problema similar o vertical+tipo igual):\n"
        f"{ideas_previas}\n\n"
        f"SEÑALES DE MERCADO EN TIEMPO REAL:\n"
        f"[HackerNews]:\n{fmt(hn)}\n"
        f"[GitHub trending — herramientas calientes]:\n{fmt(gh)}\n"
        f"[Reddit — problemas reales usuarios]:\n{fmt(rd)}\n"
        f"[ProductHunt — lanzamientos]:\n{fmt(ph)}\n"
        f"[IA curada]:\n{fmt(cur)}\n\n"
        f"CRITERIOS NO NEGOCIABLES:\n"
        f"- Construible con 0 euros usando IA actual\n"
        f"- Primera venta posible en menos de 4 semanas\n"
        f"- Nicho MUY especifico — NO para todos\n"
        f"- Aprovecha una herramienta de GitHub trending de arriba\n"
        f"- Score minimo requerido: {score_obj}/100\n"
        f"- opinion_profesional e hipotesis_testeable deben ser objetos JSON, NO strings\n\n"
        f"REGLA DE ORO: sustituye TODOS los valores de ejemplo del template por datos REALES de esta idea.\n\n"
        f"Devuelve SOLO este JSON con datos reales:\n"
        f"{template_json}"
    )

def get_prompt_critico(idea: dict) -> str:
    nombre   = idea.get("nombre", "?")
    tagline  = idea.get("tagline", "")
    problema = idea.get("problema", "")[:400]
    solucion = idea.get("solucion", "")[:400]
    cliente  = idea.get("cliente_objetivo", "")[:200]
    pvunica  = idea.get("propuesta_valor_unica", "")[:200]
    mercado  = idea.get("mercado", {})
    modelo   = idea.get("modelo_negocio", {})
    scores   = idea.get("scores", {})

    return (
        f"Analiza esta idea de startup con maxima objetividad como socio de YC:\n\n"
        f"NOMBRE: {nombre}\n"
        f"TAGLINE: {tagline}\n"
        f"PROBLEMA: {problema}\n"
        f"SOLUCION: {solucion}\n"
        f"CLIENTE: {cliente}\n"
        f"PROPUESTA UNICA: {pvunica}\n"
        f"TAM: {mercado.get('TAM','?') if isinstance(mercado,dict) else '?'}\n"
        f"COMPETIDORES: {mercado.get('competidores','?') if isinstance(mercado,dict) else '?'}\n"
        f"PRICING: {modelo.get('pricing','?') if isinstance(modelo,dict) else '?'}\n"
        f"SCORE IA: {scores.get('score_total',0)}\n\n"
        f"Responde SOLO con este JSON:\n"
        '{"veredicto": "1 frase directa — buena/mala/interesante y por que",'
        '"objeciones_principales": ["objecion1 concreta con dato", "objecion2", "objecion3"],'
        '"fortalezas_reales": ["fortaleza1 confirmada", "fortaleza2"],'
        '"ajuste_score": -5,'
        '"score_critico_final": 70,'
        '"recomendacion": "invertir/pivotar/descartar",'
        '"pivote_sugerido": "Si pivotar, hacia donde exactamente. Si no, escribe null"}'
    )

def calcular_score_ponderado(scores: dict) -> float:
    pesos = {
        "critico": 0.25, "generador": 0.25, "ejecutabilidad": 0.20,
        "monetizacion": 0.15, "timing": 0.10, "viral": 0.05
    }
    return round(sum(scores.get(k, 0) * v for k, v in pesos.items()), 1)

def _llamar_groq_raw(prompt: str, system: str, temp: float = 0.7, max_tokens: int = 1000) -> str:
    """Llamada directa a Groq sin reintentos de modelo — para llamadas secundarias."""
    import groq
    client = groq.Groq(api_key=GROQ_API_KEY, timeout=60)
    try:
        resp = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=max_tokens,
            temperature=temp,
        )
        if resp.choices and resp.choices[0].message.content:
            return resp.choices[0].message.content.strip()
    except Exception as e:
        print(f"   ⚠️ Groq raw: {e}")
    return ""

def llamar_groq(prompt: str) -> str:
    import groq
    pesos   = _cargar_pesos()
    temp    = pesos.get("temperatura_groq", 0.85)
    modelos = ["llama-3.3-70b-versatile", "llama3-70b-8192", "mixtral-8x7b-32768"]
    client  = groq.Groq(api_key=GROQ_API_KEY, timeout=90)

    for modelo in modelos:
        print(f"   Modelo: {modelo}")
        for intento in range(3):
            try:
                resp = client.chat.completions.create(
                    model=modelo,
                    messages=[
                        {"role": "system", "content": PROMPT_SISTEMA},
                        {"role": "user",   "content": prompt},
                    ],
                    max_tokens=4000,
                    temperature=temp,
                )
                n = len(resp.choices) if resp.choices else 0
                print(f"   choices: {n}")
                if n == 0:
                    print(f"   ⚠️ choices vacio en {modelo}")
                    break
                content = resp.choices[0].message.content
                if content and content.strip():
                    print(f"✅ OK {modelo} ({len(content)} chars)")
                    return content.strip()
                print(f"   ⚠️ content vacio en {modelo}")
                break
            except Exception as e:
                err = str(e).lower()
                if "rate" in err or "429" in err or "limit" in err:
                    espera = (intento + 1) * 20
                    print(f"   ⏳ Rate limit → {espera}s...")
                    time.sleep(espera)
                elif any(x in err for x in ["not found","decommission","does not exist","invalid model"]):
                    print(f"   ⚠️ {modelo} no disponible")
                    break
                else:
                    print(f"   ❌ {modelo}: {e}")
                    break

    raise RuntimeError("Ningun modelo Groq disponible")

def limpiar_json(texto: str) -> str:
    if not isinstance(texto, str):
        return json.dumps(texto, ensure_ascii=False)
    texto = texto.strip()
    if "```json" in texto:
        texto = texto.split("```json").split("```").strip()[1]
    elif "```" in texto:
        texto = texto.split("```")[1].split("```")[0].strip()
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1:
        texto = texto[inicio:fin+1]
    return texto

def _aplicar_scoring_critico(idea: dict) -> dict:
    """
    Mejora #2: Segunda IA con rol de inversor YC critico.
    Ajusta el score final y añade objeciones reales.
    """
    print("🔍 Aplicando scoring critico (IA inversora)...")
    try:
        prompt   = get_prompt_critico(idea)
        respuesta = _llamar_groq_raw(prompt, PROMPT_CRITICO, temp=0.6, max_tokens=800)
        if not respuesta:
            return idea

        critica = json.loads(limpiar_json(respuesta))
        idea["scoring_critico"] = critica

        # Aplicar ajuste al score total
        scores       = idea.get("scores", {})
        ajuste       = critica.get("ajuste_score", 0)
        score_actual = scores.get("score_total", 0)
        score_nuevo  = max(20, min(98, score_actual + ajuste))
        scores["score_total"]    = score_nuevo
        scores["score_critico"]  = critica.get("score_critico_final", score_actual)
        idea["scores"] = scores

        recomendacion = critica.get("recomendacion","")
        veredicto     = critica.get("veredicto","")[:100]
        print(f"   ✅ Critica: {recomendacion} | Score ajustado: {score_actual} → {score_nuevo} ({ajuste:+d})")
        print(f"   📝 Veredicto: {veredicto}")
    except Exception as e:
        print(f"   ⚠️ Scoring critico omitido: {e}")

    return idea

def _auto_aprender():
    try:
        from agents.weekly_learner import analizar_y_aprender
        resultado = analizar_y_aprender()
        print(f"🧠 Auto-aprendizaje: {resultado.get('resumen','')[:120]}")
    except Exception as e:
        print(f"⚠️ Auto-aprendizaje omitido: {e}")

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
    except ImportError as e:
        print(f"⚠️ Modulos opcionales: {e}")

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
        contexto = {
            "ideas_previas": "", "total_analizadas": 0, "tasa_exito": "N/A",
            "score_promedio": 0, "verticales_saturadas": "", "verticales_disliked": ""
        }

    pesos      = _cargar_pesos()
    umbral_dup = pesos.get("umbral_duplicado", 0.38)
    tema       = os.environ.get("IDEA_TOPIC", "")
    if tema:
        print(f"🎯 Tema: '{tema}'")

    idea = None
    for intento_gen in range(4):
        print(f"🧠 Generando idea (intento {intento_gen+1}/4)...")
        prompt = get_prompt_idea(contexto, tendencias, tema)
        try:
            respuesta = llamar_groq(prompt)
        except Exception as e:
            print(f"❌ Error Groq: {e}")
            return False, "", ""

        try:
            idea_candidata = json.loads(limpiar_json(respuesta))
        except Exception as e:
            print(f"❌ JSON invalido: {e} | Raw: {str(respuesta)[:300]}")
            continue

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado de '{dup_nombre}' — ampliando contexto y regenerando...")
                contexto["ideas_previas"] += (
                    f"\n- DESCARTADA: '{idea_candidata.get('nombre','?')}' "
                    f"(similar a '{dup_nombre}' — genera algo COMPLETAMENTE diferente)"
                )
                continue
        except Exception as e:
            print(f"⚠️ Anti-dup: {e}")

        idea = idea_candidata
        break

    if not idea:
        print("❌ No se genero idea unica en 4 intentos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea aprobada: {nombre}")

    # Normalizar prompt_mvp
    pm = idea.get("prompt_mvp", {})
    if isinstance(pm, str):
        try:   idea["prompt_mvp"] = json.loads(pm)
        except: idea["prompt_mvp"] = {"ia_recomendada": "Claude 3.5 Sonnet", "primer_cliente_script": pm}

    # Score inicial
    scores = idea.get("scores", {})
    if not isinstance(scores, dict): scores = {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores

    # Mejora #2: Scoring critico con segunda IA
    idea = _aplicar_scoring_critico(idea)

    # Validacion real de mercado
    if validar_idea_fn:
        try:
            ev = validar_idea_fn(idea)
            idea["validacion_mercado"]   = ev
            scores = idea.get("scores", {})
            scores["score_total"]        = ev.get("score_final_ajustado", scores.get("score_total",0))
            scores["score_mercado_real"] = ev.get("score_mercado_real", 0)
            idea["scores"] = scores
            print(f"   ✅ Score con datos reales: {scores['score_total']}")
        except Exception as e:
            print(f"   ⚠️ Validacion omitida: {e}")

    score = idea.get("scores", {}).get("score_total", 0)
    print(f"📊 Score FINAL: {score}/100")

    try:
        registrar_idea(idea)
        print("💾 KB actualizada")
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
            landing_url = l.get("url_publica", "")
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

    herramienta = idea.get("herramienta_ia_clave", "")
    hipotesis   = ""
    if isinstance(idea.get("hipotesis_testeable"), dict):
        hipotesis = idea["hipotesis_testeable"].get("experimento_48h", "")
    tagline    = idea.get("tagline", "")
    problema   = idea.get("problema", "")[:150]
    monetiz    = ""
    if isinstance(idea.get("estrategia_monetizacion"), dict):
        monetiz = idea["estrategia_monetizacion"].get("semana1", "")[:120]
    veredicto_critico = ""
    if isinstance(idea.get("scoring_critico"), dict):
        veredicto_critico = idea["scoring_critico"].get("veredicto","")[:120]
    recomendacion = ""
    if isinstance(idea.get("scoring_critico"), dict):
        recomendacion = idea["scoring_critico"].get("recomendacion","")

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

# aqui finaliza el codigo de run_batch.py
