import asyncio
import discord
from discord.ext import commands, tasks
import aiohttp
import os
from cogs.event import EVENT_ID

class SalesFree(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        # ----------------------------------------
        # Regroupement des variables principales
        # ----------------------------------------
        self.channel_id = int(os.getenv('SALES_CHANNEL_ID', 0))
        sales_role_event_id = os.getenv('SALES_ROLE_ID')
        self.sales_role_event_mention = f"<@&{sales_role_event_id}>" if sales_role_event_id else None
        
        # Headers pour les requêtes aiohttp
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_sales.is_running():
            self.check_sales.start()

    # ----------------------------------------
    # Boucle principale (Toutes les 4 heures)
    # ----------------------------------------
    @tasks.loop(hours=4)
    async def check_sales(self):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"Channel ID wrong or empty : {self.channel_id}")
            return
            
        print("Recherche des jeux gratuits en cours...")
        current_games = await self.get_current_sales()
        
        # Nettoyage des ventes terminées puis publication des nouvelles
        await self.clean_done_sales(channel, current_games)
        await self.post_new_sales(channel, current_games)

    async def get_current_sales(self):
        all_games = []
        epic_sales = await self.get_epic_sales()
        steam_sales = await self.get_steam_sales()
        
        all_games.extend(epic_sales)
        all_games.extend(steam_sales)
        return all_games

    # ----------------------------------------
    # Scrapper : Epic Games Store (Via API GamerPower)
    # ----------------------------------------
    async def get_epic_sales(self):
        # Utilisation de GamerPower pour contourner l'instabilité de l'API Epic Games
        url = "https://www.gamerpower.com/api/giveaways?platform=epic-games-store&type=game"
        games_found = []

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                timeout = aiohttp.ClientTimeout(total=8)
                async with session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        print(f"Erreur GamerPower API (Epic) : {response.status}")
                        return []
                    items = await response.json()
            except Exception as e:
                print(f"Erreur de connexion GamerPower (Epic) : {e}")
                return []

            if not isinstance(items, list):
                return []

            for item in items:
                if item.get('status') != "Active":
                    continue

                title = item.get('title')
                game_url = item.get('open_giveaway')
                image_url = item.get('image') or item.get('thumbnail')
                
                raw_price = item.get('worth', '0.00')
                old_price = raw_price.replace('$', '') if raw_price != "N/A" else "0.00"
                
                description = item.get('description', 'Jeu gratuit sur Epic Games !')
                game_id = item.get('id')

                games_found.append({
                    'id': f"gamerpower_epic_{game_id}",
                    'title': title,
                    'url': game_url,
                    'old_price': old_price,
                    'image': image_url,
                    'tags': ["Epic Games |", "Giveaway"],
                    'description': description
                })

        print(f"Recherche Epic Games terminée : {len(games_found)} jeu(x) trouvé(s)")
        return games_found

    # ----------------------------------------
    # Scrapper : Steam (Via API GamerPower)
    # ----------------------------------------
    async def get_steam_sales(self):
        url = "https://www.gamerpower.com/api/giveaways?platform=steam&type=game"
        games_found = []

        async with aiohttp.ClientSession(headers=self.headers) as session:
            try:
                timeout = aiohttp.ClientTimeout(total=8)
                async with session.get(url, timeout=timeout) as response:
                    if response.status != 200:
                        print(f"Erreur GamerPower API (Steam) : {response.status}")
                        return []
                    items = await response.json()
            except Exception as e:
                print(f"Erreur de connexion GamerPower (Steam) : {e}")
                return []

            if not isinstance(items, list):
                return []

            for item in items:
                if item.get('status') != "Active":
                    continue

                title = item.get('title')
                game_url = item.get('open_giveaway')
                image_url = item.get('image') or item.get('thumbnail')
                
                raw_price = item.get('worth', '0.00')
                old_price = raw_price.replace('$', '') if raw_price != "N/A" else "0.00"
                
                description = item.get('description', 'Jeu gratuit sur Steam !')
                game_id = item.get('id')

                games_found.append({
                    'id': f"gamerpower_steam_{game_id}",
                    'title': title,
                    'url': game_url,
                    'old_price': old_price,
                    'image': image_url,
                    'tags': ["Steam |", "Giveaway"],
                    'description': description
                })

        print(f"Recherche Steam terminée : {len(games_found)} jeu(x) trouvé(s)")
        return games_found

    # ----------------------------------------
    # Gestion de l'affichage (Discord Embeds)
    # ----------------------------------------
    async def clean_done_sales(self, channel, current_games):
        current_ids = {game['id'] for game in current_games}
        async for message in channel.history(limit=100):
            if message.author != self.bot.user:
                await message.delete()
                continue
            
            if not message.embeds:
                await message.delete()
                continue

            embed = message.embeds[0]
            footer_text = embed.footer.text if embed.footer else None

            if footer_text and footer_text in EVENT_ID:
                continue
            
            msg_games_id = footer_text.replace("ID: ", "") if footer_text else None

            if msg_games_id not in current_ids:
                await message.delete()
                print(f"Jeu expiré supprimé : {msg_games_id}")

    async def post_new_sales(self, channel, current_games):
        already_posted_ids = []

        async for message in channel.history(limit=100):
            if message.author == self.bot.user and message.embeds:
                footer = message.embeds[0].footer.text
                if footer:
                    clean_id = footer.replace("ID: ", "")
                    already_posted_ids.append(clean_id)
                    
        for game in current_games:
            if game['id'] not in already_posted_ids:
                price_text = f"~~{game['old_price']}€~~ **-100 %**"
                desc_text = game.get('description', 'Pas de description disponible')
                description = desc_text[:200] + "..."
                
                if self.sales_role_event_mention:
                    description += f"\n\n{self.sales_role_event_mention}"
                    
                embed = discord.Embed(
                    title=game['title'],
                    url=game['url'],
                    description=description,
                    color=0x87CEEB
                )

                image_url = game.get('image')
                if image_url:
                    embed.set_image(url=game['image']) 

                embed.add_field(name="Prix", value=price_text, inline=False)

                tags = game.get('tags', [])
                if tags:
                    formatted_tags = " ".join([f"`{tag}`" for tag in tags[:5]])
                    embed.add_field(name="Tags", value=formatted_tags, inline=False)

                embed.set_footer(text=f"ID: {game['id']}")
                await channel.send(embed=embed)
                print(f"Nouveau jeu gratuit publié : {game['title']}")

async def setup(bot):
    await bot.add_cog(SalesFree(bot))