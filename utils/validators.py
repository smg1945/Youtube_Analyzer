"""
validators.py
입력값 유효성 검증 함수들
"""

import re
import os
from pathlib import Path


def validate_api_key(api_key):
    """YouTube API 키 유효성 검사"""
    if not api_key or not isinstance(api_key, str):
        return False, "API 키가 비어있거나 문자열이 아닙니다."
    
    # 기본 길이 확인 (일반적으로 39자)
    if len(api_key) < 20 or len(api_key) > 50:
        return False, "API 키 길이가 올바르지 않습니다."
    
    # 허용된 문자만 포함하는지 확인
    if not re.match(r'^[A-Za-z0-9_-]+$', api_key):
        return False, "API 키에 허용되지 않은 문자가 포함되어 있습니다."
    
    # 기본 패턴 확인 (Google API 키 패턴)
    if api_key.startswith('AIza') and len(api_key) == 39:
        return True, "유효한 Google API 키 형식입니다."
    
    return True, "API 키 형식이 올바른 것으로 보입니다."


def validate_youtube_url(url):
    """YouTube URL 유효성 검사"""
    if not url or not isinstance(url, str):
        return False, "URL이 비어있거나 문자열이 아닙니다."
    
    # 기본 URL 형식 확인
    url_pattern = re.compile(
        r'^https?://'  # http:// or https://
        r'(?:www\.)?'  # optional www.
        r'(?:youtube\.com|youtu\.be|youtube-nocookie\.com)'  # YouTube domains
        r'.*$', re.IGNORECASE
    )
    
    if not url_pattern.match(url):
        return False, "올바른 YouTube URL이 아닙니다."
    
    # 영상 ID 추출 시도
    video_id_patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'youtube\.com/v/([a-zA-Z0-9_-]{11})'
    ]
    
    for pattern in video_id_patterns:
        if re.search(pattern, url):
            return True, "유효한 YouTube 영상 URL입니다."
    
    # 채널 URL 확인
    channel_patterns = [
        r'youtube\.com/channel/([a-zA-Z0-9_-]+)',
        r'youtube\.com/c/([a-zA-Z0-9_-]+)',
        r'youtube\.com/@([a-zA-Z0-9_-]+)',
        r'youtube\.com/user/([a-zA-Z0-9_-]+)'
    ]
    
    for pattern in channel_patterns:
        if re.search(pattern, url):
            return True, "유효한 YouTube 채널 URL입니다."
    
    return False, "인식할 수 있는 YouTube URL 형식이 아닙니다."


def validate_channel_id(channel_id):
    """YouTube 채널 ID 유효성 검사"""
    if not channel_id or not isinstance(channel_id, str):
        return False, "채널 ID가 비어있거나 문자열이 아닙니다."
    
    # UC로 시작하는 24자리 채널 ID (일반적인 형식)
    if re.match(r'^UC[a-zA-Z0-9_-]{22}$', channel_id):
        return True, "유효한 YouTube 채널 ID입니다."
    
    # @ 핸들 형식
    if re.match(r'^@[a-zA-Z0-9_-]+$', channel_id):
        return True, "유효한 YouTube 채널 핸들입니다."
    
    # 사용자명 형식 (레거시)
    if re.match(r'^[a-zA-Z0-9_-]+$', channel_id) and len(channel_id) <= 20:
        return True, "유효한 채널명으로 보입니다."
    
    return False, "올바른 채널 ID 형식이 아닙니다."


def validate_search_keyword(keyword):
    """검색 키워드 유효성 검사"""
    if not keyword or not isinstance(keyword, str):
        return False, "검색 키워드가 비어있거나 문자열이 아닙니다."
    
    # 길이 확인
    if len(keyword.strip()) < 1:
        return False, "검색 키워드가 너무 짧습니다."
    
    if len(keyword) > 100:
        return False, "검색 키워드가 너무 깁니다 (최대 100자)."
    
    # 특수문자 확인 (기본적인 것만)
    if keyword.strip() == "":
        return False, "공백만으로는 검색할 수 없습니다."
    
    return True, "유효한 검색 키워드입니다."


def validate_file_path(file_path):
    """파일 경로 유효성 검사"""
    if not file_path or not isinstance(file_path, str):
        return False, "파일 경로가 비어있거나 문자열이 아닙니다."
    
    try:
        path = Path(file_path)
        
        # 상위 디렉토리 존재 확인
        if path.parent != Path('.') and not path.parent.exists():
            return False, f"디렉토리가 존재하지 않습니다: {path.parent}"
        
        # 파일명 길이 확인
        if len(path.name) > 255:
            return False, "파일명이 너무 깁니다 (최대 255자)."
        
        # 금지된 문자 확인 (Windows 기준)
        forbidden_chars = r'[<>:"/\\|?*]'
        if re.search(forbidden_chars, path.name):
            return False, "파일명에 사용할 수 없는 문자가 포함되어 있습니다."
        
        # 예약된 이름 확인 (Windows)
        reserved_names = [
            'CON', 'PRN', 'AUX', 'NUL',
            'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
            'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
        ]
        
        if path.stem.upper() in reserved_names:
            return False, f"예약된 파일명입니다: {path.stem}"
        
        return True, "유효한 파일 경로입니다."
        
    except Exception as e:
        return False, f"파일 경로 검증 오류: {str(e)}"


def validate_settings(settings):
    """설정 딕셔너리 유효성 검사"""
    if not isinstance(settings, dict):
        return False, "설정이 딕셔너리 형태가 아닙니다."
    
    errors = []
    
    # 필수 설정 확인
    required_keys = ['api_key']
    for key in required_keys:
        if key not in settings:
            errors.append(f"필수 설정이 누락되었습니다: {key}")
    
    # API 키 검증
    if 'api_key' in settings:
        valid, msg = validate_api_key(settings['api_key'])
        if not valid:
            errors.append(f"API 키 오류: {msg}")
    
    # 숫자 설정들 검증
    numeric_settings = {
        'max_results': (1, 500),
        'quota_limit': (1000, 1000000),
        'max_workers': (1, 20),
        'timeout': (5, 300),
        'retry_count': (0, 10)
    }
    
    for key, (min_val, max_val) in numeric_settings.items():
        if key in settings:
            value = settings[key]
            if not isinstance(value, (int, float)):
                errors.append(f"{key}는 숫자여야 합니다.")
            elif value < min_val or value > max_val:
                errors.append(f"{key}는 {min_val}-{max_val} 사이여야 합니다.")
    
    # 문자열 설정들 검증
    string_settings = ['language', 'region', 'theme']
    for key in string_settings:
        if key in settings and not isinstance(settings[key], str):
            errors.append(f"{key}는 문자열이어야 합니다.")
    
    # 불린 설정들 검증
    boolean_settings = ['debug_mode', 'auto_save', 'remember_tab']
    for key in boolean_settings:
        if key in settings and not isinstance(settings[key], bool):
            errors.append(f"{key}는 true/false 값이어야 합니다.")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, "설정이 유효합니다."


def validate_video_id(video_id):
    """YouTube 영상 ID 유효성 검사"""
    if not video_id or not isinstance(video_id, str):
        return False, "영상 ID가 비어있거나 문자열이 아닙니다."
    
    # YouTube 영상 ID는 11자리 영숫자+하이픈+언더스코어
    if re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return True, "유효한 YouTube 영상 ID입니다."
    
    return False, "올바른 YouTube 영상 ID 형식이 아닙니다."


def validate_date_range(start_date, end_date):
    """날짜 범위 유효성 검사"""
    from datetime import datetime, timedelta
    
    try:
        if isinstance(start_date, str):
            start_date = datetime.fromisoformat(start_date)
        if isinstance(end_date, str):
            end_date = datetime.fromisoformat(end_date)
        
        if start_date >= end_date:
            return False, "시작 날짜가 종료 날짜보다 늦습니다."
        
        # 최대 범위 확인 (1년)
        if (end_date - start_date).days > 365:
            return False, "날짜 범위가 1년을 초과할 수 없습니다."
        
        # 미래 날짜 확인
        now = datetime.now()
        if end_date > now:
            return False, "종료 날짜가 미래일 수 없습니다."
        
        return True, "유효한 날짜 범위입니다."
        
    except Exception as e:
        return False, f"날짜 형식 오류: {str(e)}"


def validate_region_code(region_code):
    """지역 코드 유효성 검사"""
    if not region_code or not isinstance(region_code, str):
        return False, "지역 코드가 비어있거나 문자열이 아닙니다."
    
    # ISO 3166-1 alpha-2 코드 (2자리)
    if re.match(r'^[A-Z]{2}$', region_code):
        # 일반적인 지역 코드들
        valid_regions = {
            'KR', 'US', 'JP', 'GB', 'DE', 'FR', 'CA', 'AU', 'IN', 'BR',
            'RU', 'IT', 'ES', 'MX', 'NL', 'SE', 'NO', 'DK', 'FI', 'PL'
        }
        
        if region_code in valid_regions:
            return True, "유효한 지역 코드입니다."
        else:
            return True, "지역 코드 형식은 올바르지만 지원 여부를 확인하세요."
    
    return False, "올바른 지역 코드 형식이 아닙니다 (예: KR, US, JP)."


def validate_language_code(language_code):
    """언어 코드 유효성 검사"""
    if not language_code or not isinstance(language_code, str):
        return False, "언어 코드가 비어있거나 문자열이 아닙니다."
    
    # ISO 639-1 코드 (2자리) 또는 지역 포함 (5자리)
    if re.match(r'^[a-z]{2}(-[A-Z]{2})?$', language_code):
        return True, "유효한 언어 코드입니다."
    
    return False, "올바른 언어 코드 형식이 아닙니다 (예: ko, en, ko-KR)."