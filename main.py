import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True 


bot = commands.Bot(command_prefix="!", intents=intents)

async def load_extensions():
    try:
        await bot.load_extension("cogs.sales_free")
        print("✅ Cog 'SalesFree' chargé avec succès !")
        await bot.load_extension("cogs.event")
        print("✅ Cog 'Event' chargé avec succès !")
        await bot.load_extension("cogs.commandes")
        print("✅ Cog 'Event' chargé avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du Cog : {e}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

@bot.event
async def on_ready():
    await bot.tree.sync() # Obligatoire pour faire apparaître les commandes "/"
    print(f"Connecté et commandes synchronisées pour {bot.user} !")

@bot.tree.command(name="refresh_sales", description="Relance la vérification des promotions manuellement")
async def refresh_sales(interaction: discord.Interaction):
    cog = interaction.client.get_cog('SalesFree') 
    
    if cog:
        await interaction.response.send_message("Refresh en cours ...")
        await cog.check_sales()
    else:
        await interaction.response.send_message("Erreur : Le module 'SalesFree' est introuvable.", ephemeral=True)

if __name__ == "__main__":
    asyncio.run(main())