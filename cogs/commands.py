import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv
from utils.audio import (
    add_musique, add_playlist, quit_vocal, 
    skip_musique, now_playing, pause_musique, 
    resume_musique, check_vocal_access
)
from utils.UI import VoteView

# Charger les variables .env
load_dotenv()



class SalesCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(name="refresh_sales", description="Relance la vérification des promotions manuellement")
    async def refresh_sales(self, interaction: discord.Interaction):
        cog = self.bot.get_cog('SalesFree') 
        
        if cog:
            await interaction.response.send_message("Refresh en cours ...")
            await cog.check_sales()
        else:
            await interaction.response.send_message("Erreur : Le module 'SalesFree' est introuvable.", ephemeral=True)

class MusicCommands(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="add_musique", description="Ajoute une musique seule à la file d'attente.")
    async def cmd_add_musique(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        success, message = await add_musique(interaction, url)
        await interaction.followup.send(message)

    @app_commands.command(name="add_playlist", description="Ajoute ou remplace une playlist dans la file d'attente.")
    async def cmd_add_playlist(self, interaction: discord.Interaction, url: str):
        await interaction.response.defer()
        success, message = await add_playlist(interaction, url)
        await interaction.followup.send(message)

    @app_commands.command(name="leave", description="Déconnecte le bot et purge la file d'attente.")
    async def cmd_leave(self, interaction: discord.Interaction):
        success, message = await quit_vocal(interaction)
        await interaction.response.send_message(message)

    @app_commands.command(name="now_playing", description="Affiche la musique en cours de lecture.")
    async def cmd_now_playing(self, interaction: discord.Interaction):
        success, message = await now_playing(interaction)
        await interaction.response.send_message(message)

    @app_commands.command(name="pause", description="Met la musique en pause.")
    async def cmd_pause(self, interaction: discord.Interaction):
        success, message = await pause_musique(interaction)
        await interaction.response.send_message(message)

    @app_commands.command(name="resume", description="Reprend la lecture de la musique.")
    async def cmd_resume(self, interaction: discord.Interaction):
        success, message = await resume_musique(interaction)
        await interaction.response.send_message(message)

    @app_commands.command(name="skipvote", description="Lance un vote pour passer à la musique suivante.")
    async def cmd_skipvote(self, interaction: discord.Interaction):
        success, message, guild_id, voice_client = check_vocal_access(interaction)
        
        if not success:
            await interaction.response.send_message(message, ephemeral=True)
            return

        voters = [m.id for m in interaction.user.voice.channel.members if not m.bot]

        async def on_vote_finish(result, original_interaction):
            if not result["valid"] or not result["winner"]:
                return "Le vote a échoué (égalité ou participation insuffisante)."
            
            if result["winner"] == "Oui":
                skip_success, skip_msg = await skip_musique(original_interaction)
                return f"Le peuple a parlé ('Oui') ! {skip_msg}"
            else:
                return "Le vote pour passer la musique a été refusé ('Non')."

        vote_view = VoteView(
            interaction=interaction,
            question="Voulez-vous passer la musique actuelle ?",
            choices=["Oui", "Non"],
            allowed_users=voters,
            timeout=30,
            on_finish=on_vote_finish
        )

        await interaction.response.send_message(
            embed=vote_view.build_embed(),
            view=vote_view
        )
        
        vote_view.message = await interaction.original_response()

async def setup(bot):
    await bot.add_cog(SalesCommands(bot))
    await bot.add_cog(MusicCommands(bot))