import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 인증 정보
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 2. 키워드 (사진의 '유리' 포함)
KEYWORDS = ["창호", "유리", "샷시", "창문", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_bid_data(operation):
    now = datetime.utcnow() + timedelta(hours=9)
    # 3일치 검색 (16, 17, 18일)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d')
    end_date = now.strftime('%Y%m%d')
    
    # [중요] 찬우님 사진에 있는 주소로 정확히 수정 (05 삭제)
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService/{operation}"
    
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
        
        # 만약 조달청이 이상한 에러 페이지를 보냈을 경우 확인용
        if res.status_code != 200:
            return f"SERVER_ERROR:{res.status_code}"

        # JSON 데이터 분석
        try:
            data = res.json()
            header = data.get('response', {}).get('header', {})
            if header.get('resultCode') != '00':
                return f"API_MSG:{header.get('resultMsg')}"
                
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # JSON이 아닐 경우 XML로 한 번 더 시도
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
            
    except Exception as e:
        return f"SYSTEM_ERROR:{str(e)}"

def main():
    # 찬우님이 말씀하신 물품과 공사만 딱 뒤집니다.
    goods_res = get_bid_data("getBidPblancListInfoThng")
    const_res = get_bid_data("getBidPblancListInfoCnstwk")
    
    all_items = []
    log_msg = ""

    # 결과 분석
    for name, res in [("물품", goods_res), ("공사", const_res)]:
        if isinstance(res, list):
            all_items.extend(res)
            log_msg += f"{name}:{len(res)}건 "
        else:
            log_msg += f"{name}:오류({res}) "

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

    today_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d')
    
    if found:
        message = f"✅ {today_str} 창호/유리 알림 ({len(found)}건)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 0건일 때 왜 0건인지 상세하게 보고
        message = f"🔍 {today_str} 업무 보고\n\n총 {len(all_items)}건의 전체 공고를 읽었으나 키워드 일치 건이 없습니다.\n상태: {log_msg}"
        send_telegram(message)

if __name__ == "__main__":
    main()
