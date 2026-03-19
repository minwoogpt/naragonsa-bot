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

# 3. 찬우님이 보내주신 지역코드 매핑 리스트
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
    # 넉넉하게 최근 3일치 (오늘, 어제, 그저께)
    start_date = (now - timedelta(days=2)).strftime('%Y%m%d') + "0000"
    end_date = now.strftime('%Y%m%d') + "2359"
    
    # 1페이지부터 데이터가 없을 때까지 최대 10페이지까지 훑습니다.
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
            
            # 데이터가 1건일 때를 대비해 리스트로 통일
            if isinstance(items, dict): items = [items]
            all_items.extend(items)
            
            # 가져온 데이터가 999개보다 적으면 마지막 페이지이므로 중단
            if len(items) < 999:
                break
        except:
            # JSON 에러나 통신 에러 시 중단
            break
            
    return all_items

def main():
    # 찬우님 요청: 용역은 빼고 '공사'와 '물품'만 집중 타격!
    goods_list = get_bid_data("getBidPblancListInfoThng") # 물품
    const_list = get_bid_data("getBidPblancListInfoCnstwk") # 공사
    
    all_items = goods_list + const_list
    found = []
    seen_ids = set() # 중복 제거용
    
    for item in all_items:
        title = item.get('bidNtceNm', '') # 공고명
        bid_no = item.get('bidNtceNo', '') # 입찰공고번호
        
        # 키워드 매칭
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                # 1. 날짜 정보
                pub_date = item.get('ntcePblshDt') or item.get('bidNtceDt') or "게시일 확인불가"
                end_date = item.get('bidClseDt') or "마감정보없음"
                
                # 2. [초강력 지역 정보 추출] - 조달청이 숨겨놓을 수 있는 5가지 칸을 다 털어버립니다.
                # prtcptPsblRgnNm: 참가가능지역
                # rgstRtstrctNm: 등록제한지역
                # limitRgnNm: 제한지역명
                # region_cd_translated: 찬우님이 주신 지역코드 번역값
                
                region_nm = item.get('prtcptPsblRgnNm') or item.get('rgstRtstrctNm') or item.get('limitRgnNm')
                region_cd = item.get('prtcptLmtRgnCd')
                
                # 글자로 된 지역 정보가 없으면, 찬우님이 주신 코드를 번역해서 사용합니다.
                region_final = region_nm or REGION_MAP.get(region_cd) or "제한없음(전국)"
                buyer = item.get('ntceInsttNm') or "기관미상" # 김해시, 부산광역시 교육청 등

                link = item.get('bidNtceDtlUrl', '#')

                # 찬우님 커스텀 형식: 제목 + 지역 + 기관 + 날짜 + 링크
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
        # 알림 전송
        message = f"✅ {now_str} 지역맞춤 알림\n(최근 3일 공고 {len(all_items)}건 중 {len(found)}건 발견)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 조건에 맞는 공고가 없을 때
        message = f"🔍 {now_str} 확인 완료\n최근 3일 공고를 다 뒤졌으나 조건에 맞는 공고가 없습니다."
        send_telegram(message)

if __name__ == "__main__":
    main()
