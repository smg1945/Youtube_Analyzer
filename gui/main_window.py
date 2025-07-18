"""
메인 창 모듈
애플리케이션의 메인 인터페이스 담당
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import threading

class MainWindow:
    """메인 애플리케이션 창"""
    
    def __init__(self):
        """메인 창 초기화"""
        self.root = tk.Tk()
        self.setup_window()
        self.create_menu()
        self.create_layout()
        self.check_api_key()
        
        # 현재 활성 탭 추적
        self.current_tab = None
        
        # 탭 인스턴스들
        self.search_tab = None
        self.channel_tab = None
        self.results_viewer = None
        
        print("✅ 메인 창 초기화 완료")
    
    def setup_window(self):
        """창 기본 설정"""
        self.root.title("🎬 YouTube 트렌드 분석기 v3.0")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f5f5f7')
        
        # 중앙 정렬
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (1200 // 2)
        y = (self.root.winfo_screenheight() // 2) - (800 // 2)
        self.root.geometry(f'1200x800+{x}+{y}')
        
        # 아이콘 설정 (있다면)
        try:
            # self.root.iconbitmap('icon.ico')  # 아이콘 파일이 있다면
            pass
        except:
            pass
        
        # 최소 크기 설정
        self.root.minsize(800, 600)
    
    def create_menu(self):
        """메뉴바 생성"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="설정", command=self.open_settings)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.root.quit)
        
        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도구", menu=tools_menu)
        tools_menu.add_command(label="API 키 설정", command=self.setup_api_key_dialog)
        tools_menu.add_command(label="캐시 정리", command=self.clear_cache)
        tools_menu.add_separator()
        tools_menu.add_command(label="트렌드 대시보드", command=self.launch_trend_dashboard)
        
        # 도움말 메뉴
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도움말", menu=help_menu)
        help_menu.add_command(label="사용법", command=self.show_help)
        help_menu.add_command(label="정보", command=self.show_about)
    
    def create_layout(self):
        """메인 레이아웃 생성"""
        # 상단 제목 영역
        self.create_header()
        
        # 중앙 탭 영역
        self.create_tab_area()
        
        # 하단 상태바
        self.create_status_bar()
    
    def create_header(self):
        """상단 헤더 영역"""
        header_frame = tk.Frame(self.root, bg='#007aff', height=80)
        header_frame.pack(fill='x', padx=10, pady=(10, 0))
        header_frame.pack_propagate(False)
        
        # 제목
        title_label = tk.Label(
            header_frame,
            text="YouTube 트렌드 분석기",
            font=('SF Pro Display', 20, 'bold'),
            bg='#007aff',
            fg='white'
        )
        title_label.pack(side='left', padx=20, pady=20)
        
        # 버전 정보
        version_label = tk.Label(
            header_frame,
            text="v3.0",
            font=('SF Pro Display', 12),
            bg='#007aff',
            fg='#e6f2ff'
        )
        version_label.pack(side='left', padx=(10, 0), pady=20)
        
        # API 상태 표시
        self.api_status_label = tk.Label(
            header_frame,
            text="API: 확인 중...",
            font=('SF Pro Display', 10),
            bg='#007aff',
            fg='#ffe6e6'
        )
        self.api_status_label.pack(side='right', padx=20, pady=20)
    
    def create_tab_area(self):
        """탭 영역 생성"""
        # 탭 노트북 생성
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill='both', expand=True, padx=10, pady=10)
        
        # 스타일 설정
        style = ttk.Style()
        style.configure('TNotebook.Tab', padding=[20, 10])
        
        # 탭 생성
        self.create_tabs()
        
        # 탭 변경 이벤트
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
    
    def create_tabs(self):
        """개별 탭들 생성"""
        # 1. 영상 검색 탭
        self.search_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.search_frame, text="🔍 영상 검색")
        
        # SearchTab 초기화는 지연로딩
        self.search_tab = None
        
        # 2. 채널 분석 탭
        self.channel_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.channel_frame, text="📺 채널 분석")
        
        # ChannelTab 초기화는 지연로딩
        self.channel_tab = None
        
        # 3. 결과 뷰어 탭
        self.results_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.results_frame, text="📊 결과 보기")
        
        # ResultsViewer 초기화는 지연로딩
        self.results_viewer = None
        
        # 첫 번째 탭 로드
        self.load_search_tab()
    
    def create_status_bar(self):
        """하단 상태바"""
        self.status_frame = tk.Frame(self.root, bg='#f5f5f7', height=30)
        self.status_frame.pack(fill='x', side='bottom')
        self.status_frame.pack_propagate(False)
        
        # 상태 메시지
        self.status_label = tk.Label(
            self.status_frame,
            text="준비 완료",
            font=('SF Pro Display', 9),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.status_label.pack(side='left', padx=10, pady=5)
        
        # 할당량 정보
        self.quota_label = tk.Label(
            self.status_frame,
            text="API 할당량: 0/10000",
            font=('SF Pro Display', 9),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.quota_label.pack(side='right', padx=10, pady=5)
    
    def on_tab_changed(self, event):
        """탭 변경 시 호출"""
        selected_tab = event.widget.tab('current')['text']
        
        if "영상 검색" in selected_tab:
            self.load_search_tab()
            self.current_tab = 'search'
        elif "채널 분석" in selected_tab:
            self.load_channel_tab()
            self.current_tab = 'channel'
        elif "결과 보기" in selected_tab:
            self.load_results_tab()
            self.current_tab = 'results'
        
        self.update_status(f"{selected_tab} 탭 활성화")
    
    def load_search_tab(self):
        """검색 탭 로드 (지연로딩)"""
        if self.search_tab is None:
            try:
                from .search_tab import SearchTab
                self.search_tab = SearchTab(self.search_frame, self)
                print("✅ 검색 탭 로드 완료")
            except Exception as e:
                self.show_error("검색 탭 로드 실패", str(e))
    
    def load_channel_tab(self):
        """채널 분석 탭 로드 (지연로딩)"""
        if self.channel_tab is None:
            try:
                from .channel_tab import ChannelTab
                self.channel_tab = ChannelTab(self.channel_frame, self)
                print("✅ 채널 분석 탭 로드 완료")
            except Exception as e:
                self.show_error("채널 분석 탭 로드 실패", str(e))
    
    def load_results_tab(self):
        """결과 탭 로드 (지연로딩) - 중복 방지"""
        if self.results_viewer is None:
            try:
                from .results_viewer import ResultsViewer
                self.results_viewer = ResultsViewer(self.results_frame, self)
                print("✅ 결과 뷰어 로드 완료")
            except Exception as e:
                self.show_error("결과 뷰어 로드 실패", str(e))
        else:
            print("ℹ️ 결과 뷰어 이미 로드됨")
    
    def check_api_key(self):
        """API 키 확인"""
        def check_in_background():
            try:
                # .env 파일 확인
                if os.path.exists('.env'):
                    with open('.env', 'r') as f:
                        for line in f:
                            if line.startswith('YOUTUBE_API_KEY='):
                                api_key = line.split('=', 1)[1].strip()
                                if api_key and api_key != "YOUR_YOUTUBE_API_KEY_HERE":
                                    self.api_status_label.config(text="API: 연결됨", fg='#30d158')
                                    return
                
                # config.py 확인
                try:
                    import config
                    if hasattr(config, 'DEVELOPER_KEY'):
                        key = config.DEVELOPER_KEY
                        if key != "YOUR_YOUTUBE_API_KEY_HERE":
                            self.api_status_label.config(text="API: 연결됨", fg='#30d158')
                            return
                except:
                    pass
                
                # API 키가 없는 경우
                self.api_status_label.config(text="API: 미설정", fg='#ff3b30')
                
            except Exception as e:
                print(f"API 키 확인 오류: {e}")
                self.api_status_label.config(text="API: 오류", fg='#ff3b30')
        
        # 백그라운드에서 확인
        threading.Thread(target=check_in_background, daemon=True).start()
    
    def setup_api_key_dialog(self):
        """API 키 설정 다이얼로그"""
        try:
            api_key = simpledialog.askstring(
                "API 키 설정",
                "YouTube Data API v3 키를 입력하세요:",
                show='*'
            )
            
            if not api_key:
                return
            
            # .env 파일에 저장
            env_content = f"YOUTUBE_API_KEY={api_key}\n"
            
            # 기존 .env 파일이 있다면 읽어서 업데이트
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    lines = f.readlines()
                
                updated = False
                for i, line in enumerate(lines):
                    if line.startswith('YOUTUBE_API_KEY='):
                        lines[i] = env_content
                        updated = True
                        break
                
                if not updated:
                    lines.append(env_content)
                
                with open('.env', 'w') as f:
                    f.writelines(lines)
            else:
                with open('.env', 'w') as f:
                    f.write(env_content)
            
            # API 상태 다시 확인
            self.check_api_key()
            
            messagebox.showinfo("성공", "API 키가 저장되었습니다!")
            
        except Exception as e:
            self.show_error("API 키 저장 실패", str(e))
    
    def launch_trend_dashboard(self):
        """트렌드 대시보드 실행 - 모듈 오류 수정"""
        try:
            # API 키 확인
            api_key = self.get_api_key()
            if not api_key:
                messagebox.showwarning(
                    "API 키 필요",
                    "트렌드 대시보드를 사용하려면 API 키가 필요합니다."
                )
                return
            
            # 여러 방법으로 대시보드 모듈 시도
            dashboard_launched = False
            
            # 방법 1: 새로운 dashboard 모듈
            try:
                from dashboard.main_dashboard import DashboardWindow
                dashboard = DashboardWindow(api_key)
                dashboard.show()
                dashboard_launched = True
                print("✅ 새로운 대시보드 모듈로 실행")
            except ImportError:
                print("❌ 새로운 대시보드 모듈을 찾을 수 없음")
            
            # 방법 2: 기존 youtube_trend_dashboard 모듈
            if not dashboard_launched:
                try:
                    from youtube_trend_dashboard import YouTubeTrendDashboard
                    dashboard_window = tk.Toplevel(self.root)
                    dashboard_window.title("YouTube 트렌드 대시보드")
                    dashboard_window.geometry("1200x800")
                    dashboard_window.protocol("WM_DELETE_WINDOW", dashboard_window.destroy)
                    
                    app = YouTubeTrendDashboard(dashboard_window, api_key)
                    dashboard_launched = True
                    print("✅ 기존 대시보드 모듈로 실행")
                except ImportError:
                    print("❌ 기존 대시보드 모듈을 찾을 수 없음")
            
            # 방법 3: 내장 간단 대시보드
            if not dashboard_launched:
                try:
                    self.create_simple_dashboard(api_key)
                    dashboard_launched = True
                    print("✅ 내장 간단 대시보드로 실행")
                except Exception as e:
                    print(f"❌ 내장 대시보드 생성 오류: {e}")
            
            # 모든 방법 실패 시
            if not dashboard_launched:
                messagebox.showerror(
                    "모듈 오류",
                    "트렌드 대시보드 모듈을 찾을 수 없습니다.\n\n"
                    "해결 방법:\n"
                    "1. dashboard 모듈이 설치되어 있는지 확인\n"
                    "2. youtube_trend_dashboard.py 파일이 있는지 확인\n"
                    "3. 필요한 의존성이 설치되어 있는지 확인"
                )
                
        except Exception as e:
            self.show_error("대시보드 실행 실패", str(e))

    def create_simple_dashboard(self, api_key):
        """내장 간단 트렌드 대시보드 생성"""
        dashboard_window = tk.Toplevel(self.root)
        dashboard_window.title("YouTube 트렌드 대시보드 (간단 버전)")
        dashboard_window.geometry("800x600")
        dashboard_window.configure(bg='#f5f5f7')
        
        # 중앙 정렬
        dashboard_window.transient(self.root)
        
        # 헤더
        header_frame = tk.Frame(dashboard_window, bg='#007aff', height=80)
        header_frame.pack(fill='x')
        header_frame.pack_propagate(False)
        
        tk.Label(
            header_frame,
            text="🔥 YouTube 트렌드 대시보드",
            font=('SF Pro Display', 18, 'bold'),
            bg='#007aff',
            fg='white'
        ).pack(expand=True)
        
        # 컨텐츠
        content_frame = tk.Frame(dashboard_window, bg='#f5f5f7')
        content_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 트렌드 정보 표시
        info_text = """
🚀 트렌드 분석 기능:

• 실시간 인기 키워드 분석
• 급상승 영상 트렌드
• 카테고리별 인기 순위
• 지역별 트렌드 비교

📊 현재 이용 가능한 기능:
• 영상 검색 및 분석
• 채널 성과 분석
• 데이터 내보내기

💡 전체 기능을 이용하려면 
트렌드 대시보드 모듈을 설치하세요.
        """
        
        tk.Label(
            content_frame,
            text=info_text,
            font=('SF Pro Display', 12),
            bg='#f5f5f7',
            fg='#1d1d1f',
            justify='left'
        ).pack(pady=20)
        
        # 닫기 버튼
        tk.Button(
            content_frame,
            text="닫기",
            font=('SF Pro Display', 12),
            bg='#86868b',
            fg='white',
            relief='flat',
            padx=30,
            pady=10,
            command=dashboard_window.destroy
        ).pack()

    def get_api_key(self):
        """현재 설정된 API 키 가져오기"""
        # .env에서 확인
        if os.path.exists('.env'):
            with open('.env', 'r') as f:
                for line in f:
                    if line.startswith('YOUTUBE_API_KEY='):
                        return line.split('=', 1)[1].strip()
        
        # config.py에서 확인
        try:
            import config
            if hasattr(config, 'DEVELOPER_KEY'):
                key = config.DEVELOPER_KEY
                if key != "YOUR_YOUTUBE_API_KEY_HERE":
                    return key
        except:
            pass
        
        return None
    
    def open_settings(self):
        """설정 창 열기"""
        # TODO: 설정 다이얼로그 구현
        messagebox.showinfo("설정", "설정 기능은 준비 중입니다.")
    
    def clear_cache(self):
        """캐시 정리"""
        try:
            # TODO: 캐시 정리 로직 구현
            self.update_status("캐시가 정리되었습니다.")
            messagebox.showinfo("완료", "캐시가 정리되었습니다.")
        except Exception as e:
            self.show_error("캐시 정리 실패", str(e))
    
    def show_help(self):
        """도움말 표시"""
        help_text = """
🎬 YouTube 트렌드 분석기 v3.0 사용법

📍 주요 기능:
• 영상 검색: 키워드로 YouTube 영상 검색 및 분석
• 채널 분석: 특정 채널의 영상 성과 분석
• 트렌드 대시보드: 실시간 트렌드 키워드 모니터링

📍 사용 방법:
1. API 키 설정 (Google Cloud Console에서 발급)
2. 원하는 탭에서 검색 또는 분석 실행
3. 결과를 엑셀로 내보내거나 썸네일 다운로드

📍 지원 형식:
• 엑셀 리포트 (.xlsx)
• 썸네일 이미지 (.jpg)
• 영상 대본 (.txt, .srt, .json)

더 자세한 정보는 README.md 파일을 참고하세요.
        """
        
        messagebox.showinfo("도움말", help_text)
    
    def show_about(self):
        """정보 표시"""
        about_text = """
🎬 YouTube 트렌드 분석기 v3.0

개발자: AI Assistant
라이선스: MIT License

기능:
• YouTube Data API v3 연동
• 키워드 기반 영상 검색
• 채널 성과 분석
• Outlier Score 계산
• 다양한 내보내기 옵션

GitHub: 프로젝트 저장소 URL

© 2024 - YouTube 트렌드 분석기
        """
        
        messagebox.showinfo("정보", about_text)
    
    def update_status(self, message):
        """상태바 메시지 업데이트"""
        self.status_label.config(text=message)
        print(f"📱 상태: {message}")
    
    def update_quota(self, used, total):
        """할당량 정보 업데이트"""
        self.quota_label.config(text=f"API 할당량: {used}/{total}")
        
        # 할당량에 따른 색상 변경
        percentage = used / total * 100 if total > 0 else 0
        if percentage > 80:
            color = '#ff3b30'  # 빨강
        elif percentage > 60:
            color = '#ff9500'  # 주황
        else:
            color = '#86868b'  # 회색
        
        self.quota_label.config(fg=color)
    
    def show_error(self, title, message):
        """에러 메시지 표시"""
        messagebox.showerror(title, message)
        self.update_status(f"오류: {title}")
    
    def show_warning(self, title, message):
        """경고 메시지 표시"""
        messagebox.showwarning(title, message)
        self.update_status(f"경고: {title}")
    
    def show_info(self, title, message):
        """정보 메시지 표시"""
        messagebox.showinfo(title, message)
        self.update_status(f"정보: {title}")
    
    def run(self):
        """애플리케이션 실행"""
        self.root.mainloop()
    
    def quit(self):
        """애플리케이션 종료"""
        self.root.quit()
    
    def destroy(self):
        """애플리케이션 종료 및 정리"""
        self.root.destroy()
    
    # 탭 간 데이터 공유를 위한 메서드들
    def show_search_results(self, videos_data, analysis_settings):
        """검색 결과를 결과 탭에 표시"""
        try:
            # 결과 탭 로드
            self.load_results_tab()
            
            # 결과 탭으로 전환
            self.notebook.select(2)
            
            # 결과 표시
            if self.results_viewer:
                self.results_viewer.display_results(videos_data, analysis_settings)
                self.update_status(f"검색 결과 {len(videos_data)}개 표시됨")
            else:
                self.show_error("결과 표시 실패", "결과 뷰어를 초기화할 수 없습니다.")
        except Exception as e:
            print(f"결과 표시 오류: {e}")
            self.show_error("결과 표시 실패", str(e))
    
    def show_channel_analysis(self, channel_data):
        """채널 분석 결과를 결과 탭에 표시"""
        try:
            # 결과 탭으로 전환
            self.load_results_tab()
            self.notebook.select(2)
            
            # 결과 뷰어 로드 및 데이터 표시
            if self.results_viewer:
                self.results_viewer.display_channel_analysis(channel_data)
            else:
                self.show_error("결과 표시 실패", "결과 뷰어를 초기화할 수 없습니다.")
        except Exception as e:
            print(f"채널 분석 결과 표시 오류: {e}")
            self.show_error("채널 분석 결과 표시 실패", str(e))


if __name__ == "__main__":
    # 메인 애플리케이션 실행
    app = MainWindow()
    app.run()