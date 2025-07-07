"""
YouTube 영상 대본 다운로드 모듈 - Whisper 우선 버전
Whisper → yt-dlp → youtube-transcript-api → Speech Recognition 순서
"""

import os
import re
import json
import subprocess
import tempfile
import time
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# Whisper 모델 (최우선)
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

# 기존 transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False

# 음성 인식 라이브러리
try:
    import speech_recognition as sr
    SPEECH_RECOGNITION_AVAILABLE = True
except ImportError:
    SPEECH_RECOGNITION_AVAILABLE = False

# 오디오 처리
try:
    from pydub import AudioSegment
    from pydub.utils import make_chunks
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False


class WhisperFirstTranscriptDownloader:
    def __init__(self, whisper_model="base", output_dir="transcripts"):
        """
        Whisper 우선 대본 다운로더 초기화
        
        Args:
            whisper_model (str): Whisper 모델 크기 ("tiny", "base", "small", "medium", "large")
            output_dir (str): 출력 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.temp_dir = Path(tempfile.gettempdir()) / "youtube_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Whisper 모델 로드 (최우선)
        self.whisper_model = None
        if WHISPER_AVAILABLE:
            try:
                print(f"🤖 Whisper 모델 로드 중: {whisper_model}")
                self.whisper_model = whisper.load_model(whisper_model)
                print("✅ Whisper 모델 로드 완료")
            except Exception as e:
                print(f"❌ Whisper 모델 로드 실패: {e}")
        
        # 음성 인식기 초기화
        self.recognizer = sr.Recognizer() if SPEECH_RECOGNITION_AVAILABLE else None
        
        # 텍스트 포맷터
        self.formatter = TextFormatter() if TRANSCRIPT_API_AVAILABLE else None
        
        # 요청 제한 대응
        self.last_request_time = 0
        self.request_delay = 1  # 초
    
    def download_transcript(self, video_id: str, languages: List[str] = ['ko', 'en']) -> Dict:
        """
        대본 다운로드 - Whisper 우선 순서
        
        순서: Whisper → yt-dlp → youtube-transcript-api → Speech Recognition
        
        Args:
            video_id (str): YouTube 영상 ID
            languages (list): 선호 언어 목록
            
        Returns:
            dict: 결과 정보
        """
        result = {
            'success': False,
            'method': '',
            'filepath': '',
            'error': '',
            'duration': 0,
            'text_length': 0
        }
        
        print(f"📝 대본 다운로드 시작: {video_id}")
        
        # 방법 1: Whisper 음성 인식 시도 (최우선)
        if WHISPER_AVAILABLE and self.whisper_model:
            print("🎯 방법 1: Whisper 음성 인식 시도...")
            whisper_result = self._try_whisper_transcription(video_id, languages)
            if whisper_result['success']:
                result.update(whisper_result)
                result['method'] = 'whisper'
                print(f"✅ Whisper 성공: {result['text_length']} 글자")
                return result
            else:
                print(f"❌ Whisper 실패: {whisper_result.get('error', 'Unknown error')}")
        
        # 방법 2: yt-dlp 직접 오디오 다운로드 + 간단한 처리
        print("🎯 방법 2: yt-dlp 오디오 다운로드 시도...")
        ytdlp_result = self._try_ytdlp_direct(video_id, languages)
        if ytdlp_result['success']:
            result.update(ytdlp_result)
            result['method'] = 'yt-dlp'
            print(f"✅ yt-dlp 성공: {result['text_length']} 글자")
            return result
        else:
            print(f"❌ yt-dlp 실패: {ytdlp_result.get('error', 'Unknown error')}")
        
        # 방법 3: 기존 transcript-api 시도 (재시도 로직 추가)
        if TRANSCRIPT_API_AVAILABLE:
            print("🎯 방법 3: YouTube Transcript API 시도...")
            transcript_result = self._try_transcript_api_with_retry(video_id, languages, max_retries=2)
            if transcript_result['success']:
                result.update(transcript_result)
                result['method'] = 'transcript_api'
                print(f"✅ Transcript API 성공: {result['text_length']} 글자")
                return result
            else:
                print(f"❌ Transcript API 실패: {transcript_result.get('error', 'Unknown error')}")
        
        # 방법 4: Google Speech Recognition 시도 (최후 수단)
        if SPEECH_RECOGNITION_AVAILABLE:
            print("🎯 방법 4: Google Speech Recognition 시도...")
            speech_result = self._try_speech_recognition(video_id)
            if speech_result['success']:
                result.update(speech_result)
                result['method'] = 'speech_recognition'
                print(f"✅ Speech Recognition 성공: {result['text_length']} 글자")
                return result
            else:
                print(f"❌ Speech Recognition 실패: {speech_result.get('error', 'Unknown error')}")
        
        # 모든 방법 실패
        result['error'] = "모든 대본 추출 방법이 실패했습니다."
        print(f"❌ 모든 방법 실패: {result['error']}")
        return result
    
    def _try_whisper_transcription(self, video_id: str, languages: List[str]) -> Dict:
        """Whisper 음성 인식 시도 - 개선된 버전"""
        try:
            # 1. 오디오 다운로드
            audio_path = self._download_audio_for_whisper(video_id)
            if not audio_path:
                return {'success': False, 'error': '오디오 다운로드 실패'}
            
            print(f"🎵 오디오 다운로드 완료: {audio_path.name}")
            
            # 2. 파일 크기 확인 (너무 큰 파일은 처리하지 않음)
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 100:  # 100MB 제한
                audio_path.unlink()
                return {'success': False, 'error': f'파일이 너무 큽니다: {file_size_mb:.1f}MB'}
            
            # 3. Whisper로 음성 인식
            print("🤖 Whisper 음성 인식 시작...")
            
            # 언어 설정 (한국어 우선)
            language = 'ko' if 'ko' in languages else languages[0] if languages else None
            
            # Whisper 옵션 최적화
            result = self.whisper_model.transcribe(
                str(audio_path),
                language=language,
                fp16=False,  # CPU 호환성
                verbose=False,
                temperature=0,  # 더 안정적인 결과
                best_of=1,  # 속도 최적화
                beam_size=1,  # 속도 최적화
                patience=1.0
            )
            
            transcript_text = result['text'].strip()
            
            # 4. 결과 검증
            if not transcript_text or len(transcript_text) < 10:
                audio_path.unlink()
                return {'success': False, 'error': '추출된 텍스트가 너무 짧습니다'}
            
            # 5. 파일 저장
            filepath = self._save_transcript(video_id, transcript_text, 
                                           f"whisper_{language or 'auto'}")
            
            # 6. 임시 파일 정리
            audio_path.unlink()
            
            print(f"✅ Whisper 음성 인식 완료: {len(transcript_text)} 글자")
            
            return {
                'success': True,
                'filepath': filepath,
                'text_length': len(transcript_text),
                'language': result.get('language', language),
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            print(f"❌ Whisper 음성 인식 오류: {e}")
            # 임시 파일 정리
            try:
                if 'audio_path' in locals() and audio_path.exists():
                    audio_path.unlink()
            except:
                pass
            return {'success': False, 'error': str(e)}
    
    def _download_audio_for_whisper(self, video_id: str) -> Optional[Path]:
        """Whisper용 최적화된 오디오 다운로드"""
        try:
            audio_path = self.temp_dir / f"{video_id}_whisper.wav"
            
            # Whisper용 최적화된 yt-dlp 명령어
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '5',  # 중간 품질 (파일 크기 고려)
                '--postprocessor-args', '-ar 16000 -ac 1',  # 16kHz, 모노 (Whisper 최적화)
                '--output', str(audio_path),
                '--no-playlist',
                '--match-filter', 'duration < 1800',  # 30분 제한
                '--no-warnings',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            # 실행 (타임아웃 단축)
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            if result.returncode == 0 and audio_path.exists():
                return audio_path
            else:
                print(f"yt-dlp 오류: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("오디오 다운로드 타임아웃 (2분)")
            return None
        except Exception as e:
            print(f"오디오 다운로드 오류: {e}")
            return None
    
    def _try_ytdlp_direct(self, video_id: str, languages: List[str]) -> Dict:
        """yt-dlp로 직접 처리"""
        try:
            # 간단한 방법: yt-dlp로 자막 추출 시도
            subtitles_path = self._extract_subtitles_ytdlp(video_id, languages)
            if subtitles_path:
                with open(subtitles_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # 자막 정리
                cleaned_text = self._clean_subtitle_text(content)
                
                if cleaned_text and len(cleaned_text) > 10:
                    filepath = self._save_transcript(video_id, cleaned_text, "ytdlp_subtitles")
                    
                    # 임시 파일 정리
                    subtitles_path.unlink()
                    
                    return {
                        'success': True,
                        'filepath': filepath,
                        'text_length': len(cleaned_text),
                        'language': languages[0] if languages else 'auto'
                    }
            
            return {'success': False, 'error': 'yt-dlp로 자막을 찾을 수 없습니다'}
            
        except Exception as e:
            return {'success': False, 'error': f'yt-dlp 처리 오류: {str(e)}'}
    
    def _extract_subtitles_ytdlp(self, video_id: str, languages: List[str]) -> Optional[Path]:
        """yt-dlp로 자막 추출"""
        try:
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
            for lang in lang_codes:
                possible_files = [
                    output_path.parent / f"{output_path.name}.{lang}.vtt",
                    output_path.parent / f"{output_path.name}.{lang}.auto.vtt"
                ]
                
                for file_path in possible_files:
                    if file_path.exists():
                        return file_path
            
            return None
            
        except Exception as e:
            print(f"자막 추출 오류: {e}")
            return None
    
    def _clean_subtitle_text(self, vtt_content: str) -> str:
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
            
            # 중복 제거 및 정리
            unique_lines = []
            for line in text_lines:
                if line not in unique_lines:
                    unique_lines.append(line)
            
            return ' '.join(unique_lines)
            
        except Exception as e:
            print(f"자막 정리 오류: {e}")
            return ""
    
    def _try_transcript_api_with_retry(self, video_id: str, languages: List[str], max_retries: int = 2) -> Dict:
        """기존 transcript-api 시도 (재시도 로직 추가)"""
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = attempt * 5  # 5초, 10초 대기
                    print(f"⏳ API 요청 재시도 {attempt + 1}/{max_retries} (대기: {wait_time}초)")
                    time.sleep(wait_time)
                
                # 요청 제한 대응
                current_time = time.time()
                if current_time - self.last_request_time < self.request_delay:
                    sleep_time = self.request_delay - (current_time - self.last_request_time)
                    time.sleep(sleep_time)
                
                self.last_request_time = time.time()
                
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                
                # 선호 언어로 대본 찾기
                transcript = None
                for lang in languages:
                    try:
                        transcript = transcript_list.find_transcript([lang])
                        break
                    except:
                        continue
                
                # 자동 생성 대본 시도
                if not transcript:
                    try:
                        transcript = transcript_list.find_generated_transcript(languages)
                    except:
                        try:
                            transcript = transcript_list.find_generated_transcript(['en'])
                        except:
                            continue
                
                if transcript:
                    transcript_data = transcript.fetch()
                    formatted_text = self.formatter.format_transcript(transcript_data)
                    
                    # 파일 저장
                    filepath = self._save_transcript(video_id, formatted_text, 
                                                   f"transcript_api_{transcript.language}")
                    
                    return {
                        'success': True,
                        'filepath': filepath,
                        'text_length': len(formatted_text),
                        'language': transcript.language,
                        'is_generated': transcript.is_generated
                    }
                    
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "Too Many Requests" in error_msg:
                    print(f"❌ API 요청 제한 (시도 {attempt + 1}/{max_retries}): {e}")
                    if attempt < max_retries - 1:
                        time.sleep(10)  # 긴 대기
                        continue
                else:
                    print(f"❌ Transcript API 오류 (시도 {attempt + 1}/{max_retries}): {e}")
                    break
        
        return {'success': False, 'error': '대본을 찾을 수 없거나 API 요청 제한 초과'}
    
    def _try_speech_recognition(self, video_id: str) -> Dict:
        """Google Speech Recognition 시도 - 최후 수단"""
        try:
            # 간단한 오디오 다운로드
            audio_path = self._download_simple_audio(video_id)
            if not audio_path:
                return {'success': False, 'error': '오디오 다운로드 실패'}
            
            print("🎤 Speech Recognition 시작...")
            
            # 짧은 오디오만 처리 (5분 이하)
            file_size_mb = audio_path.stat().st_size / (1024 * 1024)
            if file_size_mb > 50:  # 50MB 제한
                audio_path.unlink()
                return {'success': False, 'error': '파일이 너무 큽니다 (Speech Recognition 제한)'}
            
            # 오디오를 청크로 나누기
            if PYDUB_AVAILABLE:
                text_chunks = self._transcribe_audio_chunks_simple(audio_path)
                transcript_text = ' '.join(text_chunks)
            else:
                # 전체 파일 처리
                with sr.AudioFile(str(audio_path)) as source:
                    audio = self.recognizer.record(source)
                    transcript_text = self.recognizer.recognize_google(audio, language='ko-KR')
            
            # 임시 파일 정리
            audio_path.unlink()
            
            if transcript_text and len(transcript_text) > 10:
                filepath = self._save_transcript(video_id, transcript_text, "speech_recognition")
                
                print(f"✅ Speech Recognition 완료: {len(transcript_text)} 글자")
                
                return {
                    'success': True,
                    'filepath': filepath,
                    'text_length': len(transcript_text),
                    'language': 'ko'
                }
            else:
                return {'success': False, 'error': '추출된 텍스트가 너무 짧습니다'}
            
        except Exception as e:
            print(f"❌ Speech Recognition 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def _download_simple_audio(self, video_id: str) -> Optional[Path]:
        """간단한 오디오 다운로드 (Speech Recognition용)"""
        try:
            audio_path = self.temp_dir / f"{video_id}_simple.wav"
            
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'wav',
                '--postprocessor-args', '-t 300',  # 5분 제한
                '--output', str(audio_path),
                '--no-playlist',
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and audio_path.exists():
                return audio_path
            else:
                return None
                
        except Exception as e:
            print(f"간단한 오디오 다운로드 실패: {e}")
            return None
    
    def _transcribe_audio_chunks_simple(self, audio_path: Path) -> List[str]:
        """간단한 오디오 청크 처리"""
        try:
            audio = AudioSegment.from_wav(str(audio_path))
            
            # 20초 청크로 나누기 (더 짧게)
            chunk_length_ms = 20000
            chunks = make_chunks(audio, chunk_length_ms)
            
            transcripts = []
            max_chunks = min(len(chunks), 15)  # 최대 5분 (20초 x 15)
            
            for i, chunk in enumerate(chunks[:max_chunks]):
                chunk_path = self.temp_dir / f"simple_chunk_{i}.wav"
                
                try:
                    chunk.export(str(chunk_path), format="wav")
                    
                    with sr.AudioFile(str(chunk_path)) as source:
                        audio_data = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio_data, language='ko-KR')
                        transcripts.append(text)
                        
                except Exception as e:
                    print(f"청크 {i+1} 처리 오류: {e}")
                    continue
                finally:
                    if chunk_path.exists():
                        chunk_path.unlink()
            
            return transcripts
            
        except Exception as e:
            print(f"청크 처리 오류: {e}")
            return []
    
    def _save_transcript(self, video_id: str, text: str, method: str) -> str:
        """대본 텍스트 파일 저장"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{video_id}_{method}_{timestamp}.txt"
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"Video ID: {video_id}\n")
            f.write(f"Method: {method}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write(f"Text Length: {len(text)} characters\n")
            f.write("-" * 50 + "\n\n")
            f.write(text)
        
        return str(filepath)
    
    def download_multiple_transcripts(self, video_ids: List[str], languages: List[str] = ['ko', 'en']) -> Dict:
        """여러 영상의 대본 일괄 다운로드 - Whisper 우선"""
        results = {
            'success': [],
            'failed': [],
            'total': len(video_ids),
            'methods_used': {},
            'summary': {}
        }
        
        print(f"📝 {len(video_ids)}개 영상의 대본 일괄 다운로드 시작 (Whisper 우선)")
        
        for i, video_id in enumerate(video_ids, 1):
            print(f"\n진행률: {i}/{len(video_ids)} ({i/len(video_ids)*100:.1f}%)")
            
            # 적절한 딜레이 (Whisper는 로컬이므로 짧게)
            if i > 1:
                time.sleep(0.5)  # 0.5초 대기
            
            result = self.download_transcript(video_id, languages)
            
            if result['success']:
                results['success'].append({
                    'video_id': video_id,
                    'method': result['method'],
                    'filepath': result['filepath'],
                    'text_length': result['text_length']
                })
                
                # 방법별 통계
                method = result['method']
                if method not in results['methods_used']:
                    results['methods_used'][method] = 0
                results['methods_used'][method] += 1
                
            else:
                results['failed'].append({
                    'video_id': video_id,
                    'error': result['error']
                })
        
        # 요약 정보
        results['summary'] = {
            'success_count': len(results['success']),
            'failed_count': len(results['failed']),
            'success_rate': len(results['success']) / len(video_ids) * 100 if video_ids else 0
        }
        
        print(f"\n📊 대본 다운로드 완료!")
        print(f"   성공: {results['summary']['success_count']}개")
        print(f"   실패: {results['summary']['failed_count']}개")
        print(f"   성공률: {results['summary']['success_rate']:.1f}%")
        
        # 방법별 통계
        print(f"\n📋 사용된 방법별 통계:")
        for method, count in results['methods_used'].items():
            percentage = (count / results['summary']['success_count'] * 100) if results['summary']['success_count'] > 0 else 0
            print(f"   {method}: {count}개 ({percentage:.1f}%)")
        
        return results
    
    def get_available_methods(self) -> Dict[str, bool]:
        """사용 가능한 대본 추출 방법 확인"""
        return {
            'whisper': WHISPER_AVAILABLE and self.whisper_model is not None,
            'yt_dlp': self._check_yt_dlp_available(),
            'transcript_api': TRANSCRIPT_API_AVAILABLE,
            'speech_recognition': SPEECH_RECOGNITION_AVAILABLE,
            'pydub': PYDUB_AVAILABLE
        }
    
    def _check_yt_dlp_available(self) -> bool:
        """yt-dlp 설치 여부 확인"""
        try:
            result = subprocess.run(['yt-dlp', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            return result.returncode == 0
        except:
            return False
    
    def cleanup_temp_files(self):
        """임시 파일 정리"""
        try:
            for file in self.temp_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            print("✅ 임시 파일 정리 완료")
        except Exception as e:
            print(f"❌ 임시 파일 정리 오류: {e}")


# 사용 예시
if __name__ == "__main__":
    # 다운로더 초기화
    downloader = WhisperFirstTranscriptDownloader(
        whisper_model="base",  # "tiny", "base", "small", "medium", "large"
        output_dir="whisper_first_transcripts"
    )
    
    # 사용 가능한 방법 확인
    methods = downloader.get_available_methods()
    print("🔍 사용 가능한 대본 추출 방법 (우선순위순):")
    method_names = {
        'whisper': '1. Whisper (로컬 음성 인식)',
        'yt_dlp': '2. yt-dlp (자막 추출)',
        'transcript_api': '3. YouTube Transcript API',
        'speech_recognition': '4. Google Speech Recognition'
    }
    
    for method, available in methods.items():
        if method in method_names:
            status = '✅' if available else '❌'
            print(f"   {method_names[method]}: {status}")
    
    # 단일 영상 테스트
    video_id = "dQw4w9WgXcQ"  # 예시 영상 ID
    result = downloader.download_transcript(video_id, languages=['ko', 'en'])
    
    if result['success']:
        print(f"\n✅ 대본 다운로드 성공!")
        print(f"   방법: {result['method']}")
        print(f"   파일: {result['filepath']}")
        print(f"   길이: {result['text_length']} 글자")
    else:
        print(f"\n❌ 대본 다운로드 실패: {result['error']}")
    
    # 임시 파일 정리
    downloader.cleanup_temp_files()