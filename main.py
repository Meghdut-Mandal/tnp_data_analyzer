import os
import json
import dominate
from telethon import TelegramClient
from elasticsearch import Elasticsearch
from dotenv import load_dotenv
from dominate.tags import *

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
    elastic_output = []
    for companyName in companies:
        body = {
            "query": {
                "match": {
                    "raw_text": companyName
                }
            },
            "size": 10
        }
        result = elasticClient.search(body=body, index='telegram_messages')
        transformed_hit = transform_hits(companyName, result)
        elastic_output.append(transformed_hit)
        print("Company : ", companyName, " result ", result)
    render_page(elastic_output)


def transform_hits(companyName, result):
    hits = result.raw['hits']['hits']
    result_hits = []
    for raw_hit in hits:
        raw_hit = raw_hit['_source']

        textRaw = raw_hit['raw_text']

        # if the text is too big..
        if len(textRaw) > 150:
            textRaw = textRaw[:130] + "..."

        tran_hits = {
            'text': textRaw,
            'timestamp': raw_hit['timestamp'],
            'media_type': raw_hit['media']['type']
        }
        result_hits.append(tran_hits)
    out = {
        "companyName": companyName,
        "searchData": result_hits
    }
    return out


def render_page(companyData):
    pageTitle = 'Company Arrival Sheet'
    doc = dominate.document(title=pageTitle)
    with doc.head:
        # include the bootstrap magic
        link(rel='stylesheet',
             href='http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/css/bootstrap-combined.min.css')
        script(type='text/javascript', src='http://ajax.googleapis.com/ajax/libs/jquery/1.10.2/jquery.min.js')
        script(type='text/javascript', src='http://netdna.bootstrapcdn.com/twitter-bootstrap/2.3.2/js/bootstrap.min.js')

    with doc:
        with div(cls='container'):
            with div(cls='starter-template'):
                h1(pageTitle)
            with div(cls='menu'):
                with div(cls='accordion accordion-flush', id="accordianMain"):
                    count = 0
                    for companyEntry in companyData:  # for each college
                        count = count + 1
                        # generate the heading used for toggling
                        render_company_data(companyEntry, count)

    with open("results.html", "w") as outfile:
        outfile.truncate(0)
        outfile.write(doc.render())


@div(cls='accordion-group')
def render_company_data(companyEntry, count):
    id = 'item' + str(count)
    with div(cls='accordion-heading'):
        with a(companyEntry['companyName'], cls='accordion-toggle', href='#' + id):
            attr({
                'data-toggle': 'collapse'
            })
    with div(id=id, cls='accordion-body collapse'):
        attr({
            'data-bs-parent': '#accordianMain'
        })
        with div(cls='accordion-inner'):
            with table(cls='table table-striped table-condensed'):
                with thead():
                    # the table header for each company entry
                    with tr():
                        th("Text")
                        th("Time")
                        th("Media Type")
                with tbody():
                    for hit in companyEntry['searchData']:
                        # render each hit to a table row
                        with tr():
                            td(hit['text'])
                            td(hit['timestamp'])
                            td(hit['media_type'])


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
