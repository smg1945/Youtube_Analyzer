"""
YouTube 트렌드 분석기 GUI (완전한 버전)
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext
import threading
import os
import sys
from datetime import datetime
import webbrowser
import requests
import re

# 프로젝트 모듈들
import config
from youtube_api import YouTubeAPIClient
from data_analyzer import DataAnalyzer
from excel_generator import ExcelGenerator
from transcript_downloader import TranscriptDownloader

class YouTubeTrendAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 YouTube 트렌드 분석기 v2.1")
        self.root.geometry("950x750")
        self.root.configure(bg='#f0f0f0')
        
        # 분석 관련 객체들
        self.api_client = None
        self.analyzer = None
        self.excel_generator = None
        self.transcript_downloader = None
        
        # 분석 결과 저장
        self.analyzed_videos = []
        self.current_settings = {}
        
        # GUI 구성 요소 생성
        self.create_widgets()
        
        # API 키 확인
        self.check_api_key()
    
    def check_api_key(self):
        """API 키 확인"""
        if not config.DEVELOPER_KEY or config.DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
            messagebox.showerror(
                "API 키 오류", 
                "YouTube API 키가 설정되지 않았습니다!\n\n"
                "config.py 파일에서 DEVELOPER_KEY를 설정해주세요.\n\n"
                "Google Cloud Console에서 YouTube Data API v3 키를 발급받으세요."
            )
    
    def create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 제목
        title_label = tk.Label(
            main_frame, 
            text="🎬 YouTube 트렌드 분석기 v2.1",
            font=("Arial", 18, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # 왼쪽 설정 패널
        self.create_settings_panel(main_frame)
        
        # 오른쪽 결과 패널
        self.create_results_panel(main_frame)
        
        # 하단 버튼 패널
        self.create_button_panel(main_frame)
        
        # 상태바
        self.create_status_bar(main_frame)
        
        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=2)
        main_frame.rowconfigure(1, weight=1)
    
    def create_settings_panel(self, parent):
        """설정 패널 생성"""
        settings_frame = ttk.LabelFrame(parent, text="⚙️ 분석 설정", padding="10")
        settings_frame.grid(row=1, column=0, padx=(0, 10), sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 분석 모드
        ttk.Label(settings_frame, text="분석 모드:").grid(row=0, column=0, sticky=tk.W, pady=(0, 5))
        self.mode_var = tk.StringVar(value="trending")
        ttk.Radiobutton(settings_frame, text="트렌딩 분석", variable=self.mode_var, 
                       value="trending", command=self.on_mode_change).grid(row=1, column=0, sticky=tk.W)
        ttk.Radiobutton(settings_frame, text="키워드 검색", variable=self.mode_var, 
                       value="keyword", command=self.on_mode_change).grid(row=2, column=0, sticky=tk.W)
        
        # 지역 선택
        ttk.Label(settings_frame, text="지역:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.region_var = tk.StringVar(value="KR")
        region_frame = ttk.Frame(settings_frame)
        region_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        ttk.Radiobutton(region_frame, text="한국", variable=self.region_var, value="KR").pack(side=tk.LEFT)
        ttk.Radiobutton(region_frame, text="글로벌", variable=self.region_var, value="US").pack(side=tk.LEFT)
        
        # 영상 유형 (중요: 수정된 부분)
        ttk.Label(settings_frame, text="영상 유형:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.video_type_var = tk.StringVar(value="all")
        
        video_type_frame = ttk.Frame(settings_frame)
        video_type_frame.grid(row=6, column=0, columnspan=2, sticky=(tk.W, tk.E))
        
        ttk.Radiobutton(video_type_frame, text="전체", variable=self.video_type_var, 
                       value="all", command=self.on_video_type_change).grid(row=0, column=0, sticky=tk.W)
        ttk.Radiobutton(video_type_frame, text="롱폼 (>60초)", variable=self.video_type_var, 
                       value="long", command=self.on_video_type_change).grid(row=0, column=1, sticky=tk.W, padx=(10, 0))
        ttk.Radiobutton(video_type_frame, text="쇼츠 (≤60초)", variable=self.video_type_var, 
                       value="shorts", command=self.on_video_type_change).grid(row=0, column=2, sticky=tk.W, padx=(10, 0))
        
        # 영상 유형 안내 라벨
        self.video_type_info = tk.Label(
            settings_frame, 
            text="💡 롱폼: 60초 초과 영상, 쇼츠: 60초 이하 영상",
            font=("Arial", 8),
            fg="gray",
            bg='#f0f0f0'
        )
        self.video_type_info.grid(row=7, column=0, columnspan=2, sticky=tk.W, pady=(2, 0))
        
        # 키워드 검색 전용 설정
        self.keyword_frame = ttk.LabelFrame(settings_frame, text="🔍 키워드 검색 설정")
        self.keyword_frame.grid(row=8, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        # 키워드 입력
        ttk.Label(self.keyword_frame, text="검색 키워드:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.keyword_entry = ttk.Entry(self.keyword_frame, width=30)
        self.keyword_entry.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 5))
        self.keyword_entry.bind('<KeyRelease>', self.on_keyword_change)  # 실시간 유효성 검사
        
        # 키워드 안내
        self.keyword_info = tk.Label(
            self.keyword_frame,
            text="예: 건강, 다이어트, 요리, BTS 등",
            font=("Arial", 8),
            fg="gray",
            bg='#f0f0f0'
        )
        self.keyword_info.grid(row=2, column=0, sticky=tk.W)
        
        # 검색 기간
        ttk.Label(self.keyword_frame, text="검색 기간:").grid(row=3, column=0, sticky=tk.W, pady=(10, 5))
        self.period_var = tk.StringVar(value="30")
        period_frame = ttk.Frame(self.keyword_frame)
        period_frame.grid(row=4, column=0, sticky=(tk.W, tk.E))
        ttk.Radiobutton(period_frame, text="7일", variable=self.period_var, value="7").pack(side=tk.LEFT)
        ttk.Radiobutton(period_frame, text="30일", variable=self.period_var, value="30").pack(side=tk.LEFT, padx=(10, 0))
        ttk.Radiobutton(period_frame, text="90일", variable=self.period_var, value="90").pack(side=tk.LEFT, padx=(10, 0))
        
        # 필터 설정
        ttk.Label(self.keyword_frame, text="최대 구독자 수:").grid(row=5, column=0, sticky=tk.W, pady=(10, 5))
        self.max_subscribers_var = tk.StringVar(value="none")
        sub_frame = ttk.Frame(self.keyword_frame)
        sub_frame.grid(row=6, column=0, sticky=(tk.W, tk.E))
        ttk.Radiobutton(sub_frame, text="제한없음", variable=self.max_subscribers_var, value="none").pack(side=tk.LEFT)
        ttk.Radiobutton(sub_frame, text="100만", variable=self.max_subscribers_var, value="1000000").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(sub_frame, text="10만", variable=self.max_subscribers_var, value="100000").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(sub_frame, text="2만", variable=self.max_subscribers_var, value="20000").pack(side=tk.LEFT, padx=(5, 0))
        
        ttk.Label(self.keyword_frame, text="최소 조회수:").grid(row=7, column=0, sticky=tk.W, pady=(10, 5))
        self.min_views_var = tk.StringVar(value="none")
        views_frame = ttk.Frame(self.keyword_frame)
        views_frame.grid(row=8, column=0, sticky=(tk.W, tk.E))
        ttk.Radiobutton(views_frame, text="제한없음", variable=self.min_views_var, value="none").pack(side=tk.LEFT)
        ttk.Radiobutton(views_frame, text="1천", variable=self.min_views_var, value="1000").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(views_frame, text="1만", variable=self.min_views_var, value="10000").pack(side=tk.LEFT, padx=(5, 0))
        ttk.Radiobutton(views_frame, text="10만", variable=self.min_views_var, value="100000").pack(side=tk.LEFT, padx=(5, 0))
        
        # 카테고리 (트렌딩 모드 전용)
        self.category_frame = ttk.LabelFrame(settings_frame, text="📂 카테고리")
        self.category_frame.grid(row=9, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        ttk.Label(self.category_frame, text="카테고리:").grid(row=0, column=0, sticky=tk.W, pady=5)
        self.category_var = tk.StringVar(value="all")
        self.category_combo = ttk.Combobox(self.category_frame, textvariable=self.category_var, width=25, state="readonly")
        self.category_combo['values'] = [(f"{v} ({k})" if k != "all" else v) for k, v in config.YOUTUBE_CATEGORIES.items()]
        self.category_combo.set("전체 (all)")
        self.category_combo.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # API 절약 모드
        self.api_frame = ttk.LabelFrame(settings_frame, text="⚡ API 사용량 절약")
        self.api_frame.grid(row=10, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        self.light_mode_var = tk.BooleanVar(value=True)  # 기본값을 True로 변경
        ttk.Checkbutton(
            self.api_frame, 
            text="경량 모드 (Outlier Score 간소화로 API 사용량 90% 절약)", 
            variable=self.light_mode_var
        ).grid(row=0, column=0, sticky=tk.W, pady=5)
        
        ttk.Label(
            self.api_frame, 
            text="💡 첫 실행시에는 경량 모드를 권장합니다",
            font=("Arial", 8),
            foreground="blue",
            background='#f0f0f0'
        ).grid(row=1, column=0, sticky=tk.W)
        
        # 초기 상태 설정
        self.on_mode_change()
        
        # 컬럼 가중치
        settings_frame.columnconfigure(0, weight=1)
        self.keyword_frame.columnconfigure(0, weight=1)
        self.category_frame.columnconfigure(0, weight=1)
        self.api_frame.columnconfigure(0, weight=1)
    
    def on_video_type_change(self):
        """영상 유형 변경시 호출"""
        video_type = self.video_type_var.get()
        if video_type == "shorts":
            self.video_type_info.config(
                text="💡 쇼츠: 60초 이하 영상 (일반적으로 세로형)",
                fg="purple"
            )
        elif video_type == "long":
            self.video_type_info.config(
                text="💡 롱폼: 60초 초과 영상 (일반적으로 가로형)",
                fg="blue"
            )
        else:
            self.video_type_info.config(
                text="💡 전체: 모든 유형의 영상 포함",
                fg="gray"
            )
    
    def on_keyword_change(self, event):
        """키워드 변경시 실시간 유효성 검사"""
        keyword = self.keyword_entry.get().strip()
        if len(keyword) > 50:
            self.keyword_info.config(text="⚠️ 키워드가 너무 깁니다 (50자 이하 권장)", fg="red")
        elif len(keyword) == 0:
            self.keyword_info.config(text="예: 건강, 다이어트, 요리, BTS 등", fg="gray")
        else:
            self.keyword_info.config(text="✅ 유효한 키워드", fg="green")
    
    def create_results_panel(self, parent):
        """결과 패널 생성"""
        results_frame = ttk.LabelFrame(parent, text="📊 분석 결과", padding="10")
        results_frame.grid(row=1, column=1, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # 진행 상태
        self.progress_frame = ttk.Frame(results_frame)
        self.progress_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
        
        self.progress_label = ttk.Label(self.progress_frame, text="분석 준비 완료")
        self.progress_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(self.progress_frame, mode='indeterminate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # 결과 트리뷰
        columns = ("순위", "제목", "채널", "조회수", "Outlier점수", "영상유형", "길이")
        self.results_tree = ttk.Treeview(results_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 헤더 설정
        for col in columns:
            self.results_tree.heading(col, text=col)
            if col == "제목":
                self.results_tree.column(col, width=280)
            elif col == "채널":
                self.results_tree.column(col, width=120)
            elif col == "영상유형":
                self.results_tree.column(col, width=80)
            elif col == "길이":
                self.results_tree.column(col, width=80)
            else:
                self.results_tree.column(col, width=80)
        
        # 스크롤바
        scrollbar = ttk.Scrollbar(results_frame, orient=tk.VERTICAL, command=self.results_tree.yview)
        self.results_tree.configure(yscrollcommand=scrollbar.set)
        
        self.results_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        
        # 더블클릭 이벤트
        self.results_tree.bind("<Double-1>", self.on_video_double_click)
        
        # 컬럼 가중치
        results_frame.columnconfigure(0, weight=1)
        results_frame.rowconfigure(1, weight=1)
        self.progress_frame.columnconfigure(0, weight=1)
    
    def create_button_panel(self, parent):
        """버튼 패널 생성"""
        button_frame = ttk.Frame(parent)
        button_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        # 분석 시작 버튼
        self.analyze_button = ttk.Button(
            button_frame, 
            text="🚀 분석 시작", 
            command=self.start_analysis,
            style="Accent.TButton"
        )
        self.analyze_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 엑셀 저장 버튼
        self.excel_button = ttk.Button(
            button_frame, 
            text="📊 엑셀 저장", 
            command=self.save_excel,
            state=tk.DISABLED
        )
        self.excel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 채널 분석 버튼
        self.channel_button = ttk.Button(
            button_frame, 
            text="📺 채널 분석", 
            command=self.analyze_channel,
            state=tk.DISABLED
        )
        self.channel_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 썸네일 다운로드 버튼
        self.thumbnail_button = ttk.Button(
            button_frame, 
            text="🖼️ 썸네일 다운로드", 
            command=self.download_thumbnails,
            state=tk.DISABLED
        )
        self.thumbnail_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 설정 테스트 버튼
        test_button = ttk.Button(
            button_frame, 
            text="🔧 설정 테스트", 
            command=self.test_current_settings
        )
        test_button.pack(side=tk.LEFT, padx=(0, 10))
        
        # 정보 버튼
        info_button = ttk.Button(
            button_frame, 
            text="ℹ️ 정보", 
            command=self.show_info
        )
        info_button.pack(side=tk.RIGHT)
    
    def test_current_settings(self):
        """현재 설정으로 간단한 테스트"""
        settings = self.prepare_settings()
        if not settings:
            return
        
        # 테스트 결과 창
        test_window = tk.Toplevel(self.root)
        test_window.title("🔧 설정 테스트 결과")
        test_window.geometry("600x400")
        
        text_area = scrolledtext.ScrolledText(test_window, wrap=tk.WORD, width=70, height=20)
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 설정 정보 출력
        text_area.insert(tk.END, "🔧 현재 설정 테스트\n")
        text_area.insert(tk.END, "=" * 50 + "\n\n")
        
        text_area.insert(tk.END, f"분석 모드: {settings['mode_name']}\n")
        text_area.insert(tk.END, f"지역: {settings['region_name']}\n")
        text_area.insert(tk.END, f"영상 유형: {settings['video_type_name']}\n")
        
        if settings['mode'] == 'keyword':
            text_area.insert(tk.END, f"키워드: '{settings['keyword']}'\n")
            text_area.insert(tk.END, f"검색 기간: {settings['period_days']}일\n")
            text_area.insert(tk.END, f"최대 구독자: {settings['max_subscribers_name']}\n")
            text_area.insert(tk.END, f"최소 조회수: {settings['min_views_name']}\n")
        else:
            text_area.insert(tk.END, f"카테고리: {settings['category_name']}\n")
        
        text_area.insert(tk.END, f"경량 모드: {'활성화' if settings['light_mode'] else '비활성화'}\n\n")
        
        # 설정 분석
        text_area.insert(tk.END, "📊 설정 분석 결과:\n")
        text_area.insert(tk.END, "-" * 30 + "\n")
        
        if settings['mode'] == 'keyword':
            # 키워드 분석
            keyword = settings['keyword']
            if len(keyword) < 2:
                text_area.insert(tk.END, "⚠️ 키워드가 너무 짧습니다. (2자 이상 권장)\n")
            elif len(keyword) > 20:
                text_area.insert(tk.END, "⚠️ 키워드가 너무 깁니다. (20자 이하 권장)\n")
            else:
                text_area.insert(tk.END, "✅ 키워드 길이 적절\n")
            
            # 필터 분석
            if settings.get('max_subscribers') and settings.get('min_views'):
                if settings['max_subscribers'] < 100000 and settings['min_views'] > 50000:
                    text_area.insert(tk.END, "⚠️ 필터가 너무 엄격합니다. 결과가 없을 수 있습니다.\n")
                else:
                    text_area.insert(tk.END, "✅ 필터 설정 적절\n")
            
            # 검색 기간 분석
            if settings['period_days'] < 7:
                text_area.insert(tk.END, "⚠️ 검색 기간이 짧습니다. 30일 이상 권장\n")
            else:
                text_area.insert(tk.END, "✅ 검색 기간 적절\n")
        
        text_area.insert(tk.END, "\n💡 권장사항:\n")
        if not settings['light_mode']:
            text_area.insert(tk.END, "- 첫 실행시에는 경량 모드 활성화 권장\n")
        if settings['mode'] == 'keyword' and settings.get('min_views', 0) > 50000:
            text_area.insert(tk.END, "- 최소 조회수를 낮춰보세요 (1만 이하)\n")
        if settings['mode'] == 'keyword' and settings.get('max_subscribers', float('inf')) < 500000:
            text_area.insert(tk.END, "- 최대 구독자를 늘려보세요 (100만 이상)\n")
        
        text_area.config(state=tk.DISABLED)
    
    def create_status_bar(self, parent):
        """상태바 생성"""
        self.status_var = tk.StringVar()
        self.status_var.set("준비 완료")
        
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))
        
        status_label = ttk.Label(status_frame, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        status_label.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # API 사용량 표시
        self.api_usage_var = tk.StringVar()
        self.api_usage_var.set("API: 0/10000")
        api_label = ttk.Label(status_frame, textvariable=self.api_usage_var, relief=tk.SUNKEN, anchor=tk.E)
        api_label.pack(side=tk.RIGHT, padx=(10, 0))
    
    def on_mode_change(self):
        """분석 모드 변경시 호출"""
        mode = self.mode_var.get()
        
        if mode == "keyword":
            self.keyword_frame.grid()
            self.category_frame.grid_remove()
        else:
            self.keyword_frame.grid_remove()
            self.category_frame.grid()
    
    def on_video_double_click(self, event):
        """영상 더블클릭시 호출"""
        selection = self.results_tree.selection()
        if selection:
            item = self.results_tree.item(selection[0])
            rank = int(item['values'][0]) - 1
            
            if 0 <= rank < len(self.analyzed_videos):
                video = self.analyzed_videos[rank]
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                webbrowser.open(video_url)
    
    def start_analysis(self):
        """분석 시작"""
        # 설정 검증
        if not self.validate_settings():
            return
        
        # 버튼 비활성화
        self.analyze_button.config(state=tk.DISABLED)
        self.excel_button.config(state=tk.DISABLED)
        self.channel_button.config(state=tk.DISABLED)
        self.thumbnail_button.config(state=tk.DISABLED)
        
        # 진행 상태 초기화
        self.progress_bar.start()
        self.progress_label.config(text="분석 중...")
        self.status_var.set("분석 진행 중...")
        
        # 결과 초기화
        for item in self.results_tree.get_children():
            self.results_tree.delete(item)
        
        # 별도 스레드에서 분석 실행
        analysis_thread = threading.Thread(target=self.run_analysis)
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def validate_settings(self):
        """설정 검증 - 개선된 버전"""
        if self.mode_var.get() == "keyword":
            keyword = self.keyword_entry.get().strip()
            if not keyword:
                messagebox.showerror("입력 오류", "키워드를 입력해주세요.")
                return False
            
            if len(keyword) > 100:
                messagebox.showerror("입력 오류", "키워드가 너무 깁니다. (100자 이하)")
                return False
        
        if not config.DEVELOPER_KEY or config.DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
            messagebox.showerror("API 키 오류", "YouTube API 키가 설정되지 않았습니다.")
            return False
        
        return True
    
    def prepare_settings(self):
        """GUI 설정을 분석용 설정으로 변환 - 개선된 버전"""
        try:
            settings = {
                'mode': self.mode_var.get(),
                'region': self.region_var.get(),
                'video_type': self.video_type_var.get(),  # 중요: 이 부분이 누락되어 있었음
                'language': 'ko' if self.region_var.get() == 'KR' else 'en',
                'light_mode': self.light_mode_var.get()
            }
            
            # 모드별 설정 이름
            settings['mode_name'] = "키워드 검색" if settings['mode'] == "keyword" else "트렌딩 분석"
            settings['region_name'] = "한국" if settings['region'] == "KR" else "글로벌"
            
            # 영상 유형 이름
            video_type_names = {
                "all": "전체",
                "long": "롱폼",
                "shorts": "쇼츠"
            }
            settings['video_type_name'] = video_type_names.get(settings['video_type'], "전체")
            
            if settings['mode'] == "keyword":
                settings.update({
                    'keyword': self.keyword_entry.get().strip(),
                    'period_days': int(self.period_var.get()),
                    'max_subscribers': None if self.max_subscribers_var.get() == "none" else int(self.max_subscribers_var.get()),
                    'min_views': None if self.min_views_var.get() == "none" else int(self.min_views_var.get())
                })
                
                # 설정 이름
                settings['max_subscribers_name'] = "제한 없음" if settings['max_subscribers'] is None else f"{settings['max_subscribers']:,} 이하"
                settings['min_views_name'] = "제한 없음" if settings['min_views'] is None else f"{settings['min_views']:,} 이상"
            else:
                category_text = self.category_var.get()
                category_id = "all"
                for k, v in config.YOUTUBE_CATEGORIES.items():
                    if v in category_text:
                        category_id = k
                        break
                settings['category'] = category_id
                settings['category_name'] = config.YOUTUBE_CATEGORIES.get(category_id, "전체")
            
            return settings
            
        except Exception as e:
            messagebox.showerror("설정 오류", f"설정 준비 중 오류: {e}")
            return None
    
    def run_analysis(self):
        """실제 분석 실행 (별도 스레드)"""
        try:
            # 설정 준비
            settings = self.prepare_settings()
            if not settings:
                self.root.after(0, lambda: self.analysis_failed("설정 준비 실패"))
                return
                
            self.current_settings = settings
            
            # 분석 객체 초기화
            self.root.after(0, lambda: self.progress_label.config(text="분석 도구 초기화 중..."))
            
            self.api_client = YouTubeAPIClient(config.DEVELOPER_KEY)
            self.analyzer = DataAnalyzer(language=settings['language'])
            self.transcript_downloader = TranscriptDownloader()
            
            # 영상 데이터 수집
            self.root.after(0, lambda: self.progress_label.config(text="영상 데이터 수집 중..."))
            videos = self.collect_video_data(settings)
            
            if not videos:
                self.root.after(0, lambda: self.analysis_failed("영상 데이터를 가져올 수 없습니다."))
                return
            
            # 영상 분석
            self.root.after(0, lambda: self.progress_label.config(text="영상 분석 중..."))
            self.analyzed_videos = self.analyze_videos(videos, settings)
            
            if not self.analyzed_videos:
                self.root.after(0, lambda: self.analysis_failed("분석 가능한 영상이 없습니다."))
                return
            
            # 결과 표시
            self.root.after(0, self.analysis_completed)
            
        except Exception as e:
            error_msg = f"분석 중 오류 발생: {str(e)}"
            self.root.after(0, lambda: self.analysis_failed(error_msg))
    
    def collect_video_data(self, settings):
        """영상 데이터 수집 - 개선된 버전"""
        try:
            # API 사용량 확인
            quota_status = self.api_client.get_quota_status()
            if quota_status['percentage'] > 95:
                raise Exception(f"API 할당량이 부족합니다 ({quota_status['used']}/10000 사용). 내일 다시 시도해주세요.")
            
            if settings['mode'] == "keyword":
                return self.api_client.search_videos_by_keyword(
                    keyword=settings['keyword'],
                    region_code=settings['region'],
                    max_results=200,
                    max_subscriber_count=settings.get('max_subscribers'),
                    min_view_count=settings.get('min_views'),
                    period_days=settings.get('period_days', 30),
                    video_type=settings['video_type']  # 중요: video_type 전달
                )
            else:
                if settings['video_type'] == "shorts":
                    return self.api_client.get_trending_shorts(
                        region_code=settings['region'],
                        max_results=200
                    )
                else:
                    category_id = settings['category'] if settings['category'] != "all" else None
                    videos = self.api_client.get_trending_videos(
                        region_code=settings['region'],
                        category_id=category_id,
                        max_results=200
                    )
                    
                    if settings['video_type'] != "all":
                        videos = self.api_client.filter_videos_by_type(videos, settings['video_type'])
                    
                    return videos
        except Exception as e:
            if "quotaExceeded" in str(e) or "할당량" in str(e):
                self.root.after(0, lambda: messagebox.showerror(
                    "API 할당량 초과", 
                    f"YouTube API 할당량을 초과했습니다.\n\n"
                    f"현재 사용량: {self.api_client.get_quota_usage() if hasattr(self, 'api_client') and self.api_client else 'Unknown'}/10,000\n\n"
                    f"해결 방법:\n"
                    f"1. 내일 다시 시도해주세요 (할당량은 매일 자정 UTC 기준으로 리셋)\n"
                    f"2. 경량 모드를 사용해서 API 사용량을 절약하세요\n"
                    f"3. 더 적은 수의 영상을 분석해보세요"
                ))
            raise e
    
    def analyze_videos(self, videos, settings):
        """영상 분석"""
        analyzed_videos = []
        total_videos = len(videos)
        light_mode = settings.get('light_mode', False)
        
        if light_mode:
            print("⚡ 경량 모드로 분석합니다. API 사용량을 90% 절약합니다.")
        
        # 채널별 평균 통계 캐시
        channel_stats_cache = {}
        
        for i, video in enumerate(videos, 1):
            # 진행률 업데이트
            progress_text = f"영상 분석 중... ({i}/{total_videos})"
            if light_mode:
                progress_text += " [경량 모드]"
            self.root.after(0, lambda t=progress_text: self.progress_label.config(text=t))
            
            try:
                # 기본 정보 추출
                video_id = video['id']
                snippet = video['snippet']
                statistics = video['statistics']
                content_details = video['contentDetails']
                channel_id = snippet['channelId']
                
                # 영상 길이 파싱
                duration_seconds = self.api_client.parse_duration(content_details['duration'])
                
                # 채널 평균 통계 가져오기 (경량 모드 지원)
                if channel_id not in channel_stats_cache:
                    channel_stats = self.api_client.get_channel_recent_videos_stats(
                        channel_id, 
                        light_mode=light_mode
                    )
                    channel_stats_cache[channel_id] = channel_stats
                else:
                    channel_stats = channel_stats_cache[channel_id]
                
                # Outlier Score 계산
                outlier_score = self.analyzer.calculate_outlier_score(statistics, channel_stats)
                outlier_category = self.analyzer.categorize_outlier_score(outlier_score)
                
                # 댓글 가져오기 (경량 모드에서는 건너뛰기)
                if light_mode:
                    comments = []
                else:
                    comments = self.api_client.get_video_comments(video_id, max_results=config.COMMENTS_PER_VIDEO)
                
                # 썸네일 URL 저장
                thumbnail_url = self.api_client.get_best_thumbnail_url(snippet['thumbnails'])
                
                # 분석 수행
                analysis = {
                    'keywords': self.analyzer.extract_keywords_from_title(
                        snippet['title'], max_keywords=config.KEYWORD_EXTRACTION_COUNT
                    ),
                    'sentiment': self.analyzer.analyze_comments_sentiment(comments) if not light_mode else {'positive': 0, 'neutral': 100, 'negative': 0},
                    'engagement_score': self.analyzer.calculate_engagement_score(video),
                    'formatted_duration': self.analyzer.format_duration(duration_seconds),
                    'video_type': self.analyzer.determine_video_type(duration_seconds),
                    'views_per_day': self.analyzer.calculate_views_per_day(video),
                    'outlier_score': outlier_score,
                    'outlier_category': outlier_category,
                    'channel_avg_views': channel_stats.get('avg_views', 0) if channel_stats else 0,
                    'thumbnail_url': thumbnail_url
                }
                
                # 결과 저장
                video['analysis'] = analysis
                video['rank'] = i
                analyzed_videos.append(video)
                
                # API 사용량 업데이트
                quota_status = self.api_client.get_quota_status()
                usage_text = f"API: {quota_status['used']}/10000 ({quota_status['percentage']:.1f}%)"
                self.root.after(0, lambda usage=usage_text: self.api_usage_var.set(usage))
                
                # API 할당량 거의 소진시 경고
                if quota_status['percentage'] > 95:
                    self.root.after(0, lambda: messagebox.showwarning(
                        "API 할당량 부족", 
                        "API 할당량이 거의 소진되었습니다. 분석을 중단하고 내일 다시 시도해주세요."
                    ))
                    break
                
            except Exception as e:
                print(f"영상 분석 오류 (ID: {video.get('id', 'Unknown')}): {e}")
                continue
        
        # Outlier Score 기준으로 정렬하고 상위 100개만 선택
        analyzed_videos.sort(key=lambda x: x['analysis']['outlier_score'], reverse=True)
        top_outliers = analyzed_videos[:config.MAX_RESULTS]
        
        # 순위 재조정
        for i, video in enumerate(top_outliers, 1):
            video['rank'] = i
        
        return top_outliers
    
    def analysis_completed(self):
        """분석 완료 처리"""
        self.progress_bar.stop()
        self.progress_label.config(text=f"분석 완료! {len(self.analyzed_videos)}개 영상")
        self.status_var.set(f"분석 완료 - {len(self.analyzed_videos)}개 영상")
        
        # 결과를 트리뷰에 표시
        for video in self.analyzed_videos:
            snippet = video['snippet']
            statistics = video['statistics']
            analysis = video['analysis']
            
            title = snippet['title'][:45] + "..." if len(snippet['title']) > 45 else snippet['title']
            channel = snippet['channelTitle'][:15] + "..." if len(snippet['channelTitle']) > 15 else snippet['channelTitle']
            views = f"{int(statistics.get('viewCount', 0)):,}"
            outlier_score = f"{analysis['outlier_score']:.1f}x"
            video_type = analysis['video_type']
            duration = analysis['formatted_duration']
            
            self.results_tree.insert("", tk.END, values=(
                video['rank'], title, channel, views, outlier_score, video_type, duration
            ))
        
        # 버튼 활성화
        self.analyze_button.config(state=tk.NORMAL)
        self.excel_button.config(state=tk.NORMAL)
        self.channel_button.config(state=tk.NORMAL)
        self.thumbnail_button.config(state=tk.NORMAL)
        
        # 완료 메시지
        video_type_msg = f" ({self.current_settings.get('video_type_name', '전체')} 유형)"
        messagebox.showinfo("분석 완료", f"총 {len(self.analyzed_videos)}개 영상 분석이 완료되었습니다!{video_type_msg}")
    
    def analysis_failed(self, error_msg):
        """분석 실패 처리"""
        self.progress_bar.stop()
        self.progress_label.config(text="분석 실패")
        self.status_var.set("분석 실패")
        
        # 버튼 활성화
        self.analyze_button.config(state=tk.NORMAL)
        
        # 오류 메시지
        messagebox.showerror("분석 실패", error_msg)
    
    def save_excel(self):
        """엑셀 저장"""
        if not self.analyzed_videos:
            messagebox.showwarning("저장 오류", "저장할 분석 결과가 없습니다.")
            return
        
        try:
            # 파일 경로 선택
            filename = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
                title="엑셀 파일 저장"
            )
            
            if filename:
                self.excel_generator = ExcelGenerator(filename)
                self.excel_generator.create_excel_file(self.analyzed_videos, self.current_settings)
                
                messagebox.showinfo("저장 완료", f"엑셀 파일이 저장되었습니다:\n{filename}")
                
        except Exception as e:
            messagebox.showerror("저장 실패", f"엑셀 저장 중 오류 발생:\n{str(e)}")
    
    def download_thumbnails(self):
        """선택된 영상들의 썸네일 다운로드"""
        if not self.analyzed_videos:
            messagebox.showwarning("다운로드 오류", "다운로드할 영상이 없습니다.")
            return
        
        # 썸네일 다운로드 옵션 창 열기
        ThumbnailDownloadWindow(self.root, self.analyzed_videos, self.api_client)
    
    def analyze_channel(self):
        """채널 분석"""
        selection = self.results_tree.selection()
        if not selection:
            messagebox.showwarning("선택 오류", "분석할 영상을 선택해주세요.")
            return
        
        # 선택된 영상 정보 가져오기
        item = self.results_tree.item(selection[0])
        rank = int(item['values'][0]) - 1
        
        if 0 <= rank < len(self.analyzed_videos):
            selected_video = self.analyzed_videos[rank]
            
            # 채널 분석 창 열기
            ChannelAnalysisWindow(self.root, selected_video, self.api_client, self.transcript_downloader)
    
    def show_info(self):
        """정보 창 표시"""
        info_text = f"""
🎬 YouTube 트렌드 분석기 v2.1

📊 주요 기능:
• 실시간 트렌딩 영상 분석
• 키워드 기반 영상 검색
• 영상 유형별 분석 (전체/롱폼/쇼츠)
• Outlier Score 기반 성과 분석
• 채널별 대본 다운로드
• 음성 인식 자막 생성
• 엑셀 리포트 자동 생성

🔧 기술 스택:
• YouTube Data API v3
• OpenAI Whisper (음성 인식)
• KoNLPy (한국어 처리)
• tkinter (GUI)

⚠️ 주의사항:
• YouTube API 키가 필요합니다
• 첫 실행시에는 경량 모드 권장
• API 일일 할당량을 확인해주세요 (10,000 단위)

💡 최신 개선사항:
• 영상 유형 필터링 정확도 향상
• 롱폼/쇼츠 구분 개선 (60초 기준)
• 설정 검증 및 테스트 기능 추가
• API 사용량 최적화

👨‍💻 개발: YouTube 트렌드 분석팀
📅 버전: 2.1 ({datetime.now().year})
        """
        
        messagebox.showinfo("프로그램 정보", info_text)


class ThumbnailDownloadWindow:
    def __init__(self, parent, analyzed_videos, api_client):
        self.parent = parent
        self.analyzed_videos = analyzed_videos
        self.api_client = api_client
        
        # 새 창 생성
        self.window = tk.Toplevel(parent)
        self.window.title("🖼️ 썸네일 다운로드")
        self.window.geometry("950x650")
        self.window.configure(bg='#f0f0f0')
        
        self.create_widgets()
    
    def create_widgets(self):
        """위젯 생성"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = tk.Label(
            main_frame,
            text="🖼️ 썸네일 다운로드",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0'
        )
        title_label.pack(pady=(0, 10))
        
        # 설명
        desc_label = tk.Label(
            main_frame,
            text="다운로드할 영상들을 선택하세요. 체크박스를 사용하여 개별 선택하거나 전체 선택할 수 있습니다.",
            bg='#f0f0f0',
            fg='#666'
        )
        desc_label.pack(pady=(0, 10))
        
        # 영상 목록 프레임
        list_frame = ttk.LabelFrame(main_frame, text="영상 목록", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 캔버스와 스크롤바를 사용한 체크박스 리스트
        canvas_frame = ttk.Frame(list_frame)
        canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(canvas_frame, bg='white')
        scrollbar = ttk.Scrollbar(canvas_frame, orient=tk.VERTICAL, command=self.canvas.yview)
        self.scrollable_frame = ttk.Frame(self.canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        # 체크박스 변수들
        self.checkbox_vars = []
        
        # 영상 목록 생성
        for i, video in enumerate(self.analyzed_videos):
            var = tk.BooleanVar()
            self.checkbox_vars.append(var)
            
            frame = ttk.Frame(self.scrollable_frame)
            frame.pack(fill=tk.X, padx=5, pady=2)
            
            # 체크박스
            checkbox = ttk.Checkbutton(frame, variable=var)
            checkbox.pack(side=tk.LEFT)
            
            # 순위
            rank_label = tk.Label(frame, text=f"{i+1:2d}.", width=4, bg='white')
            rank_label.pack(side=tk.LEFT)
            
            # 제목과 정보
            title = video['snippet']['title'][:55] + "..." if len(video['snippet']['title']) > 55 else video['snippet']['title']
            channel = video['snippet']['channelTitle'][:20] + "..." if len(video['snippet']['channelTitle']) > 20 else video['snippet']['channelTitle']
            views = f"{int(video['statistics'].get('viewCount', 0)):,}"
            outlier_score = f"{video['analysis']['outlier_score']:.1f}x"
            video_type = video['analysis'].get('video_type', '알수없음')
            duration = video['analysis'].get('formatted_duration', '00:00')
            
            info_text = f"{title} | 📺 {channel} | 📊 {views} 조회수 | 🔥 {outlier_score} | 🎬 {video_type} ({duration})"
            info_label = tk.Label(frame, text=info_text, anchor='w', bg='white', font=("Arial", 9))
            info_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(10, 0))
        
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 선택 버튼 프레임
        select_frame = ttk.Frame(main_frame)
        select_frame.pack(fill=tk.X, pady=(0, 10))
        
        ttk.Button(select_frame, text="전체 선택", command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="선택 해제", command=self.select_none).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="상위 10개", command=self.select_top_10).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="바이럴 영상만", command=self.select_viral).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="롱폼만", command=self.select_long).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(select_frame, text="쇼츠만", command=self.select_shorts).pack(side=tk.LEFT)
        
        # 다운로드 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="📁 폴더 선택 후 다운로드", command=self.download_to_folder).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="🖼️ 기본 폴더에 다운로드", command=self.download_to_default).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="닫기", command=self.window.destroy).pack(side=tk.RIGHT)
    
    def select_all(self):
        """전체 선택"""
        for var in self.checkbox_vars:
            var.set(True)
    
    def select_none(self):
        """선택 해제"""
        for var in self.checkbox_vars:
            var.set(False)
    
    def select_top_10(self):
        """상위 10개 선택"""
        for i, var in enumerate(self.checkbox_vars):
            var.set(i < 10)
    
    def select_viral(self):
        """바이럴 영상만 선택 (Outlier Score 3.0x 이상)"""
        for i, var in enumerate(self.checkbox_vars):
            if i < len(self.analyzed_videos):
                outlier_score = self.analyzed_videos[i]['analysis']['outlier_score']
                var.set(outlier_score >= 3.0)
    
    def select_long(self):
        """롱폼 영상만 선택"""
        for i, var in enumerate(self.checkbox_vars):
            if i < len(self.analyzed_videos):
                video_type = self.analyzed_videos[i]['analysis'].get('video_type', '')
                var.set(video_type == '롱폼')
    
    def select_shorts(self):
        """쇼츠 영상만 선택"""
        for i, var in enumerate(self.checkbox_vars):
            if i < len(self.analyzed_videos):
                video_type = self.analyzed_videos[i]['analysis'].get('video_type', '')
                var.set(video_type == '쇼츠')
    
    def get_selected_videos(self):
        """선택된 영상들 반환"""
        selected = []
        for i, var in enumerate(self.checkbox_vars):
            if var.get() and i < len(self.analyzed_videos):
                video = self.analyzed_videos[i]
                selected.append({
                    'video_id': video['id'],
                    'title': video['snippet']['title'],
                    'thumbnail_url': video['analysis'].get('thumbnail_url'),
                    'rank': i + 1
                })
        return selected
    
    def download_to_default(self):
        """기본 폴더에 다운로드"""
        selected_videos = self.get_selected_videos()
        
        if not selected_videos:
            messagebox.showwarning("선택 오류", "다운로드할 영상을 선택해주세요.")
            return
        
        self.start_download(selected_videos)
    
    def download_to_folder(self):
        """사용자가 선택한 폴더에 다운로드"""
        selected_videos = self.get_selected_videos()
        
        if not selected_videos:
            messagebox.showwarning("선택 오류", "다운로드할 영상을 선택해주세요.")
            return
        
        folder = filedialog.askdirectory(title="썸네일 저장 폴더 선택")
        
        if folder:
            self.start_download(selected_videos, custom_folder=folder)
    
    def start_download(self, selected_videos, custom_folder=None):
        """다운로드 시작"""
        if not messagebox.askyesno("다운로드 확인", 
                                 f"{len(selected_videos)}개 영상의 썸네일을 다운로드하시겠습니까?\n\n"
                                 f"저장 위치: {custom_folder if custom_folder else '기본 폴더 (thumbnails/)'}"):
            return
        
        # 진행 창 생성
        progress_window = self.create_progress_window(len(selected_videos))
        
        # 별도 스레드에서 다운로드 실행
        download_thread = threading.Thread(
            target=self.run_thumbnail_download,
            args=(selected_videos, custom_folder, progress_window)
        )
        download_thread.daemon = True
        download_thread.start()
    
    def create_progress_window(self, total_count):
        """진행 상황 창 생성"""
        progress_window = tk.Toplevel(self.window)
        progress_window.title("썸네일 다운로드 진행 상황")
        progress_window.geometry("450x200")
        progress_window.configure(bg='#f0f0f0')
        
        frame = ttk.Frame(progress_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="썸네일 다운로드 중...", font=("Arial", 12)).pack(pady=(0, 10))
        
        progress_var = tk.StringVar()
        progress_label = ttk.Label(frame, textvariable=progress_var)
        progress_label.pack(pady=(0, 10))
        
        progress_bar = ttk.Progressbar(frame, maximum=total_count, mode='determinate')
        progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # 취소 버튼 (구현하지 않음 - 복잡성 때문에)
        ttk.Label(frame, text="다운로드가 완료될 때까지 기다려주세요...", 
                 font=("Arial", 9), foreground="gray").pack()
        
        return {
            'window': progress_window,
            'progress_var': progress_var,
            'progress_bar': progress_bar
        }
    
    def run_thumbnail_download(self, selected_videos, custom_folder, progress_window):
        """썸네일 다운로드 실행"""
        try:
            downloaded_files = []
            failed_count = 0
            
            # 폴더 생성
            if custom_folder:
                download_folder = custom_folder
            else:
                download_folder = 'thumbnails'
            
            os.makedirs(download_folder, exist_ok=True)
            
            for i, video_info in enumerate(selected_videos, 1):
                # 진행 상황 업데이트
                progress_text = f"다운로드 중: {i}/{len(selected_videos)} - {video_info.get('title', '')[:30]}..."
                self.window.after(0, lambda t=progress_text: progress_window['progress_var'].set(t))
                self.window.after(0, lambda i=i: progress_window['progress_bar'].config(value=i))
                
                if video_info['thumbnail_url']:
                    try:
                        response = requests.get(video_info['thumbnail_url'], timeout=10)
                        if response.status_code == 200:
                            # 안전한 파일명 생성
                            safe_title = re.sub(r'[^\w\s-]', '', video_info['title'].replace(' ', '_'))[:30]
                            filename = f"{video_info['rank']:03d}_{safe_title}_{video_info['video_id']}.jpg"
                            
                            file_path = os.path.join(download_folder, filename)
                            
                            with open(file_path, 'wb') as f:
                                f.write(response.content)
                            
                            downloaded_files.append(file_path)
                        else:
                            failed_count += 1
                    except Exception as e:
                        print(f"썸네일 다운로드 오류: {e}")
                        failed_count += 1
                else:
                    failed_count += 1
            
            # ZIP 파일 생성 (옵션)
            zip_file = None
            if downloaded_files and not custom_folder:
                try:
                    import zipfile
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    zip_filename = f"selected_thumbnails_{timestamp}.zip"
                    
                    with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path in downloaded_files:
                            if os.path.exists(file_path):
                                filename = os.path.basename(file_path)
                                zipf.write(file_path, filename)
                    
                    zip_file = zip_filename
                except Exception as e:
                    print(f"ZIP 파일 생성 오류: {e}")
            
            # 결과 메시지 생성
            result_msg = f"썸네일 다운로드 완료!\n\n"
            result_msg += f"성공: {len(downloaded_files)}개\n"
            result_msg += f"실패: {failed_count}개\n"
            result_msg += f"저장 위치: {download_folder}\n"
            
            if zip_file:
                result_msg += f"\nZIP 파일: {zip_file}"
            
            # 결과 표시
            self.window.after(0, lambda: self.show_download_result(result_msg, progress_window))
            
        except Exception as e:
            error_msg = f"썸네일 다운로드 중 오류 발생: {str(e)}"
            self.window.after(0, lambda: messagebox.showerror("다운로드 오류", error_msg))
            self.window.after(0, lambda: progress_window['window'].destroy())
    
    def show_download_result(self, result_msg, progress_window):
        """다운로드 결과 표시"""
        progress_window['window'].destroy()
        messagebox.showinfo("다운로드 완료", result_msg)


class ChannelAnalysisWindow:
    def __init__(self, parent, selected_video, api_client, transcript_downloader):
        self.parent = parent
        self.selected_video = selected_video
        self.api_client = api_client
        self.transcript_downloader = transcript_downloader
        
        # 새 창 생성
        self.window = tk.Toplevel(parent)
        self.window.title(f"📺 채널 분석 - {selected_video['snippet']['channelTitle']}")
        self.window.geometry("900x700")
        self.window.configure(bg='#f0f0f0')
        
        # 채널 영상 목록
        self.channel_videos = []
        self.selected_videos = []
        
        self.create_widgets()
        self.load_channel_videos()
    
    def create_widgets(self):
        """위젯 생성"""
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        channel_name = self.selected_video['snippet']['channelTitle']
        title_label = tk.Label(
            main_frame,
            text=f"📺 {channel_name} 채널 분석",
            font=("Arial", 14, "bold"),
            bg='#f0f0f0'
        )
        title_label.pack(pady=(0, 10))
        
        # 기준 영상 정보
        info_frame = ttk.LabelFrame(main_frame, text="기준 영상 정보", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        base_video_title = self.selected_video['snippet']['title'][:60] + "..." if len(self.selected_video['snippet']['title']) > 60 else self.selected_video['snippet']['title']
        base_video_views = f"{int(self.selected_video['statistics'].get('viewCount', 0)):,}"
        base_video_outlier = f"{self.selected_video['analysis']['outlier_score']:.1f}x"
        
        info_text = f"🎬 {base_video_title}\n📊 {base_video_views} 조회수 | 🔥 {base_video_outlier} Outlier점수"
        info_label = tk.Label(info_frame, text=info_text, bg='#f0f0f0', justify=tk.LEFT)
        info_label.pack(anchor=tk.W)
        
        # 채널 영상 목록
        list_frame = ttk.LabelFrame(main_frame, text="채널 영상 목록", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 영상 리스트박스
        listbox_frame = ttk.Frame(list_frame)
        listbox_frame.pack(fill=tk.BOTH, expand=True)
        
        self.videos_listbox = tk.Listbox(listbox_frame, selectmode=tk.EXTENDED, height=15, font=("Arial", 9))
        scrollbar_videos = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=self.videos_listbox.yview)
        self.videos_listbox.configure(yscrollcommand=scrollbar_videos.set)
        
        self.videos_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar_videos.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭으로 영상 열기
        self.videos_listbox.bind("<Double-1>", self.on_video_double_click)
        
        # 자막 설정
        settings_frame = ttk.LabelFrame(main_frame, text="자막 다운로드 설정", padding="10")
        settings_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 언어 설정
        lang_frame = ttk.Frame(settings_frame)
        lang_frame.pack(fill=tk.X)
        
        ttk.Label(lang_frame, text="언어 우선순위:").pack(side=tk.LEFT)
        self.language_var = tk.StringVar(value="ko_first")
        ttk.Radiobutton(lang_frame, text="한국어 우선", variable=self.language_var, value="ko_first").pack(side=tk.LEFT, padx=10)
        ttk.Radiobutton(lang_frame, text="영어 우선", variable=self.language_var, value="en_first").pack(side=tk.LEFT, padx=10)
        
        # 음성 인식 설정
        speech_frame = ttk.Frame(settings_frame)
        speech_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.speech_recognition_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            speech_frame, 
            text="자막이 없는 경우 음성 인식 사용 (시간 소요 많음)", 
            variable=self.speech_recognition_var
        ).pack(side=tk.LEFT)
        
        # 버튼
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)
        
        ttk.Button(button_frame, text="전체 선택", command=self.select_all).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(button_frame, text="선택 해제", command=self.select_none).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="📺 채널 페이지 열기", command=self.open_channel_page).pack(side=tk.LEFT, padx=(0, 10))
        
        ttk.Button(button_frame, text="📝 대본 다운로드", command=self.download_transcripts).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="닫기", command=self.window.destroy).pack(side=tk.RIGHT)
    
    def load_channel_videos(self):
        """채널 영상 목록 로드"""
        channel_id = self.selected_video['snippet']['channelId']
        
        # 로딩 메시지
        self.videos_listbox.insert(tk.END, "채널 영상 목록 로드 중...")
        self.window.update()
        
        try:
            self.channel_videos = self.api_client.get_channel_videos(channel_id, max_results=50)
            
            # 리스트박스 초기화
            self.videos_listbox.delete(0, tk.END)
            
            # 영상 목록 추가
            for i, video in enumerate(self.channel_videos, 1):
                title = video['title'][:50] + "..." if len(video['title']) > 50 else video['title']
                views = f"{video.get('view_count', 0):,}"
                duration_seconds = 0
                
                try:
                    duration_seconds = self.api_client.parse_duration(video.get('duration', 'PT0S'))
                except:
                    pass
                
                if duration_seconds < 3600:
                    duration_str = f"{duration_seconds//60:02d}:{duration_seconds%60:02d}"
                else:
                    hours = duration_seconds // 3600
                    minutes = (duration_seconds % 3600) // 60
                    seconds = duration_seconds % 60
                    duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
                
                # 영상 유형 판별
                video_type = "쇼츠" if duration_seconds <= 60 else "롱폼"
                published_date = video['published_at'][:10]  # YYYY-MM-DD
                
                display_text = f"{i:2d}. {title} | 👁 {views} | ⏰ {duration_str} | 🎬 {video_type} | 📅 {published_date}"
                self.videos_listbox.insert(tk.END, display_text)
            
            if not self.channel_videos:
                self.videos_listbox.insert(tk.END, "채널 영상을 찾을 수 없습니다.")
            else:
                print(f"✅ 채널 영상 목록 로드 완료: {len(self.channel_videos)}개")
                
        except Exception as e:
            self.videos_listbox.delete(0, tk.END)
            self.videos_listbox.insert(tk.END, f"오류: {str(e)}")
            print(f"❌ 채널 영상 목록 로드 오류: {e}")
    
    def on_video_double_click(self, event):
        """영상 더블클릭시 YouTube에서 열기"""
        selection = self.videos_listbox.curselection()
        if selection:
            index = selection[0]
            if 0 <= index < len(self.channel_videos):
                video_id = self.channel_videos[index]['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(video_url)
    
    def open_channel_page(self):
        """채널 페이지 열기"""
        channel_id = self.selected_video['snippet']['channelId']
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        webbrowser.open(channel_url)
    
    def select_all(self):
        """전체 선택"""
        self.videos_listbox.select_set(0, tk.END)
    
    def select_none(self):
        """선택 해제"""
        self.videos_listbox.selection_clear(0, tk.END)
    
    def download_transcripts(self):
        """선택된 영상들의 대본 다운로드"""
        selection = self.videos_listbox.curselection()
        
        if not selection:
            messagebox.showwarning("선택 오류", "다운로드할 영상을 선택해주세요.")
            return
        
        # 선택된 영상들 정보 수집
        selected_videos = [self.channel_videos[i] for i in selection]
        
        if not selected_videos:
            return
        
        # 언어 설정
        lang_setting = self.language_var.get()
        if lang_setting == "ko_first":
            language_codes = ['ko', 'kr', 'en']
        else:
            language_codes = ['en', 'ko', 'kr']
        
        enable_speech = self.speech_recognition_var.get()
        
        # 확인 대화상자
        channel_name = self.selected_video['snippet']['channelTitle']
        confirm_msg = f"{len(selected_videos)}개 영상의 대본을 다운로드하시겠습니까?\n\n"
        confirm_msg += f"채널: {channel_name}\n"
        confirm_msg += f"언어: {language_codes[0]} 우선\n"
        
        if enable_speech:
            confirm_msg += "\n⚠️ 음성 인식이 활성화되어 시간이 많이 소요될 수 있습니다."
        
        if not messagebox.askyesno("다운로드 확인", confirm_msg):
            return
        
        # 진행 창 생성
        progress_window = self.create_progress_window(len(selected_videos))
        
        # 별도 스레드에서 다운로드 실행
        download_thread = threading.Thread(
            target=self.run_transcript_download,
            args=(selected_videos, language_codes, enable_speech, progress_window)
        )
        download_thread.daemon = True
        download_thread.start()
    
    def create_progress_window(self, total_videos):
        """진행 상황 창 생성"""
        progress_window = tk.Toplevel(self.window)
        progress_window.title("대본 다운로드 진행 상황")
        progress_window.geometry("500x250")
        progress_window.configure(bg='#f0f0f0')
        
        frame = ttk.Frame(progress_window, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="대본 다운로드 중...", font=("Arial", 12)).pack(pady=(0, 10))
        
        progress_var = tk.StringVar()
        progress_label = ttk.Label(frame, textvariable=progress_var, wraplength=450)
        progress_label.pack(pady=(0, 10))
        
        progress_bar = ttk.Progressbar(frame, maximum=total_videos, mode='determinate')
        progress_bar.pack(fill=tk.X, pady=(0, 10))
        
        # 상태 정보
        status_var = tk.StringVar()
        status_label = ttk.Label(frame, textvariable=status_var, font=("Arial", 9), foreground="gray")
        status_label.pack()
        
        return {
            'window': progress_window,
            'progress_var': progress_var,
            'progress_bar': progress_bar,
            'status_var': status_var
        }
    
    def run_transcript_download(self, selected_videos, language_codes, enable_speech, progress_window):
        """대본 다운로드 실행"""
        try:
            # Whisper 모델 로드 (음성 인식 사용시)
            if enable_speech:
                self.window.after(0, lambda: progress_window['progress_var'].set("Whisper 모델 로딩 중..."))
                self.window.after(0, lambda: progress_window['status_var'].set("AI 음성 인식 모델을 준비하고 있습니다..."))
                
                if not self.transcript_downloader.load_whisper_model("base"):
                    self.window.after(0, lambda: messagebox.showerror("오류", "Whisper 모델 로드에 실패했습니다."))
                    self.window.after(0, lambda: progress_window['window'].destroy())
                    return
            
            # 대본 다운로드
            downloaded_files = []
            failed_videos = []
            speech_recognized = 0
            
            for i, video in enumerate(selected_videos, 1):
                video_title = video['title'][:30] + "..." if len(video['title']) > 30 else video['title']
                progress_text = f"진행: {i}/{len(selected_videos)} - {video_title}"
                
                self.window.after(0, lambda t=progress_text: progress_window['progress_var'].set(t))
                self.window.after(0, lambda i=i: progress_window['progress_bar'].config(value=i))
                
                # 현재 작업 상태 표시
                if enable_speech:
                    status_text = "자막 확인 중..."
                    self.window.after(0, lambda s=status_text: progress_window['status_var'].set(s))
                
                # 대본 다운로드 시도
                result = self.transcript_downloader.download_transcript(
                    video['id'],
                    video['title'],
                    language_codes,
                    enable_speech_recognition=enable_speech
                )
                
                if result['success']:
                    downloaded_files.append(result['file_path'])
                    if result.get('method') == 'speech_recognition':
                        speech_recognized += 1
                else:
                    failed_videos.append(f"{video['title']}: {result.get('error', '알 수 없는 오류')}")
            
            # ZIP 파일 생성
            channel_name = self.selected_video['snippet']['channelTitle']
            zip_file = self.transcript_downloader.create_transcript_zip(channel_name)
            
            # 결과 표시
            self.window.after(0, lambda: self.show_download_results(
                len(selected_videos), len(downloaded_files), len(failed_videos), 
                speech_recognized, zip_file, failed_videos, progress_window, channel_name
            ))
            
        except Exception as e:
            error_msg = f"대본 다운로드 중 오류 발생: {str(e)}"
            self.window.after(0, lambda: messagebox.showerror("다운로드 오류", error_msg))
            self.window.after(0, lambda: progress_window['window'].destroy())
    
    def show_download_results(self, total, success, failed, speech_recognized, zip_file, failed_list, progress_window, channel_name):
        """다운로드 결과 표시"""
        progress_window['window'].destroy()
        
        result_msg = f"대본 다운로드 완료!\n\n"
        result_msg += f"채널: {channel_name}\n"
        result_msg += f"총 요청: {total}개\n"
        result_msg += f"성공: {success}개\n"
        result_msg += f"실패: {failed}개\n"
        
        if speech_recognized > 0:
            result_msg += f"음성 인식: {speech_recognized}개\n"
        
        if zip_file:
            result_msg += f"\n📦 ZIP 파일: {zip_file}"
        
        result_msg += f"\n📁 개별 파일: transcripts/ 폴더"
        
        if failed_list:
            result_msg += f"\n\n실패한 영상들:\n"
            for fail in failed_list[:3]:  # 최대 3개만 표시
                result_msg += f"• {fail}\n"
            if len(failed_list) > 3:
                result_msg += f"... 외 {len(failed_list) - 3}개 더"
        
        # 활용 팁 추가
        if success > 0:
            result_msg += f"\n\n💡 활용 팁:\n"
            result_msg += f"• 대본을 분석해서 성공 패턴 파악\n"
            result_msg += f"• 키워드 사용 빈도 및 화법 연구\n"
            result_msg += f"• 스토리텔링 구조 벤치마킹"
        
        messagebox.showinfo("다운로드 완료", result_msg)


def main():
    """메인 함수"""
    # tkinter 앱 생성
    root = tk.Tk()
    
    # 스타일 설정
    style = ttk.Style()
    style.theme_use('clam')
    
    # 앱 실행
    app = YouTubeTrendAnalyzerGUI(root)
    
    # 윈도우 아이콘 설정 (선택사항)
    try:
        root.iconbitmap('icon.ico')
    except:
        pass
    
    # 메인 루프 실행
    root.mainloop()

if __name__ == "__main__":
    main()