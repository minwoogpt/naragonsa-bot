import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET

# 깃허브 시크릿에서 가져오기
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

KEYWORDS = ["창호", "유리", "금속제창", "샷시", "창틀"]

def get_data(operation):
    today = datetime.now().strftime('%Y%m%d')
    # 문서에 명시된 서비스 명칭에 따라 05가 붙거나 안 붙을 수 있습니다. 
    # 에러가 계속되면 BidPublicInfoService05로 수정해보세요.
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService05/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json', # JSON을 시도하지만 안 되면 XML로 처리함
        'numOfRows': '500',
        'inqryDiv': '1',
        'inqryBgnDt': today + "0000",
        'inqryEndDt': today + "2359"
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        # 1. JSON 시도
        try:
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # 2. JSON 실패 시 XML로 직접 파싱 (가장 확실한 방법)
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
    # 물품(Thng)과 공사(Cnstwk) 두 군데서 검색
    results = get_data("getBidPblancListInfoThng") + get_data("getBidPblancListInfoCnstwk")
    
    found = []
    seen_ids = set() # 중복 제거
    
    for item in results:
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
        # 공고가 없을 때도 메시지를 받고 싶다면 아래 주석 해제
        # send_telegram(f"📅 {today_str} 새로 올라온 공고가 없습니다.")
        pass

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    # 메시지가 너무 길면 텔레그램에서 거부할 수 있으므로 자름
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

if __name__ == "__main__":
    main()
