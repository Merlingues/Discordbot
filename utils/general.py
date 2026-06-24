import discord
import random

""" SEND IMAGE """
async def send_image(interaction: discord.Interaction, description: str, image_url: str, color: discord.Color = discord.Color.blurple()):
 
    embed = discord.Embed(description=description, color=color)
    embed.set_image(url=image_url)
    
    if interaction.response.is_done():
        await interaction.followup.send(embed=embed)
    else:
        await interaction.response.send_message(embed=embed)

""" VOCAL KICK """
async def vkick_member(self, member):
    if not member.voice:
        return
    await member.move_to(None)
        
""" SERVEUR KICK"""
async def skick_member(self, member, *, reason: str):
    if not member.voice:
        return
    await member.kick(reason=reason)

""" VOCAL CHANGE """
async def vchange_member(self, member, salon_cible):
    if not member.voice:
        return
    await member.move_to(salon_cible)

""" SALON ALEATOIRE """
async def random_salon(member: discord.Member):
    serveur = member.guild

    if not serveur.voice_channels:
        return None, None

    salon_cible = random.choice(serveur.voice_channels)

    return salon_cible.id, salon_cible.name