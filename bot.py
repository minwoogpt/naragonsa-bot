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
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d') + "0000"
    end_date = now.strftime('%Y%m%d') + "2359"
    
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
            
            if not items: break
            if isinstance(items, dict): items = [items]
            all_items.extend(items)
            if len(items) < 999: break
        except:
            break
            
    return all_items

def main():
    goods_list = get_bid_data("getBidPblancListInfoThng")
    const_list = get_bid_data("getBidPblancListInfoCnstwk")
    
    all_items = goods_list + const_list
    found = []
    seen_ids = set()
    
    for item in all_items:
        title = item.get('bidNtceNm', '')
        bid_no = item.get('bidNtceNo', '')
        
        # [수정 핵심] 날짜 정보 - 여러 항목을 꼼꼼히 체크
        pub_date = item.get('ntcePblshDt') or item.get('bidNtceDt') or "게시일 확인불가"
        end_date = item.get('bidClseDt') or "마감정보없음"
        
        # [수정 핵심] 지역 정보 - 조달청 API의 여러 지역 필드를 모두 확인
        # 1. prtcptPsblRgnNm (참가가능지역명) -> 웹의 '참가가능지역'과 일치함
        # 2. rgstRtstrctNm (등록제한명)
        region = item.get('prtcptPsblRgnNm') or item.get('rgstRtstrctNm') or "제한없음(전국)"
        
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                
                msg_unit = (
                    f"📍 {title}\n"
                    f"🌍 지역: {region}\n"
                    f"📅 게시: {pub_date}\n"
                    f"⏳ 마감: {end_date}\n"
                    f"🔗 {link}"
                )
                found.append(msg_unit)
                seen_ids.add(bid_no)

    now_str = (datetime.utcnow() + timedelta(hours=9)).strftime('%Y-%m-%d %H:%M')
    
    if found:
        message = f"✅ {now_str} 창호/유리 맞춤 알림\n(전체 {len(all_items)}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        message = f"🔍 {now_str} 확인 완료\n최근 3일 공고 중 일치 건이 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
