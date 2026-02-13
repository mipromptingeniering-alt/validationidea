import os
import json
from groq import Groq

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

def critique(idea):
    """
    Crítica detallada con puntos débiles específicos para feedback
    """
    print("🎯 Agente Crítico iniciado...")
    
    nombre = idea.get('nombre', '')
    descripcion = idea.get('descripcion', '')
    problema = idea.get('problema', '')
    solucion = idea.get('solucion', '')
    publico = idea.get('publico_objetivo', '')
    tam = idea.get('tam', '')
    diferenciacion = idea.get('diferenciacion', '')
    competencia = idea.get('competencia', [])
    precio = idea.get('precio_sugerido', '')
    
    prompt = f"""Eres un crítico IMPLACABLE de ideas SaaS. Tu trabajo es encontrar TODOS los problemas.

IDEA A EVALUAR:
Nombre: {nombre}
Descripción: {descripcion}
Problema: {problema}
Solución: {solucion}
Público: {publico}
TAM: {tam}
Diferenciación: {diferenciacion}
Competencia: {', '.join(competencia)}
Precio: {precio}

EVALÚA CON CRITERIO ESTRICTO (escala 0-100):

CRITERIOS (cada uno 0-20 puntos):
1. MERCADO: ¿Es suficientemente grande? ¿Está en crecimiento?
2. PROBLEMA: ¿Es real y urgente? ¿Tiene datos/evidencia?
3. SOLUCIÓN: ¿Es única? ¿Factible técnicamente?
4. DIFERENCIACIÓN: ¿Qué hace que sea 10x mejor que alternativas?
5. VIABILIDAD: ¿Se puede construir en 4-6 semanas? ¿Monetizable?

SÉ BRUTAL. Si algo es mediocre, penaliza fuerte.

RESPONDE EN JSON EXACTO (sin markdown):
{{
  "score_critico": 75,
  "puntos_fuertes": ["Punto fuerte 1", "Punto fuerte 2"],
  "puntos_debiles": ["Problema específico 1", "Problema específico 2", "Problema 3"],
  "recomendaciones": ["Mejora concreta 1", "Mejora 2", "Mejora 3"],
  "score_mercado": 18,
  "score_problema": 16,
  "score_solucion": 14,
  "score_diferenciacion": 12,
  "score_viabilidad": 15,
  "veredicto": "Explicación de 2-3 frases del veredicto final"
}}"""

    try:
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "Eres un crítico experto en startups SaaS. Eres IMPLACABLE pero justo. Respondes SOLO con JSON válido."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.3,
            max_tokens=1500
        )
        
        response_text = chat_completion.choices[0].message.content.strip()
        
        if response_text.startswith('```'):
            response_text = response_text.split('```')[1]
            if response_text.startswith('json'):
                response_text = response_text[4:]
            response_text = response_text.strip()
        
        critique_data = json.loads(response_text)
        
        # Validación adicional basada en reglas
        puntos_debiles_extra = []
        penalizacion = 0
        
        # Regla 1: Categorías saturadas
        categorias_ban = ['documentacion', 'dashboard', 'analytics', 'gestor']
        for cat in categorias_ban:
            if cat in nombre.lower() or cat in descripcion.lower():
                puntos_debiles_extra.append(f"Categoría saturada: '{cat}'")
                penalizacion += 15
        
        # Regla 2: Mercado muy pequeño
        if tam and tam != 'N/A':
            valor = int(''.join(filter(str.isdigit, tam)))
            if valor < 10:
                puntos_debiles_extra.append(f"Mercado muy pequeño: {tam}")
                penalizacion += 20
        
        # Regla 3: Diferenciación débil
        if not diferenciacion or len(diferenciacion) < 30:
            puntos_debiles_extra.append("Diferenciación poco clara o genérica")
            penalizacion += 10
        
        # Regla 4: Precio irrealista
        if precio and precio != 'N/A':
            precio_num = int(''.join(filter(str.isdigit, precio)))
            if precio_num < 10:
                puntos_debiles_extra.append(f"Precio demasiado bajo: {precio}")
                penalizacion += 5
            elif precio_num > 200:
                puntos_debiles_extra.append(f"Precio demasiado alto para validación: {precio}")
                penalizacion += 5
        
        # Aplicar penalizaciones
        if puntos_debiles_extra:
            critique_data['puntos_debiles'].extend(puntos_debiles_extra)
            critique_data['score_critico'] = max(0, critique_data['score_critico'] - penalizacion)
        
        score = critique_data.get('score_critico', 0)
        print(f"✅ Crítica completada - Score: {score}")
        
        if puntos_debiles_extra:
            print(f"⚠️  Penalizaciones aplicadas: -{penalizacion} puntos")
        
        return critique_data
    
    except Exception as e:
        print(f"❌ Error en crítica: {e}")
        return {
            "score_critico": 0,
            "puntos_fuertes": [],
            "puntos_debiles": ["Error en evaluación"],
            "recomendaciones": [],
            "veredicto": "Error al evaluar"
        }

def decide_publish(idea, critique, config):
    """
    Decisión de publicación más estricta
    """
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0)
    
    umbral_min = config.get('umbral_minimo', 70)
    umbral_crit = config.get('umbral_critico', 50)
    
    # Ambos deben superar umbrales
    if score_gen >= umbral_min and score_crit >= umbral_crit:
        print(f"✅ PUBLICAR - Gen:{score_gen} Crit:{score_crit}")
        return True
    else:
        print(f"❌ RECHAZAR - Gen:{score_gen} Crit:{score_crit}")
        return False

if __name__ == "__main__":
    test_idea = {
        'nombre': 'TestMaster Pro',
        'descripcion': 'Testing automático con IA',
        'problema': 'Devs pierden 15h/semana en tests manuales',
        'solucion': 'IA genera tests automáticos en tiempo real',
        'publico_objetivo': 'Equipos desarrollo',
        'tam': '150M€',
        'diferenciacion': 'Generación automática vs manual',
        'competencia': ['Jest', 'Cypress'],
        'precio_sugerido': '49€/mes'
    }
    
    print("🧪 Probando crítico...")
    critique_result = critique(test_idea)
    print(json.dumps(critique_result, indent=2, ensure_ascii=False))
