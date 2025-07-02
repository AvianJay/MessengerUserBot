#!/usr/bin/env python
from selenium import webdriver
from selenium.common import NoSuchElementException, ElementNotInteractableException
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.common.by import By
from selenium.webdriver import Keys, ActionChains
from selenium.webdriver.support.ui import Select
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time
import sys
import os
import json
import requests
import threading
import server
from datetime import datetime, timedelta
import pickle
import random
import naniexam
import hleexam
import quote
import hashlib
from g4f.client import Client
gptClient = Client()

config_version = 6
bot_version = "0.9 Beta"

qwerty_to_bopomofo = {
    # 聲母/韻母（符號區）
    '1': 'ㄅ', 'q': 'ㄆ', 'a': 'ㄇ', 'z': 'ㄈ',
    '2': 'ㄉ', 'w': 'ㄊ', 's': 'ㄋ', 'x': 'ㄌ',
    'e': 'ㄍ', 'd': 'ㄎ', 'c': 'ㄏ',
    'r': 'ㄐ', 'f': 'ㄑ', 'v': 'ㄒ',
    '5': 'ㄓ', 't': 'ㄔ', 'g': 'ㄕ', 'b': 'ㄖ',
    'y': 'ㄗ', 'h': 'ㄘ', 'n': 'ㄙ',
    'u': 'ㄧ', 'j': 'ㄨ', 'm': 'ㄩ',
    '8': 'ㄚ', 'i': 'ㄛ', 'k': 'ㄜ', ',': 'ㄝ',
    '9': 'ㄞ', 'o': 'ㄟ', 'l': 'ㄠ', '.': 'ㄡ',
    '0': 'ㄢ', 'p': 'ㄣ', ';': 'ㄤ', '/': 'ㄥ',
    '-': 'ㄦ',

    # 聲調符號（音調）
    '6': 'ˊ',  # 第二聲
    '3': 'ˇ',  # 第三聲
    '4': 'ˋ',  # 第四聲
    '7': '˙'   # 輕聲
}

default_config = {
    "email": 'blahblahblah@meta.com',
    'password': 'MetaIsTheBest',
    'thread_id': '123456789',
    'check_pagamo': False,
    'headless': False,
    'message_log_server': True,
    "config_version": config_version,
    # "graph_token": "",
    "sync_cookies": True,
    "sync_cookies_duration": 5,
    "owner_id": 0,
    "public_url": "http://example.com:3000/",
    "use_wdm": True,
    "server_port": 3000,
    "adult_content": False,
}
config_path = "config.json"
config = None

try:
    if os.path.exists(config_path):
        config = json.load(open(config_path, "r"))
        # Todo: verify
        if not isinstance(config, dict):
            print("Config file is not a valid JSON(dict) object, resetting to default config.")
            config = default_config.copy()
        for key in config.keys():
            if not isinstance(config[key], type(default_config[key])):
                print(f"Config key '{key}' has an invalid type, resetting to default value.")
                config[key] = default_config[key]
        # if "config_version" not in config:
        #     print("Config file does not have 'config_version', resetting to default config.")
        #     config = default_config.copy()
    else:
        config = default_config.copy()
        json.dump(config, open(config_path, "w"))
        print("First start, please edit config and execute again!")
        sys.exit(1)
except ValueError:
    config = default_config.copy()
    json.dump(config, open(config_path, "w"))

if config.get("config_version", 0) < config_version:
    print("Updating config file from version", config.get("config_version", 0), "to version", config_version)
    for k in default_config.keys():
        if config.get(k) == None:
            config[k] = default_config[k]
    config["config_version"] = config_version
    print("Saving...")
    json.dump(config, open(config_path, "w"))
    print("Done.")

opt = webdriver.ChromeOptions()
opt.add_argument("--disable-notifications")
opt.add_argument("--disable-gpu")
opt.add_argument("--disable-accelerated-video")
opt.add_argument("--disable-accelerated-video-encode")
if config['headless']:
    opt.add_argument("--headless")

if config.get("use_wdm", True):
    driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opt)
else:
    driver = webdriver.Chrome(options=opt)

class MessengerUser(object):
    def __init__(self, name, avatar, id):
        self.name = name
        self.avatar = avatar
        self.id = id

    def __str__(self):
        return f"{self.name} ({self.id})"

    def __repr__(self):
        return f"MessengerUser(name={self.name}, avatar={self.avatar}, id={self.id})"
    
    def to_dict(self):
        return {
            "name": self.name,
            "avatar": self.avatar,
            "id": self.id
        }
    
    def is_self(self):
        return self.id == 0

    @classmethod
    def from_dict(cls, data):
        return cls(
            name=data.get("name"),
            avatar=data.get("avatar"),
            id=data.get("id")
        )

class MessengerMessage(object):
    def __init__(self, sender: MessengerUser, message, time=datetime.now().timestamp(), reply=None):
        self.sender = sender
        self.message = message
        self.time = time
        self.reply = reply

    def __str__(self):
        reply_str = f" (reply to {self.reply.sender})" if self.reply else ""
        return f"{self.sender} : {self.message} at {self.time}{reply_str}"

    def __repr__(self):
        return f"MessengerMessage(sender={repr(self.sender)}, message={self.message}, time={self.time}, reply={repr(self.reply)})"
    
    def to_dict(self):
        return {
            "sender": self.sender.to_dict(),
            "message": self.message,
            "time": self.time,
            "reply": self.reply.to_dict() if self.reply else None
        }

    @classmethod
    def from_dict(cls, data):
        sender = MessengerUser.from_dict(data["sender"])
        message = data["message"]
        time_val = data.get("time", datetime.now().timestamp())
        reply = cls.from_dict(data["reply"]) if data.get("reply") else None
        return cls(sender, message, time_val, reply)

def login():
    print('Try to login...')
    if os.path.exists('cookies.pkl'):
        print('Cookie Found. Login with cookie...')
        driver.get("https://www.messenger.com/")
        cookies = pickle.load(open("cookies.pkl", "rb"))
        for cookie in cookies:
            add = {'name': cookie['name'], 'value': cookie['value']}
            driver.add_cookie(add)
        driver.get(f'https://www.messenger.com/t/{config["thread_id"]}')
    else:
        print('Cookie not found. Login with email and password...')
        driver.get("https://www.messenger.com/")
        time.sleep(2)
        ActionChains(driver) \
            .send_keys_to_element(driver.find_element(By.ID, "email"), config['email']) \
            .perform()
        ActionChains(driver) \
            .send_keys_to_element(driver.find_element(By.ID, "pass"), config['password']) \
            .perform()
        driver.find_element(By.CSS_SELECTOR, "span._2qcu").click()
        driver.find_element(By.ID, 'loginbutton').click()
        driver.implicitly_wait(5)
        input("waiting... pls enter.")
        print('Saving cookie...')
        save_cookies()

def save_cookies():
    pickle.dump(driver.get_cookies(), open("cookies.pkl", "wb"))

def sync_cookies():
    while True:
        print("Saving Cookies...")
        save_cookies()
        time.sleep(config["sync_cookies_duration"] * 60)


def enter():
    ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()


def denyuser(name, mode="c", action=None):
    if os.path.exists("denyusers.json"):
        denys = json.load(open("denyusers.json", "r"))
    else:
        denys = {}
    if mode == "c":
        return denys.get(name, False)
    elif mode == "s":
        if action is None:
            denys[name] = not denys.get(name, False)
        else:
            denys[name] = action
        json.dump(denys, open("denyusers.json", "w"))


pcookies, pheaders, pdata = {}, {}, {}


def checkp(send):
    text = None
    ids = cache("pagamo", default=[])
    response = requests.post('https://www.pagamo.org/mission', cookies=pcookies, headers=pheaders, data=pdata)
    json_obj = json.loads(response.content)
    m = 0
    n = ''
    a = ''
    r = ''
    s = ''
    id = 0
    if json_obj['data']['missions'][0]:
        text = []
        for i in json_obj['data']['missions']:
            print('名稱：' + i['name'] + '分類：' + i['category'])
            text.append(f'名稱：{i["name"]}分類：{i["category"]}')
            if i['category'] == 'general':
                # 在這裡進行mission的處理
                m = 1
                a = i['assigner']
                n = i['name']
                r = i['remain_text']
                s = i['status']
                id = int(i['id'])
    if m == 1 and send and not id in ids and s == 'is_new':
        stext = []
        stext.append('\\PaGamONotify/')
        stext.append('新的PaGamO作業！')
        stext.append(f'作業：{n}')
        stext.append(f'{a}老師出的')
        stext.append(r)
        for m in stext:
            formatedtext = m + '\n'
        sendmsg(stext)
        ids.append(id)
        cache("pagamo", ids)
        print('有新的作業！ID:' + str(id))
        print('傳送完畢。訊息：' + formatedtext)
    else:
        print('沒有新作業或send是false。')
    return text


def gototid(tid):
    href_value = f'/t/{tid}/'  # 要查找的href值

    driver.find_element(By.CSS_SELECTOR, f'a[href="{href_value}"]').click()


sendmsg_limiter = threading.Semaphore(1)

def sendmsg(msg_list):
    # m = '\n'.join(msg_list)  # 避免開頭多 \n
    acquired = sendmsg_limiter.acquire()
    print("Sending Message")
    try:
        if isinstance(msg_list, str):
            msg_list = msg_list.strip().split("\n")
        try:
            textbox = driver.find_element(By.CSS_SELECTOR, '[aria-placeholder="Aa"]')
            textbox.click()  # 確保獲得焦點
            for msg in msg_list:
                if "{random}" in msg:
                    msgs = msg.split("{random}")
                    for idx, m in enumerate(msgs):
                        textbox.send_keys(m)
                        if idx != len(msgs) - 1:
                            textbox.send_keys(" @")
                            time.sleep(.2)
                            for i in range(random.randint(0, 6)):
                                ActionChains(driver).send_keys(Keys.ARROW_DOWN).perform()
                            ActionChains(driver).send_keys(Keys.ENTER).perform()
                else:
                    textbox.send_keys(msg)
                    ActionChains(driver).key_down(Keys.SHIFT).send_keys(Keys.ENTER).key_up(Keys.SHIFT).perform()
            # Only press ENTER at the end to send the message
            textbox.send_keys(Keys.ENTER)
        except Exception as e:
            print("錯誤:", e)
    finally:
        if acquired:
            sendmsg_limiter.release()

server.sendmsg = sendmsg


def sendimage(filepath):
    upload = driver.find_element(By.CSS_SELECTOR, 'input[type="file"]')
    upload.send_keys(os.path.abspath(filepath))
    sendmsg([])


get_running = []
get_limiter = threading.Semaphore(1)

def web_get_user_picture(id, hash):
    if id in get_running:
        return
    else:
        get_running.append(id)
    get_limiter.acquire()
    print("Trying to get avatar on Facebook...")
    caches = cache("highqsave", default={})
    pic_driver = webdriver.Chrome(options=opt)
    try:
        if os.path.exists('cookies_facebook.pkl'):
            print('Cookie Found. Login with cookie...')
            pic_driver.get("https://www.facebook.com/")
            cookies = pickle.load(open("cookies_facebook.pkl", "rb"))
            for cookie in cookies:
                add = {'name': cookie['name'], 'value': cookie['value']}
                pic_driver.add_cookie(add)
        else:
            print('Cookie not found. Login with email and password...')
            pic_driver.get("https://www.facebook.com/")
            time.sleep(2)
            ActionChains(pic_driver) \
                .send_keys_to_element(pic_driver.find_element(By.ID, "email"), config['email']) \
                .perform()
            ActionChains(pic_driver) \
                .send_keys_to_element(pic_driver.find_element(By.ID, "pass"), config['password']) \
                .perform()
            pic_driver.find_element(By.CSS_SELECTOR, "button[name=login]").click()
            # pic_driver.find_element(By.ID, 'loginbutton').click()
            pic_driver.implicitly_wait(5)
            input("waiting... pls enter.")
            print('Saving cookie...')
            pickle.dump(pic_driver.get_cookies(), open("cookies_facebook.pkl", "wb"))
        print("Go to user profile page...")
        pic_driver.get(f"https://www.facebook.com/{id}/")
        for i in range(10):
            print(str(i) + "...")
            if i == 9:
                print("idk")
                # pic_driver.quit()
                # get_running.remove(id)
                # return
                break
            time.sleep(5)
            if pic_driver.title != "Facebook":
                break
        try:
            pic_driver.find_element(By.CSS_SELECTOR, "[aria-label=關閉]").click()
            # time.sleep(1)
        except Exception as e:
            # print(str(e))
            pass
        time.sleep(2)
        im = pic_driver.find_element(By.CSS_SELECTOR, "image[style='height:168px;width:168px']")
        # height:168px;width:168px
        # xlink:href
        furl = im.get_attribute("xlink:href")
        imb = im.find_element(By.XPATH, "../../../../.")
        try:
            imb.click()
            time.sleep(1)
            for i in range(10):
                print(str(i) + "...")
                try:
                    image = pic_driver.find_element(By.CSS_SELECTOR, "img[data-visualcompletion=media-vc-image]")
                    break
                except:
                    time.sleep(5)
            url = image.get_attribute("src")
            print("Got image URL.")
        except:
            url = furl
            print("Using smaller picture.")

        r = requests.get(url, stream=True)
        if r.status_code == 200:
            temp_path = os.path.join("picture_caches", f"{id}.jpg")
            with open(temp_path, 'wb') as f:
                for chunk in r.iter_content(1024):
                    f.write(chunk)
            caches[id] = hash
            cache("highqsave", caches)
            print("Downloaded.")
        pic_driver.quit()
        print("Replacing original picture...")
        try:
            with open('messagelog.json', 'r') as f:
                mjson = json.loads(f.read())
            if mjson['messages'] is None:
                mjson['messages'] = []
        except:
            mjson = {}
            mjson['messages'] = []
        for msg in mjson["messages"]:
            for i, h in caches.items():
                msg["sender"]["avatar"] = msg["sender"]["avatar"].replace(h, i)
        with open('messagelog.json', 'w') as f:
            f.write(json.dumps(mjson))
        print("Finished.")
    except Exception as e:
        try:
            pic_driver.quit()
        except:
            pass
        print("ERROR:", str(e))
    get_running.remove(id)
    get_limiter.release()
    return


def get_user_picture(id, orig):
    # if not config["graph_token"]:
    #     return None
    # res = requests.get(f"https://graph.facebook.com/{id}?fields=picture.width(720).height(720)&redirect=false&access_token={config["graph_token"]}").json()
    # if res.get("picture"):
    #     return res.get("picture", {}).get("data", {}).get("url", None)
    id = str(id)
    caches = cache("highqsave", default={})
    if picture_caches.get(orig):
        with open(os.path.join("picture_caches", f"{picture_caches[orig]}.jpg"), "rb") as f:
            hash = hashlib.sha256(f.read()).hexdigest()
        if caches.get(id):
            if caches.get(id) == hash:
                return os.path.join("picture_caches", f"{id}.jpg")
            else:
                t = threading.Thread(target=web_get_user_picture, args=(id, hash,))
                t.daemon = True
                t.start()
                return os.path.join("picture_caches", f"{id}.jpg")
        else:
            t = threading.Thread(target=web_get_user_picture, args=(id, hash,))
            t.daemon = True
            t.start()
            return cache_picture(orig)
    r = requests.get(orig, stream=True)
    if r.status_code == 200:
        hash = hashlib.sha256()
        for chunk in r.iter_content(1024):
            hash.update(chunk)
        hash = hash.hexdigest()
        if caches.get(id):
            if caches.get(id) == hash:
                return os.path.join("picture_caches", f"{id}.jpg")
            else:
                t = threading.Thread(target=web_get_user_picture, args=(id, hash,))
                t.daemon = True
                t.start()
                return os.path.join("picture_caches", f"{id}.jpg")
        else:
            t = threading.Thread(target=web_get_user_picture, args=(id, hash,))
            t.daemon = True
            t.start()
            return cache_picture(orig)
    return cache_picture(orig)


def cache(id, data=None, default=None):
    if os.path.exists(".cache.json"):
        cachef = json.load(open(".cache.json", "r"))
    else:
        cachef = {}
    if data:
        cachef[id] = data
        json.dump(cachef, open(".cache.json", "w"))
    else:
        return cachef.get(id, default)


picture_caches = cache("picture", default={})

def cache_picture(url):
    global picture_caches
    if os.path.exists(os.path.join("picture_caches", "temp.jpg")):
        os.remove(os.path.join("picture_caches", "temp.jpg"))
    if "platform-lookaside.fbsbx.com" in url:
        try:
            qid = url.split("asid=")[1].split("&")[0]
        except IndexError:
            qid = url
    else:
        qid = url

    if picture_caches.get(qid):
        return os.path.join("picture_caches", f"{picture_caches[qid]}.jpg")

    if not os.path.exists("picture_caches"):
        os.mkdir("picture_caches")

    r = requests.get(url, stream=True)
    if r.status_code == 200:
        temp_path = os.path.join("picture_caches", f"temp_{int(time.time()*1000)}.jpg")
        with open(temp_path, 'wb') as f:
            for chunk in r.iter_content(1024):
                f.write(chunk)

        with open(temp_path, "rb") as f:
            hash = hashlib.sha256(f.read()).hexdigest()

        final_path = os.path.join("picture_caches", f"{hash}.jpg")
        if not os.path.exists(final_path):
            os.rename(temp_path, final_path)
        else:
            os.remove(temp_path)
        picture_caches[qid] = hash
        cache("picture", picture_caches)
        return final_path
    else:
        return None


bopomofo_set = set(qwerty_to_bopomofo.values())

def checkmsg(message: MessengerMessage):
    returnvalue = None
    is_self = message.sender.is_self()
    if is_self: return
    msg = message.message.strip().split()
    reply = message.reply
    # print('Checking message ' + str(msg))
    if msg[0].startswith('!'):
        print('Checking message ' + msg[0])
        if msg[0] == '!sadbee':
            returnvalue = ["傻逼"]
        elif msg[0] == '!say':
            if len(msg) == 2:
                returnvalue = [msg[1]]
            elif len(msg) > 2:
                c = None
                returnvalue = []
                for m in msg:
                    if c is not None:
                        returnvalue.append(m)
                    else:
                        c = True
            else:
                returnvalue = ["把要我說的訊息放後面好嗎(!say [訊息])"]
        # elif msg[0] == '!pagamo':
        #     text = checkp(False)
        #     if text is None:
        #         text = ['沒作業']
        #     returnvalue = text
        elif msg[0] == '!log':
            text = [config["public_url"]]
            returnvalue = text
        elif msg[0] == '!help':
            text = []
            text.append('哈哈這是指令')
            text.append('!help - 顯示這個訊息')
            text.append('!say [訊息] - 說話')
            # text.append('!pagamo - 看PaGamO作業')
            text.append('!sadbee - 傻逼')
            text.append('!log - 聊天記錄的網址')
            text.append('!miq (回覆的訊息) - 創建一個引用圖片的訊息')
            text.append('!dsize - 測量長度')
            text.append('!gpt [文字] - 與ChatGPT聊天')
            text.append('!gptclean - 清除GPT記憶')
            text.append('!gptsearch [文字] - 有搜尋功能的GPT')
            text.append('!gptimage [**提示] - AI生圖')
            text.append('!2zhuyin [字串 or 回覆] - 沒切輸入法')
            text.append('!userinfo [回覆] - 使用者資訊')
            text.append('!webhook - 查看Webhook資訊')
            if config["adult_content"]:
                text.append("!r34 [**tags] (page=頁數) - r34 muhehehe")
                text.append("!r34tag [query] - r34 tags search")
            text.append('!about - 關於')
            if message.sender.id == config["owner_id"]:
                text.append('')
                text.append('管理員指令：')
                text.append('!denyuser [使用者ID/回覆的訊息] - 禁止使用者使用指令')
                text.append('!shutdown - 關閉機器人')
            returnvalue = text
        elif msg[0] == '!getnanians':
            if msg[1]:
                t = []
                t.append(naniexam.get(msg[1]))
                returnvalue = t
            else:
                returnvalue = ['用法：!getnanians [題目ID]']
        elif msg[0] == '!gethleans':
            # hleexam.get(hleexam.getcid(msg[1]), "HanlinQT.json")
            if msg[1]:
                t = []
                t.append(hleexam.get(hleexam.getcid(msg[1]), "HanlinQT.json"))
                hleexam.create(open("HanlinQT.json", 'r', encoding="utf-8").read(), "HanlinQT.html")
                t.append('http://ip.avianjay.sbs:3000/hans')
                returnvalue = t
            else:
                returnvalue = ['用法：!gethleans [題目ID]']
        elif msg[0] == '!gpt':
            if len(msg) == 2:
                returnvalue = []
                returnvalue = gpt(msg[1]).split("\n")
            elif len(msg) > 2:
                c = None
                returnvalue = []
                del msg[0]
                gpttxt = " ".join(msg)
                returnvalue = gpt(gpttxt).split("\n")
            else:
                returnvalue = ['用法：!gpt [**文字]']
        elif msg[0] == '!gptclean':
            gptClean()
            returnvalue = ['成功清除記憶。']
        elif msg[0] == '!gptsearch':
            if len(msg) == 2:
                returnvalue = []
                returnvalue = gpt(msg[1], search=True).split("\n")
            elif len(msg) > 2:
                c = None
                returnvalue = []
                del msg[0]
                gpttxt = " ".join(msg)
                returnvalue = gpt(gpttxt, search=True).split("\n")
            else:
                returnvalue = ['用法：!gptsearch [**文字]']
        elif msg[0] == '!gptimage':
            if len(msg) == 2:
                returnvalue = []
                returnvalue.append(gptImage(msg[1]))
            elif len(msg) > 2:
                c = None
                returnvalue = []
                del msg[0]
                gpttxt = " ".join(msg)
                returnvalue.append(gptImage(gpttxt))
            else:
                returnvalue = ['用法：!gptimage [**提示]']
        elif msg[0] == '!r34':
            if config["adult_content"]:
                if len(msg) == 2:
                    if 'page=' in msg[1]:
                        pid = msg[1].split('page=')[1]
                        returnvalue = []
                        returnvalue.append(r34(pid=pid))
                    else:
                        returnvalue = []
                        returnvalue.append(r34(msg[1]))
                elif len(msg) > 2:
                    c = None
                    r34tag = None
                    pid = 1
                    returnvalue = ['']
                    for m in msg:
                        if c is not None:
                            if 'page=' in m:
                                pid = m.split('page=')[1]
                            else:
                                if not r34tag:
                                    r34tag = m
                                else:
                                    r34tag = r34tag + '%20' + m
                        else:
                            c = True
                    returnvalue.append(r34(r34tag))
                else:
                    returnvalue = [r34()]
            else:
                returnvalue = ["這個指令需要開啟成人內容。"]
        elif msg[0] == '!r34tag':
            if config["adult_content"]:
                if len(msg) == 2:
                    returnvalue = []
                    returnvalue.append(r34tags(msg[1]))
                elif len(msg) > 2:
                    returnvalue = '僅限1個！'
                else:
                    returnvalue = [r34tags()]
            else:
                returnvalue = ["這個指令需要開啟成人內容。"]
        elif msg[0] == '!about':
            returnvalue = []
            returnvalue.append('Messenger Bot v' + str(bot_version))
            returnvalue.append('by AvianJay')
            returnvalue.append('本次更新：')
            returnvalue.append('AutoReply更新')
            returnvalue.append('更多敷衍')
            returnvalue.append('資料處理更新')
            returnvalue.append('新增userinfo指令')
            returnvalue.append('更新dsize指令')
            returnvalue.append('更新webdriver-manager')
            returnvalue.append('現可禁止使用者使用指令')
            returnvalue.append('現可使用指令關閉機器人')
            returnvalue.append('現可限制成人內容')
        elif msg[0] == '!dsize':
            returnvalue = dsize(message.sender)
        elif msg[0] == '!miq':
            if reply:
                fn = quote.create(reply.sender.avatar, reply.message, reply.sender.name)
                sendimage(fn)
            else:
                returnvalue = ["找不到已回覆的訊息。"]
        elif msg[0] == '!2zhuyin':
            if reply[0]:
                returnvalue = toZhuyin(reply[0])
            elif len(msg) > 1:
                returnvalue = toZhuyin(msg[1])
            else:
                returnvalue = ["傻逼沒東西"]
        elif msg[0] == '!userinfo':
            senderdict = message.sender.to_dict()
            returnvalue = ["用戶資訊："]
            returnvalue.append(f"名稱：{senderdict['name']}")
            returnvalue.append(f"ID：{senderdict['id']}")
            returnvalue.append(f"頭像：{config['public_url']}{senderdict['avatar']}")
            if message.reply:
                replydict = message.reply.sender.to_dict()
                returnvalue.append("回覆的訊息：")
                returnvalue.append(f"名稱：{replydict['name']}")
                returnvalue.append(f"ID：{replydict['id']}")
                returnvalue.append(f"頭像：{config['public_url']}{replydict['avatar']}")
        elif msg[0] == '!deny':
            if message.sender.id == config["owner_id"]:
                if reply:
                    if reply.sender.id:
                        if not len(msg) == 2 and msg[1] == "c":
                            denyuser(reply.sender.id, "s")
                        seted = "禁止" if denyuser(reply.sender.id, "c") else "允許"
                        returnvalue = [f"{reply.sender.id} 已被{seted}使用指令"]
                    else:
                        returnvalue = ["回覆的訊息沒有使用者ID。"]
                elif len(msg) >= 2:
                    if not len(msg) == 3 and msg[2] == "c":
                        denyuser(msg[1], "s")
                    seted = "禁止" if denyuser(msg[1], "c") else "允許"
                    returnvalue = [f"{msg[1]} 已被{seted}使用指令"]
                else:
                    returnvalue = ["用法：!denyuser [使用者ID/回覆的訊息]"]
            else:
                returnvalue = ["你沒有權限使用這個指令。"]
        elif msg[0] == '!shutdown':
            if message.sender.id == config["owner_id"]:
                returnvalue = ["正在關閉機器人..."]
                sendmsg(returnvalue)
                driver.quit()
                sys.exit(0)
            else:
                returnvalue = ["你沒有權限使用這個指令。"]
        elif msg[0] == '!webhook':
            webhook_url = config.get("public_url", "http://example.com:3000/") + server.secret
            returnvalue = [f"Webhook URL: {webhook_url}"]
            returnvalue.append("支持的Webhook類型：")
            returnvalue.append("discord, slack, github")
            returnvalue.append("只需在Webhook URL後面加上類型即可，例如：/discord")
        else:
            returnvalue = ["傻逼我看不懂你的指令"]
    elif msg[0].startswith("！"):
        returnvalue = ['用半形!傻逼']
    # lol autoreply
    elif msg[0].lower() in ["好", "好。", "cl3", "👌", "👍", "。"]:
        returnvalue = ['好。'] if is_self else None
    elif msg[0].lower() in ["好你嗎", "好你媽", "好三小", "好你媽啦", "好你碼", "好你妹", "好你老師", "好你爸", "好你爸啦", "好你媽啦", "好你妹啦", "好你老師啦", "好你碼啦", "行你媽", "行你嗎", "行三小", "行你媽啦", "行你碼", "行你妹", "行你老師", "行你爸", "行你爸啦", "行你媽啦", "行你妹啦", "行你老師啦", "行你碼啦", "哭三小", "哭你媽", "哭你嗎", "哭你妹", "哭你老師", "哭你爸", "哭你媽啦", "哭你妹啦", "哭你老師啦", "哭你爸啦"]:
        returnvalue = ['我做錯了嗎(⁠´⁠；⁠ω⁠；⁠｀⁠)'] if is_self else None
    elif msg[0].lower() in ["行", "說幹就幹", "好吧", "vu/6", "vu/", "vu/6行", "vu/6好吧", "vu/6說幹就幹", "行吧", "行。", "行了", "行了嗎", "行了嗎？"]:
        returnvalue = ['行吧。'] if is_self else None
    elif msg[0].lower() in ["幹", "乾", "靠北", "靠杯", "操", "呃", "崩潰", "fk", "fuck", "fucking", "fucking hell", "fucking", "e04", "靠北啊", "靠北阿", "靠杯啊", "靠杯阿", "媽的", "媽的啊", "媽的阿", "媽的啦", "媽的啦啊", "媽的啦阿", "媽的啦啊阿", "媽的啦啊阿啊", "幹你娘", "幹你娘啊", "幹你娘阿", "幹你娘啦", "幹你娘啦啊", "幹你娘啦阿", "幹你娘啦啊阿", "幹你娘啦啊阿啊", "幹你娘啦啊阿啊啊", "幹你娘啦啊阿啊啊啊", "幹你娘啦啊阿啊啊啊啊", "幹你娘啦啊阿啊啊啊啊啊", "幹你娘啦啊阿啊啊啊啊啊啊", "幹你娘啦啊阿啊啊啊啊啊阿", "幹你娘啦啊阿啊啊啊啊阿", "幹你娘啦阿", "操你媽", "操你媽啊", "操你媽阿", "操你媽啦", "操你媽啦啊", "操你媽啦阿", "操你媽啦啊阿", "操你媽啦啊阿啊", "操你媽啦啊阿啊啊", "操你媽啦啊阿啊啊啊", "操你媽啦啊阿啊啊啊啊", "操你媽啦啊阿啊啊啊啊啊", "操你媽啦啊阿啊啊啊啊阿", "操你媽啦啊阿啊啊啊阿", "操你媽啦阿", "操你媽啦啊", "操你媽啦啊阿", "操你媽啦啊阿啊", "操你媽啦啊阿啊啊", "操你媽啦啊阿啊啊啊", "操你媽啦啊阿啊啊啊啊", "操你媽啦啊阿啊啊啊啊阿", "操你媽啦啊阿啊啊啊阿"]:
        returnvalue = [random.choice(['你壞壞 不可以這樣', "我要跟老師講", "到底 都你在搞", "就你在搞", "就{random}在搞", "在哭", "。", "好啦好啦"])] if is_self else None

    elif msg[0] in ["笑死", "xd", "XD", "XDDD", "xdxd", "🤣", "哈哈", "哈哈哈", "噗"]:
        returnvalue = [random.choice(['你很快樂欸', "笑死", "好好笑", "超好笑"])] if is_self else None

    elif msg[0] in ["？", "?", "??", "???", "？？", "？？？", "問號", "問號臉", "蛤", "蛤？", "蛤蛤", "蛤蛤？", "蛤蛤蛤", "蛤蛤蛤？", "什麼", "什麼？", "什麼啦", "什麼東西", "什麼東西啊", "虫合", "虫合？", "虫合啦", "虫合東西", "虫合東西啊", "虫合東西啦", "虫合東西啊啦"]:
        returnvalue = [random.choice(['？你在問我嗎', "蛤", "虫合", "？"])] if is_self else None

    elif msg[0] in ["掰", "88", "bye", "再見", "晚安"]:
        returnvalue = ['掰掰～晚安唷～'] if is_self else None

    elif msg[0] in ["嗨", "hello", "hi", "你好", "👋"]:
        returnvalue = [random.choice(['嗨～你來啦', "海你好", "hii", "害你好"])] if is_self else None

    elif msg[0] in ["不要", "我不要", "不想", "不可以", "我拒絕", "幹不要"]:
        returnvalue = [random.choice(['喔...（默默縮回去）\n行吧。', "好吧"])] if is_self else None

    elif msg[0] in ["你很煩", "你有病", "你閉嘴", "白癡", "87", "87了", "87你媽", "87你爸", "87你老師", "87你妹", "噁", "噁心", "噁心死了", "噁心到爆"]:
        returnvalue = [random.choice(['你再說一次試試看（´-_ゝ-）', "在哭"])] if is_self else None

    elif any(m in bopomofo_set for m in msg[0]):
        returnvalue = ['你這什麼注音發言'] if is_self else None

    elif msg[0] in ["現在幾點", "幾點", "幾點啦", "幾.", "欸幹現在幾點", "現在幾點啦", "現在幾點了", "現在幾點鐘", "現在幾點了啦"]:
        now = datetime.now().strftime("%H:%M:%S")
        returnvalue = [f'現在是 {now} 喔'] if is_self else None

    elif random.randint(0, 50) == 30:
        returnvalue = [random.choice([
            '好。', "行。", "好吧。", "行吧。", "好唷。", "行唷。", "好啦。", "行啦。", "好啊。", "行啊。",
            "哇", "喔是喔真的假的", "嗯嗯", "收到", "了解", "知道了", "OK", "O", "👌", "👍", "嗯", "喔", "噢", "哦", "好喔", "行喔",
            "好啦好啦", "行啦行啦", "好哦", "行哦", "好耶", "行耶", "好der", "行der", "好勒", "行勒", "好捏", "行捏", "好嘛", "行嘛",
            "好嘛好嘛", "行嘛行嘛", "好啦好啦", "行啦行啦", "嗯嗯嗯", "嗯嗯好", "嗯嗯行", "嗯嗯嗯嗯", "嗯嗯嗯嗯嗯", "嗯嗯嗯嗯嗯嗯", "好好好", "行行行"
        ])] if is_self else None
    return returnvalue


def savemsg(message: MessengerMessage):
    # current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    # print(f'Saving Log {sender} pic {senderpic} msg {msg} time {current_time}')
    print(message)

    try:
        with open('messagelog.json', 'r') as f:
            mjson = json.loads(f.read())
        if mjson['messages'] is None:
            mjson['messages'] = []
    except:
        mjson = {}
        mjson['messages'] = []
    # if '已收回' in msg and '則訊息' in msg:
    #     mjson['messages'][-1]['message'] = f'{mjson["messages"][-1]["message"]}（可能已收回）'
    # else:
    mjson['messages'].append(message.to_dict())

    with open('messagelog.json', 'w') as f:
        f.write(json.dumps(mjson))


def process_message(message: MessengerMessage):
    try:
        sender = message.sender
        savemsg(message)
        if not denyuser(sender.id) and sender.id != -1:
            msg = checkmsg(message)
            if msg:
                sendmsg(msg)
    except KeyboardInterrupt:
        print("Detected KeyboardInterrupt. Exiting...")
        sys.exit(0)
    except Exception as e:
        print("Error:", str(e))
        try:
            sendmsg(["錯誤", str(e)])
        except:
            pass


def get_user_id(element):
    button = element.find_element(By.XPATH, "../.")
    button.click()
    linkele = None
    link = None
    for i in range(10):
        try:
            menu = driver.find_element(By.CSS_SELECTOR, "[role=menu]")
            linkele = menu.find_element(By.CSS_SELECTOR, "a")
            link = linkele.get_attribute("href")
            break
        except:
            time.sleep(.2)
            continue
    if not link:
        return None
    # ActionChains(driver).key_down(Keys.ESCAPE).perform()
    try:
        button.click()
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        pass
    try:
        return int(link.split(".com/")[1].split("/")[0])
    except:
        return link.split(".com/")[1].split("/")[0]


def checksend(latestmsg):
    # global text

    def find_reply_info(replytext):
        try:
            msglog = json.load(open("messagelog.json", "r"))["messages"]
            for msg in reversed(msglog):
                if msg["message"].strip() == replytext.strip():
                    reply = MessengerMessage.from_dict(msg)
                    return reply
        except Exception as e:
            print("Failed to open messagelog:", str(e))
        return MessengerMessage(
            sender=MessengerUser("不知道是誰", "https://avianjay.sbs/mr.jpg", -1),
            message=replytext,
            reply=None
        )

    xpath = '/html/body/div[1]/div/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[3]/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div/div/div[position()=last()]'
    xpathtyping = '/html/body/div[1]/div/div/div/div/div[2]/div/div/div[1]/div[1]/div/div[3]/div/div/div[1]/div/div/div/div/div/div[2]/div/div/div/div[1]/div/div/div/div/div/div/div/div[position()=last()-1]'

    text = ""
    replytext = None
    reply = None

    try:
        baseele = driver.find_element(By.XPATH, xpath)
        if baseele.get_attribute("role") == "grid":
            baseele = driver.find_element(By.XPATH, xpathtyping)

        try:
            ele = baseele.find_element(By.CSS_SELECTOR, "div[dir=auto]")
            text = ele.text
            if not text:
                # try to get emoji
                ele = baseele.find_element(By.CSS_SELECTOR, "img[referrerpolicy=origin-when-cross-origin]")
                src = ele.get_attribute("src")
                if "emoji.php" in src:
                    text = ele.get_attribute("alt")
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            ele = baseele.find_element(By.CSS_SELECTOR, "img[referrerpolicy=origin-when-cross-origin]")
            text = ele.get_attribute("src")
        
        lastm = [latestmsg[-1]]
        if len(latestmsg) > 1:
            lastm.append(latestmsg[-2])
        if baseele.id in lastm or text.startswith("blob:https://"):
            return latestmsg

        # 嘗試擷取回覆內容
        try:
            rele = baseele.find_elements(By.CSS_SELECTOR, "span[dir=auto][style='----base-line-clamp-line-height: 16px; --lineHeight: 16px;']")[0]
            relep = rele.find_element(By.XPATH, "./..")
            if relep.get_attribute("role") == "presentation":
                replytext = rele.find_element(By.CSS_SELECTOR, "div > div").text
                reply = find_reply_info(replytext)
            else:
                relei = baseele.find_element(By.CSS_SELECTOR, "img[alt=原始圖像]")
                replytext = relei.get_attribute('src')
                reply = find_reply_info(replytext)
        except KeyboardInterrupt:
            raise KeyboardInterrupt
        except:
            pass

        # reply = MessengerMessage(
        #     text=replytext,
        #     sender=replyinfo,
        #     reply=None
        # )
    
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except:
        text = "無法獲取訊息"
        # reply_user = None
        reply = None

    # not_self = True

    try:
        sender_element = None
        for _ in range(5):
            try:
                sender_element = baseele.find_element(By.CSS_SELECTOR, 'img[style="border-radius: 50%;"]')
                break
            except Exception:
                time.sleep(0.05)
        if sender_element is None:
            raise Exception("Cannot find sender element after retries")
        sender_name = sender_element.get_attribute('alt')
        userid = get_user_id(sender_element)
        sender_picture_path = get_user_picture(userid, sender_element.get_attribute('src'))
    except KeyboardInterrupt:
        raise KeyboardInterrupt
    except Exception as e:
        print("Error getting sender info:", str(e))
        sender_name = "ㄐㄐ人"
        sender_picture_path = cache_picture("https://avianjay.sbs/mr.jpg")
        userid = 0
        # not_self = False

    sender = MessengerUser(sender_name, sender_picture_path, userid)
    message = MessengerMessage(sender, text, reply=reply)

    # if not latestmsg:
    #     latestmsg.append(text)
    #     savemsg(sender_name, sender_picture_path, text)
    #     if not denyuser(sender_name):
    #         msg = checkmsg(text.split(' '), True, sender_name, reply)
    #         if msg:
    #             sendmsg(msg)
    if text != latestmsg[-1]:
        if text == "無法獲取訊息" and not message.sender.is_self():
            return latestmsg
        latestmsg.append(baseele.id)
        threading.Thread(target=process_message, args=(message,)).start()

        # savemsg(sender_name, sender_picture_path, text)
        # if not denyuser(sender_name):
        #     msg = checkmsg(text.split(' '), not_self, sender_name, reply)
        #     if msg:
        #         sendmsg(msg)

    return latestmsg


def pagamochk():
    while True:
        print('開始檢查PaGamO作業')
        checkp(True)
        print('檢查完畢。')
        time.sleep(300)


def searchans(q):
    ans = json.loads(open('pagamoquestions.json', 'r').read())
    finded = []
    for question in ans:
        if q in question['question']:
            f = {}
            f['q'] = question['question']
            f['a'] = question[question['correct']]
            finded.append(f)
    return finded

messages = [{"role": "system", "content": "你是一個文字助理，回答會被貼到 Messenger，請勿使用 Markdown，例如星號粗體、井號標題、反引號等，請用純文字格式回答。"}]

def gpt(text, search=False):
    global messages
    print("GPT Message:", text)
    sendmsg(["等一下..."])
    messages.append({"role": "user", "content": text})
    response = gptClient.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        web_search=search
    )
    reply_content = response.choices[0].message.content
    messages.append({"role": "assistant", "content": reply_content})
    return reply_content


def gptClean():
    global messages
    messages = [{"role": "system", "content": "你是一個文字助理，回答會被貼到 Messenger，請勿使用 Markdown，例如星號粗體、井號標題、反引號等，請用純文字格式回答。"}]


def gptImage(prompt):
    print("Generating Image Prompt:", prompt)
    sendmsg(["等一下我在生..."])
    response = gptClient.images.generate(
        model="gpt-image",
        prompt=prompt,
        response_format="url"
    )
    return response.data[0].url

last_used = cache("dsize", default={})

def dsize(sender):
    global last_used
    user_id = sender.id
    now_ts = time.time()  # 現在的 timestamp

    # 檢查是否已使用過且未過一天
    now = datetime.utcnow().date()
    last = datetime.utcfromtimestamp(last_used[user_id]).date()

    if user_id in last_used and now == last:
        return "一天只能量一次屌長。"

    # 更新使用時間為 timestamp
    last_used[user_id] = now_ts
    cache("dsize", last_used)

    # 隨機產生長度 (2-30)
    size = random.randint(2, 30)
    d_string = "=" * (size - 2)

    return [f"{sender.name} 的長度：{size}cm", f"8{d_string}D"]


def r34(tags=None, pid=1):
    if tags:
        r = requests.get(f'https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&tags={tags}&pid={pid}')
    else:
        r = requests.get(f'https://api.rule34.xxx/index.php?page=dapi&s=post&q=index&json=1&pid={pid}')
    try:
        rj = r.json()
        selected = random.choice(rj)
        return selected['file_url']
    except:
        return f'錯誤！{r.text}'


def r34tags(query=None):
    r = requests.get('https://api.rule34.xxx/index.php?page=dapi&s=tag&q=index&limit=999999')
    tags = []
    try:
        r1 = r.text.split('name="')
        r1.remove(r1[0])
        r2 = []
        for i in r1:
            r2.append(i.split('" ambiguous')[0])
        result = ''
        if query:
            for index, value in enumerate(r2):
                if index>10:
                    break
                if query in value or value.startswith(query) or value.endswith(query):
                    result = result + ' ' + value
        else:
            result = " ".join([random.choice(r2) for i in range(10)])
        if result == '':
            return '無搜尋結果'
        else:
            return result.strip()
    except:
        return '錯誤！'
    

def toZhuyin(string):
    out = ""
    for s in string:
        out += qwerty_to_bopomofo.get(s, s)
    return out


if __name__ == '__main__':
    print('Messenger Bot By AvianJay v' + str(bot_version))
    latestmsg = ["FIRST_TEMP_MESSAGE"]
    driver.delete_all_cookies()
    login()
    print("Waiting website loaded...")
    while True:
        try:
            try:
                driver.find_element(By.CSS_SELECTOR, "[aria-label=關閉]").click()
                time.sleep(1)
            except Exception as e:
                # print(str(e))
                pass
            try:
                driver.find_element(By.CSS_SELECTOR, "[aria-label=不還原訊息]").click()
            except:
                pass
            gototid(config['thread_id'])
            break
        except Exception as e:
            # print(str(e))
            time.sleep(1)
            pass
    time.sleep(5)
    if config['check_pagamo']:
        task = threading.Thread(target=pagamochk)
        task.daemon = True
        task.start()
    if config['message_log_server']:
        servert = threading.Thread(target=server.run, args=(config['server_port'],))
        servert.daemon = True
        servert.start()
    if config['sync_cookies']:
        sync_cookies = threading.Thread(target=sync_cookies)
        sync_cookies.daemon = True
        sync_cookies.start()
    try:
        sendmsg(["原神，啟動！"])
        # pass
    except:
        print("Failed to send started message.")
    while True:
        time.sleep(.1)
        try:
            latestmsg = checksend(latestmsg)
        except KeyboardInterrupt:
            print("Detected KeyboardInterrupt. Exiting...")
            sys.exit(0)
        except Exception as e:
            print("Error:", str(e))
            try:
                sendmsg(["錯誤", str(e)])
            except:
                pass
