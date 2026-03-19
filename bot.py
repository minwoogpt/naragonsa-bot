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
    # 넉넉하게 최근 3일치 (17, 18, 19일)
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
    # 찬우님이 확인하신 '공사'와 '물품' 위주로 검색
    categories = {
        "공사": "getBidPblancListInfoCnstwk",
        "물품": "getBidPblancListInfoThng",
        "용역": "getBidPblancListInfoServc"
    }
    
    found = []
    seen_ids = set()
    total_searched = 0
    
    for cat_name, op in categories.items():
        items = get_bid_data(op)
        total_searched += len(items)
        
        for item in items:
            title = item.get('bidNtceNm', '') # 공사명
            bid_no = item.get('bidNtceNo', '') # 입찰공고번호
            
            # 키워드 매칭 (창호, 유리 등)
            if title and any(key in title for key in KEYWORDS):
                if bid_no not in seen_ids:
                    # [지역 정보 정밀 타격] 
                    # 공사는 rgstRtstrctNm, 물품은 prtcptPsblRgnNm에 주로 들어있음
                    region = item.get('rgstRtstrctNm') or item.get('prtcptPsblRgnNm') or item.get('limitRgnNm') or "지역제한없음"
                    buyer = item.get('ntceInsttNm') or "기관미상" # 대구교육대학교 등
                    
                    # 날짜 정보
                    pub_date = item.get('ntcePblshDt') or item.get('bidNtceDt') or "게시일미상"
                    end_date = item.get('bidClseDt') or "마감미상"
                    link = item.get('bidNtceDtlUrl', '#')

                    # 텔레그램 메시지 구성
                    msg_unit = (
                        f"📍 [{cat_name}] {title}\n"
                        f"🌍 지역: {region} ({buyer})\n"
                        f"📅 게시: {pub_date}\n"
                        f"⏳ 마감: {end_date}\n"
                        f"🔗 {link}"
                    )
                    found.append(msg_unit)
                    seen_ids.add(bid_no)

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        # 알림 전송
        message = f"✅ {now_str} 통합 알림\n(최근 3일 {total_searched}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        message = f"🔍 {now_str} 확인 완료\n조건에 맞는 공고가 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
