import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv
from utils.check import check_command, apply_cooldown
from utils.general import send_image, vchange_member, random_salon

load_dotenv()

class Pêche(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """CONFIGURATION"""
    Role_Name = "HALIEUS"
    Role_ID = int(os.getenv("HALIEUS_ID"))
    COOLDOWN = 2700

    """COMMANDE /pêche """
    @app_commands.command(name="pêche", description="Chasse une mouche")
    async def pêche(self, interaction: discord.Interaction):

        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="pêche",
        role_name=self.Role_Name,
        require_voice=True
        )
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
        
        apply_cooldown (interaction.user.id, "pêche", self.cooldowns)

        salon_id, salon_name = await random_salon(member=interaction.user)
        url_colere = os.getenv("COLERE_URL")

        poisson = {
            "Sparus aurata": {
                "poid": [0.1, 3.0], 
                "url": os.getenv("GOUJON_URL")
            },
            "Dicentrarchus labrax": {
                "poid": [3.1, 10.0], 
                "url": os.getenv("BAR_URL")
            },
            "Muraena helena": {
                "poid": [10.1, 15.0], 
                "url": os.getenv("MURENA_URL")
            },
            "Conger conger": {
                "poid": [15.1, 45.0], 
                "url": os.getenv("CONGRE_URL")
            },
            "Thunnus thynnus": {
                "poid": [45.1, 90.0], 
                "url": os.getenv("THON_URL")
            }
        }

        roll = random.randint(0, 1000)
        poid = roll / 10


        if poid <= 3.0:
            nom_poisson = "Sparus aurata"
            url_poisson = poisson[nom_poisson]["url"]
        elif poid <= 10.0:
            nom_poisson = "Dicentrarchus labrax"
            url_poisson = poisson[nom_poisson]["url"]
        elif poid <= 15.0:
            nom_poisson = "Muraena helena"
            url_poisson = poisson[nom_poisson]["url"]
        elif poid <= 45:
            nom_poisson = "Conger conger"
            url_poisson = poisson[nom_poisson]["url"]
        else:
            nom_poisson = "Thunnus thynnus"
            url_poisson = poisson[nom_poisson]["url"]


        if roll <= 900 :
            texte_poisson = f"Le grand {self.Role_Name.lower()} à pêcher un {nom_poisson} de {poid} kg"
            await send_image(interaction=interaction, description=texte_poisson, image_url=url_poisson, color=discord.Color.blue())

        elif roll <= 920 :
            await vchange_member(member=interaction.user, salon_cible=salon_id)
            texte_colere = f"Posëidon est en colère contre le grand {self.Role_Name.lower()}.\n Il s'est fait bouger dans le channel : {salon_name}."
            
            await send_image(interaction=interaction, description=texte_colere, image_url=url_colere, color=discord.Color.red())
        else:
            members = [                
                m for m in interaction.user.voice.channel.members
                if not m.bot and m != interaction.user
            ]

            perdant = random.choice(members)

            await vchange_member(member=perdant, salon_cible=salon_id)
            texte_colere = f"Posëidon est en colère contre le grand {perdant.display_name}.\n Il s'est fais bouger dans le channel : {salon_name}."
            await send_image(interaction=interaction, description=texte_colere, image_url=url_colere, color=discord.Color.red())

async def setup(bot):
    await bot.add_cog(Pêche(bot))