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
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(parent, bg=self.card_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg=self.card_bg)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 필터 추가
        self.create_filters(scrollable_frame)
        
        # 레이아웃
        canvas.pack(side="left", fill="both", expand=True, padx=10)
        scrollbar.pack(side="right", fill="y")
        
        # 검색 버튼
        self.search_button = tk.Button(parent, text="검색 시작",
                                     command=self.start_analysis,
                                     bg=self.accent_color, fg="white",
                                     font=('Arial', 12, 'bold'),
                                     pady=10)
        self.search_button.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=10)
    
    def create_filters(self, parent):
        """필터 생성"""
        # 검색 키워드
        tk.Label(parent, text="검색 키워드", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(10, 5))
        
        self.keyword_entry = tk.Entry(parent, font=('Arial', 11))
        self.keyword_entry.pack(fill=tk.X, pady=(0, 15))
        self.keyword_entry.insert(0, "서울 카페")
        
        # 정렬 기준
        tk.Label(parent, text="정렬 기준", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.sort_var = tk.StringVar(value="관련성")
        sort_combo = ttk.Combobox(parent, textvariable=self.sort_var,
                                 values=["관련성", "업로드 날짜", "조회수"],
                                 state="readonly", font=('Arial', 11))
        sort_combo.pack(fill=tk.X, pady=(0, 15))
        
        # 업로드 기간
        tk.Label(parent, text="업로드 기간", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.period_var = tk.StringVar(value="일주일")
        period_combo = ttk.Combobox(parent, textvariable=self.period_var,
                                   values=["오늘", "2일", "일주일", "한달", "3개월"],
                                   state="readonly", font=('Arial', 11))
        period_combo.pack(fill=tk.X, pady=(0, 15))
        
        # 영상 유형
        tk.Label(parent, text="영상 유형", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.video_type_var = tk.StringVar(value="전체")
        type_combo = ttk.Combobox(parent, textvariable=self.video_type_var,
                                 values=["전체", "쇼츠", "롱폼"],
                                 state="readonly", font=('Arial', 11))
        type_combo.pack(fill=tk.X, pady=(0, 15))
        
        # 최소 조회수
        tk.Label(parent, text="최소 조회수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.min_views_var = tk.StringVar(value="10,000")
        views_combo = ttk.Combobox(parent, textvariable=self.min_views_var,
                                  values=["제한없음", "10,000", "100,000", "1,000,000"],
                                  state="readonly", font=('Arial', 11))
        views_combo.pack(fill=tk.X, pady=(0, 15))
        
        # 최대 구독자 수
        tk.Label(parent, text="최대 구독자 수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.max_subscribers_var = tk.StringVar(value="100,000")
        subs_combo = ttk.Combobox(parent, textvariable=self.max_subscribers_var,
                                 values=["제한없음", "1,000", "10,000", "100,000"],
                                 state="readonly", font=('Arial', 11))
        subs_combo.pack(fill=tk.X, pady=(0, 15))
    
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
        keyword = self.keyword_entry.get().strip()
        if not keyword:
            messagebox.showwarning("오류", "검색 키워드를 입력해주세요.")
            return
        
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("오류", "API 키를 입력해주세요.")
            return
        
        # 버튼 비활성화
        self.search_button.configure(state='disabled', text="검색 중...")
        self.progress_label.config(text="검색 중...")
        
        # 기존 결과 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 캐시 초기화
        self.channel_cache = {}
        
        # 설정 준비
        settings = self.prepare_settings()
        
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
                self.root.after(0, self.reset_search_button)
                return
            
            self.update_progress(f"{len(videos)}개 영상 발견...")
            
            # 간단한 분석
            analyzed_videos = self.quick_analyze_videos(videos)
            
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
                self.update_progress(f"분석 중... {i+1}/{len(videos)}")
        
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
        self.search_button.configure(state='normal', text="검색 시작")
    
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
        self.results_count_label.config(text=f"총 {len(videos)}개")
        self.progress_label.config(text="분석 완료!")
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
        messagebox.showinfo("알림", "채널 분석 기능은 개발 중입니다.")
    
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