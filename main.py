import discord
from discord import app_commands
from discord.ext import commands
import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True 
intents.voice_states = True    
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    # On synchronise globalement (prend un peu plus de temps à apparaître, mais pas besoin d'ID)
    await bot.tree.sync()
    print(f"✅ Bot prêt ! Toutes les commandes ont été synchronisées globalement pour {bot.user}")
    
async def load_extensions():
    try:
        await bot.load_extension("cogs.sales_free")
        print("✅ Cog 'SalesFree' chargé avec succès !")
        await bot.load_extension("cogs.event")
        print("✅ Cog 'Event' chargé avec succès !")
        await bot.load_extension("cogs.commands")
        print("✅ Cog 'commands' chargé avec succès !")
        await bot.load_extension("roles.sacerdos")
        print("✅ Role 'Sacerdos' chargé avec succès")
        await bot.load_extension("roles.poliorcetiste")
        print("✅ Role 'Poliorcetiste' chargé avec succès")
    except Exception as e:
        print(f"❌ Erreur lors du chargement du Cog : {e}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))


if __name__ == "__main__":
    asyncio.run(main())