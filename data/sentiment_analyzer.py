"""
감정 분석 전용 모듈
댓글 감정 분석, 긍정/부정 분류, 감정 트렌드 분석 담당
"""

import re
from collections import Counter, defaultdict

# 선택적 import
try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("⚠️ TextBlob이 설치되지 않았습니다. 고급 감정 분석이 제한됩니다.")

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False
    print("⚠️ VADER Sentiment가 설치되지 않았습니다. 소셜미디어 감정 분석이 제한됩니다.")

class SentimentAnalyzer:
    """감정 분석 클래스"""
    
    def __init__(self, language="ko"):
        """
        감정 분석기 초기화
        
        Args:
            language (str): 분석 언어 ("ko" 또는 "en")
        """
        self.language = language
        
        # VADER 분석기 초기화 (영어, 소셜미디어 특화)
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
        else:
            self.vader_analyzer = None
        
        # 키워드 기반 감정 사전 로드
        self.sentiment_keywords = self._load_sentiment_keywords(language)
        
        print(f"✅ 감정 분석기 초기화 완료 (언어: {language})")
        print(f"   사용 가능한 엔진: {self._get_available_engines()}")
    
    def analyze_comments_sentiment(self, comments):
        """
        댓글 감정 분석
        
        Args:
            comments (list): 댓글 목록 [{'text': '댓글내용', ...}, ...]
            
        Returns:
            dict: 감정 분석 결과
        """
        if not comments:
            return {
                'positive': 0.0,
                'neutral': 0.0,
                'negative': 0.0,
                'total_comments': 0,
                'analysis_method': 'none'
            }
        
        print(f"💭 댓글 감정 분석 시작: {len(comments)}개")
        
        # 사용 가능한 최적의 분석 방법 선택
        if TEXTBLOB_AVAILABLE and self.language == "en":
            result = self._analyze_with_textblob(comments)
            result['analysis_method'] = 'textblob'
        elif VADER_AVAILABLE:
            result = self._analyze_with_vader(comments)
            result['analysis_method'] = 'vader'
        else:
            result = self._analyze_with_keywords(comments)
            result['analysis_method'] = 'keywords'
        
        result['total_comments'] = len(comments)
        
        print(f"✅ 감정 분석 완료: 긍정 {result['positive']:.1f}%, "
              f"중립 {result['neutral']:.1f}%, 부정 {result['negative']:.1f}%")
        
        return result
    
    def _analyze_with_textblob(self, comments):
        """TextBlob을 사용한 감정 분석"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        sentiment_scores = []
        
        for comment in comments:
            try:
                text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                sentiment_scores.append(polarity)
                
                if polarity > 0.1:
                    positive_count += 1
                elif polarity < -0.1:
                    negative_count += 1
                else:
                    neutral_count += 1
                    
            except Exception as e:
                neutral_count += 1  # 분석 실패시 중립으로 처리
        
        total = len(comments)
        if total == 0:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
        
        return {
            'positive': round(positive_count / total * 100, 2),
            'neutral': round(neutral_count / total * 100, 2),
            'negative': round(negative_count / total * 100, 2),
            'avg_sentiment_score': round(sum(sentiment_scores) / len(sentiment_scores), 3) if sentiment_scores else 0,
            'sentiment_distribution': {
                'scores': sentiment_scores,
                'std_dev': self._calculate_std_dev(sentiment_scores)
            }
        }
    
    def _analyze_with_vader(self, comments):
        """VADER를 사용한 감정 분석 (소셜미디어 특화)"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        compound_scores = []
        
        for comment in comments:
            try:
                text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
                scores = self.vader_analyzer.polarity_scores(text)
                compound = scores['compound']
                compound_scores.append(compound)
                
                # VADER의 compound score 기준
                if compound >= 0.05:
                    positive_count += 1
                elif compound <= -0.05:
                    negative_count += 1
                else:
                    neutral_count += 1
                    
            except Exception as e:
                neutral_count += 1
        
        total = len(comments)
        if total == 0:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
        
        return {
            'positive': round(positive_count / total * 100, 2),
            'neutral': round(neutral_count / total * 100, 2),
            'negative': round(negative_count / total * 100, 2),
            'avg_compound_score': round(sum(compound_scores) / len(compound_scores), 3) if compound_scores else 0,
            'sentiment_intensity': self._categorize_sentiment_intensity(compound_scores)
        }
    
    def _analyze_with_keywords(self, comments):
        """키워드 기반 감정 분석"""
        positive_count = 0
        negative_count = 0
        keyword_matches = {'positive': [], 'negative': []}
        
        pos_keywords = self.sentiment_keywords['positive']
        neg_keywords = self.sentiment_keywords['negative']
        
        for comment in comments:
            try:
                text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
                text_lower = text.lower()
                
                # 긍정 키워드 매칭
                pos_matches = [word for word in pos_keywords if word in text_lower]
                neg_matches = [word for word in neg_keywords if word in text_lower]
                
                if pos_matches and not neg_matches:
                    positive_count += 1
                    keyword_matches['positive'].extend(pos_matches)
                elif neg_matches and not pos_matches:
                    negative_count += 1
                    keyword_matches['negative'].extend(neg_matches)
                elif pos_matches and neg_matches:
                    # 둘 다 있으면 더 많은 쪽으로 분류
                    if len(pos_matches) > len(neg_matches):
                        positive_count += 1
                        keyword_matches['positive'].extend(pos_matches)
                    else:
                        negative_count += 1
                        keyword_matches['negative'].extend(neg_matches)
                # 아무것도 없으면 중립
                
            except Exception as e:
                continue
        
        total = len(comments)
        neutral_count = total - positive_count - negative_count
        
        if total == 0:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
        
        return {
            'positive': round(positive_count / total * 100, 2),
            'neutral': round(neutral_count / total * 100, 2),
            'negative': round(negative_count / total * 100, 2),
            'keyword_analysis': {
                'positive_keywords_found': Counter(keyword_matches['positive']),
                'negative_keywords_found': Counter(keyword_matches['negative']),
                'total_positive_matches': len(keyword_matches['positive']),
                'total_negative_matches': len(keyword_matches['negative'])
            }
        }
    
    def analyze_sentiment_trends(self, time_series_comments):
        """
        시간별 감정 트렌드 분석
        
        Args:
            time_series_comments (list): [{'date': '2024-01-01', 'comments': [...]}, ...]
            
        Returns:
            dict: 시간별 감정 트렌드
        """
        trends = {}
        
        for data_point in time_series_comments:
            date = data_point['date']
            comments = data_point['comments']
            
            sentiment_result = self.analyze_comments_sentiment(comments)
            trends[date] = sentiment_result
        
        # 트렌드 요약
        summary = self._summarize_sentiment_trends(trends)
        
        return {
            'daily_trends': trends,
            'trend_summary': summary,
            'analysis_period': {
                'start_date': min(trends.keys()) if trends else None,
                'end_date': max(trends.keys()) if trends else None,
                'total_days': len(trends)
            }
        }
    
    def detect_sentiment_anomalies(self, comments, threshold=2.0):
        """
        감정 이상치 탐지
        
        Args:
            comments (list): 댓글 목록
            threshold (float): 이상치 기준 (표준편차 배수)
            
        Returns:
            dict: 이상치 탐지 결과
        """
        if not comments:
            return {'anomalies': [], 'total_anomalies': 0}
        
        # 개별 댓글의 감정 점수 계산
        comment_sentiments = []
        
        for i, comment in enumerate(comments):
            text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
            
            # 단일 댓글 감정 분석
            single_result = self.analyze_comments_sentiment([comment])
            
            # 감정 점수 계산 (긍정: +1, 중립: 0, 부정: -1의 가중 평균)
            sentiment_score = (single_result['positive'] - single_result['negative']) / 100
            
            comment_sentiments.append({
                'index': i,
                'text': text[:100] + '...' if len(text) > 100 else text,
                'sentiment_score': sentiment_score,
                'classification': self._classify_single_sentiment(single_result)
            })
        
        # 평균과 표준편차 계산
        scores = [cs['sentiment_score'] for cs in comment_sentiments]
        mean_score = sum(scores) / len(scores)
        std_dev = self._calculate_std_dev(scores)
        
        # 이상치 탐지
        anomalies = []
        for cs in comment_sentiments:
            deviation = abs(cs['sentiment_score'] - mean_score)
            if deviation > threshold * std_dev:
                cs['anomaly_score'] = deviation / std_dev
                anomalies.append(cs)
        
        # 이상치 점수 순으로 정렬
        anomalies.sort(key=lambda x: x['anomaly_score'], reverse=True)
        
        return {
            'anomalies': anomalies,
            'total_anomalies': len(anomalies),
            'anomaly_rate': round(len(anomalies) / len(comments) * 100, 2),
            'sentiment_stats': {
                'mean_score': round(mean_score, 3),
                'std_dev': round(std_dev, 3),
                'threshold_used': threshold
            }
        }
    
    def analyze_emotional_keywords(self, comments):
        """
        감정별 키워드 분석
        
        Args:
            comments (list): 댓글 목록
            
        Returns:
            dict: 감정별 키워드 분석 결과
        """
        emotional_keywords = {
            'positive': defaultdict(int),
            'negative': defaultdict(int),
            'neutral': defaultdict(int)
        }
        
        for comment in comments:
            text = comment.get('text', '') if isinstance(comment, dict) else str(comment)
            
            # 단일 댓글 감정 분석
            sentiment = self.analyze_comments_sentiment([comment])
            
            # 감정 분류
            if sentiment['positive'] > max(sentiment['negative'], sentiment['neutral']):
                category = 'positive'
            elif sentiment['negative'] > max(sentiment['positive'], sentiment['neutral']):
                category = 'negative'
            else:
                category = 'neutral'
            
            # 키워드 추출 (간단한 방법)
            words = re.findall(r'\b\w+\b', text.lower())
            for word in words:
                if len(word) > 2:  # 3글자 이상
                    emotional_keywords[category][word] += 1
        
        # 각 감정별 상위 키워드 추출
        result = {}
        for emotion, keywords in emotional_keywords.items():
            top_keywords = dict(Counter(keywords).most_common(20))
            result[emotion] = {
                'keywords': top_keywords,
                'total_words': sum(keywords.values()),
                'unique_words': len(keywords)
            }
        
        return result
    
    def _load_sentiment_keywords(self, language):
        """언어별 감정 키워드 사전 로드"""
        keywords = {
            'ko': {
                'positive': [
                    '좋다', '최고', '대박', '멋지다', '훌륭', '완벽', '사랑', '감사', 
                    '재밌', '웃겨', '굿', '베스트', '좋아', '예쁘다', '맛있', '행복',
                    '기쁘다', '놀랍', '신기', '대단', '쩐다', '개좋', '개웃', '킹받',
                    '극찬', '추천', '인정', '레전드', '갓', '혜자', '꿀', '짱'
                ],
                'negative': [
                    '싫다', '별로', '최악', '나쁘다', '짜증', '화나', '실망', '안좋', 
                    '못해', '어이없', '빡치', '재미없', '지겨', '답답', '후회',
                    '끔찍', '역겨', '못생', '추하', '더럽', '개빡', '열받', '빌런',
                    '쓰레기', '망함', '실패', '엉망', '개별로', '노잼', '핵노잼'
                ]
            },
            'en': {
                'positive': [
                    'good', 'great', 'amazing', 'awesome', 'perfect', 'love', 'best', 
                    'wonderful', 'excellent', 'fantastic', 'brilliant', 'outstanding',
                    'incredible', 'beautiful', 'nice', 'cool', 'sweet', 'fun',
                    'happy', 'joy', 'pleased', 'satisfied', 'impressed', 'wow'
                ],
                'negative': [
                    'bad', 'terrible', 'awful', 'hate', 'worst', 'disappointing', 
                    'boring', 'stupid', 'horrible', 'disgusting', 'annoying',
                    'frustrating', 'pathetic', 'useless', 'waste', 'crap',
                    'sucks', 'lame', 'dumb', 'ridiculous', 'trash', 'garbage'
                ]
            }
        }
        
        return keywords.get(language, keywords['en'])
    
    def _classify_single_sentiment(self, sentiment_result):
        """단일 감정 결과 분류"""
        positive = sentiment_result['positive']
        negative = sentiment_result['negative']
        neutral = sentiment_result['neutral']
        
        if positive > max(negative, neutral):
            return 'positive'
        elif negative > max(positive, neutral):
            return 'negative'
        else:
            return 'neutral'
    
    def _categorize_sentiment_intensity(self, compound_scores):
        """감정 강도 카테고리화"""
        if not compound_scores:
            return {}
        
        intensities = {
            'very_positive': len([s for s in compound_scores if s >= 0.5]),
            'positive': len([s for s in compound_scores if 0.05 <= s < 0.5]),
            'neutral': len([s for s in compound_scores if -0.05 < s < 0.05]),
            'negative': len([s for s in compound_scores if -0.5 < s <= -0.05]),
            'very_negative': len([s for s in compound_scores if s <= -0.5])
        }
        
        total = len(compound_scores)
        return {
            category: {
                'count': count,
                'percentage': round(count / total * 100, 2)
            }
            for category, count in intensities.items()
        }
    
    def _summarize_sentiment_trends(self, trends):
        """감정 트렌드 요약"""
        if not trends:
            return {}
        
        dates = sorted(trends.keys())
        
        # 각 감정의 시간별 변화
        positive_trend = [trends[date]['positive'] for date in dates]
        negative_trend = [trends[date]['negative'] for date in dates]
        neutral_trend = [trends[date]['neutral'] for date in dates]
        
        return {
            'overall_trend': {
                'positive': {
                    'avg': round(sum(positive_trend) / len(positive_trend), 2),
                    'trend': self._calculate_trend_direction(positive_trend)
                },
                'negative': {
                    'avg': round(sum(negative_trend) / len(negative_trend), 2),
                    'trend': self._calculate_trend_direction(negative_trend)
                },
                'neutral': {
                    'avg': round(sum(neutral_trend) / len(neutral_trend), 2),
                    'trend': self._calculate_trend_direction(neutral_trend)
                }
            },
            'volatility': {
                'positive': round(self._calculate_std_dev(positive_trend), 2),
                'negative': round(self._calculate_std_dev(negative_trend), 2),
                'neutral': round(self._calculate_std_dev(neutral_trend), 2)
            }
        }
    
    def _calculate_trend_direction(self, values):
        """트렌드 방향 계산"""
        if len(values) < 2:
            return 'stable'
        
        # 선형 트렌드 계산 (간단한 방법)
        first_half = sum(values[:len(values)//2]) / (len(values)//2)
        second_half = sum(values[len(values)//2:]) / (len(values) - len(values)//2)
        
        diff = second_half - first_half
        
        if diff > 2:
            return 'rising'
        elif diff < -2:
            return 'falling'
        else:
            return 'stable'
    
    def _calculate_std_dev(self, values):
        """표준편차 계산"""
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _get_available_engines(self):
        """사용 가능한 감정 분석 엔진 목록"""
        engines = ['keywords']  # 기본 키워드 방식은 항상 사용 가능
        
        if TEXTBLOB_AVAILABLE:
            engines.append('textblob')
        if VADER_AVAILABLE:
            engines.append('vader')
        
        return engines
    
    def get_analysis_info(self):
        """분석 정보 반환"""
        return {
            'language': self.language,
            'available_engines': self._get_available_engines(),
            'textblob_available': TEXTBLOB_AVAILABLE,
            'vader_available': VADER_AVAILABLE,
            'features': {
                'basic_sentiment': True,
                'sentiment_trends': True,
                'anomaly_detection': True,
                'emotional_keywords': True,
                'intensity_analysis': VADER_AVAILABLE,
                'multilingual': TEXTBLOB_AVAILABLE
            },
            'keyword_dictionary_size': {
                'positive': len(self.sentiment_keywords['positive']),
                'negative': len(self.sentiment_keywords['negative'])
            }
        }


# 감정 분석 결과 후처리 유틸리티
class SentimentResultProcessor:
    """감정 분석 결과 후처리 클래스"""
    
    @staticmethod
    def normalize_sentiment_scores(sentiment_results):
        """감정 점수 정규화"""
        total = sentiment_results['positive'] + sentiment_results['negative'] + sentiment_results['neutral']
        
        if total == 0:
            return sentiment_results
        
        return {
            'positive': round(sentiment_results['positive'] / total * 100, 2),
            'negative': round(sentiment_results['negative'] / total * 100, 2),
            'neutral': round(sentiment_results['neutral'] / total * 100, 2)
        }
    
    @staticmethod
    def get_dominant_sentiment(sentiment_results):
        """주요 감정 추출"""
        sentiments = ['positive', 'negative', 'neutral']
        max_sentiment = max(sentiments, key=lambda s: sentiment_results.get(s, 0))
        
        return {
            'dominant_sentiment': max_sentiment,
            'confidence': sentiment_results.get(max_sentiment, 0),
            'sentiment_distribution': sentiment_results
        }
    
    @staticmethod
    def calculate_sentiment_polarity(sentiment_results):
        """감정 극성 계산 (-1 ~ +1)"""
        positive = sentiment_results.get('positive', 0)
        negative = sentiment_results.get('negative', 0)
        
        total_polar = positive + negative
        if total_polar == 0:
            return 0.0
        
        polarity = (positive - negative) / total_polar
        return round(polarity, 3)