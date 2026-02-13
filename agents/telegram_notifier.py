import os
import requests
from datetime import datetime
import pytz

def send_telegram_notification(idea, critique, landing_url, report_url):
    """
    Envía notificación Telegram con hora CORRECTA (CET/CEST)
    """
    
    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        print("⚠️  Variables Telegram no configuradas")
        return False
    
    # Hora correcta en zona horaria española
    tz = pytz.timezone('Europe/Madrid')
    now = datetime.now(tz)
    timestamp = now.strftime('%d/%m/%Y %H:%M CET')
    
    nombre = idea.get('nombre', 'Idea SaaS')
    descripcion = idea.get('descripcion_corta', idea.get('descripcion', 'Sin descripción'))
    score_gen = idea.get('score_generador', 0)
    score_crit = critique.get('score_critico', 0) if critique else 0
    precio = idea.get('precio_sugerido', 'N/A')
    publico = idea.get('publico_objetivo', 'N/A')
    tam = idea.get('tam', 'N/A')
    
    # URLs completas de GitHub Pages
    base_url = "https://mipromptingeniering-alt.github.io/validationidea"
    landing_full = f"{base_url}/{landing_url}"
    report_full = f"{base_url}/{report_url}"
    dashboard_full = f"{base_url}/landing-pages/index.html"
    
    message = f"""🚀 **NUEVA IDEA VALIDADA**

📅 **Fecha:** {timestamp}

**{nombre}**
_{descripcion}_

📊 **Scores:**
• Generador: {score_gen}/100
• Crítico: {score_crit}/100

💰 **Precio:** {precio}
👥 **Público:** {publico}
📈 **TAM:** {tam}

🔗 **Links:**
• [Landing Page]({landing_full})
• [Informe Técnico]({report_full})
• [Dashboard]({dashboard_full})

---
_Generado automáticamente_
"""
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'Markdown',
        'disable_web_page_preview': False
    }
    
    try:
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
        print(f"✅ Telegram enviado a {chat_id}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"❌ Error Telegram: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Respuesta: {e.response.text}")
        return False


if __name__ == "__main__":
    # Test
    test_idea = {
        'nombre': 'Test SaaS',
        'descripcion_corta': 'Idea de prueba',
        'score_generador': 85,
        'precio_sugerido': '49€/mes',
        'publico_objetivo': 'Desarrolladores',
        'tam': '100M€'
    }
    
    test_critique = {
        'score_critico': 72
    }
    
    print("🧪 Enviando notificación de prueba...")
    send_telegram_notification(
        test_idea,
        test_critique,
        'landing-pages/test-saas.html',
        'reports/test-saas.html'
    )
