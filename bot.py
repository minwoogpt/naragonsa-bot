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
    # 최근 3일치 (17, 18, 19일)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d') + "0000"
    end_date = now.strftime('%Y%m%d') + "2359"
    
    # 1페이지부터 데이터가 없을 때까지 계속 뒤집니다 (최대 10페이지까지 설정)
    for page in range(1, 11):
        url = f"http://apis.data.go.kr/1230000/ad/BidPublicInfoService/{operation}"
        params = {
            'serviceKey': API_KEY,
            'type': 'json',
            'numOfRows': '999',
            'pageNo': str(page),
            'inqryDiv': '1', 
            'inqryBgnDt': start_date,
            'inqryEndDt': end_date
        }

        try:
            res = requests.get(url, params=params, timeout=30)
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            
            if not items: # 더 이상 가져올 데이터가 없으면 중단
                break
            
            if isinstance(items, dict): items = [items]
            all_items.extend(items)
            
            # 만약 가져온 데이터가 999개보다 적으면 마지막 페이지라는 뜻이므로 중단
            if len(items) < 999:
                break
        except:
            break
            
    return all_items

def main():
    # 물품과 공사만 집중 타격!
    goods_list = get_bid_data("getBidPblancListInfoThng")
    const_list = get_bid_data("getBidPblancListInfoCnstwk")
    
    all_items = goods_list + const_list
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

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        message = f"✅ {now_str} 물품/공사 통합 보고\n(최근 3일 전체 {len(all_items)}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
    else:
        message = f"🔍 {now_str} 확인 완료\n전체 {len(all_items)}건을 중 일치하는 건이 없습니다."
        
    send_telegram(message)

if __name__ == "__main__":
    main()
