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

        salon_id, salon_name = random_salon(member=interaction.user)
        url_colere = "https://cdn.shopify.com/s/files/1/0655/2633/3707/files/greek-mythology-god-poseido_480x480.jpg?v=1726238198"
        poisson = {
            "Goujon d'Aristote": {
                "poid": [0.1, 3.0],
                "url": "https://cdn.discordapp.com/attachments/TON_ID/image_petit.jpg"
            },
            "Bar de Phocée": {
                "poid": [3.1, 10.0],
                "url": "https://cdn.discordapp.com/attachments/TON_ID/image_moyen.jpg"
            },
            "Murène de Crète": {
                "poid": [10.1, 15.0],
                "url": "https://cdn.discordapp.com/attachments/TON_ID/image_murene.jpg"
            },
            "Thon rouge de Sicile": {
                "poid": [15.1, 45.0],
                "url": "https://cdn.discordapp.com/attachments/TON_ID/image_thon.jpg"
            },
            "Monstre des abysses de Charybde": {
                "poid": [45.1, 95.0],
                "url": "https://cdn.discordapp.com/attachments/TON_ID/image_monstre.jpg"
            }
        }

        roll = random.randint(0, 1000)
        poid = roll / 10


        if poid <= 3.0:
            nom_poisson = "Goujon d'Aristote"
            url_poisson = poisson[nom_poisson]["url"]
        elif poid <= 10.0:
            nom_poisson = "Bar de Phocée"
            url_poisson = poisson[nom_poisson]["url"]
        elif poid <= 15.0:
            nom_poisson = "Murène de Crète"
            url_poisson = poisson[nom_poisson]["url"]
        elif poid <= 90:
            nom_poisson = "Thon rouge de Sicile"
            url_poisson = poisson[nom_poisson]["url"]
        else:
            nom_poisson = "Monstre des abysses de Charybde"
            url_poisson = poisson[nom_poisson]["url"]


        if roll <= 950 :
            await interaction.response.send_message(
                f"Le grand {self.Role_Name.lower()} à pêcher un {nom_poisson} de {poid} kg"
            )
            await send_image(destination=interaction.channel, source=url_poisson, local=False)

        elif roll <= 960 :
            await vchange_member(member=interaction.user, salon_cible=salon_id)
            await interaction.response.send_message(
                f"Posëidon est en colère contre le grand {self.Role_Name.lower()}.\n Il s'est fais bouger dans le channel : {salon_name}."
            )
            await send_image(destination=interaction.channel, source=url_colere, local=False)
        else:
            members = [                
                m for m in interaction.user.voice.channel.members
                if not m.bot and m != interaction.user
            ]

            perdant = random.choice(members)

            vchange_member(member=perdant, salon_cible=salon_id)
            await interaction.response.send_message(
                f"Posëidon est en colère contre le grand {perdant.display_name}.\n Il s'est fais bouger dans le channel : {salon_name}."
            )
            await send_image(destination=interaction.channel, source=url_colere, local=False)

async def setup(bot):
    await bot.add_cog(Pêche(bot))