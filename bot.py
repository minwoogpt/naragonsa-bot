import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 환경 설정 (깃허브 시크릿)
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 2. 찬우님 지정 키워드 (딱 5개)
KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    now = datetime.now()
    # [날짜 설정] 오늘부터 3일 전까지 검색 (확인용)
    start_date = (now - timedelta(days=3)).strftime('%Y%m%d')
    end_date = now.strftime('%Y%m%d')
    
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
        # JSON으로 먼저 시도, 안되면 XML로 파싱
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
    except:
        return []

def main():
    # 3. 딱 '물품'과 '공사'만 검색
    results = get_bid_data("getBidPblancListInfoThng") + get_bid_data("getBidPblancListInfoCnstwk")
    
    found = []
    seen_ids = set() # 중복 제거
    
    for item in results:
        title = item.get('bidNtceNm', '') # 공고명(이름) 가져오기
        bid_no = item.get('bidNtceNo', '')
        
        # 이름(title) 안에 키워드가 있는지 확인
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                found.append(f"📍 {title}\n🔗 {link}")
                seen_ids.add(bid_no)

    today_str = datetime.now().strftime('%Y-%m-%d')
    if found:
        message = f"📅 {today_str} 창호/유리 알림 ({len(found)}건)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 0건일 때도 잘 작동하는지 보고 싶으면 아래 메시지 유지, 아니면 주석처리 하세요.
        send_telegram(f"📅 {today_str} 확인 결과, 최근 3일 내 관련 공고가 없습니다.")

if __name__ == "__main__":
    main()
