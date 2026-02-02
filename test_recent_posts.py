"""
Test: Analyze the last 2 posts from 100xclub channel
"""

import asyncio
import re
import base64
import aiohttp
from telethon import TelegramClient
from signal_detector_v2 import parse_trade_signal_v2

API_ID = 33336670
API_HASH = 'a0294468ed3f843181e88417cc6cd271'
GROQ_API_KEY = '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'

async def analyze_image(image_bytes):
    """Analyze image with Groq"""
    try:
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        prompt = """Analyze this trading chart/image. Extract:
1. What cryptocurrency/coin is shown?
2. What timeframe?
3. Is it LONG (bullish) or SHORT (bearish)?
4. Any key levels (entry, stop loss, targets)?
5. Any patterns visible?

Respond in JSON format."""

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
                    return data['choices'][0]['message']['content']
                else:
                    return f"Error: {response.status}"
    except Exception as e:
        return f"Error: {e}"

async def main():
    print("=" * 70)
    print("Testing Last 2 Posts from 100xclub Channel")
    print("=" * 70)

    client = TelegramClient('100xclub_session', API_ID, API_HASH)
    await client.start()
    print("[OK] Connected\n")

    channel = None
    async for dialog in client.iter_dialogs():
        if '100x' in dialog.name.lower():
            channel = dialog.entity
            break

    if not channel:
        print("[ERROR] Channel not found")
        await client.disconnect()
        return

    post_num = 0
    async for message in client.iter_messages(channel, limit=5):
        # Skip messages without content
        if not message.text and not message.photo and not message.video:
            continue

        post_num += 1
        if post_num > 2:
            break

        print(f"\n{'='*70}")
        print(f"POST #{post_num}")
        print(f"{'='*70}")
        print(f"Date: {message.date.strftime('%Y-%m-%d %H:%M')}")
        print(f"Message ID: {message.id}")

        # Text content
        text = message.text or ''
        clean_text = text.encode('ascii', 'ignore').decode('ascii')
        print(f"\nTEXT CONTENT:")
        print(f"{clean_text[:500]}")
        if len(text) > 500:
            print("... (truncated)")

        # Check for media
        print(f"\nMEDIA:")
        has_photo = bool(message.photo)
        has_video = bool(message.video)
        has_document = bool(message.document)

        print(f"  Photo: {'Yes' if has_photo else 'No'}")
        print(f"  Video: {'Yes' if has_video else 'No'}")
        print(f"  Document: {'Yes' if has_document else 'No'}")

        # Analyze photo if present
        if has_photo:
            print(f"\n[Analyzing image...]")
            try:
                photo_bytes = await client.download_media(message.photo, bytes)
                analysis = await analyze_image(photo_bytes)
                print(f"IMAGE ANALYSIS:\n{analysis}")
            except Exception as e:
                print(f"Error analyzing image: {e}")

        # If video, describe it
        if has_video:
            print(f"\nVIDEO INFO:")
            if message.video:
                duration = getattr(message.video, 'duration', 'Unknown')
                size = getattr(message.video, 'size', 0)
                print(f"  Duration: {duration} seconds")
                print(f"  Size: {size / 1024 / 1024:.1f} MB")
            # Check if there's a video thumbnail we can analyze
            if hasattr(message.video, 'thumbs') and message.video.thumbs:
                print(f"\n[Analyzing video thumbnail...]")
                try:
                    # Download thumbnail
                    thumb_bytes = await client.download_media(message.video.thumbs[0], bytes)
                    if thumb_bytes:
                        analysis = await analyze_image(thumb_bytes)
                        print(f"THUMBNAIL ANALYSIS:\n{analysis}")
                except Exception as e:
                    print(f"Could not analyze thumbnail: {e}")

        # Run signal detector
        print(f"\n{'='*70}")
        print(f"SIGNAL DETECTION (v2):")
        print(f"{'='*70}")
        signal = parse_trade_signal_v2(text)
        if signal and signal['detected']:
            print(f"  DETECTED: YES")
            print(f"  Coins: {', '.join(signal['coins'])}")
            print(f"  Direction: {signal['direction']}")
            print(f"  Action: {signal.get('action', 'N/A')}")
            print(f"  Confidence: {signal['confidence']}")
            print(f"  Methods: {signal['methods'][:3]}")
            print(f"\n  --> This WOULD be sent as a Telegram notification!")
        else:
            print(f"  DETECTED: NO")
            print(f"  --> This would NOT trigger a notification")

    await client.disconnect()
    print(f"\n{'='*70}")
    print("Test complete!")

if __name__ == '__main__':
    asyncio.run(main())
