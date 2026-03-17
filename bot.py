import requests
import os
from datetime import datetime
import xml.etree.ElementTree as ET

API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

KEYWORDS = ["창호", "유리", "금속제창", "샷시", "창틀"]

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_data(operation):
    today = datetime.now().strftime('%Y%m%d')
    # 혹시 에러가 나면 05를 지운 BidPublicInfoService 로도 시도해봐야 합니다.
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService05/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '500',
        'inqryDiv': '1',
        'inqryBgnDt': today + "0000",
        'inqryEndDt': today + "2359"
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
            # XML 파싱 시도
            root = ET.fromstring(res.text)
            items = []
            for item_node in root.findall('.//item'):
                item_dict = {child.tag: child.text for child in item_node}
                items.append(item_dict)
            return items
    except Exception as e:
        return f"ERROR: {str(e)}"

def main():
    # 1. 시작 알림 (이게 오면 깃허브-텔레그램 연결은 성공!)
    send_telegram("🔍 나라장터에서 창호/유리 공고를 확인하는 중입니다...")

    results_thng = get_data("getBidPblancListInfoThng")
    results_cnst = get_data("getBidPblancListInfoCnstwk")
    
    # 에러 체크
    if isinstance(results_thng, str) and "ERROR" in results_thng:
        send_telegram(f"❌ API 연결 오류: {results_thng}")
        return

    all_results = results_thng + results_cnst
    found = []
    seen_ids = set()
    
    for item in all_results:
        title = item.get('bidNtceNm', '')
        bid_no = item.get('bidNtceNo', '')
        if title and any(key in title for key in KEYWORDS):
            if bid_no not in seen_ids:
                link = item.get('bidNtceDtlUrl', '#')
                found.append(f"📍 {title}\n🔗 {link}")
                seen_ids.add(bid_no)

    today_str = datetime.now().strftime('%Y-%m-%d')
    if found:
        message = f"📅 {today_str} 검색 결과 ({len(found)}건)\n\n" + "\n\n".join(found)
        send_telegram(message)
    else:
        # 공고가 없어도 결과를 알려줌
        send_telegram(f"📅 {today_str} 확인 결과, 새로 올라온 공고가 0건입니다.")

if __name__ == "__main__":
    main()
