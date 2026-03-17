import requests
import os
from datetime import datetime

API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def test_busan_api():
    # 부산 대기오염 예경보 발령 현황 조회 URL
    url = "http://apis.data.go.kr/6260000/AirQualityInfoService/getAirQualityForecastInfo"
    
    params = {
        'serviceKey': API_KEY, # 아까 그 똑같은 열쇠를 씁니다
        'type': 'json',
        'numOfRows': '10',
        'pageNo': '1'
    }

    try:
        # 1. 일단 찔러보기
        res = requests.get(url, params=params, timeout=30)
        
        # 2. 상태 확인
        if res.status_code == 200:
            try:
                data = res.json()
                # 데이터가 정상적으로 들어있는지 확인
                if 'getAirQualityForecastInfo' in data:
                    return "✅ 성공! 열쇠(API 키)가 아주 잘 작동합니다. 조달청만 기다리면 되겠네요!"
                else:
                    return f"❓ 연결은 됐는데 내용이 좀 이상해요: {res.text[:100]}"
            except:
                return f"❓ 데이터 형식 에러 (인증키 등록 대기 중일 수 있음): {res.text[:100]}"
        else:
            return f"❌ 서버 응답 실패 (코드: {res.status_code})"
            
    except Exception as e:
        return f"❌ 연결 실패: {str(e)}"

def main():
    send_telegram("🧪 API 키 효능 테스트 시작 (부산 대기오염 데이터)...")
    result = test_busan_api()
    send_telegram(result)

if __name__ == "__main__":
    main()
