"""
채널 다운로더 GUI - 사용자 친화적인 채널 분석 및 다운로드 인터페이스
"""

import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import webbrowser
import os
from datetime import datetime
import re

class ChannelDownloaderWindow:
    def __init__(self, parent, api_client, transcript_downloader):
        """채널 다운로더 창 초기화"""
        self.parent = parent
        self.api_client = api_client
        self.transcript_downloader = transcript_downloader
        
        # 채널 다운로더 임포트
        try:
            from channel_downloader import ChannelDownloader
            self.channel_downloader = ChannelDownloader(api_client, transcript_downloader)
        except ImportError:
            messagebox.showerror("오류", "channel_downloader.py 파일을 찾을 수 없습니다.")
            return
        
        # 창 생성
        self.window = tk.Toplevel(parent)
        self.window.title("🎬 YouTube 채널 다운로더")
        self.window.geometry("900x700")
        self.window.configure(bg='#f0f0f0')
        
        # 데이터 저장
        self.current_channel_info = None
        self.current_videos = []
        self.download_thread = None
        self.download_folder_path = None
        
        self.create_widgets()
        self.center_window()
    
    def center_window(self):
        """창을 화면 중앙에 배치"""
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (900 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f"900x700+{x}+{y}")
    
    def create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.window, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = tk.Label(
            main_frame,
            text="🎬 YouTube 채널 다운로더",
            font=("Arial", 16, "bold"),
            bg='#f0f0f0',
            fg='#2c3e50'
        )
        title_label.pack(pady=(0, 20))
        
        # URL 입력 섹션
        self.create_url_input_section(main_frame)
        
        # 채널 정보 섹션
        self.create_channel_info_section(main_frame)
        
        # 다운로드 옵션 섹션
        self.create_download_section(main_frame)
        
        # 진행 상황 섹션
        self.create_progress_section(main_frame)
    
    def create_url_input_section(self, parent):
        """URL 입력 섹션 생성"""
        url_frame = ttk.LabelFrame(parent, text="📎 채널 URL 입력", padding="10")
        url_frame.pack(fill=tk.X, pady=(0, 10))
        
        # URL 입력
        input_frame = ttk.Frame(url_frame)
        input_frame.pack(fill=tk.X)
        
        ttk.Label(input_frame, text="YouTube 채널 URL:").pack(side=tk.LEFT)
        
        self.url_entry = ttk.Entry(input_frame, width=60, font=("Arial", 10))
        self.url_entry.pack(side=tk.LEFT, padx=(10, 10), fill=tk.X, expand=True)
        self.url_entry.bind('<Return>', self.on_analyze_channel)
        
        self.analyze_button = ttk.Button(
            input_frame, 
            text="🔍 채널 분석", 
            command=self.analyze_channel
        )
        self.analyze_button.pack(side=tk.RIGHT)
        
        # URL 예시
        example_frame = ttk.Frame(url_frame)
        example_frame.pack(fill=tk.X, pady=(10, 0))
        
        ttk.Label(example_frame, text="💡 지원 형식:", font=("Arial", 9)).pack(side=tk.LEFT)
        
        example_text = "https://www.youtube.com/@username | https://www.youtube.com/channel/UC... | https://www.youtube.com/c/channelname"
        example_label = tk.Label(
            example_frame, 
            text=example_text,
            font=("Arial", 8),
            fg="gray",
            bg='#f0f0f0'
        )
        example_label.pack(side=tk.LEFT, padx=(10, 0))
    
    def create_channel_info_section(self, parent):
        """채널 정보 섹션 생성"""
        info_frame = ttk.LabelFrame(parent, text="📺 채널 정보", padding="10")
        info_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        # 채널 기본 정보 (왼쪽)
        left_frame = ttk.Frame(info_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        
        self.channel_info_text = scrolledtext.ScrolledText(
            left_frame, 
            width=35, 
            height=12,
            font=("Arial", 9),
            state=tk.DISABLED
        )
        self.channel_info_text.pack(fill=tk.BOTH, expand=True)
        
        # 영상 목록 (오른쪽)
        right_frame = ttk.Frame(info_frame)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        # 영상 목록 헤더
        list_header = ttk.Frame(right_frame)
        list_header.pack(fill=tk.X, pady=(0, 5))
        
        ttk.Label(list_header, text="📋 영상 목록", font=("Arial", 10, "bold")).pack(side=tk.LEFT)
        
        self.video_count_label = ttk.Label(list_header, text="", foreground="gray")
        self.video_count_label.pack(side=tk.RIGHT)
        
        # 영상 목록 트리뷰
        columns = ("순번", "제목", "유형", "길이", "조회수", "업로드일")
        self.videos_tree = ttk.Treeview(right_frame, columns=columns, show="headings", height=10)
        
        # 컬럼 설정
        self.videos_tree.heading("순번", text="순번")
        self.videos_tree.heading("제목", text="제목")
        self.videos_tree.heading("유형", text="유형")
        self.videos_tree.heading("길이", text="길이")
        self.videos_tree.heading("조회수", text="조회수")
        self.videos_tree.heading("업로드일", text="업로드일")
        
        self.videos_tree.column("순번", width=50)
        self.videos_tree.column("제목", width=200)
        self.videos_tree.column("유형", width=60)
        self.videos_tree.column("길이", width=70)
        self.videos_tree.column("조회수", width=100)
        self.videos_tree.column("업로드일", width=100)
        
        # 스크롤바
        videos_scrollbar = ttk.Scrollbar(right_frame, orient=tk.VERTICAL, command=self.videos_tree.yview)
        self.videos_tree.configure(yscrollcommand=videos_scrollbar.set)
        
        self.videos_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        videos_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 더블클릭으로 영상 열기
        self.videos_tree.bind("<Double-1>", self.on_video_double_click)
    
    def create_download_section(self, parent):
        """다운로드 옵션 섹션 생성"""
        download_frame = ttk.LabelFrame(parent, text="⬇️ 다운로드 옵션", padding="10")
        download_frame.pack(fill=tk.X, pady=(0, 10))
        
        # 왼쪽: 다운로드 옵션
        left_options = ttk.Frame(download_frame)
        left_options.pack(side=tk.LEFT, fill=tk.Y)
        
        # 다운로드 유형
        ttk.Label(left_options, text="다운로드 유형:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        self.download_transcripts_var = tk.BooleanVar(value=True)
        self.download_thumbnails_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(
            left_options, 
            text="📝 대본/자막 다운로드", 
            variable=self.download_transcripts_var
        ).pack(anchor=tk.W, pady=(5, 0))
        
        ttk.Checkbutton(
            left_options, 
            text="🖼️ 썸네일 다운로드", 
            variable=self.download_thumbnails_var
        ).pack(anchor=tk.W, pady=(5, 0))
        
        # 언어 설정
        ttk.Label(left_options, text="자막 언어 우선순위:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        
        self.language_var = tk.StringVar(value="ko_first")
        ttk.Radiobutton(left_options, text="한국어 → 영어", variable=self.language_var, value="ko_first").pack(anchor=tk.W)
        ttk.Radiobutton(left_options, text="영어 → 한국어", variable=self.language_var, value="en_first").pack(anchor=tk.W)
        ttk.Radiobutton(left_options, text="한국어만", variable=self.language_var, value="ko_only").pack(anchor=tk.W)
        
        # 음성 인식 옵션
        self.enable_speech_recognition_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            left_options, 
            text="🤖 자막 없을 시 음성인식 사용 (느림)",
            variable=self.enable_speech_recognition_var
        ).pack(anchor=tk.W, pady=(10, 0))
        
        # 오른쪽: 필터링 옵션
        right_options = ttk.Frame(download_frame)
        right_options.pack(side=tk.RIGHT, fill=tk.Y, padx=(20, 0))
        
        # 영상 필터
        ttk.Label(right_options, text="영상 필터:", font=("Arial", 10, "bold")).pack(anchor=tk.W)
        
        filter_frame = ttk.Frame(right_options)
        filter_frame.pack(anchor=tk.W, pady=(5, 0))
        
        self.include_shorts_var = tk.BooleanVar(value=True)
        self.include_long_var = tk.BooleanVar(value=True)
        
        ttk.Checkbutton(filter_frame, text="쇼츠", variable=self.include_shorts_var).pack(side=tk.LEFT)
        ttk.Checkbutton(filter_frame, text="롱폼", variable=self.include_long_var).pack(side=tk.LEFT, padx=(10, 0))
        
        # 최대 영상 수
        ttk.Label(right_options, text="최대 영상 수:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        
        max_videos_frame = ttk.Frame(right_options)
        max_videos_frame.pack(anchor=tk.W)
        
        self.max_videos_var = tk.StringVar(value="50")
        max_videos_combo = ttk.Combobox(
            max_videos_frame, 
            textvariable=self.max_videos_var,
            values=["10", "20", "50", "100", "200"],
            width=10,
            state="readonly"
        )
        max_videos_combo.pack(side=tk.LEFT)
        
        # 기타 옵션
        ttk.Label(right_options, text="기타 옵션:", font=("Arial", 10, "bold")).pack(anchor=tk.W, pady=(15, 5))
        
        self.create_zip_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            right_options, 
            text="📦 ZIP 파일 생성", 
            variable=self.create_zip_var
        ).pack(anchor=tk.W)
        
        self.open_folder_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(
            right_options, 
            text="📁 완료 후 폴더 열기", 
            variable=self.open_folder_var
        ).pack(anchor=tk.W, pady=(5, 0))
    
    def create_progress_section(self, parent):
        """진행 상황 섹션 생성"""
        progress_frame = ttk.LabelFrame(parent, text="📊 진행 상황", padding="10")
        progress_frame.pack(fill=tk.X)
        
        # 진행 상태 라벨
        self.progress_label = ttk.Label(progress_frame, text="채널 URL을 입력하고 분석 버튼을 클릭하세요.")
        self.progress_label.pack(anchor=tk.W, pady=(0, 5))
        
        # 진행률 표시
        progress_bar_frame = ttk.Frame(progress_frame)
        progress_bar_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.progress_bar = ttk.Progressbar(progress_bar_frame, mode='determinate')
        self.progress_bar.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        self.progress_percent_label = ttk.Label(progress_bar_frame, text="0%")
        self.progress_percent_label.pack(side=tk.RIGHT, padx=(10, 0))
        
        # 버튼 프레임
        button_frame = ttk.Frame(progress_frame)
        button_frame.pack(fill=tk.X)
        
        # 다운로드 시작 버튼
        self.download_button = ttk.Button(
            button_frame, 
            text="🚀 다운로드 시작", 
            command=self.start_download,
            state=tk.DISABLED
        )
        self.download_button.pack(side=tk.LEFT)
        
        # 폴더 열기 버튼
        self.open_folder_button = ttk.Button(
            button_frame, 
            text="📁 다운로드 폴더 열기", 
            command=self.open_download_folder,
            state=tk.DISABLED
        )
        self.open_folder_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # 채널 페이지 열기 버튼
        self.open_channel_button = ttk.Button(
            button_frame, 
            text="🌐 채널 페이지 열기", 
            command=self.open_channel_page,
            state=tk.DISABLED
        )
        self.open_channel_button.pack(side=tk.LEFT, padx=(10, 0))
        
        # 닫기 버튼
        ttk.Button(button_frame, text="❌ 닫기", command=self.window.destroy).pack(side=tk.RIGHT)
    
    def on_analyze_channel(self, event=None):
        """엔터 키로 채널 분석"""
        self.analyze_channel()
    
    def analyze_channel(self):
        """채널 분석 실행"""
        channel_url = self.url_entry.get().strip()
        
        if not channel_url:
            messagebox.showwarning("입력 오류", "채널 URL을 입력해주세요.")
            return
        
        # UI 비활성화
        self.analyze_button.config(state=tk.DISABLED)
        self.progress_label.config(text="채널 정보 분석 중...")
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        
        # 별도 스레드에서 분석 실행
        analysis_thread = threading.Thread(target=self.run_channel_analysis, args=(channel_url,))
        analysis_thread.daemon = True
        analysis_thread.start()
    
    def run_channel_analysis(self, channel_url):
        """채널 분석 실행 (별도 스레드)"""
        try:
            # 채널 URL 유효성 검사
            is_valid, result = self.channel_downloader.validate_channel_url(channel_url)
            
            if not is_valid:
                self.window.after(0, lambda: self.analysis_failed(result))
                return
            
            self.current_channel_info = result
            
            # 채널 미리보기 가져오기
            self.window.after(0, lambda: self.progress_label.config(text="채널 영상 목록 수집 중..."))
            
            preview_data = self.channel_downloader.get_channel_preview(channel_url, max_preview_videos=50)
            
            if not preview_data:
                self.window.after(0, lambda: self.analysis_failed("채널 데이터를 가져올 수 없습니다."))
                return
            
            self.current_videos = preview_data['preview_videos']
            
            # UI 업데이트
            self.window.after(0, lambda: self.analysis_completed(preview_data))
            
        except Exception as e:
            error_msg = f"채널 분석 중 오류: {str(e)}"
            self.window.after(0, lambda: self.analysis_failed(error_msg))
    
    def analysis_completed(self, preview_data):
        """채널 분석 완료 처리"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate', value=0)
        self.progress_label.config(text=f"분석 완료: {len(self.current_videos)}개 영상 발견")
        
        # 채널 정보 표시
        self.display_channel_info(preview_data)
        
        # 영상 목록 표시
        self.display_video_list(self.current_videos)
        
        # 버튼 활성화
        self.analyze_button.config(state=tk.NORMAL)
        self.download_button.config(state=tk.NORMAL)
        self.open_channel_button.config(state=tk.NORMAL)
    
    def analysis_failed(self, error_msg):
        """채널 분석 실패 처리"""
        self.progress_bar.stop()
        self.progress_bar.config(value=0)
        self.progress_label.config(text="분석 실패")
        
        self.analyze_button.config(state=tk.NORMAL)
        
        messagebox.showerror("분석 실패", error_msg)
    
    def display_channel_info(self, preview_data):
        """채널 정보 표시"""
        channel_info = preview_data['channel_info']
        video_stats = preview_data['video_type_stats']
        
        info_text = f"""📺 채널 정보
{'=' * 30}

채널명: {channel_info['channel_name']}
채널 ID: {channel_info['channel_id']}
구독자 수: {channel_info.get('subscriber_count', 0):,}명
총 영상 수: {channel_info.get('video_count', 0):,}개

📊 분석된 영상 통계
{'=' * 30}

총 분석 영상: {video_stats['total']}개
• 쇼츠: {video_stats['shorts']}개
• 롱폼: {video_stats['long']}개
평균 조회수: {preview_data['avg_views']:,.0f}

⏱️ 예상 다운로드 시간
{'=' * 30}

{preview_data['estimated_download_time']}

💰 예상 API 비용
{'=' * 30}

약 {preview_data['estimated_api_cost']} 유닛

📝 채널 설명
{'=' * 30}

{channel_info.get('description', '설명 없음')}
"""
        
        self.channel_info_text.config(state=tk.NORMAL)
        self.channel_info_text.delete(1.0, tk.END)
        self.channel_info_text.insert(1.0, info_text)
        self.channel_info_text.config(state=tk.DISABLED)
    
    def display_video_list(self, videos):
        """영상 목록 표시"""
        # 기존 항목 삭제
        for item in self.videos_tree.get_children():
            self.videos_tree.delete(item)
        
        # 영상 목록 추가
        for i, video in enumerate(videos, 1):
            title = video['title'][:30] + "..." if len(video['title']) > 30 else video['title']
            video_type = video.get('video_type', '알수없음')
            duration = video.get('formatted_duration', '00:00')
            views = f"{video.get('view_count', 0):,}"
            upload_date = video['published_at'][:10]
            
            self.videos_tree.insert("", tk.END, values=(
                i, title, video_type, duration, views, upload_date
            ))
        
        # 개수 표시 업데이트
        self.video_count_label.config(text=f"총 {len(videos)}개 영상")
    
    def on_video_double_click(self, event):
        """영상 더블클릭 시 YouTube에서 열기"""
        selection = self.videos_tree.selection()
        if selection:
            item = self.videos_tree.item(selection[0])
            video_index = int(item['values'][0]) - 1
            
            if 0 <= video_index < len(self.current_videos):
                video_id = self.current_videos[video_index]['id']
                video_url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(video_url)
    
    def start_download(self):
        """다운로드 시작"""
        if not self.current_channel_info or not self.current_videos:
            messagebox.showwarning("오류", "먼저 채널을 분석해주세요.")
            return
        
        # 다운로드 옵션 확인
        if not self.download_transcripts_var.get() and not self.download_thumbnails_var.get():
            messagebox.showwarning("옵션 오류", "대본 또는 썸네일 중 하나는 선택해야 합니다.")
            return
        
        # 필터링된 영상 목록 준비
        filtered_videos = self.get_filtered_videos()
        
        if not filtered_videos:
            messagebox.showwarning("필터 오류", "다운로드할 영상이 없습니다. 필터 설정을 확인해주세요.")
            return
        
        # 확인 대화상자
        download_types = []
        if self.download_transcripts_var.get():
            download_types.append("대본")
        if self.download_thumbnails_var.get():
            download_types.append("썸네일")
        
        confirm_msg = f"""다음 설정으로 다운로드를 시작하시겠습니까?

📺 채널: {self.current_channel_info['channel_name']}
📊 영상 수: {len(filtered_videos)}개
📥 다운로드 유형: {', '.join(download_types)}
🌐 언어: {self.get_language_setting_text()}

⚠️ 다운로드에는 시간이 소요될 수 있습니다."""
        
        if not messagebox.askyesno("다운로드 확인", confirm_msg):
            return
        
        # UI 비활성화
        self.download_button.config(state=tk.DISABLED)
        self.analyze_button.config(state=tk.DISABLED)
        
        # 진행 상황 초기화
        self.progress_bar.config(value=0, maximum=100)
        self.progress_label.config(text="다운로드 시작...")
        
        # 별도 스레드에서 다운로드 실행
        self.download_thread = threading.Thread(
            target=self.run_download, 
            args=(filtered_videos,)
        )
        self.download_thread.daemon = True
        self.download_thread.start()
    
    def get_filtered_videos(self):
        """필터링된 영상 목록 반환"""
        filtered = []
        
        max_videos = int(self.max_videos_var.get())
        include_shorts = self.include_shorts_var.get()
        include_long = self.include_long_var.get()
        
        for video in self.current_videos[:max_videos]:
            video_type = video.get('video_type', '')
            
            if video_type == "쇼츠" and not include_shorts:
                continue
            if video_type == "롱폼" and not include_long:
                continue
            
            filtered.append(video)
        
        return filtered
    
    def get_language_setting_text(self):
        """언어 설정 텍스트 반환"""
        lang_setting = self.language_var.get()
        if lang_setting == "ko_first":
            return "한국어 → 영어"
        elif lang_setting == "en_first":
            return "영어 → 한국어"
        else:
            return "한국어만"
    
    def run_download(self, filtered_videos):
        """다운로드 실행 (별도 스레드)"""
        try:
            # 다운로드 옵션 설정
            download_options = {
                'download_transcripts': self.download_transcripts_var.get(),
                'download_thumbnails': self.download_thumbnails_var.get(),
                'language_codes': self.get_language_codes(),
                'enable_speech_recognition': self.enable_speech_recognition_var.get(),
                'create_zip': self.create_zip_var.get()
            }
            
            # 다운로드 실행
            result = self.channel_downloader.download_channel_content(
                self.current_channel_info,
                filtered_videos,
                download_options,
                progress_callback=self.update_download_progress
            )
            
            # 결과 처리
            self.window.after(0, lambda: self.download_completed(result))
            
        except Exception as e:
            error_msg = f"다운로드 중 오류: {str(e)}"
            self.window.after(0, lambda: self.download_failed(error_msg))
    
    def get_language_codes(self):
        """언어 코드 목록 반환"""
        lang_setting = self.language_var.get()
        if lang_setting == "ko_first":
            return ['ko', 'kr', 'en']
        elif lang_setting == "en_first":
            return ['en', 'ko', 'kr']
        else:
            return ['ko', 'kr']
    
    def update_download_progress(self, message):
        """다운로드 진행 상황 업데이트"""
        self.window.after(0, lambda: self.progress_label.config(text=message))
        
        # 진행률 계산
        if "대본 다운로드:" in message:
            try:
                parts = message.split(":")
                if len(parts) > 1:
                    progress_info = parts[1].strip().split("/")
                    if len(progress_info) == 2:
                        current = int(progress_info[0])
                        total = int(progress_info[1].split()[0])
                        progress_percent = (current / total) * 50  # 대본이 50%
                        self.window.after(0, lambda: self.progress_bar.config(value=progress_percent))
                        self.window.after(0, lambda: self.progress_percent_label.config(text=f"{progress_percent:.0f}%"))
            except:
                pass
        elif "썸네일 다운로드:" in message:
            try:
                parts = message.split(":")
                if len(parts) > 1:
                    progress_info = parts[1].strip().split("/")
                    if len(progress_info) == 2:
                        current = int(progress_info[0])
                        total = int(progress_info[1].split()[0])
                        progress_percent = 50 + (current / total) * 50  # 썸네일이 나머지 50%
                        self.window.after(0, lambda: self.progress_bar.config(value=progress_percent))
                        self.window.after(0, lambda: self.progress_percent_label.config(text=f"{progress_percent:.0f}%"))
            except:
                pass
    
    def download_completed(self, result):
        """다운로드 완료 처리"""
        if result['success']:
            self.progress_bar.config(value=100)
            self.progress_percent_label.config(text="100%")
            self.progress_label.config(text="다운로드 완료!")
            
            # 결과 표시
            summary = result['summary']
            result_msg = f"""🎉 다운로드 완료!

📊 결과 요약:
• 채널: {summary['channel_name']}
• 총 영상: {summary['total_videos']}개
• 대본 다운로드: {summary['transcripts_downloaded']}개
• 썸네일 다운로드: {summary['thumbnails_downloaded']}개
• 실패: {summary['failed_downloads']}개
• 성공률: {summary['success_rate']:.1f}%

📁 저장 위치:
{result['download_folder']}
"""
            
            if summary.get('zip_file'):
                result_msg += f"\n📦 ZIP 파일: {summary['zip_file']}"
            
            messagebox.showinfo("다운로드 완료", result_msg)
            
            # 버튼 활성화
            self.open_folder_button.config(state=tk.NORMAL)
            
            # 자동으로 폴더 열기
            if self.open_folder_var.get():
                self.download_folder_path = result['download_folder']
                self.open_download_folder()
        else:
            self.progress_label.config(text="다운로드 실패")
            messagebox.showerror("다운로드 실패", result.get('error', '알 수 없는 오류'))
        
        # UI 복원
        self.download_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
    
    def download_failed(self, error_msg):
        """다운로드 실패 처리"""
        self.progress_label.config(text="다운로드 실패")
        self.progress_bar.config(value=0)
        self.progress_percent_label.config(text="0%")
        
        # UI 복원
        self.download_button.config(state=tk.NORMAL)
        self.analyze_button.config(state=tk.NORMAL)
        
        messagebox.showerror("다운로드 실패", error_msg)
    
    def open_download_folder(self):
        """다운로드 폴더 열기"""
        if hasattr(self, 'download_folder_path') and self.download_folder_path and os.path.exists(self.download_folder_path):
            try:
                import subprocess
                import platform
                
                if platform.system() == "Windows":
                    os.startfile(self.download_folder_path)
                elif platform.system() == "Darwin":  # macOS
                    subprocess.run(["open", self.download_folder_path])
                else:  # Linux
                    subprocess.run(["xdg-open", self.download_folder_path])
            except Exception as e:
                messagebox.showerror("오류", f"폴더를 열 수 없습니다: {e}")
        else:
            messagebox.showwarning("경고", "다운로드 폴더가 없습니다.")
    
    def open_channel_page(self):
        """채널 페이지 열기"""
        if self.current_channel_info:
            channel_url = f"https://www.youtube.com/channel/{self.current_channel_info['channel_id']}"
            webbrowser.open(channel_url)