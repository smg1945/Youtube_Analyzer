"""
YouTube 트렌드 분석기 GUI - 개선된 버전
- macOS 스타일 UI
- 처리 속도 최적화
- 더 많은 결과 출력
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
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


class ImprovedYouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube DeepSearch - 콘텐츠 분석 툴")
        self.root.geometry("1200x800")
        
        # macOS 스타일 색상
        self.bg_color = "#f5f5f7"
        self.white = "#ffffff"
        self.gray = "#86868b"
        self.blue = "#007aff"
        self.dark_text = "#1d1d1f"
        
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
        
        # 처리 속도 향상을 위한 스레드 풀
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=5)
        
        # GUI 구성
        self.create_widgets()
        
        # API 키 자동 로드
        self.load_api_key()
    
    def setup_styles(self):
        """macOS 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 버튼 스타일
        style.configure('Blue.TButton',
                       background=self.blue,
                       foreground='white',
                       borderwidth=0,
                       focuscolor='none',
                       font=('SF Pro Display', 11))
        style.map('Blue.TButton',
                 background=[('active', '#0051d5')])
        
        # 엔트리 스타일
        style.configure('Modern.TEntry',
                       fieldbackground='white',
                       borderwidth=1,
                       relief='solid',
                       font=('SF Pro Display', 11))
        
        # 라벨프레임 스타일
        style.configure('Card.TLabelframe',
                       background='white',
                       borderwidth=1,
                       relief='solid',
                       font=('SF Pro Display', 10, 'bold'))
        style.configure('Card.TLabelframe.Label',
                       background='white',
                       foreground=self.dark_text)
    
    def create_widgets(self):
        """위젯 생성"""
        # 상단 API 키 입력 영역
        self.create_api_section()
        
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 왼쪽 패널 (설정)
        left_panel = tk.Frame(main_container, bg=self.bg_color, width=350)
        left_panel.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 20))
        left_panel.pack_propagate(False)
        
        self.create_filters_section(left_panel)
        
        # 오른쪽 패널 (결과)
        right_panel = tk.Frame(main_container, bg=self.bg_color)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        self.create_results_section(right_panel)
        
        # 하단 버튼 영역
        self.create_bottom_buttons()
    
    def create_api_section(self):
        """API 키 입력 섹션"""
        api_frame = tk.Frame(self.root, bg='white', height=80)
        api_frame.pack(fill=tk.X, padx=20, pady=(20, 10))
        api_frame.pack_propagate(False)
        
        # API 키 라벨
        api_label = tk.Label(api_frame, text="API 키", 
                            font=('SF Pro Display', 12), 
                            bg='white', fg=self.dark_text)
        api_label.pack(side=tk.LEFT, padx=20, pady=25)
        
        # API 키 입력
        self.api_entry = ttk.Entry(api_frame, font=('SF Pro Display', 11), 
                                  style='Modern.TEntry', width=50)
        self.api_entry.pack(side=tk.LEFT, padx=(0, 20), pady=25)
        
        # API 키 저장 버튼
        save_api_btn = tk.Button(api_frame, text="저장", 
                                font=('SF Pro Display', 11),
                                bg=self.blue, fg='white',
                                borderwidth=0, padx=20,
                                command=self.save_api_key)
        save_api_btn.pack(side=tk.LEFT, pady=25)
    
    def create_filters_section(self, parent):
        """필터 설정 섹션"""
        # 검색 키워드
        keyword_frame = ttk.LabelFrame(parent, text="검색 키워드", 
                                      style='Card.TLabelframe', padding=15)
        keyword_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.keyword_entry = ttk.Entry(keyword_frame, font=('SF Pro Display', 11),
                                      style='Modern.TEntry')
        self.keyword_entry.pack(fill=tk.X)
        self.keyword_entry.insert(0, "서울 카페")
        
        # 최소 조회수
        views_frame = ttk.LabelFrame(parent, text="최소 조회수", 
                                    style='Card.TLabelframe', padding=15)
        views_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.min_views_var = tk.StringVar(value="1000")
        views_combo = ttk.Combobox(views_frame, textvariable=self.min_views_var,
                                  values=["0", "1000", "10000", "50000", "100000"],
                                  state="readonly", font=('SF Pro Display', 11))
        views_combo.pack(fill=tk.X)
        
        # 업로드 기간
        period_frame = ttk.LabelFrame(parent, text="업로드 기간", 
                                     style='Card.TLabelframe', padding=15)
        period_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.period_var = tk.StringVar(value="7")
        periods = [
            ("오늘", "1"),
            ("2일", "2"),
            ("일주일", "7"),
            ("한달", "30"),
            ("3개월", "90")
        ]
        
        for text, value in periods:
            rb = tk.Radiobutton(period_frame, text=text, variable=self.period_var,
                               value=value, bg='white', font=('SF Pro Display', 10),
                               activebackground='white')
            rb.pack(anchor=tk.W, pady=2)
        
        # 동영상 유형
        type_frame = ttk.LabelFrame(parent, text="동영상 유형", 
                                   style='Card.TLabelframe', padding=15)
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        self.include_all_var = tk.BooleanVar(value=True)
        self.include_shorts_var = tk.BooleanVar(value=False)
        self.include_long_var = tk.BooleanVar(value=False)
        
        tk.Checkbutton(type_frame, text="전체", variable=self.include_all_var,
                      bg='white', font=('SF Pro Display', 10),
                      command=self.on_all_check).pack(anchor=tk.W)
        tk.Checkbutton(type_frame, text="쇼츠", variable=self.include_shorts_var,
                      bg='white', font=('SF Pro Display', 10)).pack(anchor=tk.W)
        tk.Checkbutton(type_frame, text="롱폼", variable=self.include_long_var,
                      bg='white', font=('SF Pro Display', 10)).pack(anchor=tk.W)
        
        # 분석 버튼
        self.analyze_btn = tk.Button(parent, text="검색",
                                    font=('SF Pro Display', 14, 'bold'),
                                    bg=self.blue, fg='white',
                                    borderwidth=0, padx=30, pady=10,
                                    command=self.start_analysis)
        self.analyze_btn.pack(pady=20)
    
    def create_results_section(self, parent):
        """결과 테이블 섹션"""
        # 결과 프레임
        results_frame = tk.Frame(parent, bg='white')
        results_frame.pack(fill=tk.BOTH, expand=True)
        
        # 헤더
        header_frame = tk.Frame(results_frame, bg='white', height=40)
        header_frame.pack(fill=tk.X)
        header_frame.pack_propagate(False)
        
        tk.Label(header_frame, text="🎬 검색 결과", 
                font=('SF Pro Display', 14, 'bold'),
                bg='white', fg=self.dark_text).pack(side=tk.LEFT, padx=20, pady=10)
        
        self.results_count_label = tk.Label(header_frame, text="", 
                                           font=('SF Pro Display', 11),
                                           bg='white', fg=self.gray)
        self.results_count_label.pack(side=tk.RIGHT, padx=20, pady=10)
        
        # 트리뷰
        tree_frame = tk.Frame(results_frame, bg='white')
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # 컬럼 정의
        columns = ("순번", "업로드 날짜", "조회수", "제목", "채널", "평균 조회수", 
                  "채널 총 구독자", "반응 참여 평가", "평균 대비 성능")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=20)
        
        # 컬럼 설정
        column_widths = {
            "순번": 50,
            "업로드 날짜": 100,
            "조회수": 100,
            "제목": 250,
            "채널": 150,
            "평균 조회수": 100,
            "채널 총 구독자": 120,
            "반응 참여 평가": 120,
            "평균 대비 성능": 120
        }
        
        for col in columns:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 스크롤바
        vsb = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        hsb = ttk.Scrollbar(tree_frame, orient="horizontal", command=self.tree.xview)
        self.tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        self.tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        tree_frame.grid_rowconfigure(0, weight=1)
        tree_frame.grid_columnconfigure(0, weight=1)
        
        # 더블클릭 이벤트
        self.tree.bind("<Double-1>", self.on_video_double_click)
        
        # 진행 상태 표시
        self.progress_label = tk.Label(results_frame, text="", 
                                      font=('SF Pro Display', 11),
                                      bg='white', fg=self.gray)
        self.progress_label.pack(pady=10)
    
    def create_bottom_buttons(self):
        """하단 버튼들"""
        button_frame = tk.Frame(self.root, bg=self.bg_color)
        button_frame.pack(fill=tk.X, padx=20, pady=(0, 20))
        
        buttons = [
            ("모두 선택", self.select_all),
            ("모두 해제", self.deselect_all),
            ("엑셀 추출", self.export_excel),
            ("채널 링크 열기", self.open_channel),
            ("영상 링크 열기", self.open_video),
            ("썸네일 다운로드", self.download_thumbnails)
        ]
        
        for text, command in buttons:
            btn = tk.Button(button_frame, text=text,
                           font=('SF Pro Display', 11),
                           bg='white', fg=self.dark_text,
                           borderwidth=1, relief='solid',
                           padx=15, pady=5,
                           command=command)
            btn.pack(side=tk.LEFT, padx=(0, 10))
    
    def on_all_check(self):
        """전체 체크박스 처리"""
        if self.include_all_var.get():
            self.include_shorts_var.set(False)
            self.include_long_var.set(False)
    
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
        """분석 시작 - 최적화된 버전"""
        # 검증
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("오류", "검색 키워드를 입력해주세요.")
            return
        
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("오류", "API 키를 입력해주세요.")
            return
        
        # 버튼 비활성화
        self.analyze_btn.config(state=tk.DISABLED)
        self.progress_label.config(text="검색 중...")
        
        # 기존 결과 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 설정 준비
        settings = self.prepare_settings()
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self.run_fast_analysis, args=(settings,))
        thread.daemon = True
        thread.start()
    
    def prepare_settings(self):
        """설정 준비"""
        video_type = "all"
        if self.include_shorts_var.get():
            video_type = "shorts"
        elif self.include_long_var.get():
            video_type = "long"
        
        return {
            'keyword': self.keyword_entry.get().strip(),
            'min_views': int(self.min_views_var.get()),
            'period_days': int(self.period_var.get()),
            'video_type': video_type,
            'region': 'KR',
            'max_results': 200,  # 더 많은 결과
            'light_mode': True   # 항상 경량 모드로 빠른 처리
        }
    
    def run_fast_analysis(self, settings):
        """빠른 분석 실행"""
        try:
            # API 클라이언트 초기화
            self.api_client = YouTubeAPIClient(self.api_entry.get().strip())
            self.analyzer = DataAnalyzer(language='ko')
            
            # 진행 상황 업데이트
            self.update_progress("영상 검색 중...")
            
            # 영상 검색 (개선된 API 사용)
            videos = self.api_client.search_videos_by_keyword(
                keyword=settings['keyword'],
                region_code=settings['region'],
                max_results=settings['max_results'],
                min_view_count=settings['min_views'],
                period_days=settings['period_days'],
                video_type=settings['video_type'],
                search_intensity="medium"  # 중간 강도로 빠른 처리
            )
            
            if not videos:
                self.update_progress("검색 결과가 없습니다.")
                self.root.after(0, lambda: self.analyze_btn.config(state=tk.NORMAL))
                return
            
            self.update_progress(f"{len(videos)}개 영상 분석 중...")
            
            # 병렬 처리로 빠른 분석
            analyzed_videos = self.analyze_videos_parallel(videos, settings)
            
            # 결과 정렬 (조회수 기준)
            analyzed_videos.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
            
            self.analyzed_videos = analyzed_videos
            
            # UI 업데이트
            self.root.after(0, lambda: self.display_results(analyzed_videos))
            
        except Exception as e:
            self.update_progress(f"오류: {str(e)}")
            self.root.after(0, lambda: self.analyze_btn.config(state=tk.NORMAL))
    
    def analyze_videos_parallel(self, videos, settings):
        """병렬 처리로 빠른 영상 분석"""
        analyzed_videos = []
        total = len(videos)
        
        # 채널 통계 캐시
        channel_cache = {}
        
        def analyze_single_video(video, index):
            try:
                # 기본 정보
                channel_id = video['snippet']['channelId']
                
                # 채널 통계 (캐시 활용)
                if channel_id not in channel_cache:
                    channel_stats = self.api_client.get_channel_recent_videos_stats(
                        channel_id, light_mode=True
                    )
                    channel_cache[channel_id] = channel_stats
                else:
                    channel_stats = channel_cache[channel_id]
                
                # 분석 데이터
                video['analysis'] = {
                    'channel_avg_views': channel_stats.get('avg_views', 0) if channel_stats else 0,
                    'outlier_score': self.calculate_simple_outlier_score(video, channel_stats),
                    'engagement_category': self.get_engagement_category(video),
                    'video_type': self.get_video_type(video)
                }
                
                video['rank'] = index + 1
                return video
                
            except Exception as e:
                print(f"영상 분석 오류: {e}")
                return None
        
        # 병렬 처리
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            for i, video in enumerate(videos):
                future = executor.submit(analyze_single_video, video, i)
                futures.append(future)
                
                # 진행 상황 업데이트
                if i % 10 == 0:
                    self.update_progress(f"분석 중... {i}/{total}")
            
            # 결과 수집
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    analyzed_videos.append(result)
        
        return analyzed_videos
    
    def calculate_simple_outlier_score(self, video, channel_stats):
        """간단한 Outlier Score 계산"""
        try:
            current_views = int(video['statistics'].get('viewCount', 0))
            avg_views = channel_stats.get('avg_views', 1) if channel_stats else 1
            
            if avg_views == 0:
                avg_views = 1
            
            return round(current_views / avg_views, 2)
        except:
            return 1.0
    
    def get_engagement_category(self, video):
        """참여도 카테고리"""
        try:
            views = int(video['statistics'].get('viewCount', 0))
            likes = int(video['statistics'].get('likeCount', 0))
            
            if views == 0:
                return "평가불가"
            
            engagement_rate = (likes / views) * 100
            
            if engagement_rate >= 5:
                return "매우 높음"
            elif engagement_rate >= 3:
                return "높음"
            elif engagement_rate >= 1:
                return "보통"
            else:
                return "낮음"
        except:
            return "평가불가"
    
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
            title = snippet['title'][:40] + "..." if len(snippet['title']) > 40 else snippet['title']
            
            # 채널명
            channel = snippet['channelTitle']
            
            # 평균 조회수
            avg_views = f"{int(analysis.get('channel_avg_views', 0)):,}"
            
            # 구독자 수 (채널 정보에서 가져와야 하지만 빠른 처리를 위해 생략)
            subscribers = "-"
            
            # 참여도
            engagement = analysis.get('engagement_category', '평가불가')
            
            # Outlier Score
            outlier = f"{analysis.get('outlier_score', 1.0)}x"
            
            # 트리에 추가
            self.tree.insert("", tk.END, values=(
                i, published, views, title, channel, 
                avg_views, subscribers, engagement, outlier
            ))
        
        # 결과 수 업데이트
        self.results_count_label.config(text=f"총 {len(videos)}개")
        self.progress_label.config(text="분석 완료!")
        self.analyze_btn.config(state=tk.NORMAL)
    
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
    
    def select_all(self):
        """모두 선택"""
        for item in self.tree.get_children():
            self.tree.selection_add(item)
    
    def deselect_all(self):
        """모두 해제"""
        self.tree.selection_remove(self.tree.get_children())
    
    def export_excel(self):
        """엑셀 내보내기"""
        if not self.analyzed_videos:
            messagebox.showwarning("오류", "내보낼 데이터가 없습니다.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")]
        )
        
        if filename:
            try:
                # 엑셀 생성기 사용
                excel_gen = ExcelGenerator(filename)
                excel_gen.create_excel_file(self.analyzed_videos, self.current_settings)
                messagebox.showinfo("성공", f"엑셀 파일이 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("오류", f"엑셀 저장 실패: {str(e)}")
    
    def open_channel(self):
        """채널 열기"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("오류", "채널을 선택해주세요.")
            return
        
        for item in selection:
            index = int(self.tree.item(item)['values'][0]) - 1
            if 0 <= index < len(self.analyzed_videos):
                channel_id = self.analyzed_videos[index]['snippet']['channelId']
                url = f"https://www.youtube.com/channel/{channel_id}"
                webbrowser.open(url)
    
    def open_video(self):
        """영상 열기"""
        selection = self.tree.selection()
        if not selection:
            messagebox.showwarning("오류", "영상을 선택해주세요.")
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
            messagebox.showwarning("오류", "다운로드할 영상을 선택해주세요.")
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