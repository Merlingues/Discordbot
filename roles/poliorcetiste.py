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

class Catapulte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """CONFIGURATION"""
    Role_Name = "POLIORCETISTE"
    Role_ID = int(os.getenv("POLIORCETISTE_ID"))
    SELF_DEAFEN = 180
    OTHER_DEAFEN = 120
    COOLDOWN = 2700

    """ DEAFEN VOCAL """
    async def deafen_member(self, member, duration):
        if not member.voice:
            return

        await member.edit(deafen=True)
        await asyncio.sleep(duration)

        if member.voice:
            await member.edit(deafen=False)

    """COMMANDE /catapulte """
    @app_commands.command(name="catapulte", description="Tentative de tir de la pars du Poliorcetiste")
    async def catapulte(self, interaction: discord.Interaction):

        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="catapulte",
        role_name=self.Role_Name,
        require_voice=True
        )
        
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        apply_cooldown (interaction.user.id, "catapulte", self.cooldowns)

        roll = random.uniform(0, 100)
        degree = 95 - roll
        direction = random.randint(0, 3)
        if direction == 0:
            direction = "Nord"
        elif direction == 1:
            direction = "Sud"
        elif direction == 2:
            direction = "Est"
        else:
            direction = "Ouest"


        # 95% → RIEN
        if roll <= 95:
            await interaction.response.send_message(f"Le {self.Role_Name} a loupé son tir de {degree}° {direction}")
            return

        # 1% → TU TE FAIS MUTE
        elif roll <= 96:
            asyncio.create_task(self.deafen_member(interaction.user, self.SELF_DEAFEN))
            await interaction.response.send_message(
                f"{interaction.user.display_name} s'est tiré dessus, il s'est mis en sourdine tout seul"
            )
            return
        else:
            members = [                
                m for m in interaction.user.voice.channel.members
                if not m.bot and m != interaction.user
            ]

            perdant = random.choice(members)

            asyncio.create_task(self.deafen_member(perdant, self.OTHER_DEAFEN))
            await interaction.response.send_message(
                f"{interaction.user.display_name} a tire en plein dans la maison de {perdant}, il est devenu sourd"
            )

async def setup(bot):
    await bot.add_cog(Catapulte(bot))