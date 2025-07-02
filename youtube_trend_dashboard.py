"""
YouTube 트렌드 실시간 대시보드
tkinter를 활용한 실시간 트렌드 모니터링 GUI
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import time
from datetime import datetime, timedelta
import json
import os

class YouTubeTrendDashboard:
    def __init__(self, root, api_key):
        self.root = root
        self.root.title("🔥 YouTube 실시간 트렌드 대시보드")
        self.root.geometry("1400x900")
        
        # 색상 테마
        self.bg_color = "#1a1a1a"
        self.card_bg = "#2d2d2d"
        self.text_color = "#ffffff"
        self.accent_color = "#ff0000"
        self.secondary_color = "#909090"
        
        self.root.configure(bg=self.bg_color)
        
        # 분석기 초기화
        from youtube_trend_analyzer import YouTubeTrendKeywordAnalyzer
        self.analyzer = YouTubeTrendKeywordAnalyzer(api_key)
        
        # 데이터 저장소
        self.current_trends = []
        self.trend_history = []
        self.auto_refresh = tk.BooleanVar(value=True)
        self.refresh_interval = 300  # 5분
        
        # GUI 구성
        self.create_widgets()
        
        # 초기 데이터 로드
        self.refresh_data()
        
        # 자동 새로고침 시작
        self.start_auto_refresh()
    
    def create_widgets(self):
        """위젯 생성"""
        # 헤더
        self.create_header()
        
        # 메인 컨테이너
        main_container = tk.Frame(self.root, bg=self.bg_color)
        main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        # 왼쪽: 실시간 트렌드
        left_frame = tk.Frame(main_container, bg=self.bg_color)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 10))
        
        self.create_trend_list(left_frame)
        
        # 오른쪽: 상세 정보
        right_frame = tk.Frame(main_container, bg=self.bg_color, width=500)
        right_frame.pack(side=tk.RIGHT, fill=tk.Y)
        right_frame.pack_propagate(False)
        
        self.create_detail_panel(right_frame)
        
        # 하단: 통계
        self.create_statistics_panel()
    
    def create_header(self):
        """헤더 생성"""
        header = tk.Frame(self.root, bg=self.card_bg, height=80)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        # 로고/제목
        title = tk.Label(header, text="🔥 YouTube 실시간 트렌드", 
                        font=("Arial", 24, "bold"),
                        bg=self.card_bg, fg=self.text_color)
        title.pack(side=tk.LEFT, padx=30, pady=20)
        
        # 컨트롤 패널
        control_frame = tk.Frame(header, bg=self.card_bg)
        control_frame.pack(side=tk.RIGHT, padx=30, pady=20)
        
        # 지역 선택
        tk.Label(control_frame, text="지역:", bg=self.card_bg, 
                fg=self.secondary_color).pack(side=tk.LEFT, padx=(0, 5))
        
        self.region_var = tk.StringVar(value="KR")
        region_combo = ttk.Combobox(control_frame, textvariable=self.region_var,
                                   values=["KR", "US", "JP", "GB"], 
                                   state="readonly", width=10)
        region_combo.pack(side=tk.LEFT, padx=(0, 20))
        
        # 자동 새로고침
        auto_check = tk.Checkbutton(control_frame, text="자동 새로고침",
                                   variable=self.auto_refresh,
                                   bg=self.card_bg, fg=self.text_color,
                                   selectcolor=self.card_bg)
        auto_check.pack(side=tk.LEFT, padx=(0, 10))
        
        # 새로고침 버튼
        refresh_btn = tk.Button(control_frame, text="🔄 새로고침",
                              bg=self.accent_color, fg="white",
                              font=("Arial", 11, "bold"),
                              borderwidth=0, padx=15, pady=5,
                              command=self.refresh_data)
        refresh_btn.pack(side=tk.LEFT)
        
        # 마지막 업데이트
        self.last_update_label = tk.Label(header, text="",
                                        bg=self.card_bg, 
                                        fg=self.secondary_color)
        self.last_update_label.pack(side=tk.RIGHT, padx=20)
    
    def create_trend_list(self, parent):
        """트렌드 리스트 생성"""
        # 제목
        title_frame = tk.Frame(parent, bg=self.card_bg)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="🏆 실시간 인기 키워드",
                font=("Arial", 16, "bold"),
                bg=self.card_bg, fg=self.text_color).pack(pady=10)
        
        # 리스트 프레임
        list_frame = tk.Frame(parent, bg=self.card_bg)
        list_frame.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤 가능한 캔버스
        canvas = tk.Canvas(list_frame, bg=self.card_bg, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=canvas.yview)
        self.trend_frame = tk.Frame(canvas, bg=self.card_bg)
        
        self.trend_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.trend_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_detail_panel(self, parent):
        """상세 정보 패널"""
        # 제목
        title_frame = tk.Frame(parent, bg=self.card_bg)
        title_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(title_frame, text="📊 키워드 상세 정보",
                font=("Arial", 16, "bold"),
                bg=self.card_bg, fg=self.text_color).pack(pady=10)
        
        # 상세 정보 프레임
        self.detail_frame = tk.Frame(parent, bg=self.card_bg)
        self.detail_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 초기 메시지
        tk.Label(self.detail_frame, text="키워드를 클릭하면\n상세 정보가 표시됩니다",
                font=("Arial", 12),
                bg=self.card_bg, fg=self.secondary_color).pack(pady=50)
    
    def create_statistics_panel(self):
        """통계 패널"""
        stats_frame = tk.Frame(self.root, bg=self.card_bg, height=150)
        stats_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=(10, 0))
        stats_frame.pack_propagate(False)
        
        # 통계 카드들
        stats_container = tk.Frame(stats_frame, bg=self.card_bg)
        stats_container.pack(expand=True)
        
        self.stat_cards = []
        stat_titles = ["총 키워드", "신규 키워드", "급상승 키워드", "분석 영상"]
        
        for i, title in enumerate(stat_titles):
            card = self.create_stat_card(stats_container, title, "0")
            card.grid(row=0, column=i, padx=20, pady=30)
            self.stat_cards.append(card)
    
    def create_stat_card(self, parent, title, value):
        """통계 카드 생성"""
        card = tk.Frame(parent, bg="#3d3d3d", width=200, height=80)
        card.pack_propagate(False)
        
        title_label = tk.Label(card, text=title,
                             font=("Arial", 10),
                             bg="#3d3d3d", fg=self.secondary_color)
        title_label.pack(pady=(15, 5))
        
        value_label = tk.Label(card, text=value,
                             font=("Arial", 20, "bold"),
                             bg="#3d3d3d", fg=self.text_color)
        value_label.pack()
        
        return {'frame': card, 'title': title_label, 'value': value_label}
    
    def refresh_data(self):
        """데이터 새로고침"""
        # 로딩 표시
        self.last_update_label.config(text="업데이트 중...")
        
        # 별도 스레드에서 실행
        thread = threading.Thread(target=self._fetch_trends)
        thread.daemon = True
        thread.start()
    
    def _fetch_trends(self):
        """트렌드 데이터 가져오기"""
        try:
            # 트렌드 분석
            report = self.analyzer.generate_trend_report(
                region_code=self.region_var.get(),
                save_to_file=False
            )
            
            # 이전 데이터와 비교
            if self.current_trends:
                self._compare_trends(report['top_trending_keywords'])
            
            self.current_trends = report['top_trending_keywords'][:30]
            
            # UI 업데이트
            self.root.after(0, lambda: self._update_ui(report))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"데이터 로드 실패: {str(e)}"))
    
    def _compare_trends(self, new_trends):
        """트렌드 변화 감지"""
        old_keywords = {item['keyword']: item['rank'] for item in self.current_trends}
        
        for item in new_trends[:30]:
            keyword = item['keyword']
            if keyword in old_keywords:
                # 순위 변화 계산
                old_rank = old_keywords[keyword]
                rank_change = old_rank - item['rank']
                item['rank_change'] = rank_change
                item['status'] = 'up' if rank_change > 0 else 'down' if rank_change < 0 else 'same'
            else:
                # 신규 키워드
                item['rank_change'] = 0
                item['status'] = 'new'
    
    def _update_ui(self, report):
        """UI 업데이트"""
        # 트렌드 리스트 업데이트
        for widget in self.trend_frame.winfo_children():
            widget.destroy()
        
        for item in self.current_trends:
            self._create_trend_item(item)
        
        # 통계 업데이트
        total_keywords = len(report['top_trending_keywords'])
        new_keywords = sum(1 for item in self.current_trends if item.get('status') == 'new')
        rising_keywords = sum(1 for item in self.current_trends if item.get('rank_change', 0) > 3)
        
        self.stat_cards[0]['value'].config(text=str(total_keywords))
        self.stat_cards[1]['value'].config(text=str(new_keywords))
        self.stat_cards[2]['value'].config(text=str(rising_keywords))
        self.stat_cards[3]['value'].config(text=str(report['total_videos_analyzed']))
        
        # 마지막 업데이트 시간
        self.last_update_label.config(
            text=f"마지막 업데이트: {datetime.now().strftime('%H:%M:%S')}"
        )
    
    def _create_trend_item(self, item):
        """트렌드 아이템 생성"""
        # 아이템 프레임
        item_frame = tk.Frame(self.trend_frame, bg="#3d3d3d", height=60)
        item_frame.pack(fill=tk.X, padx=10, pady=5)
        item_frame.pack_propagate(False)
        
        # 순위
        rank_frame = tk.Frame(item_frame, bg="#3d3d3d", width=60)
        rank_frame.pack(side=tk.LEFT, fill=tk.Y)
        rank_frame.pack_propagate(False)
        
        rank_label = tk.Label(rank_frame, text=str(item['rank']),
                            font=("Arial", 20, "bold"),
                            bg="#3d3d3d", fg=self.text_color)
        rank_label.pack(expand=True)
        
        # 변화 표시
        if item.get('status') == 'new':
            change_text = "🆕"
            change_color = "#00ff00"
        elif item.get('status') == 'up':
            change_text = f"▲{abs(item['rank_change'])}"
            change_color = "#00ff00"
        elif item.get('status') == 'down':
            change_text = f"▼{abs(item['rank_change'])}"
            change_color = "#ff6666"
        else:
            change_text = "—"
            change_color = self.secondary_color
        
        change_label = tk.Label(rank_frame, text=change_text,
                              font=("Arial", 9),
                              bg="#3d3d3d", fg=change_color)
        change_label.pack()
        
        # 키워드 정보
        info_frame = tk.Frame(item_frame, bg="#3d3d3d")
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10)
        
        keyword_label = tk.Label(info_frame, text=item['keyword'],
                               font=("Arial", 14, "bold"),
                               bg="#3d3d3d", fg=self.text_color,
                               anchor="w")
        keyword_label.pack(fill=tk.X, pady=(10, 2))
        
        stats_text = f"출현: {item['frequency']}회 | 평균 조회수: {item['avg_views']}"
        stats_label = tk.Label(info_frame, text=stats_text,
                             font=("Arial", 10),
                             bg="#3d3d3d", fg=self.secondary_color,
                             anchor="w")
        stats_label.pack(fill=tk.X)
        
        # 클릭 이벤트
        for widget in [item_frame, rank_frame, rank_label, change_label, 
                      info_frame, keyword_label, stats_label]:
            widget.bind("<Button-1>", lambda e, data=item: self.show_detail(data))
            widget.bind("<Enter>", lambda e, f=item_frame: f.config(bg="#4d4d4d"))
            widget.bind("<Leave>", lambda e, f=item_frame: f.config(bg="#3d3d3d"))
    
    def show_detail(self, item):
        """상세 정보 표시"""
        # 기존 위젯 제거
        for widget in self.detail_frame.winfo_children():
            widget.destroy()
        
        # 키워드 제목
        title = tk.Label(self.detail_frame, text=item['keyword'],
                       font=("Arial", 18, "bold"),
                       bg=self.card_bg, fg=self.accent_color)
        title.pack(pady=(0, 20))
        
        # 통계 정보
        stats_frame = tk.Frame(self.detail_frame, bg=self.card_bg)
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        stats_info = [
            ("트렌드 점수", f"{item['trend_score']}"),
            ("출현 빈도", f"{item['frequency']}회"),
            ("평균 조회수", item['avg_views']),
            ("총 조회수", item['total_views'])
        ]
        
        for label, value in stats_info:
            row = tk.Frame(stats_frame, bg=self.card_bg)
            row.pack(fill=tk.X, pady=2)
            
            tk.Label(row, text=f"{label}:",
                   font=("Arial", 10),
                   bg=self.card_bg, fg=self.secondary_color,
                   width=15, anchor="w").pack(side=tk.LEFT)
            
            tk.Label(row, text=value,
                   font=("Arial", 10, "bold"),
                   bg=self.card_bg, fg=self.text_color).pack(side=tk.LEFT)
        
        # 연관 키워드
        if item['related_keywords']:
            tk.Label(self.detail_frame, text="연관 키워드",
                   font=("Arial", 12, "bold"),
                   bg=self.card_bg, fg=self.text_color).pack(pady=(20, 10))
            
            related_frame = tk.Frame(self.detail_frame, bg=self.card_bg)
            related_frame.pack(fill=tk.X)
            
            for keyword in item['related_keywords'][:5]:
                tag = tk.Label(related_frame, text=f"#{keyword}",
                             font=("Arial", 10),
                             bg="#4d4d4d", fg=self.text_color,
                             padx=10, pady=5)
                tag.pack(side=tk.LEFT, padx=2, pady=2)
        
        # 대표 영상
        if item['top_videos']:
            tk.Label(self.detail_frame, text="대표 영상",
                   font=("Arial", 12, "bold"),
                   bg=self.card_bg, fg=self.text_color).pack(pady=(20, 10))
            
            for video in item['top_videos'][:3]:
                video_frame = tk.Frame(self.detail_frame, bg="#3d3d3d")
                video_frame.pack(fill=tk.X, pady=5, padx=10)
                
                tk.Label(video_frame, text=video['title'],
                       font=("Arial", 9),
                       bg="#3d3d3d", fg=self.text_color,
                       wraplength=400, justify="left").pack(anchor="w", padx=10, pady=(5, 2))
                
                tk.Label(video_frame, text=f"{video['channel']} | {video['views']} 조회",
                       font=("Arial", 8),
                       bg="#3d3d3d", fg=self.secondary_color).pack(anchor="w", padx=10, pady=(0, 5))
    
    def start_auto_refresh(self):
        """자동 새로고침 시작"""
        def refresh_loop():
            while True:
                if self.auto_refresh.get():
                    self.root.after(0, self.refresh_data)
                time.sleep(self.refresh_interval)
        
        thread = threading.Thread(target=refresh_loop)
        thread.daemon = True
        thread.start()


def main():
    """메인 함수"""
    root = tk.Tk()
    
    # API 키 입력
    api_key = tk.simpledialog.askstring("API Key", "YouTube API Key를 입력하세요:")
    if not api_key:
        return
    
    # 대시보드 실행
    app = YouTubeTrendDashboard(root, api_key)
    root.mainloop()


if __name__ == "__main__":
    import tkinter.simpledialog as simpledialog
    main()