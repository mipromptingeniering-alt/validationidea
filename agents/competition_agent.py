"""
Competition Agent: análisis de competencia robusto
"""
import os
import json
import re
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def analyze_competition(idea):
    """Analiza competencia con parsing robusto"""
    
    print("🔍 Analizando competencia...")
    
    prompt = f"""Analiza la competencia para esta idea de negocio.

IDEA: {idea.get('nombre')}
DESCRIPCIÓN: {idea.get('descripcion')}
PROBLEMA: {idea.get('problema')}
SOLUCIÓN: {idea.get('solucion')}

Responde SOLO con un objeto JSON válido (sin markdown, sin ```json):
{{
  "competidores_directos": [
    {{"nombre": "Ejemplo Inc", "descripcion": "Qué hacen", "diferenciador": "Qué tienen único"}}
  ],
  "competidores_indirectos": ["Nombre 1", "Nombre 2", "Nombre 3"],
  "ventaja_competitiva": "Por qué esta idea es mejor o diferente",
  "riesgo_competitivo": "Bajo",
  "barreras_entrada": "Principales barreras para competir",
  "nicho_recomendado": "Segmento específico donde empezar"
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
            max_tokens=1200
        )
        
        content = response.choices.message.content.strip()
        
        # Limpiar markdown si existe
        content = re.sub(r'^```json\s*', '', content)
        content = re.sub(r'\s*```$', '', content)
        content = content.strip()
        
        analysis = json.loads(content)
        
        print(f"✅ {len(analysis.get('competidores_directos', []))} competidores encontrados")
        
        return analysis
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Error JSON: {e}")
        return {
            "competidores_directos": [],
            "competidores_indirectos": [],
            "ventaja_competitiva": "No analizado",
            "riesgo_competitivo": "Medio",
            "barreras_entrada": "No analizado",
            "nicho_recomendado": "Mercado general"
        }
    except Exception as e:
        print(f"⚠️ Error: {e}")
        return None