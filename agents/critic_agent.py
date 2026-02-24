import os
import json
from groq import Groq
from agents.encoding_helper import fix_llm_encoding


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
- <50: Idea debil, problema no real o mercado saturado
- 50-70: Idea basica con mejoras necesarias
- 70-85: Buena idea con mercado claro
- 85+: Idea excepcional con ventaja competitiva clara

viral_score (0-100): Potencial de difusion organica
- La gente lo compartira? Tiene efecto WOW?
- Es facil de explicar en una frase?
- Resuelve un dolor que muchos sienten?

score_generador (0-100): Calidad tecnica y ejecutabilidad
- Se puede construir con recursos limitados?
- El stack es moderno y mantenible?
- El MVP es alcanzable en el tiempo estimado?

score_money (0-100): Potencial real de generar ingresos
- Tiene modelo de negocio claro con precio definido?
- La competencia es manejable o el nicho esta sin explotar?
- El tiempo de payback es corto (menos de 6 meses)?
- Permite ingresos recurrentes (suscripcion, SaaS, marketplace)?
- <50: Monetizacion vaga o mercado con poco dinero
- 50-70: Ingresos posibles pero lentos o inciertos
- 70-85: Modelo claro con recurrencia razonable
- 85+: Ingresos rapidos, recurrentes y escalables

Da fortalezas y debilidades ESPECIFICAS (no genericas).

Responde SOLO JSON valido sin markdown:
{{
  "score_critico": <numero 0-100>,
  "viral_score": <numero 0-100>,
  "score_generador": <numero 0-100>,
  "score_money": <numero 0-100>,
  "puntos_fuertes": ["fortaleza especifica 1", "fortaleza especifica 2", "fortaleza especifica 3"],
  "puntos_debiles": ["debilidad especifica 1", "debilidad especifica 2"],
  "resumen": "Evaluacion ejecutiva en 2 frases concretas"
}}"""

    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    for attempt in range(3):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=600,
            )
            content = response.choices[0].message.content.strip()
            content = fix_llm_encoding(content)

            # Limpiar markdown si existe
            if "```json" in content:
                content = content.split("```json").split("```").strip()[1]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Extraer solo el bloque JSON
            inicio = content.find("{")
            fin = content.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                content = content[inicio:fin]

            result = json.loads(content)

            # Asegurar que existen todos los campos
            result.setdefault("score_critico",   70)
            result.setdefault("viral_score",      55)
            result.setdefault("score_generador",  70)
            result.setdefault("score_money",      60)
            result.setdefault("puntos_fuertes",  ["Problema identificado", "Solucion viable"])
            result.setdefault("puntos_debiles",  ["Validar demanda real"])
            result.setdefault("resumen",         "Idea con potencial. Requiere validacion.")

            sc = result["score_critico"]
            sv = result["viral_score"]
            sg = result["score_generador"]
            sm = result["score_money"]
            print(f"📊 Score Critico: {sc} | Viral: {sv} | Generador: {sg} | Money: {sm}")
            return result

        except Exception as e:
            print(f"⚠️  Critico intento {attempt + 1}: {e}")

    # Fallback conservador
    return {
        "score_critico":  68,
        "viral_score":    55,
        "score_generador": 70,
        "score_money":    60,
        "puntos_fuertes": ["Problema real identificado", "Mercado existente"],
        "puntos_debiles": ["Necesita validacion de demanda", "Analizar competencia"],
        "resumen": "Idea viable con potencial moderado. Requiere validacion antes de construir."
    }
