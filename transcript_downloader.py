"""
YouTube 영상 대본 다운로드 모듈
"""

import os
import re
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api.formatters import TextFormatter


class TranscriptDownloader:
    def __init__(self):
        self.formatter = TextFormatter()
        self.download_dir = "transcripts"
        
        # 다운로드 폴더 생성
        os.makedirs(self.download_dir, exist_ok=True)
    
    def download_transcript(self, video_id, languages=['ko', 'en']):
        """
        YouTube 영상 대본 다운로드
        
        Args:
            video_id (str): YouTube 영상 ID
            languages (list): 선호 언어 목록
            
        Returns:
            str: 저장된 파일 경로
        """
        try:
            # 대본 가져오기
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 선호 언어로 대본 찾기
            transcript = None
            for lang in languages:
                try:
                    transcript = transcript_list.find_transcript([lang])
                    break
                except:
                    continue
            
            # 자동 생성 대본도 시도
            if not transcript:
                try:
                    transcript = transcript_list.find_generated_transcript(languages)
                except:
                    # 영어 자동 생성 시도
                    transcript = transcript_list.find_generated_transcript(['en'])
            
            if transcript:
                # 대본 내용 가져오기
                transcript_data = transcript.fetch()
                
                # 텍스트 포맷팅
                formatted_text = self.formatter.format_transcript(transcript_data)
                
                # 파일명 생성
                safe_filename = self._make_safe_filename(video_id)
                filepath = os.path.join(self.download_dir, f"{safe_filename}.txt")
                
                # 파일 저장
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(f"YouTube Video ID: {video_id}\n")
                    f.write(f"Language: {transcript.language}\n")
                    f.write(f"Generated: {'Yes' if transcript.is_generated else 'No'}\n")
                    f.write("-" * 50 + "\n\n")
                    f.write(formatted_text)
                
                return filepath
            else:
                raise Exception("대본을 찾을 수 없습니다.")
                
        except Exception as e:
            raise Exception(f"대본 다운로드 실패: {str(e)}")
    
    def download_multiple_transcripts(self, video_ids, languages=['ko', 'en']):
        """
        여러 영상의 대본 일괄 다운로드
        
        Args:
            video_ids (list): YouTube 영상 ID 목록
            languages (list): 선호 언어 목록
            
        Returns:
            dict: 결과 정보
        """
        results = {
            'success': [],
            'failed': [],
            'total': len(video_ids)
        }
        
        for video_id in video_ids:
            try:
                filepath = self.download_transcript(video_id, languages)
                results['success'].append({
                    'video_id': video_id,
                    'filepath': filepath
                })
            except Exception as e:
                results['failed'].append({
                    'video_id': video_id,
                    'error': str(e)
                })
        
        return results
    
    def _make_safe_filename(self, video_id):
        """안전한 파일명 생성"""
        # 특수문자 제거
        safe_name = re.sub(r'[^\w\s-]', '', video_id)
        safe_name = re.sub(r'[-\s]+', '-', safe_name)
        
        # 타임스탬프 추가
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        return f"transcript_{safe_name}_{timestamp}"
    
    def get_available_languages(self, video_id):
        """
        사용 가능한 대본 언어 목록 가져오기
        
        Args:
            video_id (str): YouTube 영상 ID
            
        Returns:
            list: 사용 가능한 언어 코드 목록
        """
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            languages = []
            for transcript in transcript_list:
                languages.append({
                    'code': transcript.language_code,
                    'name': transcript.language,
                    'is_generated': transcript.is_generated
                })
            
            return languages
            
        except Exception as e:
            return []


# 사용 예시
if __name__ == "__main__":
    downloader = TranscriptDownloader()
    
    # 단일 영상 대본 다운로드
    try:
        video_id = "dQw4w9WgXcQ"  # 예시 영상 ID
        filepath = downloader.download_transcript(video_id)
        print(f"대본 저장됨: {filepath}")
    except Exception as e:
        print(f"오류: {e}")