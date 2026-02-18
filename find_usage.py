with open('agents/generator_agent.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines, 1):
    if 'fix_llm_encoding' in line and 'import' not in line:
        print(f"Línea {i}: {line.strip()}")
        if i < len(lines):
            print(f"Línea {i+1}: {lines[i].strip()}")
