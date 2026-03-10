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

def _cargar_pesos() -> dict:
    try:
        with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "temperatura_groq":       0.85,
            "umbral_duplicado":       0.38,
            "verticales_preferidas":  [],
            "verticales_penalizadas": [],
            "tags_exitosos":          [],
            "ia_tools_top":           [],
            "score_objetivo":         75,
            "patrones_exitosos":      [],
        }

def get_prompt_idea(contexto: dict, tendencias: list, tema: str = "") -> str:
    pesos         = _cargar_pesos()
    score_obj     = pesos.get("score_objetivo", 75)
    ideas_previas = contexto.get("ideas_previas", "ninguna aun")[:1500]
    tema_str      = f"TEMA OBLIGATORIO: '{tema}'. Toda la idea DEBE girar en torno a este tema.\n\n" if tema else ""

    # Tendencias agrupadas por fuente
    hn  = [t for t in tendencias if "[HN]"      in t][:5]
    gh  = [t for t in tendencias if "[GitHub"   in t][:4]
    rd  = [t for t in tendencias if "[Reddit]"  in t][:3]
    ph  = [t for t in tendencias if "[PH]"      in t][:3]
    cur = [t for t in tendencias if not any(x in t for x in ["[HN]","[GitHub","[Reddit]","[PH]"])][:3]
    def fmt(lst): return "\n".join(f"  • {t}" for t in lst) if lst else "  • N/A"

    tendencias_bloque = (
        f"SEÑALES DE MERCADO EN TIEMPO REAL:\n"
        f"[HackerNews]:\n{fmt(hn)}\n"
        f"[GitHub trending]:\n{fmt(gh)}\n"
        f"[Reddit — problemas reales]:\n{fmt(rd)}\n"
        f"[ProductHunt]:\n{fmt(ph)}\n"
        f"[IA curada]:\n{fmt(cur)}"
    )

    aprendizaje = ""
    if pesos.get("verticales_preferidas"):
        aprendizaje += f"✅ Verticales con mejor historico: {', '.join(pesos['verticales_preferidas'][:4])}\n"
    if pesos.get("verticales_penalizadas"):
        aprendizaje += f"❌ Verticales a evitar: {', '.join(pesos['verticales_penalizadas'][:4])}\n"
    if pesos.get("patrones_exitosos"):
        aprendizaje += f"🏆 Patrones exitosos: {', '.join(pesos['patrones_exitosos'][:3])}\n"
    if pesos.get("tags_exitosos"):
        aprendizaje += f"🏷️ Tags ganadores: {', '.join(pesos['tags_exitosos'][:6])}\n"
    if contexto.get("score_promedio", 0) > 0:
        aprendizaje += f"📊 Score promedio actual: {contexto['score_promedio']} — supera este numero\n"

    # Template JSON de salida — sin placeholders, todo descriptivo
    template_json = """{
  "nombre": "NombreProducto",
  "tagline": "Que hace en menos de 10 palabras",
  "problema": "Descripcion extensa del problema real con datos y persona concreta",
  "solucion": "Como la IA lo resuelve de forma unica y mejor que alternativas",
  "cliente_objetivo": "Persona exacta: cargo, sector, empresa, tamaño, dolor especifico",
  "propuesta_valor_unica": "Ventaja injusta dificil de copiar en 6 meses",
  "herramienta_ia_clave": "Herramienta IA especifica de las tendencias que hace esto posible HOY",
  "mercado": {
    "TAM": "$ con calculo justificado",
    "SAM": "$ con calculo justificado",
    "SOM": "objetivo año 1 $",
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
      "mes3":  {"mrr_eur": 5000,   "usuarios": 80,  "cac_eur": 30,  "ltv_eur": 1000},
      "mes6":  {"mrr_eur": 12000,  "usuarios": 180, "cac_eur": 30,  "ltv_eur": 1100},
      "mes12": {"mrr_eur": 50000,  "usuarios": 600, "margen_pct": 72},
      "mes24": {"mrr_eur": 150000, "arr_eur": 1800000, "breakeven": "mes 5"}
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
      "nombre_idea": "NOMBRE DE LA IDEA",
      "objetivo": "MVP funcional en 3 semanas con 0 euros",
      "ia_recomendada": "Claude 3.5 Sonnet en Cursor IDE",
      "stack_completo": "Next.js 14 + Supabase + Vercel + Stripe"
    },
    "system_prompt": "Eres un desarrollador senior full-stack experto en Next.js y Supabase. Tu tarea es construir [NOMBRE] desde cero, un [TIPO] que [SOLUCION]. Dirigido a [CLIENTE]. Prioriza codigo limpio, funcional y deployable en una sola sesion de Cursor.",
    "contexto_negocio": {
      "problema_resuelto": "EL PROBLEMA CONCRETO DE ESTA IDEA",
      "propuesta_valor": "LA PROPUESTA VALOR UNICA DE ESTA IDEA",
      "usuario_objetivo": "EL CLIENTE OBJETIVO DE ESTA IDEA",
      "modelo_monetizacion": "EL PRICING EXACTO DE ESTA IDEA"
    },
    "arquitectura_tecnica": {
      "base_datos": "Schema Supabase con tablas reales de esta idea",
      "auth": "Supabase Auth email/password + magic link",
      "frontend": "Next.js 14 App Router + Tailwind CSS + shadcn/ui",
      "backend": "Supabase Edge Functions o Next.js API Routes",
      "pagos": "Stripe Checkout + webhook para activar suscripcion",
      "deploy": "Vercel free tier"
    },
    "instrucciones_paso_a_paso": [
      "1. npx create-next-app@latest [nombre] --typescript --tailwind",
      "2. Configura Supabase: crea proyecto, ejecuta SQL schema, añade .env.local",
      "3. Implementa [FEATURE_1_REAL] — descripcion tecnica detallada",
      "4. Implementa [FEATURE_2_REAL] — descripcion tecnica detallada",
      "5. Integra Stripe: producto, webhook, checkout flow completo",
      "6. Deploy Vercel: conecta repo, env vars, primer deploy"
    ],
    "features_mvp": [
      {"nombre": "FEATURE_1_REAL", "descripcion": "Detalle tecnico completo", "prioridad": "P0"},
      {"nombre": "FEATURE_2_REAL", "descripcion": "Detalle tecnico completo", "prioridad": "P0"},
      {"nombre": "FEATURE_3_REAL", "descripcion": "Detalle tecnico completo", "prioridad": "P1"}
    ],
    "output_esperado": [
      "Estructura de carpetas completa",
      "Schema SQL Supabase listo para ejecutar",
      "Todos los componentes React funcionales",
      "API routes implementadas",
      "Integracion Stripe completa",
      ".env.example con todas las variables",
      "README.md con instrucciones deploy"
    ],
    "primer_cliente_script": "Descripcion exacta de como conseguir el primer cliente en 48h"
  },
  "estrategia_monetizacion": {
    "semana1": "Accion concreta con canal y mensaje exacto para 5 usuarios",
    "semana4": "Como cerrar primera venta con nombre de plataforma",
    "mes3":    "50 clientes — estrategia detallada con metricas",
    "mes6":    "Palanca de crecimiento principal con numero",
    "canales": ["Canal 1 paso a paso gratuito", "Canal 2 paso a paso gratuito"],
    "precio_optimo_justificado": "Precio y por que maximiza conversion y LTV"
  },
  "hipotesis_testeable": {
    "hipotesis_principal": "Si [cliente exacto] usa [producto] entonces [resultado medible] en [tiempo]",
    "metrica_exito": "Numero concreto y fecha que confirma exito",
    "experimento_48h": "Test sin codigo para validar en 48h con plataforma concreta",
    "senal_de_alarma": "Metrica que indicaria que no tiene mercado"
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
    "unicidad": "Que la hace unica HOY en el mercado, citando tendencia",
    "riesgo_principal": "Mayor riesgo con probabilidad estimada en %",
    "timing": "Por que ahora es el momento exacto citando tendencia real",
    "dia_uno": "Primera accion concreta si la ejecutaras mañana",
    "fallo_probable": "En que podria fallar siendo honesto"
  },
  "scores": {
    "critico": 75,
    "viral": 55,
    "generador": 80,
    "monetizacion": 72,
    "ejecutabilidad": 85,
    "timing": 78,
    "score_total": 0
  },
  "vertical": "SaaS",
  "tipo": "B2B",
  "tags": ["tag1", "tag2", "tag3", "tag4"]
}"""

    return (
        f"{tema_str}"
        f"MISION: Genera UNA idea de startup COMPLETAMENTE ORIGINAL para 2026.\n\n"
        f"APRENDIZAJE DEL SISTEMA:\n"
        f"{aprendizaje if aprendizaje else 'Sistema en fase inicial — genera idea de maxima calidad.'}\n\n"
        f"IDEAS YA GENERADAS (PROHIBIDO repetir nombre, problema similar o vertical+tipo igual):\n"
        f"{ideas_previas}\n\n"
        f"{tendencias_bloque}\n\n"
        f"CRITERIOS NO NEGOCIABLES:\n"
        f"• Construible con 0 euros usando IA actual\n"
        f"• Primera venta posible en menos de 4 semanas\n"
        f"• Nicho MUY especifico — NO 'para todos'\n"
        f"• Aprovecha una herramienta de GitHub trending de arriba\n"
        f"• Score minimo requerido: {score_obj}/100\n"
        f"• Los campos prompt_mvp, opinion_profesional y hipotesis_testeable deben ser OBJETOS (no strings)\n\n"
        f"REGLA DE ORO: sustituye TODOS los valores de ejemplo del template por datos REALES de esta idea especifica.\n\n"
        f"Devuelve SOLO este JSON con datos reales (no copies los valores de ejemplo, rellena con datos reales):\n"
        f"{template_json}"
    )

def calcular_score_ponderado(scores: dict) -> float:
    pesos = {
        "critico": 0.25, "generador": 0.25, "ejecutabilidad": 0.20,
        "monetizacion": 0.15, "timing": 0.10, "viral": 0.05
    }
    return round(sum(scores.get(k, 0) * v for k, v in pesos.items()), 1)

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
        texto = texto.split("```")[16].split("```")[0].strip()
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1:
        texto = texto[inicio:fin+1]
    return texto

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
            print(f"❌ JSON invalido: {e}")
            print(f"   Raw (300c): {str(respuesta)[:300]}")
            continue

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado de '{dup_nombre}' — regenerando con contexto ampliado...")
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

    # Normalizar prompt_mvp si vino como string
    pm = idea.get("prompt_mvp", {})
    if isinstance(pm, str):
        try:   idea["prompt_mvp"] = json.loads(pm)
        except: idea["prompt_mvp"] = {"ia_recomendada": "Claude 3.5 Sonnet", "primer_cliente_script": pm}

    scores = idea.get("scores", {})
    if not isinstance(scores, dict): scores = {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores

    if validar_idea_fn:
        try:
            ev = validar_idea_fn(idea)
            idea["validacion_mercado"]   = ev
            scores["score_total"]        = ev.get("score_final_ajustado", scores["score_total"])
            scores["score_mercado_real"] = ev.get("score_mercado_real", 0)
            idea["scores"] = scores
            print(f"   ✅ Score real: {scores['score_total']}")
        except Exception as e:
            print(f"   ⚠️ Validacion omitida: {e}")

    score = scores["score_total"]
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

    tagline  = idea.get("tagline", "")
    problema = idea.get("problema", "")[:200]
    monetiz  = ""
    if isinstance(idea.get("estrategia_monetizacion"), dict):
        monetiz = idea["estrategia_monetizacion"].get("semana1", "")[:150]

    print(f"SCORE_FINAL:{score}")
    print(f"HERRAMIENTA_IA:{herramienta[:80]}")
    print(f"HIPOTESIS:{hipotesis[:120]}")
    print(f"LANDING_URL:{landing_url}")
    print(f"TAGLINE:{tagline[:100]}")
    print(f"PROBLEMA:{problema[:150]}")
    print(f"MONETIZ_S1:{monetiz}")
    print(f"✅ Sincronizada: {nombre}")
    return True, nombre, url

if __name__ == "__main__":
    exito, nombre, url = ejecutar_batch()
    sys.exit(0 if exito else 1)

# aqui finaliza el codigo de run_batch.py
