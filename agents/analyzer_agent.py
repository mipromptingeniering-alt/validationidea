import os
import time
import requests
from groq import Groq
from agents.encoding_helper import fix_llm_encoding


def generate_complete_report(idea):
    """Genera informe completo de 15 secciones (~2500 palabras)"""

    context = f"""
NOMBRE: {idea.get('nombre', 'N/A')}
PROBLEMA: {idea.get('problema', 'N/A')}
SOLUCION: {idea.get('solucion', 'N/A')}
DESCRIPCION: {idea.get('descripcion', 'N/A')}
PROPUESTA DE VALOR: {idea.get('propuesta_valor', idea.get('Value', 'N/A'))}
TIPO: {idea.get('tipo', 'N/A')}
MERCADO OBJETIVO: {idea.get('vertical', idea.get('Target', 'N/A'))}
PRECIO: {idea.get('precio', 'N/A')} euros
MONETIZACION: {idea.get('monetizacion', idea.get('Business', 'N/A'))}
STACK TECNOLOGICO: {idea.get('tool', 'N/A')}
ESFUERZO MVP: {idea.get('esfuerzo', 'N/A')} horas
REVENUE ESTIMADO 6 MESES: {idea.get('revenue_6m', 'N/A')} euros
ESTRATEGIA LANZAMIENTO: {idea.get('como', idea.get('Marketing', 'N/A'))}
SCORE CRITICO: {idea.get('score_critico', 'N/A')}/100
SCORE VIRAL: {idea.get('viral_score', 'N/A')}/100
SCORE GENERADOR: {idea.get('score_generador', 'N/A')}/100
FORTALEZAS: {', '.join(idea.get('fortalezas', idea.get('puntos_fuertes', [])))}
DEBILIDADES: {', '.join(idea.get('debilidades', idea.get('puntos_debiles', [])))}
"""

    prompt = f"""Eres un analista de negocios experto con 15 anos de experiencia en startups digitales. 
Genera un informe COMPLETO y DETALLADO en espanol sobre esta idea de negocio.
{context}
Genera EXACTAMENTE estos 15 apartados. Cada uno con minimo 150 palabras, datos concretos y ejemplos reales:

## 1. IDEA Y PROPUESTA DE VALOR
[Que hace unico este producto, diferenciacion vs competencia, por que ahora]

## 2. ANALISIS DE MERCADO
[TAM/SAM/SOM con numeros reales en euros, tendencias 2025-2026, tasa de crecimiento]

## 3. CLIENTE IDEAL (BUYER PERSONA)
[Perfil detallado: edad, profesion, ingresos, problemas diarios, donde los encuentras online]

## 4. ANALISIS DE LA COMPETENCIA
[3-5 competidores reales con sus precios, puntos debiles y como diferenciarte]

## 5. MODELO DE NEGOCIO
[Flujo de ingresos detallado, pricing por tier, costes fijos/variables, margen bruto estimado]

## 6. VALIDACION DEL NEGOCIO
[Como validar en 2 semanas: landing page, encuestas, MVP minimo, metricas de validacion]

## 7. PLAN FINANCIERO
[Proyeccion mes 1-12: costes iniciales, punto de equilibrio, ingresos esperados con numeros]

## 8. ESTRATEGIA DE MARKETING DIGITAL
[Canales prioritarios, contenido SEO, ads, email, estrategia de lanzamiento semana a semana]

## 9. TECNOLOGIA Y HERRAMIENTAS
[Stack completo con herramientas especificas, no-code vs codigo, tiempo real de desarrollo]

## 10. METRICAS Y KPIs
[8 KPIs criticos con objetivos concretos para dia 30, dia 60, dia 90]

## 11. ASPECTOS LEGALES Y FISCALES
[Forma juridica en Espana, IVA, LOPD/RGPD, terminos de servicio, registro necesario]

## 12. OPERACIONES Y GESTION
[Flujo operativo diario, tareas automatizables, herramientas de gestion, tiempo dedicacion]

## 13. MARCA Y CONFIANZA
[Nombre, identidad, estrategia de contenido para construir autoridad en 90 dias]

## 14. RIESGOS Y PLAN B
[Top 5 riesgos con probabilidad e impacto, estrategias de mitigacion, alternativas]

## 15. HOJA DE RUTA: PRIMEROS 90 DIAS
[Semana 1-2: validacion. Semana 3-4: MVP. Mes 2: primeros clientes. Mes 3: escalar]

IMPORTANTE: Minimo 2500 palabras. Se especifico con datos reales. Sin frases genericas."""

    # Intentar con Groq primero
    groq_key = os.environ.get("GROQ_API_KEY")
    if groq_key:
        for attempt in range(3):
            try:
                print(f"🔄 Generando informe Groq (intento {attempt + 1}/3)...")
                client = Groq(api_key=groq_key)
                response = client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=4000,
                )
                text = response.choices[0].message.content.strip()
                text = fix_llm_encoding(text)
                if len(text) > 500:
                    print(f"✅ Informe Groq: {len(text)} caracteres")
                    return text
            except Exception as e:
                err = str(e)
                if "rate_limit" in err or "429" in err or "quota" in err.lower():
                    wait = 45 * (attempt + 1)
                    print(f"⏳ Rate limit Groq. Esperando {wait}s...")
                    time.sleep(wait)
                else:
                    print(f"⚠️  Error Groq intento {attempt + 1}: {e}")
                    time.sleep(5)

    # Fallback: Gemini
    gemini_key = os.environ.get("GEMINI_API_KEY")
    if gemini_key:
        for attempt in range(3):
            try:
                print(f"🔄 Fallback Gemini (intento {attempt + 1}/3)...")
                url = (
                    f"https://generativelanguage.googleapis.com/v1beta/models/"
                    f"gemini-2.0-flash:generateContent?key={gemini_key}"
                )
                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"maxOutputTokens": 4000, "temperature": 0.7},
                }
                resp = requests.post(url, json=payload, timeout=90)
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"]
                text = fix_llm_encoding(text)
                if len(text) > 500:
                    print(f"✅ Informe Gemini: {len(text)} caracteres")
                    return text
            except Exception as e:
                wait = 30 * (attempt + 1)
                print(f"⚠️  Gemini intento {attempt + 1}: {e}. Esperando {wait}s...")
                time.sleep(wait)

    print("❌ No se pudo generar el informe")
    return None
