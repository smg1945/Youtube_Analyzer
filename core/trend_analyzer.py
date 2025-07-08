"""
YouTube 트렌드 분석 전용 모듈
키워드 트렌드, 급상승 분석, 연관성 분석 담당
"""

import re
from collections import Counter, defaultdict
from datetime import datetime, timedelta

# 선택적 import (설치되지 않은 경우 기본 기능으로 대체)
try:
    from konlpy.tag import Okt
    KONLPY_AVAILABLE = True
except ImportError:
    KONLPY_AVAILABLE = False

class TrendAnalyzer:
    """YouTube 트렌드 분석 클래스"""
    
    def __init__(self, youtube_client, language="ko"):
        """
        트렌드 분석기 초기화
        
        Args:
            youtube_client: YouTubeClient 인스턴스
            language (str): 분석 언어 ("ko" 또는 "en")
        """
        self.client = youtube_client
        self.language = language
        
        # 한국어 형태소 분석기 초기화
        if KONLPY_AVAILABLE and language == "ko":
            self.okt = Okt()
        else:
            self.okt = None
    
    def analyze_trending_keywords(self, region_code='KR', max_results=200):
        """
        트렌딩 키워드 분석
        
        Args:
            region_code (str): 지역 코드
            max_results (int): 분석할 영상 수
            
        Returns:
            dict: 트렌드 분석 결과
        """
        print(f"🔍 트렌딩 키워드 분석 시작 ({region_code})")
        
        try:
            # 1. 트렌딩 영상 수집
            from .video_search import TrendingVideoSearcher
            searcher = TrendingVideoSearcher(self.client)
            videos = searcher.get_category_trending_videos(region_code, max_results)
            
            if not videos:
                return {'error': '트렌딩 영상을 가져올 수 없습니다.'}
            
            print(f"✅ {len(videos)}개 트렌딩 영상 수집 완료")
            
            # 2. 키워드 추출 및 분석
            keyword_stats = self._extract_keywords_from_videos(videos)
            
            # 3. 트렌드 점수 계산
            trend_results = self._calculate_trend_scores(keyword_stats)
            
            # 4. 연관 키워드 분석
            related_keywords = self._analyze_keyword_relationships(keyword_stats)
            
            # 5. 시간대별 트렌드 분석
            temporal_trends = self._analyze_temporal_trends(videos, keyword_stats)
            
            return {
                'analysis_time': datetime.now().isoformat(),
                'region': region_code,
                'total_videos_analyzed': len(videos),
                'total_keywords_found': len(keyword_stats),
                'trending_keywords': trend_results[:50],
                'related_keywords': related_keywords,
                'temporal_trends': temporal_trends,
                'keyword_statistics': self._generate_keyword_statistics(keyword_stats)
            }
            
        except Exception as e:
            print(f"❌ 트렌딩 키워드 분석 오류: {e}")
            return {'error': str(e)}
    
    def _extract_keywords_from_videos(self, videos):
        """영상 메타데이터에서 키워드 추출"""
        keyword_stats = defaultdict(lambda: {
            'count': 0,
            'total_views': 0,
            'avg_views': 0,
            'videos': [],
            'categories': set(),
            'first_seen': None,
            'last_seen': None
        })
        
        print("🔤 키워드 추출 중...")
        
        for i, video in enumerate(videos):
            try:
                # 영상 정보 추출
                title = video['snippet']['title']
                tags = video['snippet'].get('tags', [])
                description = video['snippet'].get('description', '')[:200]
                views = int(video['statistics'].get('viewCount', 0))
                category_id = video['snippet'].get('categoryId', 'Unknown')
                published_at = video['snippet']['publishedAt']
                
                # 키워드 추출
                all_keywords = set()
                
                # 1. 제목에서 키워드 추출
                title_keywords = self._extract_keywords_from_text(title)
                all_keywords.update(title_keywords)
                
                # 2. 태그 정제
                clean_tags = [self._clean_keyword(tag) for tag in tags[:10]]
                all_keywords.update([tag for tag in clean_tags if len(tag) >= 2])
                
                # 3. 설명에서 해시태그 추출
                hashtags = re.findall(r'#(\w+)', description)
                all_keywords.update([self._clean_keyword(tag) for tag in hashtags])
                
                # 통계 업데이트
                for keyword in all_keywords:
                    if len(keyword) >= 2:
                        stats = keyword_stats[keyword]
                        stats['count'] += 1
                        stats['total_views'] += views
                        stats['categories'].add(category_id)
                        
                        video_info = {
                            'title': title,
                            'views': views,
                            'channel': video['snippet']['channelTitle'],
                            'published_at': published_at,
                            'video_id': video['id']
                        }
                        stats['videos'].append(video_info)
                        
                        # 시간 정보 업데이트
                        if stats['first_seen'] is None or published_at < stats['first_seen']:
                            stats['first_seen'] = published_at
                        if stats['last_seen'] is None or published_at > stats['last_seen']:
                            stats['last_seen'] = published_at
                
                if (i + 1) % 50 == 0:
                    print(f"   진행률: {i + 1}/{len(videos)}")
                    
            except Exception as e:
                print(f"⚠️ 영상 처리 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                continue
        
        # 평균 조회수 계산
        for keyword, stats in keyword_stats.items():
            if stats['count'] > 0:
                stats['avg_views'] = stats['total_views'] // stats['count']
                stats['categories'] = list(stats['categories'])
        
        print(f"✅ 키워드 추출 완료: {len(keyword_stats)}개 고유 키워드")
        return dict(keyword_stats)
    
    def _extract_keywords_from_text(self, text):
        """텍스트에서 핵심 키워드 추출"""
        if not text:
            return []
        
        # 특수문자 제거
        clean_text = re.sub(r'[^\w\s가-힣]', ' ', text)
        
        if self.language == "ko" and self.okt:
            # 한국어 키워드 추출
            try:
                nouns = self.okt.nouns(clean_text)
                keywords = [word for word in nouns if len(word) >= 2]
                
                # 불용어 제거
                stopwords = {'것', '수', '내', '거', '때문', '위해', '통해', '따라', '대해', '에서', '으로', '에게'}
                keywords = [word for word in keywords if word not in stopwords]
                
                return keywords[:10]  # 상위 10개
            except:
                pass
        
        # 영어 또는 한국어 처리 실패 시
        words = clean_text.lower().split()
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if len(word) > 2 and word not in stopwords]
        
        return keywords[:10]
    
    def _clean_keyword(self, keyword):
        """키워드 정제"""
        # 소문자 변환, 특수문자 제거
        keyword = re.sub(r'[^\w\s가-힣]', '', keyword.lower())
        return keyword.strip()
    
    def _calculate_trend_scores(self, keyword_stats):
        """트렌드 점수 계산"""
        trend_scores = {}
        
        for keyword, stats in keyword_stats.items():
            # 트렌드 점수 = (등장 빈도 × 평균 조회수) / 1000000
            # 추가 가중치: 카테고리 다양성, 최신성
            
            base_score = (stats['count'] * stats['avg_views']) / 1000000
            
            # 카테고리 다양성 보너스
            category_bonus = min(len(stats['categories']) * 0.1, 0.5)
            
            # 최신성 보너스 (최근 24시간 내 등장한 키워드)
            recency_bonus = 0
            if stats['last_seen']:
                try:
                    last_seen_dt = datetime.fromisoformat(stats['last_seen'].replace('Z', '+00:00'))
                    hours_ago = (datetime.now(last_seen_dt.tzinfo) - last_seen_dt).total_seconds() / 3600
                    if hours_ago <= 24:
                        recency_bonus = 0.3
                except:
                    pass
            
            final_score = base_score * (1 + category_bonus + recency_bonus)
            
            trend_scores[keyword] = {
                'score': round(final_score, 2),
                'frequency': stats['count'],
                'avg_views': stats['avg_views'],
                'total_views': stats['total_views'],
                'category_count': len(stats['categories']),
                'categories': stats['categories'],
                'recency_hours': self._calculate_recency_hours(stats['last_seen']) if stats['last_seen'] else None,
                'sample_videos': sorted(stats['videos'], key=lambda x: x['views'], reverse=True)[:3]
            }
        
        # 점수 기준 정렬
        sorted_trends = sorted(trend_scores.items(), 
                              key=lambda x: x[1]['score'], 
                              reverse=True)
        
        return [{'keyword': k, **v} for k, v in sorted_trends]
    
    def _analyze_keyword_relationships(self, keyword_stats):
        """키워드 간 연관성 분석"""
        print("🔗 키워드 연관성 분석 중...")
        
        keyword_cooccurrence = defaultdict(lambda: defaultdict(int))
        
        # 동일 영상에 등장한 키워드들의 동시 등장 빈도 계산
        for keyword, stats in keyword_stats.items():
            for video in stats['videos']:
                video_title = video['title'].lower()
                
                # 이 영상에 등장한 다른 키워드들 찾기
                for other_keyword in keyword_stats.keys():
                    if other_keyword != keyword and other_keyword.lower() in video_title:
                        keyword_cooccurrence[keyword][other_keyword] += 1
        
        # 각 키워드별 상위 연관 키워드 추출
        related_keywords = {}
        for keyword in keyword_stats.keys():
            if keyword in keyword_cooccurrence:
                related = sorted(keyword_cooccurrence[keyword].items(), 
                               key=lambda x: x[1], reverse=True)[:5]
                
                related_keywords[keyword] = [
                    {
                        'keyword': rel_keyword,
                        'cooccurrence_count': count,
                        'relevance_score': round(count / keyword_stats[keyword]['count'], 3)
                    }
                    for rel_keyword, count in related
                ]
        
        return related_keywords
    
    def _analyze_temporal_trends(self, videos, keyword_stats):
        """시간대별 트렌드 분석"""
        print("⏰ 시간대별 트렌드 분석 중...")
        
        # 시간대별 키워드 등장 빈도
        hourly_trends = defaultdict(lambda: defaultdict(int))
        daily_trends = defaultdict(lambda: defaultdict(int))
        
        for video in videos:
            try:
                published_at = video['snippet']['publishedAt']
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                
                hour = dt.hour
                day = dt.strftime('%A')
                title = video['snippet']['title']
                
                # 이 영상의 키워드들 찾기
                video_keywords = []
                for keyword in keyword_stats.keys():
                    if keyword.lower() in title.lower():
                        video_keywords.append(keyword)
                        hourly_trends[hour][keyword] += 1
                        daily_trends[day][keyword] += 1
                        
            except Exception as e:
                continue
        
        # 가장 활발한 시간대/요일 찾기
        peak_hours = {}
        peak_days = {}
        
        for hour, keywords in hourly_trends.items():
            total_activity = sum(keywords.values())
            peak_hours[hour] = total_activity
        
        for day, keywords in daily_trends.items():
            total_activity = sum(keywords.values())
            peak_days[day] = total_activity
        
        most_active_hour = max(peak_hours, key=peak_hours.get) if peak_hours else None
        most_active_day = max(peak_days, key=peak_days.get) if peak_days else None
        
        return {
            'hourly_distribution': dict(hourly_trends),
            'daily_distribution': dict(daily_trends),
            'peak_activity': {
                'hour': most_active_hour,
                'day': most_active_day,
                'hour_activity': peak_hours.get(most_active_hour, 0) if most_active_hour else 0,
                'day_activity': peak_days.get(most_active_day, 0) if most_active_day else 0
            }
        }
    
    def _generate_keyword_statistics(self, keyword_stats):
        """키워드 통계 생성"""
        if not keyword_stats:
            return {}
        
        # 기본 통계
        total_keywords = len(keyword_stats)
        frequencies = [stats['count'] for stats in keyword_stats.values()]
        avg_frequencies = [stats['avg_views'] for stats in keyword_stats.values()]
        
        return {
            'total_unique_keywords': total_keywords,
            'frequency_stats': {
                'min': min(frequencies) if frequencies else 0,
                'max': max(frequencies) if frequencies else 0,
                'avg': round(sum(frequencies) / len(frequencies), 2) if frequencies else 0
            },
            'view_stats': {
                'min_avg_views': min(avg_frequencies) if avg_frequencies else 0,
                'max_avg_views': max(avg_frequencies) if avg_frequencies else 0,
                'overall_avg_views': round(sum(avg_frequencies) / len(avg_frequencies), 2) if avg_frequencies else 0
            },
            'distribution': {
                'high_frequency_keywords': len([f for f in frequencies if f >= 10]),
                'medium_frequency_keywords': len([f for f in frequencies if 5 <= f < 10]),
                'low_frequency_keywords': len([f for f in frequencies if f < 5])
            }
        }
    
    def _calculate_recency_hours(self, timestamp):
        """최신성 계산 (시간 단위)"""
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hours_ago = (datetime.now(dt.tzinfo) - dt).total_seconds() / 3600
            return round(hours_ago, 1)
        except:
            return None
    
    def compare_trends(self, region1='KR', region2='US', max_results=100):
        """
        지역별 트렌드 비교
        
        Args:
            region1 (str): 첫 번째 지역 코드
            region2 (str): 두 번째 지역 코드
            max_results (int): 분석할 영상 수
            
        Returns:
            dict: 지역별 트렌드 비교 결과
        """
        print(f"🌍 지역별 트렌드 비교: {region1} vs {region2}")
        
        try:
            # 각 지역의 트렌드 분석
            trends1 = self.analyze_trending_keywords(region1, max_results)
            trends2 = self.analyze_trending_keywords(region2, max_results)
            
            if 'error' in trends1 or 'error' in trends2:
                return {'error': '지역별 트렌드 분석 실패'}
            
            # 공통 키워드 찾기
            keywords1 = set(item['keyword'] for item in trends1['trending_keywords'])
            keywords2 = set(item['keyword'] for item in trends2['trending_keywords'])
            
            common_keywords = keywords1 & keywords2
            unique_to_region1 = keywords1 - keywords2
            unique_to_region2 = keywords2 - keywords1
            
            # 지역별 특성 분석
            comparison = {
                'analysis_time': datetime.now().isoformat(),
                'regions_compared': [region1, region2],
                'region1_stats': {
                    'total_keywords': len(keywords1),
                    'unique_keywords': len(unique_to_region1),
                    'top_keywords': [item['keyword'] for item in trends1['trending_keywords'][:10]]
                },
                'region2_stats': {
                    'total_keywords': len(keywords2),
                    'unique_keywords': len(unique_to_region2),
                    'top_keywords': [item['keyword'] for item in trends2['trending_keywords'][:10]]
                },
                'comparison': {
                    'common_keywords_count': len(common_keywords),
                    'common_keywords': list(common_keywords)[:20],
                    'unique_to_region1': list(unique_to_region1)[:10],
                    'unique_to_region2': list(unique_to_region2)[:10],
                    'similarity_score': round(len(common_keywords) / len(keywords1 | keywords2) * 100, 2) if (keywords1 | keywords2) else 0
                }
            }
            
            return comparison
            
        except Exception as e:
            print(f"❌ 지역별 트렌드 비교 오류: {e}")
            return {'error': str(e)}
    
    def detect_emerging_trends(self, region_code='KR', hours_threshold=6):
        """
        신흥 트렌드 감지
        
        Args:
            region_code (str): 지역 코드
            hours_threshold (int): 신흥 트렌드 기준 시간 (시간)
            
        Returns:
            dict: 신흥 트렌드 정보
        """
        print(f"🚀 신흥 트렌드 감지 중... (최근 {hours_threshold}시간)")
        
        try:
            # 트렌딩 키워드 분석
            trends = self.analyze_trending_keywords(region_code)
            
            if 'error' in trends:
                return trends
            
            # 최근 등장한 키워드들 필터링
            emerging_keywords = []
            
            for item in trends['trending_keywords']:
                recency_hours = item.get('recency_hours')
                if recency_hours and recency_hours <= hours_threshold:
                    emerging_keywords.append({
                        'keyword': item['keyword'],
                        'trend_score': item['score'],
                        'frequency': item['frequency'],
                        'hours_since_first_seen': recency_hours,
                        'sample_videos': item['sample_videos']
                    })
            
            # 급상승 점수 계산 (빈도 / 시간)
            for keyword in emerging_keywords:
                keyword['velocity_score'] = round(
                    keyword['frequency'] / max(keyword['hours_since_first_seen'], 0.1), 2
                )
            
            # 급상승 점수 기준 정렬
            emerging_keywords.sort(key=lambda x: x['velocity_score'], reverse=True)
            
            return {
                'analysis_time': datetime.now().isoformat(),
                'region': region_code,
                'hours_threshold': hours_threshold,
                'emerging_trends_count': len(emerging_keywords),
                'emerging_keywords': emerging_keywords[:20],
                'detection_summary': {
                    'total_analyzed': len(trends['trending_keywords']),
                    'emerging_detected': len(emerging_keywords),
                    'emergence_rate': round(len(emerging_keywords) / len(trends['trending_keywords']) * 100, 2) if trends['trending_keywords'] else 0
                }
            }
            
        except Exception as e:
            print(f"❌ 신흥 트렌드 감지 오류: {e}")
            return {'error': str(e)}