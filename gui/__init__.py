"""
gui/__init__.py
GUI 모듈의 진입점
"""

from .main_window import MainWindow
from .search_tab import SearchTab
from .results_viewer import ResultsViewer

__version__ = "3.0.0"
__all__ = [
    'MainWindow',
    'SearchTab', 
    'ResultsViewer'
]

# 편의 함수들
def create_main_application():
    """
    메인 애플리케이션 생성
    
    Returns:
        MainWindow: 메인 창 인스턴스
    """
    return MainWindow()

def launch_search_interface(parent=None):
    """
    검색 인터페이스만 실행
    
    Args:
        parent: 부모 위젯 (선택사항)
        
    Returns:
        SearchTab: 검색 탭 인스턴스
    """
    import tkinter as tk
    
    if parent is None:
        root = tk.Tk()
        root.title("YouTube 영상 검색")
        root.geometry("1000x700")
        parent = root
    
    return SearchTab(parent)

def launch_results_viewer(videos_data, parent=None):
    """
    결과 뷰어만 실행
    
    Args:
        videos_data (list): 영상 데이터 목록
        parent: 부모 위젯 (선택사항)
        
    Returns:
        ResultsViewer: 결과 뷰어 인스턴스
    """
    import tkinter as tk
    
    if parent is None:
        root = tk.Toplevel()
        root.title("검색 결과")
        root.geometry("1200x800")
        parent = root
    
    viewer = ResultsViewer(parent)
    viewer.display_results(videos_data)
    return viewer