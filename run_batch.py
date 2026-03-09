import os, sys, json, time
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

# ── Pesos del sistema de aprendizaje
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
 os.environ.get("GROQ_API_KEY", "")

PROMPT_SISTEMA = """Eres un analista de startups de clase mundial con 20 años de experiencia.
Tu misión: generar ideas de startup ORIGINALES, disruptivas y monetizables RÁPIDO.
Reglas absolutas:
1. NUNCA repitas ni hagas variaciones de ideas ya generadas — ni en nombre, ni en problema, ni en vertical+tipo
2. Prioriza ideas construibles GRATIS con herramientas IA actuales
3. Busca nichos donde la IA crea ventaja injusta y nueva HOY
4. Respondes SIEMPRE con JSON válido puro — sin texto, sin markdown, sin bloques ```"""

def get_prompt_idea(contexto: dict, tendencias: list, tema: str = "") -> str:
    tendencias_str = "\n".join(f"- {t}" for t in tendencias[:20]) if tendencias else "- No disponibles"
    tema_str       = f"\n🎯 TEMA SOLICITADO: '{tema}'\n" if tema else ""

    aprendizaje = ""
    if contexto.get("total_analizadas", 0) > 5:
        aprendizaje = (
            f"\n📊 APRENDIZAJE DEL SISTEMA:\n"
            f"- Verticales con mejor score: {contexto.get('mejores_verticales','N/A')}\n"
            f"- Tags exitosos: {contexto.get('tags_exitosos','N/A')}\n"
            f"- Herramientas IA que funcionan: {contexto.get('ia_tools_top','N/A')}\n"
            f"- Score promedio actual: {contexto.get('score_promedio',0)} — SUPÉRALO\n"
            f"- Tasa de éxito: {contexto.get('tasa_exito','N/A')} — MEJÓRALA\n"
            f"- Verticales SATURADAS (evitar): {contexto.get('verticales_saturadas','ninguna')}\n"
            f"- Verticales DESCARTADAS por feedback: {contexto.get('verticales_disliked','ninguna')}\n"
        )

    return f"""
Genera UNA idea de startup COMPLETAMENTE ORIGINAL y diferente.
{tema_str}{aprendizaje}
━━━━━━━━━━━━━━━━━━━
IDEAS YA GENERADAS — PROHIBIDO repetir nombre, problema similar, o vertical+tipo igual:
{contexto.get('ideas_previas','ninguna aún')}
━━━━━━━━━━━━━━━━━━━
SEÑALES DE MERCADO AHORA (úsalas como inspiración directa):
{tendencias_str}
━━━━━━━━━━━━━━━━━━━

CRITERIOS OBLIGATORIOS:
✅ Construible GRATIS con herramientas IA actuales (Cursor, Claude, n8n, Bolt.new, Supabase free, etc.)
✅ Monetizable en menos de 4 semanas desde MVP
✅ Nicho MUY específico — no ideas genéricas de "gestión" o "productividad"
✅ Aprovecha alguna herramienta IA de las señales de mercado
✅ Vertical, tipo y problema completamente diferente a las ideas ya generadas

Responde ÚNICAMENTE con JSON puro (sin nada antes ni después):
{{
  "nombre": "NombreProducto",
  "tagline": "Qué hace en menos de 10 palabras",
  "problema": "Problema concreto, urgente, con persona real que lo sufre ahora mismo.",
  "solucion": "Solución específica usando IA actual. Por qué es mejor que lo existente.",
  "cliente_objetivo": "Persona exacta: cargo, sector, empresa de X empleados, dolor concreto.",
  "propuesta_valor_unica": "Ventaja defendible. Por qué gana vs alternativas. Qué no pueden copiar fácil.",

  "herramienta_ia_clave": "Herramienta IA específica de las tendencias que hace posible esto HOY y no hace 2 años. Ej: 'n8n + GPT-4o permite automatizar X sin código por primera vez'",

  "mercado": {{
    "TAM": "Mercado total $ con fuente o lógica",
    "SAM": "Mercado alcanzable $ con lógica",
    "SOM": "Objetivo año 1 $ realista",
    "competidores": ["Competidor1 — debilidad específica y explotable", "Competidor2 — debilidad"],
    "ventaja_competitiva": "Moat concreto y difícil de copiar en <12 meses"
  }},

  "modelo_negocio": {{
    "tipo": "SaaS/Marketplace/B2B/B2C/API/etc.",
    "pricing": "Precio exacto con justificación basada en valor real entregado",
    "canales_adquisicion": ["Canal 1 gratuito con táctica concreta paso a paso", "Canal 2 gratuito"],
    "time_to_revenue": "X semanas"
  }},

  "estudio_economico": {{
    "conservador": {{
      "supuestos": "Crecimiento lento, competencia fuerte, 1 fundador solo",
      "mes6":  {{"mrr_eur": 800,   "usuarios": 15,  "cac_eur": 60,  "ltv_eur": 450}},
      "mes12": {{"mrr_eur": 3000,  "usuarios": 55,  "margen_pct": 62}},
      "mes24": {{"mrr_eur": 8000,  "arr_eur": 96000,   "breakeven": "mes 16"}}
    }},
    "realista": {{
      "supuestos": "Crecimiento normal, product-market fit en mes 3",
      "mes6":  {{"mrr_eur": 4000,  "usuarios": 70,  "cac_eur": 45,  "ltv_eur": 700}},
      "mes12": {{"mrr_eur": 14000, "usuarios": 200, "margen_pct": 67}},
      "mes24": {{"mrr_eur": 40000, "arr_eur": 480000,  "breakeven": "mes 9"}}
    }},
    "optimista": {{
      "supuestos": "Viral en nicho, partnerships tempranos, equipo de 2",
      "mes6":  {{"mrr_eur": 12000, "usuarios": 180, "cac_eur": 30,  "ltv_eur": 1100}},
      "mes12": {{"mrr_eur": 50000, "usuarios": 600, "margen_pct": 72}},
      "mes24": {{"mrr_eur": 150000,"arr_eur": 1800000, "breakeven": "mes 5"}}
    }}
  }},

  "dafo": {{
    "fortalezas":    ["F1 específica y real", "F2", "F3"],
    "debilidades":   ["D1 honesta", "D2"],
    "oportunidades": ["O1 basada en tendencia real ahora", "O2", "O3"],
    "amenazas":      ["A1 realista con nombre concreto", "A2"]
  }},

  "mvp": {{
    "features_minimas": ["Feature 1 — qué hace exactamente + por qué es la más importante", "Feature 2", "Feature 3"],
    "stack_recomendado": "Herramientas GRATUITAS específicas: ej 'Cursor+Claude para código, Supabase free para DB, n8n self-hosted para automatización, Vercel free para deploy'",
    "tiempo_semanas": 3,
    "coste_estimado_eur": 0
  }},

  "prompt_mvp": {{
    "ia_recomendada": "Claude 3.5 Sonnet en Cursor IDE",
    "prompt_completo": "Construye [NOMBRE] desde cero. Es [tipo de app] que [solución en 1 frase]. Stack COMPLETAMENTE GRATUITO: [lista tecnologías con versiones free]. Base de datos: [estructura exacta de tablas con campos]. Funcionalidades MVP: 1) [feature con lógica técnica detallada], 2) [feature], 3) [feature]. Flujo del usuario paso a paso: [cada paso]. Autenticación: [método]. Stripe para cobros: [implementación técnica]. Deploy gratuito: [plataforma + pasos]. Genera proyecto completo: estructura de carpetas, todos los archivos con código real, variables de entorno (.env.example), README con instalación paso a paso."
  }},

  "estrategia_monetizacion": {{
    "semana1":  "Acción gratuita y concreta para 5 primeros usuarios — canal exacto y mensaje",
    "semana4":  "Primera venta de pago — cómo cerrarla, a quién, con qué argumento",
    "mes3":     "Escalar a 50 clientes — estrategia con métricas concretas",
    "mes6":     "Crecimiento sostenido — palanca principal y objetivo MRR",
    "canales":  ["Canal 1 gratuito: táctica completa paso a paso", "Canal 2 gratuito"],
    "precio_optimo_justificado": "Precio exacto y por qué este número específico maximiza conversión y revenue"
  }},

  "opinion_profesional": "5 frases honestas: (1) qué hace única esta idea HOY, (2) riesgo principal real con nombre, (3) por qué el timing es ahora y no en 6 meses, (4) qué haría el día 1 si la ejecutara, (5) en qué podría fallar aunque todo salga bien.",

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
        "critico":        0.25,
        "generador":      0.25,
        "ejecutabilidad": 0.20,
        "monetizacion":   0.15,
        "timing":         0.10,
        "viral":          0.05,
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
            # Protección: choices puede venir como lista o como objeto
            choice = resp.choices[0]
            if isinstance(choice, list):
                choice = choice[0]
            if hasattr(choice, "message"):
                return choice.message.content.strip()
            elif isinstance(choice, dict):
                return choice.get("message", {}).get("content", "").strip()
            return str(choice)
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err:
                espera = (intento + 1) * 8
                print(f"⏳ Rate limit (intento {intento+1}) → esperando {espera}s...")
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
        print(f"❌ Error de importación: {e}")
        return False, "", ""

    print("🌐 Obteniendo tendencias...")
    try:
        actualizar_tendencias()
        tendencias = get_tendencias()
        print(f"✅ {len(tendencias)} tendencias cargadas")
    except Exception as e:
        print(f"⚠️ Tendencias no disponibles: {e}")
        tendencias = []

    print("📚 Cargando contexto KB...")
    try:
        contexto = get_contexto_para_prompt()
        stats    = get_stats()
        print(f"📊 KB: {stats.get('total_ideas',0)} ideas | Score promedio: {stats.get('score_promedio',0)}")
    except Exception as e:
        print(f"⚠️ Error KB: {e}")
        contexto = {"ideas_previas":"","mejores_verticales":"","tags_exitosos":"",
                    "ia_tools_top":"","total_analizadas":0,"tasa_exito":"N/A",
                    "score_promedio":0,"verticales_saturadas":"","verticales_disliked":""}

    tema = os.environ.get("IDEA_TOPIC", "")
    if tema:
        print(f"🎯 Tema forzado: '{tema}'")

    # Intentar hasta 3 veces si sale duplicado
    idea = None
    for intento_gen in range(3):
        print(f"🧠 Generando idea con IA (intento {intento_gen+1}/3)...")
        prompt = get_prompt_idea(contexto, tendencias, tema)
        try:
            respuesta = llamar_groq(prompt)
            print(f"✅ Respuesta recibida ({len(respuesta)} chars)")
        except Exception as e:
            print(f"❌ Error Groq: {e}")
            return False, "", ""

        try:
            json_limpio = limpiar_json(respuesta)
            idea_candidata = json.loads(json_limpio)
            print(f"✅ JSON parseado: {idea_candidata.get('nombre','?')}")
        except Exception as e:
            print(f"❌ JSON inválido: {e}")
            print(f"Raw (500 chars): {str(respuesta)[:500]}")
            return False, "", ""

        # ── Verificar duplicado semántico
        try:
            dup, dup_nombre = es_duplicado(idea_candidata)
            if dup:
                print(f"⚠️ Duplicado detectado: '{idea_candidata.get('nombre','?')}' ≈ '{dup_nombre}' — regenerando...")
                # Añadir al contexto para que no lo repita
                contexto["ideas_previas"] += f"\n- {idea_candidata.get('nombre','?')} (DESCARTADA POR SIMILAR A {dup_nombre})"
                continue
        except Exception as e:
            print(f"⚠️ Error verificando duplicado: {e}")

        idea = idea_candidata
        break

    if idea is None:
        print("❌ No se pudo generar una idea única tras 3 intentos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea aprobada: {nombre}")

    scores = idea.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores
    score = scores["score_total"]
    print(f"📊 Score: {score}/100 | C:{scores.get('critico',0)} V:{scores.get('viral',0)} G:{scores.get('generador',0)} M:{scores.get('monetizacion',0)} E:{scores.get('ejecutabilidad',0)} T:{scores.get('timing',0)}")

    try:
        registrar_idea(idea)
        print(f"💾 Guardada en KB")
    except Exception as e:
        print(f"⚠️ Error KB: {e}")

    os.makedirs("data", exist_ok=True)
    try:
        ruta = "data/ideas.json"
        ideas_local = []
        if os.path.exists(ruta):
            with open(ruta, "r", encoding="utf-8") as f:
                ideas_local = json.load(f)
        ideas_local.append(idea)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(ideas_local, f, ensure_ascii=False, indent=2)
        print(f"💾 ideas.json: total {len(ideas_local)}")
    except Exception as e:
        print(f"⚠️ Error ideas.json: {e}")

    print("🔗 Sincronizando con Notion...")
    try:
        url = sync_idea_to_notion(idea)
        if url:
            print(f"NOTION_URL:{url}")
            print(f"SCORE_FINAL:{score}")
            print(f"HERRAMIENTA_IA:{idea.get('herramienta_ia_clave','')[:80]}")
            print(f"✅ Sincronizada: {nombre}")
            return True, nombre, url
        else:
            print(f"SCORE_FINAL:{score}")
            print(f"✅ Sincronizada: {nombre}")
            return True, nombre, ""
    except Exception as e:
        print(f"❌ Error Notion: {e}")
        print(f"SCORE_FINAL:{score}")
        print(f"✅ Sincronizada: {nombre}")
        return True, nombre, ""

if __name__ == "__main__":
    exito, nombre, url = ejecutar_batch()
    sys.exit(0 if exito else 1)

# aqui finaliza el codigo de run_batch.py
