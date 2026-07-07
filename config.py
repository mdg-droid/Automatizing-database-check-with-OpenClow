from dotenv import load_dotenv
import os

load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_API_TOKEN")
DATA_SOURCE_ID = os.getenv("NOTION_DATA_SOURCE_ID")
SUBCOMPETENZE_DATA_SOURCE_ID = os.getenv("NOTION_SUBCOMPETENZE_DATA_SOURCE_ID")

if SUBCOMPETENZE_DATA_SOURCE_ID is None:
    raise Exception("NOTION_SUBCOMPETENZE_DATA_SOURCE_ID absent")

if NOTION_TOKEN is None:
    raise Exception("NOTION_API_TOKEN absent")

if DATA_SOURCE_ID is None:
    raise Exception("NOTION_DATA_SOURCE_ID absent")
