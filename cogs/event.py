import discord
from discord.ext import commands
from utils.general import move_prison
import os
import asyncio

# Ta liste contient désormais des ID textuels
EVENT_ID = ["SALES_ROLE"] 

class Event(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        #Event sales
        channel_id_env = os.getenv('SALES_CHANNEL_ID')
        self.channel_id = int(channel_id_env) if channel_id_env else 0
        
        role_id_env = os.getenv('SALES_ROLE_ID')
        self.role_id = int(role_id_env) if role_id_env else 0
        
        if self.role_id == 0:
            print("SALES_ROLE_ID manquant ou invalide")

        #Event Prison
        self.alone_tasks = {}
        self.TIME_LIMIT = 30 * 60

    """ EVENT SALES """
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

    """ EVENT PRISON """
    @commands.Cog.listener() 
    async def on_voice_state_update(self, member, before, after):
        # On ignore si le membre n'a pas changé de salon
        if before.channel == after.channel:
            return

        def check_channel(channel):
            if not channel:
                return

            prison_id = int(os.getenv("PRISON_CHANNEL_ID"))
            if channel.id == prison_id:
                return

            # CAS 1 : Quelqu'un se retrouve seul
            if len(channel.members) == 1:
                alone_member = channel.members[0]
                if alone_member.id not in self.alone_tasks:                  
                    task = self.bot.loop.create_task(
                        move_prison(
                            alone_member,     # member
                            channel.id,       # channel_id
                            self.TIME_LIMIT,  # timelimit
                            self.alone_tasks  # alone_tasks
                        )
                    )
                    self.alone_tasks[alone_member.id] = task

            # CAS 2 : Quelqu'un rejoint, annulation des chronomètres
            elif len(channel.members) > 1:
                for current_member in channel.members:
                    if current_member.id in self.alone_tasks:
                        self.alone_tasks[current_member.id].cancel()
                        del self.alone_tasks[current_member.id]

        # 1. Vérification du salon quitté
        if before.channel:
            check_channel(before.channel)
            # Annulation de la tâche du membre qui vient de partir s'il en avait une
            if member.id in self.alone_tasks:
                self.alone_tasks[member.id].cancel()
                del self.alone_tasks[member.id]

        # 2. Vérification du salon rejoint
        if after.channel:
            check_channel(after.channel)
            
async def setup(bot):
    await bot.add_cog(Event(bot))