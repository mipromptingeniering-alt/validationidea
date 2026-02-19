# agents/generator_agent.py - VERSION 2.0 con auto-mejora dinamica
import json
import hashlib
import os
from collections import Counter
from groq import Groq
from dotenv import load_dotenv
from agents.encoding_helper import fix_llm_encoding

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))


def load_existing_ideas():
    try:
        if os.path.exists("data/ideas.json"):
            with open("data/ideas.json", "r", encoding="utf-8") as f:
                ideas = json.load(f)
            return ideas if isinstance(ideas, list) else []
    except Exception:
        pass
    return []


def get_best_examples(ideas, n=5):
    """Obtiene los N mejores ejemplos ordenados por score (auto-mejora real)"""
    scored = [i for i in ideas if isinstance(i.get("score"), (int, float))]
    if not scored:
        return ideas[:n]
    return sorted(scored, key=lambda x: x.get("score", 0), reverse=True)[:n]


def get_idea_hash(idea):
    key = f"{idea.get('nombre', '')}{idea.get('problema', '')}"
    return hashlib.md5(key.lower().encode()).hexdigest()


def get_existing_hashes(ideas):
    return {get_idea_hash(i) for i in ideas}


def build_dynamic_prompt(existing_ideas):
    """Construye prompt con ejemplos dinamicos de las mejores ideas"""
    best = get_best_examples(existing_ideas, n=5)
    existing_names = {i.get("nombre", "").lower() for i in existing_ideas}

    # Detectar verticales saturadas (>= 3 ideas en la misma vertical)
    vertical_count = Counter(i.get("vertical", "") for i in existing_ideas)
    overused = [v for v, c in vertical_count.items() if c >= 3 and v]

    # --- Seccion de ejemplos dinamicos ---
    if best:
        examples_text = "\n\nEJEMPLOS DE IDEAS CON MEJOR SCORE (aprende de su estructura):\n"
        for idx, ex in enumerate(best, 1):
            examples_text += (
                f"\nEjemplo {idx} — Score: {ex.get('score', 'N/A')}\n"
                f"  Nombre: {ex.get('nombre', '')}\n"
                f"  Problema: {ex.get('problema', '')}\n"
                f"  Solucion: {ex.get('solucion', '')}\n"
                f"  Tipo: {ex.get('tipo', '')} | Vertical: {ex.get('vertical', '')}\n"
                f"  Monetizacion: {ex.get('monetizacion', '')}\n"
            )
    else:
        examples_text = """
EJEMPLOS DE IDEAS EXITOSAS:
Ejemplo 1: MealPlanAI - SaaS que genera planes de comida personalizados con IA, 9EUR/mes
Ejemplo 2: ContractBot - Plugin para abogados que analiza contratos, 29EUR/mes
Ejemplo 3: SEO Mentor Guide - PDF completo de SEO para freelancers, 27EUR unico pago
"""

    # --- Seccion de restricciones ---
    avoid_section = ""
    if existing_names:
        sample_names = ", ".join(list(existing_names)[:8])
        avoid_section += f"\n\nNO generes ideas similares a: {sample_names}"
    if overused:
        avoid_section += f"\nEVITA las verticales ya saturadas: {', '.join(overused)}"

    prompt = f"""Eres un experto en negocios digitales. Genera UNA idea de negocio UNICA, ORIGINAL y ALTAMENTE VIABLE con score objetivo de 80+.

CRITERIOS DE CALIDAD:
- Resuelve un problema REAL y especifico (no generico)
- Nicho claro y alcanzable
- Modelo de monetizacion probado (SaaS, info-product, etc.)
- Construible con IA/automatizacion con presupuesto bajo
- MVP realizable en menos de 40 horas
- Revenue potencial 6 meses: entre 500 EUR y 5000 EUR
{examples_text}{avoid_section}

Responde EXCLUSIVAMENTE en formato JSON valido (sin markdown, sin texto extra):
{{
  "nombre": "Nombre memorable del producto",
  "problema": "Problema especifico que resuelve",
  "solucion": "Como lo resuelve de forma unica",
  "descripcion": "Descripcion en 2-3 frases",
  "propuesta_valor": "Por que es mejor que alternativas",
  "tipo": "SaaS|PDF|Plugin|Agencia|Marketplace|Tool",
  "vertical": "Mercado objetivo especifico",
  "precio": "Precio en euros (numero)",
  "monetizacion": "suscripcion|unico pago|freemium|comision",
  "tool": "Stack tecnico: Python|No-code|Webflow|etc",
  "esfuerzo": "Horas para MVP",
  "revenue_6m": "Ingresos estimados 6 meses en euros",
  "como": "3 pasos concretos para lanzar"
}}"""
    return prompt


def generate():
    """Genera una idea de negocio unica — retorna dict o None"""
    existing_ideas = load_existing_ideas()
    existing_hashes = get_existing_hashes(existing_ideas)

    for attempt in range(1, 6):
        try:
            prompt = build_dynamic_prompt(existing_ideas)

            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=1000,
            )

            content = response.choices[0].message.content.strip()

            # Limpiar markdown si existe
            if "```json" in content:
                content = content.split("```json").split("```").strip()[1]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Fix encoding UTF-8
            content = fix_llm_encoding(content)

            # Parsear JSON
            idea = json.loads(content)

            # Validar campos requeridos
            required = ["nombre", "problema", "solucion", "descripcion", "tipo"]
            if not all(f in idea for f in required):
                print(f"⚠️  Intento {attempt}: Faltan campos requeridos")
                continue

            # Verificar unicidad
            h = get_idea_hash(idea)
            if h in existing_hashes:
                print(f"⚠️  Intento {attempt}: Idea duplicada, generando otra...")
                continue

            print(f"✅ Idea generada (intento {attempt}): {idea.get('nombre')}")
            return idea

        except json.JSONDecodeError as e:
            print(f"⚠️  Intento {attempt}: Error JSON — {e}")
        except Exception as e:
            print(f"⚠️  Intento {attempt}: Error — {e}")

    print("❌ No se pudo generar idea valida despues de 5 intentos")
    return None
