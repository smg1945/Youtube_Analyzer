"""
YouTube 채널 분석 전용 모듈
채널 정보 수집, 영상 분석, 성과 측정 담당
"""

import re
import time
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
import config

class ChannelAnalyzer:
    """YouTube 채널 분석 클래스"""
    
    def __init__(self, youtube_client):
        """
        채널 분석기 초기화
        
        Args:
            youtube_client: YouTubeClient 인스턴스
        """
        self.client = youtube_client
        self.channel_cache = {}  # 채널 정보 캐싱
        
    def extract_channel_id_from_url(self, url_or_input):
        """
        URL이나 입력에서 채널 ID 추출
        
        Args:
            url_or_input (str): 채널 URL, ID, 핸들명 등
            
        Returns:
            tuple: (channel_id, channel_handle)
        """
        try:
            # 이미 채널 ID인 경우
            if re.match(r'^UC[a-zA-Z0-9_-]{22}$', url_or_input):
                return url_or_input, None
            
            # 채널 URL에서 ID 추출
            patterns = [
                r'youtube\.com/channel/([UC][a-zA-Z0-9_-]{22})',
                r'youtube\.com/c/([a-zA-Z0-9_.-]+)',
                r'youtube\.com/user/([a-zA-Z0-9_.-]+)',
                r'youtube\.com/@([a-zA-Z0-9_.-]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url_or_input)
                if match:
                    identifier = match.group(1)
                    
                    # UC로 시작하는 경우 채널 ID
                    if identifier.startswith('UC'):
                        return identifier, None
                    else:
                        # 핸들이나 사용자명인 경우 채널 ID로 변환 필요
                        return self.resolve_channel_handle(identifier)
            
            # 직접 핸들명인 경우
            return self.resolve_channel_handle(url_or_input)
            
        except Exception as e:
            print(f"채널 ID 추출 오류: {e}")
            return None, None
    
    def resolve_channel_handle(self, handle):
        """
        채널 핸들을 채널 ID로 변환
        
        Args:
            handle (str): 채널 핸들 또는 사용자명
            
        Returns:
            tuple: (channel_id, handle)
        """
        try:
            print(f"🔍 채널 검색 중: '{handle}'")
            
            # 채널 검색
            channels = self.client.search_channels(handle, max_results=10)
            
            if not channels:
                print(f"❌ '{handle}' 채널을 찾을 수 없습니다.")
                return None, handle
            
            # 가장 일치하는 채널 찾기
            for channel in channels:
                channel_title = channel['snippet']['title'].lower()
                channel_id = channel['id']['channelId']
                
                # 정확한 일치 또는 유사한 일치 확인
                if (handle.lower() == channel_title or 
                    handle.lower() in channel_title or 
                    channel_title in handle.lower()):
                    
                    print(f"✅ 채널 발견: {channel['snippet']['title']} (ID: {channel_id})")
                    return channel_id, handle
            
            # 첫 번째 결과 사용
            first_channel = channels[0]
            channel_id = first_channel['id']['channelId']
            channel_title = first_channel['snippet']['title']
            
            print(f"⚠️ 정확한 일치를 찾지 못했습니다. 첫 번째 결과 사용: {channel_title}")
            return channel_id, handle
            
        except Exception as e:
            print(f"채널 핸들 변환 오류: {e}")
            return None, handle
    
    def analyze_channel(self, channel_id, max_videos=50, detailed=True):
        """
        채널 종합 분석
        
        Args:
            channel_id (str): 채널 ID
            max_videos (int): 분석할 최대 영상 수
            detailed (bool): 상세 분석 여부
            
        Returns:
            dict: 채널 분석 결과
        """
        print(f"\n📊 채널 분석 시작: {channel_id}")
        
        try:
            # 1. 채널 기본 정보
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return {'error': '채널 정보를 가져올 수 없습니다.'}
            
            # 2. 채널 영상 목록
            videos = self.get_channel_videos(channel_id, max_videos)
            if not videos:
                return {'error': '채널의 영상을 찾을 수 없습니다.'}
            
            # 3. 영상 분석
            video_analysis = self.analyze_videos(videos, detailed)
            
            # 4. 채널 성과 분석
            performance_analysis = self.analyze_channel_performance(channel_info, videos)
            
            # 5. 트렌드 분석
            trend_analysis = self.analyze_channel_trends(videos)
            
            # 결과 취합
            analysis_result = {
                'channel_info': channel_info,
                'video_count': len(videos),
                'videos': videos,
                'video_analysis': video_analysis,
                'performance_analysis': performance_analysis,
                'trend_analysis': trend_analysis,
                'analysis_timestamp': datetime.now().isoformat(),
                'analysis_settings': {
                    'max_videos': max_videos,
                    'detailed': detailed
                }
            }
            
            print(f"✅ 채널 분석 완료: {len(videos)}개 영상 분석됨")
            return analysis_result
            
        except Exception as e:
            print(f"❌ 채널 분석 오류: {e}")
            return {'error': str(e)}
    
    def get_channel_info(self, channel_id):
        """캐시를 사용한 채널 정보 가져오기"""
        # 캐시 확인
        if config.ENABLE_CHANNEL_CACHE and channel_id in self.channel_cache:
            cache_time, cached_info = self.channel_cache[channel_id]
            
            # 캐시가 유효한지 확인 (30분)
            if (datetime.now() - cache_time).seconds < config.CACHE_DURATION_MINUTES * 60:
                print(f"📋 캐시에서 채널 정보 로드: {cached_info['snippet']['title']}")
                return cached_info
        
        # 새로 가져오기
        channel_info = self.client.get_channel_info(channel_id)
        
        # 캐시에 저장
        if config.ENABLE_CHANNEL_CACHE and channel_info:
            self.channel_cache[channel_id] = (datetime.now(), channel_info)
        
        return channel_info
    
    def get_channel_videos(self, channel_id, max_results=50, order='date'):
        """
        채널의 영상 목록 가져오기
        
        Args:
            channel_id (str): 채널 ID
            max_results (int): 최대 결과 수
            order (str): 정렬 기준
            
        Returns:
            list: 영상 목록
        """
        print(f"📹 채널 영상 목록 수집 중... (최대 {max_results}개)")
        
        try:
            videos = self.client.get_channel_videos(channel_id, max_results, order)
            
            if videos:
                print(f"✅ {len(videos)}개 영상 수집 완료")
            else:
                print("❌ 영상을 찾을 수 없습니다.")
            
            return videos
            
        except Exception as e:
            print(f"❌ 채널 영상 목록 가져오기 오류: {e}")
            return []
    
    def analyze_videos(self, videos, detailed=True):
        """
        영상들 분석
        
        Args:
            videos (list): 영상 목록
            detailed (bool): 상세 분석 여부
            
        Returns:
            dict: 영상 분석 결과
        """
        print(f"🔍 {len(videos)}개 영상 분석 중...")
        
        try:
            analysis = {
                'total_videos': len(videos),
                'total_views': 0,
                'total_likes': 0,
                'total_comments': 0,
                'avg_views': 0,
                'avg_likes': 0,
                'avg_comments': 0,
                'avg_engagement_rate': 0,
                'video_types': {'shorts': 0, 'long': 0},
                'top_performers': [],
                'worst_performers': [],
                'upload_frequency': {},
                'keywords': []
            }
            
            video_metrics = []
            all_keywords = []
            upload_dates = []
            
            for i, video in enumerate(videos):
                try:
                    snippet = video['snippet']
                    statistics = video['statistics']
                    
                    # 기본 지표
                    views = int(statistics.get('viewCount', 0))
                    likes = int(statistics.get('likeCount', 0))
                    comments = int(statistics.get('commentCount', 0))
                    
                    analysis['total_views'] += views
                    analysis['total_likes'] += likes
                    analysis['total_comments'] += comments
                    
                    # 참여도 계산
                    engagement_rate = ((likes + comments) / views * 100) if views > 0 else 0
                    
                    # 영상 유형 분류
                    duration = video.get('parsed_duration', '00:00')
                    is_shorts = self.is_shorts_video(duration)
                    video_type = 'shorts' if is_shorts else 'long'
                    analysis['video_types'][video_type] += 1
                    
                    # 영상별 메트릭 저장
                    video_metric = {
                        'video_id': video['id'],
                        'title': snippet['title'],
                        'views': views,
                        'likes': likes,
                        'comments': comments,
                        'engagement_rate': engagement_rate,
                        'type': video_type,
                        'published_at': snippet['publishedAt'],
                        'duration': duration
                    }
                    video_metrics.append(video_metric)
                    
                    # 업로드 날짜 수집
                    upload_date = snippet['publishedAt'][:10]
                    upload_dates.append(upload_date)
                    
                    # 키워드 추출 (간단한 방식)
                    if detailed:
                        title_keywords = self.extract_keywords_from_title(snippet['title'])
                        all_keywords.extend(title_keywords)
                    
                    # 영상에 분석 결과 추가
                    video['analysis'] = {
                        'rank': i + 1,
                        'engagement_rate': engagement_rate,
                        'outlier_score': self.calculate_outlier_score(views, engagement_rate, analysis['total_views'], len(videos)),
                        'video_type': video_type
                    }
                    
                except Exception as e:
                    print(f"영상 분석 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                    continue
            
            # 평균 계산
            if len(videos) > 0:
                analysis['avg_views'] = analysis['total_views'] // len(videos)
                analysis['avg_likes'] = analysis['total_likes'] // len(videos)
                analysis['avg_comments'] = analysis['total_comments'] // len(videos)
                
                avg_engagement = sum(vm['engagement_rate'] for vm in video_metrics) / len(video_metrics)
                analysis['avg_engagement_rate'] = avg_engagement
            
            # 상위/하위 성과 영상 (상위/하위 5개)
            video_metrics.sort(key=lambda x: x['views'], reverse=True)
            analysis['top_performers'] = video_metrics[:5]
            analysis['worst_performers'] = video_metrics[-5:] if len(video_metrics) >= 5 else []
            
            # 업로드 빈도 분석
            analysis['upload_frequency'] = self.analyze_upload_frequency(upload_dates)
            
            # 키워드 분석
            if detailed and all_keywords:
                from collections import Counter
                keyword_counts = Counter(all_keywords)
                analysis['keywords'] = [{'word': word, 'count': count} 
                                      for word, count in keyword_counts.most_common(10)]
            
            print(f"✅ 영상 분석 완료 - 평균 조회수: {analysis['avg_views']:,}, 평균 참여도: {analysis['avg_engagement_rate']:.2f}%")
            return analysis
            
        except Exception as e:
            print(f"❌ 영상 분석 오류: {e}")
            return {}
    
    def analyze_channel_performance(self, channel_info, videos):
        """
        채널 성과 분석
        
        Args:
            channel_info (dict): 채널 정보
            videos (list): 영상 목록
            
        Returns:
            dict: 성과 분석 결과
        """
        try:
            statistics = channel_info['statistics']
            
            # 기본 성과 지표
            total_subscribers = int(statistics.get('subscriberCount', 0))
            total_videos = int(statistics.get('videoCount', 0))
            total_views = int(statistics.get('viewCount', 0))
            
            # 최근 영상들의 성과
            recent_views = sum(int(video['statistics'].get('viewCount', 0)) for video in videos)
            recent_video_count = len(videos)
            
            # 성과 지표 계산
            avg_views_per_video = total_views // total_videos if total_videos > 0 else 0
            recent_avg_views = recent_views // recent_video_count if recent_video_count > 0 else 0
            
            # 구독자 대비 조회수 비율
            views_per_subscriber = total_views / total_subscribers if total_subscribers > 0 else 0
            
            # 성과 등급 계산
            performance_grade = self.calculate_performance_grade(
                total_subscribers, avg_views_per_video, recent_avg_views
            )
            
            performance_analysis = {
                'total_subscribers': total_subscribers,
                'total_videos': total_videos,
                'total_views': total_views,
                'avg_views_per_video': avg_views_per_video,
                'recent_avg_views': recent_avg_views,
                'views_per_subscriber': views_per_subscriber,
                'performance_grade': performance_grade,
                'growth_indicators': self.analyze_growth_indicators(videos),
                'consistency_score': self.calculate_consistency_score(videos)
            }
            
            print(f"📈 성과 분석 완료 - 등급: {performance_grade}, 평균 조회수: {avg_views_per_video:,}")
            return performance_analysis
            
        except Exception as e:
            print(f"❌ 성과 분석 오류: {e}")
            return {}
    
    def analyze_channel_trends(self, videos):
        """
        채널 트렌드 분석
        
        Args:
            videos (list): 영상 목록
            
        Returns:
            dict: 트렌드 분석 결과
        """
        try:
            # 시간별 성과 분석
            monthly_performance = {}
            video_types_trend = {'shorts': [], 'long': []}
            
            for video in videos:
                try:
                    published_at = video['snippet']['publishedAt']
                    month_key = published_at[:7]  # YYYY-MM
                    
                    views = int(video['statistics'].get('viewCount', 0))
                    duration = video.get('parsed_duration', '00:00')
                    video_type = 'shorts' if self.is_shorts_video(duration) else 'long'
                    
                    if month_key not in monthly_performance:
                        monthly_performance[month_key] = {
                            'views': 0, 'videos': 0, 'shorts': 0, 'long': 0
                        }
                    
                    monthly_performance[month_key]['views'] += views
                    monthly_performance[month_key]['videos'] += 1
                    monthly_performance[month_key][video_type] += 1
                    
                    video_types_trend[video_type].append({
                        'date': published_at[:10],
                        'views': views
                    })
                    
                except Exception as e:
                    print(f"트렌드 분석 중 영상 처리 오류: {e}")
                    continue
            
            # 트렌드 방향 계산
            trend_direction = self.calculate_trend_direction(monthly_performance)
            
            trend_analysis = {
                'monthly_performance': monthly_performance,
                'trend_direction': trend_direction,
                'video_types_trend': video_types_trend,
                'best_performing_month': self.find_best_month(monthly_performance),
                'content_strategy_insights': self.generate_content_insights(videos)
            }
            
            print("📊 트렌드 분석 완료")
            return trend_analysis
            
        except Exception as e:
            print(f"❌ 트렌드 분석 오류: {e}")
            return {}
    
    # 유틸리티 메서드들
    def is_shorts_video(self, duration_str):
        """영상이 쇼츠인지 판단"""
        try:
            if ':' not in duration_str:
                return False
            
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                minutes, seconds = map(int, parts)
                total_seconds = minutes * 60 + seconds
            elif len(parts) == 3:  # HH:MM:SS
                hours, minutes, seconds = map(int, parts)
                total_seconds = hours * 3600 + minutes * 60 + seconds
            else:
                return False
            
            return total_seconds <= config.SHORT_VIDEO_MAX_DURATION
            
        except Exception:
            return False
    
    def extract_keywords_from_title(self, title):
        """제목에서 키워드 추출"""
        try:
            # 간단한 키워드 추출 (한글, 영문)
            import re
            
            # 특수문자 제거 및 단어 분리
            clean_title = re.sub(r'[^\w\s가-힣]', ' ', title)
            words = [word.strip() for word in clean_title.split() if len(word.strip()) >= 2]
            
            # 불용어 제거 (간단한 리스트)
            stop_words = {'있는', '그는', '그녀', '이것', '저것', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to'}
            keywords = [word for word in words if word.lower() not in stop_words]
            
            return keywords[:5]  # 상위 5개만
            
        except Exception as e:
            print(f"키워드 추출 오류: {e}")
            return []
    
    def calculate_outlier_score(self, views, engagement_rate, total_views, video_count):
        """아웃라이어 점수 계산"""
        try:
            avg_views = total_views / video_count if video_count > 0 else 1
            view_ratio = views / avg_views if avg_views > 0 else 1
            
            # 조회수 비율과 참여도를 조합한 점수
            outlier_score = (view_ratio * 0.7 + engagement_rate * 0.3) * 10
            return min(outlier_score, 100)  # 최대 100점
            
        except Exception:
            return 0
    
    def analyze_upload_frequency(self, upload_dates):
        """업로드 빈도 분석"""
        try:
            from collections import Counter
            from datetime import datetime
            
            # 월별 업로드 수
            monthly_uploads = Counter()
            
            for date_str in upload_dates:
                month_key = date_str[:7]  # YYYY-MM
                monthly_uploads[month_key] += 1
            
            # 평균 업로드 빈도
            if monthly_uploads:
                avg_monthly = sum(monthly_uploads.values()) / len(monthly_uploads)
            else:
                avg_monthly = 0
            
            return {
                'monthly_uploads': dict(monthly_uploads),
                'avg_monthly_uploads': avg_monthly,
                'most_active_month': monthly_uploads.most_common(1)[0] if monthly_uploads else None
            }
            
        except Exception as e:
            print(f"업로드 빈도 분석 오류: {e}")
            return {}
    
    def calculate_performance_grade(self, subscribers, avg_views, recent_avg_views):
        """성과 등급 계산"""
        try:
            # 구독자 수 기반 기준점
            if subscribers < 1000:
                base_threshold = 100
            elif subscribers < 10000:
                base_threshold = 1000
            elif subscribers < 100000:
                base_threshold = 5000
            elif subscribers < 1000000:
                base_threshold = 10000
            else:
                base_threshold = 50000
            
            # 조회수 대비 등급
            if recent_avg_views >= base_threshold * 5:
                return 'S'
            elif recent_avg_views >= base_threshold * 3:
                return 'A'
            elif recent_avg_views >= base_threshold * 2:
                return 'B'
            elif recent_avg_views >= base_threshold:
                return 'C'
            else:
                return 'D'
                
        except Exception:
            return 'Unknown'
    
    def analyze_growth_indicators(self, videos):
        """성장 지표 분석"""
        try:
            if len(videos) < 5:
                return {'trend': 'insufficient_data'}
            
            # 최근 5개와 이전 5개 비교
            recent_videos = videos[:5]
            older_videos = videos[-5:] if len(videos) >= 10 else videos[5:10]
            
            recent_avg = sum(int(v['statistics'].get('viewCount', 0)) for v in recent_videos) / len(recent_videos)
            older_avg = sum(int(v['statistics'].get('viewCount', 0)) for v in older_videos) / len(older_videos)
            
            if older_avg == 0:
                growth_rate = 0
            else:
                growth_rate = ((recent_avg - older_avg) / older_avg) * 100
            
            if growth_rate > 20:
                trend = 'growing'
            elif growth_rate > -10:
                trend = 'stable'
            else:
                trend = 'declining'
            
            return {
                'trend': trend,
                'growth_rate': growth_rate,
                'recent_avg_views': recent_avg,
                'older_avg_views': older_avg
            }
            
        except Exception as e:
            print(f"성장 지표 분석 오류: {e}")
            return {'trend': 'unknown'}
    
    def calculate_consistency_score(self, videos):
        """일관성 점수 계산"""
        try:
            if len(videos) < 3:
                return 0
            
            view_counts = [int(v['statistics'].get('viewCount', 0)) for v in videos]
            
            # 표준편차를 이용한 일관성 측정
            mean_views = sum(view_counts) / len(view_counts)
            variance = sum((x - mean_views) ** 2 for x in view_counts) / len(view_counts)
            std_dev = variance ** 0.5
            
            # 변동계수 (CV) 계산
            cv = (std_dev / mean_views) * 100 if mean_views > 0 else 100
            
            # 일관성 점수 (CV가 낮을수록 높은 점수)
            consistency_score = max(0, 100 - cv)
            
            return min(consistency_score, 100)
            
        except Exception as e:
            print(f"일관성 점수 계산 오류: {e}")
            return 0
    
    def calculate_trend_direction(self, monthly_performance):
        """트렌드 방향 계산"""
        try:
            if len(monthly_performance) < 2:
                return 'insufficient_data'
            
            # 월별 평균 조회수 계산
            monthly_averages = []
            for month_data in monthly_performance.values():
                if month_data['videos'] > 0:
                    avg_views = month_data['views'] / month_data['videos']
                    monthly_averages.append(avg_views)
            
            if len(monthly_averages) < 2:
                return 'insufficient_data'
            
            # 최근 3개월과 이전 비교
            recent_avg = sum(monthly_averages[-3:]) / min(3, len(monthly_averages))
            older_avg = sum(monthly_averages[:-3]) / max(1, len(monthly_averages) - 3)
            
            if recent_avg > older_avg * 1.2:
                return 'upward'
            elif recent_avg < older_avg * 0.8:
                return 'downward'
            else:
                return 'stable'
                
        except Exception as e:
            print(f"트렌드 방향 계산 오류: {e}")
            return 'unknown'
    
    def find_best_month(self, monthly_performance):
        """최고 성과 월 찾기"""
        try:
            best_month = None
            best_avg_views = 0
            
            for month, data in monthly_performance.items():
                if data['videos'] > 0:
                    avg_views = data['views'] / data['videos']
                    if avg_views > best_avg_views:
                        best_avg_views = avg_views
                        best_month = month
            
            return {
                'month': best_month,
                'avg_views': best_avg_views
            } if best_month else None
            
        except Exception as e:
            print(f"최고 성과 월 찾기 오류: {e}")
            return None
    
    def generate_content_insights(self, videos):
        """콘텐츠 전략 인사이트 생성"""
        try:
            insights = []
            
            # 영상 유형별 성과 분석
            shorts_performance = []
            long_performance = []
            
            for video in videos:
                views = int(video['statistics'].get('viewCount', 0))
                duration = video.get('parsed_duration', '00:00')
                
                if self.is_shorts_video(duration):
                    shorts_performance.append(views)
                else:
                    long_performance.append(views)
            
            # 쇼츠 vs 롱폼 비교
            if shorts_performance and long_performance:
                shorts_avg = sum(shorts_performance) / len(shorts_performance)
                long_avg = sum(long_performance) / len(long_performance)
                
                if shorts_avg > long_avg * 1.5:
                    insights.append("쇼츠 콘텐츠가 더 높은 조회수를 기록하고 있습니다.")
                elif long_avg > shorts_avg * 1.5:
                    insights.append("롱폼 콘텐츠가 더 높은 조회수를 기록하고 있습니다.")
                else:
                    insights.append("쇼츠와 롱폼 콘텐츠의 성과가 비슷합니다.")
            
            # 업로드 시간 패턴 (향후 구현)
            # 제목 패턴 분석 (향후 구현)
            
            return insights
            
        except Exception as e:
            print(f"콘텐츠 인사이트 생성 오류: {e}")
            return []
    
    def clear_cache(self):
        """캐시 정리"""
        self.channel_cache.clear()
        print("🧹 채널 분석 캐시가 정리되었습니다.")
    
    def get_cache_info(self):
        """캐시 정보 반환"""
        return {
            'cached_channels': len(self.channel_cache),
            'cache_enabled': config.ENABLE_CHANNEL_CACHE,
            'cache_duration': config.CACHE_DURATION_MINUTES
        }


# 편의 함수들
def quick_channel_analysis(api_key, channel_input, max_videos=50):
    """
    빠른 채널 분석
    
    Args:
        api_key (str): YouTube API 키
        channel_input (str): 채널 URL 또는 ID
        max_videos (int): 분석할 최대 영상 수
        
    Returns:
        dict: 채널 분석 결과
    """
    try:
        from .youtube_client import YouTubeClient
        
        client = YouTubeClient(api_key)
        analyzer = ChannelAnalyzer(client)
        
        # 채널 ID 추출
        channel_id, _ = analyzer.extract_channel_id_from_url(channel_input)
        if not channel_id:
            return {'error': '유효하지 않은 채널 정보입니다.'}
        
        return analyzer.analyze_channel(channel_id, max_videos)
        
    except Exception as e:
        return {'error': str(e)}


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 채널 분석기 테스트")
    
    import config
    if config.DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("❌ API 키가 설정되지 않았습니다.")
    else:
        try:
            from .youtube_client import YouTubeClient
            
            client = YouTubeClient(config.DEVELOPER_KEY)
            analyzer = ChannelAnalyzer(client)
            
            # 테스트 채널 (YouTube 공식 채널)
            test_channel = "UC_x5XG1OV2P6uZZ5FSM9Ttw"  # YouTube 공식 채널
            
            print(f"테스트 채널 분석: {test_channel}")
            result = analyzer.analyze_channel(test_channel, max_videos=10, detailed=False)
            
            if 'error' not in result:
                print("✅ 채널 분석 테스트 성공")
                channel_name = result['channel_info']['snippet']['title']
                video_count = result['video_count']
                print(f"   채널명: {channel_name}")
                print(f"   분석된 영상 수: {video_count}")
            else:
                print(f"❌ 채널 분석 테스트 실패: {result['error']}")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")