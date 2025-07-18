"""
채널 상세 정보 창 모듈
채널 검색 시 상세 정보를 표시하는 팝업 창
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import webbrowser
import threading
from datetime import datetime
import os

# 이미지 처리를 위한 import (선택적)
try:
    from PIL import Image, ImageTk
    import requests
    from io import BytesIO
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("⚠️ PIL/Pillow가 설치되지 않았습니다. 썸네일 표시가 제한됩니다.")

class ChannelDetailWindow:
    """채널 상세 정보 창"""
    
    def __init__(self, parent, channel_data, youtube_client):
        self.parent = parent
        self.channel_data = channel_data
        self.youtube_client = youtube_client
        
        # 새 창 생성
        self.window = tk.Toplevel(parent)
        self.setup_window()
        self.create_layout()
        self.load_channel_info()
        
    def setup_window(self):
        """창 설정"""
        channel_name = self.channel_data.get('snippet', {}).get('title', '채널')
        self.window.title(f"채널 상세 정보 - {channel_name}")
        self.window.geometry("1000x700")
        self.window.configure(bg='#f5f5f7')
        
        # 중앙 정렬
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (1000 // 2)
        y = (self.window.winfo_screenheight() // 2) - (700 // 2)
        self.window.geometry(f'1000x700+{x}+{y}')
        
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # 닫기 이벤트
        self.window.protocol("WM_DELETE_WINDOW", self.on_closing)
        
    def create_layout(self):
        """레이아웃 생성"""
        # 메인 컨테이너
        main_frame = tk.Frame(self.window, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 상단: 채널 기본 정보
        self.create_channel_header(main_frame)
        
        # 중간: 탭 노트북
        self.create_tab_notebook(main_frame)
        
        # 하단: 액션 버튼들
        self.create_action_buttons(main_frame)
        
    def create_channel_header(self, parent):
        """채널 기본 정보 헤더"""
        header_frame = tk.LabelFrame(
            parent,
            text="📺 채널 정보",
            font=('SF Pro Display', 14, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=20,
            pady=15
        )
        header_frame.pack(fill='x', pady=(0, 20))
        
        # 채널 썸네일과 기본 정보
        info_frame = tk.Frame(header_frame, bg='#f5f5f7')
        info_frame.pack(fill='x')
        
        # 썸네일 (왼쪽)
        thumbnail_frame = tk.Frame(info_frame, bg='#f5f5f7')
        thumbnail_frame.pack(side='left', padx=(0, 20))
        
        self.thumbnail_label = tk.Label(
            thumbnail_frame,
            text="썸네일\n로딩 중...",
            font=('SF Pro Display', 10),
            bg='#e5e5e7',
            width=15,
            height=8,
            relief='solid',
            borderwidth=1
        )
        self.thumbnail_label.pack()
        
        # 채널 정보 (오른쪽)
        details_frame = tk.Frame(info_frame, bg='#f5f5f7')
        details_frame.pack(side='left', fill='both', expand=True)
        
        # 채널명
        snippet = self.channel_data.get('snippet', {})
        statistics = self.channel_data.get('statistics', {})
        
        channel_name = snippet.get('title', '알 수 없음')
        self.channel_name_label = tk.Label(
            details_frame,
            text=channel_name,
            font=('SF Pro Display', 16, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            wraplength=400,
            justify='left'
        )
        self.channel_name_label.pack(anchor='w', pady=(0, 10))
        
        # 구독자 수, 영상 수 등
        try:
            subscriber_count = int(statistics.get('subscriberCount', 0))
            video_count = int(statistics.get('videoCount', 0))
            view_count = int(statistics.get('viewCount', 0))
            
            stats_text = f"구독자: {subscriber_count:,}명\n"
            stats_text += f"총 영상: {video_count:,}개\n"
            stats_text += f"총 조회수: {view_count:,}회"
        except ValueError:
            stats_text = "구독자: 비공개\n"
            stats_text += f"총 영상: {statistics.get('videoCount', '0')}개\n"
            stats_text += f"총 조회수: {statistics.get('viewCount', '0')}회"
        
        self.stats_label = tk.Label(
            details_frame,
            text=stats_text,
            font=('SF Pro Display', 12),
            bg='#f5f5f7',
            fg='#86868b',
            justify='left'
        )
        self.stats_label.pack(anchor='w')
        
        # 채널 설명 (요약)
        description = snippet.get('description', '')
        if description:
            short_desc = description[:200] + "..." if len(description) > 200 else description
            desc_label = tk.Label(
                details_frame,
                text=f"설명: {short_desc}",
                font=('SF Pro Display', 10),
                bg='#f5f5f7',
                fg='#86868b',
                justify='left',
                wraplength=400
            )
            desc_label.pack(anchor='w', pady=(10, 0))
        
    def create_tab_notebook(self, parent):
        """탭 노트북 생성"""
        self.notebook = ttk.Notebook(parent)
        self.notebook.pack(fill='both', expand=True, pady=(0, 20))
        
        # 1. 최근 영상 탭
        self.videos_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.videos_frame, text="📹 최근 영상")
        self.create_videos_tab()
        
        # 2. 채널 통계 탭
        self.stats_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.stats_frame, text="📊 상세 통계")
        self.create_stats_tab()
        
        # 3. 다운로드 탭
        self.download_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.download_frame, text="⬇️ 다운로드")
        self.create_download_tab()
        
    def create_videos_tab(self):
        """최근 영상 탭"""
        # 영상 목록 테이블
        columns = ('title', 'views', 'likes', 'comments', 'published', 'duration')
        
        # 테이블 컨테이너
        table_container = tk.Frame(self.videos_frame, bg='#f5f5f7')
        table_container.pack(fill='both', expand=True, padx=10, pady=10)
        
        self.videos_tree = ttk.Treeview(
            table_container,
            columns=columns,
            show='headings',
            height=15
        )
        
        # 컬럼 설정
        self.videos_tree.heading('title', text='제목')
        self.videos_tree.heading('views', text='조회수')
        self.videos_tree.heading('likes', text='좋아요')
        self.videos_tree.heading('comments', text='댓글')
        self.videos_tree.heading('published', text='업로드일')
        self.videos_tree.heading('duration', text='길이')
        
        self.videos_tree.column('title', width=300)
        self.videos_tree.column('views', width=100)
        self.videos_tree.column('likes', width=80)
        self.videos_tree.column('comments', width=80)
        self.videos_tree.column('published', width=100)
        self.videos_tree.column('duration', width=80)
        
        # 스크롤바
        scrollbar_v = ttk.Scrollbar(table_container, orient='vertical', command=self.videos_tree.yview)
        scrollbar_h = ttk.Scrollbar(table_container, orient='horizontal', command=self.videos_tree.xview)
        self.videos_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        # 그리드 레이아웃
        self.videos_tree.grid(row=0, column=0, sticky='nsew')
        scrollbar_v.grid(row=0, column=1, sticky='ns')
        scrollbar_h.grid(row=1, column=0, sticky='ew')
        
        table_container.grid_rowconfigure(0, weight=1)
        table_container.grid_columnconfigure(0, weight=1)
        
        # 더블클릭으로 영상 열기
        self.videos_tree.bind('<Double-1>', self.on_video_double_click)
        
    def create_stats_tab(self):
        """상세 통계 탭"""
        stats_container = tk.Frame(self.stats_frame, bg='#f5f5f7')
        stats_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 통계 정보 표시
        statistics = self.channel_data.get('statistics', {})
        snippet = self.channel_data.get('snippet', {})
        
        # 기본 통계
        basic_stats = [
            ("총 구독자 수", self.format_number(statistics.get('subscriberCount', 0))),
            ("총 영상 수", self.format_number(statistics.get('videoCount', 0))),
            ("총 조회수", self.format_number(statistics.get('viewCount', 0))),
            ("숨겨진 구독자 수", "예" if statistics.get('hiddenSubscriberCount') else "아니요"),
        ]
        
        # 채널 정보
        channel_info = [
            ("채널 생성일", snippet.get('publishedAt', '')[:10]),
            ("국가", snippet.get('country', '알 수 없음')),
            ("기본 언어", snippet.get('defaultLanguage', '알 수 없음')),
        ]
        
        # 기본 통계 섹션
        basic_frame = tk.LabelFrame(
            stats_container,
            text="📊 기본 통계",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=15,
            pady=10
        )
        basic_frame.pack(fill='x', pady=(0, 15))
        
        for i, (label, value) in enumerate(basic_stats):
            self.create_stat_row(basic_frame, label, value, i)
        
        # 채널 정보 섹션
        info_frame = tk.LabelFrame(
            stats_container,
            text="ℹ️ 채널 정보",
            font=('SF Pro Display', 12, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            padx=15,
            pady=10
        )
        info_frame.pack(fill='x')
        
        for i, (label, value) in enumerate(channel_info):
            self.create_stat_row(info_frame, label, value, i)
    
    def create_stat_row(self, parent, label_text, value_text, row):
        """통계 행 생성"""
        row_frame = tk.Frame(parent, bg='#f5f5f7')
        row_frame.pack(fill='x', pady=2)
        
        tk.Label(
            row_frame,
            text=f"{label_text}:",
            font=('SF Pro Display', 11),
            bg='#f5f5f7',
            fg='#86868b',
            width=20,
            anchor='w'
        ).pack(side='left')
        
        tk.Label(
            row_frame,
            text=str(value_text),
            font=('SF Pro Display', 11, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f',
            anchor='w'
        ).pack(side='left', padx=(10, 0))
            
    def create_download_tab(self):
        """다운로드 탭"""
        download_container = tk.Frame(self.download_frame, bg='#f5f5f7')
        download_container.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 제목
        title_label = tk.Label(
            download_container,
            text="📥 다운로드 옵션",
            font=('SF Pro Display', 14, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        title_label.pack(pady=(0, 20))
        
        # 다운로드 옵션들
        options = [
            ("채널 썸네일 다운로드", "채널의 프로필 이미지를 다운로드합니다", self.download_channel_thumbnail),
            ("최근 영상 썸네일 일괄 다운로드", "최근 영상들의 썸네일을 모두 다운로드합니다", self.download_video_thumbnails),
            ("영상 자막 일괄 다운로드", "최근 영상들의 자막을 모두 다운로드합니다", self.download_subtitles),
            ("채널 정보 엑셀로 내보내기", "채널 정보와 영상 목록을 엑셀 파일로 저장합니다", self.export_to_excel),
        ]
        
        for title, description, command in options:
            option_frame = tk.Frame(download_container, bg='#f5f5f7')
            option_frame.pack(fill='x', pady=5)
            
            btn = tk.Button(
                option_frame,
                text=title,
                font=('SF Pro Display', 12, 'bold'),
                bg='#007aff',
                fg='white',
                relief='flat',
                padx=20,
                pady=10,
                command=command,
                width=30,
                anchor='w'
            )
            btn.pack(side='left')
            
            desc_label = tk.Label(
                option_frame,
                text=description,
                font=('SF Pro Display', 10),
                bg='#f5f5f7',
                fg='#86868b'
            )
            desc_label.pack(side='left', padx=(15, 0), anchor='w')
            
    def create_action_buttons(self, parent):
        """하단 액션 버튼들"""
        button_frame = tk.Frame(parent, bg='#f5f5f7')
        button_frame.pack(fill='x')
        
        # 채널 분석 버튼
        analyze_btn = tk.Button(
            button_frame,
            text="📊 채널 분석 시작",
            font=('SF Pro Display', 12, 'bold'),
            bg='#34c759',
            fg='white',
            relief='flat',
            padx=30,
            pady=12,
            command=self.start_channel_analysis
        )
        analyze_btn.pack(side='left')
        
        # YouTube에서 열기 버튼
        open_btn = tk.Button(
            button_frame,
            text="🔗 YouTube에서 열기",
            font=('SF Pro Display', 12),
            bg='#ff3b30',
            fg='white',
            relief='flat',
            padx=30,
            pady=12,
            command=self.open_in_youtube
        )
        open_btn.pack(side='left', padx=(10, 0))
        
        # 닫기 버튼
        close_btn = tk.Button(
            button_frame,
            text="닫기",
            font=('SF Pro Display', 12),
            bg='#86868b',
            fg='white',
            relief='flat',
            padx=30,
            pady=12,
            command=self.on_closing
        )
        close_btn.pack(side='right')
        
    def load_channel_info(self):
        """채널 정보 로드"""
        try:
            # 채널 썸네일 로드
            self.load_thumbnail()
            
            # 최근 영상 로드
            self.load_recent_videos()
            
        except Exception as e:
            print(f"채널 정보 로드 오류: {e}")
            
    def load_thumbnail(self):
        """채널 썸네일 로드"""
        def load_in_background():
            try:
                if not PIL_AVAILABLE:
                    self.thumbnail_label.config(text="썸네일\n(PIL 필요)", bg='#e5e5e7')
                    return
                
                thumbnail_url = self.channel_data.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url')
                if not thumbnail_url:
                    # medium이나 default 시도
                    thumbnails = self.channel_data.get('snippet', {}).get('thumbnails', {})
                    thumbnail_url = thumbnails.get('medium', {}).get('url') or thumbnails.get('default', {}).get('url')
                
                if thumbnail_url:
                    response = requests.get(thumbnail_url, timeout=5)
                    response.raise_for_status()
                    
                    img = Image.open(BytesIO(response.content))
                    img = img.resize((120, 120), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    
                    # UI 스레드에서 업데이트
                    self.window.after(0, lambda: self.update_thumbnail(photo))
                else:
                    self.window.after(0, lambda: self.thumbnail_label.config(text="썸네일\n없음", bg='#e5e5e7'))
                    
            except Exception as e:
                print(f"썸네일 로드 오류: {e}")
                self.window.after(0, lambda: self.thumbnail_label.config(text="썸네일\n로드 실패", bg='#e5e5e7'))
        
        # 백그라운드에서 로드
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def update_thumbnail(self, photo):
        """썸네일 업데이트 (UI 스레드에서 호출)"""
        try:
            self.thumbnail_label.config(image=photo, text="")
            self.thumbnail_label.image = photo  # 참조 유지
        except Exception as e:
            print(f"썸네일 업데이트 오류: {e}")
            
    def load_recent_videos(self):
        """최근 영상 로드"""
        def load_in_background():
            try:
                channel_id = self.channel_data.get('id')
                if not channel_id:
                    return
                
                print(f"채널 {channel_id}의 최근 영상 로드 중...")
                
                # 채널의 uploads 플레이리스트 ID 구하기
                uploads_playlist_id = 'UU' + channel_id[2:]  # UC -> UU로 변경
                
                # 플레이리스트 아이템 가져오기
                request = self.youtube_client.youtube.playlistItems().list(
                    part='snippet',
                    playlistId=uploads_playlist_id,
                    maxResults=20,
                    order='date'
                )
                
                response = request.execute()
                items = response.get('items', [])
                
                if not items:
                    print("최근 영상이 없습니다.")
                    return
                
                # 비디오 ID 추출
                video_ids = [item['snippet']['resourceId']['videoId'] for item in items]
                
                # 비디오 상세 정보 가져오기
                videos_request = self.youtube_client.youtube.videos().list(
                    part='snippet,statistics,contentDetails',
                    id=','.join(video_ids)
                )
                
                videos_response = videos_request.execute()
                videos = videos_response.get('items', [])
                
                # UI 업데이트
                self.window.after(0, lambda: self.update_videos_table(videos))
                
            except Exception as e:
                print(f"최근 영상 로드 오류: {e}")
        
        # 백그라운드에서 로드
        threading.Thread(target=load_in_background, daemon=True).start()
    
    def update_videos_table(self, videos):
        """영상 테이블 업데이트 (UI 스레드에서 호출)"""
        try:
            # 기존 데이터 삭제
            for item in self.videos_tree.get_children():
                self.videos_tree.delete(item)
            
            # 새 데이터 추가
            for video in videos:
                snippet = video.get('snippet', {})
                statistics = video.get('statistics', {})
                content_details = video.get('contentDetails', {})
                
                title = snippet.get('title', '')[:40] + "..." if len(snippet.get('title', '')) > 40 else snippet.get('title', '')
                views = self.format_number(statistics.get('viewCount', 0))
                likes = self.format_number(statistics.get('likeCount', 0))
                comments = self.format_number(statistics.get('commentCount', 0))
                published = snippet.get('publishedAt', '')[:10]
                
                # 영상 길이 파싱
                duration = content_details.get('duration', '')
                formatted_duration = self.parse_duration(duration)
                
                self.videos_tree.insert('', 'end', values=(
                    title, views, likes, comments, published, formatted_duration
                ), tags=(video['id'],))  # video_id를 태그로 저장
                
            print(f"✅ {len(videos)}개 영상 목록 업데이트 완료")
            
        except Exception as e:
            print(f"영상 테이블 업데이트 오류: {e}")
    
    def on_video_double_click(self, event):
        """영상 더블클릭 시 YouTube에서 열기"""
        try:
            selection = self.videos_tree.selection()
            if not selection:
                return
            
            item = self.videos_tree.item(selection[0])
            tags = item.get('tags', [])
            
            if tags:
                video_id = tags[0]
                url = f"https://www.youtube.com/watch?v={video_id}"
                webbrowser.open(url)
            else:
                messagebox.showwarning("경고", "영상 링크를 찾을 수 없습니다.")
                
        except Exception as e:
            print(f"영상 열기 오류: {e}")
            messagebox.showerror("오류", "영상을 열 수 없습니다.")
    
    # 다운로드 메서드들
    def download_channel_thumbnail(self):
        """채널 썸네일 다운로드"""
        try:
            thumbnail_url = self.channel_data.get('snippet', {}).get('thumbnails', {}).get('high', {}).get('url')
            if not thumbnail_url:
                messagebox.showwarning("경고", "썸네일 URL을 찾을 수 없습니다.")
                return
            
            # 파일 저장 대화상자
            channel_name = self.channel_data.get('snippet', {}).get('title', 'channel')
            safe_name = "".join(c for c in channel_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
            
            filename = filedialog.asksaveasfilename(
                defaultextension=".jpg",
                filetypes=[("JPEG files", "*.jpg"), ("All files", "*.*")],
                initialvalue=f"{safe_name}_thumbnail.jpg"
            )
            
            if filename:
                # 다운로드 실행
                import requests
                response = requests.get(thumbnail_url, timeout=10)
                response.raise_for_status()
                
                with open(filename, 'wb') as f:
                    f.write(response.content)
                
                messagebox.showinfo("완료", f"썸네일이 저장되었습니다:\n{filename}")
                
        except Exception as e:
            print(f"썸네일 다운로드 오류: {e}")
            messagebox.showerror("오류", f"썸네일 다운로드 중 오류가 발생했습니다:\n{str(e)}")
        
    def download_video_thumbnails(self):
        """최근 영상 썸네일 일괄 다운로드"""
        messagebox.showinfo("준비 중", "영상 썸네일 일괄 다운로드 기능을 준비 중입니다.")
        
    def download_subtitles(self):
        """자막 일괄 다운로드"""
        messagebox.showinfo("준비 중", "자막 일괄 다운로드 기능을 준비 중입니다.")
        
    def export_to_excel(self):
        """엑셀로 내보내기"""
        messagebox.showinfo("준비 중", "엑셀 내보내기 기능을 준비 중입니다.")
        
    def start_channel_analysis(self):
        """채널 분석 시작"""
        try:
            # 부모 창으로 이동하여 채널 분석 시작
            if hasattr(self.parent, 'main_window'):
                main_window = self.parent.main_window
            else:
                # 부모가 메인 창인 경우
                main_window = self.parent
            
            # 채널 분석 탭 로드
            if hasattr(main_window, 'load_channel_tab'):
                main_window.load_channel_tab()
                
                # 채널 분석 탭으로 전환
                main_window.notebook.select(1)  # 채널 분석 탭
                
                # 채널 URL 설정
                if hasattr(main_window, 'channel_tab') and main_window.channel_tab:
                    channel_id = self.channel_data.get('id')
                    channel_url = f"https://www.youtube.com/channel/{channel_id}"
                    main_window.channel_tab.set_channel_input(channel_url)
                    
                    channel_name = self.channel_data.get('snippet', {}).get('title', '선택된 채널')
                    messagebox.showinfo("채널 분석", f"'{channel_name}' 채널 분석 페이지로 이동합니다.")
                    
                    # 창 닫기
                    self.on_closing()
                else:
                    messagebox.showerror("오류", "채널 분석 탭을 로드할 수 없습니다.")
            else:
                messagebox.showerror("오류", "메인 창을 찾을 수 없습니다.")
            
        except Exception as e:
            print(f"채널 분석 시작 오류: {e}")
            messagebox.showerror("오류", f"채널 분석을 시작할 수 없습니다:\n{str(e)}")
        
    def open_in_youtube(self):
        """YouTube에서 채널 열기"""
        try:
            channel_id = self.channel_data.get('id')
            if channel_id:
                url = f"https://www.youtube.com/channel/{channel_id}"
                webbrowser.open(url)
            else:
                messagebox.showerror("오류", "채널 ID를 찾을 수 없습니다.")
        except Exception as e:
            print(f"YouTube 열기 오류: {e}")
            messagebox.showerror("오류", "YouTube 페이지를 열 수 없습니다.")
    
    def on_closing(self):
        """창 닫기"""
        try:
            self.window.grab_release()
            self.window.destroy()
        except Exception as e:
            print(f"창 닫기 오류: {e}")
    
    # 유틸리티 메서드들
    def format_number(self, number):
        """숫자 포맷팅"""
        try:
            if isinstance(number, str):
                number = int(number)
            return f"{number:,}"
        except (ValueError, TypeError):
            return str(number)
    
    def parse_duration(self, duration):
        """YouTube duration 파싱 (PT1H2M3S -> 1:02:03)"""
        if not duration:
            return "00:00"
        
        try:
            import re
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration)
            
            if not match:
                return "00:00"
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            if hours > 0:
                return f"{hours}:{minutes:02d}:{seconds:02d}"
            else:
                return f"{minutes}:{seconds:02d}"
                
        except Exception as e:
            print(f"Duration 파싱 오류: {e}")
            return "00:00"


if __name__ == "__main__":
    # 테스트용 코드
    print("ChannelDetailWindow 모듈이 직접 실행되었습니다.")
    print("이 모듈은 main_window.py에서 import하여 사용하세요.")