import discord
from discord.ext import commands
import aiohttp
import re
import unicodedata

class ReactionInsulte(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.insultes = set()
        # Lien brut vers une liste publique reconnue de gros mots en français
        self.url_liste = "https://raw.githubusercontent.com/LDNOOBW/List-of-Dirty-Naughty-Obscene-and-Otherwise-Bad-Words/master/fr"

    @commands.Cog.listener()
    async def on_ready(self):
        print("Moderation cog is ready!")
        await self.ensure_notification_message()
    
    async def cog_load(self):
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url_liste) as response:
                    if response.status == 200:
                        texte = await response.text()
                        self.insultes = set(texte.splitlines())
                        print(f"Liste des insultes chargée : {len(self.insultes)} mots.")
        except Exception as e:
            print(f"Erreur lors du chargement de la liste d'insultes : {e}")

    def normaliser_texte(self, texte):
        """Supprime les accents et passe en minuscules pour intercepter 'toutes les formes'."""
        texte = unicodedata.normalize('NFD', texte).encode('ascii', 'ignore').decode('utf-8')
        return texte.lower()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        texte_propre = self.normaliser_texte(message.content)

        # Expression régulière pour détecter "saint truc", "saints trucs", "saint-truc", "sainttruc", etc.
        if re.search(r'saints?\W*trucs?', texte_propre):
            
            # Découpe le message de l'utilisateur en mots individuels (sans la ponctuation)
            mots_du_message = set(re.findall(r'\b\w+\b', texte_propre))
            
            # Vérifie s'il y a une intersection (au moins un mot en commun) entre le message et la liste web
            if mots_du_message.intersection(self.insultes):
                await message.reply(f"{message.author.display_name} simple mortel, ton arrogance ne m'atteint pas")

async def setup(bot):
    await bot.add_cog(ReactionInsulte(bot))