import os
import sys
import json
from datetime import datetime

os.environ["PYTHONUTF8"] = "1"

def ejecutar_batch():
    print(f"\n{'=' * 60}")
    print(f"🚀 validationidea TOP QUALITY - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    from agents.generator_agent import generar_idea
    from agents.critic_agent import critique
    from agents.knowledge_base import aprender
    from agents.notion_sync_agent import sync_idea_to_notion
    from agents.cola_csv import guardar_en_cola

    max_intentos = 5  # Genera hasta 5 ideas, se queda con la MEJOR
    
    mejor_idea = None
    mejor_score = 0
    
    # 🆕 GENERAR MÚLTIPLES + ELEGIR LA MEJOR
    for intento in range(max_intentos):
        print(f"\n🔄 Intento {intento+1}/{max_intentos} - Buscando idea TOP...")
        
        # Cargar ideas existentes
        ideas_existentes = []
        ruta_ideas = os.path.join("data", "ideas.json")
        if os.path.exists(ruta_ideas):
            try:
                with open(ruta_ideas, "r", encoding="utf-8") as f:
                    ideas_existentes = json.load(f)
            except Exception:
                ideas_existentes = []

        # 1. Generar idea
        print("🧠 Generando idea TOP...")
        idea = generar_idea(ideas_existentes)
        if not idea:
            print("❌ No se pudo generar")
            continue

        nombre = idea.get("nombre", "Sin nombre")
        print(f"💡 Candidata: {nombre}")

        # 2. Evaluar
        print("🔍 Evaluando...")
        try:
            evaluacion = critique(idea)
            if evaluacion:
                idea.update(evaluacion)
                
                # 🆕 SCORE GENERAL PRECISO
                score_general = (
                    idea.get("score_critico", 0) * 0.4 +
                    idea.get("score_generador", 0) * 0.3 +
                    idea.get("viral_score", 0) * 0.2 +
                    idea.get("score_money", 0) * 0.1
                )
                idea["score_general"] = round(score_general, 1)
                
                print(f"📊 Score: {idea['score_general']}/100")
                print(f"   └─ C:{idea.get('score_critico',0):2d} V:{idea.get('viral_score',0):2d} G:{idea.get('score_generador',0):2d} M:{idea.get('score_money',0):2d}")
                
                # 🆕 GUARDAR MEJOR IDEA
                if score_general > mejor_score:
                    mejor_score = score_general
                    mejor_idea = idea.copy()
                    print(f"🏆 NUEVA MEJOR: {nombre} ({score_general:.1f})")
                else:
                    print(f"⏭️ Descartada ({score_general:.1f} < {mejor_score:.1f})")
                    
        except Exception as e:
            print(f"⚠️ Error evaluando: {e}")
            continue

    if not mejor_idea or mejor_score < 70:
        print(f"❌ No se encontró idea TOP (mejor: {mejor_score:.1f}). Reintentando en próximo batch.")
        return False

    idea = mejor_idea
    print(f"\n🎯 IDEA FINAL SELECCIONADA: {idea['nombre']} - Score {idea['score_general']}/100")

    # 3. Guardar
    ideas_existentes.append(idea)
    os.makedirs("data", exist_ok=True)
    try:
        with open(ruta_ideas, "w", encoding="utf-8") as f:
            json.dump(ideas_existentes, f, ensure_ascii=False, indent=2)
        print("💾 Guardada TOP idea")
    except Exception as e:
        print(f"⚠️ Error guardando: {e}")

    # 4. Knowledge Base (SOLO aprende de TOP ideas)
    try:
        score_kb = idea.get("score_generador")
        if score_kb:
            aprender(idea, score_kb)
            print(f"📚 KB aprendió TOP idea (score={score_kb})")
    except Exception as e:
        print(f"⚠️ Error KB: {e}")

    # 5. Notion
    print("🔗 Sincronizando TOP idea...")
    try:
        resultado = sync_idea_to_notion(idea)
        if resultado:
            print(f"✅ TOP idea en Notion: {idea['nombre']}")
            return True
        else:
            raise Exception("Notion falló")
    except Exception as e:
        print(f"❌ Notion falló: {e}")
        guardar_en_cola(
            nombre_idea=idea["nombre"],
            motivo_fallo=str(e),
            datos_json=idea
        )
        return False

if __name__ == "__main__":
    exito = ejecutar_batch()
    sys.exit(0 if exito else 1)
