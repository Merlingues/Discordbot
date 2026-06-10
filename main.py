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

@bot.event
async def on_ready():
    # On synchronise l'arbre ici, une fois que le bot est prêt et les cogs chargés
    await bot.tree.sync()
    print(f"Connecté et commandes synchronisées pour {bot.user} !")
    
async def load_extensions():
    try:
        await bot.load_extension("cogs.sales_free")
        print("✅ Cog 'SalesFree' chargé avec succès !")
        await bot.load_extension("cogs.event")
        print("✅ Cog 'Event' chargé avec succès !")
        await bot.load_extension("cogs.commands")
        print("✅ Cog 'Event' chargé avec succès !")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du Cog : {e}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))


if __name__ == "__main__":
    asyncio.run(main())