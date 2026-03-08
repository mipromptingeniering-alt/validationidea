import os, sys, json, time
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PROMPT_SISTEMA = """Eres un analista de startups de clase mundial con 20 años de experiencia.
Tu misión: generar ideas de startup con potencial REAL de monetización rápida.
Basas tus análisis en datos reales del mercado, no en suposiciones optimistas.
Respondes SIEMPRE con JSON válido y nada más."""

def get_prompt_idea(contexto: dict, tendencias: list, tema: str = "") -> str:
    tendencias_str = "\n".join(f"- {t}" for t in tendencias[:6]) if tendencias else "- No disponibles"
    tema_str = f"\nTEMA ESPECÍFICO SOLICITADO: Genera una idea relacionada con '{tema}'\n" if tema else ""

    mejora_str = ""
    if contexto.get("total_analizadas", 0) > 5:
        mejora_str = (
            f"\nAPRENDIZAJE ACUMULADO — usa esto para generar una idea MEJOR que las anteriores:\n"
            f"- Verticales que han funcionado bien: {contexto.get('mejores_verticales','N/A')}\n"
            f"- Tags que correlacionan con éxito: {contexto.get('tags_exitosos','N/A')}\n"
            f"- Score promedio actual: {contexto.get('score_promedio','N/A')} — supéralo\n"
            f"- Tasa de éxito actual: {contexto.get('tasa_exito','N/A')} — mejórala\n"
        )

    return f"""
Genera UNA idea de startup original y con potencial real de monetización.
{tema_str}{mejora_str}
IDEAS YA GENERADAS (NO repetir ni hacer variaciones de estas):
{contexto.get('ideas_previas', 'ninguna aún')}

TENDENCIAS ACTUALES DEL MERCADO TECH (úsalas como inspiración):
{tendencias_str}

Responde ÚNICAMENTE con este JSON (sin texto antes ni después, sin markdown):
{{
  "nombre": "NombreProducto",
  "tagline": "Propuesta de valor en menos de 10 palabras",
  "problema": "Problema concreto y urgente que resuelve. Quién lo sufre y por qué importa ahora.",
  "solucion": "Cómo lo resuelve de forma única y mejor que las alternativas.",
  "cliente_objetivo": "Perfil exacto: empresa/persona, sector, tamaño, dolor específico.",
  "propuesta_valor_unica": "Ventaja real y defendible frente a competidores.",

  "mercado": {{
    "TAM": "Mercado total estimado en $ con justificación",
    "SAM": "Mercado alcanzable en $ con justificación",
    "SOM": "Objetivo realista año 1 en $",
    "competidores": ["Competidor1 — su debilidad", "Competidor2 — su debilidad"],
    "ventaja_competitiva": "Moat real y por qué es difícil de copiar"
  }},

  "modelo_negocio": {{
    "tipo": "SaaS / Marketplace / B2B / B2C / Freemium / etc.",
    "pricing": "Precio concreto con justificación basada en valor",
    "canales_adquisicion": ["Canal1 con táctica específica", "Canal2 con táctica específica"],
    "time_to_revenue": "X semanas desde lanzamiento MVP"
  }},

  "estudio_economico": {{
    "conservador": {{
      "supuestos": "Qué asumo en este escenario",
      "mes6":  {{"mrr_eur": 500,   "usuarios": 10, "cac_eur": 80,  "ltv_eur": 400}},
      "mes12": {{"mrr_eur": 2000,  "usuarios": 40, "margen_pct": 60}},
      "mes24": {{"mrr_eur": 6000,  "arr_eur": 72000,  "breakeven": "mes 18"}}
    }},
    "realista": {{
      "supuestos": "Qué asumo en este escenario",
      "mes6":  {{"mrr_eur": 3000,  "usuarios": 50,  "cac_eur": 60,  "ltv_eur": 600}},
      "mes12": {{"mrr_eur": 10000, "usuarios": 150, "margen_pct": 65}},
      "mes24": {{"mrr_eur": 30000, "arr_eur": 360000, "breakeven": "mes 10"}}
    }},
    "optimista": {{
      "supuestos": "Qué asumo en este escenario",
      "mes6":  {{"mrr_eur": 10000, "usuarios": 150, "cac_eur": 40,  "ltv_eur": 900}},
      "mes12": {{"mrr_eur": 40000, "usuarios": 500, "margen_pct": 70}},
      "mes24": {{"mrr_eur": 120000,"arr_eur": 1440000,"breakeven": "mes 6"}}
    }}
  }},

  "dafo": {{
    "fortalezas":    ["F1 concreta", "F2 concreta", "F3 concreta"],
    "debilidades":   ["D1 concreta", "D2 concreta"],
    "oportunidades": ["O1 concreta", "O2 concreta", "O3 concreta"],
    "amenazas":      ["A1 concreta", "A2 concreta"]
  }},

  "mvp": {{
    "features_minimas": ["Feature 1 imprescindible", "Feature 2", "Feature 3"],
    "stack_recomendado": "Tecnologías específicas y por qué para este caso",
    "tiempo_semanas": 8,
    "coste_estimado_eur": 0
  }},

  "prompt_mvp": {{
    "ia_recomendada": "Claude 3.5 Sonnet en Cursor IDE — porque tiene mejor razonamiento de arquitectura y es el más eficaz construyendo productos completos desde un prompt",
    "prompt_completo": "Construye [NOMBRE] desde cero. Es una aplicación [tipo] que [solución]. Stack: [tecnologías concretas]. Funcionalidades MVP: 1) [feature1 con detalle técnico completo], 2) [feature2 con detalle], 3) [feature3 con detalle]. Base de datos: [estructura de tablas exacta]. Flujo principal del usuario: [pasos detallados]. Autenticación: [método exacto]. Monetización integrada: [cómo cobrar con Stripe]. Deploy en: [plataforma]. Genera el proyecto completo con estructura de carpetas, todos los archivos, package.json o requirements.txt, y README de instalación paso a paso."
  }},

  "estrategia_monetizacion": {{
    "semana1":  "Acción concreta para conseguir primeros 5 usuarios",
    "semana4":  "Cómo conseguir la primera venta de pago",
    "mes3":     "Estrategia para escalar a 50 clientes",
    "mes6":     "Estrategia de crecimiento sostenido",
    "canales":  ["Canal con ROI más alto y cómo usarlo", "Canal secundario"],
    "precio_optimo_justificado": "Por qué este precio maximiza revenue sin frenar adopción"
  }},

  "opinion_profesional": "Análisis honesto en 4-5 frases: qué hace especial esta idea ahora, cuál es el riesgo principal, por qué AHORA es el momento, y qué harías primero si la ejecutaras mañana.",

  "scores": {{
    "critico":        75,
    "viral":          50,
    "generador":      80,
    "monetizacion":   70,
    "ejecutabilidad": 85,
    "timing":         75,
    "score_total":    0
  }},

  "vertical": "SaaS",
  "tipo": "B2B",
  "tags": ["tag1", "tag2", "tag3"]
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

def llamar_groq(prompt: str, modelo: str = "llama-3.3-70b-versatile") -> str:
    import groq
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
                temperature=0.8,
            )
            return resp.choices[0].message.content.strip()
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err:
                espera = (intento + 1) * 5
                print(f"⏳ Rate limit (intento {intento+1}) → {espera}s...")
                time.sleep(espera)
                if intento == 1:
                    modelo = "llama-3.1-8b-instant"
                    print(f"🔄 Cambiando a modelo ligero: {modelo}")
            else:
                raise
    raise RuntimeError("Groq no disponible tras 3 intentos")

def limpiar_json(texto) -> str:
    # Protección: si Groq devuelve lista u otro tipo, convertir a string
    if not isinstance(texto, str):
        texto = json.dumps(texto, ensure_ascii=False)
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

def ejecutar_batch():
    try:
        from agents.knowledge_base    import get_contexto_para_prompt, registrar_idea, get_stats
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
        contexto = {"ideas_previas": "", "mejores_verticales": "", "tags_exitosos": "",
                    "total_analizadas": 0, "tasa_exito": "N/A", "score_promedio": 0}

    tema = os.environ.get("IDEA_TOPIC", "")
    if tema:
        print(f"🎯 Tema forzado: '{tema}'")

    print("🧠 Generando idea con IA...")
    prompt = get_prompt_idea(contexto, tendencias, tema)
    try:
        respuesta = llamar_groq(prompt)
        print(f"✅ Respuesta recibida ({len(respuesta)} chars)")
    except Exception as e:
        print(f"❌ Error Groq: {e}")
        return False, "", ""

    try:
        json_limpio = limpiar_json(respuesta)
        idea = json.loads(json_limpio)
        print(f"✅ JSON parseado correctamente")
    except Exception as e:
        print(f"❌ JSON inválido: {e}")
        print(f"Raw (primeros 500 chars): {str(respuesta)[:500]}")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea generada: {nombre}")

    scores = idea.get("scores", {})
    scores["score_total"] = calcular_score_ponderado(scores)
    idea["scores"] = scores
    score = scores["score_total"]
    print(f"📊 Score: {score}/100 | C:{scores.get('critico',0)} V:{scores.get('viral',0)} G:{scores.get('generador',0)} M:{scores.get('monetizacion',0)} E:{scores.get('ejecutabilidad',0)} T:{scores.get('timing',0)}")

    try:
        registrar_idea(idea)
        print(f"💾 Guardada en KB")
    except Exception as e:
        print(f"⚠️ Error guardando en KB: {e}")

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
        print(f"💾 Guardada en ideas.json (total: {len(ideas_local)})")
    except Exception as e:
        print(f"⚠️ Error ideas.json: {e}")

    print("🔗 Sincronizando con Notion...")
    try:
        url = sync_idea_to_notion(idea)
        if url:
            print(f"NOTION_URL:{url}")
            print(f"SCORE_FINAL:{score}")
            print(f"✅ Sincronizada: {nombre}")
            print(f"✅ Notion OK: {url}")
            return True, nombre, url
        else:
            print(f"⚠️ Notion devolvió None — guardada localmente")
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
