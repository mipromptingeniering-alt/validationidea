"""
Añade campos a Notion FORZADAMENTE
"""
import os
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = "308313aca133809cb9fde119be25681d"

print("🔍 Verificando acceso a base de datos...")

try:
    database = notion.databases.retrieve(database_id=DATABASE_ID)
    print(f"✅ Base de datos encontrada: {database.get('title', [{}])[0].get('plain_text', 'Sin nombre')}")
    
    # Definir campos COMPLETOS
    new_properties = {
        "Nombre": {"title": {}},
        "Descripción": {"rich_text": {}},
        "Problema": {"rich_text": {}},
        "Solución": {"rich_text": {}},
        "Público Objetivo": {"rich_text": {}},
        "Modelo Negocio": {"rich_text": {}},
        "MVP": {"rich_text": {}},
        "Propuesta Valor": {"rich_text": {}},
        "Métricas Clave": {"rich_text": {}},
        "Riesgos": {"rich_text": {}},
        "Canales Marketing": {"rich_text": {}},
        "Próximos Pasos": {"rich_text": {}},
        "Puntos Fuertes": {"rich_text": {}},
        "Puntos Débiles": {"rich_text": {}},
        "Análisis Completo": {"rich_text": {}},
        "Research": {"rich_text": {}},
        "Score Generador": {"number": {}},
        "Score Crítico": {"number": {}},
        "Viral Score": {"number": {}},
        "Fecha Creación": {"date": {}},
        "Tags": {"multi_select": {"options": [
            {"name": "🔥 Viral", "color": "red"},
            {"name": "⭐ Alta Calidad", "color": "yellow"},
            {"name": "Tecnología", "color": "blue"},
            {"name": "SaaS", "color": "green"}
        ]}}
    }
    
    print(f"\n📝 Añadiendo {len(new_properties)} campos...")
    
    # Actualizar base de datos
    updated = notion.databases.update(
        database_id=DATABASE_ID,
        properties=new_properties
    )
    
    print("✅ ¡CAMPOS AÑADIDOS!")
    
    # Verificar
    db_check = notion.databases.retrieve(database_id=DATABASE_ID)
    props = db_check.get("properties", {})
    print(f"\n📊 Verificación: {len(props)} campos en la base de datos")
    
    if len(props) > 0:
        print("\n✅ CAMPOS CREADOS:")
        for prop_name in props.keys():
            print(f"  • {prop_name}")
    else:
        print("\n❌ ERROR: Los campos NO se guardaron")
        print("⚠️ Verifica que tienes permisos de edición en la base de datos")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    print("\n💡 POSIBLES CAUSAS:")
    print("  1. El DATABASE_ID es incorrecto")
    print("  2. El token no tiene permisos de edición")
    print("  3. La base de datos fue eliminada")
    print("\n🔧 SOLUCIÓN:")
    print("  1. Ve a Notion y crea una nueva base de datos")
    print("  2. Comparte la BD con tu integración")
    print("  3. Copia el nuevo ID de la URL")