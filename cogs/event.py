import discord
from discord.ext import commands
import os

# Ta liste contient désormais des ID textuels
EVENT_ID = ["SALES_ROLE"] 

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        
        channel_id_env = os.getenv('SALES_CHANNEL_ID')
        self.channel_id = int(channel_id_env) if channel_id_env else 0
        
        role_id_env = os.getenv('SALES_ROLE_ID')
        self.role_id = int(role_id_env) if role_id_env else 0
        
        if self.role_id == 0:
            print("SALES_ROLE_ID manquant ou invalide")

    @commands.Cog.listener()
    async def on_ready(self):
        print("Event cog is ready!")
        await self.ensure_notification_message()

    async def ensure_notification_message(self):
        if self.channel_id == 0:
            return
            
        channel = self.bot.get_channel(self.channel_id)
        if not channel:
            print(f"Channel not found: {self.channel_id}")
            return

        # Vérification si le message existe déjà en lisant les footers
        async for message in channel.history(limit=50):
            if message.embeds:
                embed = message.embeds[0]
                if embed.footer.text == "SALES_ROLE":
                    if not message.pinned:
                        await message.pin()
                    await self.add_reaction_if_missing(message)
                    return

        # Si non trouvé, on le crée
        embed = discord.Embed(
            title="Bienvenue à la Popina",
            description="@everyone\nVoici la carte de notre popina, où tu y trouveras tous les jeux actuellement en promotion à 100%, clique sur la cloche pour être notifié des prochaines promotions",
            color=0x87CEEB
        )
        embed.set_footer(text="SALES_ROLE") # L'ID texte est placé ici

        message = await channel.send(embed=embed)
        await message.pin()
        await message.add_reaction("🔔")

    async def add_reaction_if_missing(self, message):
        for reaction in message.reactions:
            if str(reaction.emoji) == "🔔":
                return
        await message.add_reaction("🔔")

    @commands.Cog.listener()
    async def on_message_delete(self, message):
        # Si un message est supprimé, on vérifie si son footer contient notre ID texte
        if message.embeds:
            if message.embeds[0].footer.text == "SALES_ROLE":
                print("Le message d'événement a été supprimé ! Recréation en cours...")
                await self.ensure_notification_message()

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):
        if str(payload.emoji) != "🔔":
            return
        if payload.user_id == self.bot.user.id:
            return

        # 1. On récupère le salon
        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        # 2. On récupère le message complet pour pouvoir lire son embed
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not message.embeds:
            return
            
        # 3. On compare le texte du footer avec notre liste EVENT_ID
        if message.embeds[0].footer.text not in EVENT_ID:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = payload.member or guild.get_member(payload.user_id)
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                return

        role = guild.get_role(self.role_id)
        if not role:
            print(f"Role not found: {self.role_id}")
            return
            
        if role not in member.roles:
            await member.add_roles(role)
            print(f"Added role {role.name} to {member.display_name}")

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):
        if str(payload.emoji) != "🔔":
            return
        if payload.user_id == self.bot.user.id:
            return

        channel = self.bot.get_channel(payload.channel_id)
        if not channel:
            return
            
        try:
            message = await channel.fetch_message(payload.message_id)
        except discord.NotFound:
            return

        if not message.embeds:
            return
            
        if message.embeds[0].footer.text not in EVENT_ID:
            return

        guild = self.bot.get_guild(payload.guild_id)
        if not guild:
            return

        member = guild.get_member(payload.user_id)
        if not member:
            try:
                member = await guild.fetch_member(payload.user_id)
            except discord.NotFound:
                return

        role = guild.get_role(self.role_id)
        if not role:
            print(f"Role not found: {self.role_id}")
            return
            
        if role in member.roles:
            await member.remove_roles(role)
            print(f"Removed role {role.name} from {member.display_name}")

async def setup(bot):
    await bot.add_cog(Event(bot))