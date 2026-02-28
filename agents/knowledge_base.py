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
                    # Validar estructura
                    data.setdefault("top_ideas", [])
                    data.setdefault("total_ideas", 0)
                    data.setdefault("mejor_score", 0)
                    return data
            except:
                pass
        return {
            "top_ideas": [],
            "total_ideas": 0,
            "mejor_score": 0
        }
    
    def aprender(self, idea, score_generador):
        score_general = idea.get("score_general", 0)
        
        self.kb["total_ideas"] += 1
        if score_general > self.kb["mejor_score"]:
            self.kb["mejor_score"] = score_general
        
        if score_general >= 75:
            self.kb["top_ideas"].append({
                "nombre": idea.get("nombre"),
                "vertical": idea.get("vertical", "Desconocido"),
                "score": score_general
            })
            self.kb["top_ideas"] = self.kb["top_ideas"][-10:]
        
        self._guardar()
        print(f"[KB] ✅ {idea.get('nombre')} | score={score_general:.1f} | total={self.kb['total_ideas']}")
    
    def get_contexto_para_generador(self):
        try:
            top3 = self.kb.get("top_ideas", [])[:3]
            if not top3:
                return "KB vacía - genera libremente"
            contexto = "🏆 TOP ideas:\n" + "\n".join([
                f"- {i['nombre']} ({i['vertical']}, {i['score']:.0f})"
                for i in top3
            ])
            return contexto[:800]
        except:
            return "KB inicializando..."

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
