import json
import os
from datetime import datetime


class KnowledgeBase:
    def __init__(self, data_file="data/ideas.json", kb_file="data/knowledge_base.json"):
        self.data_file = data_file
        self.kb_file = kb_file
        self.knowledge = self._load_knowledge()

    def _load_knowledge(self):
        if os.path.exists(self.kb_file):
            try:
                with open(self.kb_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "total_ideas": 0,
            "avg_score": 0,
            "best_verticals": [],
            "best_types": [],
            "best_monetization": [],
            "score_distribution": {},
            "top_ideas": [],
            "insights": [],
            "last_updated": None,
        }

    def _save_knowledge(self):
        os.makedirs("data", exist_ok=True)
        with open(self.kb_file, "w", encoding="utf-8") as f:
            json.dump(self.knowledge, f, ensure_ascii=False, indent=2)

    def _load_all_ideas(self):
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        return []

    def _get_score(self, idea):
        """Obtiene el score de una idea — compatible con score_critico y score"""
        return idea.get("score_critico") or idea.get("score") or 0

    def analyze(self, new_idea=None):
        """Analiza todas las ideas y actualiza el conocimiento"""
        ideas = self._load_all_ideas()
        if not ideas:
            return self.knowledge

        self.knowledge["total_ideas"] = len(ideas)
        scored = [i for i in ideas if isinstance(self._get_score(i), (int, float)) and self._get_score(i) > 0]

        if scored:
            scores = [self._get_score(i) for i in scored]
            self.knowledge["avg_score"] = round(sum(scores) / len(scores), 1)

            # Top 5 ideas por score
            top = sorted(scored, key=lambda x: self._get_score(x), reverse=True)[:5]
            self.knowledge["top_ideas"] = [
                {
                    "nombre": i.get("nombre"),
                    "score": self._get_score(i),
                    "tipo": i.get("tipo", i.get("vertical", ""))
                }
                for i in top
            ]

            # Distribucion de scores
            dist = {"0-50": 0, "51-70": 0, "71-80": 0, "81-100": 0}
            for s in scores:
                if s <= 50:
                    dist["0-50"] += 1
                elif s <= 70:
                    dist["51-70"] += 1
                elif s <= 80:
                    dist["71-80"] += 1
                else:
                    dist["81-100"] += 1
            self.knowledge["score_distribution"] = dist

            # Mejores verticales
            vertical_data = {}
            for i in scored:
                v = i.get("vertical", i.get("target", "Otro"))
                if v:
                    vertical_data.setdefault(v, []).append(self._get_score(i))
            v_avg = {v: round(sum(s) / len(s), 1) for v, s in vertical_data.items()}
            self.knowledge["best_verticals"] = sorted(
                v_avg.items(), key=lambda x: x[1], reverse=True
            )[:5]

            # Mejores tipos
            type_data = {}
            for i in scored:
                t = i.get("tipo", "Otro")
                if t:
                    type_data.setdefault(t, []).append(self._get_score(i))
            t_avg = {t: round(sum(s) / len(s), 1) for t, s in type_data.items()}
            self.knowledge["best_types"] = sorted(
                t_avg.items(), key=lambda x: x[1], reverse=True
            )[:3]

            # Mejores monetizaciones
            mon_data = {}
            for i in scored:
                m = i.get("monetizacion", i.get("modelo_negocio", "Otro"))
                if m:
                    mon_data.setdefault(str(m)[:50], []).append(self._get_score(i))
            m_avg = {m: round(sum(s) / len(s), 1) for m, s in mon_data.items()}
            self.knowledge["best_monetization"] = sorted(
                m_avg.items(), key=lambda x: x[1], reverse=True
            )[:3]

        self.knowledge["insights"] = self._generate_insights()
        self.knowledge["last_updated"] = datetime.now().isoformat()
        self._save_knowledge()

        print(
            f"📚 KB actualizada: {len(ideas)} ideas | "
            f"Avg score: {self.knowledge.get('avg_score', 0)} | "
            f"Insights: {len(self.knowledge['insights'])}"
        )
        return self.knowledge

    def _generate_insights(self):
        insights = []
        avg = self.knowledge.get("avg_score", 0)

        if avg >= 80:
            insights.append(f"🏆 Alta calidad: score promedio {avg}")
        elif avg >= 65:
            insights.append(f"📈 Buena calidad: score promedio {avg}")
        elif avg > 0:
            insights.append(f"⚠️  Mejorar prompts: score promedio {avg} (objetivo: 80+)")

        best_v = self.knowledge.get("best_verticals", [])
        if best_v:
            insights.append(f"🎯 Mejor vertical: {best_v[0][0]} (avg: {best_v[0][1]})")

        best_t = self.knowledge.get("best_types", [])
        if best_t:
            insights.append(f"💡 Mejor tipo: {best_t[0][0]} (avg: {best_t[0][1]})")

        dist = self.knowledge.get("score_distribution", {})
        total = self.knowledge.get("total_ideas", 1)
        if dist and total > 0:
            high = dist.get("81-100", 0)
            pct = round(high / total * 100, 1)
            insights.append(f"⭐ {pct}% de ideas con score 81+")

        top = self.knowledge.get("top_ideas", [])
        if top:
            insights.append(f"🥇 Mejor idea: {top[0]['nombre']} (score: {top[0]['score']})")

        return insights

    def get_prompt_hints(self):
        hints = []
        best_v = self.knowledge.get("best_verticals", [])
        if best_v:
            top_v = [v[0] for v in best_v[:3]]
            hints.append(f"Verticales con mejor rendimiento: {', '.join(top_v)}")
        best_t = self.knowledge.get("best_types", [])
        if best_t:
            top_t = [t[0] for t in best_t[:2]]
            hints.append(f"Tipos mas exitosos: {', '.join(top_t)}")
        best_m = self.knowledge.get("best_monetization", [])
        if best_m:
            hints.append(f"Mejor monetizacion: {best_m[0][0]}")
        return hints

    def get_summary(self):
        return {
            "total_ideas": self.knowledge.get("total_ideas", 0),
            "avg_score": self.knowledge.get("avg_score", 0),
            "top_ideas": self.knowledge.get("top_ideas", []),
            "insights": self.knowledge.get("insights", []),
            "last_updated": self.knowledge.get("last_updated", "Nunca"),
        }
