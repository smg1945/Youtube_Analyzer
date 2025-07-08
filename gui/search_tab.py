"""
검색 탭 모듈
영상 검색 인터페이스 담당
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime

# Core 모듈들
from core import VideoSearcher, YouTubeClient
from data import create_analysis_suite
from exporters import quick_excel_export, quick_thumbnail_download

class SearchTab:
    """영상 검색 탭 클래스"""
    
    def __init__(self, parent, main_window):
        """
        검색 탭 초기화
        
        Args:
            parent: 부모 위젯
            main_window: 메인 창 인스턴스
        """
        self.parent = parent
        self.main_window = main_window
        
        # 분석 상태
        self.is_analyzing = False
        self.current_videos = []
        self.analysis_settings = {}
        
        # YouTube 클라이언트
        self.youtube_client = None
        self.video_searcher = None
        
        # 분석 도구들
        self.analysis_suite = create_analysis_suite(language="ko")
        
        self.create_layout()
        print("✅ 검색 탭 초기화 완료")
    
    def create_layout(self):
        """레이아웃 생성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.parent, bg='#f5f5f7')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 상단: 검색 설정 영역
        self.create_search_settings(main_container)
        
        # 중간: 필터 설정 영역
        self.create_filter_settings(main_container)
        
        # 하단: 버튼 및 진행률 영역
        self.create_action_area(main_container)
    
    def create_search_settings(self, parent):
        """검색 설정 영역"""
        settings_frame = tk.LabelFrame(
            parent,
            text="🔍 검색 설정",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        settings_frame.pack(fill='x', pady=(0, 15))
        
        # 키워드 입력
        keyword_frame = tk.Frame(settings_frame, bg='#f5f5f7')
        keyword_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            keyword_frame,
            text="검색 키워드:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.keyword_entry = tk.Entry(
            keyword_frame,
            font=('SF Pro Display', 11),
            width=30,
            relief='flat',
            bd=5
        )
        self.keyword_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        # 검색 예시 라벨
        example_label = tk.Label(
            keyword_frame,
            text="예: '맛집', '여행', '요리'",
            font=('SF Pro Display', 9),
            bg='#f5f5f7',
            fg='#86868b'
        )
        example_label.pack(side='right', padx=(10, 0))
        
        # 기본 설정 행
        basic_frame = tk.Frame(settings_frame, bg='#f5f5f7')
        basic_frame.pack(fill='x', pady=(0, 10))
        
        # 지역 설정
        tk.Label(
            basic_frame,
            text="지역:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.region_var = tk.StringVar(value="KR")
        region_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.region_var,
            values=["KR", "US", "JP", "GB"],
            state="readonly",
            width=8
        )
        region_combo.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        # 정렬 기준
        tk.Label(
            basic_frame,
            text="정렬:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=2, sticky='w', padx=(0, 10))
        
        self.order_var = tk.StringVar(value="relevance")
        order_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.order_var,
            values=["relevance", "date", "viewCount"],
            state="readonly",
            width=12
        )
        order_combo.grid(row=0, column=3, sticky='w', padx=(0, 20))
        
        # 최대 결과 수
        tk.Label(
            basic_frame,
            text="최대 결과:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=4, sticky='w', padx=(0, 10))
        
        self.max_results_var = tk.StringVar(value="200")
        max_results_combo = ttk.Combobox(
            basic_frame,
            textvariable=self.max_results_var,
            values=["50", "100", "200", "300"],
            state="readonly",
            width=8
        )
        max_results_combo.grid(row=0, column=5, sticky='w')
    
    def create_filter_settings(self, parent):
        """필터 설정 영역"""
        filter_frame = tk.LabelFrame(
            parent,
            text="🔧 필터 설정",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        filter_frame.pack(fill='x', pady=(0, 15))
        
        # 첫 번째 행
        row1_frame = tk.Frame(filter_frame, bg='#f5f5f7')
        row1_frame.pack(fill='x', pady=(0, 10))
        
        # 영상 유형
        tk.Label(
            row1_frame,
            text="영상 유형:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.video_type_var = tk.StringVar(value="all")
        video_type_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.video_type_var,
            values=["all", "shorts", "long"],
            state="readonly",
            width=10
        )
        video_type_combo.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        # 업로드 기간
        tk.Label(
            row1_frame,
            text="업로드 기간:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=2, sticky='w', padx=(0, 10))
        
        self.period_var = tk.StringVar(value="30")
        period_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.period_var,
            values=["1", "3", "7", "30", "90"],
            state="readonly",
            width=8
        )
        period_combo.grid(row=0, column=3, sticky='w')
        
        tk.Label(
            row1_frame,
            text="일",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=4, sticky='w', padx=(5, 0))
        
        # 두 번째 행
        row2_frame = tk.Frame(filter_frame, bg='#f5f5f7')
        row2_frame.pack(fill='x')
        
        # 최소 조회수
        tk.Label(
            row2_frame,
            text="최소 조회수:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.min_views_var = tk.StringVar(value="0")
        min_views_combo = ttk.Combobox(
            row2_frame,
            textvariable=self.min_views_var,
            values=["0", "1000", "10000", "50000", "100000"],
            state="readonly",
            width=12
        )
        min_views_combo.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        # 최대 구독자
        tk.Label(
            row2_frame,
            text="최대 구독자:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=2, sticky='w', padx=(0, 10))
        
        self.max_subscribers_var = tk.StringVar(value="1000000")
        max_subs_combo = ttk.Combobox(
            row2_frame,
            textvariable=self.max_subscribers_var,
            values=["10000", "100000", "1000000", "무제한"],
            state="readonly",
            width=12
        )
        max_subs_combo.grid(row=0, column=3, sticky='w')
    
    def create_action_area(self, parent):
        """액션 영역 (버튼, 진행률)"""
        action_frame = tk.Frame(parent, bg='#f5f5f7')
        action_frame.pack(fill='x')
        
        # 버튼 영역
        button_frame = tk.Frame(action_frame, bg='#f5f5f7')
        button_frame.pack(side='left')
        
        # 검색 버튼
        self.search_button = tk.Button(
            button_frame,
            text="🔍 검색 시작",
            font=('SF Pro Display', 12, 'bold'),
            bg='#007aff',
            fg='white',
            width=15,
            height=2,
            borderwidth=0,
            cursor='hand2',
            command=self.start_search
        )
        self.search_button.pack(side='left', padx=(0, 10))
        
        # 중지 버튼
        self.stop_button = tk.Button(
            button_frame,
            text="⏹ 중지",
            font=('SF Pro Display', 12),
            bg='#ff3b30',
            fg='white',
            width=10,
            height=2,
            borderwidth=0,
            cursor='hand2',
            command=self.stop_search,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=(0, 10))
        
        # 내보내기 버튼들
        export_frame = tk.Frame(button_frame, bg='#f5f5f7')
        export_frame.pack(side='left', padx=(20, 0))
        
        self.excel_button = tk.Button(
            export_frame,
            text="📊 엑셀 내보내기",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            width=15,
            borderwidth=0,
            cursor='hand2',
            command=self.export_excel,
            state='disabled'
        )
        self.excel_button.pack(side='top', pady=(0, 5))
        
        self.thumbnail_button = tk.Button(
            export_frame,
            text="🖼️ 썸네일 다운로드",
            font=('SF Pro Display', 11),
            bg='#ff9500',
            fg='white',
            width=15,
            borderwidth=0,
            cursor='hand2',
            command=self.download_thumbnails,
            state='disabled'
        )
        self.thumbnail_button.pack(side='top')
        
        # 진행률 영역
        progress_frame = tk.Frame(action_frame, bg='#f5f5f7')
        progress_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=300
        )
        self.progress_bar.pack(side='top', fill='x', pady=(10, 5))
        
        # 진행률 텍스트
        self.progress_label = tk.Label(
            progress_frame,
            text="대기 중...",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.progress_label.pack(side='bottom')
    
    def start_search(self):
        """검색 시작"""
        # 입력값 검증
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("입력 오류", "검색 키워드를 입력해주세요.")
            return
        
        if self.is_analyzing:
            messagebox.showwarning("진행 중", "이미 분석이 진행 중입니다.")
            return
        
        # API 키 확인
        api_key = self.main_window.get_api_key()
        if not api_key:
            messagebox.showwarning("API 키 필요", "검색을 위해 API 키가 필요합니다.")
            self.main_window.setup_api_key_dialog()
            return
        
        # UI 상태 변경
        self.set_analyzing_state(True)
        
        # 검색 설정 구성
        search_settings = self.get_search_settings()
        
        # 백그라운드에서 검색 실행
        def search_thread():
            try:
                self.perform_search(api_key, keyword, search_settings)
            except Exception as e:
                self.main_window.root.after(0, lambda: self.handle_search_error(e))
            finally:
                self.main_window.root.after(0, lambda: self.set_analyzing_state(False))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def get_search_settings(self):
        """검색 설정 가져오기"""
        max_subscribers = self.max_subscribers_var.get()
        if max_subscribers == "무제한":
            max_subscribers = None
        else:
            max_subscribers = int(max_subscribers)
        
        return {
            'region_code': self.region_var.get(),
            'order': self.order_var.get(),
            'max_results': int(self.max_results_var.get()),
            'video_type': self.video_type_var.get(),
            'period_days': int(self.period_var.get()),
            'min_view_count': int(self.min_views_var.get()) if self.min_views_var.get() != "0" else None,
            'max_subscriber_count': max_subscribers
        }
    
    def perform_search(self, api_key, keyword, settings):
        """실제 검색 수행"""
        self.update_progress(10, "YouTube API 연결 중...")
        
        # YouTube 클라이언트 초기화
        self.youtube_client = YouTubeClient(api_key)
        self.video_searcher = VideoSearcher(self.youtube_client)
        
        # API 연결 테스트
        if not self.youtube_client.test_connection():
            raise Exception("YouTube API 연결에 실패했습니다.")
        
        self.update_progress(20, "영상 검색 중...")
        
        # 영상 검색
        videos = self.video_searcher.search_with_filters(keyword, settings)
        
        if not videos:
            raise Exception("검색 결과가 없습니다. 다른 키워드나 필터를 시도해보세요.")
        
        self.update_progress(50, f"{len(videos)}개 영상 분석 중...")
        
        # 영상 분석
        analyzed_videos = self.analyze_videos(videos, settings)
        
        self.update_progress(90, "결과 정리 중...")
        
        # 분석 설정 저장
        self.analysis_settings = {
            'keyword': keyword,
            'mode': 'keyword_search',
            'mode_name': f"키워드 검색: '{keyword}'",
            'region_name': self.get_region_name(settings['region_code']),
            'video_type_name': self.get_video_type_name(settings['video_type']),
            'period_days': settings['period_days'],
            'min_views_name': self.format_number(settings.get('min_view_count', 0)),
            'max_subscribers_name': self.format_number(settings.get('max_subscriber_count', 0)) if settings.get('max_subscriber_count') else "무제한",
            'total_found': len(analyzed_videos),
            'search_timestamp': datetime.now().isoformat()
        }
        
        # 결과 저장
        self.current_videos = analyzed_videos
        
        self.update_progress(100, f"완료! {len(analyzed_videos)}개 영상 분석 완료")
        
        # UI 업데이트 (메인 스레드에서)
        self.main_window.root.after(0, self.on_search_complete)
    
    def analyze_videos(self, videos, settings):
        """영상 분석"""
        analyzed_videos = []
        total_videos = len(videos)
        
        for i, video in enumerate(videos):
            if not self.is_analyzing:  # 중지 요청 확인
                break
            
            try:
                # 기본 분석
                analysis = self.analyze_single_video(video, i + 1)
                video['analysis'] = analysis
                analyzed_videos.append(video)
                
                # 진행률 업데이트
                progress = 50 + (i / total_videos) * 40
                self.update_progress(progress, f"분석 중... ({i+1}/{total_videos})")
                
            except Exception as e:
                print(f"영상 분석 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                continue
        
        return analyzed_videos
    
    def analyze_single_video(self, video, rank):
        """단일 영상 분석"""
        analysis = {
            'rank': rank,
            'keywords': [],
            'outlier_score': 1.0,
            'outlier_category': '😐 평균',
            'engagement_score': 0.0,
            'like_rate': 0.0,
            'comment_rate': 0.0,
            'views_per_day': 0.0,
            'growth_velocity': {'velocity_rating': '알수없음'},
            'video_type': '알수없음',
            'duration_seconds': 0,
            'formatted_duration': '00:00',
            'channel_avg_views': 0
        }
        
        try:
            # 참여도 계산
            calc = self.analysis_suite['engagement_calculator']
            analysis['engagement_score'] = calc.calculate_engagement_score(video)
            analysis['like_rate'] = calc.calculate_like_rate(video)
            analysis['comment_rate'] = calc.calculate_comment_rate(video)
            analysis['views_per_day'] = calc.calculate_views_per_day(video)
            analysis['growth_velocity'] = calc.calculate_growth_velocity(video)
            
            # 키워드 추출
            text_analyzer = self.analysis_suite['text_analyzer']
            title = video['snippet']['title']
            analysis['keywords'] = text_analyzer.extract_keywords_from_title(title, max_keywords=5)
            
            # 영상 길이 분석
            duration_str = video['contentDetails']['duration']
            duration_seconds = self.parse_duration(duration_str)
            analysis['duration_seconds'] = duration_seconds
            analysis['formatted_duration'] = self.format_duration(duration_seconds)
            
            # 영상 유형 결정
            if duration_seconds <= 60:
                analysis['video_type'] = '쇼츠'
            else:
                analysis['video_type'] = '롱폼'
            
            # Outlier Score 계산 (간단 버전)
            # TODO: 채널 평균과 비교하여 정확한 계산
            current_views = int(video['statistics'].get('viewCount', 0))
            estimated_avg = 50000  # 임시 평균값
            analysis['outlier_score'] = max(0.1, current_views / estimated_avg)
            analysis['outlier_category'] = calc.categorize_outlier_score(analysis['outlier_score'])
            analysis['channel_avg_views'] = estimated_avg
            
        except Exception as e:
            print(f"영상 분석 세부 오류: {e}")
        
        return analysis
    
    def parse_duration(self, duration_str):
        """YouTube duration 파싱"""
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        
        if not match:
            return 0
        
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        
        return hours * 3600 + minutes * 60 + seconds
    
    def format_duration(self, seconds):
        """초를 시:분:초 형식으로 변환"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def on_search_complete(self):
        """검색 완료 후 처리"""
        # 내보내기 버튼 활성화
        self.excel_button.config(state='normal')
        self.thumbnail_button.config(state='normal')
        
        # 할당량 업데이트
        if self.youtube_client:
            quota_used = self.youtube_client.get_quota_usage()
            self.main_window.update_quota(quota_used, 10000)
        
        # 결과를 메인 창의 결과 탭에 표시
        self.main_window.show_search_results(self.current_videos, self.analysis_settings)
        
        # 완료 메시지
        self.main_window.show_info(
            "검색 완료",
            f"{len(self.current_videos)}개 영상 분석이 완료되었습니다.\n\n"
            f"결과 탭에서 자세한 내용을 확인하세요."
        )
    
    def stop_search(self):
        """검색 중지"""
        self.is_analyzing = False
        self.update_progress(0, "중지됨")
        self.main_window.update_status("검색이 중지되었습니다.")
    
def export_excel(self):
    """엑셀 내보내기"""
    if not self.current_videos:
        messagebox.showwarning("데이터 없음", "내보낼 데이터가 없습니다.")
        return
    
    try:
        from exporters import ExcelExporter
        from tkinter import filedialog
        from datetime import datetime
        
        # 저장 위치 선택
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"youtube_analysis_{timestamp}.xlsx"
        
        file_path = filedialog.asksaveasfilename(
            title="엑셀 파일 저장",
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            initialname=default_filename
        )
        
        if not file_path:
            return
        
        # 엑셀 내보내기
        exporter = ExcelExporter()
        result = exporter.export_analysis_results(
            self.current_videos,
            self.analysis_settings,
            file_path
        )
        
        if result.get('success'):
            messagebox.showinfo(
                "내보내기 완료",
                f"엑셀 파일이 저장되었습니다.\n\n"
                f"파일: {file_path}\n"
                f"영상 수: {len(self.current_videos)}개"
            )
            self.main_window.update_status("엑셀 내보내기 완료")
        else:
            raise Exception(result.get('error', '알 수 없는 오류'))
            
    except Exception as e:
        messagebox.showerror("내보내기 실패", f"엑셀 내보내기 중 오류가 발생했습니다:\n{str(e)}")

def export_thumbnails(self):
    """썸네일 다운로드"""
    if not self.current_videos:
        messagebox.showwarning("데이터 없음", "다운로드할 데이터가 없습니다.")
        return
    
    try:
        from exporters import ThumbnailDownloader
        from tkinter import filedialog
        import os
        
        # 다운로드 폴더 선택
        download_dir = filedialog.askdirectory(
            title="썸네일 다운로드 폴더 선택"
        )
        
        if not download_dir:
            return
        
        # 썸네일 다운로드
        downloader = ThumbnailDownloader(download_dir)
        
        # 진행률 다이얼로그 표시
        from gui.dialogs.progress_dialog import ProgressDialog
        
        steps = ["썸네일 URL 추출", "이미지 다운로드", "파일 정리"]
        progress_dialog = ProgressDialog(
            self.main_window.root,
            title="썸네일 다운로드",
            steps=steps
        )
        
        def download_thumbnails():
            try:
                progress_dialog.next_step("썸네일 URL 추출")
                
                # 영상 데이터에서 썸네일 URL 추출
                video_list = []
                for video in self.current_videos:
                    video_info = {
                        'id': video['id'],
                        'title': video['snippet']['title'],
                        'channel': video['snippet']['channelTitle'],
                        'thumbnail_url': video['snippet'].get('thumbnails', {}).get('medium', {}).get('url', ''),
                        'outlier_score': video.get('analysis', {}).get('outlier_score', 0)
                    }
                    video_list.append(video_info)
                
                progress_dialog.update_step_progress(100)
                progress_dialog.next_step("이미지 다운로드")
                
                # 다운로드 실행
                result = downloader.download_video_thumbnails(
                    video_list,
                    resize=(320, 180),
                    create_zip=True
                )
                
                progress_dialog.update_step_progress(100)
                progress_dialog.next_step("파일 정리")
                
                # ZIP 파일 생성 (옵션)
                if result.get('success') and result.get('downloaded_files'):
                    zip_result = downloader._create_zip_file(result['downloaded_files'])
                    if zip_result.get('success'):
                        result['zip_file'] = zip_result['zip_path']
                
                progress_dialog.complete_all("썸네일 다운로드 완료!")
                
                # 결과 메시지
                self.main_window.root.after(1000, lambda: self.show_download_result(result, download_dir))
                
            except Exception as e:
                progress_dialog.abort_with_error(str(e))
                self.main_window.root.after(1000, lambda: messagebox.showerror("다운로드 실패", str(e)))
        
        # 백그라운드에서 다운로드 실행
        import threading
        download_thread = threading.Thread(target=download_thumbnails, daemon=True)
        download_thread.start()
        
        progress_dialog.show()
        
    except Exception as e:
        messagebox.showerror("다운로드 실패", f"썸네일 다운로드 중 오류가 발생했습니다:\n{str(e)}")

def show_download_result(self, result, download_dir):
    """다운로드 결과 표시"""
    if result.get('success'):
        downloaded_count = result.get('successful_downloads', 0)
        failed_count = result.get('failed_downloads', 0)
        zip_file = result.get('zip_file', '')
        
        message = f"썸네일 다운로드 완료!\n\n"
        message += f"성공: {downloaded_count}개\n"
        message += f"실패: {failed_count}개\n"
        message += f"저장 위치: {download_dir}\n"
        
        if zip_file:
            message += f"\n📦 ZIP 파일: {os.path.basename(zip_file)}"
        
        # 폴더 열기 옵션
        result_choice = messagebox.askyesno(
            "다운로드 완료",
            message + "\n\n폴더를 열까요?"
        )
        
        if result_choice:
            import subprocess
            import platform
            
            try:
                if platform.system() == "Windows":
                    subprocess.run(["explorer", download_dir])
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", download_dir])
                else:  # Linux
                    subprocess.run(["xdg-open", download_dir])
            except Exception as e:
                print(f"폴더 열기 실패: {e}")
        
        self.main_window.update_status(f"썸네일 {downloaded_count}개 다운로드 완료")
    else:
        messagebox.showerror("다운로드 실패", result.get('error', '알 수 없는 오류'))

def get_region_name(self, region_code):
    """지역 코드를 이름으로 변환"""
    region_names = {
        'KR': '한국',
        'US': '미국',
        'JP': '일본',
        'GB': '영국',
        'DE': '독일',
        'FR': '프랑스'
    }
    return region_names.get(region_code, region_code)

def get_video_type_name(self, video_type):
    """영상 유형 코드를 이름으로 변환"""
    type_names = {
        'all': '전체',
        'shorts': '쇼츠 (60초 이하)',
        'long': '롱폼 (10분 이상)',
        'medium': '일반 (1-10분)'
    }
    return type_names.get(video_type, video_type)

def format_number(self, number):
    """숫자를 천 단위 구분자로 포맷"""
    if number == 0:
        return "0"
    
    if number >= 1000000:
        return f"{number/1000000:.1f}M"
    elif number >= 1000:
        return f"{number/1000:.1f}K"
    else:
        return str(number)

def create_action_area_complete(self, parent):
    """완성된 액션 영역"""
    action_frame = tk.Frame(parent, bg='#f5f5f7')
    action_frame.pack(fill='x')
    
    # 버튼 영역
    button_frame = tk.Frame(action_frame, bg='#f5f5f7')
    button_frame.pack(side='left')
    
    # 검색 버튼
    self.search_button = tk.Button(
        button_frame,
        text="🔍 검색 시작",
        font=('SF Pro Display', 12, 'bold'),
        bg='#007aff',
        fg='white',
        width=15,
        height=2,
        borderwidth=0,
        cursor='hand2',
        command=self.start_search
    )
    self.search_button.pack(side='left', padx=(0, 10))
    
    # 중지 버튼
    self.stop_button = tk.Button(
        button_frame,
        text="⏹ 중지",
        font=('SF Pro Display', 12),
        bg='#ff3b30',
        fg='white',
        width=12,
        height=2,
        borderwidth=0,
        cursor='hand2',
        command=self.stop_search,
        state='disabled'
    )
    self.stop_button.pack(side='left', padx=(0, 10))
    
    # 내보내기 버튼들
    export_frame = tk.Frame(button_frame, bg='#f5f5f7')
    export_frame.pack(side='left', padx=(20, 0))
    
    # 엑셀 내보내기 버튼
    self.excel_button = tk.Button(
        export_frame,
        text="📊 엑셀 내보내기",
        font=('SF Pro Display', 11),
        bg='#34c759',
        fg='white',
        width=15,
        borderwidth=0,
        cursor='hand2',
        command=self.export_excel,
        state='disabled'
    )
    self.excel_button.pack(side='left', padx=(0, 5))
    
    # 썸네일 다운로드 버튼
    self.thumbnail_button = tk.Button(
        export_frame,
        text="🖼 썸네일 다운로드",
        font=('SF Pro Display', 11),
        bg='#ff9500',
        fg='white',
        width=15,
        borderwidth=0,
        cursor='hand2',
        command=self.export_thumbnails,
        state='disabled'
    )
    self.thumbnail_button.pack(side='left')
    
    # 진행률 영역
    progress_frame = tk.Frame(action_frame, bg='#f5f5f7')
    progress_frame.pack(side='right', fill='x', expand=True, padx=(20, 0))
    
    # 진행률 라벨
    self.progress_label = tk.Label(
        progress_frame,
        text="대기 중...",
        font=('SF Pro Display', 10),
        bg='#f5f5f7',
        fg='#86868b'
    )
    self.progress_label.pack(anchor='e', pady=(0, 5))
    
    # 진행률 바
    self.progress_var = tk.DoubleVar()
    self.progress_bar = ttk.Progressbar(
        progress_frame,
        variable=self.progress_var,
        maximum=100,
        length=300,
        mode='determinate'
    )
    self.progress_bar.pack(anchor='e')

def validate_search_inputs(self):
    """검색 입력값 유효성 검사"""
    keyword = self.keyword_entry.get().strip()
    
    if not keyword:
        messagebox.showerror("입력 오류", "검색 키워드를 입력해주세요.")
        self.keyword_entry.focus()
        return False
    
    if len(keyword) < 2:
        messagebox.showerror("입력 오류", "키워드는 2자 이상 입력해주세요.")
        self.keyword_entry.focus()
        return False
    
    if len(keyword) > 100:
        messagebox.showerror("입력 오류", "키워드는 100자를 초과할 수 없습니다.")
        self.keyword_entry.focus()
        return False
    
    return True

def reset_ui_state(self):
    """UI 상태 초기화"""
    # 버튼 상태
    self.search_button.config(state='normal', text="🔍 검색 시작")
    self.stop_button.config(state='disabled')
    self.excel_button.config(state='disabled')
    self.thumbnail_button.config(state='disabled')
    
    # 진행률 초기화
    self.progress_var.set(0)
    self.progress_label.config(text="대기 중...")
    
    # 검색 플래그
    self.is_analyzing = False

def update_progress(self, value, message=""):
    """진행률 업데이트"""
    self.progress_var.set(value)
    if message:
        self.progress_label.config(text=message)
    
    # UI 업데이트 강제 적용
    self.main_window.root.update_idletasks()
    
    print(f"📊 진행률: {value:.1f}% - {message}")

def enable_search_ui(self):
    """검색 UI 활성화"""
    self.search_button.config(state='normal', text="🔍 검색 시작")
    self.stop_button.config(state='disabled')
    
def disable_search_ui(self):
    """검색 UI 비활성화 (검색 중)"""
    self.search_button.config(state='disabled', text="검색 중...")
    self.stop_button.config(state='normal')