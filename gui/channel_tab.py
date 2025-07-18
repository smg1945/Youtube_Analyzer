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
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.input_method_var = tk.StringVar(value="url")
        
        # URL 라디오 버튼
        url_radio = tk.Radiobutton(
            method_frame,
            text="채널 URL",
            variable=self.input_method_var,
            value="url",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f',
            command=self.on_input_method_changed
        )
        url_radio.pack(side='left', padx=(20, 10))
        
        # ID 라디오 버튼
        id_radio = tk.Radiobutton(
            method_frame,
            text="채널 ID",
            variable=self.input_method_var,
            value="id",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f',
            command=self.on_input_method_changed
        )
        id_radio.pack(side='left', padx=(0, 10))
        
        # 검색 라디오 버튼
        search_radio = tk.Radiobutton(
            method_frame,
            text="채널명 검색",
            variable=self.input_method_var,
            value="search",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f',
            command=self.on_input_method_changed
        )
        search_radio.pack(side='left')
        
        # 채널 입력
        channel_input_frame = tk.Frame(input_frame, bg='#f5f5f7')
        channel_input_frame.pack(fill='x', pady=(0, 10))
        
        self.channel_label = tk.Label(
            channel_input_frame,
            text="채널 URL:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        self.channel_label.pack(side='left')
        
        self.channel_var = tk.StringVar()
        self.channel_entry = tk.Entry(
            channel_input_frame,
            textvariable=self.channel_var,
            font=('SF Pro Display', 11),
            width=50
        )
        self.channel_entry.pack(side='left', padx=(10, 10), fill='x', expand=True)
        
        # 채널 검색 버튼 (검색 모드일 때만 표시)
        self.search_btn = tk.Button(
            channel_input_frame,
            text="🔍 검색",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            relief='flat',
            padx=15,
            pady=5,
            command=self.search_channel
        )
        # 초기에는 숨김
        
        # 예시 텍스트
        self.example_label = tk.Label(
            input_frame,
            text="예시: https://www.youtube.com/channel/UCxxxxxxxxxxxxxxx",
            font=('SF Pro Display', 9),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.example_label.pack(anchor='w')
    
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
        videos_frame = tk.Frame(row1_frame, bg='#f5f5f7')
        videos_frame.pack(side='left', padx=(0, 30))
        
        tk.Label(
            videos_frame,
            text="분석할 영상 수:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.max_videos_var = tk.StringVar(value="50")
        videos_entry = tk.Entry(
            videos_frame,
            textvariable=self.max_videos_var,
            font=('SF Pro Display', 11),
            width=10
        )
        videos_entry.pack(side='left', padx=(10, 0))
        
        # 정렬 기준
        sort_frame = tk.Frame(row1_frame, bg='#f5f5f7')
        sort_frame.pack(side='left')
        
        tk.Label(
            sort_frame,
            text="정렬 기준:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left')
        
        self.sort_var = tk.StringVar(value="date")
        sort_combo = ttk.Combobox(
            sort_frame,
            textvariable=self.sort_var,
            values=["date", "viewCount", "relevance"],
            state="readonly",
            width=12
        )
        sort_combo.pack(side='left', padx=(10, 0))
        
        # 두 번째 행
        row2_frame = tk.Frame(settings_frame, bg='#f5f5f7')
        row2_frame.pack(fill='x')
        
        # 분석 옵션 체크박스들
        self.include_shorts_var = tk.BooleanVar(value=True)
        shorts_check = tk.Checkbutton(
            row2_frame,
            text="쇼츠 포함",
            variable=self.include_shorts_var,
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        shorts_check.pack(side='left', padx=(0, 20))
        
        self.detailed_analysis_var = tk.BooleanVar(value=True)
        detailed_check = tk.Checkbutton(
            row2_frame,
            text="상세 분석",
            variable=self.detailed_analysis_var,
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        detailed_check.pack(side='left', padx=(0, 20))
        
        self.cache_enabled_var = tk.BooleanVar(value=True)
        cache_check = tk.Checkbutton(
            row2_frame,
            text="캐시 사용",
            variable=self.cache_enabled_var,
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        cache_check.pack(side='left')
    
    def create_action_area(self, parent):
        """액션 및 진행률 영역"""
        action_frame = tk.Frame(parent, bg='#f5f5f7')
        action_frame.pack(fill='x')
        
        # 버튼들
        button_frame = tk.Frame(action_frame, bg='#f5f5f7')
        button_frame.pack(fill='x', pady=(0, 15))
        
        # 분석 시작 버튼
        self.analyze_btn = tk.Button(
            button_frame,
            text="📊 분석 시작",
            font=('SF Pro Display', 12, 'bold'),
            bg='#007aff',
            fg='white',
            relief='flat',
            padx=30,
            pady=12,
            command=self.start_analysis
        )
        self.analyze_btn.pack(side='left', padx=(0, 10))
        
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
            command=self.stop_analysis,
            state='disabled'
        )
        self.stop_btn.pack(side='left', padx=(0, 10))
        
        # 채널 미리보기 버튼
        self.preview_btn = tk.Button(
            button_frame,
            text="👁️ 미리보기",
            font=('SF Pro Display', 12),
            bg='#34c759',
            fg='white',
            relief='flat',
            padx=20,
            pady=12,
            command=self.preview_channel
        )
        self.preview_btn.pack(side='left')
        
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
    
    def create_results_area(self, parent):
        """결과 영역 생성 (초기에는 숨김)"""
        self.results_frame = tk.LabelFrame(
            parent,
            text="📈 분석 결과",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        # 초기에는 pack하지 않음
    
    def on_input_method_changed(self):
        """입력 방법 변경 시 호출"""
        method = self.input_method_var.get()
        
        if method == "url":
            self.channel_label.config(text="채널 URL:")
            self.example_label.config(text="예시: https://www.youtube.com/channel/UCxxxxxxxxxxxxxxx")
            self.search_btn.pack_forget()
        elif method == "id":
            self.channel_label.config(text="채널 ID:")
            self.example_label.config(text="예시: UCxxxxxxxxxxxxxxx")
            self.search_btn.pack_forget()
        elif method == "search":
            self.channel_label.config(text="채널명:")
            self.example_label.config(text="예시: 김미쿡, 크크크크, 승우아빠")
            self.search_btn.pack(side='right', padx=(5, 0))
        
        # 입력창 초기화
        self.channel_var.set("")
    
    def search_channel(self):
        """채널명으로 채널 검색"""
        channel_name = self.channel_var.get().strip()
        if not channel_name:
            messagebox.showwarning("입력 오류", "검색할 채널명을 입력해주세요.")
            return
        
        try:
            # API 키 확인
            api_key = self.main_window.get_api_key()
            if not api_key:
                messagebox.showerror("API 키 오류", "YouTube API 키가 설정되지 않았습니다.")
                return
            
            self.update_progress(10, "채널 검색 중...")
            
            # YouTube 클라이언트 초기화
            if not self.youtube_client:
                self.youtube_client = YouTubeClient(api_key)
            
            # 채널 검색
            search_request = self.youtube_client.youtube.search().list(
                part='snippet',
                q=channel_name,
                type='channel',
                maxResults=10
            )
            search_response = search_request.execute()
            
            channels = search_response.get('items', [])
            if not channels:
                messagebox.showinfo("검색 결과 없음", f"'{channel_name}' 채널을 찾을 수 없습니다.")
                self.update_progress(0, "준비 완료")
                return
            
            # 채널 선택 다이얼로그
            channel_options = []
            for channel in channels:
                title = channel['snippet']['title']
                channel_id = channel['id']['channelId']
                description = channel['snippet']['description'][:100] + "..." if len(channel['snippet']['description']) > 100 else channel['snippet']['description']
                channel_options.append(f"{title} (ID: {channel_id})")
            
            # 선택 다이얼로그
            selected = self.show_channel_selection_dialog(channel_options, channels)
            if selected:
                channel_url = f"https://www.youtube.com/channel/{selected['id']['channelId']}"
                self.channel_var.set(channel_url)
                messagebox.showinfo("채널 선택됨", f"채널이 선택되었습니다: {selected['snippet']['title']}")
            
            self.update_progress(0, "준비 완료")
            
        except Exception as e:
            print(f"채널 검색 오류: {e}")
            messagebox.showerror("검색 오류", f"채널 검색 중 오류가 발생했습니다: {str(e)}")
            self.update_progress(0, "준비 완료")
    
    def show_channel_selection_dialog(self, options, channels):
        """채널 선택 다이얼로그"""
        dialog = tk.Toplevel(self.parent)
        dialog.title("채널 선택")
        dialog.geometry("600x400")
        dialog.configure(bg='#f5f5f7')
        dialog.transient(self.main_window.root)
        dialog.grab_set()
        
        # 중앙 정렬
        dialog.update_idletasks()
        x = (dialog.winfo_screenwidth() // 2) - (600 // 2)
        y = (dialog.winfo_screenheight() // 2) - (400 // 2)
        dialog.geometry(f'600x400+{x}+{y}')
        
        selected_channel = None
        
        # 제목
        title_label = tk.Label(
            dialog,
            text="분석할 채널을 선택하세요",
            font=('SF Pro Display', 14, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        title_label.pack(pady=20)
        
        # 리스트박스
        listbox_frame = tk.Frame(dialog, bg='#f5f5f7')
        listbox_frame.pack(fill='both', expand=True, padx=20, pady=(0, 20))
        
        listbox = tk.Listbox(
            listbox_frame,
            font=('SF Pro Display', 11),
            height=10
        )
        listbox.pack(side='left', fill='both', expand=True)
        
        scrollbar = tk.Scrollbar(listbox_frame, orient='vertical', command=listbox.yview)
        scrollbar.pack(side='right', fill='y')
        listbox.configure(yscrollcommand=scrollbar.set)
        
        # 옵션 추가
        for option in options:
            listbox.insert(tk.END, option)
        
        # 버튼 프레임
        button_frame = tk.Frame(dialog, bg='#f5f5f7')
        button_frame.pack(pady=(0, 20))
        
        def on_select():
            nonlocal selected_channel
            selection = listbox.curselection()
            if selection:
                selected_channel = channels[selection[0]]
                dialog.destroy()
        
        def on_cancel():
            dialog.destroy()
        
        select_btn = tk.Button(
            button_frame,
            text="선택",
            font=('SF Pro Display', 12),
            bg='#007aff',
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            command=on_select
        )
        select_btn.pack(side='left', padx=(0, 10))
        
        cancel_btn = tk.Button(
            button_frame,
            text="취소",
            font=('SF Pro Display', 12),
            bg='#86868b',
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            command=on_cancel
        )
        cancel_btn.pack(side='left')
        
        # 더블클릭으로도 선택 가능
        listbox.bind('<Double-Button-1>', lambda e: on_select())
        
        dialog.wait_window()
        return selected_channel
    
    def preview_channel(self):
        """채널 미리보기"""
        try:
            channel_input = self.channel_var.get().strip()
            if not channel_input:
                messagebox.showwarning("입력 오류", "채널 정보를 입력해주세요.")
                return
            
            # API 키 확인
            api_key = self.main_window.get_api_key()
            if not api_key:
                messagebox.showerror("API 키 오류", "YouTube API 키가 설정되지 않았습니다.")
                return
            
            # YouTube 클라이언트 초기화
            if not self.youtube_client:
                self.youtube_client = YouTubeClient(api_key)
            
            self.update_progress(20, "채널 정보 확인 중...")
            
            # 채널 ID 추출
            if not self.channel_analyzer:
                self.channel_analyzer = ChannelAnalyzer(self.youtube_client)
            
            channel_id, channel_handle = self.channel_analyzer.extract_channel_id_from_url(channel_input)
            
            if not channel_id:
                messagebox.showerror("채널 오류", "유효하지 않은 채널 정보입니다.")
                self.update_progress(0, "준비 완료")
                return
            
            # 채널 정보 가져오기
            channel_data = self.youtube_client.get_channel_info(channel_id)
            if not channel_data:
                messagebox.showerror("채널 오류", "채널 정보를 가져올 수 없습니다.")
                self.update_progress(0, "준비 완료")
                return
            
            self.update_progress(100, "채널 정보 로드 완료")
            
            # 채널 상세 정보 창 열기
            from .channel_detail_window import ChannelDetailWindow
            detail_window = ChannelDetailWindow(self.main_window.root, channel_data, self.youtube_client)
            
            self.update_progress(0, "준비 완료")
            
        except Exception as e:
            print(f"채널 미리보기 오류: {e}")
            messagebox.showerror("미리보기 오류", f"채널 미리보기 중 오류가 발생했습니다: {str(e)}")
            self.update_progress(0, "준비 완료")
    
    def start_analysis(self):
        """분석 시작"""
        if self.is_analyzing:
            return
        
        # 입력 검증
        channel_input = self.channel_var.get().strip()
        if not channel_input:
            messagebox.showwarning("입력 오류", "채널 정보를 입력해주세요.")
            return
        
        try:
            max_videos = int(self.max_videos_var.get())
            if max_videos <= 0 or max_videos > 200:
                messagebox.showwarning("입력 오류", "분석할 영상 수는 1~200 사이여야 합니다.")
                return
        except ValueError:
            messagebox.showwarning("입력 오류", "분석할 영상 수를 올바르게 입력해주세요.")
            return
        
        # UI 상태 변경
        self.is_analyzing = True
        self.analyze_btn.config(state='disabled')
        self.stop_btn.config(state='normal')
        self.update_progress(0, "분석 준비 중...")
        
        # 분석 설정
        analysis_settings = {
            'channel_input': channel_input,
            'max_videos': max_videos,
            'sort_by': self.sort_var.get(),
            'include_shorts': self.include_shorts_var.get(),
            'detailed_analysis': self.detailed_analysis_var.get(),
            'cache_enabled': self.cache_enabled_var.get()
        }
        
        # 백그라운드에서 분석 실행
        analysis_thread = threading.Thread(
            target=self.execute_analysis,
            args=(analysis_settings,),
            daemon=True
        )
        analysis_thread.start()
    
    def execute_analysis(self, settings):
        """실제 분석 실행"""
        try:
            # API 키 확인
            api_key = self.main_window.get_api_key()
            if not api_key:
                self.handle_analysis_error("API 키가 설정되지 않았습니다.")
                return
            
            # YouTube 클라이언트 초기화
            if not self.youtube_client:
                self.youtube_client = YouTubeClient(api_key)
            
            if not self.channel_analyzer:
                self.channel_analyzer = ChannelAnalyzer(self.youtube_client)
            
            self.update_progress(10, "채널 정보 확인 중...")
            
            # 채널 ID 추출
            channel_id, channel_handle = self.channel_analyzer.extract_channel_id_from_url(settings['channel_input'])
            
            if not channel_id:
                self.handle_analysis_error("유효하지 않은 채널 정보입니다.")
                return
            
            self.update_progress(20, "채널 기본 정보 로드 중...")
            
            # 채널 정보 가져오기
            channel_data = self.youtube_client.get_channel_info(channel_id)
            if not channel_data:
                self.handle_analysis_error("채널 정보를 가져올 수 없습니다.")
                return
            
            self.update_progress(40, "영상 목록 수집 중...")
            
            # 채널 영상 목록 가져오기
            videos = self.channel_analyzer.get_channel_videos(
                channel_id,
                max_results=settings['max_videos'],
                order=settings['sort_by']
            )
            
            if not videos:
                self.handle_analysis_error("채널의 영상을 찾을 수 없습니다.")
                return
            
            self.update_progress(60, f"{len(videos)}개 영상 분석 중...")
            
            # 영상 분석
            analyzed_videos = []
            for i, video in enumerate(videos):
                if not self.is_analyzing:  # 중지 체크
                    break
                
                # 간단한 분석 수행
                analysis = self.analyze_single_video(video, i + 1)
                video['analysis'] = analysis
                analyzed_videos.append(video)
                
                # 진행률 업데이트
                progress = 60 + (i / len(videos)) * 30
                self.update_progress(progress, f"영상 분석 중... ({i+1}/{len(videos)})")
            
            if self.is_analyzing:
                self.current_channel_data = channel_data
                self.current_videos = analyzed_videos
                
                self.update_progress(100, f"완료! 채널 분석됨 ({len(analyzed_videos)}개 영상)")
                
                # 결과 표시
                self.show_analysis_results(channel_data, analyzed_videos)
            
        except Exception as e:
            self.handle_analysis_error(str(e))
        finally:
            # UI 상태 복원
            self.is_analyzing = False
            self.analyze_btn.config(state='normal')
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
                'engagement_rate': engagement_rate,
                'outlier_score': outlier_score,
                'video_type': video_type
            }
            
        except Exception as e:
            print(f"영상 분석 오류: {e}")
            return {
                'rank': rank,
                'engagement_rate': 0,
                'outlier_score': 0,
                'video_type': '일반'
            }
    
    def show_analysis_results(self, channel_data, analyzed_videos):
        """분석 결과 표시"""
        try:
            # 메인 창의 결과 뷰어로 이동
            self.main_window.show_channel_analysis({
                'channel': channel_data,
                'videos': analyzed_videos,
                'analysis_type': 'channel'
            })
            
        except Exception as e:
            print(f"결과 표시 오류: {e}")
            messagebox.showerror("결과 표시 오류", "분석 결과를 표시할 수 없습니다.")
    
    def stop_analysis(self):
        """분석 중지"""
        self.is_analyzing = False
        self.update_progress(0, "중지됨")
        print("🛑 사용자에 의해 분석이 중지되었습니다.")
    
    def handle_analysis_error(self, error):
        """분석 오류 처리"""
        error_msg = str(error)
        print(f"❌ 분석 오류: {error_msg}")
        
        # 사용자 친화적 오류 메시지
        if "API" in error_msg:
            user_msg = "YouTube API 연결에 문제가 있습니다. API 키를 확인해주세요."
        elif "quota" in error_msg.lower():
            user_msg = "API 할당량이 초과되었습니다. 잠시 후 다시 시도해주세요."
        elif "연결" in error_msg:
            user_msg = "인터넷 연결을 확인해주세요."
        else:
            user_msg = f"분석 중 오류가 발생했습니다: {error_msg}"
        
        messagebox.showerror("분석 오류", user_msg)
        self.update_progress(0, "오류 발생")
    
    def update_progress(self, value, text):
        """진행률 업데이트"""
        self.progress_var.set(value)
        self.progress_label.config(text=text)
        self.parent.update_idletasks()
    
    def set_channel_input(self, channel_url):
        """외부에서 채널 URL 설정 (결과 뷰어에서 호출)"""
        try:
            self.channel_var.set(channel_url)
            
            # URL 입력 모드로 변경
            self.input_method_var.set("url")
            self.on_input_method_changed()
            
            print(f"✅ 채널 URL 설정됨: {channel_url}")
            
        except Exception as e:
            print(f"채널 URL 설정 오류: {e}")


# 필요한 경우 ChannelAnalyzer 클래스에 추가할 메서드
class ChannelAnalyzerExtension:
    """채널 분석기 확장 메서드들"""
    
    def extract_channel_id_from_url(self, url_or_input):
        """URL이나 입력에서 채널 ID 추출"""
        try:
            import re
            
            # 이미 채널 ID인 경우
            if re.match(r'^UC[a-zA-Z0-9_-]{22}$', url_or_input):
                return url_or_input, None
            
            # 채널 URL에서 ID 추출
            patterns = [
                r'youtube\.com/channel/([UC][a-zA-Z0-9_-]{22})',
                r'youtube\.com/c/([a-zA-Z0-9_-]+)',
                r'youtube\.com/user/([a-zA-Z0-9_-]+)',
                r'youtube\.com/@([a-zA-Z0-9_-]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url_or_input)
                if match:
                    identifier = match.group(1)
                    
                    # UC로 시작하는 경우 채널 ID
                    if identifier.startswith('UC'):
                        return identifier, None
                    else:
                        # 핸들이나 사용자명인 경우 채널 ID로 변환 필요
                        return self.resolve_channel_handle(identifier)
            
            # 직접 핸들명인 경우
            return self.resolve_channel_handle(url_or_input)
            
        except Exception as e:
            print(f"채널 ID 추출 오류: {e}")
            return None, None
    
    def resolve_channel_handle(self, handle):
        """채널 핸들을 채널 ID로 변환"""
        try:
            # YouTube API를 사용해 핸들을 채널 ID로 변환
            # 실제 구현에서는 search API 등을 사용
            return None, handle
        except Exception as e:
            print(f"핸들 변환 오류: {e}")
            return None, None