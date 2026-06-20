import discord
import random

""" SEND IMAGE """
async def send_image(destination, source: str, local: bool = True):
    if local:
        await destination.send(file=discord.File(source))
    else:
        await destination.send(content=source)

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