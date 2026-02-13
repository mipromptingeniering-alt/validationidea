import fetch from 'node-fetch';

export default async function handler(req, res) {
  // CORS
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type');
  
  if (req.method === 'OPTIONS') {
    return res.status(200).end();
  }
  
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }
  
  try {
    const { email, idea, timestamp } = req.body;
    
    // Validación
    if (!email || !idea) {
      return res.status(400).json({ error: 'Email e idea requeridos' });
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return res.status(400).json({ error: 'Email inválido' });
    }
    
    // 1. Enviar a Telegram
    const telegramToken = process.env.TELEGRAM_BOT_TOKEN;
    const telegramChatId = process.env.TELEGRAM_CHAT_ID;
    
    if (telegramToken && telegramChatId) {
      const message = `🎉 NUEVO REGISTRO

📧 Email: ${email}
💡 Idea: ${idea}
📅 Fecha: ${new Date(timestamp).toLocaleString('es-ES', { timeZone: 'Europe/Madrid' })}

---
¡Alguien está interesado en tu idea!`;
      
      await fetch(`https://api.telegram.org/bot${telegramToken}/sendMessage`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          chat_id: telegramChatId,
          text: message,
          parse_mode: 'Markdown'
        })
      });
    }
    
    // 2. Disparar GitHub Action para actualizar CSV
    const githubToken = process.env.GITHUB_TOKEN;
    const repoOwner = 'mipromptingeniering-alt';
    const repoName = 'validationidea';
    
    if (githubToken) {
      await fetch(`https://api.github.com/repos/${repoOwner}/${repoName}/dispatches`, {
        method: 'POST',
        headers: {
          'Authorization': `token ${githubToken}`,
          'Accept': 'application/vnd.github.v3+json',
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          event_type: 'email_registered',
          client_payload: {
            email: email,
            idea: idea,
            timestamp: timestamp
          }
        })
      });
    }
    
    // 3. Guardar en base de datos simple (opcional - KV store de Vercel)
    // Por ahora, solo responder OK
    
    console.log(`✅ Registro exitoso: ${email} → ${idea}`);
    
    return res.status(200).json({ 
      success: true, 
      message: 'Registro exitoso' 
    });
    
  } catch (error) {
    console.error('Error:', error);
    return res.status(500).json({ 
      error: 'Error del servidor',
      details: error.message 
    });
  }
}
