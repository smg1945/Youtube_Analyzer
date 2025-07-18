"""
YouTube 영상 검색 전용 모듈
검색, 필터링, 정렬 기능 담당
"""

import time
import re
from datetime import datetime, timedelta
from googleapiclient.errors import HttpError
import config

class VideoSearcher:
    """YouTube 영상 검색 클래스"""
    
    def __init__(self, youtube_client):
        """
        영상 검색기 초기화
        
        Args:
            youtube_client: YouTubeClient 인스턴스
        """
        self.client = youtube_client
        
    def search_by_keyword(self, keyword, region_code="KR", max_results=200, 
                         period_days=30, order="relevance"):
        """
        키워드로 영상 검색
        
        Args:
            keyword (str): 검색 키워드
            region_code (str): 지역 코드
            max_results (int): 최대 결과 수
            period_days (int): 검색 기간 (일)
            order (str): 정렬 기준 ("relevance", "date", "viewCount")
            
        Returns:
            list: 검색된 영상 목록
        """
        print(f"\n🔍 키워드 검색 시작: '{keyword}'")
        print(f"   지역: {region_code}, 정렬: {order}, 기간: {period_days}일")
        
        try:
            # 1. API 연결 테스트
            if not self.client.test_connection():
                return []
            
            # 2. 검색 파라미터 검증
            validation_errors = self._validate_search_parameters(keyword, region_code, period_days)
            if validation_errors:
                print(f"❌ 검색 파라미터 오류: {', '.join(validation_errors)}")
                return []
            
            # 3. 검색 기간 설정
            published_after = (datetime.now() - timedelta(days=period_days)).isoformat() + 'Z'
            
            # 4. 영상 검색 실행
            video_ids = self._execute_search(keyword, region_code, published_after, order, max_results)
            
            if not video_ids:
                print(f"❌ '{keyword}' 키워드로 영상을 찾을 수 없습니다.")
                self._print_search_suggestions(keyword, period_days)
                return []
            
            # 5. 영상 상세 정보 가져오기
            print("📊 영상 상세 정보 수집 중...")
            videos = self.client.get_video_details(video_ids)
            
            if not videos:
                print("❌ 영상 상세 정보를 가져올 수 없습니다.")
                return []
            
            print(f"✅ 검색 완료: {len(videos)}개 영상")
            return videos
            
        except Exception as e:
            print(f"❌ 검색 오류: {e}")
            return []
    
    def _execute_search(self, keyword, region_code, published_after, order, max_results):
        """실제 검색 실행"""
        try:
            video_ids = []
            page_token = None
            batch_size = 50  # API 제한
            
            while len(video_ids) < max_results:
                request = self.client.youtube.search().list(
                    part='id',
                    q=keyword,
                    type='video',
                    regionCode=region_code,
                    publishedAfter=published_after,
                    order=order,
                    maxResults=min(batch_size, max_results - len(video_ids)),
                    pageToken=page_token
                )
                
                response = request.execute()
                
                # 영상 ID 추출
                batch_ids = [item['id']['videoId'] for item in response.get('items', [])]
                video_ids.extend(batch_ids)
                
                # 다음 페이지 토큰
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                
                # API 할당량 업데이트
                self.client.quota_used += 100
                
                print(f"   검색 진행: {len(video_ids)}/{max_results}")
            
            return video_ids[:max_results]
            
        except HttpError as e:
            if e.resp.status == 403:
                print("❌ API 할당량 초과 또는 권한 오류")
            else:
                print(f"❌ API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 검색 실행 오류: {e}")
            return []
    
    def filter_by_video_type(self, videos, video_type):
        """
        영상 유형별 필터링
        
        Args:
            videos (list): 영상 목록
            video_type (str): "all", "shorts", "long"
            
        Returns:
            list: 필터링된 영상 목록
        """
        if video_type == "all":
            return videos
        
        print(f"🔧 영상 유형 필터링: {video_type}")
        
        filtered_videos = []
        shorts_count = 0
        long_count = 0
        invalid_count = 0
        
        for video in videos:
            try:
                # contentDetails에서 duration 확인
                duration = video.get('contentDetails', {}).get('duration', '')
                
                if not duration:
                    invalid_count += 1
                    continue
                
                # 길이를 초 단위로 변환
                duration_seconds = self._parse_duration_to_seconds(duration)
                
                # 유형 분류 (60초 기준)
                is_shorts = duration_seconds <= config.SHORT_VIDEO_MAX_DURATION
                
                if is_shorts:
                    shorts_count += 1
                    if video_type == "shorts":
                        filtered_videos.append(video)
                else:
                    long_count += 1
                    if video_type == "long":
                        filtered_videos.append(video)
                        
            except Exception as e:
                print(f"영상 유형 분류 오류: {e}")
                invalid_count += 1
                continue
        
        print(f"   쇼츠: {shorts_count}개, 롱폼: {long_count}개, 오류: {invalid_count}개")
        print(f"   선택된 유형: {len(filtered_videos)}개")
        
        return filtered_videos
    
    def filter_by_metrics(self, videos, min_view_count=None, max_subscriber_count=None):
        """
        지표별 필터링 (조회수, 구독자 수)
        
        Args:
            videos (list): 영상 목록
            min_view_count (int): 최소 조회수
            max_subscriber_count (int): 최대 구독자 수
            
        Returns:
            list: 필터링된 영상 목록
        """
        if not min_view_count and not max_subscriber_count:
            return videos
        
        print("🔧 지표 필터링 적용 중...")
        
        filtered_videos = []
        channel_cache = {}
        skipped_view_count = 0
        skipped_subscriber_count = 0
        
        for i, video in enumerate(videos, 1):
            print(f"   필터링 진행: {i}/{len(videos)}", end='\r')
            
            try:
                # 조회수 필터 체크
                if min_view_count:
                    video_views = int(video['statistics'].get('viewCount', 0))
                    if video_views < min_view_count:
                        skipped_view_count += 1
                        continue
                
                # 구독자 수 필터 체크
                if max_subscriber_count:
                    channel_id = video['snippet']['channelId']
                    
                    # 캐시에서 구독자 수 확인
                    if channel_id not in channel_cache:
                        channel_info = self.client.get_channel_info(channel_id)
                        if channel_info:
                            subscriber_count = int(channel_info['statistics'].get('subscriberCount', 0))
                            channel_cache[channel_id] = subscriber_count
                        else:
                            channel_cache[channel_id] = 0
                    
                    channel_subscribers = channel_cache[channel_id]
                    if channel_subscribers > max_subscriber_count:
                        skipped_subscriber_count += 1
                        continue
                
                # 모든 필터 통과
                filtered_videos.append(video)
                
            except Exception as e:
                print(f"\n❌ 영상 처리 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                continue
        
        print(f"\n✅ 지표 필터링 완료:")
        print(f"   조회수 필터로 제외: {skipped_view_count}개")
        print(f"   구독자 수 필터로 제외: {skipped_subscriber_count}개")
        print(f"   최종 결과: {len(filtered_videos)}개")
        
        return filtered_videos
    
    def sort_videos(self, videos, sort_by="relevance"):
        """
        영상 정렬
        
        Args:
            videos (list): 영상 목록
            sort_by (str): 정렬 기준 ("relevance", "date", "viewCount")
            
        Returns:
            list: 정렬된 영상 목록
        """
        if sort_by == "viewCount":
            videos.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
        elif sort_by == "date":
            videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
        # relevance는 API가 이미 정렬한 상태
        
        return videos
    
    def search_with_filters(self, keyword, filters):
        """
        필터를 적용한 통합 검색
        
        Args:
            keyword (str): 검색 키워드
            filters (dict): 필터 설정
            
        Returns:
            list: 필터링된 영상 목록
        """
        # 1. 기본 검색
        videos = self.search_by_keyword(
            keyword=keyword,
            region_code=filters.get('region_code', 'KR'),
            max_results=filters.get('max_results', 200),
            period_days=filters.get('period_days', 30),
            order=filters.get('order', 'relevance')
        )
        
        if not videos:
            return []
        
        # 2. 영상 유형 필터링
        video_type = filters.get('video_type', 'all')
        if video_type != 'all':
            videos = self.filter_by_video_type(videos, video_type)
            if not videos:
                print(f"❌ {video_type} 유형의 영상이 없습니다.")
                return []
        
        # 3. 지표 필터링
        videos = self.filter_by_metrics(
            videos,
            min_view_count=filters.get('min_view_count'),
            max_subscriber_count=filters.get('max_subscriber_count')
        )
        
        if not videos:
            print("❌ 필터링 후 남은 영상이 없습니다.")
            self._print_filter_suggestions(filters)
            return []
        
        # 4. 최종 정렬
        videos = self.sort_videos(videos, filters.get('order', 'relevance'))
        
        return videos[:filters.get('max_results', 200)]
    
    def parse_duration(self, duration):
        """YouTube 영상 길이 파싱 (PT1H2M3S -> 1:02:03)"""
        if not duration:
            return "00:00"
        
        try:
            # PT1H2M3S 형태의 duration 파싱
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration)
            
            if not match:
                return "00:00"
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
                
        except Exception as e:
            print(f"영상 길이 파싱 오류: {e}")
            return "00:00"
    
    def _parse_duration_to_seconds(self, duration):
        """YouTube duration을 초 단위로 변환"""
        if not duration:
            return 0
        
        try:
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration)
            
            if not match:
                return 0
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception as e:
            print(f"Duration 파싱 오류: {e}")
            return 0
    
    def _validate_search_parameters(self, keyword, region_code, period_days):
        """검색 파라미터 유효성 검사"""
        errors = []
        
        if not keyword or len(keyword.strip()) == 0:
            errors.append("키워드가 비어있습니다")
        
        if len(keyword) > 100:
            errors.append("키워드가 너무 깁니다 (100자 이하)")
        
        if region_code not in ['KR', 'US']:
            errors.append(f"지원하지 않는 지역 코드: {region_code}")
        
        if period_days < 1 or period_days > 365:
            errors.append("검색 기간이 유효하지 않습니다 (1-365일)")
        
        return errors
    
    def _print_search_suggestions(self, keyword, period_days):
        """검색 제안사항 출력"""
        print("💡 해결 방법:")
        print("   1. 다른 키워드를 시도해보세요:")
        if "건강" in keyword:
            print("      - '다이어트', '운동', '홈트', '건강식'")
        elif "음식" in keyword or "요리" in keyword:
            print("      - '레시피', '맛집', '쿠킹', '베이킹'")
        else:
            print("      - 더 일반적인 키워드 사용")
        print(f"   2. 검색 기간을 늘려보세요: {period_days}일 → 30일 또는 90일")
        print("   3. 지역을 변경해보세요: 한국 ↔ 글로벌")
    
    def _print_filter_suggestions(self, filters):
        """필터 제안사항 출력"""
        print("💡 해결 방법:")
        if filters.get('min_view_count'):
            min_views = filters['min_view_count']
            print(f"   1. 최소 조회수 낮추기: {min_views:,} → {min_views//10:,}")
        if filters.get('max_subscriber_count'):
            max_subs = filters['max_subscriber_count']
            print(f"   2. 최대 구독자 늘리기: {max_subs:,} → {max_subs*5:,}")
        period_days = filters.get('period_days', 30)
        print(f"   3. 검색 기간 늘리기: {period_days}일 → {period_days*2}일")
        print("   4. 모든 필터 해제 후 테스트")


class TrendingVideoSearcher(VideoSearcher):
    """트렌딩 영상 검색 클래스"""
    
    def get_trending_videos(self, region_code="KR", category_id=None, max_results=200):
        """
        실시간 트렌딩 영상 목록 가져오기
        
        Args:
            region_code (str): 지역 코드
            category_id (str): 카테고리 ID
            max_results (int): 최대 결과 수
            
        Returns:
            list: 트렌딩 영상 목록
        """
        try:
            if not self.client.can_use_quota(1):
                raise Exception("API 할당량이 부족합니다.")
            
            request = self.client.youtube.videos().list(
                part='id,snippet,statistics,contentDetails',
                chart='mostPopular',
                regionCode=region_code,
                maxResults=min(max_results, 50),
                videoCategoryId=category_id
            )
            
            response = request.execute()
            videos = response.get('items', [])
            
            # 영상 길이 파싱 추가
            for video in videos:
                duration = video.get('contentDetails', {}).get('duration', '')
                video['parsed_duration'] = self.parse_duration(duration)
            
            self.client.quota_used += 1
            
            print(f"✅ 트렌딩 영상 {len(videos)}개 수집 완료")
            return videos
            
        except Exception as e:
            print(f"❌ 트렌딩 영상 수집 오류: {e}")
            return []
    
    def get_category_trending_videos(self, region_code="KR", max_results=200):
        """
        카테고리별 트렌딩 영상 수집
        
        Args:
            region_code (str): 지역 코드
            max_results (int): 최대 결과 수
            
        Returns:
            list: 카테고리별 트렌딩 영상 목록
        """
        all_videos = []
        categories = ['10', '17', '19', '20', '22', '23', '24', '25', '26']  # 주요 카테고리
        
        videos_per_category = max_results // len(categories)
        
        for category in categories:
            try:
                videos = self.get_trending_videos(
                    region_code=region_code,
                    category_id=category,
                    max_results=videos_per_category
                )
                all_videos.extend(videos)
                
                if len(all_videos) >= max_results:
                    break
                    
            except Exception as e:
                print(f"카테고리 {category} 영상 수집 오류: {e}")
                continue
        
        return all_videos[:max_results]


# YouTubeClient 클래스에 추가할 메서드
class YouTubeClientExtension:
    """YouTube 클라이언트 확장 메서드들"""
    
    def get_video_details(self, video_ids):
        """영상 상세 정보 가져오기 - 길이 정보 포함"""
        if not video_ids:
            return []
        
        try:
            all_videos = []
            batch_size = 50  # YouTube API 제한
            
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                request = self.youtube.videos().list(
                    part='id,snippet,statistics,contentDetails',  # contentDetails 추가
                    id=','.join(batch_ids)
                )
                response = request.execute()
                
                # 영상 정보 처리
                for video in response.get('items', []):
                    # 영상 길이 파싱
                    duration = video.get('contentDetails', {}).get('duration', '')
                    video['parsed_duration'] = self.parse_duration(duration)
                    
                    all_videos.append(video)
                
                self.quota_used += 1
                
            return all_videos
            
        except Exception as e:
            print(f"영상 상세 정보 가져오기 오류: {e}")
            return []
    
    def parse_duration(self, duration):
        """YouTube 영상 길이 파싱"""
        searcher = VideoSearcher(self)
        return searcher.parse_duration(duration)