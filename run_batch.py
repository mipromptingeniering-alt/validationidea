import os, sys, json, time
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PROMPT_SISTEMA = """Eres un analista de startups de clase mundial con 20 años de experiencia.
Tu misión: generar ideas de startup ORIGINALES, disruptivas y monetizables RÁPIDO.
Reglas absolutas:
1. NUNCA repitas ni hagas variaciones de ideas ya generadas
2. Prioriza ideas construibles GRATIS con herramientas IA actuales
3. Busca nichos donde la IA crea ventaja injusta y nueva HOY
4. Respondes SIEMPRE con JSON válido puro — sin texto, sin markdown, sin bloques ```"""

def _cargar_pesos() -> dict:
    try:
        with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "temperatura_groq":       0.9,
            "umbral_duplicado":       0.42,
            "verticales_preferidas":  [],
            "verticales_penalizadas": [],
            "tags_exitosos":          [],
            "ia_tools_top":           [],
            "score_objetivo":         75,
            "patrones_exitosos":      [],
        }

def get_prompt_idea(contexto: dict, tendencias: list, tema: str = "") -> str:
    pesos          = _cargar_pesos()
    tendencias_str = "\n".join(f"- {t}" for t in tendencias[:20]) if tendencias else "- No disponibles"
    tema_str       = f"\n🎯 TEMA SOLICITADO: '{tema}'\n" if tema else ""
    score_obj      = pesos.get("score_objetivo", 75)

    preferencias = ""
    if pesos.get("verticales_preferidas"):
        preferencias += f"\n✅ VERTICALES QUE FUNCIONAN (priorizarlas): {', '.join(pesos['verticales_preferidas'][:4])}"
    if pesos.get("verticales_penalizadas"):
        preferencias += f"\n❌ VERTICALES PENALIZADAS (evitar): {', '.join(pesos['verticales_penalizadas'][:4])}"
    if pesos.get("patrones_exitosos"):
        preferencias += f"\n🏆 PATRONES EXITOSOS: {', '.join(pesos['patrones_exitosos'][:3])}"
    if pesos.get("tags_exitosos"):
        preferencias += f"\n🏷️ TAGS EXITOSOS: {', '.join(pesos['tags_exitosos'][:5])}"
    if pesos.get("ia_tools_top"):
        preferencias += f"\n🤖 IA TOOLS TOP: {', '.join(pesos['ia_tools_top'][:3])}"

    aprendizaje = ""
    if contexto.get("total_analizadas", 0) > 5:
        aprendizaje = (
            f"\n📊 CONTEXTO DEL SISTEMA:\n"
            f"- Score promedio: {contexto.get('score_promedio', 0)} — genera ideas con score >= {score_obj}\n"
            f"- Tasa de exito: {contexto.get('tasa_exito', 'N/A')}\n"
            f"- Verticales saturadas: {contexto.get('verticales_saturadas', 'ninguna')}\n"
            f"- Verticales descartadas: {contexto.get('verticales_disliked', 'ninguna')}\n"
            f"{preferencias}\n"
        )

    return f"""
Genera UNA idea de startup COMPLETAMENTE ORIGINAL.
{tema_str}{aprendizaje}
IDEAS YA GENERADAS — NO repetir nombre, problema similar, ni vertical+tipo igual:
{contexto.get('ideas_previas', 'ninguna aun')}

SEÑALES DE MERCADO EN TIEMPO REAL:
{tendencias_str}

CRITERIOS OBLIGATORIOS:
- Construible GRATIS con IA actual (Cursor, Claude, n8n, Supabase free, Vercel free)
- Monetizable en menos de 4 semanas desde MVP
- Nicho MUY especifico
- Score objetivo >= {score_obj}/100

Responde UNICAMENTE con JSON puro (sin nada antes ni despues):
{{
  "nombre": "NombreProducto",
  "tagline": "Que hace en menos de 10 palabras",
  "problema": "Problema concreto y urgente con persona real.",
  "solucion": "Solucion especifica usando IA actual.",
  "cliente_objetivo": "Persona exacta: cargo, sector, empresa, dolor concreto.",
  "propuesta_valor_unica": "Ventaja defendible y dificil de copiar.",
  "herramienta_ia_clave": "Herramienta IA especifica que hace esto posible HOY",

  "mercado": {{
    "TAM": "$ con logica",
    "SAM": "$ con logica",
    "SOM": "Objetivo año 1 $",
    "competidores": ["Competidor1 — debilidad explotable", "Competidor2 — debilidad"],
    "ventaja_competitiva": "Moat real y dificil de copiar"
  }},

  "modelo_negocio": {{
    "tipo": "SaaS/Marketplace/B2B/B2C/API/etc.",
    "pricing": "Precio exacto con justificacion",
    "canales_adquisicion": ["Canal 1 gratuito — tactica concreta", "Canal 2"],
    "time_to_revenue": "X semanas"
  }},

  "estudio_economico": {{
    "conservador": {{
      "supuestos": "1 fundador, crecimiento lento",
      "mes6":  {{"mrr_eur": 800,   "usuarios": 15,  "cac_eur": 60,  "ltv_eur": 450}},
      "mes12": {{"mrr_eur": 3000,  "usuarios": 55,  "margen_pct": 62}},
      "mes24": {{"mrr_eur": 8000,  "arr_eur": 96000,  "breakeven": "mes 16"}}
    }},
    "realista": {{
      "supuestos": "Product-market fit mes 3",
      "mes6":  {{"mrr_eur": 4000,  "usuarios": 70,  "cac_eur": 45,  "ltv_eur": 700}},
      "mes12": {{"mrr_eur": 14000, "usuarios": 200, "margen_pct": 67}},
      "mes24": {{"mrr_eur": 40000, "arr_eur": 480000, "breakeven": "mes 9"}}
    }},
    "optimista": {{
      "supuestos": "Viral en nicho, equipo 2",
      "mes6":  {{"mrr_eur": 12000, "usuarios": 180, "cac_eur": 30,  "ltv_eur": 1100}},
      "mes12": {{"mrr_eur": 50000, "usuarios": 600, "margen_pct": 72}},
      "mes24": {{"mrr_eur": 150000,"arr_eur": 1800000,"breakeven": "mes 5"}}
    }}
  }},

  "dafo": {{
    "fortalezas":    ["F1 especifica", "F2", "F3"],
    "debilidades":   ["D1 honesta", "D2"],
    "oportunidades": ["O1 basada en tendencia real", "O2", "O3"],
    "amenazas":      ["A1 con nombre concreto", "A2"]
  }},

  "mvp": {{
    "features_minimas": ["Feature 1 — detalle tecnico", "Feature 2", "Feature 3"],
    "stack_recomendado": "Stack GRATUITO: Cursor+Claude, Supabase free, Vercel free, n8n self-hosted",
    "tiempo_semanas": 3,
    "coste_estimado_eur": 0
  }},

  "prompt_mvp": {{
    "ia_recomendada": "Claude 3.5 Sonnet en Cursor IDE",
    "prompt_completo": "Construye [NOMBRE] desde cero. Stack gratuito: [tecnologias]. Base de datos: [tablas]. Funcionalidades: 1) [feature], 2) [feature], 3) [feature]. Flujo usuario: [pasos]. Auth: [metodo]. Stripe: [implementacion]. Deploy: [plataforma]. Genera carpetas, archivos completos, .env.example y README."
  }},

  "estrategia_monetizacion": {{
    "semana1":  "5 primeros usuarios — canal y mensaje exacto",
    "semana4":  "Primera venta — como cerrarla",
    "mes3":     "50 clientes — estrategia con metricas",
    "mes6":     "Crecimiento sostenido — palanca principal",
    "canales":  ["Canal gratuito 1 paso a paso", "Canal gratuito 2"],
    "precio_optimo_justificado": "Precio y por que maximiza conversion"
  }},

  "hipotesis_testeable": {{
    "hipotesis_principal": "Si [cliente] usa [producto] entonces [resultado medible] en [tiempo]",
    "metrica_exito":       "Numero concreto que confirma que funciona",
    "experimento_48h":     "Test mas barato posible para validar en 48h sin codigo",
    "senal_de_alarma":     "Que señal indicaria que no tiene mercado"
  }},

  "opinion_profesional": "5 frases: (1) que la hace unica HOY, (2) riesgo principal, (3) por que el timing es ahora, (4) dia 1 si la ejecutaras, (5) en que podria fallar.",

  "scores": {{
    "critico":        75,
    "viral":          55,
    "generador":      80,
    "monetizacion":   72,
    "ejecutabilidad": 85,
    "timing":         78,
    "score_total":    0
  }},

  "vertical": "SaaS",
  "tipo": "B2B",
  "tags": ["tag1", "tag2", "tag3", "tag4"]
}}
"""

def calcular_score_ponderado(scores: dict) -> float:
    pesos = {
        "critico": 0.25, "generador": 0.25, "ejecutabilidad": 0.20,
        "monetizacion": 0.15, "timing": 0.10, "viral": 0.05
    }
    return round(sum(scores.get(k, 0) * v for k, v in pesos.items()), 1)

def llamar_groq(prompt: str) -> str:
    import groq
    pesos  = _cargar_pesos()
    temp   = pesos.get("temperatura_groq", 0.9)
    modelo = "llama-3.3-70b-versatile"
    client = groq.Groq(api_key=GROQ_API_KEY, timeout=60)
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
            choice = resp.choices
            if isinstance(choice, list):
                choice = choice
            if hasattr(choice, "message"):
                return choice.message.content.strip()
            elif isinstance(choice, dict):
                return choice.get("message", {}).get("content", "").strip()
            return str(choice)
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err:
                espera = (intento + 1) * 8
                print(f"⏳ Rate limit (intento {intento+1}) → {espera}s...")
                time.sleep(espera)
                if intento == 1:
                    modelo = "llama-3.1-8b-instant"
                    print(f"🔄 Cambiando a modelo ligero: {modelo}")
            else:
                raise
    raise RuntimeError("Groq no disponible tras 3 intentos")

def limpiar_json(texto) -> str:
    if not isinstance(texto, str):
        texto = json.dumps(texto, ensure_ascii=False)
    texto = texto.strip()
    if "```json" in texto:
        texto = texto.split("```json")[1].split("```")[0].strip()
    elif "```" in texto:
        texto = texto.split("```").split("```").strip()[1]
    inicio = texto.find("{")
    fin    = texto.rfind("}")
    if inicio != -1 and fin != -1:
        texto = texto[inicio:fin+1]
    return texto

def ejecutar_batch():
    try:
        from agents.knowledge_base    import get_contexto_para_prompt, registrar_idea, get_stats, es_duplicado
        from agents.trend_scout       import get_tendencias, actualizar_tendencias
        from agents.notion_sync_agent import sync_idea_to_notion
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False, "", ""

    # Importaciones opcionales — no bloquean si fallan
    validar_idea   = None
    generar_landing = None
    try:
        from agents.market_validator  import validar_idea
        from agents.landing_generator import generar_landing
    except ImportError as e:
        print(f"⚠️ Modulos opcionales no disponibles: {e}")

    print("🌐 Obteniendo tendencias...")
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
        print(f"📊 KB: {stats.get('total_ideas', 0)} ideas | Promedio: {stats.get('score_promedio', 0)}")
    except Exception as e:
        print(f"⚠️ KB: {e}")
        contexto = {
            "ideas_previas": "", "mejores_verticales": "", "tags_exitosos": "",
            "ia_tools_top": "", "total_analizadas": 0, "tasa_exito": "N/A",
            "score_promedio": 0, "verticales_saturadas": "", "verticales_disliked": ""
        }

    pesos      = _cargar_pesos()
    umbral_dup = pesos.get("umbral_duplicado", 0.42)
    tema       = os.environ.get("IDEA_TOPIC", "")
    if tema:
        print(f"🎯 Tema: '{tema}'")

    # Generar con hasta 3 reintentos anti-duplicado
    idea = None
    for intento_gen in range(3):
        print(f"🧠 Generando idea (intento {intento_gen + 1}/3)...")
        prompt = get_prompt_idea(contexto, tendencias, tema)
        try:
            respuesta = llamar_groq(prompt)
        except Exception as e:
            print(f"❌ Error Groq: {e}")
            return False, "", ""

        try:
            idea_candidata = json.loads(limpiar_json(respuesta))
        except Exception as e:
            print(f"❌ JSON invalido: {e} | Raw: {str(respuesta)[:500]}")
            return False, "", ""

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado: '{idea_candidata.get('nombre','?')}' similar a '{dup_nombre}' — regenerando...")
                contexto["ideas_previas"] += f"\n- {idea_candidata.get('nombre','?')} (DESCARTADA, similar a {dup_nombre})"
                continue
        except Exception as e:
            print(f"⚠️ Anti-dup error: {e}")

        idea = idea_candidata
        break

    if not idea:
        print("❌ No se pudo generar idea unica en 3 intentos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea: {nombre}")

    # Score IA
    scores = idea.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores

    # Validacion real de mercado (opcional)
    if validar_idea:
        try:
            evidencias = validar_idea(idea)
            idea["validacion_mercado"] = evidencias
            score_ajustado = evidencias.get("score_final_ajustado", scores["score_total"])
            scores["score_total"]          = score_ajustado
            scores["score_mercado_real"]   = evidencias.get("score_mercado_real", 0)
            idea["scores"] = scores
            print(f"   ✅ Score ajustado con datos reales: {score_ajustado}")
        except Exception as e:
            print(f"   ⚠️ Validacion real omitida: {e}")

    score = scores["score_total"]
    print(
        f"📊 Score FINAL: {score}/100 | "
        f"C:{scores.get('critico',0)} V:{scores.get('viral',0)} "
        f"G:{scores.get('generador',0)} M:{scores.get('monetizacion',0)} "
        f"E:{scores.get('ejecutabilidad',0)} T:{scores.get('timing',0)}"
    )

    # Guardar en KB
    try:
        registrar_idea(idea)
        print("💾 KB actualizada")
    except Exception as e:
        print(f"⚠️ Error KB: {e}")

    # Guardar en ideas.json
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

    # Landing page (opcional)
    landing_url = ""
    if generar_landing:
        try:
            landing = generar_landing(idea)
            landing_url = landing.get("url_publica", "")
            if landing_url:
                idea["landing_url"] = landing_url
                print(f"🌐 Landing: {landing_url}")
        except Exception as e:
            print(f"⚠️ Landing: {e}")

    # Sync Notion
    print("🔗 Sincronizando Notion...")
    url = ""
    try:
        url = sync_idea_to_notion(idea)
        if url:
            print(f"NOTION_URL:{url}")
    except Exception as e:
        print(f"❌ Notion: {e}")

    herramienta = idea.get("herramienta_ia_clave", "")
    hipotesis   = ""
    if isinstance(idea.get("hipotesis_testeable"), dict):
        hipotesis = idea["hipotesis_testeable"].get("experimento_48h", "")

    print(f"SCORE_FINAL:{score}")
    print(f"HERRAMIENTA_IA:{herramienta[:80]}")
    print(f"HIPOTESIS:{hipotesis[:120]}")
    print(f"LANDING_URL:{landing_url}")
    print(f"✅ Sincronizada: {nombre}")
    return True, nombre, url

if __name__ == "__main__":
    exito, nombre, url = ejecutar_batch()
    sys.exit(0 if exito else 1)

# aqui finaliza el codigo de run_batch.py
