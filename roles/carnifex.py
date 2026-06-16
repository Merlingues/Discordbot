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

class Execute(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """CONFIGURATION"""
    Role_Name = "CARNIFEX"
    Role_ID = int(os.getenv("CARNIFEX_ID"))
    COOLDOWN = 43200

    """ VOCAL KICK """
    async def vkick_member(self, member):
        if not member.voice:
            return
        await member.move_to(None)
        
    """ SERVEUR KCIK"""
    async def skick_member(self, member, *, reason: str):
        if not member.voice:
            return
        await member.kick(reason=reason)

    """COMMANDE /execute """
    @app_commands.command(name="execute", description="Execute les coupables d'infractions")
    async def execute(self, interaction: discord.Interaction, reason: str):

        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="execute",
        role_name=self.Role_Name,
        require_voice=True
        )
        
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        apply_cooldown (interaction.user.id, "execute", self.cooldowns)

        roll = random.randint(0, 1000)

        # 95% → RIEN
        if roll <= 950:
            await interaction.response.send_message(f"Un peu de patience {self.Role_Name}, dans ce vocal personne n'est coupable de {reason}")
            return

        # 4,9 % -> Kick un membre du voc sauf le CARNIFEX
        elif roll <= 999:
            
            members = [
                m for m in interaction.user.voice.channel.members
                if not m.bot and m != interaction.user
            ]
            
            perdant = random.choice(members)
            
            asyncio.create_task(self.vkick_member(perdant))
            await interaction.response.send_message(
                f"{perdant} est coupable de {reason}, {self.Role_Name} dégages moi ca"
            )
            return
        else:
            members = [
                m for m in interaction.user.voice.channel.members
                if not m.bot and m != interaction.user
            ]

            perdant = random.choice(members)

            asyncio.create_task(self.skick_member(perdant, reason=reason))
            await interaction.response.send_message(
                f"{perdant} à été kick du serveur, pour la gravité de son crime : **{reason.upper()}**"
            )

async def setup(bot):
    await bot.add_cog(Execute(bot))