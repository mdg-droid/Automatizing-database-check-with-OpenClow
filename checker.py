import json
import re

from openclaw.agent import ask_openclaw
from verifier.prompt import build_prompt


def _extract_json(raw_response: str) -> dict:
    """
    Extrait le premier objet JSON valide trouvé dans la réponse.
    Les petits modèles locaux (ex: llama3.2) ajoutent parfois du texte
    autour du JSON malgré la consigne "réponds uniquement en JSON".
    """
    try:
        return json.loads(raw_response)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{.*\}", raw_response, re.DOTALL)
    if not match:
        raise ValueError(f"Aucun JSON trouvé dans la réponse OpenClaw : {raw_response!r}")

    return json.loads(match.group(0))


def verify_player(player: dict) -> dict:
    """
    Fait vérifier un player par OpenClaw et retourne un dict
    {"data_check": str, "false_fields": list[str]} prêt à être passé à update_player().
    """
    prompt = build_prompt(player)
    raw_response = ask_openclaw(prompt)

    result = _extract_json(raw_response)

    if "data_check" not in result or "false_fields" not in result:
        raise ValueError(f"Réponse OpenClaw incomplète : {result}")

    return result
