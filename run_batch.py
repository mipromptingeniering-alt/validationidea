import os, sys, json, time, re
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PROMPT_SISTEMA = (
    "Eres un analista de startups de clase mundial. "
    "Generas ideas originales y monetizables. "
    "REGLA ABSOLUTA: tu respuesta es UNICAMENTE un objeto JSON valido. "
    "Sin texto antes. Sin texto despues. Sin markdown. Sin explicaciones. Solo JSON."
)

def _cargar_pesos() -> dict:
    try:
        with open("config/prompt_weights.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {
            "temperatura_groq":       0.85,
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
    tendencias_str = "\n".join(f"- {t}" for t in tendencias[:15]) if tendencias else "- No disponibles"
    tema_str       = f"TEMA REQUERIDO: '{tema}'. " if tema else ""
    score_obj      = pesos.get("score_objetivo", 75)

    ideas_previas = contexto.get("ideas_previas", "ninguna aun")

    return (
        f"{tema_str}Genera UNA idea de startup original para el año 2026. "
        f"Score minimo requerido: {score_obj}/100. "
        f"Construible gratis con IA. Monetizable en menos de 4 semanas.\n\n"
        f"IDEAS YA EXISTENTES (NO repetir):\n{ideas_previas}\n\n"
        f"TENDENCIAS ACTUALES:\n{tendencias_str}\n\n"
        f"Devuelve SOLO este JSON con los campos reales (sin comentarios, sin markdown):\n"
        '{"nombre":"X","tagline":"X","problema":"X","solucion":"X",'
        '"cliente_objetivo":"X","propuesta_valor_unica":"X","herramienta_ia_clave":"X",'
        '"mercado":{"TAM":"X","SAM":"X","SOM":"X","competidores":["X"],"ventaja_competitiva":"X"},'
        '"modelo_negocio":{"tipo":"X","pricing":"X","canales_adquisicion":["X"],"time_to_revenue":"X"},'
        '"estudio_economico":{'
        '"conservador":{"supuestos":"X","mes6":{"mrr_eur":800,"usuarios":15,"cac_eur":60,"ltv_eur":450},"mes12":{"mrr_eur":3000,"usuarios":55,"margen_pct":62},"mes24":{"mrr_eur":8000,"arr_eur":96000,"breakeven":"mes 16"}},'
        '"realista":{"supuestos":"X","mes6":{"mrr_eur":4000,"usuarios":70,"cac_eur":45,"ltv_eur":700},"mes12":{"mrr_eur":14000,"usuarios":200,"margen_pct":67},"mes24":{"mrr_eur":40000,"arr_eur":480000,"breakeven":"mes 9"}},'
        '"optimista":{"supuestos":"X","mes6":{"mrr_eur":12000,"usuarios":180,"cac_eur":30,"ltv_eur":1100},"mes12":{"mrr_eur":50000,"usuarios":600,"margen_pct":72},"mes24":{"mrr_eur":150000,"arr_eur":1800000,"breakeven":"mes 5"}}},'
        '"dafo":{"fortalezas":["X"],"debilidades":["X"],"oportunidades":["X"],"amenazas":["X"]},'
        '"mvp":{"features_minimas":["X","X","X"],"stack_recomendado":"X","tiempo_semanas":3,"coste_estimado_eur":0},'
        '"prompt_mvp":{"ia_recomendada":"Claude 3.5 Sonnet en Cursor IDE","prompt_completo":"X"},'
        '"estrategia_monetizacion":{"semana1":"X","semana4":"X","mes3":"X","mes6":"X","canales":["X"],"precio_optimo_justificado":"X"},'
        '"hipotesis_testeable":{"hipotesis_principal":"X","metrica_exito":"X","experimento_48h":"X","senal_de_alarma":"X"},'
        '"opinion_profesional":"X",'
        '"scores":{"critico":75,"viral":55,"generador":80,"monetizacion":72,"ejecutabilidad":85,"timing":78,"score_total":0},'
        '"vertical":"SaaS","tipo":"B2B","tags":["tag1","tag2","tag3"]}'
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
        print(f"   Probando modelo: {modelo}")
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
                # Verificar que choices no este vacio
                if not resp.choices:
                    print(f"   ⚠️ {modelo}: choices vacio")
                    break
                content = resp.choices[0].message.content
                if content and content.strip():
                    print(f"✅ Respuesta de {modelo} ({len(content)} chars)")
                    return content.strip()
                print(f"   ⚠️ {modelo}: content vacio")
                break
            except Exception as e:
                err = str(e).lower()
                if "rate" in err or "429" in err or "limit" in err:
                    espera = (intento + 1) * 20
                    print(f"   ⏳ Rate limit {modelo} intento {intento+1} → {espera}s...")
                    time.sleep(espera)
                elif "model" in err and ("not found" in err or "decommission" in err or "exist" in err):
                    print(f"   ⚠️ Modelo {modelo} no disponible — probando siguiente")
                    break
                else:
                    print(f"   ❌ {modelo} error: {e}")
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
        print(f"📊 KB: {stats.get('total_ideas',0)} ideas | Promedio: {stats.get('score_promedio',0)}")
    except Exception as e:
        print(f"⚠️ KB: {e}")
        contexto = {
            "ideas_previas": "", "total_analizadas": 0, "tasa_exito": "N/A",
            "score_promedio": 0, "verticales_saturadas": "", "verticales_disliked": ""
        }

    pesos      = _cargar_pesos()
    umbral_dup = pesos.get("umbral_duplicado", 0.42)
    tema       = os.environ.get("IDEA_TOPIC", "")
    if tema:
        print(f"🎯 Tema: '{tema}'")

    idea = None
    for intento_gen in range(3):
        print(f"🧠 Generando idea (intento {intento_gen+1}/3)...")
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
            return False, "", ""

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado de '{dup_nombre}' — regenerando...")
                contexto["ideas_previas"] += f"\n- {idea_candidata.get('nombre','?')} (ya existe, similar a {dup_nombre})"
                continue
        except Exception as e:
            print(f"⚠️ Anti-dup: {e}")

        idea = idea_candidata
        break

    if not idea:
        print("❌ No se genero idea unica en 3 intentos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea: {nombre}")

    scores = idea.get("scores", {})
    if not isinstance(scores, dict):
        scores = {}
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
