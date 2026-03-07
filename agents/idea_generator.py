PROMPT_IDEA_COMPLETA = """
Eres un analista de startups de clase mundial. Genera UNA idea de startup en JSON.
Contexto del mercado actual: {tendencias}
Ideas ya analizadas (NO repetir): {ideas_previas}
Verticales con mejor rendimiento histórico: {mejores_verticales}

Responde SOLO con este JSON (sin texto extra):
{{
  "nombre": "NombreProducto",
  "tagline": "Frase de valor en <10 palabras",
  "problema": "Problema concreto que resuelve (2-3 frases)",
  "solucion": "Cómo lo resuelve de forma única (2-3 frases)",
  "cliente_objetivo": "Perfil exacto del cliente ideal",
  "propuesta_valor_unica": "Por qué es mejor que alternativas existentes",
  
  "mercado": {{
    "TAM": "Total Addressable Market en $ (con fuente estimada)",
    "SAM": "Serviceable Addressable Market en $",
    "SOM": "Serviceable Obtainable Market año 1 en $",
    "competidores": ["Comp1", "Comp2", "Comp3"],
    "ventaja_competitiva": "Moat real y defensible"
  }},
  
  "modelo_negocio": {{
    "tipo": "SaaS/Marketplace/B2B/B2C/etc",
    "pricing": "Precio concreto con justificación",
    "canales_adquisicion": ["Canal1", "Canal2"],
    "time_to_revenue": "X semanas desde lanzamiento MVP"
  }},
  
  "estudio_economico": {{
    "conservador": {{
      "mes6":  {{"mrr": 0, "usuarios": 0, "cac": 0, "ltv": 0}},
      "mes12": {{"mrr": 0, "usuarios": 0, "margen": "0%"}},
      "mes24": {{"mrr": 0, "arr": 0, "breakeven": "mes X"}},
      "supuestos": "Explica los supuestos del escenario"
    }},
    "realista": {{
      "mes6":  {{"mrr": 0, "usuarios": 0, "cac": 0, "ltv": 0}},
      "mes12": {{"mrr": 0, "usuarios": 0, "margen": "0%"}},
      "mes24": {{"mrr": 0, "arr": 0, "breakeven": "mes X"}},
      "supuestos": "Explica los supuestos del escenario"
    }},
    "optimista": {{
      "mes6":  {{"mrr": 0, "usuarios": 0, "cac": 0, "ltv": 0}},
      "mes12": {{"mrr": 0, "usuarios": 0, "margen": "0%"}},
      "mes24": {{"mrr": 0, "arr": 0, "breakeven": "mes X"}},
      "supuestos": "Explica los supuestos del escenario"
    }}
  }},
  
  "dafo": {{
    "debilidades": ["D1", "D2", "D3"],
    "amenazas":    ["A1", "A2", "A3"],
    "fortalezas":  ["F1", "F2", "F3"],
    "oportunidades": ["O1", "O2", "O3"]
  }},
  
  "mvp": {{
    "features_minimas": ["Feature 1", "Feature 2", "Feature 3"],
    "stack_recomendado": "Tecnologías exactas para este caso",
    "tiempo_estimado": "X semanas con 1 dev",
    "coste_estimado": "$ con recursos mínimos"
  }},
  
  "prompt_mvp_json": {{
    "ia_recomendada": "Claude 3.5 Sonnet / GPT-4o / Cursor — por qué",
    "prompt": "Prompt completo y detallado para que una IA construya el MVP desde cero. Incluir stack, arquitectura, features, flujo de usuario, base de datos, y pasos de implementación. Mínimo 300 palabras."
  }},
  
  "estrategia_monetizacion_rapida": {{
    "semana1": "Acción concreta para conseguir primeros usuarios",
    "semana4": "Primera venta o revenue concreto",
    "mes3":    "Estrategia de escala inicial",
    "canales_growth": ["Canal1 con táctica específica", "Canal2"],
    "precio_optimo": "Justificación del precio basada en valor entregado"
  }},
  
  "opinion_profesional": "Tu análisis honesto de 3-4 frases: qué hace especial esta idea, riesgos reales, y por qué AHORA es el momento (o no)",
  
  "scores": {{
    "critico":        <0-100 — ¿resuelve un dolor real urgente?>,
    "viral":          <0-100 — ¿tiene potencial de growth orgánico?>,
    "generador":      <0-100 — ¿puede generar revenue rápido?>,
    "monetizacion":   <0-100 — ¿modelo de negocio sólido y escalable?>,
    "ejecutabilidad": <0-100 — ¿puede un solo dev lanzarlo en <3 meses?>,
    "timing":         <0-100 — ¿es el momento adecuado del mercado?>,
    "score_total":    <promedio_ponderado>
  }},
  
  "vertical": "FinTech|HealthTech|EdTech|SaaS|Marketplace|etc",
  "tipo": "B2B|B2C|B2B2C",
  "tags": ["tag1", "tag2", "tag3"]
}}
"""
