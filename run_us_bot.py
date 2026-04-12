import os
import requests
import asyncio
from telethon import TelegramClient

# GitHub Secrets에서 가져올 설정값들
API_ID         = int(os.environ["TG_API_ID"])
API_HASH       = os.environ["TG_API_HASH"]
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID     = int(os.environ["TELEGRAM_CHAT_ID"])
FMP_API_KEY    = os.environ["FMP_API_KEY"]

# 감시할 주요 서류 종류 (8-K: 주요 뉴스, 4: 내부자 거래)
WATCH_FORMS = ["8-K", "4"]

async def main():
    # 미국 공시 API 호출 (최신 50건)
    url = f"https://financialmodelingprep.com/api/v3/rss_feed?limit=50&apikey={FMP_API_KEY}"
    
    try:
        response = requests.get(url).json()
    except Exception as e:
        print(f"API 호출 에러: {e}")
        return

    bot = TelegramClient('bot_session', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    found_any = False
    for item in response:
        # 설정한 서류 종류(8-K, 4)만 골라냅니다
        if item.get('type') in WATCH_FORMS:
            found_any = True
            symbol = item.get('symbol', 'N/A')
            form_type = item.get('type', 'N/A')
            filling_date = item.get('fillingDate', '')
            title = item.get('fillingVar', '공시 내용 확인')
            url = item.get('url', '')

            text = f"🇺🇸 **미국 주식 공시 알림 ({form_type})**\n\n"
            text += f"🏢 **종목**: {symbol}\n"
            text += f"📅 **일시**: {filling_date}\n"
            text += f"📝 **내용**: {title}\n\n"
            text += f"🔗 [공시 원문 보기]({url})"

            # 텔레그램으로 전송
            await bot.send_message(MY_CHAT_ID, text, link_preview=False)
            await asyncio.sleep(1) # 메시지 과부하 방지

    if not found_any:
        print("최근 8-K 또는 4번 공시가 없습니다.")

    await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
