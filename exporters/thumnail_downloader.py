"""
썸네일 다운로드 전용 모듈
YouTube 영상 썸네일 다운로드, 크기 조정, 압축 기능 담당
"""

import os
import re
import requests
import zipfile
from datetime import datetime
from pathlib import Path
from PIL import Image
from io import BytesIO
import concurrent.futures
import time
import config

class ThumbnailDownloader:
    """썸네일 다운로드 클래스"""
    
    def __init__(self, output_dir="thumbnails", max_workers=5):
        """
        썸네일 다운로더 초기화
        
        Args:
            output_dir (str): 출력 디렉토리
            max_workers (int): 병렬 다운로드 워커 수
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.max_workers = max_workers
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # 다운로드 통계
        self.stats = {
            'total_requested': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_existing': 0
        }
        
        print(f"✅ 썸네일 다운로더 초기화 완료 (출력: {self.output_dir})")
    
    def download_video_thumbnail(self, video_data, quality='high', resize=None, add_rank=False):
        """
        단일 영상 썸네일 다운로드
        
        Args:
            video_data (dict): 영상 데이터
            quality (str): 썸네일 품질 ('maxres', 'high', 'medium', 'default')
            resize (tuple): 리사이즈 크기 (width, height) - 선택사항
            add_rank (bool): 파일명에 순위 추가 여부
            
        Returns:
            dict: 다운로드 결과
        """
        try:
            video_id = video_data.get('id', '')
            if not video_id:
                return {'success': False, 'error': '영상 ID가 없습니다'}
            
            # 썸네일 URL 가져오기
            thumbnail_url = self._get_best_thumbnail_url(video_data, quality)
            if not thumbnail_url:
                return {'success': False, 'error': '썸네일 URL을 찾을 수 없습니다'}
            
            # 파일명 생성
            filename = self._generate_filename(video_data, add_rank)
            filepath = self.output_dir / filename
            
            # 이미 존재하는지 확인
            if filepath.exists():
                self.stats['skipped_existing'] += 1
                return {
                    'success': True,
                    'filepath': str(filepath),
                    'skipped': True,
                    'message': '이미 존재하는 파일'
                }
            
            # 다운로드 실행
            result = self._download_and_save(thumbnail_url, filepath, resize)
            
            if result['success']:
                self.stats['successful_downloads'] += 1
            else:
                self.stats['failed_downloads'] += 1
            
            return result
            
        except Exception as e:
            self.stats['failed_downloads'] += 1
            return {'success': False, 'error': f'다운로드 오류: {str(e)}'}
    
    def download_multiple_thumbnails(self, videos_data, quality='high', resize=None, 
                                   add_rank=True, create_zip=True):
        """
        여러 영상의 썸네일 일괄 다운로드
        
        Args:
            videos_data (list): 영상 데이터 목록
            quality (str): 썸네일 품질
            resize (tuple): 리사이즈 크기
            add_rank (bool): 순위 추가 여부
            create_zip (bool): ZIP 파일 생성 여부
            
        Returns:
            dict: 일괄 다운로드 결과
        """
        if not videos_data:
            return {'success': False, 'error': '다운로드할 영상이 없습니다'}
        
        print(f"🖼️ {len(videos_data)}개 영상 썸네일 다운로드 시작")
        print(f"   품질: {quality}, 워커: {self.max_workers}")
        if resize:
            print(f"   리사이즈: {resize[0]}x{resize[1]}")
        
        self.stats['total_requested'] = len(videos_data)
        start_time = time.time()
        
        # 병렬 다운로드
        downloaded_files = []
        failed_videos = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 작업 제출
            future_to_video = {
                executor.submit(
                    self.download_video_thumbnail, 
                    video, quality, resize, add_rank
                ): video for video in videos_data
            }
            
            # 결과 수집
            for i, future in enumerate(concurrent.futures.as_completed(future_to_video), 1):
                video = future_to_video[future]
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        if not result.get('skipped', False):
                            downloaded_files.append(result['filepath'])
                    else:
                        failed_videos.append({
                            'video_id': video.get('id', 'Unknown'),
                            'title': video.get('snippet', {}).get('title', 'Unknown')[:50],
                            'error': result['error']
                        })
                    
                    # 진행률 출력
                    if i % 10 == 0 or i == len(videos_data):
                        progress = (i / len(videos_data)) * 100
                        print(f"   진행률: {progress:.1f}% ({i}/{len(videos_data)})")
                
                except Exception as e:
                    failed_videos.append({
                        'video_id': video.get('id', 'Unknown'),
                        'title': video.get('snippet', {}).get('title', 'Unknown')[:50],
                        'error': str(e)
                    })
        
        # 실행 시간 계산
        execution_time = time.time() - start_time
        
        # ZIP 파일 생성
        zip_filepath = None
        if create_zip and downloaded_files:
            zip_filepath = self._create_zip_file(downloaded_files)
        
        # 결과 정리
        result = {
            'success': True,
            'summary': {
                'total_requested': self.stats['total_requested'],
                'successful_downloads': self.stats['successful_downloads'],
                'failed_downloads': self.stats['failed_downloads'],
                'skipped_existing': self.stats['skipped_existing'],
                'success_rate': (self.stats['successful_downloads'] / self.stats['total_requested'] * 100) if self.stats['total_requested'] > 0 else 0,
                'execution_time': round(execution_time, 2)
            },
            'downloaded_files': downloaded_files,
            'failed_videos': failed_videos,
            'zip_file': zip_filepath
        }
        
        # 결과 출력
        print(f"\n✅ 썸네일 다운로드 완료!")
        print(f"   성공: {self.stats['successful_downloads']}개")
        print(f"   실패: {self.stats['failed_downloads']}개")
        print(f"   건너뜀: {self.stats['skipped_existing']}개")
        print(f"   성공률: {result['summary']['success_rate']:.1f}%")
        print(f"   실행 시간: {execution_time:.1f}초")
        
        if zip_filepath:
            print(f"   ZIP 파일: {zip_filepath}")
        
        return result
    
    def download_channel_thumbnails(self, channel_videos, quality='high', resize=None):
        """
        채널의 모든 영상 썸네일 다운로드
        
        Args:
            channel_videos (list): 채널 영상 목록
            quality (str): 썸네일 품질
            resize (tuple): 리사이즈 크기
            
        Returns:
            dict: 다운로드 결과
        """
        if not channel_videos:
            return {'success': False, 'error': '채널 영상이 없습니다'}
        
        # 채널명으로 폴더 생성
        channel_name = channel_videos[0].get('snippet', {}).get('channelTitle', 'Unknown_Channel')
        safe_channel_name = self._sanitize_filename(channel_name)
        
        channel_dir = self.output_dir / safe_channel_name
        channel_dir.mkdir(exist_ok=True)
        
        # 임시로 출력 디렉토리 변경
        original_output_dir = self.output_dir
        self.output_dir = channel_dir
        
        try:
            # 일괄 다운로드 실행
            result = self.download_multiple_thumbnails(
                channel_videos, quality, resize, add_rank=True, create_zip=True
            )
            
            result['channel_name'] = channel_name
            result['channel_directory'] = str(channel_dir)
            
            return result
            
        finally:
            # 출력 디렉토리 복원
            self.output_dir = original_output_dir
    
    def _get_best_thumbnail_url(self, video_data, preferred_quality='high'):
        """최적의 썸네일 URL 가져오기"""
        try:
            thumbnails = video_data.get('snippet', {}).get('thumbnails', {})
            
            # 품질 우선순위 설정
            quality_priority = {
                'maxres': ['maxres', 'high', 'medium', 'default'],
                'high': ['high', 'medium', 'default'],
                'medium': ['medium', 'default', 'high'],
                'default': ['default', 'medium', 'high']
            }
            
            priorities = quality_priority.get(preferred_quality, quality_priority['high'])
            
            for quality in priorities:
                if quality in thumbnails and 'url' in thumbnails[quality]:
                    return thumbnails[quality]['url']
            
            return None
            
        except Exception as e:
            print(f"썸네일 URL 추출 오류: {e}")
            return None
    
    def _generate_filename(self, video_data, add_rank=False):
        """안전한 파일명 생성"""
        try:
            video_id = video_data.get('id', 'unknown')
            title = video_data.get('snippet', {}).get('title', 'Unknown Title')
            rank = video_data.get('rank', 0)
            
            # 제목 정리 (파일명으로 사용 가능하게)
            safe_title = self._sanitize_filename(title)
            safe_title = safe_title[:config.THUMBNAIL_MAX_FILENAME_LENGTH]
            
            # 파일명 조합
            if add_rank and rank > 0:
                filename = f"{rank:03d}_{safe_title}_{video_id}.jpg"
            else:
                filename = f"{safe_title}_{video_id}.jpg"
            
            return filename
            
        except Exception as e:
            print(f"파일명 생성 오류: {e}")
            return f"thumbnail_{video_data.get('id', 'unknown')}.jpg"
    
    def _sanitize_filename(self, filename):
        """파일명에서 사용할 수 없는 문자 제거"""
        # Windows에서 사용할 수 없는 문자들 제거
        invalid_chars = r'[<>:"/\\|?*]'
        safe_filename = re.sub(invalid_chars, '', filename)
        
        # 연속된 공백을 하나로
        safe_filename = re.sub(r'\s+', ' ', safe_filename)
        
        # 앞뒤 공백 제거
        safe_filename = safe_filename.strip()
        
        # 너무 짧으면 기본값
        if len(safe_filename) < 3:
            safe_filename = "thumbnail"
        
        return safe_filename
    
    def _download_and_save(self, url, filepath, resize=None):
        """실제 다운로드 및 저장"""
        try:
            # HTTP 요청
            response = self.session.get(url, timeout=config.THUMBNAIL_DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            
            # 이미지 처리
            image_data = BytesIO(response.content)
            image = Image.open(image_data)
            
            # 리사이즈 (필요한 경우)
            if resize:
                image = image.resize(resize, Image.Resampling.LANCZOS)
            
            # 파일 저장
            image.save(filepath, 'JPEG', quality=95, optimize=True)
            
            return {
                'success': True,
                'filepath': str(filepath),
                'file_size': filepath.stat().st_size,
                'image_size': image.size
            }
            
        except requests.exceptions.Timeout:
            return {'success': False, 'error': '다운로드 타임아웃'}
        except requests.exceptions.RequestException as e:
            return {'success': False, 'error': f'네트워크 오류: {str(e)}'}
        except Exception as e:
            return {'success': False, 'error': f'이미지 처리 오류: {str(e)}'}
    
    def _create_zip_file(self, file_paths):
        """다운로드된 파일들을 ZIP으로 압축"""
        try:
            if not file_paths:
                return None
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = self.output_dir / f"thumbnails_{timestamp}.zip"
            
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for file_path in file_paths:
                    file_path = Path(file_path)
                    if file_path.exists():
                        # ZIP 내에서는 파일명만 사용
                        arcname = file_path.name
                        zipf.write(file_path, arcname)
            
            return str(zip_filename)
            
        except Exception as e:
            print(f"ZIP 파일 생성 오류: {e}")
            return None
    
    def resize_existing_images(self, target_size, quality=90):
        """
        기존 이미지들을 리사이즈
        
        Args:
            target_size (tuple): 목표 크기 (width, height)
            quality (int): JPEG 품질 (1-100)
            
        Returns:
            dict: 리사이즈 결과
        """
        image_files = list(self.output_dir.glob("*.jpg"))
        
        if not image_files:
            return {'success': False, 'error': '리사이즈할 이미지가 없습니다'}
        
        print(f"🔧 {len(image_files)}개 이미지 리사이즈 시작 ({target_size[0]}x{target_size[1]})")
        
        resized_count = 0
        failed_count = 0
        
        for image_file in image_files:
            try:
                with Image.open(image_file) as img:
                    # 원본 크기와 비교
                    if img.size != target_size:
                        resized_img = img.resize(target_size, Image.Resampling.LANCZOS)
                        resized_img.save(image_file, 'JPEG', quality=quality, optimize=True)
                        resized_count += 1
                
            except Exception as e:
                print(f"리사이즈 실패 ({image_file.name}): {e}")
                failed_count += 1
        
        result = {
            'success': True,
            'total_images': len(image_files),
            'resized_count': resized_count,
            'failed_count': failed_count,
            'target_size': target_size
        }
        
        print(f"✅ 리사이즈 완료: {resized_count}개 성공, {failed_count}개 실패")
        
        return result
    
    def create_thumbnail_grid(self, image_paths, grid_size=(5, 4), output_filename=None):
        """
        썸네일들을 그리드로 배열한 이미지 생성
        
        Args:
            image_paths (list): 이미지 파일 경로 목록
            grid_size (tuple): 그리드 크기 (cols, rows)
            output_filename (str): 출력 파일명
            
        Returns:
            str: 생성된 그리드 이미지 경로
        """
        try:
            if not image_paths:
                return None
            
            cols, rows = grid_size
            max_images = cols * rows
            selected_images = image_paths[:max_images]
            
            # 첫 번째 이미지로 크기 확인
            with Image.open(selected_images[0]) as first_img:
                thumb_width, thumb_height = first_img.size
            
            # 그리드 이미지 크기 계산
            grid_width = thumb_width * cols
            grid_height = thumb_height * rows
            
            # 빈 그리드 이미지 생성
            grid_image = Image.new('RGB', (grid_width, grid_height), color='white')
            
            # 이미지들을 그리드에 배치
            for i, img_path in enumerate(selected_images):
                if i >= max_images:
                    break
                
                row = i // cols
                col = i % cols
                
                x = col * thumb_width
                y = row * thumb_height
                
                try:
                    with Image.open(img_path) as img:
                        # 크기가 다르면 리사이즈
                        if img.size != (thumb_width, thumb_height):
                            img = img.resize((thumb_width, thumb_height), Image.Resampling.LANCZOS)
                        
                        grid_image.paste(img, (x, y))
                        
                except Exception as e:
                    print(f"그리드 이미지 처리 오류 ({img_path}): {e}")
                    continue
            
            # 파일 저장
            if not output_filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"thumbnail_grid_{timestamp}.jpg"
            
            output_path = self.output_dir / output_filename
            grid_image.save(output_path, 'JPEG', quality=95, optimize=True)
            
            print(f"✅ 썸네일 그리드 생성 완료: {output_path}")
            return str(output_path)
            
        except Exception as e:
            print(f"썸네일 그리드 생성 오류: {e}")
            return None
    
    def cleanup_old_files(self, days_old=7):
        """
        오래된 썸네일 파일들 정리
        
        Args:
            days_old (int): 삭제할 파일 나이 (일)
            
        Returns:
            dict: 정리 결과
        """
        try:
            cutoff_time = time.time() - (days_old * 24 * 60 * 60)
            
            deleted_files = []
            failed_deletions = []
            
            for file_path in self.output_dir.rglob("*"):
                if file_path.is_file():
                    try:
                        if file_path.stat().st_mtime < cutoff_time:
                            file_path.unlink()
                            deleted_files.append(str(file_path))
                    except Exception as e:
                        failed_deletions.append({
                            'file': str(file_path),
                            'error': str(e)
                        })
            
            result = {
                'success': True,
                'deleted_count': len(deleted_files),
                'failed_count': len(failed_deletions),
                'deleted_files': deleted_files,
                'failed_deletions': failed_deletions
            }
            
            print(f"🧹 파일 정리 완료: {len(deleted_files)}개 삭제, {len(failed_deletions)}개 실패")
            
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_download_stats(self):
        """다운로드 통계 반환"""
        return self.stats.copy()
    
    def reset_stats(self):
        """통계 초기화"""
        self.stats = {
            'total_requested': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'skipped_existing': 0
        }


# 편의 함수들
def quick_thumbnail_download(videos_data, quality='high', resize=None, output_dir="thumbnails"):
    """
    빠른 썸네일 다운로드
    
    Args:
        videos_data (list): 영상 데이터 목록
        quality (str): 품질
        resize (tuple): 리사이즈 크기
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 다운로드 결과
    """
    downloader = ThumbnailDownloader(output_dir)
    return downloader.download_multiple_thumbnails(videos_data, quality, resize)

def download_top_performers_thumbnails(videos_data, top_count=10, output_dir="top_thumbnails"):
    """
    상위 성과 영상들의 썸네일만 다운로드
    
    Args:
        videos_data (list): 영상 데이터 목록
        top_count (int): 상위 개수
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 다운로드 결과
    """
    # Outlier Score 기준으로 정렬
    sorted_videos = sorted(
        videos_data, 
        key=lambda x: x.get('analysis', {}).get('outlier_score', 0), 
        reverse=True
    )
    
    top_videos = sorted_videos[:top_count]
    
    downloader = ThumbnailDownloader(output_dir)
    return downloader.download_multiple_thumbnails(top_videos, quality='maxres', add_rank=True)

def create_thumbnail_comparison_grid(videos_data, grid_size=(5, 4), output_dir="thumbnails"):
    """
    썸네일 비교 그리드 생성
    
    Args:
        videos_data (list): 영상 데이터 목록
        grid_size (tuple): 그리드 크기
        output_dir (str): 출력 디렉토리
        
    Returns:
        str: 생성된 그리드 이미지 경로
    """
    downloader = ThumbnailDownloader(output_dir)
    
    # 먼저 썸네일 다운로드
    result = downloader.download_multiple_thumbnails(videos_data, create_zip=False)
    
    if result['success'] and result['downloaded_files']:
        # 그리드 생성
        return downloader.create_thumbnail_grid(result['downloaded_files'], grid_size)
    
    return None