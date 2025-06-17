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

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(899561903448260628)
        motivazione = self.motivazione.value.strip() if self.motivazione.value.strip() else "a seguito del superamento dei requisiti necessari per tale qualifica."
        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        emoji_promozione = trova_emoji(self.nuova_qualifica.value, interaction.guild.emojis)
        messaggio = f"> **{self.qualifica_operatore.value}** {emoji_qualifica} {self.utente.mention} viene promosso alla qualifica di **{self.nuova_qualifica.value}** {emoji_promozione} {motivazione}\n\n*Promosso da: {interaction.user.mention}*"
        ruolo_attuale = trova_ruolo(self.qualifica_operatore.value, interaction.guild.roles)
        ruolo_nuovo = trova_ruolo(self.nuova_qualifica.value, interaction.guild.roles)
        try:
            if ruolo_attuale and ruolo_attuale in self.utente.roles:
                await self.utente.remove_roles(ruolo_attuale)
            if ruolo_nuovo:
                await self.utente.add_roles(ruolo_nuovo)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Permessi insufficienti per i ruoli.", ephemeral=True)
            return
        try:
            embed_dm = discord.Embed(
                title="📈 Nuova Promozione!",
                description=f"> **{self.qualifica_operatore.value}** {emoji_qualifica} sei stato promosso a **{self.nuova_qualifica.value}** {emoji_promozione} {motivazione}",
                color=discord.Color.blue()
            )
            embed_dm.set_footer(text=f"Promosso da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass
        await canale.send(messaggio)
        await interaction.response.send_message("✅ Promozione inviata e ruoli aggiornati!", ephemeral=True)

@bot.tree.command(name="promozione-operatore", description="Promuovi un operatore compilando il form.")
@app_commands.describe(utente="Utente da promuovere")
async def promozione_operatore(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(PromozioneForm(utente=utente))

# ✅ Trasferimento operatore aggiornato con reparti NTP/SPS
class TrasferimentoForm(ui.Modal, title="🔄 Form Trasferimento Operatore"):

    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    reparto_attuale = ui.TextInput(label="Reparto attuale (NTP o SPS)", style=TextStyle.short)
    reparto_trasferimento = ui.TextInput(label="Reparto di trasferimento (NTP o SPS)", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione trasferimento (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(899561903448260628)

        # ✨ Mappa reparti
        reparti = {
            "ntp": ("Nucleo Traduzioni e Piantonamenti", 922893733148635196),
            "sps": ("Servizio di Polizia Stradale", 819254117758664714)
        }

        def normalizza(valore):
            return valore.lower().strip().replace(" ", "")

        rep_att = normalizza(self.reparto_attuale.value)
        rep_tra = normalizza(self.reparto_trasferimento.value)

        if rep_att not in reparti or rep_tra not in reparti:
            await interaction.response.send_message("❌ I reparti devono essere 'NTP' o 'SPS'.", ephemeral=True)
            return

        nome_rep_att, ruolo_att_id = reparti[rep_att]
        nome_rep_tra, ruolo_tra_id = reparti[rep_tra]

        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        motivazione = (
            self.motivazione.value.strip()
            if self.motivazione.value.strip()
            else "a seguito dell'approvazione della richiesta di trasferimento vista necessità di personale all'interno del reparto."
        )

        messaggio = (
            f"> **{self.qualifica_operatore.value}** {emoji_qualifica} "
            f"{self.utente.mention} viene *trasferito* da **{nome_rep_att}** a **{nome_rep_tra}** {motivazione}\n\n"
            f"*Autorizzato da: {interaction.user.mention}*"
        )

        ruolo_attuale = interaction.guild.get_role(ruolo_att_id)
        ruolo_nuovo = interaction.guild.get_role(ruolo_tra_id)

        try:
            if ruolo_attuale and ruolo_attuale in self.utente.roles:
                await self.utente.remove_roles(ruolo_attuale)
            if ruolo_nuovo:
                await self.utente.add_roles(ruolo_nuovo)
        except discord.Forbidden:
            await interaction.response.send_message("❌ Non ho i permessi per modificare i ruoli reparto.", ephemeral=True)
            return

        try:
            embed_dm = discord.Embed(
                title="🔄 Trasferimento Eseguito",
                description=(
                    f"> **{self.qualifica_operatore.value}** {emoji_qualifica} sei stato *trasferito* da "
                    f"**{nome_rep_att}** a **{nome_rep_tra}** {motivazione}"
                ),
                color=discord.Color.dark_teal()
            )
            embed_dm.set_footer(
                text=f"Trasferito da: {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        await canale.send(messaggio)
        await interaction.response.send_message("✅ Trasferimento completato!", ephemeral=True)

@bot.tree.command(name="trasferimento-operatore", description="Trasferisce un operatore in un altro reparto.")
@app_commands.describe(utente="Utente da trasferire")
async def trasferimento_operatore(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [819251679081791498, 896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(TrasferimentoForm(utente=utente))

# 🚀 Avvio
bot.run(os.getenv("DISCORD_TOKEN"))
