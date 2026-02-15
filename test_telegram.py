"""
Test Telegram: diagnóstico completo
"""
import os
import requests
import sys

# Cargar desde .env manualmente
with open('.env', 'r') as f:
    for line in f:
        if '=' in line and not line.startswith('#'):
            key, value = line.strip().split('=', 1)
            os.environ[key] = value

BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '').strip()
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID', '').strip()

print("="*60)
print("🔍 DIAGNÓSTICO TELEGRAM")
print("="*60)

# 1. Verificar variables
print("\n1️⃣ Variables de entorno:")
if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN vacío")
    sys.exit(1)
else:
    print(f"✅ Token: {BOT_TOKEN[:10]}...{BOT_TOKEN[-5:]}")

if not CHAT_ID:
    print("❌ TELEGRAM_CHAT_ID vacío")
    sys.exit(1)
else:
    print(f"✅ Chat ID: {CHAT_ID}")

# 2. Verificar bot
print("\n2️⃣ Verificando bot en Telegram API...")
try:
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getMe'
    response = requests.get(url, timeout=10)
    
    if response.status_code == 200:
        bot_info = response.json()
        if bot_info.get('ok'):
            print(f"✅ Bot conectado: @{bot_info['result']['username']}")
        else:
            print(f"❌ Error: {bot_info}")
            sys.exit(1)
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error de conexión: {e}")
    sys.exit(1)

# 3. Verificar chat
print("\n3️⃣ Verificando acceso al chat...")
try:
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/getChat'
    response = requests.get(url, params={'chat_id': CHAT_ID}, timeout=10)
    
    if response.status_code == 200:
        chat_info = response.json()
        if chat_info.get('ok'):
            print(f"✅ Chat encontrado: {chat_info['result'].get('first_name', 'N/A')}")
        else:
            print(f"❌ Chat no accesible. ¿Enviaste /start al bot?")
            print(f"   Error: {chat_info.get('description', 'Unknown')}")
            print(f"\n💡 SOLUCIÓN:")
            print(f"   1. Busca tu bot en Telegram: @{bot_info['result']['username']}")
            print(f"   2. Envía /start")
            print(f"   3. Vuelve a ejecutar este test")
            sys.exit(1)
    else:
        print(f"❌ HTTP {response.status_code}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# 4. Enviar mensaje de prueba
print("\n4️⃣ Enviando mensaje de prueba...")
try:
    url = f'https://api.telegram.org/bot{BOT_TOKEN}/sendMessage'
    data = {
        'chat_id': CHAT_ID,
        'text': '🧪 **TEST EXITOSO**\n\nChet This está conectado correctamente ✅',
        'parse_mode': 'Markdown'
    }
    
    response = requests.post(url, json=data, timeout=10)
    
    if response.status_code == 200:
        result = response.json()
        if result.get('ok'):
            print("✅ Mensaje enviado correctamente")
            print("\n" + "="*60)
            print("🎉 TELEGRAM CONFIGURADO CORRECTAMENTE")
            print("="*60)
        else:
            print(f"❌ Error enviando: {result}")
    else:
        print(f"❌ HTTP {response.status_code}: {response.text}")
        sys.exit(1)
        
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)