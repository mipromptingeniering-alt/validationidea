import os
import json
import subprocess
from datetime import datetime
import re

VERSION_FILE = 'VERSION.json'

def get_current_version():
    """Lee versión actual"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, 'r') as f:
            return json.load(f)
    
    return {
        "version": "1.0.0",
        "major": 1,
        "minor": 0,
        "patch": 0,
        "timestamp": datetime.now().isoformat(),
        "changelog": []
    }

def get_git_changes():
    """Obtiene cambios desde último commit"""
    try:
        # Files modificados
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1', 'HEAD'],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return []
        
        files = result.stdout.strip().split('\n')
        return [f for f in files if f]
    
    except:
        return []

def analyze_changes(files):
    """Analiza tipo de cambios"""
    
    change_type = {
        'breaking': False,
        'feature': False,
        'fix': False,
        'docs': False,
        'refactor': False
    }
    
    breaking_patterns = [
        'agents/',  # Cambios en agentes pueden romper workflow
        'main_workflow.py',
        'config/'
    ]
    
    feature_patterns = [
        'new',
        'add',
        'feature'
    ]
    
    for file in files:
        # Detectar breaking
        for pattern in breaking_patterns:
            if pattern in file:
                # Leer contenido para ver si es breaking
                if 'agents/' in file or 'main_workflow.py' in file:
                    change_type['breaking'] = True
        
        # Detectar features
        if any(p in file.lower() for p in feature_patterns):
            change_type['feature'] = True
        
        # Detectar fixes
        if 'fix' in file.lower() or 'bug' in file.lower():
            change_type['fix'] = True
        
        # Detectar docs
        if '.md' in file or 'doc' in file.lower():
            change_type['docs'] = True
    
    return change_type

def suggest_version_bump(change_type):
    """Sugiere qué versión incrementar"""
    
    if change_type['breaking']:
        return 'major', "⚠️  BREAKING CHANGE detectado - incrementar MAJOR"
    
    if change_type['feature']:
        return 'minor', "✨ Nueva feature detectada - incrementar MINOR"
    
    if change_type['fix']:
        return 'patch', "🔧 Fix detectado - incrementar PATCH"
    
    return 'patch', "📝 Cambios menores - incrementar PATCH"

def increment_version(version, bump_type):
    """Incrementa versión según tipo"""
    
    if bump_type == 'major':
        version['major'] += 1
        version['minor'] = 0
        version['patch'] = 0
    elif bump_type == 'minor':
        version['minor'] += 1
        version['patch'] = 0
    else:  # patch
        version['patch'] += 1
    
    version['version'] = f"{version['major']}.{version['minor']}.{version['patch']}"
    version['timestamp'] = datetime.now().isoformat()
    
    return version

def get_commit_message():
    """Obtiene último commit message"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True
        )
        return result.stdout.strip()
    except:
        return "No commit message"

def update_version_file(version, bump_type, reason, commit_msg):
    """Actualiza VERSION.json"""
    
    # Añadir al changelog
    changelog_entry = {
        "version": version['version'],
        "date": datetime.now().strftime('%Y-%m-%d'),
        "type": bump_type,
        "reason": reason,
        "commit": commit_msg[:100]
    }
    
    version['changelog'].insert(0, changelog_entry)
    
    # Mantener solo últimos 20 entries
    version['changelog'] = version['changelog'][:20]
    
    with open(VERSION_FILE, 'w') as f:
        json.dump(version, f, indent=2)
    
    print(f"\n✅ Versión actualizada: {version['version']}")
    print(f"📝 Razón: {reason}")
    print(f"💬 Commit: {commit_msg[:80]}")

def show_version_info(version):
    """Muestra info de versión actual"""
    
    print("\n" + "="*60)
    print(f"📦 VERSIÓN ACTUAL: {version['version']}")
    print("="*60)
    print(f"Actualizada: {version['timestamp'][:19]}")
    
    if version['changelog']:
        print(f"\n📋 ÚLTIMOS CAMBIOS:\n")
        for entry in version['changelog'][:5]:
            print(f"  v{entry['version']} ({entry['date']})")
            print(f"    {entry['type'].upper()}: {entry['reason']}")
            print(f"    └─ {entry['commit']}\n")

def auto_version():
    """Versionado automático basado en cambios"""
    
    print("\n🔍 Analizando cambios para versionado automático...\n")
    
    # Versión actual
    version = get_current_version()
    print(f"Versión actual: {version['version']}")
    
    # Cambios
    files = get_git_changes()
    
    if not files:
        print("⚠️  No hay cambios detectados")
        return version
    
    print(f"\n📁 Archivos modificados ({len(files)}):")
    for f in files[:10]:
        print(f"  - {f}")
    if len(files) > 10:
        print(f"  ... y {len(files) - 10} más")
    
    # Analizar
    change_type = analyze_changes(files)
    bump_type, reason = suggest_version_bump(change_type)
    
    print(f"\n💡 Sugerencia: {bump_type.upper()}")
    print(f"   {reason}")
    
    # Confirmar
    response = input("\n¿Incrementar versión? (yes/no): ")
    
    if response.lower() != 'yes':
        print("❌ Cancelado")
        return version
    
    # Incrementar
    version = increment_version(version, bump_type)
    commit_msg = get_commit_message()
    update_version_file(version, bump_type, reason, commit_msg)
    
    show_version_info(version)
    
    return version


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'show':
            version = get_current_version()
            show_version_info(version)
        elif sys.argv[1] == 'bump':
            bump_type = sys.argv[2] if len(sys.argv) > 2 else 'patch'
            version = get_current_version()
            version = increment_version(version, bump_type)
            commit_msg = get_commit_message()
            update_version_file(version, bump_type, f"Manual {bump_type} bump", commit_msg)
        else:
            auto_version()
    else:
        auto_version()
