import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv
from utils.check import check_command, apply_cooldown
from utils.audio import add_musique

# Charger les variables .env
load_dotenv()

class Bzzzz(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """CONFIGURATION"""
    Role_Name = "MUSCAE CAPTOR"
    Role_ID = int(os.getenv("MUSCAE_CAPTOR_ID"))
    COOLDOWN = 3600

    """COMMANDE /bzzzz """
    @app_commands.command(name="bzzzz", description="Chasse une mouche")
    async def bzzzz(self, interaction: discord.Interaction):

        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="bzzzz",
        role_name=self.Role_Name,
        require_voice=True
        )
        
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        apply_cooldown (interaction.user.id, "bzzzz", self.cooldowns)
        
        """ LANCEMENT DU SON DE LA MOUCHE """
        url = "https://www.youtube.com/watch?v=bcuKTheCcsE"
        await interaction.response.defer(ephemeral=True)
        await add_musique(interaction, url)
        url2 = "https://www.youtube.com/watch?v=ISsYS8KarW4"
        await add_musique(interaction, url2)
        await interaction.delete_original_response()

async def setup(bot):
    await bot.add_cog(Bzzzz(bot))