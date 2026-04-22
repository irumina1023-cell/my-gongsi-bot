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

# 💡 실적 관련 키워드 (8-K 수시공시 중 실적발표만 걸러내기 위함)
EARNINGS_KEYWORDS = ["earning", "financial", "result", "quarter"]

async def main():
    # 💡 탐색 범위를 최신 50개 -> 500개로 대폭 늘렸습니다!
    url = f"https://financialmodelingprep.com/api/v3/rss_feed?limit=500&apikey={FMP_API_KEY}"
    
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

    found_msgs = []
    for item in response:
        if not isinstance(item, dict):
            continue

        form_type = item.get('type', '')
        title = item.get('fillingVar', '').lower()

        # 💡 10-Q(분기실적), 10-K(연간실적)는 무조건 수집! 
        # 8-K는 제목에 실적 관련 단어가 있을 때만 수집합니다.
        is_earnings = False
        if form_type in ["10-Q", "10-K"]:
            is_earnings = True
        elif form_type == "8-K" and any(kw in title for kw in EARNINGS_KEYWORDS):
            is_earnings = True

        if is_earnings:
            symbol = item.get('symbol', 'N/A')
            filling_date = item.get('fillingDate', 'N/A')
            original_title = item.get('fillingVar', '공시 내용 확인')
            link = item.get('url', '')

            text = f"🇺🇸 **미국 실적 공시 ({form_type})**\n\n"
            text += f"🏢 **종목**: {symbol}\n"
            text += f"📅 **일시**: {filling_date}\n"
            text += f"📝 **내용**: {original_title}\n"
            text += f"🔗 [원문 보기]({link})"

            found_msgs.append(text)

    if found_msgs:
        # 💡 미국은 공시가 너무 많아서 텔레그램 스팸 차단을 막기 위해 최신 15건만 끊어서 보냅니다.
        await bot.send_message(MY_CHAT_ID, f"🇺🇸 **미국 실적 공시 요약**\n검색된 실적 공시 중 최신 {min(len(found_msgs), 15)}건을 보내드립니다.")
        for msg in found_msgs[:15]:
            await bot.send_message(MY_CHAT_ID, msg, link_preview=False)
            await asyncio.sleep(1) # 과부하 방지
    else:
        await bot.send_message(MY_CHAT_ID, "🇺🇸 최근 수집된 미국 실적 공시가 없습니다.")

    await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
