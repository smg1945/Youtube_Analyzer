"""
대본 다운로드 전용 모듈
YouTube 영상 대본 추출, 자막 다운로드, 텍스트 처리 담당
"""

import os
import re
import time
import json
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import concurrent.futures

# 선택적 import (사용 가능한 것만 활용)
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter, SRTFormatter, JSONFormatter
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("⚠️ youtube-transcript-api가 설치되지 않았습니다. 기본 자막 추출이 제한됩니다.")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("⚠️ Whisper가 설치되지 않았습니다. 음성 인식 기능이 제한됩니다.")

class TranscriptDownloader:
    """대본 다운로드 클래스"""
    
    def __init__(self, output_dir="transcripts", whisper_model="base"):
        """
        대본 다운로더 초기화
        
        Args:
            output_dir (str): 출력 디렉토리
            whisper_model (str): Whisper 모델 크기 ("tiny", "base", "small", "medium", "large")
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.temp_dir = Path(tempfile.gettempdir()) / "youtube_transcripts"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Whisper 모델 로드 (선택사항)
        self.whisper_model = None
        if WHISPER_AVAILABLE:
            try:
                print(f"🤖 Whisper 모델 로드 중: {whisper_model}")
                self.whisper_model = whisper.load_model(whisper_model)
                print("✅ Whisper 모델 로드 완료")
            except Exception as e:
                print(f"❌ Whisper 모델 로드 실패: {e}")
        
        # 포맷터 초기화
        if TRANSCRIPT_API_AVAILABLE:
            self.formatters = {
                'text': TextFormatter(),
                'srt': SRTFormatter(),
                'json': JSONFormatter()
            }
        else:
            self.formatters = {}
        
        # 통계
        self.stats = {
            'total_requested': 0,
            'successful_downloads': 0,
            'failed_downloads': 0,
            'method_used': {}
        }
        
        print(f"✅ 대본 다운로더 초기화 완료")
        print(f"   사용 가능한 방법: {self._get_available_methods()}")
    
    def download_transcript(self, video_id: str, languages: List[str] = ['ko', 'en'], 
                          output_format='text', use_whisper=False):
        """
        단일 영상 대본 다운로드
        
        Args:
            video_id (str): YouTube 영상 ID
            languages (list): 선호 언어 목록
            output_format (str): 출력 형식 ('text', 'srt', 'json')
            use_whisper (bool): Whisper 음성 인식 사용 여부
            
        Returns:
            dict: 다운로드 결과
        """
        print(f"📝 대본 다운로드 시작: {video_id}")
        
        result = {
            'success': False,
            'video_id': video_id,
            'method': '',
            'filepath': '',
            'error': '',
            'text_length': 0,
            'language': ''
        }
        
        try:
            # 방법 1: Whisper 음성 인식 (요청된 경우)
            if use_whisper and self.whisper_model:
                print("🎯 방법 1: Whisper 음성 인식 시도...")
                whisper_result = self._try_whisper_transcription(video_id, languages, output_format)
                if whisper_result['success']:
                    result.update(whisper_result)
                    result['method'] = 'whisper'
                    self._update_stats('whisper', True)
                    return result
            
            # 방법 2: YouTube Transcript API (가장 안정적)
            if TRANSCRIPT_API_AVAILABLE:
                print("🎯 방법 2: YouTube Transcript API 시도...")
                api_result = self._try_transcript_api(video_id, languages, output_format)
                if api_result['success']:
                    result.update(api_result)
                    result['method'] = 'transcript_api'
                    self._update_stats('transcript_api', True)
                    return result
            
            # 방법 3: yt-dlp 자막 추출
            print("🎯 방법 3: yt-dlp 자막 추출 시도...")
            ytdlp_result = self._try_ytdlp_subtitles(video_id, languages, output_format)
            if ytdlp_result['success']:
                result.update(ytdlp_result)
                result['method'] = 'yt-dlp'
                self._update_stats('yt-dlp', True)
                return result
            
            # 모든 방법 실패
            result['error'] = "모든 대본 추출 방법이 실패했습니다."
            self._update_stats('failed', True)
            return result
            
        except Exception as e:
            result['error'] = f"대본 다운로드 오류: {str(e)}"
            self._update_stats('error', True)
            return result
    
    def download_multiple_transcripts(self, video_ids: List[str], languages: List[str] = ['ko', 'en'],
                                    output_format='text', use_whisper=False, max_workers=3):
        """
        여러 영상의 대본 일괄 다운로드
        
        Args:
            video_ids (list): YouTube 영상 ID 목록
            languages (list): 선호 언어 목록
            output_format (str): 출력 형식
            use_whisper (bool): Whisper 사용 여부
            max_workers (int): 병렬 처리 워커 수
            
        Returns:
            dict: 일괄 다운로드 결과
        """
        if not video_ids:
            return {'success': False, 'error': '다운로드할 영상 ID가 없습니다'}
        
        print(f"📝 {len(video_ids)}개 영상 대본 일괄 다운로드 시작")
        self.stats['total_requested'] = len(video_ids)
        
        successful_downloads = []
        failed_downloads = []
        
        # 병렬 처리 (적절한 워커 수로 제한)
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 작업 제출
            future_to_video = {
                executor.submit(
                    self.download_transcript, 
                    video_id, languages, output_format, use_whisper
                ): video_id for video_id in video_ids
            }
            
            # 결과 수집
            for i, future in enumerate(concurrent.futures.as_completed(future_to_video), 1):
                video_id = future_to_video[future]
                
                try:
                    result = future.result()
                    
                    if result['success']:
                        successful_downloads.append(result)
                    else:
                        failed_downloads.append(result)
                    
                    # 진행률 출력
                    if i % 5 == 0 or i == len(video_ids):
                        progress = (i / len(video_ids)) * 100
                        print(f"   진행률: {progress:.1f}% ({i}/{len(video_ids)})")
                    
                    # API 요청 제한 고려 (짧은 대기)
                    time.sleep(0.5)
                    
                except Exception as e:
                    failed_downloads.append({
                        'success': False,
                        'video_id': video_id,
                        'error': str(e)
                    })
        
        # 결과 정리
        result = {
            'success': True,
            'summary': {
                'total_requested': len(video_ids),
                'successful_downloads': len(successful_downloads),
                'failed_downloads': len(failed_downloads),
                'success_rate': (len(successful_downloads) / len(video_ids) * 100) if video_ids else 0
            },
            'successful_downloads': successful_downloads,
            'failed_downloads': failed_downloads,
            'method_statistics': self.stats['method_used'].copy()
        }
        
        # 결과 출력
        print(f"\n✅ 대본 다운로드 완료!")
        print(f"   성공: {len(successful_downloads)}개")
        print(f"   실패: {len(failed_downloads)}개")
        print(f"   성공률: {result['summary']['success_rate']:.1f}%")
        
        # 방법별 통계
        if self.stats['method_used']:
            print(f"\n📊 사용된 방법별 통계:")
            for method, count in self.stats['method_used'].items():
                print(f"   {method}: {count}개")
        
        # ZIP 파일 생성 (성공한 경우)
        if successful_downloads:
            zip_path = self._create_transcripts_zip(successful_downloads)
            result['zip_file'] = zip_path
        
        return result
    
    def _try_transcript_api(self, video_id: str, languages: List[str], output_format: str):
        """YouTube Transcript API 시도"""
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 선호 언어로 대본 찾기
            transcript = None
            selected_language = None
            
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    selected_language = lang
                    break
                except:
                    continue
            
            # 자동 생성 대본 시도
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                    selected_language = transcript.language
                except:
                    try:
                        transcript = transcript_list.find_generated_transcript(['en'])
                        selected_language = 'en'
                    except:
                        return {'success': False, 'error': '사용 가능한 대본이 없습니다'}
            
            # 대본 데이터 가져오기
            transcript_data = transcript.fetch()
            
            # 포맷에 따라 변환
            if output_format in self.formatters:
                formatted_text = self.formatters[output_format].format_transcript(transcript_data)
            else:
                # 기본 텍스트 형식
                formatted_text = ' '.join([item['text'] for item in transcript_data])
            
            # 파일 저장
            filepath = self._save_transcript(video_id, formatted_text, f"api_{selected_language}", output_format)
            
            return {
                'success': True,
                'filepath': filepath,
                'text_length': len(formatted_text),
                'language': selected_language,
                'is_generated': transcript.is_generated
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Transcript API 오류: {str(e)}'}
    
    def _try_ytdlp_subtitles(self, video_id: str, languages: List[str], output_format: str):
        """yt-dlp 자막 추출 시도"""
        try:
            # yt-dlp 설치 확인
            if not self._check_ytdlp_available():
                return {'success': False, 'error': 'yt-dlp가 설치되지 않았습니다'}
            
            output_path = self.temp_dir / f"{video_id}_subs"
            
            # 언어 설정
            lang_codes = languages + ['en', 'auto']
            sub_langs = ','.join(lang_codes)
            
            cmd = [
                'yt-dlp',
                '--write-auto-subs',
                '--write-subs',
                '--sub-langs', sub_langs,
                '--sub-format', 'vtt',
                '--skip-download',
                '--output', str(output_path),
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            # 생성된 자막 파일 찾기
            subtitle_file = None
            selected_language = None
            
            for lang in lang_codes:
                possible_files = [
                    output_path.parent / f"{output_path.name}.{lang}.vtt",
                    output_path.parent / f"{output_path.name}.{lang}.auto.vtt"
                ]
                
                for file_path in possible_files:
                    if file_path.exists():
                        subtitle_file = file_path
                        selected_language = lang
                        break
                
                if subtitle_file:
                    break
            
            if not subtitle_file:
                return {'success': False, 'error': 'yt-dlp로 자막을 찾을 수 없습니다'}
            
            # 자막 파일 읽기 및 정리
            with open(subtitle_file, 'r', encoding='utf-8') as f:
                vtt_content = f.read()
            
            cleaned_text = self._clean_vtt_content(vtt_content)
            
            # 임시 파일 정리
            subtitle_file.unlink()
            
            if len(cleaned_text) < 10:
                return {'success': False, 'error': '추출된 텍스트가 너무 짧습니다'}
            
            # 포맷 변환 (필요한 경우)
            if output_format == 'srt':
                formatted_text = self._convert_to_srt(vtt_content)
            elif output_format == 'json':
                formatted_text = self._convert_to_json(cleaned_text, selected_language)
            else:
                formatted_text = cleaned_text
            
            # 파일 저장
            filepath = self._save_transcript(video_id, formatted_text, f"ytdlp_{selected_language}", output_format)
            
            return {
                'success': True,
                'filepath': filepath,
                'text_length': len(cleaned_text),
                'language': selected_language
            }
            
        except subprocess.TimeoutExpired:
            return {'success': False, 'error': 'yt-dlp 타임아웃'}
        except Exception as e:
            return {'success': False, 'error': f'yt-dlp 오류: {str(e)}'}
    
    def _try_whisper_transcription(self, video_id: str, languages: List[str], output_format: str):
        """Whisper 음성 인식 시도"""
        try:
            # 오디오 다운로드
            audio_path = self._download_audio_for_whisper(video_id)
            if not audio_path:
                return {'success': False, 'error': '오디오 다운로드 실패'}
            
            print(f"🎵 오디오 다운로드 완료: {audio_path.name}")
            
            # 파일 크기 확인
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:  # 100MB 제한
                audio_path.unlink()
                return {'success': False, 'error': f'파일이 너무 큽니다: {file_size_mb:.1f}MB'}
            
            # Whisper 음성 인식
            print("🤖 Whisper 음성 인식 시작...")
            
            language = 'ko' if 'ko' in languages else languages[0] if languages else None
            
            result = self.whisper_model.transcribe(
                str(audio_path),
                language=language,
                fp16=False,
                verbose=False,
                temperature=0
            )
            
            transcript_text = result['text'].strip()
            
            # 임시 파일 정리
            audio_path.unlink()
            
            if len(transcript_text) < 10:
                return {'success': False, 'error': '추출된 텍스트가 너무 짧습니다'}
            
            # 포맷 변환
            if output_format == 'json':
                formatted_text = json.dumps({
                    'text': transcript_text,
                    'language': result.get('language', language),
                    'segments': result.get('segments', [])
                }, ensure_ascii=False, indent=2)
            else:
                formatted_text = transcript_text
            
            # 파일 저장
            filepath = self._save_transcript(video_id, formatted_text, f"whisper_{result.get('language', language)}", output_format)
            
            return {
                'success': True,
                'filepath': filepath,
                'text_length': len(transcript_text),
                'language': result.get('language', language),
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            return {'success': False, 'error': f'Whisper 오류: {str(e)}'}
    
    def _download_audio_for_whisper(self, video_id: str) -> Optional[Path]:
        """Whisper용 오디오 다운로드"""
        try:
            audio_path = self.temp_dir / f"{video_id}_whisper.wav"
            
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '5',
                '--postprocessor-args', '-ar 16000 -ac 1',
                '--output', str(audio_path),
                '--no-playlist',
                '--match-filter', 'duration < 1800',  # 30분 제한
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and audio_path.exists():
                return audio_path
            else:
                return None
                
        except Exception as e:
            print(f"오디오 다운로드 오류: {e}")
            return None
    
    def _clean_vtt_content(self, vtt_content: str) -> str:
        """VTT 자막 내용 정리"""
        try:
            lines = vtt_content.split('\n')
            text_lines = []
            
            for line in lines:
                line = line.strip()
                # 시간 코드나 메타데이터 제거
                if '-->' in line or line.startswith('WEBVTT') or line.startswith('NOTE'):
                    continue
                if re.match(r'^\d+$', line):  # 숫자만 있는 라인
                    continue
                if line and not line.startswith('<'):
                    # HTML 태그 제거
                    clean_line = re.sub(r'<[^>]+>', '', line)
                    if clean_line.strip():
                        text_lines.append(clean_line.strip())
            
            # 중복 제거
            unique_lines = []
            for line in text_lines:
                if line not in unique_lines:
                    unique_lines.append(line)
            
            return ' '.join(unique_lines)
            
        except Exception as e:
            print(f"자막 정리 오류: {e}")
            return ""
    
    def _convert_to_srt(self, vtt_content: str) -> str:
        """VTT를 SRT 형식으로 변환"""
        try:
            # 간단한 VTT -> SRT 변환
            lines = vtt_content.split('\n')
            srt_lines = []
            counter = 1
            
            for i, line in enumerate(lines):
                if '-->' in line:
                    # 시간 코드 변환 (VTT -> SRT)
                    time_line = line.replace('.', ',')  # SRT는 , 사용
                    srt_lines.append(str(counter))
                    srt_lines.append(time_line)
                    
                    # 다음 라인들에서 텍스트 찾기
                    j = i + 1
                    while j < len(lines) and lines[j].strip() and '-->' not in lines[j]:
                        text_line = lines[j].strip()
                        if text_line and not text_line.startswith('<'):
                            clean_text = re.sub(r'<[^>]+>', '', text_line)
                            if clean_text.strip():
                                srt_lines.append(clean_text)
                        j += 1
                    
                    srt_lines.append('')  # 빈 줄
                    counter += 1
            
            return '\n'.join(srt_lines)
            
        except Exception as e:
            print(f"SRT 변환 오류: {e}")
            return vtt_content
    
    def _convert_to_json(self, text: str, language: str) -> str:
        """텍스트를 JSON 형식으로 변환"""
        data = {
            'text': text,
            'language': language,
            'length': len(text),
            'extracted_at': datetime.now().isoformat()
        }
        return json.dumps(data, ensure_ascii=False, indent=2)
    
    def _save_transcript(self, video_id: str, text: str, method: str, output_format: str) -> str:
        """대본 텍스트 파일 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 확장자 결정
        extensions = {'text': 'txt', 'srt': 'srt', 'json': 'json'}
        ext = extensions.get(output_format, 'txt')
        
        filename = f"{video_id}_{method}_{timestamp}.{ext}"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            if output_format == 'text':
                f.write(f"Video ID: {video_id}\n")
                f.write(f"Method: {method}\n")
                f.write(f"Timestamp: {timestamp}\n")
                f.write(f"Text Length: {len(text)} characters\n")
                f.write("-" * 50 + "\n\n")
            f.write(text)
        
        return str(filepath)
    
    def _create_transcripts_zip(self, successful_downloads: List[Dict]) -> Optional[str]:
        """성공한 대본들을 ZIP으로 압축"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            zip_filename = self.output_dir / f"transcripts_{timestamp}.zip"
            
            import zipfile
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for download in successful_downloads:
                    filepath = download['filepath']
                    if os.path.exists(filepath):
                        filename = os.path.basename(filepath)
                        zipf.write(filepath, filename)
            
            print(f"📦 대본 ZIP 파일 생성: {zip_filename}")
            return str(zip_filename)
            
        except Exception as e:
            print(f"ZIP 파일 생성 오류: {e}")
            return None
    
    def _check_ytdlp_available(self) -> bool:
        """yt-dlp 설치 여부 확인"""
        try:
            result = subprocess.run(['yt-dlp', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def _get_available_methods(self) -> List[str]:
        """사용 가능한 추출 방법 목록"""
        methods = []
        
        if TRANSCRIPT_API_AVAILABLE:
            methods.append('transcript_api')
        if self._check_ytdlp_available():
            methods.append('yt-dlp')
        if WHISPER_AVAILABLE and self.whisper_model:
            methods.append('whisper')
        
        return methods
    
    def _update_stats(self, method: str, success: bool):
        """통계 업데이트"""
        if method not in self.stats['method_used']:
            self.stats['method_used'][method] = 0
        
        self.stats['method_used'][method] += 1
        
        if success:
            self.stats['successful_downloads'] += 1
        else:
            self.stats['failed_downloads'] += 1
    
    def get_stats(self) -> Dict:
        """통계 반환"""
        return self.stats.copy()
    
    def cleanup_temp_files(self):
        """임시 파일 정리"""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            print("✅ 임시 파일 정리 완료")
        except Exception as e:
            print(f"❌ 임시 파일 정리 오류: {e}")


# 편의 함수들
def quick_transcript_download(video_ids: List[str], languages=['ko', 'en'], 
                            output_format='text', output_dir="transcripts"):
    """
    빠른 대본 다운로드
    
    Args:
        video_ids (list): YouTube 영상 ID 목록
        languages (list): 선호 언어
        output_format (str): 출력 형식
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 다운로드 결과
    """
    downloader = TranscriptDownloader(output_dir)
    
    if len(video_ids) == 1:
        return downloader.download_transcript(video_ids[0], languages, output_format)
    else:
        return downloader.download_multiple_transcripts(video_ids, languages, output_format)

def download_high_performance_transcripts(videos_data: List[Dict], min_outlier_score=2.0, 
                                        output_dir="top_transcripts"):
    """
    고성과 영상들의 대본만 다운로드
    
    Args:
        videos_data (list): 영상 데이터 목록
        min_outlier_score (float): 최소 Outlier Score
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 다운로드 결과
    """
    # 고성과 영상 필터링
    high_performers = [
        video for video in videos_data 
        if video.get('analysis', {}).get('outlier_score', 0) >= min_outlier_score
    ]
    
    if not high_performers:
        return {'success': False, 'error': f'Outlier Score {min_outlier_score} 이상인 영상이 없습니다'}
    
    video_ids = [video['id'] for video in high_performers]
    
    downloader = TranscriptDownloader(output_dir)
    result = downloader.download_multiple_transcripts(video_ids, ['ko', 'en'], 'text')
    
    result['filter_criteria'] = f'Outlier Score >= {min_outlier_score}'
    result['total_videos_analyzed'] = len(videos_data)
    result['high_performers_found'] = len(high_performers)
    
    return result

def extract_transcript_keywords(transcript_files: List[str], language='ko'):
    """
    대본 파일들에서 키워드 추출
    
    Args:
        transcript_files (list): 대본 파일 경로 목록
        language (str): 언어
        
    Returns:
        dict: 키워드 분석 결과
    """
    try:
        from data import TextAnalyzer
        
        analyzer = TextAnalyzer(language)
        all_texts = []
        
        # 모든 대본 파일 읽기
        for filepath in transcript_files:
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                    # 메타데이터 부분 제거 (--- 이후가 실제 텍스트)
                    if '---' in content:
                        content = content.split('---', 1)[-1]
                    
                    all_texts.append(content.strip())
                    
            except Exception as e:
                print(f"파일 읽기 오류 ({filepath}): {e}")
                continue
        
        if not all_texts:
            return {'success': False, 'error': '읽을 수 있는 대본 파일이 없습니다'}
        
        # 텍스트 분석
        keyword_freq = analyzer.analyze_keyword_frequency(all_texts)
        trending_keywords = analyzer.find_trending_keywords(all_texts)
        
        # 고빈도 키워드 추출 (상위 20개)
        top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]
        
        # 키워드 클러스터링
        keyword_clusters = analyzer.cluster_similar_keywords([kw[0] for kw in top_keywords])
        
        # 감정 분석 (한국어만)
        sentiment_analysis = None
        if language == 'ko':
            try:
                sentiment_analysis = analyzer.analyze_sentiment_distribution(all_texts)
            except Exception as e:
                print(f"감정 분석 오류: {e}")
        
        # 결과 구성
        result = {
            'success': True,
            'total_transcripts': len(transcript_files),
            'processed_transcripts': len(all_texts),
            'total_words': sum(len(text.split()) for text in all_texts),
            'keyword_frequency': dict(top_keywords),
            'trending_keywords': trending_keywords,
            'keyword_clusters': keyword_clusters,
            'language': language,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        # 감정 분석 결과 추가 (있는 경우)
        if sentiment_analysis:
            result['sentiment_analysis'] = sentiment_analysis
        
        # 키워드 트렌드 분석
        if len(all_texts) > 1:
            try:
                keyword_trends = analyzer.analyze_keyword_trends_across_videos(all_texts)
                result['keyword_trends'] = keyword_trends
            except Exception as e:
                print(f"키워드 트렌드 분석 오류: {e}")
        
        return result
        
    except ImportError:
        return {
            'success': False, 
            'error': 'TextAnalyzer 모듈을 찾을 수 없습니다. data 모듈이 설치되어 있는지 확인하세요.'
        }
    except Exception as e:
        return {'success': False, 'error': f'키워드 추출 오류: {str(e)}'}

def compare_transcript_methods(video_id: str, languages=['ko', 'en'], output_dir="method_comparison"):
    """
    여러 추출 방법으로 같은 영상의 대본을 비교
    
    Args:
        video_id (str): YouTube 영상 ID
        languages (list): 언어 목록
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 방법별 비교 결과
    """
    downloader = TranscriptDownloader(output_dir)
    
    results = {}
    methods = ['transcript_api', 'yt-dlp', 'whisper']
    
    for method in methods:
        if method == 'whisper':
            result = downloader.download_transcript(video_id, languages, 'text', use_whisper=True)
        else:
            result = downloader.download_transcript(video_id, languages, 'text', use_whisper=False)
        
        results[method] = result
    
    # 비교 분석
    comparison = {
        'video_id': video_id,
        'methods_tested': methods,
        'results': results,
        'success_count': sum(1 for r in results.values() if r['success']),
        'best_method': None,
        'longest_text': None
    }
    
    # 가장 긴 텍스트를 생성한 방법 찾기
    max_length = 0
    for method, result in results.items():
        if result['success'] and result['text_length'] > max_length:
            max_length = result['text_length']
            comparison['best_method'] = method
            comparison['longest_text'] = result
    
    return comparison