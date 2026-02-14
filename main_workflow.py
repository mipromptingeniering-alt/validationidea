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

# ============ CONFIGURACIÓN ============
IDEAS_FILE = 'data/ideas.json'
CACHE_FILE = 'data/cache.json'
CACHE_HOURS = 24

# ============ CACHE MANAGEMENT ============
def is_cache_valid():
    """Verifica si el cache es válido (<24h)"""
    if not os.path.exists(CACHE_FILE):
        return False
    
    try:
        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)
            last_run = datetime.fromisoformat(cache['last_run'])
            
            if datetime.now() - last_run < timedelta(hours=CACHE_HOURS):
                print(f"✅ Cache válido (última ejecución: {last_run.strftime('%Y-%m-%d %H:%M')})")
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
    """Actualiza trends virales si cache expiró (>6h)"""
    
    if not TRENDS_ENABLED:
        print("ℹ️  Trend Hunter no disponible")
        return
    
    try:
        if not trend_hunter_agent.is_cache_valid():
            print("\n🔍 Cache de trends expirado - actualizando...")
            print("⚠️  Esto puede tomar 2-3 minutos...")
            
            trend_hunter_agent.hunt_viral_opportunities()
            
            print("✅ Trends actualizados correctamente")
        else:
            print("✅ Trends actualizados recientemente (cache válido)")
    
    except Exception as e:
        print(f"⚠️  Error actualizando trends: {e}")
        print("   Continuando con generación normal...")

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
    
    # Añadir metadata
    idea['created_at'] = datetime.now().isoformat()
    idea['status'] = 'pendiente'
    
    data['ideas'].append(idea)
    data['last_update'] = datetime.now().isoformat()
    data['total_ideas'] = len(data['ideas'])
    
    os.makedirs('data', exist_ok=True)
    
    with open(IDEAS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    print(f"💾 Idea guardada en {IDEAS_FILE}")

# ============ WORKFLOW PRINCIPAL ============
def print_header():
    """Imprime header del workflow"""
    print("\n" + "="*80)
    print("🚀 CHET THIS - WORKFLOW DE GENERACIÓN DE IDEAS")
    print("="*80)
    print(f"📅 Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)

def main():
    """Workflow principal"""
    
    print_header()
    
    # 1. Verificar cache
    if is_cache_valid():
        print("\n⏭️  Ejecución reciente detectada - workflow cancelado")
        print("   (Para forzar ejecución, elimina data/cache.json)")
        return
    
    print("\n▶️  Iniciando workflow completo...")
    
    # 2. 🔥 Actualizar trends virales (si está habilitado)
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
        print("\n❌ No se pudo generar idea - abortando workflow")
        return
    
    print(f"\n✅ Idea generada: {idea['nombre']}")
    
    # Mostrar si es viral
    if idea.get('viral_score'):
        print(f"   🔥 VIRAL - Score: {idea['viral_score']}/100")
        print(f"   {idea.get('urgency', 'N/A')} - Ventana: {idea.get('window', 'N/A')}")
    
    # 4. Investigar idea
    print("\n" + "-"*80)
    print("PASO 3: INVESTIGAR IDEA")
    print("-"*80)
    
    research = researcher_agent.research(idea)
    
    if not research:
        print("\n⚠️  Investigación falló - guardando idea sin research")
    else:
        print(f"\n✅ Investigación completada")
        idea['research'] = research
    
    # 5. Guardar idea
    print("\n" + "-"*80)
    print("PASO 4: GUARDAR IDEA")
    print("-"*80)
    
    save_idea(idea)
    
    # 6. Actualizar cache
    update_cache()
    
    # 7. Resumen final
    print("\n" + "="*80)
    print("✅ WORKFLOW COMPLETADO CON ÉXITO")
    print("="*80)
    print(f"\n📦 Producto: {idea['nombre']}")
    print(f"💰 Precio: €{idea['precio_sugerido']}")
    print(f"⏱️  Tiempo: {idea['tiempo_estimado']}")
    print(f"💵 Revenue 6m: {idea['revenue_6_meses']}")
    
    if idea.get('viral_score'):
        print(f"\n🔥 OPORTUNIDAD VIRAL:")
        print(f"   Score: {idea['viral_score']}/100")
        print(f"   Urgencia: {idea['urgency']}")
        print(f"   Ventana: {idea['window']}")
        print(f"   Fuente: {idea.get('source_type', 'N/A')}")
    
    print(f"\n📁 Guardado en: {IDEAS_FILE}")
    print(f"📊 Total ideas en sistema: {len(load_ideas()['ideas'])}")
    print("\n" + "="*80)

if __name__ == "__main__":
    main()
