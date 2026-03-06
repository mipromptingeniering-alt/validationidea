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
                max_tokens=700,
            )
        except Exception as e:
            if "429" in str(e) or "rate" in str(e).lower():
                espera = min(4 * (2 ** intento) + random.uniform(0, 2), 25)
                print(f"⏳ Rate limit (intento {intento+1}) → {espera:.0f}s...")
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
        if n == v or (len(n) >= 4 and len(v) >= 4 and n[:5] == v[:5]):
            return True
    return False

def generar_idea(ideas_existentes):
    try:
        contexto_kb = get_contexto_para_generador()
        print("📚 Contexto KB inyectado en el prompt")
    except Exception as e:
        print(f"⚠️ Sin contexto KB: {e}")
        contexto_kb = "Sin contexto previo"

    nombres_existentes = [i.get("nombre", "") for i in ideas_existentes[-30:]]

    sectores = [
        "salud mental digital", "turismo rural España", "educación online adultos",
        "finanzas personales jóvenes", "productividad freelance", "comercio local Murcia",
        "deporte amateur", "gastronomía local", "mascotas", "sostenibilidad hogar",
        "inmobiliario pequeño", "servicios para autónomos", "bienestar mayores",
        "idiomas online", "delivery especializado"
    ]
    sector = random.choice(sectores)

    prompt = f"""Eres un experto mundial en startups. Crea UNA idea de negocio digital ORIGINAL.

SECTOR: {sector}

IDEAS YA EXISTENTES - NO REPETIR:
{json.dumps(nombres_existentes[-20:], ensure_ascii=False)}

PATRONES EXITOSOS ANTERIORES:
{contexto_kb}

REGLAS:
- Nombre DIFERENTE a todos los existentes
- Problema REAL y concreto
- Ejecutable en 30 días con menos de 500€
- Ingresos recurrentes

Responde SOLO JSON válido, sin markdown, sin texto extra:
{{
  "nombre": "NombreUnico",
  "descripcion": "Qué hace en 2 frases",
  "problema": "Dolor concreto del usuario",
  "solucion": "Cómo lo resuelve",
  "vertical": "SaaS / App móvil / Marketplace / Web / Local",
  "tipo": "SaaS / App móvil / Marketplace / Web / Consultoría",
  "monetizacion": "Modelo exacto con precio",
  "propuesta_valor": "Por qué pagarían",
  "mvp": "3 pasos para MVP en 30 días",
  "marketing": "Cómo conseguir 100 usuarios gratis"
}}"""

    for intento in range(3):
        response = _groq_chat([{"role": "user", "content": prompt}])
        if not response:
            print(f"⚠️ Sin respuesta Groq intento {intento+1}")
            continue

        try:
            content = response.choices[0].message.content.strip()
            content = fix_llm_encoding(content)

            if "```" in content:
                for part in content.split("```"):
                    if "{" in part:
                        content = part.replace("json", "").strip()
                        break

            inicio = content.find("{")
            fin = content.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                content = content[inicio:fin]

            idea = json.loads(content)

            nombre = idea.get("nombre", "").strip()
            if not nombre or nombre.lower() == "desconocido":
                print(f"⚠️ Nombre vacío intento {intento+1}")
                continue

            if es_repetida(nombre, ideas_existentes):
                print(f"⚠️ Repetida: {nombre} → regenerando")
                continue

            idea.setdefault("descripcion", "")
            idea.setdefault("problema", "")
            idea.setdefault("solucion", "")
            idea.setdefault("vertical", "SaaS")
            idea.setdefault("tipo", "SaaS")
            idea.setdefault("monetizacion", "Suscripción mensual")
            idea.setdefault("propuesta_valor", "")
            idea.setdefault("mvp", "")
            idea.setdefault("marketing", "")
            idea.setdefault("fecha", __import__("datetime").datetime.now().isoformat())

            print(f"✅ Idea generada (KB+P10): {nombre}")
            return idea

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON inválido intento {intento+1}: {e}")
        except Exception as e:
            print(f"⚠️ Error intento {intento+1}: {e}")

    print("❌ No se pudo generar idea válida")
    return None
# FIN COMPLETO generator_agent.py
