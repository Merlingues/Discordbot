import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv
from utils.check import check_command, apply_cooldown
from utils.audio import play_youtube_sound

# Charger les variables .env
load_dotenv()

class Execute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """CONFIGURATION"""
    Role_Name = "MUSCAE CAPTOR"
    Role_ID = int(os.getenv("MUSCAE_CAPTOR_ID"))
    COOLDOWN = 3600

    """COMMANDE /bzzzz """
    @app_commands.command(name="bzzzz", description="Chasse une mouche")
    async def bzzzz(self, interaction: discord.Interaction, reason: str):

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
        await play_youtube_sound(interaction, url)
        url2 = "https://www.youtube.com/watch?v=ISsYS8KarW4"
        await play_youtube_sound(interaction, url2)
        await interaction.delete_original_response()