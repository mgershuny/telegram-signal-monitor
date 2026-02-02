"""
Backtest with Enhanced Signal Detector v2
"""

import asyncio
from datetime import datetime, timedelta
from telethon import TelegramClient
from signal_detector_v2 import parse_trade_signal_v2

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'

async def main():
    print("=" * 70)
    print("100xclub Channel Backtest - Enhanced Detector v2")
    print("=" * 70)

    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.start()
    print("[OK] Connected to Telegram\n")

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

    cutoff_date = datetime.now() - timedelta(days=60)
    print(f"\n[INFO] Scanning messages since {cutoff_date.strftime('%Y-%m-%d')}...")
    print("-" * 70)

    signals_found = []
    total_messages = 0

    async for message in client.iter_messages(channel, limit=1000):
        if message.date.replace(tzinfo=None) < cutoff_date:
            break

        total_messages += 1
        text = message.text or ''

        signal = parse_trade_signal_v2(text)
        if signal and signal['detected']:
            signal['date'] = message.date.strftime('%Y-%m-%d %H:%M')
            signal['message_id'] = message.id
            signals_found.append(signal)

    print(f"\n{'='*70}")
    print(f"BACKTEST RESULTS (v2 Enhanced Detector)")
    print(f"{'='*70}")
    print(f"Total messages scanned: {total_messages}")
    print(f"Trade signals detected: {len(signals_found)}")
    print(f"{'='*70}\n")

    if signals_found:
        print("DETECTED SIGNALS:\n")
        for i, signal in enumerate(signals_found, 1):
            coins_str = ', '.join(signal['coins'])
            direction_arrow = '^' if signal['direction'] == 'LONG' else 'v' if signal['direction'] == 'SHORT' else '?'
            action = signal.get('action', 'TRADE')

            # Clean text for display
            clean_text = signal['raw_text'].encode('ascii', 'ignore').decode('ascii')

            print(f"#{i} | {signal['date']} | Confidence: {signal['confidence']}")
            print(f"   [{direction_arrow}] {signal['direction']} {coins_str} ({action})")
            if signal.get('entry'):
                print(f"   Entry: ${signal['entry']}")
            if signal.get('stop_loss'):
                print(f"   Stop Loss: ${signal['stop_loss']}")
            if signal.get('targets'):
                print(f"   Targets: {', '.join(signal['targets'])}")
            if signal.get('leverage'):
                print(f"   Leverage: {signal['leverage']}x")
            print(f"   Methods: {', '.join(signal['methods'][:3])}")
            print(f"   Preview: {clean_text[:80]}...")
            print()

    # Summary by coin
    if signals_found:
        print(f"\n{'='*70}")
        print("SIGNALS BY COIN:")
        print(f"{'='*70}")
        coin_counts = {}
        for signal in signals_found:
            for coin in signal['coins']:
                if coin not in ['USDT', 'USDC', 'DAI', 'BUSD']:
                    coin_counts[coin] = coin_counts.get(coin, 0) + 1

        for coin, count in sorted(coin_counts.items(), key=lambda x: -x[1])[:15]:
            print(f"  {coin}: {count} signal(s)")

        print(f"\n{'='*70}")
        print("SIGNALS BY DIRECTION:")
        print(f"{'='*70}")
        direction_counts = {}
        for signal in signals_found:
            direction_counts[signal['direction']] = direction_counts.get(signal['direction'], 0) + 1

        for direction, count in sorted(direction_counts.items(), key=lambda x: -x[1]):
            arrow = '^' if direction == 'LONG' else 'v' if direction == 'SHORT' else '?'
            print(f"  [{arrow}] {direction}: {count} signal(s)")

        print(f"\n{'='*70}")
        print("SIGNALS BY ACTION TYPE:")
        print(f"{'='*70}")
        action_counts = {}
        for signal in signals_found:
            action = signal.get('action', 'Unknown')
            action_counts[action] = action_counts.get(action, 0) + 1

        for action, count in sorted(action_counts.items(), key=lambda x: -x[1]):
            print(f"  {action}: {count} signal(s)")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
