import os
import time
import requests
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
GROQ_MODEL = "llama-3.3-70b-versatile"
GEMINI_MODEL = "gemini-2.0-flash"


def _llamar_groq(prompt, max_tokens=4000, temperatura=0.7):
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)
        for intento in range(3):
            try:
                response = client.chat.completions.create(
                    model=GROQ_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=temperatura,
                    max_tokens=max_tokens,
                )
                choices = response.choices
                if choices:
                    return next(iter(choices)).message.content
            except Exception as e:
                msg = str(e).lower()
                if "rate_limit" in msg or "429" in msg or "daily" in msg:
                    espera = 30 * (intento + 1)
                    print(f"⚠️  Groq rate limit. Esperando {espera}s...")
                    time.sleep(espera)
                else:
                    print(f"❌ Groq error: {e}")
                    break
    except Exception as e:
        print(f"❌ Groq init error: {e}")
    return None


def _llamar_gemini(prompt, max_tokens=4000):
    if not GEMINI_API_KEY:
        return None
    url = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
    )
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": 0.7,
            "maxOutputTokens": max_tokens,
        },
    }
    for intento in range(3):
        try:
            r = requests.post(url, json=payload, timeout=60)
            if r.status_code == 200:
                data = r.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            elif r.status_code == 429:
                espera = 45 * (intento + 1)
                print(f"⚠️  Gemini rate limit. Esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"❌ Gemini error {r.status_code}: {r.text[:200]}")
                break
        except Exception as e:
            print(f"❌ Gemini error: {e}")
            time.sleep(30)
    return None


def llamar_ia(prompt, max_tokens=4000):
    """Llama a Groq primero, si falla usa Gemini."""
    print("🤖 Llamando a Groq...")
    resultado = _llamar_groq(prompt, max_tokens=max_tokens)
    if resultado and len(resultado.strip()) > 50:
        return resultado
    print("🔄 Groq falló. Usando Gemini...")
    resultado = _llamar_gemini(prompt, max_tokens=max_tokens)
    if resultado and len(resultado.strip()) > 50:
        return resultado
    print("❌ Ambos LLMs fallaron.")
    return None


def generate_complete_report(idea):
    """Genera un informe completo de 15 apartados (~2500 palabras)."""

    nombre = idea.get("nombre", "Sin nombre")
    print(f"📝 Generando informe completo para: {nombre}")

    contexto = f"""
NOMBRE: {idea.get('nombre', '')}
PROBLEMA: {idea.get('problema', idea.get('Problem', ''))}
SOLUCIÓN: {idea.get('solucion', idea.get('Solution', ''))}
DESCRIPCIÓN: {idea.get('descripcion', idea.get('Description', ''))}
PROPUESTA DE VALOR: {idea.get('propuesta_valor', idea.get('Value', ''))}
TIPO: {idea.get('tipo', '')}
VERTICAL/MERCADO: {idea.get('vertical', idea.get('Target', ''))}
PRECIO: {idea.get('precio', '')}
MONETIZACIÓN: {idea.get('monetizacion', idea.get('Business', ''))}
STACK TECNOLÓGICO: {idea.get('tool', '')}
ESFUERZO MVP: {idea.get('esfuerzo', idea.get('MVP', ''))}
REVENUE 6 MESES: {idea.get('revenue_6m', '')}
ESTRATEGIA LANZAMIENTO: {idea.get('como', idea.get('Marketing', ''))}
FORTALEZAS: {', '.join(idea.get('fortalezas', [])) if isinstance(idea.get('fortalezas', []), list) else idea.get('fortalezas', '')}
DEBILIDADES: {', '.join(idea.get('debilidades', [])) if isinstance(idea.get('debilidades', []), list) else idea.get('debilidades', '')}
SCORE CRÍTICO: {idea.get('score_critico', idea.get('ScoreCritic', 0))}/100
SCORE VIRAL: {idea.get('viral_score', idea.get('ScoreViral', 0))}/100
SCORE GENERADOR: {idea.get('score_generador', idea.get('ScoreGen', 0))}/100
"""

    prompt = f"""Eres un experto analista de negocios digitales con 15 años de experiencia lanzando productos SaaS, herramientas de IA y negocios online. 

Analiza esta idea de negocio y genera un INFORME COMPLETO, DETALLADO y ACCIONABLE en español.

--- DATOS DE LA IDEA ---
{contexto.strip()}
--- FIN DATOS ---

Genera el informe con EXACTAMENTE estos 15 apartados, usando ## para los títulos. 
Cada apartado debe tener mínimo 150 palabras con datos concretos, ejemplos reales y pasos accionables.
Usa números, porcentajes y referencias a empresas/herramientas reales cuando sea posible.

## 1. IDEA Y PROPUESTA DE VALOR
Explica el problema con datos de mercado. Cuantifica el dolor. Describe la solución con claridad. Define la propuesta de valor única y por qué es difícil de copiar.

## 2. ANÁLISIS DE MERCADO
Tamaño del mercado TAM/SAM/SOM con cifras reales. Tendencias actuales. Por qué es el momento adecuado para lanzar ahora. Segmentación del mercado.

## 3. CLIENTE IDEAL (BUYER PERSONA)
Define 2 perfiles de cliente con nombre ficticio, edad, trabajo, ingresos, problemas diarios, dónde busca soluciones, qué le frena comprar, qué le haría comprar.

## 4. ANÁLISIS DE LA COMPETENCIA
Lista 4-5 competidores reales con nombre. Para cada uno: precio, fortaleza principal, debilidad principal. Tabla comparativa. Posicionamiento diferencial de esta idea.

## 5. MODELO DE NEGOCIO
Estructura de ingresos detallada. Precios por tier (Gratis/Basic/Pro/Enterprise si aplica). Proyección de MRR a 3/6/12 meses con escenario conservador y optimista. Métricas unitarias: LTV, CAC, payback period.

## 6. VALIDACIÓN DEL NEGOCIO
Plan de validación en 30 días sin gastar dinero. Landing page + waitlist. Canales para encontrar los primeros 10 clientes. Indicadores que confirman product-market fit. Señales de alarma.

## 7. PLAN FINANCIERO
Inversión inicial necesaria (desglosada). Costes fijos mensuales. Punto de equilibrio. Flujo de caja mes a mes para los primeros 6 meses. Qué necesitas para ser rentable.

## 8. ESTRATEGIA DE MARKETING DIGITAL
3 canales principales con tácticas específicas. Contenido que funciona para este nicho. Estrategia SEO con 10 keywords objetivo. Plan de redes sociales. Estrategia de email marketing.

## 9. TECNOLOGÍA Y HERRAMIENTAS
Stack técnico recomendado con herramientas concretas y coste. Plan de desarrollo del MVP en fases. Tiempo estimado por fase. Qué externalizar y qué construir tú mismo. Herramientas de IA que aceleran el desarrollo.

## 10. MÉTRICAS Y KPIs
10 métricas clave organizadas por categoría (adquisición, activación, retención, ingresos, referidos). Valores objetivo para cada métrica. Dashboard recomendado. Frecuencia de revisión.

## 11. ASPECTOS LEGALES Y FISCALES
Forma jurídica recomendada. Registros necesarios. Protección de datos (RGPD si aplica). Términos de servicio esenciales. Aspectos fiscales clave. Riesgos legales específicos de este negocio.

## 12. OPERACIONES Y GESTIÓN
Estructura del equipo para el lanzamiento (puede ser solo fundador). Procesos clave a automatizar desde el día 1. Herramientas de gestión recomendadas. Plan de escalado del equipo.

## 13. MARCA Y CONFIANZA
Estrategia de naming y posicionamiento de marca. Cómo construir autoridad en el nicho en 90 días. Estrategia de social proof (casos de éxito, testimonios). Construcción de comunidad.

## 14. RIESGOS Y PLAN B
Top 5 riesgos ordenados por probabilidad e impacto. Plan de mitigación para cada uno. Señales de que hay que pivotar. 3 pivots posibles si el modelo principal no funciona.

## 15. MENTALIDAD Y ESTRATEGIA PERSONAL
Hoja de ruta semana a semana para los primeros 90 días. Los 3 errores más comunes en este tipo de negocio. Recursos (libros, cursos, comunidades) específicos para este nicho. El único KPI más importante en el que enfocarse el primer mes.

Recuerda: mínimo 2500 palabras en total, máximo detalle, ejemplos concretos y accionables."""

    informe = llamar_ia(prompt, max_tokens=4000)

    if not informe:
        print(f"❌ No se pudo generar informe para {nombre}")
        return None

    print(f"✅ Informe generado: {len(informe)} caracteres, ~{len(informe.split()) } palabras")
    return informe
