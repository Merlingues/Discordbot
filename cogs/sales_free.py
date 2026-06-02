import asyncio
import discord
from discord.ext import commands, tasks
import aiohttp
import os
from bs4 import BeautifulSoup
from cogs.event import EVENT_ID

class SalesFree(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.channel_id = int(os.getenv('SALES_CHANNEL_ID'))
        sales_role_event_id = os.getenv('SALES_ROLE_ID')
        self.sales_role_event_mention = f"<@&{sales_role_event_id}>" if sales_role_event_id else None

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.check_sales.is_running():
            self.check_sales.start()

    @tasks.loop(hours=4)
    async def check_sales(self):
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"Channel ID wrong or empty : {self.channel_id}")
            return
        # Récupération des jeux gratuit via une fonction, défini hors de la boucle
        current_games = await self.get_current_sales()
        # Nettoyage des sales terminées
        await self.clean_done_sales(channel, current_games)
        # Publication des nouvelles sales
        await self.post_new_sales(channel, current_games)

    # Sous-fonction pour récupérer les jeux gratuits
    async def get_current_sales(self):
        # variables de stockage des jeux en réduction à 100%
        all_games = []
        # Récupération des données des APIs Steam et Epic Games
        epic_sales = await self.get_epic_sales()
        steam_sales = await self.get_steam_sales()
        # Ajout des jeux en réduction à 100% à la liste
        all_games.extend(epic_sales)
        all_games.extend(steam_sales)
        # Sortie de tous les jeux en réduction à 100%
        return all_games

    async def get_epic_sales(self):
        url = "https://store-site-backend-static.ak.epicgames.com/freeGamesPromotions"
        games_found = []

        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                data = await response.json()
                items = data['data']['Catalog']['searchStore']['elements']
                for item in items:
                    promotions = item.get('promotions')
                    if not promotions:
                        continue
                    sales_info = item['price']['totalPrice']
                    before_sales = sales_info['originalPrice']
                    after_sales = sales_info['discountPrice']
                    if before_sales > 0 and after_sales == 0:
                        tags = [cat.get('name') for cat in item.get('categories', []) if cat.get('name') and cat.get('name') != 'Games']
                        image = None
                        for img in item.get('keyImages', []):
                            image = img.get('url')
                            break

                        mappings = item.get('offerMappings', [])
                        if mappings and len(mappings) > 0:
                            slug = mappings[0].get('pageSlug')
                            game_url = f"https://store.epicgames.com/fr/p/{slug}"
                        else:
                            slug = None
                            search_query = f"{item['title']} Epic Games Store"
                            game_url = f"https://www.google.com/search?q={search_query.replace(' ', '+')}"

                        Epic_sale = {
                            'id': f"epic_{item['id']}",
                            'title': item['title'],
                            'old_price': before_sales / 100,
                            'description': item.get('description', 'Pas de description disponible'),
                            'url': game_url,
                            'tags': tags,
                            'image': image
                        }
                        games_found.append(Epic_sale)
        return games_found
    
    async def get_steam_sales(self):
        url = "https://www.cheapshark.com/api/1.0/deals?storeID=1&upperPrice=0"
        games_found = []
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(url) as response:
                if response.status != 200:
                    print(f"Erreur CheapShark : {response.status}")
                    return []

                data = await response.json()

                for item in data:
                    game_id = item.get('steamAppID')
                    
                    if not game_id:
                        continue
                        
                    title = item.get('title')
                    game_url = f"https://store.steampowered.com/app/{game_id}/"
                    old_price = item.get('normalPrice', 'N/A')
                    
                    image_url = f"https://cdn.akamai.steamstatic.com/steam/apps/{game_id}/header.jpg"

                    tags = ["Steam |"]
                    steam_api_url = f"https://store.steampowered.com/api/appdetails?appids={game_id}&l=french"

                    async with session.get(steam_api_url) as steam_resp:
                        if steam_resp.status == 200:
                            details = await steam_resp.json()
                            if details and details.get(str(game_id), {}).get('success'):
                                data = details[str(game_id)]['data']
                                genres = data.get('genres', [])
                                for genre in genres[:3]:
                                    tags.append(genre.get('description'))

                    games_found.append({
                        'id': f"steam_{game_id}",
                        'title': title,
                        'url': game_url,
                        'old_price': f"{old_price}€",
                        'image': image_url,
                        'tags': tags
                    })

            return games_found

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
                print(f"Deleted message for game ID: {msg_games_id}")

    async def post_new_sales(self, channel, current_games):
        already_posted_ids = []

        async for message in channel.history(limit=100):
            if message.author == self.bot.user and message.embeds:
                footer = message.embeds[0].footer.text
                if footer :
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
                    url = game['url'],
                    description = description,
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

async def setup(bot):

    await bot.add_cog(SalesFree(bot))