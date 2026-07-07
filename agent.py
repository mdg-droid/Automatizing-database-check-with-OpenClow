import json
import os
import subprocess
import tempfile
import uuid

# Agent OpenClaw à utiliser (voir `openclaw agents list`)
OPENCLAW_AGENT_ID = "main"

# Modèle explicite : la résolution par défaut échouait ("model not found by provider"),
# on force donc le modèle voulu.
OPENCLAW_MODEL = "openai/gpt-5.5"

# Vérification web => peut prendre du temps, on laisse une marge large
OPENCLAW_TIMEOUT_SECONDS = 300


def ask_openclaw(prompt: str) -> str:
    """
    Envoie un prompt à OpenClaw via `openclaw agent --json` et retourne le texte de sa réponse.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(prompt)
        message_file_path = f.name

    # Session unique à chaque appel : chaque player est vérifié isolément, sans
    # accumuler l'historique des précédents (évite un contexte qui grossit sans fin
    # et des réponses qui dérivent au fil des appels).
    session_key = f"agent:main:verify-{uuid.uuid4()}"

    command = [
        "openclaw", "agent",
        "--agent", OPENCLAW_AGENT_ID,
        "--session-key", session_key,
        "--message-file", message_file_path,
        "--model", OPENCLAW_MODEL,
        "--json",
    ]

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=OPENCLAW_TIMEOUT_SECONDS
        )
    finally:
        os.remove(message_file_path)

    if result.returncode != 0:
        raise RuntimeError(f"OpenClaw a échoué (code {result.returncode}): {result.stderr}")

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError as e:
        raise ValueError(f"Sortie OpenClaw non-JSON. stdout brut : {result.stdout!r}") from e

    # La clé finalAssistantVisibleText apparaît tantôt sous "meta" à la racine,
    # tantôt sous "result.meta" selon le contexte d'exécution (observé empiriquement
    # avec Ollama vs Gemini vs OpenAI) : on gère les deux emplacements plutôt que
    # de se fier à un seul chemin fixe.
    meta = payload.get("meta") or payload.get("result", {}).get("meta")

    if meta is None or "finalAssistantVisibleText" not in meta:
        raise ValueError(
            f"Clé 'finalAssistantVisibleText' introuvable (ni sous meta, ni sous result.meta). "
            f"stdout brut : {result.stdout!r}"
        )

    return meta["finalAssistantVisibleText"]
