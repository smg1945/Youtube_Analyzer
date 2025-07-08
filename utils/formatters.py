"""
formatters.py
숫자, 날짜, 텍스트 포맷팅 유틸리티 함수들
"""

import re
from datetime import datetime


def format_number(number):
    """숫자를 천 단위 구분자로 포맷"""
    if number == 0:
        return "0"
    
    if number >= 1000000:
        return f"{number/1000000:.1f}M"
    elif number >= 1000:
        return f"{number/1000:.1f}K"
    else:
        return str(number)


def format_duration(duration_str):
    """YouTube 영상 길이를 사람이 읽기 쉬운 형태로 변환"""
    if not duration_str:
        return "0:00"
    
    # ISO 8601 duration (PT4M13S) 형태 처리
    if duration_str.startswith('PT'):
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return "0:00"
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"
    
    # 이미 포맷된 형태라면 그대로 반환
    return duration_str


def format_datetime(dt, format_type='readable'):
    """날짜시간을 다양한 형태로 포맷"""
    if isinstance(dt, str):
        try:
            # ISO 형태 파싱 시도
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    if not isinstance(dt, datetime):
        return str(dt)
    
    formats = {
        'readable': '%Y-%m-%d %H:%M:%S',
        'date': '%Y-%m-%d',
        'time': '%H:%M:%S',
        'korean': '%Y년 %m월 %d일 %H시 %M분',
        'relative': None  # 별도 처리
    }
    
    if format_type == 'relative':
        return format_relative_time(dt)
    
    format_str = formats.get(format_type, formats['readable'])
    return dt.strftime(format_str)


def format_relative_time(dt):
    """상대적 시간 표시 (3일 전, 2시간 전 등)"""
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except:
            return dt
    
    now = datetime.now()
    if dt.tzinfo:
        now = now.replace(tzinfo=dt.tzinfo)
    
    diff = now - dt
    days = diff.days
    seconds = diff.seconds
    
    if days > 365:
        years = days // 365
        return f"{years}년 전"
    elif days > 30:
        months = days // 30
        return f"{months}개월 전"
    elif days > 0:
        return f"{days}일 전"
    elif seconds > 3600:
        hours = seconds // 3600
        return f"{hours}시간 전"
    elif seconds > 60:
        minutes = seconds // 60
        return f"{minutes}분 전"
    else:
        return "방금 전"


def format_file_size(bytes_value):
    """바이트를 읽기 쉬운 형태로 포맷"""
    if bytes_value == 0:
        return "0 B"
    
    size_names = ["B", "KB", "MB", "GB", "TB"]
    import math
    
    i = int(math.floor(math.log(bytes_value, 1024)))
    p = math.pow(1024, i)
    s = round(bytes_value / p, 2)
    
    return f"{s} {size_names[i]}"


def format_percentage(value, total, decimal_places=1):
    """백분율 포맷"""
    if total == 0:
        return "0%"
    
    percentage = (value / total) * 100
    return f"{percentage:.{decimal_places}f}%"


def format_views_short(views):
    """조회수를 간단한 형태로 포맷 (1.2M, 5.8K 등)"""
    if views >= 1000000000:
        return f"{views/1000000000:.1f}B"
    elif views >= 1000000:
        return f"{views/1000000:.1f}M"
    elif views >= 1000:
        return f"{views/1000:.1f}K"
    else:
        return str(views)


def format_currency(amount, currency='KRW'):
    """통화 포맷"""
    if currency == 'KRW':
        return f"{amount:,}원"
    elif currency == 'USD':
        return f"${amount:,.2f}"
    elif currency == 'JPY':
        return f"¥{amount:,}"
    else:
        return f"{amount:,} {currency}"


def format_score(score, max_score=100, decimal_places=1):
    """점수 포맷 (0-100 등)"""
    return f"{score:.{decimal_places}f}/{max_score}"


def format_ratio(numerator, denominator, format_type='percentage'):
    """비율 포맷"""
    if denominator == 0:
        return "N/A"
    
    ratio = numerator / denominator
    
    if format_type == 'percentage':
        return f"{ratio * 100:.1f}%"
    elif format_type == 'decimal':
        return f"{ratio:.3f}"
    elif format_type == 'fraction':
        return f"{numerator}/{denominator}"
    else:
        return str(ratio)


def truncate_text(text, max_length=50, suffix="..."):
    """텍스트 자르기"""
    if not text:
        return ""
    
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def format_list(items, separator=", ", max_items=None):
    """리스트를 문자열로 포맷"""
    if not items:
        return ""
    
    if max_items and len(items) > max_items:
        displayed_items = items[:max_items]
        return separator.join(map(str, displayed_items)) + f" (+{len(items) - max_items} more)"
    
    return separator.join(map(str, items))


def format_engagement_rate(likes, views, comments=None):
    """참여율 계산 및 포맷"""
    if views == 0:
        return "0%"
    
    engagement = likes
    if comments:
        engagement += comments
    
    rate = (engagement / views) * 100
    return f"{rate:.2f}%"


def clean_filename(filename):
    """파일명에서 유효하지 않은 문자 제거"""
    # Windows/macOS/Linux에서 파일명으로 사용할 수 없는 문자들
    invalid_chars = r'[<>:"/\\|?*]'
    
    # 유효하지 않은 문자를 언더스코어로 대체
    clean_name = re.sub(invalid_chars, '_', filename)
    
    # 연속된 언더스코어를 하나로
    clean_name = re.sub(r'_+', '_', clean_name)
    
    # 앞뒤 공백 및 점 제거
    clean_name = clean_name.strip(' .')
    
    # 너무 긴 경우 자르기
    if len(clean_name) > 200:
        clean_name = clean_name[:200]
    
    return clean_name or "untitled"


def format_outlier_score(score):
    """Outlier Score를 등급으로 포맷"""
    if score >= 80:
        return f"{score:.1f} (🔥 매우 높음)"
    elif score >= 60:
        return f"{score:.1f} (📈 높음)"
    elif score >= 40:
        return f"{score:.1f} (📊 보통)"
    elif score >= 20:
        return f"{score:.1f} (📉 낮음)"
    else:
        return f"{score:.1f} (❄️ 매우 낮음)"