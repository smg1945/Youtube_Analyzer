"""
YouTube Data API 관련 함수들 (수정된 버전 - 필터링 로직 개선)
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
        
        # API 키 검증
        if not self.api_key or self.api_key == "YOUR_YOUTUBE_API_KEY_HERE":
            raise ValueError("YouTube API 키가 설정되지 않았습니다. config.py에서 DEVELOPER_KEY를 설정해주세요.")
        
        try:
            self.youtube = build(
                config.YOUTUBE_API_SERVICE_NAME,
                config.YOUTUBE_API_VERSION,
                developerKey=self.api_key
            )
            print(f"✅ YouTube API 클라이언트 초기화 완료")
        except Exception as e:
            raise Exception(f"YouTube API 클라이언트 초기화 실패: {e}")
            
        self.quota_used = 0
        self.quota_limit = config.API_QUOTA_LIMIT
        
    def test_api_connection(self):
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
                print("💡 원인: API 할당량 초과 - 내일 다시 시도해주세요")
            elif "keyInvalid" in str(e):
                print("💡 원인: 잘못된 API 키 - config.py에서 API 키를 확인해주세요")
            return False
        except Exception as e:
            print(f"❌ API 연결 테스트 중 예상치 못한 오류: {e}")
            return False
    
    def search_videos_by_keyword(self, keyword, region_code="KR", max_results=200, 
                                max_subscriber_count=None, min_view_count=None, period_days=30,
                                video_type="all"):
        """
        키워드로 영상 검색 (구독자 수, 조회수, 영상 유형 필터 포함) - 수정된 버전
        
        Args:
            keyword (str): 검색 키워드
            region_code (str): 지역 코드
            max_results (int): 최대 결과 수
            max_subscriber_count (int): 최대 구독자 수
            min_view_count (int): 최소 조회수
            period_days (int): 검색 기간 (일)
            video_type (str): 영상 유형 ("all", "long", "shorts")
        """
        print(f"\n🔍 키워드 검색 시작")
        print(f"   키워드: '{keyword}'")
        print(f"   지역: {region_code}")
        print(f"   영상 유형: {video_type}")
        print(f"   기간: 최근 {period_days}일")
        print(f"   최대 구독자: {max_subscriber_count if max_subscriber_count else '제한 없음'}")
        print(f"   최소 조회수: {min_view_count if min_view_count else '제한 없음'}")
        
        try:
            # 1단계: API 연결 테스트
            if not self.test_api_connection():
                return []
            
            # 2단계: 검색 파라미터 유효성 검사
            validation_errors = self.validate_search_parameters(keyword, region_code, period_days)
            if validation_errors:
                print(f"❌ 검색 파라미터 오류: {', '.join(validation_errors)}")
                return []
            
            # 3단계: 검색 기간 설정
            published_after = (datetime.now() - timedelta(days=period_days)).isoformat() + 'Z'
            print(f"📅 검색 기간: {published_after} 이후")
            
            # 4단계: 키워드로 영상 검색 (더 많은 결과 수집)
            print("🔍 YouTube에서 영상 검색 중...")
            all_video_ids = []
            
            # 여러 번 검색해서 더 많은 결과 수집
            search_iterations = 3 if video_type != "all" else 2
            
            for iteration in range(search_iterations):
                try:
                    # 검색 쿼리 다양화
                    search_query = keyword
                    if video_type == "shorts":
                        search_query += " #shorts" if iteration == 1 else " 쇼츠" if iteration == 2 else ""
                    elif video_type == "long":
                        # 롱폼을 위한 추가 키워드는 사용하지 않음 (필터링으로 처리)
                        pass
                    
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=search_query,
                        type='video',
                        order='date',
                        publishedAfter=published_after,
                        regionCode=region_code,
                        maxResults=50,  # 배치당 50개
                        relevanceLanguage='ko' if region_code == 'KR' else 'en'
                    )
                    search_response = search_request.execute()
                    self.quota_used += 100
                    
                    batch_video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                    all_video_ids.extend(batch_video_ids)
                    
                    print(f"   검색 배치 {iteration + 1}: {len(batch_video_ids)}개 영상 발견")
                    
                    # API 요청 제한 고려
                    time.sleep(0.2)
                    
                except HttpError as e:
                    print(f"❌ 검색 배치 {iteration + 1} 오류: {e}")
                    if "quotaExceeded" in str(e):
                        break
                    continue
            
            # 중복 제거
            unique_video_ids = list(dict.fromkeys(all_video_ids))
            print(f"✅ 검색 완료: 총 {len(unique_video_ids)}개 고유 영상 발견")
            
            if not unique_video_ids:
                print(f"❌ '{keyword}' 키워드로 영상을 찾을 수 없습니다.")
                self._print_search_suggestions(keyword, period_days)
                return []
            
            # 5단계: 영상 상세 정보 가져오기
            print("📊 영상 상세 정보 수집 중...")
            videos_details = self.get_video_details(unique_video_ids)
            
            if not videos_details:
                print("❌ 영상 상세 정보를 가져올 수 없습니다.")
                return []
            
            print(f"✅ 상세 정보 수집 완료: {len(videos_details)}개")
            
            # 6단계: 영상 유형 필터링 (가장 먼저 적용)
            if video_type != "all":
                print(f"🎬 영상 유형 필터링 적용 중: {video_type}")
                videos_details = self.filter_videos_by_type(videos_details, video_type)
                print(f"   영상 유형 필터링 후: {len(videos_details)}개 영상")
                
                if not videos_details:
                    print(f"❌ {video_type} 유형의 영상이 없습니다.")
                    self._print_video_type_suggestions(video_type)
                    return []
            
            # 7단계: 조회수 및 구독자 수 필터링
            print("🔧 추가 필터링 적용 중...")
            filtered_videos = self._apply_additional_filters(
                videos_details, 
                min_view_count, 
                max_subscriber_count
            )
            
            if not filtered_videos:
                print("❌ 필터링 후 남은 영상이 없습니다.")
                self._print_filter_suggestions(min_view_count, max_subscriber_count, period_days)
                return []
            
            # 최신순으로 정렬
            filtered_videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
            
            print(f"🎉 최종 결과: {len(filtered_videos)}개 영상 ({video_type} 유형)")
            return filtered_videos[:max_results]
            
        except Exception as e:
            print(f"❌ 키워드 검색 전체 과정 오류: {e}")
            import traceback
            print("상세 오류 정보:")
            print(traceback.format_exc())
            return []

    def filter_videos_by_type(self, videos, video_type="all"):
        """
        영상 유형별 필터링 - 개선된 버전
        
        Args:
            videos (list): 영상 목록
            video_type (str): "all", "long", "shorts"
            
        Returns:
            list: 필터링된 영상 목록
        """
        if video_type == "all":
            return videos
        
        filtered_videos = []
        shorts_count = 0
        long_count = 0
        invalid_count = 0
        
        for video in videos:
            try:
                duration_str = video['contentDetails']['duration']
                duration_seconds = self.parse_duration(duration_str)
                
                # 영상 유형 판별
                is_shorts = duration_seconds <= config.SHORT_VIDEO_MAX_DURATION  # 60초 이하
                is_long = duration_seconds > config.LONG_VIDEO_MIN_DURATION     # 60초 초과
                
                if video_type == "shorts" and is_shorts:
                    filtered_videos.append(video)
                    shorts_count += 1
                elif video_type == "long" and is_long:
                    filtered_videos.append(video)
                    long_count += 1
                    
            except Exception as e:
                print(f"⚠️ 영상 유형 판별 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                invalid_count += 1
                continue
        
        # 필터링 결과 출력
        print(f"   🎬 영상 유형 분석 결과:")
        print(f"      쇼츠 (≤60초): {shorts_count}개")
        print(f"      롱폼 (>60초): {long_count}개")
        print(f"      오류/무효: {invalid_count}개")
        print(f"      선택된 유형 ({video_type}): {len(filtered_videos)}개")
        
        return filtered_videos

    def _apply_additional_filters(self, videos, min_view_count, max_subscriber_count):
        """추가 필터링 적용 (조회수, 구독자 수)"""
        filtered_videos = []
        channel_subscriber_cache = {}
        
        skipped_view_count = 0
        skipped_subscriber_count = 0
        api_errors = 0
        
        for i, video in enumerate(videos, 1):
            print(f"   필터링 진행: {i}/{len(videos)}", end='\r')
            
            try:
                channel_id = video['snippet']['channelId']
                video_views = int(video['statistics'].get('viewCount', 0))
                
                # 조회수 필터 체크
                if min_view_count and video_views < min_view_count:
                    skipped_view_count += 1
                    continue
                
                # 구독자 수 필터 체크
                if max_subscriber_count:
                    if channel_id not in channel_subscriber_cache:
                        try:
                            channel_info = self.get_channel_info(channel_id)
                            if channel_info:
                                subscriber_count = int(channel_info['statistics'].get('subscriberCount', 0))
                                channel_subscriber_cache[channel_id] = subscriber_count
                            else:
                                channel_subscriber_cache[channel_id] = 0
                                api_errors += 1
                        except Exception as e:
                            print(f"\n⚠️ 채널 정보 가져오기 실패 (채널 ID: {channel_id}): {e}")
                            channel_subscriber_cache[channel_id] = 0
                            api_errors += 1
                    
                    channel_subscribers = channel_subscriber_cache[channel_id]
                    if channel_subscribers > max_subscriber_count:
                        skipped_subscriber_count += 1
                        continue
                
                # 모든 필터 통과
                filtered_videos.append(video)
                
            except Exception as e:
                print(f"\n❌ 영상 처리 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                continue
        
        print(f"\n✅ 추가 필터링 완료:")
        print(f"   원본 영상 수: {len(videos)}개")
        print(f"   조회수 필터로 제외: {skipped_view_count}개")
        print(f"   구독자 수 필터로 제외: {skipped_subscriber_count}개")
        print(f"   API 오류: {api_errors}개")
        print(f"   최종 결과: {len(filtered_videos)}개")
        
        return filtered_videos

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

    def _print_video_type_suggestions(self, video_type):
        """영상 유형 제안사항 출력"""
        print(f"💡 해결 방법 ({video_type} 유형 없음):")
        if video_type == "shorts":
            print("   1. '쇼츠', '#shorts' 키워드 추가")
            print("   2. 전체 유형으로 검색 후 수동 필터링")
        elif video_type == "long":
            print("   1. 더 일반적인 키워드 사용")
            print("   2. 검색 기간 늘리기")
        print("   3. 전체 유형으로 먼저 테스트")

    def _print_filter_suggestions(self, min_view_count, max_subscriber_count, period_days):
        """필터 제안사항 출력"""
        print("💡 해결 방법:")
        if min_view_count:
            print(f"   1. 최소 조회수 낮추기: {min_view_count:,} → {min_view_count//10:,}")
        if max_subscriber_count:
            print(f"   2. 최대 구독자 늘리기: {max_subscriber_count:,} → {max_subscriber_count*5:,}")
        print(f"   3. 검색 기간 늘리기: {period_days}일 → {period_days*2}일")
        print("   4. 모든 필터 해제 후 테스트")

    def validate_search_parameters(self, keyword, region_code, period_days):
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

    def get_video_details(self, video_ids):
        """영상 상세 정보 가져오기"""
        try:
            if not video_ids:
                return []
                
            video_details = []
            
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
                    
                    if i + 50 < len(video_ids):
                        time.sleep(0.1)
                        
                except HttpError as e:
                    print(f"❌ 영상 상세 정보 배치 오류: {e}")
                    continue
            
            return video_details
            
        except Exception as e:
            print(f"❌ 영상 상세 정보 가져오기 전체 오류: {e}")
            return []

    def get_trending_videos(self, region_code="KR", category_id=None, max_results=200):
        """실시간 트렌딩 영상 목록 가져오기"""
        try:
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
            
            self.quota_used += 1
            return response.get('items', [])
            
        except HttpError as e:
            if "quotaExceeded" in str(e):
                raise Exception("YouTube API 일일 할당량을 초과했습니다. 내일 다시 시도해주세요.")
            else:
                print(f"YouTube API 오류: {e}")
                return []

    def get_channel_info(self, channel_id):
        """채널 정보 가져오기"""
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

    def get_channel_recent_videos_stats(self, channel_id, max_results=10, light_mode=False):
        """채널의 최근 영상들 통계 가져오기 (outlier score 계산용)"""
        try:
            if light_mode:
                # 경량 모드: 간단한 추정치 사용
                return {
                    'avg_views': 10000,
                    'avg_likes': 100,
                    'avg_comments': 10,
                    'video_count': 10,
                    'max_views': 50000,
                    'min_views': 1000
                }
            
            # 정상 모드
            search_request = self.youtube.search().list(
                part='snippet',
                channelId=channel_id,
                type='video',
                order='date',
                maxResults=max_results
            )
            search_response = search_request.execute()
            
            self.quota_used += 100
            
            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
            
            if not video_ids:
                return None
            
            videos_stats = self.get_video_details(video_ids)
            
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
            
            return {
                'avg_views': sum(view_counts) / len(view_counts),
                'avg_likes': sum(like_counts) / len(like_counts),
                'avg_comments': sum(comment_counts) / len(comment_counts),
                'video_count': len(view_counts),
                'max_views': max(view_counts),
                'min_views': min(view_counts)
            }
            
        except HttpError as e:
            print(f"채널 통계 가져오기 오류 (채널 ID: {channel_id}): {e}")
            return None

    def parse_duration(self, duration_str):
        """YouTube API의 duration 문자열을 초 단위로 변환"""
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

    # 기타 메서드들은 동일하게 유지
    def check_quota_remaining(self):
        remaining = self.quota_limit - self.quota_used
        return max(0, remaining)
    
    def can_use_quota(self, required_units):
        return self.quota_used + required_units <= self.quota_limit
    
    def get_quota_status(self):
        used_percentage = (self.quota_used / self.quota_limit) * 100
        return {
            'used': self.quota_used,
            'limit': self.quota_limit,
            'remaining': self.check_quota_remaining(),
            'percentage': used_percentage,
            'status': 'high' if used_percentage > 80 else 'medium' if used_percentage > 50 else 'low'
        }

    def get_video_comments(self, video_id, max_results=50):
        """영상 댓글 가져오기"""
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

    def get_best_thumbnail_url(self, thumbnails):
        """최고 품질의 썸네일 URL 반환"""
        quality_priority = ['maxres', 'high', 'medium', 'default']
        
        for quality in quality_priority:
            if quality in thumbnails:
                return thumbnails[quality]['url']
        
        return None

    def download_thumbnail(self, thumbnail_url, video_id, video_title="", rank=0):
        """썸네일 이미지 다운로드"""
        if not thumbnail_url:
            return None
            
        try:
            response = requests.get(thumbnail_url, timeout=config.THUMBNAIL_DOWNLOAD_TIMEOUT)
            if response.status_code == 200:
                os.makedirs('thumbnails', exist_ok=True)
                
                safe_title = re.sub(r'[^\w\s-]', '', video_title.replace(' ', '_'))[:config.THUMBNAIL_MAX_FILENAME_LENGTH]
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
                print(f"❌ 썸네일 다운로드 실패 (HTTP {response.status_code})")
                return None
        except Exception as e:
            print(f"❌ 썸네일 다운로드 오류: {e}")
            return None

    def download_multiple_thumbnails(self, videos_info):
        """여러 영상의 썸네일을 일괄 다운로드"""
        try:
            print(f"🖼️ {len(videos_info)}개 영상의 썸네일 다운로드를 시작합니다...")
            
            downloaded_files = []
            failed_count = 0
            
            for i, video_info in enumerate(videos_info, 1):
                print(f"   진행률: {i}/{len(videos_info)}", end="\r")
                
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
        """채널의 영상 목록 가져오기"""
        try:
            # 채널의 업로드 플레이리스트 ID 가져오기
            channel_request = self.youtube.channels().list(
                part='contentDetails',
                id=channel_id
            )
            channel_response = channel_request.execute()
            
            if not channel_response['items']:
                print(f"❌ 채널 정보를 찾을 수 없습니다: {channel_id}")
                return []
            
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
            
            # 영상 상세 정보 가져오기
            if videos:
                video_ids = [video['id'] for video in videos]
                detailed_videos = self.get_video_details(video_ids)
                
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
            
            print(f"✅ 채널 영상 목록 가져오기 완료: {len(videos)}개")
            return videos[:max_results]
            
        except Exception as e:
            print(f"❌ 채널 영상 목록 가져오기 오류: {e}")
            return []

    def get_quota_usage(self):
        """현재 API 할당량 사용량 반환"""
        return self.quota_used