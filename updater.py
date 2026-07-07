from notion_client import Client
from config import NOTION_TOKEN

notion = Client(auth=NOTION_TOKEN)


def update_player(page_id, data_check, false_fields):
    """
    Met à jour :
    - Data check
    - Campi falsi
    - Qualità dato
    - Verify
    """

    notion.pages.update(
        page_id=page_id,
        properties={

            "Data check": {
                "select": {
                    "name": data_check
                }
            },

            "Campi falsi": {
                "multi_select": [
                    {"name": field}
                    for field in false_fields
                ]
            },

            "Qualità dato": {
                "select": {
                    "name": "Verificato"
                }
            },

            "Verify": {
                "checkbox": False
            }

        }
    )


def set_verification_status(page_id, status):
    """
    Met à jour uniquement "Verification status" (Waiting, Running, Done, Error),
    pour suivre l'avancement du traitement OpenClaw en temps réel.
    """

    notion.pages.update(
        page_id=page_id,
        properties={
            "Verification status": {
                "select": {
                    "name": status
                }
            }
        }
    )
