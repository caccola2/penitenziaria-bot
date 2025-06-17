import os
import discord
from discord.ext import commands
from discord import app_commands, ui, TextStyle, Interaction
from flask import Flask
from threading import Thread
import unicodedata

# 🌐 Web server
app = Flask('')

@app.route('/')
def home():
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# ⚙️ Setup bot
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
        print(f"Errore sincronizzazione: {e}")
    print(f"Bot connesso come {bot.user}")

# ✅ Attività
@bot.tree.command(name="attivita-istituzionale", description="Invia un'attività programmata.")
@app_commands.describe(attivita="Nome dell'attività", luogo="Luogo di incontro", data_orario="Data e ora")
async def attivita(interaction: discord.Interaction, attivita: str, luogo: str, data_orario: str):
    user_roles = [role.id for role in interaction.user.roles]
    if not any(r in user_roles for r in [819251679081791498, 815496510653333524]):
        await interaction.response.send_message("Non hai i permessi.", ephemeral=True)
        return

    channel = bot.get_channel(904658463739772998)
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
              "*Info precise verranno fornite appena disponibili.*",
        inline=False
    )
    embed.set_footer(text=f"Attività aperta da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await channel.send("||<@&791772896736313371>||")
    await interaction.response.send_message("Attività inviata!", ephemeral=True)

# ✅ Check
@bot.tree.command(name="check", description="Verifica se il bot è online.")
async def check(interaction: discord.Interaction):
    await interaction.response.send_message("Il bot funziona porcodio 🐷⚡", ephemeral=True)

# 🔍 Emoji intelligente
def trova_emoji(nome_qualifica, emoji_lista):
    def normalizza(testo):
        testo = testo.lower().replace(" ", "").replace("-", "")
        testo = ''.join(c for c in unicodedata.normalize('NFD', testo) if unicodedata.category(c) != 'Mn')
        return testo
    nome_norm = normalizza(nome_qualifica)
    for emoji in emoji_lista:
        if nome_norm == normalizza(emoji.name):
            return str(emoji)
    for emoji in emoji_lista:
        nome_emoji = normalizza(emoji.name)
        if nome_norm in nome_emoji and not nome_emoji.startswith("allievo"):
            return str(emoji)
    return ""

# 🔍 Ruolo intelligente
def trova_ruolo(nome, ruoli):
    nome_norm = nome.lower().replace(" ", "")
    for r in ruoli:
        if nome_norm == r.name.lower().replace(" ", ""):
            return r
    for r in ruoli:
        if nome_norm in r.name.lower().replace(" ", "") and not r.name.lower().startswith("allievo"):
            return r
    return None

# ✅ Promozione operatore
class PromozioneForm(ui.Modal, title="📈 Form Promozione Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    nuova_qualifica = ui.TextInput(label="Qualifica da attestare", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione promozione (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Me
