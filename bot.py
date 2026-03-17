import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET

# 깃허브 시크릿에서 가져오기
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 찬우님 사업 맞춤 키워드
KEYWORDS = ["창호", "유리", "금속제창", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    today = datetime.now().strftime('%Y%m%d')
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService05/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json', # JSON을 우선 요청
        'numOfRows': '999',
        'inqryDiv': '1', # 공고게시일 기준
        'inqryBgnDt': today + "0000",
        'inqryEndDt': today + "2359"
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        
        # 1. JSON 형식으로 시도
        try:
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # 2. XML 형식으로 시도 (JSON 실패 시)
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
    except Exception as e:
        print(f"Error calling {operation}: {e}")
        return []

def main():
    # 실행 알림 (테스트 성공 확인용)
    # send_telegram("🔍 나라장터 창호/유리 공고 검색을 시작합니다...")

    # 물품조회 + 공사조회 합치기
    all_items = get_bid_data("getBidPblancListInfoThng") + get_bid_data("getBidPblancListInfoCnstwk")
    
    found = []
    seen_ids = set()
    
    for item in all_items:
        title = item.get('bidNtceNm', '')
        bid_no = item.get('bidNtceNo', '')
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                found.append(f"📍 {title}\n🔗 {link}")
                seen_ids.add(bid_no)

    today_str = datetime.now().strftime('%Y-%m-%d')
    if found:
        message = f"📅 {today_str} 창호/유리 입찰 알림\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 공고가 0건일 때 메시지를 받고 싶지 않다면 아래 줄을 주석처리(#) 하세요.
        send_telegram(f"📅 {today_str} 확인 결과, 새로 올라온 창호/유리 공고가 없습니다.")

if __name__ == "__main__":
    main()
