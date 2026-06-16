import discord
from discord.ext import commands
from discord import app_commands
import asyncio
import time
import random
import os
from dotenv import load_dotenv

# Charger les variables .env
load_dotenv()


""" MUTE VOCAL """
def mute_member(self, member, duration):
    if not member.voice:
        return

    await member.edit(mute=True)
    self.bot.shared["effect"] = "mute"
    await asyncio.sleep(duration)

    if member.voice:
        await member.edit(mute=False)
        self.bot.shared["effect"] = None

""" DEAFEN VOCAL """
def deafen_member(self, member, duration):
    if not member.voice:
        return

    await member.edit(deafen=True)
    self.bot.shared["effect"] = "deafen"
    await asyncio.sleep(duration)

    if member.voice:
        await member.edit(deafen=False)
        self.bot.shared["effect"] = None