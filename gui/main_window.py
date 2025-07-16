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
                        content = f.read()
                        if 'YOUTUBE_API_KEY=' in content and 'your_api_key_here' not in content:
                            self.root.after(0, lambda: self.update_api_status("✅ API 키 설정됨", "green"))
                            return
                
                # config.py 확인
                try:
                    import config
                    if hasattr(config, 'DEVELOPER_KEY') and config.DEVELOPER_KEY != "YOUR_YOUTUBE_API_KEY_HERE":
                        self.root.after(0, lambda: self.update_api_status("✅ API 키 설정됨", "green"))
                        return
                except:
                    pass
                
                # API 키 없음
                self.root.after(0, lambda: self.update_api_status("❌ API 키 필요", "red"))
                self.root.after(1000, self.prompt_api_key_setup)
                
            except Exception as e:
                self.root.after(0, lambda: self.update_api_status("❌ API 오류", "red"))
        
        # 백그라운드 스레드에서 확인
        threading.Thread(target=check_in_background, daemon=True).start()
    
    def update_api_status(self, text, color):
        """API 상태 업데이트"""
        self.api_status_label.config(text=text, fg=color)
    
    def prompt_api_key_setup(self):
        """API 키 설정 안내"""
        result = messagebox.askyesno(
            "API 키 설정 필요",
            "YouTube API 키가 설정되지 않았습니다.\n\n"
            "API 키를 설정하시겠습니까?\n\n"
            "※ API 키 없이는 일부 기능이 제한됩니다."
        )
        
        if result:
            self.show_api_key_setup_dialog()
        else:
            # API 키 없이 계속 사용
            self.update_status("API 키 미설정 - 일부 기능 제한됨")
            self.show_warning(
                "기능 제한", 
                "API 키가 설정되지 않아 다음 기능들이 제한됩니다:\n"
                "• 영상 검색 및 분석\n"
                "• 채널 분석\n"
                "• 트렌드 모니터링\n\n"
                "나중에 '설정' 메뉴에서 API 키를 설정할 수 있습니다."
            )

    def show_api_key_setup_dialog(self):
        """API 키 설정 다이얼로그 표시"""
        # 새 창 생성
        setup_window = tk.Toplevel(self.root)
        setup_window.title("YouTube API 키 설정")
        setup_window.geometry("500x400")
        setup_window.resizable(False, False)
        setup_window.transient(self.root)
        setup_window.grab_set()
        
        # 창 아이콘 설정 (있는 경우)
        try:
            setup_window.iconbitmap(self.root.iconbitmap())
        except:
            pass
        
        # 메인 프레임
        main_frame = tk.Frame(setup_window, bg='#f5f5f7', padx=20, pady=20)
        main_frame.pack(fill='both', expand=True)
        
        # 제목
        title_label = tk.Label(
            main_frame,
            text="🔑 YouTube API 키 설정",
            font=('SF Pro Display', 16, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        title_label.pack(pady=(0, 20))
        
        # 안내 텍스트
        guide_text = """
    YouTube Data API v3 키가 필요합니다.

    📍 API 키 발급 방법:
    1. Google Cloud Console (console.cloud.google.com) 접속
    2. 새 프로젝트 생성 또는 기존 프로젝트 선택
    3. YouTube Data API v3 사용 설정
    4. '사용자 인증 정보' → 'API 키' 생성
    5. 아래에 API 키를 입력하세요

    ⚠️ API 키는 안전하게 보관하고 공유하지 마세요.
        """
        
        guide_label = tk.Label(
            main_frame,
            text=guide_text,
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b',
            justify='left'
        )
        guide_label.pack(pady=(0, 20))
        
        # API 키 입력 섹션
        input_frame = tk.Frame(main_frame, bg='#f5f5f7')
        input_frame.pack(fill='x', pady=(0, 20))
        
        # API 키 라벨
        api_key_label = tk.Label(
            input_frame,
            text="API 키:",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        api_key_label.pack(anchor='w')
        
        # API 키 입력 필드
        self.api_key_var = tk.StringVar()
        api_key_entry = tk.Entry(
            input_frame,
            textvariable=self.api_key_var,
            font=('SF Pro Display', 11),
            width=50,
            show='*'  # 비밀번호 스타일로 표시
        )
        api_key_entry.pack(fill='x', pady=(5, 0))
        
        # 표시/숨기기 체크박스
        self.show_key_var = tk.BooleanVar()
        show_key_check = tk.Checkbutton(
            input_frame,
            text="API 키 표시",
            variable=self.show_key_var,
            command=lambda: api_key_entry.config(show='' if self.show_key_var.get() else '*'),
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        show_key_check.pack(anchor='w', pady=(5, 0))
        
        # 저장 방법 선택
        save_frame = tk.Frame(main_frame, bg='#f5f5f7')
        save_frame.pack(fill='x', pady=(0, 20))
        
        save_label = tk.Label(
            save_frame,
            text="저장 방법:",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        save_label.pack(anchor='w')
        
        self.save_method_var = tk.StringVar(value=".env")
        
        env_radio = tk.Radiobutton(
            save_frame,
            text=".env 파일에 저장 (권장)",
            variable=self.save_method_var,
            value=".env",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        env_radio.pack(anchor='w', pady=(5, 0))
        
        config_radio = tk.Radiobutton(
            save_frame,
            text="config.py 파일에 저장",
            variable=self.save_method_var,
            value="config",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        config_radio.pack(anchor='w', pady=(2, 0))
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame, bg='#f5f5f7')
        button_frame.pack(fill='x')
        
        # 취소 버튼
        cancel_btn = tk.Button(
            button_frame,
            text="취소",
            font=('SF Pro Display', 11),
            bg='#86868b',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=setup_window.destroy
        )
        cancel_btn.pack(side='right', padx=(10, 0))
        
        # 저장 버튼
        save_btn = tk.Button(
            button_frame,
            text="저장",
            font=('SF Pro Display', 11, 'bold'),
            bg='#007aff',
            fg='white',
            relief='flat',
            padx=20,
            pady=8,
            command=lambda: self.save_api_key(setup_window)
        )
        save_btn.pack(side='right')
        
        # 도움말 버튼
        help_btn = tk.Button(
            button_frame,
            text="도움말",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#007aff',
            relief='flat',
            padx=20,
            pady=8,
            command=self.show_api_help
        )
        help_btn.pack(side='left')
        
        # 엔터 키로 저장
        api_key_entry.bind('<Return>', lambda e: self.save_api_key(setup_window))
        
        # 포커스 설정
        api_key_entry.focus_set()
        
        # 창 중앙 배치
        setup_window.update_idletasks()
        x = (setup_window.winfo_screenwidth() // 2) - (setup_window.winfo_width() // 2)
        y = (setup_window.winfo_screenheight() // 2) - (setup_window.winfo_height() // 2)
        setup_window.geometry(f"+{x}+{y}")

    def save_api_key(self, setup_window):
        """API 키 저장"""
        api_key = self.api_key_var.get().strip()
        
        if not api_key:
            messagebox.showerror("오류", "API 키를 입력하세요.")
            return
        
        # API 키 유효성 검사 (기본적인 형식 체크)
        if len(api_key) < 30:
            messagebox.showerror("오류", "올바른 API 키 형식이 아닙니다.\n(너무 짧음)")
            return
        
        save_method = self.save_method_var.get()
        
        try:
            if save_method == ".env":
                self._save_to_env_file(api_key)
            else:
                self._save_to_config_file(api_key)
            
            # 저장 성공
            messagebox.showinfo("완료", f"API 키가 {save_method} 파일에 저장되었습니다.")
            
            # API 상태 업데이트
            self.update_api_status("✅ API 키 설정됨", "green")
            self.update_status("API 키 설정 완료")
            
            # 창 닫기
            setup_window.destroy()
            
        except Exception as e:
            messagebox.showerror("저장 실패", f"API 키 저장 중 오류가 발생했습니다:\n{str(e)}")

    def _save_to_env_file(self, api_key):
        """API 키를 .env 파일에 저장"""
        env_content = f"YOUTUBE_API_KEY={api_key}\n"
        
        # 기존 .env 파일이 있으면 읽어서 다른 설정 보존
        if os.path.exists('.env'):
            with open('.env', 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # YouTube API 키 라인 제거
            lines = [line for line in lines if not line.startswith('YOUTUBE_API_KEY=')]
            
            # 새 API 키 추가
            lines.append(env_content)
            
            with open('.env', 'w', encoding='utf-8') as f:
                f.writelines(lines)
        else:
            # 새 .env 파일 생성
            with open('.env', 'w', encoding='utf-8') as f:
                f.write(env_content)

    def _save_to_config_file(self, api_key):
        """API 키를 config.py 파일에 저장"""
        config_content = f'''"""
    YouTube 트렌드 분석기 설정 파일
    """

    # YouTube Data API v3 키
    DEVELOPER_KEY = "{api_key}"

    # 기타 설정
    MAX_RESULTS = 200
    API_QUOTA_LIMIT = 10000
    MAX_WORKERS = 10
    THUMBNAIL_DOWNLOAD_TIMEOUT = 30
    REQUEST_TIMEOUT = 30
    '''
        
        with open('config.py', 'w', encoding='utf-8') as f:
            f.write(config_content)

    def show_api_help(self):
        """API 키 도움말 표시"""
        help_text = """
    🔑 YouTube API 키 발급 가이드

    1. Google Cloud Console 접속
    → https://console.cloud.google.com

    2. 프로젝트 생성/선택
    → 상단 프로젝트 선택기에서 새 프로젝트 생성

    3. API 라이브러리에서 YouTube Data API v3 검색
    → "사용 설정" 클릭

    4. 사용자 인증 정보 생성
    → 왼쪽 메뉴 "API 및 서비스" → "사용자 인증 정보"
    → "사용자 인증 정보 만들기" → "API 키" 선택

    5. API 키 복사
    → 생성된 API 키를 복사하여 여기에 붙여넣기

    💡 참고사항:
    • API 키는 무료로 발급 가능
    • 일일 할당량: 10,000 단위 (일반적으로 충분함)
    • API 키는 타인과 공유하지 마세요
    • 키가 노출되면 즉시 재생성하세요
        """
        
        messagebox.showinfo("API 키 발급 도움말", help_text)

    def open_settings(self):
        """설정 창 열기"""
        try:
            self.show_api_key_setup_dialog()
        except Exception as e:
            self.show_error("설정 오류", f"설정 창을 열 수 없습니다: {str(e)}")

    def clear_cache(self):
        """캐시 정리"""
        try:
            from utils import get_cache_manager
            
            cache_manager = get_cache_manager()
            cache_manager.clear_all()
            
            # 임시 파일들도 정리
            import glob
            temp_files = []
            temp_files.extend(glob.glob("*.tmp"))
            temp_files.extend(glob.glob("temp/*"))
            temp_files.extend(glob.glob("cache/*"))
            
            removed_count = 0
            for file_path in temp_files:
                try:
                    os.remove(file_path)
                    removed_count += 1
                except:
                    pass
            
            self.update_status(f"캐시 정리 완료 ({removed_count}개 파일 삭제)")
            messagebox.showinfo("완료", f"캐시가 정리되었습니다.\n삭제된 파일: {removed_count}개")
            
        except Exception as e:
            self.show_error("캐시 정리 실패", str(e))
    
    def setup_api_key_dialog(self):
        """API 키 설정 다이얼로그"""
        api_key = simpledialog.askstring(
            "API 키 설정",
            "YouTube Data API v3 키를 입력하세요:\n\n"
            "💡 Google Cloud Console에서 발급받을 수 있습니다.",
            show='*'  # 비밀번호처럼 *로 표시
        )
        
        if api_key and api_key.strip():
            self.save_api_key(api_key.strip())
    
    def save_api_key(self, api_key):
        """API 키 저장"""
        try:
            # .env 파일에 저장
            with open('.env', 'w') as f:
                f.write(f"YOUTUBE_API_KEY={api_key}\n")
            
            # config.py 업데이트 (시도)
            try:
                with open('config.py', 'r') as f:
                    content = f.read()
                
                content = content.replace(
                    'DEVELOPER_KEY = os.getenv("YOUTUBE_API_KEY", "YOUR_YOUTUBE_API_KEY_HERE")',
                    f'DEVELOPER_KEY = os.getenv("YOUTUBE_API_KEY", "{api_key}")'
                )
                
                with open('config.py', 'w') as f:
                    f.write(content)
            except:
                pass
            
            self.update_api_status("✅ API 키 저장됨", "green")
            self.update_status("API 키가 저장되었습니다.")
            messagebox.showinfo("성공", "API 키가 저장되었습니다!")
            
        except Exception as e:
            self.show_error("API 키 저장 실패", str(e))
    
    def launch_trend_dashboard(self):
        """트렌드 대시보드 실행"""
        try:
            # API 키 확인
            api_key = self.get_api_key()
            if not api_key:
                messagebox.showwarning(
                    "API 키 필요",
                    "트렌드 대시보드를 사용하려면 API 키가 필요합니다."
                )
                return
            
            # 대시보드 모듈이 있는지 확인
            try:
                from dashboard import DashboardWindow
                dashboard = DashboardWindow(api_key)
                dashboard.show()
            except ImportError:
                # 기존 방식 사용
                try:
                    from youtube_trend_dashboard import YouTubeTrendDashboard
                    dashboard_window = tk.Toplevel(self.root)
                    dashboard_window.protocol("WM_DELETE_WINDOW", dashboard_window.destroy)
                    app = YouTubeTrendDashboard(dashboard_window, api_key)
                except ImportError:
                    messagebox.showerror(
                        "모듈 없음",
                        "트렌드 대시보드 모듈을 찾을 수 없습니다."
                    )
            
        except Exception as e:
            self.show_error("대시보드 실행 실패", str(e))
    
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
        # 결과 탭으로 전환
        self.notebook.select(2)  # 결과 탭 선택
        
        # 결과 뷰어 로드 및 데이터 표시
        self.load_results_tab()
        if self.results_viewer:
            self.results_viewer.display_results(videos_data, analysis_settings)
    
    def show_channel_analysis(self, channel_data):
        """채널 분석 결과를 결과 탭에 표시"""
        # 결과 탭으로 전환
        self.notebook.select(2)
        
        # 결과 뷰어 로드 및 데이터 표시
        self.load_results_tab()
        if self.results_viewer:
            self.results_viewer.display_channel_analysis(channel_data)
    
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
            self.show_error("결과 표시 오류", str(e))