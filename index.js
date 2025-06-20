require("dotenv").config();
const noblox = require("noblox.js");

async function startApp() {
    const cookie = process.env.ROBLOX_COOKIE;
    try {
        await noblox.setCookie(cookie);
        const currentUser = await noblox.getCurrentUser();
        console.log(`Autenticato come ${currentUser.UserName}`);
    } catch (err) {
        console.error("Errore nell'autenticazione:", err);
    }
}

startApp();
