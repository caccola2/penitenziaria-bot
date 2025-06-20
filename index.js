require('dotenv').config();
const noblox = require('noblox.js');
const express = require('express');
const app = express();
const port = 3000;

const COOKIE = process.env.COOKIE;
const GROUP_ID = parseInt(process.env.GROUP_ID);

async function startApp() {
    try {
        const currentUser = await noblox.setCookie(COOKIE);
        console.log(`Autenticato come ${currentUser.UserName}`);

        app.use(express.json());

        app.post('/rank', async (req, res) => {
            const { username, rank } = req.body;

            if (!username || !rank) {
                return res.status(400).send("Fornisci username e rank.");
            }

            try {
                const userId = await noblox.getIdFromUsername(username);
                await noblox.setRank(GROUP_ID, userId, rank);
                res.send(`Utente ${username} aggiornato al grado ${rank}`);
            } catch (err) {
                console.error(err);
                res.status(500).send("Errore durante il rank.");
            }
        });

        app.listen(port, () => {
            console.log(`Server attivo su http://localhost:${port}`);
        });
    } catch (err) {
        console.error("Errore nell'autenticazione:", err);
    }
}

startApp();
