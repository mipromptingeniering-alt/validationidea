import re
with open('agents/critic_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
matches = re.finditer(r'(response\.(choices|content).*?)[\n;]', content)
print("=== PROCESAMIENTO DE RESPUESTA EN CRITIC ===")
for match in matches:
    start = match.start()
    lines_before = content[:start].count('\n')
    print(f"Línea {lines_before}: {match.group(1)}")
