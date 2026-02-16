"""
Notion Sync Agent - Sincronización correcta a base de datos real
✅ Mapeo exacto a las 21 columnas que existen en tu Notion
"""
import os
from datetime import datetime
from notion_client import Client

DATABASE_ID = "308313aca133800981cfc48f32c52146"

def sync_idea_to_notion(idea):
    """Sincroniza idea completa a Notion"""
    try:
        notion = Client(auth=os.environ.get("NOTION_TOKEN"))
        
        print(f"📤 Sincronizando '{idea.get('nombre', 'Sin nombre')}' a Notion...")
        
        # Helper para textos
        def text_prop(value):
            if not value:
                return {"rich_text": []}
            return {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
        
        # Determinar emoji
        score = idea.get('score_critico', 0)
        if score >= 90:
            emoji = "💎"
        elif score >= 85:
            emoji = "⭐"
        elif score >= 80:
            emoji = "🔥"
        else:
            emoji = "💡"
        
        # Propiedades base
        properties = {
            "Name": {
                "title": [{"text": {"content": f"{emoji} {idea.get('nombre', 'Sin título')[:95]}"}}]
            }
        }
        
        # Mapeo de campos textuales
        text_fields = {
            "Description": idea.get("descripcion"),
            "Problem": idea.get("problema"),
            "Solution": idea.get("solucion"),
            "Target": idea.get("publico_objetivo") or idea.get("target"),
            "Business": idea.get("modelo_negocio"),
            "MVP": idea.get("mvp"),
            "Value": idea.get("propuesta_valor"),
            "Metrics": idea.get("metricas_clave") or idea.get("metricas"),
            "Risks": idea.get("riesgos"),
            "Marketing": idea.get("canales_marketing") or idea.get("estrategia_marketing"),
            "NextSteps": idea.get("proximos_pasos"),
            "Research": idea.get("research_summary") or "",
        }
        
        for field_name, field_value in text_fields.items():
            if field_value:
                properties[field_name] = text_prop(field_value)
        
        # Critique fields
        critique = idea.get("critique", {})
        if critique.get("puntos_fuertes"):
            strengths = "\n• ".join(critique["puntos_fuertes"])
            properties["Strengths"] = text_prop(strengths)
        
        if critique.get("puntos_debiles"):
            weaknesses = "\n• ".join(critique["puntos_debiles"])
            properties["Weaknesses"] = text_prop(weaknesses)
        
        # Report generado
        report_lines = [
            f"📊 ANÁLISIS COMPLETO - {idea.get('nombre', 'Sin nombre')}",
            "",
            f"🎯 Score Crítico: {idea.get('score_critico', 0)}/100",
            f"🔥 Score Viral: {idea.get('viral_score', idea.get('score_viral', 0))}/100",
            f"📈 Score Generador: {idea.get('score_generador', 0)}/100",
            "",
            "✅ FORTALEZAS:",
        ]
        
        if critique.get("puntos_fuertes"):
            for punto in critique["puntos_fuertes"][:3]:
                report_lines.append(f"  • {punto}")
        
        report_lines.append("")
        report_lines.append("⚠️ DEBILIDADES:")
        
        if critique.get("puntos_debiles"):
            for punto in critique["puntos_debiles"][:3]:
                report_lines.append(f"  • {punto}")
        
        properties["Report"] = text_prop("\n".join(report_lines))
        
        # Scores numéricos
        properties["ScoreGen"] = {"number": int(idea.get("score_generador", 0))}
        properties["ScoreCritic"] = {"number": int(idea.get("score_critico", 0))}
        properties["ScoreViral"] = {"number": int(idea.get("viral_score", idea.get("score_viral", 0)))}
        
        # Fecha
        properties["Date"] = {"date": {"start": idea.get("fecha") or datetime.now().isoformat()}}
        
        # Tags
        tags = []
        score_critico = idea.get("score_critico", 0)
        
        if score_critico >= 90:
            tags.append({"name": "💎 Excepcional"})
        elif score_critico >= 85:
            tags.append({"name": "⭐ Premium"})
        elif score_critico >= 80:
            tags.append({"name": "🔥 Calidad"})
        
        if idea.get("viral_score", 0) >= 85:
            tags.append({"name": "🚀 Viral"})
        
        if idea.get("riesgos") and "bajo" in str(idea.get("riesgos")).lower():
            tags.append({"name": "✅ Bajo Riesgo"})
        
        if tags:
            properties["Tags"] = {"multi_select": tags}
        
        # Crear página
        page = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
        
        print(f"✅ Sincronizado: {page['url']}")
        return page
        
    except Exception as e:
        print(f"❌ Error Notion: {e}")
        import traceback
        traceback.print_exc()
        return None

if __name__ == "__main__":
    # Test con idea mínima
    test_idea = {
        "nombre": "Test Product",
        "descripcion": "Descripción de prueba",
        "problema": "Problema a resolver",
        "score_critico": 85,
        "fecha": datetime.now().isoformat()
    }
    sync_idea_to_notion(test_idea)