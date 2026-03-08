"""
Ejecutar UNA vez para migrar ideas existentes a la nueva KB.
Después de hacer git push, Railway lo ejecutará automáticamente
al arrancar si lo añades al Procfile, o puedes ejecutarlo manualmente.
"""
import json, os, sys
sys.path.insert(0, os.path.dirname(__file__))

def migrar():
    ruta = "data/ideas.json"
    if not os.path.exists(ruta):
        print("❌ No existe data/ideas.json")
        return

    with open(ruta, "r", encoding="utf-8") as f:
        ideas = json.load(f)

    print(f"📦 Migrando {len(ideas)} ideas a la nueva KB...")

    from agents.knowledge_base import registrar_idea, get_stats

    migradas = 0
    for idea in ideas:
        try:
            # Compatibilidad con ideas antiguas sin scores nuevos
            if "scores" not in idea:
                idea["scores"] = {
                    "critico": 70, "viral": 50, "generador": 70,
                    "monetizacion": 65, "ejecutabilidad": 70, "timing": 65,
                    "score_total": 68.0
                }
            elif "score_total" not in idea.get("scores", {}):
                s = idea["scores"]
                s["score_total"] = round(
                    s.get("critico",70)*0.25 +
                    s.get("generador",70)*0.25 +
                    s.get("ejecutabilidad",70)*0.20 +
                    s.get("monetizacion",65)*0.15 +
                    s.get("timing",65)*0.10 +
                    s.get("viral",50)*0.05, 1
                )
            registrar_idea(idea)
            migradas += 1
        except Exception as e:
            print(f"⚠️ Error migrando '{idea.get('nombre','?')}': {e}")

    stats = get_stats()
    print(f"✅ Migración completada: {migradas} ideas")
    print(f"📊 KB — Score promedio: {stats['score_promedio']} | Mejor: {stats['mejor_score']} | Tasa éxito: {stats['tasa_exito']}")

if __name__ == "__main__":
    migrar()
