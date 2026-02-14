import os
import shutil
import glob

def migrate_landings():
    """Migra landings de estructura vieja a nueva"""
    
    print("\n🔄 Migrando landing pages a estructura correcta...\n")
    
    landing_dir = 'landing-pages'
    
    if not os.path.exists(landing_dir):
        print("❌ Directorio landing-pages no existe")
        return
    
    # Buscar archivos .html directamente en landing-pages/
    html_files = glob.glob(f"{landing_dir}/*.html")
    
    migrated = 0
    
    for html_file in html_files:
        filename = os.path.basename(html_file)
        slug = filename.replace('.html', '')
        
        # Crear directorio slug/
        new_dir = f"{landing_dir}/{slug}"
        os.makedirs(new_dir, exist_ok=True)
        
        # Mover archivo a slug/index.html
        new_path = f"{new_dir}/index.html"
        
        try:
            shutil.move(html_file, new_path)
            print(f"✅ Migrado: {filename} → {slug}/index.html")
            migrated += 1
        except Exception as e:
            print(f"⚠️  Error migrando {filename}: {e}")
    
    print(f"\n✅ {migrated} landing pages migradas correctamente")


if __name__ == "__main__":
    migrate_landings()
