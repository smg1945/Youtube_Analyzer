"""
결과 뷰어 모듈
검색 결과 및 분석 결과 표시 담당
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser
from datetime import datetime

class ResultsViewer:
    """결과 뷰어 클래스"""
    
    def __init__(self, parent, main_window):
        """
        결과 뷰어 초기화
        
        Args:
            parent: 부모 위젯
            main_window: 메인 창 인스턴스
        """
        self.parent = parent
        self.main_window = main_window
        
        # 현재 표시 중인 데이터
        self.current_videos = []
        self.current_settings = {}
        
        self.create_layout()
        print("✅ 결과 뷰어 초기화 완료")
    
    def create_layout(self):
        """레이아웃 생성"""
        # 메인 컨테이너
        main_container = tk.Frame(self.parent, bg='#f5f5f7')
        main_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 상단: 결과 요약 정보
        self.create_summary_area(main_container)
        
        # 중간: 영상 목록 테이블
        self.create_video_table(main_container)
        
        # 하단: 액션 버튼들
        self.create_action_buttons(main_container)
    
    def create_summary_area(self, parent):
        """결과 요약 영역"""
        summary_frame = tk.LabelFrame(
            parent,
            text="📊 분석 요약",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        summary_frame.pack(fill='x', pady=(0, 15))
        
        # 요약 정보를 표시할 라벨들
        self.summary_labels = {}
        
        # 첫 번째 행
        row1_frame = tk.Frame(summary_frame, bg='#f5f5f7')
        row1_frame.pack(fill='x', pady=(0, 10))
        
        # 분석 모드
        self.summary_labels['mode'] = self.create_summary_item(
            row1_frame, "분석 모드:", "없음", 0, 0, 2
        )
        
        # 총 영상 수
        self.summary_labels['total'] = self.create_summary_item(
            row1_frame, "총 영상:", "0개", 0, 2, 1
        )
        
        # 분석 일시
        self.summary_labels['timestamp'] = self.create_summary_item(
            row1_frame, "분석 일시:", "없음", 0, 3, 2
        )
        
        # 두 번째 행
        row2_frame = tk.Frame(summary_frame, bg='#f5f5f7')
        row2_frame.pack(fill='x')
        
        # 평균 조회수
        self.summary_labels['avg_views'] = self.create_summary_item(
            row2_frame, "평균 조회수:", "0", 0, 0, 1
        )
        
        # 평균 참여도
        self.summary_labels['avg_engagement'] = self.create_summary_item(
            row2_frame, "평균 참여도:", "0.0", 0, 1, 1
        )
        
        # 바이럴 영상 수
        self.summary_labels['viral_count'] = self.create_summary_item(
            row2_frame, "바이럴 영상:", "0개", 0, 2, 1
        )
        
        # 상위 성과 영상
        self.summary_labels['top_performer'] = self.create_summary_item(
            row2_frame, "최고 성과:", "없음", 0, 3, 2
        )
    
    def create_summary_item(self, parent, label_text, value_text, row, col, colspan=1):
        """요약 아이템 생성"""
        # 라벨
        label = tk.Label(
            parent,
            text=label_text,
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        label.grid(row=row, column=col, sticky='w', padx=(0, 5))
        
        # 값
        value_label = tk.Label(
            parent,
            text=value_text,
            font=('SF Pro Display', 10, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20), columnspan=colspan-1)
        
        return value_label
    
    def create_video_table(self, parent):
        """영상 목록 테이블"""
        table_frame = tk.LabelFrame(
            parent,
            text="🎬 영상 목록",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=10,
            pady=10
        )
        table_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # 테이블 생성
        self.create_treeview(table_frame)
        
        # 정렬 및 필터 옵션
        self.create_table_controls(table_frame)
    
    def create_treeview(self, parent):
        """트리뷰 테이블 생성"""
        # 테이블 컨테이너
        table_container = tk.Frame(parent, bg='#f5f5f7')
        table_container.pack(fill='both', expand=True)
        
        # 컬럼 정의
        columns = (
            'rank', 'title', 'channel', 'views', 'outlier_score', 
            'engagement', 'video_type', 'duration', 'upload_date'
        )
        
        # 트리뷰 생성
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='headings',
            height=15
        )
        
        # 컬럼 헤더 설정
        column_configs = {
            'rank': ('순위', 50, 'center'),
            'title': ('제목', 300, 'w'),
            'channel': ('채널', 150, 'w'),
            'views': ('조회수', 100, 'e'),
            'outlier_score': ('Outlier', 80, 'center'),
            'engagement': ('참여도', 80, 'center'),
            'video_type': ('유형', 60, 'center'),
            'duration': ('길이', 80, 'center'),
            'upload_date': ('업로드', 100, 'center')
        }
        
        for col, (text, width, anchor) in column_configs.items():
            self.tree.heading(col, text=text, command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=width, anchor=anchor)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_container, orient='horizontal', command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 레이아웃
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # 더블클릭 이벤트
        self.tree.bind('<Double-1>', self.on_video_double_click)
        
        # 우클릭 컨텍스트 메뉴
        self.tree.bind('<Button-3>', self.show_context_menu)
        
        # 컨텍스트 메뉴 생성
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="🔗 YouTube에서 열기", command=self.open_in_youtube)
        self.context_menu.add_command(label="📋 링크 복사", command=self.copy_video_link)
        self.context_menu.add_separator()
        self.context_menu.add_command(label="📊 상세 정보", command=self.show_video_details)
    
    def create_table_controls(self, parent):
        """테이블 컨트롤"""
        controls_frame = tk.Frame(parent, bg='#f5f5f7')
        controls_frame.pack(fill='x', pady=(10, 0))
        
        # 필터 옵션
        filter_frame = tk.Frame(controls_frame, bg='#f5f5f7')
        filter_frame.pack(side='left')
        
        tk.Label(
            filter_frame,
            text="필터:",
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(0, 5))
        
        # 영상 유형 필터
        self.filter_type_var = tk.StringVar(value="전체")
        type_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_type_var,
            values=["전체", "쇼츠", "롱폼"],
            state="readonly",
            width=8
        )
        type_filter.pack(side='left', padx=(0, 10))
        type_filter.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # Outlier Score 필터
        tk.Label(
            filter_frame,
            text="Outlier Score:",
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(10, 5))
        
        self.filter_outlier_var = tk.StringVar(value="전체")
        outlier_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.filter_outlier_var,
            values=["전체", "3.0x 이상", "1.5x 이상", "1.0x 이상"],
            state="readonly",
            width=10
        )
        outlier_filter.pack(side='left', padx=(0, 10))
        outlier_filter.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # 정보 표시
        info_frame = tk.Frame(controls_frame, bg='#f5f5f7')
        info_frame.pack(side='right')
        
        self.info_label = tk.Label(
            info_frame,
            text="표시: 0/0개",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.info_label.pack(side='right')
    
    def create_action_buttons(self, parent):
        """액션 버튼들"""
        button_frame = tk.Frame(parent, bg='#f5f5f7')
        button_frame.pack(fill='x')
        
        # 선택 영상 액션
        selection_frame = tk.Frame(button_frame, bg='#f5f5f7')
        selection_frame.pack(side='left')
        
        tk.Button(
            selection_frame,
            text="🔗 선택 영상 열기",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.open_selected_videos
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            selection_frame,
            text="📊 선택 영상 상세보기",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.show_selected_details
        ).pack(side='left', padx=(0, 10))
        
        # 전체 액션
        export_frame = tk.Frame(button_frame, bg='#f5f5f7')
        export_frame.pack(side='right')
        
        tk.Button(
            export_frame,
            text="📋 통계 보기",
            font=('SF Pro Display', 11),
            bg='#ff9500',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.show_statistics
        ).pack(side='left', padx=(0, 10))
        
        tk.Button(
            export_frame,
            text="🔄 새로고침",
            font=('SF Pro Display', 11),
            bg='#86868b',
            fg='white',
            borderwidth=0,
            cursor='hand2',
            command=self.refresh_view
        ).pack(side='left')
    
    def display_results(self, videos_data, analysis_settings):
        """검색 결과 표시"""
        self.current_videos = videos_data
        self.current_settings = analysis_settings
        
        # 요약 정보 업데이트
        self.update_summary()
        
        # 테이블 데이터 업데이트
        self.update_table()
        
        print(f"✅ {len(videos_data)}개 영상 결과 표시 완료")
    
    def display_channel_analysis(self, channel_data):
        """채널 분석 결과 표시"""
        # 채널 분석 결과를 영상 목록 형식으로 변환
        if 'videos' in channel_data:
            self.current_videos = channel_data['videos']
            
            # 분석 설정 구성
            self.current_settings = {
                'mode': 'channel_analysis',
                'mode_name': f"채널 분석: {channel_data.get('channel_info', {}).get('snippet', {}).get('title', 'Unknown')}",
                'total_found': len(channel_data['videos']),
                'search_timestamp': datetime.now().isoformat()
            }
            
            # 표시 업데이트
            self.update_summary()
            self.update_table()
            
            print(f"✅ 채널 분석 결과 표시 완료: {len(self.current_videos)}개 영상")
    
    def update_summary(self):
        """요약 정보 업데이트"""
        if not self.current_videos:
            return
        
        # 기본 통계 계산
        total_videos = len(self.current_videos)
        total_views = sum(int(v['statistics'].get('viewCount', 0)) for v in self.current_videos)
        avg_views = total_views // total_videos if total_videos > 0 else 0
        
        # 참여도 통계
        engagement_scores = [v.get('analysis', {}).get('engagement_score', 0) for v in self.current_videos]
        avg_engagement = sum(engagement_scores) / len(engagement_scores) if engagement_scores else 0
        
        # 바이럴 영상 수 (Outlier Score 3.0 이상)
        viral_count = sum(1 for v in self.current_videos 
                         if v.get('analysis', {}).get('outlier_score', 0) >= 3.0)
        
        # 최고 성과 영상
        top_performer = max(self.current_videos, 
                           key=lambda x: x.get('analysis', {}).get('outlier_score', 0))
        top_title = top_performer['snippet']['title'][:30] + "..." if len(top_performer['snippet']['title']) > 30 else top_performer['snippet']['title']
        
        # 분석 일시
        timestamp = self.current_settings.get('search_timestamp', '')
        if timestamp:
            dt = datetime.fromisoformat(timestamp.replace('Z', ''))
            formatted_time = dt.strftime('%Y-%m-%d %H:%M')
        else:
            formatted_time = "알 수 없음"
        
        # UI 업데이트
        self.summary_labels['mode'].config(text=self.current_settings.get('mode_name', '알 수 없음'))
        self.summary_labels['total'].config(text=f"{total_videos:,}개")
        self.summary_labels['timestamp'].config(text=formatted_time)
        self.summary_labels['avg_views'].config(text=self.format_number(avg_views))
        self.summary_labels['avg_engagement'].config(text=f"{avg_engagement:.1f}")
        self.summary_labels['viral_count'].config(text=f"{viral_count}개")
        self.summary_labels['top_performer'].config(text=top_title)
    
    def update_table(self):
        """테이블 업데이트"""
        # 기존 데이터 클리어
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 필터 적용된 데이터 가져오기
        filtered_videos = self.get_filtered_videos()
        
        # 데이터 삽입
        for video in filtered_videos:
            analysis = video.get('analysis', {})
            snippet = video['snippet']
            stats = video['statistics']
            
            # 업로드 날짜 포맷팅
            upload_date = snippet.get('publishedAt', '')
            if upload_date:
                dt = datetime.fromisoformat(upload_date.replace('Z', ''))
                formatted_date = dt.strftime('%m-%d')
            else:
                formatted_date = "알수없음"
            
            # 테이블 행 데이터
            values = (
                analysis.get('rank', 0),
                snippet.get('title', '')[:50] + ("..." if len(snippet.get('title', '')) > 50 else ""),
                snippet.get('channelTitle', '')[:20] + ("..." if len(snippet.get('channelTitle', '')) > 20 else ""),
                self.format_number(int(stats.get('viewCount', 0))),
                f"{analysis.get('outlier_score', 1.0):.1f}x",
                f"{analysis.get('engagement_score', 0):.1f}",
                analysis.get('video_type', '알수없음'),
                analysis.get('formatted_duration', '00:00'),
                formatted_date
            )
            
            # 행 삽입
            item = self.tree.insert('', 'end', values=values)
            
            # Outlier Score에 따른 행 색상
            outlier_score = analysis.get('outlier_score', 1.0)
            if outlier_score >= 5.0:
                self.tree.set(item, 'outlier_score', f"🔥 {outlier_score:.1f}x")
            elif outlier_score >= 3.0:
                self.tree.set(item, 'outlier_score', f"⭐ {outlier_score:.1f}x")
            elif outlier_score >= 1.5:
                self.tree.set(item, 'outlier_score', f"📈 {outlier_score:.1f}x")
            elif outlier_score < 0.7:
                self.tree.set(item, 'outlier_score', f"📉 {outlier_score:.1f}x")
        
        # 정보 업데이트
        self.info_label.config(text=f"표시: {len(filtered_videos):,}/{len(self.current_videos):,}개")
    
    def get_filtered_videos(self):
        """필터가 적용된 영상 목록 반환"""
        if not self.current_videos:
            return []
        
        filtered = self.current_videos.copy()
        
        # 영상 유형 필터
        type_filter = self.filter_type_var.get()
        if type_filter != "전체":
            type_map = {"쇼츠": "쇼츠", "롱폼": "롱폼"}
            filtered = [v for v in filtered 
                       if v.get('analysis', {}).get('video_type') == type_map[type_filter]]
        
        # Outlier Score 필터
        outlier_filter = self.filter_outlier_var.get()
        if outlier_filter != "전체":
            threshold_map = {"3.0x 이상": 3.0, "1.5x 이상": 1.5, "1.0x 이상": 1.0}
            threshold = threshold_map[outlier_filter]
            filtered = [v for v in filtered 
                       if v.get('analysis', {}).get('outlier_score', 0) >= threshold]
        
        return filtered
    
    def sort_by_column(self, column):
        """컬럼별 정렬"""
        # 현재 정렬 상태 확인
        current_sort = getattr(self, '_current_sort', None)
        reverse = current_sort == column
        
        # 정렬 키 함수 정의
        def sort_key(video):
            analysis = video.get('analysis', {})
            snippet = video['snippet']
            stats = video['statistics']
            
            if column == 'rank':
                return analysis.get('rank', 999)
            elif column == 'title':
                return snippet.get('title', '').lower()
            elif column == 'channel':
                return snippet.get('channelTitle', '').lower()
            elif column == 'views':
                return int(stats.get('viewCount', 0))
            elif column == 'outlier_score':
                return analysis.get('outlier_score', 0)
            elif column == 'engagement':
                return analysis.get('engagement_score', 0)
            elif column == 'video_type':
                return analysis.get('video_type', '')
            elif column == 'duration':
                return analysis.get('duration_seconds', 0)
            elif column == 'upload_date':
                return snippet.get('publishedAt', '')
            else:
                return 0
        
        # 정렬 실행
        try:
            self.current_videos.sort(key=sort_key, reverse=reverse)
            self._current_sort = None if reverse else column
            self.update_table()
        except Exception as e:
            print(f"정렬 오류: {e}")
    
    def apply_filters(self, event=None):
        """필터 적용"""
        self.update_table()
    
    def on_video_double_click(self, event):
        """영상 더블클릭 이벤트"""
        self.open_in_youtube()
    
    def show_context_menu(self, event):
        """컨텍스트 메뉴 표시"""
        # 선택된 아이템 확인
        item = self.tree.selection()
        if item:
            self.context_menu.post(event.x_root, event.y_root)
    
    def open_in_youtube(self):
        """YouTube에서 열기"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            # 선택된 영상의 인덱스 찾기
            item_values = self.tree.item(selected[0])['values']
            rank = int(item_values[0])
            
            # 해당 영상 찾기
            video = next((v for v in self.current_videos 
                         if v.get('analysis', {}).get('rank') == rank), None)
            
            if video:
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                webbrowser.open(video_url)
            
        except Exception as e:
            self.main_window.show_error("링크 열기 실패", str(e))
    
    def copy_video_link(self):
        """영상 링크 복사"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            # 선택된 영상의 링크 클립보드에 복사
            item_values = self.tree.item(selected[0])['values']
            rank = int(item_values[0])
            
            video = next((v for v in self.current_videos 
                         if v.get('analysis', {}).get('rank') == rank), None)
            
            if video:
                video_url = f"https://www.youtube.com/watch?v={video['id']}"
                self.main_window.root.clipboard_clear()
                self.main_window.root.clipboard_append(video_url)
                self.main_window.update_status("영상 링크가 클립보드에 복사되었습니다.")
            
        except Exception as e:
            self.main_window.show_error("링크 복사 실패", str(e))
    
    def show_video_details(self):
        """영상 상세 정보 표시"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            item_values = self.tree.item(selected[0])['values']
            rank = int(item_values[0])
            
            video = next((v for v in self.current_videos 
                         if v.get('analysis', {}).get('rank') == rank), None)
            
            if video:
                self.show_video_details_dialog(video)
            
        except Exception as e:
            self.main_window.show_error("상세 정보 표시 실패", str(e))
    
    def show_video_details_dialog(self, video):
        """영상 상세 정보 다이얼로그"""
        # 상세 정보 창 생성
        detail_window = tk.Toplevel(self.main_window.root)
        detail_window.title("영상 상세 정보")
        detail_window.geometry("500x600")
        detail_window.configure(bg='#f5f5f7')
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(detail_window, bg='#f5f5f7')
        scrollbar = ttk.Scrollbar(detail_window, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f7')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 영상 정보 표시
        snippet = video['snippet']
        stats = video['statistics']
        analysis = video.get('analysis', {})
        
        details = [
            ("제목", snippet.get('title', '')),
            ("채널", snippet.get('channelTitle', '')),
            ("업로드 일시", snippet.get('publishedAt', '')),
            ("조회수", self.format_number(int(stats.get('viewCount', 0)))),
            ("좋아요", self.format_number(int(stats.get('likeCount', 0)))),
            ("댓글수", self.format_number(int(stats.get('commentCount', 0)))),
            ("영상 길이", analysis.get('formatted_duration', '00:00')),
            ("영상 유형", analysis.get('video_type', '알수없음')),
            ("Outlier Score", f"{analysis.get('outlier_score', 1.0):.2f}x"),
            ("참여도 점수", f"{analysis.get('engagement_score', 0):.2f}"),
            ("좋아요율", f"{analysis.get('like_rate', 0):.4f}%"),
            ("댓글율", f"{analysis.get('comment_rate', 0):.4f}%"),
            ("일평균 조회수", self.format_number(analysis.get('views_per_day', 0))),
            ("핵심 키워드", ', '.join(analysis.get('keywords', []))),
        ]
        
        for i, (label, value) in enumerate(details):
            tk.Label(
                scrollable_frame,
                text=f"{label}:",
                font=('SF Pro Display', 11, 'bold'),
                bg='#f5f5f7',
                anchor='w'
            ).grid(row=i, column=0, sticky='w', padx=10, pady=5)
            
            value_label = tk.Label(
                scrollable_frame,
                text=str(value),
                font=('SF Pro Display', 11),
                bg='#f5f5f7',
                anchor='w',
                wraplength=300
            )
            value_label.grid(row=i, column=1, sticky='w', padx=10, pady=5)
        
        # 레이아웃
        canvas.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")
    
    def open_selected_videos(self):
        """선택된 영상들 열기"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        # 최대 5개까지만 열기
        if len(selected) > 5:
            result = messagebox.askyesno(
                "많은 영상 선택",
                f"{len(selected)}개 영상이 선택되었습니다.\n"
                f"최대 5개까지만 열 수 있습니다.\n"
                f"처음 5개만 여시겠습니까?"
            )
            if not result:
                return
            selected = selected[:5]
        
        # 선택된 영상들 열기
        for item in selected:
            try:
                item_values = self.tree.item(item)['values']
                rank = int(item_values[0])
                
                video = next((v for v in self.current_videos 
                             if v.get('analysis', {}).get('rank') == rank), None)
                
                if video:
                    video_url = f"https://www.youtube.com/watch?v={video['id']}"
                    webbrowser.open(video_url)
                
            except Exception as e:
                print(f"영상 열기 오류: {e}")
    
    def show_selected_details(self):
        """선택된 영상들 상세보기"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        # 선택된 영상 정보를 요약해서 표시
        selected_videos = []
        for item in selected:
            try:
                item_values = self.tree.item(item)['values']
                rank = int(item_values[0])
                
                video = next((v for v in self.current_videos 
                             if v.get('analysis', {}).get('rank') == rank), None)
                
                if video:
                    selected_videos.append(video)
                
            except Exception as e:
                print(f"영상 정보 추출 오류: {e}")
        
        if selected_videos:
            self.show_multiple_videos_summary(selected_videos)
    
    def show_multiple_videos_summary(self, videos):
        """여러 영상 요약 정보 표시"""
        # 요약 창 생성
        summary_window = tk.Toplevel(self.main_window.root)
        summary_window.title(f"선택된 영상 요약 ({len(videos)}개)")
        summary_window.geometry("600x400")
        summary_window.configure(bg='#f5f5f7')
        
        # 요약 정보 계산
        total_views = sum(int(v['statistics'].get('viewCount', 0)) for v in videos)
        avg_outlier = sum(v.get('analysis', {}).get('outlier_score', 0) for v in videos) / len(videos)
        avg_engagement = sum(v.get('analysis', {}).get('engagement_score', 0) for v in videos) / len(videos)
        
        # 요약 텍스트 생성
        summary_text = f"""
선택된 영상 분석 요약

📊 기본 통계:
• 총 영상 수: {len(videos):,}개
• 총 조회수: {self.format_number(total_views)}
• 평균 Outlier Score: {avg_outlier:.2f}x
• 평균 참여도: {avg_engagement:.2f}

🎬 영상 목록:
"""
        
        for i, video in enumerate(videos[:10], 1):  # 최대 10개만 표시
            title = video['snippet']['title'][:50]
            views = self.format_number(int(video['statistics'].get('viewCount', 0)))
            outlier = video.get('analysis', {}).get('outlier_score', 0)
            summary_text += f"{i}. {title} | {views} 조회수 | {outlier:.1f}x\n"
        
        if len(videos) > 10:
            summary_text += f"... 외 {len(videos) - 10}개 영상\n"
        
        # 텍스트 위젯
        text_widget = tk.Text(
            summary_window,
            font=('SF Pro Display', 11),
            bg='white',
            wrap='word',
            padx=20,
            pady=20
        )
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        text_widget.insert('1.0', summary_text)
        text_widget.config(state='disabled')
    
    def show_statistics(self):
        """전체 통계 보기"""
        if not self.current_videos:
            messagebox.showwarning("데이터 없음", "표시할 통계가 없습니다.")
            return
        
        # 통계 계산
        from data import StatisticsCalculator
        
        calc = StatisticsCalculator()
        
        # 조회수 통계
        view_counts = [int(v['statistics'].get('viewCount', 0)) for v in self.current_videos]
        view_stats = calc.calculate_descriptive_stats(view_counts)
        
        # 참여도 통계
        engagement_scores = [v.get('analysis', {}).get('engagement_score', 0) for v in self.current_videos]
        engagement_stats = calc.calculate_descriptive_stats(engagement_scores)
        
        # 통계 창 표시
        self.show_statistics_dialog(view_stats, engagement_stats)
    
    def show_statistics_dialog(self, view_stats, engagement_stats):
        """통계 다이얼로그 표시"""
        stats_window = tk.Toplevel(self.main_window.root)
        stats_window.title("상세 통계")
        stats_window.geometry("500x400")
        stats_window.configure(bg='#f5f5f7')
        
        # 통계 텍스트 생성
        stats_text = f"""
📊 상세 통계 분석

🔍 조회수 통계:
• 평균: {self.format_number(view_stats['mean'])}
• 중간값: {self.format_number(view_stats['median'])}
• 최대: {self.format_number(view_stats['max'])}
• 최소: {self.format_number(view_stats['min'])}
• 표준편차: {self.format_number(view_stats['std_dev'])}

⚡ 참여도 통계:
• 평균: {engagement_stats['mean']:.2f}
• 중간값: {engagement_stats['median']:.2f}
• 최대: {engagement_stats['max']:.2f}
• 최소: {engagement_stats['min']:.2f}
• 표준편차: {engagement_stats['std_dev']:.2f}

📈 성과 분포:
• 바이럴 영상 (5.0x+): {sum(1 for v in self.current_videos if v.get('analysis', {}).get('outlier_score', 0) >= 5.0)}개
• 히트 영상 (3.0x+): {sum(1 for v in self.current_videos if v.get('analysis', {}).get('outlier_score', 0) >= 3.0)}개
• 양호 영상 (1.5x+): {sum(1 for v in self.current_videos if v.get('analysis', {}).get('outlier_score', 0) >= 1.5)}개

🎬 영상 유형:
• 쇼츠: {sum(1 for v in self.current_videos if v.get('analysis', {}).get('video_type') == '쇼츠')}개
• 롱폼: {sum(1 for v in self.current_videos if v.get('analysis', {}).get('video_type') == '롱폼')}개
        """
        
        # 텍스트 위젯
        text_widget = tk.Text(
            stats_window,
            font=('SF Pro Display', 11),
            bg='white',
            wrap='word',
            padx=20,
            pady=20
        )
        text_widget.pack(fill='both', expand=True, padx=20, pady=20)
        text_widget.insert('1.0', stats_text)
        text_widget.config(state='disabled')
    
    def refresh_view(self):
        """뷰 새로고침"""
        if self.current_videos:
            self.update_summary()
            self.update_table()
            self.main_window.update_status("결과 뷰가 새로고침되었습니다.")
    
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