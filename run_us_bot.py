import os
import requests
import asyncio
from datetime import datetime, timedelta, timezone
from telethon import TelegramClient

# GitHub Secrets 설정값
API_ID         = int(os.environ["TG_API_ID"])
API_HASH       = os.environ["TG_API_HASH"]
BOT_TOKEN      = os.environ["TELEGRAM_BOT_TOKEN"]
MY_CHAT_ID     = int(os.environ["TELEGRAM_CHAT_ID"])
FMP_API_KEY    = os.environ["FMP_API_KEY"]

# 관심 종목 리스트 (대표님이 직접 관리하시는 종목들)
TARGET_SYMBOLS = ["TSLA", "PLTR", "NVDA", "MSFT", "AAPL"]

# 실적 관련 키워드
EARNINGS_KEYWORDS = ["earning", "financial", "result", "quarter"]

async def main():
    # 1. 시간 설정 (한국 시간 기준 지난 24시간)
    KST = timezone(timedelta(hours=9))
    now_kst = datetime.now(KST)
    since_kst = now_kst - timedelta(hours=24)
    
    url = f"https://financialmodelingprep.com/api/v3/rss_feed?limit=500&apikey={FMP_API_KEY}"
    
    try:
        response = requests.get(url).json()
        if not isinstance(response, list): return
    except Exception as e:
        print(f"API 호출 에러: {e}")
        return

    bot = TelegramClient('bot_session_us_daily', API_ID, API_HASH)
    await bot.start(bot_token=BOT_TOKEN)

    found_msgs = []
    
    for item in response:
        if not isinstance(item, dict): continue

        # 관심 종목 필터링
        symbol = item.get('symbol', '')
        if symbol not in TARGET_SYMBOLS: continue

        # 시간 필터링 (공시 시간이 지난 24시간 이내인지 확인)
        # FMP 날짜 형식: "2024-04-12 12:51:00"
        filling_date_str = item.get('fillingDate', '')
        try:
            # FMP 시간은 기본적으로 동부 표준시(EST) 기준이거나 UTC에 가깝습니다. 
            # 여기서는 단순히 시간 순서대로 500개를 보되, '최근 24시간' 내의 것만 담습니다.
            filling_date = datetime.strptime(filling_date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            if filling_date < (datetime.now(timezone.utc) - timedelta(hours=24)):
                continue # 24시간보다 더 오래된 공시는 무시
        except:
            pass

        form_type = item.get('type', '')
        title = item.get('fillingVar', '').lower()

        is_earnings = False
        if form_type in ["10-Q", "10-K"]:
            is_earnings = True
        elif form_type == "8-K" and any(kw in title for kw in EARNINGS_KEYWORDS):
            is_earnings = True

        if is_earnings:
            original_title = item.get('fillingVar', '공시 내용 확인')
            link = item.get('url', '')
            
            msg = (
                f"🇺🇸 **{symbol} 실적 소식 ({form_type})**\n"
                f"⏰ {filling_date_str}\n"
                f"📝 {original_title}\n"
                f"🔗 [원문]({link}) | [대본](https://seekingalpha.com/symbol/{symbol}/earnings/transcripts)\n"
                f"{'─'*20}"
            )
            found_msgs.append(msg)

    # 2. 메시지 전송
    today_str = now_kst.strftime("%m/%d")
    header = f"📅 **{today_str} 미국 우량주 실적 요약**\n"
    
    if found_msgs:
        # 메시지가 너무 길어지지 않게 나누어 전송
        await bot.send_message(MY_CHAT_ID, header + f"총 {len(found_msgs)}건의 소식이 있습니다.")
        for i in range(0, len(found_msgs), 5): # 5개씩 묶어서 전송
            chunk = "\n\n".join(found_msgs[i:i+5])
            await bot.send_message(MY_CHAT_ID, chunk, link_preview=False)
            await asyncio.sleep(1)
    else:
        await bot.send_message(MY_CHAT_ID, header + "지난 24시간 동안 업데이트된 실적 공시가 없습니다.")

    await bot.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
