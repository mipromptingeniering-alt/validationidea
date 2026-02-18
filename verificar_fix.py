print("=== VERIFICANDO generator_agent.py ===")
with open('agents/generator_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
problemas = []
for i, line in enumerate(lines, 1):
    if ".split('```json').split('```')" in line or ".split('```').split('```')" in line:
        problemas.append(f"Línea {i}: {line.strip()}")

if problemas:
    print("❌ TODAVÍA HAY DOBLE SPLIT():")
    for p in problemas:
        print(f"  {p}")
else:
    print("✅ No hay doble split()")

print("\n=== VERIFICANDO critic_agent.py ===")
with open('agents/critic_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
problemas = []
for i, line in enumerate(lines, 1):
    if ".split('```json').split('```')" in line or ".split('```').split('```')" in line:
        problemas.append(f"Línea {i}: {line.strip()}")

if problemas:
    print("❌ TODAVÍA HAY DOBLE SPLIT():")
    for p in problemas:
        print(f"  {p}")
else:
    print("✅ No hay doble split()")
