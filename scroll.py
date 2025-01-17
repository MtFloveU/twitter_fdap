import asyncio
import websockets
import json
import time

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
    first_time = True  # 初始时为第一次调用
    while True:
        try:
            found = await check_page_content(uri, target_number)
            if found:
                with open('./temp/fetched-followers.txt', 'w') as file:
                    file.write(str('1'))
                return
            await scroll_page(uri, first_time)  # Pass first_time to scroll_page
            first_time = False  # 后续调用不再是第一次
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Connection closed, retrying: {e}")
            await asyncio.sleep(1)  # 等待1秒后重试连接

async def check_page_content(uri, target_number):
    try:
        # 执行 JavaScript 获取页面内容
        js_code = "parseInt(document.querySelector('.flex.flex-col.flex-grow .text-sm').innerText.trim(), 10);"
        response = await send_js_code(uri, js_code)

        # 获取并解析数字
        value = response.get("result", {}).get("result", {}).get("value")
        if value is None:
            print("Failed to extract number from the page.")
            return False

        value = int(value)
        print(f"Current fetched count: {value}")

        # 检查目标数字是否在范围内
        reduce_response = await send_js_code(uri, "if (document.querySelector('pre.leading-none.text-xs.max-h-48.bg-base-200')) { parseInt(document.querySelector('pre.leading-none.text-xs.max-h-48.bg-base-200').textContent.split('\\n').reduce((sum, line) => sum + (line.match(/Followers: (\\\\d+) items received/) ? (50 - parseInt(line.match(/Followers: (\\\\d+) items received/)[1], 10)) : 0), 0)); }")
        target_number = int(target_number)
        reduce_count = reduce_response.get("result", {}).get("result", {}).get("value")
        if reduce_count is None:
            print("Failed to extract reduced count.")
            return False

        reduce_count = int(reduce_count)
        real_target_number = target_number - reduce_count
        if real_target_number == value:
            print(f"Target number {real_target_number} found!")
            return True
        else:
            return False
    except Exception as e:
        print(f"Error in check_page_content: {e}")
        return False

async def scroll_page(uri, first_time):
    try:
        async with websockets.connect(uri) as websocket:
            for _ in range(5):  # 滑动5次
                # 滑动页面
                await send_js_code(uri, "window.scrollBy(0, window.innerHeight * 6);")

                # 检测按钮是否存在
                check_button_js = """
                (() => {
                        return document.querySelector('.css-175oi2r.r-sdzlij.r-1phboty.r-rs99b7.r-lrvibr.r-2yi16.r-1qi8awa.r-3pj75a.r-1loqt21.r-o7ynqc.r-6416eg.r-1ny4l3l') !== null;
                    })();

                """
                button_exists = await send_js_code(uri, check_button_js)

                if button_exists.get('result', {}).get('result', {}).get('value') is True:
                    print("Looks like you've hit the Twitter's rate limit. Retrying, this may take a while.")
                    for i in range(60, -1, -1):
                        print(f"\r{i}", end="", flush=True)
                        time.sleep(1)

                    # 点击按钮
                    await send_js_code(uri, "document.querySelector('.css-175oi2r.r-4d76ec').querySelector('button').click();")

                await asyncio.sleep(0.2)  # 每次滑动之间等待0.2秒

            # 获取更新后的页面内容
            js_code = """
                Array.from(document.querySelectorAll('.text-sm.text-base-content.leading-5.text-opacity-70.m-0'))
                .map(el => el.innerText).join(' ');
            """
            response = await send_js_code(uri, js_code)
            page_content = response.get("result", {}).get("result", {}).get("value", "")

    except Exception as e:
        print(f"Error in scroll_page: {e}")

async def main():
    # 从文件中读取 WebSocket URL
    with open('./temp/debug_url.txt', 'r') as file:
        websocket_url = file.read().strip()

    # 从文件中读取目标数字
    with open('./temp/target_number-1.txt', 'r') as file:
        target_number = file.read().strip()

    await monitor_page(websocket_url, target_number)

if __name__ == "__main__":
    asyncio.run(main())
