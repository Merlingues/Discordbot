import time
from typing import MutableMapping, Hashable
import discord

'''
Format dictionnaire de cooldown
{
 user_id: {
     "nom_commande": timestamp_derniere_utilisation
 }
}
'''
CooldownStore = MutableMapping[int, MutableMapping[Hashable, float]]

#Retourne un temps pour les messages d'erreur
def format_remaining(seconds):
    seconds = max(0, int(seconds))
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60

    if hours > 0:
        return f"{hours}h {minutes:02d}min"
    if minutes > 0:
        return f"{minutes} minute{'s' if minutes > 1 else ''}"
    return f"{secs} seconde{'s' if secs > 1 else ''}"

#Vérifie si le membre possède le rôle demandé.
def has_role(member, role_id):
    return any(role.id == role_id for role in member.roles)

#Vérifie si le membre est connecté dans un salon vocal.
def is_in_voice(member):
    return bool(member.voice and member.voice.channel)

#Calcul le cooldown du membre
def cooldown_remaining(user_id, command_name, cooldowns: CooldownStore, cooldown_seconds):
    user_cooldowns = cooldowns.get(user_id, {})
    last_use = user_cooldowns.get(command_name, 0)

    elapsed = time.time() - last_use
    remaining = cooldown_seconds - elapsed

    return max(0, int(remaining))


def apply_cooldown(user_id, command_name, cooldowns: CooldownStore):
    #Applique / met à jour le cooldown d'un utilisateur pour une commande précise.
    if user_id not in cooldowns:
        cooldowns[user_id] = {}

    cooldowns[user_id][command_name] = time.time()

#Supprime le cooldown d'un utilisateur pour une commande précise.
def clear_cooldown(user_id, command_name, cooldowns: CooldownStore):
    if user_id in cooldowns:
        cooldowns[user_id].pop(command_name, None)

        # Nettoyage si l'utilisateur n'a plus aucun cooldown
        if not cooldowns[user_id]:
            cooldowns.pop(user_id, None)


def check_command(
    interaction,
    *,
    authorized_role_id,
    cooldowns: CooldownStore,
    cooldown_seconds,
    command_name=None,
    role_name="ce rôle",
    require_voice=True,
):

    user = interaction.user

    if command_name is None:
        command_name = interaction.command.name if interaction.command else "unknown"

    if not isinstance(user, discord.Member):
        return False, "Cette commande doit être utilisée dans un serveur."

    if not has_role(user, authorized_role_id):
        return False, f"Seuls les {role_name} peuvent utiliser cette commande."

    if require_voice and not is_in_voice(user):
        return False, "Tu dois être dans un vocal pour utiliser cette commande."

    remaining = cooldown_remaining(
        user.id,
        command_name,
        cooldowns,
        cooldown_seconds,
    )

    if remaining > 0:
        return False, f"Commande /{command_name} en cooldown : {format_remaining(remaining)} restantes."

    return True, None
