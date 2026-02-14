import os
import json
import subprocess
from datetime import datetime

VERSION_FILE = 'VERSION.json'

def get_current_version():
    """Lee versión actual o inicializa"""
    if os.path.exists(VERSION_FILE):
        try:
            with open(VERSION_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    
    return {
        "version": "1.0.0",
        "major": 1,
        "minor": 0,
        "patch": 0,
        "date": "2026-02-14",
        "changelog": []
    }

def save_version(version):
    """Guarda versión"""
    with open(VERSION_FILE, 'w', encoding='utf-8') as f:
        json.dump(version, f, indent=2, ensure_ascii=False)

def get_git_diff():
    """Obtiene archivos modificados"""
    try:
        result = subprocess.run(
            ['git', 'diff', '--name-only', 'HEAD~1..HEAD'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode == 0:
            files = [f for f in result.stdout.strip().split('\n') if f]
            return files
        return []
    except:
        return []

def get_last_commit():
    """Obtiene último commit message"""
    try:
        result = subprocess.run(
            ['git', 'log', '-1', '--pretty=%B'],
            capture_output=True,
            text=True,
            timeout=5
        )
        return result.stdout.strip() if result.returncode == 0 else "No message"
    except:
        return "No message"

def analyze_changes(files):
    """Analiza tipo de cambio"""
    
    # Breaking changes
    breaking_files = [
        'main_workflow.py',
        'agents/generator_agent.py',
        'agents/critic_agent.py'
    ]
    
    for file in files:
        for pattern in breaking_files:
            if pattern in file:
                return 'major', f"⚠️  Breaking: {file}"
    
    # Features
    if any('new' in f.lower() or 'add' in f.lower() for f in files):
        return 'minor', f"✨ Feature: {files[0]}"
    
    # Fix/patch
    return 'patch', f"🔧 Fix: {files[0] if files else 'varios'}"

def increment_version(version, bump_type):
    """Incrementa versión"""
    
    if bump_type == 'major':
        version['major'] += 1
        version['minor'] = 0
        version['patch'] = 0
    elif bump_type == 'minor':
        version['minor'] += 1
        version['patch'] = 0
    else:
        version['patch'] += 1
    
    version['version'] = f"{version['major']}.{version['minor']}.{version['patch']}"
    version['date'] = datetime.now().strftime('%Y-%m-%d')
    
    return version

def add_changelog(version, bump_type, description, commit):
    """Añade entrada changelog"""
    
    entry = {
        "version": version['version'],
        "date": version['date'],
        "type": bump_type,
        "description": description,
        "commit": commit[:100]
    }
    
    version['changelog'].insert(0, entry)
    version['changelog'] = version['changelog'][:50]
    
    return version

def show_version():
    """Muestra versión actual"""
    version = get_current_version()
    
    print("\n" + "="*60)
    print(f"📦 VERSION: {version['version']}")
    print("="*60)
    print(f"📅 {version['date']}\n")
    
    if version['changelog']:
        print("📋 CHANGELOG (Últimas 5):\n")
        for entry in version['changelog'][:5]:
            emoji = {'major': '🔴', 'minor': '🟡', 'patch': '🟢'}.get(entry['type'], '⚪')
            print(f"{emoji} v{entry['version']} ({entry['date']})")
            print(f"   {entry.get('description', 'No desc')}")
            print()

def auto_version():
    """Versionado automático"""
    
    print("\n🔍 Analizando cambios...\n")
    
    version = get_current_version()
    print(f"Actual: {version['version']}")
    
    files = get_git_diff()
    
    if not files:
        print("⚠️  Sin cambios")
        show_version()
        return
    
    print(f"\n📁 {len(files)} archivos:")
    for f in files[:5]:
        print(f"  - {f}")
    if len(files) > 5:
        print(f"  ... +{len(files)-5}")
    
    bump_type, description = analyze_changes(files)
    commit = get_last_commit()
    
    print(f"\n💡 Tipo: {bump_type.upper()}")
    print(f"   {description}")
    
    version = increment_version(version, bump_type)
    version = add_changelog(version, bump_type, description, commit)
    
    save_version(version)
    
    print(f"\n✅ Nueva versión: {version['version']}\n")

def manual_bump(bump_type, description=None):
    """Bump manual"""
    
    if bump_type not in ['major', 'minor', 'patch']:
        print(f"❌ Tipo inválido: {bump_type}")
        return
    
    version = get_current_version()
    version = increment_version(version, bump_type)
    
    if not description:
        description = f"Manual {bump_type} bump"
    
    commit = get_last_commit()
    version = add_changelog(version, bump_type, description, commit)
    
    save_version(version)
    
    print(f"\n✅ Versión: {version['version']}")
    show_version()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        auto_version()
    elif sys.argv[1] == 'show':
        show_version()
    elif sys.argv[1] == 'bump':
        bump_type = sys.argv[2] if len(sys.argv) > 2 else 'patch'
        description = ' '.join(sys.argv[3:]) if len(sys.argv) > 3 else None
        manual_bump(bump_type, description)
    else:
        print("Uso:")
        print("  python version-manager.py           # Auto-version")
        print("  python version-manager.py show      # Ver versión")
        print("  python version-manager.py bump major")
