import os
import re
import json
import time


def _similitud_semantica(idea_nueva: dict, ideas_existentes: list) -> tuple:
    """P10: Jaccard sobre palabras clave 4+ letras."""
    def palabras_clave(idea):
        texto = " ".join([
            str(idea.get("nombre",   "")),
            str(idea.get("vertical", "")),
            str(idea.get("problema", ""))[:150],
        ]).lower()
        return set(re.findall(r"\w{4,}", texto))

    nuevas = palabras_clave(idea_nueva)
    if not nuevas:
        return 0.0, ""

    max_sim    = 0.0
    nombre_sim = ""
    for idea_vieja in ideas_existentes[-50:]:
        if not isinstance(idea_vieja, dict):
            continue
        viejas = palabras_clave(idea_vieja)
        if not viejas:
            continue
        union = nuevas | viejas
        sim   = len(nuevas & viejas) / len(union) if union else 0.0
        if sim > max_sim:
            max_sim    = sim
            nombre_sim = idea_vieja.get("nombre", "?")

    return max_sim, nombre_sim


def generar_idea(ideas_existentes=None):
    """Genera 1 idea de negocio única con contexto KB (P1) + detector semántico (P10)."""
    try:
        import groq
        from agents.knowledge_base import get_contexto_para_generador
    except ImportError as e:
        print(f"❌ Error importando dependencias en generator_agent: {e}")
        return None

    client = groq.Groq(api_key=os.environ.get("GROQ_API_KEY"))

    # P1: Contexto de Knowledge Base
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
        print(f"⚠️ No se pudo obtener contexto KB: {e}")

    # Exclusiones: últimas 20 ideas por nombre
    exclusiones = ""
    if ideas_existentes:
        nombres = [
            i.get("nombre") or i.get("name") or ""
            for i in ideas_existentes[-20:]
            if isinstance(i, dict)
        ]
        nombres = [n for n in nombres if n]
        if nombres:
            exclusiones = (
                "\n\nIDEAS YA GENERADAS (no repetir ni hacer variaciones):\n"
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
        '  "nombre": "Nombre memorable (máx 3 palabras)",\n'
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

    MAX_INTENTOS_LLM       = 3
    MAX_REINTENTOS_SIMILAR = 2
    reintentos_similitud   = 0

    for intento in range(MAX_INTENTOS_LLM):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_prompt}
                ],
                temperature=0.9,
                max_tokens=800
            )

            contenido = response.choices[0].message.content.strip()

            if "```json" in contenido:
                contenido = contenido.split("```json").split("```").strip()[1]
            elif "```" in contenido:
                contenido = contenido.split("```")[1].split("```")[0].strip()

            inicio = contenido.find("{")
            fin    = contenido.rfind("}") + 1
            if inicio >= 0 and fin > inicio:
                contenido = contenido[inicio:fin]

            idea = json.loads(contenido)

            # P10: verificar similitud semántica
            if ideas_existentes:
                similitud, nombre_similar = _similitud_semantica(idea, ideas_existentes)
                if similitud > 0.70 and reintentos_similitud < MAX_REINTENTOS_SIMILAR:
                    reintentos_similitud += 1
                    print(
                        f"⚠️ P10: '{idea.get('nombre')}' similar a "
                        f"'{nombre_similar}' ({similitud:.0%}) — regenerando ({reintentos_similitud}/2)..."
                    )
                    user_prompt_extra = (
                        user_prompt +
                        f"\n- ESPECIALMENTE evitar cualquier idea similar a: {nombre_similar}"
                    )
                    response2 = client.chat.completions.create(
                        model="llama-3.3-70b-versatile",
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user",   "content": user_prompt_extra}
                        ],
                        temperature=min(0.9 + reintentos_similitud * 0.05, 1.0),
                        max_tokens=800
                    )
                    c2 = response2.choices[0].message.content.strip()
                    if "```json" in c2:
                        c2 = c2.split("```json").split("```").strip()[1]
                    elif "```" in c2:
                        c2 = c2.split("```")[1].split("```")[0].strip()
                    i2, f2 = c2.find("{"), c2.rfind("}") + 1
                    if i2 >= 0 and f2 > i2:
                        c2 = c2[i2:f2]
                    try:
                        idea = json.loads(c2)
                    except Exception:
                        pass

            print(f"✅ Idea generada (KB+P10): {idea.get('nombre', 'Sin nombre')}")
            return idea

        except json.JSONDecodeError as e:
            print(f"⚠️ JSON inválido intento {intento + 1}: {e}")
            time.sleep(5)
        except Exception as e:
            error_str = str(e)
            if "429" in error_str or "rate_limit" in error_str.lower():
                espera = 8 * (2 ** min(intento, 2))
                print(f"⚠️ Rate limit Groq (intento {intento + 1}), esperando {espera}s...")
                time.sleep(espera)
            else:
                print(f"❌ Error Groq intento {intento + 1}: {e}")
                time.sleep(5)

    print("❌ Todos los intentos fallaron en generator_agent")
    return None
