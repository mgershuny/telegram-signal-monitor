"""
Convert existing session file to session string
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'

async def main():
    print("=" * 50)
    print("Converting Session File to String")
    print("=" * 50)

    # Connect using existing session file
    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.connect()

    if not await client.is_user_authorized():
        print("[ERROR] Session not authorized. Run channel_monitor.py first.")
        return

    # Export to StringSession
    string_session = StringSession.save(client.session)

    print()
    print("=" * 50)
    print("YOUR SESSION STRING:")
    print("=" * 50)
    print()
    print(string_session)
    print()
    print("=" * 50)
    print()
    print("Copy the string above and add it to Render as:")
    print("TELEGRAM_SESSION environment variable")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
