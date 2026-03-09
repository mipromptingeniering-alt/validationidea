import os, sys, json, time, re
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"
print("=" * 50)
print(f"🚀 run_batch iniciado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")

PROMPT_SISTEMA = """Eres un analista de startups de clase mundial con 20 años de experiencia.
Tu mision: generar ideas de startup ORIGINALES, disruptivas y monetizables RAPIDO.
Reglas absolutas:
1. NUNCA repitas ni hagas variaciones de ideas ya generadas
2. Prioriza ideas construibles GRATIS con herramientas IA actuales
3. Busca nichos donde la IA crea ventaja injusta y nueva HOY
4. Respondes SIEMPRE con JSON valido puro — sin texto, sin markdown, sin bloques```"""

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
    tema_str       = f"\nTEMA SOLICITADO: '{tema}'\n" if tema else ""
    score_obj      = pesos.get("score_objetivo", 75)

    preferencias = ""
    if pesos.get("verticales_preferidas"):
        preferencias += f"\n- VERTICALES QUE FUNCIONAN: {', '.join(pesos['verticales_preferidas'][:4])}"
    if pesos.get("verticales_penalizadas"):
        preferencias += f"\n- VERTICALES A EVITAR: {', '.join(pesos['verticales_penalizadas'][:4])}"
    if pesos.get("patrones_exitosos"):
        preferencias += f"\n- PATRONES EXITOSOS: {', '.join(pesos['patrones_exitosos'][:3])}"
    if pesos.get("tags_exitosos"):
        preferencias += f"\n- TAGS EXITOSOS: {', '.join(pesos['tags_exitosos'][:5])}"

    aprendizaje = ""
    if contexto.get("total_analizadas", 0) > 5:
        aprendizaje = (
            f"\nCONTEXTO:\n"
            f"- Score promedio: {contexto.get('score_promedio', 0)} — genera ideas con score >= {score_obj}\n"
            f"- Verticales saturadas: {contexto.get('verticales_saturadas', 'ninguna')}\n"
            f"- Verticales descartadas: {contexto.get('verticales_disliked', 'ninguna')}\n"
            f"{preferencias}\n"
        )

    return (
        f"Genera UNA idea de startup COMPLETAMENTE ORIGINAL.\n"
        f"{tema_str}{aprendizaje}\n"
        f"IDEAS YA GENERADAS (NO repetir nombre, problema similar, ni vertical+tipo igual):\n"
        f"{contexto.get('ideas_previas', 'ninguna aun')}\n\n"
        f"SEÑALES DE MERCADO AHORA:\n{tendencias_str}\n\n"
        f"CRITERIOS:\n"
        f"- Construible GRATIS con IA actual\n"
        f"- Monetizable en menos de 4 semanas\n"
        f"- Nicho MUY especifico\n"
        f"- Score >= {score_obj}/100\n\n"
        f"Responde UNICAMENTE con este JSON (sin texto antes ni despues):\n"
        + json.dumps({
            "nombre": "NombreProducto",
            "tagline": "Que hace en menos de 10 palabras",
            "problema": "Problema concreto y urgente con persona real.",
            "solucion": "Solucion especifica usando IA actual.",
            "cliente_objetivo": "Persona exacta: cargo, sector, empresa, dolor concreto.",
            "propuesta_valor_unica": "Ventaja defendible y dificil de copiar.",
            "herramienta_ia_clave": "Herramienta IA especifica que hace esto posible HOY",
            "mercado": {
                "TAM": "$ con logica",
                "SAM": "$ con logica",
                "SOM": "Objetivo anio 1 $",
                "competidores": ["Competidor1 debilidad", "Competidor2 debilidad"],
                "ventaja_competitiva": "Moat real"
            },
            "modelo_negocio": {
                "tipo": "SaaS/B2B/etc.",
                "pricing": "Precio exacto con justificacion",
                "canales_adquisicion": ["Canal 1 gratuito", "Canal 2"],
                "time_to_revenue": "X semanas"
            },
            "estudio_economico": {
                "conservador": {
                    "supuestos": "1 fundador, crecimiento lento",
                    "mes6":  {"mrr_eur": 800,   "usuarios": 15,  "cac_eur": 60,  "ltv_eur": 450},
                    "mes12": {"mrr_eur": 3000,  "usuarios": 55,  "margen_pct": 62},
                    "mes24": {"mrr_eur": 8000,  "arr_eur": 96000,  "breakeven": "mes 16"}
                },
                "realista": {
                    "supuestos": "Product-market fit mes 3",
                    "mes6":  {"mrr_eur": 4000,  "usuarios": 70,  "cac_eur": 45,  "ltv_eur": 700},
                    "mes12": {"mrr_eur": 14000, "usuarios": 200, "margen_pct": 67},
                    "mes24": {"mrr_eur": 40000, "arr_eur": 480000, "breakeven": "mes 9"}
                },
                "optimista": {
                    "supuestos": "Viral en nicho, equipo 2",
                    "mes6":  {"mrr_eur": 12000, "usuarios": 180, "cac_eur": 30,  "ltv_eur": 1100},
                    "mes12": {"mrr_eur": 50000, "usuarios": 600, "margen_pct": 72},
                    "mes24": {"mrr_eur": 150000,"arr_eur": 1800000,"breakeven": "mes 5"}
                }
            },
            "dafo": {
                "fortalezas":    ["F1", "F2", "F3"],
                "debilidades":   ["D1", "D2"],
                "oportunidades": ["O1", "O2", "O3"],
                "amenazas":      ["A1", "A2"]
            },
            "mvp": {
                "features_minimas": ["Feature 1", "Feature 2", "Feature 3"],
                "stack_recomendado": "Cursor+Claude, Supabase free, Vercel free",
                "tiempo_semanas": 3,
                "coste_estimado_eur": 0
            },
            "prompt_mvp": {
                "ia_recomendada": "Claude 3.5 Sonnet en Cursor IDE",
                "prompt_completo": "Construye [NOMBRE] desde cero. Stack gratuito: [tecnologias]. Base de datos: [tablas]. Funcionalidades: 1)[feature] 2)[feature] 3)[feature]. Flujo: [pasos]. Auth: [metodo]. Stripe: [impl]. Deploy: [plataforma]. Genera carpetas, archivos, .env.example y README."
            },
            "estrategia_monetizacion": {
                "semana1":  "5 primeros usuarios — canal y mensaje exacto",
                "semana4":  "Primera venta — como cerrarla",
                "mes3":     "50 clientes — estrategia con metricas",
                "mes6":     "Crecimiento sostenido",
                "canales":  ["Canal gratuito 1", "Canal gratuito 2"],
                "precio_optimo_justificado": "Precio y justificacion"
            },
            "hipotesis_testeable": {
                "hipotesis_principal": "Si [cliente] usa [producto] entonces [resultado] en [tiempo]",
                "metrica_exito":       "Numero concreto de exito",
                "experimento_48h":     "Test mas barato para validar en 48h sin codigo",
                "senal_de_alarma":     "Que señal indicaria que no tiene mercado"
            },
            "opinion_profesional": "5 frases honestas sobre la idea.",
            "scores": {
                "critico": 75, "viral": 55, "generador": 80,
                "monetizacion": 72, "ejecutabilidad": 85, "timing": 78, "score_total": 0
            },
            "vertical": "SaaS",
            "tipo": "B2B",
            "tags": ["tag1", "tag2", "tag3"]
        }, ensure_ascii=False, indent=2)
    )

def calcular_score_ponderado(scores: dict) -> float:
    pesos = {
        "critico": 0.25, "generador": 0.25, "ejecutabilidad": 0.20,
        "monetizacion": 0.15, "timing": 0.10, "viral": 0.05
    }
    return round(sum(scores.get(k, 0) * v for k, v in pesos.items()), 1)

def _extraer_content(resp) -> str:
    """
    Extractor defensivo que maneja TODOS los formatos posibles
    del SDK de Groq — sin importar version ni modelo.
    """
    try:
        # Formato estandar SDK moderno
        return resp.choices.message.content.strip()
    except (AttributeError, TypeError, IndexError):
        pass
    try:
        # choices es lista (SDK antiguo o modelo ligero)
        choice = resp.choices
        if isinstance(choice, list):
            choice = choice
        if hasattr(choice, "message"):
            return choice.message.content.strip()
        if isinstance(choice, dict):
            return choice.get("message", {}).get("content", "").strip()
    except (AttributeError, TypeError, IndexError):
        pass
    try:
        # Acceso dict directo
        return resp["choices"]["message"]["content"].strip()
    except (KeyError, TypeError, IndexError):
        pass
    try:
        # Serializar y extraer con regex
        raw = str(resp)
        m = re.search(r"content=['\"](.+?)['\"](?:,\s*role=|\))", raw, re.DOTALL)
        if m:
            return m.group(1).replace("\\n", "\n").replace("\\'", "'").strip()
    except Exception:
        pass
    raise ValueError(f"No se pudo extraer content de la respuesta: {type(resp)}")

def llamar_groq(prompt: str) -> str:
    """
    Llama a Groq con json_object forzado para obtener JSON limpio directo.
    Usa solo llama-3.3-70b-versatile — NO cambia modelo para evitar
    incompatibilidades de formato entre modelos.
    """
    import groq
    pesos  = _cargar_pesos()
    temp   = pesos.get("temperatura_groq", 0.9)
    modelo = "llama-3.3-70b-versatile"
    client = groq.Groq(api_key=GROQ_API_KEY, timeout=90)

    for intento in range(4):
        try:
            resp = client.chat.completions.create(
                model=modelo,
                messages=[
                    {"role": "system", "content": PROMPT_SISTEMA},
                    {"role": "user",   "content": prompt},
                ],
                max_tokens=4000,
                temperature=temp,
                response_format={"type": "json_object"},
            )
            content = _extraer_content(resp)
            if content:
                print(f"✅ Respuesta recibida ({len(content)} chars)")
                return content
            raise ValueError("Content vacio")
        except Exception as e:
            err = str(e).lower()
            if "rate" in err or "429" in err or "limit" in err:
                espera = [intento][15][16]
                print(f"⏳ Rate limit (intento {intento+1}/4) → esperando {espera}s...")
                time.sleep(espera)
            elif "json" in err and "response_format" in err:
                # Modelo no soporta json_object — reintentar sin el
                print(f"⚠️ json_object no soportado — reintentando sin response_format...")
                try:
                    resp2 = client.chat.completions.create(
                        model=modelo,
                        messages=[
                            {"role": "system", "content": PROMPT_SISTEMA},
                            {"role": "user",   "content": prompt},
                        ],
                        max_tokens=4000,
                        temperature=temp,
                    )
                    content = _extraer_content(resp2)
                    if content:
                        print(f"✅ Respuesta sin json_object ({len(content)} chars)")
                        return content
                except Exception as e2:
                    print(f"❌ Reintento sin json_object: {e2}")
                    raise
            else:
                print(f"❌ Error Groq no recuperable: {e}")
                raise

    raise RuntimeError("Groq no disponible tras 4 intentos")

def limpiar_json(texto: str) -> str:
    if not isinstance(texto, str):
        texto = json.dumps(texto, ensure_ascii=False)
    texto = texto.strip()
    if "```json" in texto:
        texto = texto.split("```json")[17].split("```")[0].strip()
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
        print(f"❌ Import error critico: {e}")
        return False, "", ""

    validar_idea_fn    = None
    generar_landing_fn = None
    try:
        from agents.market_validator  import validar_idea    as validar_idea_fn
        from agents.landing_generator import generar_landing as generar_landing_fn
    except ImportError as e:
        print(f"⚠️ Modulos opcionales no cargados: {e}")

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
            "ideas_previas": "", "mejores_verticales": "", "tags_exitosos": "",
            "ia_tools_top": "", "total_analizadas": 0, "tasa_exito": "N/A",
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
            print(f"❌ JSON invalido: {e} | Raw (200c): {str(respuesta)[:200]}")
            return False, "", ""

        try:
            dup, dup_nombre = es_duplicado(idea_candidata, umbral=umbral_dup)
            if dup:
                print(f"⚠️ Duplicado: '{idea_candidata.get('nombre','?')}' ~ '{dup_nombre}' — regenerando...")
                contexto["ideas_previas"] += f"\n- {idea_candidata.get('nombre','?')} (DESCARTADA, similar a {dup_nombre})"
                continue
        except Exception as e:
            print(f"⚠️ Anti-dup: {e}")

        idea = idea_candidata
        break

    if not idea:
        print("❌ No se genero idea unica en 3 intentos")
        return False, "", ""

    nombre = idea.get("nombre", "SinNombre")
    print(f"💡 Idea aprobada: {nombre}")

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
            print(f"   ✅ Score ajustado con datos reales: {scores['score_total']}")
        except Exception as e:
            print(f"   ⚠️ Validacion real omitida: {e}")

    score = scores["score_total"]
    print(
        f"📊 Score FINAL: {score}/100 | "
        f"C:{scores.get('critico',0)} V:{scores.get('viral',0)} "
        f"G:{scores.get('generador',0)} M:{scores.get('monetizacion',0)} "
        f"E:{scores.get('ejecutabilidad',0)} T:{scores.get('timing',0)}"
    )

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
            landing     = generar_landing_fn(idea)
            landing_url = landing.get("url_publica", "")
            if landing_url:
                idea["landing_url"] = landing_url
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
