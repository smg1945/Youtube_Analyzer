"""
채널 분석 탭 모듈
YouTube 채널 분석 인터페이스 담당
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, simpledialog
import threading
import re
from datetime import datetime

# Core 모듈들
from core import ChannelAnalyzer, YouTubeClient
from data import create_analysis_suite
from exporters import quick_excel_export, quick_thumbnail_download

class ChannelTab:
    """채널 분석 탭 클래스"""
    
    def __init__(self, parent, main_window):
        """
        채널 분석 탭 초기화
        
        Args:
            parent: 부모 위젯
            main_window: 메인 창 인스턴스
        """
        self.parent = parent
        self.main_window = main_window
        
        # 분석 상태
        self.is_analyzing = False
        self.current_channel_data = None
        self.current_videos = []
        
        # YouTube 클라이언트
        self.youtube_client = None
        self.channel_analyzer = None
        
        # 분석 도구들
        self.analysis_suite = create_analysis_suite(language="ko")
        
        self.create_layout()
        print("✅ 채널 분석 탭 초기화 완료")
    
    def create_layout(self):
        """레이아웃 생성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.parent, bg='#f5f5f7')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 상단: 채널 입력 영역
        self.create_channel_input(main_container)
        
        # 중간: 분석 설정 영역
        self.create_analysis_settings(main_container)
        
        # 하단: 액션 및 진행률 영역
        self.create_action_area(main_container)
        
        # 결과 영역 (초기에는 숨김)
        self.create_results_area(main_container)
    
    def create_channel_input(self, parent):
        """채널 입력 영역"""
        input_frame = tk.LabelFrame(
            parent,
            text="📺 채널 정보",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        input_frame.pack(fill='x', pady=(0, 15))
        
        # 입력 방법 선택
        method_frame = tk.Frame(input_frame, bg='#f5f5f7')
        method_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(
            method_frame,
            text="입력 방법:",
            font=('SF Pro Display', 11, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.input_method_var = tk.StringVar(value="url")
        
        url_radio = tk.Radiobutton(
            method_frame,
            text="채널 URL",
            variable=self.input_method_var,
            value="url",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            command=self.on_input_method_changed
        )
        url_radio.pack(side='left', padx=(20, 10))
        
        name_radio = tk.Radiobutton(
            method_frame,
            text="채널명 검색",
            variable=self.input_method_var,
            value="name",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            command=self.on_input_method_changed
        )
        name_radio.pack(side='left', padx=(0, 10))
        
        id_radio = tk.Radiobutton(
            method_frame,
            text="채널 ID",
            variable=self.input_method_var,
            value="id",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            command=self.on_input_method_changed
        )
        id_radio.pack(side='left')
        
        # 채널 입력 필드
        input_field_frame = tk.Frame(input_frame, bg='#f5f5f7')
        input_field_frame.pack(fill='x', pady=(0, 10))
        
        self.input_label = tk.Label(
            input_field_frame,
            text="채널 URL:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        self.input_label.pack(side='left')
        
        self.channel_entry = tk.Entry(
            input_field_frame,
            font=('SF Pro Display', 11),
            width=50,
            relief='flat',
            bd=5
        )
        self.channel_entry.pack(side='left', padx=(10, 10), fill='x', expand=True)
        
        # 검색 버튼
        self.search_channel_button = tk.Button(
            input_field_frame,
            text="🔍 채널 찾기",
            font=('SF Pro Display', 10),
            bg='#007aff',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.search_channel
        )
        self.search_channel_button.pack(side='right')
        
        # 예시 텍스트
        self.example_label = tk.Label(
            input_frame,
            text="예: https://www.youtube.com/@channelname 또는 https://www.youtube.com/channel/UC...",
            font=('SF Pro Display', 9),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.example_label.pack(anchor='w')
        
        # 발견된 채널 정보 (초기에는 숨김)
        self.channel_info_frame = tk.Frame(input_frame, bg='#e6f3ff', relief='solid', bd=1)
        self.channel_info_label = tk.Label(
            self.channel_info_frame,
            text="",
            font=('SF Pro Display', 10),
            bg='#e6f3ff',
            fg='#1d1d1f',
            justify='left'
        )
        self.channel_info_label.pack(padx=10, pady=5)
    
    def create_analysis_settings(self, parent):
        """분석 설정 영역"""
        settings_frame = tk.LabelFrame(
            parent,
            text="⚙️ 분석 설정",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        settings_frame.pack(fill='x', pady=(0, 15))
        
        # 첫 번째 행
        row1_frame = tk.Frame(settings_frame, bg='#f5f5f7')
        row1_frame.pack(fill='x', pady=(0, 10))
        
        # 분석할 영상 수
        tk.Label(
            row1_frame,
            text="분석할 영상 수:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        self.video_count_var = tk.StringVar(value="50")
        video_count_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.video_count_var,
            values=["10", "25", "50", "100"],
            state="readonly",
            width=8
        )
        video_count_combo.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        # 정렬 순서
        tk.Label(
            row1_frame,
            text="정렬 순서:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=2, sticky='w', padx=(0, 10))
        
        self.sort_order_var = tk.StringVar(value="date")
        sort_combo = ttk.Combobox(
            row1_frame,
            textvariable=self.sort_order_var,
            values=["date", "viewCount"],
            state="readonly",
            width=12
        )
        sort_combo.grid(row=0, column=3, sticky='w')
        
        # 두 번째 행
        row2_frame = tk.Frame(settings_frame, bg='#f5f5f7')
        row2_frame.pack(fill='x')
        
        # 포함할 분석
        tk.Label(
            row2_frame,
            text="포함할 분석:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7'
        ).grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        analysis_options_frame = tk.Frame(row2_frame, bg='#f5f5f7')
        analysis_options_frame.grid(row=0, column=1, sticky='w', columnspan=3)
        
        self.include_performance_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            analysis_options_frame,
            text="성과 분석",
            variable=self.include_performance_var,
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(0, 15))
        
        self.include_trends_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            analysis_options_frame,
            text="업로드 트렌드",
            variable=self.include_trends_var,
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(0, 15))
        
        self.include_content_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            analysis_options_frame,
            text="컨텐츠 패턴",
            variable=self.include_content_var,
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left')
    
    def create_action_area(self, parent):
        """액션 영역"""
        action_frame = tk.Frame(parent, bg='#f5f5f7')
        action_frame.pack(fill='x', pady=(0, 15))
        
        # 버튼 영역
        button_frame = tk.Frame(action_frame, bg='#f5f5f7')
        button_frame.pack(side='left')
        
        # 분석 시작 버튼
        self.analyze_button = tk.Button(
            button_frame,
            text="📊 분석 시작",
            font=('SF Pro Display', 12, 'bold'),
            bg='#34c759',
            fg='white',
            width=15,
            height=2,
            borderwidth=0,
            cursor='hand2',
            command=self.start_analysis
        )
        self.analyze_button.pack(side='left', padx=(0, 10))
        
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
            command=self.stop_analysis,
            state='disabled'
        )
        self.stop_button.pack(side='left', padx=(0, 10))
        
        # 내보내기 버튼들
        export_frame = tk.Frame(button_frame, bg='#f5f5f7')
        export_frame.pack(side='left', padx=(20, 0))
        
        self.export_excel_button = tk.Button(
            export_frame,
            text="📊 엑셀 내보내기",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            width=15,
            borderwidth=0,
            cursor='hand2',
            command=self.export_excel,
            state='disabled'
        )
        self.export_excel_button.pack(side='top', pady=(0, 5))
        
        self.download_thumbnails_button = tk.Button(
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
        self.download_thumbnails_button.pack(side='top')
        
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
    
    def create_results_area(self, parent):
        """결과 영역 (초기에는 숨김)"""
        self.results_frame = tk.LabelFrame(
            parent,
            text="📊 분석 결과",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        # 초기에는 pack하지 않음
        
        # 결과 요약
        self.create_results_summary()
        
        # 상위 영상 목록
        self.create_top_videos_list()
    
    def create_results_summary(self):
        """결과 요약 영역"""
        summary_frame = tk.Frame(self.results_frame, bg='#f5f5f7')
        summary_frame.pack(fill='x', pady=(0, 15))
        
        # 채널 기본 정보
        self.channel_summary_label = tk.Label(
            summary_frame,
            text="",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f',
            justify='left'
        )
        self.channel_summary_label.pack(anchor='w')
        
        # 성과 요약
        performance_frame = tk.Frame(summary_frame, bg='#f5f5f7')
        performance_frame.pack(fill='x', pady=(10, 0))
        
        self.performance_labels = {}
        
        # 성과 지표들을 3열로 배치
        performance_items = [
            ("총 영상 수", "total_videos"),
            ("평균 조회수", "avg_views"),
            ("평균 참여도", "avg_engagement"),
            ("바이럴 영상", "viral_count"),
            ("업로드 주기", "upload_frequency"),
            ("일관성 점수", "consistency")
        ]
        
        for i, (label_text, key) in enumerate(performance_items):
            row = i // 3
            col = i % 3
            
            item_frame = tk.Frame(performance_frame, bg='#f5f5f7')
            item_frame.grid(row=row, column=col, sticky='w', padx=(0, 30), pady=5)
            
            tk.Label(
                item_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 10),
                bg='#f5f5f7',
                fg='#86868b'
            ).pack(side='left')
            
            self.performance_labels[key] = tk.Label(
                item_frame,
                text="0",
                font=('SF Pro Display', 10, 'bold'),
                bg='#f5f5f7',
                fg='#1d1d1f'
            )
            self.performance_labels[key].pack(side='left', padx=(5, 0))
    
    def create_top_videos_list(self):
        """상위 영상 목록"""
        list_frame = tk.Frame(self.results_frame, bg='#f5f5f7')
        list_frame.pack(fill='both', expand=True)
        
        tk.Label(
            list_frame,
            text="🏆 상위 성과 영상 (Top 10)",
            font=('SF Pro Display', 11, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(anchor='w', pady=(0, 10))
        
        # 간단한 리스트박스
        self.top_videos_listbox = tk.Listbox(
            list_frame,
            font=('SF Pro Display', 10),
            height=6,
            selectmode='extended'
        )
        self.top_videos_listbox.pack(fill='both', expand=True)
        
        # 더블클릭으로 YouTube에서 열기
        self.top_videos_listbox.bind('<Double-1>', self.open_selected_video)
    
    def on_input_method_changed(self):
        """입력 방법 변경 시"""
        method = self.input_method_var.get()
        
        if method == "url":
            self.input_label.config(text="채널 URL:")
            self.example_label.config(text="예: https://www.youtube.com/@channelname 또는 https://www.youtube.com/channel/UC...")
        elif method == "name":
            self.input_label.config(text="채널명:")
            self.example_label.config(text="예: '침착맨', '쯔양', '피식대학' 등")
        elif method == "id":
            self.input_label.config(text="채널 ID:")
            self.example_label.config(text="예: UCXvSjNInOMxKZMbRHzwNSiQ (UC로 시작하는 24자리)")
        
        # 입력 필드 클리어
        self.channel_entry.delete(0, tk.END)
        self.hide_channel_info()
    
    def search_channel(self):
        """채널 검색"""
        input_text = self.channel_entry.get().strip()
        if not input_text:
            messagebox.showwarning("입력 오류", "채널 정보를 입력해주세요.")
            return
        
        # API 키 확인
        api_key = self.main_window.get_api_key()
        if not api_key:
            messagebox.showwarning("API 키 필요", "채널 검색을 위해 API 키가 필요합니다.")
            self.main_window.setup_api_key_dialog()
            return
        
        # 백그라운드에서 채널 검색
        def search_thread():
            try:
                self.update_progress(20, "채널 검색 중...")
                
                # YouTube 클라이언트 초기화
                self.youtube_client = YouTubeClient(api_key)
                self.channel_analyzer = ChannelAnalyzer(self.youtube_client)
                
                # 채널 ID 추출
                channel_id, channel_name = self.channel_analyzer.extract_channel_id_from_url(input_text)
                
                if not channel_id:
                    raise Exception("채널을 찾을 수 없습니다. URL, 이름 또는 ID를 확인해주세요.")
                
                self.update_progress(50, "채널 정보 수집 중...")
                
                # 채널 정보 가져오기
                channel_info = self.youtube_client.get_channel_info(channel_id)
                
                if not channel_info:
                    raise Exception("채널 정보를 가져올 수 없습니다.")
                
                # UI 업데이트
                self.main_window.root.after(0, lambda: self.show_channel_info(channel_info, channel_id))
                
                self.update_progress(100, "채널 검색 완료")
                
            except Exception as e:
                self.main_window.root.after(0, lambda: self.handle_search_error(e))
            finally:
                self.main_window.root.after(0, lambda: self.update_progress(0, "대기 중..."))
        
        threading.Thread(target=search_thread, daemon=True).start()
    
    def show_channel_info(self, channel_info, channel_id):
        """찾은 채널 정보 표시"""
        snippet = channel_info['snippet']
        stats = channel_info['statistics']
        
        channel_title = snippet['title']
        subscriber_count = int(stats.get('subscriberCount', 0))
        video_count = int(stats.get('videoCount', 0))
        view_count = int(stats.get('viewCount', 0))
        
        info_text = (
            f"✅ 채널 발견: {channel_title}\n"
            f"📊 구독자: {self.format_number(subscriber_count)}명 | "
            f"영상: {video_count:,}개 | "
            f"총 조회수: {self.format_number(view_count)}"
        )
        
        self.channel_info_label.config(text=info_text)
        self.channel_info_frame.pack(fill='x', pady=(10, 0))
        
        # 분석 버튼 활성화
        self.analyze_button.config(state='normal')
        
        # 분석할 채널 정보 저장
        self.found_channel_id = channel_id
        self.found_channel_info = channel_info
    
    def hide_channel_info(self):
        """채널 정보 숨기기"""
        self.channel_info_frame.pack_forget()
        self.analyze_button.config(state='disabled')
    
    def start_analysis(self):
        """채널 분석 시작"""
        if self.is_analyzing:
            messagebox.showwarning("진행 중", "이미 분석이 진행 중입니다.")
            return
        
        if not hasattr(self, 'found_channel_id'):
            messagebox.showwarning("채널 선택 필요", "먼저 채널을 검색해주세요.")
            return
        
        # UI 상태 변경
        self.set_analyzing_state(True)
        
        # 분석 설정 구성
        analysis_settings = self.get_analysis_settings()
        
        # 백그라운드에서 분석 실행
        def analysis_thread():
            try:
                self.perform_channel_analysis(analysis_settings)
            except Exception as e:
                self.main_window.root.after(0, lambda: self.handle_analysis_error(e))
            finally:
                self.main_window.root.after(0, lambda: self.set_analyzing_state(False))
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def get_analysis_settings(self):
        """분석 설정 가져오기"""
        return {
            'video_count': int(self.video_count_var.get()),
            'sort_order': self.sort_order_var.get(),
            'include_performance': self.include_performance_var.get(),
            'include_trends': self.include_trends_var.get(),
            'include_content': self.include_content_var.get()
        }
    
    def perform_channel_analysis(self, settings):
        """실제 채널 분석 수행"""
        self.update_progress(10, "채널 분석 시작...")
        
        # 채널 종합 분석
        analysis_result = self.channel_analyzer.analyze_channel(
            self.found_channel_id,
            video_count=settings['video_count'],
            sort_order=settings['sort_order']
        )
        
        if 'error' in analysis_result:
            raise Exception(analysis_result['error'])
        
        self.update_progress(50, "영상 분석 중...")
        
        # 개별 영상 분석 강화
        videos = analysis_result['videos']
        analyzed_videos = []
        
        for i, video in enumerate(videos):
            if not self.is_analyzing:
                break
            
            try:
                # 개별 영상 분석
                enhanced_analysis = self.analyze_single_video(video, i + 1)
                video['analysis'] = enhanced_analysis
                analyzed_videos.append(video)
                
                # 진행률 업데이트
                progress = 50 + (i / len(videos)) * 40
                self.update_progress(progress, f"영상 분석 중... ({i+1}/{len(videos)})")
                
            except Exception as e:
                print(f"영상 분석 오류: {e}")
                continue
        
        self.update_progress(90, "결과 정리 중...")
        
        # 분석 결과 저장
        analysis_result['videos'] = analyzed_videos
        self.current_channel_data = analysis_result
        self.current_videos = analyzed_videos
        
        self.update_progress(100, "분석 완료!")
        
        # UI 업데이트 (메인 스레드에서)
        self.main_window.root.after(0, self.on_analysis_complete)
    
    def analyze_single_video(self, video, rank):
        """단일 영상 분석 강화"""
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
            'formatted_duration': '00:00'
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
            analysis['video_type'] = '쇼츠' if duration_seconds <= 60 else '롱폼'
            
            # Outlier Score 계산 (채널 평균 기준)
            current_views = int(video['statistics'].get('viewCount', 0))
            channel_avg = self.current_channel_data.get('statistics', {}).get('avg_views', 50000) if self.current_channel_data else 50000
            
            analysis['outlier_score'] = max(0.1, current_views / channel_avg)
            analysis['outlier_category'] = calc.categorize_outlier_score(analysis['outlier_score'])
            
        except Exception as e:
            print(f"영상 분석 세부 오류: {e}")
        
        return analysis
    
    def on_analysis_complete(self):
        """분석 완료 후 처리"""
        # 결과 영역 표시
        self.results_frame.pack(fill='both', expand=True, pady=(15, 0))
        
        # 결과 표시
        self.display_analysis_results()
        
        # 내보내기 버튼 활성화
        self.export_excel_button.config(state='normal')
        self.download_thumbnails_button.config(state='normal')
        
        # 할당량 업데이트
        if self.youtube_client:
            quota_used = self.youtube_client.get_quota_usage()
            self.main_window.update_quota(quota_used, 10000)
        
        # 완료 메시지
        channel_title = self.current_channel_data['channel_info']['snippet']['title']
        self.main_window.show_info(
            "분석 완료",
            f"'{channel_title}' 채널 분석이 완료되었습니다.\n\n"
            f"{len(self.current_videos)}개 영상을 분석했습니다."
        )
        
        # 메인 창의 결과 탭에도 표시
        self.main_window.show_channel_analysis(self.current_channel_data)
    
    def display_analysis_results(self):
        """분석 결과 표시"""
        channel_info = self.current_channel_data['channel_info']
        statistics = self.current_channel_data['statistics']
        performance = self.current_channel_data.get('performance', {})
        
        # 채널 요약 정보
        snippet = channel_info['snippet']
        stats = channel_info['statistics']
        
        summary_text = (
            f"📺 {snippet['title']}\n"
            f"📊 구독자: {self.format_number(int(stats.get('subscriberCount', 0)))}명 | "
            f"총 영상: {int(stats.get('videoCount', 0)):,}개 | "
            f"총 조회수: {self.format_number(int(stats.get('viewCount', 0)))}"
        )
        self.channel_summary_label.config(text=summary_text)
        
        # 성과 지표들
        performance_data = {
            'total_videos': f"{statistics.get('total_videos', 0):,}개",
            'avg_views': self.format_number(statistics.get('avg_views', 0)),
            'avg_engagement': f"{statistics.get('avg_engagement_rate', 0):.3f}%",
            'viral_count': f"{performance.get('viral_count', 0)}개",
            'upload_frequency': f"{statistics.get('avg_upload_frequency', 0):.1f}일",
            'consistency': f"{statistics.get('consistency_score', 0):.1f}%"
        }
        
        for key, value in performance_data.items():
            if key in self.performance_labels:
                self.performance_labels[key].config(text=value)
        
        # 상위 영상 목록
        self.top_videos_listbox.delete(0, tk.END)
        
        top_videos = sorted(
            self.current_videos,
            key=lambda x: x.get('analysis', {}).get('outlier_score', 0),
            reverse=True
        )[:10]
        
        for i, video in enumerate(top_videos, 1):
            title = video['snippet']['title']
            views = self.format_number(int(video['statistics'].get('viewCount', 0)))
            outlier = video.get('analysis', {}).get('outlier_score', 0)
            
            list_item = f"{i:2d}. {title[:40]}... | {views} | {outlier:.1f}x"
            self.top_videos_listbox.insert(tk.END, list_item)
    
    def stop_analysis(self):
        """분석 중지"""
        self.is_analyzing = False
        self.update_progress(0, "중지됨")
        self.main_window.update_status("채널 분석이 중지되었습니다.")
    
    def export_excel(self):
        """엑셀 내보내기"""
        if not self.current_videos:
            messagebox.showwarning("데이터 없음", "내보낼 데이터가 없습니다.")
            return
        
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx")],
                title="엑셀 파일 저장"
            )
            
            if filename:
                def export_thread():
                    try:
                        # 분석 설정 구성
                        channel_title = self.current_channel_data['channel_info']['snippet']['title']
                        export_settings = {
                            'mode': 'channel_analysis',
                            'mode_name': f"채널 분석: {channel_title}",
                            'channel_name': channel_title,
                            'total_found': len(self.current_videos),
                            'search_timestamp': datetime.now().isoformat()
                        }
                        
                        result_file = quick_excel_export(
                            self.current_videos,
                            export_settings,
                            filename
                        )
                        
                        self.main_window.root.after(0, lambda: self.main_window.show_info(
                            "내보내기 완료",
                            f"엑셀 파일이 저장되었습니다:\n{result_file}"
                        ))
                        
                    except Exception as e:
                        self.main_window.root.after(0, lambda: self.main_window.show_error(
                            "내보내기 실패", str(e)
                        ))
                
                threading.Thread(target=export_thread, daemon=True).start()
                
        except Exception as e:
            self.main_window.show_error("내보내기 오류", str(e))
    
    def download_thumbnails(self):
        """썸네일 다운로드"""
        if not self.current_videos:
            messagebox.showwarning("데이터 없음", "다운로드할 데이터가 없습니다.")
            return
        
        try:
            folder = filedialog.askdirectory(title="썸네일 저장 폴더 선택")
            
            if folder:
                def download_thread():
                    try:
                        result = quick_thumbnail_download(
                            self.current_videos,
                            quality='high',
                            output_dir=folder
                        )
                        
                        if result['success']:
                            self.main_window.root.after(0, lambda: self.main_window.show_info(
                                "다운로드 완료",
                                f"썸네일 다운로드 완료:\n"
                                f"성공: {result['summary']['successful_downloads']}개\n"
                                f"실패: {result['summary']['failed_downloads']}개"
                            ))
                        else:
                            self.main_window.root.after(0, lambda: self.main_window.show_error(
                                "다운로드 실패", result.get('error', '알 수 없는 오류')
                            ))
                        
                    except Exception as e:
                        self.main_window.root.after(0, lambda: self.main_window.show_error(
                            "다운로드 오류", str(e)
                        ))
                
                threading.Thread(target=download_thread, daemon=True).start()
                
        except Exception as e:
            self.main_window.show_error("다운로드 오류", str(e))
    
    def open_selected_video(self, event):
        """선택된 영상 YouTube에서 열기"""
        selection = self.top_videos_listbox.curselection()
        if not selection:
            return
        
        try:
            index = selection[0]
            if index < len(self.current_videos):
                video = self.current_videos[index]
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                
                import webbrowser
                webbrowser.open(video_url)
                
        except Exception as e:
            self.main_window.show_error("링크 열기 실패", str(e))
    
    def set_analyzing_state(self, analyzing):
        """분석 상태 변경"""
        self.is_analyzing = analyzing
        
        if analyzing:
            self.analyze_button.config(state='disabled')
            self.stop_button.config(state='normal')
            self.search_channel_button.config(state='disabled')
            self.main_window.update_status("채널 분석 중...")
        else:
            self.analyze_button.config(state='normal' if hasattr(self, 'found_channel_id') else 'disabled')
            self.stop_button.config(state='disabled')
            self.search_channel_button.config(state='normal')
            self.main_window.update_status("채널 분석 완료")
    
    def update_progress(self, value, text):
        """진행률 업데이트"""
        self.main_window.root.after(0, lambda: self._update_progress_ui(value, text))
    
    def _update_progress_ui(self, value, text):
        """진행률 UI 업데이트"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.main_window.update_status(text)
    
    def handle_search_error(self, error):
        """검색 오류 처리"""
        error_message = str(error)
        
        if "quotaExceeded" in error_message:
            self.main_window.show_error("API 할당량 초과", 
                "YouTube API 일일 할당량을 초과했습니다.\n내일 다시 시도하거나 다른 API 키를 사용하세요.")
        elif "채널을 찾을 수 없습니다" in error_message:
            self.main_window.show_warning("채널 없음",
                "입력한 정보로 채널을 찾을 수 없습니다.\n다른 URL이나 채널명을 시도해보세요.")
        else:
            self.main_window.show_error("검색 오류", error_message)
    
    def handle_analysis_error(self, error):
        """분석 오류 처리"""
        self.main_window.show_error("분석 오류", str(error))
        self.update_progress(0, "오류 발생")
    
    # 유틸리티 메서드들
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
    
    def format_number(self, number):
        """숫자 포맷팅"""
        if isinstance(number, str):
            try:
                number = float(number)
            except:
                return str(number)
        
        if number >= 1000000:
            return f"{number/1000000:.1f}M"
        elif number >= 1000:
            return f"{number/1000:.1f}K"
        else:
            return f"{number:,.0f}" if number == int(number) else f"{number:.1f}"