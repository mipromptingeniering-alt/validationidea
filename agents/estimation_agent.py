"""
Estimation Agent: estimaciones robustas
"""
import os
import json
import re
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def estimate_project(idea):
    """Estima costos y tiempos con parsing robusto"""
    
    print("💰 Estimando inversión y tiempo...")
    
    prompt = f"""Estima inversión y tiempo de desarrollo para esta idea.

IDEA: {idea.get('nombre')}
MVP: {idea.get('mvp')}
MODELO: {idea.get('modelo_negocio')}

Responde SOLO con un objeto JSON válido (sin markdown, sin ```json):
{{
  "inversion_mvp_usd": 5000,
  "tiempo_desarrollo_semanas": 8,
  "equipo_necesario": ["1 Full-stack Dev", "1 Designer"],
  "costos_mensuales_operacion": 500,
  "tiempo_breakeven_meses": 12,
  "viabilidad_tecnica": "Alta",
  "complejidad": "Media"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=800
        )
        
        content = response.choices[0].message.content.strip()
        
        # Limpiar markdown
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()
        
        estimation = json.loads(content)
        
        print(f"✅ Inversión: ${estimation.get('inversion_mvp_usd', 0):,}")
        
        return estimation
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Error JSON: {e}")
        return {
            "inversion_mvp_usd": 10000,
            "tiempo_desarrollo_semanas": 12,
            "equipo_necesario": ["1 Developer"],
            "costos_mensuales_operacion": 1000,
            "tiempo_breakeven_meses": 18,
            "viabilidad_tecnica": "Media",
            "complejidad": "Media"
        }
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None