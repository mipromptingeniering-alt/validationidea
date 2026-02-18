# Corregir generator_agent.py
with open('agents/generator_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Reemplazar líneas problemáticas
content = content.replace(
    "content = content.split('```json').split('```').strip()[1]",
    "content = content.split('```json')[1].split('```')[0].strip()"
)
content = content.replace(
    "content = content.split('```').split('```')[0].strip()",
    "content = content.split('```')[1].split('```')[0].strip()"
)

with open('agents/generator_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

# Corregir critic_agent.py
with open('agents/critic_agent.py', 'r', encoding='utf-8') as f:
    content = f.read()

content = content.replace(
    "content = content.split('```json').split('```').strip()[1]",
    "content = content.split('```json')[1].split('```')[0].strip()"
)
content = content.replace(
    "content = content.split('```').split('```')[0].strip()",
    "content = content.split('```')[1].split('```')[0].strip()"
)

with open('agents/critic_agent.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ Corregido completamente")
