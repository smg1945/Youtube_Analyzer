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
        
        # 정렬 상태 추적
        self.sort_reverse = {}
        
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
        
        # 값
        value_label = tk.Label(
            parent,
            text=value_text,
            font=('SF Pro Display', 10, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )

        if colspan > 1:
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20), columnspan=colspan-1)
        else:
            value_label.grid(row=row, column=col+1, sticky='w', padx=(0, 20))
        
        return value_label

    def create_video_table(self, parent):
        """영상 목록 테이블 생성 - 정렬 기능 추가"""
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
        
        # 컬럼 헤더 설정 및 정렬 기능 추가
        headers = {
            'rank': '순위',
            'title': '영상 제목',
            'channel': '채널명',
            'views': '조회수',
            'outlier_score': 'Outlier Score',
            'engagement': '참여도',
            'video_type': '유형',
            'duration': '길이',
            'upload_date': '업로드일'
        }
        
        for col, header in headers.items():
            self.tree.heading(col, text=header, command=lambda c=col: self.sort_column(c))
            self.sort_reverse[col] = False
            
            # 컬럼 너비 설정
            if col == 'title':
                self.tree.column(col, width=300)
            elif col == 'channel':
                self.tree.column(col, width=150)
            elif col in ['views', 'outlier_score', 'engagement']:
                self.tree.column(col, width=100)
            else:
                self.tree.column(col, width=80)
        
        # 더블클릭 이벤트 (YouTube 링크 열기)
        self.tree.bind('<Double-1>', self.on_video_double_click)
        
        # 스크롤바
        scrollbar_v = ttk.Scrollbar(table_container, orient='vertical', command=self.tree.yview)
        scrollbar_h = ttk.Scrollbar(table_container, orient='horizontal', command=self.tree.xview)
        self.tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # 그리드 레이아웃
        self.tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_v.grid(row=0, column=1, sticky='ns')
        scrollbar_h.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)

    def create_filter_area(self, parent):
        """필터 영역 생성"""
        filter_frame = tk.Frame(parent, bg='#f5f5f7')
        filter_frame.pack(fill='x', pady=(0, 10))
        
        tk.Label(
            filter_frame,
            text="🔍 빠른 필터:",
            font=('SF Pro Display', 10, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        ).pack(side='left', padx=(0, 10))
        
        # 검색 입력창
        self.search_var = tk.StringVar()
        search_entry = tk.Entry(
            filter_frame,
            textvariable=self.search_var,
            font=('SF Pro Display', 10),
            width=20
        )
        search_entry.pack(side='left', padx=(0, 10))
        search_entry.bind('<KeyRelease>', self.on_search_changed)
        
        # 유형 필터
        self.type_filter_var = tk.StringVar(value="전체")
        type_combo = ttk.Combobox(
            filter_frame,
            textvariable=self.type_filter_var,
            values=["전체", "쇼츠", "롱폼"],
            state="readonly",
            width=10
        )
        type_combo.pack(side='left', padx=(0, 10))
        type_combo.bind('<<ComboboxSelected>>', self.on_filter_changed)

    def create_action_buttons(self, parent):
        """액션 버튼들 생성 - 채널 분석 버튼 추가"""
        action_frame = tk.LabelFrame(
            parent,
            text="⚡ 액션",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=15,
            pady=10
        )
        action_frame.pack(fill='x')
        
        # 버튼들
        buttons_frame = tk.Frame(action_frame, bg='#f5f5f7')
        buttons_frame.pack(fill='x')
        
        # 선택된 영상의 채널 분석 버튼
        self.analyze_channel_btn = tk.Button(
            buttons_frame,
            text="📺 채널 분석",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.analyze_selected_channel
        )
        self.analyze_channel_btn.pack(side='left', padx=(0, 10))
        
        # 엑셀 내보내기 버튼
        self.export_btn = tk.Button(
            buttons_frame,
            text="📊 엑셀 내보내기",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.export_to_excel
        )
        self.export_btn.pack(side='left', padx=(0, 10))
        
        # 썸네일 다운로드 버튼
        self.download_btn = tk.Button(
            buttons_frame,
            text="🖼️ 썸네일 다운로드",
            font=('SF Pro Display', 11),
            bg='#ff9500',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=self.download_thumbnails
        )
        self.download_btn.pack(side='left')
        
        # 선택 정보
        self.selection_label = tk.Label(
            action_frame,
            text="선택된 영상: 0개",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.selection_label.pack(anchor='w', pady=(10, 0))

    def sort_column(self, col):
        """컬럼 기준으로 정렬"""
        try:
            # 현재 데이터 가져오기
            data = [(self.tree.set(child, col), child) for child in self.tree.get_children('')]
            
            # 정렬 (숫자 컬럼과 텍스트 컬럼 구분)
            if col in ['rank', 'views', 'outlier_score', 'engagement']:
                # 숫자 정렬
                data.sort(key=lambda x: float(x[0].replace(',', '').replace('%', '') or 0), reverse=self.sort_reverse[col])
            elif col == 'upload_date':
                # 날짜 정렬
                data.sort(key=lambda x: x[0], reverse=self.sort_reverse[col])
            else:
                # 텍스트 정렬
                data.sort(key=lambda x: x[0].lower(), reverse=self.sort_reverse[col])
            
            # 정렬된 순서로 아이템 재배치
            for index, (val, child) in enumerate(data):
                self.tree.move(child, '', index)
            
            # 정렬 방향 토글
            self.sort_reverse[col] = not self.sort_reverse[col]
            
            # 헤더에 정렬 방향 표시
            for column in self.tree['columns']:
                current_heading = self.tree.heading(column)['text']
                clean_heading = current_heading.replace(' ↑', '').replace(' ↓', '')
                
                if column == col:
                    arrow = ' ↓' if self.sort_reverse[col] else ' ↑'
                    self.tree.heading(column, text=clean_heading + arrow)
                else:
                    self.tree.heading(column, text=clean_heading)
                    
        except Exception as e:
            print(f"정렬 오류: {e}")

    def on_video_double_click(self, event):
        """영상 더블클릭 시 YouTube에서 열기"""
        try:
            selection = self.tree.selection()
            if not selection:
                return
                
            item = self.tree.item(selection[0])
            values = item['values']
            
            if not values:
                return
                
            # 현재 영상 데이터에서 실제 video_id 찾기
            title = values[1]  # 제목
            
            # 현재 영상 목록에서 해당 제목의 영상 찾기
            for video in self.current_videos:
                video_title = video['snippet']['title']
                # 제목이 잘린 경우를 고려하여 부분 매치
                if title.replace('...', '') in video_title or video_title.startswith(title.replace('...', '')):
                    video_id = video['id']
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    webbrowser.open(url)
                    return
                    
            # 찾지 못한 경우 오류 메시지
            messagebox.showwarning("경고", "해당 영상의 링크를 찾을 수 없습니다.")
            
        except Exception as e:
            print(f"영상 열기 오류: {e}")
            messagebox.showerror("오류", "영상을 열 수 없습니다.")

    def analyze_selected_channel(self):
        """선택된 영상의 채널 분석"""
        try:
            selection = self.tree.selection()
            if not selection:
                messagebox.showwarning("경고", "분석할 영상을 선택해주세요.")
                return
            
            # 선택된 영상 정보 가져오기
            item = self.tree.item(selection[0])
            values = item['values']
            
            if not values:
                return
            
            # 영상 제목으로 실제 영상 데이터 찾기
            title = values[1]  # 제목
            
            selected_video = None
            for video in self.current_videos:
                video_title = video['snippet']['title']
                if title.replace('...', '') in video_title or video_title.startswith(title.replace('...', '')):
                    selected_video = video
                    break
            
            if not selected_video:
                messagebox.showerror("오류", "선택된 영상 정보를 찾을 수 없습니다.")
                return
            
            # 채널 ID 추출
            channel_id = selected_video['snippet']['channelId']
            channel_title = selected_video['snippet']['channelTitle']
            
            # 채널 분석 탭으로 이동
            if hasattr(self.main_window, 'load_channel_tab'):
                self.main_window.load_channel_tab()
                
                # 채널 분석 탭으로 전환
                self.main_window.notebook.select(1)  # 채널 분석 탭
                
                # 채널 분석 시작
                if hasattr(self.main_window, 'channel_tab') and self.main_window.channel_tab:
                    # 채널 URL 입력란에 채널 ID 설정
                    channel_url = f"https://www.youtube.com/channel/{channel_id}"
                    self.main_window.channel_tab.set_channel_input(channel_url)
                    
                    messagebox.showinfo("채널 분석", f"'{channel_title}' 채널 분석을 시작합니다.")
            else:
                messagebox.showerror("오류", "채널 분석 탭을 로드할 수 없습니다.")
            
        except Exception as e:
            print(f"채널 분석 오류: {e}")
            messagebox.showerror("오류", "채널 분석 중 오류가 발생했습니다.")

    def on_search_changed(self, event):
        """검색어 변경 시 필터 적용"""
        self.apply_filters()

    def on_filter_changed(self, event):
        """필터 변경 시 적용"""
        self.apply_filters()

    def apply_filters(self):
        """현재 필터 적용"""
        if not self.current_videos:
            return
        
        search_text = self.search_var.get().lower()
        type_filter = self.type_filter_var.get()
        
        # 기존 데이터 삭제
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 필터링된 영상들 표시
        for video in self.current_videos:
            title = video['snippet']['title'].lower()
            video_type = video.get('analysis', {}).get('video_type', '일반')
            
            # 검색어 필터
            if search_text and search_text not in title:
                continue
            
            # 유형 필터
            if type_filter != "전체" and type_filter != video_type:
                continue
            
            # 조건을 만족하는 영상 추가
            self.insert_video_row(video)
        
        self.update_selection_info()

    def display_results(self, videos_data, analysis_settings):
        """결과 표시"""
        try:
            self.current_videos = videos_data
            self.current_settings = analysis_settings
            
            # 요약 정보 업데이트
            self.update_summary_info()
            
            # 테이블 업데이트
            self.update_table()
            
            print(f"✅ 결과 표시 완료: {len(videos_data)}개 영상")
            
        except Exception as e:
            print(f"결과 표시 오류: {e}")
            messagebox.showerror("오류", "결과를 표시할 수 없습니다.")

    def update_summary_info(self):
        """요약 정보 업데이트"""
        try:
            if not self.current_videos:
                return
            
            # 기본 통계 계산
            total_videos = len(self.current_videos)
            total_views = sum(int(video['statistics'].get('viewCount', 0)) for video in self.current_videos)
            avg_views = total_views // total_videos if total_videos > 0 else 0
            
            # 참여도 계산
            engagement_rates = []
            for video in self.current_videos:
                analysis = video.get('analysis', {})
                engagement_rates.append(analysis.get('engagement_rate', 0))
            
            avg_engagement = sum(engagement_rates) / len(engagement_rates) if engagement_rates else 0
            
            # 고성과 영상 (상위 20%)
            high_performers_count = int(total_videos * 0.2)
            
            # 정보 업데이트
            self.summary_labels['mode'].config(text="영상 검색")
            self.summary_labels['total'].config(text=f"{total_videos:,}개")
            self.summary_labels['timestamp'].config(text=datetime.now().strftime("%Y-%m-%d %H:%M"))
            self.summary_labels['avg_views'].config(text=f"{avg_views:,}")
            self.summary_labels['avg_engagement'].config(text=f"{avg_engagement:.2f}%")
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
            
            # 데이터 삽입
            for video in self.current_videos:
                self.insert_video_row(video)
            
            # 선택 정보 업데이트
            self.update_selection_info()
            
        except Exception as e:
            print(f"테이블 업데이트 오류: {e}")

    def insert_video_row(self, video):
        """영상 행 삽입 - 길이 정보 수정"""
        try:
            snippet = video['snippet']
            statistics = video['statistics']
            analysis = video.get('analysis', {})
            
            # 데이터 준비
            rank = analysis.get('rank', 0)
            title = snippet.get('title', '')[:50] + "..." if len(snippet.get('title', '')) > 50 else snippet.get('title', '')
            channel = snippet.get('channelTitle', '')[:20] + "..." if len(snippet.get('channelTitle', '')) > 20 else snippet.get('channelTitle', '')
            views = self.format_number(int(statistics.get('viewCount', 0)))
            outlier_score = f"{analysis.get('outlier_score', 0):.1f}"
            engagement = f"{analysis.get('engagement_rate', 0):.2f}%"
            video_type = analysis.get('video_type', '일반')
            
            # 영상 길이 - parse_duration 결과 사용
            duration = video.get('parsed_duration', '00:00')
            
            upload_date = snippet.get('publishedAt', '')[:10]
            
            # 테이블에 삽입
            item_id = self.tree.insert('', 'end', values=(
                rank, title, channel, views, outlier_score, 
                engagement, video_type, duration, upload_date
            ))
            
            # 영상 데이터를 아이템에 연결 (추후 사용을 위해)
            self.tree.set(item_id, 'video_data', video)
            
        except Exception as e:
            print(f"영상 행 삽입 오류: {e}")

    def format_number(self, number):
        """숫자 포맷팅 (천 단위 구분)"""
        try:
            return f"{number:,}"
        except:
            return str(number)

    def update_selection_info(self):
        """선택 정보 업데이트"""
        try:
            total_items = len(self.tree.get_children())
            self.selection_label.config(text=f"총 영상: {total_items}개")
        except Exception as e:
            print(f"선택 정보 업데이트 오류: {e}")

    def export_to_excel(self):
        """엑셀로 내보내기"""
        try:
            if not self.current_videos:
                messagebox.showwarning("경고", "내보낼 데이터가 없습니다.")
                return
            
            # TODO: 엑셀 내보내기 구현
            messagebox.showinfo("내보내기", "엑셀 내보내기 기능을 구현중입니다.")
            
        except Exception as e:
            print(f"엑셀 내보내기 오류: {e}")
            messagebox.showerror("오류", "엑셀 내보내기 중 오류가 발생했습니다.")

    def download_thumbnails(self):
        """썸네일 다운로드"""
        try:
            if not self.current_videos:
                messagebox.showwarning("경고", "다운로드할 데이터가 없습니다.")
                return
            
            # TODO: 썸네일 다운로드 구현
            messagebox.showinfo("다운로드", "썸네일 다운로드 기능을 구현중입니다.")
            
        except Exception as e:
            print(f"썸네일 다운로드 오류: {e}")
            messagebox.showerror("오류", "썸네일 다운로드 중 오류가 발생했습니다.")

    def display_channel_analysis(self, channel_data):
        """채널 분석 결과 표시"""
        try:
            # TODO: 채널 분석 결과 표시 구현
            print("📺 채널 분석 결과 표시 (구현 예정)")
            
        except Exception as e:
            print(f"채널 분석 결과 표시 오류: {e}")