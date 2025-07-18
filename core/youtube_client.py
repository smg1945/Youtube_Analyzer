"""
YouTube API 클라이언트 모듈
YouTube Data API v3와의 연동을 담당
"""

import re
import time
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

class YouTubeClient:
    """YouTube API 클라이언트"""
    
    def __init__(self, api_key):
        """
        YouTube 클라이언트 초기화
        
        Args:
            api_key (str): YouTube Data API v3 키
        """
        self.api_key = api_key
        self.quota_used = 0
        self.quota_limit = config.API_QUOTA_LIMIT
        
        try:
            self.youtube = build(
                config.YOUTUBE_API_SERVICE_NAME,
                config.YOUTUBE_API_VERSION,
                developerKey=api_key
            )
            print("✅ YouTube API 클라이언트 초기화 완료")
        except Exception as e:
            print(f"❌ YouTube API 클라이언트 초기화 실패: {e}")
            raise
    
    def test_connection(self):
        """API 연결 테스트"""
        try:
            # 간단한 API 호출로 연결 테스트
            request = self.youtube.videos().list(
                part='snippet',
                chart='mostPopular',
                regionCode='KR',
                maxResults=1
            )
            response = request.execute()
            
            self.quota_used += 1
            print("✅ YouTube API 연결 확인됨")
            return True
            
        except HttpError as e:
            if e.resp.status == 403:
                print("❌ API 키가 유효하지 않거나 할당량이 초과되었습니다.")
            elif e.resp.status == 400:
                print("❌ 잘못된 API 요청입니다.")
            else:
                print(f"❌ API 오류 (상태 코드: {e.resp.status})")
            return False
        except Exception as e:
            print(f"❌ 연결 테스트 실패: {e}")
            return False
    
    def can_use_quota(self, cost):
        """할당량 사용 가능 여부 확인"""
        return (self.quota_used + cost) <= self.quota_limit
    
    def get_video_details(self, video_ids):
        """
        영상 상세 정보 가져오기 - 길이 정보 포함
        
        Args:
            video_ids (list): 영상 ID 목록
            
        Returns:
            list: 영상 상세 정보 목록
        """
        if not video_ids:
            return []
        
        try:
            all_videos = []
            batch_size = 50  # YouTube API 제한
            
            for i in range(0, len(video_ids), batch_size):
                batch_ids = video_ids[i:i + batch_size]
                
                if not self.can_use_quota(1):
                    print("⚠️ API 할당량 부족으로 일부 영상 정보를 가져올 수 없습니다.")
                    break
                
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
                print(f"   배치 {i//batch_size + 1}: {len(batch_ids)}개 영상 처리됨")
                
                # API 요청 간격 조절
                time.sleep(0.1)
                
            print(f"✅ 총 {len(all_videos)}개 영상 상세 정보 수집 완료")
            return all_videos
            
        except HttpError as e:
            print(f"❌ 영상 상세 정보 API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 영상 상세 정보 가져오기 오류: {e}")
            return []
    
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
    
    def get_channel_info(self, channel_id):
        """
        채널 정보 가져오기
        
        Args:
            channel_id (str): 채널 ID
            
        Returns:
            dict: 채널 정보
        """
        try:
            if not self.can_use_quota(1):
                print("⚠️ API 할당량 부족으로 채널 정보를 가져올 수 없습니다.")
                return None
            
            request = self.youtube.channels().list(
                part='id,snippet,statistics,contentDetails',
                id=channel_id
            )
            response = request.execute()
            
            items = response.get('items', [])
            if items:
                self.quota_used += 1
                print(f"✅ 채널 정보 로드 완료: {items[0]['snippet']['title']}")
                return items[0]
            else:
                print(f"❌ 채널을 찾을 수 없습니다: {channel_id}")
                return None
                
        except HttpError as e:
            print(f"❌ 채널 정보 API 오류: {e}")
            return None
        except Exception as e:
            print(f"❌ 채널 정보 가져오기 오류: {e}")
            return None
    
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
        try:
            # 채널의 uploads 플레이리스트 ID 구하기
            channel_info = self.get_channel_info(channel_id)
            if not channel_info:
                return []
            
            # uploads 플레이리스트 ID는 채널 ID의 UC를 UU로 바꾼 것
            uploads_playlist_id = 'UU' + channel_id[2:] if channel_id.startswith('UC') else channel_id
            
            print(f"📺 채널 영상 목록 수집 중... (플레이리스트: {uploads_playlist_id})")
            
            video_ids = []
            page_token = None
            
            while len(video_ids) < max_results:
                if not self.can_use_quota(1):
                    print("⚠️ API 할당량 부족으로 일부 영상만 가져옵니다.")
                    break
                
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=min(50, max_results - len(video_ids)),
                    pageToken=page_token
                )
                
                response = request.execute()
                items = response.get('items', [])
                
                if not items:
                    break
                
                # 비디오 ID 추출
                for item in items:
                    video_id = item['snippet']['resourceId']['videoId']
                    video_ids.append(video_id)
                
                page_token = response.get('nextPageToken')
                if not page_token:
                    break
                
                self.quota_used += 1
                time.sleep(0.1)  # API 요청 간격 조절
            
            print(f"📋 {len(video_ids)}개 영상 ID 수집 완료")
            
            # 영상 상세 정보 가져오기
            if video_ids:
                videos = self.get_video_details(video_ids)
                
                # 정렬 적용
                if order == 'date':
                    videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
                elif order == 'viewCount':
                    videos.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
                
                return videos
            else:
                return []
                
        except HttpError as e:
            print(f"❌ 채널 영상 목록 API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 채널 영상 목록 가져오기 오류: {e}")
            return []
    
    def search_channels(self, query, max_results=10):
        """
        채널 검색
        
        Args:
            query (str): 검색어
            max_results (int): 최대 결과 수
            
        Returns:
            list: 검색된 채널 목록
        """
        try:
            if not self.can_use_quota(100):
                print("⚠️ API 할당량 부족으로 채널 검색을 할 수 없습니다.")
                return []
            
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='channel',
                maxResults=max_results,
                order='relevance'
            )
            
            response = request.execute()
            channels = response.get('items', [])
            
            self.quota_used += 100
            print(f"🔍 채널 검색 완료: {len(channels)}개 결과")
            
            return channels
            
        except HttpError as e:
            print(f"❌ 채널 검색 API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 채널 검색 오류: {e}")
            return []
    
    def get_trending_videos(self, region_code='KR', category_id=None, max_results=50):
        """
        트렌딩 영상 가져오기
        
        Args:
            region_code (str): 지역 코드
            category_id (str): 카테고리 ID (선택사항)
            max_results (int): 최대 결과 수
            
        Returns:
            list: 트렌딩 영상 목록
        """
        try:
            if not self.can_use_quota(1):
                print("⚠️ API 할당량 부족으로 트렌딩 영상을 가져올 수 없습니다.")
                return []
            
            request_params = {
                'part': 'id,snippet,statistics,contentDetails',
                'chart': 'mostPopular',
                'regionCode': region_code,
                'maxResults': max_results
            }
            
            if category_id:
                request_params['videoCategoryId'] = category_id
            
            request = self.youtube.videos().list(**request_params)
            response = request.execute()
            
            videos = response.get('items', [])
            
            # 영상 길이 파싱 추가
            for video in videos:
                duration = video.get('contentDetails', {}).get('duration', '')
                video['parsed_duration'] = self.parse_duration(duration)
            
            self.quota_used += 1
            print(f"📈 트렌딩 영상 {len(videos)}개 수집 완료 ({region_code})")
            
            return videos
            
        except HttpError as e:
            print(f"❌ 트렌딩 영상 API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 트렌딩 영상 가져오기 오류: {e}")
            return []
    
    def get_video_comments(self, video_id, max_results=20):
        """
        영상 댓글 가져오기
        
        Args:
            video_id (str): 영상 ID
            max_results (int): 최대 댓글 수
            
        Returns:
            list: 댓글 목록
        """
        try:
            if not self.can_use_quota(1):
                print("⚠️ API 할당량 부족으로 댓글을 가져올 수 없습니다.")
                return []
            
            request = self.youtube.commentThreads().list(
                part='snippet',
                videoId=video_id,
                maxResults=max_results,
                order='relevance'
            )
            
            response = request.execute()
            comments = response.get('items', [])
            
            self.quota_used += 1
            
            # 댓글 텍스트만 추출
            comment_texts = []
            for comment in comments:
                text = comment['snippet']['topLevelComment']['snippet']['textDisplay']
                comment_texts.append(text)
            
            return comment_texts
            
        except HttpError as e:
            if e.resp.status == 403:
                print(f"⚠️ 영상 {video_id}의 댓글이 비활성화되어 있습니다.")
            else:
                print(f"❌ 댓글 가져오기 API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 댓글 가져오기 오류: {e}")
            return []
    
    def get_video_captions(self, video_id):
        """
        영상 자막 목록 가져오기
        
        Args:
            video_id (str): 영상 ID
            
        Returns:
            list: 자막 목록
        """
        try:
            if not self.can_use_quota(50):
                print("⚠️ API 할당량 부족으로 자막 정보를 가져올 수 없습니다.")
                return []
            
            request = self.youtube.captions().list(
                part='snippet',
                videoId=video_id
            )
            
            response = request.execute()
            captions = response.get('items', [])
            
            self.quota_used += 50
            
            return captions
            
        except HttpError as e:
            if e.resp.status == 403:
                print(f"⚠️ 영상 {video_id}의 자막에 접근할 수 없습니다.")
            else:
                print(f"❌ 자막 목록 API 오류: {e}")
            return []
        except Exception as e:
            print(f"❌ 자막 목록 가져오기 오류: {e}")
            return []
    
    def get_quota_usage(self):
        """현재 할당량 사용량 반환"""
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.quota_limit - self.quota_used,
            'percentage': (self.quota_used / self.quota_limit) * 100 if self.quota_limit > 0 else 0
        }
    
    def reset_quota_counter(self):
        """할당량 카운터 리셋"""
        self.quota_used = 0
        print("🔄 API 할당량 카운터가 리셋되었습니다.")
    
    def extract_video_id_from_url(self, url):
        """YouTube URL에서 비디오 ID 추출"""
        try:
            patterns = [
                r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
                r'youtube\.com/watch\?.*v=([a-zA-Z0-9_-]{11})'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    return match.group(1)
            
            # URL이 아니라 직접 ID인 경우
            if re.match(r'^[a-zA-Z0-9_-]{11}$', url):
                return url
            
            return None
            
        except Exception as e:
            print(f"비디오 ID 추출 오류: {e}")
            return None
    
    def extract_channel_id_from_url(self, url):
        """YouTube URL에서 채널 ID 추출"""
        try:
            patterns = [
                r'youtube\.com/channel/([UC][a-zA-Z0-9_-]{22})',
                r'youtube\.com/c/([a-zA-Z0-9_.-]+)',
                r'youtube\.com/user/([a-zA-Z0-9_.-]+)',
                r'youtube\.com/@([a-zA-Z0-9_.-]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url)
                if match:
                    identifier = match.group(1)
                    
                    # UC로 시작하는 경우 채널 ID
                    if identifier.startswith('UC'):
                        return identifier
                    else:
                        # 핸들이나 사용자명인 경우 검색으로 채널 ID 찾기
                        return self.resolve_channel_identifier(identifier)
            
            # 직접 채널 ID인 경우
            if re.match(r'^UC[a-zA-Z0-9_-]{22}$', url):
                return url
            
            # 핸들명인 경우
            return self.resolve_channel_identifier(url)
            
        except Exception as e:
            print(f"채널 ID 추출 오류: {e}")
            return None
    
    def resolve_channel_identifier(self, identifier):
        """채널 핸들이나 사용자명을 채널 ID로 변환"""
        try:
            # 채널 검색으로 시도
            channels = self.search_channels(identifier, max_results=5)
            
            for channel in channels:
                channel_title = channel['snippet']['title'].lower()
                if identifier.lower() in channel_title or channel_title in identifier.lower():
                    return channel['id']['channelId']
            
            print(f"⚠️ '{identifier}'에 해당하는 채널을 찾을 수 없습니다.")
            return None
            
        except Exception as e:
            print(f"채널 ID 변환 오류: {e}")
            return None
    
    def get_api_info(self):
        """API 클라이언트 정보 반환"""
        return {
            'api_key_set': bool(self.api_key and self.api_key != "YOUR_YOUTUBE_API_KEY_HERE"),
            'service_name': config.YOUTUBE_API_SERVICE_NAME,
            'api_version': config.YOUTUBE_API_VERSION,
            'quota_usage': self.get_quota_usage()
        }


# 유틸리티 함수들
def create_client(api_key=None):
    """
    YouTube 클라이언트 생성 헬퍼 함수
    
    Args:
        api_key (str): API 키 (None인 경우 config에서 가져옴)
        
    Returns:
        YouTubeClient: 클라이언트 인스턴스
    """
    if not api_key:
        api_key = config.DEVELOPER_KEY
    
    return YouTubeClient(api_key)

def test_api_key(api_key):
    """
    API 키 유효성 테스트
    
    Args:
        api_key (str): 테스트할 API 키
        
    Returns:
        bool: 유효성 여부
    """
    try:
        client = YouTubeClient(api_key)
        return client.test_connection()
    except Exception as e:
        print(f"API 키 테스트 실패: {e}")
        return False


if __name__ == "__main__":
    # 테스트 코드
    print("🧪 YouTube 클라이언트 테스트")
    
    # API 키 확인
    if config.DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
        print("❌ API 키가 설정되지 않았습니다.")
        print("config.py 파일에서 DEVELOPER_KEY를 설정하세요.")
    else:
        try:
            # 클라이언트 생성 및 테스트
            client = create_client()
            
            if client.test_connection():
                print("✅ YouTube API 연결 성공")
                
                # 간단한 기능 테스트
                print("\n📊 기능 테스트:")
                
                # 트렌딩 영상 테스트
                trending = client.get_trending_videos(max_results=5)
                print(f"   트렌딩 영상: {len(trending)}개")
                
                # 할당량 정보
                quota_info = client.get_quota_usage()
                print(f"   할당량 사용: {quota_info['used']}/{quota_info['limit']} ({quota_info['percentage']:.1f}%)")
                
            else:
                print("❌ YouTube API 연결 실패")
                
        except Exception as e:
            print(f"❌ 테스트 실패: {e}")