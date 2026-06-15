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
    await bot.add_cog(SalesCommands(bot))