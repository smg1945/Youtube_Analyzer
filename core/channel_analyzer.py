"""
YouTube 채널 분석 전용 모듈
채널 정보 수집, 영상 분석, 통계 계산 담당
"""

import re
import urllib.parse
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError

class ChannelAnalyzer:
    """YouTube 채널 분석 클래스"""
    
    def __init__(self, youtube_client):
        """
        채널 분석기 초기화
        
        Args:
            youtube_client: YouTubeClient 인스턴스
        """
        self.client = youtube_client
    
    def analyze_channel(self, channel_id, video_count=50, sort_order="date"):
        """
        채널 종합 분석
        
        Args:
            channel_id (str): 채널 ID
            video_count (int): 분석할 영상 수
            sort_order (str): 정렬 순서 ("date", "viewCount")
            
        Returns:
            dict: 채널 분석 결과
        """
        print(f"📺 채널 분석 시작: {channel_id}")
        
        try:
            # 1. 채널 기본 정보
            channel_info = self.client.get_channel_info(channel_id)
            if not channel_info:
                return {'error': '채널 정보를 찾을 수 없습니다.'}
            
            # 2. 채널 영상 목록
            videos = self.get_channel_videos(channel_id, video_count, sort_order)
            if not videos:
                return {'error': '채널 영상을 가져올 수 없습니다.'}
            
            # 3. 채널 통계 계산
            channel_stats = self.calculate_channel_statistics(videos)
            
            # 4. 성과 분석
            performance_analysis = self.analyze_video_performance(videos)
            
            # 5. 트렌드 분석
            trend_analysis = self.analyze_upload_trends(videos)
            
            # 6. 컨텐츠 분석
            content_analysis = self.analyze_content_patterns(videos)
            
            return {
                'channel_info': channel_info,
                'videos': videos,
                'statistics': channel_stats,
                'performance': performance_analysis,
                'trends': trend_analysis,
                'content': content_analysis,
                'analyzed_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            print(f"❌ 채널 분석 오류: {e}")
            return {'error': str(e)}
    
    def get_channel_videos(self, channel_id, max_results=50, order='date'):
        """
        채널의 영상 목록 가져오기
        
        Args:
            channel_id (str): 채널 ID
            max_results (int): 최대 영상 수
            order (str): 정렬 순서
            
        Returns:
            list: 영상 목록
        """
        try:
            print(f"📹 채널 영상 수집: {max_results}개")
            
            # 1. 채널의 업로드 플레이리스트 ID 가져오기
            channel_request = self.client.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response['items']:
                print(f"❌ 채널 정보를 찾을 수 없습니다: {channel_id}")
                return []
            
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            self.client.quota_used += 1
            
            # 2. 플레이리스트에서 영상 목록 가져오기
            playlist_items = self.client.get_playlist_items(uploads_playlist_id, max_results)
            
            if not playlist_items:
                return []
            
            # 3. 영상 ID 추출
            video_ids = [item['snippet']['resourceId']['videoId'] for item in playlist_items]
            
            # 4. 영상 상세 정보 가져오기
            videos = self.client.get_video_details(video_ids)
            
            # 5. 정렬
            if order == 'viewCount':
                videos.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
            elif order == 'date':
                videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
            
            print(f"✅ 채널 영상 수집 완료: {len(videos)}개")
            return videos
            
        except Exception as e:
            print(f"❌ 채널 영상 목록 가져오기 오류: {e}")
            return []
    
    def calculate_channel_statistics(self, videos):
        """
        채널 통계 계산
        
        Args:
            videos (list): 영상 목록
            
        Returns:
            dict: 채널 통계
        """
        if not videos:
            return {}
        
        try:
            # 기본 통계
            total_videos = len(videos)
            total_views = sum(int(v['statistics'].get('viewCount', 0)) for v in videos)
            total_likes = sum(int(v['statistics'].get('likeCount', 0)) for v in videos)
            total_comments = sum(int(v['statistics'].get('commentCount', 0)) for v in videos)
            
            # 평균 통계
            avg_views = total_views / total_videos if total_videos > 0 else 0
            avg_likes = total_likes / total_videos if total_videos > 0 else 0
            avg_comments = total_comments / total_videos if total_videos > 0 else 0
            
            # 최고/최저 성과
            view_counts = [int(v['statistics'].get('viewCount', 0)) for v in videos]
            max_views = max(view_counts) if view_counts else 0
            min_views = min(view_counts) if view_counts else 0
            
            # 참여도 계산
            engagement_rates = []
            for video in videos:
                views = int(video['statistics'].get('viewCount', 0))
                likes = int(video['statistics'].get('likeCount', 0))
                comments = int(video['statistics'].get('commentCount', 0))
                
                if views > 0:
                    engagement_rate = ((likes + comments) / views) * 100
                    engagement_rates.append(engagement_rate)
            
            avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
            
            # 영상 유형별 통계
            shorts_count = 0
            long_count = 0
            
            for video in videos:
                try:
                    duration_str = video['contentDetails']['duration']
                    duration_seconds = self.client.parse_duration(duration_str)
                    
                    if duration_seconds <= 60:
                        shorts_count += 1
                    else:
                        long_count += 1
                except:
                    continue
            
            return {
                'total_videos': total_videos,
                'total_views': total_views,
                'total_likes': total_likes,
                'total_comments': total_comments,
                'avg_views': round(avg_views, 2),
                'avg_likes': round(avg_likes, 2),
                'avg_comments': round(avg_comments, 2),
                'max_views': max_views,
                'min_views': min_views,
                'avg_engagement_rate': round(avg_engagement, 4),
                'shorts_count': shorts_count,
                'long_videos_count': long_count,
                'shorts_ratio': round((shorts_count / total_videos * 100), 2) if total_videos > 0 else 0
            }
            
        except Exception as e:
            print(f"❌ 채널 통계 계산 오류: {e}")
            return {}
    
    def analyze_video_performance(self, videos):
        """
        영상 성과 분석
        
        Args:
            videos (list): 영상 목록
            
        Returns:
            dict: 성과 분석 결과
        """
        if not videos:
            return {}
        
        try:
            # 조회수 기준 성과 분석
            view_counts = [int(v['statistics'].get('viewCount', 0)) for v in videos]
            avg_views = sum(view_counts) / len(view_counts)
            
            # 성과별 영상 분류
            viral_videos = []  # 평균의 5배 이상
            hit_videos = []    # 평균의 3배 이상
            good_videos = []   # 평균의 1.5배 이상
            poor_videos = []   # 평균의 0.7배 미만
            
            for video in videos:
                views = int(video['statistics'].get('viewCount', 0))
                ratio = views / avg_views if avg_views > 0 else 0
                
                video_performance = {
                    'video': video,
                    'views': views,
                    'performance_ratio': ratio
                }
                
                if ratio >= 5.0:
                    viral_videos.append(video_performance)
                elif ratio >= 3.0:
                    hit_videos.append(video_performance)
                elif ratio >= 1.5:
                    good_videos.append(video_performance)
                elif ratio < 0.7:
                    poor_videos.append(video_performance)
            
            # 최고 성과 영상들
            top_videos = sorted(videos, key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)[:5]
            
            return {
                'avg_views': avg_views,
                'viral_count': len(viral_videos),
                'hit_count': len(hit_videos),
                'good_count': len(good_videos),
                'poor_count': len(poor_videos),
                'viral_videos': viral_videos[:3],  # 상위 3개만
                'hit_videos': hit_videos[:3],
                'top_videos': top_videos,
                'performance_distribution': {
                    'viral': round(len(viral_videos) / len(videos) * 100, 2),
                    'hit': round(len(hit_videos) / len(videos) * 100, 2),
                    'good': round(len(good_videos) / len(videos) * 100, 2),
                    'poor': round(len(poor_videos) / len(videos) * 100, 2)
                }
            }
            
        except Exception as e:
            print(f"❌ 성과 분석 오류: {e}")
            return {}
    
    def analyze_upload_trends(self, videos):
        """
        업로드 트렌드 분석
        
        Args:
            videos (list): 영상 목록
            
        Returns:
            dict: 트렌드 분석 결과
        """
        if not videos:
            return {}
        
        try:
            # 월별 업로드 패턴
            monthly_uploads = {}
            daily_uploads = {'Monday': 0, 'Tuesday': 0, 'Wednesday': 0, 'Thursday': 0, 
                           'Friday': 0, 'Saturday': 0, 'Sunday': 0}
            
            for video in videos:
                try:
                    published_at = video['snippet']['publishedAt']
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    
                    # 월별
                    month_key = dt.strftime('%Y-%m')
                    monthly_uploads[month_key] = monthly_uploads.get(month_key, 0) + 1
                    
                    # 요일별
                    day_name = dt.strftime('%A')
                    daily_uploads[day_name] += 1
                    
                except:
                    continue
            
            # 최근 활동 패턴
            recent_30days = [v for v in videos if self._is_recent_video(v, 30)]
            recent_7days = [v for v in videos if self._is_recent_video(v, 7)]
            
            # 업로드 주기 계산
            upload_frequency = self._calculate_upload_frequency(videos)
            
            return {
                'monthly_uploads': monthly_uploads,
                'daily_pattern': daily_uploads,
                'most_active_day': max(daily_uploads, key=daily_uploads.get),
                'recent_30days_count': len(recent_30days),
                'recent_7days_count': len(recent_7days),
                'upload_frequency_days': upload_frequency,
                'consistency_score': self._calculate_consistency_score(monthly_uploads)
            }
            
        except Exception as e:
            print(f"❌ 업로드 트렌드 분석 오류: {e}")
            return {}
    
    def analyze_content_patterns(self, videos):
        """
        컨텐츠 패턴 분석
        
        Args:
            videos (list): 영상 목록
            
        Returns:
            dict: 컨텐츠 분석 결과
        """
        if not videos:
            return {}
        
        try:
            # 제목 길이 분석
            title_lengths = [len(v['snippet']['title']) for v in videos]
            avg_title_length = sum(title_lengths) / len(title_lengths)
            
            # 영상 길이 분석
            durations = []
            for video in videos:
                try:
                    duration_str = video['contentDetails']['duration']
                    duration_seconds = self.client.parse_duration(duration_str)
                    durations.append(duration_seconds)
                except:
                    continue
            
            avg_duration = sum(durations) / len(durations) if durations else 0
            
            # 성과 좋은 영상들의 패턴
            top_performers = sorted(videos, key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)[:10]
            
            top_title_lengths = [len(v['snippet']['title']) for v in top_performers]
            avg_top_title_length = sum(top_title_lengths) / len(top_title_lengths) if top_title_lengths else 0
            
            # 카테고리 분석
            categories = {}
            for video in videos:
                category_id = video['snippet'].get('categoryId', 'Unknown')
                categories[category_id] = categories.get(category_id, 0) + 1
            
            most_used_category = max(categories, key=categories.get) if categories else 'Unknown'
            
            return {
                'avg_title_length': round(avg_title_length, 2),
                'avg_duration_seconds': round(avg_duration, 2),
                'avg_duration_formatted': self._format_duration(avg_duration),
                'top_performers_avg_title_length': round(avg_top_title_length, 2),
                'category_distribution': categories,
                'most_used_category': most_used_category,
                'title_length_range': {
                    'min': min(title_lengths) if title_lengths else 0,
                    'max': max(title_lengths) if title_lengths else 0
                },
                'duration_range': {
                    'min_seconds': min(durations) if durations else 0,
                    'max_seconds': max(durations) if durations else 0,
                    'min_formatted': self._format_duration(min(durations)) if durations else "00:00",
                    'max_formatted': self._format_duration(max(durations)) if durations else "00:00"
                }
            }
            
        except Exception as e:
            print(f"❌ 컨텐츠 패턴 분석 오류: {e}")
            return {}
    
    def extract_channel_id_from_url(self, url_or_id):
        """
        URL 또는 핸들에서 채널 ID 추출
        
        Args:
            url_or_id (str): 채널 URL, 핸들, 또는 ID
            
        Returns:
            tuple: (channel_id, channel_name)
        """
        try:
            url_or_id = url_or_id.strip()
            
            # 이미 채널 ID인 경우
            if url_or_id.startswith('UC') and len(url_or_id) == 24:
                return url_or_id, None
            
            # URL에서 추출
            patterns = [
                (r'youtube\.com/channel/([a-zA-Z0-9_-]+)', 'channel'),
                (r'youtube\.com/c/([^/?]+)', 'custom'),
                (r'youtube\.com/user/([^/?]+)', 'user'),
                (r'youtube\.com/@([^/?]+)', 'handle'),
                (r'youtube\.com/([a-zA-Z0-9가-힣_-]+)$', 'legacy')
            ]
            
            for pattern, url_type in patterns:
                match = re.search(pattern, url_or_id)
                if match:
                    identifier = match.group(1)
                    identifier = urllib.parse.unquote(identifier, encoding='utf-8')
                    
                    if identifier.startswith('UC') and len(identifier) == 24:
                        return identifier, None
                    
                    # API로 채널 ID 찾기
                    channel_id = self._resolve_channel_identifier(identifier, url_type)
                    if channel_id:
                        return channel_id, identifier
            
            # 직접 검색
            channel_id = self._search_channel_by_name(url_or_id)
            if channel_id:
                return channel_id, url_or_id
            
            return None, None
            
        except Exception as e:
            print(f"채널 ID 추출 오류: {e}")
            return None, None
    
    def _resolve_channel_identifier(self, identifier, url_type):
        """채널 식별자를 채널 ID로 변환"""
        try:
            channels = self.client.search_channels(identifier, max_results=10)
            
            for channel in channels:
                channel_title = channel['snippet']['title']
                custom_url = channel['snippet'].get('customUrl', '')
                
                # 정확한 매치 확인
                if (custom_url.lower() == f"@{identifier.lower()}" or
                    custom_url.lower() == identifier.lower() or
                    channel_title.lower() == identifier.lower()):
                    return channel['snippet']['channelId']
            
            # 첫 번째 결과 반환
            if channels:
                return channels[0]['snippet']['channelId']
            
            return None
            
        except Exception as e:
            print(f"채널 식별자 해결 오류: {e}")
            return None
    
    def _search_channel_by_name(self, channel_name):
        """채널명으로 검색"""
        try:
            channels = self.client.search_channels(channel_name, max_results=5)
            
            for channel in channels:
                found_title = channel['snippet']['title']
                if self._is_channel_name_match(channel_name, found_title):
                    return channel['snippet']['channelId']
            
            # 첫 번째 결과 반환
            if channels:
                return channels[0]['snippet']['channelId']
            
            return None
            
        except Exception as e:
            print(f"채널명 검색 오류: {e}")
            return None
    
    def _is_channel_name_match(self, input_name, found_name):
        """채널명 매치 확인"""
        input_normalized = input_name.lower().strip().replace(' ', '')
        found_normalized = found_name.lower().strip().replace(' ', '')
        
        return (input_normalized == found_normalized or
                input_normalized in found_normalized or
                found_normalized in input_normalized)
    
    def _is_recent_video(self, video, days):
        """최근 영상인지 확인"""
        try:
            published_at = video['snippet']['publishedAt']
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            cutoff_date = datetime.now(dt.tzinfo) - timedelta(days=days)
            return dt >= cutoff_date
        except:
            return False
    
    def _calculate_upload_frequency(self, videos):
        """업로드 주기 계산 (일 단위)"""
        if len(videos) < 2:
            return 0
        
        try:
            dates = []
            for video in videos:
                published_at = video['snippet']['publishedAt']
                dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                dates.append(dt)
            
            dates.sort()
            
            # 연속된 업로드 간의 간격 계산
            intervals = []
            for i in range(1, len(dates)):
                interval = (dates[i] - dates[i-1]).days
                intervals.append(interval)
            
            return sum(intervals) / len(intervals) if intervals else 0
            
        except:
            return 0
    
    def _calculate_consistency_score(self, monthly_uploads):
        """업로드 일관성 점수 계산"""
        if not monthly_uploads:
            return 0
        
        try:
            upload_counts = list(monthly_uploads.values())
            if len(upload_counts) < 2:
                return 100
            
            # 표준편차 기반 일관성 점수
            mean_uploads = sum(upload_counts) / len(upload_counts)
            variance = sum((x - mean_uploads) ** 2 for x in upload_counts) / len(upload_counts)
            std_dev = variance ** 0.5
            
            # 변동계수의 역수로 일관성 점수 계산
            cv = std_dev / mean_uploads if mean_uploads > 0 else float('inf')
            consistency_score = max(0, 100 - (cv * 50))
            
            return round(consistency_score, 2)
            
        except:
            return 0
    
    def _format_duration(self, seconds):
        """초를 시:분:초 형식으로 변환"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"