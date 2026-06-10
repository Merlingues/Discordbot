import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv

# Charger les variables .env
load_dotenv()


class Mutus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """ CONFIGURATION """
    Role_Name = "SACARDOS"
    ROLE_AUTORISE_ID = int(os.getenv("ROLE_AUTORISE_ID"))
    MUTE_DURATION_SELF = 300
    MUTE_DURATION_OTHER = 120
    COOLDOWN = 2700

    """ VERIFICATION ROLE + COOLDOWN """
    def check_conditions(self, interaction: discord.Interaction):
        user = interaction.user

        # Vérif rôle
        if self.ROLE_AUTORISE_ID not in [r.id for r in user.roles]:
            return False, f"Seuls les {self.Role_Name} peuvent utiliser cette commande"

        # Vérif vocal
        if not user.voice or not user.voice.channel:
            return False, "Tu dois être dans un vocal pour utiliser cette commande."

        # Vérif cooldown
        last_use = self.cooldowns.get(user.id, 0)
        if time.time() - last_use < self.COOLDOWN:
            remaining = int(self.COOLDOWN - (time.time() - last_use))
            minutes = remaining // 60
            return False, f"Commande en cooldown : {minutes} minutes restantes."

        return True, None

    """ MUTE VOCAL """
    async def mute_member(self, member: discord.Member, duration: int):
        if not member.voice:
            return

        await member.edit(mute=True)
        await asyncio.sleep(duration)

        if member.voice:
            await member.edit(mute=False)

    """ COMMANDE /mutus """
    @app_commands.command(name="mutus", description="Le sarcados reçoit une révélation ... ou pas")
    async def mutus(self, interaction: discord.Interaction):

        ok, message = self.check_conditions(interaction)
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return

        # Appliquer cooldown
        self.cooldowns[interaction.user.id] = time.time()

        roll = random.uniform(0, 100)

        # 99% → RIEN
        if roll <= 99:
            await interaction.response.send_message("...")
            return

        # 0.1% → TU TE FAIS MUTE
        elif roll <= 99.1:
            await self.mute_member(interaction.user, self.MUTE_DURATION_SELF)
            await interaction.response.send_message(
                f"{interaction.user.display_name} a soulé le divin, il s'est fait mute"
            )
            return

        # 0.9% → CHOIX DANS LE VOCAL
        else:
            members = [m for m in interaction.user.voice.channel.members if not m.bot]

            if len(members) <= 1:
                await interaction.response.send_message("Tu es solo mon reuf.", ephemeral=True)
                return

            try:
                await interaction.user.send(
                    "Choisis une personne à mute :\n" +
                    "\n".join([m.display_name for m in members if m != interaction.user])
                )
            except:
                await interaction.response.send_message("MP bloqués. ❌", ephemeral=True)
                return

            await interaction.response.send_message("Regarde tes MP 👀", ephemeral=True)

            def check(msg):
                return msg.author == interaction.user and isinstance(msg.channel, discord.DMChannel)

            try:
                reply = await self.bot.wait_for("message", check=check, timeout=30)
            except:
                await interaction.user.send("Temps écoulé.")
                return

            target = discord.utils.find(
                lambda m: m.display_name == reply.content,
                members
            )

            if not target or target == interaction.user:
                await interaction.user.send("Choix invalide.")
                return

            await self.mute_member(target, self.MUTE_DURATION_OTHER)
            await interaction.user.send(
                f"{target.display_name} a été mute par le divin grâce à {interaction.user.display_name}"
            )

class SalesCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="refresh_sales", description="Relance la vérification des promotions manuellement")
    async def refresh_sales(self, interaction: discord.Interaction):
        cog = self.bot.get_cog('SalesFree') 
        
        if cog:
            await interaction.response.send_message("Refresh en cours ...")
            await cog.check_sales()
        else:
            await interaction.response.send_message("Erreur : Le module 'SalesFree' est introuvable.", ephemeral=True)



async def setup(bot):
    await bot.add_cog(Mutus(bot))