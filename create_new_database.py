"""
Crea una nueva base de datos completa en Notion
"""
import os
import json
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_TOKEN"))

print("🔍 Buscando páginas disponibles...")

try:
    # Buscar páginas donde podemos crear la BD
    search = notion.search(filter={"property": "object", "value": "page"})
    
    pages = search.get("results", [])
    if not pages:
        print("❌ No se encontraron páginas")
        print("⚠️ Necesitas crear una página en Notion primero")
        exit(1)
    
    # Usar la primera página como parent
    parent_page = pages[0]
    print(f"✅ Usando página: {parent_page.get('id')}")
    
    print("\n🏗️ Creando base de datos 'Chet This - Ideas'...")
    
    # Definir estructura completa
    database = notion.databases.create(
        parent={"type": "page_id", "page_id": parent_page["id"]},
        title=[{"type": "text", "text": {"content": "💡 Chet This - Ideas"}}],
        properties={
            "Nombre": {
                "title": {}
            },
            "Descripción": {
                "rich_text": {}
            },
            "Problema": {
                "rich_text": {}
            },
            "Solución": {
                "rich_text": {}
            },
            "Público Objetivo": {
                "rich_text": {}
            },
            "Modelo Negocio": {
                "rich_text": {}
            },
            "MVP": {
                "rich_text": {}
            },
            "Propuesta Valor": {
                "rich_text": {}
            },
            "Métricas Clave": {
                "rich_text": {}
            },
            "Riesgos": {
                "rich_text": {}
            },
            "Canales Marketing": {
                "rich_text": {}
            },
            "Próximos Pasos": {
                "rich_text": {}
            },
            "Puntos Fuertes": {
                "rich_text": {}
            },
            "Puntos Débiles": {
                "rich_text": {}
            },
            "Análisis Completo": {
                "rich_text": {}
            },
            "Research": {
                "rich_text": {}
            },
            "Score Generador": {
                "number": {
                    "format": "number"
                }
            },
            "Score Crítico": {
                "number": {
                    "format": "number"
                }
            },
            "Viral Score": {
                "number": {
                    "format": "number"
                }
            },
            "Fecha Creación": {
                "date": {}
            },
            "Tags": {
                "multi_select": {
                    "options": [
                        {"name": "🔥 Viral", "color": "red"},
                        {"name": "⭐ Alta Calidad", "color": "yellow"},
                        {"name": "💡 Innovadora", "color": "orange"},
                        {"name": "🚀 SaaS", "color": "green"},
                        {"name": "💰 E-commerce", "color": "purple"},
                        {"name": "🤖 IA", "color": "pink"},
                        {"name": "📱 App", "color": "blue"}
                    ]
                }
            },
            "Estado": {
                "select": {
                    "options": [
                        {"name": "🆕 Nueva", "color": "blue"},
                        {"name": "🔍 En análisis", "color": "yellow"},
                        {"name": "✅ Aprobada", "color": "green"},
                        {"name": "🚀 En desarrollo", "color": "purple"},
                        {"name": "❌ Descartada", "color": "red"}
                    ]
                }
            }
        }
    )
    
    db_id = database["id"]
    db_url = database["url"]
    
    print("\n✅ ¡BASE DE DATOS CREADA!")
    print(f"\n🔗 URL: {db_url}")
    print(f"🆔 ID: {db_id}")
    
    # Guardar ID en archivo
    config = {
        "database_id": db_id,
        "database_url": db_url,
        "created_at": str(database.get("created_time", ""))
    }
    
    with open("notion_config.json", "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)
    
    print("\n📄 Configuración guardada en: notion_config.json")
    
    # Verificar campos
    props = database.get("properties", {})
    print(f"\n📊 {len(props)} campos creados:")
    for prop_name in props.keys():
        print(f"  ✅ {prop_name}")
    
    print("\n🎉 ¡TODO LISTO!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()