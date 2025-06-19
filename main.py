import os
import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, TextStyle
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
        print(f"[DEBUG] Comandi slash sincronizzati: {len(synced)}")
    except Exception as e:
        print(f"[DEBUG] Errore sincronizzazione: {e}")
    print(f"[DEBUG] Bot connesso come {bot.user}")

# 🔍 Funzioni "intelligenti"
def normalizza(testo):
    testo = testo.lower().replace(" ", "").replace("-", "")
    return ''.join(c for c in unicodedata.normalize('NFD', testo)
                   if unicodedata.category(c) != 'Mn')

def trova_emoji(nome_qualifica, emoji_lista):
    nome_norm = normalizza(nome_qualifica)
    for emoji in emoji_lista:
        if nome_norm == normalizza(emoji.name):
            return str(emoji)
    for emoji in emoji_lista:
        nome_emoji = normalizza(emoji.name)
        if nome_norm in nome_emoji and not nome_emoji.startswith("allievo"):
            return str(emoji)
    return ""

def trova_ruolo(nome, ruoli):
    nome_norm = normalizza(nome)
    for r in ruoli:
        if nome_norm == normalizza(r.name):
            return r
    for r in ruoli:
        n = normalizza(r.name)
        if nome_norm in n and not n.startswith("allievo"):
            return r
    return None

# ✅ Comando: attività istituzionale
@bot.tree.command(name="attivita-istituzionale", description="Invia un'attività programmata.")
@app_commands.describe(attivita="Nome dell'attività", luogo="Luogo di incontro", data_orario="Data e ora")
async def attivita(interaction: discord.Interaction, attivita: str, luogo: str, data_orario: str):
    print(f"[DEBUG] /attivita chiamato da {interaction.user} con params: {attivita}, {luogo}, {data_orario}")
    user_roles = [r.id for r in interaction.user.roles]
    if not any(r in user_roles for r in [819251679081791498, 815496510653333524]):
        print("[DEBUG] Utente non autorizzato.")
        await interaction.response.send_message("Non hai i permessi.", ephemeral=True)
        return

    channel = bot.get_channel(904658463739772998)
    if channel is None:
        print("[DEBUG] Canale attività non trovato.")
        await interaction.response.send_message("Canale non trovato.", ephemeral=True)
        return

    embed = discord.Embed(
        title="**<:PP:793201995041079317> | ATTIVITÀ PROGRAMMATA**",
        color=discord.Color.from_str("#1e1f3f")
    )
    embed.add_field(name="🎯 Attività o evento", value=f"> {attivita}", inline=False)
    embed.add_field(name="📍 Luogo di incontro", value=f"> {luogo}", inline=False)
    embed.add_field(name="🕒 Data e orario", value=f"> {data_orario}", inline=False)
    embed.add_field(
        name="✅ Presenza",
        value=(
            "*Reagite alla reazione per segnare la presenza.*\n"
            "*Info precise verranno fornite appena disponibili.*"
        ),
        inline=False
    )
    embed.set_footer(text=f"Attività aperta da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
    msg = await channel.send(embed=embed)
    await msg.add_reaction("✅")
    await channel.send("||<@&791772896736313371>||")
    await interaction.response.send_message("Attività inviata!", ephemeral=True)

# ✅ Comando: check
@bot.tree.command(name="check", description="Verifica se il bot è online.")
async def check(interaction: discord.Interaction):
    print(f"[DEBUG] /check chiamato da {interaction.user}")
    await interaction.response.send_message("Il bot funziona porcodio 🐷⚡", ephemeral=True)

# ✅ Modal: promozione
class PromozioneForm(ui.Modal, title="📈 Form Promozione Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    nuova_qualifica = ui.TextInput(label="Qualifica da attestare", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione promozione (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        print(f"[DEBUG] PromozioneForm on_submit per {self.utente} da {interaction.user}")
        canale = interaction.client.get_channel(899561903448260628)
        print(f"[DEBUG] Canale promozione: {canale}")
        motivazione = self.motivazione.value.strip() or "a seguito del superamento dei requisiti necessari per tale qualifica."
        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        emoji_promozione = trova_emoji(self.nuova_qualifica.value, interaction.guild.emojis)
        mess = (f"> **{self.qualifica_operatore.value}** {emoji_qualifica} "
                f"{self.utente.mention} viene promosso alla qualifica di **{self.nuova_qualifica.value}** "
                f"{emoji_promozione} {motivazione}\n\n*Promosso da: {interaction.user.mention}*")
        ruolo_attuale = trova_ruolo(self.qualifica_operatore.value, interaction.guild.roles)
        ruolo_nuovo = trova_ruolo(self.nuova_qualifica.value, interaction.guild.roles)
        try:
            if ruolo_attuale and ruolo_attuale in self.utente.roles:
                await self.utente.remove_roles(ruolo_attuale)
                print(f"[DEBUG] Rimosso ruolo {ruolo_attuale} da {self.utente}")
            if ruolo_nuovo:
                await self.utente.add_roles(ruolo_nuovo)
                print(f"[DEBUG] Aggiunto ruolo {ruolo_nuovo} a {self.utente}")
        except discord.Forbidden:
            print("[DEBUG] Permessi insufficienti per ruoli.")
            await interaction.response.send_message("❌ Permessi insufficienti per i ruoli.", ephemeral=True)
            return
        try:
            embed_dm = discord.Embed(
                title="📈 Nuova Promozione!",
                description=(f"> **{self.qualifica_operatore.value}** {emoji_qualifica} "
                             f"sei stato promosso a **{self.nuova_qualifica.value}** {emoji_promozione} {motivazione}"),
                color=discord.Color.blue()
            )
            embed_dm.set_footer(text=f"Promosso da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            print("[DEBUG] DM non inviabile.")
        await canale.send(mess)
        await interaction.response.send_message("✅ Promozione inviata e ruoli aggiornati!", ephemeral=True)

@bot.tree.command(name="promozione-operatore", description="Promuovi un operatore compilando il form.")
@app_commands.describe(utente="Utente da promuovere")
async def promozione_operatore(interaction: Interaction, utente: discord.Member):
    print(f"[DEBUG] /promozione-operatore chiamato da {interaction.user} su {utente}")
    ruoli_aut = [819251679081791498, 896679736418381855, 815496510653333524]
    user_roles = [r.id for r in interaction.user.roles]
    if not any(r in user_roles for r in ruoli_aut):
        print("[DEBUG] Utente promotore non autorizzato.")
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(PromozioneForm(utente=utente))

# ✅ Modal: trasferimento
class TrasferimentoForm(ui.Modal, title="🔄 Form Trasferimento Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    reparto_attuale = ui.TextInput(label="Reparto attuale (NTP o SPS)", style=TextStyle.short)
    reparto_trasferimento = ui.TextInput(label="Reparto di trasferimento (NTP o SPS)", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione trasferimento (opzionale)", style=TextStyle.paragraph, required=False)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        print(f"[DEBUG] TrasferimentoForm on_submit per {self.utente} da {interaction.user}")
        canale = interaction.client.get_channel(791774585007767593)
        reparti = {
            "ntp": ("Nucleo Traduzioni e Piantonamenti", 922893733148635196),
            "sps": ("Servizio di Polizia Stradale", 819254117758664714)
        }
        def norm(v): return normalizza(v)
        att = norm(self.reparto_attuale.value)
        tra = norm(self.reparto_trasferimento.value)
        if att not in reparti or tra not in reparti:
            print("[DEBUG] Reparti non validi.")
            await interaction.response.send_message("❌ I reparti devono essere 'NTP' o 'SPS'.", ephemeral=True)
            return
        n_att, id_att = reparti[att]
        n_tra, id_tra = reparti[tra]
        emoji_qual = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        motiv = self.motivazione.value.strip() or "a seguito dell'approvazione..."
        mess = (f"> **{self.qualifica_operatore.value}** {emoji_qual} "
                f"{self.utente.mention} viene *trasferito* da **{n_att}** a **{n_tra}** {motiv}\n\n"
                f"*Autorizzato da: {interaction.user.mention}*")
        ruolo_att = interaction.guild.get_role(id_att)
        ruolo_tra = interaction.guild.get_role(id_tra)
        try:
            if ruolo_att and ruolo_att in self.utente.roles:
                await self.utente.remove_roles(ruolo_att)
                print(f"[DEBUG] Rimosso ruolo reparto {ruolo_att}")
            if ruolo_tra:
                await self.utente.add_roles(ruolo_tra)
                print(f"[DEBUG] Aggiunto ruolo reparto {ruolo_tra}")
        except discord.Forbidden:
            print("[DEBUG] Permessi insufficienti reparto.")
            await interaction.response.send_message("❌ Non ho i permessi per modificare i ruoli reparto.", ephemeral=True)
            return
        try:
            embed_dm = discord.Embed(
                title="🔄 Trasferimento Eseguito",
                description=(f"> **{self.qualifica_operatore.value}** {emoji_qual} sei stato *trasferito* da "
                             f"**{n_att}** a **{n_tra}** {motiv}"),
                color=discord.Color.dark_teal()
            )
            embed_dm.set_footer(text=f"Trasferito da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            print("[DEBUG] DM trasferimento non inviabile.")
        await canale.send(mess)
        await interaction.response.send_message("✅ Trasferimento completato!", ephemeral=True)

@bot.tree.command(name="trasferimento-operatore", description="Trasferisce un operatore in un altro reparto.")
@app_commands.describe(utente="Utente da trasferire")
async def trasferimento_operatore(interaction: Interaction, utente: discord.Member):
    print(f"[DEBUG] /trasferimento-operatore chiamato da {interaction.user} su {utente}")
    ruoli_aut = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(r.id in ruoli_aut for r in interaction.user.roles):
        print("[DEBUG] Utente trasferimento non autorizzato.")
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(TrasferimentoForm(utente=utente))

# ✅ Modal: rimprovero
class RimproveroForm(ui.Modal, title="⚠️ Form Rimprovero Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione del rimprovero", style=TextStyle.paragraph)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        print(f"[DEBUG] RimproveroForm on_submit per {self.utente} da {interaction.user}")
        canale = interaction.client.get_channel(1251591493857312779)
        emoji_qual = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        motiv = self.motivazione.value.strip()
        mess = (f"> **{self.qualifica_operatore.value}** {emoji_qual} "
                f"{self.utente.mention} riceve un **RIMPROVERO** {motiv}\n\n"
                f"*Rimproverato da: {interaction.user.mention}*")
        try:
            embed_dm = discord.Embed(
                title="⚠️ Rimprovero Ricevuto",
                description=(f"> **{self.qualifica_operatore.value}** {emoji_qual}, hai ricevuto un **rimprovero**: {motiv}"),
                color=discord.Color.red()
            )
            embed_dm.set_footer(text=f"Rimproverato da: {interaction.user.display_name}", icon_url=interaction.user.display_avatar.url)
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            print("[DEBUG] DM rimprovero non inviabile.")
        await canale.send(mess)
        await interaction.response.send_message("⚠️ Rimprovero inviato!", ephemeral=True)

@bot.tree.command(name="rimprovero-operatore", description="Rimprovera un operatore compilando il form.")
@app_commands.describe(utente="Utente da rimproverare")
async def rimprovero_operatore(interaction: Interaction, utente: discord.Member):
    print(f"[DEBUG] /rimprovero-operatore chiamato da {interaction.user} su {utente}")
    ruoli_aut = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(r.id in ruoli_aut for r in interaction.user.roles):
        print("[DEBUG] Utente rimprovero non autorizzato.")
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(RimproveroForm(utente=utente))

# ✅ Sospensione cautelare
class SospensioneCautelareForm(ui.Modal, title="⛔ Form Sospensione Cautelare"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione (opzionale)", style=TextStyle.paragraph, required=False)
    status = ui.TextInput(label="Status (Attivo o Non attivo)", style=TextStyle.short)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(1251591493857312779)
        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        motivazione = self.motivazione.value.strip()
        status_norm = self.status.value.strip().lower()

        if status_norm not in ["attivo", "non attivo"]:
            await interaction.response.send_message("❌ Lo status deve essere 'Attivo' o 'Non attivo'.", ephemeral=True)
            return

        if status_norm == "attivo":
            motivazione_testo = motivazione or "a seguito del provvedimento disposto dall'Autorità Giudiziaria"
            messaggio = (
                f"> **{self.qualifica_operatore.value}** {emoji_qualifica} {self.utente.mention} riceve la **SOSPENSIONE CAUTELARE** {motivazione_testo}\n\n"
                f"*Provvedimento disposto da: {interaction.user.mention}*"
            )
        else:
            motivazione_testo = motivazione or "a seguito dell'assoluzione disposta dall'Autorità Giudiziaria"
            messaggio = (
                f"> **{self.qualifica_operatore.value}** {emoji_qualifica} {self.utente.mention} termina la **SOSPENSIONE CAUTELARE** {motivazione_testo}\n\n"
                f"*Provvedimento revocato da: {interaction.user.mention}*"
            )

        try:
            embed_dm = discord.Embed(
                title="⛔ Provvedimento di Sospensione Cautelare",
                description=messaggio,
                color=discord.Color.orange()
            )
            embed_dm.set_footer(
                text=f"Status: {self.status.value.title()} • Eseguito da: {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        await canale.send(messaggio)
        await interaction.response.send_message("⛔ Sospensione cautelare registrata!", ephemeral=True)

@bot.tree.command(name="sospensione-cautelare", description="Registra una sospensione cautelare.")
@app_commands.describe(utente="Utente interessato dalla sospensione")
async def sospensione_cautelare(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(SospensioneCautelareForm(utente=utente))

# ✅ Interdizione operatore
class InterdizioneForm(ui.Modal, title="⛔ Form Interdizione Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione dell'interdizione", style=TextStyle.paragraph)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(1251591493857312779)
        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        motivazione = self.motivazione.value.strip()

        messaggio = (
            f"> **{self.qualifica_operatore.value}** {emoji_qualifica} "
            f"{self.utente.mention} riceve un'**INTERDIZIONE** {motivazione}\n\n"
            f"*Interdetto da: {interaction.user.mention}*"
        )

        try:
            embed_dm = discord.Embed(
                title="⛔ Interdizione Ricevuta",
                description=(
                    f"> **{self.qualifica_operatore.value}** {emoji_qualifica}, hai ricevuto un'interdizione: {motivazione}"
                ),
                color=discord.Color.dark_red()
            )
            embed_dm.set_footer(
                text=f"Interdizione da: {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        await canale.send(messaggio)
        await interaction.response.send_message("⛔ Interdizione inviata!", ephemeral=True)

@bot.tree.command(name="interdizione-operatore", description="Interdisci un operatore compilando il form.")
@app_commands.describe(utente="Utente da interdire")
async def interdizione_operatore(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(InterdizioneForm(utente=utente))


# ✅ Destituzione operatore
class DestituzioneForm(ui.Modal, title="📤 Form Destituzione Operatore"):
    qualifica_operatore = ui.TextInput(label="Qualifica Operatore", style=TextStyle.short)
    motivazione = ui.TextInput(label="Motivazione della destituzione", style=TextStyle.paragraph)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(1251591493857312779)
        emoji_qualifica = trova_emoji(self.qualifica_operatore.value, interaction.guild.emojis)
        motivazione = self.motivazione.value.strip()

        messaggio = (
            f"> **{self.qualifica_operatore.value}** {emoji_qualifica} "
            f"{self.utente.mention} viene **DESTITUITO** {motivazione}\n\n"
            f"*Destituito da: {interaction.user.mention}*"
        )

        try:
            embed_dm = discord.Embed(
                title="📤 Destituzione Ricevuta",
                description=(
                    f"> **{self.qualifica_operatore.value}** {emoji_qualifica}, hai ricevuto una destituzione: {motivazione}"
                ),
                color=discord.Color.orange()
            )
            embed_dm.set_footer(
                text=f"Destituzione da: {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        await canale.send(messaggio)
        await interaction.response.send_message("📤 Destituzione inviata!", ephemeral=True)

@bot.tree.command(name="destituzione-operatore", description="Destituisci un operatore compilando il form.")
@app_commands.describe(utente="Utente da destituire")
async def destituzione_operatore(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(DestituzioneForm(utente=utente))


# ✅ /pec
class PecForm(ui.Modal, title="Invio Comunicazione PEC"):
    oggetto = ui.TextInput(
        label="Oggetto",
        style=TextStyle.short,
        placeholder="Es: Notifica provvedimento disciplinare",
        required=True
    )
    contenuto = ui.TextInput(
        label="✒️ Contenuto del messaggio",
        style=TextStyle.paragraph,
        placeholder="Testo completo della comunicazione",
        required=True
    )
    firma = ui.TextInput(
        label="Firma (es. Grado e Nome)",
        style=TextStyle.short,
        placeholder="Es: Vice Ispettore - Mario Rossi",
        required=True
    )

    def __init__(self, destinatario: discord.Member):
        super().__init__()
        self.destinatario = destinatario

    async def on_submit(self, interaction: Interaction):
        embed = discord.Embed(
            title="Notifica Provvedimento",
            description=(
                "**Corpo di Polizia Penitenziaria**\n\n"
                f"{self.contenuto.value.strip()}\n\n"
                f"—\n*{self.firma.value.strip()}*"
            ),
            color=discord.Color.dark_blue()
        )
        embed.set_footer(
            text="Sistema di Comunicazioni Dirette – Polizia Penitenziaria",
            icon_url=interaction.client.user.avatar.url  # Logo del bot
        )

        try:
            await self.destinatario.send(embed=embed)
            await interaction.response.send_message("PEC inviata correttamente via DM.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("L'utente ha i DM disattivati.", ephemeral=True)

@bot.tree.command(name="pec", description="Invia una comunicazione ufficiale in DM.")
@app_commands.describe(destinatario="Utente destinatario della PEC")
async def pec(interaction: Interaction, destinatario: discord.Member):
    RUOLI_AUTORIZZATI = [819251679081791498, 896679736418381855, 815496510653333524]
    if not any(r.id in RUOLI_AUTORIZZATI for r in interaction.user.roles):
        await interaction.response.send_message("Non hai i permessi per usare questo comando.", ephemeral=True)
        return

    await interaction.response.send_modal(PecForm(destinatario))


# ✅ Reintegro
class ReintegroForm(ui.Modal, title="Form Reintegro Operatore"):
    reparto_assegnazione = ui.TextInput(label="Reparto di Assegnazione", style=TextStyle.short)

    def __init__(self, utente: discord.Member):
        super().__init__()
        self.utente = utente

    async def on_submit(self, interaction: Interaction):
        canale = interaction.client.get_channel(791774585007767593)
        reparto = self.reparto_assegnazione.value.strip()

        messaggio = (
            f"> L'**Agente** <:AgentePP:899769709333979197> {self.utente.mention} "
            f"conclude il corso d'aggiornamento presso la Direzione delle Scuole. "
            f"Esso viene assegnato al **{reparto}**, presso la Casa Circondariale \"G. Salvia\".\n\n"
            f"*Il suddetto {self.qualifica_operatore.value} dovrà affrontare un primo periodo di prova, "
            "della durata iniziale di nr. 7 (sette) giorni, sotto la supervisione della Direzione del Personale.*"
        )

        try:
            embed_dm = discord.Embed(
                title="Reintegro Accettato",
                description=(
                    f"L'**{self.qualifica_operatore.value}** {emoji_qualifica}, hai concluso il corso d'aggiornamento e sei assegnato al reparto {reparto}."
                ),
                color=discord.Color.green()
            )
            embed_dm.set_footer(
                text=f"Reintegrato da: {interaction.user.display_name}",
                icon_url=interaction.user.display_avatar.url
            )
            await self.utente.send(embed=embed_dm)
        except discord.Forbidden:
            pass

        await canale.send(messaggio)
        await interaction.response.send_message("Reintegro inviato correttamente!", ephemeral=True)

@bot.tree.command(name="reintegro-operatore", description="Reintegra un operatore compilando il form.")
@app_commands.describe(utente="Utente da reintegrare")
async def reintegro_operatore(interaction: Interaction, utente: discord.Member):
    ruoli_autorizzati = [896679736418381855, 815496510653333524]
    user_roles = [role.id for role in interaction.user.roles]
    if not any(role_id in user_roles for role_id in ruoli_autorizzati):
        await interaction.response.send_message("❌ Permessi insufficienti.", ephemeral=True)
        return
    await interaction.response.send_modal(ReintegroForm(utente=utente))



# 🚀 Avvio
if __name__ == "__main__":
    token = os.getenv("DISCORD_TOKEN")
    if token:
        print("[DEBUG] Avvio bot...")
        bot.run(token)
    else:
        print("[DEBUG] Variabile DISCORD_TOKEN non trovata.")
