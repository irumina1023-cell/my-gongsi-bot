import asyncio
import os
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient
from telethon.sessions import StringSession

# GitHub Secrets 설정값
API_ID         = int(os.environ["TG_API_ID"])
API_HASH       = os.environ["TG_API_HASH"]
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID     = int(os.environ["TELEGRAM_CHAT_ID"])
SESSION_STRING = os.environ["TG_SESSION_STRING"]

SOURCE_CHANNEL = "@darthacking"

# 💡 '1분기'를 빼고 '실적 발표'로 범용성을 높였습니다.
CATEGORIES = {
    "실적": {"label": "📈 실적 발표", "keywords": ["영업실적", "잠정실적", "결산실적", "실적발표"]},
    "변동": {"label": "📊 30% 변동 공시", "keywords": ["30%", "30 %", "매출액 또는 손익구조", "영업손실 전환", "흑자전환", "적자전환"]},
    "수주": {"label": "🏗 수주 공시", "keywords": ["수주", "계약 체결", "공급계약", "납품계약", "단일판매"]},
    "투자": {"label": "💰 투자 공시", "keywords": ["투자", "출자", "지분 취득", "인수", "M&A", "타법인 주식"]},
}

def classify(text: str):
    for cat_key, cat in CATEGORIES.items():
        if any(kw in text for kw in cat["keywords"]): 
            return cat_key
    return None

def clean_text(text: str):
    return text[:250] + "…" if len(text) > 250 else text

async def main():
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
        if not msg.text: 
            continue
        if msg.date.astimezone(KST) < since_dt: 
            break
        cat = classify(msg.text)
        if cat: 
            buffer[cat].append(msg.text)

    total = sum(len(v) for v in buffer.values())
    today_str = now_kst.strftime("%Y년 %m월 %d일")

    if total == 0:
        await bot_client.send_message(MY_CHAT_ID, f"📭 <b>{today_str} 공시 요약</b>\n수집된 공시가 없습니다.", parse_mode="html")
    else:
        await bot_client.send_message(MY_CHAT_ID, f"📋 <b>{today_str} 공시 일일 요약</b>\n총 <b>{total}건</b> 수집\n{'─'*28}", parse_mode="html")
        for cat_key, cat in CATEGORIES.items():
            items = buffer.get(cat_key, [])
            if items:
                msg_text = f"{cat['label']} <b>({len(items)}건)</b>\n\n" + "\n\n".join(f"• {clean_text(t)}" for t in items)
            else:
                msg_text = f"{cat['label']}\n없음"
            await bot_client.send_message(MY_CHAT_ID, msg_text, parse_mode="html", link_preview=False)
            await asyncio.sleep(0.5)

    await user_client.disconnect()
    await bot_client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
