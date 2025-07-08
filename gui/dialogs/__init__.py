"""
gui/dialogs/__init__.py
다이얼로그 모듈의 진입점
"""

from .progress_dialog import ProgressDialog
from .settings_dialog import SettingsDialog
from .video_details_dialog import VideoDetailsDialog

__version__ = "3.0.0"
__all__ = [
    'ProgressDialog',
    'SettingsDialog', 
    'VideoDetailsDialog'
]

# 편의 함수들
def show_progress_dialog(parent, title="진행 중...", cancel_callback=None):
    """
    진행률 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        title (str): 다이얼로그 제목
        cancel_callback: 취소 콜백 함수
        
    Returns:
        ProgressDialog: 진행률 다이얼로그 인스턴스
    """
    return ProgressDialog(parent, title, cancel_callback)

def show_settings_dialog(parent, current_settings=None):
    """
    설정 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        current_settings (dict): 현재 설정값
        
    Returns:
        dict: 새로운 설정값 또는 None (취소시)
    """
    dialog = SettingsDialog(parent, current_settings)
    dialog.show()
    return dialog.get_result()

def show_video_details_dialog(parent, video_data):
    """
    영상 상세 정보 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        video_data (dict): 영상 데이터
        
    Returns:
        VideoDetailsDialog: 상세 정보 다이얼로그 인스턴스
    """
    return VideoDetailsDialog(parent, video_data)