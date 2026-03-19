import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 인증 정보
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 2. 키워드
KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    all_items = []
    now = datetime.utcnow() + timedelta(hours=9)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d') + "0000"
    end_date = now.strftime('%Y%m%d') + "2359"
    
    for page in range(1, 11):
        url = f"http://apis.data.go.kr/1230000/ad/BidPublicInfoService/{operation}"
        params = {
            'serviceKey': API_KEY, 'type': 'json', 'numOfRows': '999',
            'pageNo': str(page), 'inqryDiv': '1', 
            'inqryBgnDt': start_date, 'inqryEndDt': end_date
        }
        try:
            res = requests.get(url, params=params, timeout=30)
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if not items: break
            if isinstance(items, dict): items = [items]
            all_items.extend(items)
            if len(items) < 999: break
        except:
            break
    return all_items

def main():
    # 물품과 공사만 딱 뒤집니다.
    search_targets = {
        "물품": "getBidPblancListInfoThng",
        "공사": "getBidPblancListInfoCnstwk"
    }
    
    found = []
    seen_ids = set()
    total_count = 0
    
    for cat_name, operation in search_targets.items():
        items = get_bid_data(operation)
        total_count += len(items)
        
        for item in items:
            title = item.get('bidNtceNm', '')
            bid_no = item.get('bidNtceNo', '')
            
            if title and any(key in title for key in KEYWORDS):
                if bid_no not in seen_ids:
                    # 지역 대신 '기관명'을 강조합니다. (이게 훨씬 정확합니다)
                    buyer = item.get('ntceInsttNm') or "기관명없음"
                    
                    # 날짜 정보
                    pub_date = item.get('ntcePblshDt') or item.get('bidNtceDt') or "날짜미상"
                    end_date = item.get('bidClseDt') or "마감미상"
                    link = item.get('bidNtceDtlUrl', '#')

                    # 깔끔하게 정리된 메시지
                    msg_unit = (
                        f"📍 [{cat_name}] {title}\n"
                        f"🏢 기관: {buyer}\n"
                        f"📅 게시: {pub_date}\n"
                        f"⏳ 마감: {end_date}\n"
                        f"🔗 {link}"
                    )
                    found.append(msg_unit)
                    seen_ids.add(bid_no)

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        message = f"✅ {now_str} 창호/유리 알림\n(3일간 {total_count}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        message = f"🔍 {now_str} 확인 완료\n새로운 공고가 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
