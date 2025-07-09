"""
utils/__init__.py
유틸리티 모듈의 진입점 (수정됨)
"""

# 현재 사용 가능한 모듈만 import
try:
    from .formatters import (
        format_number, format_duration, format_datetime, 
        format_file_size, format_percentage, format_views_short,
        format_outlier_score, clean_filename
    )
    FORMATTERS_AVAILABLE = True
except ImportError:
    FORMATTERS_AVAILABLE = False
    print("⚠️ formatters 모듈을 로드할 수 없습니다.")

# 다른 모듈들은 차차 구현 예정
VALIDATORS_AVAILABLE = False
CACHE_MANAGER_AVAILABLE = False
ERROR_HANDLER_AVAILABLE = False

__version__ = "3.0.0"

# 사용 가능한 기능만 __all__에 포함
__all__ = []

if FORMATTERS_AVAILABLE:
    __all__.extend([
        'format_number', 'format_duration', 'format_datetime',
        'format_file_size', 'format_percentage', 'format_views_short',
        'format_outlier_score', 'clean_filename'
    ])

# 기본 유틸리티 함수들 (내장)
def safe_int(value, default=0):
    """안전한 정수 변환"""
    try:
        return int(value)
    except (ValueError, TypeError):
        return default

def safe_float(value, default=0.0):
    """안전한 실수 변환"""
    try:
        return float(value)
    except (ValueError, TypeError):
        return default

def safe_string(value, default=""):
    """안전한 문자열 변환"""
    try:
        return str(value) if value is not None else default
    except:
        return default

def truncate_string(text, max_length=50, suffix="..."):
    """문자열 자르기"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix

def parse_duration(duration_str):
    """YouTube 영상 길이 파싱 (초 단위로 변환)"""
    import re
    
    if not duration_str:
        return 0
    
    # ISO 8601 duration (PT4M13S) 형태 처리
    if duration_str.startswith('PT'):
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
    else:
        # 이미 포맷된 형태 (4:13, 1:04:13)
        pattern = r'(?:(\d+):)?(\d+):(\d+)'
    
    match = re.match(pattern, duration_str)
    
    if not match:
        return 0
    
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2) or 0)
    seconds = int(match.group(3) or 0)
    
    return hours * 3600 + minutes * 60 + seconds

def extract_video_id_from_url(url):
    """YouTube URL에서 영상 ID 추출"""
    import re
    
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]+)',
        r'youtube\.com/embed/([a-zA-Z0-9_-]+)',
        r'youtube\.com/v/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    
    # URL이 아니라 그냥 ID인 경우
    if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
        return url
    
    return None

def get_file_extension(filename):
    """파일 확장자 추출"""
    import os
    return os.path.splitext(filename)[1].lower()

def ensure_directory_exists(directory_path):
    """디렉토리가 존재하지 않으면 생성"""
    import os
    
    try:
        os.makedirs(directory_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"디렉토리 생성 실패 ({directory_path}): {e}")
        return False

def get_system_info():
    """시스템 정보 반환"""
    import platform
    import sys
    
    return {
        'platform': platform.system(),
        'platform_version': platform.version(),
        'python_version': sys.version,
        'architecture': platform.architecture()[0]
    }

def format_bytes(bytes_value):
    """바이트를 읽기 쉬운 형태로 포맷"""
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    
    return f"{s} {size_names[i]}"

def generate_timestamp(format_type='full'):
    """타임스탬프 생성"""
    from datetime import datetime
    
    now = datetime.now()
    
    formats = {
        'full': '%Y%m%d_%H%M%S',
        'date': '%Y%m%d',
        'time': '%H%M%S',
        'readable': '%Y-%m-%d %H:%M:%S',
        'filename': '%Y%m%d_%H%M%S'
    }
    
    return now.strftime(formats.get(format_type, formats['full']))

def is_valid_url(url):
    """URL 유효성 검사"""
    import re
    
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
        r'localhost|'  # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
        r'(?::\d+)?'  # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
    
    return url_pattern.match(url) is not None

# 기본 캐시 관리 (단순 버전)
_simple_cache = {}

def get_cache(key):
    """간단한 캐시에서 값 가져오기"""
    return _simple_cache.get(key)

def set_cache(key, value):
    """간단한 캐시에 값 저장"""
    _simple_cache[key] = value

def clear_cache():
    """간단한 캐시 정리"""
    global _simple_cache
    _simple_cache.clear()

# 기본 에러 처리
def log_error(error_msg, error_type="ERROR"):
    """간단한 에러 로깅"""
    from datetime import datetime
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {error_type}: {error_msg}")

def handle_api_error(error):
    """API 에러 처리"""
    error_msg = str(error)
    
    if "quotaExceeded" in error_msg:
        return "API 할당량이 초과되었습니다. 내일 다시 시도하세요."
    elif "keyInvalid" in error_msg:
        return "API 키가 유효하지 않습니다. 키를 확인하세요."
    elif "keyMissing" in error_msg:
        return "API 키가 설정되지 않았습니다."
    else:
        return f"API 오류: {error_msg}"

# 기본 유효성 검증
def validate_api_key(api_key):
    """API 키 기본 유효성 검사"""
    if not api_key or not isinstance(api_key, str):
        return False
    
    # 기본 형태 확인 (39자리 영숫자)
    if len(api_key) != 39:
        return False
    
    # 알파벳과 숫자, 하이픈, 언더스코어만 허용
    import re
    return bool(re.match(r'^[A-Za-z0-9_-]+$', api_key))

def validate_youtube_url(url):
    """YouTube URL 유효성 검사"""
    if not url:
        return False
    
    youtube_patterns = [
        r'youtube\.com',
        r'youtu\.be',
        r'youtube-nocookie\.com'
    ]
    
    return any(pattern in url.lower() for pattern in youtube_patterns)

# __all__에 추가 함수들 포함
__all__.extend([
    'safe_int', 'safe_float', 'safe_string', 'truncate_string',
    'parse_duration', 'extract_video_id_from_url', 'get_file_extension',
    'ensure_directory_exists', 'get_system_info', 'format_bytes',
    'generate_timestamp', 'is_valid_url', 'get_cache', 'set_cache',
    'clear_cache', 'log_error', 'handle_api_error', 'validate_api_key',
    'validate_youtube_url'
])