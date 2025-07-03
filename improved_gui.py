"""
YouTube 트렌드 분석기 GUI - macOS 스타일 디자인
- 세련된 macOS 스타일 UI
- 채널 분석 기능
- 대본/썸네일 다운로드
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, font
import threading
import os
import sys
from datetime import datetime, timedelta
import webbrowser
import queue
import concurrent.futures

# 프로젝트 모듈들
import config
from youtube_api import YouTubeAPIClient
from data_analyzer import DataAnalyzer
from excel_generator import ExcelGenerator


class ModernButton(tk.Canvas):
    """macOS 스타일 버튼"""
    def __init__(self, parent, text="", command=None, style="primary", **kwargs):
        super().__init__(parent, highlightthickness=0, **kwargs)
        
        self.command = command
        self.text = text
        self.style = style
        
        # 스타일별 색상
        self.colors = {
            "primary": {"bg": "#007AFF", "hover": "#0051D5", "fg": "white"},
            "secondary": {"bg": "#F2F2F7", "hover": "#E5E5EA", "fg": "#000000"},
            "danger": {"bg": "#FF3B30", "hover": "#D70015", "fg": "white"}
        }
        
        self.current_color = self.colors[style]["bg"]
        self.draw_button()
        
        # 이벤트 바인딩
        self.bind("<Enter>", self.on_hover)
        self.bind("<Leave>", self.on_leave)
        self.bind("<Button-1>", self.on_click)
        self.bind("<ButtonRelease-1>", self.on_release)
    
    def draw_button(self):
        self.delete("all")
        width = self.winfo_reqwidth() or 100
        height = self.winfo_reqheight() or 32
        
        # 둥근 모서리 버튼
        self.create_rounded_rectangle(2, 2, width-2, height-2, 
                                     radius=8, fill=self.current_color, 
                                     outline="", tags="button")
        
        # 텍스트
        self.create_text(width//2, height//2, text=self.text,
                        fill=self.colors[self.style]["fg"],
                        font=("SF Pro Display", 11, "bold"))
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius=8, **kwargs):
        points = []
        for x, y in [(x1, y1 + radius), (x1, y1), (x1 + radius, y1),
                     (x2 - radius, y1), (x2, y1), (x2, y1 + radius),
                     (x2, y2 - radius), (x2, y2), (x2 - radius, y2),
                     (x1 + radius, y2), (x1, y2), (x1, y2 - radius)]:
            points.extend([x, y])
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def on_hover(self, event):
        self.current_color = self.colors[self.style]["hover"]
        self.draw_button()
    
    def on_leave(self, event):
        self.current_color = self.colors[self.style]["bg"]
        self.draw_button()
    
    def on_click(self, event):
        self.move("all", 1, 1)
    
    def on_release(self, event):
        self.move("all", -1, -1)
        if self.command:
            self.command()


class ChannelAnalysisDialog(tk.Toplevel):
    """채널 분석 다이얼로그"""
    def __init__(self, parent, channel_id, channel_name, api_client):
        super().__init__(parent)
        
        self.title(f"채널 분석 - {channel_name}")
        self.geometry("1000x700")
        self.configure(bg="#F5F5F7")
        
        self.channel_id = channel_id
        self.channel_name = channel_name
        self.api_client = api_client
        self.channel_videos = []
        
        # macOS 스타일 설정
        self.setup_styles()
        
        # UI 생성
        self.create_widgets()
        
        # 채널 영상 로드
        self.load_channel_videos()
    
    def setup_styles(self):
        """macOS 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 트리뷰 스타일
        style.configure("Channel.Treeview",
                       background="white",
                       foreground="black",
                       fieldbackground="white",
                       borderwidth=0)
        style.configure("Channel.Treeview.Heading",
                       background="#F5F5F7",
                       foreground="black",
                       borderwidth=0,
                       relief="flat")
        style.map("Channel.Treeview",
                 background=[('selected', '#007AFF')],
                 foreground=[('selected', 'white')])
    
    def create_widgets(self):
        """위젯 생성"""
        # 헤더
        header_frame = tk.Frame(self, bg="white", height=60)
        header_frame.pack(fill=tk.X, padx=0, pady=(0, 1))
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text=f"📺 {self.channel_name}",
                font=("SF Pro Display", 18, "bold"),
                bg="white", fg="#1D1D1F").pack(side=tk.LEFT, padx=20, pady=15)
        
        # 영상 목록
        list_frame = tk.Frame(self, bg="white")
        list_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 컬럼 정의
        columns = ("선택", "업로드일", "제목", "조회수", "좋아요", "영상유형", "길이")
        
        self.tree = ttk.Treeview(list_frame, columns=columns, show="tree headings",
                                style="Channel.Treeview", height=20)
        
        # 체크박스 컬럼
        self.tree.column("#0", width=50, stretch=False)
        self.tree.heading("#0", text="✓")
        
        # 다른 컬럼들
        column_widths = {
            "선택": 0,  # 숨김
            "업로드일": 100,
            "제목": 400,
            "조회수": 100,
            "좋아요": 80,
            "영상유형": 80,
            "길이": 80
        }
        
        for col in columns:
            if col != "선택":
                self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 스크롤바
        vsb = ttk.Scrollbar(list_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 체크박스 이미지
        self.checked_img = self.create_checkbox_image(True)
        self.unchecked_img = self.create_checkbox_image(False)
        
        # 선택 상태 저장
        self.selected_items = set()
        
        # 클릭 이벤트
        self.tree.bind("<Button-1>", self.on_item_click)
        
        # 버튼 프레임
        button_frame = tk.Frame(self, bg="#F5F5F7", height=80)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM)
        button_frame.pack_propagate(False)
        
        # 버튼들을 담을 컨테이너
        button_container = tk.Frame(button_frame, bg="#F5F5F7")
        button_container.pack(expand=True)
        
        # 선택 버튼들
        select_frame = tk.Frame(button_container, bg="#F5F5F7")
        select_frame.pack(side=tk.LEFT, padx=10)
        
        ModernButton(select_frame, text="모두 선택", 
                    command=self.select_all, style="secondary",
                    width=100, height=32).pack(side=tk.LEFT, padx=5)
        
        ModernButton(select_frame, text="모두 해제", 
                    command=self.deselect_all, style="secondary",
                    width=100, height=32).pack(side=tk.LEFT, padx=5)
        
        # 다운로드 버튼들
        download_frame = tk.Frame(button_container, bg="#F5F5F7")
        download_frame.pack(side=tk.LEFT, padx=20)
        
        ModernButton(download_frame, text="썸네일 다운로드", 
                    command=self.download_thumbnails, style="primary",
                    width=140, height=32).pack(side=tk.LEFT, padx=5)
        
        ModernButton(download_frame, text="대본 다운로드", 
                    command=self.download_transcripts, style="primary",
                    width=140, height=32).pack(side=tk.LEFT, padx=5)
        
        # 닫기 버튼
        ModernButton(button_container, text="닫기", 
                    command=self.destroy, style="secondary",
                    width=80, height=32).pack(side=tk.RIGHT, padx=10)
        
        # 진행 상태
        self.progress_label = tk.Label(self, text="", 
                                     font=("SF Pro Display", 11),
                                     bg="#F5F5F7", fg="#86868B")
        self.progress_label.pack(pady=5)
    
    def create_checkbox_image(self, checked=False):
        """체크박스 이미지 생성"""
        img = tk.PhotoImage(width=16, height=16)
        
        if checked:
            # 체크된 상태
            for x in range(16):
                for y in range(16):
                    if x in [0, 15] or y in [0, 15]:
                        img.put("#007AFF", (x, y))
                    elif 3 <= x <= 6 and 7 <= y <= 10:
                        img.put("#007AFF", (x, y))
                    elif 7 <= x <= 12 and 4 <= y <= 9:
                        img.put("#007AFF", (x, y))
                    else:
                        img.put("#E5F1FF", (x, y))
        else:
            # 체크 안된 상태
            for x in range(16):
                for y in range(16):
                    if x in [0, 15] or y in [0, 15]:
                        img.put("#C0C0C0", (x, y))
                    else:
                        img.put("white", (x, y))
        
        return img
    
    def on_item_click(self, event):
        """아이템 클릭 처리"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "tree":
            item = self.tree.identify_row(event.y)
            if item:
                if item in self.selected_items:
                    self.selected_items.remove(item)
                    self.tree.item(item, image=self.unchecked_img)
                else:
                    self.selected_items.add(item)
                    self.tree.item(item, image=self.checked_img)
    
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
                                   values=("", upload_date, video['title'], 
                                          views, likes, video_type, duration),
                                   image=self.unchecked_img)
            
            # 영상 ID 저장
            self.tree.set(item, "video_id", video['id'])
        
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
            self.tree.item(item, image=self.checked_img)
    
    def deselect_all(self):
        """모두 해제"""
        for item in self.tree.get_children():
            if item in self.selected_items:
                self.selected_items.remove(item)
            self.tree.item(item, image=self.unchecked_img)
    
    def download_thumbnails(self):
        """선택한 영상의 썸네일 다운로드"""
        if not self.selected_items:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        # 선택된 영상 정보 수집
        thumbnails_to_download = []
        for item in self.selected_items:
            video_id = self.tree.set(item, "video_id")
            video_title = self.tree.item(item)['values'][2]
            
            # 썸네일 URL 찾기
            for video in self.channel_videos:
                if video['id'] == video_id:
                    thumbnails_to_download.append({
                        'video_id': video_id,
                        'title': video_title,
                        'thumbnail_url': video.get('thumbnail_url', '')
                    })
                    break
        
        if thumbnails_to_download:
            self.progress_label.config(text="썸네일 다운로드 중...")
            
            thread = threading.Thread(target=lambda: self._download_thumbnails(thumbnails_to_download))
            thread.daemon = True
            thread.start()
    
    def _download_thumbnails(self, thumbnails):
        """썸네일 다운로드 실행"""
        result = self.api_client.download_multiple_thumbnails(thumbnails)
        
        self.after(0, lambda: messagebox.showinfo("완료", 
            f"썸네일 다운로드 완료!\n"
            f"성공: {len(result.get('downloaded_files', []))}개\n"
            f"실패: {result.get('failed_count', 0)}개"))
        
        self.after(0, lambda: self.progress_label.config(text=""))
    
    def download_transcripts(self):
        """선택한 영상의 대본 다운로드"""
        if not self.selected_items:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        # 선택된 영상 ID 수집
        video_ids = []
        for item in self.selected_items:
            video_id = self.tree.set(item, "video_id")
            video_ids.append(video_id)
        
        if video_ids:
            self.progress_label.config(text="대본 다운로드 중...")
            
            thread = threading.Thread(target=lambda: self._download_transcripts(video_ids))
            thread.daemon = True
            thread.start()
    
    def _download_transcripts(self, video_ids):
        """대본 다운로드 실행"""
        try:
            # 대본 다운로드를 위한 transcript_downloader 모듈이 필요
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
        self.root.geometry("1300x850")
        
        # macOS 스타일 색상
        self.bg_color = "#F5F5F7"
        self.card_bg = "#FFFFFF"
        self.sidebar_bg = "#F2F2F7"
        self.accent_color = "#007AFF"
        self.text_primary = "#1D1D1F"
        self.text_secondary = "#86868B"
        
        self.root.configure(bg=self.bg_color)
        
        # 스타일 설정
        self.setup_styles()
        
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
        
        # GUI 구성
        self.create_widgets()
        
        # API 키 자동 로드
        self.load_api_key()
    
    def setup_styles(self):
        """macOS 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 전체 스타일
        style.configure('.',
                       background=self.bg_color,
                       foreground=self.text_primary,
                       borderwidth=0,
                       focuscolor='none')
        
        # 엔트리 스타일
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       borderwidth=0,
                       insertwidth=2,
                       relief='flat',
                       font=('SF Pro Display', 12))
        
        # 콤보박스 스타일
        style.configure('Modern.TCombobox',
                       fieldbackground='white',
                       borderwidth=0,
                       relief='flat',
                       arrowcolor=self.accent_color,
                       font=('SF Pro Display', 12))
        
        # 라벨프레임 스타일
        style.configure('Card.TLabelframe',
                       background=self.card_bg,
                       borderwidth=0,
                       relief='flat',
                       font=('SF Pro Display', 11, 'bold'))
        style.configure('Card.TLabelframe.Label',
                       background=self.card_bg,
                       foreground=self.text_primary)
        
        # 트리뷰 스타일
        style.configure("Modern.Treeview",
                       background="white",
                       foreground=self.text_primary,
                       fieldbackground="white",
                       borderwidth=0,
                       font=('SF Pro Display', 11))
        style.configure("Modern.Treeview.Heading",
                       background=self.sidebar_bg,
                       foreground=self.text_primary,
                       borderwidth=0,
                       relief="flat",
                       font=('SF Pro Display', 11, 'bold'))
        style.map("Modern.Treeview",
                 background=[('selected', self.accent_color)],
                 foreground=[('selected', 'white')])
    
    def create_card_frame(self, parent, **kwargs):
        """카드 스타일 프레임 생성"""
        frame = tk.Frame(parent, bg=self.card_bg, **kwargs)
        
        # 그림자 효과 (간단한 방식)
        shadow = tk.Frame(parent, bg="#E5E5E7", height=2)
        shadow.place(in_=frame, x=2, y=2, relwidth=1, relheight=1)
        
        return frame
    
    def create_widgets(self):
        """위젯 생성"""
        # 상단 헤더
        self.create_header()
        
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 왼쪽 사이드바 (설정)
        sidebar = self.create_card_frame(main_container, width=320)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        sidebar.pack_propagate(False)
        
        self.create_filters_section(sidebar)
        
        # 오른쪽 메인 영역 (결과)
        main_area = self.create_card_frame(main_container)
        main_area.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_results_section(main_area)
        
        # 하단 액션 바
        self.create_action_bar()
    
    def create_header(self):
        """상단 헤더"""
        header = tk.Frame(self.root, bg=self.card_bg, height=80)
        header.pack(fill=tk.X, padx=0, pady=(0, 20))
        header.pack_propagate(False)
        
        # 앱 타이틀
        title_frame = tk.Frame(header, bg=self.card_bg)
        title_frame.pack(side=tk.LEFT, padx=30, pady=20)
        
        tk.Label(title_frame, text="YouTube", 
                font=("SF Pro Display", 24, "bold"),
                bg=self.card_bg, fg=self.text_primary).pack(side=tk.LEFT)
        
        tk.Label(title_frame, text="DeepSearch", 
                font=("SF Pro Display", 24),
                bg=self.card_bg, fg=self.accent_color).pack(side=tk.LEFT, padx=(5, 0))
        
        # API 키 섹션
        api_frame = tk.Frame(header, bg=self.card_bg)
        api_frame.pack(side=tk.RIGHT, padx=30, pady=20)
        
        tk.Label(api_frame, text="API Key", 
                font=("SF Pro Display", 11),
                bg=self.card_bg, fg=self.text_secondary).pack(side=tk.LEFT, padx=(0, 10))
        
        self.api_entry = ttk.Entry(api_frame, font=('SF Pro Display', 11), 
                                  style='Modern.TEntry', width=35, show="*")
        self.api_entry.pack(side=tk.LEFT, padx=(0, 10))
        
        # 빠른 모드
        self.fast_mode_check = tk.Checkbutton(api_frame, text="빠른 분석",
                                             variable=self.fast_mode,
                                             bg=self.card_bg, fg=self.text_secondary,
                                             font=('SF Pro Display', 11),
                                             activebackground=self.card_bg,
                                             highlightthickness=0)
        self.fast_mode_check.pack(side=tk.LEFT)
    
    def create_filters_section(self, parent):
        """필터 설정 섹션"""
        # 섹션 타이틀
        tk.Label(parent, text="검색 필터",
                font=('SF Pro Display', 16, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(pady=(20, 15), padx=20)
        
        # 필터 컨테이너
        filters_container = tk.Frame(parent, bg=self.card_bg)
        filters_container.pack(fill=tk.BOTH, expand=True, padx=20)
        
        # 검색 키워드
        self.create_filter_group(filters_container, "검색 키워드", "entry")
        
        # 정렬 기준
        self.sort_var = tk.StringVar(value="관련성")
        self.create_filter_group(filters_container, "정렬 기준", "combo",
                               values=["관련성", "업로드 날짜", "조회수"],
                               variable=self.sort_var)
        
        # 업로드 기간
        self.period_var = tk.StringVar(value="일주일")
        self.create_filter_group(filters_container, "업로드 기간", "combo",
                               values=["오늘", "2일", "일주일", "한달", "3개월"],
                               variable=self.period_var)
        
        # 영상 유형
        self.video_type_var = tk.StringVar(value="전체")
        self.create_filter_group(filters_container, "영상 유형", "combo",
                               values=["전체", "쇼츠", "롱폼"],
                               variable=self.video_type_var)
        
        # 최소 조회수
        self.min_views_var = tk.StringVar(value="10,000")
        self.create_filter_group(filters_container, "최소 조회수", "combo",
                               values=["제한없음", "10,000", "100,000", "1,000,000"],
                               variable=self.min_views_var)
        
        # 최대 구독자 수
        self.max_subscribers_var = tk.StringVar(value="100,000")
        self.create_filter_group(filters_container, "최대 구독자 수", "combo",
                               values=["제한없음", "1,000", "10,000", "100,000"],
                               variable=self.max_subscribers_var)
        
        # 검색 버튼
        button_container = tk.Frame(parent, bg=self.card_bg)
        button_container.pack(fill=tk.X, side=tk.BOTTOM, pady=20, padx=20)
        
        self.search_button = ModernButton(button_container, text="검색 시작",
                                        command=self.start_analysis, style="primary",
                                        width=280, height=44)
        self.search_button.pack()
    
    def create_filter_group(self, parent, label, widget_type, **kwargs):
        """필터 그룹 생성"""
        group = tk.Frame(parent, bg=self.card_bg)
        group.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(group, text=label,
                font=('SF Pro Display', 11),
                bg=self.card_bg, fg=self.text_secondary).pack(anchor=tk.W, pady=(0, 5))
        
        if widget_type == "entry":
            self.keyword_entry = ttk.Entry(group, font=('SF Pro Display', 12),
                                         style='Modern.TEntry')
            self.keyword_entry.pack(fill=tk.X, ipady=6)
            self.keyword_entry.insert(0, "서울 카페")
            
        elif widget_type == "combo":
            combo = ttk.Combobox(group, textvariable=kwargs.get('variable'),
                               values=kwargs.get('values', []),
                               state="readonly", font=('SF Pro Display', 12),
                               style='Modern.TCombobox')
            combo.pack(fill=tk.X, ipady=6)
    
    def create_results_section(self, parent):
        """결과 표시 섹션"""
        # 헤더
        header_frame = tk.Frame(parent, bg=self.card_bg, height=60)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="검색 결과", 
                font=('SF Pro Display', 16, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(side=tk.LEFT, padx=20, pady=15)
        
        self.results_count_label = tk.Label(header_frame, text="", 
                                           font=('SF Pro Display', 12),
                                           bg=self.card_bg, fg=self.text_secondary)
        self.results_count_label.pack(side=tk.RIGHT, padx=20, pady=15)
        
        # 트리뷰
        tree_frame = tk.Frame(parent, bg=self.card_bg)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 컬럼 정의
        columns = ("순번", "업로드 날짜", "조회수", "제목", "채널", "좋아요 비율", "영상 유형")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", 
                                style="Modern.Treeview", height=20, selectmode="extended")
        
        # 컬럼 설정
        column_widths = {
            "순번": 50,
            "업로드 날짜": 100,
            "조회수": 100,
            "제목": 350,
            "채널": 150,
            "좋아요 비율": 100,
            "영상 유형": 80
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 스크롤바
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        vsb.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭 이벤트
        self.tree.bind("<Double-1>", self.on_video_double_click)
        
        # 진행 상태
        self.progress_label = tk.Label(parent, text="", 
                                      font=('SF Pro Display', 11),
                                      bg=self.card_bg, fg=self.text_secondary)
        self.progress_label.pack(pady=(0, 10))
    
    def create_action_bar(self):
        """하단 액션 바"""
        action_bar = tk.Frame(self.root, bg=self.sidebar_bg, height=70)
        action_bar.pack(fill=tk.X, side=tk.BOTTOM)
        action_bar.pack_propagate(False)
        
        # 버튼 컨테이너
        button_container = tk.Frame(action_bar, bg=self.sidebar_bg)
        button_container.pack(expand=True)
        
        # 액션 버튼들
        actions = [
            ("채널 분석", self.analyze_channel, "primary"),
            ("엑셀 추출", self.export_excel, "secondary"),
            ("영상 열기", self.open_video, "secondary"),
            ("썸네일 다운로드", self.download_thumbnails, "secondary")
        ]
        
        for text, command, style in actions:
            ModernButton(button_container, text=text, command=command, 
                        style=style, width=120, height=36).pack(side=tk.LEFT, padx=5)
    
    # 나머지 메서드들은 기존과 동일하되, 일부 수정 필요한 부분만 변경
    
    def analyze_channel(self):
        """선택한 영상의 채널 분석"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("알림", "채널을 분석할 영상을 선택해주세요.")
            return
        
        # 첫 번째 선택 항목의 채널 정보
        item = selection[0]
        index = int(self.tree.item(item)['values'][0]) - 1
        
        if 0 <= index < len(self.analyzed_videos):
            video = self.analyzed_videos[index]
            channel_id = video['snippet']['channelId']
            channel_name = video['snippet']['channelTitle']
            
            # 채널 분석 다이얼로그 열기
            dialog = ChannelAnalysisDialog(self.root, channel_id, channel_name, self.api_client)
            dialog.transient(self.root)
            dialog.grab_set()
    
    # 매핑 딕셔너리들
    def __init__(self, root):
        # ... 기존 __init__ 코드 ...
        
        # 매핑 추가
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
        
        # 나머지 초기화 코드
        super().__init__()
        self.root = root
        # ... 나머지 설정 ...
        
        # GUI 구성
        self.create_widgets()
        self.load_api_key()
    
    # 기존 메서드들 유지 (load_api_key, save_api_key, start_analysis 등)
    def load_api_key(self):
        """API 키 자동 로드"""
        if config.DEVELOPER_KEY and config.DEVELOPER_KEY != "YOUR_YOUTUBE_API_KEY_HERE":
            self.api_entry.insert(0, config.DEVELOPER_KEY)
    
    def save_api_key(self):
        """API 키 저장"""
        api_key = self.api_entry.get().strip()
        if api_key:
            config.DEVELOPER_KEY = api_key
            messagebox.showinfo("성공", "API 키가 저장되었습니다.")
    
    def start_analysis(self):
        """분석 시작"""
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("오류", "검색 키워드를 입력해주세요.")
            return
        
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("오류", "API 키를 입력해주세요.")
            return
        
        # 버튼 비활성화
        self.search_button.configure(state=tk.DISABLED)
        self.progress_label.config(text="검색 중...")
        
        # 기존 결과 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 캐시 초기화
        self.channel_cache = {}
        
        # 설정 준비
        settings = self.prepare_settings()
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.run_fast_analysis, args=(settings,))
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
    
    # 나머지 메서드들 (run_fast_analysis, quick_analyze_videos 등) 동일하게 유지
    def run_fast_analysis(self, settings):
        """빠른 분석 실행"""
        try:
            # API 클라이언트 초기화
            self.api_client = YouTubeAPIClient(self.api_entry.get().strip())
            self.analyzer = DataAnalyzer(language='ko')
            
            # 진행 상황 업데이트
            self.update_progress("영상 검색 중...")
            
            # 영상 검색
            videos = self.api_client.search_videos_by_keyword(
                keyword=settings['keyword'],
                region_code=settings['region'],
                max_results=settings['max_results'],
                max_subscriber_count=settings['max_subscribers'],
                min_view_count=settings['min_views'],
                period_days=settings['period_days'],
                video_type=settings['video_type'],
                order=settings['sort_by']
            )
            
            if not videos:
                self.update_progress("검색 결과가 없습니다.")
                self.root.after(0, lambda: self.search_button.configure(state=tk.NORMAL))
                return
            
            self.update_progress(f"{len(videos)}개 영상 발견...")
            
            # 빠른 모드에서는 채널 정보 스킵
            if settings['fast_mode']:
                analyzed_videos = self.quick_analyze_videos(videos)
            else:
                analyzed_videos = self.analyze_videos_parallel(videos, settings)
            
            # 결과 정렬
            if settings['sort_by'] == 'viewCount':
                analyzed_videos.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
            elif settings['sort_by'] == 'date':
                analyzed_videos.sort(key=lambda x: x['snippet']['publishedAt'], reverse=True)
            
            self.analyzed_videos = analyzed_videos
            self.current_settings = settings
            
            # UI 업데이트
            self.root.after(0, lambda: self.display_results(analyzed_videos))
            
        except Exception as e:
            self.update_progress(f"오류: {str(e)}")
            self.root.after(0, lambda: self.search_button.configure(state=tk.NORMAL))
    
    def quick_analyze_videos(self, videos):
        """빠른 분석 (채널 정보 없이)"""
        analyzed_videos = []
        
        for i, video in enumerate(videos):
            # 기본 분석만 수행
            video['analysis'] = {
                'engagement_rate': self.calculate_engagement_rate(video),
                'video_type': self.get_video_type(video)
            }
            video['rank'] = i + 1
            analyzed_videos.append(video)
            
            # 진행 상황 업데이트
            if i % 10 == 0:
                self.update_progress(f"분석 중... {i}/{len(videos)}")
        
        return analyzed_videos
    
    def analyze_videos_parallel(self, videos, settings):
        """병렬 처리로 영상 분석 (전체 분석)"""
        analyzed_videos = []
        total = len(videos)
        
        def analyze_single_video(video, index):
            try:
                channel_id = video['snippet']['channelId']
                
                # 채널 정보 (캐시 활용)
                if channel_id not in self.channel_cache:
                    channel_info = self.api_client.get_channel_info(channel_id)
                    if channel_info:
                        self.channel_cache[channel_id] = channel_info
                else:
                    channel_info = self.channel_cache[channel_id]
                
                # 분석 데이터
                video['analysis'] = {
                    'engagement_rate': self.calculate_engagement_rate(video),
                    'video_type': self.get_video_type(video),
                    'channel_subscribers': int(channel_info['statistics'].get('subscriberCount', 0)) if channel_info else 0
                }
                
                video['rank'] = index + 1
                return video
                
            except Exception as e:
                print(f"영상 분석 오류: {e}")
                return None
        
        # 병렬 처리
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for i, video in enumerate(videos):
                future = executor.submit(analyze_single_video, video, i)
                futures.append(future)
                
                if i % 10 == 0:
                    self.update_progress(f"상세 분석 중... {i}/{total}")
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    analyzed_videos.append(result)
        
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
            
            # 날짜 포맷
            published = snippet['publishedAt'][:10]
            
            # 조회수 포맷
            views = f"{int(stats.get('viewCount', 0)):,}"
            
            # 제목 축약
            title = snippet['title'][:50] + "..." if len(snippet['title']) > 50 else snippet['title']
            
            # 채널명
            channel = snippet['channelTitle']
            
            # 좋아요 비율
            engagement = f"{analysis.get('engagement_rate', 0)}%"
            
            # 영상 유형
            video_type = analysis.get('video_type', '알수없음')
            
            # 트리에 추가
            self.tree.insert("", tk.END, values=(
                i, published, views, title, channel, engagement, video_type
            ))
        
        # 결과 수 업데이트
        self.results_count_label.config(text=f"총 {len(videos)}개")
        self.progress_label.config(text="분석 완료!")
        self.search_button.configure(state=tk.NORMAL)
    
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
    
    def export_excel(self):
        """엑셀 내보내기"""
        if not self.analyzed_videos:
            messagebox.showwarning("알림", "내보낼 데이터가 없습니다.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
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
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("알림", "영상을 선택해주세요.")
            return
        
        for item in selection:
            index = int(self.tree.item(item)['values'][0]) - 1
            if 0 <= index < len(self.analyzed_videos):
                video_id = self.analyzed_videos[index]['id']
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(url)
    
    def download_thumbnails(self):
        """썸네일 다운로드"""
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
            if result['success']:
                messagebox.showinfo("성공", 
                    f"썸네일 다운로드 완료!\n"
                    f"성공: {len(result['downloaded_files'])}개\n"
                    f"실패: {result['failed_count']}개")
            else:
                messagebox.showerror("오류", result['error'])


def main():
    """메인 함수"""
    root = tk.Tk()
    app = ImprovedYouTubeAnalyzerGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()