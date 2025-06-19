"""
YouTube 트렌드 분석기 - 메인 실행 파일
"""

import os
import sys
from datetime import datetime
import config
from youtube_api import YouTubeAPIClient
from data_analyzer import DataAnalyzer
from excel_generator import ExcelGenerator

class YouTubeTrendAnalyzer:
    def __init__(self):
        """YouTube 트렌드 분석기 초기화"""
        self.api_client = None
        self.analyzer = None
        self.excel_generator = None
        
    def display_welcome(self):
        """환영 메시지 출력"""
        print("=" * 60)
        print("🎬 YouTube 트렌드 분석기 v1.0")
        print("=" * 60)
        print("최신 트렌드 영상을 분석하여 엑셀 리포트를 생성합니다.")
        print()
    
    def get_user_settings(self):
        """사용자 설정 입력 받기"""
        settings = {}
        
        print("📋 분석 설정을 선택해주세요:")
        print()
        
        # 0. 분석 모드 선택
        print("0. 분석 모드:")
        print("   1) 트렌딩 영상 분석")
        print("   2) 키워드 검색 분석")
        
        while True:
            choice = input("선택 (1-2): ").strip()
            if choice == "1":
                settings['mode'] = "trending"
                settings['mode_name'] = "트렌딩 분석"
                break
            elif choice == "2":
                settings['mode'] = "keyword"
                settings['mode_name'] = "키워드 분석"
                break
            else:
                print("올바른 번호를 선택해주세요.")
        
        print()
        
        # 1. 지역 선택
        print("1. 분석 지역:")
        print("   1) 한국 (KR)")
        print("   2) 글로벌 (US)")
        
        while True:
            choice = input("선택 (1-2): ").strip()
            if choice == "1":
                settings['region'] = "KR"
                settings['region_name'] = "한국"
                settings['language'] = "ko"
                break
            elif choice == "2":
                settings['region'] = "US"
                settings['region_name'] = "글로벌"
                settings['language'] = "en"
                break
            else:
                print("올바른 번호를 선택해주세요.")
        
        print()
        
        # 키워드 모드인 경우 추가 설정
        if settings['mode'] == "keyword":
            # 키워드 입력
            keyword = input("검색할 키워드를 입력하세요: ").strip()
            if not keyword:
                print("키워드가 입력되지 않았습니다. 분석을 취소합니다.")
                return None
            settings['keyword'] = keyword
            
            # 검색 기간 설정
            print("\\n검색 기간:")
            print("   1) 최근 7일")
            print("   2) 최근 30일")
            print("   3) 최근 90일")
            
            while True:
                choice = input("선택 (1-3): ").strip()
                if choice == "1":
                    settings['period_days'] = 7
                    settings['period_name'] = "최근 7일"
                    break
                elif choice == "2":
                    settings['period_days'] = 30
                    settings['period_name'] = "최근 30일"
                    break
                elif choice == "3":
                    settings['period_days'] = 90
                    settings['period_name'] = "최근 90일"
                    break
                else:
                    print("올바른 번호를 선택해주세요.")
            
            # 최대 구독자 수 설정
            print("\\n최대 구독자 수 필터 (대형 채널 제외):")
            print("   1) 제한 없음")
            print("   2) 100만 이하")
            print("   3) 10만 이하")
            print("   4) 1만 이하")
            print("   5) 직접 입력")
            
            while True:
                choice = input("선택 (1-5): ").strip()
                if choice == "1":
                    settings['max_subscribers'] = None
                    settings['max_subscribers_name'] = "제한 없음"
                    break
                elif choice == "2":
                    settings['max_subscribers'] = 1000000
                    settings['max_subscribers_name'] = "100만 이하"
                    break
                elif choice == "3":
                    settings['max_subscribers'] = 100000
                    settings['max_subscribers_name'] = "10만 이하"
                    break
                elif choice == "4":
                    settings['max_subscribers'] = 10000
                    settings['max_subscribers_name'] = "1만 이하"
                    break
                elif choice == "5":
                    try:
                        custom_count = int(input("최대 구독자 수를 입력하세요: "))
                        if custom_count > 0:
                            settings['max_subscribers'] = custom_count
                            settings['max_subscribers_name'] = f"{custom_count:,} 이하"
                            break
                        else:
                            print("0보다 큰 숫자를 입력해주세요.")
                    except ValueError:
                        print("숫자를 입력해주세요.")
                else:
                    print("올바른 번호를 선택해주세요.")
            
            # 최소 조회수 설정
            print("\\n최소 조회수 필터:")
            print("   1) 제한 없음")
            print("   2) 1,000 이상")
            print("   3) 10,000 이상")
            print("   4) 100,000 이상")
            print("   5) 직접 입력")
            
            while True:
                choice = input("선택 (1-5): ").strip()
                if choice == "1":
                    settings['min_views'] = None
                    settings['min_views_name'] = "제한 없음"
                    break
                elif choice == "2":
                    settings['min_views'] = 1000
                    settings['min_views_name'] = "1,000 이상"
                    break
                elif choice == "3":
                    settings['min_views'] = 10000
                    settings['min_views_name'] = "10,000 이상"
                    break
                elif choice == "4":
                    settings['min_views'] = 100000
                    settings['min_views_name'] = "100,000 이상"
                    break
                elif choice == "5":
                    try:
                        custom_views = int(input("최소 조회수를 입력하세요: "))
                        if custom_views >= 0:
                            settings['min_views'] = custom_views
                            settings['min_views_name'] = f"{custom_views:,} 이상"
                            break
                        else:
                            print("0 이상의 숫자를 입력해주세요.")
                    except ValueError:
                        print("숫자를 입력해주세요.")
                else:
                    print("올바른 번호를 선택해주세요.")
        
        print()
        
        # 2. 영상 유형 선택
        print("2. 영상 유형:")
        print("   1) 전체")
        print("   2) 롱폼만")
        if settings['mode'] == "trending":
            print("   3) 쇼츠만 (⚠️ API 사용량 높음)")
        else:
            print("   3) 쇼츠만")
        
        while True:
            choice = input("선택 (1-3): ").strip()
            if choice == "1":
                settings['video_type'] = "all"
                settings['video_type_name'] = "전체"
                break
            elif choice == "2":
                settings['video_type'] = "long"
                settings['video_type_name'] = "롱폼"
                break
            elif choice == "3":
                settings['video_type'] = "shorts"
                settings['video_type_name'] = "쇼츠"
                if settings['mode'] == "trending":
                    print("ℹ️  쇼츠 분석은 검색 기반으로 진행되어 API 사용량이 많습니다.")
                break
            else:
                print("올바른 번호를 선택해주세요.")
        
        print()
        
        # 3. 카테고리 선택 (트렌딩 모드에서만)
        if settings['mode'] == "trending":
            print("3. 카테고리:")
            print("   1) 전체")
            print("   2) 특정 카테고리")
            
            category_choice = input("선택 (1-2): ").strip()
            
            if category_choice == "1":
                settings['category'] = "all"
                settings['category_name'] = "전체"
            elif category_choice == "2":
                print("\\n사용 가능한 카테고리:")
                categories = [(k, v) for k, v in config.YOUTUBE_CATEGORIES.items() if k != "all"]
                for i, (cat_id, cat_name) in enumerate(categories, 1):
                    print(f"   {i}) {cat_name}")
                
                while True:
                    try:
                        cat_choice = int(input("카테고리 번호 선택: ")) - 1
                        if 0 <= cat_choice < len(categories):
                            settings['category'] = categories[cat_choice][0]
                            settings['category_name'] = categories[cat_choice][1]
                            break
                        else:
                            print("올바른 번호를 선택해주세요.")
                    except ValueError:
                        print("숫자를 입력해주세요.")
            else:
                settings['category'] = "all"
                settings['category_name'] = "전체"
        else:
            settings['category'] = "all"
            settings['category_name'] = "키워드 검색"
        
        print()
        
        # 설정 확인
        print("📋 선택된 설정:")
        print(f"   모드: {settings['mode_name']}")
        if settings['mode'] == "keyword":
            print(f"   키워드: '{settings['keyword']}'")
            print(f"   검색 기간: {settings['period_name']}")
            print(f"   최대 구독자: {settings['max_subscribers_name']}")
            print(f"   최소 조회수: {settings['min_views_name']}")
        print(f"   지역: {settings['region_name']}")
        print(f"   유형: {settings['video_type_name']}")
        print(f"   카테고리: {settings['category_name']}")
        if settings['mode'] == "trending":
            print("   📊 실시간 트렌딩 영상 중 Outlier Score 상위 100개 분석")
        else:
            print("   🔍 키워드 검색 결과를 최신순으로 정렬 후 Outlier Score 분석")
        print()
        
        confirm = input("이 설정으로 분석을 시작하시겠습니까? (y/n): ").strip().lower()
        if confirm not in ['y', 'yes', '예']:
            print("분석이 취소되었습니다.")
            return None
        
        return settings
    
    def initialize_components(self, settings):
        """컴포넌트 초기화"""
        print("🔧 분석 도구를 초기화하는 중...")
        
        # API 클라이언트 초기화
        if not config.DEVELOPER_KEY or config.DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
            print("❌ YouTube API 키가 설정되지 않았습니다!")
            print("config.py 파일에서 DEVELOPER_KEY를 설정해주세요.")
            return False
        
        self.api_client = YouTubeAPIClient(config.DEVELOPER_KEY)
        
        # 데이터 분석기 초기화
        self.analyzer = DataAnalyzer(language=settings['language'])
        
        # 엑셀 생성기 초기화
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"YouTube_Trend_{settings['region']}_{settings['video_type']}_{timestamp}.xlsx"
        self.excel_generator = ExcelGenerator(filename)
        
        print("✅ 초기화 완료!")
        return True
    
    def collect_video_data(self, settings):
        """영상 데이터 수집 (트렌딩 또는 키워드 검색)"""
        
        if settings['mode'] == "keyword":
            # 키워드 검색 모드
            print(f"🔍 '{settings['keyword']}' 키워드 검색 중...")
            
            trending_videos = self.api_client.search_videos_by_keyword(
                keyword=settings['keyword'],
                region_code=settings['region'],
                max_results=200,
                max_subscriber_count=settings.get('max_subscribers'),
                min_view_count=settings.get('min_views'),
                period_days=settings.get('period_days', 30)
            )
        else:
            # 트렌딩 모드
            print(f"🔍 {settings['region_name']} {settings['video_type_name']} 영상 데이터 수집 중...")
            
            if settings['video_type'] == "shorts":
                # 쇼츠 전용 검색
                print("🎬 쇼츠 전용 검색을 사용합니다...")
                trending_videos = self.api_client.get_trending_shorts(
                    region_code=settings['region'],
                    max_results=200
                )
            else:
                # 일반 트렌딩 영상 가져오기
                category_id = settings['category'] if settings['category'] != "all" else None
                trending_videos = self.api_client.get_trending_videos(
                    region_code=settings['region'],
                    category_id=category_id,
                    max_results=200
                )
        
        if not trending_videos:
            if settings['mode'] == "keyword":
                print(f"❌ '{settings['keyword']}' 키워드로 영상을 찾을 수 없습니다.")
                print("💡 해결 방법:")
                print("   1. 다른 키워드를 시도해보세요")
                print("   2. 검색 기간을 늘려보세요")
                print("   3. 구독자/조회수 필터를 완화해보세요")
            elif settings['video_type'] == "shorts":
                print("❌ 쇼츠 영상을 찾을 수 없습니다.")
                print("💡 해결 방법:")
                print("   1. 다른 지역(한국↔글로벌)을 선택해보세요")
                print("   2. 전체 영상 분석 후 쇼츠 필터링을 시도해보세요")
                print("   3. 쇼츠는 검색 기반이므로 결과가 제한적일 수 있습니다")
            else:
                print("❌ 트렌딩 영상을 가져올 수 없습니다.")
            return []
        
        print(f"📊 {len(trending_videos)}개의 영상 데이터를 가져왔습니다.")
        
        # 영상 유형별 필터링 (트렌딩 모드의 롱폼만 해당)
        if settings['mode'] == "trending" and settings['video_type'] == "long":
            trending_videos = self.api_client.filter_videos_by_type(
                trending_videos, 
                settings['video_type']
            )
            print(f"🔧 {settings['video_type_name']} 필터링 후: {len(trending_videos)}개 영상")
        elif settings['mode'] == "keyword" and settings['video_type'] != "all":
            # 키워드 검색에서 영상 유형 필터링
            trending_videos = self.api_client.filter_videos_by_type(
                trending_videos, 
                settings['video_type']
            )
            print(f"🔧 {settings['video_type_name']} 필터링 후: {len(trending_videos)}개 영상")
        
        return trending_videos
    
    def analyze_videos(self, videos, settings):
        """영상 데이터 분석 (Outlier Score 기반)"""
        print("🧠 영상 데이터 분석 중...")
        print("📊 각 채널의 평균 성과 대비 outlier score 계산 중...")
        
        analyzed_videos = []
        total_videos = len(videos)
        
        # 채널별 평균 통계 캐시 (API 절약)
        channel_stats_cache = {}
        
        for i, video in enumerate(videos, 1):
            print(f"   진행률: {i}/{total_videos} ({i/total_videos*100:.1f}%)", end="\\r")
            
            try:
                # 기본 정보 추출
                video_id = video['id']
                snippet = video['snippet']
                statistics = video['statistics']
                content_details = video['contentDetails']
                channel_id = snippet['channelId']
                
                # 영상 길이 파싱
                duration_seconds = self.api_client.parse_duration(content_details['duration'])
                
                # 채널 평균 통계 가져오기 (캐시 활용)
                if channel_id not in channel_stats_cache:
                    channel_stats = self.api_client.get_channel_recent_videos_stats(channel_id)
                    channel_stats_cache[channel_id] = channel_stats
                else:
                    channel_stats = channel_stats_cache[channel_id]
                
                # Outlier Score 계산
                outlier_score = self.analyzer.calculate_outlier_score(statistics, channel_stats)
                outlier_category = self.analyzer.categorize_outlier_score(outlier_score)
                
                # 댓글 가져오기
                comments = self.api_client.get_video_comments(
                    video_id, 
                    max_results=config.COMMENTS_PER_VIDEO
                )
                
                # 썸네일 URL 저장 (다운로드는 나중에 선택적으로)
                thumbnail_url = self.api_client.get_best_thumbnail_url(
                    snippet['thumbnails']
                )
                
                # 분석 수행
                analysis = {
                    'keywords': self.analyzer.extract_keywords_from_title(
                        snippet['title'], 
                        max_keywords=config.KEYWORD_EXTRACTION_COUNT
                    ),
                    'sentiment': self.analyzer.analyze_comments_sentiment(comments),
                    'engagement_score': self.analyzer.calculate_engagement_score(video),
                    'formatted_duration': self.analyzer.format_duration(duration_seconds),
                    'video_type': self.analyzer.determine_video_type(duration_seconds),
                    'views_per_day': self.analyzer.calculate_views_per_day(video),
                    'outlier_score': outlier_score,
                    'outlier_category': outlier_category,
                    'channel_avg_views': channel_stats.get('avg_views', 0) if channel_stats else 0,
                    'thumbnail_url': thumbnail_url  # URL만 저장, 다운로드는 나중에
                }
                
                # 결과 저장
                video['analysis'] = analysis
                video['rank'] = i
                analyzed_videos.append(video)
                
            except Exception as e:
                print(f"\\n❌ 영상 분석 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                continue
        
        print(f"\\n📊 {len(analyzed_videos)}개 영상 분석 완료!")
        
        # Outlier Score 기준으로 정렬하고 상위 100개만 선택
        analyzed_videos.sort(key=lambda x: x['analysis']['outlier_score'], reverse=True)
        top_outliers = analyzed_videos[:config.MAX_RESULTS]
        
        # 순위 재조정
        for i, video in enumerate(top_outliers, 1):
            video['rank'] = i
        
        print(f"🔥 Outlier Score 기준 상위 {len(top_outliers)}개 영상 선별 완료!")
        print(f"   최고 Outlier Score: {top_outliers[0]['analysis']['outlier_score']}x")
        
        return top_outliers
    
    def manage_thumbnails(self, analyzed_videos, settings):
        """썸네일 파일 관리 및 정리"""
        print("🖼️  썸네일 파일 관리 중...")
        
        try:
            import zipfile
            from datetime import datetime
            
            # 썸네일 다운로드 통계
            downloaded_count = 0
            failed_count = 0
            thumbnail_files = []
            
            for video in analyzed_videos:
                thumbnail_path = video.get('analysis', {}).get('thumbnail_path')
                if thumbnail_path and os.path.exists(thumbnail_path):
                    downloaded_count += 1
                    thumbnail_files.append(thumbnail_path)
                else:
                    failed_count += 1
            
            print(f"✅ 썸네일 다운로드 완료: {downloaded_count}개")
            if failed_count > 0:
                print(f"❌ 썸네일 다운로드 실패: {failed_count}개")
            
            # 썸네일 폴더가 존재하고 파일이 있는 경우
            if thumbnail_files:
                # ZIP 파일 생성
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                mode_suffix = f"_{settings['mode']}" if settings['mode'] == "keyword" else ""
                keyword_suffix = f"_{settings.get('keyword', '').replace(' ', '_')}" if settings.get('keyword') else ""
                zip_filename = f"thumbnails_{settings['region']}{mode_suffix}{keyword_suffix}_{timestamp}.zip"
                
                with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                    for thumbnail_path in thumbnail_files:
                        if os.path.exists(thumbnail_path):
                            # ZIP 내에서의 파일명
                            arcname = os.path.basename(thumbnail_path)
                            zipf.write(thumbnail_path, arcname)
                
                print(f"📦 썸네일 ZIP 파일 생성: {zip_filename}")
                print(f"📁 개별 썸네일 파일 위치: thumbnails/ 폴더")
                
                # 썸네일 사용 가이드 출력
                print("\\n🖼️  썸네일 활용 가이드:")
                print(f"   • ZIP 파일: {zip_filename} (모든 썸네일 포함)")
                print("   • 개별 파일: thumbnails/ 폴더에서 확인 가능")
                print("   • 파일명 형식: 순위_제목_영상ID.jpg")
                print("   • 벤치마킹용 썸네일 분석에 활용하세요!")
                
                return zip_filename
            else:
                print("⚠️  다운로드된 썸네일이 없습니다.")
                return None
                
        except Exception as e:
            print(f"❌ 썸네일 관리 오류: {e}")
            return None
    
    def generate_excel_report(self, analyzed_videos, settings):
        """엑셀 리포트 생성"""
        print("📊 엑셀 리포트 생성 중...")
        
        try:
            self.excel_generator.create_excel_file(analyzed_videos, settings)
            filename = self.excel_generator.get_filename()
            
            print(f"✅ 엑셀 리포트가 생성되었습니다: {filename}")
            print(f"📈 총 {len(analyzed_videos)}개 영상의 분석 결과가 포함되었습니다.")
            
            return filename
            
        except Exception as e:
            print(f"❌ 엑셀 리포트 생성 오류: {e}")
            return None
    
    def display_summary(self, analyzed_videos, settings, api_usage):
        """분석 요약 출력"""
        print("\\n" + "=" * 60)
        print("📈 분석 요약")
        print("=" * 60)
        
        total_views = sum(int(v.get('statistics', {}).get('viewCount', 0)) for v in analyzed_videos)
        total_likes = sum(int(v.get('statistics', {}).get('likeCount', 0)) for v in analyzed_videos)
        total_comments = sum(int(v.get('statistics', {}).get('commentCount', 0)) for v in analyzed_videos)
        avg_engagement = sum(v.get('analysis', {}).get('engagement_score', 0) for v in analyzed_videos) / len(analyzed_videos) if analyzed_videos else 0
        avg_outlier_score = sum(v.get('analysis', {}).get('outlier_score', 0) for v in analyzed_videos) / len(analyzed_videos) if analyzed_videos else 0
        
        # Outlier 카테고리별 개수 계산
        outlier_categories = {}
        for video in analyzed_videos:
            category = video.get('analysis', {}).get('outlier_category', '😐 평균')
            outlier_categories[category] = outlier_categories.get(category, 0) + 1
        
        print(f"분석 모드: {settings['mode_name']}")
        if settings['mode'] == "keyword":
            print(f"검색 키워드: '{settings['keyword']}'")
            print(f"검색 기간: {settings['period_name']}")
            print(f"최대 구독자: {settings['max_subscribers_name']}")
            print(f"최소 조회수: {settings['min_views_name']}")
        print(f"분석 지역: {settings['region_name']}")
        print(f"영상 유형: {settings['video_type_name']}")
        print(f"카테고리: {settings['category_name']}")
        print()
        if settings['mode'] == "keyword":
            print(f"검색된 영상 수: {len(analyzed_videos)}개 (최신순 정렬, Outlier Score 상위)")
        else:
            print(f"분석된 영상 수: {len(analyzed_videos)}개 (Outlier Score 상위)")
        print(f"총 조회수: {total_views:,}")
        print(f"총 좋아요: {total_likes:,}")
        print(f"총 댓글: {total_comments:,}")
        print(f"평균 참여도 점수: {avg_engagement:.2f}")
        print(f"평균 Outlier Score: {avg_outlier_score:.2f}x")
        print()
        print("🔥 Outlier 등급별 분포:")
        for category, count in sorted(outlier_categories.items(), key=lambda x: x[1], reverse=True):
            print(f"   {category}: {count}개")
        print()
        print(f"API 사용량: {api_usage} units / {config.API_QUOTA_LIMIT} (일일 한도)")
        
        if api_usage > config.API_QUOTA_LIMIT * 0.8:
            print("⚠️  API 사용량이 80%를 초과했습니다. 내일 다시 실행해주세요.")
        
        # 상위 5개 영상 출력
        if settings['mode'] == "keyword":
            print(f"\\n🏆 '{settings['keyword']}' 상위 5개 Outlier 영상:")
        else:
            print("\\n🏆 상위 5개 Outlier 영상:")
        for i, video in enumerate(analyzed_videos[:5], 1):
            title = video['snippet']['title'][:50] + "..." if len(video['snippet']['title']) > 50 else video['snippet']['title']
            views = int(video['statistics'].get('viewCount', 0))
            outlier_score = video['analysis']['outlier_score']
            outlier_category = video['analysis']['outlier_category']
            channel_name = video['snippet']['channelTitle']
            print(f"   {i}. {title}")
            print(f"      📺 {channel_name} | 📊 {views:,} 조회수 | 🔥 {outlier_score}x | {outlier_category}")
    
    def run(self):
        """메인 실행 함수"""
        try:
            # 환영 메시지
            self.display_welcome()
            
            # 사용자 설정 입력
            settings = self.get_user_settings()
            if not settings:
                return
            
            # 컴포넌트 초기화
            if not self.initialize_components(settings):
                return
            
            # 영상 데이터 수집
            videos = self.collect_video_data(settings)
            if not videos:
                return
            
            # 영상 분석
            analyzed_videos = self.analyze_videos(videos, settings)
            if not analyzed_videos:
                print("❌ 분석할 영상이 없습니다.")
                return
            
            # 엑셀 리포트 생성
            excel_file = self.generate_excel_report(analyzed_videos, settings)
            if not excel_file:
                return
            
            # 분석 요약 출력
            self.display_summary(
                analyzed_videos, 
                settings, 
                self.api_client.get_quota_usage()
            )
            
            print("\\n🎉 분석이 완료되었습니다!")
            print("=" * 60)
            
            # 추가 기능: 채널 분석 및 자막 다운로드
            self.offer_additional_features(analyzed_videos, settings)
            
        except KeyboardInterrupt:
            print("\\n\\n❌ 사용자에 의해 분석이 중단되었습니다.")
        except Exception as e:
            print(f"\\n❌ 예상치 못한 오류가 발생했습니다: {e}")
            print("프로그램을 다시 실행해주세요.")

    def offer_additional_features(self, analyzed_videos, settings):
        """추가 기능 제공 (채널 분석, 자막 다운로드)"""
        print("\\n🔧 추가 기능을 사용하시겠습니까?")
        print("   1) 특정 채널의 다른 영상 대본 다운로드")
        print("   2) 종료")
        
        choice = input("선택 (1-2): ").strip()
        
        if choice == "1":
            self.channel_transcript_analysis(analyzed_videos)
        else:
            print("프로그램을 종료합니다.")
    
    def channel_transcript_analysis(self, analyzed_videos):
        """채널별 자막 분석 기능"""
        try:
            from transcript_downloader import TranscriptDownloader
            
            print("\\n" + "=" * 60)
            print("📺 채널 분석 및 대본 다운로드")
            print("=" * 60)
            
            # 분석된 영상 목록 보여주기
            print("\\n분석된 영상 목록:")
            for i, video in enumerate(analyzed_videos[:20], 1):  # 상위 20개만 표시
                title = video['snippet']['title'][:60] + "..." if len(video['snippet']['title']) > 60 else video['snippet']['title']
                channel = video['snippet']['channelTitle']
                views = int(video['statistics'].get('viewCount', 0))
                outlier_score = video['analysis']['outlier_score']
                print(f"   {i:2d}. {title}")
                print(f"       📺 {channel} | 📊 {views:,} 조회수 | 🔥 {outlier_score}x")
            
            if len(analyzed_videos) > 20:
                print(f"\\n   ... 외 {len(analyzed_videos) - 20}개 영상 더 있음")
            
            # 영상 선택
            print("\\n채널을 분석할 영상의 번호를 입력하세요:")
            try:
                video_choice = int(input("영상 번호: ")) - 1
                if 0 <= video_choice < len(analyzed_videos):
                    selected_video = analyzed_videos[video_choice]
                    self.analyze_channel_videos(selected_video)
                else:
                    print("올바른 번호를 입력해주세요.")
            except ValueError:
                print("숫자를 입력해주세요.")
                
        except ImportError:
            print("❌ 자막 다운로드 기능을 사용하려면 youtube-transcript-api를 설치해주세요.")
            print("pip install youtube-transcript-api")
    
    def analyze_channel_videos(self, selected_video):
        """선택된 영상의 채널 분석"""
        try:
            from transcript_downloader import TranscriptDownloader
            
            channel_id = selected_video['snippet']['channelId']
            channel_name = selected_video['snippet']['channelTitle']
            video_title = selected_video['snippet']['title']
            
            print(f"\\n📺 선택된 채널: {channel_name}")
            print(f"🎬 기준 영상: {video_title}")
            print("\\n해당 채널의 다른 영상들을 가져오는 중...")
            
            # 채널의 다른 영상들 가져오기
            channel_videos = self.api_client.get_channel_videos(
                channel_id, 
                max_results=50, 
                order='date'
            )
            
            if not channel_videos:
                print("❌ 채널 영상을 가져올 수 없습니다.")
                return
            
            print(f"✅ {len(channel_videos)}개의 영상을 발견했습니다.")
            
            # 영상 목록 표시
            print(f"\\n📋 {channel_name}의 최근 영상 목록:")
            print("-" * 80)
            
            for i, video in enumerate(channel_videos, 1):
                title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
                views = video.get('view_count', 0)
                duration = self.api_client.parse_duration(video.get('duration', 'PT0S'))
                duration_str = self.format_duration_simple(duration)
                published = video['published_at'][:10]  # YYYY-MM-DD 형식
                
                print(f"{i:2d}. {title}")
                print(f"    📊 {views:,} 조회수 | ⏰ {duration_str} | 📅 {published}")
            
            # 사용자가 다운로드할 영상 선택
            print("\\n" + "=" * 60)
            print("📝 대본을 다운로드할 영상을 선택하세요")
            print("예: 1,3,5-10,15 (쉼표와 하이픈으로 구분)")
            print("또는 'all'을 입력하면 모든 영상 선택")
            
            selection = input("\\n선택할 영상 번호: ").strip()
            
            if selection.lower() == 'all':
                selected_videos = channel_videos
            else:
                selected_videos = self.parse_video_selection(selection, channel_videos)
            
            if selected_videos:
                print(f"\\n📝 {len(selected_videos)}개 영상의 대본 다운로드를 시작합니다...")
                self.download_selected_transcripts(selected_videos, channel_name)
            else:
                print("선택된 영상이 없습니다.")
                
        except Exception as e:
            print(f"채널 분석 오류: {e}")
    
    def parse_video_selection(self, selection, video_list):
        """사용자 선택 문자열 파싱"""
        selected_videos = []
        
        try:
            parts = selection.split(',')
            
            for part in parts:
                part = part.strip()
                if '-' in part:
                    # 범위 선택 (예: 5-10)
                    start, end = map(int, part.split('-'))
                    for i in range(start, end + 1):
                        if 1 <= i <= len(video_list):
                            selected_videos.append(video_list[i-1])
                else:
                    # 단일 선택 (예: 3)
                    i = int(part)
                    if 1 <= i <= len(video_list):
                        selected_videos.append(video_list[i-1])
            
            # 중복 제거
            seen_ids = set()
            unique_videos = []
            for video in selected_videos:
                if video['id'] not in seen_ids:
                    seen_ids.add(video['id'])
                    unique_videos.append(video)
            
            return unique_videos
            
        except Exception as e:
            print(f"선택 파싱 오류: {e}")
            return []
    
    def download_selected_transcripts(self, selected_videos, channel_name):
        """선택된 영상들의 자막 다운로드"""
        try:
            from transcript_downloader import TranscriptDownloader
            
            downloader = TranscriptDownloader()
            
            # 언어 설정
            print("\\n자막 언어 우선순위를 선택하세요:")
            print("   1) 한국어 우선 (ko → en)")
            print("   2) 영어 우선 (en → ko)")
            print("   3) 한국어만 (ko)")
            print("   4) 영어만 (en)")
            
            lang_choice = input("선택 (1-4): ").strip()
            
            if lang_choice == "1":
                language_codes = ['ko', 'kr', 'en']
            elif lang_choice == "2":
                language_codes = ['en', 'ko', 'kr']
            elif lang_choice == "3":
                language_codes = ['ko', 'kr']
            elif lang_choice == "4":
                language_codes = ['en']
            else:
                language_codes = ['ko', 'kr', 'en']  # 기본값
            
            # 자막 다운로드 실행
            result = downloader.download_multiple_transcripts(selected_videos, language_codes)
            
            # ZIP 파일 생성
            zip_file = downloader.create_transcript_zip(channel_name)
            
            # 결과 요약
            print("\\n" + "=" * 60)
            print("📝 자막 다운로드 완료!")
            print("=" * 60)
            print(f"📺 채널: {channel_name}")
            print(f"📊 요청한 영상: {len(selected_videos)}개")
            print(f"✅ 성공: {result['stats']['success']}개")
            print(f"❌ 실패: {result['stats']['failed']}개")
            print(f"🚫 자막 없음: {result['stats']['no_transcript']}개")
            
            if zip_file:
                print(f"\\n📦 생성된 파일:")
                print(f"   • ZIP 파일: {zip_file}")
                print(f"   • 개별 파일: transcripts/ 폴더")
                print("\\n💡 활용 팁:")
                print("   • 대본을 분석해서 해당 채널의 스크립트 패턴 파악")
                print("   • 성공한 영상들의 스토리텔링 구조 연구")
                print("   • 키워드 사용 빈도 및 화법 스타일 벤치마킹")
            else:
                print("\\n📁 개별 자막 파일들이 transcripts/ 폴더에 저장되었습니다.")
                
        except Exception as e:
            print(f"자막 다운로드 오류: {e}")
    
    def format_duration_simple(self, duration_seconds):
        """
        초 단위 duration을 시:분:초 형태로 변환
        
        Args:
            duration_seconds (int): 초 단위 duration
            
        Returns:
            str: "HH:MM:SS" 또는 "MM:SS" 형태
        """
        if duration_seconds < 3600:  # 1시간 미만
            minutes = duration_seconds // 60
            seconds = duration_seconds % 60
            return f"{minutes:02d}:{seconds:02d}"
        else:  # 1시간 이상
            hours = duration_seconds // 3600
            minutes = (duration_seconds % 3600) // 60
            seconds = duration_seconds % 60
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

def main():
    """메인 함수"""
    # API 키 확인
    if not os.path.exists('config.py'):
        print("❌ config.py 파일이 없습니다!")
        print("먼저 config.py를 생성하고 YouTube API 키를 설정해주세요.")
        return
    
    # 썸네일 폴더 생성
    os.makedirs('thumbnails', exist_ok=True)
    
    # 분석기 실행
    analyzer = YouTubeTrendAnalyzer()
    analyzer.run()

if __name__ == "__main__":
    main()