"""
YouTube 트렌드 분석기 GUI - 한글 채널명 처리 수정 버전
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import os
import webbrowser
import concurrent.futures
from datetime import datetime, timedelta
import urllib.parse
import re

# 프로젝트 모듈들
import config
from youtube_api import YouTubeAPIClient
from data_analyzer import DataAnalyzer
from excel_generator import ExcelGenerator


class ImprovedYouTubeAnalyzerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("YouTube DeepSearch - 콘텐츠 분석 툴")
        self.root.geometry("1200x850")
        
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
        self.selected_items = set()
        
        # 캐시
        self.channel_cache = {}
        
        # 빠른 모드 옵션
        self.fast_mode = tk.BooleanVar(value=True)
        
        # 현재 탭
        self.current_tab = tk.StringVar(value="keyword")
        
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
        tk.Label(parent, text="검색 옵션", 
                font=('Arial', 16, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(pady=20)
        
        # 탭 프레임 생성
        tab_frame = tk.Frame(parent, bg=self.card_bg)
        tab_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        # 탭 버튼들
        tab_button_frame = tk.Frame(tab_frame, bg=self.card_bg)
        tab_button_frame.pack(fill=tk.X)
        
        self.keyword_tab_btn = tk.Button(tab_button_frame, text="키워드 검색",
                                       command=lambda: self.switch_tab("keyword"),
                                       bg=self.accent_color, fg="white",
                                       font=('Arial', 10, 'bold'),
                                       relief='flat', bd=0, pady=5)
        self.keyword_tab_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 2))
        
        self.channel_tab_btn = tk.Button(tab_button_frame, text="채널 분석",
                                       command=lambda: self.switch_tab("channel"),
                                       bg="#e0e0e0", fg="black",
                                       font=('Arial', 10),
                                       relief='flat', bd=0, pady=5)
        self.channel_tab_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(2, 0))
        
        # 필터 컨테이너
        self.filters_frame = tk.Frame(parent, bg=self.card_bg)
        self.filters_frame.pack(fill=tk.BOTH, expand=True, padx=10)
        
        # 키워드 검색 탭
        self.keyword_frame = tk.Frame(self.filters_frame, bg=self.card_bg)
        self.keyword_frame.pack(fill=tk.BOTH, expand=True)
        
        # 채널 분석 탭
        self.channel_frame = tk.Frame(self.filters_frame, bg=self.card_bg)
        
        # 필터 추가
        self.create_keyword_filters(self.keyword_frame)
        self.create_channel_filters(self.channel_frame)
        
        # 검색 버튼들
        button_frame = tk.Frame(parent, bg=self.card_bg)
        button_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=10, pady=20)
        
        self.search_button = tk.Button(button_frame, text="🔍 검색 시작",
                                     command=self.start_analysis,
                                     bg=self.accent_color, fg="white",
                                     font=('Arial', 14, 'bold'),
                                     pady=15, relief='raised', bd=2)
        self.search_button.pack(fill=tk.X)
        
        self.channel_analyze_button = tk.Button(button_frame, text="📺 채널 분석",
                                              command=self.start_channel_analysis,
                                              bg="#FF6B35", fg="white",
                                              font=('Arial', 14, 'bold'),
                                              pady=15, relief='raised', bd=2)
    
    def switch_tab(self, tab_name):
        """탭 전환"""
        self.current_tab.set(tab_name)
        
        if tab_name == "keyword":
            self.keyword_frame.pack(fill=tk.BOTH, expand=True)
            self.channel_frame.pack_forget()
            self.search_button.pack(fill=tk.X)
            self.channel_analyze_button.pack_forget()
            
            # 탭 버튼 스타일 업데이트
            self.keyword_tab_btn.config(bg=self.accent_color, fg="white", font=('Arial', 10, 'bold'))
            self.channel_tab_btn.config(bg="#e0e0e0", fg="black", font=('Arial', 10))
            
        elif tab_name == "channel":
            self.channel_frame.pack(fill=tk.BOTH, expand=True)
            self.keyword_frame.pack_forget()
            self.search_button.pack_forget()
            self.channel_analyze_button.pack(fill=tk.X)
            
            # 탭 버튼 스타일 업데이트
            self.channel_tab_btn.config(bg=self.accent_color, fg="white", font=('Arial', 10, 'bold'))
            self.keyword_tab_btn.config(bg="#e0e0e0", fg="black", font=('Arial', 10))

    def create_channel_filters(self, parent):
        """채널 분석 필터 생성"""
        # 채널 URL/ID 입력
        channel_frame = tk.Frame(parent, bg=self.card_bg)
        channel_frame.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(channel_frame, text="📺 채널 주소 또는 ID", 
                font=('Arial', 12, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.channel_url_entry = tk.Entry(channel_frame, font=('Arial', 12), relief='solid', bd=1)
        self.channel_url_entry.pack(fill=tk.X, ipady=8)
        
        # 입력 힌트
        hint_frame = tk.Frame(channel_frame, bg=self.card_bg)
        hint_frame.pack(fill=tk.X, pady=(2, 0))
        
        tk.Label(hint_frame, text="지원 형식:", 
                font=('Arial', 9, 'bold'),
                bg=self.card_bg, fg=self.text_secondary).pack(anchor=tk.W)
        
        hints = [
            "• https://www.youtube.com/channel/UC...",
            "• https://www.youtube.com/c/채널명",
            "• https://www.youtube.com/@핸들명",
            "• 채널 ID만 입력 (UC...)"
        ]
        
        for hint in hints:
            tk.Label(hint_frame, text=hint, 
                    font=('Arial', 8),
                    bg=self.card_bg, fg=self.text_secondary).pack(anchor=tk.W)
        
        # 분석 옵션
        options_frame = tk.Frame(parent, bg=self.card_bg)
        options_frame.pack(fill=tk.X, pady=(20, 15))
        
        tk.Label(options_frame, text="🔧 분석 옵션", 
                font=('Arial', 12, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 10))
        
        # 영상 개수
        video_count_frame = tk.Frame(options_frame, bg=self.card_bg)
        video_count_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(video_count_frame, text="📊 분석할 영상 수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.channel_video_count_var = tk.StringVar(value="50")
        video_count_combo = ttk.Combobox(video_count_frame, textvariable=self.channel_video_count_var,
                                        values=["10", "25", "50", "100"],
                                        state="readonly", font=('Arial', 11))
        video_count_combo.pack(fill=tk.X)
        
        # 정렬 방식
        channel_sort_frame = tk.Frame(options_frame, bg=self.card_bg)
        channel_sort_frame.pack(fill=tk.X, pady=(0, 10))
        
        tk.Label(channel_sort_frame, text="📈 정렬 방식", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.channel_sort_var = tk.StringVar(value="최신순")
        channel_sort_combo = ttk.Combobox(channel_sort_frame, textvariable=self.channel_sort_var,
                                         values=["최신순", "조회수순"],
                                         state="readonly", font=('Arial', 11))
        channel_sort_combo.pack(fill=tk.X)

    def start_channel_analysis(self):
        """채널 분석 시작 - 한글 처리 개선"""
        channel_input = self.channel_url_entry.get().strip()
        if not channel_input:
            messagebox.showwarning("오류", "채널 주소 또는 ID를 입력해주세요.")
            return
        
        api_key = self.api_entry.get().strip()
        if not api_key:
            messagebox.showwarning("오류", "API 키를 입력해주세요.")
            return
        
        # API 클라이언트 초기화
        try:
            if not self.api_client:
                self.api_client = YouTubeAPIClient(api_key)
        except Exception as e:
            messagebox.showerror("오류", f"API 클라이언트 초기화 실패: {str(e)}")
            return
        
        # 진행 상황 표시
        self.progress_label.config(text="🔍 채널 정보를 분석하는 중...")
        
        # 별도 스레드에서 채널 정보 처리
        thread = threading.Thread(target=self._process_channel_analysis, args=(channel_input,))
        thread.daemon = True
        thread.start()
    
    def _process_channel_analysis(self, channel_input):
        """채널 분석 처리 - 한글 지원 강화"""
        try:
            # 채널 ID 추출 (한글 처리 개선)
            channel_id, channel_name = self.extract_channel_info_korean(channel_input)
            
            if not channel_id:
                self.root.after(0, lambda: messagebox.showerror("오류", 
                    "유효하지 않은 채널 주소입니다.\n"
                    "다음 형식을 확인해주세요:\n"
                    "• https://www.youtube.com/@채널명\n"
                    "• https://www.youtube.com/c/채널명\n"
                    "• https://www.youtube.com/channel/UC...\n"
                    "• UC로 시작하는 채널 ID"))
                self.root.after(0, lambda: self.progress_label.config(text=""))
                return
            
            # 채널 이름 가져오기 (ID만 입력된 경우)
            if not channel_name:
                try:
                    channel_info = self.api_client.get_channel_info(channel_id)
                    if channel_info:
                        channel_name = channel_info['snippet']['title']
                    else:
                        channel_name = "알 수 없는 채널"
                except Exception as e:
                    print(f"채널 정보 가져오기 오류: {e}")
                    channel_name = "알 수 없는 채널"
            
            # 채널 분석 다이얼로그 열기
            self.root.after(0, lambda: self._open_channel_analysis_dialog(channel_id, channel_name))
            
        except Exception as e:
            error_msg = f"채널 분석 처리 중 오류: {str(e)}"
            print(error_msg)
            self.root.after(0, lambda: messagebox.showerror("오류", error_msg))
            self.root.after(0, lambda: self.progress_label.config(text=""))
    
    def extract_channel_info_korean(self, channel_input):
        """한글 채널명 처리 개선 버전"""
        import re
        import urllib.parse
        
        channel_input = channel_input.strip()
        
        print(f"🔍 채널 입력 분석: {channel_input}")
        
        # 이미 채널 ID인 경우 (UC로 시작)
        if channel_input.startswith('UC') and len(channel_input) == 24:
            print("✅ 채널 ID 형태로 인식")
            return channel_input, None
        
        # URL에서 채널 정보 추출
        patterns = [
            (r'youtube\.com/channel/([a-zA-Z0-9_-]+)', 'channel'),
            (r'youtube\.com/c/([^/?]+)', 'custom'),
            (r'youtube\.com/user/([^/?]+)', 'user'),
            (r'youtube\.com/@([^/?]+)', 'handle'),
            (r'youtube\.com/([a-zA-Z0-9가-힣_-]+)$', 'legacy')
        ]
        
        for pattern, url_type in patterns:
            match = re.search(pattern, channel_input)
            if match:
                identifier = match.group(1)
                print(f"✅ URL 패턴 매칭: {url_type} - {identifier}")
                
                # URL 디코딩 (한글 처리)
                try:
                    identifier = urllib.parse.unquote(identifier, encoding='utf-8')
                    print(f"📝 URL 디코딩 결과: {identifier}")
                except Exception as e:
                    print(f"⚠️ URL 디코딩 오류: {e}")
                
                # 채널 ID인 경우 바로 반환
                if identifier.startswith('UC') and len(identifier) == 24:
                    return identifier, None
                
                # 다른 형태인 경우 API로 채널 ID 찾기
                try:
                    channel_id = self.resolve_channel_identifier_korean(identifier, url_type, channel_input)
                    if channel_id:
                        return channel_id, identifier
                except Exception as e:
                    print(f"❌ 채널 ID 해결 오류: {e}")
        
        # URL 패턴이 매칭되지 않는 경우, 직접 채널명으로 검색
        try:
            print(f"🔍 직접 채널명 검색 시도: {channel_input}")
            channel_id = self.search_channel_by_name_korean(channel_input)
            if channel_id:
                return channel_id, channel_input
        except Exception as e:
            print(f"❌ 직접 검색 오류: {e}")
        
        return None, None

    def resolve_channel_identifier_korean(self, identifier, url_type, original_url):
        """한글 채널 식별자를 채널 ID로 변환"""
        try:
            print(f"🔄 채널 ID 해결 시도: {identifier} (타입: {url_type})")
            
            # @handle 형태인 경우
            if url_type == 'handle':
                return self.search_channel_by_handle_korean(identifier)
            
            # 커스텀 URL이나 사용자명인 경우
            else:
                return self.search_channel_by_name_korean(identifier)
                
        except Exception as e:
            print(f"❌ 채널 식별자 해결 오류: {e}")
            return None

    def search_channel_by_handle_korean(self, handle):
        """핸들명으로 채널 검색 (한글 지원)"""
        try:
            print(f"🎯 핸들 검색: @{handle}")
            
            # 핸들명에서 @제거
            clean_handle = handle.lstrip('@')
            
            # 여러 검색 쿼리 시도
            search_queries = [
                f"@{clean_handle}",
                clean_handle,
                f'"{clean_handle}"'
            ]
            
            for query in search_queries:
                try:
                    print(f"   검색 쿼리: {query}")
                    
                    search_request = self.api_client.youtube.search().list(
                        part='snippet',
                        q=query,
                        type='channel',
                        maxResults=10
                    )
                    search_response = search_request.execute()
                    
                    # 정확한 매치 찾기
                    for item in search_response.get('items', []):
                        channel_title = item['snippet']['title']
                        custom_url = item['snippet'].get('customUrl', '')
                        
                        print(f"   검색 결과: {channel_title} (customUrl: {custom_url})")
                        
                        # 핸들명 매치 확인
                        if (custom_url.lower() == f"@{clean_handle.lower()}" or
                            custom_url.lower() == clean_handle.lower() or
                            channel_title.lower() == clean_handle.lower()):
                            
                            channel_id = item['snippet']['channelId']
                            print(f"✅ 핸들 매치 성공: {channel_id}")
                            return channel_id
                    
                    # 정확한 매치가 없으면 첫 번째 결과 사용
                    if search_response.get('items'):
                        channel_id = search_response['items'][0]['snippet']['channelId']
                        print(f"📝 첫 번째 결과 사용: {channel_id}")
                        return channel_id
                        
                except Exception as e:
                    print(f"   쿼리 '{query}' 검색 오류: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ 핸들 검색 오류: {e}")
            return None

    def search_channel_by_name_korean(self, channel_name):
        """채널명으로 검색 (한글 지원 강화)"""
        try:
            print(f"📺 채널명 검색: {channel_name}")
            
            # 한글이 포함된 경우 URL 인코딩
            encoded_name = urllib.parse.quote(channel_name, safe='')
            
            # 여러 검색 전략 시도
            search_strategies = [
                channel_name,  # 원본
                f'"{channel_name}"',  # 따옴표로 감싸기
                encoded_name,  # URL 인코딩
                channel_name.replace(' ', ''),  # 공백 제거
            ]
            
            for strategy in search_strategies:
                try:
                    print(f"   검색 전략: {strategy}")
                    
                    search_request = self.api_client.youtube.search().list(
                        part='snippet',
                        q=strategy,
                        type='channel',
                        maxResults=15
                    )
                    search_response = search_request.execute()
                    
                    # 검색 결과 분석
                    for item in search_response.get('items', []):
                        found_title = item['snippet']['title']
                        channel_id = item['snippet']['channelId']
                        
                        print(f"   검색 결과: {found_title}")
                        
                        # 정확한 매치 확인
                        if self._is_channel_name_match(channel_name, found_title):
                            print(f"✅ 채널명 매치 성공: {channel_id}")
                            return channel_id
                    
                    # 정확한 매치가 없으면 첫 번째 결과 사용 (유사도 확인)
                    if search_response.get('items'):
                        first_result = search_response['items'][0]
                        first_title = first_result['snippet']['title']
                        first_id = first_result['snippet']['channelId']
                        
                        # 유사도 확인
                        if self._calculate_similarity(channel_name, first_title) > 0.7:
                            print(f"📝 유사한 첫 번째 결과 사용: {first_id} ({first_title})")
                            return first_id
                        
                except Exception as e:
                    print(f"   검색 전략 '{strategy}' 오류: {e}")
                    continue
            
            return None
            
        except Exception as e:
            print(f"❌ 채널명 검색 오류: {e}")
            return None

    def _is_channel_name_match(self, input_name, found_name):
        """채널명 매치 확인 (한글 지원)"""
        try:
            # 정규화
            input_normalized = input_name.lower().strip().replace(' ', '')
            found_normalized = found_name.lower().strip().replace(' ', '')
            
            # 정확한 매치
            if input_normalized == found_normalized:
                return True
            
            # 포함 관계 확인
            if input_normalized in found_normalized or found_normalized in input_normalized:
                return True
            
            # 한글의 경우 초성, 중성, 종성 분리해서 확인할 수도 있지만
            # 여기서는 간단한 방법 사용
            
            return False
            
        except Exception as e:
            print(f"채널명 매치 확인 오류: {e}")
            return False

    def _calculate_similarity(self, str1, str2):
        """문자열 유사도 계산 (간단한 버전)"""
        try:
            # 레벤슈타인 거리 기반 유사도 (간단 버전)
            str1 = str1.lower().strip()
            str2 = str2.lower().strip()
            
            if str1 == str2:
                return 1.0
            
            # 포함 관계로 간단히 계산
            if str1 in str2 or str2 in str1:
                return 0.8
            
            # 공통 문자 비율
            common_chars = set(str1) & set(str2)
            total_chars = set(str1) | set(str2)
            
            if not total_chars:
                return 0.0
            
            return len(common_chars) / len(total_chars)
            
        except Exception as e:
            print(f"유사도 계산 오류: {e}")
            return 0.0

    def _open_channel_analysis_dialog(self, channel_id, channel_name):
        """채널 분석 다이얼로그 열기"""
        try:
            self.progress_label.config(text="")
            
            dialog = EnhancedChannelAnalysisDialog(
                self.root, 
                channel_id, 
                channel_name, 
                self.api_client,
                int(self.channel_video_count_var.get()),
                "date" if self.channel_sort_var.get() == "최신순" else "viewCount"
            )
            dialog.transient(self.root)
            dialog.grab_set()
        except Exception as e:
            messagebox.showerror("오류", f"채널 분석 다이얼로그 생성 실패: {str(e)}")

    def create_keyword_filters(self, parent):
        """키워드 검색 필터 생성"""
        # 검색 키워드
        keyword_frame = tk.Frame(parent, bg=self.card_bg)
        keyword_frame.pack(fill=tk.X, pady=(10, 15))
        
        tk.Label(keyword_frame, text="🔍 검색 키워드", 
                font=('Arial', 12, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.keyword_entry = tk.Entry(keyword_frame, font=('Arial', 12), relief='solid', bd=1)
        self.keyword_entry.pack(fill=tk.X, ipady=8)
        self.keyword_entry.insert(0, "서울 카페")
        
        # 정렬 기준
        sort_frame = tk.Frame(parent, bg=self.card_bg)
        sort_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(sort_frame, text="📊 정렬 기준", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.sort_var = tk.StringVar(value="관련성")
        sort_combo = ttk.Combobox(sort_frame, textvariable=self.sort_var,
                                 values=["관련성", "업로드 날짜", "조회수"],
                                 state="readonly", font=('Arial', 11))
        sort_combo.pack(fill=tk.X)
        
        # 업로드 기간
        period_frame = tk.Frame(parent, bg=self.card_bg)
        period_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(period_frame, text="📅 업로드 기간", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.period_var = tk.StringVar(value="일주일")
        period_combo = ttk.Combobox(period_frame, textvariable=self.period_var,
                                   values=["오늘", "2일", "일주일", "한달", "3개월"],
                                   state="readonly", font=('Arial', 11))
        period_combo.pack(fill=tk.X)
        
        # 영상 유형
        type_frame = tk.Frame(parent, bg=self.card_bg)
        type_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(type_frame, text="🎬 영상 유형", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.video_type_var = tk.StringVar(value="전체")
        type_combo = ttk.Combobox(type_frame, textvariable=self.video_type_var,
                                 values=["전체", "쇼츠", "롱폼"],
                                 state="readonly", font=('Arial', 11))
        type_combo.pack(fill=tk.X)
        
        # 최소 조회수
        views_frame = tk.Frame(parent, bg=self.card_bg)
        views_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(views_frame, text="👀 최소 조회수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.min_views_var = tk.StringVar(value="10,000")
        views_combo = ttk.Combobox(views_frame, textvariable=self.min_views_var,
                                  values=["제한없음", "10,000", "100,000", "1,000,000"],
                                  state="readonly", font=('Arial', 11))
        views_combo.pack(fill=tk.X)
        
        # 최대 구독자 수
        subs_frame = tk.Frame(parent, bg=self.card_bg)
        subs_frame.pack(fill=tk.X, pady=(0, 15))
        
        tk.Label(subs_frame, text="👥 최대 구독자 수", 
                font=('Arial', 11, 'bold'),
                bg=self.card_bg, fg=self.text_primary).pack(anchor=tk.W, pady=(0, 5))
        
        self.max_subscribers_var = tk.StringVar(value="100,000")
        subs_combo = ttk.Combobox(subs_frame, textvariable=self.max_subscribers_var,
                                 values=["제한없음", "1,000", "10,000", "100,000"],
                                 state="readonly", font=('Arial', 11))
        subs_combo.pack(fill=tk.X)

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
        self.search_button.configure(state='disabled', text="🔍 검색 중...")
        self.progress_label.config(text="🚀 검색을 시작합니다...")
        
        # 기존 결과 초기화
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.selected_items.clear()
        
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
            self.update_progress("🔍 YouTube에서 영상을 검색하고 있습니다...")
            
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
                self.update_progress("❌ 검색 결과가 없습니다. 다른 키워드를 시도해보세요.")
                self.root.after(0, self.reset_search_button)
                return
            
            self.update_progress(f"✅ {len(videos)}개 영상 발견! 분석을 시작합니다...")
            
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
            self.update_progress(f"❌ 오류: {str(e)}")
            self.root.after(0, self.reset_search_button)
    
    def quick_analyze_videos(self, videos):
        """빠른 분석"""
        analyzed_videos = []
        
        for i, video in enumerate(videos):
            # 영상 길이 계산
            duration_seconds = 0
            formatted_duration = "00:00"
            video_type = "알수없음"
            
            try:
                duration_str = video['contentDetails']['duration']
                duration_seconds = self.api_client.parse_duration(duration_str)
                formatted_duration = self.format_duration(duration_seconds)
                video_type = "쇼츠" if duration_seconds <= 60 else "롱폼"
            except Exception as e:
                print(f"영상 길이 계산 오류: {e}")
            
            # 간단한 outlier score 계산
            current_views = int(video['statistics'].get('viewCount', 0))
            channel_avg_views = max(current_views // 2, 1000)
            outlier_score = round(current_views / channel_avg_views, 2)
            
            # Outlier 카테고리 계산
            outlier_category = self.categorize_outlier_score(outlier_score)
            
            # 분석 정보 추가
            video['analysis'] = {
                'engagement_rate': self.calculate_engagement_rate(video),
                'video_type': video_type,
                'formatted_duration': formatted_duration,
                'duration_seconds': duration_seconds,
                'channel_avg_views': channel_avg_views,
                'outlier_score': outlier_score,
                'outlier_category': outlier_category,
                'engagement_score': self.calculate_engagement_score(video),
                'views_per_day': self.calculate_views_per_day(video)
            }
            video['rank'] = i + 1
            analyzed_videos.append(video)
            
            # 진행 상황 업데이트
            if i % 10 == 0:
                self.update_progress(f"📊 분석 진행: {i+1}/{len(videos)} ({((i+1)/len(videos)*100):.0f}%)")
        
        return analyzed_videos
    
    def format_duration(self, seconds):
        """초를 시:분:초 형식으로 변환"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def categorize_outlier_score(self, outlier_score):
        """Outlier Score를 카테고리로 분류"""
        if outlier_score >= 5.0:
            return "🔥 바이럴"
        elif outlier_score >= 3.0:
            return "⭐ 히트"
        elif outlier_score >= 1.5:
            return "📈 양호"
        elif outlier_score >= 0.7:
            return "😐 평균"
        else:
            return "📉 저조"
    
    def calculate_engagement_score(self, video):
        """참여도 점수 계산"""
        try:
            stats = video.get('statistics', {})
            
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            comment_count = int(stats.get('commentCount', 0))
            
            if view_count == 0:
                return 0.0
            
            # 참여도 점수 계산
            like_ratio = (like_count / view_count) * 100
            comment_ratio = (comment_count / view_count) * 100
            
            engagement_score = (like_ratio * 0.7 + comment_ratio * 0.3) * 1000
            
            return min(round(engagement_score, 2), 100.0)
            
        except Exception as e:
            print(f"참여도 점수 계산 오류: {e}")
            return 0.0
    
    def calculate_views_per_day(self, video):
        """일일 평균 조회수 계산"""
        try:
            published_at = video['snippet']['publishedAt']
            view_count = int(video['statistics'].get('viewCount', 0))
            
            # 업로드 날짜 파싱
            upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_date = datetime.now(upload_date.tzinfo)
            
            # 경과 일수 계산
            days_elapsed = (current_date - upload_date).days
            if days_elapsed == 0:
                days_elapsed = 1
            
            return round(view_count / days_elapsed, 2)
            
        except Exception as e:
            print(f"일일 평균 조회수 계산 오류: {e}")
            return 0.0
    
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
    
    def update_progress(self, message):
        """진행 상황 업데이트"""
        self.root.after(0, lambda: self.progress_label.config(text=message))
    
    def reset_search_button(self):
        """검색 버튼 리셋"""
        self.search_button.configure(state='normal', text="🔍 검색 시작")
    
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
            title = snippet['title'][:30] + "..." if len(snippet['title']) > 30 else snippet['title']
            channel = snippet['channelTitle'][:15] + "..." if len(snippet['channelTitle']) > 15 else snippet['channelTitle']
            duration = analysis.get('formatted_duration', '00:00')
            video_type = analysis.get('video_type', '알수없음')
            outlier_score = f"{analysis.get('outlier_score', 1.0):.1f}x"
            engagement_score = f"{analysis.get('engagement_score', 0):.1f}"
            
            # 트리에 추가
            self.tree.insert("", tk.END, values=(
                "☐", i, published, views, title, channel, duration, video_type, outlier_score, engagement_score
            ))
        
        # 상태 업데이트
        self.results_count_label.config(text=f"총 {len(videos)}개 영상")
        self.progress_label.config(text="🎉 분석 완료! 결과를 확인하세요.")
        self.reset_search_button()
    
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
        columns = ("선택", "순번", "업로드 날짜", "조회수", "제목", "채널", "영상 길이", "영상 유형", "Outlier점수", "참여도점수")
        
        self.tree = ttk.Treeview(tree_frame, columns=columns, show="headings", height=15)
        
        # 컬럼 설정
        column_widths = {
            "선택": 50, "순번": 50, "업로드 날짜": 100, "조회수": 100, 
            "제목": 250, "채널": 130, "영상 길이": 80, "영상 유형": 80,
            "Outlier점수": 100, "참여도점수": 100
        }
        
        for col in columns:
            if col == "선택":
                self.tree.heading(col, text=col)
            else:
                self.tree.heading(col, text=col, command=lambda c=col: self.sort_treeview(c))
            self.tree.column(col, width=column_widths.get(col, 100))
        
        # 정렬 상태 추적
        self.sort_reverse = {}
        
        # 스크롤바
        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        
        # 레이아웃
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 이벤트 바인딩
        self.tree.bind("<Button-1>", self.on_item_click)
        self.tree.bind("<Double-1>", self.on_video_double_click)
        
        # 진행 상태 라벨
        self.progress_label = tk.Label(parent, text="", 
                                      font=('Arial', 11),
                                      bg=self.card_bg, fg=self.text_secondary)
        self.progress_label.pack(pady=10)
    
    def create_action_bar(self, parent):
        """하단 액션 바"""
        action_frame = tk.Frame(parent, bg=self.card_bg, height=100, relief='solid', bd=1)
        action_frame.pack(fill=tk.X, pady=(10, 0))
        action_frame.pack_propagate(False)
        
        # 상단 버튼 행 (선택 관련)
        top_button_row = tk.Frame(action_frame, bg=self.card_bg)
        top_button_row.pack(pady=(10, 5))
        
        # 선택 관련 버튼들
        tk.Button(top_button_row, text="모두 선택", 
                 command=self.select_all, bg="#e0e0e0", fg="black",
                 font=('Arial', 10), padx=8, pady=3).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_button_row, text="모두 해제", 
                 command=self.deselect_all, bg="#e0e0e0", fg="black",
                 font=('Arial', 10), padx=8, pady=3).pack(side=tk.LEFT, padx=5)
        
        tk.Button(top_button_row, text="상위 10개 선택", 
                 command=self.select_top_10, bg="#e0e0e0", fg="black",
                 font=('Arial', 10), padx=8, pady=3).pack(side=tk.LEFT, padx=5)
        
        # 하단 버튼 행 (액션 관련)
        bottom_button_row = tk.Frame(action_frame, bg=self.card_bg)
        bottom_button_row.pack(pady=(5, 10))
        
        # 분석 관련 버튼
        tk.Button(bottom_button_row, text="📺 선택한 채널 분석", 
                 command=self.analyze_selected_channels, bg="#FF6B35", fg="white",
                 font=('Arial', 11, 'bold'), padx=12, pady=5).pack(side=tk.LEFT, padx=10)
        
        # 구분선
        separator = tk.Frame(bottom_button_row, width=2, height=30, bg="#ccc")
        separator.pack(side=tk.LEFT, padx=10)
        
        # 다운로드 관련 버튼들
        tk.Button(bottom_button_row, text="📊 엑셀 추출", 
                 command=self.export_to_excel, bg="#28A745", fg="white",
                 font=('Arial', 11, 'bold'), padx=12, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(bottom_button_row, text="🖼️ 썸네일 다운로드", 
                 command=self.download_thumbnails, bg="#007AFF", fg="white",
                 font=('Arial', 11, 'bold'), padx=12, pady=5).pack(side=tk.LEFT, padx=5)
        
        tk.Button(bottom_button_row, text="📝 대본 다운로드", 
                 command=self.download_transcripts, bg="#007AFF", fg="white",
                 font=('Arial', 11, 'bold'), padx=12, pady=5).pack(side=tk.LEFT, padx=5)
    
    def on_item_click(self, event):
        """아이템 클릭 처리 (체크박스 토글)"""
        region = self.tree.identify_region(event.x, event.y)
        if region == "cell":
            item = self.tree.identify_row(event.y)
            column = self.tree.identify_column(event.x)
            
            # 선택 컬럼 클릭 시 체크박스 토글
            if item and column == "#1":  # 첫 번째 컬럼
                if item in self.selected_items:
                    self.selected_items.remove(item)
                    values = list(self.tree.item(item)['values'])
                    values[0] = "☐"
                    self.tree.item(item, values=values)
                else:
                    self.selected_items.add(item)
                    values = list(self.tree.item(item)['values'])
                    values[0] = "☑"
                    self.tree.item(item, values=values)
    
    def on_video_double_click(self, event):
        """영상 더블클릭 - YouTube에서 열기"""
        item = self.tree.identify_row(event.y)
        column = self.tree.identify_column(event.x)
        
        # 선택 컬럼이 아닌 경우에만 영상 열기
        if item and column != "#1":
            try:
                item_values = self.tree.item(item)['values']
                rank = int(item_values[1]) - 1  # 순위에서 인덱스로 변환
                
                if 0 <= rank < len(self.analyzed_videos):
                    video_id = self.analyzed_videos[rank]['id']
                    url = f"https://www.youtube.com/watch?v={video_id}"
                    webbrowser.open(url)
            except Exception as e:
                print(f"영상 열기 오류: {e}")
    
    def select_all(self):
        """모든 영상 선택"""
        for item in self.tree.get_children():
            self.selected_items.add(item)
            values = list(self.tree.item(item)['values'])
            values[0] = "☑"
            self.tree.item(item, values=values)
    
    def deselect_all(self):
        """모든 영상 선택 해제"""
        for item in self.tree.get_children():
            if item in self.selected_items:
                self.selected_items.remove(item)
            values = list(self.tree.item(item)['values'])
            values[0] = "☐"
            self.tree.item(item, values=values)
    
    def select_top_10(self):
        """상위 10개 영상 선택"""
        self.deselect_all()
        
        # Outlier 점수 기준으로 상위 10개 선택
        items_with_scores = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            try:
                outlier_score = float(values[8].replace('x', ''))
                items_with_scores.append((item, outlier_score))
            except:
                items_with_scores.append((item, 0.0))
        
        # 점수순으로 정렬
        items_with_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 상위 10개 선택
        for i, (item, score) in enumerate(items_with_scores[:10]):
            self.selected_items.add(item)
            values = list(self.tree.item(item)['values'])
            values[0] = "☑"
            self.tree.item(item, values=values)
    
    def export_to_excel(self):
        """엑셀로 결과 내보내기"""
        if not self.analyzed_videos:
            messagebox.showwarning("알림", "내보낼 데이터가 없습니다.")
            return
        
        filename = filedialog.asksaveasfilename(
            defaultextension=".xlsx",
            filetypes=[("Excel files", "*.xlsx"), ("All files", "*.*")],
            title="분석 결과 저장"
        )
        
        if filename:
            try:
                self.excel_generator = ExcelGenerator(filename)
                
                # 설정 정보 준비
                settings = {
                    'mode': 'keyword',
                    'mode_name': '키워드 검색',
                    'keyword': self.current_settings.get('keyword', ''),
                    'region_name': '한국',
                    'video_type_name': self.video_type_var.get(),
                    'period_days': self.current_settings.get('period_days', 7),
                    'max_subscribers_name': self.max_subscribers_var.get(),
                    'min_views_name': self.min_views_var.get()
                }
                
                self.excel_generator.create_excel_file(self.analyzed_videos, settings)
                messagebox.showinfo("성공", f"분석 결과가 저장되었습니다:\n{filename}")
            except Exception as e:
                messagebox.showerror("오류", f"엑셀 저장 실패: {str(e)}")
    
    def download_thumbnails(self):
        """선택한 영상의 썸네일 다운로드"""
        if not self.selected_items:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        selected_videos = []
        for item in self.selected_items:
            item_values = self.tree.item(item)['values']
            rank = int(item_values[1]) - 1
            
            if 0 <= rank < len(self.analyzed_videos):
                video = self.analyzed_videos[rank]
                selected_videos.append({
                    'video_id': video['id'],
                    'title': video['snippet']['title'],
                    'thumbnail_url': self.api_client.get_best_thumbnail_url(
                        video['snippet']['thumbnails']
                    ),
                    'rank': rank + 1
                })
        
        if selected_videos:
            self.progress_label.config(text="썸네일 다운로드 중...")
            
            thread = threading.Thread(target=lambda: self._download_thumbnails(selected_videos))
            thread.daemon = True
            thread.start()
    
    def _download_thumbnails(self, videos):
        """썸네일 다운로드 실행"""
        try:
            result = self.api_client.download_multiple_thumbnails(videos)
            
            self.root.after(0, lambda: messagebox.showinfo("완료", 
                f"썸네일 다운로드 완료!\n"
                f"성공: {len(result.get('downloaded_files', []))}개\n"
                f"실패: {result.get('failed_count', 0)}개"))
            
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"썸네일 다운로드 실패: {str(e)}"))
        
        self.root.after(0, lambda: self.progress_label.config(text=""))
    
    def download_transcripts(self):
        """선택한 영상의 대본 다운로드"""
        if not self.selected_items:
            messagebox.showwarning("알림", "다운로드할 영상을 선택해주세요.")
            return
        
        video_ids = []
        for item in self.selected_items:
            item_values = self.tree.item(item)['values']
            rank = int(item_values[1]) - 1
            
            if 0 <= rank < len(self.analyzed_videos):
                video = self.analyzed_videos[rank]
                video_ids.append(video['id'])
        
        if video_ids:
            self.progress_label.config(text="대본 다운로드 중...")
            
            thread = threading.Thread(target=lambda: self._download_transcripts(video_ids))
            thread.daemon = True
            thread.start()
    
    def _download_transcripts(self, video_ids):
        """대본 다운로드 실행"""
        try:
            # transcript_downloader 모듈 사용
            try:
                from transcript_downloader_fixed import WhisperFirstTranscriptDownloader
                downloader = WhisperFirstTranscriptDownloader()
                
                results = downloader.download_multiple_transcripts(video_ids)
                
                self.root.after(0, lambda: messagebox.showinfo("완료", 
                    f"대본 다운로드 완료!\n"
                    f"성공: {results['summary']['success_count']}개\n"
                    f"실패: {results['summary']['failed_count']}개\n"
                    f"성공률: {results['summary']['success_rate']:.1f}%"))
                
            except ImportError:
                self.root.after(0, lambda: messagebox.showerror("오류", 
                    "대본 다운로드 기능은 transcript_downloader 모듈이 필요합니다."))
                
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("오류", f"대본 다운로드 실패: {str(e)}"))
        
        self.root.after(0, lambda: self.progress_label.config(text=""))
    
    def analyze_selected_channels(self):
        """선택한 영상들의 채널 분석"""
        if not self.selected_items:
            messagebox.showwarning("알림", "분석할 영상을 선택해주세요.")
            return
        
        if not self.analyzed_videos:
            messagebox.showwarning("알림", "분석된 영상 데이터가 없습니다.")
            return
        
        try:
            # 선택된 영상들의 채널 정보 수집
            selected_channels = {}
            processed_count = 0
            
            for item in self.selected_items:
                try:
                    item_values = self.tree.item(item)['values']
                    if not item_values or len(item_values) < 2:
                        continue
                        
                    rank = int(item_values[1]) - 1
                    
                    if 0 <= rank < len(self.analyzed_videos):
                        video = self.analyzed_videos[rank]
                        if 'snippet' in video:
                            channel_id = video['snippet'].get('channelId', '')
                            channel_name = video['snippet'].get('channelTitle', 'Unknown Channel')
                            video_title = video['snippet'].get('title', 'Unknown Video')
                            
                            if channel_id and channel_name:
                                if channel_id not in selected_channels:
                                    selected_channels[channel_id] = {
                                        'name': channel_name,
                                        'videos': []
                                    }
                                selected_channels[channel_id]['videos'].append(video_title)
                                processed_count += 1
                except Exception as e:
                    continue
            
            if not selected_channels:
                messagebox.showwarning("알림", 
                    f"선택된 {len(self.selected_items)}개 영상에서 유효한 채널을 찾을 수 없습니다.")
                return
            
            # 채널이 1개인 경우 바로 분석
            if len(selected_channels) == 1:
                channel_id = list(selected_channels.keys())[0]
                channel_info = selected_channels[channel_id]
                channel_name = channel_info['name']
                
                self._open_channel_analysis(channel_id, channel_name)
            
            # 채널이 여러 개인 경우 선택 다이얼로그 표시
            else:
                self._show_channel_selection_dialog(selected_channels)
                
        except Exception as e:
            messagebox.showerror("오류", f"채널 분석 준비 중 오류가 발생했습니다: {str(e)}")
    
    def _show_channel_selection_dialog(self, channels):
        """채널 선택 다이얼로그 표시"""
        try:
            dialog = ChannelSelectionDialog(self.root, channels, self._open_channel_analysis)
            dialog.transient(self.root)
            dialog.grab_set()
        except Exception as e:
            messagebox.showerror("오류", f"채널 선택 다이얼로그 생성 실패: {str(e)}")
    
    def _open_channel_analysis(self, channel_id, channel_name):
        """채널 분석 다이얼로그 열기"""
        try:
            if not self.api_client:
                messagebox.showerror("오류", "API 클라이언트가 초기화되지 않았습니다.")
                return
            
            if not channel_id or not channel_name:
                messagebox.showerror("오류", "채널 정보가 유효하지 않습니다.")
                return
            
            dialog = EnhancedChannelAnalysisDialog(
                self.root, 
                channel_id, 
                channel_name, 
                self.api_client,
                50,  # 기본 50개 영상 분석
                "date"  # 최신순 정렬
            )
            dialog.transient(self.root)
            dialog.grab_set()
        except Exception as e:
            messagebox.showerror("오류", f"채널 분석 다이얼로그 생성 실패: {str(e)}")

    def sort_treeview(self, col):
        """트리뷰 정렬"""
        # 정렬 상태 토글
        reverse = not self.sort_reverse.get(col, False)
        self.sort_reverse[col] = reverse
        
        # 데이터 가져오기
        data = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            data.append((values, item))
        
        # 컬럼별 정렬 로직
        if col == "순번":
            data.sort(key=lambda x: int(x[0][1]), reverse=reverse)
        elif col == "업로드 날짜":
            data.sort(key=lambda x: x[0][2], reverse=reverse)
        elif col == "조회수":
            data.sort(key=lambda x: int(str(x[0][3]).replace(',', '')), reverse=reverse)
        elif col == "제목":
            data.sort(key=lambda x: x[0][4], reverse=reverse)
        elif col == "채널":
            data.sort(key=lambda x: x[0][5], reverse=reverse)
        elif col == "영상 길이":
            data.sort(key=lambda x: self._duration_to_seconds(x[0][6]), reverse=reverse)
        elif col == "영상 유형":
            data.sort(key=lambda x: x[0][7], reverse=reverse)
        elif col == "Outlier점수":
            data.sort(key=lambda x: float(str(x[0][8]).replace('x', '')), reverse=reverse)
        elif col == "참여도점수":
            data.sort(key=lambda x: float(x[0][9]), reverse=reverse)
        
        # 정렬된 순서로 아이템 재배치
        for index, (values, item) in enumerate(data):
            self.tree.move(item, '', index)
        
        # 헤더에 정렬 표시
        for column in self.tree['columns']:
            if column == col:
                sort_symbol = " ▼" if reverse else " ▲"
                self.tree.heading(column, text=column + sort_symbol)
            elif column != "선택":
                self.tree.heading(column, text=column)
    
    def _duration_to_seconds(self, duration_str):
        """시간 문자열을 초로 변환"""
        try:
            parts = duration_str.split(':')
            if len(parts) == 2:  # MM:SS
                return int(parts[0]) * 60 + int(parts[1])
            elif len(parts) == 3:  # HH:MM:SS
                return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
            else:
                return 0
        except:
            return 0


# 채널 선택 및 분석 다이얼로그 클래스들은 기존과 동일...
# (EnhancedChannelAnalysisDialog, ChannelSelectionDialog)

# 메인 실행
if __name__ == "__main__":
    root = tk.Tk()
    app = ImprovedYouTubeAnalyzerGUI(root)
    root.mainloop()