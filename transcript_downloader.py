"""
YouTube 영상 자막/대본 다운로드 및 음성 인식 관련 함수들
"""

import os
import re
import tempfile
import subprocess
from datetime import datetime
import zipfile

try:
    from youtube_transcript_api import YouTubeTranscriptApi
    from youtube_transcript_api.formatters import TextFormatter
    TRANSCRIPT_API_AVAILABLE = True
except ImportError:
    TRANSCRIPT_API_AVAILABLE = False
    print("youtube-transcript-api가 설치되지 않았습니다. 자막 다운로드 기능이 제한됩니다.")

try:
    import yt_dlp
    YT_DLP_AVAILABLE = True
except ImportError:
    YT_DLP_AVAILABLE = False
    print("yt-dlp가 설치되지 않았습니다. 영상 다운로드 기능이 제한됩니다.")

try:
    import whisper
    WHISPER_AVAILABLE = True
except ImportError:
    WHISPER_AVAILABLE = False
    print("openai-whisper가 설치되지 않았습니다. 음성 인식 기능이 제한됩니다.")

class TranscriptDownloader:
    def __init__(self):
        """자막 다운로더 초기화"""
        self.text_formatter = TextFormatter() if TRANSCRIPT_API_AVAILABLE else None
        self.whisper_model = None
        self.download_stats = {
            'success': 0,
            'failed': 0,
            'no_transcript': 0,
            'speech_to_text': 0
        }
    
    def load_whisper_model(self, model_size="base"):
        """
        Whisper 모델 로드
        
        Args:
            model_size (str): 모델 크기 ("tiny", "base", "small", "medium", "large")
        
        Returns:
            bool: 로드 성공 여부
        """
        if not WHISPER_AVAILABLE:
            print("❌ Whisper가 설치되지 않았습니다.")
            return False
        
        try:
            print(f"🤖 Whisper {model_size} 모델 로딩 중...")
            self.whisper_model = whisper.load_model(model_size)
            print("✅ Whisper 모델 로드 완료!")
            return True
        except Exception as e:
            print(f"❌ Whisper 모델 로드 실패: {e}")
            return False
    
    def get_available_transcripts(self, video_id):
        """
        영상의 사용 가능한 자막 언어 목록 가져오기
        
        Args:
            video_id (str): 영상 ID
            
        Returns:
            list: 사용 가능한 자막 언어 목록
        """
        if not TRANSCRIPT_API_AVAILABLE:
            return []
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            available_transcripts = []
            
            for transcript in transcript_list:
                transcript_info = {
                    'language_code': transcript.language_code,
                    'language': transcript.language,
                    'is_generated': transcript.is_generated,
                    'is_translatable': transcript.is_translatable
                }
                available_transcripts.append(transcript_info)
            
            return available_transcripts
            
        except Exception as e:
            print(f"자막 목록 가져오기 오류 (영상 ID: {video_id}): {e}")
            return []
    
    def download_audio_from_youtube(self, video_id, output_path="temp_audio"):
        """
        YouTube 영상에서 오디오 추출
        
        Args:
            video_id (str): 영상 ID
            output_path (str): 오디오 파일 저장 경로
            
        Returns:
            str: 추출된 오디오 파일 경로 (실패시 None)
        """
        if not YT_DLP_AVAILABLE:
            print("❌ yt-dlp가 설치되지 않았습니다.")
            return None
        
        try:
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # 임시 디렉토리 생성
            os.makedirs(output_path, exist_ok=True)
            audio_file = os.path.join(output_path, f"{video_id}.wav")
            
            # yt-dlp 옵션 설정
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(output_path, f"{video_id}.%(ext)s"),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'wav',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            print(f"🎵 영상 {video_id}의 오디오 추출 중...")
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            
            if os.path.exists(audio_file):
                print(f"✅ 오디오 추출 완료: {audio_file}")
                return audio_file
            else:
                print(f"❌ 오디오 파일을 찾을 수 없습니다: {audio_file}")
                return None
                
        except Exception as e:
            print(f"❌ 오디오 추출 실패: {e}")
            return None
    
    def transcribe_audio_with_whisper(self, audio_file_path, language=None):
        """
        Whisper를 사용해서 오디오를 텍스트로 변환
        
        Args:
            audio_file_path (str): 오디오 파일 경로
            language (str): 언어 코드 ("ko", "en" 등, None이면 자동 감지)
            
        Returns:
            dict: {'success': bool, 'text': str, 'language': str}
        """
        if not self.whisper_model:
            if not self.load_whisper_model():
                return {'success': False, 'error': 'Whisper 모델 로드 실패'}
        
        try:
            print("🤖 Whisper로 음성 인식 중...")
            
            # Whisper로 음성 인식 수행
            if language:
                result = self.whisper_model.transcribe(audio_file_path, language=language)
            else:
                result = self.whisper_model.transcribe(audio_file_path)
            
            text = result["text"].strip()
            detected_language = result.get("language", "unknown")
            
            if text:
                print(f"✅ 음성 인식 완료 (언어: {detected_language})")
                return {
                    'success': True,
                    'text': text,
                    'language': detected_language
                }
            else:
                return {'success': False, 'error': '인식된 텍스트가 없습니다'}
                
        except Exception as e:
            print(f"❌ 음성 인식 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    def generate_transcript_from_speech(self, video_id, video_title="", language=None):
        """
        음성 인식을 통한 자막 생성
        
        Args:
            video_id (str): 영상 ID
            video_title (str): 영상 제목
            language (str): 언어 코드
            
        Returns:
            dict: 생성 결과
        """
        temp_dir = "temp_audio"
        audio_file = None
        
        try:
            # 1. YouTube에서 오디오 추출
            audio_file = self.download_audio_from_youtube(video_id, temp_dir)
            if not audio_file:
                return {'success': False, 'error': '오디오 추출 실패'}
            
            # 2. Whisper로 음성 인식
            transcript_result = self.transcribe_audio_with_whisper(audio_file, language)
            if not transcript_result['success']:
                return transcript_result
            
            # 3. 텍스트 파일 저장
            transcript_text = transcript_result['text']
            detected_language = transcript_result['language']
            
            # 파일명 생성
            safe_title = re.sub(r'[^\w\s-]', '', video_title.replace(' ', '_'))[:50]
            filename = f"{safe_title}_{video_id}_speech_transcript.txt" if safe_title else f"{video_id}_speech_transcript.txt"
            
            # 자막 폴더 생성
            os.makedirs('transcripts', exist_ok=True)
            file_path = f'transcripts/{filename}'
            
            # 파일 저장
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"영상 제목: {video_title}\n")
                f.write(f"영상 ID: {video_id}\n")
                f.write(f"생성 방법: 음성 인식 (Whisper)\n")
                f.write(f"감지된 언어: {detected_language}\n")
                f.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 50 + "\n\n")
                f.write(transcript_text)
            
            self.download_stats['speech_to_text'] += 1
            
            return {
                'success': True,
                'file_path': file_path,
                'language': f"{detected_language} (음성 인식)",
                'text': transcript_text,
                'filename': filename,
                'method': 'speech_recognition'
            }
            
        except Exception as e:
            self.download_stats['failed'] += 1
            return {'success': False, 'error': str(e)}
        
        finally:
            # 임시 오디오 파일 정리
            if audio_file and os.path.exists(audio_file):
                try:
                    os.remove(audio_file)
                    print(f"🗑️ 임시 오디오 파일 삭제: {audio_file}")
                except:
                    pass
    
    def download_transcript(self, video_id, video_title="", language_codes=['ko', 'kr', 'en'], 
                          auto_generated=True, enable_speech_recognition=True):
        """
        영상의 자막 다운로드 (자막이 없으면 음성 인식 시도)
        
        Args:
            video_id (str): 영상 ID
            video_title (str): 영상 제목
            language_codes (list): 선호하는 언어 코드 순서
            auto_generated (bool): 자동 생성 자막 허용 여부
            enable_speech_recognition (bool): 음성 인식 사용 여부
            
        Returns:
            dict: 다운로드 결과 {'success': bool, 'file_path': str, 'language': str, 'text': str}
        """
        if not TRANSCRIPT_API_AVAILABLE:
            if enable_speech_recognition:
                print("⚠️ 자막 API가 없으므로 음성 인식을 시도합니다...")
                return self.generate_transcript_from_speech(video_id, video_title, language_codes[0] if language_codes else None)
            else:
                return {'success': False, 'error': 'youtube-transcript-api가 설치되지 않음'}
        
        try:
            # 1단계: 기존 자막 다운로드 시도
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            selected_transcript = None
            selected_language = None
            
            # 우선순위에 따라 자막 선택
            for lang_code in language_codes:
                try:
                    # 수동 자막 우선 시도
                    for transcript in transcript_list:
                        if (transcript.language_code == lang_code and 
                            not transcript.is_generated):
                            selected_transcript = transcript
                            selected_language = f"{transcript.language} (수동)"
                            break
                    
                    if selected_transcript:
                        break
                    
                    # 자동 생성 자막 시도 (허용된 경우)
                    if auto_generated:
                        for transcript in transcript_list:
                            if (transcript.language_code == lang_code and 
                                transcript.is_generated):
                                selected_transcript = transcript
                                selected_language = f"{transcript.language} (자동)"
                                break
                    
                    if selected_transcript:
                        break
                        
                except:
                    continue
            
            # 선택된 자막이 없으면 첫 번째 사용 가능한 자막 사용
            if not selected_transcript:
                for transcript in transcript_list:
                    if auto_generated or not transcript.is_generated:
                        selected_transcript = transcript
                        selected_language = f"{transcript.language} ({'자동' if transcript.is_generated else '수동'})"
                        break
            
            # 2단계: 자막이 있으면 다운로드
            if selected_transcript:
                # 자막 데이터 가져오기
                transcript_data = selected_transcript.fetch()
                
                # 텍스트 형태로 변환
                transcript_text = self.text_formatter.format_transcript(transcript_data)
                
                # 파일명 생성
                safe_title = re.sub(r'[^\w\s-]', '', video_title.replace(' ', '_'))[:50]
                filename = f"{safe_title}_{video_id}_transcript.txt" if safe_title else f"{video_id}_transcript.txt"
                
                # 자막 폴더 생성
                os.makedirs('transcripts', exist_ok=True)
                file_path = f'transcripts/{filename}'
                
                # 파일 저장
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(f"영상 제목: {video_title}\n")
                    f.write(f"영상 ID: {video_id}\n")
                    f.write(f"자막 언어: {selected_language}\n")
                    f.write(f"다운로드 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write("=" * 50 + "\n\n")
                    f.write(transcript_text)
                
                self.download_stats['success'] += 1
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'language': selected_language,
                    'text': transcript_text,
                    'filename': filename,
                    'method': 'existing_transcript'
                }
            
            # 3단계: 자막이 없으면 음성 인식 시도
            elif enable_speech_recognition:
                print(f"ℹ️ 영상 {video_id}: 사용 가능한 자막이 없어 음성 인식을 시도합니다...")
                return self.generate_transcript_from_speech(video_id, video_title, language_codes[0] if language_codes else None)
            
            else:
                self.download_stats['no_transcript'] += 1
                return {'success': False, 'error': '사용 가능한 자막이 없음 (음성 인식 비활성화)'}
            
        except Exception as e:
            # 자막 API 실패시 음성 인식 시도
            if enable_speech_recognition:
                print(f"⚠️ 자막 다운로드 실패, 음성 인식을 시도합니다: {e}")
                return self.generate_transcript_from_speech(video_id, video_title, language_codes[0] if language_codes else None)
            else:
                self.download_stats['failed'] += 1
                return {'success': False, 'error': str(e)}
    
    def download_multiple_transcripts(self, video_list, language_codes=['ko', 'kr', 'en'], 
                                    enable_speech_recognition=True):
        """
        여러 영상의 자막을 일괄 다운로드 (음성 인식 포함)
        
        Args:
            video_list (list): 영상 정보 목록 [{'id': str, 'title': str}, ...]
            language_codes (list): 선호하는 언어 코드 순서
            enable_speech_recognition (bool): 음성 인식 사용 여부
            
        Returns:
            dict: 다운로드 결과 요약
        """
        print(f"📝 {len(video_list)}개 영상의 자막 다운로드를 시작합니다...")
        if enable_speech_recognition:
            print("🤖 자막이 없는 영상은 음성 인식으로 처리됩니다.")
        
        self.download_stats = {'success': 0, 'failed': 0, 'no_transcript': 0, 'speech_to_text': 0}
        downloaded_files = []
        
        for i, video in enumerate(video_list, 1):
            print(f"   진행률: {i}/{len(video_list)} - {video.get('title', video['id'])[:30]}...", end="\r")
            
            result = self.download_transcript(
                video['id'],
                video.get('title', ''),
                language_codes,
                enable_speech_recognition=enable_speech_recognition
            )
            
            if result['success']:
                downloaded_files.append(result['file_path'])
            
        print(f"\n✅ 자막 다운로드 완료!")
        print(f"   기존 자막: {self.download_stats['success']}개")
        print(f"   음성 인식: {self.download_stats['speech_to_text']}개")
        print(f"   실패: {self.download_stats['failed']}개")
        print(f"   자막 없음: {self.download_stats['no_transcript']}개")
        
        return {
            'stats': self.download_stats,
            'files': downloaded_files
        }
    
    def create_transcript_zip(self, channel_name="", keyword=""):
        """
        다운로드된 모든 자막을 ZIP 파일로 압축
        
        Args:
            channel_name (str): 채널명 (파일명에 포함)
            keyword (str): 키워드 (파일명에 포함)
            
        Returns:
            str: ZIP 파일 경로
        """
        try:
            transcript_folder = 'transcripts'
            if not os.path.exists(transcript_folder):
                return None
            
            transcript_files = [f for f in os.listdir(transcript_folder) if f.endswith('.txt')]
            if not transcript_files:
                return None
            
            # ZIP 파일명 생성
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            safe_channel = re.sub(r'[^\w\s-]', '', channel_name.replace(' ', '_'))[:20] if channel_name else ""
            safe_keyword = re.sub(r'[^\w\s-]', '', keyword.replace(' ', '_'))[:20] if keyword else ""
            
            zip_filename = f"transcripts"
            if safe_channel:
                zip_filename += f"_{safe_channel}"
            if safe_keyword:
                zip_filename += f"_{safe_keyword}"
            zip_filename += f"_{timestamp}.zip"
            
            # ZIP 파일 생성
            with zipfile.ZipFile(zip_filename, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for filename in transcript_files:
                    file_path = os.path.join(transcript_folder, filename)
                    zipf.write(file_path, filename)
            
            print(f"📦 자막 ZIP 파일 생성: {zip_filename}")
            return zip_filename
            
        except Exception as e:
            print(f"자막 ZIP 생성 오류: {e}")
            return None
    
    def analyze_transcript_text(self, transcript_text):
        """
        자막 텍스트 간단 분석
        
        Args:
            transcript_text (str): 자막 텍스트
            
        Returns:
            dict: 분석 결과
        """
        try:
            words = transcript_text.split()
            sentences = transcript_text.split('.')
            
            analysis = {
                'total_words': len(words),
                'total_sentences': len([s for s in sentences if s.strip()]),
                'avg_words_per_sentence': len(words) / len([s for s in sentences if s.strip()]) if sentences else 0,
                'estimated_reading_time': len(words) / 200,  # 분당 200단어 기준
                'character_count': len(transcript_text)
            }
            
            return analysis
            
        except Exception as e:
            print(f"자막 분석 오류: {e}")
            return {}
    
    def get_download_stats(self):
        """다운로드 통계 반환"""
        return self.download_stats.copy()
    
    def cleanup_temp_files(self):
        """임시 파일 정리"""
        try:
            temp_dir = "temp_audio"
            if os.path.exists(temp_dir):
                for filename in os.listdir(temp_dir):
                    file_path = os.path.join(temp_dir, filename)
                    try:
                        os.remove(file_path)
                    except:
                        pass
                try:
                    os.rmdir(temp_dir)
                    print("🗑️ 임시 파일 정리 완료")
                except:
                    pass
        except Exception as e:
            print(f"임시 파일 정리 오류: {e}")
    
    def get_transcript_summary(self, transcript_files):
        """
        자막 파일들의 요약 정보 생성
        
        Args:
            transcript_files (list): 자막 파일 경로 목록
            
        Returns:
            dict: 요약 정보
        """
        try:
            total_words = 0
            total_chars = 0
            total_files = len(transcript_files)
            method_count = {'existing_transcript': 0, 'speech_recognition': 0}
            
            for file_path in transcript_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 헤더 부분 제거 (=" * 50 이후의 내용만)
                        if "=" * 50 in content:
                            actual_content = content.split("=" * 50, 1)[-1].strip()
                        else:
                            actual_content = content
                        
                        words = actual_content.split()
                        total_words += len(words)
                        total_chars += len(actual_content)
                        
                        # 생성 방법 확인
                        if "음성 인식" in content:
                            method_count['speech_recognition'] += 1
                        else:
                            method_count['existing_transcript'] += 1
            
            summary = {
                'total_files': total_files,
                'total_words': total_words,
                'total_characters': total_chars,
                'avg_words_per_file': total_words / total_files if total_files > 0 else 0,
                'existing_transcripts': method_count['existing_transcript'],
                'speech_recognition': method_count['speech_recognition'],
                'estimated_reading_time_minutes': total_words / 200  # 분당 200단어 기준
            }
            
            return summary
            
        except Exception as e:
            print(f"자막 요약 생성 오류: {e}")
            return {}
    
    def export_transcripts_to_single_file(self, transcript_files, output_filename="combined_transcripts.txt"):
        """
        여러 자막 파일을 하나의 파일로 합치기
        
        Args:
            transcript_files (list): 자막 파일 경로 목록
            output_filename (str): 출력 파일명
            
        Returns:
            str: 생성된 파일 경로
        """
        try:
            os.makedirs('transcripts', exist_ok=True)
            output_path = f'transcripts/{output_filename}'
            
            with open(output_path, 'w', encoding='utf-8') as output_file:
                output_file.write(f"통합 자막 파일\n")
                output_file.write(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                output_file.write(f"포함된 파일 수: {len(transcript_files)}\n")
                output_file.write("=" * 80 + "\n\n")
                
                for i, file_path in enumerate(transcript_files, 1):
                    if os.path.exists(file_path):
                        filename = os.path.basename(file_path)
                        output_file.write(f"\n{'=' * 80}\n")
                        output_file.write(f"파일 {i}: {filename}\n")
                        output_file.write(f"{'=' * 80}\n\n")
                        
                        with open(file_path, 'r', encoding='utf-8') as input_file:
                            content = input_file.read()
                            output_file.write(content)
                            output_file.write("\n\n")
            
            print(f"📄 통합 자막 파일 생성: {output_path}")
            return output_path
            
        except Exception as e:
            print(f"통합 파일 생성 오류: {e}")
            return None
    
    def search_in_transcripts(self, search_term, transcript_files):
        """
        자막 파일들에서 특정 단어/구문 검색
        
        Args:
            search_term (str): 검색할 단어/구문
            transcript_files (list): 검색할 자막 파일 목록
            
        Returns:
            list: 검색 결과 [{'file': str, 'matches': int, 'contexts': list}]
        """
        try:
            results = []
            search_term_lower = search_term.lower()
            
            for file_path in transcript_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                        # 실제 자막 내용만 추출 (헤더 제외)
                        if "=" * 50 in content:
                            actual_content = content.split("=" * 50, 1)[-1].strip()
                        else:
                            actual_content = content
                        
                        # 검색
                        content_lower = actual_content.lower()
                        matches = content_lower.count(search_term_lower)
                        
                        if matches > 0:
                            # 검색어 주변 문맥 추출
                            contexts = []
                            sentences = actual_content.split('.')
                            
                            for sentence in sentences:
                                if search_term_lower in sentence.lower():
                                    contexts.append(sentence.strip())
                            
                            results.append({
                                'file': os.path.basename(file_path),
                                'file_path': file_path,
                                'matches': matches,
                                'contexts': contexts[:5]  # 최대 5개 문맥
                            })
            
            # 검색 결과를 매치 수 기준으로 정렬
            results.sort(key=lambda x: x['matches'], reverse=True)
            
            return results
            
        except Exception as e:
            print(f"자막 검색 오류: {e}")
            return []