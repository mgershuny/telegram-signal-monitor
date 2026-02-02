"""
Test chart analysis on recent messages with images
"""

import asyncio
import re
import os
import base64
import aiohttp
from datetime import datetime, timedelta
from telethon import TelegramClient

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'
GROQ_API_KEY = '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'

async def analyze_chart_image(image_bytes):
    """Analyze trading chart using Groq vision"""
    try:
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')

        prompt = """Analyze this trading chart image. Extract:
1. What cryptocurrency/coin is shown? (e.g., BTC, ETH, SOL)
2. What timeframe? (1m, 5m, 15m, 1h, 4h, 1d)
3. Is the chart showing a LONG (bullish) or SHORT (bearish) setup?
4. Any key levels visible (support, resistance, entry, stop loss, targets)?
5. Any patterns visible (breakout, breakdown, consolidation, trend)?

Respond in this exact JSON format:
{
  "coins": ["BTC"],
  "timeframe": "4h",
  "direction": "LONG",
  "key_levels": {"entry": "95000", "stop_loss": "93500", "target": "100000"},
  "pattern": "breakout above resistance",
  "confidence": 85
}

If you cannot determine something, use null for that field."""

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'meta-llama/llama-4-scout-17b-16e-instruct',
                    'messages': [
                        {
                            'role': 'user',
                            'content': [
                                {'type': 'text', 'text': prompt},
                                {'type': 'image_url', 'image_url': {'url': f'data:image/jpeg;base64,{image_base64}'}}
                            ]
                        }
                    ],
                    'max_tokens': 500
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    content = data['choices'][0]['message']['content']
                    return content
                else:
                    text = await response.text()
                    return f"Error {response.status}: {text}"
    except Exception as e:
        return f"Exception: {e}"

async def main():
    print("=" * 70)
    print("Chart Analysis Test - Recent Images from 100xclub")
    print("=" * 70)

    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.start()
    print("[OK] Connected\n")

    channel = None
    async for dialog in client.iter_dialogs():
        if '100x' in dialog.name.lower():
            channel = dialog.entity
            print(f"[OK] Found: {dialog.name}\n")
            break

    if not channel:
        print("[ERROR] Channel not found")
        await client.disconnect()
        return

    # Find messages with photos
    print("Looking for messages with charts...\n")
    print("-" * 70)

    charts_found = 0
    async for message in client.iter_messages(channel, limit=100):
        if message.photo:
            charts_found += 1
            date_str = message.date.strftime('%Y-%m-%d %H:%M')
            text = (message.text or '')[:100]
            clean_text = text.encode('ascii', 'ignore').decode('ascii')

            print(f"[CHART #{charts_found}] {date_str}")
            print(f"Text: {clean_text}...")
            print(f"Analyzing...")

            try:
                # Download image
                photo_bytes = await client.download_media(message.photo, bytes)
                print(f"Downloaded {len(photo_bytes)} bytes")

                # Analyze
                analysis = await analyze_chart_image(photo_bytes)
                print(f"Analysis:\n{analysis}")
            except Exception as e:
                print(f"Error: {e}")

            print("-" * 70)

            if charts_found >= 3:
                break

    print(f"\nFound and analyzed {charts_found} chart(s)")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
