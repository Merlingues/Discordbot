import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv
from utils.check import check_command, apply_cooldown

# Charger les variables .env
load_dotenv()



class Mutus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """ CONFIGURATION """
    Role_Name = "SACERDOS"
    Role_ID = int(os.getenv("SACERDOS_ID"))
    SELF_MUTE = 300
    OTHER_MUTE = 120
    COOLDOWN = 2700


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

        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="mutus",
        role_name=self.Role_Name,
        require_voice=True
        )
        
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
            
        apply_cooldown (interaction.user.id, "mutus", self.cooldowns)

        roll = random.uniform(0, 100)

        # 99% → RIEN
        if roll <= 95:
            await interaction.response.send_message("...")
            return

        # 1% → TU TE FAIS MUTE
        elif roll <= 96:
            asyncio.create_task(self.mute_member(interaction.user, self.SELF_MUTE))
            await interaction.response.send_message(
                f"{interaction.user.display_name} a soulé le divin, il s'est fait mute"
            )
            return

        # 4% → CHOIX DANS LE VOCAL
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

            asyncio.create_task(self.mute_member(target, self.OTHER_MUTE))
            await interaction.user.send(
                f"{target.display_name} a été mute par le divin grâce à {interaction.user.display_name}"
            )

async def setup(bot):
    await bot.add_cog(Mutus(bot))