"""
YouTube 트렌드 분석기 v3.0 - 수정된 메인 실행 파일
utils.formatters 문제 해결 버전
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
    optional_warnings = []
    
    for module_name, class_or_function in modules_to_test:
        try:
            module = __import__(module_name, fromlist=[class_or_function])
            getattr(module, class_or_function)
            print(f"✅ {module_name}.{class_or_function}")
        except Exception as e:
            error_msg = str(e).lower()
            
            # 선택적 의존성인지 확인
            if any(opt in error_msg for opt in ['vader', 'whisper', 'sentiment']):
                optional_warnings.append(f"{module_name}.{class_or_function}: {str(e)}")
                print(f"⚠️ {module_name}.{class_or_function}: {str(e)} (선택사항)")
            else:
                failed_imports.append(f"{module_name}.{class_or_function}: {str(e)}")
                print(f"❌ {module_name}.{class_or_function}: {str(e)}")
    
    # 선택적 의존성 경고 표시
    if optional_warnings:
        print("\n⚠️ 선택적 기능들:")
        for warning in optional_warnings:
            print(f"   {warning}")
        print("\n   추가 설치로 더 많은 기능을 사용할 수 있습니다:")
        print("   pip install vaderSentiment openai-whisper")
    
    # 필수 모듈 실패 확인
    if failed_imports:
        print("\n❌ 필수 모듈을 import할 수 없습니다:")
        for failure in failed_imports:
            print(f"   {failure}")
        return False
    
    print("\n✅ 모든 필수 모듈이 정상적으로 로드되었습니다!")
    return True

def create_main_application():
    """메인 애플리케이션 생성"""
    try:
        from gui import MainWindow
        
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
    
    # 오류 로그 파일에 저장
    try:
        import os
        from datetime import datetime
        
        # logs 디렉토리 생성
        os.makedirs('logs', exist_ok=True)
        
        # 오류 로그 파일명 생성
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_filename = f"logs/error_{timestamp}.log"
        
        # 오류 정보 작성
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(f"YouTube 트렌드 분석기 v3.0 - 오류 리포트\n")
            f.write(f"발생 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Python 버전: {sys.version}\n")
            f.write(f"플랫폼: {sys.platform}\n")
            f.write("-" * 50 + "\n")
            f.write(error_msg)
        
        print(f"📝 오류 로그가 저장되었습니다: {log_filename}")
        
    except Exception as log_error:
        print(f"오류 로그 저장 실패: {log_error}")

def main():
    """메인 함수"""
    try:
        # 전역 예외 처리기 설정
        sys.excepthook = handle_global_exception
        
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
            print("\n⚠️ 일부 필수 모듈에 문제가 있습니다.")
            print("다음을 확인해주세요:")
            print("1. utils/formatters.py 파일이 있는지 확인")
            print("2. 모든 필수 패키지가 설치되었는지 확인")
            print("3. 프로젝트 구조가 올바른지 확인")
            
            input("문제를 해결한 후 아무 키나 눌러 종료...")
            return
        
        # 4. 메인 애플리케이션 생성 및 실행
        print("\n🚀 메인 애플리케이션 시작...")
        app = create_main_application()
        
        if app:
            print("✅ 애플리케이션이 성공적으로 시작되었습니다!")
            print("🎬 YouTube 트렌드 분석기 v3.0을 즐겨보세요!")
            
            # 애플리케이션 실행
            app.run()
            
        else:
            print("❌ 애플리케이션을 시작할 수 없습니다.")
            print("자세한 오류 정보는 위의 에러 메시지를 확인하세요.")
    
    except KeyboardInterrupt:
        print("\n👋 사용자가 프로그램을 중단했습니다.")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류가 발생했습니다: {e}")
        traceback.print_exc()
        try:
            messagebox.showerror("오류", f"프로그램 실행 중 오류가 발생했습니다:\n{str(e)}")
        except:
            pass
    
    finally:
        print("\n🔚 프로그램을 종료합니다.")
        input("아무 키나 눌러 종료...")

if __name__ == "__main__":
    main()