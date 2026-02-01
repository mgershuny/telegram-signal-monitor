"""
100xclub Telegram Channel Monitor - Polling Version for GitHub Actions
Checks for new messages since last run and exits
"""

import asyncio
import re
import os
import json
import aiohttp
from datetime import datetime, timedelta
from telethon import TelegramClient
from telethon.sessions import StringSession

# ============================================
# CONFIGURATION FROM ENVIRONMENT VARIABLES
# ============================================

API_ID = int(os.environ.get('TELEGRAM_API_ID', '33336670'))
API_HASH = os.environ.get('TELEGRAM_API_HASH', 'a0294468ed3f843181e88417cc6cd271')
SESSION_STRING = os.environ.get('TELEGRAM_SESSION', '')
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8327044619:AAEqx5cegbQzYD3XOKP8GG4_jrwnEu7rRqg')
CHAT_ID = int(os.environ.get('CHAT_ID', '1203745980'))

# How far back to check (in minutes)
CHECK_MINUTES = int(os.environ.get('CHECK_MINUTES', '10'))

# ============================================
# TRADE SIGNAL DETECTION
# ============================================

TRADE_KEYWORDS = ['long', 'short', 'buy', 'sell', 'entry', 'target', 'tp', 'sl', 'stop loss', 'take profit']
COIN_PATTERN = re.compile(r'\b(BTC|ETH|SOL|XRP|ADA|DOGE|AVAX|DOT|LINK|MATIC|UNI|ATOM|LTC|BCH|NEAR|APT|ARB|OP|SUI|SEI|TIA|JUP|BONK|WIF|PEPE|SHIB|FLOKI|INJ|FET|RENDER|TAO|WLD|STRK|MANTA|DYM|ALT|PIXEL|PORTAL|AEVO)\b', re.IGNORECASE)

def parse_trade_signal(text):
    """Parse a message to extract trade signal information"""
    if not text:
        return None

    text_lower = text.lower()

    # Check for trade keywords
    keyword_count = sum(1 for kw in TRADE_KEYWORDS if kw in text_lower)
    if keyword_count < 2:
        return None

    # Extract coins
    coin_matches = COIN_PATTERN.findall(text)
    coins = list(set(c.upper() for c in coin_matches))

    if not coins:
        return None

    # Detect direction
    direction = None
    if re.search(r'\b(long|buy|bullish|going long)\b', text_lower):
        direction = 'LONG'
    elif re.search(r'\b(short|sell|bearish|going short)\b', text_lower):
        direction = 'SHORT'

    # Extract entry price
    entry_match = re.search(r'(?:entry|enter|buy at|sell at)[:\s]*\$?([\d,]+\.?\d*)', text_lower)
    entry = entry_match.group(1).replace(',', '') if entry_match else None

    # Extract targets
    target_matches = re.findall(r'(?:tp|target|take profit)[:\s]*\$?([\d,]+\.?\d*)', text_lower)
    targets = [t.replace(',', '') for t in target_matches] if target_matches else []

    # Extract stop loss
    sl_match = re.search(r'(?:sl|stop ?loss|stop)[:\s]*\$?([\d,]+\.?\d*)', text_lower)
    stop_loss = sl_match.group(1).replace(',', '') if sl_match else None

    # Extract leverage
    leverage_match = re.search(r'(\d+)x', text_lower)
    leverage = leverage_match.group(1) if leverage_match else None

    return {
        'coins': coins,
        'direction': direction or 'Unknown',
        'entry': entry,
        'targets': targets,
        'stop_loss': stop_loss,
        'leverage': leverage,
        'raw_text': text[:500]
    }

async def send_telegram_notification(signal_data):
    """Send notification directly via bot"""
    coins_str = ', '.join(signal_data['coins'])
    direction_emoji = '📈' if signal_data['direction'] == 'LONG' else '📉'

    message = f"""🚨 *NEW 100XCLUB TRADE SIGNAL* 🚨

📡 Source: Telegram Channel (Auto-Detected)
⏰ Time: {signal_data['timestamp']}

🪙 Coin(s): *{coins_str}*
{direction_emoji} Direction: *{signal_data['direction']}*
💰 Entry: {signal_data.get('entry') or 'Not specified'}
🎯 Targets: {', '.join(signal_data.get('targets', [])) or 'Not specified'}
🛑 Stop Loss: {signal_data.get('stop_loss') or 'Not specified'}
⚡ Leverage: {signal_data.get('leverage') or 'Not specified'}x

📝 Signal:
```
{signal_data['raw_text'][:300]}
```

⚠️ Reply with:
• `APPROVE {signal_data['coins'][0]} {signal_data['direction']} 50` to trade $50
• `SKIP` to ignore"""

    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': message,
        'parse_mode': 'Markdown'
    }

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status == 200:
                    print(f"[OK] Notification sent for: {coins_str}")
                else:
                    text = await response.text()
                    print(f"[ERROR] Telegram notification failed: {response.status} - {text}")
    except Exception as e:
        print(f"[ERROR] Telegram error: {e}")

async def main():
    print("=" * 50)
    print("100xclub Channel Monitor - Polling Mode")
    print(f"Checking messages from last {CHECK_MINUTES} minutes")
    print("=" * 50)

    if not SESSION_STRING:
        print("[ERROR] No TELEGRAM_SESSION environment variable set!")
        return

    # Create client using StringSession
    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

    await client.start()
    print("[OK] Connected to Telegram")

    # Find the 100xclub channel
    channel = None
    async for dialog in client.iter_dialogs():
        if '100x' in dialog.name.lower():
            channel = dialog.entity
            print(f"[OK] Found channel: {dialog.name}")
            break

    if not channel:
        print("[ERROR] Could not find 100xclub channel!")
        await client.disconnect()
        return

    # Get messages from the last X minutes
    cutoff_time = datetime.utcnow() - timedelta(minutes=CHECK_MINUTES)
    signals_found = 0

    print(f"[INFO] Checking messages since {cutoff_time.isoformat()}...")

    async for message in client.iter_messages(channel, limit=50):
        if message.date.replace(tzinfo=None) < cutoff_time:
            break

        text = message.text or ''
        signal = parse_trade_signal(text)

        if signal:
            signal['timestamp'] = message.date.isoformat()
            signal['message_id'] = message.id
            signals_found += 1

            print(f"[SIGNAL] {signal['coins']} - {signal['direction']}")
            await send_telegram_notification(signal)

    print(f"\n[DONE] Found {signals_found} trade signal(s)")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
