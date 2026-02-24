import os
import json
import time


def generar_idea(ideas_existentes=None):
    """Genera 1 idea de negocio única usando Groq con contexto evolutivo de KB."""
    try:
        import groq
        from agents.knowledge_base import get_contexto_para_generador
    except ImportError as e:
        print(f"❌ Error importando dependencias en generator_agent: {e}")
        return None

    client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # ── P1: Inyectar contexto de Knowledge Base ──────────────────────────────
    kb_contexto = ""
    try:
        kb_raw = get_contexto_para_generador()
        if kb_raw:
            kb_contexto = (
                "\n\nCONTEXTO DE APRENDIZAJE — usa esto para mejorar la calidad:\n"
                + str(kb_raw)
            )
            print("📚 Contexto KB inyectado en el prompt")
    except Exception as e:
        print(f"⚠️ No se pudo obtener contexto KB (continuamos sin él): {e}")

    # ── Exclusiones: ideas ya generadas ──────────────────────────────────────
    exclusiones = ""
    if ideas_existentes:
        nombres = []
        for i in ideas_existentes[-20:]:
            if isinstance(i, dict):
                n = i.get("nombre") or i.get("name") or ""
                if n:
                    nombres.append(n)
        if nombres:
            exclusiones = (
                "\n\nIDEAS YA GENERADAS (no repitas ni hagas variaciones):\n"
                + "\n".join(f"- {n}" for n in nombres)
            )

    system_prompt = (
        "Eres un experto en startups, validación de ideas de negocio y emprendimiento digital. "
        "Tu misión es generar ideas CONCRETAS, INNOVADORAS y con ALTO POTENCIAL de monetización. "
        "Prioriza: modelo de negocio claro, problema urgente y solución diferenciada."
        + kb_contexto
    )

    user_prompt = (
        "Genera exactamente 1 idea de negocio nueva y viable.\n"
        "Responde ÚNICAMENTE con JSON válido, sin texto antes ni después:\n"
        "{\n"
        '  "nombre": "Nombre memorable de la idea",\n'
        '  "vertical": "SaaS / App móvil / Marketplace / IA / Hardware / Servicio / E-commerce / Educación / Salud / Fintech",\n'
        '  "problema": "Descripción clara del problema (mínimo 50 palabras)",\n'
        '  "solucion": "Cómo lo resuelve de forma concreta (mínimo 50 palabras)",\n'
        '  "descripcion": "Descripción completa del negocio (mínimo 100 palabras)",\n'
        '  "propuesta_valor": "Propuesta única y diferenciada",\n'
        '  "cliente_objetivo": "Cliente ideal con demografía y comportamiento",\n'
        '  "mvp": "Producto mínimo viable para validar en 30 días",\n'
        '  "marketing": "Estrategia de adquisición de primeros clientes",\n'
        '  "metricas": "3-5 métricas clave de éxito",\n'
        '  "modelo_negocio": "Cómo genera ingresos con precio aproximado",\n'
        '  "investigacion": "Tamaño de mercado y contexto competitivo"\n'
        "}"
        + exclusiones
    )

    for intento in range(5):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.9,
                max_tokens=800
            )

            contenido = response.choices[0].message.content.strip()

            # Limpiar markdown si existe
            if "```json" in contenido:
                contenido = contenido.split("```json").split("```").strip()[1]
            elif "```" in contenido:
                contenido = contenido.split("```")[1].split("```")[0].strip()

            # Extraer solo el bloque JSON
            inicio = contenido.find("{")
            fin = contenido.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                contenido = contenido[inicio:fin]

            idea = json.loads(contenido)
            print(f"✅ Idea generada (con KB context): {idea.get('nombre', 'Sin nombre')}")
            return idea

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON inválido intento {intento + 1}: {e}")
            time.sleep(5)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                espera = 30 * (2 ** min(intento, 3))
                print(f"⚠️ Rate limit Groq (intento {intento + 1}), esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"❌ Error Groq intento {intento + 1}: {e}")
                time.sleep(5)

    print("❌ Todos los intentos con Groq fallaron en generator_agent")
    return None
