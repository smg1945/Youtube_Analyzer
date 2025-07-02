"""
YouTube 트렌드 분석기 v3.0
통합 실행 파일
"""

import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox
import subprocess

class YouTubeAnalyzerLauncher:
    def __init__(self, root):
        self.root = root
        self.root.title("🎬 YouTube 트렌드 분석기 v3.0")
        self.root.geometry("600x400")
        self.root.configure(bg='#f5f5f7')
        
        # 중앙 정렬
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (600 // 2)
        y = (self.root.winfo_screenheight() // 2) - (400 // 2)
        self.root.geometry(f'600x400+{x}+{y}')
        
        self.create_widgets()
        self.check_api_key()
    
    def create_widgets(self):
        """위젯 생성"""
        # 제목
        title_label = tk.Label(
            self.root,
            text="YouTube 트렌드 분석기",
            font=('SF Pro Display', 24, 'bold'),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        title_label.pack(pady=30)
        
        # 버전 정보
        version_label = tk.Label(
            self.root,
            text="v3.0 - 통합 버전",
            font=('SF Pro Display', 12),
            bg='#f5f5f7',
            fg='#86868b'
        )
        version_label.pack(pady=(0, 30))
        
        # 버튼 프레임
        button_frame = tk.Frame(self.root, bg='#f5f5f7')
        button_frame.pack(expand=True)
        
        # 영상 검색 분석기 버튼
        search_btn = tk.Button(
            button_frame,
            text="🔍 영상 검색 분석기",
            font=('SF Pro Display', 14),
            bg='#007aff',
            fg='white',
            width=25,
            height=3,
            borderwidth=0,
            cursor='hand2',
            command=self.launch_search_analyzer
        )
        search_btn.pack(pady=10)
        
        # 설명
        tk.Label(
            button_frame,
            text="키워드로 YouTube 영상을 검색하고 분석합니다",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        ).pack(pady=(0, 20))
        
        # 트렌드 대시보드 버튼
        trend_btn = tk.Button(
            button_frame,
            text="🔥 트렌드 키워드 대시보드",
            font=('SF Pro Display', 14),
            bg='#ff3b30',
            fg='white',
            width=25,
            height=3,
            borderwidth=0,
            cursor='hand2',
            command=self.launch_trend_dashboard
        )
        trend_btn.pack(pady=10)
        
        # 설명
        tk.Label(
            button_frame,
            text="실시간 YouTube 트렌드 키워드를 모니터링합니다",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        ).pack(pady=(0, 20))
        
        # 종료 버튼
        exit_btn = tk.Button(
            self.root,
            text="종료",
            font=('SF Pro Display', 12),
            bg='#e5e5e7',
            fg='#1d1d1f',
            width=10,
            borderwidth=0,
            cursor='hand2',
            command=self.root.quit
        )
        exit_btn.pack(pady=20)
    
    def check_api_key(self):
        """API 키 확인"""
        try:
            # .env 파일 확인
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    content = f.read()
                    if 'YOUTUBE_API_KEY=' in content and 'your_api_key_here' not in content:
                        return True
            
            # config.py 확인
            try:
                import config
                if hasattr(config, 'DEVELOPER_KEY') and config.DEVELOPER_KEY != "YOUR_YOUTUBE_API_KEY_HERE":
                    return True
            except:
                pass
            
            # API 키 설정 안내
            result = messagebox.askyesno(
                "API 키 설정 필요",
                "YouTube API 키가 설정되지 않았습니다.\n\n"
                "API 키를 설정하시겠습니까?"
            )
            
            if result:
                self.setup_api_key()
                
        except Exception as e:
            print(f"API 키 확인 오류: {e}")
    
    def setup_api_key(self):
        """API 키 설정"""
        dialog = tk.Toplevel(self.root)
        dialog.title("API 키 설정")
        dialog.geometry("500x200")
        dialog.configure(bg='#f5f5f7')
        
        # 중앙 정렬
        dialog.transient(self.root)
        dialog.grab_set()
        
        # 안내 문구
        tk.Label(
            dialog,
            text="YouTube Data API v3 키를 입력하세요:",
            font=('SF Pro Display', 12),
            bg='#f5f5f7'
        ).pack(pady=20)
        
        # 입력 필드
        api_entry = tk.Entry(dialog, font=('SF Pro Display', 11), width=50)
        api_entry.pack(pady=10)
        
        # 버튼 프레임
        btn_frame = tk.Frame(dialog, bg='#f5f5f7')
        btn_frame.pack(pady=20)
        
        def save_api_key():
            api_key = api_entry.get().strip()
            if api_key:
                # .env 파일에 저장
                with open('.env', 'w') as f:
                    f.write(f"YOUTUBE_API_KEY={api_key}\n")
                
                # config.py 업데이트
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
                
                messagebox.showinfo("성공", "API 키가 저장되었습니다!")
                dialog.destroy()
            else:
                messagebox.showwarning("오류", "API 키를 입력해주세요.")
        
        tk.Button(
            btn_frame,
            text="저장",
            font=('SF Pro Display', 11),
            bg='#007aff',
            fg='white',
            borderwidth=0,
            padx=20,
            pady=5,
            command=save_api_key
        ).pack(side=tk.LEFT, padx=5)
        
        tk.Button(
            btn_frame,
            text="취소",
            font=('SF Pro Display', 11),
            bg='#e5e5e7',
            borderwidth=0,
            padx=20,
            pady=5,
            command=dialog.destroy
        ).pack(side=tk.LEFT, padx=5)
        
        # API 키 획득 방법 안내
        info_text = "💡 Google Cloud Console에서 YouTube Data API v3 키를 발급받으세요."
        tk.Label(
            dialog,
            text=info_text,
            font=('SF Pro Display', 9),
            bg='#f5f5f7',
            fg='#86868b'
        ).pack(pady=10)
    
    def launch_search_analyzer(self):
        """영상 검색 분석기 실행"""
        try:
            from improved_gui import ImprovedYouTubeAnalyzerGUI
            
            search_window = tk.Toplevel()
            search_window.protocol("WM_DELETE_WINDOW", search_window.destroy)
            
            app = ImprovedYouTubeAnalyzerGUI(search_window)
            
        except Exception as e:
            messagebox.showerror(
                "실행 오류",
                f"영상 검색 분석기를 실행할 수 없습니다.\n\n"
                f"오류: {str(e)}\n\n"
                f"improved_gui.py 파일이 있는지 확인하세요."
            )
    
    def launch_trend_dashboard(self):
        """트렌드 대시보드 실행"""
        try:
            # API 키 가져오기
            api_key = None
            
            # .env에서 확인
            if os.path.exists('.env'):
                with open('.env', 'r') as f:
                    for line in f:
                        if line.startswith('YOUTUBE_API_KEY='):
                            api_key = line.split('=', 1)[1].strip()
                            break
            
            # config.py에서 확인
            if not api_key:
                try:
                    import config
                    if hasattr(config, 'DEVELOPER_KEY'):
                        api_key = config.DEVELOPER_KEY
                except:
                    pass
            
            # 입력 받기
            if not api_key or api_key == "YOUR_YOUTUBE_API_KEY_HERE":
                import tkinter.simpledialog as simpledialog
                api_key = simpledialog.askstring(
                    "API Key",
                    "YouTube API Key를 입력하세요:",
                    parent=self.root
                )
                
                if not api_key:
                    return
            
            # 대시보드 실행
            from youtube_trend_dashboard import YouTubeTrendDashboard
            
            dashboard_window = tk.Toplevel()
            dashboard_window.protocol("WM_DELETE_WINDOW", dashboard_window.destroy)
            
            app = YouTubeTrendDashboard(dashboard_window, api_key)
            
        except Exception as e:
            messagebox.showerror(
                "실행 오류",
                f"트렌드 대시보드를 실행할 수 없습니다.\n\n"
                f"오류: {str(e)}\n\n"
                f"youtube_trend_dashboard.py 파일이 있는지 확인하세요."
            )


def main():
    """메인 함수"""
    # 필수 패키지 확인
    try:
        import pandas
        import requests
        from googleapiclient.discovery import build
    except ImportError as e:
        print(f"❌ 필수 패키지가 설치되지 않았습니다: {e}")
        print("다음 명령을 실행하세요:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    # GUI 실행
    root = tk.Tk()
    app = YouTubeAnalyzerLauncher(root)
    root.mainloop()


if __name__ == "__main__":
    main()