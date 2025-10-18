import websockets
import json
import time
import argparse
import asyncio
import os

parser = argparse.ArgumentParser()
parser.add_argument('--following', action='store_true')
args = parser.parse_args()

last_fetch = None
value = 0
repeat = 0
rate_retry = 0
try:
    terminal_width = os.get_terminal_size().columns
except OSError:
    terminal_width = 80  # 默认终端宽度

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

async def monitor_page(uri, target_number):
    first_time = True
    while True:
        try:
            found = await check_page_content(uri, target_number)
            if found:
                if args.following:
                    with open('./temp/fetched-following.txt', 'w') as file:
                        file.write(str('1'))
                    return
                else:
                    with open('./temp/fetched-followers.txt', 'w') as file:
                        file.write(str('1'))
                    return
            await scroll_page(uri, first_time)
            first_time = False
        except websockets.exceptions.ConnectionClosedError:
            await asyncio.sleep(1)

async def check_page_content(uri, target_number):
    global last_fetch
    global value
    if value != 0:
        last_fetch = value

    try:
        if args.following:
            js_code = r"parseInt(document.querySelectorAll('.text-sm.text-base-content.leading-5.text-opacity-70.m-0')[1].innerText.match(/\d+/)[0]);"
        else:
            js_code = r"parseInt(document.querySelectorAll('.text-sm.text-base-content.leading-5.text-opacity-70.m-0')[0].innerText.match(/\d+/)[0]);"
        response = await send_js_code(uri, js_code)

        value = response.get("result", {}).get("result", {}).get("value", 0)
        value = int(value) if value else 0

        if args.following:
            reduce_response = await send_js_code(uri, "if (document.querySelector('pre.leading-none.text-xs.max-h-48.bg-base-200')) { parseInt(document.querySelector('pre.leading-none.text-xs.max-h-48.bg-base-200').textContent.split('\\n').reduce((sum, line) => sum + (line.match(/Following: (\\\\d+) items received/) ? (50 - parseInt(line.match(/Following: (\\\\d+) items received/)[1], 10)) : 0), 0)); }")
        else:
            reduce_response = await send_js_code(uri, "if (document.querySelector('pre.leading-none.text-xs.max-h-48.bg-base-200')) { parseInt(document.querySelector('pre.leading-none.text-xs.max-h-48.bg-base-200').textContent.split('\\n').reduce((sum, line) => sum + (line.match(/Followers: (\\\\d+) items received/) ? (50 - parseInt(line.match(/Followers: (\\\\d+) items received/)[1], 10)) : 0), 0)); }")

        global real_target_number
        target_number = int(target_number) if target_number else 0
        reduce_count = reduce_response.get("result", {}).get("result", {}).get("value", 0)
        reduce_count = int(reduce_count) if reduce_count else 0
        real_target_number = target_number - reduce_count
        global repeat

        if last_fetch == value:
            repeat += 1
        else:
            repeat = 0
        if real_target_number == value:
            print(f"\r{' ' * terminal_width}", end='')
            print(f"\rProgress: {value}/{real_target_number}", end='')
            print("\nSuccess")
            if not args.following:
                await send_js_code(uri, f"window.location.replace('https://x.com/{id_value}/following')")
            return True
        is_nofollow = await send_js_code(uri, "(() => document.querySelector('.css-175oi2r.r-1kihuf0[data-testid=\"emptyState\"]') != null)();")
        check_retry_button_js_first = """
                    (() => {
                            return document.querySelector('button[class*="css-"][class*="r-sdzlij"][style*="background-color: rgb(29, 155, 240);"]') !== null;
                        })();
                """
        button_exists_response_first = await send_js_code(uri, check_retry_button_js_first)
        if is_nofollow.get('result', {}).get('result', {}).get('value') and not button_exists_response_first.get('result', {}).get('result', {}).get('value') and value == 0:
            if args.following:
                print("\nSuccess (You haven't followed anyone)")
            else:
                print("\nSuccess (You don't have any followers)")
                if not args.following:
                    await send_js_code(uri, f"window.location.replace('https://x.com/{id_value}/following')")
                    await send_js_code(uri, f"window.location.reload()")
                    time.sleep(2)
            return True
        elif repeat >= 5:
            check_retry_button = """
            (() => {
                    return document.querySelector('button[class*="css-"][class*="r-sdzlij"][style*="background-color: rgb(29, 155, 240);"]') == null;
                })();
            """
            check_loading_circle = """
            (() => {
                    return document.querySelector('div[role="progressbar"][aria-valuemax="1"][aria-valuemin="0"].css-175oi2r.r-1awozwy.r-1777fci') == null;
                })();
            """
            retry_button_response = await send_js_code(uri, check_retry_button)
            await asyncio.sleep(0.3)
            loading_response = await send_js_code(uri, check_loading_circle)
            if retry_button_response.get('result', {}).get('result', {}).get('value') and loading_response.get('result', {}).get('result', {}).get('value') and value + 50 >= real_target_number:
                print("\nSuccess(inferred)")
                if not args.following:
                    await send_js_code(uri, f"window.location.replace('https://x.com/{id_value}/following')")
                return True
            else:
                print(f"\r{' ' * terminal_width}", end='')
                print(f"\rProgress: {value}/{real_target_number} (Repeat: {repeat})", end='')
                return False
        else:
            if repeat == 0:
                print(f"\r{' ' * terminal_width}", end='')
                print(f"\rProgress: {value}/{real_target_number}", end='')
            else:
                print(f"\r{' ' * terminal_width}", end='')
                print(f"\rProgress: {value}/{real_target_number} (Repeat: {repeat})", end='')
            return False
        last_fetch = value
    except Exception as e:
        print(f"Error in check_page_content: {e}")
        return False

async def scroll_page(uri, first_time):
    try:
        async with websockets.connect(uri) as websocket:
            for _ in range(5):
                await send_js_code(uri, "window.scrollBy(0, window.innerHeight * 6);")
                check_retry_button_js = """
                (() => {
                        return document.querySelector('button[class*="css-"][class*="r-sdzlij"][style*="background-color: rgb(29, 155, 240);"]') !== null;
                    })();
                """
                button_exists_response = await send_js_code(uri, check_retry_button_js)
                button_exists = button_exists_response.get('result', {}).get('result', {}).get('value')
                global rate_retry
                if button_exists:
                    rate_retry += 1
                    print(f"\r{' ' * terminal_width}", end='')
                    print(f"\rLooks like you've hit Twitter's rate limit. Retrying...", end='')
                    await send_js_code(uri, "document.querySelector('button[class*=\"css-\"][class*=\"r-sdzlij\"][style*=\"background-color: rgb(29, 155, 240);\"]')?.click();")
                    check_loading_circle = """
                    (() => {
                    return document.querySelector('div[role="progressbar"][aria-valuemax="1"][aria-valuemin="0"].css-175oi2r.r-1awozwy.r-1777fci') == null;
                    })();
                    """
                    await asyncio.sleep(2)
                    loading_response = await send_js_code(uri, check_loading_circle)
                    button_exists_response = await send_js_code(uri, check_retry_button_js)
                    if loading_response.get("result", {}).get("result", {}).get("value", "") and button_exists_response.get("result", {}).get("result", {}).get("value", ""):
                        for i in range(25, -1, -1):
                            print(f"\r{' ' * terminal_width}", end='')
                            print(f"\r{i}s Looks like you've hit Twitter's rate limit. Waiting... Retry: {rate_retry} Progress: {value}/{real_target_number}", end='')
                            time.sleep(1)
                else:
                    rate_retry = 0
                await asyncio.sleep(0.2)
            js_code = """
                Array.from(document.querySelectorAll('.text-sm.text-base-content.leading-5.text-opacity-70.m-0'))
                .map(el => el.innerText).join(' ');
            """
            response = await send_js_code(uri, js_code)
            page_content = response.get("result", {}).get("result", {}).get("value", "")
    except Exception as e:
        print(f"Error in scroll_page: {e}")

async def main():
    global id_value
    with open('./temp/debug_url.txt', 'r') as file:
        websocket_url = file.read().strip()
    with open('./temp/id.txt', 'r') as file:
        id_value = file.read().strip()

    if args.following:
        with open('./temp/target_number-2.txt', 'r') as file:
            target_number = file.read().strip()
    else:
        with open('./temp/target_number-1.txt', 'r') as file:
            target_number = file.read().strip()
    await monitor_page(websocket_url, target_number)

if __name__ == "__main__":
    asyncio.run(main())
