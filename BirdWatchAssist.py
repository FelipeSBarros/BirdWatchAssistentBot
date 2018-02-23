# -*- coding: utf-8 -*-
"""
Created on Fri Feb 23 15:16:52 2018

@author: felipe
"""

import json 
import requests
import time
import urllib #to handle with special characters
import pandas as pd
from dbhelper import DBHelper # import class and method created to work with sqlite3
from API import API, EBirdKey # bot API

TOKEN = API
URL = "https://api.telegram.org/bot{}/".format(TOKEN)
db = DBHelper()

def get_url(url): # Function to get URL and set encode
    response = requests.get(url)
    content = response.content.decode("utf8")
    return content

def get_json_from_url(url): # function the get and return json from URL
    content = get_url(url)
    js = json.loads(content)
    return js

def get_last_update_id(updates): #Function to calculate and get the last update id
    update_ids = []
    for update in updates["result"]:
        update_ids.append(int(update["update_id"]))
    return max(update_ids)

def get_updates(offset=None):
    url = URL + "getUpdates?timeout=100"
    if offset:
        url += "&offset={}".format(offset) #  (in URLs, the argument list strats with ? but further arguments are separated with &).
    js = get_json_from_url(url)
    return js

def get_last_chat_id_and_text(updates):
    num_updates = len(updates["result"])
    last_update = num_updates - 1
    text = updates["result"][last_update]["message"]["text"]
    chat_id = updates["result"][last_update]["message"]["chat"]["id"]
    return (text, chat_id)

def send_message(text, chat_id, reply_markup = None):
    text = urllib.parse.quote_plus(text)
    url = URL + "sendMessage?text={}&chat_id={}".format(text, chat_id)
    if reply_markup:
        url += "&reply_markup={}".format(reply_markup)
    get_url(url)
    
def send_location(chat, lon, lat):
    #lat = -22.0
    #lon = -42.0
    url = URL + "sendLocation?chat_id={}&latitude={}&longitude={}".format(chat, lat, lon)
    get_url(url)
    
def get_location():
    reply_markup = ['{"keyboard":[[{"text":"Send Location","request_location":true}]]}']
    url = URL + "sendMessage?chat_id={}&text=Send Location&reply_markup={}".format(chat, reply_markup[0])
    get_url(url)
    #url = URL + "sendMessage?chat_id={}&text=Send Location&reply_markup={'keyboard':[[{'text':'Send Location','request_location':true}]]}".format(chat)
    
    
    return json.dumps(reply_markup)    

def bird_search(lon, lat):
    url = "https://ebird.org/ws2.0/data/obs/geo/recent"
    querystring = {"lat":"{}".format(lat),"lng":"{}".format(lon)}
    headers = {'X-eBirdApiToken': '{}'.format('gcqrk8ecdt96')}
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(response.text)
    response = pd.DataFrame(response)
    response = response[["sciName", "comName", "lng", "lat"]]
    return response
                
def handle_updates(updates):
    for update in updates["result"]:
        chat = update["message"]["chat"]["id"]
        
        if "text" in update["message"].keys():
            text = update["message"]["text"]
            if text == "/start":
                send_message("Welcome to your personal To Do list. Send any text to me and I'll store it as an item. Send /done to remove items", chat)
                reply_markup = get_location()
                #send_message(teschat_id = chat, reply_markup)
                send_location(chat)
            else:
                pass
        elif "location" in update["message"].keys():
            lon = update["message"]["location"]['longitude']
            lat = update["message"]["location"]['latitude']
            send_location(chat, lon, lat)
            birds = bird_search(lon, lat)
            #send_message("{}".format(birds), chat)
        else:
            pass   
        #elif text.startswith("/"):
        #    continue
#        elif text in items:
#            db.delete_item(text, chat)
#            items = db.get_items(chat)
#            message = "\n".join(items)
#            keyboard = build_keyboard(items)
#            send_message("Select an item to delete", chat, keyboard)
#        else:
#            db.add_item(text, chat)
#            items = db.get_items(chat)
#            message = "\n".join(items)
#            send_message(message, chat)

def main():
    db.setup()
    last_update_id = None
    while True:
        print("getting updates")
        updates = get_updates(last_update_id)
        if len(updates["result"])>0:
            last_update_id = get_last_update_id(updates) + 1
            handle_updates(updates)
        time.sleep(0.5)


if __name__ == '__main__':
    main()