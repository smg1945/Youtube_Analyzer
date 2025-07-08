"""
error_handler.py
에러 처리 및 로깅 시스템
"""

import os
import sys
import logging
import traceback
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any


class ErrorHandler:
    """에러 처리 클래스"""
    
    def __init__(self, log_dir="logs", log_level=logging.INFO):
        """
        에러 핸들러 초기화
        
        Args:
            log_dir (str): 로그 디렉토리 경로
            log_level: 로그 레벨
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.log_level = log_level
        self.logger = None
        
        # 에러 통계
        self.error_stats = {
            'total_errors': 0,
            'api_errors': 0,
            'validation_errors': 0,
            'file_errors': 0,
            'network_errors': 0,
            'unknown_errors': 0
        }
        
        self.setup_logging()
        print(f"📝 에러 핸들러 초기화: {self.log_dir}")
    
    def setup_logging(self, log_file: Optional[str] = None, log_level: Optional[int] = None):
        """로깅 시스템 설정"""
        if log_level:
            self.log_level = log_level
        
        # 로거 설정
        self.logger = logging.getLogger('youtube_analyzer')
        self.logger.setLevel(self.log_level)
        
        # 기존 핸들러 제거
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # 파일 핸들러
        if not log_file:
            timestamp = datetime.now().strftime("%Y%m%d")
            log_file = f"app_{timestamp}.log"
        
        log_path = self.log_dir / log_file
        
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
        file_handler.setLevel(self.log_level)
        
        # 콘솔 핸들러
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.WARNING)
        
        # 포맷터
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.logger.info("로깅 시스템 초기화 완료")
    
    def log_error(self, error: Exception, context: Optional[Dict[str, Any]] = None):
        """에러 로깅"""
        self.error_stats['total_errors'] += 1
        
        # 에러 타입 분류
        error_type = self._classify_error(error)
        self.error_stats[f'{error_type}_errors'] += 1
        
        # 에러 정보 수집
        error_info = {
            'timestamp': datetime.now().isoformat(),
            'error_type': error_type,
            'error_class': error.__class__.__name__,
            'error_message': str(error),
            'traceback': traceback.format_exc(),
            'context': context or {}
        }
        
        # 로그 기록
        self.logger.error(f"[{error_type.upper()}] {error.__class__.__name__}: {str(error)}")
        
        if context:
            self.logger.error(f"Context: {json.dumps(context, ensure_ascii=False, indent=2)}")
        
        # 에러 파일 저장 (중요한 에러의 경우)
        if error_type in ['api', 'file']:
            self._save_error_details(error_info)
        
        return error_info
    
    def _classify_error(self, error: Exception) -> str:
        """에러 타입 분류"""
        error_class = error.__class__.__name__
        error_msg = str(error).lower()
        
        # API 에러
        if any(keyword in error_class.lower() for keyword in ['http', 'api', 'quota', 'auth']):
            return 'api'
        if any(keyword in error_msg for keyword in ['quota', 'api key', 'unauthorized', 'forbidden']):
            return 'api'
        
        # 네트워크 에러
        if any(keyword in error_class.lower() for keyword in ['connection', 'timeout', 'network', 'ssl']):
            return 'network'
        if any(keyword in error_msg for keyword in ['connection', 'timeout', 'network', 'ssl']):
            return 'network'
        
        # 파일 에러
        if any(keyword in error_class.lower() for keyword in ['file', 'permission', 'io']):
            return 'file'
        if any(keyword in error_msg for keyword in ['file', 'directory', 'permission', 'not found']):
            return 'file'
        
        # 검증 에러
        if any(keyword in error_class.lower() for keyword in ['value', 'type', 'validation']):
            return 'validation'
        if any(keyword in error_msg for keyword in ['invalid', 'required', 'missing', 'wrong']):
            return 'validation'
        
        return 'unknown'
    
    def _save_error_details(self, error_info: Dict[str, Any]):
        """에러 상세 정보를 파일에 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            error_file = self.log_dir / f"error_detail_{timestamp}.json"
            
            with open(error_file, 'w', encoding='utf-8') as f:
                json.dump(error_info, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.logger.error(f"에러 상세 정보 저장 실패: {e}")
    
    def handle_api_error(self, error: Exception) -> str:
        """API 에러 처리 및 사용자 친화적 메시지 반환"""
        self.log_error(error, {'error_source': 'youtube_api'})
        
        error_msg = str(error).lower()
        
        # YouTube API 에러별 처리
        if 'quotaexceeded' in error_msg:
            return "API 할당량이 초과되었습니다. 내일 다시 시도하세요."
        elif 'keyinvalid' in error_msg or 'invalid api key' in error_msg:
            return "API 키가 유효하지 않습니다. 설정에서 올바른 키를 입력하세요."
        elif 'keymissing' in error_msg:
            return "API 키가 설정되지 않았습니다. 설정에서 API 키를 입력하세요."
        elif 'forbidden' in error_msg:
            return "API 액세스가 거부되었습니다. 키 권한을 확인하세요."
        elif 'not found' in error_msg:
            return "요청한 리소스를 찾을 수 없습니다."
        elif 'rate limit' in error_msg or 'too many requests' in error_msg:
            return "요청이 너무 많습니다. 잠시 후 다시 시도하세요."
        elif 'timeout' in error_msg:
            return "요청 시간이 초과되었습니다. 네트워크 연결을 확인하세요."
        elif 'connection' in error_msg:
            return "네트워크 연결에 문제가 있습니다. 인터넷 연결을 확인하세요."
        else:
            return f"API 오류가 발생했습니다: {str(error)}"
    
    def handle_file_error(self, error: Exception, file_path: str = "") -> str:
        """파일 에러 처리"""
        self.log_error(error, {'error_source': 'file_operation', 'file_path': file_path})
        
        error_msg = str(error).lower()
        
        if 'permission' in error_msg:
            return f"파일 접근 권한이 없습니다: {file_path}"
        elif 'not found' in error_msg:
            return f"파일을 찾을 수 없습니다: {file_path}"
        elif 'exists' in error_msg:
            return f"파일이 이미 존재합니다: {file_path}"
        elif 'space' in error_msg or 'disk' in error_msg:
            return "디스크 공간이 부족합니다."
        else:
            return f"파일 처리 중 오류가 발생했습니다: {str(error)}"
    
    def handle_validation_error(self, error: Exception, field_name: str = "") -> str:
        """검증 에러 처리"""
        self.log_error(error, {'error_source': 'validation', 'field': field_name})
        
        error_msg = str(error)
        
        if field_name:
            return f"{field_name} 입력값이 올바르지 않습니다: {error_msg}"
        else:
            return f"입력값 검증 오류: {error_msg}"
    
    def get_error_stats(self) -> Dict[str, Any]:
        """에러 통계 반환"""
        total = self.error_stats['total_errors']
        
        stats = self.error_stats.copy()
        
        # 비율 계산
        if total > 0:
            for key in stats:
                if key.endswith('_errors') and key != 'total_errors':
                    stats[f'{key}_rate'] = round(stats[key] / total * 100, 2)
        
        return stats
    
    def clear_error_stats(self):
        """에러 통계 초기화"""
        for key in self.error_stats:
            self.error_stats[key] = 0
        
        self.logger.info("에러 통계가 초기화되었습니다.")
    
    def get_recent_errors(self, count: int = 10) -> list:
        """최근 에러 로그 반환"""
        try:
            # 가장 최근 로그 파일 찾기
            log_files = list(self.log_dir.glob("app_*.log"))
            if not log_files:
                return []
            
            latest_log = max(log_files, key=lambda x: x.stat().st_mtime)
            
            errors = []
            with open(latest_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # ERROR 레벨 로그만 추출
            for line in reversed(lines):
                if ' - ERROR - ' in line:
                    errors.append(line.strip())
                    if len(errors) >= count:
                        break
            
            return errors
            
        except Exception as e:
            self.logger.error(f"최근 에러 로그 조회 실패: {e}")
            return []
    
    def export_error_report(self, output_file: Optional[str] = None) -> str:
        """에러 리포트 내보내기"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"error_report_{timestamp}.json"
        
        output_path = self.log_dir / output_file
        
        try:
            report = {
                'generated_at': datetime.now().isoformat(),
                'statistics': self.get_error_stats(),
                'recent_errors': self.get_recent_errors(50),
                'system_info': self._get_system_info()
            }
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"에러 리포트 생성됨: {output_path}")
            return str(output_path)
            
        except Exception as e:
            self.logger.error(f"에러 리포트 생성 실패: {e}")
            raise
    
    def _get_system_info(self) -> Dict[str, str]:
        """시스템 정보 수집"""
        import platform
        
        return {
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'architecture': platform.architecture()[0],
            'processor': platform.processor() or 'Unknown',
            'hostname': platform.node(),
            'system': platform.system(),
            'release': platform.release()
        }


# 편의 함수들
def log_error(error: Exception, context: Optional[Dict[str, Any]] = None):
    """전역 에러 로깅 함수"""
    # 전역 에러 핸들러 인스턴스가 없으면 생성
    if not hasattr(log_error, '_handler'):
        log_error._handler = ErrorHandler()
    
    return log_error._handler.log_error(error, context)


def handle_api_error(error: Exception) -> str:
    """전역 API 에러 처리 함수"""
    if not hasattr(handle_api_error, '_handler'):
        handle_api_error._handler = ErrorHandler()
    
    return handle_api_error._handler.handle_api_error(error)


def handle_file_error(error: Exception, file_path: str = "") -> str:
    """전역 파일 에러 처리 함수"""
    if not hasattr(handle_file_error, '_handler'):
        handle_file_error._handler = ErrorHandler()
    
    return handle_file_error._handler.handle_file_error(error, file_path)


def setup_global_error_handler():
    """전역 예외 처리기 설정"""
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        
        # 에러 핸들러로 처리
        error_handler = ErrorHandler()
        error_handler.log_error(exc_value, {
            'exc_type': exc_type.__name__,
            'traceback': ''.join(traceback.format_exception(exc_type, exc_value, exc_traceback))
        })
        
        # 기본 처리도 수행
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
    
    sys.excepthook = handle_exception