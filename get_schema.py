import os
import requests

NOTION_TOKEN = os.environ.get('NOTION_TOKEN')
DATABASE_ID = "308313aca133809cb9fde119be25681d"

headers = {
    "Authorization": f"Bearer {NOTION_TOKEN}",
    "Notion-Version": "2022-06-28"
}

response = requests.get(
    f"https://api.notion.com/v1/databases/{DATABASE_ID}",
    headers=headers
)

if response.status_code == 200:
    db = response.json()
    print("\n📊 PROPIEDADES ENCONTRADAS EN TU DATABASE:\n")
    for prop_name, prop_data in db['properties'].items():
        print(f"  - {prop_name} ({prop_data['type']})")
else:
    print(f"❌ Error: {response.text}")