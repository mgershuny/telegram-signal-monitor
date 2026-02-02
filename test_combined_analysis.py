"""
Test: Combined text + image analysis for signal detection
"""

import asyncio
import re
import base64
import aiohttp
from telethon import TelegramClient

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'
GROQ_API_KEY = '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'

# Check for trading intent without requiring a coin
INTENT_PATTERNS = [
    r'\b(i am|im|i\'m)\s+(longing|shorting|long|short)\b',
    r'\b(longing|shorting)\s+(here|now|this)\b',
    r'\btook\s+(a\s+)?(long|short)\b',
    r'\b(going|went)\s+(long|short)\b',
]

async def analyze_image(image_bytes):
    """Analyze image with Groq"""
    try:
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        prompt = """Look at this image. What cryptocurrency coin is shown? Just respond with the coin ticker symbol (like BTC, ETH, SOL) and nothing else. If you can't determine the coin, respond with "UNKNOWN"."""

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
                    'max_tokens': 50
                }
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data['choices'][0]['message']['content'].strip().upper()
                else:
                    return None
    except Exception as e:
        return None

def detect_trading_intent(text):
    """Detect if text shows trading intent without requiring coin name"""
    text_lower = text.lower()

    for pattern in INTENT_PATTERNS:
        match = re.search(pattern, text_lower)
        if match:
            direction = None
            matched = match.group(0)
            if 'long' in matched:
                direction = 'LONG'
            elif 'short' in matched:
                direction = 'SHORT'
            return {
                'has_intent': True,
                'direction': direction,
                'match': matched
            }
    return {'has_intent': False}

async def main():
    print("=" * 70)
    print("Combined Text + Image Signal Detection Test")
    print("=" * 70)

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
        print(f"POST #{post_num} - {message.date.strftime('%Y-%m-%d %H:%M')}")
        print(f"{'='*70}")

        text = message.text or ''
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(f"Text: {clean_text}")

        # Step 1: Check for trading intent in text
        intent = detect_trading_intent(text)
        print(f"\n1. Trading Intent: {intent}")

        # Step 2: If intent found but no coin, check image
        coin_from_image = None
        if message.photo:
            print(f"\n2. Analyzing image for coin...")
            photo_bytes = await client.download_media(message.photo, bytes)
            coin_from_image = await analyze_image(photo_bytes)
            print(f"   Coin from image: {coin_from_image}")

        # Step 3: Combined signal
        print(f"\n3. COMBINED SIGNAL:")
        if intent['has_intent'] and coin_from_image and coin_from_image != 'UNKNOWN':
            print(f"   *** SIGNAL DETECTED ***")
            print(f"   Coin: {coin_from_image}")
            print(f"   Direction: {intent['direction']}")
            print(f"   Source: Text intent + Image coin")
            print(f"\n   --> Cloud monitor WOULD send notification:")
            print(f"       '{intent['direction']} {coin_from_image}' detected from 100xclub")
        elif intent['has_intent']:
            print(f"   Intent found but coin unclear")
            print(f"   --> Would need manual review")
        else:
            print(f"   No clear trading signal")

    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
