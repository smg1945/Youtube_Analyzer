"""
data/__init__.py
Data 분석 모듈의 진입점
"""

from .text_analyzer import TextAnalyzer, KeywordTrendAnalyzer
from .sentiment_analyzer import SentimentAnalyzer, SentimentResultProcessor
from .engagement_calculator import EngagementCalculator, PerformanceAnalyzer
from .statistics_calculator import StatisticsCalculator

__version__ = "3.0.0"
__all__ = [
    'TextAnalyzer',
    'KeywordTrendAnalyzer',
    'SentimentAnalyzer', 
    'SentimentResultProcessor',
    'EngagementCalculator',
    'PerformanceAnalyzer',
    'StatisticsCalculator'
]

# 편의 함수들
def create_analysis_suite(language="ko"):
    """
    데이터 분석 도구 세트 생성
    
    Args:
        language (str): 분석 언어
        
    Returns:
        dict: 분석 도구들이 담긴 딕셔너리
    """
    text_analyzer = TextAnalyzer(language)
    sentiment_analyzer = SentimentAnalyzer(language)
    engagement_calculator = EngagementCalculator()
    statistics_calculator = StatisticsCalculator()
    
    return {
        'text_analyzer': text_analyzer,
        'keyword_trend_analyzer': KeywordTrendAnalyzer(text_analyzer),
        'sentiment_analyzer': sentiment_analyzer,
        'sentiment_processor': SentimentResultProcessor(),
        'engagement_calculator': engagement_calculator,
        'performance_analyzer': PerformanceAnalyzer(engagement_calculator),
        'statistics_calculator': statistics_calculator
    }

def quick_text_analysis(texts, language="ko"):
    """
    빠른 텍스트 분석
    
    Args:
        texts (list): 분석할 텍스트 목록
        language (str): 언어
        
    Returns:
        dict: 텍스트 분석 결과
    """
    analyzer = TextAnalyzer(language)
    
    # 키워드 추출
    all_keywords = []
    for text in texts:
        keywords = analyzer.extract_keywords_from_title(text)
        all_keywords.extend(keywords)
    
    # 빈도 분석
    keyword_freq = analyzer.analyze_keyword_frequency(texts)
    
    # 텍스트 패턴 분석
    pattern_analysis = analyzer.analyze_text_patterns(texts)
    
    return {
        'total_texts': len(texts),
        'keywords_extracted': len(all_keywords),
        'keyword_frequency': keyword_freq,
        'text_patterns': pattern_analysis,
        'trending_keywords': analyzer.extract_trending_keywords(texts)
    }

def quick_sentiment_analysis(comments, language="ko"):
    """
    빠른 감정 분석
    
    Args:
        comments (list): 댓글 목록
        language (str): 언어
        
    Returns:
        dict: 감정 분석 결과
    """
    analyzer = SentimentAnalyzer(language)
    
    # 기본 감정 분석
    sentiment_result = analyzer.analyze_comments_sentiment(comments)
    
    # 결과 정규화
    normalized_result = SentimentResultProcessor.normalize_sentiment_scores(sentiment_result)
    
    # 주요 감정 추출
    dominant_sentiment = SentimentResultProcessor.get_dominant_sentiment(normalized_result)
    
    # 감정 극성 계산
    polarity = SentimentResultProcessor.calculate_sentiment_polarity(normalized_result)
    
    return {
        'sentiment_scores': normalized_result,
        'dominant_sentiment': dominant_sentiment,
        'polarity': polarity,
        'analysis_method': sentiment_result.get('analysis_method', 'unknown'),
        'total_comments': len(comments)
    }

def quick_performance_analysis(videos_data):
    """
    빠른 성과 분석
    
    Args:
        videos_data (list): 영상 데이터 목록
        
    Returns:
        dict: 성과 분석 결과
    """
    calc = EngagementCalculator()
    analyzer = PerformanceAnalyzer(calc)
    stats_calc = StatisticsCalculator()
    
    # 참여도 점수 계산
    engagement_scores = [calc.calculate_engagement_score(video) for video in videos_data]
    
    # 조회수 통계
    view_counts = [int(video['statistics'].get('viewCount', 0)) for video in videos_data]
    view_stats = stats_calc.calculate_descriptive_stats(view_counts)
    
    # 고성과 영상 식별
    high_performers = analyzer.identify_high_performers(videos_data, 'engagement')
    
    # 성과 분포 분석
    performance_dist = stats_calc.analyze_performance_distribution(videos_data, 'viewCount')
    
    return {
        'total_videos': len(videos_data),
        'engagement_summary': {
            'avg_engagement': round(sum(engagement_scores) / len(engagement_scores), 2) if engagement_scores else 0,
            'max_engagement': max(engagement_scores) if engagement_scores else 0,
            'min_engagement': min(engagement_scores) if engagement_scores else 0
        },
        'view_statistics': view_stats,
        'high_performers': high_performers,
        'performance_distribution': performance_dist
    }