import os
import json
import time
import random
from groq import Groq
from agents.encoding_helper import fix_llm_encoding

def _groq_chat(messages, max_intentos=3):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    model = "llama-3.3-70b-versatile"
    for intento in range(max_intentos):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,
                max_tokens=600,
            )
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                espera = min(4 * (2 ** intento) + random.uniform(0, 2), 30)
                print(f"⏳ Rate limit detectado (intento {intento+1}/{max_intentos})")
                print(f"⏰ Esperando {espera:.1f}s (backoff)...")
                time.sleep(espera)
                if intento >= 1:
                    model = "llama-3.1-8b-instant"
                    print("🔄 Cambiando a modelo ligero: llama-3.1-8b-instant")
            else:
                raise
    return None

def critique(idea):
    nombre      = idea.get("nombre", "")
    problema    = idea.get("problema", "")
    solucion    = idea.get("solucion", "")
    tipo        = idea.get("tipo", "")
    vertical    = idea.get("vertical", "")
    monetizacion = idea.get("monetizacion", idea.get("modelo_negocio", ""))
    propuesta   = idea.get("propuesta_valor", "")

    prompt = f"""Eres un inversor experto y crítico ESTRICTO de startups. Evalúa esta idea con RIGOR MÁXIMO.

IDEA: {nombre}
PROBLEMA: {problema}
SOLUCIÓN: {solucion}
TIPO: {tipo}
MERCADO: {vertical}
MONETIZACIÓN: {monetizacion}
PROPUESTA VALOR: {propuesta}

CRITERIOS DE EVALUACIÓN ESTRICTOS:

score_critico (0-100): Viabilidad real
- ¿El problema es REAL y frecuente?
- ¿La solución es 10x mejor que alternativas?
- ¿El mercado tiene dinero suficiente?
- Sé ESTRICTO: la mayoría de ideas merecen 60-75

viral_score (0-100): Difusión orgánica
- ¿La gente lo compartirá espontáneamente?
- ¿Se explica en 5 segundos?
- La mayoría de SaaS tienen viral bajo (40-55)

score_generador (0-100): Ejecutabilidad técnica
- ¿Se puede construir en 30 días con menos de 500€?
- ¿El stack es moderno?

score_money (0-100): Potencial de ingresos REALES
- ¿Cuánto puede ganar al año 1 realistamente?
- ¿Hay competencia que valide el mercado?
- Sé REALISTA: la mayoría tardan en monetizar

IMPORTANTE: Da scores VARIADOS y REALISTAS, no siempre 80. 
Si algo es mediocre, pon 55. Si es excepcional, pon 90.

Responde SOLO JSON válido sin markdown:
{{
  "score_critico": <numero 0-100>,
  "viral_score": <numero 0-100>,
  "score_generador": <numero 0-100>,
  "score_money": <numero 0-100>,
  "puntos_fuertes": ["fortaleza concreta 1", "fortaleza concreta 2", "fortaleza concreta 3"],
  "puntos_debiles": ["debilidad concreta 1", "debilidad concreta 2"],
  "resumen": "Evaluación ejecutiva en 2 frases MUY concretas sobre ESTA idea específica"
}}"""

    try:
        response = _groq_chat([{"role": "user", "content": prompt}])
        if not response:
            raise Exception("Sin respuesta de Groq")

        content = response.choices[0].message.content.strip()
        content = fix_llm_encoding(content)

        if "```" in content:
            parts = content.split("```")
            for part in parts:
                if "{" in part:
                    content = part.replace("json", "").strip()
                    break

        inicio = content.find("{")
        fin = content.rfind("}") + 1
        if inicio >= 0 and fin > inicio:
            content = content[inicio:fin]

        result = json.loads(content)

        result.setdefault("score_critico", 68)
        result.setdefault("viral_score", 50)
        result.setdefault("score_generador", 70)
        result.setdefault("score_money", 58)
        result.setdefault("puntos_fuertes", ["Problema identificado"])
        result.setdefault("puntos_debiles", ["Validar demanda real"])
        result.setdefault("resumen", "Idea con potencial. Requiere validación.")

        sc = result["score_critico"]
        sv = result["viral_score"]
        sg = result["score_generador"]
        sm = result["score_money"]
        print(f"📊 Score Critico: {sc} | Viral: {sv} | Generador: {sg} | Money: {sm}")
        return result

    except Exception as e:
        print(f"❌ Error final en critique: {e}")
        return {
            "score_critico": 65,
            "viral_score": 48,
            "score_generador": 68,
            "score_money": 55,
            "puntos_fuertes": ["Problema real identificado", "Mercado existente"],
            "puntos_debiles": ["Necesita validación de demanda", "Analizar competencia"],
            "resumen": "Idea con potencial moderado. Requiere validación antes de construir."
        }
# FIN COMPLETO critic_agent.py
