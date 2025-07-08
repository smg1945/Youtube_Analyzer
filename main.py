"""
YouTube 트렌드 분석기 v3.0 - 리팩토링된 메인 실행 파일
새로운 모듈 구조를 사용하는 통합 실행 파일
"""

import sys
import os
import tkinter as tk
from tkinter import messagebox
import traceback

def check_python_version():
    """Python 버전 확인"""
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 이상이 필요합니다.")
        print(f"현재 버전: {sys.version}")
        sys.exit(1)

def check_required_packages():
    """필수 패키지 설치 확인"""
    required_packages = [
        ('pandas', 'pandas'),
        ('requests', 'requests'),
        ('googleapiclient', 'google-api-python-client'),
        ('openpyxl', 'openpyxl'),
        ('PIL', 'Pillow'),
        ('dotenv', 'python-dotenv')
    ]
    
    missing_packages = []
    
    for module_name, package_name in required_packages:
        try:
            __import__(module_name)
        except ImportError:
            missing_packages.append(package_name)
    
    if missing_packages:
        print("❌ 다음 패키지들이 설치되지 않았습니다:")
        for package in missing_packages:
            print(f"   - {package}")
        print("\n다음 명령을 실행하여 설치하세요:")
        print("pip install -r requirements.txt")
        print("\n또는 개별 설치:")
        print(f"pip install {' '.join(missing_packages)}")
        sys.exit(1)

def setup_environment():
    """환경 설정"""
    # 현재 디렉토리를 Python 경로에 추가
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    # 환경변수 로드 시도
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass  # python-dotenv가 없어도 계속 진행

def show_startup_info():
    """시작 정보 표시"""
    print("=" * 60)
    print("🎬 YouTube 트렌드 분석기 v3.0")
    print("=" * 60)
    print("새로운 모듈형 구조로 리팩토링된 버전")
    print()
    print("📁 모듈 구조:")
    print("├── core/          # 핵심 비즈니스 로직")
    print("├── data/          # 데이터 처리 및 분석")
    print("├── exporters/     # 내보내기 기능")
    print("├── gui/           # 사용자 인터페이스")
    print("├── utils/         # 유틸리티 함수")
    print("└── main.py        # 메인 실행 파일")
    print()

def test_module_imports():
    """모듈 import 테스트"""
    modules_to_test = [
        ('core', 'YouTubeClient'),
        ('data', 'create_analysis_suite'),
        ('exporters', 'ExcelExporter'),
        ('gui', 'MainWindow'),
        ('utils', 'format_number')
    ]
    
    failed_imports = []
    
    for module_name, class_or_function in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_or_function])
            getattr(module, class_or_function)
            print(f"✅ {module_name}.{class_or_function}")
        except Exception as e:
            failed_imports.append(f"{module_name}.{class_or_function}: {str(e)}")
            print(f"❌ {module_name}.{class_or_function}: {str(e)}")
    
    if failed_imports:
        print("\n❌ 일부 모듈을 import할 수 없습니다:")
        for failure in failed_imports:
            print(f"   {failure}")
        return False
    
    print("\n✅ 모든 모듈이 정상적으로 로드되었습니다!")
    return True

def create_main_application():
    """메인 애플리케이션 생성"""
    try:
        from gui import MainWindow
        
        # Tkinter 루트 창 생성
        root = tk.Tk()
        root.withdraw()  # 기본 창 숨기기
        
        # 메인 애플리케이션 생성
        app = MainWindow()
        
        return app
        
    except Exception as e:
        print(f"❌ 애플리케이션 생성 실패: {e}")
        traceback.print_exc()
        return None

def handle_global_exception(exc_type, exc_value, exc_traceback):
    """전역 예외 처리"""
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    
    error_msg = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    
    print(f"\n❌ 치명적 오류 발생:")
    print(error_msg)
    
    # GUI가 활성화된 경우 다이얼로그로도 표시
    try:
        messagebox.showerror(
            "치명적 오류", 
            f"예상치 못한 오류가 발생했습니다:\n\n{str(exc_value)}\n\n"
            f"오류 로그를 확인하거나 개발자에게 문의하세요."
        )
    except:
        pass

def run_legacy_mode():
    """레거시 모드 실행 (기존 파일들 사용)"""
    try:
        print("🔄 레거시 모드로 실행 중...")
        
        # 기존 improved_gui.py 사용
        if os.path.exists('improved_gui.py'):
            print("📱 기존 GUI를 사용합니다...")
            import improved_gui
            
            root = tk.Tk()
            app = improved_gui.ImprovedYouTubeAnalyzerGUI(root)
            root.mainloop()
            
        else:
            print("❌ 기존 GUI 파일을 찾을 수 없습니다.")
            print("improved_gui.py 파일이 있는지 확인하세요.")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 레거시 모드 실행 실패: {e}")
        return False

def show_module_selection_dialog():
    """모듈 선택 다이얼로그"""
    root = tk.Tk()
    root.withdraw()
    
    choice = messagebox.askyesnocancel(
        "실행 모드 선택",
        "새로운 모듈형 구조를 사용하시겠습니까?\n\n"
        "예: 새로운 구조 사용 (권장)\n"
        "아니오: 기존 구조 사용\n"
        "취소: 종료"
    )
    
    root.destroy()
    
    return choice

def main():
    """메인 함수"""
    try:
        # 1. 기본 환경 체크
        print("🔍 환경 확인 중...")
        check_python_version()
        setup_environment()
        check_required_packages()
        
        # 2. 시작 정보 표시
        show_startup_info()
        
        # 3. 모듈 import 테스트
        print("📦 모듈 로드 테스트:")
        modules_ok = test_module_imports()
        
        if not modules_ok:
            print("\n⚠️ 일부 모듈에 문제가 있습니다.")
            
            # 사용자에게 선택권 제공
            choice = show_module_selection_dialog()
            
            if choice is None:  # 취소
                print("👋 프로그램을 종료합니다.")
                return
            elif choice is False:  # 기존 구조 사용
                if not run_legacy_mode():
                    print("❌ 실행할 수 있는 모드가 없습니다.")
                    return
                else:
                    return
            # choice가 True면 계속 진행 (새 구조 강제 시도)
        
        # 4. 전역 예외 처리 설정
        sys.excepthook = handle_global_exception
        
        # 5. 메인 애플리케이션 생성 및 실행
        print("\n🚀 애플리케이션 시작 중...")
        
        app = create_main_application()
        
        if app is None:
            print("❌ 애플리케이션을 시작할 수 없습니다.")
            
            # 레거시 모드로 fallback
            print("🔄 레거시 모드로 전환 시도...")
            if not run_legacy_mode():
                print("❌ 모든 실행 방법이 실패했습니다.")
                return
            else:
                return
        
        # 6. GUI 실행
        print("✅ 애플리케이션이 시작되었습니다!")
        print("=" * 60)
        
        # 메인 루프 실행
        app.run()
        
    except KeyboardInterrupt:
        print("\n👋 사용자에 의해 중단되었습니다.")
    
    except Exception as e:
        print(f"\n❌ 실행 중 오류 발생: {e}")
        traceback.print_exc()
        
        # 최후의 방법으로 기본 메시지 출력
        try:
            messagebox.showerror(
                "실행 오류",
                f"프로그램 실행 중 오류가 발생했습니다:\n\n{str(e)}\n\n"
                f"문제가 지속되면 개발자에게 문의하세요."
            )
        except:
            pass
    
    finally:
        print("\n🔚 프로그램을 종료합니다.")

def run_cli_mode():
    """CLI 모드 실행 (GUI 없이)"""
    print("🖥️ CLI 모드로 실행 중...")
    
    try:
        from core import create_analyzer_suite
        from utils import get_cache_manager
        
        # API 키 입력
        api_key = input("YouTube API 키를 입력하세요: ").strip()
        
        if not api_key:
            print("❌ API 키가 필요합니다.")
            return
        
        # 분석 도구 초기화
        analyzer_suite = create_analyzer_suite(api_key)
        
        print("✅ CLI 모드 준비 완료!")
        print("사용 가능한 명령:")
        print("- search <키워드>: 영상 검색")
        print("- trend <지역>: 트렌드 분석")
        print("- quit: 종료")
        
        while True:
            try:
                command = input("\n> ").strip().split()
                
                if not command:
                    continue
                
                if command[0] == 'quit':
                    break
                elif command[0] == 'search' and len(command) > 1:
                    keyword = ' '.join(command[1:])
                    print(f"🔍 '{keyword}' 검색 중...")
                    # 여기에 검색 로직 구현
                elif command[0] == 'trend':
                    region = command[1] if len(command) > 1 else 'KR'
                    print(f"📈 {region} 트렌드 분석 중...")
                    # 여기에 트렌드 분석 로직 구현
                else:
                    print("❓ 알 수 없는 명령입니다.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ 명령 실행 오류: {e}")
        
        print("👋 CLI 모드를 종료합니다.")
        
    except Exception as e:
        print(f"❌ CLI 모드 초기화 실패: {e}")

if __name__ == "__main__":
    # 명령행 인수 확인
    if len(sys.argv) > 1:
        if sys.argv[1] == '--cli':
            run_cli_mode()
        elif sys.argv[1] == '--legacy':
            run_legacy_mode()
        elif sys.argv[1] == '--test':
            check_python_version()
            setup_environment()
            check_required_packages()
            test_module_imports()
        elif sys.argv[1] == '--help':
            print("YouTube 트렌드 분석기 v3.0 사용법:")
            print()
            print("python main.py           # GUI 모드 (기본)")
            print("python main.py --cli     # CLI 모드")
            print("python main.py --legacy  # 레거시 모드")
            print("python main.py --test    # 모듈 테스트")
            print("python main.py --help    # 도움말")
        else:
            print(f"❓ 알 수 없는 옵션: {sys.argv[1]}")
            print("--help 옵션을 사용하여 사용법을 확인하세요.")
    else:
        # 기본 GUI 모드
        main()