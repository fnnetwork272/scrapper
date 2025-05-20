from telethon import TelegramClient

api_id = 25031007  # Replace with your API ID
api_hash = "68029e5e2d9c4dd11f600e1692c3acaa"  # Replace with your API hash
client = TelegramClient("test_session", api_id, api_hash)

async def main():
    try:
        await client.start()
        me = await client.get_me()
        print(f"Logged in as {me.first_name}")
    except Exception as e:
        print(f"Error: {e}")

import asyncio
asyncio.run(main())
