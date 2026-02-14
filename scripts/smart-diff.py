import difflib
import os
from colorama import init, Fore, Style

init(autoreset=True)

def show_diff(file1_content, file2_content, file_name=""):
    """Muestra diff inteligente entre dos versiones"""
    
    lines1 = file1_content.splitlines(keepends=True)
    lines2 = file2_content.splitlines(keepends=True)
    
    diff = difflib.unified_diff(
        lines1,
        lines2,
        fromfile=f"{file_name} (antes)",
        tofile=f"{file_name} (después)",
        lineterm=''
    )
    
    print(f"\n{'='*60}")
    print(f"DIFF: {file_name}")
    print(f"{'='*60}\n")
    
    changes_count = {'added': 0, 'removed': 0, 'context': 0}
    
    for line in diff:
        if line.startswith('+++') or line.startswith('---'):
            print(Fore.CYAN + line)
        elif line.startswith('@@'):
            print(Fore.MAGENTA + line)
        elif line.startswith('+'):
            print(Fore.GREEN + line)
            changes_count['added'] += 1
        elif line.startswith('-'):
            print(Fore.RED + line)
            changes_count['removed'] += 1
        else:
            print(line)
            changes_count['context'] += 1
    
    print(f"\n{Fore.YELLOW}Resumen:")
    print(f"{Fore.GREEN}  +{changes_count['added']} líneas añadidas")
    print(f"{Fore.RED}  -{changes_count['removed']} líneas eliminadas")
    print(f"{Fore.WHITE}  {changes_count['context']} líneas contexto\n")

def compare_files(file_path, checkpoint_id):
    """Compara archivo actual con versión en checkpoint"""
    
    checkpoint_file = f".checkpoints/{checkpoint_id}/{file_path}"
    
    if not os.path.exists(file_path):
        print(f"❌ Archivo actual no existe: {file_path}")
        return
    
    if not os.path.exists(checkpoint_file):
        print(f"❌ Archivo en checkpoint no existe: {checkpoint_file}")
        return
    
    with open(file_path, 'r', encoding='utf-8') as f:
        current_content = f.read()
    
    with open(checkpoint_file, 'r', encoding='utf-8') as f:
        checkpoint_content = f.read()
    
    show_diff(checkpoint_content, current_content, file_path)

def generate_smart_diff(old_code, new_code, context_lines=3):
    """Genera diff inteligente mostrando solo cambios relevantes"""
    
    old_lines = old_code.splitlines()
    new_lines = new_code.splitlines()
    
    diff = list(difflib.unified_diff(
        old_lines,
        new_lines,
        lineterm='',
        n=context_lines
    ))
    
    if not diff:
        return "✅ No hay cambios"
    
    # Agrupar cambios
    changes = []
    current_change = []
    
    for line in diff:
        if line.startswith('@@'):
            if current_change:
                changes.append(current_change)
            current_change = [line]
        elif line.startswith(('+', '-', ' ')):
            current_change.append(line)
    
    if current_change:
        changes.append(current_change)
    
    # Formatear output
    output = []
    
    for i, change in enumerate(changes, 1):
        output.append(f"\n### Cambio {i}")
        output.append("```diff")
        output.extend(change)
        output.append("```")
    
    return "\n".join(output)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 3:
        print("Uso:")
        print("  python smart-diff.py <archivo> <checkpoint_id>")
        print("\nEjemplo:")
        print("  python smart-diff.py agents/generator_agent.py checkpoint_20260214_134200")
    else:
        compare_files(sys.argv[1], sys.argv[2])
