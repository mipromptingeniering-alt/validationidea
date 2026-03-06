import os
import json
import time
import random
from groq import Groq
from agents.encoding_helper import fix_llm_encoding
from agents.knowledge_base import get_contexto_para_generador

def _groq_chat(messages, max_intentos=3):
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))
    model = "llama-3.3-70b-versatile"
    for intento in range(max_intentos):
        try:
            return client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.85,
                max_tokens=900,
            )
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                espera = min(4 * (2 ** intento) + random.uniform(0, 2), 30)
                print(f"⏳ Rate limit (intento {intento+1}) → esperando {espera:.0f}s...")
                time.sleep(espera)
                if intento >= 1:
                    model = "llama-3.1-8b-instant"
                    print("🔄 Cambiando a modelo ligero")
            else:
                print(f"❌ Error Groq: {e}")
                return None
    return None

def es_repetida(nombre, ideas_existentes):
    n = nombre.lower().strip()
    for idea in ideas_existentes:
        v = idea.get("nombre", "").lower().strip()
        if n == v or n in v or v in n:
            return True
        if len(n) >= 5 and len(v) >= 5 and n[:5] == v[:5]:
            return True
    return False

def generar_idea(ideas_existentes):
    try:
        contexto_kb = get_contexto_para_generador()
        print("📚 Contexto KB inyectado en el prompt")
    except Exception as e:
        print(f"⚠️ No se pudo obtener contexto KB: {e}")
        contexto_kb = "Sin contexto previo"

    nombres_existentes = [i.get("nombre", "") for i in ideas_existentes[-30:]]
    
    sectores = ["salud mental", "turismo rural", "educación online", "finanzas personales",
                "productividad", "comercio local Murcia", "deporte", "gastronomía",
                "mascotas", "sostenibilidad", "inmobiliario", "servicios freelance"]
    sector_sugerido = random.choice(sectores)

    prompt = f"""Eres el mejor experto mundial en startups y negocios digitales.

Crea UNA idea de negocio digital ORIGINAL y NUNCA ANTES VISTA.

SECTOR SUGERIDO: {sector_sugerido}

IDEAS YA EXISTENTES (NO REPETIR NINGUNA):
{json.dumps(nombres_existentes, ensure_ascii=False)}

CONTEXTO KB - PATRONES GANADORES:
{contexto_kb}

REQUISITOS OBLIGATORIOS:
- Nombre DIFERENTE a todos los existentes
- Problema REAL y CONCRETO (no genérico)
- Solución SIMPLE ejecutable en 30 días con menos de 500€
- Modelo de negocio con ingresos recurrentes
- Score potencial >80/100

Responde ÚNICAMENTE con JSON válido, sin markdown, sin explicaciones:
{{
  "nombre": "NombreUnico",
  "descripcion": "Qué hace en 2 frases concretas",
  "problema": "Dolor específico que sufre el usuario",
  "solucion": "Cómo lo resuelve exactamente",
  "vertical": "Categoría: SaaS / App móvil / Marketplace / Web / Local",
  "tipo": "SaaS / App móvil / Marketplace / Web / Consultoría / Comunidad",
  "monetizacion": "Modelo exacto: Suscripción 9.99€/mes / Comisión 5% / etc",
  "propuesta_valor": "Por qué un usuario pagaría por esto",
  "mvp": "3 pasos concretos para el MVP en 30 días",
  "marketing": "Cómo conseguir los primeros 100 usuarios gratis"
}}"""

    for intento in range(3):
        response = _groq_chat([{"role": "user", "content": prompt}])
        if not response:
            print(f"⚠️ JSON inválido intento {intento+1}: No response")
            continue

        try:
            content = response.choices[0].message.content.strip()
            content = fix_llm_encoding(content)

            if "```" in content:
                parts = content.split("```")
                for part in parts:
                    if "{" in part:
                        content = part.replace("json", "").strip()
                        break

            inicio = content.find("{")
            fin = content.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                content = content[inicio:fin]

            idea = json.loads(content)

            campos = ["nombre", "descripcion", "problema", "solucion", "vertical", "tipo"]
            for campo in campos:
                idea.setdefault(campo, "Desconocido")

            nombre = idea.get("nombre", "")
            if not nombre or nombre == "Desconocido":
                print(f"⚠️ Nombre vacío intento {intento+1}")
                continue

            if es_repetida(nombre, ideas_existentes):
                print(f"⚠️ Idea repetida: {nombre} — regenerando...")
                continue

            idea.setdefault("monetizacion", "Suscripción mensual")
            idea.setdefault("propuesta_valor", "Ahorra tiempo y dinero")
            idea.setdefault("mvp", "Landing + formulario + core básico")
            idea.setdefault("marketing", "SEO + comunidades + redes sociales")
            idea.setdefault("fecha", __import__("datetime").datetime.now().isoformat())

            print(f"✅ Idea generada (KB+P10): {nombre}")
            return idea

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON inválido intento {intento+1}: {e}")
            continue
        except Exception as e:
            print(f"⚠️ Error intento {intento+1}: {e}")
            continue

    print("❌ No se pudo generar idea válida")
    return None
# FIN COMPLETO generator_agent.py
