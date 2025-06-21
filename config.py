"""
YouTube 트렌드 분석기 설정 파일
"""
import os
from dotenv import load_dotenv

load_dotenv()


# YouTube Data API 설정
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
DEVELOPER_KEY = os.getenv("YOUTUBE_API_KEY")  # 실제 API 키로 교체 필요

# 기본 설정값
DEFAULT_REGION = "KR"  # KR(한국) 또는 US(글로벌)
DEFAULT_PERIOD = "month"  # week 또는 month
DEFAULT_VIDEO_TYPE = "all"  # all, long, shorts
DEFAULT_CATEGORY = "all"  # all 또는 특정 카테고리 ID
MAX_RESULTS = 100  # 분석할 영상 개수

# YouTube 카테고리 ID 매핑
YOUTUBE_CATEGORIES = {
    "all": "전체",
    "1": "영화 및 애니메이션",
    "2": "자동차 및 차량",
    "10": "음악",
    "15": "애완동물 및 동물",
    "17": "스포츠",
    "19": "여행 및 이벤트",
    "20": "게임",
    "22": "사람 및 블로그",
    "23": "코미디",
    "24": "엔터테인먼트",
    "25": "뉴스 및 정치",
    "26": "노하우 및 스타일",
    "27": "교육",
    "28": "과학 기술",
    "29": "비영리 단체 및 사회운동"
}

# 영상 유형 필터 설정
SHORT_VIDEO_MAX_DURATION = 60  # 쇼츠 최대 길이 (초)
LONG_VIDEO_MIN_DURATION = 60   # 롱폼 최소 길이 (초)

# 분석 설정
COMMENTS_PER_VIDEO = 50  # 영상당 분석할 댓글 수
KEYWORD_EXTRACTION_COUNT = 10  # 추출할 키워드 개수

# 엑셀 출력 설정
EXCEL_FILENAME_FORMAT = "YouTube_Trend_Analysis_{region}_{period}_{timestamp}.xlsx"
THUMBNAIL_COLUMN_WIDTH = 15
THUMBNAIL_ROW_HEIGHT = 80

# 썸네일 다운로드 설정
THUMBNAIL_DOWNLOAD_TIMEOUT = 10  # 썸네일 다운로드 타임아웃 (초)
THUMBNAIL_MAX_FILENAME_LENGTH = 30  # 파일명에 포함될 제목 최대 길이
THUMBNAIL_QUALITY_PRIORITY = ['maxres', 'high', 'medium', 'default']  # 썸네일 품질 우선순위

# 자막 다운로드 설정
TRANSCRIPT_LANGUAGE_PRIORITY = ['ko', 'kr', 'en']  # 자막 언어 우선순위
TRANSCRIPT_ALLOW_AUTO_GENERATED = True  # 자동 생성 자막 허용 여부
TRANSCRIPT_MAX_FILENAME_LENGTH = 50  # 자막 파일명 최대 길이
CHANNEL_VIDEOS_MAX_RESULTS = 50  # 채널별 영상 최대 가져오기 수

# 지역별 설정
REGION_SETTINGS = {
    "KR": {
        "name": "한국",
        "language": "ko",
        "region_code": "KR"
    },
    "US": {
        "name": "글로벌",
        "language": "en",
        "region_code": "US"
    }
}

# API 요청 제한 설정
API_QUOTA_LIMIT = 10000  # 일일 할당량
REQUESTS_PER_SECOND = 10  # 초당 요청 제한
# 참고 (API 사용량):
# - 일반 모드: ~2,000-4,000 units (채널별 Outlier Score 계산 포함)
# - 경량 모드: ~200-400 units (Outlier Score 간소화, 댓글 분석 생략)
# - 키워드 검색: ~1,500-3,000 units (필터 조건에 따라 변동)
# - 할당량 리셋: 매일 자정 UTC 기준
# ⚠️ 할당량 초과 시 경량 모드를 사용하세요!

# 3. API 키 테스트 코드
def test_api_key():
    """API 키 테스트"""
    try:
        from googleapiclient.discovery import build
        
        # 여기에 실제 API 키 입력
        API_KEY = "AIzaSyC-dK6T-XXXXX-XXXXXXXXXXXXXXXXXXXXX"  # 실제 API 키로 변경
        
        youtube = build('youtube', 'v3', developerKey=API_KEY)
        
        # 간단한 API 호출 테스트
        request = youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            regionCode='KR',
            maxResults=1
        )
        response = request.execute()
        
        print("✅ API 키가 올바르게 설정되었습니다!")
        print(f"테스트 결과: {len(response.get('items', []))}개 영상 조회")
        return True
        
    except Exception as e:
        print(f"❌ API 키 오류: {e}")
        if "keyInvalid" in str(e):
            print("💡 해결방법: API 키가 잘못되었습니다. Google Cloud Console에서 새 API 키를 발급받으세요.")
        elif "quotaExceeded" in str(e):
            print("💡 해결방법: API 할당량이 초과되었습니다. 내일 다시 시도하거나 새 프로젝트를 만드세요.")
        return False

if __name__ == "__main__":
    test_api_key()