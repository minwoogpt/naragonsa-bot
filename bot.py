import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def call_api(service_name, operation):
    now = datetime.now()
    # 어제부터 오늘까지의 데이터를 넉넉히 잡습니다 (동기화 지연 대비)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d')
    end_date = now.strftime('%Y%m%d')
    
    url = f"http://apis.data.go.kr/1230000/{service_name}/{operation}"
    
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
        # 1. JSON 파싱
        try:
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # 2. XML 파싱
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
    except:
        return []

def main():
    # 주소 두 종류를 다 준비합니다.
    services = ["BidPublicInfoService05", "BidPublicInfoService"]
    operations = ["getBidPblancListInfoThng", "getBidPblancListInfoCnstwk"]
    
    all_items = []
    used_service = ""

    for svc in services:
        current_items = []
        for op in operations:
            current_items += call_api(svc, op)
        
        # 만약 데이터를 하나라도 가져왔다면 그 주소를 사용하고 중단
        if len(current_items) > 0:
            all_items = current_items
            used_service = svc
            break
    
    total_count = len(all_items)
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
        message = f"✅ {today_str} 알림 (통로: {used_service})\n{total_count}건 중 {len(found)}건 발견!\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        if total_count > 0:
            message = f"🔍 {today_str} 보고\n조달청({used_service})에서 **총 {total_count}건**을 읽어왔으나, 찬우님 키워드와 일치하는 건이 없습니다."
        else:
            message = f"❌ {today_str} 경보\n조달청 모든 주소에서 0건이 반환되었습니다. 아직 열쇠가 등록 중이거나 오늘 공고가 정말 없는 상태입니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
