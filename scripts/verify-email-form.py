import os
import requests
from bs4 import BeautifulSoup

def check_email_form():
    """Verifica si formulario email funciona en landings"""
    
    print("🔍 Verificando formulario email en landing pages...\n")
    
    # Buscar landings
    landing_dir = 'landing-pages'
    
    if not os.path.exists(landing_dir):
        print("❌ Directorio landing-pages no existe")
        return
    
    landings = [d for d in os.listdir(landing_dir) if os.path.isdir(f"{landing_dir}/{d}")]
    
    print(f"📊 {len(landings)} landing pages encontradas\n")
    
    for slug in landings[:3]:  # Verificar primeras 3
        html_file = f"{landing_dir}/{slug}/index.html"
        
        if not os.path.exists(html_file):
            continue
        
        with open(html_file, 'r', encoding='utf-8') as f:
            html = f.read()
        
        soup = BeautifulSoup(html, 'html.parser')
        
        # Buscar formulario
        forms = soup.find_all('form')
        
        print(f"📄 {slug}:")
        
        if not forms:
            print("   ❌ No hay formularios")
            continue
        
        for i, form in enumerate(forms):
            action = form.get('action', '')
            method = form.get('method', '')
            
            print(f"   📝 Form {i+1}:")
            print(f"      Action: {action}")
            print(f"      Method: {method}")
            
            # Verificar inputs
            email_input = form.find('input', {'type': 'email'})
            if email_input:
                print(f"      ✅ Input email: name='{email_input.get('name')}'")
            else:
                print(f"      ❌ No hay input email")
            
            # Verificar si apunta a Vercel
            if 'vercel' in action or '/api/' in action:
                print(f"      ✅ Conectado a Vercel API")
            else:
                print(f"      ⚠️  No conectado a Vercel (action: {action})")
        
        print()
    
    # Verificar si existe API endpoint en Vercel
    print("\n🔍 Verificando Vercel API endpoint...")
    
    api_file = 'api/submit-email.js'
    
    if os.path.exists(api_file):
        print(f"✅ API endpoint existe: {api_file}")
        
        with open(api_file, 'r', encoding='utf-8') as f:
            code = f.read()
            
        if 'export default' in code or 'module.exports' in code:
            print("✅ Formato Vercel Function correcto")
        else:
            print("⚠️  Formato puede no ser válido para Vercel")
    else:
        print(f"❌ API endpoint NO existe: {api_file}")
        print("   Necesitas crear api/submit-email.js")
    
    print("\n📋 RESUMEN:")
    print("Si formularios tienen action='/api/submit-email' y existe api/submit-email.js")
    print("entonces el sistema FUNCIONA ✅")
    print("\nSi no, necesitas:")
    print("1. Crear api/submit-email.js con Vercel Function")
    print("2. Actualizar formularios para usar action='/api/submit-email'")


if __name__ == "__main__":
    check_email_form()
