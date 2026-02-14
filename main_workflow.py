import os
import json
import time
from datetime import datetime, timedelta
from agents import generator_agent, researcher_agent

# ============ TREND HUNTER INTEGRATION ============
try:
    from agents import trend_hunter_agent
    TRENDS_ENABLED = True
except ImportError:
    TRENDS_ENABLED = False

# ============ CONFIGURACIÃ“N ============
IDEAS_FILE = 'data/ideas.json'
CACHE_FILE = 'data/cache.json'
CACHE_HOURS = 24

# ============ CACHE MANAGEMENT ============
def is_cache_valid():
    """Verifica si el cache es vÃ¡lido (<24h)"""
    if not os.path.exists(CACHE_FILE):
        return False
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            last_run = datetime.fromisoformat(cache['last_run'])
            
            if datetime.now() - last_run < timedelta(hours=CACHE_HOURS):
                print(f"âœ… Cache vÃ¡lido (Ãºltima ejecuciÃ³n: {last_run.strftime('%Y-%m-%d %H:%M')})")
                return True
    except:
        pass
    
    return False

def update_cache():
    """Actualiza timestamp del cache"""
    os.makedirs('data', exist_ok=True)
    
    cache = {
        'last_run': datetime.now().isoformat(),
        'next_run': (datetime.now() + timedelta(hours=CACHE_HOURS)).isoformat()
    }
    
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, indent=2)

# ============ TRENDS UPDATE ============
def update_viral_trends():
    """Actualiza trends virales si cache expirÃ³ (>6h)"""
    
    if not TRENDS_ENABLED:
        print("â„¹ï¸  Trend Hunter no disponible")
        return
    
    try:
        if not trend_hunter_agent.is_cache_valid():
            print("\nðŸ” Cache de trends expirado - actualizando...")
            print("âš ï¸  Esto puede tomar 2-3 minutos...")
            
            trend_hunter_agent.hunt_viral_opportunities()
            
            print("âœ… Trends actualizados correctamente")
        else:
            print("âœ… Trends actualizados recientemente (cache vÃ¡lido)")
    
    except Exception as e:
        print(f"âš ï¸  Error actualizando trends: {e}")
        print("   Continuando con generaciÃ³n normal...")

# ============ IDEAS MANAGEMENT ============
def load_ideas():
    """Carga ideas desde JSON"""
    if os.path.exists(IDEAS_FILE):
        try:
            with open(IDEAS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {'ideas': [], 'last_update': datetime.now().isoformat()}
    
    return {'ideas': [], 'last_update': datetime.now().isoformat()}

def save_idea(idea):
    """Guarda nueva idea en JSON"""
    data = load_ideas()
    
    # AÃ±adir metadata
    idea['created_at'] = datetime.now().isoformat()
    idea['status'] = 'pendiente'
    
    data['ideas'].append(idea)
    data['last_update'] = datetime.now().isoformat()
    data['total_ideas'] = len(data['ideas'])
    
    os.makedirs('data', exist_ok=True)
    
    with open(IDEAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"ðŸ’¾ Idea guardada en {IDEAS_FILE}")

# ============ WORKFLOW PRINCIPAL ============
def print_header():
    """Imprime header del workflow"""
    print("\n" + "="*80)
    print("ðŸš€ CHET THIS - WORKFLOW DE GENERACIÃ“N DE IDEAS")
    print("="*80)
    print(f"ðŸ“… Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

def main():
    """Workflow principal"""
    
    print_header()
    
    # 1. Verificar cache
    if is_cache_valid():
        print("\nâ­ï¸  EjecuciÃ³n reciente detectada - workflow cancelado")
        print("   (Para forzar ejecuciÃ³n, elimina data/cache.json)")
        return
    
    print("\nâ–¶ï¸  Iniciando workflow completo...")
    
    # 2. ðŸ”¥ Actualizar trends virales (si estÃ¡ habilitado)
    print("\n" + "-"*80)
    print("PASO 1: ACTUALIZAR TENDENCIAS VIRALES")
    print("-"*80)
    
    update_viral_trends()
    
    # 3. Generar idea
    print("\n" + "-"*80)
    print("PASO 2: GENERAR IDEA DE PRODUCTO")
    print("-"*80)
    
    idea = generator_agent.generate()
    
    if not idea:
        print("\nâŒ No se pudo generar idea - abortando workflow")
        return
    
    print(f"\nâœ… Idea generada: {idea['nombre']}")
    
    # Mostrar si es viral
    if idea.get('viral_score'):
        print(f"   ðŸ”¥ VIRAL - Score: {idea['viral_score']}/100")
        print(f"   {idea.get('urgency', 'N/A')} - Ventana: {idea.get('window', 'N/A')}")
    
    # 4. Investigar idea
    print("\n" + "-"*80)

    # -------------------------------------------------------------------------
    # PASO 3: CRITICAR IDEA
    # -------------------------------------------------------------------------
    print("\n" + "-"*80)
    print("PASO 3: CRITICAR IDEA")
    print("-"*80)
    
    from agents import critic_agent
    
    critique_result = critic_agent.critique(idea)
    
    if not critique_result:
        print("⚠️ Crítica falló - usando scores por defecto")
        critique_result = {
            'score_critico': idea.get('score_generador', 75),
            'puntos_fuertes': ['Pendiente de evaluar'],
            'puntos_debiles': ['Pendiente de evaluar'],
            'resumen': 'Aprobada por defecto'
        }
    
    score_critico = critique_result.get('score_critico', 75)
    print(f"📊 Score Crítico: {score_critico}/100")
    print(f"✅ Puntos fuertes: {', '.join(critique_result.get('puntos_fuertes', []))}")
    print(f"⚠️ Puntos débiles: {', '.join(critique_result.get('puntos_debiles', []))}")
    
    # Añadir crítica a la idea
    idea['score_critico'] = score_critico
    idea['critique'] = critique_result
    
    # Decidir si publicar
    config = critic_agent.load_config()
    should_publish = critic_agent.decide_publish(idea, critique_result, config)
    
    if not should_publish:
        print(f"❌ Idea RECHAZADA - Score {score_critico} muy bajo")
        print("   No se guardará ni notificará")
        return
    
    print(f"✅ Idea APROBADA para continuar")

    # -------------------------------------------------------------------------
    # PASO 4: INVESTIGAR IDEA (antes PASO 3)
    print("PASO 4: INVESTIGAR IDEA")
    print("-"*80)
    
    research = researcher_agent.research(idea)
    
    if not research:
        print("\nâš ï¸  InvestigaciÃ³n fallÃ³ - guardando idea sin research")
    else:
        print(f"\nâœ… InvestigaciÃ³n completada")
        idea['research'] = research
    
    # 5. Guardar idea
    print("\n" + "-"*80)
    print("PASO 5: GUARDAR IDEA")
    print("-"*80)
    
    save_idea(idea)
    # 5. Notificar Telegram
    print("\n" + "-"*80)
    print("PASO 6: NOTIFICAR TELEGRAM")
    print("-"*80)
    
    try:
        from agents import telegram_notifier
        
        # Preparar critique
        critique = {
            'score_critico': idea.get('viral_score', idea.get('score_generador', 85))
        }
        
        # URLs
        landing_url = "https://github.com/mipromptingeniering-alt/validationidea/blob/main/data/ideas.json"
        report_url = "https://github.com/mipromptingeniering-alt/validationidea/blob/main/data/viral-trends.json"
        
        # Llamar función correcta
        success = telegram_notifier.send_telegram_notification(
            idea=idea,
            critique=critique,
            landing_url=landing_url,
            report_url=report_url
        )
        
        if success:
            print("✅ Notificación enviada a Telegram")
        else:
            print("⚠️ No se pudo enviar notificación")
    
    except Exception as e:
        print(f"⚠️ Error Telegram: {e}")
    
    # 6. Actualizar cache
    update_cache()
    
    # 7. Resumen final
    print("\n" + "="*80)
    print("âœ… WORKFLOW COMPLETADO CON Ã‰XITO")
    print("="*80)
    print(f"\nðŸ“¦ Producto: {idea['nombre']}")
    print(f"ðŸ’° Precio: â‚¬{idea['precio_sugerido']}")
    print(f"â±ï¸  Tiempo: {idea['tiempo_estimado']}")
    print(f"ðŸ’µ Revenue 6m: {idea['revenue_6_meses']}")
    
    if idea.get('viral_score'):
        print(f"\nðŸ”¥ OPORTUNIDAD VIRAL:")
        print(f"   Score: {idea['viral_score']}/100")
        print(f"   Urgencia: {idea['urgency']}")
        print(f"   Ventana: {idea['window']}")
        print(f"   Fuente: {idea.get('source_type', 'N/A')}")
    
    print(f"\nðŸ“ Guardado en: {IDEAS_FILE}")
    print(f"ðŸ“Š Total ideas en sistema: {len(load_ideas()['ideas'])}")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
