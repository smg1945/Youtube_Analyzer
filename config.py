"""
YouTube 트렌드 분석기 설정 파일 - 최종 버전
"""
import os
from dotenv import load_dotenv

# .env 파일 로드
load_dotenv()

# YouTube Data API 설정
YOUTUBE_API_SERVICE_NAME = "youtube"
YOUTUBE_API_VERSION = "v3"
DEVELOPER_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY_HERE")

# 최적화된 기본 설정값
DEFAULT_REGION = "KR"
DEFAULT_PERIOD = "week"
DEFAULT_VIDEO_TYPE = "all"
DEFAULT_CATEGORY = "all"
MAX_RESULTS = 200  # 더 많은 결과 제공

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

# 최적화된 분석 설정
COMMENTS_PER_VIDEO = 0  # 댓글 분석 비활성화로 속도 향상
KEYWORD_EXTRACTION_COUNT = 5  # 키워드 추출 개수

# 엑셀 출력 설정 부분에서 썸네일 행 높이 증가:
EXCEL_FILENAME_FORMAT = "YouTube_Analysis_{region}_{timestamp}.xlsx"
THUMBNAIL_COLUMN_WIDTH = 15
THUMBNAIL_ROW_HEIGHT = 80  # 기존 80에서 더 크게 변경

# 썸네일 다운로드 설정
THUMBNAIL_DOWNLOAD_TIMEOUT = 5  # 타임아웃 감소
THUMBNAIL_MAX_FILENAME_LENGTH = 30
THUMBNAIL_QUALITY_PRIORITY = ['high', 'medium', 'default']

# 자막 다운로드 설정
TRANSCRIPT_LANGUAGE_PRIORITY = ['ko', 'kr', 'en']
TRANSCRIPT_ALLOW_AUTO_GENERATED = True
TRANSCRIPT_MAX_FILENAME_LENGTH = 50
CHANNEL_VIDEOS_MAX_RESULTS = 50

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
REQUESTS_PER_SECOND = 20  # 초당 요청 제한

# 검색 최적화 설정
SEARCH_MAX_PAGES = 10  # 페이지당 50개 = 최대 500개 검색
SEARCH_RESULTS_PER_PAGE = 50
BATCH_SIZE = 50  # 배치 처리 크기

# 병렬 처리 설정
MAX_WORKERS = 10  # 병렬 처리 워커 수
ENABLE_PARALLEL_PROCESSING = True

# 캐싱 설정
ENABLE_CHANNEL_CACHE = True  # 채널 정보 캐싱
CACHE_DURATION_MINUTES = 30  # 캐시 유효 시간

def get_optimized_settings():
    """최적화된 설정 반환"""
    return {
        'light_mode': True,  # 항상 경량 모드
        'skip_comments': True,  # 댓글 분석 스킵
        'parallel_processing': ENABLE_PARALLEL_PROCESSING,
        'cache_channels': ENABLE_CHANNEL_CACHE,
        'batch_size': BATCH_SIZE,
        'max_workers': MAX_WORKERS
    }

# 설정 검증
def validate_config():
    """설정 유효성 검사"""
    if DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("⚠️  YouTube API 키가 설정되지 않았습니다.")
        print("   config.py 또는 .env 파일에서 DEVELOPER_KEY를 설정하세요.")
        return False
    return True

# 테스트 함수
if __name__ == "__main__":
    print("🔧 설정 파일 테스트")
    print(f"API 키 설정: {'✅' if validate_config() else '❌'}")
    print(f"기본 지역: {DEFAULT_REGION}")
    print(f"최대 결과: {MAX_RESULTS}")
    print(f"병렬 처리: {'활성화' if ENABLE_PARALLEL_PROCESSING else '비활성화'}")