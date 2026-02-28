import os
import json
from datetime import datetime

class KnowledgeBase:
    def __init__(self):
        self.ruta_kb = os.path.join("data", "knowledge_base.json")
        self.kb = self._cargar_kb()

    def _cargar_kb(self):
        if os.path.exists(self.ruta_kb):
            try:
                with open(self.ruta_kb, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    data.setdefault("top_ideas", [])
                    data.setdefault("total_ideas", 0)
                    data.setdefault("mejor_score", 0)
                    data.setdefault("scores_lista", [])
                    data.setdefault("verticales", {})
                    data.setdefault("tipos", {})
                    return data
            except:
                pass
        return {
            "top_ideas": [],
            "total_ideas": 0,
            "mejor_score": 0,
            "scores_lista": [],
            "verticales": {},
            "tipos": {}
        }

    def aprender(self, idea, score_generador):
        score_general = idea.get("score_general", 0)
        vertical = idea.get("vertical", "Desconocido")
        tipo = idea.get("tipo", "Desconocido")

        self.kb["total_ideas"] += 1
        self.kb["scores_lista"].append(score_general)
        self.kb["scores_lista"] = self.kb["scores_lista"][-50:]

        if score_general > self.kb["mejor_score"]:
            self.kb["mejor_score"] = score_general

        # Contar verticales y tipos ganadores
        if score_general >= 75:
            self.kb["verticales"][vertical] = self.kb["verticales"].get(vertical, 0) + 1
            self.kb["tipos"][tipo] = self.kb["tipos"].get(tipo, 0) + 1

        if score_general >= 75:
            self.kb["top_ideas"].append({
                "nombre": idea.get("nombre"),
                "vertical": vertical,
                "tipo": tipo,
                "score": score_general
            })
            self.kb["top_ideas"] = self.kb["top_ideas"][-10:]

        self._guardar()
        print(f"[KB] ✅ {idea.get('nombre')} | score={score_general:.1f} | total={self.kb['total_ideas']}")

    def get_contexto_para_generador(self):
        try:
            top3 = self.kb.get("top_ideas", [])[-3:]
            if not top3:
                return "KB iniciando — genera libremente"
            return "🏆 TOP ideas:\n" + "\n".join([
                f"- {i['nombre']} ({i['vertical']}, {i['score']:.0f}pts)"
                for i in top3
            ])
        except:
            return "KB disponible"

    def get_stats(self):
        """Stats para resumen diario de Telegram"""
        scores = self.kb.get("scores_lista", [])
        score_prom = sum(scores) / len(scores) if scores else 0

        verticales = self.kb.get("verticales", {})
        mejor_vertical = max(verticales, key=verticales.get) if verticales else "N/A"

        tipos = self.kb.get("tipos", {})
        mejor_tipo = max(tipos, key=tipos.get) if tipos else "N/A"

        return {
            "total_ideas": self.kb.get("total_ideas", 0),
            "score_promedio": round(score_prom, 1),
            "mejor_score": self.kb.get("mejor_score", 0),
            "mejor_vertical": mejor_vertical,
            "mejor_tipo": mejor_tipo
        }

    def _guardar(self):
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.ruta_kb, "w", encoding="utf-8") as f:
                json.dump(self.kb, f, ensure_ascii=False, indent=2)
        except:
            pass

kb_global = KnowledgeBase()

def aprender(idea, score_generador):
    kb_global.aprender(idea, score_generador)

def get_contexto_para_generador():
    return kb_global.get_contexto_para_generador()

def get_stats():
    return kb_global.get_stats()
