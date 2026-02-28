import os
import json
import time
import random
from groq import Groq
from agents.encoding_helper import fix_llm_encoding

def _groq_chat_robusto(client, model_primary, model_fallback, messages, max_intentos=3):
    """Llamada robusta a Groq: respeta retry-after + fallback automático"""
    model = model_primary
    
    for intento in range(max_intentos):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
            return response
        
        except Exception as e:
            error_msg = str(e).lower()
            es_rate_limit = "429" in error_msg or "rate limit" in error_msg
            
            if not es_rate_limit:
                raise
            
            print(f"⏳ Rate limit detectado (intento {intento+1}/{max_intentos})")
            
            # Buscar tiempo de espera en el error
            retry_after = None
            if "try again in" in error_msg:
                # Extrae minutos/segundos del mensaje de Groq
                parts = error_msg.split("try again in")
                if len(parts) > 1:
                    time_part = parts[1].split(".")[0]  # "6m47.808s" → "6m47"
                    if "m" in time_part and "s" in time_part:
                        mins = int(time_part.split("m")[0])
                        secs = int(time_part.split("s")[0].split("m")[-1])
                        retry_after = mins * 60 + secs
            
            if retry_after:
                print(f"⏰ Esperando {retry_after}s (según Groq)...")
                time.sleep(retry_after)
            else:
                # Backoff exponencial + jitter
                espera = min(2 ** intento * 2 + random.uniform(0, 2), 30)
                print(f"⏰ Esperando {espera:.1f}s (backoff)...")
                time.sleep(espera)
            
            # Cambiar a modelo ligero en intento 2+
            if intento >= 1 and model_fallback:
                model = model_fallback
                print(f"🔄 Cambiando a modelo ligero: {model_fallback}")
    
    raise Exception("Todos los reintentos fallaron")

def critique(idea):
    """Evalúa la idea con scoring completo: critico, viral, generador y money (P5)"""
    nombre      = idea.get("nombre", "")
    problema    = idea.get("problema", "")
    solucion    = idea.get("solucion", "")
    tipo        = idea.get("tipo", "")
    vertical    = idea.get("vertical", "")
    monetizacion = idea.get("monetizacion", idea.get("modelo_negocio", ""))

    prompt = f"""Eres un critico de negocios experto y estricto. Evalua esta idea de negocio digital.

IDEA: {nombre}
PROBLEMA: {problema}
SOLUCION: {solucion}
TIPO: {tipo}
MERCADO: {vertical}
MONETIZACION: {monetizacion}

Evalua con CRITERIOS ESTRICTOS y devuelve 4 scores:

score_critico (0-100): Viabilidad real del negocio
score_generador (0-100): Calidad tecnica y ejecutabilidad  
viral_score (0-100): Potencial de difusion organica
score_money (0-100): Potencial real de generar ingresos

Da fortalezas y debilidades ESPECIFICAS.

Responde SOLO JSON valido sin markdown:
{{
  "score_critico": <numero 0-100>,
  "viral_score": <numero 0-100>,
  "score_generador": <numero 0-100>,
  "score_money": <numero 0-100>,
  "puntos_fuertes": ["fortaleza 1", "fortaleza 2"],
  "puntos_debiles": ["debilidad 1"],
  "resumen": "2 frases concretas"
}}"""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    try:
        # Modelo grande → fallback automático a ligero
        response = _groq_chat_robusto(
            client=client,
            model_primary="llama-3.3-70b-versatile",
            model_fallback="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}]
        )
        
        content = response.choices[0].message.content.strip()
        content = fix_llm_encoding(content)

        # Limpiar markdown si existe
        if "```json" in content:
            parts = content.split("```json")
            if len(parts) > 1:
                content = parts[1].split("```").strip()
        
        # Extraer JSON
        inicio = content.find("{")
        fin = content.rfind("}") + 1
        if inicio >= 0 and fin > inicio:
            content = content[inicio:fin]
        
        result = json.loads(content)

        # Validar campos obligatorios
        result.setdefault("score_critico", 70)
        result.setdefault("viral_score", 55)
        result.setdefault("score_generador", 70)
        result.setdefault("score_money", 60)
        result.setdefault("puntos_fuertes", ["Default fuerte"])
        result.setdefault("puntos_debiles", ["Default débil"])
        result.setdefault("resumen", "Idea evaluada.")

        sc = result["score_critico"]
        sv = result["viral_score"]
        sg = result["score_generador"]
        sm = result["score_money"]
        print(f"📊 Score Critico: {sc} | Viral: {sv} | Generador: {sg} | Money: {sm}")
        return result

    except Exception as e:
        print(f"❌ Error final en critique: {e}")
        # Fallback conservador
        return {
            "score_critico": 68,
            "viral_score": 55,
            "score_generador": 70,
            "score_money": 60,
            "puntos_fuertes": ["Problema real", "Mercado existente"],
            "puntos_debiles": ["Validar demanda", "Competencia"],
            "resumen": "Idea viable. Requiere validación."
        }
