"""
Competition Agent: analiza competencia en Product Hunt, Crunchbase, etc.
"""
import os
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_competition(idea):
    """Analiza competencia para una idea"""
    
    print("🔍 Analizando competencia...")
    
    prompt = f"""Analiza la competencia para esta idea:

IDEA: {idea.get('nombre')}
DESCRIPCIÓN: {idea.get('descripcion')}
PROBLEMA: {idea.get('problema')}
SOLUCIÓN: {idea.get('solucion')}

Genera un análisis en JSON:
{{
  "competidores_directos": [
    {{"nombre": "Competidor A", "descripcion": "...", "diferenciador": "lo que ellos tienen"}}
  ],
  "competidores_indirectos": ["Nombre 1", "Nombre 2"],
  "ventaja_competitiva": "Por qué esta idea es mejor",
  "riesgo_competitivo": "Bajo/Medio/Alto",
  "barreras_entrada": "Principales barreras para competir",
  "nicho_recomendado": "Segmento específico donde ganar primero"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=1000
        )
        
        import json
        analysis = json.loads(response.choices[0].message.content)
        
        print(f"✅ Encontrados {len(analysis.get('competidores_directos', []))} competidores")
        
        return analysis
        
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None