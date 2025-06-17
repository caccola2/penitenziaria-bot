import os
import discord
from discord.ext import commands
from discord import app_commands, ui, TextStyle, Interaction
from flask import Flask
from threading import Thread
import unicodedata

# 🌐 Web server per Render
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# ⚙️ Impostazioni bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"Errore durante la sincronizzazione: {e}")
    print(f"Bot connesso come {bot.user}")

# 🔍 Normalizzazione emoji
def trova_emoji(nome_qualifica, emoji_lista):
    def normalizza(testo):
        testo = testo.lower().replace(" ", "").replace("-", "")
        return ''.join(c for c in unicodedata.normalize('NFD', testo) if unicodedata.category(c) != 'Mn')

    nome_norm = normalizza(nome_qualifica)

    for emoji in emoji_lista:
        if nome_norm == normalizza(emoji.name):
            return str(emoji)
    for emoji in emoji_lista:
        if nome_norm in normalizza(emoji.name):
            return str(emoji)
    return ""

# 📦 Form per Trasferimento
class TrasferimentoForm(ui.Modal, title="📦 Form Trasferimento Operatore"):
    reparto_attuale = ui.TextInput(label="Reparto Attuale (NTP o SPS)", style=TextStyle.short)
    reparto_trasferimento = ui.TextInput(label="Reparto di Trasferimento (NTP o SPS)", style=TextStyle.short)
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione trasferimento (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(899561903448260628)

        ruoli_reparto = {
            "ntp": ("Nucleo Traduzioni e Piantonamenti", 922893733148635196),
            "sps": ("Servizio di Polizia Stradale", 819254117758664714)
        }

        rep_att_key = self.reparto_attuale.value.strip().lower()
        rep_trasf_key = self.reparto_trasferimento.value.strip().lower()

        nome_attuale, id_attuale = ruoli_reparto.get(rep_att_key, (None, None))
        nome_trasf, id_trasf = ruoli_reparto.get(rep_trasf_key, (None, None))

        if not all([nome_attuale, nome_trasf]):
            await interaction.response.send_message("❌ Reparto non valido. Usa 'NTP' o 'SPS' solo.", ephemeral=True)
            return

        motivazione = (
            self.motivazione.value.strip()
            if self.motivazione.value.strip()
            else "a seguito dell'approvazione della richiesta di trasferimento vista necessità di personale all'interno del reparto."
        )

        emoji = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)

        # Cambia ruoli
        try:
            ruolo_attuale = interaction.guild.get_role(id_attuale)
            ruolo_nuovo = interaction.guild.get_role(id_trasf)
            if ruolo_attuale in self.utente.roles:
                await self.utente.remove_roles(ruolo_attuale)
            await self.utente.add_roles(ruolo_nuovo)
        except Exception as e:
            await interaction.response.send_message(f"Errore nel cambio ruoli: {e}", ephemeral=True)
            return

        messaggio = (
            f"> **{self.qualifica_operatore.value}** {emoji} {self.utente.mention} viene *trasferito* presso il **{nome_trasf.upper()}**
            {motivazione}\n\n*Approvato da: {interaction.user.mention}*"
        )

        await canale.send(messaggio)
        await self.utente.send(
            f"🔁 Sei stato trasferito nel reparto **{nome_trasf}** come **{self.qualifica_operatore.value}**. {motivazione}"
        )
        await interaction.response.send_message("✅ Trasferimento registrato e DM inviato!", ephemeral=True)

# ➕ Comando
@bot.tree.command(name="trasferimento-operatore", description="Trasferisci un operatore da un reparto all'altro")
@app_commands.describe(utente="Utente da trasferire")
async def trasferimento_operatore(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]

    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Non hai i permessi per usare questo comando.", ephemeral=True)
        return

    await interaction.response.send_modal(TrasferimentoForm(utente=utente))

# 🔁 Avvio del bot
bot.run(os.getenv("DISCORD_TOKEN"))
