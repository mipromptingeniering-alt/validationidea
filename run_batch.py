import json
import os
from datetime import datetime
from dotenv import load_dotenv
from agents.generator_agent import generate
from agents.critic_agent import critique
from agents.notion_sync_agent import sync_idea_to_notion

load_dotenv()

DATA_FILE = "data/ideas.json"
MIN_SCORE = 65


def load_ideas():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, list) else []
        except Exception:
            return []
    return []


def save_idea(idea):
    ideas = load_ideas()
    idea["id"]    = len(ideas) + 1
    idea["fecha"] = datetime.now().isoformat()
    idea["date"]  = idea["fecha"]
    ideas.append(idea)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(ideas, f, ensure_ascii=False, indent=2)
    print(f"💾 Guardada localmente (total: {len(ideas)})")


def main():
    print("\n" + "=" * 60)
    print("🚀 VALIDATION IDEA — Generador Automatico v2.0")
    print("=" * 60 + "\n")

    # KB: mostrar stats sin bloquear
    try:
        from agents.knowledge_base import get_stats, get_contexto_para_generador
        kb = get_stats()
        print(f"📚 KB: {kb['total']} ideas analizadas | Mejor tipo: {kb['mejor_tipo']}")
        ctx = get_contexto_para_generador()
        if ctx:
            print(f"   💡 {ctx[:200]}")
    except Exception as e:
        print(f"📚 KB no disponible: {e}")

    # PASO 1: Generar idea
    print("\n--- GENERANDO IDEA ---")
    idea = generate()
    if not idea:
        print("❌ No se pudo generar una idea valida")
        return False
    print(f"✅ Idea: {idea.get('nombre')}")

    # PASO 2: Evaluar idea
    print("\n--- EVALUANDO IDEA ---")
    evaluation = critique(idea)
    if not evaluation:
        print("❌ No se pudo evaluar la idea")
        return False

    score = evaluation.get("score_critico") or evaluation.get("score", 0)

    idea["score_critico"]   = score
    idea["score_generador"] = idea.get("score_generador", 80)
    idea["viral_score"]     = evaluation.get("viral_score", 0)
    idea["fortalezas"]      = evaluation.get("puntos_fuertes", [])
    idea["debilidades"]     = evaluation.get("puntos_debiles", [])
    idea["resumen"]         = evaluation.get("resumen", "")

    print(f"📊 Score: {score}/100")
    print(f"💪 Fortalezas: {idea['fortalezas']}")
    print(f"⚠️  Debilidades: {idea['debilidades']}")

    # PASO 3: Verificación de calidad mínima
    if score < MIN_SCORE:
        print(f"\n⚠️  Score {score} < {MIN_SCORE} — idea descartada")
        return False

    print(f"\n✅ Idea APROBADA (score: {score})")

    # PASO 4: Guardar localmente
    save_idea(idea)

    # PASO 5: Actualizar Knowledge Base
    try:
        from agents.knowledge_base import aprender
        aprender(idea, score)
        print("🧠 Knowledge Base actualizada")
    except Exception as e:
        print(f"⚠️  KB no actualizada: {e}")

    # PASO 6: Sincronizar con Notion
    print("\n--- SINCRONIZANDO CON NOTION ---")
    try:
        result = sync_idea_to_notion(idea)
        if result:
            print(f"✅ Sincronizado: {result.get('url', result)}")
        else:
            print("⚠️  Notion falló, pero idea guardada localmente")
    except Exception as e:
        print(f"⚠️  Error Notion: {e}")

    print("\n" + "=" * 60)
    print(f"🎉 COMPLETADO: {idea.get('nombre')} (Score: {score})")
    print("=" * 60 + "\n")
    return True


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
