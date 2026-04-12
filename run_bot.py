import asyncio
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.tl.types import MessageEntityUrl, MessageEntityTextUrl

# GitHub Secrets에서 가져올 설정값들
API_ID         = int(os.environ["TG_API_ID"])
API_HASH       = os.environ["TG_API_HASH"]
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID     = int(os.environ["TELEGRAM_CHAT_ID"])
SESSION_STRING = os.environ["TG_SESSION_STRING"]

SOURCE_CHANNEL = "@darthacking"

CATEGORIES = {
    "변동": {"label": "📊 30% 변동 공시", "keywords": ["30%", "30 %", "매출액 또는 손익구조", "영업손실 전환", "흑자전환", "적자전환"]},
    "수주": {"label": "🏗 수주 공시", "keywords": ["수주", "계약 체결", "공급계약", "납품계약", "단일판매"]},
    "투자": {"label": "💰 투자 공시", "keywords": ["투자", "출자", "지분 취득", "인수", "M&A", "타법인 주식"]},
}

def classify(text: str) -> str | None:
    for cat_key, cat in CATEGORIES.items():
        if any(kw in text for kw in cat["keywords"]): return cat_key
    return None

def clean_text(text: str) -> str:
    return text[:250] + "…" if len(text) > 250 else text

async def main():
    from telethon.sessions import StringSession
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    since_dt = now_kst - timedelta(hours=24)

    user_client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)
    bot_client = TelegramClient(StringSession(), API_ID, API_HASH)

    await user_client.connect()
    await bot_client.start(bot_token=BOT_TOKEN)

    from collections import defaultdict
    buffer = defaultdict(list)

    async for msg in user_client.iter_messages(SOURCE_CHANNEL, limit=300):
        if not msg.text: continue
        if msg.date.astimezone(KST) < since_dt: break
        cat = classify(msg.text)
        if cat: buffer[cat].append(msg.text)

    total = sum(len(v) for v in buffer.values())
    today_str = now_kst.strftime("%Y년 %m월 %d일")

    if total == 0:
        await bot_client.send_message(MY_CHAT_ID, f"📭 <b>{today_str} 공시 요약</b>\n수집된 공시가 없습니다.", parse_mode="html")
    else:
