"""
Get full message details
"""

import asyncio
from telethon import TelegramClient

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'

async def main():
    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.start()

    channel = None
    async for dialog in client.iter_dialogs():
        if '100x' in dialog.name.lower():
            channel = dialog.entity
            break

    post_num = 0
    async for message in client.iter_messages(channel, limit=5):
        if not message.text and not message.photo and not message.video:
            continue

        post_num += 1
        if post_num > 2:
            break

        print(f"\n{'='*70}")
        print(f"POST #{post_num} - ID: {message.id}")
        print(f"Date: {message.date}")
        print(f"{'='*70}")
        print(f"FULL RAW TEXT:")
        print(repr(message.text))
        print(f"\nFORMATTED:")
        print(message.text)
        print(f"\n--- Entities ---")
        if message.entities:
            for e in message.entities:
                print(f"  {e}")
        else:
            print("  None")

        if message.reply_to:
            print(f"\nReply to: {message.reply_to}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
