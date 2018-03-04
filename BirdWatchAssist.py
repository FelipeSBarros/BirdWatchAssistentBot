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
import random
from dbhelper import DBHelper # import class and method created to work with sqlite3
from API import API, EBirdKey # bot API, E-Bird API

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

def build_keyboard(items):
    keyboard = [[item] for item in items]
    reply_markup = {"keyboard" : keyboard, "one_time_keyboard" : True}
    return json.dumps(reply_markup)
    
def send_location(chat, lon, lat):
    #lat = -27.364056
    #lon = -55.904087

    url = URL + "sendLocation?chat_id={}&latitude={}&longitude={}".format(chat, lat, lon)
    get_url(url)
    
def get_location():
    reply_markup = {"keyboard": [[{"text": "Send Location", "request_location": True}], ["Cancel"]], "one_time_keyboard": True, "resize_keyboard": True}
    json.dumps(reply_markup)
    return json.dumps(reply_markup)

def bird_search(lon, lat):
    url = "https://ebird.org/ws2.0/data/obs/geo/recent"
    querystring = {"lat":"{}".format(lat),"lng":"{}".format(lon)}
    headers = {'X-eBirdApiToken': '{}'.format(EBirdKey)}
    response = requests.request("GET", url, headers=headers, params=querystring)
    response = json.loads(response.text)
    response = pd.DataFrame(response)
    response = response[["sciName"]]#, "comName", "lng", "lat"]]
    response = response.rename(index=str, columns={"sciName":"ScientificName"})#, "comName":"CommonName"})
    response  = response.sample(5)
    response = response.values.flatten().tolist()
    return response#.sort()

def get_birdSongs(birdName, chat):
    url = 'http://www.xeno-canto.org/api/2/recordings?query={}'.format(birdName)
    soundLink = requests.get(url)
    if soundLink.status_code == 200:
        soundLink = soundLink.content.decode("utf8")
        soundLink = json.loads(soundLink)
        if len(soundLink["recordings"]) >= 1:
            soundLink = random.choice(soundLink["recordings"])
            #soundLink = soundLink["recordings"]
            file = soundLink["file"]
            file = file.strip("//")
            sngType = soundLink["type"]
            requests.get(URL+'sendAudio?chat_id={}&audio={}&caption=Type: {}'.format(chat, file, sngType))
        else:
            pass
    else:
        msg = "I Couldn't find any bird song for {} on *Xeno-Canto database".format(birdName)
        send_message(msg, chat)

def handle_updates(updates):
    for update in updates["result"]:
        chat = update["message"]["chat"]["id"]
        
        if "text" in update["message"].keys():
            text = update["message"]["text"]
            if text == "/start":
                send_message("Welcome to your personal Bird Wathcing Assistent.\nThis Bot will help you by provinding information of recently seen bird around your area.\n\nShare your location and it will retreive a list of five randomly selected species recently seen and registered on E-Bird Database.\n\nThen, choosing one species will retrieve its songs, so you can get used with its songs.", chat)
                reply_markup = get_location()
                send_message("Send Loction", chat_id = chat, reply_markup = reply_markup)
            elif text.startswith("Song:"):
                birdname = text.strip("Song: ")
                print(birdname)
                get_birdSongs(birdname, chat)
            else:
                pass
        elif "location" in update["message"].keys():
            lon = update["message"]["location"]['longitude']
            lat = update["message"]["location"]['latitude']
            birds = bird_search(lon, lat)
            birds = ['{}{}'.format("Song: ", b) for b in birds]
            print(lon, lat)
            keyboard = build_keyboard(birds)
            send_message("Select an item to delete", chat, keyboard)
        else:
            pass

def main():
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