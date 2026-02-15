"""
Notion Sync Agent: versión mejorada con emojis y análisis completo
"""
import os
import json
from notion_client import Client
from datetime import datetime

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = "308313ac-a133-8009-81cf-c48f32c52146"

def sync_idea_to_notion(idea):
    """Sincroniza idea completa a Notion con análisis de competencia"""
    
    print(f"📤 Sincronizando '{idea.get('nombre', 'Sin nombre')}' a Notion...")
    
    # Analizar competencia y estimación
    from agents import competition_agent, estimation_agent
    
    competition = competition_agent.analyze_competition(idea)
    estimation = estimation_agent.estimate_project(idea)
    
    # Determinar emoji según categoría y scores
    emoji = get_emoji(idea)
    
    # Reporte técnico MEJORADO
    report = generate_enhanced_report(idea, competition, estimation)
    
    # Propiedades
    properties = {
        "Name": {"title": [{"text": {"content": f"{emoji} {idea.get('nombre', 'Untitled')[:95]}"}}]},
    }
    
    def add_text(key, value):
        if value:
            properties[key] = {"rich_text": [{"text": {"content": str(value)[:2000]}}]}
    
    add_text("Description", idea.get("descripcion"))
    add_text("Problem", idea.get("problema"))
    add_text("Solution", idea.get("solucion"))
    add_text("Target", idea.get("publico_objetivo"))
    add_text("Business", idea.get("modelo_negocio"))
    add_text("MVP", idea.get("mvp"))
    add_text("Value", idea.get("propuesta_valor"))
    add_text("Metrics", idea.get("metricas_clave"))
    add_text("Risks", idea.get("riesgos"))
    add_text("Marketing", idea.get("canales_marketing"))
    add_text("NextSteps", idea.get("proximos_pasos"))
    add_text("Report", report)
    
    # Números
    properties["ScoreGen"] = {"number": idea.get("score_generador", 0)}
    properties["ScoreCritic"] = {"number": idea.get("score_critico", 0)}
    properties["ScoreViral"] = {"number": idea.get("viral_score", 0)}
    
    # Crítica
    critique = idea.get("critique", {})
    if critique.get("puntos_fuertes"):
        add_text("Strengths", "\n• ".join(critique["puntos_fuertes"]))
    if critique.get("puntos_debiles"):
        add_text("Weaknesses", "\n• ".join(critique["puntos_debiles"]))
    
    # Research
    if idea.get("research"):
        add_text("Research", json.dumps(idea["research"], indent=2, ensure_ascii=False))
    
    # Fecha
    properties["Date"] = {"date": {"start": datetime.now().isoformat()}}
    
    # Tags mejorados
    tags = []
    if idea.get("viral_score", 0) >= 85:
        tags.append({"name": "🔥 Viral"})
    if idea.get("score_critico", 0) >= 85:
        tags.append({"name": "⭐ Quality"})
    if idea.get("score_critico", 0) >= 90:
        tags.append({"name": "💎 Premium"})
    
    if estimation and estimation.get("viabilidad_tecnica") == "Alta":
        tags.append({"name": "✅ Viable"})
    
    if competition and competition.get("riesgo_competitivo") == "Bajo":
        tags.append({"name": "🎯 Low Risk"})
    
    if tags:
        properties["Tags"] = {"multi_select": tags}
    
    # Crear página
    try:
        page = notion.pages.create(
            parent={"database_id": DATABASE_ID},
            properties=properties
        )
        print(f"✅ Sincronizado: {page['url']}")
        
        # Guardar para notificaciones
        idea['notion_url'] = page['url']
        idea['competition'] = competition
        idea['estimation'] = estimation
        
        return page
    except Exception as e:
        print(f"❌ Error: {e}")
        return None

def get_emoji(idea):
    """Selecciona emoji según categoría y score"""
    score = idea.get("score_critico", 0)
    viral = idea.get("viral_score", 0)
    
    if score >= 90:
        return "💎"
    elif score >= 85:
        return "⭐"
    elif viral >= 85:
        return "🔥"
    else:
        return "💡"

def generate_enhanced_report(idea, competition, estimation):
    """Genera reporte técnico completo con análisis"""
    
    report = f"""# 📊 TECHNICAL REPORT

## 🎯 OVERVIEW
Score: {idea.get('score_critico', 0)}/100 | Viral: {idea.get('viral_score', 0)}/100

{idea.get('descripcion', 'N/A')}

## 🔍 ANALYSIS
**Problem:** {idea.get('problema', 'N/A')}
**Solution:** {idea.get('solucion', 'N/A')}
**Target:** {idea.get('publico_objetivo', 'N/A')}

## 💼 BUSINESS MODEL
**Monetization:** {idea.get('modelo_negocio', 'N/A')}
**Value Prop:** {idea.get('propuesta_valor', 'N/A')}

## 🚀 EXECUTION PLAN
**MVP:** {idea.get('mvp', 'N/A')}
**KPIs:** {idea.get('metricas_clave', 'N/A')}
**Marketing:** {idea.get('canales_marketing', 'N/A')}
**Next 30 days:** {idea.get('proximos_pasos', 'N/A')}

"""
    
    # Añadir análisis de competencia
    if competition:
        report += f"""
## 🥊 COMPETITION ANALYSIS
**Competitive Risk:** {competition.get('riesgo_competitivo', 'Unknown')}
**Competitive Advantage:** {competition.get('ventaja_competitiva', 'N/A')}
**Entry Barriers:** {competition.get('barreras_entrada', 'N/A')}
**Recommended Niche:** {competition.get('nicho_recomendado', 'N/A')}

**Direct Competitors:**"""
        
        for comp in competition.get('competidores_directos', [])[:3]:
            report += f"\n• {comp.get('nombre', 'Unknown')} - {comp.get('diferenciador', 'N/A')}"
        
        if competition.get('competidores_indirectos'):
            report += f"\n\n**Indirect Competitors:** {', '.join(competition.get('competidores_indirectos', [])[:5])}"
    
    # Añadir estimación
    if estimation:
        report += f"""

## 💰 INVESTMENT & TIMELINE
**MVP Investment:** ${estimation.get('inversion_mvp_usd', 0):,} USD
**Development Time:** {estimation.get('tiempo_desarrollo_semanas', 0)} weeks
**Team Needed:** {', '.join(estimation.get('equipo_necesario', []))}
**Monthly Costs:** ${estimation.get('costos_mensuales_operacion', 0)}/mo
**Break-even:** {estimation.get('tiempo_breakeven_meses', 0)} months
**Technical Viability:** {estimation.get('viabilidad_tecnica', 'Unknown')}
**Complexity:** {estimation.get('complejidad', 'Unknown')}
"""
    
    # Añadir riesgos
    report += f"""
## ⚠️ RISKS
{idea.get('riesgos', 'Not identified')}

---
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}
"""
    
    return report