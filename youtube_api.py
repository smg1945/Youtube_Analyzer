"""
YouTube Data API 관련 함수들
"""

import os
import re
import requests
import time
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from PIL import Image
from io import BytesIO
import config

class YouTubeAPIClient:
    def __init__(self, api_key=None):
        """YouTube API 클라이언트 초기화"""
        self.api_key = api_key or config.DEVELOPER_KEY
        self.youtube = build(
            config.YOUTUBE_API_SERVICE_NAME,
            config.YOUTUBE_API_VERSION,
            developerKey=self.api_key
        )
        self.quota_used = 0
        self.quota_limit = config.API_QUOTA_LIMIT
        
    def check_quota_remaining(self):
        """남은 할당량 확인"""
        remaining = self.quota_limit - self.quota_used
        return max(0, remaining)
    
    def can_use_quota(self, required_units):
        """필요한 할당량을 사용할 수 있는지 확인"""
        return self.quota_used + required_units <= self.quota_limit
    
    def get_quota_status(self):
        """할당량 상태 정보 반환"""
        used_percentage = (self.quota_used / self.quota_limit) * 100
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.check_quota_remaining(),
            'percentage': used_percentage,
            'status': 'high' if used_percentage > 80 else 'medium' if used_percentage > 50 else 'low'
        }

    def get_trending_videos(self, region_code="KR", category_id=None, max_results=200):
        """
        실시간 트렌딩 영상 목록 가져오기 (더 많은 영상을 수집해서 outlier 분석)
        
        Args:
            region_code (str): 지역 코드 (KR, US 등)
            category_id (str): 카테고리 ID (None이면 전체)
            max_results (int): 최대 결과 수
            
        Returns:
            list: 트렌딩 영상 목록
        """
        try:
            # API 할당량 확인
            if not self.can_use_quota(1):
                raise Exception("API 할당량이 부족합니다. 내일 다시 시도해주세요.")
            
            request_params = {
                'part': 'snippet,statistics,contentDetails',
                'chart': 'mostPopular',
                'regionCode': region_code,
                'maxResults': max_results
            }
            
            if category_id and category_id != "all":
                request_params['videoCategoryId'] = category_id
            
            request = self.youtube.videos().list(**request_params)
            response = request.execute()
            
            self.quota_used += 1  # API 할당량 추적
            
            return response.get('items', [])
            
        except HttpError as e:
            if "quotaExceeded" in str(e):
                raise Exception("YouTube API 일일 할당량을 초과했습니다. 내일 다시 시도해주세요.")
            else:
                print(f"YouTube API 오류: {e}")
                return []

    def get_trending_shorts(self, region_code="KR", max_results=200):
        """
        트렌딩 쇼츠 영상 가져오기 (검색 기반)
        
        Args:
            region_code (str): 지역 코드
            max_results (int): 최대 결과 수
            
        Returns:
            list: 쇼츠 영상 목록
        """
        try:
            from datetime import datetime, timedelta
            
            # 최근 7일간의 영상 중에서 검색
            published_after = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
            
            all_shorts = []
            
            # 방법 1: 쇼츠 관련 키워드로 검색
            search_queries = ['#Shorts', 'Shorts', '쇼츠'] if region_code == 'KR' else ['#Shorts', 'Shorts']
            
            for query in search_queries:
                try:
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=query,
                        type='video',
                        order='viewCount',
                        publishedAfter=published_after,
                        regionCode=region_code,
                        maxResults=30,
                        relevanceLanguage='ko' if region_code == 'KR' else 'en'
                    )
                    search_response = search_request.execute()
                    
                    self.quota_used += 100  # search API 사용량
                    
                    # 영상 ID 추출
                    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                    
                    if video_ids:
                        # 영상 상세 정보 가져오기
                        videos_details = self.get_video_details(video_ids)
                        
                        # 실제로 쇼츠인지 확인 (60초 이하)
                        for video in videos_details:
                            duration = self.parse_duration(video['contentDetails']['duration'])
                            if duration <= 60:  # 60초 이하만 쇼츠로 인정
                                all_shorts.append(video)
                    
                except Exception as e:
                    print(f"쇼츠 검색 오류 (쿼리: {query}): {e}")
                    continue
            
            # 방법 2: 일반 검색에서 짧은 영상들 찾기
            try:
                # 인기 있는 카테고리에서 최근 영상 검색
                popular_categories = ['10', '20', '22', '23', '24']  # 음악, 게임, 블로그, 코미디, 엔터테인먼트
                
                for category in popular_categories:
                    search_request = self.youtube.search().list(
                        part='snippet',
                        type='video',
                        order='viewCount',
                        publishedAfter=published_after,
                        regionCode=region_code,
                        maxResults=20,
                        relevanceLanguage='ko' if region_code == 'KR' else 'en'
                    )
                    search_response = search_request.execute()
                    
                    self.quota_used += 100
                    
                    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                    
                    if video_ids:
                        videos_details = self.get_video_details(video_ids)
                        
                        for video in videos_details:
                            duration = self.parse_duration(video['contentDetails']['duration'])
                            if duration <= 60:
                                all_shorts.append(video)
                                
            except Exception as e:
                print(f"카테고리별 쇼츠 검색 오류: {e}")
            
            # 중복 제거 (video ID 기준)
            seen_ids = set()
            unique_shorts = []
            for video in all_shorts:
                if video['id'] not in seen_ids:
                    seen_ids.add(video['id'])
                    unique_shorts.append(video)
            
            # 조회수 기준으로 정렬
            unique_shorts.sort(key=lambda x: int(x.get('statistics', {}).get('viewCount', 0)), reverse=True)
            
            print(f"🎬 총 {len(unique_shorts)}개의 쇼츠를 발견했습니다.")
            
            return unique_shorts[:max_results]
            
        except Exception as e:
            print(f"쇼츠 검색 전체 오류: {e}")
            return []

    def search_videos_by_keyword(self, keyword, region_code="KR", max_results=200, 
                                max_subscriber_count=None, min_view_count=None, period_days=30):
        """
        키워드로 영상 검색 (구독자 수, 조회수 필터 포함)
        
        Args:
            keyword (str): 검색 키워드
            region_code (str): 지역 코드
            max_results (int): 최대 결과 수
            max_subscriber_count (int): 최대 구독자 수 (None이면 제한 없음)
            min_view_count (int): 최소 조회수 (None이면 제한 없음)
            period_days (int): 검색 기간 (일)
            
        Returns:
            list: 검색된 영상 목록
        """
        try:
            from datetime import datetime, timedelta
            
            # 검색 기간 설정
            published_after = (datetime.now() - timedelta(days=period_days)).isoformat() + 'Z'
            
            print(f"🔍 '{keyword}' 키워드로 최근 {period_days}일 영상 검색 중...")
            
            # 키워드로 영상 검색
            search_request = self.youtube.search().list(
                part='snippet',
                q=keyword,
                type='video',
                order='date',  # 최신순 정렬
                publishedAfter=published_after,
                regionCode=region_code,
                maxResults=max_results,
                relevanceLanguage='ko' if region_code == 'KR' else 'en'
            )
            search_response = search_request.execute()
            
            self.quota_used += 100  # search API 사용량
            
            # 영상 ID 추출
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                return []
            
            # 영상 상세 정보 가져오기
            videos_details = self.get_video_details(video_ids)
            
            print(f"📊 {len(videos_details)}개 영상 발견, 필터링 적용 중...")
            
            # 채널별 구독자 수 캐시
            channel_subscriber_cache = {}
            filtered_videos = []
            
            for video in videos_details:
                try:
                    channel_id = video['snippet']['channelId']
                    video_views = int(video['statistics'].get('viewCount', 0))
                    
                    # 조회수 필터 체크
                    if min_view_count and video_views < min_view_count:
                        continue
                    
                    # 구독자 수 필터 체크 (필요한 경우만)
                    if max_subscriber_count:
                        if channel_id not in channel_subscriber_cache:
                            channel_info = self.get_channel_info(channel_id)
                            if channel_info:
                                subscriber_count = int(channel_info['statistics'].get('subscriberCount', 0))
                                channel_subscriber_cache[channel_id] = subscriber_count
                            else:
                                channel_subscriber_cache[channel_id] = 0
                        
                        channel_subscribers = channel_subscriber_cache[channel_id]
                        if channel_subscribers > max_subscriber_count:
                            continue
                    
                    # 필터 통과한 영상 추가
                    filtered_videos.append(video)
                    
                except Exception as e:
                    print(f"영상 필터링 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                    continue
            
            # 최신순으로 정렬 (한 번 더 확실하게)
            filtered_videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
            
            print(f"✅ 필터링 완료: {len(filtered_videos)}개 영상")
            
            return filtered_videos
            
        except Exception as e:
            print(f"키워드 검색 오류: {e}")
            return []

    def get_video_details(self, video_ids):
        """
        영상 상세 정보 가져오기
        
        Args:
            video_ids (list): 영상 ID 목록
            
        Returns:
            list: 영상 상세 정보 목록
        """
        try:
            # API는 한 번에 최대 50개 영상 정보를 가져올 수 있음
            video_details = []
            
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                
                request = self.youtube.videos().list(
                    part='snippet,statistics,contentDetails,status',
                    id=','.join(batch_ids)
                )
                response = request.execute()
                video_details.extend(response.get('items', []))
                
                self.quota_used += 1
                time.sleep(0.1)  # API 요청 제한 고려
            
            return video_details
            
        except HttpError as e:
            print(f"영상 상세 정보 가져오기 오류: {e}")
            return []

    def get_video_comments(self, video_id, max_results=50):
        """
        영상 댓글 가져오기
        
        Args:
            video_id (str): 영상 ID
            max_results (int): 최대 댓글 수
            
        Returns:
            list: 댓글 목록
        """
        try:
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                order='relevance'  # 관련성 순으로 정렬
            )
            response = request.execute()
            
            self.quota_used += 1
            
            comments = []
            for item in response.get('items', []):
                comment = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'text': comment['textDisplay'],
                    'author': comment['authorDisplayName'],
                    'likes': comment['likeCount'],
                    'published_at': comment['publishedAt']
                })
            
            return comments
            
        except HttpError as e:
            print(f"댓글 가져오기 오류 (영상 ID: {video_id}): {e}")
            return []

    def download_thumbnail(self, thumbnail_url, video_id, video_title="", rank=0, quality="high"):
        """썸네일 이미지 다운로드"""
        if not thumbnail_url:
            return None
            
        try:
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code == 200:
                os.makedirs('thumbnails', exist_ok=True)
                
                safe_title = re.sub(r'[^\w\s-]', '', video_title.replace(' ', '_'))[:30]
                if rank > 0:
                    filename = f"{rank:03d}_{safe_title}_{video_id}.jpg"
                else:
                    filename = f"{safe_title}_{video_id}.jpg"
                
                image_path = f'thumbnails/{filename}'
                
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                print(f"✅ 썸네일 다운로드 완료: {filename}")
                return image_path
            else:
                print(f"❌ 썸네일 다운로드 실패 (HTTP {response.status_code}): {thumbnail_url}")
                return None
        except Exception as e:
            print(f"❌ 썸네일 다운로드 오류: {e}")
            return None

    def download_multiple_thumbnails(self, videos_info):
        """
        여러 영상의 썸네일을 일괄 다운로드
        
        Args:
            videos_info (list): [{'video_id': str, 'title': str, 'thumbnail_url': str, 'rank': int}]
            
        Returns:
            dict: 다운로드 결과
        """
        try:
            print(f"🖼️ {len(videos_info)}개 영상의 썸네일 다운로드를 시작합니다...")
            
            downloaded_files = []
            failed_count = 0
            
            for i, video_info in enumerate(videos_info, 1):
                print(f"   진행률: {i}/{len(videos_info)} - {video_info.get('title', '')[:30]}...", end="\r")
                
                result = self.download_thumbnail(
                    video_info['thumbnail_url'],
                    video_info['video_id'],
                    video_info.get('title', ''),
                    video_info.get('rank', 0)
                )
                
                if result:
                    downloaded_files.append(result)
                else:
                    failed_count += 1
            
            print(f"\n✅ 썸네일 다운로드 완료!")
            print(f"   성공: {len(downloaded_files)}개")
            print(f"   실패: {failed_count}개")
            
            # ZIP 파일 생성
            if downloaded_files:
                zip_filename = self.create_thumbnails_zip(downloaded_files)
                return {
                    'success': True,
                    'downloaded_files': downloaded_files,
                    'failed_count': failed_count,
                    'zip_file': zip_filename
                }
            else:
                return {
                    'success': False,
                    'error': '다운로드된 썸네일이 없습니다'
                }
                
        except Exception as e:
            print(f"❌ 썸네일 일괄 다운로드 오류: {e}")
            return {'success': False, 'error': str(e)}

    def create_thumbnails_zip(self, thumbnail_files):
        """썸네일 파일들을 ZIP으로 압축"""
        try:
            from datetime import datetime
            import zipfile
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = f"selected_thumbnails_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in thumbnail_files:
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        zipf.write(file_path, filename)
            
            print(f"📦 썸네일 ZIP 파일 생성: {zip_filename}")
            return zip_filename
            
        except Exception as e:
            print(f"❌ 썸네일 ZIP 생성 오류: {e}")
            return None

    def get_channel_videos(self, channel_id, max_results=50, order='date'):
        """
        채널의 영상 목록 가져오기
        
        Args:
            channel_id (str): 채널 ID
            max_results (int): 최대 결과 수
            order (str): 정렬 방식 ('date', 'viewCount', 'relevance')
            
        Returns:
            list: 채널 영상 목록
        """
        try:
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response['items']:
                return []
            
            # 업로드 플레이리스트 ID
            uploads_playlist_id = channel_response['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            
            self.quota_used += 1
            
            # 플레이리스트에서 영상 목록 가져오기
            videos = []
            next_page_token = None
            
            while len(videos) < max_results:
                playlist_request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(videos)),
                    pageToken=next_page_token
                )
                playlist_response = playlist_request.execute()
                
                self.quota_used += 1
                
                for item in playlist_response['items']:
                    video_info = {
                        'id': item['snippet']['resourceId']['videoId'],
                        'title': item['snippet']['title'],
                        'description': item['snippet']['description'][:200] + '...' if len(item['snippet']['description']) > 200 else item['snippet']['description'],
                        'published_at': item['snippet']['publishedAt'],
                        'thumbnail_url': item['snippet']['thumbnails'].get('medium', {}).get('url', '')
                    }
                    videos.append(video_info)
                
                next_page_token = playlist_response.get('nextPageToken')
                if not next_page_token:
                    break
            
            # 영상 상세 정보 가져오기 (조회수, 좋아요 등)
            if videos:
                video_ids = [video['id'] for video in videos]
                detailed_videos = self.get_video_details(video_ids)
                
                # 상세 정보와 기본 정보 합치기
                detailed_video_dict = {video['id']: video for video in detailed_videos}
                
                for video in videos:
                    if video['id'] in detailed_video_dict:
                        detailed_info = detailed_video_dict[video['id']]
                        video.update({
                            'view_count': int(detailed_info['statistics'].get('viewCount', 0)),
                            'like_count': int(detailed_info['statistics'].get('likeCount', 0)),
                            'comment_count': int(detailed_info['statistics'].get('commentCount', 0)),
                            'duration': detailed_info['contentDetails']['duration']
                        })
            
            # 정렬
            if order == 'viewCount':
                videos.sort(key=lambda x: x.get('view_count', 0), reverse=True)
            elif order == 'date':
                videos.sort(key=lambda x: x['published_at'], reverse=True)
            
            return videos[:max_results]
            
        except Exception as e:
            print(f"채널 영상 목록 가져오기 오류: {e}")
            return []
            
            response = requests.get(thumbnail_url, timeout=10)
            if response.status_code == 200:
                # 썸네일 폴더 생성
                os.makedirs('thumbnails', exist_ok=True)
                
                # 파일명 생성 (순위_제목_영상ID.jpg)
                # 제목에서 파일명에 사용할 수 없는 문자 제거
                safe_title = re.sub(r'[^\w\s-]', '', video_title.replace(' ', '_'))[:30]
                if rank > 0:
                    filename = f"{rank:03d}_{safe_title}_{video_id}.jpg"
                else:
                    filename = f"{safe_title}_{video_id}.jpg"
                
                image_path = f'thumbnails/{filename}'
                
                # 이미지 저장
                with open(image_path, 'wb') as f:
                    f.write(response.content)
                
                return image_path
            else:
                print(f"썸네일 다운로드 실패 (HTTP {response.status_code}): {thumbnail_url}")
                return None
                
        except Exception as e:
            print(f"썸네일 다운로드 오류: {e}")
            return None

    def get_best_thumbnail_url(self, thumbnails):
        """
        최고 품질의 썸네일 URL 반환
        
        Args:
            thumbnails (dict): YouTube API의 thumbnails 딕셔너리
            
        Returns:
            str: 최고 품질 썸네일 URL
        """
        # 품질 우선순위: maxres > high > medium > default
        quality_priority = ['maxres', 'high', 'medium', 'default']
        
        for quality in quality_priority:
            if quality in thumbnails:
                return thumbnails[quality]['url']
        
        return None

    def parse_duration(self, duration_str):
        """
        YouTube API의 duration 문자열을 초 단위로 변환
        
        Args:
            duration_str (str): PT15M33S 형태의 duration 문자열
            
        Returns:
            int: 초 단위 duration
        """
        import re
        
        # PT15M33S 형태에서 시간, 분, 초 추출
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds

    def filter_videos_by_type(self, videos, video_type="all"):
        """
        영상 유형별 필터링 (전체/롱폼/쇼츠)
        
        Args:
            videos (list): 영상 목록
            video_type (str): "all", "long", "shorts"
            
        Returns:
            list: 필터링된 영상 목록
        """
        if video_type == "all":
            return videos
        
        filtered_videos = []
        
        for video in videos:
            duration = self.parse_duration(video['contentDetails']['duration'])
            
            if video_type == "shorts" and duration <= config.SHORT_VIDEO_MAX_DURATION:
                filtered_videos.append(video)
            elif video_type == "long" and duration > config.LONG_VIDEO_MIN_DURATION:
                filtered_videos.append(video)
        
        return filtered_videos

    def get_channel_info(self, channel_id):
        """
        채널 정보 가져오기
        
        Args:
            channel_id (str): 채널 ID
            
        Returns:
            dict: 채널 정보
        """
        try:
            request = self.youtube.channels().list(
                part='snippet,statistics',
                id=channel_id
            )
            response = request.execute()
            
            self.quota_used += 1
            
            if response['items']:
                return response['items'][0]
            else:
                return None
                
        except HttpError as e:
            print(f"채널 정보 가져오기 오류: {e}")
            return None

    def get_channel_recent_videos_stats(self, channel_id, max_results=10):
        """
        채널의 최근 영상들 통계 가져오기 (outlier score 계산용)
        
        Args:
            channel_id (str): 채널 ID
            max_results (int): 분석할 최근 영상 수
            
        Returns:
            dict: 평균 조회수, 좋아요, 댓글 수 등
        """
        try:
            # 채널의 최근 영상 검색
            search_request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                order='date',
                maxResults=max_results
            )
            search_response = search_request.execute()
            
            self.quota_used += 100  # search API 사용량
            
            # 영상 ID 추출
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                return None
            
            # 영상 상세 정보 가져오기
            videos_stats = self.get_video_details(video_ids)
            
            # 통계 계산
            view_counts = []
            like_counts = []
            comment_counts = []
            
            for video in videos_stats:
                stats = video.get('statistics', {})
                view_counts.append(int(stats.get('viewCount', 0)))
                like_counts.append(int(stats.get('likeCount', 0)))
                comment_counts.append(int(stats.get('commentCount', 0)))
            
            if not view_counts:
                return None
            
            # 평균 계산
            avg_stats = {
                'avg_views': sum(view_counts) / len(view_counts),
                'avg_likes': sum(like_counts) / len(like_counts),
                'avg_comments': sum(comment_counts) / len(comment_counts),
                'video_count': len(view_counts),
                'max_views': max(view_counts),
                'min_views': min(view_counts)
            }
            
            return avg_stats
            
        except HttpError as e:
            print(f"채널 통계 가져오기 오류 (채널 ID: {channel_id}): {e}")
            return None

    def get_quota_usage(self):
        """현재 API 할당량 사용량 반환"""
        return self.quota_used