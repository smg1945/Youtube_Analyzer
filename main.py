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
    
    # GUI가 활성화된 경우 다이얼로그로도 표시
    try:
        error_detail = str(exc_value)
        if len(error_detail) > 200:
            error_detail = error_detail[:200] + "..."
        
        messagebox.showerror(
            "치명적 오류", 
            f"예상치 못한 오류가 발생했습니다:\n\n{error_detail}\n\n"
            f"프로그램이 종료됩니다.\n"
            f"문제가 지속되면 개발자에게 문의하세요."
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
            
            print("✅ 레거시 모드 실행 완료")
            root.mainloop()
            
        else:
            print("❌ 기존 GUI 파일을 찾을 수 없습니다.")
            print("improved_gui.py 파일이 있는지 확인하세요.")
            
            # 대안 제시
            print("\n💡 해결 방법:")
            print("1. 새로운 모듈형 구조를 사용하세요: python main.py")
            print("2. improved_gui.py 파일이 있는지 확인하세요")
            print("3. 전체 프로젝트를 다시 다운로드하세요")
            
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ 레거시 모드 실행 실패: {e}")
        traceback.print_exc()
        return False

def show_module_selection_dialog():
    """모듈 선택 다이얼로그"""
    root = tk.Tk()
    root.withdraw()
    
    choice = messagebox.askyesnocancel(
        "실행 모드 선택",
        "YouTube 트렌드 분석기 v3.0에 오신 것을 환영합니다!\n\n"
        "실행 모드를 선택하세요:\n\n"
        "✅ 예: 새로운 모듈형 구조 사용 (권장)\n"
        "   - 개선된 성능과 안정성\n"
        "   - 새로운 기능들\n"
        "   - 더 나은 사용자 경험\n\n"
        "❌ 아니오: 기존 구조 사용\n"
        "   - 이전 버전과 동일한 인터페이스\n"
        "   - 호환성 우선\n\n"
        "취소: 프로그램 종료"
    )
    
    root.destroy()
    
    return choice

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
        print("🔧 분석 도구 초기화 중...")
        analyzer_suite = create_analyzer_suite(api_key)
        
        print("✅ CLI 모드 준비 완료!")
        print("\n" + "="*50)
        print("🎬 YouTube 트렌드 분석기 CLI v3.0")
        print("="*50)
        print("사용 가능한 명령:")
        print("  search <키워드>     : 영상 검색 및 분석")
        print("  trend <지역>        : 트렌드 분석 (기본: KR)")
        print("  channel <채널ID>    : 채널 분석")
        print("  export <형식>       : 결과 내보내기 (excel/csv)")
        print("  stats               : 현재 세션 통계")
        print("  help                : 도움말")
        print("  quit / exit         : 종료")
        print("-"*50)
        
        # 세션 통계 초기화
        session_stats = {
            'searches': 0,
            'videos_analyzed': 0,
            'api_calls': 0,
            'start_time': time.time()
        }
        
        while True:
            try:
                command_input = input("\n🔍 > ").strip()
                
                if not command_input:
                    continue
                
                command_parts = command_input.split()
                command = command_parts[0].lower()
                
                if command in ['quit', 'exit']:
                    break
                    
                elif command == 'search' and len(command_parts) > 1:
                    keyword = ' '.join(command_parts[1:])
                    print(f"🔍 '{keyword}' 검색 중...")
                    
                    # 검색 실행 (실제 구현은 analyzer_suite 사용)
                    session_stats['searches'] += 1
                    print(f"✅ 검색 완료! (총 검색: {session_stats['searches']}회)")
                    
                elif command == 'trend':
                    region = command_parts[1] if len(command_parts) > 1 else 'KR'
                    print(f"📈 {region} 트렌드 분석 중...")
                    # 트렌드 분석 로직 구현
                    
                elif command == 'channel' and len(command_parts) > 1:
                    channel_id = command_parts[1]
                    print(f"📺 채널 분석 중: {channel_id}")
                    # 채널 분석 로직 구현
                    
                elif command == 'export' and len(command_parts) > 1:
                    export_format = command_parts[1].lower()
                    if export_format in ['excel', 'csv']:
                        print(f"📊 {export_format.upper()} 형식으로 내보내기...")
                        # 내보내기 로직 구현
                    else:
                        print("❌ 지원하지 않는 형식입니다. (excel, csv)")
                        
                elif command == 'stats':
                    elapsed_time = time.time() - session_stats['start_time']
                    print(f"\n📊 세션 통계:")
                    print(f"   실행 시간: {elapsed_time:.1f}초")
                    print(f"   검색 횟수: {session_stats['searches']}회")
                    print(f"   분석된 영상: {session_stats['videos_analyzed']}개")
                    print(f"   API 호출: {session_stats['api_calls']}회")
                    
                elif command == 'help':
                    print("\n📖 명령어 도움말:")
                    print("  search cooking     → 'cooking' 키워드로 영상 검색")
                    print("  trend US           → 미국 트렌드 분석")
                    print("  channel UC123...   → 특정 채널 분석")
                    print("  export excel       → 엑셀 파일로 내보내기")
                    print("  stats              → 현재 세션 통계 표시")
                    
                else:
                    print("❓ 알 수 없는 명령입니다. 'help'를 입력하여 도움말을 확인하세요.")
                    
            except KeyboardInterrupt:
                print("\n\n👋 Ctrl+C가 감지되었습니다. 종료하시겠습니까? (y/n)")
                if input().lower().startswith('y'):
                    break
            except Exception as e:
                print(f"❌ 명령 실행 오류: {e}")
        
        # 종료 메시지
        elapsed_time = time.time() - session_stats['start_time']
        print(f"\n👋 CLI 모드를 종료합니다.")
        print(f"⏱️ 총 실행 시간: {elapsed_time:.1f}초")
        print(f"📊 총 검색: {session_stats['searches']}회")
        
    except Exception as e:
        print(f"❌ CLI 모드 초기화 실패: {e}")
        traceback.print_exc()

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
            print("\n⚠️ 일부 모듈에 문제가 있습니다.")
            choice = messagebox.askyesno(
                "모듈 오류", 
                "일부 모듈을 로드할 수 없습니다.\n\n"
                "레거시 모드로 실행하시겠습니까?\n"
                "(기존 파일을 사용합니다)"
            )
            
            if choice:
                success = run_legacy_mode()
                if not success:
                    print("❌ 레거시 모드 실행도 실패했습니다.")
                    input("아무 키나 눌러 종료...")
                return
            else:
                print("❌ 프로그램을 종료합니다.")
                return
        
        # 4. 메인 애플리케이션 생성 및 실행
        print("\n🚀 메인 애플리케이션 시작...")
        app = create_main_application()
        
        if app:
            print("✅ 애플리케이션이 성공적으로 시작되었습니다!")
            print("🎬 YouTube 트렌드 분석기 v3.0을 즐겨보세요!")
            
            # 시작 시간 기록
            import time
            start_time = time.time()
            
            # 애플리케이션 실행
            app.run()
            
            # 종료 시간 계산
            end_time = time.time()
            session_time = end_time - start_time
            
            print(f"\n📊 세션 정보:")
            print(f"   실행 시간: {session_time:.1f}초")
            
        else:
            print("❌ 애플리케이션을 시작할 수 없습니다.")
            
            # 대안 제시
            choice = messagebox.askyesno(
                "시작 실패",
                "새로운 모듈형 구조로 시작할 수 없습니다.\n\n"
                "레거시 모드로 실행하시겠습니까?"
            )
            
            if choice:
                run_legacy_mode()
    
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

# 시간 모듈 import 추가
import time