"""
Generate a Telegram session string for Render deployment
Run this ONCE locally to get your session string
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'

async def main():
    print("=" * 50)
    print("Telegram Session String Generator")
    print("=" * 50)
    print()

    # Create client with StringSession
    client = TelegramClient(StringSession(), API_ID, API_HASH)

    await client.start()

    # Get the session string
    session_string = client.session.save()

    print()
    print("=" * 50)
    print("YOUR SESSION STRING (copy this entire line):")
    print("=" * 50)
    print()
    print(session_string)
    print()
    print("=" * 50)
    print()
    print("IMPORTANT: Keep this string SECRET!")
    print("Add it as TELEGRAM_SESSION environment variable on Render")
    print()

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
