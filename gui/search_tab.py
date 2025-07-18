"""
검색 탭 모듈
영상 검색 인터페이스 담당
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
from datetime import datetime
import re

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
        
        self.keyword_var = tk.StringVar()
        self.keyword_entry = tk.Entry(
            keyword_frame,
            textvariable=self.keyword_var,
            font=('SF Pro Display', 11),
            width=30
        )
        self.keyword_entry.pack(side='left', padx=(10, 0), fill='x', expand=True)
        
        # 검색 옵션들
        options_frame = tk.Frame(settings_frame, bg='#f5f5f7')
        options_frame.pack(fill='x', pady=(10, 0))
        
        # 지역 설정
        region_frame = tk.Frame(options_frame, bg='#f5f5f7')
        region_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(
            region_frame,
            text="지역:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.region_var = tk.StringVar(value="KR")
        region_combo = ttk.Combobox(
            region_frame,
            textvariable=self.region_var,
            values=["KR", "US"],
            state="readonly",
            width=8
        )
        region_combo.pack(side='left', padx=(5, 0))
        
        # 정렬 기준
        order_frame = tk.Frame(options_frame, bg='#f5f5f7')
        order_frame.pack(side='left', padx=(0, 20))
        
        tk.Label(
            order_frame,
            text="정렬:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.order_var = tk.StringVar(value="relevance")
        order_combo = ttk.Combobox(
            order_frame,
            textvariable=self.order_var,
            values=["relevance", "date", "viewCount"],
            state="readonly",
            width=12
        )
        order_combo.pack(side='left', padx=(5, 0))
        
        # 검색 기간
        period_frame = tk.Frame(options_frame, bg='#f5f5f7')
        period_frame.pack(side='left')
        
        tk.Label(
            period_frame,
            text="기간(일):",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.period_var = tk.StringVar(value="30")
        period_entry = tk.Entry(
            period_frame,
            textvariable=self.period_var,
            font=('SF Pro Display', 11),
            width=8
        )
        period_entry.pack(side='left', padx=(5, 0))
    
    def create_filter_settings(self, parent):
        """필터 설정 영역 - 자릿수 구분 기능 추가"""
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
        
        # 첫 번째 행: 조회수 및 구독자 수 필터
        row1_frame = tk.Frame(filter_frame, bg='#f5f5f7')
        row1_frame.pack(fill='x', pady=(0, 10))
        
        # 조회수 필터 (자릿수 구분 적용)
        views_frame = tk.Frame(row1_frame, bg='#f5f5f7')
        views_frame.pack(side='left', padx=(0, 30))
        
        tk.Label(
            views_frame,
            text="최소 조회수:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.min_views_var = tk.StringVar()
        self.min_views_entry = tk.Entry(
            views_frame,
            textvariable=self.min_views_var,
            font=('SF Pro Display', 11),
            width=15
        )
        self.min_views_entry.pack(side='left', padx=(10, 5))
        
        # 자릿수 구분 실시간 적용
        self.min_views_var.trace('w', self.format_number_input)
        
        # 구독자 수 필터 (자릿수 구분 적용)
        subs_frame = tk.Frame(row1_frame, bg='#f5f5f7')
        subs_frame.pack(side='left')
        
        tk.Label(
            subs_frame,
            text="최대 구독자 수:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.max_subs_var = tk.StringVar()
        self.max_subs_entry = tk.Entry(
            subs_frame,
            textvariable=self.max_subs_var,
            font=('SF Pro Display', 11),
            width=15
        )
        self.max_subs_entry.pack(side='left', padx=(10, 5))
        
        # 자릿수 구분 실시간 적용
        self.max_subs_var.trace('w', self.format_number_input)
        
        # 두 번째 행: 기타 필터들
        row2_frame = tk.Frame(filter_frame, bg='#f5f5f7')
        row2_frame.pack(fill='x')
        
        # 영상 유형 필터
        type_frame = tk.Frame(row2_frame, bg='#f5f5f7')
        type_frame.pack(side='left', padx=(0, 30))
        
        tk.Label(
            type_frame,
            text="영상 유형:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.video_type_var = tk.StringVar(value="all")
        type_combo = ttk.Combobox(
            type_frame,
            textvariable=self.video_type_var,
            values=["all", "shorts", "long"],
            state="readonly",
            width=12
        )
        type_combo.pack(side='left', padx=(10, 0))
        
        # 최대 결과 수
        results_frame = tk.Frame(row2_frame, bg='#f5f5f7')
        results_frame.pack(side='left')
        
        tk.Label(
            results_frame,
            text="최대 결과:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.max_results_var = tk.StringVar(value="200")
        results_entry = tk.Entry(
            results_frame,
            textvariable=self.max_results_var,
            font=('SF Pro Display', 11),
            width=8
        )
        results_entry.pack(side='left', padx=(10, 0))

    def format_number_input(self, *args):
        """숫자 입력 시 자릿수 구분 적용"""
        try:
            # 현재 포커스된 위젯 확인
            focused_widget = self.parent.focus_get()
            
            for entry, var in [(self.min_views_entry, self.min_views_var), 
                               (self.max_subs_entry, self.max_subs_var)]:
                if focused_widget == entry:
                    try:
                        cursor_pos = entry.index(tk.INSERT)
                        
                        # 숫자만 추출
                        numbers_only = re.sub(r'[^\d]', '', var.get())
                        
                        if numbers_only:
                            # 자릿수 구분 적용
                            formatted = "{:,}".format(int(numbers_only))
                            
                            # 변경사항 추적 비활성화
                            var.trace_vdelete('w', var.trace_vinfo()[0][1])
                            var.set(formatted)
                            
                            # 커서 위치 복원
                            try:
                                entry.icursor(min(cursor_pos, len(formatted)))
                            except:
                                pass
                            
                            # 변경사항 추적 재활성화
                            var.trace('w', self.format_number_input)
                            
                    except Exception as e:
                        print(f"숫자 포맷팅 오류: {e}")
                        
        except Exception as e:
            print(f"전체 포맷팅 오류: {e}")
    
    def create_action_area(self, parent):
        """액션 및 진행률 영역"""
        action_frame = tk.Frame(parent, bg='#f5f5f7')
        action_frame.pack(fill='x')
        
        # 버튼들
        button_frame = tk.Frame(action_frame, bg='#f5f5f7')
        button_frame.pack(fill='x', pady=(0, 15))
        
        # 검색 시작 버튼
        self.search_btn = tk.Button(
            button_frame,
            text="🔍 검색 시작",
            font=('SF Pro Display', 12, 'bold'),
            bg='#007aff',
            fg='white',
            relief='flat',
            padx=30,
            pady=12,
            command=self.start_search
        )
        self.search_btn.pack(side='left', padx=(0, 10))
        
        # 중지 버튼
        self.stop_btn = tk.Button(
            button_frame,
            text="⏹️ 중지",
            font=('SF Pro Display', 12),
            bg='#ff3b30',
            fg='white',
            relief='flat',
            padx=20,
            pady=12,
            command=self.stop_search,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        # 진행률 표시
        progress_frame = tk.Frame(action_frame, bg='#f5f5f7')
        progress_frame.pack(fill='x', pady=(0, 10))
        
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            progress_frame,
            variable=self.progress_var,
            maximum=100
        )
        self.progress_bar.pack(fill='x', pady=(0, 5))
        
        self.progress_label = tk.Label(
            progress_frame,
            text="준비 완료",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.progress_label.pack()
    
    def get_filter_values(self):
        """필터 값들을 숫자로 변환하여 반환"""
        try:
            # 쉼표 제거 후 숫자 변환
            min_views = None
            if self.min_views_var.get().strip():
                min_views = int(self.min_views_var.get().replace(',', ''))
                
            max_subs = None
            if self.max_subs_var.get().strip():
                max_subs = int(self.max_subs_var.get().replace(',', ''))
                
            period_days = int(self.period_var.get()) if self.period_var.get() else 30
            max_results = int(self.max_results_var.get()) if self.max_results_var.get() else 200
                
            return {
                'keyword': self.keyword_var.get().strip(),
                'region_code': self.region_var.get(),
                'order': self.order_var.get(),
                'period_days': period_days,
                'min_view_count': min_views,
                'max_subscriber_count': max_subs,
                'video_type': self.video_type_var.get(),
                'max_results': max_results
            }
        except ValueError as e:
            messagebox.showerror("입력 오류", "숫자 형식이 올바르지 않습니다.")
            return {}
    
    def start_search(self):
        """검색 시작"""
        if self.is_analyzing:
            return
        
        # 입력 검증
        filters = self.get_filter_values()
        if not filters or not filters['keyword']:
            messagebox.showwarning("입력 오류", "검색 키워드를 입력해주세요.")
            return
        
        # UI 상태 변경
        self.is_analyzing = True
        self.search_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.update_progress(0, "검색 준비 중...")
        
        # 백그라운드에서 검색 실행
        search_thread = threading.Thread(
            target=self.execute_search,
            args=(filters,),
            daemon=True
        )
        search_thread.start()
    
    def execute_search(self, filters):
        """실제 검색 실행"""
        try:
            # YouTube 클라이언트 초기화
            api_key = self.main_window.get_api_key()
            if not api_key:
                self.handle_search_error("API 키가 설정되지 않았습니다.")
                return
            
            self.youtube_client = YouTubeClient(api_key)
            self.video_searcher = VideoSearcher(self.youtube_client)
            
            self.update_progress(10, "영상 검색 중...")
            
            # 영상 검색
            videos = self.video_searcher.search_with_filters(filters['keyword'], filters)
            
            if not videos:
                self.handle_search_error("검색 결과가 없습니다.")
                return
            
            self.update_progress(50, f"{len(videos)}개 영상 분석 중...")
            
            # 분석 수행
            analyzed_videos = []
            for i, video in enumerate(videos):
                if not self.is_analyzing:  # 중지 체크
                    break
                
                # 간단한 분석 수행
                analysis = self.analyze_single_video(video, i + 1)
                video['analysis'] = analysis
                analyzed_videos.append(video)
                
                # 진행률 업데이트
                progress = 50 + (i / len(videos)) * 40
                self.update_progress(progress, f"분석 중... ({i+1}/{len(videos)})")
            
            if self.is_analyzing:
                self.current_videos = analyzed_videos
                self.analysis_settings = filters
                
                self.update_progress(100, f"완료! {len(analyzed_videos)}개 영상 분석됨")
                
                # 결과 표시
                self.show_results_in_viewer(analyzed_videos, filters)
            
        except Exception as e:
            self.handle_search_error(str(e))
        finally:
            # UI 상태 복원
            self.is_analyzing = False
            self.search_btn.config(state='normal')
            self.stop_btn.config(state='disabled')
    
    def analyze_single_video(self, video, rank):
        """개별 영상 분석"""
        try:
            snippet = video['snippet']
            statistics = video['statistics']
            
            # 기본 정보 추출
            title = snippet.get('title', '')
            views = int(statistics.get('viewCount', 0))
            likes = int(statistics.get('likeCount', 0))
            comments = int(statistics.get('commentCount', 0))
            
            # 간단한 키워드 추출
            keywords = []
            if title:
                # 특수문자 제거 후 단어 분리
                clean_title = re.sub(r'[^\w\s가-힣]', ' ', title)
                words = [word for word in clean_title.split() if len(word) >= 2]
                keywords = words[:5]  # 상위 5개 단어
            
            # 참여도 계산
            engagement_rate = 0
            if views > 0:
                engagement_rate = ((likes + comments) / views) * 100
            
            # 아웃라이어 점수 (간단한 계산)
            outlier_score = min(engagement_rate * 10, 100)
            
            # 영상 유형 판별
            duration = video.get('parsed_duration', '00:00')
            video_type = '쇼츠' if ':' in duration and int(duration.split(':')[0]) == 0 and int(duration.split(':')[1]) <= 1 else '롱폼'
            
            return {
                'rank': rank,
                'keywords': keywords,
                'engagement_rate': engagement_rate,
                'outlier_score': outlier_score,
                'video_type': video_type
            }
            
        except Exception as e:
            print(f"영상 분석 오류: {e}")
            return {
                'rank': rank,
                'keywords': [],
                'engagement_rate': 0,
                'outlier_score': 0,
                'video_type': '일반'
            }
    
    def update_progress(self, value, text):
        """진행률 업데이트"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.parent.update_idletasks()
    
    def stop_search(self):
        """검색 중지"""
        self.is_analyzing = False
        self.update_progress(0, "중지됨")
        print("🛑 사용자에 의해 검색이 중지되었습니다.")

    def handle_search_error(self, error):
        """검색 오류 처리"""
        error_msg = str(error)
        print(f"❌ 검색 오류: {error_msg}")
        
        # 사용자 친화적 오류 메시지
        if "API" in error_msg:
            user_msg = "YouTube API 연결에 문제가 있습니다. API 키를 확인해주세요."
        elif "quota" in error_msg.lower():
            user_msg = "API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요."
        elif "연결" in error_msg:
            user_msg = "인터넷 연결을 확인해주세요."
        else:
            user_msg = f"검색 중 오류가 발생했습니다: {error_msg}"
        
        messagebox.showerror("검색 오류", user_msg)
        self.update_progress(0, "오류 발생")

    def show_results_in_viewer(self, videos_data, analysis_settings):
        """결과 뷰어에 결과 표시"""
        try:
            # 결과 탭 로드 (아직 로드되지 않은 경우)
            self.main_window.load_results_tab()
            
            # 결과 탭으로 전환
            self.main_window.notebook.select(2)  # 세 번째 탭 (결과 보기)
            
            # 결과 표시
            if self.main_window.results_viewer:
                self.main_window.results_viewer.display_results(videos_data, analysis_settings)
            else:
                print("❌ 결과 뷰어를 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"결과 표시 오류: {e}")