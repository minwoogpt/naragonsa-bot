import requests
import os
from datetime import datetime

# 깃허브 시크릿에서 열쇠 가져오기
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 찬우님 검색 키워드
KEYWORDS = ["창호", "유리", "금속제창", "샷시", "창틀"]

def check_bid():
    today = datetime.now().strftime('%Y%m%d')
    url = "http://apis.data.go.kr/1230000/BidPublicInfoService05/getBidPblancListInfoSearch"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '500',
        'inqryDiv': '1',
        'inqryBgnDt': today + "0000",
        'inqryEndDt': today + "2359"
    }

    try:
        res = requests.get(url, params=params)
        data = res.json()
        
        found = []
        if 'body' in data['response'] and 'items' in data['response']['body']:
            items = data['response']['body']['items']
            if isinstance(items, dict): items = [items] 
            
            for item in items:
                title = item['bidNtceNm']
                if any(key in title for key in KEYWORDS):
                    link = item['bidNtceDtlUrl']
                    found.append(f"📍 {title}\n🔗 {link}")

        if found:
            send_msg(f"📅 {today} 창호/유리 결과\n\n" + "\n\n".join(found))
        else:
            send_msg(f"📅 {today} 새로 올라온 관련 공고가 없습니다.")
            
    except Exception as e:
        send_msg(f"❌ 에러 발생: {str(e)}")

def send_msg(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text})

if __name__ == "__main__":
    check_bid()
