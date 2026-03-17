import requests
import os
from datetime import datetime, timedelta # timedelta 추가
import xml.etree.ElementTree as ET

API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    # [수정] 오늘부터 3일 전까지의 공고를 모두 훑습니다.
    now = datetime.now()
    start_date = (now - timedelta(days=3)).strftime('%Y%m%d') # 3일 전
    end_date = now.strftime('%Y%m%d') # 오늘
    
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService05/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '999',
        'inqryDiv': '1', 
        'inqryBgnDt': start_date + "0000",
        'inqryEndDt': end_date + "2359"
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        try:
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
    except Exception:
        return []

def main():
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

    if found:
        # 중복 공고 제외하고 최신순으로 보여줌
        message = f"📅 최근 3일간 창호/유리 검색 결과 ({len(found)}건)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        send_telegram(f"📅 확인 결과, 최근 3일 내 새로 올라온 관련 공고가 없습니다.")

if __name__ == "__main__":
    main()
