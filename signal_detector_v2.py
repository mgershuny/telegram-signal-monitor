"""
Enhanced Signal Detection v2
Multiple detection methods for higher accuracy
"""

import re

# Expanded coin list
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
    # Stables (to detect position closes)
    'USDT', 'USDC', 'DAI', 'BUSD',
    # Others
    'TON', 'KAS', 'STX', 'ORDI', 'RUNE', 'TRX', 'LEO', 'OKB', 'CRO', 'MNT'
]

COIN_PATTERN = re.compile(r'\b(' + '|'.join(COINS) + r')\b', re.IGNORECASE)

class SignalDetector:
    """
    Multi-method signal detection for trading messages
    """

    # Method 1: Direct action patterns (highest confidence)
    DIRECT_ACTION_PATTERNS = [
        # "Longed BTC", "Shorted SOL", etc
        (r'\b(longed|shorted|bought|sold)\s+([A-Z]{2,6})\b', 'direct_action'),
        # "Long BTC", "Short SOL" (without -ed)
        (r'\b(long|short)\s+([A-Z]{2,6})\b', 'direct_action'),
        # "BTC long", "SOL short"
        (r'\b([A-Z]{2,6})\s+(long|short)\b', 'direct_action_reverse'),
        # "Took a BTC long/short"
        (r'\btook\s+(?:a\s+)?(?:this\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'took_position'),
        # "Took long/short on BTC"
        (r'\btook\s+(?:a\s+)?(?:this\s+)?(long|short)\s+(?:on\s+)?([A-Z]{2,6})\b', 'took_position'),
        # "Taking this SOL long"
        (r'\btaking\s+(?:this\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'taking_position'),
        # "Entered BTC long"
        (r'\bentered?\s+(?:a\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'entered_position'),
        # "Added to BTC long"
        (r'\badded\s+(?:to\s+)?(?:my\s+)?([A-Z]{2,6})?\s*(long|short)\b', 'added_position'),
    ]

    # Method 2: Scalp patterns
    SCALP_PATTERNS = [
        (r'\bscalp\s+(long|short)\s+([A-Z]{2,6})\b', 'scalp'),
        (r'\b([A-Z]{2,6})\s+scalp\s+(long|short)\b', 'scalp_reverse'),
        (r'\bscalp(?:ed|ing)?\s+([A-Z]{2,6})\b', 'scalp_coin'),
        (r'\btook\s+(?:a\s+)?(?:this\s+)?([A-Z]{2,6})?\s*scalp\s*(long|short)?\b', 'took_scalp'),
    ]

    # Method 3: Position update patterns
    UPDATE_PATTERNS = [
        (r'\b(?:updated?|new)\s+([A-Z]{2,6})?\s*(?:sl|stop\s*loss|tp|take\s*profit)\b', 'update'),
        (r'\b([A-Z]{2,6})\s+(?:sl|stop\s*loss|tp|take\s*profit)\s*(?:updated?|changed?|moved?)\b', 'update_reverse'),
        (r'\bsl\s+(?:at|to|@)\s*\$?([\d,.]+)\b', 'sl_level'),
        (r'\btp\s+(?:at|to|@)\s*\$?([\d,.]+)\b', 'tp_level'),
    ]

    # Method 4: Position close patterns
    CLOSE_PATTERNS = [
        (r'\bclosed?\s+(?:my\s+)?(?:the\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'closed'),
        (r'\bclosing\s+(?:my\s+)?(?:the\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'closing'),
        (r'\bexited?\s+(?:my\s+)?(?:the\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'exited'),
        (r'\breduced?\s+(?:my\s+)?([A-Z]{2,6})?\s*(long|short)?\b', 'reduced'),
    ]

    # Method 5: Entry patterns
    ENTRY_PATTERNS = [
        (r'\bentry\s*(?:at|@|:)?\s*\$?([\d,.]+)\b', 'entry_price'),
        (r'\benter(?:ed|ing)?\s+(?:at|@)?\s*\$?([\d,.]+)\b', 'enter_price'),
        (r'\bbuy\s+(?:at|@|zone)?\s*\$?([\d,.]+)\b', 'buy_zone'),
        (r'\bsell\s+(?:at|@|zone)?\s*\$?([\d,.]+)\b', 'sell_zone'),
    ]

    # Keywords that indicate trading activity
    TRADING_KEYWORDS = {
        'high_confidence': ['longed', 'shorted', 'scalp', 'entry', 'sl', 'tp', 'stop loss', 'take profit'],
        'medium_confidence': ['long', 'short', 'buy', 'sell', 'target', 'position'],
        'low_confidence': ['bullish', 'bearish', 'breakout', 'breakdown', 'support', 'resistance'],
        'action_verbs': ['took', 'taking', 'entered', 'entering', 'closed', 'closing', 'added', 'reduced', 'exited'],
    }

    @classmethod
    def detect(cls, text):
        """
        Detect trading signals using multiple methods
        Returns: dict with signal info or None
        """
        if not text or len(text) < 10:
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
            'raw_text': text[:500]
        }

        # Extract all coins mentioned
        coin_matches = COIN_PATTERN.findall(text)
        result['coins'] = list(set(c.upper() for c in coin_matches))

        # Skip if no coins found (except for stables)
        tradeable_coins = [c for c in result['coins'] if c not in ['USDT', 'USDC', 'DAI', 'BUSD']]
        if not tradeable_coins:
            return None

        # Method 1: Direct action patterns
        for pattern, method_name in cls.DIRECT_ACTION_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['detected'] = True
                result['methods'].append(f'direct_action:{method_name}')
                result['confidence'] += 40

                # Extract direction
                groups = match.groups()
                for g in groups:
                    if g and g.lower() in ['long', 'longed', 'bought', 'buy']:
                        result['direction'] = 'LONG'
                        result['action'] = 'OPEN'
                    elif g and g.lower() in ['short', 'shorted', 'sold', 'sell']:
                        result['direction'] = 'SHORT'
                        result['action'] = 'OPEN'

        # Method 2: Scalp patterns
        for pattern, method_name in cls.SCALP_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['detected'] = True
                result['methods'].append(f'scalp:{method_name}')
                result['confidence'] += 35
                result['action'] = 'SCALP'

                groups = match.groups()
                for g in groups:
                    if g and g.lower() == 'long':
                        result['direction'] = 'LONG'
                    elif g and g.lower() == 'short':
                        result['direction'] = 'SHORT'

        # Method 3: Position update patterns
        for pattern, method_name in cls.UPDATE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['detected'] = True
                result['methods'].append(f'update:{method_name}')
                result['confidence'] += 25
                result['action'] = 'UPDATE'

                # Extract SL/TP levels
                if 'sl_level' in method_name:
                    result['stop_loss'] = match.group(1)
                if 'tp_level' in method_name:
                    result['targets'].append(match.group(1))

        # Method 4: Position close patterns
        for pattern, method_name in cls.CLOSE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['detected'] = True
                result['methods'].append(f'close:{method_name}')
                result['confidence'] += 30
                result['action'] = 'CLOSE'

                groups = match.groups()
                for g in groups:
                    if g and g.lower() == 'long':
                        result['direction'] = 'LONG'
                    elif g and g.lower() == 'short':
                        result['direction'] = 'SHORT'

        # Method 5: Entry patterns
        for pattern, method_name in cls.ENTRY_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                result['methods'].append(f'entry:{method_name}')
                result['confidence'] += 15
                result['entry'] = match.group(1)

        # Keyword-based confidence boost
        for kw in cls.TRADING_KEYWORDS['high_confidence']:
            if kw in text_lower:
                result['confidence'] += 10
        for kw in cls.TRADING_KEYWORDS['medium_confidence']:
            if kw in text_lower:
                result['confidence'] += 5
        for kw in cls.TRADING_KEYWORDS['action_verbs']:
            if kw in text_lower:
                result['confidence'] += 8

        # Extract leverage
        leverage_match = re.search(r'(\d+)x\b', text_lower)
        if leverage_match:
            result['leverage'] = leverage_match.group(1)
            result['confidence'] += 5

        # Determine final direction if not set
        if not result['direction']:
            if re.search(r'\b(long|buy|bullish)\b', text_lower):
                result['direction'] = 'LONG'
            elif re.search(r'\b(short|sell|bearish)\b', text_lower):
                result['direction'] = 'SHORT'
            else:
                result['direction'] = 'Unknown'

        # Only return if we have some confidence
        if result['confidence'] >= 20:
            result['detected'] = True
            return result

        return None


def parse_trade_signal_v2(text):
    """
    Enhanced signal parser using SignalDetector
    """
    return SignalDetector.detect(text)


# Test
if __name__ == '__main__':
    test_messages = [
        "Took sol scalp long too",
        "Longed BTC",
        "shorted SOL too",
        "UPDATED SOL SL:",
        "Took an ETH scalp long",
        "BTC long sl at 89.100",
        "Closed SOL",
        "Taking this SOL scalp long",
        "Added to my LINK long",
        "Reduced BTC short by 50%",
        "Entry at $95,000 with SL at $93,500",
        "This is just a random message about crypto",
        "Hello everyone, welcome to the channel",
    ]

    print("Testing Signal Detector v2:\n")
    for msg in test_messages:
        result = parse_trade_signal_v2(msg)
        if result:
            print(f"[DETECTED] {msg[:50]}...")
            print(f"  Coins: {result['coins']}")
            print(f"  Direction: {result['direction']}")
            print(f"  Action: {result['action']}")
            print(f"  Confidence: {result['confidence']}")
            print(f"  Methods: {result['methods']}")
            print()
        else:
            print(f"[SKIPPED] {msg[:50]}...")
            print()
