import requests
import os
from datetime import datetime

API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def get_data(operation):
    today = datetime.now().strftime('%Y%m%d')
    url = f"http://apis.data.go.kr/1230000/BidPublicInfoService05/{operation}"
    
    params = {
        'serviceKey': API_KEY,
        'type': 'json',
        'numOfRows': '10',
        'inqryDiv': '1',
        'inqryBgnDt': today + "0000",
        'inqryEndDt': today + "2359"
    }

    try:
        # 인증키를 URL에 직접 붙여서 보내는 가장 원시적이고 확실한 방법으로 시도
        full_url = f"{url}?serviceKey={API_KEY}&type=json&numOfRows=10&inqryDiv=1&inqryBgnDt={today}0000&inqryEndDt={today}2359"
        res = requests.get(full_url, timeout=30)
        
        # 만약 결과가 정상이 아니면 상태 코드와 내용을 텔레그램으로 전송
        if res.status_code != 200:
            return f"❌ 서버 응답 실패 (코드: {res.status_code})"
        
        if not res.text.strip():
            return "❌ 서버에서 빈 내용을 보냈습니다 (인증키 미등록 의심)"
            
        # 데이터가 있으면 일단 성공으로 간주하고 리턴
        return "SUCCESS"
        
    except Exception as e:
        return f"❌ 연결 자체 실패: {str(e)}"

def main():
    send_telegram("🚀 디버깅 시작...")
    
    # 두 가지 서비스 중 하나라도 찔러봅니다.
    status = get_data("getBidPblancListInfoThng")
    
    if status == "SUCCESS":
        send_telegram("✅ 조달청 서버 연결 성공! 이제 공고가 올라오면 알림이 갈 겁니다.")
    else:
        send_telegram(f"결과: {status}\n\n💡 팁: 인증키를 '디코딩' 키로 넣으셨나요? 만약 그렇다면 1~2시간 뒤에 다시 해보세요.")

if __name__ == "__main__":
    main()
