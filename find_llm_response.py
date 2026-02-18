import re

with open('agents/generator_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()
    
# Buscar donde se hace el API call
matches = re.finditer(r'(client\.chat\.completions\.create.*?)', content, re.DOTALL)

print("=== LLAMADAS A GROQ API ===")
for i, match in enumerate(matches, 1):
    start = match.start()
    lines_before = content[:start].count('\n')
    print(f"\nLínea aproximada {lines_before}:")
    print(match.group(1)[:200])

# Buscar donde se procesa la respuesta
response_matches = re.finditer(r'(response\.(choices|content).*?)[\n;]', content)
print("\n\n=== PROCESAMIENTO DE RESPUESTA ===")
for match in response_matches:
    start = match.start()
    lines_before = content[:start].count('\n')
    print(f"Línea {lines_before}: {match.group(1)}")
