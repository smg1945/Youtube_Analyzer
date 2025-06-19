"""
YouTube 트렌드 분석기 GUI 실행 스크립트
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox

def check_dependencies():
    """필수 라이브러리 설치 확인"""
    missing_packages = []
    
    try:
        import pandas
    except ImportError:
        missing_packages.append("pandas")
    
    try:
        import openpyxl
    except ImportError:
        missing_packages.append("openpyxl")
    
    try:
        from googleapiclient.discovery import build
    except ImportError:
        missing_packages.append("google-api-python-client")
    
    try:
        import requests
    except ImportError:
        missing_packages.append("requests")
    
    try:
        from PIL import Image
    except ImportError:
        missing_packages.append("Pillow")
    
    # 선택적 패키지들
    optional_missing = []
    
    try:
        import konlpy
    except ImportError:
        optional_missing.append("konlpy (한국어 키워드 추출)")
    
    try:
        import textblob
    except ImportError:
        optional_missing.append("textblob (영어 감정 분석)")
    
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
    except ImportError:
        optional_missing.append("youtube-transcript-api (자막 다운로드)")
    
    try:
        import yt_dlp
    except ImportError:
        optional_missing.append("yt-dlp (영상 다운로드)")
    
    try:
        import whisper
    except ImportError:
        optional_missing.append("openai-whisper (음성 인식)")
    
    return missing_packages, optional_missing

def show_dependency_info(missing_packages, optional_missing):
    """의존성 정보 표시"""
    if missing_packages:
        error_msg = "다음 필수 패키지가 설치되지 않았습니다:\\n\\n"
        error_msg += "\\n".join(f"• {pkg}" for pkg in missing_packages)
        error_msg += "\\n\\n설치 명령어:\\n"
        error_msg += f"pip install {' '.join(missing_packages)}"
        
        messagebox.showerror("필수 패키지 누락", error_msg)
        return False
    
    if optional_missing:
        warning_msg = "다음 선택적 패키지가 설치되지 않았습니다:\\n"
        warning_msg += "(일부 기능이 제한될 수 있습니다)\\n\\n"
        warning_msg += "\\n".join(f"• {pkg}" for pkg in optional_missing)
        warning_msg += "\\n\\n계속 진행하시겠습니까?"
        
        return messagebox.askyesno("선택적 패키지 누락", warning_msg)
    
    return True

def main():
    """메인 실행 함수"""
    print("🎬 YouTube 트렌드 분석기 GUI 시작 중...")
    
    # 의존성 확인
    missing_packages, optional_missing = check_dependencies()
    
    # GUI 초기화 (의존성 확인용)
    root = tk.Tk()
    root.withdraw()  # 임시로 숨김
    
    # 의존성 정보 표시
    if not show_dependency_info(missing_packages, optional_missing):
        root.destroy()
        return
    
    # 설정 파일 확인
    try:
        import config
        if not config.DEVELOPER_KEY or config.DEVELOPER_KEY == "YOUR_YOUTUBE_API_KEY_HERE":
            messagebox.showwarning(
                "API 키 필요", 
                "YouTube API 키가 설정되지 않았습니다.\\n\\n"
                "config.py 파일에서 DEVELOPER_KEY를 설정한 후 다시 실행해주세요.\\n\\n"
                "API 키는 Google Cloud Console에서 발급받을 수 있습니다."
            )
    except ImportError:
        messagebox.showerror(
            "설정 파일 오류", 
            "config.py 파일을 찾을 수 없습니다.\\n\\n"
            "프로젝트 파일이 모두 있는지 확인해주세요."
        )
        root.destroy()
        return
    
    root.destroy()
    
    # GUI 앱 실행
    try:
        from gui_app import main as run_gui
        print("✅ 의존성 확인 완료, GUI 실행 중...")
        run_gui()
    except ImportError as e:
        error_msg = f"GUI 모듈을 불러올 수 없습니다: {e}\\n\\n"
        error_msg += "gui_app.py 파일이 같은 폴더에 있는지 확인해주세요."
        
        # 콘솔에서 실행된 경우를 위한 에러 출력
        print(f"❌ 오류: {error_msg}")
        
        # GUI 에러 표시
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("GUI 실행 오류", error_msg)
        root.destroy()
    except Exception as e:
        error_msg = f"GUI 실행 중 오류 발생: {e}"
        print(f"❌ 오류: {error_msg}")
        
        # GUI 에러 표시
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("실행 오류", error_msg)
        root.destroy()

if __name__ == "__main__":
    main()