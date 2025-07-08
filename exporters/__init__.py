"""
exporters/__init__.py
Exporters 모듈의 진입점
"""

from .excel_exporter import ExcelExporter, quick_excel_export, export_comparison_report
from .thumbnail_downloader import ThumbnailDownloader, quick_thumbnail_download, download_top_performers_thumbnails, create_thumbnail_comparison_grid
from .transcript_downloader import TranscriptDownloader, quick_transcript_download, download_high_performance_transcripts, extract_transcript_keywords, compare_transcript_methods

__version__ = "3.0.0"
__all__ = [
    'ExcelExporter',
    'ThumbnailDownloader', 
    'TranscriptDownloader',
    'quick_excel_export',
    'export_comparison_report',
    'quick_thumbnail_download',
    'download_top_performers_thumbnails',
    'create_thumbnail_comparison_grid',
    'quick_transcript_download',
    'download_high_performance_transcripts',
    'extract_transcript_keywords',
    'compare_transcript_methods'
]

# 편의 함수들
def create_export_suite(output_base_dir="exports"):
    """
    내보내기 도구 세트 생성
    
    Args:
        output_base_dir (str): 기본 출력 디렉토리
        
    Returns:
        dict: 내보내기 도구들이 담긴 딕셔너리
    """
    import os
    
    # 하위 디렉토리 생성
    excel_dir = os.path.join(output_base_dir, "excel")
    thumbnails_dir = os.path.join(output_base_dir, "thumbnails")  
    transcripts_dir = os.path.join(output_base_dir, "transcripts")
    
    return {
        'excel_exporter': ExcelExporter(),
        'thumbnail_downloader': ThumbnailDownloader(thumbnails_dir),
        'transcript_downloader': TranscriptDownloader(transcripts_dir),
        'directories': {
            'base': output_base_dir,
            'excel': excel_dir,
            'thumbnails': thumbnails_dir,
            'transcripts': transcripts_dir
        }
    }

def export_complete_analysis(videos_data, analysis_settings, include_thumbnails=True, 
                           include_transcripts=False, output_dir="complete_export"):
    """
    완전한 분석 결과 내보내기 (엑셀 + 썸네일 + 대본)
    
    Args:
        videos_data (list): 영상 데이터 목록
        analysis_settings (dict): 분석 설정
        include_thumbnails (bool): 썸네일 포함 여부
        include_transcripts (bool): 대본 포함 여부
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 내보내기 결과
    """
    import os
    from datetime import datetime
    
    # 출력 디렉토리 생성
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    full_output_dir = f"{output_dir}_{timestamp}"
    os.makedirs(full_output_dir, exist_ok=True)
    
    results = {
        'output_directory': full_output_dir,
        'total_videos': len(videos_data),
        'exports': {}
    }
    
    print(f"📦 완전한 분석 결과 내보내기 시작")
    print(f"   대상: {len(videos_data)}개 영상")
    print(f"   출력: {full_output_dir}")
    
    # 1. 엑셀 리포트 생성
    print("\n📊 1단계: 엑셀 리포트 생성...")
    try:
        excel_filename = os.path.join(full_output_dir, "analysis_report.xlsx")
        exporter = ExcelExporter(excel_filename)
        excel_result = exporter.export_video_analysis(videos_data, analysis_settings)
        
        results['exports']['excel'] = {
            'success': True,
            'filepath': excel_result,
            'file_size': os.path.getsize(excel_result) if os.path.exists(excel_result) else 0
        }
        print(f"✅ 엑셀 리포트 완료: {excel_result}")
        
    except Exception as e:
        results['exports']['excel'] = {'success': False, 'error': str(e)}
        print(f"❌ 엑셀 리포트 실패: {e}")
    
    # 2. 썸네일 다운로드 (선택사항)
    if include_thumbnails:
        print("\n🖼️ 2단계: 썸네일 다운로드...")
        try:
            thumbnails_dir = os.path.join(full_output_dir, "thumbnails")
            downloader = ThumbnailDownloader(thumbnails_dir)
            
            thumbnail_result = downloader.download_multiple_thumbnails(
                videos_data, quality='high', add_rank=True, create_zip=True
            )
            
            results['exports']['thumbnails'] = thumbnail_result
            print(f"✅ 썸네일 다운로드 완료: {thumbnail_result['summary']['successful_downloads']}개")
            
        except Exception as e:
            results['exports']['thumbnails'] = {'success': False, 'error': str(e)}
            print(f"❌ 썸네일 다운로드 실패: {e}")
    
    # 3. 대본 다운로드 (선택사항)
    if include_transcripts:
        print("\n📝 3단계: 대본 다운로드...")
        try:
            transcripts_dir = os.path.join(full_output_dir, "transcripts")
            transcript_downloader = TranscriptDownloader(transcripts_dir)
            
            video_ids = [video.get('id', '') for video in videos_data if video.get('id')]
            transcript_result = transcript_downloader.download_multiple_transcripts(
                video_ids, languages=['ko', 'en'], max_workers=2
            )
            
            results['exports']['transcripts'] = transcript_result
            print(f"✅ 대본 다운로드 완료: {transcript_result['summary']['successful_downloads']}개")
            
        except Exception as e:
            results['exports']['transcripts'] = {'success': False, 'error': str(e)}
            print(f"❌ 대본 다운로드 실패: {e}")
    
    # 4. 요약 보고서 생성
    print("\n📋 4단계: 요약 보고서 생성...")
    summary_report = _create_export_summary(results, analysis_settings)
    summary_path = os.path.join(full_output_dir, "export_summary.txt")
    
    try:
        with open(summary_path, 'w', encoding='utf-8') as f:
            f.write(summary_report)
        
        results['summary_report'] = summary_path
        print(f"✅ 요약 보고서 완료: {summary_path}")
        
    except Exception as e:
        print(f"❌ 요약 보고서 실패: {e}")
    
    print(f"\n🎉 완전한 내보내기 완료!")
    print(f"   출력 디렉토리: {full_output_dir}")
    
    return results

def export_top_performers(videos_data, top_count=10, min_outlier_score=2.0, 
                         output_dir="top_performers"):
    """
    상위 성과 영상들만 선별해서 내보내기
    
    Args:
        videos_data (list): 영상 데이터 목록
        top_count (int): 상위 개수
        min_outlier_score (float): 최소 Outlier Score
        output_dir (str): 출력 디렉토리
        
    Returns:
        dict: 내보내기 결과
    """
    print(f"🏆 상위 성과 영상 내보내기 시작")
    print(f"   기준: 상위 {top_count}개 또는 Outlier Score {min_outlier_score}x 이상")
    
    # 고성과 영상 필터링
    high_performers = []
    
    for video in videos_data:
        outlier_score = video.get('analysis', {}).get('outlier_score', 0)
        if outlier_score >= min_outlier_score:
            high_performers.append(video)
    
    # 상위 개수만큼 선택 (Outlier Score 기준 정렬)
    high_performers.sort(key=lambda x: x.get('analysis', {}).get('outlier_score', 0), reverse=True)
    selected_videos = high_performers[:top_count]
    
    if not selected_videos:
        return {
            'success': False, 
            'error': f'조건에 맞는 영상이 없습니다 (Outlier Score >= {min_outlier_score})'
        }
    
    print(f"   선별된 영상: {len(selected_videos)}개")
    
    # 분석 설정 업데이트
    top_analysis_settings = {
        'mode': 'top_performers',
        'mode_name': f'상위 {len(selected_videos)}개 고성과 영상',
        'filter_criteria': f'Outlier Score >= {min_outlier_score}x',
        'total_analyzed': len(videos_data),
        'selected_count': len(selected_videos)
    }
    
    # 완전한 내보내기 실행
    return export_complete_analysis(
        selected_videos, 
        top_analysis_settings, 
        include_thumbnails=True, 
        include_transcripts=True,
        output_dir=output_dir
    )

def _create_export_summary(results, analysis_settings):
    """내보내기 요약 보고서 생성"""
    from datetime import datetime
    
    summary = []
    summary.append("=" * 60)
    summary.append("YouTube 트렌드 분석 내보내기 요약 보고서")
    summary.append("=" * 60)
    summary.append(f"생성 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    summary.append(f"분석 영상 수: {results['total_videos']}개")
    summary.append(f"출력 디렉토리: {results['output_directory']}")
    summary.append("")
    
    # 분석 설정 정보
    summary.append("📊 분석 설정")
    summary.append("-" * 30)
    for key, value in analysis_settings.items():
        if key.endswith('_name') or key in ['mode', 'keyword', 'region']:
            summary.append(f"  {key}: {value}")
    summary.append("")
    
    # 내보내기 결과
    summary.append("📦 내보내기 결과")
    summary.append("-" * 30)
    
    for export_type, export_result in results['exports'].items():
        if export_result.get('success', False):
            summary.append(f"✅ {export_type.upper()}: 성공")
            
            if export_type == 'excel':
                file_size = export_result.get('file_size', 0) / 1024 / 1024  # MB
                summary.append(f"    파일 크기: {file_size:.1f} MB")
                
            elif export_type == 'thumbnails':
                thumb_summary = export_result.get('summary', {})
                summary.append(f"    성공: {thumb_summary.get('successful_downloads', 0)}개")
                summary.append(f"    실패: {thumb_summary.get('failed_downloads', 0)}개")
                summary.append(f"    성공률: {thumb_summary.get('success_rate', 0):.1f}%")
                
            elif export_type == 'transcripts':
                trans_summary = export_result.get('summary', {})
                summary.append(f"    성공: {trans_summary.get('successful_downloads', 0)}개")
                summary.append(f"    실패: {trans_summary.get('failed_downloads', 0)}개")
                summary.append(f"    성공률: {trans_summary.get('success_rate', 0):.1f}%")
                
                # 방법별 통계
                method_stats = export_result.get('method_statistics', {})
                if method_stats:
                    summary.append("    사용된 방법:")
                    for method, count in method_stats.items():
                        summary.append(f"      {method}: {count}개")
        else:
            summary.append(f"❌ {export_type.upper()}: 실패")
            summary.append(f"    오류: {export_result.get('error', 'Unknown error')}")
        
        summary.append("")
    
    # 파일 목록
    summary.append("📁 생성된 파일 목록")
    summary.append("-" * 30)
    
    import os
    try:
        for root, dirs, files in os.walk(results['output_directory']):
            level = root.replace(results['output_directory'], '').count(os.sep)
            indent = ' ' * 2 * level
            summary.append(f"{indent}{os.path.basename(root)}/")
            
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                file_path = os.path.join(root, file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                summary.append(f"{sub_indent}{file} ({file_size:.1f} KB)")
    except Exception as e:
        summary.append(f"파일 목록 생성 오류: {e}")
    
    summary.append("")
    summary.append("=" * 60)
    summary.append("보고서 끝")
    summary.append("=" * 60)
    
    return '\n'.join(summary)