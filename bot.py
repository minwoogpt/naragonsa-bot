import requests
import os
from datetime import datetime, timedelta

# 깃허브 시크릿에서 가져오기
API_KEY = os.environ['DATA_API_KEY']
TOKEN = os.environ['TELEGRAM_TOKEN']
CHAT_ID = os.environ['TELEGRAM_CHAT_ID']

def send_telegram(text):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, data={'chat_id': CHAT_ID, 'text': text[:4000]})

def test_weather_api():
    # 기상청 단기예보(초단기실황) 주소
    url = "http://apis.data.go.kr/1360000/VilageFcstInfoService_2.0/getUltraSrtNcst"
    
    # 현재 시간 설정 (기상청은 매시각 10분 이후에 데이터가 나옵니다)
    now = datetime.now() + timedelta(hours=9) # 한국 시간 기준
    if now.minute < 15: # 안전하게 15분 전이면 한 시간 전 데이터 조회
        now = now - timedelta(hours=1)
    
    base_date = now.strftime('%Y%m%d')
    base_time = now.strftime('%H00')

    params = {
        'serviceKey': API_KEY,
        'numOfRows': '10',
        'pageNo': '1',
        'dataType': 'JSON',
        'base_date': base_date,
        'base_time': base_time,
        'nx': '96', # 부산 강서구 인근 좌표
        'ny': '76'
    }

    try:
        res = requests.get(url, params=params, timeout=30)
        
        if res.status_code == 200:
            data = res.json()
            result_code = data.get('response', {}).get('header', {}).get('resultCode')
            
            if result_code == '00':
                # 성공 시 온도 데이터 추출
                items = data['response']['body']['items']['item']
                temp = ""
                for item in items:
                    if item['category'] == 'T1H': # 기온 항목
                        temp = item['obsrValue']
                return f"✅ 기상청 연결 성공!\n현재 부산 기온: {temp}도\n\n결론: 찬우님 API 키는 아주 잘 작동합니다!"
            else:
                msg = data.get('response', {}).get('header', {}).get('resultMsg')
                return f"❓ 연결은 됐으나 기상청이 거절함: {msg}\n(인증키 등록 대기 중일 확률 높음)"
        else:
            return f"❌ 서버 응답 실패 (코드: {res.status_code})"
            
    except Exception as e:
        return f"❌ 연결 실패 에러: {str(e)}"

def main():
    send_telegram("🌡️ 기상청 데이터를 찔러보고 있습니다...")
    result = test_weather_api()
    send_telegram(result)

if __name__ == "__main__":
    main()
