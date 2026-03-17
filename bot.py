import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 환경 설정 (깃허브 시크릿)
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 2. 찬우님 지정 키워드
KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    now = datetime.now()
    # 최근 3일치를 뒤져서 확실하게 체크합니다.
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
    # 물품과 공사 데이터를 가져옵니다.
    goods_results = get_bid_data("getBidPblancListInfoThng")
    const_results = get_bid_data("getBidPblancListInfoCnstwk")
    
    # [열일 보고용] 총 몇 개를 가져왔는지 합산
    total_raw_count = len(goods_results) + len(const_results)
    
    all_results = goods_results + const_results
    found = []
    seen_ids = set()
    
    for item in all_results:
        title = item.get('bidNtceNm', '')
        bid_no = item.get('bidNtceNo', '')
        
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                found.append(f"📍 {title}\n🔗 {link}")
                seen_ids.add(bid_no)

    today_str = datetime.now().strftime('%Y-%m-%d')
    
    if found:
        # 공고를 찾았을 때
        message = f"✅ {today_str} 창호/유리 알림\n(총 {total_raw_count}건을 뒤져서 {len(found)}건 발견!)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 공고가 하나도 없을 때 (찬우님이 요청하신 보고 방식)
        message = f"🔍 {today_str} 업무 보고\n\n최근 3일간 올라온 **총 {total_raw_count}건**의 공고를 샅샅이 뒤졌으나, 찬우님의 키워드('창호', '유리' 등)와 일치하는 건이 하나도 없었습니다. 조용하네요!"
        send_telegram(message)

if __name__ == "__main__":
    main()
