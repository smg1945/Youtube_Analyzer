"""
영상 상세 정보 다이얼로그 모듈
영상의 상세 정보를 표시하는 다이얼로그
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime

class VideoDetailsDialog:
    """영상 상세 정보 다이얼로그 클래스"""
    
    def __init__(self, parent, video_data):
        """
        영상 상세 정보 다이얼로그 초기화
        
        Args:
            parent: 부모 위젯
            video_data (dict): 영상 데이터
        """
        self.parent = parent
        self.video_data = video_data
        
        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("영상 상세 정보")
        self.dialog.geometry("600x700")
        self.dialog.configure(bg='#f5f5f7')
        self.dialog.resizable(True, True)
        
        # 모달 설정
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 중앙 정렬
        self.center_dialog()
        
        # 닫기 이벤트
        self.dialog.protocol("WM_DELETE_WINDOW", self.close)
        
        self.create_widgets()
        self.load_video_data()
    
    def center_dialog(self):
        """다이얼로그를 부모 창 중앙에 배치"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = 600
        dialog_height = 700
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def create_widgets(self):
        """위젯 생성"""
        # 메인 컨테이너
        main_frame = tk.Frame(self.dialog, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 탭 노트북
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill='both', expand=True, pady=(0, 15))
        
        # 각 탭 생성
        self.create_basic_info_tab()
        self.create_statistics_tab()
        self.create_analysis_tab()
        self.create_channel_tab()
        
        # 하단 버튼들
        self.create_buttons(main_frame)
    
    def create_basic_info_tab(self):
        """기본 정보 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="기본 정보")
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(tab_frame, bg='#f5f5f7')
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f7')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 기본 정보 필드들
        self.basic_info_fields = {}
        
        info_fields = [
            ("제목", "title", True),
            ("채널명", "channel_title", False),
            ("영상 ID", "video_id", False),
            ("채널 ID", "channel_id", False),
            ("업로드 일시", "published_at", False),
            ("영상 길이", "duration", False),
            ("영상 유형", "video_type", False),
            ("카테고리", "category", False),
            ("언어", "language", False),
            ("설명", "description", True)
        ]
        
        for i, (label_text, field_key, is_multiline) in enumerate(info_fields):
            # 라벨
            label = tk.Label(
                scrollable_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7',
                anchor='nw'
            )
            label.grid(row=i, column=0, sticky='nw', padx=(10, 20), pady=10)
            
            # 값 위젯
            if is_multiline:
                # 여러 줄 텍스트
                text_widget = tk.Text(
                    scrollable_frame,
                    height=4 if field_key == 'description' else 2,
                    width=40,
                    font=('SF Pro Display', 10),
                    wrap='word',
                    bg='white',
                    relief='solid',
                    bd=1,
                    state='disabled'
                )
                text_widget.grid(row=i, column=1, sticky='w', padx=(0, 10), pady=10)
                self.basic_info_fields[field_key] = text_widget
            else:
                # 단일 줄 텍스트
                value_label = tk.Label(
                    scrollable_frame,
                    text="",
                    font=('SF Pro Display', 10),
                    bg='#f5f5f7',
                    anchor='w',
                    wraplength=350,
                    justify='left'
                )
                value_label.grid(row=i, column=1, sticky='w', padx=(0, 10), pady=10)
                self.basic_info_fields[field_key] = value_label
        
        # 레이아웃
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_statistics_tab(self):
        """통계 정보 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="통계")
        
        main_frame = tk.Frame(tab_frame, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 기본 통계
        basic_stats_frame = tk.LabelFrame(main_frame, text="기본 통계", bg='#f5f5f7', padx=15, pady=15)
        basic_stats_frame.pack(fill='x', pady=(0, 20))
        
        self.stat_labels = {}
        
        basic_stats = [
            ("조회수", "view_count"),
            ("좋아요", "like_count"),
            ("댓글수", "comment_count"),
            ("좋아요율", "like_rate"),
            ("댓글율", "comment_rate")
        ]
        
        for i, (label_text, key) in enumerate(basic_stats):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(
                basic_stats_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 11),
                bg='#f5f5f7'
            ).grid(row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            value_label = tk.Label(
                basic_stats_frame,
                text="0",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7'
            )
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 30), pady=5)
            self.stat_labels[key] = value_label
        
        # 성과 분석
        performance_frame = tk.LabelFrame(main_frame, text="성과 분석", bg='#f5f5f7', padx=15, pady=15)
        performance_frame.pack(fill='x', pady=(0, 20))
        
        performance_stats = [
            ("Outlier Score", "outlier_score"),
            ("성과 등급", "outlier_category"),
            ("참여도 점수", "engagement_score"),
            ("일평균 조회수", "views_per_day"),
            ("성장 속도", "growth_velocity")
        ]
        
        for i, (label_text, key) in enumerate(performance_stats):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(
                performance_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 11),
                bg='#f5f5f7'
            ).grid(row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            value_label = tk.Label(
                performance_frame,
                text="계산 중...",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7'
            )
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 30), pady=5)
            self.stat_labels[key] = value_label
        
        # 시간 분석
        time_frame = tk.LabelFrame(main_frame, text="시간 분석", bg='#f5f5f7', padx=15, pady=15)
        time_frame.pack(fill='x')
        
        time_stats = [
            ("업로드 후 경과", "time_elapsed"),
            ("업로드 요일", "upload_day"),
            ("업로드 시간", "upload_time")
        ]
        
        for i, (label_text, key) in enumerate(time_stats):
            tk.Label(
                time_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 11),
                bg='#f5f5f7'
            ).grid(row=i, column=0, sticky='w', padx=(0, 10), pady=5)
            
            value_label = tk.Label(
                time_frame,
                text="계산 중...",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7'
            )
            value_label.grid(row=i, column=1, sticky='w', pady=5)
            self.stat_labels[key] = value_label
    
    def create_analysis_tab(self):
        """분석 결과 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="분석 결과")
        
        main_frame = tk.Frame(tab_frame, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 키워드 분석
        keywords_frame = tk.LabelFrame(main_frame, text="키워드 분석", bg='#f5f5f7', padx=15, pady=15)
        keywords_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(
            keywords_frame,
            text="핵심 키워드:",
            font=('SF Pro Display', 11, 'bold'),
            bg='#f5f5f7'
        ).pack(anchor='w', pady=(0, 10))
        
        self.keywords_text = tk.Text(
            keywords_frame,
            height=3,
            font=('SF Pro Display', 10),
            bg='white',
            relief='solid',
            bd=1,
            state='disabled'
        )
        self.keywords_text.pack(fill='x')
        
        # 제목 분석
        title_frame = tk.LabelFrame(main_frame, text="제목 분석", bg='#f5f5f7', padx=15, pady=15)
        title_frame.pack(fill='x', pady=(0, 20))
        
        self.title_analysis_labels = {}
        
        title_analysis = [
            ("제목 길이", "title_length"),
            ("단어 수", "word_count"),
            ("특수문자 포함", "has_special_chars"),
            ("숫자 포함", "has_numbers"),
            ("이모지 포함", "has_emoji")
        ]
        
        for i, (label_text, key) in enumerate(title_analysis):
            row = i // 2
            col = (i % 2) * 2
            
            tk.Label(
                title_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 10),
                bg='#f5f5f7'
            ).grid(row=row, column=col, sticky='w', padx=(0, 10), pady=5)
            
            value_label = tk.Label(
                title_frame,
                text="분석 중...",
                font=('SF Pro Display', 10, 'bold'),
                bg='#f5f5f7'
            )
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 30), pady=5)
            self.title_analysis_labels[key] = value_label
        
        # 감정 분석 (댓글이 있는 경우)
        sentiment_frame = tk.LabelFrame(main_frame, text="감정 분석", bg='#f5f5f7', padx=15, pady=15)
        sentiment_frame.pack(fill='x')
        
        self.sentiment_labels = {}
        
        sentiment_analysis = [
            ("긍정", "positive"),
            ("중립", "neutral"),
            ("부정", "negative")
        ]
        
        for i, (label_text, key) in enumerate(sentiment_analysis):
            tk.Label(
                sentiment_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 10),
                bg='#f5f5f7'
            ).grid(row=i, column=0, sticky='w', padx=(0, 10), pady=5)
            
            value_label = tk.Label(
                sentiment_frame,
                text="분석 안됨",
                font=('SF Pro Display', 10, 'bold'),
                bg='#f5f5f7'
            )
            value_label.grid(row=i, column=1, sticky='w', pady=5)
            self.sentiment_labels[key] = value_label
    
    def create_channel_tab(self):
        """채널 정보 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="채널 정보")
        
        main_frame = tk.Frame(tab_frame, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 채널 기본 정보
        channel_basic_frame = tk.LabelFrame(main_frame, text="채널 기본 정보", bg='#f5f5f7', padx=15, pady=15)
        channel_basic_frame.pack(fill='x', pady=(0, 20))
        
        self.channel_labels = {}
        
        channel_info = [
            ("채널명", "channel_title"),
            ("구독자 수", "subscriber_count"),
            ("총 영상 수", "video_count"),
            ("총 조회수", "total_views"),
            ("채널 생성일", "channel_created")
        ]
        
        for i, (label_text, key) in enumerate(channel_info):
            tk.Label(
                channel_basic_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 11),
                bg='#f5f5f7'
            ).grid(row=i, column=0, sticky='w', padx=(0, 20), pady=8)
            
            value_label = tk.Label(
                channel_basic_frame,
                text="정보 없음",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7',
                wraplength=300,
                justify='left'
            )
            value_label.grid(row=i, column=1, sticky='w', pady=8)
            self.channel_labels[key] = value_label
        
        # 채널 성과 (이 영상 vs 채널 평균)
        performance_comparison_frame = tk.LabelFrame(main_frame, text="채널 대비 성과", bg='#f5f5f7', padx=15, pady=15)
        performance_comparison_frame.pack(fill='x')
        
        self.comparison_labels = {}
        
        comparison_info = [
            ("채널 평균 조회수", "channel_avg_views"),
            ("이 영상의 성과", "video_performance"),
            ("성과 비율", "performance_ratio")
        ]
        
        for i, (label_text, key) in enumerate(comparison_info):
            tk.Label(
                performance_comparison_frame,
                text=f"{label_text}:",
                font=('SF Pro Display', 11),
                bg='#f5f5f7'
            ).grid(row=i, column=0, sticky='w', padx=(0, 20), pady=8)
            
            value_label = tk.Label(
                performance_comparison_frame,
                text="계산 중...",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7'
            )
            value_label.grid(row=i, column=1, sticky='w', pady=8)
            self.comparison_labels[key] = value_label
    
    def create_buttons(self, parent):
        """버튼 영역 생성"""
        button_frame = tk.Frame(parent, bg='#f5f5f7')
        button_frame.pack(fill='x')
        
        # YouTube에서 열기
        youtube_button = tk.Button(
            button_frame,
            text="🔗 YouTube에서 열기",
            font=('SF Pro Display', 11),
            bg='#ff0000',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.open_in_youtube
        )
        youtube_button.pack(side='left')
        
        # 채널 페이지 열기
        channel_button = tk.Button(
            button_frame,
            text="📺 채널 페이지 열기",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.open_channel_page
        )
        channel_button.pack(side='left', padx=(10, 0))
        
        # 링크 복사
        copy_button = tk.Button(
            button_frame,
            text="📋 링크 복사",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.copy_video_link
        )
        copy_button.pack(side='left', padx=(10, 0))
        
        # 닫기 버튼
        close_button = tk.Button(
            button_frame,
            text="닫기",
            font=('SF Pro Display', 11),
            bg='#86868b',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.close
        )
        close_button.pack(side='right')
    
    def load_video_data(self):
        """영상 데이터 로드"""
        try:
            snippet = self.video_data.get('snippet', {})
            statistics = self.video_data.get('statistics', {})
            content_details = self.video_data.get('contentDetails', {})
            analysis = self.video_data.get('analysis', {})
            
            # 기본 정보 로드
            self.load_basic_info(snippet, content_details, analysis)
            
            # 통계 정보 로드
            self.load_statistics(statistics, analysis)
            
            # 분석 결과 로드
            self.load_analysis_results(snippet, analysis)
            
            # 채널 정보 로드
            self.load_channel_info(snippet)
            
        except Exception as e:
            messagebox.showerror("데이터 로드 오류", f"영상 데이터를 로드하는 중 오류가 발생했습니다:\n{str(e)}")
    
    def load_basic_info(self, snippet, content_details, analysis):
        """기본 정보 로드"""
        # 제목
        title = snippet.get('title', '제목 없음')
        self.update_text_widget(self.basic_info_fields['title'], title)
        
        # 기본 필드들
        basic_data = {
            'channel_title': snippet.get('channelTitle', '알 수 없음'),
            'video_id': self.video_data.get('id', '알 수 없음'),
            'channel_id': snippet.get('channelId', '알 수 없음'),
            'published_at': self.format_datetime(snippet.get('publishedAt', '')),
            'duration': analysis.get('formatted_duration', '00:00'),
            'video_type': analysis.get('video_type', '알 수 없음'),
            'category': self.get_category_name(snippet.get('categoryId', '')),
            'language': snippet.get('defaultLanguage', snippet.get('defaultAudioLanguage', '자동 감지'))
        }
        
        for key, value in basic_data.items():
            if key in self.basic_info_fields:
                self.basic_info_fields[key].config(text=value)
        
        # 설명
        description = snippet.get('description', '설명 없음')
        if len(description) > 500:
            description = description[:500] + "..."
        self.update_text_widget(self.basic_info_fields['description'], description)
    
    def load_statistics(self, statistics, analysis):
        """통계 정보 로드"""
        # 기본 통계
        view_count = int(statistics.get('viewCount', 0))
        like_count = int(statistics.get('likeCount', 0))
        comment_count = int(statistics.get('commentCount', 0))
        
        basic_stats = {
            'view_count': self.format_number(view_count),
            'like_count': self.format_number(like_count),
            'comment_count': self.format_number(comment_count),
            'like_rate': f"{analysis.get('like_rate', 0):.4f}%",
            'comment_rate': f"{analysis.get('comment_rate', 0):.4f}%"
        }
        
        for key, value in basic_stats.items():
            if key in self.stat_labels:
                self.stat_labels[key].config(text=value)
        
        # 성과 분석
        performance_stats = {
            'outlier_score': f"{analysis.get('outlier_score', 1.0):.2f}x",
            'outlier_category': analysis.get('outlier_category', '😐 평균'),
            'engagement_score': f"{analysis.get('engagement_score', 0):.2f}",
            'views_per_day': self.format_number(analysis.get('views_per_day', 0)),
            'growth_velocity': analysis.get('growth_velocity', {}).get('velocity_rating', '알 수 없음')
        }
        
        for key, value in performance_stats.items():
            if key in self.stat_labels:
                self.stat_labels[key].config(text=value)
        
        # 시간 분석
        published_at = self.video_data.get('snippet', {}).get('publishedAt', '')
        if published_at:
            try:
                upload_dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                current_dt = datetime.now(upload_dt.tzinfo)
                
                # 경과 시간
                elapsed = current_dt - upload_dt
                elapsed_text = self.format_time_elapsed(elapsed)
                
                # 업로드 요일 및 시간
                upload_day = upload_dt.strftime('%A')
                upload_time = upload_dt.strftime('%H:%M')
                
                time_stats = {
                    'time_elapsed': elapsed_text,
                    'upload_day': upload_day,
                    'upload_time': upload_time
                }
                
                for key, value in time_stats.items():
                    if key in self.stat_labels:
                        self.stat_labels[key].config(text=value)
                        
            except Exception as e:
                print(f"시간 분석 오류: {e}")
    
    def load_analysis_results(self, snippet, analysis):
        """분석 결과 로드"""
        # 키워드 분석
        keywords = analysis.get('keywords', [])
        keywords_text = ', '.join(keywords) if keywords else '키워드 추출 안됨'
        self.update_text_widget(self.keywords_text, keywords_text)
        
        # 제목 분석
        title = snippet.get('title', '')
        title_analysis = self.analyze_title(title)
        
        for key, value in title_analysis.items():
            if key in self.title_analysis_labels:
                self.title_analysis_labels[key].config(text=value)
        
        # 감정 분석 (analysis에 있다면)
        sentiment = analysis.get('sentiment', {})
        if sentiment:
            sentiment_data = {
                'positive': f"{sentiment.get('positive', 0):.1f}%",
                'neutral': f"{sentiment.get('neutral', 0):.1f}%",
                'negative': f"{sentiment.get('negative', 0):.1f}%"
            }
            
            for key, value in sentiment_data.items():
                if key in self.sentiment_labels:
                    self.sentiment_labels[key].config(text=value)
    
    def load_channel_info(self, snippet):
        """채널 정보 로드"""
        # 기본 채널 정보는 snippet에서 가져올 수 있는 것만
        channel_data = {
            'channel_title': snippet.get('channelTitle', '알 수 없음'),
            'subscriber_count': '정보 없음',
            'video_count': '정보 없음',
            'total_views': '정보 없음',
            'channel_created': '정보 없음'
        }
        
        for key, value in channel_data.items():
            if key in self.channel_labels:
                self.channel_labels[key].config(text=value)
        
        # 성과 비교
        analysis = self.video_data.get('analysis', {})
        current_views = int(self.video_data.get('statistics', {}).get('viewCount', 0))
        channel_avg = analysis.get('channel_avg_views', 0)
        
        comparison_data = {
            'channel_avg_views': self.format_number(channel_avg) if channel_avg > 0 else '정보 없음',
            'video_performance': self.format_number(current_views),
            'performance_ratio': f"{analysis.get('outlier_score', 1.0):.2f}x" if channel_avg > 0 else '계산 불가'
        }
        
        for key, value in comparison_data.items():
            if key in self.comparison_labels:
                self.comparison_labels[key].config(text=value)
    
    def analyze_title(self, title):
        """제목 분석"""
        import re
        
        return {
            'title_length': f"{len(title)}자",
            'word_count': f"{len(title.split())}개",
            'has_special_chars': "있음" if re.search(r'[!@#$%^&*(),.?":{}|<>]', title) else "없음",
            'has_numbers': "있음" if re.search(r'\d', title) else "없음",
            'has_emoji': "있음" if re.search(r'[😀-🙏]', title) else "없음"
        }
    
    def update_text_widget(self, text_widget, content):
        """텍스트 위젯 업데이트"""
        text_widget.config(state='normal')
        text_widget.delete('1.0', tk.END)
        text_widget.insert('1.0', content)
        text_widget.config(state='disabled')
    
    def open_in_youtube(self):
        """YouTube에서 영상 열기"""
        video_id = self.video_data.get('id', '')
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("오류", "영상 ID를 찾을 수 없습니다.")
    
    def open_channel_page(self):
        """채널 페이지 열기"""
        channel_id = self.video_data.get('snippet', {}).get('channelId', '')
        if channel_id:
            url = f"https://www.youtube.com/channel/{channel_id}"
            webbrowser.open(url)
        else:
            messagebox.showwarning("오류", "채널 ID를 찾을 수 없습니다.")
    
    def copy_video_link(self):
        """영상 링크 복사"""
        video_id = self.video_data.get('id', '')
        if video_id:
            url = f"https://www.youtube.com/watch?v={video_id}"
            self.dialog.clipboard_clear()
            self.dialog.clipboard_append(url)
            messagebox.showinfo("복사 완료", "영상 링크가 클립보드에 복사되었습니다.")
        else:
            messagebox.showwarning("오류", "영상 ID를 찾을 수 없습니다.")
    
    def close(self):
        """다이얼로그 닫기"""
        if self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()
    
    # 유틸리티 메서드들
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
    
    def format_datetime(self, datetime_str):
        """날짜시간 포맷팅"""
        if not datetime_str:
            return "알 수 없음"
        
        try:
            dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
            return dt.strftime('%Y년 %m월 %d일 %H:%M')
        except:
            return datetime_str
    
    def format_time_elapsed(self, timedelta_obj):
        """경과 시간 포맷팅"""
        total_seconds = int(timedelta_obj.total_seconds())
        
        if total_seconds < 3600:  # 1시간 미만
            minutes = total_seconds // 60
            return f"{minutes}분 전"
        elif total_seconds < 86400:  # 1일 미만
            hours = total_seconds // 3600
            return f"{hours}시간 전"
        else:  # 1일 이상
            days = total_seconds // 86400
            if days < 30:
                return f"{days}일 전"
            elif days < 365:
                months = days // 30
                return f"{months}개월 전"
            else:
                years = days // 365
                return f"{years}년 전"
    
    def get_category_name(self, category_id):
        """카테고리 ID를 이름으로 변환"""
        categories = {
            "1": "영화 및 애니메이션",
            "2": "자동차 및 차량",
            "10": "음악",
            "15": "애완동물 및 동물",
            "17": "스포츠",
            "19": "여행 및 이벤트",
            "20": "게임",
            "22": "사람 및 블로그",
            "23": "코미디",
            "24": "엔터테인먼트",
            "25": "뉴스 및 정치",
            "26": "노하우 및 스타일",
            "27": "교육",
            "28": "과학 기술",
            "29": "비영리 단체 및 사회운동"
        }
        
        return categories.get(category_id, f"카테고리 {category_id}")


# 편의 함수
def show_video_details(parent, video_data):
    """
    영상 상세 정보 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        video_data (dict): 영상 데이터
        
    Returns:
        VideoDetailsDialog: 다이얼로그 인스턴스
    """
    return VideoDetailsDialog(parent, video_data)