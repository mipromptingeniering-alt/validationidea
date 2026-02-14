// Vercel Serverless Function
export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Método no permitido' });
  }
  
  try {
    const { email, idea } = req.body;
    
    // Validación
    if (!email || !idea) {
      return res.status(400).json({ 
        success: false,
        error: 'Email e idea son requeridos' 
      });
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ 
        success: false,
        error: 'Email inválido' 
      });
    }
    
    // 1. Enviar a Telegram
    const telegramToken = process.env.TELEGRAM_BOT_TOKEN;
    const telegramChatId = process.env.TELEGRAM_CHAT_ID;
    
    if (telegramToken && telegramChatId) {
      const message = `🎉 NUEVO REGISTRO

📧 Email: ${email}
💡 Idea: ${idea}
📅 ${new Date().toLocaleString('es-ES', { timeZone: 'Europe/Madrid' })}

¡Alguien quiere acceso anticipado!`;
      
      const telegramUrl = `https://api.telegram.org/bot${telegramToken}/sendMessage`;
      
      await fetch(telegramUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: telegramChatId,
          text: message,
          parse_mode: 'Markdown'
        })
      });
    }
    
    // 2. Guardar en archivo JSON (Vercel tiene filesystem efímero, pero para debug)
    console.log(`✅ Registro: ${email} → ${idea}`);
    
    // 3. Disparar GitHub Action para actualizar CSV
    const githubToken = process.env.GITHUB_TOKEN;
    
    if (githubToken) {
      const githubUrl = 'https://api.github.com/repos/mipromptingeniering-alt/validationidea/dispatches';
      
      await fetch(githubUrl, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event_type: 'email_registered',
          client_payload: {
            email: email,
            idea: idea,
            timestamp: new Date().toISOString()
          }
        })
      });
    }
    
    return res.status(200).json({ 
      success: true,
      message: '¡Registro exitoso! Te contactaremos pronto.' 
    });
    
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({ 
      success: false,
      error: 'Error del servidor. Inténtalo de nuevo.' 
    });
  }
}
