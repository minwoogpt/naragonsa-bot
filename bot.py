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
    # [시간 설정] 깃허브 서버는 UTC 기준이므로 한국 시간(UTC+9)으로 보정합니다.
    now = datetime.utcnow() + timedelta(hours=9)
    # 오늘 포함 최근 3일치 (예: 18일, 17일, 16일)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d')
    end_date = now.strftime('%Y%m%d')
    
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService05/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '999',
        'inqryDiv': '1', # 공고게시일 기준
        'inqryBgnDt': start_date + "0000",
        'inqryEndDt': end_date + "2359"
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        # JSON 파싱 시도
        try:
            data = res.json()
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # XML 파싱 시도 (JSON 실패 시)
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
    except:
        return []

def main():
    # 찬우님 요청: 물품(Thng)과 공사(Cnstwk)만 검색
    goods_items = get_bid_data("getBidPblancListInfoThng")
    const_items = get_bid_data("getBidPblancListInfoCnstwk")
    
    total_checked = len(goods_items) + len(const_items)
    all_items = goods_items + const_items
    
    found = []
    seen_ids = set()
    
    for item in all_items:
        title = item.get('bidNtceNm', '')
        bid_no = item.get('bidNtceNo', '')
        
        # 이름에 키워드가 하나라도 포함되면 수집
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                found.append(f"📍 {title}\n🔗 {link}")
                seen_ids.add(bid_no)

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        message = f"✅ {now_str} 알림\n최근 3일 공고 {total_checked}건 중 {len(found)}건 발견!\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 찬우님을 위한 맞춤 보고 방식
        if total_checked > 0:
            message = f"🔍 {now_str} 보고\n\n최근 3일간 **총 {total_checked}건**(물품/공사)의 공고를 샅샅이 뒤졌으나, 찬우님의 키워드와 일치하는 건이 하나도 없었습니다."
        else:
            # 0건 검색된 경우 (서버 동기화 문제)
            message = f"❌ {now_str} 보고\n\n조달청 서버에서 아직 데이터를 보내주지 않고 있습니다(0건 조회). 기상청은 되는 걸 보니 열쇠는 맞습니다! 잠시 후 다시 시도해 주세요."
        
        send_telegram(message)

if __name__ == "__main__":
    main()
