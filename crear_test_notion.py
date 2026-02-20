codigo = """
import os
import sys
import requests

env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
env_vars = {}

if os.path.exists(env_path):
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, val = line.split("=", 1)
                env_vars[key.strip()] = val.strip()
    print("OK .env encontrado")
    print("Variables: " + str(list(env_vars.keys())))
else:
    print("ERROR .env no encontrado en: " + env_path)
    sys.exit(1)

TOKEN = env_vars.get("NOTION_TOKEN", "")
DB_ID = env_vars.get("NOTION_DATABASE_ID", "308313aca133800981cfc48f32c52146")

print("")
print("TOKEN: " + (TOKEN[:20] + "..." if TOKEN else "VACIO"))
print("DB_ID: " + DB_ID)
print("")

if not TOKEN:
    print("ERROR NOTION_TOKEN vacio")
    sys.exit(1)

HEADERS = {
    "Authorization": "Bearer " + TOKEN,
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28",
}

print("TEST 1: Token valido?")
r = requests.get("https://api.notion.com/v1/users/me", headers=HEADERS, timeout=10)
print("Status: " + str(r.status_code))
if r.status_code == 200:
    data = r.json()
    print("OK Token valido. Bot: " + str(data.get("name", "N/A")))
else:
    print("ERROR Token invalido: " + r.text[:200])
    print("Regenera en: https://www.notion.so/my-integrations")
    sys.exit(1)

print("")
print("TEST 2: Bases de datos accesibles?")
r2 = requests.post(
    "https://api.notion.com/v1/search",
    headers=HEADERS,
    json={"filter": {"value": "database", "property": "object"}, "page_size": 20},
    timeout=10
)
print("Status: " + str(r2.status_code))
if r2.status_code == 200:
    results = r2.json().get("results", [])
    print("Bases de datos encontradas: " + str(len(results)))
    for db in results:
        title_list = db.get("title", [])
        title = title_list[0]["text"]["content"] if title_list else "Sin nombre"
        db_id_clean = db["id"].replace("-", "")
        match = " <-- ESTA ES TU BD" if db_id_clean == DB_ID.replace("-", "") else ""
        print("  - " + title + ": " + db_id_clean + match)
    if not results:
        print("NINGUNA - integracion sin acceso")
        print("Solucion: Notion -> BD -> tres puntos -> Connections -> anade integracion")

print("")
print("TEST 3: Acceso directo a la BD?")
r3 = requests.post(
    "https://api.notion.com/v1/databases/" + DB_ID + "/query",
    headers=HEADERS,
    json={"page_size": 1},
    timeout=10
)
print("Status: " + str(r3.status_code))
if r3.status_code == 200:
    print("PERFECTO - Base de datos accesible. Notion funciona.")
else:
    print("ERROR: " + r3.text[:400])
"""

with open("test_notion.py", "w", encoding="utf-8") as f:
    f.write(codigo.strip())

print("test_notion.py creado. Ejecuta: python test_notion.py")
