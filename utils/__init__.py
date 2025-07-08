"""
utils/__init__.py
유틸리티 모듈의 진입점 (완전 버전)
"""

# 모든 모듈 import
from .formatters import (
    format_number, format_duration, format_datetime, 
    format_file_size, format_percentage, format_views_short,
    format_outlier_score, clean_filename, format_relative_time,
    format_currency, format_score, format_ratio, truncate_text,
    format_list, format_engagement_rate
)

from .validators import (
    validate_api_key, validate_youtube_url, validate_channel_id,
    validate_search_keyword, validate_file_path, validate_settings,
    validate_video_id, validate_date_range, validate_region_code,
    validate_language_code
)

from .cache_manager import CacheManager

from .error_handler import (
    ErrorHandler, handle_api_error, log_error, handle_file_error,
    handle_validation_error, setup_global_error_handler
)

__version__ = "3.0.0"
__all__ = [
    # Formatters
    'format_number', 'format_duration', 'format_datetime',
    'format_file_size', 'format_percentage', 'format_views_short',
    'format_outlier_score', 'clean_filename', 'format_relative_time',
    'format_currency', 'format_score', 'format_ratio', 'truncate_text',
    'format_list', 'format_engagement_rate',
    
    # Validators
    'validate_api_key', 'validate_youtube_url', 'validate_channel_id',
    'validate_search_keyword', 'validate_file_path', 'validate_settings',
    'validate_video_id', 'validate_date_range', 'validate_region_code',
    'validate_language_code',
    
    # Cache Manager
    'CacheManager',
    
    # Error Handler
    'ErrorHandler', 'handle_api_error', 'log_error', 'handle_file_error',
    'handle_validation_error', 'setup_global_error_handler'
]

# 전역 인스턴스들
_cache_manager = None
_error_handler = None

def get_cache_manager():
    """전역 캐시 매니저 인스턴스 반환"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager

def get_error_handler():
    """전역 에러 핸들러 인스턴스 반환"""
    global _error_handler
    if _error_handler is None:
        _error_handler = ErrorHandler()
    return _error_handler

def clear_cache():
    """전역 캐시 정리"""
    cache_manager = get_cache_manager()
    return cache_manager.clear_all()

def setup_error_logging(log_file=None, log_level='INFO'):
    """에러 로깅 설정"""
    error_handler = get_error_handler()
    error_handler.setup_logging(log_file, log_level)

# 추가 편의 함수들
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

def measure_execution_time(func):
    """함수 실행 시간 측정 데코레이터"""
    import time
    import functools
    
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        
        execution_time = end_time - start_time
        print(f"{func.__name__} 실행 시간: {execution_time:.3f}초")
        
        return result
    
    return wrapper

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

def retry_on_failure(max_attempts=3, delay=1, backoff_factor=2):
    """재시도 데코레이터"""
    import time
    import functools
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    
                    if attempt < max_attempts - 1:
                        wait_time = delay * (backoff_factor ** attempt)
                        print(f"재시도 {attempt + 1}/{max_attempts}: {wait_time}초 후 다시 시도...")
                        time.sleep(wait_time)
                    else:
                        print(f"최대 재시도 횟수 초과: {func.__name__}")
            
            # 모든 재시도 실패 시 마지막 예외 발생
            raise last_exception
        
        return wrapper
    return decorator

def hash_string(text, algorithm='md5'):
    """문자열 해시 생성"""
    import hashlib
    
    hash_algorithms = {
        'md5': hashlib.md5,
        'sha1': hashlib.sha1,
        'sha256': hashlib.sha256,
        'sha512': hashlib.sha512
    }
    
    if algorithm not in hash_algorithms:
        algorithm = 'md5'
    
    hash_func = hash_algorithms[algorithm]
    return hash_func(text.encode('utf-8')).hexdigest()

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

# __all__에 추가 함수들 포함
__all__.extend([
    'safe_int', 'safe_float', 'safe_string', 'parse_duration',
    'extract_video_id_from_url', 'get_file_extension', 'ensure_directory_exists',
    'get_system_info', 'measure_execution_time', 'format_bytes',
    'generate_timestamp', 'retry_on_failure', 'hash_string', 'is_valid_url',
    'get_cache_manager', 'get_error_handler', 'clear_cache', 'setup_error_logging'
])

# 초기화 메시지
print("✅ Utils 모듈 로드 완료 (formatters, validators, cache_manager, error_handler)")