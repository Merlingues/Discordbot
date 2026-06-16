import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import os
from dotenv import load_dotenv
from utils.check import check_command, apply_cooldown
from utils.effects import mute_member, deafen_member

# Charger les variables .env
load_dotenv()

class Embobine(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """CONFIGURATION"""
    Role_Name = "SOPHISTE"
    Role_ID = int(os.getenv("SOPHISTE_ID"))
    COOLDOWN = 2700
    DURATION = 120
    
    """COMMANDE /embobine"""
    @app_commands.command(name="embobine", description="Embobine tout le groupe et transfère un effet actif sur l'ensemble des personnes au sein du vocal")
    async def embobine(self, interaction: discord.Interaction):
        
        """PHASE DE TEST"""
        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="embobine",
        role_name=self.Role_Name,
        require_voice=True
        )
        
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        effect = self.bot.shared.get("effect", None)
        
        if effect is None:
            await interaction.response.send_message("Personne n'a d'effet, il n'est donc pas possible d'embobiner quelqu'un.", ephemeral=True)
            return
        
        apply_cooldown(interaction.user.id, "embobine", self.cooldowns)
        
        """APPLICATION DES EFFETS A TOUS LES MEMBRES"""
        members = [m for m in interaction.user.voice.channel.members if not m.bot]
        
        if effect == "mute":
            for member in members:
                asyncio.create_task(mute_member(member, self.DURATION))
            await interaction.response.send_message(f"**{interaction.user.display_name}** le {self.Role_Name.lower()} a rendu muet tout le monde.")
        elif effect == "deafen":
            for member in members:
                asyncio.create_task(deafen_member(member, self.DURATION))
            await interaction.response.send_message(f"**{interaction.user.display_name}** le {self.Role_Name.lower()} a assourdi tout le monde.")

async def setup(bot):
    await bot.add_cog(Embobine(bot))
