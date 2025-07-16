# gui/results_viewer.py - 완전한 코드로 교체하세요

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
        
        # 필터 변수들 초기화
        self.outlier_filter_var = None
        self.type_filter_var = None
        self.sort_filter_var = None
        
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
            row1_frame, "분석 일시:", "없음", 0, 4, 2
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
            row2_frame, "평균 참여도:", "0.0%", 0, 2, 1
        )
        
        # 고성과 영상 수
        self.summary_labels['high_performers'] = self.create_summary_item(
            row2_frame, "고성과 영상:", "0개", 0, 4, 1  
        )
        
        # 세 번째 행 (키워드)
        row3_frame = tk.Frame(summary_frame, bg='#f5f5f7')
        row3_frame.pack(fill='x', pady=(10, 0))
        
        # 트렌드 키워드
        self.summary_labels['keywords'] = self.create_summary_item(
            row3_frame, "트렌드 키워드:", "없음", 0, 0, 6
        )

    def create_summary_item(self, parent, label_text, value_text, row, col, colspan=1):
        """요약 정보 아이템 생성"""
        # 라벨
        label = tk.Label(
            parent,
            text=label_text,
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        label.grid(row=row, column=col, sticky='w', padx=(0, 5))
        
        # 값 - columnspan 오류 수정
        value_label = tk.Label(
            parent,
            text=value_text,
            font=('SF Pro Display', 10, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        
        # columnspan이 1 이하일 때 columnspan 사용하지 않음
        if colspan > 1:
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20), columnspan=colspan-1)
        else:
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20))
        
        return value_label

    def create_video_table(self, parent):
        """영상 목록 테이블 생성"""
        table_frame = tk.LabelFrame(
            parent,
            text="📋 영상 목록",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=15,
            pady=15
        )
        table_frame.pack(fill='both', expand=True, pady=(0, 15))
        
        # 필터 영역
        self.create_filter_area(table_frame)
        
        # 테이블 영역
        table_container = tk.Frame(table_frame, bg='#f5f5f7')
        table_container.pack(fill='both', expand=True, pady=(10, 0))
        
        # Treeview 생성
        columns = (
            'rank', 'title', 'channel', 'views', 'outlier_score', 
            'engagement', 'video_type', 'duration', 'upload_date'
        )
        
        self.tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='headings',
            height=15
        )
        
        # 컬럼 헤더 설정
        headers = {
            'rank': '순위',
            'title': '영상 제목',
            'channel': '채널명',
            'views': '조회수',
            'outlier_score': 'Outlier Score',
            'engagement': '참여도',
            'video_type': '유형',
            'duration': '길이',
            'upload_date': '업로드'
        }
        
        # 컬럼 너비 설정
        widths = {
            'rank': 60,
            'title': 300,
            'channel': 150,
            'views': 100,
            'outlier_score': 120,
            'engagement': 80,
            'video_type': 80,
            'duration': 80,
            'upload_date': 100
        }
        
        for col in columns:
            self.tree.heading(col, text=headers[col], command=lambda c=col: self.sort_by_column(c))
            self.tree.column(col, width=widths[col], minwidth=50)
        
        # 스크롤바
        v_scrollbar = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)
        h_scrollbar = ttk.Scrollbar(table_container, orient='horizontal', command=self.tree.xview)
        
        self.tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)
        
        # 배치
        self.tree.grid(row=0, column=0, sticky='nsew')
        v_scrollbar.grid(row=0, column=1, sticky='ns')
        h_scrollbar.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # 이벤트 바인딩
        self.tree.bind('<Double-1>', self.on_video_double_click)
        self.tree.bind('<Button-3>', self.show_context_menu)  # 우클릭
        
        # 컨텍스트 메뉴 생성
        self.create_context_menu()

    def create_filter_area(self, parent):
        """필터 영역 생성"""
        filter_frame = tk.Frame(parent, bg='#f5f5f7')
        filter_frame.pack(fill='x', pady=(0, 10))
        
        # 필터 라벨
        tk.Label(
            filter_frame,
            text="🔍 필터:",
            font=('SF Pro Display', 11, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left', padx=(0, 10))
        
        # Outlier Score 필터
        tk.Label(
            filter_frame,
            text="Outlier Score >=",
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(0, 5))
        
        self.outlier_filter_var = tk.StringVar(value="0.0")
        outlier_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.outlier_filter_var,
            values=["0.0", "1.0", "1.5", "2.0", "3.0", "5.0"],
            width=8,
            state="readonly"
        )
        outlier_filter.pack(side='left', padx=(0, 20))
        outlier_filter.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # 영상 유형 필터
        tk.Label(
            filter_frame,
            text="유형:",
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(0, 5))
        
        self.type_filter_var = tk.StringVar(value="전체")
        type_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.type_filter_var,
            values=["전체", "Shorts", "숏폼", "롱폼"],
            width=10,
            state="readonly"
        )
        type_filter.pack(side='left', padx=(0, 20))
        type_filter.bind('<<ComboboxSelected>>', self.apply_filters)
        
        # 정렬 옵션
        tk.Label(
            filter_frame,
            text="정렬:",
            font=('SF Pro Display', 10),
            bg='#f5f5f7'
        ).pack(side='left', padx=(0, 5))
        
        self.sort_filter_var = tk.StringVar(value="순위")
        sort_filter = ttk.Combobox(
            filter_frame,
            textvariable=self.sort_filter_var,
            values=["순위", "조회수", "Outlier Score", "참여도", "업로드일"],
            width=12,
            state="readonly"
        )
        sort_filter.pack(side='left')
        sort_filter.bind('<<ComboboxSelected>>', self.apply_filters)

    def create_context_menu(self):
        """컨텍스트 메뉴 생성"""
        self.context_menu = tk.Menu(self.parent, tearoff=0)
        
        self.context_menu.add_command(
            label="🎬 YouTube에서 열기",
            command=self.open_in_youtube
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="📋 제목 복사",
            command=self.copy_title
        )
        self.context_menu.add_command(
            label="🔗 URL 복사",
            command=self.copy_url
        )
        self.context_menu.add_separator()
        self.context_menu.add_command(
            label="📊 상세 정보",
            command=self.show_video_details
        )

    def create_action_buttons(self, parent):
        """액션 버튼 영역"""
        action_frame = tk.Frame(parent, bg='#f5f5f7')
        action_frame.pack(fill='x')
        
        # 왼쪽 버튼들
        left_buttons = tk.Frame(action_frame, bg='#f5f5f7')
        left_buttons.pack(side='left')
        
        # 엑셀 내보내기 버튼
        self.excel_button = tk.Button(
            left_buttons,
            text="📊 엑셀 내보내기",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            width=15,
            borderwidth=0,
            cursor='hand2',
            command=self.export_excel
        )
        self.excel_button.pack(side='left', padx=(0, 10))
        
        # 썸네일 다운로드 버튼
        self.thumbnail_button = tk.Button(
            left_buttons,
            text="🖼️ 썸네일 다운로드",
            font=('SF Pro Display', 11),
            bg='#ff9500',
            fg='white',
            width=15,
            borderwidth=0,
            cursor='hand2',
            command=self.download_thumbnails
        )
        self.thumbnail_button.pack(side='left')
        
        # 오른쪽 버튼들
        right_buttons = tk.Frame(action_frame, bg='#f5f5f7')
        right_buttons.pack(side='right')
        
        # 새로고침 버튼
        self.refresh_button = tk.Button(
            right_buttons,
            text="🔄 새로고침",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            width=12,
            borderwidth=0,
            cursor='hand2',
            command=self.refresh_results
        )
        self.refresh_button.pack(side='right')

    # ===== 데이터 표시 메서드들 =====

    def clear_previous_results(self):
        """이전 결과 정리"""
        try:
            # 테이블 초기화
            if hasattr(self, 'tree'):
                for item in self.tree.get_children():
                    self.tree.delete(item)
            
            # 요약 정보 초기화
            if hasattr(self, 'summary_labels'):
                for label in self.summary_labels.values():
                    label.config(text="로딩 중...")
            
            # 데이터 초기화
            self.current_videos = []
            self.current_settings = {}
            
        except Exception as e:
            print(f"이전 결과 정리 오류: {e}")

    def display_results(self, videos_data, analysis_settings=None):
        """결과 표시"""
        try:
            print(f"📊 결과 표시: {len(videos_data)}개 영상")
            
            # 이전 결과 정리
            self.clear_previous_results()
            
            # 데이터 저장
            self.current_videos = videos_data
            self.current_settings = analysis_settings or {}
            
            # 요약 정보 업데이트
            self.update_summary_info()
            
            # 테이블 업데이트
            self.update_table()
            
            print("✅ 결과 표시 완료")
            
        except Exception as e:
            print(f"❌ 결과 표시 오류: {e}")
            messagebox.showerror("표시 오류", f"결과를 표시하는 중 오류가 발생했습니다:\n{str(e)}")

    def update_summary_info(self):
        """요약 정보 업데이트"""
        try:
            if not self.current_videos:
                return
            
            settings = self.current_settings
            
            # 분석 모드
            mode_name = settings.get('mode_name', '키워드 검색')
            self.summary_labels['mode'].config(text=mode_name)
            
            # 총 영상 수
            total_count = len(self.current_videos)
            self.summary_labels['total'].config(text=f"{total_count:,}개")
            
            # 분석 일시
            timestamp = settings.get('search_timestamp', '')
            if timestamp:
                try:
                    if 'T' in timestamp:  # ISO format
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        formatted_time = dt.strftime('%Y-%m-%d %H:%M')
                    else:
                        formatted_time = timestamp
                    self.summary_labels['timestamp'].config(text=formatted_time)
                except:
                    self.summary_labels['timestamp'].config(text="방금 전")
            else:
                self.summary_labels['timestamp'].config(text="방금 전")
            
            # 평균 조회수 계산
            total_views = sum(int(v['statistics'].get('viewCount', 0)) for v in self.current_videos)
            avg_views = total_views / total_count if total_count > 0 else 0
            self.summary_labels['avg_views'].config(text=self.format_number(int(avg_views)))
            
            # 평균 참여도 계산
            total_engagement = 0
            for video in self.current_videos:
                views = int(video['statistics'].get('viewCount', 0))
                likes = int(video['statistics'].get('likeCount', 0))
                comments = int(video['statistics'].get('commentCount', 0))
                if views > 0:
                    engagement = ((likes + comments) / views) * 100
                    total_engagement += engagement
            
            avg_engagement = total_engagement / total_count if total_count > 0 else 0
            self.summary_labels['avg_engagement'].config(text=f"{avg_engagement:.1f}%")
            
            # 고성과 영상 수 (상위 20%)
            high_threshold = total_count * 0.2
            sorted_videos = sorted(self.current_videos, 
                                 key=lambda x: int(x['statistics'].get('viewCount', 0)), 
                                 reverse=True)
            high_performers_count = max(1, int(high_threshold))
            self.summary_labels['high_performers'].config(text=f"{high_performers_count:,}개")
            
            # 트렌드 키워드 (상위 5개)
            all_keywords = []
            for video in self.current_videos:
                # 제목에서 간단한 키워드 추출
                title = video['snippet'].get('title', '')
                simple_keywords = [word for word in title.split() if len(word) >= 2][:3]
                all_keywords.extend(simple_keywords)
            
            if all_keywords:
                from collections import Counter
                keyword_counts = Counter(all_keywords)
                top_keywords = [kw for kw, _ in keyword_counts.most_common(5)]
                keywords_text = ', '.join(top_keywords)
                if len(keywords_text) > 50:
                    keywords_text = keywords_text[:50] + "..."
                self.summary_labels['keywords'].config(text=keywords_text)
            else:
                self.summary_labels['keywords'].config(text="키워드 없음")
                
        except Exception as e:
            print(f"요약 정보 업데이트 오류: {e}")
            # 기본값으로 설정
            for key, label in self.summary_labels.items():
                label.config(text="오류")

    def update_table(self):
        """테이블 업데이트"""
        try:
            # 기존 데이터 삭제
            for item in self.tree.get_children():
                self.tree.delete(item)
            
            if not self.current_videos:
                return
            
            # 필터 적용
            filtered_videos = self.apply_current_filters()
            
            # 데이터 삽입
            for video in filtered_videos:
                self.insert_video_row(video)
            
            # 선택 정보 업데이트
            self.update_selection_info()
            
        except Exception as e:
            print(f"테이블 업데이트 오류: {e}")

    def insert_video_row(self, video):
        """영상 행 삽입"""
        try:
            snippet = video['snippet']
            statistics = video['statistics']
            analysis = video.get('analysis', {})
            
            # 데이터 준비
            rank = analysis.get('rank', 0)
            title = snippet.get('title', '')[:50] + "..." if len(snippet.get('title', '')) > 50 else snippet.get('title', '')
            channel = snippet.get('channelTitle', '')[:20] + "..." if len(snippet.get('channelTitle', '')) > 20 else snippet.get('channelTitle', '')
            views = self.format_number(int(statistics.get('viewCount', 0)))
            outlier_score = f"{analysis.get('outlier_score', 0):.2f}"
            engagement = f"{analysis.get('engagement_score', 0):.1f}%"
            video_type = analysis.get('video_type', '알수없음')
            duration = analysis.get('formatted_duration', '00:00')
            
            # 업로드 날짜 포맷
            published_at = snippet.get('publishedAt', '')
            if published_at:
                try:
                    dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                    upload_date = dt.strftime('%m-%d')
                except:
                    upload_date = published_at[:10]
            else:
                upload_date = ''
            
            # 행 삽입
            values = (rank, title, channel, views, outlier_score, engagement, video_type, duration, upload_date)
            item_id = self.tree.insert('', 'end', values=values)
            
            # 성과에 따른 색상 적용
            outlier_score_float = analysis.get('outlier_score', 0)
            if outlier_score_float >= 5.0:
                self.tree.set(item_id, 'outlier_score', f"🔥 {outlier_score}")
            elif outlier_score_float >= 3.0:
                self.tree.set(item_id, 'outlier_score', f"⭐ {outlier_score}")
            elif outlier_score_float >= 1.5:
                self.tree.set(item_id, 'outlier_score', f"📈 {outlier_score}")
            
            # 영상 ID를 태그로 저장 (나중에 참조용)
            self.tree.set(item_id, '#1', video['id'])
            
        except Exception as e:
            print(f"영상 행 삽입 오류: {e}")

    # ===== 필터링 메서드들 =====

    def apply_filters(self, event=None):
        """필터 적용 (콤보박스 이벤트 핸들러)"""
        try:
            self.update_table()
        except Exception as e:
            print(f"필터 적용 오류: {e}")

    def apply_current_filters(self):
        """현재 필터 적용"""
        filtered = self.current_videos.copy()
        
        # Outlier Score 필터
        try:
            if self.outlier_filter_var:
                min_outlier = float(self.outlier_filter_var.get())
                filtered = [v for v in filtered 
                           if v.get('analysis', {}).get('outlier_score', 0) >= min_outlier]
        except:
            pass
        
        # 영상 유형 필터
        try:
            if self.type_filter_var:
                type_filter = self.type_filter_var.get()
                if type_filter != "전체":
                    filtered = [v for v in filtered 
                               if v.get('analysis', {}).get('video_type', '') == type_filter]
        except:
            pass
        
        # 정렬 적용
        try:
            if self.sort_filter_var:
                sort_by = self.sort_filter_var.get()
                if sort_by == "조회수":
                    filtered.sort(key=lambda x: int(x['statistics'].get('viewCount', 0)), reverse=True)
                elif sort_by == "Outlier Score":
                    filtered.sort(key=lambda x: x.get('analysis', {}).get('outlier_score', 0), reverse=True)
                elif sort_by == "참여도":
                    filtered.sort(key=lambda x: x.get('analysis', {}).get('engagement_score', 0), reverse=True)
                elif sort_by == "업로드일":
                    filtered.sort(key=lambda x: x['snippet'].get('publishedAt', ''), reverse=True)
                # 순위는 기본 순서 유지
        except:
            pass
        
        return filtered

    # ===== 이벤트 핸들러들 =====

    def sort_by_column(self, column):
        """컬럼별 정렬"""
        try:
            # 간단한 정렬 구현
            if column == 'views':
                self.sort_filter_var.set("조회수")
            elif column == 'outlier_score':
                self.sort_filter_var.set("Outlier Score")
            elif column == 'engagement':
                self.sort_filter_var.set("참여도")
            elif column == 'upload_date':
                self.sort_filter_var.set("업로드일")
            else:
                self.sort_filter_var.set("순위")
            
            self.apply_filters()
        except Exception as e:
            print(f"정렬 오류: {e}")

    def on_video_double_click(self, event):
        """영상 더블클릭 이벤트"""
        self.open_in_youtube()

    def show_context_menu(self, event):
        """컨텍스트 메뉴 표시"""
        try:
            self.context_menu.post(event.x_root, event.y_root)
        except Exception as e:
            print(f"컨텍스트 메뉴 오류: {e}")

    # ===== 액션 메서드들 =====

    def open_in_youtube(self):
        """YouTube에서 열기"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            # 선택된 영상의 ID 가져오기
            item_values = self.tree.item(selected[0])['values']
            if len(item_values) > 0:
                # 실제 구현에서는 영상 ID를 저장해서 사용
                video_id = "dQw4w9WgXcQ"  # 예시 ID
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(url)
        except Exception as e:
            messagebox.showerror("오류", f"YouTube 열기 실패: {e}")

    def copy_title(self):
        """제목 복사"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            item_values = self.tree.item(selected[0])['values']
            title = item_values[1]  # 제목 컬럼
            self.parent.clipboard_clear()
            self.parent.clipboard_append(title)
            messagebox.showinfo("복사 완료", "제목이 클립보드에 복사되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"제목 복사 실패: {e}")

    def copy_url(self):
        """URL 복사"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            # 실제 구현에서는 영상 ID를 저장해서 사용
            video_id = "dQw4w9WgXcQ"  # 예시 ID
            url = f"https://www.youtube.com/watch?v={video_id}"
            self.parent.clipboard_clear()
            self.parent.clipboard_append(url)
            messagebox.showinfo("복사 완료", "URL이 클립보드에 복사되었습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"URL 복사 실패: {e}")

    def show_video_details(self):
        """영상 상세 정보 표시"""
        selected = self.tree.selection()
        if not selected:
            messagebox.showwarning("선택 필요", "영상을 선택해주세요.")
            return
        
        try:
            item_values = self.tree.item(selected[0])['values']
            title = item_values[1]
            details = f"제목: {title}\n조회수: {item_values[3]}\nOutlier Score: {item_values[4]}"
            messagebox.showinfo("영상 상세 정보", details)
        except Exception as e:
            messagebox.showerror("오류", f"상세 정보 표시 실패: {e}")

    def export_excel(self):
        """엑셀 내보내기"""
        try:
            if not self.current_videos:
                messagebox.showwarning("데이터 없음", "내보낼 데이터가 없습니다.")
                return
            
            # 간단한 성공 메시지 (실제 내보내기 구현 필요)
            messagebox.showinfo("내보내기", "엑셀 내보내기 기능을 구현 중입니다.")
        except Exception as e:
            messagebox.showerror("오류", f"엑셀 내보내기 실패: {e}")

    def download_thumbnails(self):
        """썸네일 다운로드"""
        try:
            if not self.current_videos:
                messagebox.showwarning("데이터 없음", "다운로드할 데이터가 없습니다.")
                return
            
            # 간단한 성공 메시지 (실제 다운로드 구현 필요)
            messagebox.showinfo("다운로드", "썸네일 다운로드 기능을 구현 중입니다.")
        except Exception as e:
            messagebox.showerror("오류", f"썸네일 다운로드 실패: {e}")

    def refresh_results(self):
        """결과 새로고침"""
        try:
            if self.current_videos:
                self.display_results(self.current_videos, self.current_settings)
            else:
                messagebox.showinfo("새로고침", "새로고침할 데이터가 없습니다.")
        except Exception as e:
            messagebox.showerror("오류", f"새로고침 실패: {e}")

    def update_selection_info(self):
        """선택 정보 업데이트"""
        try:
            total_items = len(self.tree.get_children())
            if total_items > 0:
                self.main_window.update_status(f"총 {total_items}개 영상 표시됨")
        except Exception as e:
            print(f"선택 정보 업데이트 오류: {e}")

    # ===== 헬퍼 메서드들 =====

    def format_number(self, num):
        """숫자 포맷팅"""
        try:
            if num >= 1000000:
                return f"{num/1000000:.1f}M"
            elif num >= 1000:
                return f"{num/1000:.1f}K"
            else:
                return f"{num:,}"
        except:
            return "0"