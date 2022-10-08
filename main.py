import os
import json

from telethon import TelegramClient
from elasticsearch import Elasticsearch
from dotenv import load_dotenv

load_dotenv()

# make a .env file and add the following values
api_id = int(os.getenv('TELEGRAM_API_ID'))
api_hash = os.getenv('TELEGRAM_API_HASH')
telethon_session_name = os.getenv('TELEGRAM_SESSION_FILENAME')
tnp_id = int(os.getenv('TNP_CHAT_ID'))
companies_file_name = os.getenv('TNP_COMPANIES_NAMES_FILE')
companies = []

client = TelegramClient(telethon_session_name, api_id, api_hash)
elasticClient = Elasticsearch("http://localhost:9200", verify_certs=False)


async def dump_telegram_messages():
    async for message in client.iter_messages(tnp_id):
        if message.text is not None:
            print(message.id, "  At : ", str(message.date), "  ", message.text)
            doc = await get_elastic_doc(message)
            elasticClient.index(index='telegram_messages', id=message.id, document=doc)


async def dump_telegram_ids():
    async for dialog in client.iter_dialogs():
        if dialog.is_channel or dialog.is_group:
            # note the chat id of the tnp group from the console
            print("CHAT NAME: ", dialog.name, '  has ID:', dialog.id)


async def get_elastic_doc(message):
    if message.document is not None:
        media = {
            'type': message.document.mime_type,
            'id': message.document.id
        }
    else:
        # Shit u need to do for elastic search
        media = {
            'type': "None",
            'id': -1
        }
    doc = {
        'raw_text': message.raw_text,
        'timestamp': message.date.strftime("%Y-%m-%dT%H:%M:%SZ"),  # proper formatting for elastic timestamp
        'media': media
    }
    return doc


def load_companies():
    f = open(companies_file_name)
    global companies
    companies = json.load(f)


def search_elastic():
    output = []
    for companyName in companies:
        body = {
            "query": {
                "match": {
                    "raw_text": companyName
                }
            },
            "size": 10,
            "sort": [
                {
                    "timestamp": {
                        "order": "asc"
                    }
                }
            ]
        }
        result = elasticClient.search(body=body, index='telegram_messages')
        out = transform_hits(companyName, result)
        output.append(out)
        print("Company : ", companyName, " result ", result)
    json_object = json.dumps(output,indent=3)
    with open("results.json", "w") as outfile:
        outfile.truncate(0)
        outfile.write(json_object)


def transform_hits(companyName, result):
    hits = result.raw['hits']['hits']
    result_hits = []
    for raw_hit in hits:
        raw_hit = raw_hit['_source']
        tran_hits = {
            'text': raw_hit['raw_text'],
            'timestamp': raw_hit['timestamp'],
            'media_type': raw_hit['media']['type']
        }
        result_hits.append(tran_hits)
    out = {
        "companyName": companyName,
        "searchData": result_hits
    }
    return out


async def main():
    global tnp_id
    load_companies()
    if tnp_id == -1:
        await dump_telegram_ids()
        tnp_id = int(input("Check the Dump above and enter the tnp chat id : "))
    # await dump_telegram_messages()
    search_elastic()


with client:
    client.loop.run_until_complete(main())
