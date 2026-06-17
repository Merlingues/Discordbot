import discord
import yt_dlp
import asyncio


## BLOC 1 : Configuration générale des extracteurs yt-dlp, des paramètres FFmpeg et initialisation des états globaux.

YTDL_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": True,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "extractor_args": {"youtube": {"player_client": ["default", "-android_sdkless"]}}
}

YTDL_PLAYLIST_OPTIONS = {
    "format": "bestaudio/best",
    "noplaylist": False,
    "quiet": True,
    "no_warnings": True,
    "default_search": "auto",
    "source_address": "0.0.0.0",
    "extract_flat": "in_playlist",
    "extractor_args": {"youtube": {"player_client": ["default", "-android_sdkless"]}}
}

FFMPEG_OPTIONS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}

ytdl = yt_dlp.YoutubeDL(YTDL_OPTIONS)
ytdl_playlist = yt_dlp.YoutubeDL(YTDL_PLAYLIST_OPTIONS)

queues = {}
current_tracks = {}


## BLOC 2 : Gestion de la connexion vocale du bot et vérification d'accès aux commandes musicales.

async def join_vocal(interaction: discord.Interaction) -> tuple[bool, str, discord.VoiceClient | None]:
    user = interaction.user

    if not getattr(user, "voice", None) or not user.voice.channel:
        return False, "Vous devez être dans un salon vocal.", None

    voice_channel = user.voice.channel
    voice_client = interaction.guild.voice_client

    if voice_client and voice_client.is_connected():
        if voice_client.channel != voice_channel:
            return False, "Le bot est déjà connecté dans un autre salon vocal.", None

        return True, "Le bot est déjà connecté au salon vocal.", voice_client

    voice_client = await voice_channel.connect()
    return True, "Bot connecté au salon vocal.", voice_client


def check_vocal_access(interaction: discord.Interaction) -> tuple[bool, str, int | None, discord.VoiceClient | None]:
    guild_id = interaction.guild.id
    voice_client = interaction.guild.voice_client
    user = interaction.user

    if not voice_client or not voice_client.is_connected():
        return False, "Le bot n'est connecté à aucun salon vocal.", None, None

    if not getattr(user, "voice", None) or not user.voice.channel:
        return False, "Vous devez être dans un salon vocal.", None, None

    if voice_client.channel != user.voice.channel:
        return False, "Vous devez être dans le même salon vocal que le bot.", None, None

    return True, "Accès vocal valide.", guild_id, voice_client


async def quit_vocal(interaction: discord.Interaction) -> tuple[bool, str]:
    guild_id = interaction.guild.id
    voice_client = interaction.guild.voice_client

    queues.pop(guild_id, None)
    current_tracks.pop(guild_id, None)

    if not voice_client or not voice_client.is_connected():
        return False, "Le bot n'est connecté à aucun salon vocal. La queue a été purgée."

    if voice_client.is_playing() or voice_client.is_paused():
        voice_client.stop()

    await voice_client.disconnect()
    return True, "Le bot a quitté le salon vocal et la queue a été purgée."


## BLOC 3 : Contrôle automatique de la lecture audio et passage à l'élément suivant de la file d'attente.

def check_next(interaction: discord.Interaction, voice_client: discord.VoiceClient):
    guild_id = interaction.guild.id

    if guild_id not in queues or len(queues[guild_id]) == 0:
        current_tracks.pop(guild_id, None)
        return

    track = queues[guild_id].pop(0)
    asyncio.run_coroutine_threadsafe(play_next(interaction, voice_client, track), interaction.client.loop)


async def play_next(interaction: discord.Interaction, voice_client: discord.VoiceClient, track: dict):
    try:
        current_tracks[interaction.guild.id] = track

        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(track["url"], download=False))
        audio_url = data["url"]

        source = discord.FFmpegPCMAudio(audio_url, **FFMPEG_OPTIONS)
        voice_client.play(source, after=lambda error: check_next(interaction, voice_client))

        return True, f"Lecture en cours : {track.get('title', 'Titre inconnu')}"

    except Exception as error:
        print(f"Erreur pendant la lecture : {error}")
        check_next(interaction, voice_client)
        return False, f"Erreur pendant la lecture : {error}"


## BLOC 4 : Extraction des informations YouTube et formatage unique des musiques stockées dans la file d'attente.

async def extract_youtube_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=False))


async def extract_playlist_info(url: str) -> dict:
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, lambda: ytdl_playlist.extract_info(url, download=False))


def format_track(entry: dict, source: str) -> dict:
    url = entry.get("webpage_url") or entry.get("url")

    if url and not url.startswith("http"):
        url = f"https://www.youtube.com/watch?v={url}"

    return {
        "title": entry.get("title", "Titre inconnu"),
        "url": url,
        "duration": entry.get("duration"),
        "source": source,
    }


## BLOC 5 : Ajout ou remplacement rapide d'une playlist complète dans la file d'attente, sans accepter de musique seule.

async def add_playlist(interaction: discord.Interaction, url: str) -> tuple[bool, str]:
    success, message, voice_client = await join_vocal(interaction)

    if not success:
        return False, message

    try:
        data = await extract_playlist_info(url)

        if "entries" not in data or not data["entries"]:
            return False, "Le lien fourni n'est pas une playlist valide."

        guild_id = interaction.guild.id
        music_tracks = [track for track in queues.get(guild_id, []) if track.get("source") == "music"]
        playlist_tracks = [format_track(entry, "playlist") for entry in data["entries"] if entry]

        queues[guild_id] = music_tracks + playlist_tracks

        if not voice_client.is_playing() and not voice_client.is_paused() and queues[guild_id]:
            track = queues[guild_id].pop(0)
            await play_next(interaction, voice_client, track)

        return True, f"Playlist ajoutée ou remplacée : {len(playlist_tracks)} musique(s)."

    except Exception as error:
        return False, f"Erreur pendant l'ajout de la playlist : {error}"


## BLOC 6 : Ajout d'une musique seule avant la playlist, mais après les musiques déjà ajoutées manuellement.

async def add_musique(interaction: discord.Interaction, url: str) -> tuple[bool, str]:
    success, message, voice_client = await join_vocal(interaction)

    if not success:
        return False, message

    try:
        data = await extract_youtube_info(url)

        if "entries" in data:
            return False, "Le lien fourni est une playlist. Cette fonction accepte uniquement une musique seule."

        guild_id = interaction.guild.id
        queues.setdefault(guild_id, [])

        track = format_track(data, "music")
        insert_index = 0

        for index, queued_track in enumerate(queues[guild_id]):
            if queued_track.get("source") == "playlist":
                break

            insert_index = index + 1

        queues[guild_id].insert(insert_index, track)

        if not voice_client.is_playing() and not voice_client.is_paused() and queues[guild_id]:
            next_track = queues[guild_id].pop(0)
            await play_next(interaction, voice_client, next_track)

        return True, f"Musique ajoutée : {track.get('title', 'Titre inconnu')}"

    except Exception as error:
        return False, f"Erreur pendant l'ajout de la musique : {error}"


## BLOC 7 : Commandes de pause, reprise, passage à la musique suivante et affichage de la musique en cours.

async def pause_musique(interaction: discord.Interaction) -> tuple[bool, str]:
    success, message, guild_id, voice_client = check_vocal_access(interaction)

    if not success:
        return False, message

    if voice_client.is_paused():
        return False, "La musique est déjà en pause."

    if not voice_client.is_playing():
        return False, "Aucune musique n'est en cours de lecture."

    voice_client.pause()
    return True, "Musique mise en pause."


async def resume_musique(interaction: discord.Interaction) -> tuple[bool, str]:
    success, message, guild_id, voice_client = check_vocal_access(interaction)

    if not success:
        return False, message

    if not voice_client.is_paused():
        return False, "Aucune musique n'est actuellement en pause."

    voice_client.resume()
    return True, "Lecture reprise."


async def skip_musique(interaction: discord.Interaction) -> tuple[bool, str]:
    success, message, guild_id, voice_client = check_vocal_access(interaction)

    if not success:
        return False, message

    if voice_client.is_playing() or voice_client.is_paused():
        if guild_id not in queues or len(queues[guild_id]) == 0:
            current_tracks.pop(guild_id, None)
            voice_client.stop()
            return True, "Musique passée. Il n'y a plus de musique dans la queue."

        voice_client.stop()
        return True, "Passage à la musique suivante."

    if guild_id in queues and len(queues[guild_id]) > 0:
        track = queues[guild_id].pop(0)
        await play_next(interaction, voice_client, track)
        return True, f"Lecture lancée : {track.get('title', 'Titre inconnu')}"

    current_tracks.pop(guild_id, None)
    return False, "Aucune musique en cours et aucune musique dans la queue."


async def now_playing(interaction: discord.Interaction) -> tuple[bool, str]:
    success, message, guild_id, voice_client = check_vocal_access(interaction)

    if not success:
        return False, message

    if guild_id not in current_tracks:
        return False, "Aucune musique n'est actuellement en cours."

    if not voice_client.is_playing() and not voice_client.is_paused():
        current_tracks.pop(guild_id, None)
        return False, "Aucune musique n'est actuellement en cours."

    track = current_tracks[guild_id]
    title = track.get("title", "Titre inconnu")
    source = track.get("source", "inconnue")
    duration = track.get("duration")
    state = "en pause" if voice_client.is_paused() else "en lecture"

    if duration:
        minutes = duration // 60
        seconds = duration % 60
        return True, f"Musique actuelle : {title} [{source}] - {minutes}:{seconds:02d} - {state}"

    return True, f"Musique actuelle : {title} [{source}] - {state}"