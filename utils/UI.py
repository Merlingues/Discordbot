import discord
import inspect

## Arguments de la commande
## interaction : interaction Discord de la commande qui lance le vote.
## question : texte affiché comme titre du vote.
## choices : liste des réponses possibles, chaque élément devient un bouton.
## allowed_users : liste des IDs utilisateurs autorisés à voter, mettre None si tout le monde peut voter.
## timeout : durée du vote en secondes avant fermeture automatique.
## required_participation_percent : pourcentage minimum de votants requis pour valider le vote, mettre None si aucun minimum.
## required_winning_percent : pourcentage minimum que doit atteindre la réponse gagnante, mettre None pour une majorité simple.
## allow_vote_change : True si un utilisateur peut modifier son vote, False s'il ne peut voter qu'une seule fois.
## auto_finish_when_full : True si le vote se termine automatiquement quand tous les utilisateurs autorisés ont voté, False pour attendre le timeout.
## on_finish : fonction appelée à la fin du vote pour traiter le résultat, mettre None si aucune action spéciale n'est nécessaire.

## BLOC 1 : Vue Discord générique permettant de créer des votes interactifs avec boutons.

class VoteView(discord.ui.View):
    def __init__(
        self,
        interaction: discord.Interaction,
        question: str,
        choices: list[str],
        allowed_users: list[int] | None = None,
        timeout: int = 30,
        required_participation_percent: int | None = None,
        required_winning_percent: int | None = None,
        allow_vote_change: bool = True,
        auto_finish_when_full: bool = True,
        on_finish=None,
    ):
        super().__init__(timeout=timeout)

        if len(choices) < 2:
            raise ValueError("Un vote doit contenir au moins deux réponses.")

        if len(choices) > 25:
            raise ValueError("Un vote avec boutons Discord ne peut pas dépasser 25 réponses.")

        if required_participation_percent is not None and allowed_users is None:
            raise ValueError("required_participation_percent nécessite allowed_users.")

        self.original_interaction = interaction
        self.question = question
        self.choices = choices
        self.allowed_users = set(allowed_users) if allowed_users else None
        self.required_participation_percent = required_participation_percent
        self.required_winning_percent = required_winning_percent
        self.allow_vote_change = allow_vote_change
        self.auto_finish_when_full = auto_finish_when_full
        self.on_finish_callback = on_finish
        self.votes = {}
        self.finished = False
        self.message = None

        for index, choice in enumerate(choices):
            button = discord.ui.Button(
                label=choice,
                style=discord.ButtonStyle.primary,
                row=index // 5,
            )
            button.callback = self.create_vote_callback(index)
            self.add_item(button)

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if self.allowed_users is not None and interaction.user.id not in self.allowed_users:
            await interaction.response.send_message(
                "Vous n'êtes pas autorisé à voter.",
                ephemeral=True,
            )
            return False

        return True

    def create_vote_callback(self, choice_index: int):
        async def callback(interaction: discord.Interaction):
            if not self.allow_vote_change and interaction.user.id in self.votes:
                await interaction.response.send_message(
                    "Vous avez déjà voté.",
                    ephemeral=True,
                )
                return

            self.votes[interaction.user.id] = choice_index

            if (
                self.auto_finish_when_full
                and self.allowed_users is not None
                and len(self.votes) >= len(self.allowed_users)
            ):
                await self.finish_vote(interaction)
                return

            await self.update_vote_message(interaction)

        return callback

    def get_counts(self) -> dict[str, int]:
        return {
            choice: list(self.votes.values()).count(index)
            for index, choice in enumerate(self.choices)
        }

    def get_result(self) -> dict:
        counts = self.get_counts()
        total_votes = len(self.votes)
        eligible_count = len(self.allowed_users) if self.allowed_users is not None else None
        participation_percent = 0

        if eligible_count:
            participation_percent = round((total_votes / eligible_count) * 100, 2)

        max_count = max(counts.values()) if counts else 0
        winners = [
            choice
            for choice, count in counts.items()
            if count == max_count and max_count > 0
        ]

        winning_percent = 0

        if total_votes > 0:
            winning_percent = round((max_count / total_votes) * 100, 2)

        quorum_ok = True

        if self.required_participation_percent is not None:
            quorum_ok = participation_percent >= self.required_participation_percent

        winning_percent_ok = True

        if self.required_winning_percent is not None:
            winning_percent_ok = winning_percent >= self.required_winning_percent

        return {
            "question": self.question,
            "counts": counts,
            "total_votes": total_votes,
            "eligible_count": eligible_count,
            "participation_percent": participation_percent,
            "required_participation_percent": self.required_participation_percent,
            "quorum_ok": quorum_ok,
            "winners": winners,
            "winner": winners[0] if len(winners) == 1 else None,
            "winning_percent": winning_percent,
            "required_winning_percent": self.required_winning_percent,
            "winning_percent_ok": winning_percent_ok,
            "valid": quorum_ok and winning_percent_ok,
        }

    def build_embed(self, finished: bool = False, extra_message: str | None = None) -> discord.Embed:
        result = self.get_result()
        counts = result["counts"]
        lines = []

        for choice, count in counts.items():
            lines.append(f"**{choice}** : {count}")

        if result["eligible_count"] is not None:
            lines.append("")
            lines.append(f"Votes : **{result['total_votes']}/{result['eligible_count']}**")
            lines.append(f"Participation : **{result['participation_percent']}%**")
        else:
            lines.append("")
            lines.append(f"Votes : **{result['total_votes']}**")

        if self.required_participation_percent is not None:
            lines.append(f"Participation requise : **{self.required_participation_percent}%**")

        if self.required_winning_percent is not None:
            lines.append(f"Pourcentage gagnant requis : **{self.required_winning_percent}%**")

        if finished:
            lines.append("")

            if not result["quorum_ok"]:
                lines.append("Résultat : **vote invalide, participation insuffisante**")
            elif not result["winning_percent_ok"]:
                lines.append("Résultat : **vote invalide, pourcentage gagnant insuffisant**")
            elif len(result["winners"]) > 1:
                lines.append(f"Résultat : **égalité entre {', '.join(result['winners'])}**")
            elif result["winner"]:
                lines.append(f"Résultat : **{result['winner']} gagne**")
            else:
                lines.append("Résultat : **aucun vote**")

        if extra_message:
            lines.append("")
            lines.append(extra_message)

        return discord.Embed(
            title=self.question,
            description="\n".join(lines),
            color=discord.Color.green() if finished else discord.Color.blurple(),
        )

    async def update_vote_message(self, interaction: discord.Interaction):
        await interaction.response.edit_message(
            embed=self.build_embed(),
            view=self,
        )

    async def finish_vote(self, interaction: discord.Interaction | None = None):
        if self.finished:
            return

        self.finished = True

        for item in self.children:
            item.disabled = True

        result = self.get_result()
        extra_message = None

        if self.on_finish_callback:
            callback_result = self.on_finish_callback(result, self.original_interaction)

            if inspect.isawaitable(callback_result):
                extra_message = await callback_result
            else:
                extra_message = callback_result

        embed = self.build_embed(finished=True, extra_message=extra_message)

        if interaction:
            if interaction.response.is_done():
                await interaction.message.edit(embed=embed, view=self)
            else:
                await interaction.response.edit_message(embed=embed, view=self)
        elif self.message:
            await self.message.edit(embed=embed, view=self)
        else:
            await self.original_interaction.edit_original_response(embed=embed, view=self)

        self.stop()

    async def on_timeout(self):
        await self.finish_vote()