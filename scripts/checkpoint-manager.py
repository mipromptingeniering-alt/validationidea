import os
import json
import shutil
from datetime import datetime
import hashlib

CHECKPOINTS_DIR = '.checkpoints'
MAX_CHECKPOINTS = 10

def create_checkpoint(description=""):
    """Crea checkpoint del estado actual del proyecto"""
    
    print(f"\n📸 Creando checkpoint...")
    
    # Crear directorio checkpoints
    os.makedirs(CHECKPOINTS_DIR, exist_ok=True)
    
    # Timestamp único
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    checkpoint_id = f"checkpoint_{timestamp}"
    checkpoint_dir = f"{CHECKPOINTS_DIR}/{checkpoint_id}"
    
    os.makedirs(checkpoint_dir, exist_ok=True)
    
    # Archivos críticos a guardar
    critical_files = [
        'agents/*.py',
        'config/*.json',
        'data/ideas-validadas.csv',
        'memory-system/*.json',
        'scripts/*.py',
        'prompts/*.json',
        'main_workflow.py'
    ]
    
    saved_files = []
    
    # Copiar archivos
    for pattern in critical_files:
        if '*' in pattern:
            directory = pattern.split('*')[0].rstrip('/')
            if os.path.exists(directory):
                for file in os.listdir(directory):
                    if file.endswith(pattern.split('*')[1]):
                        source = f"{directory}/{file}"
                        dest_dir = f"{checkpoint_dir}/{directory}"
                        os.makedirs(dest_dir, exist_ok=True)
                        shutil.copy2(source, f"{dest_dir}/{file}")
                        saved_files.append(source)
        else:
            if os.path.exists(pattern):
                dest_dir = os.path.dirname(f"{checkpoint_dir}/{pattern}")
                os.makedirs(dest_dir, exist_ok=True)
                shutil.copy2(pattern, f"{checkpoint_dir}/{pattern}")
                saved_files.append(pattern)
    
    # Metadata
    metadata = {
        "id": checkpoint_id,
        "timestamp": timestamp,
        "datetime": datetime.now().isoformat(),
        "description": description,
        "files_count": len(saved_files),
        "files": saved_files
    }
    
    with open(f"{checkpoint_dir}/metadata.json", 'w') as f:
        json.dump(metadata, f, indent=2)
    
    # Limpiar checkpoints antiguos
    cleanup_old_checkpoints()
    
    print(f"✅ Checkpoint creado: {checkpoint_id}")
    print(f"📁 {len(saved_files)} archivos guardados")
    print(f"📝 Descripción: {description}\n")
    
    return checkpoint_id

def list_checkpoints():
    """Lista checkpoints disponibles"""
    
    if not os.path.exists(CHECKPOINTS_DIR):
        print("📭 No hay checkpoints")
        return []
    
    checkpoints = []
    
    for cp_dir in sorted(os.listdir(CHECKPOINTS_DIR), reverse=True):
        metadata_file = f"{CHECKPOINTS_DIR}/{cp_dir}/metadata.json"
        
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
                checkpoints.append(metadata)
    
    return checkpoints

def restore_checkpoint(checkpoint_id):
    """Restaura proyecto a checkpoint específico"""
    
    checkpoint_dir = f"{CHECKPOINTS_DIR}/{checkpoint_id}"
    
    if not os.path.exists(checkpoint_dir):
        print(f"❌ Checkpoint no existe: {checkpoint_id}")
        return False
    
    # Leer metadata
    with open(f"{checkpoint_dir}/metadata.json", 'r') as f:
        metadata = json.load(f)
    
    print(f"\n⚠️  ROLLBACK a checkpoint: {checkpoint_id}")
    print(f"📅 Fecha: {metadata['datetime']}")
    print(f"📝 Descripción: {metadata['description']}")
    print(f"📁 {metadata['files_count']} archivos a restaurar")
    
    confirm = input("\n¿Continuar? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("❌ Rollback cancelado")
        return False
    
    # Crear backup del estado actual antes de restaurar
    print("\n📸 Creando backup del estado actual...")
    create_checkpoint("Pre-rollback backup")
    
    # Restaurar archivos
    print("\n🔄 Restaurando archivos...")
    
    for file in metadata['files']:
        source = f"{checkpoint_dir}/{file}"
        dest = file
        
        if os.path.exists(source):
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            shutil.copy2(source, dest)
            print(f"   ✅ {file}")
    
    print(f"\n✅ Rollback completado a {checkpoint_id}\n")
    
    return True

def cleanup_old_checkpoints():
    """Mantiene solo últimos MAX_CHECKPOINTS"""
    
    if not os.path.exists(CHECKPOINTS_DIR):
        return
    
    checkpoints = sorted(os.listdir(CHECKPOINTS_DIR), reverse=True)
    
    if len(checkpoints) > MAX_CHECKPOINTS:
        for cp in checkpoints[MAX_CHECKPOINTS:]:
            cp_path = f"{CHECKPOINTS_DIR}/{cp}"
            shutil.rmtree(cp_path)
            print(f"🗑️  Checkpoint antiguo eliminado: {cp}")

def show_checkpoints():
    """Muestra checkpoints disponibles"""
    
    checkpoints = list_checkpoints()
    
    if not checkpoints:
        print("📭 No hay checkpoints disponibles")
        return
    
    print(f"\n📋 CHECKPOINTS DISPONIBLES ({len(checkpoints)}):\n")
    
    for i, cp in enumerate(checkpoints, 1):
        print(f"{i}. {cp['id']}")
        print(f"   📅 {cp['datetime']}")
        print(f"   📝 {cp['description']}")
        print(f"   📁 {cp['files_count']} archivos")
        print()


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Uso:")
        print("  python checkpoint-manager.py create 'descripción'")
        print("  python checkpoint-manager.py list")
        print("  python checkpoint-manager.py restore checkpoint_YYYYMMDD_HHMMSS")
    
    elif sys.argv[1] == 'create':
        desc = sys.argv[2] if len(sys.argv) > 2 else "Manual checkpoint"
        create_checkpoint(desc)
    
    elif sys.argv[1] == 'list':
        show_checkpoints()
    
    elif sys.argv[1] == 'restore':
        if len(sys.argv) < 3:
            print("❌ Especifica checkpoint ID")
        else:
            restore_checkpoint(sys.argv[2])
