import os
import json
from groq import Groq
from agents.encoding_helper import fix_llm_encoding


def critique(idea):
    """Evalúa la idea con scoring completo: critico, viral y generador"""
    nombre = idea.get('nombre', '')
    problema = idea.get('problema', '')
    solucion = idea.get('solucion', '')
    tipo = idea.get('tipo', '')
    vertical = idea.get('vertical', '')
    monetizacion = idea.get('monetizacion', '')

    prompt = f"""Eres un critico de negocios experto y estricto. Evalua esta idea de negocio digital.

IDEA: {nombre}
PROBLEMA: {problema}
SOLUCION: {solucion}
TIPO: {tipo}
MERCADO: {vertical}
MONETIZACION: {monetizacion}

Evalua con CRITERIOS ESTRICTOS y devuelve 3 scores:

score_critico (0-100): Viabilidad real del negocio
- <50: Idea debil, problema no real o mercado saturado
- 50-70: Idea basica con mejoras necesarias
- 70-85: Buena idea con mercado claro
- 85+: Idea excepcional con ventaja competitiva clara

viral_score (0-100): Potencial de difusion organica
- ¿La gente lo compartira? ¿Tiene efecto WOW?
- ¿Es facil de explicar en una frase?
- ¿Resuelve un dolor que muchos sienten?

score_generador (0-100): Calidad tecnica y ejecutabilidad
- ¿Se puede construir con recursos limitados?
- ¿El stack es moderno y mantenible?
- ¿El MVP es alcanzable en el tiempo estimado?

Da fortalezas y debilidades ESPECIFICAS (no genericas).

Responde SOLO JSON valido sin markdown:
{{
  "score_critico": <numero 0-100>,
  "viral_score": <numero 0-100>,
  "score_generador": <numero 0-100>,
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

            if "```json" in content:
                content = content.split("```json").split("```").strip()[1]
            elif "```" in content:
                content = content.split("```")[16].split("```")[0].strip()

            result = json.loads(content)

            # Asegurar que existen todos los campos
            result.setdefault("score_critico", 70)
            result.setdefault("viral_score", 55)
            result.setdefault("score_generador", 70)
            result.setdefault("puntos_fuertes", ["Problema identificado", "Solucion viable"])
            result.setdefault("puntos_debiles", ["Validar demanda real"])
            result.setdefault("resumen", "Idea con potencial. Requiere validacion.")

            sc = result['score_critico']
            sv = result['viral_score']
            sg = result['score_generador']
            print(f"📊 Score Critico: {sc} | Viral: {sv} | Generador: {sg}")
            return result

        except Exception as e:
            print(f"⚠️  Critico intento {attempt + 1}: {e}")

    # Fallback conservador
    return {
        "score_critico": 68,
        "viral_score": 55,
        "score_generador": 70,
        "puntos_fuertes": ["Problema real identificado", "Mercado existente"],
        "puntos_debiles": ["Necesita validacion de demanda", "Analizar competencia"],
        "resumen": "Idea viable con potencial moderado. Requiere validacion antes de construir."
    }
