"""
설정 다이얼로그 모듈
애플리케이션 설정을 관리하는 다이얼로그
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os

class SettingsDialog:
    """설정 다이얼로그 클래스"""
    
    def __init__(self, parent, current_settings=None):
        """
        설정 다이얼로그 초기화
        
        Args:
            parent: 부모 위젯
            current_settings (dict): 현재 설정값
        """
        self.parent = parent
        self.current_settings = current_settings or {}
        self.result = None
        
        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("설정")
        self.dialog.geometry("500x600")
        self.dialog.configure(bg='#f5f5f7')
        self.dialog.resizable(False, False)
        
        # 모달 설정
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 중앙 정렬
        self.center_dialog()
        
        # 닫기 이벤트
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        self.create_widgets()
        self.load_current_settings()
        
    def center_dialog(self):
        """다이얼로그를 부모 창 중앙에 배치"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = 500
        dialog_height = 600
        
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
        self.notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # 각 탭 생성
        self.create_general_tab()
        self.create_api_tab()
        self.create_export_tab()
        self.create_advanced_tab()
        
        # 버튼 영역
        self.create_buttons(main_frame)
    
    def create_general_tab(self):
        """일반 설정 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="일반")
        
        # 스크롤 가능한 프레임
        canvas = tk.Canvas(tab_frame, bg='#f5f5f7')
        scrollbar = ttk.Scrollbar(tab_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg='#f5f5f7')
        
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        
        # 언어 설정
        lang_frame = tk.LabelFrame(scrollable_frame, text="언어 설정", bg='#f5f5f7', padx=10, pady=10)
        lang_frame.pack(fill='x', pady=(0, 15))
        
        tk.Label(lang_frame, text="기본 언어:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.language_var = tk.StringVar(value="ko")
        language_combo = ttk.Combobox(
            lang_frame,
            textvariable=self.language_var,
            values=["ko", "en"],
            state="readonly",
            width=10
        )
        language_combo.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # 기본 설정
        default_frame = tk.LabelFrame(scrollable_frame, text="기본 설정", bg='#f5f5f7', padx=10, pady=10)
        default_frame.pack(fill='x', pady=(0, 15))
        
        # 기본 지역
        tk.Label(default_frame, text="기본 지역:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.default_region_var = tk.StringVar(value="KR")
        region_combo = ttk.Combobox(
            default_frame,
            textvariable=self.default_region_var,
            values=["KR", "US", "JP", "GB"],
            state="readonly",
            width=10
        )
        region_combo.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # 기본 최대 결과 수
        tk.Label(default_frame, text="기본 최대 결과:", bg='#f5f5f7').grid(row=1, column=0, sticky='w', pady=5)
        self.default_max_results_var = tk.StringVar(value="200")
        max_results_combo = ttk.Combobox(
            default_frame,
            textvariable=self.default_max_results_var,
            values=["50", "100", "200", "300"],
            state="readonly",
            width=10
        )
        max_results_combo.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # UI 설정
        ui_frame = tk.LabelFrame(scrollable_frame, text="UI 설정", bg='#f5f5f7', padx=10, pady=10)
        ui_frame.pack(fill='x', pady=(0, 15))
        
        # 테마
        tk.Label(ui_frame, text="테마:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.theme_var = tk.StringVar(value="light")
        theme_combo = ttk.Combobox(
            ui_frame,
            textvariable=self.theme_var,
            values=["light", "dark"],
            state="readonly",
            width=10
        )
        theme_combo.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # 시작 시 마지막 탭 기억
        self.remember_tab_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            ui_frame,
            text="시작 시 마지막 탭 기억",
            variable=self.remember_tab_var,
            bg='#f5f5f7'
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)
        
        # 자동 저장
        self.auto_save_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            ui_frame,
            text="설정 자동 저장",
            variable=self.auto_save_var,
            bg='#f5f5f7'
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=5)
        
        # 레이아웃
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def create_api_tab(self):
        """API 설정 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="API")
        
        main_frame = tk.Frame(tab_frame, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # YouTube API 설정
        youtube_frame = tk.LabelFrame(main_frame, text="YouTube Data API v3", bg='#f5f5f7', padx=15, pady=15)
        youtube_frame.pack(fill='x', pady=(0, 20))
        
        # API 키
        tk.Label(youtube_frame, text="API 키:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.api_key_var = tk.StringVar()
        self.api_key_entry = tk.Entry(
            youtube_frame,
            textvariable=self.api_key_var,
            show="*",
            width=40,
            font=('Courier', 10)
        )
        self.api_key_entry.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # API 키 표시/숨김 버튼
        self.show_api_key_var = tk.BooleanVar()
        show_key_check = tk.Checkbutton(
            youtube_frame,
            text="표시",
            variable=self.show_api_key_var,
            command=self.toggle_api_key_visibility,
            bg='#f5f5f7'
        )
        show_key_check.grid(row=0, column=2, padx=(10, 0))
        
        # API 키 테스트 버튼
        test_button = tk.Button(
            youtube_frame,
            text="🔍 연결 테스트",
            command=self.test_api_connection,
            bg='#007aff',
            fg='white',
            borderwidth=0,
            cursor='hand2'
        )
        test_button.grid(row=1, column=1, sticky='w', pady=(10, 0))
        
        # 할당량 설정
        quota_frame = tk.LabelFrame(main_frame, text="할당량 관리", bg='#f5f5f7', padx=15, pady=15)
        quota_frame.pack(fill='x', pady=(0, 20))
        
        tk.Label(quota_frame, text="일일 할당량 한도:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.quota_limit_var = tk.StringVar(value="10000")
        quota_entry = tk.Entry(quota_frame, textvariable=self.quota_limit_var, width=10)
        quota_entry.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # 할당량 경고 설정
        tk.Label(quota_frame, text="경고 시점 (%):", bg='#f5f5f7').grid(row=1, column=0, sticky='w', pady=5)
        self.quota_warning_var = tk.StringVar(value="80")
        warning_entry = tk.Entry(quota_frame, textvariable=self.quota_warning_var, width=10)
        warning_entry.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # API 키 획득 도움말
        help_frame = tk.LabelFrame(main_frame, text="API 키 획득 방법", bg='#f5f5f7', padx=15, pady=15)
        help_frame.pack(fill='x')
        
        help_text = """
1. Google Cloud Console (console.cloud.google.com)에 접속
2. 새 프로젝트 생성 또는 기존 프로젝트 선택
3. API 및 서비스 → 라이브러리에서 'YouTube Data API v3' 검색 및 사용 설정
4. API 및 서비스 → 사용자 인증 정보에서 'API 키' 생성
5. 생성된 API 키를 위 필드에 입력
        """
        
        help_label = tk.Label(
            help_frame,
            text=help_text.strip(),
            bg='#f5f5f7',
            justify='left',
            font=('SF Pro Display', 9)
        )
        help_label.pack(anchor='w')
    
    def create_export_tab(self):
        """내보내기 설정 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="내보내기")
        
        main_frame = tk.Frame(tab_frame, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 경로 설정
        paths_frame = tk.LabelFrame(main_frame, text="저장 경로", bg='#f5f5f7', padx=15, pady=15)
        paths_frame.pack(fill='x', pady=(0, 20))
        
        # 엑셀 파일 경로
        tk.Label(paths_frame, text="엑셀:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.excel_path_var = tk.StringVar(value=os.path.expanduser("~/Downloads"))
        excel_path_entry = tk.Entry(paths_frame, textvariable=self.excel_path_var, width=30)
        excel_path_entry.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        excel_browse_btn = tk.Button(
            paths_frame,
            text="찾기",
            command=lambda: self.browse_folder(self.excel_path_var),
            bg='#86868b',
            fg='white',
            borderwidth=0,
            cursor='hand2'
        )
        excel_browse_btn.grid(row=0, column=2, padx=(10, 0))
        
        # 썸네일 경로
        tk.Label(paths_frame, text="썸네일:", bg='#f5f5f7').grid(row=1, column=0, sticky='w', pady=5)
        self.thumbnail_path_var = tk.StringVar(value=os.path.expanduser("~/Downloads/thumbnails"))
        thumbnail_path_entry = tk.Entry(paths_frame, textvariable=self.thumbnail_path_var, width=30)
        thumbnail_path_entry.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        thumbnail_browse_btn = tk.Button(
            paths_frame,
            text="찾기",
            command=lambda: self.browse_folder(self.thumbnail_path_var),
            bg='#86868b',
            fg='white',
            borderwidth=0,
            cursor='hand2'
        )
        thumbnail_browse_btn.grid(row=1, column=2, padx=(10, 0))
        
        # 내보내기 옵션
        export_frame = tk.LabelFrame(main_frame, text="내보내기 옵션", bg='#f5f5f7', padx=15, pady=15)
        export_frame.pack(fill='x', pady=(0, 20))
        
        # 자동 압축
        self.auto_zip_var = tk.BooleanVar(value=True)
        tk.Checkbutton(
            export_frame,
            text="다운로드 후 자동으로 ZIP 파일 생성",
            variable=self.auto_zip_var,
            bg='#f5f5f7'
        ).grid(row=1, column=0, columnspan=2, sticky='w', pady=5)  # columnspan=2로 수정
        
        # 기존 파일 덮어쓰기
        self.overwrite_files_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            export_frame,
            text="기존 파일 덮어쓰기",
            variable=self.overwrite_files_var,
            bg='#f5f5f7'
        ).grid(row=2, column=0, columnspan=2, sticky='w', pady=5)  # columnspan=2로 수정
    
    def create_advanced_tab(self):
        """고급 설정 탭"""
        tab_frame = ttk.Frame(self.notebook)
        self.notebook.add(tab_frame, text="고급")
        
        main_frame = tk.Frame(tab_frame, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 성능 설정
        performance_frame = tk.LabelFrame(main_frame, text="성능 설정", bg='#f5f5f7', padx=15, pady=15)
        performance_frame.pack(fill='x', pady=(0, 20))
        
        # 병렬 처리 워커 수
        tk.Label(performance_frame, text="병렬 처리 워커 수:", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.max_workers_var = tk.StringVar(value="10")
        workers_entry = tk.Entry(performance_frame, textvariable=self.max_workers_var, width=10)
        workers_entry.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # 캐시 설정
        tk.Label(performance_frame, text="캐시 유효 시간 (분):", bg='#f5f5f7').grid(row=1, column=0, sticky='w', pady=5)
        self.cache_duration_var = tk.StringVar(value="30")
        cache_entry = tk.Entry(performance_frame, textvariable=self.cache_duration_var, width=10)
        cache_entry.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # 네트워크 설정
        network_frame = tk.LabelFrame(main_frame, text="네트워크 설정", bg='#f5f5f7', padx=15, pady=15)
        network_frame.pack(fill='x', pady=(0, 20))
        
        # 요청 타임아웃
        tk.Label(network_frame, text="요청 타임아웃 (초):", bg='#f5f5f7').grid(row=0, column=0, sticky='w', pady=5)
        self.timeout_var = tk.StringVar(value="30")
        timeout_entry = tk.Entry(network_frame, textvariable=self.timeout_var, width=10)
        timeout_entry.grid(row=0, column=1, sticky='w', padx=(10, 0))
        
        # 재시도 횟수
        tk.Label(network_frame, text="재시도 횟수:", bg='#f5f5f7').grid(row=1, column=0, sticky='w', pady=5)
        self.retry_count_var = tk.StringVar(value="3")
        retry_entry = tk.Entry(network_frame, textvariable=self.retry_count_var, width=10)
        retry_entry.grid(row=1, column=1, sticky='w', padx=(10, 0))
        
        # 디버그 설정
        debug_frame = tk.LabelFrame(main_frame, text="디버그 설정", bg='#f5f5f7', padx=15, pady=15)
        debug_frame.pack(fill='x')
        
        # 디버그 모드
        self.debug_mode_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            debug_frame,
            text="디버그 모드 활성화",
            variable=self.debug_mode_var,
            bg='#f5f5f7'
        ).grid(row=0, column=0, sticky='w', pady=5)
        
        # 상세 로그
        self.verbose_logging_var = tk.BooleanVar(value=False)
        tk.Checkbutton(
            debug_frame,
            text="상세 로그 출력",
            variable=self.verbose_logging_var,
            bg='#f5f5f7'
        ).grid(row=1, column=0, sticky='w', pady=5)
        
        # 설정 초기화 버튼
        reset_button = tk.Button(
            debug_frame,
            text="🔄 기본값으로 초기화",
            command=self.reset_to_defaults,
            bg='#ff3b30',
            fg='white',
            borderwidth=0,
            cursor='hand2'
        )
        reset_button.grid(row=2, column=0, sticky='w', pady=(15, 0))
    
    def create_buttons(self, parent):
        """버튼 영역 생성"""
        button_frame = tk.Frame(parent, bg='#f5f5f7')
        button_frame.pack(fill='x')
        
        # 취소 버튼
        cancel_button = tk.Button(
            button_frame,
            text="취소",
            font=('SF Pro Display', 11),
            bg='#86868b',
            fg='white',
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.on_cancel
        )
        cancel_button.pack(side='right', padx=(10, 0))
        
        # 확인 버튼
        ok_button = tk.Button(
            button_frame,
            text="확인",
            font=('SF Pro Display', 11),
            bg='#34c759',
            fg='white',
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.on_ok
        )
        ok_button.pack(side='right')
        
        # 적용 버튼
        apply_button = tk.Button(
            button_frame,
            text="적용",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.on_apply
        )
        apply_button.pack(side='right', padx=(0, 10))
    
    def load_current_settings(self):
        """현재 설정값 로드"""
        if self.current_settings:
            # 일반 설정
            self.language_var.set(self.current_settings.get('language', 'ko'))
            self.default_region_var.set(self.current_settings.get('default_region', 'KR'))
            self.default_max_results_var.set(str(self.current_settings.get('default_max_results', 200)))
            self.theme_var.set(self.current_settings.get('theme', 'light'))
            self.remember_tab_var.set(self.current_settings.get('remember_tab', True))
            self.auto_save_var.set(self.current_settings.get('auto_save', True))
            
            # API 설정
            self.api_key_var.set(self.current_settings.get('api_key', ''))
            self.quota_limit_var.set(str(self.current_settings.get('quota_limit', 10000)))
            self.quota_warning_var.set(str(self.current_settings.get('quota_warning', 80)))
            
            # 내보내기 설정
            self.excel_path_var.set(self.current_settings.get('excel_path', os.path.expanduser("~/Downloads")))
            self.thumbnail_path_var.set(self.current_settings.get('thumbnail_path', os.path.expanduser("~/Downloads/thumbnails")))
            self.transcript_path_var.set(self.current_settings.get('transcript_path', os.path.expanduser("~/Downloads/transcripts")))
            self.thumbnail_quality_var.set(self.current_settings.get('thumbnail_quality', 'high'))
            self.auto_zip_var.set(self.current_settings.get('auto_zip', True))
            self.overwrite_files_var.set(self.current_settings.get('overwrite_files', False))
            
            # 고급 설정
            self.max_workers_var.set(str(self.current_settings.get('max_workers', 10)))
            self.cache_duration_var.set(str(self.current_settings.get('cache_duration', 30)))
            self.timeout_var.set(str(self.current_settings.get('timeout', 30)))
            self.retry_count_var.set(str(self.current_settings.get('retry_count', 3)))
            self.debug_mode_var.set(self.current_settings.get('debug_mode', False))
            self.verbose_logging_var.set(self.current_settings.get('verbose_logging', False))
    
    def toggle_api_key_visibility(self):
        """API 키 표시/숨김 토글"""
        if self.show_api_key_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def test_api_connection(self):
        """API 연결 테스트"""
        api_key = self.api_key_var.get().strip()
        if not api_key:
            messagebox.showwarning("API 키 필요", "먼저 API 키를 입력해주세요.")
            return
        
        try:
            # YouTube API 연결 테스트
            from core import YouTubeClient
            
            client = YouTubeClient(api_key)
            if client.test_connection():
                messagebox.showinfo("연결 성공", "YouTube API 연결이 성공했습니다!")
            else:
                messagebox.showerror("연결 실패", "YouTube API 연결에 실패했습니다.\nAPI 키를 확인해주세요.")
                
        except Exception as e:
            messagebox.showerror("연결 오류", f"API 연결 테스트 중 오류가 발생했습니다:\n{str(e)}")
    
    def browse_folder(self, path_var):
        """폴더 선택"""
        folder = filedialog.askdirectory(
            title="폴더 선택",
            initialdir=path_var.get()
        )
        if folder:
            path_var.set(folder)
    
    def reset_to_defaults(self):
        """기본값으로 초기화"""
        result = messagebox.askyesno(
            "설정 초기화",
            "모든 설정을 기본값으로 초기화하시겠습니까?\n\n"
            "이 작업은 되돌릴 수 없습니다."
        )
        
        if result:
            # 기본값으로 설정
            self.language_var.set('ko')
            self.default_region_var.set('KR')
            self.default_max_results_var.set('200')
            self.theme_var.set('light')
            self.remember_tab_var.set(True)
            self.auto_save_var.set(True)
            
            self.quota_limit_var.set('10000')
            self.quota_warning_var.set('80')
            
            self.excel_path_var.set(os.path.expanduser("~/Downloads"))
            self.thumbnail_path_var.set(os.path.expanduser("~/Downloads/thumbnails"))
            self.transcript_path_var.set(os.path.expanduser("~/Downloads/transcripts"))
            self.thumbnail_quality_var.set('high')
            self.auto_zip_var.set(True)
            self.overwrite_files_var.set(False)
            
            self.max_workers_var.set('10')
            self.cache_duration_var.set('30')
            self.timeout_var.set('30')
            self.retry_count_var.set('3')
            self.debug_mode_var.set(False)
            self.verbose_logging_var.set(False)
            
            messagebox.showinfo("초기화 완료", "모든 설정이 기본값으로 초기화되었습니다.")
    
    def get_settings(self):
        """현재 설정값들을 딕셔너리로 반환"""
        try:
            return {
                # 일반 설정
                'language': self.language_var.get(),
                'default_region': self.default_region_var.get(),
                'default_max_results': int(self.default_max_results_var.get()),
                'theme': self.theme_var.get(),
                'remember_tab': self.remember_tab_var.get(),
                'auto_save': self.auto_save_var.get(),
                
                # API 설정
                'api_key': self.api_key_var.get().strip(),
                'quota_limit': int(self.quota_limit_var.get()),
                'quota_warning': int(self.quota_warning_var.get()),
                
                # 내보내기 설정
                'excel_path': self.excel_path_var.get(),
                'thumbnail_path': self.thumbnail_path_var.get(),
                'transcript_path': self.transcript_path_var.get(),
                'thumbnail_quality': self.thumbnail_quality_var.get(),
                'auto_zip': self.auto_zip_var.get(),
                'overwrite_files': self.overwrite_files_var.get(),
                
                # 고급 설정
                'max_workers': int(self.max_workers_var.get()),
                'cache_duration': int(self.cache_duration_var.get()),
                'timeout': int(self.timeout_var.get()),
                'retry_count': int(self.retry_count_var.get()),
                'debug_mode': self.debug_mode_var.get(),
                'verbose_logging': self.verbose_logging_var.get()
            }
        except ValueError as e:
            messagebox.showerror("설정 오류", f"설정값에 오류가 있습니다:\n{str(e)}")
            return None
    
    def validate_settings(self, settings):
        """설정값 유효성 검사"""
        errors = []
        
        # 숫자 값들 검사
        if settings['default_max_results'] < 10 or settings['default_max_results'] > 500:
            errors.append("기본 최대 결과는 10-500 사이여야 합니다.")
        
        if settings['quota_limit'] < 1000:
            errors.append("할당량 한도는 최소 1000이어야 합니다.")
        
        if settings['quota_warning'] < 50 or settings['quota_warning'] > 95:
            errors.append("할당량 경고는 50-95% 사이여야 합니다.")
        
        if settings['max_workers'] < 1 or settings['max_workers'] > 20:
            errors.append("병렬 처리 워커 수는 1-20 사이여야 합니다.")
        
        if settings['cache_duration'] < 1:
            errors.append("캐시 유효 시간은 최소 1분이어야 합니다.")
        
        if settings['timeout'] < 5:
            errors.append("요청 타임아웃은 최소 5초여야 합니다.")
        
        if settings['retry_count'] < 0 or settings['retry_count'] > 10:
            errors.append("재시도 횟수는 0-10 사이여야 합니다.")
        
        return errors
    
    def on_apply(self):
        """적용 버튼 클릭"""
        settings = self.get_settings()
        if not settings:
            return
        
        # 유효성 검사
        errors = self.validate_settings(settings)
        if errors:
            messagebox.showerror("설정 오류", "\n".join(errors))
            return
        
        self.result = settings
        messagebox.showinfo("적용 완료", "설정이 적용되었습니다.")
    
    def on_ok(self):
        """확인 버튼 클릭"""
        settings = self.get_settings()
        if not settings:
            return
        
        # 유효성 검사
        errors = self.validate_settings(settings)
        if errors:
            messagebox.showerror("설정 오류", "\n".join(errors))
            return
        
        self.result = settings
        self.close()
    
    def on_cancel(self):
        """취소 버튼 클릭"""
        self.result = None
        self.close()
    
    def close(self):
        """다이얼로그 닫기"""
        if self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()
    
    def show(self):
        """다이얼로그 표시"""
        self.dialog.wait_window()
    
    def get_result(self):
        """결과 반환"""
        return self.result