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

        # 📩 DM embed
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
