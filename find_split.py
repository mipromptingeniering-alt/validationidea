import re

print("=== BUSCANDO .split() EN AGENTS ===\n")

for file in ['agents/generator_agent.py', 'agents/critic_agent.py']:
    with open(file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"\n{file}:")
    for i, line in enumerate(lines, 1):
        if '.split(' in line and 'import' not in line:
            print(f"  Línea {i}: {line.strip()}")
