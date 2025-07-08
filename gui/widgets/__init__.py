"""
gui/widgets/__init__.py
커스텀 위젯 모듈의 진입점
"""

from .video_tree import VideoTreeWidget
from .filter_panel import FilterPanel

__version__ = "3.0.0"
__all__ = [
    'VideoTreeWidget',
    'FilterPanel'
]

# 편의 함수들
def create_video_tree_with_filters(parent, on_video_select=None, on_video_double_click=None):
    """
    필터 패널과 함께 영상 트리 위젯 생성
    
    Args:
        parent: 부모 위젯
        on_video_select: 영상 선택 시 콜백
        on_video_double_click: 영상 더블클릭 시 콜백
        
    Returns:
        dict: {'tree': VideoTreeWidget, 'filter': FilterPanel}
    """
    import tkinter as tk
    
    # 컨테이너 프레임
    container = tk.Frame(parent, bg='#f5f5f7')
    container.pack(fill='both', expand=True)
    
    # 필터 패널
    filter_panel = FilterPanel(container)
    filter_panel.pack(fill='x', padx=10, pady=(10, 5))
    
    # 영상 트리
    video_tree = VideoTreeWidget(
        container, 
        on_select=on_video_select,
        on_double_click=on_video_double_click
    )
    video_tree.pack(fill='both', expand=True, padx=10, pady=(5, 10))
    
    # 필터와 트리 연결
    filter_panel.set_filter_callback(video_tree.apply_filters)
    
    return {
        'container': container,
        'tree': video_tree,
        'filter': filter_panel
    }

def create_simple_video_tree(parent, show_thumbnails=False):
    """
    간단한 영상 트리 위젯 생성
    
    Args:
        parent: 부모 위젯
        show_thumbnails (bool): 썸네일 표시 여부
        
    Returns:
        VideoTreeWidget: 영상 트리 위젯
    """
    return VideoTreeWidget(parent, show_thumbnails=show_thumbnails)

def create_advanced_filter_panel(parent, filter_options=None):
    """
    고급 필터 패널 생성
    
    Args:
        parent: 부모 위젯
        filter_options (dict): 필터 옵션 설정
        
    Returns:
        FilterPanel: 필터 패널
    """
    if filter_options is None:
        filter_options = {
            'show_video_type_filter': True,
            'show_outlier_filter': True,
            'show_date_filter': True,
            'show_view_filter': True,
            'show_engagement_filter': True
        }
    
    return FilterPanel(parent, **filter_options)