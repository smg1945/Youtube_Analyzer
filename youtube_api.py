"""
YouTube Data API 관련 함수들 (완전 개선된 버전)
- 대량 검색 기능 (1000+개 영상 수집)
- 다양한 검색 전략 (최신순, 관련도순, 조회수순)
- 키워드 변형을 통한 검색 범위 확장
- 스마트 필터링으로 API 효율성 극대화
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
                               video_type="all", search_intensity="medium"):
        """
        🚀 개선된 키워드로 영상 검색 - 대량 수집 및 스마트 필터링
        
        개선사항:
        - 기존: 150개 수집 → 개선: 1000+개 수집
        - 페이징 활용으로 검색 범위 대폭 확장
        - 다양한 정렬 방식으로 누락 영상 최소화
        - 키워드 변형으로 관련 영상 추가 발굴
        
        Args:
            keyword (str): 검색 키워드
            region_code (str): 지역 코드
            max_results (int): 최종 결과 수
            max_subscriber_count (int): 최대 구독자 수
            min_view_count (int): 최소 조회수
            period_days (int): 검색 기간 (일)
            video_type (str): 영상 유형 ("all", "long", "shorts")
            search_intensity (str): 검색 강도 ("basic", "medium", "maximum")
        """
        print(f"\n🔍 개선된 키워드 검색 시작")
        print(f"   키워드: '{keyword}'")
        print(f"   검색 강도: {search_intensity}")
        print(f"   목표: {max_results * 3}개 수집 → {max_results}개 필터링")
        
        try:
            # 1단계: API 연결 테스트
            if not self.test_api_connection():
                return []
            
            # 2단계: 검색 파라미터 유효성 검사
            validation_errors = self._validate_search_parameters(keyword, region_code, period_days)
            if validation_errors:
                print(f"❌ 검색 파라미터 오류: {', '.join(validation_errors)}")
                return []
            
            # 3단계: 검색 강도별 설정
            search_config = self._get_search_intensity_config(search_intensity)
            print(f"   📊 검색 설정: {search_config['max_pages']}페이지, {search_config['keyword_variations']}개 변형")
            
            # 4단계: 검색 기간 설정
            published_after = (datetime.now() - timedelta(days=period_days)).isoformat() + 'Z'
            print(f"   📅 검색 기간: {published_after} 이후")
            
            # 5단계: 모든 영상 ID를 수집할 set (중복 자동 제거)
            all_video_ids = set()
            
            # 6단계: 🔥 핵심 개선 - 다단계 검색 전략
            search_strategies = self._create_search_strategies(keyword, search_config)
            
            total_api_calls = 0
            
            for strategy_idx, strategy in enumerate(search_strategies, 1):
                print(f"\n📊 전략 {strategy_idx}: {strategy['description']}")
                
                for query in strategy['queries']:
                    if total_api_calls >= search_config['api_budget'] // 100:
                        print("⚠️ API 예산 한도 도달")
                        break
                        
                    # 페이징을 통한 대량 수집
                    strategy_videos = self._search_with_pagination(
                        query=query,
                        order=strategy['order'],
                        max_pages=strategy['max_pages'],
                        published_after=published_after,
                        region_code=region_code,
                        video_type=video_type
                    )
                    
                    before_count = len(all_video_ids)
                    all_video_ids.update(strategy_videos)
                    new_videos = len(all_video_ids) - before_count
                    
                    total_api_calls += strategy['max_pages']
                    
                    print(f"   '{query}' ({strategy['order']}): +{new_videos}개 (누적: {len(all_video_ids)}개)")
                    
                    # 목표량 달성시 조기 종료
                    if len(all_video_ids) >= max_results * 5:
                        print(f"✅ 목표 수집량 달성: {len(all_video_ids)}개")
                        break
                
                if len(all_video_ids) >= max_results * 5:
                    break
            
            print(f"\n🎉 검색 완료: 총 {len(all_video_ids)}개 고유 영상 수집")
            
            if not all_video_ids:
                print(f"❌ '{keyword}' 키워드로 영상을 찾을 수 없습니다.")
                self._print_search_suggestions(keyword, period_days)
                return []
            
            # 7단계: 영상 상세 정보 가져오기
            print("📊 영상 상세 정보 수집 중...")
            videos_details = self.get_video_details(list(all_video_ids))
            
            if not videos_details:
                print("❌ 영상 상세 정보를 가져올 수 없습니다.")
                return []
            
            print(f"✅ 상세 정보 수집 완료: {len(videos_details)}개")
            
            # 8단계: 포괄적 필터링 적용
            filtered_videos = self._apply_comprehensive_filtering(
                videos_details, video_type, min_view_count, max_subscriber_count
            )
            
            if not filtered_videos:
                print("❌ 필터링 후 남은 영상이 없습니다.")
                self._print_filter_suggestions(min_view_count, max_subscriber_count, period_days)
                return []
            
            # 9단계: 최신순 정렬 후 결과 제한
            filtered_videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
            final_results = filtered_videos[:max_results]
            
            print(f"🎊 최종 결과: {len(final_results)}개 영상")
            print(f"📈 수집 효율성: {len(final_results)}/{len(all_video_ids)} = {len(final_results)/len(all_video_ids)*100:.1f}%")
            
            return final_results
            
        except Exception as e:
            print(f"❌ 개선된 검색 전체 과정 오류: {e}")
            import traceback
            print("상세 오류 정보:")
            print(traceback.format_exc())
            return []
    
    def _get_search_intensity_config(self, intensity):
        """검색 강도별 설정 반환"""
        configs = {
            "basic": {
                "max_pages": 3,
                "keyword_variations": 1,
                "api_budget": 500,
                "strategies": 2
            },
            "medium": {
                "max_pages": 8,
                "keyword_variations": 2,
                "api_budget": 1500,
                "strategies": 4
            },
            "maximum": {
                "max_pages": 15,
                "keyword_variations": 3,
                "api_budget": 3000,
                "strategies": 6
            }
        }
        return configs.get(intensity, configs["medium"])
    
    def _create_search_strategies(self, keyword, search_config):
        """다양한 검색 전략 생성"""
        strategies = [
            # 전략 1: 최신순 대량 검색
            {
                'description': '최신순 검색',
                'order': 'date',
                'max_pages': search_config['max_pages'],
                'queries': [keyword]
            },
            # 전략 2: 관련도순 검색  
            {
                'description': '관련도순 검색',
                'order': 'relevance',
                'max_pages': max(search_config['max_pages'] - 2, 3),
                'queries': [keyword]
            },
            # 전략 3: 조회수순 검색
            {
                'description': '인기순 검색',
                'order': 'viewCount',
                'max_pages': max(search_config['max_pages'] - 4, 2),
                'queries': [keyword]
            }
        ]
        
        # 전략 4+: 키워드 변형 검색
        if search_config['keyword_variations'] > 1:
            keyword_variations = self._generate_keyword_variations(keyword)
            
            for i, variant in enumerate(keyword_variations[1:search_config['keyword_variations']], 1):
                strategies.append({
                    'description': f'변형 키워드 {i}: {variant}',
                    'order': 'date',
                    'max_pages': max(search_config['max_pages'] // 2, 2),
                    'queries': [variant]
                })
        
        return strategies[:search_config.get('strategies', 4)]
    
    def _search_with_pagination(self, query, order, max_pages, published_after, region_code, video_type):
        """페이징을 활용한 대량 검색"""
        video_ids = []
        next_page_token = None
        
        for page in range(max_pages):
            try:
                search_params = {
                    'part': 'snippet',
                    'q': query,
                    'type': 'video',
                    'order': order,
                    'publishedAfter': published_after,
                    'regionCode': region_code,
                    'maxResults': 50,
                    'relevanceLanguage': 'ko' if region_code == 'KR' else 'en'
                }
                
                # 페이지 토큰 추가
                if next_page_token:
                    search_params['pageToken'] = next_page_token
                
                # 영상 유형에 따른 추가 필터 (YouTube API 레벨)
                if video_type == "shorts":
                    search_params['videoDuration'] = 'short'  # 4분 이하
                elif video_type == "long":
                    search_params['videoDuration'] = 'medium'  # 4-20분
                
                # YouTube 검색 실행
                request = self.youtube.search().list(**search_params)
                response = request.execute()
                self.quota_used += 100
                
                # 결과 수집
                page_results = [item['id']['videoId'] for item in response.get('items', [])]
                video_ids.extend(page_results)
                
                # 다음 페이지 확인
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
                # API 요청 제한 준수
                time.sleep(0.1)
                
            except HttpError as e:
                if "quotaExceeded" in str(e):
                    print(f"\n⚠️ API 할당량 도달 (페이지 {page+1})")
                    break
                else:
                    print(f"\n❌ 페이지 {page+1} 오류: {e}")
                    continue
            except Exception as e:
                print(f"\n❌ 페이지 {page+1} 예외: {e}")
                continue
        
        return video_ids
    
    def _generate_keyword_variations(self, keyword):
        """키워드 변형 생성으로 검색 범위 확장"""
        variations = [keyword]
        
        # 한국어 키워드별 관련 용어
        korean_synonyms = {
            '건강': ['헬스', '웰빙', '다이어트', '피트니스'],
            '요리': ['쿠킹', '레시피', '음식', '맛집', '베이킹'],
            '운동': ['헬스', '홈트', '피트니스', '다이어트', '근육'],
            '여행': ['여행지', '관광', '트래블', '여행기'],
            '게임': ['게이밍', '겜', 'gaming', '게임플레이'],
            '음악': ['뮤직', '노래', '가요', 'music'],
            '리뷰': ['후기', '사용기', '언박싱', '개봉기'],
            '브이로그': ['vlog', '일상', '데일리', '루틴'],
            '먹방': ['음식', '맛집', 'mukbang', '먹거리'],
            '패션': ['스타일', '옷', '코디', 'fashion'],
            '뷰티': ['메이크업', '화장', '스킨케어', 'beauty'],
            '드라마': ['시리즈', '드라마', '웹드라마'],
            '영화': ['무비', 'movie', '영화리뷰'],
            '책': ['독서', '서평', '북리뷰', '책리뷰']
        }
        
        # 영어 키워드 처리
        english_synonyms = {
            'review': ['unboxing', 'test', 'comparison'],
            'cooking': ['recipe', 'food', 'kitchen'],
            'workout': ['fitness', 'exercise', 'gym'],
            'travel': ['trip', 'vacation', 'journey'],
            'music': ['song', 'melody', 'beats'],
            'game': ['gaming', 'gameplay'],
            'vlog': ['daily', 'lifestyle', 'routine'],
            'beauty': ['makeup', 'skincare'],
            'fashion': ['style', 'outfit', 'clothing']
        }
        
        # 키워드에 맞는 동의어 추가
        keyword_lower = keyword.lower()
        
        # 한국어 동의어 확인
        for base_word, synonyms in korean_synonyms.items():
            if base_word in keyword_lower:
                variations.extend(synonyms[:2])  # 상위 2개만
                break
        
        # 영어 동의어 확인
        for base_word, synonyms in english_synonyms.items():
            if base_word in keyword_lower:
                variations.extend(synonyms[:2])  # 상위 2개만
                break
        
        # 특수 패턴 추가
        if any(word in keyword_lower for word in ['리뷰', 'review']):
            variations.extend(['언박싱', '개봉기', '사용후기'])
        
        if any(word in keyword_lower for word in ['브이로그', 'vlog']):
            variations.extend(['일상', '데일리', '루틴'])
        
        if any(word in keyword_lower for word in ['먹방', 'mukbang']):
            variations.extend(['맛집', '음식', '먹거리'])
        
        # 중복 제거 및 최대 5개로 제한
        unique_variations = list(dict.fromkeys(variations))[:5]
        
        if len(unique_variations) > 1:
            print(f"   🔄 키워드 변형: {unique_variations}")
        
        return unique_variations
    
    def _apply_comprehensive_filtering(self, videos, video_type, min_view_count, max_subscriber_count):
        """포괄적 필터링 - 단계별 적용으로 효율성 극대화"""
        print(f"\n🔧 포괄적 필터링 시작: {len(videos)}개")
        
        # 1단계: 기본 데이터 유효성 검사
        valid_videos = []
        for video in videos:
            try:
                if (video.get('statistics', {}).get('viewCount') and 
                    video.get('contentDetails', {}).get('duration')):
                    valid_videos.append(video)
            except:
                continue
        
        print(f"   1단계 (유효성): {len(valid_videos)}개")
        
        # 2단계: 영상 유형 필터링 (빠른 처리)
        if video_type != "all":
            type_filtered = []
            shorts_count = 0
            long_count = 0
            
            for video in valid_videos:
                try:
                    duration_seconds = self.parse_duration(video['contentDetails']['duration'])
                    
                    if video_type == "shorts" and duration_seconds <= config.SHORT_VIDEO_MAX_DURATION:
                        type_filtered.append(video)
                        shorts_count += 1
                    elif video_type == "long" and duration_seconds > config.LONG_VIDEO_MIN_DURATION:
                        type_filtered.append(video)
                        long_count += 1
                except:
                    continue
            
            valid_videos = type_filtered
            print(f"   2단계 ({video_type}): {len(valid_videos)}개 (쇼츠: {shorts_count}, 롱폼: {long_count})")
        
        # 3단계: 조회수 필터링
        if min_view_count:
            view_filtered = []
            for video in valid_videos:
                try:
                    views = int(video['statistics'].get('viewCount', 0))
                    if views >= min_view_count:
                        view_filtered.append(video)
                except:
                    continue
            
            valid_videos = view_filtered
            print(f"   3단계 (조회수 {min_view_count:,}+): {len(valid_videos)}개")
        
        # 4단계: 구독자 수 필터링 (API 호출 필요하므로 마지막)
        if max_subscriber_count and valid_videos:
            print("   4단계: 구독자 수 확인 중...")
            
            # 채널별 그룹화로 API 호출 최소화
            channel_videos = {}
            for video in valid_videos:
                channel_id = video['snippet']['channelId']
                if channel_id not in channel_videos:
                    channel_videos[channel_id] = []
                channel_videos[channel_id].append(video)
            
            # 구독자 수 체크
            final_videos = []
            checked_channels = 0
            
            for channel_id, videos_list in channel_videos.items():
                try:
                    channel_info = self.get_channel_info(channel_id)
                    checked_channels += 1
                    
                    if channel_info:
                        subscribers = int(channel_info['statistics'].get('subscriberCount', 0))
                        if subscribers <= max_subscriber_count:
                            final_videos.extend(videos_list)
                    
                    # API 호출 제한
                    if checked_channels % 10 == 0:
                        time.sleep(0.1)
                        
                except Exception as e:
                    print(f"⚠️ 채널 {channel_id} 확인 오류: {e}")
                    continue
            
            valid_videos = final_videos
            print(f"   4단계 (구독자 {max_subscriber_count:,} 이하): {len(valid_videos)}개")
        
        print(f"✅ 필터링 완료: {len(valid_videos)}개 영상")
        return valid_videos
    
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
    
    def _print_filter_suggestions(self, min_view_count, max_subscriber_count, period_days):
        """필터 제안사항 출력"""
        print("💡 해결 방법:")
        if min_view_count:
            print(f"   1. 최소 조회수 낮추기: {min_view_count:,} → {min_view_count//10:,}")
        if max_subscriber_count:
            print(f"   2. 최대 구독자 늘리기: {max_subscriber_count:,} → {max_subscriber_count*5:,}")
        print(f"   3. 검색 기간 늘리기: {period_days}일 → {period_days*2}일")
        print("   4. 모든 필터 해제 후 테스트")
    
    def get_video_details(self, video_ids):
        """영상 상세 정보 가져오기 (배치 처리 최적화)"""
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
                    
                    if i + 50 < len(video_ids):
                        time.sleep(0.05)  # API 요청 제한 준수
                        
                except HttpError as e:
                    print(f"❌ 영상 상세 정보 배치 오류: {e}")
                    continue
            
            return video_details
            
        except Exception as e:
            print(f"❌ 영상 상세 정보 가져오기 전체 오류: {e}")
            return []
    
    def filter_videos_by_type(self, videos, video_type="all"):
        """영상 유형별 필터링"""
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
    
    def get_trending_shorts(self, region_code="KR", max_results=200):
        """트렌딩 쇼츠 영상 가져오기 (검색 기반)"""
        try:
            print("🎬 쇼츠 전용 검색을 실행합니다...")
            
            # 쇼츠 관련 키워드들
            shorts_keywords = ["#shorts", "쇼츠", "shorts"]
            all_shorts = []
            
            for keyword in shorts_keywords:
                try:
                    search_request = self.youtube.search().list(
                        part='snippet',
                        q=keyword,
                        type='video',
                        order='viewCount',
                        regionCode=region_code,
                        maxResults=50,
                        videoDuration='short'  # 4분 이하
                    )
                    search_response = search_request.execute()
                    self.quota_used += 100
                    
                    video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
                    
                    if video_ids:
                        videos_details = self.get_video_details(video_ids)
                        # 실제로 60초 이하인지 재확인
                        actual_shorts = self.filter_videos_by_type(videos_details, "shorts")
                        all_shorts.extend(actual_shorts)
                    
                except Exception as e:
                    print(f"쇼츠 검색 오류 (키워드: {keyword}): {e}")
                    continue
            
            # 중복 제거 및 조회수순 정렬
            unique_shorts = []
            seen_ids = set()
            
            for video in all_shorts:
                if video['id'] not in seen_ids:
                    seen_ids.add(video['id'])
                    unique_shorts.append(video)
            
            # 조회수순으로 정렬
            unique_shorts.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
            
            return unique_shorts[:max_results]
            
        except Exception as e:
            print(f"트렌딩 쇼츠 가져오기 오류: {e}")
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
    
    def get_best_thumbnail_url(self, thumbnails):
        """최고 품질의 썸네일 URL 반환"""
        quality_priority = config.THUMBNAIL_QUALITY_PRIORITY
        
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
                
                return image_path
            else:
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
    
    # API 할당량 관리 메서드들
    def check_quota_remaining(self):
        """남은 할당량 확인"""
        remaining = self.quota_limit - self.quota_used
        return max(0, remaining)
    
    def can_use_quota(self, required_units):
        """필요한 할당량 사용 가능 여부 확인"""
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
    
    def get_quota_usage(self):
        """현재 API 할당량 사용량 반환"""
        return self.quota_used
    
    def reset_quota_usage(self):
        """할당량 사용량 리셋 (디버깅용)"""
        self.quota_used = 0
        print("🔄 API 할당량 사용량이 리셋되었습니다.")
    
    def estimate_search_quota(self, keyword_count=1, max_pages=10, enable_filtering=True):
        """검색에 필요한 API 할당량 추정"""
        base_search_quota = keyword_count * max_pages * 100  # 검색 API
        video_details_quota = (keyword_count * max_pages * 50) // 50  # 영상 상세 정보
        channel_info_quota = 50 if enable_filtering else 0  # 채널 정보 (추정)
        
        total_quota = base_search_quota + video_details_quota + channel_info_quota
        
        return {
            'estimated_quota': total_quota,
            'search_quota': base_search_quota,
            'details_quota': video_details_quota,
            'filtering_quota': channel_info_quota,
            'is_feasible': total_quota <= self.quota_limit - self.quota_used
        }
    
    # 추가 유틸리티 메서드들
    def get_search_summary(self):
        """검색 요약 정보 반환"""
        return {
            'quota_used': self.quota_used,
            'quota_remaining': self.quota_limit - self.quota_used,
            'efficiency_tips': [
                "페이징을 활용해 더 많은 영상 수집",
                "다양한 정렬 방식으로 검색 범위 확장", 
                "키워드 변형으로 누락 영상 최소화",
                "스마트 필터링으로 API 호출 최적화"
            ]
        }
    
    def validate_api_key(self):
        """API 키 유효성 재검증"""
        try:
            test_request = self.youtube.channels().list(part='snippet', mine=True)
            test_request.execute()
            return True
        except:
            return self.test_api_connection()