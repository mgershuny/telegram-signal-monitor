"""
Backtest: Check historical messages from 100xclub channel
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
        'raw_text': text[:300]
    }

async def main():
    print("=" * 60)
    print("100xclub Channel Backtest - Last 2 Months")
    print("=" * 60)

    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.start()
    print("[OK] Connected to Telegram\n")

    # Find the channel
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

    # Get messages from the last 2 months
    cutoff_date = datetime.now() - timedelta(days=60)

    print(f"\n[INFO] Scanning messages since {cutoff_date.strftime('%Y-%m-%d')}...")
    print("-" * 60)

    signals_found = []
    total_messages = 0

    async for message in client.iter_messages(channel, limit=1000):
        if message.date.replace(tzinfo=None) < cutoff_date:
            break

        total_messages += 1
        text = message.text or ''

        signal = parse_trade_signal(text)
        if signal:
            signal['date'] = message.date.strftime('%Y-%m-%d %H:%M')
            signal['message_id'] = message.id
            signals_found.append(signal)

    print(f"\n{'='*60}")
    print(f"BACKTEST RESULTS")
    print(f"{'='*60}")
    print(f"Total messages scanned: {total_messages}")
    print(f"Trade signals detected: {len(signals_found)}")
    print(f"{'='*60}\n")

    if signals_found:
        print("DETECTED SIGNALS:\n")
        for i, signal in enumerate(signals_found, 1):
            coins_str = ', '.join(signal['coins'])
            direction_arrow = '^' if signal['direction'] == 'LONG' else 'v' if signal['direction'] == 'SHORT' else '?'

            print(f"#{i} | {signal['date']}")
            print(f"   [{direction_arrow}] {signal['direction']} {coins_str}")
            if signal['entry']:
                print(f"   Entry: ${signal['entry']}")
            if signal['targets']:
                print(f"   Targets: {', '.join(signal['targets'])}")
            if signal['stop_loss']:
                print(f"   Stop Loss: ${signal['stop_loss']}")
            if signal['leverage']:
                print(f"   Leverage: {signal['leverage']}x")
            print(f"   Preview: {signal['raw_text'][:100]}...")
            print()

    # Summary by coin
    if signals_found:
        print(f"\n{'='*60}")
        print("SIGNALS BY COIN:")
        print(f"{'='*60}")
        coin_counts = {}
        for signal in signals_found:
            for coin in signal['coins']:
                coin_counts[coin] = coin_counts.get(coin, 0) + 1

        for coin, count in sorted(coin_counts.items(), key=lambda x: -x[1]):
            print(f"  {coin}: {count} signal(s)")

        print(f"\n{'='*60}")
        print("SIGNALS BY DIRECTION:")
        print(f"{'='*60}")
        direction_counts = {}
        for signal in signals_found:
            direction_counts[signal['direction']] = direction_counts.get(signal['direction'], 0) + 1

        for direction, count in sorted(direction_counts.items(), key=lambda x: -x[1]):
            arrow = '^' if direction == 'LONG' else 'v' if direction == 'SHORT' else '?'
            print(f"  [{arrow}] {direction}: {count} signal(s)")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
