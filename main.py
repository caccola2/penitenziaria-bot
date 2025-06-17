import os
import discord
from discord.ext import commands
from discord import app_commands, ui, TextStyle, Interaction
from flask import Flask
from threading import Thread
import unicodedata

app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

REPARTI = {
    "ntp": {"nome": "Nucleo Traduzioni e Piantonamenti", "id": 922893733148635196},
    "sps": {"nome": "Servizio di Polizia Stradale", "id": 819254117758664714}
}

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"Errore durante la sincronizzazione dei comandi slash: {e}")
    print(f"Bot connesso come {bot.user}")

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
    return "📦"

# ✅ /check
@bot.tree.command(name="check", description="Verifica se il bot è online.")
async def check(interaction: Interaction):
    await interaction.response.send_message("✅ Il bot è online e funzionante.", ephemeral=True)

# ✅ /attivita-istituzionale
@bot.tree.command(name="attivita-istituzionale", description="Invia un'attività programmata.")
@app_commands.describe(attivita="Nome attività", luogo="Luogo incontro", data_orario="Data e orario")
async def attivita(interaction: Interaction, attivita: str, luogo: str, data_orario: str):
    ruoli_autorizzati = [819251679081791498, 815496510653333524]
    if not any(role.id in ruoli_autorizzati for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi per usare questo comando.", ephemeral=True)
        return

    canale = bot.get_channel(904658463739772998)
    embed = discord.Embed(
        title="**<:PP:793201995041079317> | ATTIVITÀ PROGRAMMATA**",
        color=discord.Color.from_str("#1e1f3f")
    )
    embed.add_field(name="🎯 Attività o evento", value=f"> {attivita}", inline=False)
    embed.add_field(name="📍 Luogo di incontro", value=f"> {luogo}", inline=False)
    embed.add_field(name="🕒 Data e orario", value=f"> {data_orario}", inline=False)
    embed.add_field(
        name="✅ Presenza",
        value="*Reagite alla reazione per segnare la presenza.*\n"
              "*Informazioni più accurate su luogo e orario dell'evento verranno fornite appena disponibili.*",
        inline=False
    )
    embed.set_footer(text=f"Attività aperta da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    msg = await canale.send(embed=embed)
    await msg.add_reaction("✅")
    await canale.send("||<@&791772896736313371>||")
    await interaction.response.send_message("✅ Attività programmata inviata con successo!", ephemeral=True)

# ✅ /promozione-operatore
class PromozioneForm(ui.Modal, title="📈 Promozione Operatore"):
    qualifica_attuale = ui.TextInput(label="Qualifica Attuale", style=TextStyle.short)
    qualifica_nuova = ui.TextInput(label="Qualifica da Attestare", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        emoji_att = trova_emoji(self.qualifica_attuale.value, interaction.guild.emojis)
        emoji_nuova = trova_emoji(self.qualifica_nuova.value, interaction.guild.emojis)
        motivazione = self.motivazione.value.strip() or "a seguito del superamento dei requisiti necessari per tale qualifica."

        embed = discord.Embed(
            description=(
                f"> **{self.qualifica_attuale.value}** {emoji_att} {self.utente.mention} viene promosso a "
                f"**{self.qualifica_nuova.value}** {emoji_nuova} {motivazione}\n\n"
                f"*Promosso da: {interaction.user.mention}*"
            ),
            color=discord.Color.green()
        )

        canale = interaction.client.get_channel(791774585007767593)
        await canale.send(embed=embed)

        try:
            await self.utente.send(embed=embed)
        except:
            pass

        await interaction.response.send_message("✅ Promozione eseguita.", ephemeral=True)

@bot.tree.command(name="promozione-operatore", description="Promuovi un operatore.")
@app_commands.describe(utente="Utente da promuovere")
async def promozione_operatore(interaction: Interaction, utente: discord.Member):
    autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(r.id in autorizzati for r in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi.", ephemeral=True)
        return
    await interaction.response.send_modal(PromozioneForm(utente))

# ✅ /trasferimento-operatore
class TrasferimentoForm(ui.Modal, title="📦 Trasferimento Operatore"):
    qualifica = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    reparto_attuale = ui.TextInput(label="Reparto Attuale (NTP/SPS)", style=TextStyle.short)
    reparto_nuovo = ui.TextInput(label="Reparto di Trasferimento (NTP/SPS)", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        guild = interaction.guild
        emoji = trova_emoji(self.qualifica.value, guild.emojis)
        codice_att = self.reparto_attuale.value.lower().strip()
        codice_new = self.reparto_nuovo.value.lower().strip()
        motivazione = self.motivazione.value.strip() or "necessità di personale nel nuovo reparto."

        if codice_att not in REPARTI or codice_new not in REPARTI:
            await interaction.response.send_message("❌ Codice reparto non valido. Usa NTP o SPS.", ephemeral=True)
            return

        ruolo_att = guild.get_role(REPARTI[codice_att]["id"])
        ruolo_new = guild.get_role(REPARTI[codice_new]["id"])
        nome_att = REPARTI[codice_att]["nome"]
        nome_new = REPARTI[codice_new]["nome"]

        try:
            await self.utente.remove_roles(ruolo_att)
            await self.utente.add_roles(ruolo_new)
        except Exception as e:
            await interaction.response.send_message(f"❌ Errore gestione ruoli: {e}", ephemeral=True)
            return

        try:
            embed_dm = discord.Embed(
                title="📦 Trasferimento Eseguito",
                description=(
                    f"**{self.qualifica.value}** {emoji} sei stato *trasferito* da "
                    f"**{nome_att.upper()}** a **{nome_new.upper()}**.\n\n"
                    f"📌 Motivo: {motivazione}"
                ),
                color=discord.Color.blue()
            )
            embed_dm.set_footer(text="Gestione trasferimenti automatici", icon_url=interaction.guild.icon.url if interaction.guild.icon else discord.Embed.Empty)
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        log_channel = bot.get_channel(791774585007767593)
        messaggio_registro = (
            f"> **{self.qualifica.value}** {emoji} {self.utente.mention} viene *trasferito* "
            f"presso il **{nome_new.upper()}** a seguito dell'approvazione della richiesta di trasferimento "
            f"vista {motivazione.lower()}."
        )
        await log_channel.send(messaggio_registro)
        await interaction.response.send_message("✅ Trasferimento completato con successo!", ephemeral=True)

@bot.tree.command(name="trasferimento-operatore", description="Trasferisci un operatore.")
@app_commands.describe(utente="Utente da trasferire")
async def trasferimento_operatore(interaction: Interaction, utente: discord.Member):
    autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(role.id in autorizzati for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi per usare questo comando.", ephemeral=True)
        return
    await interaction.response.send_modal(TrasferimentoForm(utente))

# 🔁 Avvio bot
if __name__ == \"__main__\":
    token = os.getenv(\"DISCORD_TOKEN\")
    if not token:
        print(\"❌ TOKEN mancante\")
    else:
        print(\"✅ Avvio bot in corso...\")
        bot.run(token)
