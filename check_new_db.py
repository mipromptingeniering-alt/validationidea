import os
from notion_client import Client

notion = Client(auth=os.getenv("NOTION_TOKEN"))
DB_ID = "061581aa-1a83-48a7-919f-6e88c1f8007a"

try:
    db = notion.databases.retrieve(database_id=DB_ID)
    props = db.get("properties", {})
    
    print(f"📊 Campos encontrados: {len(props)}")
    
    if len(props) > 0:
        print("\n✅ CAMPOS EXISTENTES:")
        for name in props.keys():
            print(f"  • {name}")
    else:
        print("\n⚠️ La BD está vacía. Añadiendo campos ahora...")
        
        # Añadir campos
        notion.databases.update(
            database_id=DB_ID,
            properties={
                "Name": {"title": {}},
                "Description": {"rich_text": {}},
                "Problem": {"rich_text": {}},
                "Solution": {"rich_text": {}},
                "Target": {"rich_text": {}},
                "Business": {"rich_text": {}},
                "MVP": {"rich_text": {}},
                "Value": {"rich_text": {}},
                "Metrics": {"rich_text": {}},
                "Risks": {"rich_text": {}},
                "Marketing": {"rich_text": {}},
                "NextSteps": {"rich_text": {}},
                "Strengths": {"rich_text": {}},
                "Weaknesses": {"rich_text": {}},
                "Report": {"rich_text": {}},
                "Research": {"rich_text": {}},
                "ScoreGen": {"number": {}},
                "ScoreCritic": {"number": {}},
                "ScoreViral": {"number": {}},
                "Date": {"date": {}},
                "Tags": {"multi_select": {"options": [
                    {"name": "Viral", "color": "red"},
                    {"name": "Quality", "color": "yellow"}
                ]}}
            }
        )
        
        print("✅ Campos añadidos con nombres EN INGLÉS")
        
        # Verificar de nuevo
        db2 = notion.databases.retrieve(database_id=DB_ID)
        props2 = db2.get("properties", {})
        print(f"\n📊 Ahora hay {len(props2)} campos")
        
except Exception as e:
    print(f"❌ Error: {e}")