import asyncio
import shutil
import json
import runpy
import sys
import os
import pyfiglet
import websockets
import aiohttp
import configparser
import re
from pathlib import Path

config = configparser.ConfigParser()
config.read('config.ini')

DEBUG_URL = config.get('General', 'DEBUG_URL', fallback=None)
TWITTER_ID = config.get('General', 'TWITTER_ID', fallback=None)
DOWNLOAD_DIR = config.get('General', 'DOWNLOAD_DIR', fallback=None)
TG_USER_ID = config.get('Telegram', 'USER_ID', fallback=None)
TG_API_KEY = config.get('Telegram', 'API_KEY', fallback=None)
GUIDE_MODE = False
TWITTER_ID_AUTO_DETECT = False
TWITTER_USERNAME = None
follower_count = None
friends_count = None
FOLLOWERS_STRING = None
FOLLOWING_STRING = None

async def create_new_tab():
    while True:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.put(f"http://{DEBUG_URL}/json/new") as response:
                    data = await response.json()
                    return data["webSocketDebuggerUrl"]
        except Exception as e:
            await asyncio.sleep(1)

async def try_connect(ws_url):
    while True:
        try:
            async with websockets.connect(ws_url) as websocket:
                print("Success")
                return 1
        except Exception as e:
            await asyncio.sleep(1)

async def fetch_follow_count(ws_url):
    global TWITTER_ID
    global TWITTER_USERNAME
    global follower_count
    global friends_count
    global TWITTER_ID_AUTO_DETECT

    if TWITTER_ID_AUTO_DETECT == True:
        await send_js_code(ws_url, "window.location.replace('https://x.com/home')")
        await asyncio.sleep(1)
        cookie = (await send_js_code(ws_url, "(() => document.cookie)();"))
        match = re.search(r'twid=u%3D(\d+)', cookie.get('result', {}).get('result', {}).get('value'))
        if match:
            TWITTER_ID = match.group(1)
            config.set('General', 'TWITTER_ID', TWITTER_ID)
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
            print(f"Detected Twitter ID: {TWITTER_ID}")
            await send_js_code(ws_url, f"window.location.replace('https://x.com/intent/user?user_id={TWITTER_ID}')")
        else:
            print("\nError: Not logged in")
            exit(1)
    else:
        await send_js_code(ws_url, f"window.location.replace('https://x.com/intent/user?user_id={TWITTER_ID}')")
        await asyncio.sleep(2)
    cookie = await send_js_code(ws_url, "(() => document.cookie)();")
    if f"twid=u%3D{TWITTER_ID}" not in cookie.get('result', {}).get('result', {}).get('value'):
        print("\nError: Not logged in or not the correct account")
        exit(1)
    while True:
        current_url = (await send_js_code(ws_url, "(() => window.location.href)();"))['result']['result']['value']
        if "https://x.com/intent/user?screen_name=" in current_url:
            TWITTER_USERNAME = current_url.split('=')[1]
            while True:
                ProfileFollows_raw = await send_js_code(ws_url, 'window.scriptElement||(scriptElement=document.querySelector("script[data-testid=\\"UserProfileSchema-test\\"]"))&&(JSON.parse(scriptElement.innerText).mainEntity.interactionStatistic.find(stat=>stat.name==="Follows")?.userInteractionCount)')
                if "result" in ProfileFollows_raw and "result" in ProfileFollows_raw["result"] and "value" in ProfileFollows_raw["result"]["result"]:
                    break
                await asyncio.sleep(1)
            await asyncio.sleep(2)
            follower_count = (await send_js_code(ws_url, 'document.querySelector("script[data-testid=\\"UserProfileSchema-test\\"]") ? JSON.parse(document.querySelector("script[data-testid=\\"UserProfileSchema-test\\"]").innerText).mainEntity.interactionStatistic.find(stat=>stat.name==="Follows")?.userInteractionCount ?? null : null'))["result"]["result"]["value"]
            friends_count = (await send_js_code(ws_url, 'document.querySelector("script[data-testid=\\"UserProfileSchema-test\\"]") ? JSON.parse(document.querySelector("script[data-testid=\\"UserProfileSchema-test\\"]").innerText).mainEntity.interactionStatistic.find(stat=>stat.name==="Friends")?.userInteractionCount ?? null : null'))["result"]["result"]["value"]
            print("Success")
            print(f"Username: {TWITTER_USERNAME}")
            print(f"Followers: {follower_count}, Following: {friends_count}")
            return 1
        elif current_url == "https://x.com/404":
            print("\nError: The account does not exist")
            return 1
        await asyncio.sleep(1)

async def fetch_perpare_followers_list(ws_url):
    global FOLLOWERS_STRING
    global FOLLOWING_STRING
    global GUIDE_MODE
    global TWITTER_USERNAME

    if GUIDE_MODE == True:
        print("\nBecause this is your first time using FDAP, we need to retrieve the initial data, so there will be no results yet.")
        print("The next time you run this, the results will be available.")
        await asyncio.sleep(1)
        print("Now, please install the Twitter Web Exporter extension.")
        print("You can find it here: https://github.com/prinsss/twitter-web-exporter")
        print("After installing, please refresh the Twitter page that was opened by FDAP.")
        await asyncio.sleep(1)
        print("Waiting for you to install the extension...", end="", flush=True)
        while True:
            try:
                response = await send_js_code(ws_url, "document.getElementById('twe-root') !== null")
                if response.get('result', {}).get('result', {}).get('value') == True:
                    print("Success")
                    break
                await asyncio.sleep(1)
            except Exception as e:
                print("Error: WebSocket connection failed")
                exit(1)
    await send_js_code(ws_url, "indexedDB.deleteDatabase('twitter-web-exporter');")
    await send_js_code(ws_url, f"window.location.replace('https://x.com/{TWITTER_USERNAME}/followers');")
    await asyncio.sleep(3)
    while True:
        try:
            async with websockets.connect(ws_url) as websocket:
                response = await send_js_code(ws_url, "(() => document.querySelector('p.text-base.m-0.font-medium.leading-none')?.innerText)();")
                if 'result' in response and 'result' in response['result'] and 'value' in response['result']['result']:
                    lang_response = response['result']['result']['value']
                    break
        except Exception as e:
                await asyncio.sleep(1)
            
    if lang_response == "Followers":
        with open("temp/lang.txt", "w") as file:
            file.write("en")
            FOLLOWERS_STRING = "Followers"
            FOLLOWING_STRING = "Following"
    elif lang_response == "关注者":
        with open("temp/lang.txt", "w") as file:
            file.write("zh")
            FOLLOWERS_STRING = "关注者"
            FOLLOWING_STRING = "正在关注"
    if GUIDE_MODE == False:
        print("Success")

async def send_js_code(uri, script):
    async with websockets.connect(uri) as websocket:
        js_code = {
            "id": 1,
            "method": "Runtime.evaluate",
            "params": {
                "expression": script,
                "returnByValue": True
            }
        }
        await websocket.send(json.dumps(js_code))
        response = await websocket.recv()
        return json.loads(response)

async def guide():
    global TWITTER_ID
    global DEBUG_URL
    global DOWNLOAD_DIR
    global TG_API_KEY
    global TG_USER_ID
    global GUIDE_MODE
    global TWITTER_ID_AUTO_DETECT

    print("Welcome to FDAP!")
    print("Looks like this is your first time using FDAP, switch to guide mode.")
    GUIDE_MODE = True
    if not os.path.exists('config.ini'):
        print("Error: The config.ini file does not exist, please copy the config_default.ini to config.ini or download it from the github repository.")
        exit(1)
    while not TWITTER_ID:
        print("Please enter your Twitter ID (Not username, use https://tweethunter.io/twitter-id-converter. Or type 'auto' to auto-detect later):")
        TWITTER_ID = input()
        if TWITTER_ID == 'auto':
            print("Your Twitter ID will be auto-detected later.")
            TWITTER_ID_AUTO_DETECT = True
        else:
            config.set('General', 'TWITTER_ID', TWITTER_ID)
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
    while not DEBUG_URL:
        print("Please enter the URL of your Chrome DevTools(Host:Port, such as 127.0.0.1:9222, type 'help' to get help):")
        DEBUG_URL = input()
        if DEBUG_URL == 'help':
            print("Please open Chrome with the following command:")
            print("chrome.exe --remote-debugging-port=9222 (If you are not using Windows, please use the correct command for your OS)")
            print("Open the URL: http://127.0.0.1:9222/json, if you see a list of tabs, it's working.")
            print("So now, your debugging port is 9222, so enter '127.0.0.1:9222' as the URL later.")
            await asyncio.sleep(2)
            print("Please enter the URL of your Chrome DevTools(Host:Port, such as 127.0.0.1:9222):")
            DEBUG_URL = input()
            config.set('General', 'DEBUG_URL', DEBUG_URL)
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
        else:  
            config.set('General', 'DEBUG_URL', DEBUG_URL)
            with open('config.ini', 'w') as configfile:
                config.write(configfile)
    while not DOWNLOAD_DIR or not os.path.exists(DOWNLOAD_DIR):
        print("Please enter a valid path to your Chrome's download directory:")
        DOWNLOAD_DIR = input()
        config.set('General', 'DOWNLOAD_DIR', DOWNLOAD_DIR)
        with open('config.ini', 'w') as configfile:
            config.write(configfile)
    if not TG_API_KEY or not TG_USER_ID:
        print("Please enter your Telegram API key and user ID, leave blank if you don't want to use Telegram notifications:")
        print("API Key (Use https://t.me/BotFather):")
        TG_API_KEY = input()
        print("User ID (Use https://t.me/userinfobot):")
        TG_USER_ID = input()
        config.set('Telegram', 'API_KEY', TG_API_KEY)
        config.set('Telegram', 'USER_ID', TG_USER_ID)
    print("Do you use a remote Git repository? (y/n):")
    remote = input()
    if remote.lower() == 'y':
        config.set('Git', 'REMOTE', "True")
    else:
        config.set('Git', 'REMOTE', "False")
    print("Do you have an existing database? (y/n):")
    exist = input()
    if exist.lower() == 'y':
        config.set('General', 'DATABASE_EXIST', "True")
    else:
        config.set('General', 'DATABASE_EXIST', "True")
    print("All done! You can read the README.md for more information.")

async def main():
    global DEBUG_URL
    global TWITTER_ID
    global DOWNLOAD_DIR
    global TG_USER_ID
    global TG_API_KEY

    DEBUG_URL = config.get('General', 'DEBUG_URL', fallback=None)
    TWITTER_ID = config.get('General', 'TWITTER_ID', fallback=None)
    DOWNLOAD_DIR = config.get('General', 'DOWNLOAD_DIR', fallback=None)
    TG_USER_ID = config.get('Telegram', 'USER_ID', fallback=None)
    TG_API_KEY = config.get('Telegram', 'API_KEY', fallback=None)

    welcome = pyfiglet.figlet_format("FDAP")
    print(welcome)
    if not os.path.exists('config.ini') or not DEBUG_URL or not TWITTER_ID or not DOWNLOAD_DIR or config.getboolean('General', 'NOT_FIRST_RUN', fallback=False) == False:
        await guide()
    await asyncio.sleep(0.5)
    if os.path.isdir("./temp"):
        for filename in os.listdir("./temp"):
            file_path = os.path.join("./temp", filename)
            try:
                if os.path.isfile(file_path) or os.path.islink(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print("Unknown error")
    os.makedirs('./temp', exist_ok=True)
    print(f"Connecting to {DEBUG_URL}...", end="", flush=True)
    ws_url = await create_new_tab()
    await try_connect(ws_url)
    print("Fetching your account info...", end="", flush=True)
    await fetch_follow_count(ws_url)
    print("Perparing to fetch your followers list...", end="", flush=True)
    await fetch_perpare_followers_list(ws_url)
    os.makedirs('./temp', exist_ok=True)
    with open('./temp/target_number-1.txt', 'w') as file:
        file.write(str(follower_count))
    with open('./temp/target_number-2.txt', 'w') as file:
        file.write(str(friends_count))
    with open('./temp/debug_url.txt', 'w') as file:
        file.write(str(ws_url))
    with open('./temp/id.txt', 'w') as file:
        file.write(str(TWITTER_USERNAME))
    with open('./temp/uniqueid.txt', 'w') as file:
        file.write(str(TWITTER_ID))
    print("Fetching your followers list...")
    await asyncio.to_thread(runpy.run_path, "fetch.py", run_name="__main__")
    sys.argv = ['fetch.py', '--following']
    print("Fetching your following list...")
    await asyncio.to_thread(runpy.run_path, "fetch.py", run_name="__main__")
    print("Exporting your lists...", end="", flush=True)
    for file in os.listdir(DOWNLOAD_DIR):
        if file.startswith("twitter") and file.endswith(".json"):
            os.remove(os.path.join(DOWNLOAD_DIR, file))
    await asyncio.to_thread(runpy.run_path, "export.py", run_name="__main__")
    while True:
        if any(file.startswith(f"twitter-{FOLLOWERS_STRING}") for file in os.listdir(DOWNLOAD_DIR)) and any(file.startswith(f"twitter-{FOLLOWING_STRING}") for file in os.listdir(DOWNLOAD_DIR)):
            break
        await asyncio.sleep(1)
    for file in os.listdir(DOWNLOAD_DIR):
        if file.startswith(f"twitter-{FOLLOWERS_STRING}"):
            src_path = os.path.join(DOWNLOAD_DIR, file)
            dest_path = os.path.join('./temp', "twitter-Followers-raw.json")
            # 修改以适应跨盘迁移，例：浏览器保存在c盘，代码在d盘
            shutil.move(src_path, dest_path)
        if file.startswith(f"twitter-{FOLLOWING_STRING}"):
            src_path = os.path.join(DOWNLOAD_DIR, file)
            dest_path = os.path.join('./temp', "twitter-Following-raw.json")
            shutil.move(src_path, dest_path)
    print("Success")
    await asyncio.to_thread(runpy.run_path, "sort.py", run_name="__main__")
    os.removedirs('./temp', ignore_errors=True)
    config.set('General', 'NOT_FIRST_RUN', 'true')


if __name__ == "__main__":
    asyncio.run(main())
