import os
import json
from groq import Groq

def research(idea):
    """Investiga y enriquece la idea con datos adicionales"""
    
    print(f"\n🔍 Investigando: {idea['nombre']}")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt = f"""Analiza esta idea de producto y genera investigación de mercado:

IDEA: {idea['nombre']}
PROBLEMA: {idea['problema']}
SOLUCIÓN: {idea['solucion']}
PRECIO: €{idea['precio_sugerido']}

Genera investigación concisa en JSON:
{{
  "competidores": ["Competidor 1", "Competidor 2", "Competidor 3"],
  "diferenciacion_clave": "Por qué esta idea es única",
  "riesgos_principales": ["Riesgo 1", "Riesgo 2"],
  "oportunidades": ["Oportunidad 1", "Oportunidad 2"],
  "validacion_sugerida": "Cómo validar rápidamente"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres investigador de mercado experto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        
        # Limpiar markdown
        if '```json' in content:
            content = content.split('```json').split('```').strip()[1]
        elif '```' in content:
            content = content.split('```').split('```')[0].strip()
        
        research_data = json.loads(content)
        
        print(f"✅ Investigación completada")
        return research_data
    
    except Exception as e:
        print(f"⚠️  Error en investigación: {e}")
        return {
            "competidores": ["N/A"],
            "diferenciacion_clave": "Pendiente de investigar",
            "riesgos_principales": ["Pendiente de investigar"],
            "oportunidades": ["Pendiente de investigar"],
            "validacion_sugerida": "Pendiente de investigar"
        }

if __name__ == "__main__":
    # Test
    test_idea = {
        "nombre": "Test Product",
        "problema": "Test problem",
        "solucion": "Test solution",
        "precio_sugerido": "29"
    }
    result = research(test_idea)
    print(json.dumps(result, indent=2))
import os
import json
from groq import Groq

def research(idea):
    """Investiga y enriquece la idea con datos adicionales"""
    
    print(f"\n🔍 Investigando: {idea['nombre']}")
    
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    
    prompt = f"""Analiza esta idea de producto y genera investigación de mercado:

IDEA: {idea['nombre']}
PROBLEMA: {idea['problema']}
SOLUCIÓN: {idea['solucion']}
PRECIO: €{idea['precio_sugerido']}

Genera investigación concisa en JSON:
{{
  "competidores": ["Competidor 1", "Competidor 2", "Competidor 3"],
  "diferenciacion_clave": "Por qué esta idea es única",
  "riesgos_principales": ["Riesgo 1", "Riesgo 2"],
  "oportunidades": ["Oportunidad 1", "Oportunidad 2"],
  "validacion_sugerida": "Cómo validar rápidamente"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Eres investigador de mercado experto."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        
        # Limpiar markdown
        if '```json' in content:
            content = content.split('```json').split('```').strip()[1]
        elif '```' in content:
            content = content.split('```').split('```')[0].strip()
        
        research_data = json.loads(content)
        
        print(f"✅ Investigación completada")
        return research_data
    
    except Exception as e:
        print(f"⚠️  Error en investigación: {e}")
        return {
            "competidores": ["N/A"],
            "diferenciacion_clave": "Pendiente de investigar",
            "riesgos_principales": ["Pendiente de investigar"],
            "oportunidades": ["Pendiente de investigar"],
            "validacion_sugerida": "Pendiente de investigar"
        }

if __name__ == "__main__":
    # Test
    test_idea = {
        "nombre": "Test Product",
        "problema": "Test problem",
        "solucion": "Test solution",
        "precio_sugerido": "29"
    }
    result = research(test_idea)
    print(json.dumps(result, indent=2))
