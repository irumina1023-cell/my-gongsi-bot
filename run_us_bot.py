import os
import requests
import asyncio
from telethon import TelegramClient

# GitHub Secrets 설정값
API_ID         = int(os.environ["TG_API_ID"])
API_HASH       = os.environ["TG_API_HASH"]
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID     = int(os.environ["TELEGRAM_CHAT_ID"])
FMP_API_KEY    = os.environ["FMP_API_KEY"]

# 감시할 주요 서류 종류 (8-K: 주요 뉴스, 4: 내부자 거래)
WATCH_FORMS = ["8-K", "4"]

async def main():
    # 미국 공시 API 호출 (데이터 형식을 안전하게 가져오도록 수정)
    url = f"https://financialmodelingprep.com/api/v3/rss_feed?limit=50&apikey={FMP_API_KEY}"
    
    try:
        response = requests.get(url).json()
        if not isinstance(response, list):
            print("데이터 형식이 올바르지 않습니다.")
            return
    except Exception as e:
        print(f"API 호출 에러: {e}")
        return

    bot = TelegramClient('bot_session_us', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    found_any = False
    for item in response:
        # 데이터가 딕셔너리 형태인지 한 번 더 확인 (에러 방지 핵심!)
        if not isinstance(item, dict):
            continue

        form_type = item.get('type')
        if form_type in WATCH_FORMS:
            found_any = True
            symbol = item.get('symbol', 'N/A')
            filling_date = item.get('fillingDate', 'N/A')
            title = item.get('fillingVar', '공시 내용 확인')
            url = item.get('url', '')

            text = f"🇺🇸 **미국 주식 공시 알림 ({form_type})**\n\n"
            text += f"🏢 **종목**: {symbol}\n"
            text += f"📅 **일시**: {filling_date}\n"
            text += f"📝 **내용**: {title}\n\n"
            text += f"🔗 [공시 원문 보기]({url})"

            await bot.send_message(MY_CHAT_ID, text, link_preview=False)
            await asyncio.sleep(1)

    if not found_any:
        print("최근 감시 대상 공시가 없습니다.")

    await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
