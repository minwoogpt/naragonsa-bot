import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 깃허브 시크릿 정보
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 찬우님 맞춤 키워드
KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    # 한국 시간 기준 (UTC+9)
    now = datetime.utcnow() + timedelta(hours=9)
    # 오늘 포함 최근 3일치 검색 (오늘, 어제, 그저께)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d') + "0000"
    end_date = now.strftime('%Y%m%d') + "2359"
    
    # [성공했던 주소] /ad/ 포함
    url = f"http://apis.data.go.kr/1230000/ad/BidPublicInfoService/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '999',
        'pageNo': '1',
        'inqryDiv': '1', 
        'inqryBgnDt': start_date,
        'inqryEndDt': end_date
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        if res.status_code != 200: return []
        
        try:
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # JSON 실패 시 XML 파싱
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
    except:
        return []

def main():
    # 물품과 공사만 검색
    goods_res = get_bid_data("getBidPblancListInfoThng")
    const_res = get_bid_data("getBidPblancListInfoCnstwk")
    
    all_items = goods_res + const_res
    found = []
    seen_ids = set() # 중복 제거용
    
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
        message = f"✅ {now_str} 창호/유리 알림\n(최근 3일 공고 {len(all_items)}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 공고가 없을 때도 보고받고 싶으면 유지, 아니면 주석처리 하세요.
        message = f"🔍 {now_str} 확인 완료\n최근 3일간 {len(all_items)}건의 공고를 뒤졌으나 조건에 맞는 공고가 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
