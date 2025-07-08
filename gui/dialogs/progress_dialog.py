"""
진행률 다이얼로그 모듈
작업 진행률을 표시하는 모달 다이얼로그
"""

import tkinter as tk
from tkinter import ttk

class ProgressDialog:
    """진행률 다이얼로그 클래스"""
    
    def __init__(self, parent, title="진행 중...", cancel_callback=None):
        """
        진행률 다이얼로그 초기화
        
        Args:
            parent: 부모 위젯
            title (str): 다이얼로그 제목
            cancel_callback: 취소 버튼 콜백 함수
        """
        self.parent = parent
        self.cancel_callback = cancel_callback
        self.is_cancelled = False
        
        # 다이얼로그 창 생성
        self.dialog = tk.Toplevel(parent)
        self.dialog.title(title)
        self.dialog.geometry("400x150")
        self.dialog.configure(bg='#f5f5f7')
        self.dialog.resizable(False, False)
        
        # 모달 설정
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # 중앙 정렬
        self.center_dialog()
        
        # 닫기 버튼 비활성화
        self.dialog.protocol("WM_DELETE_WINDOW", self.on_cancel)
        
        self.create_widgets()
        
    def center_dialog(self):
        """다이얼로그를 부모 창 중앙에 배치"""
        self.dialog.update_idletasks()
        
        parent_x = self.parent.winfo_rootx()
        parent_y = self.parent.winfo_rooty()
        parent_width = self.parent.winfo_width()
        parent_height = self.parent.winfo_height()
        
        dialog_width = 400
        dialog_height = 150
        
        x = parent_x + (parent_width - dialog_width) // 2
        y = parent_y + (parent_height - dialog_height) // 2
        
        self.dialog.geometry(f"{dialog_width}x{dialog_height}+{x}+{y}")
    
    def create_widgets(self):
        """위젯 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.dialog, bg='#f5f5f7')
        main_frame.pack(fill='both', expand=True, padx=20, pady=20)
        
        # 상태 메시지
        self.status_label = tk.Label(
            main_frame,
            text="작업을 시작합니다...",
            font=('SF Pro Display', 12),
            bg='#f5f5f7',
            fg='#1d1d1f'
        )
        self.status_label.pack(pady=(0, 15))
        
        # 진행률 바
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            main_frame,
            variable=self.progress_var,
            maximum=100,
            length=350,
            mode='determinate'
        )
        self.progress_bar.pack(pady=(0, 10))
        
        # 퍼센트 라벨
        self.percent_label = tk.Label(
            main_frame,
            text="0%",
            font=('SF Pro Display', 10),
            bg='#f5f5f7',
            fg='#86868b'
        )
        self.percent_label.pack(pady=(0, 15))
        
        # 버튼 영역
        button_frame = tk.Frame(main_frame, bg='#f5f5f7')
        button_frame.pack()
        
        # 취소 버튼 (콜백이 있는 경우만)
        if self.cancel_callback:
            self.cancel_button = tk.Button(
                button_frame,
                text="취소",
                font=('SF Pro Display', 11),
                bg='#ff3b30',
                fg='white',
                width=10,
                borderwidth=0,
                cursor='hand2',
                command=self.on_cancel
            )
            self.cancel_button.pack()
    
    def update_progress(self, value, message=None):
        """
        진행률 업데이트
        
        Args:
            value (float): 진행률 (0-100)
            message (str): 상태 메시지 (선택사항)
        """
        if self.dialog.winfo_exists():
            self.progress_var.set(value)
            self.percent_label.config(text=f"{value:.1f}%")
            
            if message:
                self.status_label.config(text=message)
            
            self.dialog.update_idletasks()
    
    def set_indeterminate(self, message="처리 중..."):
        """
        무한 진행률 모드로 설정
        
        Args:
            message (str): 상태 메시지
        """
        if self.dialog.winfo_exists():
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            self.status_label.config(text=message)
            self.percent_label.config(text="")
    
    def set_determinate(self):
        """결정적 진행률 모드로 설정"""
        if self.dialog.winfo_exists():
            self.progress_bar.stop()
            self.progress_bar.config(mode='determinate')
    
    def on_cancel(self):
        """취소 버튼 클릭 시"""
        if self.cancel_callback:
            self.is_cancelled = True
            self.cancel_callback()
    
    def close(self):
        """다이얼로그 닫기"""
        if self.dialog.winfo_exists():
            self.dialog.grab_release()
            self.dialog.destroy()
    
    def is_open(self):
        """다이얼로그가 열려있는지 확인"""
        return self.dialog.winfo_exists()
    
    def set_title(self, title):
        """제목 변경"""
        if self.dialog.winfo_exists():
            self.dialog.title(title)
    
    def disable_cancel(self):
        """취소 버튼 비활성화"""
        if hasattr(self, 'cancel_button') and self.dialog.winfo_exists():
            self.cancel_button.config(state='disabled')
    
    def enable_cancel(self):
        """취소 버튼 활성화"""
        if hasattr(self, 'cancel_button') and self.dialog.winfo_exists():
            self.cancel_button.config(state='normal')


class MultiStepProgressDialog(ProgressDialog):
    """다단계 진행률 다이얼로그"""
    
    def __init__(self, parent, title="진행 중...", steps=None, cancel_callback=None):
        """
        다단계 진행률 다이얼로그 초기화
        
        Args:
            parent: 부모 위젯
            title (str): 다이얼로그 제목
            steps (list): 단계 목록
            cancel_callback: 취소 콜백
        """
        self.steps = steps or []
        self.current_step = 0
        self.step_progress = 0
        
        super().__init__(parent, title, cancel_callback)
        
        if self.steps:
            self.create_step_widgets()
    
    def create_step_widgets(self):
        """단계 표시 위젯 추가"""
        # 다이얼로그 크기 조정
        self.dialog.geometry("450x200")
        
        # 단계 정보 프레임 추가
        step_frame = tk.Frame(self.dialog, bg='#f5f5f7')
        step_frame.pack(fill='x', padx=20, pady=(10, 0))
        
        # 현재 단계 라벨
        self.step_label = tk.Label(
            step_frame,
            text=f"단계 1/{len(self.steps)}: {self.steps[0] if self.steps else ''}",
            font=('SF Pro Display', 10, 'bold'),
            bg='#f5f5f7',
            fg='#007aff'
        )
        self.step_label.pack()
        
        # 전체 진행률 바 (단계별)
        self.overall_progress_var = tk.DoubleVar()
        self.overall_progress_bar = ttk.Progressbar(
            step_frame,
            variable=self.overall_progress_var,
            maximum=len(self.steps),
            length=350,
            mode='determinate'
        )
        self.overall_progress_bar.pack(pady=(5, 0))
    
    def next_step(self, step_name=None):
        """다음 단계로 진행"""
        self.current_step += 1
        self.step_progress = 0
        
        if self.current_step <= len(self.steps):
            current_step_name = step_name or (self.steps[self.current_step - 1] if self.current_step <= len(self.steps) else "완료")
            
            self.step_label.config(text=f"단계 {self.current_step}/{len(self.steps)}: {current_step_name}")
            self.overall_progress_var.set(self.current_step - 1)
            
            self.update_progress(0, f"{current_step_name} 시작...")
    
    def update_step_progress(self, value, message=None):
        """현재 단계의 진행률 업데이트"""
        self.step_progress = value
        
        # 전체 진행률 계산
        overall_progress = ((self.current_step - 1) / len(self.steps)) * 100 + (value / len(self.steps))
        
        self.update_progress(value, message)
        
        if hasattr(self, 'overall_progress_var'):
            step_completion = (self.current_step - 1) + (value / 100)
            self.overall_progress_var.set(step_completion)
    
    def complete_step(self):
        """현재 단계 완료"""
        self.update_step_progress(100, f"{self.steps[self.current_step - 1] if self.current_step <= len(self.steps) else ''} 완료")
        
        if hasattr(self, 'overall_progress_var'):
            self.overall_progress_var.set(self.current_step)
    
    def complete_all(self, message="모든 작업이 완료되었습니다."):
        """모든 작업 완료 처리"""
        try:
            # 현재 단계 완료
            if self.current_step <= len(self.steps):
                self.complete_step()
            
            # 최종 진행률 100%로 설정
            self.update_progress(100, message)
            
            # 전체 진행률도 최대값으로 설정
            if hasattr(self, 'overall_progress_var'):
                self.overall_progress_var.set(len(self.steps))
            
            # 단계 라벨 업데이트
            self.step_label.config(text=f"완료! ({len(self.steps)}/{len(self.steps)})")
            
            # 성공 메시지와 함께 완료 표시
            self.message_label.config(text=message, fg='#34c759')  # 초록색
            
            # 취소 버튼을 닫기 버튼으로 변경
            self.cancel_btn.config(text="닫기")
            
            # 완료 효과음 (선택사항)
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_OK)
            except ImportError:
                # Windows가 아닌 경우 또는 winsound가 없는 경우 무시
                pass
            
            # 완료 시간 기록
            self.end_time = time.time()
            total_time = self.end_time - self.start_time
            
            # 시간 정보 표시
            time_message = f"총 소요시간: {total_time:.1f}초"
            
            # 기존 메시지에 시간 정보 추가
            final_message = f"{message}\n{time_message}"
            self.message_label.config(text=final_message)
            
            print(f"✅ 모든 작업 완료: {message}")
            print(f"⏱️ {time_message}")
            
            # 완료 콜백 호출 (있는 경우)
            if hasattr(self, 'completion_callback') and self.completion_callback:
                try:
                    self.completion_callback(True, final_message)
                except Exception as e:
                    print(f"완료 콜백 오류: {e}")
            
            # 자동 닫기 옵션 (설정된 경우)
            if hasattr(self, 'auto_close_delay') and self.auto_close_delay > 0:
                self.root.after(self.auto_close_delay * 1000, self.close_dialog)
            
        except Exception as e:
            print(f"완료 처리 오류: {e}")
            # 오류가 발생해도 기본적인 완료 처리는 수행
            self.update_progress(100, "작업 완료 (일부 오류 발생)")
            if hasattr(self, 'overall_progress_var'):
                self.overall_progress_var.set(len(self.steps))

    def set_completion_callback(self, callback):
        """완료 시 호출할 콜백 함수 설정"""
        self.completion_callback = callback

    def set_auto_close(self, delay_seconds):
        """완료 후 자동 닫기 설정 (초 단위)"""
        self.auto_close_delay = delay_seconds

    def close_dialog(self):
        """다이얼로그 닫기"""
        try:
            if self.root and self.root.winfo_exists():
                self.root.destroy()
        except Exception as e:
            print(f"다이얼로그 닫기 오류: {e}")

    def abort_with_error(self, error_message):
        """오류로 인한 작업 중단"""
        try:
            # 오류 메시지 표시
            self.message_label.config(text=f"❌ 오류: {error_message}", fg='#ff3b30')  # 빨간색
            
            # 진행률 바를 빨간색으로 변경 (가능한 경우)
            try:
                style = ttk.Style()
                style.configure("Error.Horizontal.TProgressbar", background='#ff3b30')
                self.progress_bar.configure(style="Error.Horizontal.TProgressbar")
            except:
                pass
            
            # 취소 버튼을 닫기 버튼으로 변경
            self.cancel_btn.config(text="닫기")
            
            # 오류 효과음
            try:
                import winsound
                winsound.MessageBeep(winsound.MB_ICONERROR)
            except ImportError:
                pass
            
            print(f"❌ 작업 중단: {error_message}")
            
            # 오류 콜백 호출 (있는 경우)
            if hasattr(self, 'completion_callback') and self.completion_callback:
                try:
                    self.completion_callback(False, error_message)
                except Exception as e:
                    print(f"오류 콜백 호출 실패: {e}")
                    
        except Exception as e:
            print(f"오류 처리 중 오류 발생: {e}")


# 편의 함수들
def show_simple_progress(parent, title="처리 중...", message="잠시만 기다려주세요..."):
    """
    간단한 진행률 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        title (str): 제목
        message (str): 메시지
        
    Returns:
        ProgressDialog: 다이얼로그 인스턴스
    """
    dialog = ProgressDialog(parent, title)
    dialog.set_indeterminate(message)
    return dialog

def show_cancellable_progress(parent, title="처리 중...", cancel_callback=None):
    """
    취소 가능한 진행률 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        title (str): 제목
        cancel_callback: 취소 콜백
        
    Returns:
        ProgressDialog: 다이얼로그 인스턴스
    """
    return ProgressDialog(parent, title, cancel_callback)

def show_multi_step_progress(parent, title="처리 중...", steps=None, cancel_callback=None):
    """
    다단계 진행률 다이얼로그 표시
    
    Args:
        parent: 부모 위젯
        title (str): 제목
        steps (list): 단계 목록
        cancel_callback: 취소 콜백
        
    Returns:
        MultiStepProgressDialog: 다이얼로그 인스턴스
    """
    return MultiStepProgressDialog(parent, title, steps, cancel_callback)