import os
import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
from threading import Thread

# Web server per mantenere attivo il bot su Render
app = Flask('')

@app.route('/')
def home():
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    return "Bot attivo."

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

# Impostazioni del bot
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True  # richiesto per leggere i ruoli

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    await bot.wait_until_ready()
    try:
        synced = await bot.tree.sync()
        print(f"Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"Errore durante la sincronizzazione dei comandi slash: {e}")
    print(f"Bot connesso come {bot.user}")

@bot.tree.command(name="attivita-istituzionale", description="Invia un'attività programmata.")
@app_commands.describe(
    attivita="Nome dell'attività o evento",
    luogo="Luogo di incontro",
    data_orario="Data e orario dell'incontro"
)
async def attivita(
    interaction: discord.Interaction,
    attivita: str,
    luogo: str,
    data_orario: str
):
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in [819251679081791498, 815496510653333524]):
        await interaction.response.send_message("Non hai i permessi per usare questo comando.", ephemeral=True)
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
              "*Informazioni più accurate su luogo e orario dell'evento verranno fornite appena disponibili.*",
        inline=False
    )

    embed.set_footer(
        text=f"Attività aperta da: {interaction.user.display_name}",
        icon_url=interaction.user.display_avatar.url
    )

    sent_message = await channel.send(embed=embed)
    await sent_message.add_reaction("✅")
    await channel.send("||<@&791772896736313371>||")

    await interaction.response.send_message("Attività programmata inviata con successo!", ephemeral=True)

# ✅ Comando /check per verifica stato bot
@bot.tree.command(name="check", description="Verifica se il bot è online.")
async def check(interaction: discord.Interaction):
    await interaction.response.send_message("Il bot funziona porcodio 🐷⚡", ephemeral=True)

# Avvio del bot
bot.run(os.getenv("DISCORD_TOKEN"))

print("DEBUG: avvio riuscito")
