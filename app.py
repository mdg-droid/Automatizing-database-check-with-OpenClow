import time

from notion import get_players_to_verify, update_player, set_verification_status
from verifier.checker import verify_player

POLL_INTERVAL_SECONDS = 30


def run_once():
    players = get_players_to_verify()

    if not players:
        print("Aucun player à vérifier.")

    for player in players:
        page_id = player["id"]
        name = player["properties"]["Nome del player"]["title"][0]["plain_text"]
        set_verification_status(page_id, "Running")

        try:
            result = verify_player(player)
        except Exception as e:
            print(f"[{name}] échec de la vérification OpenClaw : {e}")
            set_verification_status(page_id, "Error")
            continue


        update_player(
            page_id=page_id,
            data_check=result["data_check"],
            false_fields=result["false_fields"]
        )
        set_verification_status(page_id, "Done")
        print(f"[{name}] mise à jour effectuée.")


if __name__ == "__main__":
    while True:
        run_once()
        print(f"Attente {POLL_INTERVAL_SECONDS}s avant le prochain passage...\n")
        time.sleep(POLL_INTERVAL_SECONDS)

