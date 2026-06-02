import discord
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
    except Exception as e:
        print(f"❌ Erreur lors du chargement du Cog : {e}")


async def main():
    async with bot:
        await load_extensions()
        await bot.start(os.getenv('DISCORD_TOKEN'))

@bot.command()
async def refresh_sales(ctx):
    cog = bot.get_cog('SalesFree')
    if cog:
        await ctx.send("Refresh en cours ...")
        await cog.check_sales()

if __name__ == "__main__":
    asyncio.run(main())