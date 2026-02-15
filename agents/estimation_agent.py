"""
Estimation Agent: estima inversión y tiempo de desarrollo
"""
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def estimate_project(idea):
    """Estima costos y tiempos"""
    
    print("💰 Estimando inversión y tiempo...")
    
    prompt = f"""Estima inversión y tiempo para esta idea:

IDEA: {idea.get('nombre')}
MVP: {idea.get('mvp')}
MODELO: {idea.get('modelo_negocio')}

Genera estimación realista en JSON:
{{
  "inversion_mvp_usd": 5000,
  "tiempo_desarrollo_semanas": 8,
  "equipo_necesario": ["1 Developer", "1 Designer"],
  "costos_mensuales_operacion": 500,
  "tiempo_breakeven_meses": 12,
  "viabilidad_tecnica": "Alta/Media/Baja",
  "complejidad": "Simple/Media/Compleja"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=800
        )
        
        import json
        estimation = json.loads(response.choices[0].message.content)
        
        print(f"✅ Inversión estimada: ${estimation.get('inversion_mvp_usd', 0)}")
        
        return estimation
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None