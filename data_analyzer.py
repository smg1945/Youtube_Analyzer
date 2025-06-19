"""
데이터 분석 관련 함수들 (키워드 추출, 감정 분석 등)
"""

import re
from collections import Counter
from datetime import datetime
import config

# 언어별 분석 도구
try:
    from konlpy.tag import Okt  # 한국어 형태소 분석
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("KoNLPy가 설치되지 않았습니다. 한국어 키워드 추출이 제한됩니다.")

try:
    from textblob import TextBlob  # 영어 감정 분석
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False
    print("TextBlob이 설치되지 않았습니다. 감정 분석이 제한됩니다.")

class DataAnalyzer:
    def __init__(self, language="ko"):
        """
        데이터 분석기 초기화
        
        Args:
            language (str): 분석 언어 ("ko" 또는 "en")
        """
        self.language = language
        
        # 한국어 형태소 분석기 초기화
        if KONLPY_AVAILABLE and language == "ko":
            self.okt = Okt()
        else:
            self.okt = None
    
    def extract_keywords_from_title(self, title, max_keywords=10):
        """
        제목에서 키워드 추출
        
        Args:
            title (str): 영상 제목
            max_keywords (int): 최대 키워드 개수
            
        Returns:
            list: 키워드 목록
        """
        if not title:
            return []
        
        if self.language == "ko" and self.okt:
            return self._extract_korean_keywords(title, max_keywords)
        else:
            return self._extract_english_keywords(title, max_keywords)
    
    def _extract_korean_keywords(self, text, max_keywords):
        """한국어 키워드 추출"""
        try:
            # 명사와 형용사만 추출
            morphs = self.okt.pos(text, stem=True)
            keywords = [word for word, pos in morphs 
                       if pos in ['Noun', 'Adjective'] and len(word) > 1]
            
            # 불용어 제거
            stopwords = {'것', '수', '내', '거', '때문', '위해', '통해', '따라', '대해', '에서', '으로', '에게'}
            keywords = [word for word in keywords if word not in stopwords]
            
            # 빈도수 기준으로 정렬
            keyword_counts = Counter(keywords)
            return [keyword for keyword, _ in keyword_counts.most_common(max_keywords)]
            
        except Exception as e:
            print(f"한국어 키워드 추출 오류: {e}")
            return self._extract_english_keywords(text, max_keywords)
    
    def _extract_english_keywords(self, text, max_keywords):
        """영어 키워드 추출"""
        try:
            # 특수문자 제거 및 소문자 변환
            cleaned_text = re.sub(r'[^a-zA-Z가-힣\s]', ' ', text)
            words = cleaned_text.lower().split()
            
            # 불용어 제거
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 
                        'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were',
                        '그', '이', '저', '것', '수', '내', '거', '때문', '위해'}
            
            keywords = [word for word in words 
                       if len(word) > 2 and word not in stopwords]
            
            # 빈도수 기준으로 정렬
            keyword_counts = Counter(keywords)
            return [keyword for keyword, _ in keyword_counts.most_common(max_keywords)]
            
        except Exception as e:
            print(f"키워드 추출 오류: {e}")
            return []
    
    def analyze_comments_sentiment(self, comments):
        """
        댓글 감정 분석
        
        Args:
            comments (list): 댓글 목록
            
        Returns:
            dict: 감정 분석 결과 {'positive': float, 'neutral': float, 'negative': float}
        """
        if not comments:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
        
        if TEXTBLOB_AVAILABLE:
            return self._analyze_sentiment_textblob(comments)
        else:
            return self._analyze_sentiment_keywords(comments)
    
    def _analyze_sentiment_textblob(self, comments):
        """TextBlob을 사용한 감정 분석"""
        positive_count = 0
        negative_count = 0
        neutral_count = 0
        
        for comment in comments:
            try:
                blob = TextBlob(comment['text'])
                polarity = blob.sentiment.polarity
                
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
            'negative': round(negative_count / total * 100, 2)
        }
    
    def _analyze_sentiment_keywords(self, comments):
        """키워드 기반 간단한 감정 분석"""
        positive_keywords = {
            'ko': ['좋다', '최고', '대박', '멋지다', '훌륭', '완벽', '사랑', '감사', '재밌', '웃겨', '굿'],
            'en': ['good', 'great', 'amazing', 'awesome', 'perfect', 'love', 'best', 'wonderful', 'excellent']
        }
        
        negative_keywords = {
            'ko': ['싫다', '별로', '최악', '나쁘다', '짜증', '화나', '실망', '안좋', '못해'],
            'en': ['bad', 'terrible', 'awful', 'hate', 'worst', 'disappointing', 'boring', 'stupid']
        }
        
        pos_words = positive_keywords.get(self.language, positive_keywords['en'])
        neg_words = negative_keywords.get(self.language, negative_keywords['en'])
        
        positive_count = 0
        negative_count = 0
        
        for comment in comments:
            text = comment['text'].lower()
            
            # 긍정 키워드 체크
            if any(word in text for word in pos_words):
                positive_count += 1
            # 부정 키워드 체크
            elif any(word in text for word in neg_words):
                negative_count += 1
        
        total = len(comments)
        neutral_count = total - positive_count - negative_count
        
        if total == 0:
            return {'positive': 0.0, 'neutral': 0.0, 'negative': 0.0}
        
        return {
            'positive': round(positive_count / total * 100, 2),
            'neutral': round(neutral_count / total * 100, 2),
            'negative': round(negative_count / total * 100, 2)
        }
    
    def calculate_engagement_score(self, video_data):
        """
        참여도 점수 계산
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            float: 참여도 점수 (0-100)
        """
        try:
            stats = video_data.get('statistics', {})
            
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            comment_count = int(stats.get('commentCount', 0))
            
            if view_count == 0:
                return 0.0
            
            # 참여도 점수 계산 (가중 평균)
            like_ratio = (like_count / view_count) * 100
            comment_ratio = (comment_count / view_count) * 100
            
            # 가중치: 좋아요 70%, 댓글 30%
            engagement_score = (like_ratio * 0.7 + comment_ratio * 0.3) * 1000
            
            # 0-100 범위로 정규화
            return min(round(engagement_score, 2), 100.0)
            
        except Exception as e:
            print(f"참여도 점수 계산 오류: {e}")
            return 0.0
    
    def format_duration(self, duration_seconds):
        """
        초 단위 duration을 시:분:초 형태로 변환
        
        Args:
            duration_seconds (int): 초 단위 duration
            
        Returns:
            str: "HH:MM:SS" 또는 "MM:SS" 형태
        """
        if duration_seconds < 3600:  # 1시간 미만
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        else:  # 1시간 이상
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def determine_video_type(self, duration_seconds):
        """
        영상 길이를 기준으로 영상 유형 결정
        
        Args:
            duration_seconds (int): 영상 길이 (초)
            
        Returns:
            str: "쇼츠" 또는 "롱폼"
        """
        if duration_seconds <= config.SHORT_VIDEO_MAX_DURATION:
            return "쇼츠"
        else:
            return "롱폼"
    
    def calculate_views_per_day(self, video_data):
        """
        일일 평균 조회수 계산
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            float: 일일 평균 조회수
        """
        try:
            published_at = video_data['snippet']['publishedAt']
            view_count = int(video_data['statistics'].get('viewCount', 0))
            
            # 업로드 날짜 파싱
            upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_date = datetime.now(upload_date.tzinfo)
            
            # 경과 일수 계산
            days_elapsed = (current_date - upload_date).days
            if days_elapsed == 0:
                days_elapsed = 1  # 최소 1일로 처리
            
            return round(view_count / days_elapsed, 2)
            
        except Exception as e:
            print(f"일일 평균 조회수 계산 오류: {e}")
            return 0.0
    
    def extract_trending_keywords(self, all_titles, max_keywords=20):
        """
        전체 제목에서 트렌딩 키워드 추출
        
        Args:
            all_titles (list): 모든 영상 제목 목록
            max_keywords (int): 최대 키워드 개수
            
        Returns:
            list: 트렌딩 키워드 목록 (빈도순)
        """
        all_keywords = []
        
        for title in all_titles:
            keywords = self.extract_keywords_from_title(title, max_keywords=50)
            all_keywords.extend(keywords)
        
        keyword_counts = Counter(all_keywords)
        return [keyword for keyword, count in keyword_counts.most_common(max_keywords)]
    
    def calculate_outlier_score(self, current_video_stats, channel_avg_stats):
        """
        vidIQ의 Outlier Score와 유사한 지표 계산
        
        Args:
            current_video_stats (dict): 현재 영상 통계
            channel_avg_stats (dict): 채널 평균 통계
            
        Returns:
            float: outlier score (1.0 = 평균, 2.0 = 평균의 2배, 등)
        """
        if not channel_avg_stats or not current_video_stats:
            return 1.0
        
        try:
            current_views = int(current_video_stats.get('viewCount', 0))
            current_likes = int(current_video_stats.get('likeCount', 0))
            current_comments = int(current_video_stats.get('commentCount', 0))
            
            avg_views = channel_avg_stats.get('avg_views', 1)
            avg_likes = channel_avg_stats.get('avg_likes', 1)
            avg_comments = channel_avg_stats.get('avg_comments', 1)
            
            # 0으로 나누기 방지
            if avg_views == 0:
                avg_views = 1
            if avg_likes == 0:
                avg_likes = 1
            if avg_comments == 0:
                avg_comments = 1
            
            # 각 지표별 배수 계산
            views_ratio = current_views / avg_views
            likes_ratio = current_likes / avg_likes
            comments_ratio = current_comments / avg_comments
            
            # 가중 평균으로 outlier score 계산
            # 조회수 50%, 좋아요 30%, 댓글 20% 가중치
            outlier_score = (views_ratio * 0.5 + likes_ratio * 0.3 + comments_ratio * 0.2)
            
            return round(outlier_score, 2)
            
        except Exception as e:
            print(f"Outlier score 계산 오류: {e}")
            return 1.0
    
    def categorize_outlier_score(self, outlier_score):
        """
        Outlier Score를 카테고리로 분류
        
        Args:
            outlier_score (float): outlier score
            
        Returns:
            str: 카테고리 ("🔥 바이럴", "⭐ 히트", "📈 양호", "😐 평균", "📉 저조")
        """
        if outlier_score >= 5.0:
            return "🔥 바이럴"
        elif outlier_score >= 3.0:
            return "⭐ 히트"
        elif outlier_score >= 1.5:
            return "📈 양호"
        elif outlier_score >= 0.7:
            return "😐 평균"
        else:
            return "📉 저조"