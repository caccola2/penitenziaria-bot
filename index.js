const express = require('express');
const noblox = require('noblox.js');

const app = express();
app.use(express.json());

// Prendi il cookie dalla variabile di ambiente di Render
const COOKIE = process.env.COOKIE;
const GROUP_ID = 8730810;

// Login a Roblox all'avvio
(async () => {
  try {
    await noblox.setCookie(COOKIE);
    console.log("✅ Login a Roblox riuscito");
  } catch (err) {
    console.error("❌ Errore durante il login:", err);
  }
})();

// Rotta per fare il rank: POST /rank con { username, rankId }
app.post('/rank', async (req, res) => {
  const { username, rankId } = req.body;

  if (!username || !rankId) {
    return res.status(400).json({ success: false, message: "username o rankId mancanti" });
  }

  try {
    const userId = await noblox.getIdFromUsername(username);
    await noblox.setRank(GROUP_ID, userId, rankId);
    res.json({ success: true, message: `✅ ${username} aggiornato al rango ${rankId}` });
  } catch (err) {
    console.error("❌ Errore durante il rank:", err);
    res.status(500).json({ success: false, message: "Errore durante il rank", error: err.message });
  }
});

// Rotta base (usata da Uptimer per tenerlo sveglio)
app.get('/', (req, res) => {
  res.send('Bot Roblox attivo ✅');
});

// Porta da usare (Render la imposta automaticamente)
const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`🚀 Server attivo sulla porta ${PORT}`));
