"""
core/__init__.py
Core 모듈의 진입점
"""

from .youtube_client import YouTubeClient
from .video_search import VideoSearcher, TrendingVideoSearcher
from .channel_analyzer import ChannelAnalyzer
from .trend_analyzer import TrendAnalyzer

__version__ = "3.0.0"
__all__ = [
    'YouTubeClient',
    'VideoSearcher', 
    'TrendingVideoSearcher',
    'ChannelAnalyzer',
    'TrendAnalyzer'
]

# 편의 함수들
def create_analyzer_suite(api_key):
    """
    분석 도구 세트 생성
    
    Args:
        api_key (str): YouTube API 키
        
    Returns:
        dict: 분석 도구들이 담긴 딕셔너리
    """
    client = YouTubeClient(api_key)
    
    return {
        'client': client,
        'video_searcher': VideoSearcher(client),
        'trending_searcher': TrendingVideoSearcher(client),
        'channel_analyzer': ChannelAnalyzer(client),
        'trend_analyzer': TrendAnalyzer(client)
    }

def quick_search(api_key, keyword, filters=None):
    """
    빠른 영상 검색
    
    Args:
        api_key (str): YouTube API 키
        keyword (str): 검색 키워드
        filters (dict): 검색 필터
        
    Returns:
        list: 검색 결과
    """
    if filters is None:
        filters = {}
    
    client = YouTubeClient(api_key)
    searcher = VideoSearcher(client)
    
    return searcher.search_with_filters(keyword, filters)

def quick_channel_analysis(api_key, channel_input):
    """
    빠른 채널 분석
    
    Args:
        api_key (str): YouTube API 키
        channel_input (str): 채널 URL 또는 ID
        
    Returns:
        dict: 채널 분석 결과
    """
    client = YouTubeClient(api_key)
    analyzer = ChannelAnalyzer(client)
    
    # 채널 ID 추출
    channel_id, _ = analyzer.extract_channel_id_from_url(channel_input)
    if not channel_id:
        return {'error': '유효하지 않은 채널 정보입니다.'}
    
    return analyzer.analyze_channel(channel_id)

def quick_trend_analysis(api_key, region='KR'):
    """
    빠른 트렌드 분석
    
    Args:
        api_key (str): YouTube API 키
        region (str): 지역 코드
        
    Returns:
        dict: 트렌드 분석 결과
    """
    client = YouTubeClient(api_key)
    analyzer = TrendAnalyzer(client)
    
    return analyzer.analyze_trending_keywords(region)
