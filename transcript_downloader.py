"""
향상된 YouTube 영상 대본 다운로드 모듈
- 기존 transcript-api 우선 시도
- 실패 시 yt-dlp + Whisper로 음성 인식
- 여러 백업 옵션 제공
"""

import os
import re
import json
import subprocess
import tempfile
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Tuple

# 기존 transcript-api
try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False

# Whisper 모델
try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False

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


class EnhancedTranscriptDownloader:
    def __init__(self, whisper_model="base", output_dir="transcripts"):
        """
        향상된 대본 다운로더 초기화
        
        Args:
            whisper_model (str): Whisper 모델 크기 ("tiny", "base", "small", "medium", "large")
            output_dir (str): 출력 디렉토리
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        
        self.temp_dir = Path(tempfile.gettempdir()) / "youtube_audio"
        self.temp_dir.mkdir(exist_ok=True)
        
        # Whisper 모델 로드
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
    
    def download_transcript(self, video_id: str, languages: List[str] = ['ko', 'en']) -> Dict:
        """
        대본 다운로드 (여러 방법 시도)
        
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
        
        # 방법 1: 기존 transcript-api 시도
        if TRANSCRIPT_API_AVAILABLE:
            transcript_result = self._try_transcript_api(video_id, languages)
            if transcript_result['success']:
                result.update(transcript_result)
                result['method'] = 'transcript_api'
                return result
        
        # 방법 2: Whisper 음성 인식 시도
        if WHISPER_AVAILABLE and self.whisper_model:
            whisper_result = self._try_whisper_transcription(video_id, languages)
            if whisper_result['success']:
                result.update(whisper_result)
                result['method'] = 'whisper'
                return result
        
        # 방법 3: Google Speech Recognition 시도
        if SPEECH_RECOGNITION_AVAILABLE:
            speech_result = self._try_speech_recognition(video_id)
            if speech_result['success']:
                result.update(speech_result)
                result['method'] = 'speech_recognition'
                return result
        
        # 모든 방법 실패
        result['error'] = "모든 대본 추출 방법이 실패했습니다."
        return result
    
    def _try_transcript_api(self, video_id: str, languages: List[str]) -> Dict:
        """기존 transcript-api 시도"""
        try:
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
                    transcript = transcript_list.find_generated_transcript(['en'])
            
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
            print(f"❌ Transcript API 실패: {e}")
            return {'success': False, 'error': str(e)}
        
        return {'success': False, 'error': '대본을 찾을 수 없습니다.'}
    
    def _try_whisper_transcription(self, video_id: str, languages: List[str]) -> Dict:
        """Whisper 음성 인식 시도"""
        try:
            # 1. 오디오 다운로드
            audio_path = self._download_audio(video_id)
            if not audio_path:
                return {'success': False, 'error': '오디오 다운로드 실패'}
            
            print(f"🎵 오디오 다운로드 완료: {audio_path}")
            
            # 2. Whisper로 음성 인식
            print("🤖 Whisper 음성 인식 시작...")
            
            # 언어 설정 (한국어 우선)
            language = 'ko' if 'ko' in languages else languages[0] if languages else None
            
            result = self.whisper_model.transcribe(
                str(audio_path),
                language=language,
                fp16=False,  # CPU 호환성
                verbose=False
            )
            
            transcript_text = result['text']
            
            # 3. 파일 저장
            filepath = self._save_transcript(video_id, transcript_text, 
                                           f"whisper_{language or 'auto'}")
            
            # 4. 임시 파일 정리
            try:
                os.remove(audio_path)
            except:
                pass
            
            print(f"✅ Whisper 음성 인식 완료: {len(transcript_text)} 글자")
            
            return {
                'success': True,
                'filepath': filepath,
                'text_length': len(transcript_text),
                'language': result.get('language', language),
                'duration': result.get('duration', 0)
            }
            
        except Exception as e:
            print(f"❌ Whisper 음성 인식 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def _try_speech_recognition(self, video_id: str) -> Dict:
        """Google Speech Recognition 시도"""
        try:
            # 오디오 다운로드
            audio_path = self._download_audio(video_id)
            if not audio_path:
                return {'success': False, 'error': '오디오 다운로드 실패'}
            
            print("🎤 Speech Recognition 시작...")
            
            # 오디오를 청크로 나누기 (파일이 큰 경우)
            if PYDUB_AVAILABLE:
                text_chunks = self._transcribe_audio_chunks(audio_path)
                transcript_text = ' '.join(text_chunks)
            else:
                # 전체 파일 처리
                with sr.AudioFile(str(audio_path)) as source:
                    audio = self.recognizer.record(source)
                    transcript_text = self.recognizer.recognize_google(audio, language='ko-KR')
            
            # 파일 저장
            filepath = self._save_transcript(video_id, transcript_text, "speech_recognition")
            
            # 임시 파일 정리
            try:
                os.remove(audio_path)
            except:
                pass
            
            print(f"✅ Speech Recognition 완료: {len(transcript_text)} 글자")
            
            return {
                'success': True,
                'filepath': filepath,
                'text_length': len(transcript_text),
                'language': 'ko'
            }
            
        except Exception as e:
            print(f"❌ Speech Recognition 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def _download_audio(self, video_id: str) -> Optional[Path]:
        """yt-dlp를 사용해서 오디오 다운로드"""
        try:
            audio_path = self.temp_dir / f"{video_id}.wav"
            
            # yt-dlp 명령어 구성
            cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'wav',
                '--audio-quality', '0',  # 최고 품질
                '--output', str(audio_path),
                '--no-playlist',
                '--max-duration', '1800',  # 30분 제한
                f'https://www.youtube.com/watch?v={video_id}'
            ]
            
            # 실행
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0 and audio_path.exists():
                return audio_path
            else:
                print(f"❌ yt-dlp 오류: {result.stderr}")
                return None
                
        except subprocess.TimeoutExpired:
            print("❌ 오디오 다운로드 타임아웃")
            return None
        except Exception as e:
            print(f"❌ 오디오 다운로드 오류: {e}")
            return None
    
    def _transcribe_audio_chunks(self, audio_path: Path) -> List[str]:
        """오디오를 청크로 나누어 처리"""
        try:
            # 오디오 로드
            audio = AudioSegment.from_wav(str(audio_path))
            
            # 30초 청크로 나누기
            chunk_length_ms = 30000
            chunks = make_chunks(audio, chunk_length_ms)
            
            transcripts = []
            
            for i, chunk in enumerate(chunks[:20]):  # 최대 10분 제한
                print(f"   청크 {i+1}/{min(len(chunks), 20)} 처리 중...")
                
                # 청크를 임시 파일로 저장
                chunk_path = self.temp_dir / f"chunk_{i}.wav"
                chunk.export(str(chunk_path), format="wav")
                
                try:
                    # 음성 인식
                    with sr.AudioFile(str(chunk_path)) as source:
                        audio_data = self.recognizer.record(source)
                        text = self.recognizer.recognize_google(audio_data, language='ko-KR')
                        transcripts.append(text)
                except:
                    # 이 청크는 건너뛰기
                    continue
                finally:
                    # 임시 파일 정리
                    try:
                        os.remove(chunk_path)
                    except:
                        pass
            
            return transcripts
            
        except Exception as e:
            print(f"❌ 청크 처리 오류: {e}")
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
        """여러 영상의 대본 일괄 다운로드"""
        results = {
            'success': [],
            'failed': [],
            'total': len(video_ids),
            'methods_used': {},
            'summary': {}
        }
        
        print(f"📝 {len(video_ids)}개 영상의 대본 일괄 다운로드 시작")
        
        for i, video_id in enumerate(video_ids, 1):
            print(f"\n진행률: {i}/{len(video_ids)} ({i/len(video_ids)*100:.1f}%)")
            
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
            'success_rate': len(results['success']) / len(video_ids) * 100
        }
        
        print(f"\n📊 대본 다운로드 완료!")
        print(f"   성공: {results['summary']['success_count']}개")
        print(f"   실패: {results['summary']['failed_count']}개")
        print(f"   성공률: {results['summary']['success_rate']:.1f}%")
        
        for method, count in results['methods_used'].items():
            print(f"   {method}: {count}개")
        
        return results
    
    def get_available_methods(self) -> Dict[str, bool]:
        """사용 가능한 대본 추출 방법 확인"""
        return {
            'transcript_api': TRANSCRIPT_API_AVAILABLE,
            'whisper': WHISPER_AVAILABLE and self.whisper_model is not None,
            'speech_recognition': SPEECH_RECOGNITION_AVAILABLE,
            'yt_dlp': self._check_yt_dlp_available(),
            'pydub': PYDUB_AVAILABLE
        }
    
    def _check_yt_dlp_available(self) -> bool:
        """yt-dlp 설치 여부 확인"""
        try:
            result = subprocess.run(['yt-dlp', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def cleanup_temp_files(self):
        """임시 파일 정리"""
        try:
            for file in self.temp_dir.glob("*"):
                file.unlink()
            print("✅ 임시 파일 정리 완료")
        except Exception as e:
            print(f"❌ 임시 파일 정리 오류: {e}")


def install_requirements():
    """필수 패키지 설치"""
    packages = [
        'openai-whisper',
        'yt-dlp',
        'SpeechRecognition',
        'pydub',
        'youtube-transcript-api'
    ]
    
    print("📦 필수 패키지 설치 중...")
    for package in packages:
        try:
            subprocess.run(['pip', 'install', package], check=True)
            print(f"✅ {package} 설치 완료")
        except subprocess.CalledProcessError:
            print(f"❌ {package} 설치 실패")


# 사용 예시
if __name__ == "__main__":
    # 패키지 설치 (필요시)
    # install_requirements()
    
    # 다운로더 초기화
    downloader = EnhancedTranscriptDownloader(
        whisper_model="base",  # "tiny", "base", "small", "medium", "large"
        output_dir="enhanced_transcripts"
    )
    
    # 사용 가능한 방법 확인
    methods = downloader.get_available_methods()
    print("🔍 사용 가능한 대본 추출 방법:")
    for method, available in methods.items():
        print(f"   {method}: {'✅' if available else '❌'}")
    
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
    
    # 여러 영상 테스트
    video_ids = ["dQw4w9WgXcQ", "jNQXAC9IVRw", "9bZkp7q19f0"]
    batch_result = downloader.download_multiple_transcripts(video_ids)
    
    # 임시 파일 정리
    downloader.cleanup_temp_files()