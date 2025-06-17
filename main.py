import os
import discord
from discord.ext import commands
from discord import app_commands, ui, TextStyle, Interaction
from flask import Flask
from threading import Thread
import unicodedata

# 🌐 Web server per mantenerlo vivo su Render
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# ✅ Configurazione base
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
        print(f"✅ Comandi sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"❌ Sync error: {e}")
    print(f"🤖 Bot connesso come {bot.user}")

# 📦 Mappa reparti (nome completo e ID ruolo)
REPARTI = {
    "ntp": ("Nucleo Traduzioni e Piantonamenti", 922893733148635196),
    "sps": ("Servizio di Polizia Stradale", 819254117758664714)
}

# 🔍 Emoji finder
def trova_emoji(nome, emoji_lista):
    def normalizza(t):
        return ''.join(c for c in unicodedata.normalize('NFD', t.lower().replace(" ", "").replace("-", ""))
                       if unicodedata.category(c) != 'Mn')
    nome_norm = normalizza(nome)
    for emoji in emoji_lista:
        if nome_norm in normalizza(emoji.name):
            return str(emoji)
    return "📦"

# ✅ Comando /check
@bot.tree.command(name="check", description="Verifica se il bot è online.")
async def check(interaction: Interaction):
    await interaction.response.send_message("✅ Il bot è online e funzionante.", ephemeral=True)

# ✅ /attivita-istituzionale
@bot.tree.command(name="attivita-istituzionale", description="Invia un'attività programmata.")
@app_commands.describe(attivita="Nome evento", luogo="Luogo incontro", data_orario="Data e orario")
async def attivita(interaction: Interaction, attivita: str, luogo: str, data_orario: str):
    if not any(role.id in [819251679081791498, 815496510653333524] for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi.", ephemeral=True)
        return

    channel = bot.get_channel(904658463739772998)
    embed = discord.Embed(title="**<:PP:793201995041079317> | ATTIVITÀ PROGRAMMATA**", color=discord.Color.from_str("#1e1f3f"))
    embed.add_field(name="🎯 Attività o evento", value=f"> {attivita}", inline=False)
    embed.add_field(name="📍 Luogo di incontro", value=f"> {luogo}", inline=False)
    embed.add_field(name="🕒 Data e orario", value=f"> {data_orario}", inline=False)
    embed.add_field(name="✅ Presenza", value="*Reagite per segnare la presenza.*", inline=False)
    embed.set_footer(text=f"Attività aperta da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await channel.send("||<@&791772896736313371>||")
    await interaction.response.send_message("✅ Attività programmata inviata!", ephemeral=True)

# ✅ Promozione
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

@bot.tree.command(name="promozione-operatore", description="Promuovi un operatore compilando un form.")
@app_commands.describe(utente="Utente da promuovere")
async def promozione_operatore(interaction: Interaction, utente: discord.Member):
    autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(r.id in autorizzati for r in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi.", ephemeral=True)
        return
    await interaction.response.send_modal(PromozioneForm(utente))

# ✅ Trasferimento
class TrasferimentoForm(ui.Modal, title="🔁 Trasferimento Operatore"):
    qualifica = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    reparto_att = ui.TextInput(label="Reparto attuale (NTP o SPS)", style=TextStyle.short)
    reparto_new = ui.TextInput(label="Reparto di trasferimento (NTP o SPS)", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        r_att = REPARTI.get(self.reparto_att.value.lower().strip())
        r_new = REPARTI.get(self.reparto_new.value.lower().strip())

        if not r_att or not r_new:
            await interaction.response.send_message("❌ Reparti validi: NTP o SPS.", ephemeral=True)
            return

        nome_att, id_att = r_att
        nome_new, id_new = r_new

        motivazione = self.motivazione.value.strip() or "necessità di personale nel nuovo reparto."
        emoji = "📦"

        # Ruoli
        ruolo_rimuovi = interaction.guild.get_role(id_att)
        ruolo_aggiungi = interaction.guild.get_role(id_new)

        if ruolo_rimuovi: await self.utente.remove_roles(ruolo_rimuovi)
        if ruolo_aggiungi: await self.utente.add_roles(ruolo_aggiungi)

        # Embed log
        embed = discord.Embed(
            title="📦 Trasferimento Eseguito",
            description=(
                f"**{self.qualifica.value}** {emoji} {self.utente.mention} è stato *trasferito* da "
                f"**{nome_att.upper()}** a **{nome_new.upper()}**.\n\nMotivo: {motivazione}"
            ),
            color=discord.Color.blue()
        )
        embed.set_footer(text=f"Trasferito da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)

        log_channel = interaction.client.get_channel(791774585007767593)
        await log_channel.send(embed=embed)

        try:
            await self.utente.send(embed=embed)
        except:
            pass

        await interaction.response.send_message("✅ Trasferimento registrato!", ephemeral=True)

@bot.tree.command(name="trasferimento-operatore", description="Trasferisci un operatore.")
@app_commands.describe(utente="Utente da trasferire")
async def trasferimento(interaction: Interaction, utente: discord.Member):
    autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(r.id in autorizzati for r in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi.", ephemeral=True)
        return
    await interaction.response.send_modal(TrasferimentoForm(utente))

# 🚀 Avvio
if __name__ == "__main__":
    print("Avvio bot...")
    bot.run(os.getenv("DISCORD_TOKEN"))
