import requests
import os
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

# 1. 인증 정보
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

# 2. 찬우님 키워드
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
    goods_list = get_bid_data("getBidPblancListInfoThng") # 물품
    const_list = get_bid_data("getBidPblancListInfoCnstwk") # 공사
    
    all_items = goods_list + const_list
    found = []
    seen_ids = set()
    
    for item in all_items:
        title = item.get('bidNtceNm', '')
        bid_no = item.get('bidNtceNo', '')
        
        # 1. 날짜 정보
        pub_date = item.get('ntcePblshDt') or item.get('bidNtceDt') or "게시일 확인불가"
        end_date = item.get('bidClseDt') or "마감정보없음"
        
        # 2. 지역 정보 (조달청이 숨겨놓을 수 있는 5가지 칸을 순서대로 다 뒤짐)
        # prtcptPsblRgnNm: 참가가능지역 (가장 유력)
        # rgstRtstrctNm: 등록제한지역 (공사에서 주로 사용)
        # limitRgnNm: 제한지역명 (일부 물품에서 사용)
        # rgnRtstrctNm: 지역제한명
        # dlvryPlace: 인도장소 (최후의 수단으로 어디로 배달하는지 확인)
        region = (
            item.get('prtcptPsblRgnNm') or 
            item.get('rgstRtstrctNm') or 
            item.get('limitRgnNm') or 
            item.get('rgnRtstrctNm') or
            item.get('dlvryPlace') or
            "제한없음(전국)"
        )
        
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
        message = f"✅ {now_str} 창호/유리 맞춤 알림\n(총 {len(all_items)}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        message = f"🔍 {now_str} 확인 완료\n키워드 일치 건이 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
