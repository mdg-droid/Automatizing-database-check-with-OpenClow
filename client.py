from notion_client import Client
from config import NOTION_TOKEN, DATA_SOURCE_ID

notion = Client(auth=NOTION_TOKEN)

def get_players_to_verify():

    players = []
    cursor = None

    while True:

        kwargs = {
            "data_source_id": DATA_SOURCE_ID,
            "page_size": 100,
            "filter": {
                "and": [
                    {
                        "property": "Verify",
                        "checkbox": {
                            "equals": True
                        }
                    },
                    {
                        "property": "Qualità dato",
                        "select": {
                            "equals": "Da verificare"
                        }
                    }
                ]
            }
        }

        if cursor:
            kwargs["start_cursor"] = cursor

        response = notion.data_sources.query(**kwargs)

        players.extend(response["results"])

        if not response["has_more"]:
            break

        cursor = response["next_cursor"]

    return players
