import os
import ast
import json
from collections import defaultdict
from datetime import datetime

def scan_project():
    """Escanea proyecto completo buscando problemas"""
    
    print("\n🔍 AUDITORÍA DE CÓDIGO\n")
    print("="*60)
    
    issues = {
        "unused_files": [],
        "dead_code": [],
        "unused_imports": [],
        "duplicate_code": [],
        "large_files": [],
        "missing_docstrings": [],
        "empty_files": []
    }
    
    # Directorios a escanear
    scan_dirs = ['agents', 'scripts', 'config']
    
    all_files = []
    for directory in scan_dirs:
        if os.path.exists(directory):
            for root, dirs, files in os.walk(directory):
                for file in files:
                    if file.endswith('.py'):
                        all_files.append(os.path.join(root, file))
    
    print(f"📊 Archivos Python encontrados: {len(all_files)}\n")
    
    # 1. Detectar archivos vacíos
    print("1️⃣  Buscando archivos vacíos...")
    for file in all_files:
        with open(file, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content or len(content) < 50:
                issues['empty_files'].append(file)
                print(f"   ⚠️  {file} - {len(content)} chars")
    
    # 2. Detectar archivos grandes
    print("\n2️⃣  Buscando archivos muy grandes (>1000 líneas)...")
    for file in all_files:
        with open(file, 'r', encoding='utf-8') as f:
            lines = len(f.readlines())
            if lines > 1000:
                issues['large_files'].append({
                    'file': file,
                    'lines': lines
                })
                print(f"   ⚠️  {file} - {lines} líneas")
    
    # 3. Detectar imports sin usar
    print("\n3️⃣  Buscando imports sin usar...")
    for file in all_files:
        unused = find_unused_imports(file)
        if unused:
            issues['unused_imports'].append({
                'file': file,
                'imports': unused
            })
            print(f"   ⚠️  {file}")
            for imp in unused:
                print(f"      - {imp}")
    
    # 4. Detectar funciones sin docstrings
    print("\n4️⃣  Buscando funciones sin docstrings...")
    for file in all_files:
        missing = find_missing_docstrings(file)
        if missing:
            issues['missing_docstrings'].append({
                'file': file,
                'functions': missing
            })
            print(f"   ⚠️  {file} - {len(missing)} funciones")
    
    # 5. Detectar posibles duplicados
    print("\n5️⃣  Buscando código duplicado...")
    duplicates = find_duplicate_code(all_files)
    if duplicates:
        issues['duplicate_code'] = duplicates
        for dup in duplicates[:3]:  # Mostrar top 3
            print(f"   ⚠️  {dup['code'][:50]}... aparece {dup['count']} veces")
    
    # Guardar reporte
    report = {
        "timestamp": datetime.now().isoformat(),
        "files_scanned": len(all_files),
        "issues": issues,
        "summary": {
            "empty_files": len(issues['empty_files']),
            "large_files": len(issues['large_files']),
            "unused_imports": len(issues['unused_imports']),
            "missing_docstrings": len(issues['missing_docstrings']),
            "duplicate_code": len(issues['duplicate_code'])
        }
    }
    
    os.makedirs('reports', exist_ok=True)
    report_file = 'reports/code-audit.json'
    
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN AUDITORÍA")
    print("="*60)
    print(f"✅ Archivos escaneados: {len(all_files)}")
    print(f"⚠️  Archivos vacíos: {report['summary']['empty_files']}")
    print(f"⚠️  Archivos grandes: {report['summary']['large_files']}")
    print(f"⚠️  Imports sin usar: {report['summary']['unused_imports']}")
    print(f"⚠️  Sin docstrings: {report['summary']['missing_docstrings']}")
    print(f"⚠️  Código duplicado: {report['summary']['duplicate_code']}")
    print(f"\n📄 Reporte completo: {report_file}\n")
    
    # Sugerencias limpieza
    suggest_cleanup(issues)
    
    return report

def find_unused_imports(file):
    """Detecta imports que no se usan"""
    try:
        with open(file, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        imports = set()
        used_names = set()
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
            elif isinstance(node, ast.Name):
                used_names.add(node.id)
        
        unused = [imp for imp in imports if imp not in used_names]
        return unused
    
    except:
        return []

def find_missing_docstrings(file):
    """Detecta funciones sin docstrings"""
    try:
        with open(file, 'r', encoding='utf-8') as f:
            tree = ast.parse(f.read())
        
        missing = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if not ast.get_docstring(node):
                    missing.append(node.name)
        
        return missing
    
    except:
        return []

def find_duplicate_code(files):
    """Detecta bloques código duplicado"""
    code_blocks = defaultdict(list)
    
    for file in files:
        try:
            with open(file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Buscar bloques de 5+ líneas
            for i in range(len(lines) - 5):
                block = ''.join(lines[i:i+5]).strip()
                if len(block) > 50:  # Ignorar bloques pequeños
                    code_blocks[block].append(file)
        except:
            continue
    
    duplicates = []
    for code, files_list in code_blocks.items():
        if len(files_list) > 1:
            duplicates.append({
                'code': code,
                'count': len(files_list),
                'files': files_list
            })
    
    return sorted(duplicates, key=lambda x: x['count'], reverse=True)

def suggest_cleanup(issues):
    """Sugiere acciones de limpieza"""
    
    print("💡 SUGERENCIAS LIMPIEZA:\n")
    
    if issues['empty_files']:
        print("🗑️  Eliminar archivos vacíos:")
        for file in issues['empty_files']:
            print(f"   rm {file}")
    
    if issues['unused_imports']:
        print("\n📦 Limpiar imports sin usar:")
        print("   python -m autoflake --remove-all-unused-imports --in-place agents/*.py scripts/*.py")
    
    if issues['large_files']:
        print("\n✂️  Refactorizar archivos grandes:")
        for item in issues['large_files']:
            print(f"   {item['file']} ({item['lines']} líneas) - considerar split")
    
    if issues['missing_docstrings']:
        print("\n📝 Añadir docstrings:")
        print("   Usar template: '''Brief description.\n\n   Args:\n       param: description\n\n   Returns:\n       description\n   '''")
    
    if issues['duplicate_code']:
        print("\n🔄 Refactorizar código duplicado:")
        print("   Extraer a funciones compartidas en utils.py")

def auto_cleanup():
    """Limpieza automática (solo acciones seguras)"""
    
    print("\n🤖 LIMPIEZA AUTOMÁTICA\n")
    
    confirm = input("¿Ejecutar limpieza automática? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Limpieza cancelada")
        return
    
    # 1. Eliminar archivos .pyc y __pycache__
    print("\n1️⃣  Eliminando archivos compilados...")
    os.system("find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null")
    os.system("find . -type f -name '*.pyc' -delete 2>/dev/null")
    print("   ✅ __pycache__ eliminados")
    
    # 2. Ordenar imports (requiere isort)
    print("\n2️⃣  Ordenando imports...")
    os.system("isort agents/ scripts/ 2>/dev/null || echo '   ⚠️  isort no instalado'")
    
    # 3. Formatear código (requiere black)
    print("\n3️⃣  Formateando código...")
    os.system("black agents/ scripts/ --line-length 100 2>/dev/null || echo '   ⚠️  black no instalado'")
    
    print("\n✅ Limpieza automática completada\n")


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'auto':
        auto_cleanup()
    else:
        scan_project()
