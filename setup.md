# 100xclub Automatic Channel Monitor Setup

## Overview
This solution automatically monitors the 100xclub Telegram channel for trade signals without requiring manual forwarding.

## Step 1: Get Telegram API Credentials

1. Go to https://my.telegram.org
2. Log in with your phone number
3. Click "API Development Tools"
4. Create a new application (any name, e.g., "Trade Monitor")
5. Copy your **api_id** and **api_hash**

## Step 2: Install Dependencies

```bash
pip install telethon aiohttp
```

## Step 3: Configure the Script

Edit `channel_monitor.py` and update these values:

```python
API_ID = 12345678  # Your api_id from my.telegram.org
API_HASH = 'your_api_hash_here'  # Your api_hash
PHONE_NUMBER = '+1234567890'  # Your phone number with country code
```

Or set environment variables:
```bash
set TELEGRAM_API_ID=12345678
set TELEGRAM_API_HASH=your_api_hash_here
set TELEGRAM_PHONE=+1234567890
```

## Step 4: Run the Monitor

```bash
cd C:\Users\musag\.openclaw\skills\crypto-trading-assistant\telethon
python channel_monitor.py
```

First run will ask you to:
1. Enter your phone number
2. Enter the verification code sent to Telegram
3. (Optional) Enter 2FA password if enabled

After first login, a session file is created and you won't need to re-authenticate.

## Step 5: Run 24/7 (Options)

### Option A: Windows Task Scheduler
1. Create a batch file `run_monitor.bat`:
```batch
@echo off
cd C:\Users\musag\.openclaw\skills\crypto-trading-assistant\telethon
python channel_monitor.py
```
2. Use Task Scheduler to run at startup

### Option B: Run as Windows Service
Use NSSM (Non-Sucking Service Manager) to create a Windows service

### Option C: Deploy to Cloud
Deploy to a cloud VM (AWS, DigitalOcean, etc.) that runs 24/7

## How It Works

1. The script uses the Telegram User API (not Bot API) to read the channel
2. When a new message arrives, it parses for trade signals
3. If a signal is detected, it:
   - Sends a notification to your Telegram bot
   - Optionally sends to n8n webhook for further processing
4. You reply APPROVE or SKIP to execute or ignore the trade

## Security Notes

- Your session file contains your login - keep it secure
- The api_id and api_hash are tied to your Telegram account
- Don't share these credentials with anyone
