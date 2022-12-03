import json
from time import sleep
import requests
import os
from dotenv import load_dotenv

load_dotenv()

from_num = os.environ.get("FROM_PHONE_NUM_ID")
to_num = os.environ.get("TO_PHONE_NUM_ID").split(",")

api_endpoint = f"https://graph.facebook.com/v15.0/{from_num}/messages"
access_token = os.environ.get("ACCESS_TOKEN_WHATSAPP")

headers = {"Authorization": f"Bearer {access_token}"}


def send_alert(gid: int) -> None:
    with open("json/alerta.json", "r") as f:
        data = json.load(f)
    
    data['to'] = to_num[0]
    data['text']['body'] = f"10+ news change on guild id: \"{gid}\", please verify."

    requests.post(api_endpoint, json=data, headers=headers)


def send_news(news: list) -> None:
    with open("json/noticia.json", "r") as f:
        data = json.load(f)
    
    components = data['template']['components']

    for n in news:
        components[0]['parameters'][0]['image']['link'] = n.thumbnail
        components[1]['parameters'][0]['text'] = n.title
        components[1]['parameters'][1]['text'] = n.description
        components[2]['parameters'][0]['text'] = n.link.split('/')[-1]

        data['template']['components'] = components
        for num in to_num:
            data['to'] = num
            #print(data)
            r = requests.post(api_endpoint, json=data, headers=headers)
            if r.status_code != 200:
                print(r.text)
            sleep(10)

