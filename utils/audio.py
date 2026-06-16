import discord
import yt_dlp
import asyncio

# BLOC 1 : Configuration générale de l'extracteur yt-dlp, des paramètres de flux FFmpeg et initialisation de la file d'attente globale.
YTDL_OPTIONS = {
    'format': 'bestaudio/best',
    'noplaylist': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0',
}

FFMPEG_OPTIONS = {
    'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn',
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
queues = {}

def check_next(interaction: discord.Interaction, voice_client: discord.VoiceClient):
    """Fonction de rappel automatique déclenchée à la fin d'un morceau pour vérifier et lancer l'élément suivant de la file d'attente."""
    guild_id = interaction.guild.id
    
    if guild_id in queues and len(queues[guild_id]) > 0:
        next_track = queues[guild_id].pop(0)
        
        asyncio.run_coroutine_threadsafe(
            play_next(interaction, voice_client, next_track), 
            interaction.client.loop
        )

async def play_next(interaction: discord.Interaction, voice_client: discord.VoiceClient, track: dict):
    """Fonction interne chargée d'extraire l'URL de streaming en temps réel et de lier la lecture audio à FFmpeg."""
    try:
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(track['url'], download=False))
        audio_url = data['url']
        
        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=lambda e: check_next(interaction, voice_client))
        
        await interaction.channel.send(f"🎵 Au tour de : **{track['title']}**")
    except Exception as e:
        print(f"Erreur lors de la lecture du morceau suivant : {e}")

async def play_youtube_sound(interaction: discord.Interaction, url: str) -> tuple[bool, str]:
    """Fonction principale appelée par vos commandes pour gérer la connexion au salon vocal, analyser le lien (vidéo ou playlist) et organiser la file d'attente."""
    user = interaction.user
    guild = interaction.guild

    if not user.voice or not user.voice.channel:
        return False, "Tu dois être dans un vocal pour que je puisse te rejoindre !"

    voice_channel = user.voice.channel

    try:
        voice_client = discord.utils.get(guild.voice_clients, guild=guild)
        if not voice_client:
            voice_client = await voice_channel.connect()
        elif voice_client.channel != voice_channel and not voice_client.is_playing():
            await voice_client.move_to(voice_channel)

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))
        
        if guild.id not in queues:
            queues[guild.id] = []

        if 'entries' in data:
            added_songs = 0
            for entry in data['entries']:
                if entry:
                    queues[guild.id].append({"url": entry['webpage_url'], "title": entry.get('title', 'Musique')})
                    added_songs += 1
            
            if not voice_client.is_playing():
                first_track = queues[guild.id].pop(0)
                await play_next(interaction, voice_client, first_track)
                return True, f"🎒 Playlist chargée : **{added_songs} musiques** ajoutées à la file. Début de la lecture !"
            
            return True, f"🎒 Playlist chargée : **{added_songs} musiques** ajoutées à la file d'attente."

        track_info = {"url": data['webpage_url'], "title": data.get('title', 'un son')}
        
        if voice_client.is_playing():
            queues[guild.id].insert(0, track_info)
            return True, f"⚡ Ajouté en priorité. Prochain morceau : **{track_info['title']}**"
        
        await play_next(interaction, voice_client, track_info)
        return True, f"🎵 En train de jouer : **{track_info['title']}**"

    except Exception as e:
        print(f"Erreur générale audio : {e}")
        return False, "Une erreur est survenue lors du traitement du lien."