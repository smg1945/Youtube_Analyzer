"""
텍스트 및 키워드 분석 전용 모듈
키워드 추출, 텍스트 정리, 언어 처리 담당
"""

import re
from collections import Counter

# 선택적 import
try:
    from konlpy.tag import Okt
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False
    print("⚠️ KoNLPy가 설치되지 않았습니다. 한국어 키워드 추출이 제한됩니다.")

class TextAnalyzer:
    """텍스트 및 키워드 분석 클래스"""
    
    def __init__(self, language="ko"):
        """
        텍스트 분석기 초기화
        
        Args:
            language (str): 분석 언어 ("ko" 또는 "en")
        """
        self.language = language
        
        # 한국어 형태소 분석기 초기화
        if KONLPY_AVAILABLE and language == "ko":
            try:
                self.okt = Okt()
                print("✅ 한국어 형태소 분석기 초기화 완료")
            except Exception as e:
                print(f"⚠️ 형태소 분석기 초기화 실패: {e}")
                self.okt = None
        else:
            self.okt = None
        
        # 언어별 불용어 설정
        self.stopwords = self._load_stopwords(language)
    
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
            keywords = [word for word in keywords if word not in self.stopwords['ko']]
            
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
            keywords = [word for word in words 
                       if len(word) > 2 and word not in self.stopwords['en']]
            
            # 빈도수 기준으로 정렬
            keyword_counts = Counter(keywords)
            return [keyword for keyword, _ in keyword_counts.most_common(max_keywords)]
            
        except Exception as e:
            print(f"키워드 추출 오류: {e}")
            return []
    
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
    
    def analyze_keyword_frequency(self, titles):
        """
        키워드 빈도 분석
        
        Args:
            titles (list): 제목 목록
            
        Returns:
            dict: 키워드 빈도 분석 결과
        """
        all_keywords = []
        title_keyword_map = {}
        
        # 각 제목별 키워드 추출
        for i, title in enumerate(titles):
            keywords = self.extract_keywords_from_title(title)
            all_keywords.extend(keywords)
            title_keyword_map[i] = keywords
        
        # 빈도 분석
        keyword_counts = Counter(all_keywords)
        total_keywords = len(all_keywords)
        unique_keywords = len(keyword_counts)
        
        # 키워드별 상세 정보
        keyword_details = {}
        for keyword, count in keyword_counts.items():
            # 이 키워드가 포함된 제목들
            containing_titles = []
            for title_idx, keywords in title_keyword_map.items():
                if keyword in keywords:
                    containing_titles.append({
                        'index': title_idx,
                        'title': titles[title_idx] if title_idx < len(titles) else ''
                    })
            
            keyword_details[keyword] = {
                'count': count,
                'frequency': round(count / total_keywords * 100, 2),
                'title_coverage': round(len(containing_titles) / len(titles) * 100, 2),
                'containing_titles': containing_titles[:5]  # 상위 5개만
            }
        
        return {
            'total_keywords': total_keywords,
            'unique_keywords': unique_keywords,
            'top_keywords': [
                {
                    'keyword': keyword,
                    **details
                }
                for keyword, details in sorted(
                    keyword_details.items(),
                    key=lambda x: x[1]['count'],
                    reverse=True
                )[:20]
            ],
            'keyword_diversity': round(unique_keywords / total_keywords * 100, 2) if total_keywords > 0 else 0
        }
    
    def clean_text(self, text):
        """
        텍스트 정리
        
        Args:
            text (str): 원본 텍스트
            
        Returns:
            str: 정리된 텍스트
        """
        if not text:
            return ""
        
        # 1. HTML 태그 제거
        text = re.sub(r'<[^>]+>', '', text)
        
        # 2. 특수문자 정리
        text = re.sub(r'[^\w\s가-힣.,!?]', ' ', text)
        
        # 3. 연속된 공백 제거
        text = re.sub(r'\s+', ' ', text)
        
        # 4. 앞뒤 공백 제거
        text = text.strip()
        
        return text
    
    def extract_hashtags(self, text):
        """
        해시태그 추출
        
        Args:
            text (str): 텍스트
            
        Returns:
            list: 해시태그 목록
        """
        if not text:
            return []
        
        # #키워드 형태의 해시태그 추출
        hashtags = re.findall(r'#(\w+)', text)
        
        # 정리 및 필터링
        cleaned_hashtags = []
        for tag in hashtags:
            cleaned_tag = self.clean_text(tag)
            if len(cleaned_tag) >= 2:
                cleaned_hashtags.append(cleaned_tag)
        
        return cleaned_hashtags
    
    def analyze_text_patterns(self, texts):
        """
        텍스트 패턴 분석
        
        Args:
            texts (list): 텍스트 목록
            
        Returns:
            dict: 패턴 분석 결과
        """
        if not texts:
            return {}
        
        # 기본 통계
        lengths = [len(text) for text in texts if text]
        word_counts = [len(text.split()) for text in texts if text]
        
        # 특수 패턴 감지
        patterns = {
            'with_numbers': len([t for t in texts if re.search(r'\d', t)]),
            'with_exclamation': len([t for t in texts if '!' in t]),
            'with_question': len([t for t in texts if '?' in t]),
            'with_emoji': len([t for t in texts if re.search(r'[😀-🙏]', t)]),
            'with_brackets': len([t for t in texts if re.search(r'[\[\](){}]', t)]),
            'with_quotes': len([t for t in texts if re.search(r'["\'\`]', t)])
        }
        
        # 언어 감지
        korean_count = len([t for t in texts if re.search(r'[가-힣]', t)])
        english_count = len([t for t in texts if re.search(r'[a-zA-Z]', t)])
        
        return {
            'total_texts': len(texts),
            'length_stats': {
                'min': min(lengths) if lengths else 0,
                'max': max(lengths) if lengths else 0,
                'avg': round(sum(lengths) / len(lengths), 2) if lengths else 0
            },
            'word_count_stats': {
                'min': min(word_counts) if word_counts else 0,
                'max': max(word_counts) if word_counts else 0,
                'avg': round(sum(word_counts) / len(word_counts), 2) if word_counts else 0
            },
            'pattern_analysis': {
                **patterns,
                'pattern_percentages': {
                    key: round(count / len(texts) * 100, 2)
                    for key, count in patterns.items()
                }
            },
            'language_distribution': {
                'korean': korean_count,
                'english': english_count,
                'korean_percentage': round(korean_count / len(texts) * 100, 2),
                'english_percentage': round(english_count / len(texts) * 100, 2)
            }
        }
    
    def find_similar_texts(self, target_text, text_list, threshold=0.7):
        """
        유사한 텍스트 찾기
        
        Args:
            target_text (str): 기준 텍스트
            text_list (list): 비교할 텍스트 목록
            threshold (float): 유사도 임계값
            
        Returns:
            list: 유사한 텍스트들과 유사도 점수
        """
        similar_texts = []
        
        target_keywords = set(self.extract_keywords_from_title(target_text))
        
        for i, text in enumerate(text_list):
            if text == target_text:
                continue
            
            text_keywords = set(self.extract_keywords_from_title(text))
            
            # 자카드 유사도 계산
            intersection = len(target_keywords & text_keywords)
            union = len(target_keywords | text_keywords)
            
            similarity = intersection / union if union > 0 else 0
            
            if similarity >= threshold:
                similar_texts.append({
                    'index': i,
                    'text': text,
                    'similarity': round(similarity, 3),
                    'common_keywords': list(target_keywords & text_keywords)
                })
        
        # 유사도 순으로 정렬
        similar_texts.sort(key=lambda x: x['similarity'], reverse=True)
        
        return similar_texts
    
    def _load_stopwords(self, language):
        """언어별 불용어 로드"""
        stopwords = {
            'ko': {
                '것', '수', '내', '거', '때문', '위해', '통해', '따라', '대해', 
                '에서', '으로', '에게', '이것', '그것', '저것', '여기', '거기', 
                '저기', '지금', '그때', '이때', '오늘', '어제', '내일', '년', 
                '월', '일', '시간', '분', '초', '때', '동안', '사이', '다음',
                '이전', '전체', '부분', '모든', '각각', '하나', '둘', '셋'
            },
            'en': {
                'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 
                'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 
                'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 
                'will', 'would', 'could', 'should', 'may', 'might', 'must', 
                'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 
                'she', 'it', 'we', 'they', 'me', 'him', 'her', 'us', 'them',
                'my', 'your', 'his', 'her', 'its', 'our', 'their'
            }
        }
        
        return stopwords
    
    def get_language_support_info(self):
        """언어 지원 정보 반환"""
        return {
            'current_language': self.language,
            'konlpy_available': KONLPY_AVAILABLE,
            'morphological_analysis': self.okt is not None,
            'supported_languages': ['ko', 'en'],
            'features': {
                'keyword_extraction': True,
                'text_cleaning': True,
                'hashtag_extraction': True,
                'pattern_analysis': True,
                'similarity_analysis': True,
                'korean_morphology': self.okt is not None
            }
        }


class KeywordTrendAnalyzer:
    """키워드 트렌드 전문 분석 클래스"""
    
    def __init__(self, text_analyzer):
        """
        키워드 트렌드 분석기 초기화
        
        Args:
            text_analyzer: TextAnalyzer 인스턴스
        """
        self.text_analyzer = text_analyzer
    
    def analyze_keyword_trends_over_time(self, time_series_data):
        """
        시간에 따른 키워드 트렌드 분석
        
        Args:
            time_series_data (list): [{'date': '2024-01-01', 'texts': [...]}] 형태
            
        Returns:
            dict: 시간별 키워드 트렌드
        """
        keyword_timeline = {}
        
        for data_point in time_series_data:
            date = data_point['date']
            texts = data_point['texts']
            
            # 해당 날짜의 키워드 추출
            all_keywords = []
            for text in texts:
                keywords = self.text_analyzer.extract_keywords_from_title(text)
                all_keywords.extend(keywords)
            
            keyword_counts = Counter(all_keywords)
            keyword_timeline[date] = dict(keyword_counts)
        
        # 트렌드 분석
        trending_keywords = self._calculate_keyword_velocity(keyword_timeline)
        
        return {
            'timeline': keyword_timeline,
            'trending_keywords': trending_keywords,
            'analysis_period': {
                'start_date': min(keyword_timeline.keys()) if keyword_timeline else None,
                'end_date': max(keyword_timeline.keys()) if keyword_timeline else None,
                'total_days': len(keyword_timeline)
            }
        }
    
    def _calculate_keyword_velocity(self, timeline):
        """키워드 상승/하락 속도 계산"""
        if len(timeline) < 2:
            return []
        
        dates = sorted(timeline.keys())
        velocities = {}
        
        for keyword in set().union(*timeline.values()):
            counts = []
            for date in dates:
                count = timeline[date].get(keyword, 0)
                counts.append(count)
            
            # 선형 회귀로 트렌드 계산 (간단 버전)
            if len(counts) >= 2:
                velocity = counts[-1] - counts[0]  # 마지막 - 첫번째
                avg_count = sum(counts) / len(counts)
                
                if avg_count > 0:
                    velocities[keyword] = {
                        'velocity': velocity,
                        'relative_velocity': velocity / avg_count,
                        'avg_frequency': avg_count,
                        'trend': 'rising' if velocity > 0 else 'falling' if velocity < 0 else 'stable'
                    }
        
        # 속도 순으로 정렬
        sorted_velocities = sorted(
            velocities.items(),
            key=lambda x: x[1]['relative_velocity'],
            reverse=True
        )
        
        return [
            {
                'keyword': keyword,
                **data
            }
            for keyword, data in sorted_velocities[:20]
        ]
    
    def find_keyword_clusters(self, texts, min_cluster_size=3):
        """
        키워드 클러스터링
        
        Args:
            texts (list): 텍스트 목록
            min_cluster_size (int): 최소 클러스터 크기
            
        Returns:
            dict: 키워드 클러스터 정보
        """
        # 모든 텍스트에서 키워드 추출
        text_keywords = []
        for text in texts:
            keywords = self.text_analyzer.extract_keywords_from_title(text)
            text_keywords.append(set(keywords))
        
        # 키워드 동시 출현 매트릭스 구성
        all_keywords = set().union(*text_keywords)
        cooccurrence = {}
        
        for kw1 in all_keywords:
            cooccurrence[kw1] = {}
            for kw2 in all_keywords:
                if kw1 != kw2:
                    count = sum(1 for keywords in text_keywords 
                              if kw1 in keywords and kw2 in keywords)
                    cooccurrence[kw1][kw2] = count
        
        # 간단한 클러스터링 (높은 동시 출현 빈도 기준)
        clusters = []
        used_keywords = set()
        
        for keyword in sorted(all_keywords, 
                            key=lambda k: sum(cooccurrence[k].values()), 
                            reverse=True):
            
            if keyword in used_keywords:
                continue
            
            # 이 키워드와 자주 함께 나타나는 키워드들 찾기
            related = []
            for other_kw, count in cooccurrence[keyword].items():
                if count >= min_cluster_size and other_kw not in used_keywords:
                    related.append((other_kw, count))
            
            if len(related) >= min_cluster_size - 1:
                cluster_keywords = [keyword] + [kw for kw, _ in related[:5]]
                clusters.append({
                    'cluster_id': len(clusters) + 1,
                    'main_keyword': keyword,
                    'related_keywords': cluster_keywords[1:],
                    'size': len(cluster_keywords),
                    'strength': sum(count for _, count in related[:5])
                })
                
                used_keywords.update(cluster_keywords)
        
        return {
            'clusters': clusters,
            'total_clusters': len(clusters),
            'clustered_keywords': len(used_keywords),
            'unclustered_keywords': len(all_keywords) - len(used_keywords)
        }