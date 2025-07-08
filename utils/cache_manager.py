"""
cache_manager.py
캐시 관리 시스템
"""

import os
import json
import pickle
import hashlib
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any, Optional, Dict


class CacheManager:
    """캐시 관리 클래스"""
    
    def __init__(self, cache_dir="cache", default_ttl=3600):
        """
        캐시 매니저 초기화
        
        Args:
            cache_dir (str): 캐시 디렉토리 경로
            default_ttl (int): 기본 TTL (초 단위)
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.default_ttl = default_ttl
        self.memory_cache = {}
        
        # 캐시 통계
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'deletes': 0,
            'clears': 0
        }
        
        print(f"📦 캐시 매니저 초기화: {self.cache_dir}")
    
    def _generate_key_hash(self, key: str) -> str:
        """키에서 해시 생성"""
        return hashlib.md5(key.encode('utf-8')).hexdigest()
    
    def _get_cache_file_path(self, key: str) -> Path:
        """캐시 파일 경로 생성"""
        key_hash = self._generate_key_hash(key)
        return self.cache_dir / f"{key_hash}.cache"
    
    def _get_metadata_file_path(self, key: str) -> Path:
        """메타데이터 파일 경로 생성"""
        key_hash = self._generate_key_hash(key)
        return self.cache_dir / f"{key_hash}.meta"
    
    def _is_expired(self, metadata: Dict) -> bool:
        """캐시가 만료되었는지 확인"""
        if 'expires_at' not in metadata:
            return True
        
        expires_at = datetime.fromisoformat(metadata['expires_at'])
        return datetime.now() > expires_at
    
    def _save_to_file(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """파일에 캐시 저장"""
        try:
            cache_file = self._get_cache_file_path(key)
            meta_file = self._get_metadata_file_path(key)
            
            ttl = ttl or self.default_ttl
            expires_at = datetime.now() + timedelta(seconds=ttl)
            
            # 데이터 저장
            with open(cache_file, 'wb') as f:
                pickle.dump(value, f)
            
            # 메타데이터 저장
            metadata = {
                'key': key,
                'created_at': datetime.now().isoformat(),
                'expires_at': expires_at.isoformat(),
                'ttl': ttl,
                'size': cache_file.stat().st_size if cache_file.exists() else 0
            }
            
            with open(meta_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            return True
            
        except Exception as e:
            print(f"캐시 파일 저장 실패 ({key}): {e}")
            return False
    
    def _load_from_file(self, key: str) -> Optional[Any]:
        """파일에서 캐시 로드"""
        try:
            cache_file = self._get_cache_file_path(key)
            meta_file = self._get_metadata_file_path(key)
            
            if not cache_file.exists() or not meta_file.exists():
                return None
            
            # 메타데이터 확인
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            if self._is_expired(metadata):
                self._delete_cache_files(key)
                return None
            
            # 데이터 로드
            with open(cache_file, 'rb') as f:
                return pickle.load(f)
                
        except Exception as e:
            print(f"캐시 파일 로드 실패 ({key}): {e}")
            return None
    
    def _delete_cache_files(self, key: str):
        """캐시 파일들 삭제"""
        try:
            cache_file = self._get_cache_file_path(key)
            meta_file = self._get_metadata_file_path(key)
            
            if cache_file.exists():
                cache_file.unlink()
            if meta_file.exists():
                meta_file.unlink()
                
        except Exception as e:
            print(f"캐시 파일 삭제 실패 ({key}): {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """캐시에서 값 가져오기"""
        # 메모리 캐시 먼저 확인
        if key in self.memory_cache:
            cache_data = self.memory_cache[key]
            if not self._is_expired(cache_data['metadata']):
                self.stats['hits'] += 1
                return cache_data['value']
            else:
                del self.memory_cache[key]
        
        # 파일 캐시 확인
        value = self._load_from_file(key)
        if value is not None:
            self.stats['hits'] += 1
            
            # 메모리 캐시에도 저장
            metadata = {
                'created_at': datetime.now().isoformat(),
                'expires_at': (datetime.now() + timedelta(seconds=self.default_ttl)).isoformat()
            }
            self.memory_cache[key] = {
                'value': value,
                'metadata': metadata
            }
            
            return value
        
        self.stats['misses'] += 1
        return default
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """캐시에 값 저장"""
        ttl = ttl or self.default_ttl
        expires_at = datetime.now() + timedelta(seconds=ttl)
        
        # 메모리 캐시에 저장
        metadata = {
            'created_at': datetime.now().isoformat(),
            'expires_at': expires_at.isoformat(),
            'ttl': ttl
        }
        
        self.memory_cache[key] = {
            'value': value,
            'metadata': metadata
        }
        
        # 파일 캐시에도 저장
        success = self._save_to_file(key, value, ttl)
        
        if success:
            self.stats['sets'] += 1
        
        return success
    
    def delete(self, key: str) -> bool:
        """캐시에서 키 삭제"""
        # 메모리 캐시에서 삭제
        if key in self.memory_cache:
            del self.memory_cache[key]
        
        # 파일 캐시에서 삭제
        try:
            self._delete_cache_files(key)
            self.stats['deletes'] += 1
            return True
        except Exception as e:
            print(f"캐시 삭제 실패 ({key}): {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """키가 캐시에 존재하는지 확인"""
        return self.get(key) is not None
    
    def clear_all(self) -> int:
        """모든 캐시 삭제"""
        deleted_count = 0
        
        # 메모리 캐시 삭제
        self.memory_cache.clear()
        
        # 파일 캐시 삭제
        try:
            for cache_file in self.cache_dir.glob("*.cache"):
                cache_file.unlink()
                deleted_count += 1
            
            for meta_file in self.cache_dir.glob("*.meta"):
                meta_file.unlink()
                
        except Exception as e:
            print(f"캐시 전체 삭제 실패: {e}")
        
        self.stats['clears'] += 1
        print(f"🗑️ {deleted_count}개 캐시 파일 삭제됨")
        
        return deleted_count
    
    def clear_expired(self) -> int:
        """만료된 캐시만 삭제"""
        deleted_count = 0
        
        # 메모리 캐시에서 만료된 것들 삭제
        expired_keys = []
        for key, cache_data in self.memory_cache.items():
            if self._is_expired(cache_data['metadata']):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.memory_cache[key]
            deleted_count += 1
        
        # 파일 캐시에서 만료된 것들 삭제
        try:
            for meta_file in self.cache_dir.glob("*.meta"):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    if self._is_expired(metadata):
                        key = metadata.get('key', '')
                        self._delete_cache_files(key)
                        deleted_count += 1
                        
                except Exception:
                    # 메타데이터 파일이 손상된 경우 삭제
                    meta_file.unlink()
                    cache_file = meta_file.with_suffix('.cache')
                    if cache_file.exists():
                        cache_file.unlink()
                    deleted_count += 1
                    
        except Exception as e:
            print(f"만료된 캐시 삭제 실패: {e}")
        
        print(f"🗑️ {deleted_count}개 만료된 캐시 삭제됨")
        return deleted_count
    
    def get_stats(self) -> Dict:
        """캐시 통계 반환"""
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0
        
        # 캐시 크기 계산
        memory_count = len(self.memory_cache)
        file_count = len(list(self.cache_dir.glob("*.cache")))
        
        # 디스크 사용량 계산
        total_size = sum(f.stat().st_size for f in self.cache_dir.glob("*") if f.is_file())
        
        return {
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'hit_rate': round(hit_rate, 2),
            'memory_count': memory_count,
            'file_count': file_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'sets': self.stats['sets'],
            'deletes': self.stats['deletes'],
            'clears': self.stats['clears']
        }
    
    def get_cache_info(self, key: str) -> Optional[Dict]:
        """특정 키의 캐시 정보 반환"""
        meta_file = self._get_metadata_file_path(key)
        
        if not meta_file.exists():
            return None
        
        try:
            with open(meta_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
            
            metadata['is_expired'] = self._is_expired(metadata)
            metadata['age_seconds'] = (
                datetime.now() - datetime.fromisoformat(metadata['created_at'])
            ).total_seconds()
            
            return metadata
            
        except Exception as e:
            print(f"캐시 정보 로드 실패 ({key}): {e}")
            return None
    
    def list_cache_keys(self, pattern: Optional[str] = None) -> list:
        """캐시된 키 목록 반환"""
        keys = []
        
        # 메모리 캐시 키들
        keys.extend(self.memory_cache.keys())
        
        # 파일 캐시 키들
        try:
            for meta_file in self.cache_dir.glob("*.meta"):
                try:
                    with open(meta_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                    
                    key = metadata.get('key', '')
                    if key and key not in keys:
                        keys.append(key)
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"캐시 키 목록 로드 실패: {e}")
        
        # 패턴 필터링
        if pattern:
            import fnmatch
            keys = [key for key in keys if fnmatch.fnmatch(key, pattern)]
        
        return sorted(keys)