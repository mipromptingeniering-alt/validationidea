"""
Verifica los nombres reales de los campos en Notion
"""
import os
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DATABASE_ID = "308313aca133809cb9fde119be25681d"

try:
    database = notion.databases.retrieve(database_id=DATABASE_ID)
    properties = database.get("properties", {})
    
    print("📊 CAMPOS REALES EN NOTION:")
    print("="*60)
    for prop_name, prop_data in properties.items():
        prop_type = prop_data.get("type", "unknown")
        print(f"  • {prop_name} ({prop_type})")
    
    print("\n" + "="*60)
    print(f"Total: {len(properties)} campos")
    
except Exception as e:
    print(f"❌ Error: {e}")