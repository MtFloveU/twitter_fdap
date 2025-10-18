import asyncio
import configparser
from telegram import Bot
from telegram.constants import ParseMode

config = configparser.ConfigParser()
config.read('config.ini')
TWITTER_ID = config.get('General', 'TWITTER_ID')

def get_token_and_user_id():
    token = config.get('Telegram', 'API_KEY')
    user_id = config.get('Telegram', 'USER_ID')
    return token, user_id

async def send_file_content(bot, user_id):
    try:
        with open(f'./data/{TWITTER_ID}/diff.md', 'r', encoding='utf-8') as file:
            content = file.read()

        await bot.send_message(
            chat_id=user_id,
            text=content,
            parse_mode=ParseMode.MARKDOWN
        )
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

async def main():
    token, user_id = get_token_and_user_id()
    bot = Bot(token=token)
    await send_file_content(bot, user_id)

if __name__ == '__main__':
    asyncio.run(main())
