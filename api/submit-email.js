export default async function handler(req, res) {
  if (req.method !== 'POST') {
    return res.status(405).json({ error: 'Method not allowed' });
  }

  const { email, idea } = req.body;
  
  if (!email || !idea) {
    return res.status(400).json({ error: 'Email e idea requeridos' });
  }

  const botToken = process.env.TELEGRAM_BOT_TOKEN;
  const chatId = process.env.TELEGRAM_CHAT_ID;

  const message = `📧 NUEVO REGISTRO

📝 Idea: ${idea}
✉️ Email: ${email}
🕐 Fecha: ${new Date().toLocaleString('es-ES')}`;

  try {
    const response = await fetch(`https://api.telegram.org/bot${botToken}/sendMessage`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        chat_id: chatId,
        text: message,
        parse_mode: 'Markdown'
      })
    });

    if (response.ok) {
      return res.status(200).json({ success: true, message: 'Registrado correctamente' });
    } else {
      throw new Error('Error Telegram');
    }
  } catch (error) {
    console.error(error);
    return res.status(500).json({ error: 'Error al registrar' });
  }
}
