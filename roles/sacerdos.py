import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv
from utils.check import check_command, apply_cooldown
from utils.effects import mute_member
from utils.UI import VoteView

# Charger les variables .env
load_dotenv()



class Mutus(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cooldowns = {}

    """ CONFIGURATION """
    Role_Name = "SACERDOS"
    Role_ID = int(os.getenv("SACERDOS_ID"))
    SELF_MUTE = 180
    OTHER_MUTE = 120
    COOLDOWN = 2700

    """ COMMANDE /mutus """
    @app_commands.command(name="mutus", description="Le sarcados reçoit une révélation ... ou pas")
    async def mutus(self, interaction: discord.Interaction):

        ok, message = check_command(
        interaction,
        authorized_role_id=self.Role_ID,
        cooldowns=self.cooldowns,
        cooldown_seconds=self.COOLDOWN,
        command_name="mutus",
        role_name=self.Role_Name,
        require_voice=True
        )
        
        if not ok:
            await interaction.response.send_message(message, ephemeral=True)
            return
            
        apply_cooldown (interaction.user.id, "mutus", self.cooldowns)

        roll = random.uniform(0, 100)

        # 95% → RIEN
        if roll <= 90:
            await interaction.response.send_message("...")
            return

        # 1% → TU TE FAIS MUTE
        elif roll <= 92:
            asyncio.create_task(mute_member(interaction.user, self.SELF_MUTE))
            await interaction.response.send_message(
                f"{interaction.user.display_name} a soulé le divin, il s'est fait mute"
            )
            return

        # 4% → CHOIX DANS LE VOCAL
        else:
            members = [
                m for m in interaction.user.voice.channel.members
                if not m.bot and m != interaction.user
            ]

            choices = [m.display_name for m in members]
            voters = [interaction.user.id]

            async def on_vote_finish(result, original_interaction):
                if not result["valid"] or not result["winner"]:
                    return "Action annulée ou invalide."
                
                target = discord.utils.get(members, display_name=result["winner"])
                
                if target:
                    asyncio.create_task(mute_member(target, self.OTHER_MUTE))
                    return f"**{target.display_name}** a été mute par le divin grâce à {interaction.user.display_name} !"
                
                return "Erreur lors de la récupération de la cible."

            vote_view = VoteView(
                interaction=interaction,
                question="Choisis une personne à mute :",
                choices=choices,
                allowed_users=voters,
                timeout=30,
                on_finish=on_vote_finish
            )

            await interaction.response.send_message(
                embed=vote_view.build_embed(),
                view=vote_view,
                ephemeral=True
            )
            
            vote_view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(Mutus(bot))