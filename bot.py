import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 인증 정보
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 2. 찬우님 맞춤 키워드
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
    
    # 데이터가 없을 때까지 끝까지 뒤집니다.
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
            
            if not items:
                break
            
            if isinstance(items, dict): items = [items]
            all_items.extend(items)
            
            if len(items) < 999:
                break
        except:
            break
            
    return all_items

def main():
    # 물품과 공사 탭만 집중적으로 검색
    goods_list = get_bid_data("getBidPblancListInfoThng")
    const_list = get_bid_data("getBidPblancListInfoCnstwk")
    
    all_items = goods_list + const_list
    found = []
    seen_ids = set()
    
    for item in all_items:
        title = item.get('bidNtceNm', '') # 공사명(공고명)
        bid_no = item.get('bidNtceNo', '')
        # 게시 일시 (예: 2026-03-19 13:46)
        pub_date = item.get('ntcePblshDt', '날짜 정보 없음') 
        
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                # 찬우님이 요청하신 형식: 제목 + 게시날짜 + 링크
                found.append(f"📍 {title}\n📅 게시: {pub_date}\n🔗 {link}")
                seen_ids.add(bid_no)

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        message = f"✅ {now_str} 창호/유리 맞춤 알림\n(전체 {len(all_items)}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
    else:
        message = f"🔍 {now_str} 확인 완료\n최근 3일 전체 {len(all_items)}건 중 일치하는 건이 없습니다."
        
    send_telegram(message)

if __name__ == "__main__":
    main()
