import os
import json
from datetime import datetime
from collections import Counter

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
                    data.setdefault("patrones_ganadores", [])
                    return data
            except:
                pass
        return {
            "top_ideas": [],
            "total_ideas": 0,
            "mejor_score": 0,
            "scores_lista": [],
            "verticales": {},
            "tipos": {},
            "patrones_ganadores": []
        }

    def aprender(self, idea, score_generador):
        score_general = idea.get("score_general", 0)
        nombre   = idea.get("nombre", "?")
        vertical = idea.get("vertical", "").strip() or "Desconocido"
        tipo     = idea.get("tipo", "").strip() or "Desconocido"

        # Limpiar tipo genérico
        if tipo.lower() in ["desconocido", "", "none", "null"]:
            # Inferir del vertical
            v = vertical.lower()
            if "app" in v:      tipo = "App móvil"
            elif "saas" in v:   tipo = "SaaS"
            elif "market" in v: tipo = "Marketplace"
            elif "web" in v:    tipo = "Web"
            elif "local" in v:  tipo = "Negocio local"
            else:               tipo = "SaaS"
            idea["tipo"] = tipo

        self.kb["total_ideas"] += 1
        self.kb["scores_lista"].append(round(score_general, 1))
        self.kb["scores_lista"] = self.kb["scores_lista"][-100:]

        if score_general > self.kb["mejor_score"]:
            self.kb["mejor_score"] = round(score_general, 1)

        # Contar verticales y tipos (solo ideas buenas)
        if score_general >= 72:
            self.kb["verticales"][vertical] = self.kb["verticales"].get(vertical, 0) + 1
            self.kb["tipos"][tipo]          = self.kb["tipos"].get(tipo, 0) + 1

        # Top 15 ideas
        if score_general >= 75:
            self.kb["top_ideas"].append({
                "nombre":   nombre,
                "vertical": vertical,
                "tipo":     tipo,
                "score":    round(score_general, 1),
                "fecha":    datetime.now().strftime("%d/%m/%Y")
            })
            # Ordenar por score y quedarse top 15
            self.kb["top_ideas"] = sorted(
                self.kb["top_ideas"], key=lambda x: x["score"], reverse=True
            )[:15]

        # Patrones ganadores (ideas >82)
        if score_general >= 82:
            self.kb["patrones_ganadores"].append({
                "vertical": vertical,
                "tipo":     tipo,
                "score":    round(score_general, 1)
            })
            self.kb["patrones_ganadores"] = self.kb["patrones_ganadores"][-20:]

        self._guardar()
        print(f"[KB] ✅ {nombre} | tipo={tipo} | vertical={vertical} | score={score_general:.1f} | total={self.kb['total_ideas']}")

    def get_contexto_para_generador(self):
        try:
            top5   = self.kb.get("top_ideas", [])[:5]
            patron = self.kb.get("patrones_ganadores", [])[:3]

            contexto = ""
            if top5:
                contexto += "🏆 MEJORES IDEAS (evitar repetir):\n"
                contexto += "\n".join([f"- {i['nombre']} ({i['tipo']}, {i['score']}pts)" for i in top5])

            if patron:
                contexto += "\n\n🔥 PATRONES GANADORES:\n"
                contexto += "\n".join([f"- {p['vertical']}/{p['tipo']} → {p['score']}pts" for p in patron])

            return contexto[:800] if contexto else "KB iniciando"
        except:
            return "KB disponible"

    def get_stats(self):
        scores = self.kb.get("scores_lista", [])
        score_prom = round(sum(scores) / len(scores), 1) if scores else 0.0

        verticales = self.kb.get("verticales", {})
        mejor_v = max(verticales, key=verticales.get) if verticales else "N/A"

        tipos = self.kb.get("tipos", {})
        mejor_t = max(tipos, key=tipos.get) if tipos else "N/A"

        top = self.kb.get("top_ideas", [])
        mejor_idea = top[0]["nombre"] if top else "N/A"

        return {
            "total_ideas":    self.kb.get("total_ideas", 0),
            "score_promedio": score_prom,
            "mejor_score":    self.kb.get("mejor_score", 0),
            "mejor_vertical": mejor_v,
            "mejor_tipo":     mejor_t,
            "mejor_idea":     mejor_idea
        }

    def get_top_ideas(self, n=5):
        return self.kb.get("top_ideas", [])[:n]

    def _guardar(self):
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.ruta_kb, "w", encoding="utf-8") as f:
                json.dump(self.kb, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"⚠️ Error guardando KB: {e}")

# ── Instancia global ──────────────────────────────────────
kb_global = KnowledgeBase()

def aprender(idea, score_generador):
    kb_global.aprender(idea, score_generador)

def get_contexto_para_generador():
    return kb_global.get_contexto_para_generador()

def get_stats():
    return kb_global.get_stats()

def get_top_ideas(n=5):
    return kb_global.get_top_ideas(n)
# FIN COMPLETO knowledge_base.py
