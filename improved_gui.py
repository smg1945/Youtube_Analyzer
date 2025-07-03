"""
YouTube 트렌드 분석기 GUI - 안정화된 버전
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import webbrowser
import concurrent.futures
from datetime import datetime, timedelta

# 프로젝트 모듈들
import config
from youtube_api import YouTubeAPIClient
from data_analyzer import DataAnalyzer
from excel_generator import ExcelGenerator


class ChannelAnalysisDialog(tk.Toplevel):
    """채널 분석 다이얼로그"""
    def __init__(self, parent, channel_id, channel_name, api_client):
        super().__init__(parent)
        
        self.title(f"채널 분석 - {channel_name}")
        self.geometry("1000x700")
        self.configure(bg="#f0f0f0")
        
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.api_client = api_client
        self.channel_videos = []
        self.selected_items = set()
        
        # UI 생성
        self.create_widgets()
        
        # 채널 영상 로드
        self.load_channel_videos()
    
    def create_widgets(self):
        """위젯 생성"""
        # 헤더
        header_frame = tk.Frame(self, bg="white", height=60, relief='solid', bd=1)
        header_frame.pack(fill=tk.X, padx=10, pady=(10, 5))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"📺 {self.channel_name}",
                font=("Arial", 18, "bold"),
                bg="white", fg="#333333").pack(side=tk.LEFT, padx=20, pady=15)
        
        # 영상 목록 프레임
        list_frame = tk.Frame(self, bg="white", relief='solid', bd=1)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # 트리뷰
        columns = ("선택", "업로드일", "제목", "조회수", "좋아요", "영상유형", "길이")
        
        self.tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 설정
        column_widths = {
            "선택": 50,
            "업로드일": 100,
            "제목": 350,
            "조회수": 100,
            "좋아요": 80,
            "영상유형": 80,
            "길이": 80
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 스크롤바
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=20, pady=20)
        vsb.pack(side=tk.RIGHT, fill=tk.Y, pady=20)
        
        # 클릭 이벤트
        self.tree.bind("<Button-1>", self.on_item_click)
        
        # 버튼 프레임
        button_frame = tk.Frame(self, bg="#f0f0f0", height=80, relief='solid', bd=1)
        button_frame.pack(fill=tk.X, padx=10, pady=(5, 10))
        button_frame.pack_propagate(False)
        
        # 버튼 컨테이너
        button_container = tk.Frame(button_frame, bg="#f0f0f0")
        button_container.pack(expand=True)
        
        # 선택 버튼들
        tk.Button(button_container, text="모두 선택", 
                 command=self.select_all, bg="#e0e0e0", fg="black",
                 font=('Arial', 11), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(button_container, text="모두 해제", 
                 command=self.deselect_all, bg="#e0e0e0", fg="black",
                 font=('Arial', 11), padx=10, pady=5).pack(side=tk.LEFT, padx=5)
        
        # 다운로드 버튼들
        tk.Button(button_container, text="썸네일 다운로드", 
                 command=self.download_thumbnails, bg="#007AFF", fg="white",
                 font=('Arial', 11, 'bold'), padx=15, pady=5).pack(side=tk.LEFT, padx=20)
        
        tk.Button(button_container, text="대본 다운로드", 
                 command=self.download_transcripts, bg="#007AFF", fg="white",
                 font=('Arial', 11, 'bold'), padx=15, pady=5).pack(side=tk.LEFT, padx=5)
        
        # 닫기 버튼
        tk.Button(button_container, text="닫기", 
                 command=self.destroy, bg="#e0e0e0", fg="black",
                 font=('Arial', 11), padx=20, pady=5).pack(side=tk.RIGHT, padx=10)
        
        # 진행 상태
        self.progress_label = tk.Label(self, text="", 
                                     font=("Arial", 11),
                                     bg="#f0f0f0", fg="#666666")
        self.progress_label.pack(pady=5)
    
    def on_item_click(self, event):
        """아이템 클릭 처리"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            # 선택 컬럼 클릭 시 체크박스 토글
            if item and column == "#1":  # 첫 번째 컬럼
                if item in self.selected_items:
                    self.selected_items.remove(item)
                    values = list(self.tree.item(item)['values'])
                    values[0] = "☐"
                    self.tree.item(item, values=values)
                else:
                    self.selected_items.add(item)
                    values = list(self.tree.item(item)['values'])
                    values[0] = "☑"
                    self.tree.item(item, values=values)
    
    def load_channel_videos(self):
        """채널 영상 로드"""
        self.progress_label.config(text="채널 영상을 불러오는 중...")
        
        thread = threading.Thread(target=self._fetch_channel_videos)
        thread.daemon = True
        thread.start()
    
    def _fetch_channel_videos(self):
        """채널 영상 가져오기"""
        try:
            videos = self.api_client.get_channel_videos(self.channel_id, max_results=50)
            self.channel_videos = videos
            
            # UI 업데이트
            self.after(0, self._display_videos)
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("오류", f"채널 영상 로드 실패: {str(e)}"))
    
    def _display_videos(self):
        """영상 목록 표시"""
        for video in self.channel_videos:
            # 날짜 포맷
            upload_date = video.get('published_at', '')[:10]
            
            # 조회수/좋아요 포맷
            views = f"{video.get('view_count', 0):,}"
            likes = f"{video.get('like_count', 0):,}"
            
            # 영상 유형과 길이
            duration_seconds = self.api_client.parse_duration(video.get('duration', 'PT0S'))
            video_type = "쇼츠" if duration_seconds <= 60 else "롱폼"
            duration = self.format_duration(duration_seconds)
            
            # 트리에 추가
            item = self.tree.insert("", tk.END, 
                                   values=("☐", upload_date, video['title'], 
                                          views, likes, video_type, duration))
        
        self.progress_label.config(text=f"총 {len(self.channel_videos)}개 영상")
    
    def format_duration(self, seconds):
        """초를 시:분:초 형식으로 변환"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes}:{secs:02d}"
    
    def select_all(self):
        """모두 선택"""
        for item in self.tree.get_children():
            self.selected_items.add(item)
            values = list(self.tree.item(item)['values'])
            values[0] = "☑"
            self.tree.item(item, values=values)
    
    def deselect_all(self):
        """모두 해제"""
        for item in self.tree.get_children():
            if item in self.selected_items:
                self.selected_items.remove(item)
            values = list(self.tree.item(item)['values'])
            values[0] = "☐"
            self.tree.item(item, values=values)
    
    def download_thumbnails(self):
        """선택한 영상의 썸네일 다운로드"""
        if not self.selected_items:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        # 선택된 영상 정보 수집
        thumbnails_to_download = []
        for item in self.selected_items:
            item_values = self.tree.item(item)['values']
            video_title = item_values[2]
            
            # 영상 ID 찾기 (실제로는 인덱스로 찾아야 함)
            item_index = list(self.tree.get_children()).index(item)
            if item_index < len(self.channel_videos):
                video = self.channel_videos[item_index]
                thumbnails_to_download.append({
                    'video_id': video['id'],
                    'title': video_title,
                    'thumbnail_url': video.get('thumbnail_url', '')
                })
        
        if thumbnails_to_download:
            self.progress_label.config(text="썸네일 다운로드 중...")
            
            thread = threading.Thread(target=lambda: self._download_thumbnails(thumbnails_to_download))
            thread.daemon = True
            thread.start()
    
    def _download_thumbnails(self, thumbnails):
        """썸네일 다운로드 실행"""
        try:
            result = self.api_client.download_multiple_thumbnails(thumbnails)
            
            self.after(0, lambda: messagebox.showinfo("완료", 
                f"썸네일 다운로드 완료!\n"
                f"성공: {len(result.get('downloaded_files', []))}개\n"
                f"실패: {result.get('failed_count', 0)}개"))
            
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("오류", f"썸네일 다운로드 실패: {str(e)}"))
        
        self.after(0, lambda: self.progress_label.config(text=""))
    
    def download_transcripts(self):
        """선택한 영상의 대본 다운로드"""
        if not self.selected_items:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        # 선택된 영상 ID 수집
        video_ids = []
        for item in self.selected_items:
            item_index = list(self.tree.get_children()).index(item)
            if item_index < len(self.channel_videos):
                video = self.channel_videos[item_index]
                video_ids.append(video['id'])
        
        if video_ids:
            self.progress_label.config(text="대본 다운로드 중...")
            
            thread = threading.Thread(target=lambda: self._download_transcripts(video_ids))
            thread.daemon = True
            thread.start()
    
    def _download_transcripts(self, video_ids):
        """대본 다운로드 실행"""
        try:
            # 대본 다운로드를 위한 transcript_downloader 모듈이 필요
            try:
                from transcript_downloader import TranscriptDownloader
                downloader = TranscriptDownloader()
                
                success_count = 0
                fail_count = 0
                
                for video_id in video_ids:
                    try:
                        downloader.download_transcript(video_id)
                        success_count += 1
                    except:
                        fail_count += 1
                
                self.after(0, lambda: messagebox.showinfo("완료", 
                    f"대본 다운로드 완료!\n"
                    f"성공: {success_count}개\n"
                    f"실패: {fail_count}개"))
                
            except ImportError:
                self.after(0, lambda: messagebox.showerror("오류", 
                    "대본 다운로드 기능은 transcript_downloader 모듈이 필요합니다."))
                
        except Exception as e:
            self.after(0, lambda: messagebox.showerror("오류", f"대본 다운로드 실패: {str(e)}"))
        
        self.after(0, lambda: self.progress_label.config(text=""))


class ImprovedYouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube DeepSearch - 콘텐츠 분석 툴")
        self.root.geometry("1200x800")
        
        # 색상 설정
        self.bg_color = "#f0f0f0"
        self.card_bg = "#ffffff"
        self.accent_color = "#007AFF"
        self.text_primary = "#333333"
        self.text_secondary = "#666666"
        
        self.root.configure(bg=self.bg_color)
        
        # 매핑 딕셔너리
        self.sort_mapping = {
            "관련성": "relevance",
            "업로드 날짜": "date", 
            "조회수": "viewCount"
        }
        
        self.period_mapping = {
            "오늘": "1",
            "2일": "2", 
            "일주일": "7",
            "한달": "30",
            "3개월": "90"
        }
        
        self.type_mapping = {
            "전체": "all",
            "쇼츠": "shorts",
            "롱폼": "long"
        }
        
        # 분석 관련 객체들
        self.api_client = None
        self.analyzer = None
        self.excel_generator = None
        
        # 분석 결과 저장
        self.analyzed_videos = []
        self.current_settings = {}
        
        # 캐시
        self.channel_cache = {}
        
        # 빠른 모드 옵션
        self.fast_mode = tk.BooleanVar(value=True)
        
        # GUI 생성
        self.create_widgets()
        
        # API 키 자동 로드
        self.load_api_key()
    
    def create_widgets(self):
        """위젯 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 상단 헤더
        self.create_header(main_frame)
        
        # 메인 컨테이너 (좌우 분할)
        content_frame = tk.Frame(main_frame, bg=self.bg_color)
        content_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 왼쪽 사이드바
        sidebar = tk.Frame(content_frame, bg=self.card_bg, width=300, relief='solid', bd=1)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        sidebar.pack_propagate(False)
        
        self.create_sidebar(sidebar)
        
        # 오른쪽 메인 영역
        main_area = tk.Frame(content_frame, bg=self.card_bg, relief='solid', bd=1)
        main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_main_area(main_area)
        
        # 하단 액션 바
        self.create_action_bar(main_frame)
    
    def create_header(self, parent):
        """상단 헤더"""
        header = tk.Frame(parent, bg=self.card_bg, height=80, relief='solid', bd=1)
        header.pack(fill=tk.X, pady=(0, 10))
        header.pack_propagate(False)
        
        # 제목
        title_frame = tk.Frame(header, bg=self.card_bg)
        title_frame.pack(side=tk.LEFT, padx=20, pady=20)
        
        tk.Label(title_frame, text="YouTube DeepSearch", 
                font=("Arial", 20, "bold"),
                bg=self.card_bg, fg=self.accent_color).pack()
        
        # API 키 입력
        api_frame = tk.Frame(header, bg=self.card_bg)
        api_frame.pack(side=tk.RIGHT, padx=20, pady=20)
        
        tk.Label(api_frame, text="API Key:", 
                font=("Arial", 10),
                bg=self.card_bg, fg=self.text_secondary).pack(side=tk.LEFT)
        
        self.api_entry = tk.Entry(api_frame, font=('Arial', 10), 
                                 width=30, show="*")
        self.api_entry.pack(side=tk.LEFT, padx=10)
        
        # 빠른 모드 체크박스
        tk.Checkbutton(api_frame, text="빠른 분석",
                      variable=self.fast_mode,
                      bg=self.card_bg, font=('Arial', 10)).pack(side=tk.LEFT, padx=10)
    
    def create_sidebar(self, parent):
        """사이드바 생성"""
        # 제목
        tk.Label(parent, text="검색 필터", 
                font=('Arial', 16, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(pady=20)
        
        # 필터 컨테이너 (스크롤 제거하고 직접 배치)
        filters_frame = tk.Frame(parent, bg=self.card_bg)
        filters_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # 필터 추가
        self.create_filters(filters_frame)
        
        # 검색 버튼 - 더 크고 눈에 띄게
        button_frame = tk.Frame(parent, bg=self.card_bg)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=20)
        
        self.search_button = tk.Button(button_frame, text="🔍 검색 시작",
                                     command=self.start_analysis,
                                     bg=self.accent_color, fg="white",
                                     font=('Arial', 14, 'bold'),
                                     pady=15, relief='raised', bd=2)
        self.search_button.pack(fill=tk.X)
    
    def create_filters(self, parent):
        """필터 생성"""
        # 검색 키워드
        keyword_frame = tk.Frame(parent, bg=self.card_bg)
        keyword_frame.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(keyword_frame, text="🔍 검색 키워드", 
                font=('Arial', 12, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.keyword_entry = tk.Entry(keyword_frame, font=('Arial', 12), relief='solid', bd=1)
        self.keyword_entry.pack(fill=tk.X, ipady=8)
        self.keyword_entry.insert(0, "서울 카페")
        
        # 입력 힌트
        tk.Label(keyword_frame, text="예: 맛집, 여행, vlog, 게임 등", 
                font=('Arial', 9),
                bg=self.card_bg, fg=self.text_secondary).pack(anchor=tk.W, pady=(2, 0))
        
        # 정렬 기준
        sort_frame = tk.Frame(parent, bg=self.card_bg)
        sort_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(sort_frame, text="📊 정렬 기준", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.sort_var = tk.StringVar(value="관련성")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                 values=["관련성", "업로드 날짜", "조회수"],
                                 state="readonly", font=('Arial', 11))
        sort_combo.pack(fill=tk.X)
        
        # 업로드 기간
        period_frame = tk.Frame(parent, bg=self.card_bg)
        period_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(period_frame, text="📅 업로드 기간", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.period_var = tk.StringVar(value="일주일")
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var,
                                   values=["오늘", "2일", "일주일", "한달", "3개월"],
                                   state="readonly", font=('Arial', 11))
        period_combo.pack(fill=tk.X)
        
        # 영상 유형
        type_frame = tk.Frame(parent, bg=self.card_bg)
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(type_frame, text="🎬 영상 유형", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.video_type_var = tk.StringVar(value="전체")
        type_combo = ttk.Combobox(type_frame, textvariable=self.video_type_var,
                                 values=["전체", "쇼츠", "롱폼"],
                                 state="readonly", font=('Arial', 11))
        type_combo.pack(fill=tk.X)
        
        # 최소 조회수
        views_frame = tk.Frame(parent, bg=self.card_bg)
        views_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(views_frame, text="👀 최소 조회수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.min_views_var = tk.StringVar(value="10,000")
        views_combo = ttk.Combobox(views_frame, textvariable=self.min_views_var,
                                  values=["제한없음", "10,000", "100,000", "1,000,000"],
                                  state="readonly", font=('Arial', 11))
        views_combo.pack(fill=tk.X)
        
        # 최대 구독자 수
        subs_frame = tk.Frame(parent, bg=self.card_bg)
        subs_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(subs_frame, text="👥 최대 구독자 수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.max_subscribers_var = tk.StringVar(value="100,000")
        subs_combo = ttk.Combobox(subs_frame, textvariable=self.max_subscribers_var,
                                 values=["제한없음", "1,000", "10,000", "100,000"],
                                 state="readonly", font=('Arial', 11))
        subs_combo.pack(fill=tk.X)
    
    def create_main_area(self, parent):
        """메인 영역 생성"""
        # 헤더
        header_frame = tk.Frame(parent, bg=self.card_bg, height=50)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="검색 결과", 
                font=('Arial', 16, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(side=tk.LEFT, padx=20, pady=15)
        
        self.results_count_label = tk.Label(header_frame, text="", 
                                           font=('Arial', 12),
                                           bg=self.card_bg, fg=self.text_secondary)
        self.results_count_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # 트리뷰 프레임
        tree_frame = tk.Frame(parent, bg=self.card_bg)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 트리뷰 생성
        columns = ("순번", "업로드 날짜", "조회수", "제목", "채널", "좋아요 비율", "영상 유형")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 설정
        column_widths = {"순번": 50, "업로드 날짜": 100, "조회수": 100, 
                        "제목": 300, "채널": 150, "좋아요 비율": 100, "영상 유형": 80}
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 스크롤바
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # 레이아웃
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭 이벤트
        self.tree.bind("<Double-1>", self.on_video_double_click)
        
        # 진행 상태 라벨
        self.progress_label = tk.Label(parent, text="", 
                                      font=('Arial', 11),
                                      bg=self.card_bg, fg=self.text_secondary)
        self.progress_label.pack(pady=10)
    
    def create_action_bar(self, parent):
        """액션 바 생성"""
        action_frame = tk.Frame(parent, bg=self.card_bg, height=60, relief='solid', bd=1)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        action_frame.pack_propagate(False)
        
        # 버튼들
        button_frame = tk.Frame(action_frame, bg=self.card_bg)
        button_frame.pack(expand=True)
        
        actions = [
            ("채널 분석", self.analyze_channel),
            ("엑셀 추출", self.export_excel),
            ("영상 열기", self.open_video),
            ("썸네일 다운로드", self.download_thumbnails)
        ]
        
        for text, command in actions:
            btn = tk.Button(button_frame, text=text, command=command,
                           bg=self.accent_color, fg="white",
                           font=('Arial', 11, 'bold'),
                           padx=15, pady=8)
            btn.pack(side=tk.LEFT, padx=5)
    
    def load_api_key(self):
        """API 키 자동 로드"""
        if config.DEVELOPER_KEY and config.DEVELOPER_KEY != "YOUR_YOUTUBE_API_KEY_HERE":
            self.api_entry.insert(0, config.DEVELOPER_KEY)
    
    def start_analysis(self):
        """분석 시작"""
        # 입력값 검증
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("입력 오류", "검색 키워드를 입력해주세요.")
            return
        
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("API 키 오류", "YouTube API 키를 입력해주세요.")
            return
        
        if api_key == "YOUR_YOUTUBE_API_KEY_HERE":
            messagebox.showwarning("API 키 오류", "유효한 YouTube API 키를 입력해주세요.")
            return
        
        # 버튼 비활성화
        self.search_button.configure(state='disabled', text="🔍 검색 중...")
        self.progress_label.config(text="🚀 검색을 시작합니다...")
        
        # 기존 결과 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        self.results_count_label.config(text="")
        
        # 캐시 초기화
        self.channel_cache = {}
        
        # 설정 준비
        try:
            settings = self.prepare_settings()
        except Exception as e:
            messagebox.showerror("설정 오류", f"설정 준비 중 오류가 발생했습니다: {str(e)}")
            self.reset_search_button()
            return
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.run_analysis, args=(settings,))
        thread.daemon = True
        thread.start()
    
    def prepare_settings(self):
        """설정 준비"""
        # 최소 조회수 파싱
        min_views_text = self.min_views_var.get()
        min_views = 0 if min_views_text == "제한없음" else int(min_views_text.replace(",", ""))
        
        # 최대 구독자 수 파싱
        max_subscribers_text = self.max_subscribers_var.get()
        max_subscribers = None if max_subscribers_text == "제한없음" else int(max_subscribers_text.replace(",", ""))
        
        return {
            'keyword': self.keyword_entry.get().strip(),
            'min_views': min_views,
            'max_subscribers': max_subscribers,
            'period_days': int(self.period_mapping[self.period_var.get()]),
            'video_type': self.type_mapping[self.video_type_var.get()],
            'sort_by': self.sort_mapping[self.sort_var.get()],
            'region': 'KR',
            'max_results': 100 if self.fast_mode.get() else 200,
            'fast_mode': self.fast_mode.get()
        }
    
    def run_analysis(self, settings):
        """분석 실행"""
        try:
            # API 클라이언트 초기화
            self.update_progress("🔧 API 클라이언트를 초기화하고 있습니다...")
            self.api_client = YouTubeAPIClient(self.api_entry.get().strip())
            self.analyzer = DataAnalyzer(language='ko')
            
            # API 연결 테스트
            self.update_progress("🔗 API 연결을 테스트하고 있습니다...")
            if not self.api_client.test_api_connection():
                self.update_progress("❌ API 연결 테스트 실패. API 키를 확인해주세요.")
                self.root.after(0, self.reset_search_button)
                return
            
            # 진행 상황 업데이트
            self.update_progress("🔍 YouTube에서 영상을 검색하고 있습니다...")
            
            # 영상 검색
            videos = self.api_client.search_videos_by_keyword(
                keyword=settings['keyword'],
                region_code=settings['region'],
                max_results=settings['max_results'],
                max_subscriber_count=settings['max_subscribers'],
                min_view_count=settings['min_views'],
                period_days=settings['period_days'],
                video_type=settings['video_type']
                # order 매개변수는 메서드 내부에서 처리
            )
            
            if not videos:
                self.update_progress("❌ 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
                self.root.after(0, self.reset_search_button)
                return
            
            self.update_progress(f"✅ {len(videos)}개 영상 발견! 분석을 시작합니다...")
            
            # 간단한 분석
            analyzed_videos = self.quick_analyze_videos(videos)
            
            # 결과 정렬 (GUI에서 직접 처리)
            if settings['sort_by'] == 'viewCount':
                analyzed_videos.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
            elif settings['sort_by'] == 'date':
                analyzed_videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
            # 'relevance'는 기본 검색 순서 유지
            
            self.analyzed_videos = analyzed_videos
            self.current_settings = settings
            
            # UI 업데이트
            self.root.after(0, lambda: self.display_results(analyzed_videos))
            
        except Exception as e:
            error_msg = str(e)
            if "quotaExceeded" in error_msg:
                self.update_progress("❌ API 할당량 초과. 내일 다시 시도해주세요.")
            elif "keyInvalid" in error_msg:
                self.update_progress("❌ 잘못된 API 키. 올바른 키를 입력해주세요.")
            else:
                self.update_progress(f"❌ 오류: {error_msg}")
            self.root.after(0, self.reset_search_button)
    
    def quick_analyze_videos(self, videos):
        """빠른 분석"""
        analyzed_videos = []
        
        for i, video in enumerate(videos):
            # 기본 분석
            video['analysis'] = {
                'engagement_rate': self.calculate_engagement_rate(video),
                'video_type': self.get_video_type(video)
            }
            video['rank'] = i + 1
            analyzed_videos.append(video)
            
            # 진행 상황 업데이트
            if i % 10 == 0:
                self.update_progress(f"📊 분석 진행: {i+1}/{len(videos)} ({((i+1)/len(videos)*100):.0f}%)")
        
        return analyzed_videos
    
    def calculate_engagement_rate(self, video):
        """좋아요 비율 계산"""
        try:
            views = int(video['statistics'].get('viewCount', 0))
            likes = int(video['statistics'].get('likeCount', 0))
            
            if views == 0:
                return 0.0
            
            return round((likes / views) * 100, 2)
        except:
            return 0.0
    
    def get_video_type(self, video):
        """영상 유형 판별"""
        try:
            duration_str = video['contentDetails']['duration']
            duration_seconds = self.api_client.parse_duration(duration_str)
            
            if duration_seconds <= 60:
                return "쇼츠"
            else:
                return "롱폼"
        except:
            return "알수없음"
    
    def update_progress(self, message):
        """진행 상황 업데이트"""
        self.root.after(0, lambda: self.progress_label.config(text=message))
    
    def reset_search_button(self):
        """검색 버튼 리셋"""
        self.search_button.configure(state='normal', text="🔍 검색 시작")
    
    def display_results(self, videos):
        """결과 표시"""
        # 기존 항목 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 새 항목 추가
        for i, video in enumerate(videos, 1):
            snippet = video['snippet']
            stats = video['statistics']
            analysis = video.get('analysis', {})
            
            # 데이터 포맷
            published = snippet['publishedAt'][:10]
            views = f"{int(stats.get('viewCount', 0)):,}"
            title = snippet['title'][:40] + "..." if len(snippet['title']) > 40 else snippet['title']
            channel = snippet['channelTitle']
            engagement = f"{analysis.get('engagement_rate', 0)}%"
            video_type = analysis.get('video_type', '알수없음')
            
            # 트리에 추가
            self.tree.insert("", tk.END, values=(
                i, published, views, title, channel, engagement, video_type
            ))
        
        # 상태 업데이트
        self.results_count_label.config(text=f"총 {len(videos)}개 영상")
        self.progress_label.config(text="🎉 분석 완료! 결과를 확인하세요.")
        self.reset_search_button()
    
    def on_video_double_click(self, event):
        """영상 더블클릭"""
        selection = self.tree.selection()
        if selection:
            item = self.tree.item(selection[0])
            index = int(item['values'][0]) - 1
            
            if 0 <= index < len(self.analyzed_videos):
                video_id = self.analyzed_videos[index]['id']
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(url)
    
    def analyze_channel(self):
        """채널 분석"""
        if not self.api_client:
            messagebox.showwarning("알림", "먼저 검색을 실행해주세요.")
            return
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("알림", "채널을 분석할 영상을 선택해주세요.")
            return
        
        # 첫 번째 선택 항목의 채널 정보
        item = self.tree.item(selection[0])
        index = int(item['values'][0]) - 1
        
        if 0 <= index < len(self.analyzed_videos):
            video = self.analyzed_videos[index]
            channel_id = video['snippet']['channelId']
            channel_name = video['snippet']['channelTitle']
            
            # 채널 분석 다이얼로그 열기
            dialog = ChannelAnalysisDialog(self.root, channel_id, channel_name, self.api_client)
            dialog.transient(self.root)
            dialog.grab_set()
    
    def export_excel(self):
        """엑셀 내보내기"""
        if not self.analyzed_videos:
            messagebox.showwarning("알림", "먼저 검색을 실행하여 분석 데이터를 생성해주세요.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="엑셀 파일 저장 위치 선택"
        )
        
        if filename:
            try:
                excel_gen = ExcelGenerator(filename)
                excel_gen.create_excel_file(self.analyzed_videos, self.current_settings)
                messagebox.showinfo("성공", f"엑셀 파일이 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("오류", f"엑셀 저장 실패: {str(e)}")
    
    def open_video(self):
        """영상 열기"""
        if not self.analyzed_videos:
            messagebox.showwarning("알림", "먼저 검색을 실행해주세요.")
            return
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("알림", "열어볼 영상을 선택해주세요.")
            return
        
        for item in selection:
            index = int(self.tree.item(item)['values'][0]) - 1
            if 0 <= index < len(self.analyzed_videos):
                video_id = self.analyzed_videos[index]['id']
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(url)
    
    def download_thumbnails(self):
        """썸네일 다운로드"""
        if not self.api_client:
            messagebox.showwarning("알림", "먼저 검색을 실행해주세요.")
            return
        
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        # 선택된 영상들의 썸네일 정보 수집
        thumbnails_to_download = []
        for item in selection:
            index = int(self.tree.item(item)['values'][0]) - 1
            if 0 <= index < len(self.analyzed_videos):
                video = self.analyzed_videos[index]
                thumbnail_url = self.api_client.get_best_thumbnail_url(
                    video['snippet']['thumbnails']
                )
                if thumbnail_url:
                    thumbnails_to_download.append({
                        'video_id': video['id'],
                        'title': video['snippet']['title'],
                        'thumbnail_url': thumbnail_url,
                        'rank': index + 1
                    })
        
        if thumbnails_to_download:
            result = self.api_client.download_multiple_thumbnails(thumbnails_to_download)
            if result.get('success'):
                messagebox.showinfo("성공", 
                    f"썸네일 다운로드 완료!\n"
                    f"성공: {len(result.get('downloaded_files', []))}개\n"
                    f"실패: {result.get('failed_count', 0)}개")
            else:
                messagebox.showerror("오류", result.get('error', '다운로드 실패'))


def main():
    """메인 함수"""
    root = tk.Tk()
    app = ImprovedYouTubeAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()