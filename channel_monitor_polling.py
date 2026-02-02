"""
100xclub Telegram Channel Monitor - Polling Version for GitHub Actions
Enhanced with v2 Signal Detector + Image Analysis + Video Transcription
"""

import asyncio
import re
import os
import base64
import aiohttp
import tempfile
import subprocess
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

    # Intent patterns - detect trading intent even without coin name
    INTENT_PATTERNS = [
        (r'\b(i am|im|i\'m)\s+(longing|shorting|long|short)\b', 'self_action'),
        (r'\b(longing|shorting)\s+(here|now|this)?\b', 'action_now'),
        (r'\b(going|went)\s+(long|short)\b', 'going_direction'),
        (r'\bam\s+(long|short)\b', 'am_position'),
    ]

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
                    if coin.upper() not in result['coins'] and coin.upper() != 'UNKNOWN':
                        result['coins'].append(coin.upper())
                        tradeable_coins.append(coin.upper())
            if image_analysis.get('direction'):
                result['direction'] = image_analysis['direction']
            result['confidence'] += 30

        # Check for intent patterns (trading intent without coin name)
        for pattern, method_name in cls.INTENT_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['methods'].append(f'intent:{method_name}')
                result['confidence'] += 35
                groups = match.groups()
                for g in groups:
                    if g and g.lower() in ['long', 'longing']:
                        result['direction'] = 'LONG'
                        result['action'] = 'OPEN'
                    elif g and g.lower() in ['short', 'shorting']:
                        result['direction'] = 'SHORT'
                        result['action'] = 'OPEN'

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
# VIDEO TRANSCRIPTION
# ============================================

async def transcribe_video(video_bytes, groq_api_key=None):
    """
    Transcribe video audio using Groq's Whisper API
    Returns: dict with transcription and detected signals
    """
    if not groq_api_key:
        return None

    try:
        # Save video to temp file
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_video:
            tmp_video.write(video_bytes)
            tmp_video_path = tmp_video.name

        # Extract audio using ffmpeg (convert to mp3)
        tmp_audio_path = tmp_video_path.replace('.mp4', '.mp3')

        try:
            # Try to extract audio with ffmpeg
            result = subprocess.run(
                ['ffmpeg', '-i', tmp_video_path, '-vn', '-acodec', 'libmp3lame',
                 '-q:a', '4', '-y', tmp_audio_path],
                capture_output=True,
                timeout=60
            )

            if result.returncode != 0 or not os.path.exists(tmp_audio_path):
                print(f"[WARN] ffmpeg audio extraction failed: {result.stderr.decode()[:200]}")
                # Cleanup
                os.unlink(tmp_video_path)
                return None

        except FileNotFoundError:
            print("[WARN] ffmpeg not installed, cannot extract audio from video")
            os.unlink(tmp_video_path)
            return None
        except subprocess.TimeoutExpired:
            print("[WARN] ffmpeg timeout during audio extraction")
            os.unlink(tmp_video_path)
            return None

        # Check audio file size (max 25MB for Groq)
        audio_size = os.path.getsize(tmp_audio_path)
        if audio_size > 25 * 1024 * 1024:
            print(f"[WARN] Audio file too large ({audio_size / 1024 / 1024:.1f}MB), max 25MB")
            os.unlink(tmp_video_path)
            os.unlink(tmp_audio_path)
            return None

        # Read audio file
        with open(tmp_audio_path, 'rb') as f:
            audio_bytes = f.read()

        # Cleanup temp files
        os.unlink(tmp_video_path)
        os.unlink(tmp_audio_path)

        # Transcribe with Groq Whisper API
        import aiohttp
        from aiohttp import FormData

        data = FormData()
        data.add_field('file', audio_bytes, filename='audio.mp3', content_type='audio/mpeg')
        data.add_field('model', 'whisper-large-v3-turbo')
        data.add_field('response_format', 'json')
        data.add_field('language', 'en')
        data.add_field('prompt', 'This is a cryptocurrency trading video discussing coins like BTC, ETH, SOL, LINK and trading strategies.')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.groq.com/openai/v1/audio/transcriptions',
                headers={
                    'Authorization': f'Bearer {groq_api_key}'
                },
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    transcription = result.get('text', '')
                    print(f"[TRANSCRIBE] Got {len(transcription)} chars of transcription")

                    # Extract trading signals from transcription
                    signals = extract_signals_from_transcription(transcription)

                    return {
                        'transcription': transcription,
                        'signals': signals,
                        'coins': signals.get('coins', []),
                        'direction': signals.get('direction'),
                        'risk_reward': signals.get('risk_reward'),
                    }
                else:
                    error_text = await response.text()
                    print(f"[ERROR] Whisper API failed: {response.status} - {error_text[:200]}")
                    return None

    except Exception as e:
        print(f"[ERROR] Video transcription error: {e}")
        return None


def extract_signals_from_transcription(transcription):
    """
    Extract trading signals from video transcription text
    """
    text = transcription.lower()
    result = {
        'coins': [],
        'direction': None,
        'risk_reward': None,
        'entry': None,
        'stop_loss': None,
        'target': None,
    }

    # Find coins mentioned
    coin_matches = COIN_PATTERN.findall(transcription)
    result['coins'] = list(set(c.upper() for c in coin_matches))

    # Filter out stablecoins
    result['coins'] = [c for c in result['coins'] if c not in ['USDT', 'USDC', 'DAI', 'BUSD']]

    # Direction detection
    long_patterns = [
        r'\b(going long|longing|long position|bullish on|buying|accumulating)\b',
        r'\b(i.m long|i am long|we.re long|we are long)\b',
        r'\b(long\s+(?:' + '|'.join(COINS[:20]) + r'))\b',
    ]
    short_patterns = [
        r'\b(going short|shorting|short position|bearish on|selling)\b',
        r'\b(i.m short|i am short|we.re short|we are short)\b',
        r'\b(short\s+(?:' + '|'.join(COINS[:20]) + r'))\b',
    ]

    for pattern in long_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            result['direction'] = 'LONG'
            break

    if not result['direction']:
        for pattern in short_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                result['direction'] = 'SHORT'
                break

    # Risk/Reward detection
    rr_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:to|:)\s*(\d+(?:\.\d+)?)\s*(?:risk|r)\s*(?:to|:)?\s*(?:reward|r)',
        r'(?:risk|r)\s*(?:to|:)?\s*(?:reward|r)\s*(?:of|is|:)?\s*(\d+(?:\.\d+)?)\s*(?:to|:)\s*(\d+(?:\.\d+)?)',
        r'(\d+(?:\.\d+)?)\s*r\s*(?:to|:)\s*(\d+(?:\.\d+)?)\s*r',
    ]

    for pattern in rr_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['risk_reward'] = f"{match.group(1)}:{match.group(2)}"
            break

    # Also check for simple "X to 1" pattern
    simple_rr = re.search(r'(\d+(?:\.\d+)?)\s*to\s*1\s*(?:risk|reward)?', text, re.IGNORECASE)
    if simple_rr and not result['risk_reward']:
        result['risk_reward'] = f"1:{simple_rr.group(1)}"

    return result


# ============================================
# YOUTUBE VIDEO DETECTION & TRANSCRIPTION
# ============================================

# Fefe's YouTube channel ID
YOUTUBE_CHANNEL_ID = 'UC4p8s5ecGS4VWBP5QUvgehg'  # 100X Club channel
YOUTUBE_CHANNEL_URL = 'https://www.youtube.com/@100XClub'

# Patterns that indicate Fefe posted a new video
VIDEO_MENTION_PATTERNS = [
    r'\bvideo\s+is\s+up\b',
    r'\bupdate\s+is\s+up\b',
    r'\bdaily\s+update\s+is\s+up\b',
    r'\bmarket\s+update\s+is\s+up\b',
    r'\bjust\s+dropped\s+(?:a\s+)?video\b',
    r'\bpublished\s+(?:the\s+)?video\b',
    r'\bcheck\s+(?:out\s+)?(?:the\s+)?(?:new\s+)?video\b',
    r'\bwatch\s+(?:the\s+)?(?:today.?s\s+)?(?:show|video|update)\b',
    r'\bon\s+the\s+100\s*x\s*club\b',
    r'\bon\s+the\s+channel\b',
]

# File to track processed video IDs (avoid re-processing)
PROCESSED_VIDEOS_FILE = '/tmp/processed_youtube_videos.txt'


def check_video_mention(text):
    """Check if text mentions a new video being posted"""
    text_lower = text.lower()
    for pattern in VIDEO_MENTION_PATTERNS:
        if re.search(pattern, text_lower, re.IGNORECASE):
            return True
    return False


def get_processed_videos():
    """Get list of already processed YouTube video IDs"""
    try:
        if os.path.exists(PROCESSED_VIDEOS_FILE):
            with open(PROCESSED_VIDEOS_FILE, 'r') as f:
                return set(line.strip() for line in f if line.strip())
    except:
        pass
    return set()


def mark_video_processed(video_id):
    """Mark a video ID as processed"""
    try:
        with open(PROCESSED_VIDEOS_FILE, 'a') as f:
            f.write(f"{video_id}\n")
    except:
        pass


async def get_latest_youtube_video():
    """
    Fetch the latest video from Fefe's 100X Club YouTube channel
    Returns: dict with video_id, title, url, published_at
    """
    try:
        # Use yt-dlp to get channel info
        result = subprocess.run(
            ['yt-dlp', '--flat-playlist', '--print', '%(id)s', '--print', '%(title)s',
             '--playlist-items', '1', YOUTUBE_CHANNEL_URL + '/videos'],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                video_id = lines[0].strip()
                title = lines[1].strip()
                return {
                    'video_id': video_id,
                    'title': title,
                    'url': f'https://www.youtube.com/watch?v={video_id}'
                }

        print(f"[YOUTUBE] yt-dlp output: {result.stdout[:200]}")
        print(f"[YOUTUBE] yt-dlp stderr: {result.stderr[:200]}")

    except subprocess.TimeoutExpired:
        print("[YOUTUBE] Timeout fetching channel info")
    except FileNotFoundError:
        print("[YOUTUBE] yt-dlp not installed")
    except Exception as e:
        print(f"[YOUTUBE] Error fetching channel: {e}")

    return None


async def download_youtube_audio(video_url, max_duration=900):
    """
    Download audio from YouTube video
    Returns: path to audio file or None
    """
    try:
        # First check video duration
        result = subprocess.run(
            ['yt-dlp', '--print', 'duration', video_url],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            try:
                duration = int(result.stdout.strip())
                if duration > max_duration:
                    print(f"[YOUTUBE] Video too long ({duration}s > {max_duration}s), skipping")
                    return None
            except:
                pass

        # Download audio
        audio_path = tempfile.mktemp(suffix='.mp3')
        result = subprocess.run(
            ['yt-dlp', '-x', '--audio-format', 'mp3', '--audio-quality', '5',
             '-o', audio_path.replace('.mp3', '.%(ext)s'), video_url],
            capture_output=True,
            text=True,
            timeout=180  # 3 minutes for download
        )

        # yt-dlp might save with different extension first
        possible_paths = [
            audio_path,
            audio_path.replace('.mp3', '.webm'),
            audio_path.replace('.mp3', '.m4a'),
        ]

        for path in possible_paths:
            mp3_path = path.replace('.webm', '.mp3').replace('.m4a', '.mp3')
            if os.path.exists(mp3_path):
                return mp3_path
            if os.path.exists(path):
                return path

        print(f"[YOUTUBE] Download failed: {result.stderr[:200]}")
        return None

    except subprocess.TimeoutExpired:
        print("[YOUTUBE] Download timeout")
    except Exception as e:
        print(f"[YOUTUBE] Download error: {e}")

    return None


async def transcribe_youtube_video(video_url, groq_api_key):
    """
    Download and transcribe a YouTube video
    Returns: dict with transcription and extracted signals
    """
    if not groq_api_key:
        return None

    print(f"[YOUTUBE] Downloading audio from: {video_url}")
    audio_path = await download_youtube_audio(video_url)

    if not audio_path or not os.path.exists(audio_path):
        return None

    try:
        # Check file size
        audio_size = os.path.getsize(audio_path)
        print(f"[YOUTUBE] Audio size: {audio_size / 1024 / 1024:.2f}MB")

        if audio_size > 25 * 1024 * 1024:
            print("[YOUTUBE] Audio too large for Groq (max 25MB)")
            os.unlink(audio_path)
            return None

        # Read and transcribe
        with open(audio_path, 'rb') as f:
            audio_bytes = f.read()

        # Cleanup
        os.unlink(audio_path)

        # Transcribe with Groq
        from aiohttp import FormData

        data = FormData()
        data.add_field('file', audio_bytes, filename='audio.mp3', content_type='audio/mpeg')
        data.add_field('model', 'whisper-large-v3-turbo')
        data.add_field('response_format', 'json')
        data.add_field('language', 'en')
        data.add_field('prompt', 'Cryptocurrency trading video by Fefe discussing BTC Bitcoin ETH Ethereum SOL Solana LINK Chainlink, entries, stop losses, and risk reward ratios.')

        async with aiohttp.ClientSession() as session:
            async with session.post(
                'https://api.groq.com/openai/v1/audio/transcriptions',
                headers={'Authorization': f'Bearer {groq_api_key}'},
                data=data
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    transcription = result.get('text', '')
                    print(f"[YOUTUBE] Transcribed {len(transcription)} chars")

                    # Extract signals
                    signals = extract_signals_from_transcription(transcription)

                    # Also look for specific entry prices mentioned
                    entries = extract_entry_prices(transcription)

                    return {
                        'transcription': transcription,
                        'coins': signals.get('coins', []),
                        'direction': signals.get('direction'),
                        'risk_reward': signals.get('risk_reward'),
                        'entries': entries,
                        'has_youtube': True,
                    }
                else:
                    print(f"[YOUTUBE] Transcription failed: {response.status}")
                    return None

    except Exception as e:
        print(f"[YOUTUBE] Transcription error: {e}")
        if audio_path and os.path.exists(audio_path):
            os.unlink(audio_path)
        return None


def extract_entry_prices(transcription):
    """Extract specific entry prices from transcription"""
    entries = {}

    # Pattern: "long Bitcoin 77750" or "Bitcoin at 77750"
    patterns = [
        r'\b(long|short)\s+(bitcoin|btc|ethereum|eth|solana|sol|link)\s+(?:at\s+)?(\d{2,6}(?:\.\d+)?)\b',
        r'\b(bitcoin|btc|ethereum|eth|solana|sol|link)\s+(?:at\s+)?(\d{2,6}(?:\.\d+)?)\b',
        r'\b(bitcoin|btc|ethereum|eth|solana|sol|link)\s+(?:entry|entered)\s+(?:at\s+)?(\d{2,6}(?:\.\d+)?)\b',
    ]

    text = transcription.lower()

    # Map common names to symbols
    name_to_symbol = {
        'bitcoin': 'BTC', 'btc': 'BTC',
        'ethereum': 'ETH', 'eth': 'ETH',
        'solana': 'SOL', 'sol': 'SOL',
        'link': 'LINK', 'chainlink': 'LINK',
    }

    for pattern in patterns:
        for match in re.finditer(pattern, text, re.IGNORECASE):
            groups = match.groups()
            if len(groups) >= 2:
                coin_name = groups[-2] if len(groups) == 3 else groups[0]
                price = groups[-1]
                symbol = name_to_symbol.get(coin_name.lower(), coin_name.upper())
                entries[symbol] = price

    return entries


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

    if signal_data.get('risk_reward'):
        message_parts.append(f"Risk/Reward: {signal_data['risk_reward']}")

    if signal_data.get('entries'):
        message_parts.append(f"")
        message_parts.append(f"*Entry Prices:*")
        for coin, price in signal_data['entries'].items():
            message_parts.append(f"  {coin}: ${price}")

    if signal_data.get('has_youtube'):
        message_parts.append(f"")
        message_parts.append(f"*[From YouTube Video]*")
    elif signal_data.get('has_video'):
        message_parts.append(f"")
        message_parts.append(f"*[From Video Analysis]*")

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
    print("100xclub Channel Monitor - Polling Mode (v2 Enhanced + Video)")
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
    processed_videos = get_processed_videos()

    async for message in client.iter_messages(channel, limit=50):
        if message.date.replace(tzinfo=None) < cutoff_time:
            break

        text = message.text or ''

        # Check if message mentions a video being posted
        youtube_analysis = None
        if check_video_mention(text) and GROQ_API_KEY:
            print(f"[YOUTUBE] Detected video mention: {text[:100]}...")

            # First check if there's a YouTube link in the message
            youtube_match = re.search(r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})', text)
            if youtube_match:
                video_id = youtube_match.group(1)
                video_url = f'https://www.youtube.com/watch?v={video_id}'
            else:
                # No link in message, fetch latest from channel
                print("[YOUTUBE] No link in message, fetching latest video from channel...")
                latest = await get_latest_youtube_video()
                if latest:
                    video_id = latest['video_id']
                    video_url = latest['url']
                    print(f"[YOUTUBE] Latest video: {latest['title']}")
                else:
                    video_id = None
                    video_url = None

            # Process video if not already done
            if video_id and video_id not in processed_videos:
                print(f"[YOUTUBE] Processing video: {video_id}")
                youtube_analysis = await transcribe_youtube_video(video_url, GROQ_API_KEY)
                if youtube_analysis:
                    mark_video_processed(video_id)
                    # Append transcription to text for signal detection
                    if youtube_analysis.get('transcription'):
                        text = text + "\n\n[YOUTUBE VIDEO TRANSCRIPTION]:\n" + youtube_analysis['transcription'][:2000]
            elif video_id:
                print(f"[YOUTUBE] Video {video_id} already processed, skipping")

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

        # Check for videos - transcribe audio
        video_analysis = None
        if message.video and GROQ_API_KEY:
            try:
                # Check video size (limit to ~50MB to avoid long downloads)
                video_size = getattr(message.video, 'size', 0)
                if video_size and video_size < 50 * 1024 * 1024:
                    print(f"[VIDEO] Downloading video ({video_size / 1024 / 1024:.1f}MB)...")
                    video_bytes = await client.download_media(message.video, bytes)
                    video_analysis = await transcribe_video(video_bytes, GROQ_API_KEY)
                    if video_analysis:
                        print(f"[VIDEO] Transcription signals: {video_analysis.get('coins')} - {video_analysis.get('direction')}")
                        # Append transcription to text for signal detection
                        if video_analysis.get('transcription'):
                            text = text + "\n\n[VIDEO TRANSCRIPTION]:\n" + video_analysis['transcription']
                else:
                    print(f"[VIDEO] Skipping large video ({video_size / 1024 / 1024:.1f}MB)")
            except Exception as e:
                print(f"[WARN] Could not transcribe video: {e}")

        # Combine all analysis (image, video, youtube)
        combined_analysis = image_analysis
        if video_analysis:
            if not combined_analysis:
                combined_analysis = {}
            # Merge video coins into analysis
            if video_analysis.get('coins'):
                existing_coins = combined_analysis.get('coins', [])
                combined_analysis['coins'] = list(set(existing_coins + video_analysis['coins']))
            if video_analysis.get('direction') and not combined_analysis.get('direction'):
                combined_analysis['direction'] = video_analysis['direction']
            if video_analysis.get('risk_reward'):
                combined_analysis['risk_reward'] = video_analysis['risk_reward']
            combined_analysis['has_video'] = True
            combined_analysis['transcription'] = video_analysis.get('transcription', '')[:500]

        # Merge YouTube analysis
        if youtube_analysis:
            if not combined_analysis:
                combined_analysis = {}
            if youtube_analysis.get('coins'):
                existing_coins = combined_analysis.get('coins', [])
                combined_analysis['coins'] = list(set(existing_coins + youtube_analysis['coins']))
            if youtube_analysis.get('direction') and not combined_analysis.get('direction'):
                combined_analysis['direction'] = youtube_analysis['direction']
            if youtube_analysis.get('risk_reward'):
                combined_analysis['risk_reward'] = youtube_analysis['risk_reward']
            if youtube_analysis.get('entries'):
                combined_analysis['entries'] = youtube_analysis['entries']
            combined_analysis['has_youtube'] = True

        # Detect signal
        signal = SignalDetector.detect(text, combined_analysis)

        if signal and signal['detected']:
            signal['timestamp'] = message.date.isoformat()
            signal['message_id'] = message.id
            # Add video-specific info
            if video_analysis:
                signal['has_video'] = True
                if video_analysis.get('risk_reward'):
                    signal['risk_reward'] = video_analysis['risk_reward']
            # Add YouTube-specific info
            if youtube_analysis:
                signal['has_youtube'] = True
                if youtube_analysis.get('risk_reward'):
                    signal['risk_reward'] = youtube_analysis['risk_reward']
                if youtube_analysis.get('entries'):
                    signal['entries'] = youtube_analysis['entries']
            signals_found += 1

            print(f"[SIGNAL] {signal['coins']} - {signal['direction']} ({signal['action']})")
            await send_telegram_notification(signal)

    print(f"\n[DONE] Found {signals_found} trade signal(s)")
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())
