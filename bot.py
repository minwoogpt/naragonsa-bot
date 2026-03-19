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

# 3. [핵심] 찬우님이 보내주신 지역코드 매핑 리스트
REGION_MAP = {
    '11': '서울', '26': '부산', '27': '대구', '28': '인천', '29': '광주',
    '30': '대전', '31': '울산', '36': '세종', '41': '경기', '42': '강원',
    '43': '충북', '44': '충남', '45': '전북', '46': '전남', '47': '경북',
    '48': '경남', '50': '제주', '00': '전국', '99': '기타'
}

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
    # 용역은 빼고 '공사'와 '물품'만 뒤집니다.
    categories = {
        "공사": "getBidPblancListInfoCnstwk",
        "물품": "getBidPblancListInfoThng"
    }
    
    found = []
    seen_ids = set()
    total_count = 0
    
    for cat_name, op in categories.items():
        items = get_bid_data(op)
        total_count += len(items)
        
        for item in items:
            title = item.get('bidNtceNm', '')
            bid_no = item.get('bidNtceNo', '')
            
            if title and any(key in title for key in KEYWORDS):
                if bid_no not in seen_ids:
                    # [지역 정보 해독] 
                    # 1. 글자로 된 지역 정보 먼저 확인
                    region_nm = item.get('prtcptPsblRgnNm') or item.get('rgstRtstrctNm')
                    
                    # 2. 글자가 없으면 찬우님이 주신 '지역코드' 확인
                    region_cd = item.get('prtcptLmtRgnCd')
                    
                    # 3. 코드가 있으면 이름으로 변환, 둘 다 없으면 기관명이라도 노출
                    region_final = region_nm or REGION_MAP.get(region_cd) or "지역정보없음"
                    buyer = item.get('ntceInsttNm') or "기관미상"
                    
                    pub_date = item.get('ntcePblshDt') or item.get('bidNtceDt') or "날짜미상"
                    end_date = item.get('bidClseDt') or "마감미상"
                    link = item.get('bidNtceDtlUrl', '#')

                    msg_unit = (
                        f"📍 [{cat_name}] {title}\n"
                        f"🌍 지역: {region_final} ({buyer})\n"
                        f"📅 게시: {pub_date}\n"
                        f"⏳ 마감: {end_date}\n"
                        f"🔗 {link}"
                    )
                    found.append(msg_unit)
                    seen_ids.add(bid_no)

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        message = f"✅ {now_str} 지역맞춤 알림\n(3일간 {total_count}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        message = f"🔍 {now_str} 확인 완료\n새로운 공고가 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
