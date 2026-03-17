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
    now = datetime.utcnow() + timedelta(hours=9)
    # 3일치 검색 (문서 규격에 맞게 12자리 YYYYMMDDHH24MI 형식으로 설정)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d') + "0000"
    end_date = now.strftime('%Y%m%d') + "2359"
    
    # [핵심 수정] 문서에 명시된 /ad/ 가 포함된 주소 사용
    url = f"http://apis.data.go.kr/1230000/ad/BidPublicInfoService/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '999',
        'pageNo': '1',
        'inqryDiv': '1', # 1: 등록일시 기준
        'inqryBgnDt': start_date,
        'inqryEndDt': end_date
    }

    try:
        # 조달청 서버는 파라미터 순서나 형식에 예민하므로 주소를 아주 깔끔하게 보냅니다.
        res = requests.get(url, params=params, timeout=30)
        
        if res.status_code == 500:
            return "ERR_500_ADDRESS_ISSUE"
        elif res.status_code != 200:
            return f"ERR_HTTP_{res.status_code}"

        # 데이터 분석
        try:
            data = res.json()
            header = data.get('response', {}).get('header', {})
            if header.get('resultCode') != '00':
                return f"ERR_API_{header.get('resultCode')}"
                
            items = data.get('response', {}).get('body', {}).get('items', [])
            if isinstance(items, dict): items = [items]
            return items
        except:
            # XML 파싱 시도
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
            
    except Exception as e:
        return f"ERR_SYS_{str(e)}"

def main():
    # 찬우님 요청: 물품(Thng)과 공사(Cnstwk)만 딱!
    goods_res = get_bid_data("getBidPblancListInfoThng")
    const_res = get_bid_data("getBidPblancListInfoCnstwk")
    
    all_items = []
    status_report = ""

    for name, res in [("물품", goods_res), ("공사", const_res)]:
        if isinstance(res, list):
            all_items.extend(res)
            status_report += f"{name}:{len(res)}건 "
        else:
            status_report += f"{name}:{res} "

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
        message = f"✅ {now_str} 창호/유리 알림\n총 {len(all_items)}건 중 {len(found)}건 발견!\n\n" + "\n\n".join(found)
    else:
        message = f"🔍 {now_str} 업무 보고\n\n최근 3일 공고 {len(all_items)}건을 뒤졌으나 키워드 일치 건이 없습니다.\n(상태: {status_report})"
        
    send_telegram(message)

if __name__ == "__main__":
    main()
