"""
100xclub Telegram Channel Monitor - Polling Version for GitHub Actions
Enhanced with v2 Signal Detector + Image Analysis
"""

import asyncio
import re
import os
import base64
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
CHECK_MINUTES = int(os.environ.get('CHECK_MINUTES', '10'))

# Optional: OpenAI/Groq API for chart analysis
GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')

# ============================================
# EXPANDED COIN LIST
# ============================================

COINS = [
    # Major
    'BTC', 'ETH', 'SOL', 'XRP', 'BNB', 'ADA', 'DOGE', 'AVAX', 'DOT', 'LINK',
    'MATIC', 'POL', 'UNI', 'ATOM', 'LTC', 'BCH', 'NEAR', 'APT', 'ARB', 'OP',
    # Layer 1/2
    'SUI', 'SEI', 'TIA', 'INJ', 'FTM', 'ALGO', 'HBAR', 'VET', 'FIL', 'ICP',
    'EGLD', 'XLM', 'XMR', 'EOS', 'FLOW', 'MINA', 'KAVA', 'ZIL', 'ONE', 'ROSE',
    # DeFi
    'AAVE', 'MKR', 'CRV', 'SNX', 'COMP', 'SUSHI', 'YFI', 'LIDO', 'LDO', 'RPL',
    'GMX', 'DYDX', 'JUP', 'RAY', 'ORCA', 'PENDLE', 'JTO', 'PYTH', 'W', 'ENA',
    # Gaming/Metaverse
    'SAND', 'MANA', 'AXS', 'GALA', 'ENJ', 'IMX', 'GMT', 'APE', 'BLUR', 'MAGIC',
    'PRIME', 'PIXEL', 'PORTAL', 'AEVO', 'RONIN', 'RON',
    # AI
    'FET', 'RENDER', 'RNDR', 'TAO', 'WLD', 'OCEAN', 'AGIX', 'NMR', 'ARKM',
    # Memes
    'BONK', 'WIF', 'PEPE', 'SHIB', 'FLOKI', 'MEME', 'MOODENG', 'PNUT', 'ACT',
    'VIRTUAL', 'AI16Z', 'FARTCOIN', 'GOAT', 'POPCAT', 'MEW', 'NEIRO', 'TURBO',
    # New/Hot
    'STRK', 'MANTA', 'DYM', 'ALT', 'ONDO', 'ETHFI', 'EIGEN', 'ZRO', 'BLAST',
    'TRUMP', 'MELANIA', 'BOME', 'SLERF', 'BRETT', 'MOTHER', 'DADDY',
    # Others
    'TON', 'KAS', 'STX', 'ORDI', 'RUNE', 'TRX', 'LEO', 'OKB', 'CRO', 'MNT',
    'CAKE', 'OSMO', 'AKT', 'RNDR', 'AR', 'GRT', 'THETA', 'XTZ', 'ALGO', 'IOTA',
    'ZEC', 'DASH', 'ETC', 'NEO', 'WAVES', 'QTUM', 'ICX', 'ZEN', 'SC', 'RVN',
    # Stables (for detection)
    'USDT', 'USDC', 'DAI', 'BUSD'
]

COIN_PATTERN = re.compile(r'\b(' + '|'.join(COINS) + r')\b', re.IGNORECASE)

# ============================================
# ENHANCED SIGNAL DETECTOR V2
# ============================================

class SignalDetector:
    # Direct action patterns
    DIRECT_ACTION_PATTERNS = [
        (r'\b(longed|shorted|bought|sold)\s+([A-Z]{2,6})\b', 'direct_action'),
        (r'\b(long|short)\s+([A-Z]{2,6})\b', 'direct_action'),
        (r'\b([A-Z]{2,6})\s+(long|short)\b', 'direct_action_reverse'),
        (r'\btook\s+(?:a\s+)?(?:this\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'took_position'),
        (r'\btook\s+(?:a\s+)?(?:this\s+)?(long|short)\s+(?:on\s+)?([A-Z]{2,6})\b', 'took_position'),
        (r'\btaking\s+(?:this\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'taking_position'),
        (r'\bentered?\s+(?:a\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'entered_position'),
        (r'\badded\s+(?:to\s+)?(?:my\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'added_position'),
    ]

    SCALP_PATTERNS = [
        (r'\bscalp\s+(long|short)\s+([A-Z]{2,6})\b', 'scalp'),
        (r'\b([A-Z]{2,6})\s+scalp\s+(long|short)\b', 'scalp_reverse'),
        (r'\bscalp(?:ed|ing)?\s+([A-Z]{2,6})\b', 'scalp_coin'),
        (r'\btook\s+(?:a\s+)?(?:this\s+)?([A-Z]{2,6})?\s*scalp\s*(long|short)?\b', 'took_scalp'),
    ]

    UPDATE_PATTERNS = [
        (r'\b(?:updated?|new)\s+([A-Z]{2,6})?\s*(?:sl|stop\s*loss|tp|take\s*profit)\b', 'update'),
        (r'\b([A-Z]{2,6})\s+(?:sl|stop\s*loss|tp|take\s*profit)\s*(?:updated?|changed?|moved?)\b', 'update_reverse'),
        (r'\bsl\s+(?:at|to|@)\s*\$?([\d,.]+)\b', 'sl_level'),
        (r'\btp\s+(?:at|to|@)\s*\$?([\d,.]+)\b', 'tp_level'),
    ]

    CLOSE_PATTERNS = [
        (r'\bclosed?\s+(?:my\s+)?(?:the\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'closed'),
        (r'\bclosing\s+(?:my\s+)?(?:the\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'closing'),
        (r'\bexited?\s+(?:my\s+)?(?:the\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'exited'),
        (r'\breduced?\s+(?:my\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'reduced'),
    ]

    TRADING_KEYWORDS = {
        'high_confidence': ['longed', 'shorted', 'scalp', 'entry', 'sl', 'tp', 'stop loss', 'take profit'],
        'medium_confidence': ['long', 'short', 'buy', 'sell', 'target', 'position'],
        'action_verbs': ['took', 'taking', 'entered', 'entering', 'closed', 'closing', 'added', 'reduced', 'exited'],
    }

    @classmethod
    def detect(cls, text, image_analysis=None):
        if not text or len(text) < 5:
            return None

        text_lower = text.lower()
        result = {
            'detected': False,
            'confidence': 0,
            'methods': [],
            'coins': [],
            'direction': None,
            'action': None,
            'entry': None,
            'stop_loss': None,
            'targets': [],
            'leverage': None,
            'has_chart': False,
            'chart_analysis': None,
            'raw_text': text[:500]
        }

        # Extract coins
        coin_matches = COIN_PATTERN.findall(text)
        result['coins'] = list(set(c.upper() for c in coin_matches))

        tradeable_coins = [c for c in result['coins'] if c not in ['USDT', 'USDC', 'DAI', 'BUSD']]

        # If we have image analysis, use it even without text coins
        if image_analysis:
            result['has_chart'] = True
            result['chart_analysis'] = image_analysis
            if image_analysis.get('coins'):
                for coin in image_analysis['coins']:
                    if coin.upper() not in result['coins']:
                        result['coins'].append(coin.upper())
                        tradeable_coins.append(coin.upper())
            if image_analysis.get('direction'):
                result['direction'] = image_analysis['direction']
            result['confidence'] += 30

        if not tradeable_coins:
            return None

        # Pattern matching
        all_patterns = [
            (cls.DIRECT_ACTION_PATTERNS, 40, 'OPEN'),
            (cls.SCALP_PATTERNS, 35, 'SCALP'),
            (cls.UPDATE_PATTERNS, 25, 'UPDATE'),
            (cls.CLOSE_PATTERNS, 30, 'CLOSE'),
        ]

        for patterns, base_confidence, action_type in all_patterns:
            for pattern, method_name in patterns:
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    result['detected'] = True
                    result['methods'].append(f'{action_type.lower()}:{method_name}')
                    result['confidence'] += base_confidence
                    if not result['action']:
                        result['action'] = action_type

                    groups = match.groups()
                    for g in groups:
                        if g and g.lower() in ['long', 'longed', 'bought', 'buy']:
                            result['direction'] = 'LONG'
                        elif g and g.lower() in ['short', 'shorted', 'sold', 'sell']:
                            result['direction'] = 'SHORT'

        # Keyword confidence
        for kw in cls.TRADING_KEYWORDS['high_confidence']:
            if kw in text_lower:
                result['confidence'] += 10
        for kw in cls.TRADING_KEYWORDS['medium_confidence']:
            if kw in text_lower:
                result['confidence'] += 5
        for kw in cls.TRADING_KEYWORDS['action_verbs']:
            if kw in text_lower:
                result['confidence'] += 8

        # Leverage
        leverage_match = re.search(r'(\d+)x\b', text_lower)
        if leverage_match:
            result['leverage'] = leverage_match.group(1)
            result['confidence'] += 5

        # Direction fallback
        if not result['direction']:
            if re.search(r'\b(long|buy|bullish)\b', text_lower):
                result['direction'] = 'LONG'
            elif re.search(r'\b(short|sell|bearish)\b', text_lower):
                result['direction'] = 'SHORT'
            else:
                result['direction'] = 'Unknown'

        # Minimum confidence threshold (lowered to 15)
        if result['confidence'] >= 15:
            result['detected'] = True
            return result

        return None


# ============================================
# CHART/IMAGE ANALYSIS
# ============================================

async def analyze_chart_image(image_bytes, groq_api_key=None):
    """
    Analyze trading chart image using Groq's vision model
    Returns: dict with detected coins, direction, patterns
    """
    if not groq_api_key:
        return None

    try:
        # Encode image to base64
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
                    'Authorization': f'Bearer {groq_api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.2-90b-vision-preview',
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

                    # Try to parse JSON from response
                    import json
                    try:
                        # Find JSON in response
                        json_match = re.search(r'\{[^{}]*\}', content, re.DOTALL)
                        if json_match:
                            return json.loads(json_match.group())
                    except:
                        pass

                    return {'raw_analysis': content}
                else:
                    print(f"[WARN] Chart analysis failed: {response.status}")
                    return None
    except Exception as e:
        print(f"[ERROR] Chart analysis error: {e}")
        return None


# ============================================
# NOTIFICATION
# ============================================

async def send_telegram_notification(signal_data):
    coins_str = ', '.join(signal_data['coins'])
    direction_emoji = '^' if signal_data['direction'] == 'LONG' else 'v' if signal_data['direction'] == 'SHORT' else '?'
    action = signal_data.get('action', 'TRADE')

    # Build message
    message_parts = [
        f"*NEW 100XCLUB SIGNAL*",
        f"",
        f"Time: {signal_data['timestamp']}",
        f"Confidence: {signal_data['confidence']}%",
        f"",
        f"[{direction_emoji}] *{signal_data['direction']} {coins_str}* ({action})",
    ]

    if signal_data.get('entry'):
        message_parts.append(f"Entry: ${signal_data['entry']}")
    if signal_data.get('stop_loss'):
        message_parts.append(f"Stop Loss: ${signal_data['stop_loss']}")
    if signal_data.get('targets'):
        message_parts.append(f"Targets: {', '.join(signal_data['targets'])}")
    if signal_data.get('leverage'):
        message_parts.append(f"Leverage: {signal_data['leverage']}x")

    if signal_data.get('has_chart') and signal_data.get('chart_analysis'):
        chart = signal_data['chart_analysis']
        message_parts.append(f"")
        message_parts.append(f"*Chart Analysis:*")
        if chart.get('timeframe'):
            message_parts.append(f"Timeframe: {chart['timeframe']}")
        if chart.get('pattern'):
            message_parts.append(f"Pattern: {chart['pattern']}")

    message_parts.append(f"")
    message_parts.append(f"Signal:")
    message_parts.append(f"```")
    clean_text = signal_data['raw_text'][:200].encode('ascii', 'ignore').decode('ascii')
    message_parts.append(clean_text)
    message_parts.append(f"```")
    message_parts.append(f"")
    message_parts.append(f"Reply:")
    message_parts.append(f"`APPROVE {signal_data['coins'][0]} {signal_data['direction']} 50` for $50")
    message_parts.append(f"`SKIP` to ignore")

    message = '\n'.join(message_parts)

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
                    print(f"[OK] Notification sent: {coins_str} {signal_data['direction']}")
                else:
                    text = await response.text()
                    print(f"[ERROR] Telegram failed: {response.status} - {text}")
    except Exception as e:
        print(f"[ERROR] Telegram error: {e}")


# ============================================
# MAIN
# ============================================

async def main():
    print("=" * 60)
    print("100xclub Channel Monitor - Polling Mode (v2 Enhanced)")
    print(f"Checking messages from last {CHECK_MINUTES} minutes")
    print("=" * 60)

    if not SESSION_STRING:
        print("[ERROR] No TELEGRAM_SESSION set!")
        return

    client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    await client.start()
    print("[OK] Connected to Telegram")

    # Find channel
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

    cutoff_time = datetime.utcnow() - timedelta(minutes=CHECK_MINUTES)
    print(f"[INFO] Checking messages since {cutoff_time.isoformat()}...")

    signals_found = 0

    async for message in client.iter_messages(channel, limit=50):
        if message.date.replace(tzinfo=None) < cutoff_time:
            break

        text = message.text or ''

        # Check for images/charts
        image_analysis = None
        if message.photo and GROQ_API_KEY:
            try:
                photo_bytes = await client.download_media(message.photo, bytes)
                image_analysis = await analyze_chart_image(photo_bytes, GROQ_API_KEY)
                if image_analysis:
                    print(f"[CHART] Analyzed image: {image_analysis}")
            except Exception as e:
                print(f"[WARN] Could not analyze image: {e}")

        # Detect signal
        signal = SignalDetector.detect(text, image_analysis)

        if signal and signal['detected']:
            signal['timestamp'] = message.date.isoformat()
            signal['message_id'] = message.id
            signals_found += 1

            print(f"[SIGNAL] {signal['coins']} - {signal['direction']} ({signal['action']})")
            await send_telegram_notification(signal)

    print(f"\n[DONE] Found {signals_found} trade signal(s)")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
