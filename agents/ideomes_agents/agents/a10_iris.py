"""A10 · Iris, ambassadrice : informe le contributeur à chaque changement de statut.
Mention IA obligatoire ; messages sensibles relus par un humain avant envoi."""

from __future__ import annotations

from .base import Agent

MENTION = "(Réponse rédigée avec l'aide de l'IA)"


class Iris(Agent):
    id = "A10"
    prompt = "iris"

    def informer(self, dossier, ctx, evenement: str, **infos) -> dict:
        sortie = self.llm(
            {
                "evenement": evenement,
                "resume": dossier.sorties.get("A3", {}).get("resume"),
                "canal": "whatsapp",
                **infos,
            },
            dossier.id,
        )
        if MENTION not in sortie["message"]:
            sortie["message"] = sortie["message"].rstrip() + " " + MENTION
        message = {
            "dossier": dossier.id,
            "destinataire": dossier.contribution.auteur_id,
            "evenement": evenement,
            **sortie,
        }
        if not dossier.contribution.auteur_id:
            message["statut_envoi"] = "sans_destinataire"
        elif sortie["sensible"]:
            message["statut_envoi"] = "a_relire"
            ctx.a_relire(message)
        else:
            message["statut_envoi"] = "en_file"
            ctx.envoyer(message)
        historique = dossier.sorties.setdefault(self.id, {"messages": []})["messages"]
        historique.append(message)
        dossier.trace(self.id, "message", evenement=evenement, statut_envoi=message["statut_envoi"])
        return message

    def traiter(self, dossier, ctx):
        return dossier.sorties.get(self.id, {"messages": []})
