import os
import discord
from discord.ext import commands
from discord import app_commands, ui, TextStyle, Interaction
from flask import Flask
from threading import Thread
import unicodedata

# 🌐 Web server per mantenere attivo il bot su Render
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
        print(f"Errore durante la sincronizzazione dei comandi slash: {e}")
    print(f"Bot connesso come {bot.user}")

# 🔎 Trova emoji da nome ruolo ottimizzato
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

# ✅ Comando /attivita-istituzionale
@bot.tree.command(name="attivita-istituzionale", description="Invia un'attività programmata.")
@app_commands.describe(
    attivita="Nome dell'attività o evento",
    luogo="Luogo di incontro",
    data_orario="Data e orario dell'incontro"
)
async def attivita(interaction: discord.Interaction, attivita: str, luogo: str, data_orario: str):
    permessi = [819251679081791498, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]

    if not any(role_id in user_roles for role_id in permessi):
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

# ✅ /check
@bot.tree.command(name="check", description="Verifica se il bot è online.")
async def check(interaction: discord.Interaction):
    await interaction.response.send_message("✅ Il bot è online!", ephemeral=True)

# ✅ PROMOZIONE OPERATORE
class PromozioneForm(ui.Modal, title="📈 Promozione Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    nuova_qualifica = ui.TextInput(label="Qualifica da attestare", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(899561903448260628)
        guild = interaction.guild

        motivazione = self.motivazione.value.strip() or "a seguito del superamento dei requisiti necessari per tale qualifica."

        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, guild.emojis)
        emoji_promozione = trova_emoji(self.nuova_qualifica.value, guild.emojis)

        ruolo_attuale = discord.utils.find(lambda r: r.name.lower() == self.qualifica_operatore.value.lower(), guild.roles)
        ruolo_nuovo = discord.utils.find(lambda r: r.name.lower() == self.nuova_qualifica.value.lower(), guild.roles)

        if ruolo_attuale:
            await self.utente.remove_roles(ruolo_attuale)
        if ruolo_nuovo:
            await self.utente.add_roles(ruolo_nuovo)

        messaggio = (
            f"> **{self.qualifica_operatore.value}** {emoji_qualifica} "
            f"{self.utente.mention} viene promosso alla qualifica di "
            f"**{self.nuova_qualifica.value}** {emoji_promozione} {motivazione}\n\n"
            f"*Promosso da: {interaction.user.mention}*"
        )

        await canale.send(messaggio)
        try:
            await self.utente.send(f"📢 Sei stato promosso a **{self.nuova_qualifica.value}**!\n{motivazione}")
        except:
            pass

        await interaction.response.send_message("✅ Promozione registrata!", ephemeral=True)

@bot.tree.command(name="promozione-operatore", description="Promuovi un operatore.")
@app_commands.describe(utente="Utente da promuovere")
async def promozione_operatore(interaction: Interaction, utente: discord.Member):
    autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(role.id in autorizzati for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi per usare questo comando.", ephemeral=True)
        return
    await interaction.response.send_modal(PromozioneForm(utente))

# ✅ TRASFERIMENTO OPERATORE
class TrasferimentoForm(ui.Modal, title="🔁 Trasferimento Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    reparto_attuale = ui.TextInput(label="Reparto attuale (NTP o SPS)", style=TextStyle.short)
    reparto_nuovo = ui.TextInput(label="Reparto di trasferimento (NTP o SPS)", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione trasferimento (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(899561903448260628)
        guild = interaction.guild

        def rep_nome(abbr):
            mapping = {
                "ntp": ("Nucleo Traduzioni e Piantonamenti", 922893733148635196),
                "sps": ("Servizio di Polizia Stradale", 819254117758664714)
            }
            return mapping.get(abbr.lower().strip())

        nome_attuale, ruolo_att = rep_nome(self.reparto_attuale.value)
        nome_nuovo, ruolo_nuovo = rep_nome(self.reparto_nuovo.value)

        emoji = trova_emoji(self.qualifica_operatore.value, guild.emojis)

        motivo = self.motivazione.value.strip() or \
            "a seguito dell'approvazione della richiesta di trasferimento vista necessità di personale all'interno del reparto."

        ruolo_rimuovere = guild.get_role(ruolo_att)
        ruolo_aggiungere = guild.get_role(ruolo_nuovo)

        if ruolo_rimuovere:
            await self.utente.remove_roles(ruolo_rimuovere)
        if ruolo_aggiungere:
            await self.utente.add_roles(ruolo_aggiungere)

        messaggio = (
            f"> **{self.qualifica_operatore.value}** {emoji} {self.utente.mention} "
            f"viene *trasferito* presso il **{nome_nuovo.upper()}** {motivo}\n\n"
            f"*Approvato da: {interaction.user.mention}*"
        )

        await canale.send(messaggio)
        try:
            await self.utente.send(
                f"📦 Sei stato trasferito presso **{nome_nuovo}**!\n{motivo}"
            )
        except:
            pass

        await interaction.response.send_message("✅ Trasferimento registrato!", ephemeral=True)

@bot.tree.command(name="trasferimento-operatore", description="Trasferisci un operatore tra reparti.")
@app_commands.describe(utente="Utente da trasferire")
async def trasferimento_operatore(interaction: Interaction, utente: discord.Member):
    autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(role.id in autorizzati for role in interaction.user.roles):
        await interaction.response.send_message("❌ Non hai i permessi per usare questo comando.", ephemeral=True)
        return
    await interaction.response.send_modal(TrasferimentoForm(utente))

# 🟨 DEBUG TEMPORANEO
print("DEBUG: Avvio bot con token:", os.getenv("DISCORD_TOKEN"))  # ⚠️ Rimuovi in produzione

# 🔁 AVVIO BOT
bot.run(os.getenv("DISCORD_TOKEN"))
