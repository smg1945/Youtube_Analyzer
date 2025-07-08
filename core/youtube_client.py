"""
YouTube API 기본 클라이언트
연결, 인증, 기본 요청 기능만 담당
"""

import os
import time
from datetime import datetime
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import config

class YouTubeClient:
    """YouTube API 기본 클라이언트"""
    
    def __init__(self, api_key=None):
        """
        YouTube API 클라이언트 초기화
        
        Args:
            api_key (str): YouTube Data API v3 키
        """
        self.api_key = api_key or config.DEVELOPER_KEY
        
        # API 키 검증
        if not self.api_key or self.api_key == "YOUR_YOUTUBE_API_KEY_HERE":
            raise ValueError("YouTube API 키가 설정되지 않았습니다.")
        
        try:
            self.youtube = build(
                config.YOUTUBE_API_SERVICE_NAME,
                config.YOUTUBE_API_VERSION,
                developerKey=self.api_key
            )
            print(f"✅ YouTube API 클라이언트 초기화 완료")
        except Exception as e:
            raise Exception(f"YouTube API 클라이언트 초기화 실패: {e}")
            
        # 할당량 관리
        self.quota_used = 0
        self.quota_limit = config.API_QUOTA_LIMIT
        
    def test_connection(self):
        """API 연결 테스트"""
        try:
            request = self.youtube.videos().list(
                part='snippet',
                chart='mostPopular',
                regionCode='KR',
                maxResults=1
            )
            response = request.execute()
            print("✅ YouTube API 연결 테스트 성공")
            return True
        except HttpError as e:
            print(f"❌ YouTube API 연결 테스트 실패: {e}")
            if "quotaExceeded" in str(e):
                print("💡 원인: API 할당량 초과")
            elif "keyInvalid" in str(e):
                print("💡 원인: 잘못된 API 키")
            return False
        except Exception as e:
            print(f"❌ API 연결 테스트 중 예상치 못한 오류: {e}")
            return False
    
    def get_video_details(self, video_ids):
        """
        영상 상세 정보 가져오기
        
        Args:
            video_ids (list): 영상 ID 목록
            
        Returns:
            list: 영상 상세 정보 목록
        """
        try:
            if not video_ids:
                return []
                
            video_details = []
            
            # 50개씩 배치 처리
            for i in range(0, len(video_ids), 50):
                batch_ids = video_ids[i:i+50]
                
                try:
                    request = self.youtube.videos().list(
                        part='snippet,statistics,contentDetails,status',
                        id=','.join(batch_ids)
                    )
                    response = request.execute()
                    batch_videos = response.get('items', [])
                    video_details.extend(batch_videos)
                    
                    self.quota_used += 1
                    print(f"   배치 {i//50 + 1}: {len(batch_videos)}개 영상 정보 수집")
                    
                    # API 요청 제한 고려
                    if i + 50 < len(video_ids):
                        time.sleep(0.1)
                        
                except HttpError as e:
                    print(f"❌ 영상 상세 정보 배치 오류: {e}")
                    continue
            
            return video_details
            
        except Exception as e:
            print(f"❌ 영상 상세 정보 가져오기 전체 오류: {e}")
            return []

    def get_channel_info(self, channel_id):
        """
        채널 정보 가져오기
        
        Args:
            channel_id (str): 채널 ID
            
        Returns:
            dict: 채널 정보 또는 None
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
            if "quotaExceeded" in str(e):
                raise e
            else:
                return None
        except Exception as e:
            return None

    def search_channels(self, query, max_results=10):
        """
        채널 검색
        
        Args:
            query (str): 검색 쿼리
            max_results (int): 최대 결과 수
            
        Returns:
            list: 검색된 채널 목록
        """
        try:
            request = self.youtube.search().list(
                part='snippet',
                q=query,
                type='channel',
                maxResults=max_results
            )
            response = request.execute()
            self.quota_used += 100
            
            return response.get('items', [])
            
        except Exception as e:
            print(f"채널 검색 오류: {e}")
            return []

    def get_playlist_items(self, playlist_id, max_results=50):
        """
        플레이리스트 아이템 가져오기
        
        Args:
            playlist_id (str): 플레이리스트 ID
            max_results (int): 최대 결과 수
            
        Returns:
            list: 플레이리스트 아이템 목록
        """
        try:
            items = []
            next_page_token = None
            
            while len(items) < max_results:
                request = self.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=playlist_id,
                    maxResults=min(50, max_results - len(items)),
                    pageToken=next_page_token
                )
                response = request.execute()
                self.quota_used += 1
                
                items.extend(response.get('items', []))
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
            
            return items[:max_results]
            
        except Exception as e:
            print(f"플레이리스트 아이템 가져오기 오류: {e}")
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
                order='relevance'
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

    def parse_duration(self, duration_str):
        """
        YouTube API의 duration 문자열을 초 단위로 변환
        
        Args:
            duration_str (str): PT15M33S 형태의 duration
            
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

    # 할당량 관리 메서드들
    def check_quota_remaining(self):
        """남은 할당량 확인"""
        remaining = self.quota_limit - self.quota_used
        return max(0, remaining)
    
    def can_use_quota(self, required_units):
        """할당량 사용 가능 여부 확인"""
        return self.quota_used + required_units <= self.quota_limit
    
    def get_quota_status(self):
        """할당량 상태 정보"""
        used_percentage = (self.quota_used / self.quota_limit) * 100
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.check_quota_remaining(),
            'percentage': used_percentage,
            'status': 'high' if used_percentage > 80 else 'medium' if used_percentage > 50 else 'low'
        }

    def get_quota_usage(self):
        """현재 할당량 사용량 반환"""
        return self.quota_used