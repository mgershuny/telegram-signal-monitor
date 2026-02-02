"""
Verbose Backtest: Show ALL messages to identify missed signals
"""

import asyncio
import re
from datetime import datetime, timedelta
from telethon import TelegramClient

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'

TRADE_KEYWORDS = ['long', 'short', 'buy', 'sell', 'entry', 'target', 'tp', 'sl', 'stop loss', 'take profit']
COIN_PATTERN = re.compile(r'\b(BTC|ETH|SOL|XRP|ADA|DOGE|AVAX|DOT|LINK|MATIC|UNI|ATOM|LTC|BCH|NEAR|APT|ARB|OP|SUI|SEI|TIA|JUP|BONK|WIF|PEPE|SHIB|FLOKI|INJ|FET|RENDER|TAO|WLD|STRK|MANTA|DYM|ALT|PIXEL|PORTAL|AEVO|HBAR|VET|FIL|SAND|MANA|AXS|GALA|ENJ|IMX|GMT|APE|BLUR|MAGIC|PENDLE|JTO|PYTH|W|ENA|ONDO|ETHFI|EIGEN|MOODENG|PNUT|ACT|VIRTUAL|AI16Z|FARTCOIN|TRUMP|MELANIA)\b', re.IGNORECASE)

def parse_trade_signal(text):
    if not text:
        return None
    text_lower = text.lower()
    keyword_count = sum(1 for kw in TRADE_KEYWORDS if kw in text_lower)
    if keyword_count < 2:
        return None
    coin_matches = COIN_PATTERN.findall(text)
    coins = list(set(c.upper() for c in coin_matches))
    if not coins:
        return None
    direction = None
    if re.search(r'\b(long|buy|bullish|going long)\b', text_lower):
        direction = 'LONG'
    elif re.search(r'\b(short|sell|bearish|going short)\b', text_lower):
        direction = 'SHORT'
    return {'coins': coins, 'direction': direction or 'Unknown'}

async def main():
    print("=" * 80)
    print("VERBOSE BACKTEST - Showing potential missed signals")
    print("=" * 80)

    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.start()

    channel = None
    async for dialog in client.iter_dialogs():
        if '100x' in dialog.name.lower():
            channel = dialog.entity
            break

    cutoff_date = datetime.now() - timedelta(days=60)

    # Potential signal keywords (broader)
    potential_keywords = [
        'long', 'short', 'buy', 'sell', 'entry', 'target', 'tp', 'sl',
        'stop loss', 'take profit', 'position', 'trade', 'setup', 'chart',
        'breakout', 'breakdown', 'support', 'resistance', 'level', 'zone',
        'scalp', 'swing', 'spot', 'futures', 'perp', 'leverage', 'margin',
        'liquidation', 'liq', 'rekt', 'pump', 'dump', 'moon', 'dip',
        'accumulate', 'accumulation', 'distribution', 'bullish', 'bearish',
        'bid', 'ask', 'filled', 'fill', 'order', 'limit', 'market',
        'closed', 'closing', 'opened', 'opening', 'added', 'adding',
        'reduced', 'reducing', 'exited', 'exit', 'entered', 'enter',
        'profit', 'loss', 'pnl', 'roi', 'r:r', 'risk', 'reward'
    ]

    print("\nMessages that mention trading-related terms but weren't detected:\n")
    print("-" * 80)

    missed_count = 0
    detected_count = 0

    async for message in client.iter_messages(channel, limit=500):
        if message.date.replace(tzinfo=None) < cutoff_date:
            break

        text = message.text or ''
        text_lower = text.lower()

        # Check if it has potential trading content
        has_potential = sum(1 for kw in potential_keywords if kw in text_lower) >= 1
        has_coin = bool(COIN_PATTERN.search(text))

        # Current detection
        detected = parse_trade_signal(text)

        if detected:
            detected_count += 1
        elif has_potential and has_coin:
            missed_count += 1
            date_str = message.date.strftime('%Y-%m-%d %H:%M')
            coins = COIN_PATTERN.findall(text)
            coins_str = ', '.join(set(c.upper() for c in coins))

            # Show keywords found
            found_keywords = [kw for kw in potential_keywords if kw in text_lower]

            # Remove emojis for printing
            clean_text = text.encode('ascii', 'ignore').decode('ascii')
            print(f"DATE: {date_str}")
            print(f"COINS: {coins_str}")
            print(f"KEYWORDS: {', '.join(found_keywords[:5])}")
            print(f"TEXT: {clean_text[:200]}...")
            print("-" * 80)

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Currently detected: {detected_count}")
    print(f"Potentially missed: {missed_count}")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
