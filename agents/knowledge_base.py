import os
import json
import requests
from datetime import datetime

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_KB_PAGE = os.environ.get("NOTION_KB_PAGE_ID", "")

HEADERS_NOTION = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

KB_VACIA = {
    "top_ideas": [],
    "total_ideas": 0,
    "mejor_score": 0,
    "scores_lista": [],
    "verticales": {},
    "tipos": {},
    "patrones_ganadores": []
}

class KnowledgeBase:
    def __init__(self):
        self.ruta_local = os.path.join("data", "knowledge_base.json")
        self.kb = self._cargar()

    def _cargar(self):
        # 1. Intentar cargar local
        if os.path.exists(self.ruta_local):
            try:
                with open(self.ruta_local, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if data.get("total_ideas", 0) > 0:
                        print(f"[KB] ✅ Cargada local: {data['total_ideas']} ideas")
                        self._rellenar_defaults(data)
                        return data
            except Exception as e:
                print(f"[KB] ⚠️ Error cargando local: {e}")

        # 2. Intentar cargar desde Notion
        data = self._cargar_desde_notion()
        if data and data.get("total_ideas", 0) > 0:
            print(f"[KB] ✅ Cargada desde Notion: {data['total_ideas']} ideas")
            self._guardar_local(data)
            return data

        # 3. KB nueva
        print("[KB] 🆕 KB nueva iniciada")
        return dict(KB_VACIA)

    def _rellenar_defaults(self, data):
        for k, v in KB_VACIA.items():
            data.setdefault(k, v)

    def _cargar_desde_notion(self):
        if not NOTION_KB_PAGE:
            return None
        try:
            resp = requests.get(
                f"https://api.notion.com/v1/blocks/{NOTION_KB_PAGE}/children",
                headers=HEADERS_NOTION, timeout=10
            )
            if resp.status_code != 200:
                return None
            blocks = resp.json().get("results", [])
            for block in blocks:
                if block.get("type") == "code":
                    textos = block["code"]["rich_text"]
                    if textos:
                        contenido = textos[0]["text"]["content"]
                        data = json.loads(contenido)
                        self._rellenar_defaults(data)
                        return data
        except Exception as e:
            print(f"[KB] ⚠️ Error cargando Notion: {e}")
        return None

    def _guardar_en_notion(self):
        if not NOTION_KB_PAGE:
            return
        try:
            contenido = json.dumps(self.kb, ensure_ascii=False)[:1990]

            # Obtener bloques existentes
            resp = requests.get(
                f"https://api.notion.com/v1/blocks/{NOTION_KB_PAGE}/children",
                headers=HEADERS_NOTION, timeout=10
            )
            if resp.status_code == 200:
                blocks = resp.json().get("results", [])
                # Borrar bloques de código existentes
                for block in blocks:
                    if block.get("type") == "code":
                        requests.delete(
                            f"https://api.notion.com/v1/blocks/{block['id']}",
                            headers=HEADERS_NOTION, timeout=10
                        )

            # Crear nuevo bloque con JSON actualizado
            requests.patch(
                f"https://api.notion.com/v1/blocks/{NOTION_KB_PAGE}/children",
                headers=HEADERS_NOTION,
                json={"children": [{
                    "object": "block",
                    "type": "code",
                    "code": {
                        "rich_text": [{"type": "text", "text": {"content": contenido}}],
                        "language": "json"
                    }
                }]},
                timeout=10
            )
        except Exception as e:
            print(f"[KB] ⚠️ Error guardando Notion: {e}")

    def _guardar_local(self, data=None):
        os.makedirs("data", exist_ok=True)
        try:
            with open(self.ruta_local, "w", encoding="utf-8") as f:
                json.dump(data or self.kb, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[KB] ⚠️ Error guardando local: {e}")

    def _guardar(self):
        self._guardar_local()
        self._guardar_en_notion()

    def aprender(self, idea, score_generador):
        score  = idea.get("score_general", 0)
        nombre = idea.get("nombre", "?")
        vertical = idea.get("vertical", "").strip() or "Desconocido"
        tipo     = idea.get("tipo", "").strip() or "Desconocido"

        if tipo.lower() in ["desconocido", "", "none", "null"]:
            v = vertical.lower()
            if "app" in v:      tipo = "App móvil"
            elif "saas" in v:   tipo = "SaaS"
            elif "market" in v: tipo = "Marketplace"
            elif "web" in v:    tipo = "Web"
            elif "local" in v:  tipo = "Negocio local"
            else:               tipo = "SaaS"
            idea["tipo"] = tipo

        self.kb["total_ideas"] += 1
        self.kb["scores_lista"].append(round(score, 1))
        self.kb["scores_lista"] = self.kb["scores_lista"][-100:]

        if score > self.kb["mejor_score"]:
            self.kb["mejor_score"] = round(score, 1)

        if score >= 72:
            self.kb["verticales"][vertical] = self.kb["verticales"].get(vertical, 0) + 1
            self.kb["tipos"][tipo]          = self.kb["tipos"].get(tipo, 0) + 1

        if score >= 75:
            self.kb["top_ideas"].append({
                "nombre":   nombre,
                "vertical": vertical,
                "tipo":     tipo,
                "score":    round(score, 1),
                "fecha":    datetime.now().strftime("%d/%m/%Y")
            })
            self.kb["top_ideas"] = sorted(
                self.kb["top_ideas"], key=lambda x: x["score"], reverse=True
            )[:15]

        if score >= 82:
            self.kb["patrones_ganadores"].append({
                "vertical": vertical,
                "tipo":     tipo,
                "score":    round(score, 1)
            })
            self.kb["patrones_ganadores"] = self.kb["patrones_ganadores"][-20:]

        self._guardar()
        print(f"[KB] ✅ {nombre} | tipo={tipo} | vertical={vertical} | score={score:.1f} | total={self.kb['total_ideas']}")

    def get_contexto_para_generador(self):
        try:
            top5   = self.kb.get("top_ideas", [])[:5]
            patron = self.kb.get("patrones_ganadores", [])[:3]
            contexto = ""
            if top5:
                contexto += "🏆 MEJORES IDEAS (no repetir):\n"
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
        mejor_v    = max(verticales, key=verticales.get) if verticales else "N/A"
        tipos      = self.kb.get("tipos", {})
        mejor_t    = max(tipos, key=tipos.get) if tipos else "N/A"
        top        = self.kb.get("top_ideas", [])
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
