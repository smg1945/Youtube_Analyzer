"""
YouTube 트렌드 분석기 최종 테스트 스크립트
모든 기능이 제대로 작동하는지 확인합니다.
"""

import sys
import os
from datetime import datetime
import traceback

def test_all_functions():
    """모든 기능 테스트"""
    print("🔧 YouTube 트렌드 분석기 최종 테스트 시작")
    print("=" * 60)
    
    test_results = []
    
    # 1. 모듈 import 테스트
    print("\n1️⃣ 모듈 Import 테스트")
    try:
        import config
        from youtube_api import YouTubeAPIClient
        from data_analyzer import DataAnalyzer
        from excel_generator import ExcelGenerator
        print("✅ 모든 핵심 모듈 import 성공")
        test_results.append(("모듈 Import", True))
    except Exception as e:
        print(f"❌ 모듈 import 실패: {e}")
        test_results.append(("모듈 Import", False))
        return test_results
    
    # 2. API 키 및 연결 테스트
    print("\n2️⃣ API 키 및 연결 테스트")
    try:
        api_client = YouTubeAPIClient()
        if api_client.test_api_connection():
            print("✅ YouTube API 연결 성공")
            test_results.append(("API 연결", True))
        else:
            print("❌ YouTube API 연결 실패")
            test_results.append(("API 연결", False))
    except Exception as e:
        print(f"❌ API 테스트 실패: {e}")
        test_results.append(("API 연결", False))
    
    # 3. 키워드 검색 테스트 (롱폼)
    print("\n3️⃣ 키워드 검색 테스트 (롱폼)")
    try:
        results = api_client.search_videos_by_keyword(
            keyword="요리",
            region_code="KR",
            max_results=10,
            video_type="long",  # 롱폼만
            period_days=30
        )
        
        if results:
            long_count = sum(1 for v in results if v.get('analysis', {}).get('video_type') == '롱폼')
            shorts_count = sum(1 for v in results if v.get('analysis', {}).get('video_type') == '쇼츠')
            
            print(f"✅ 검색 성공: {len(results)}개 영상")
            print(f"   롱폼: {long_count}개, 쇼츠: {shorts_count}개")
            
            if shorts_count == 0:
                print("✅ 롱폼 필터링 정상 작동")
                test_results.append(("롱폼 필터링", True))
            else:
                print("⚠️ 롱폼 필터링에 일부 쇼츠 포함됨")
                test_results.append(("롱폼 필터링", False))
        else:
            print("❌ 검색 결과 없음")
            test_results.append(("롱폼 필터링", False))
    except Exception as e:
        print(f"❌ 롱폼 검색 테스트 실패: {e}")
        test_results.append(("롱폼 필터링", False))
    
    # 4. 키워드 검색 테스트 (쇼츠)
    print("\n4️⃣ 키워드 검색 테스트 (쇼츠)")
    try:
        results = api_client.search_videos_by_keyword(
            keyword="요리",
            region_code="KR",
            max_results=10,
            video_type="shorts",  # 쇼츠만
            period_days=30
        )
        
        if results:
            long_count = sum(1 for v in results if v.get('analysis', {}).get('video_type') == '롱폼')
            shorts_count = sum(1 for v in results if v.get('analysis', {}).get('video_type') == '쇼츠')
            
            print(f"✅ 검색 성공: {len(results)}개 영상")
            print(f"   롱폼: {long_count}개, 쇼츠: {shorts_count}개")
            
            if long_count == 0:
                print("✅ 쇼츠 필터링 정상 작동")
                test_results.append(("쇼츠 필터링", True))
            else:
                print("⚠️ 쇼츠 필터링에 일부 롱폼 포함됨")
                test_results.append(("쇼츠 필터링", False))
        else:
            print("❌ 쇼츠 검색 결과 없음")
            test_results.append(("쇼츠 필터링", False))
    except Exception as e:
        print(f"❌ 쇼츠 검색 테스트 실패: {e}")
        test_results.append(("쇼츠 필터링", False))
    
    # 5. 데이터 분석 테스트
    print("\n5️⃣ 데이터 분석 테스트")
    try:
        analyzer = DataAnalyzer(language="ko")
        
        # 키워드 추출 테스트
        keywords = analyzer.extract_keywords_from_title("맛있는 집밥 요리 레시피 추천")
        print(f"✅ 키워드 추출: {keywords}")
        
        # Outlier Score 계산 테스트
        video_stats = {'viewCount': '100000', 'likeCount': '1000', 'commentCount': '100'}
        channel_stats = {'avg_views': 50000, 'avg_likes': 500, 'avg_comments': 50}
        outlier_score = analyzer.calculate_outlier_score(video_stats, channel_stats)
        print(f"✅ Outlier Score 계산: {outlier_score}")
        
        test_results.append(("데이터 분석", True))
    except Exception as e:
        print(f"❌ 데이터 분석 테스트 실패: {e}")
        test_results.append(("데이터 분석", False))
    
    # 6. 엑셀 생성 테스트
    print("\n6️⃣ 엑셀 생성 테스트")
    try:
        if 'results' in locals() and results:
            excel_generator = ExcelGenerator("test_output.xlsx")
            
            # 가상의 분석 설정
            test_settings = {
                'mode': 'keyword',
                'mode_name': '키워드 검색',
                'keyword': '요리',
                'region_name': '한국',
                'video_type_name': '롱폼',
                'period_days': 30
            }
            
            excel_generator.create_excel_file(results, test_settings)
            
            if os.path.exists("test_output.xlsx"):
                print("✅ 엑셀 파일 생성 성공")
                print(f"   파일 크기: {os.path.getsize('test_output.xlsx')} bytes")
                test_results.append(("엑셀 생성", True))
                
                # 테스트 파일 삭제
                os.remove("test_output.xlsx")
            else:
                print("❌ 엑셀 파일 생성 실패")
                test_results.append(("엑셀 생성", False))
        else:
            print("⚠️ 테스트할 데이터가 없어 엑셀 생성 테스트 건너뛰기")
            test_results.append(("엑셀 생성", "N/A"))
    except Exception as e:
        print(f"❌ 엑셀 생성 테스트 실패: {e}")
        test_results.append(("엑셀 생성", False))
    
    # 7. 썸네일 다운로드 기능 테스트
    print("\n7️⃣ 썸네일 다운로드 기능 테스트")
    try:
        if 'results' in locals() and results:
            test_video = results[0]
            thumbnail_url = api_client.get_best_thumbnail_url(test_video['snippet']['thumbnails'])
            
            if thumbnail_url:
                print(f"✅ 썸네일 URL 추출 성공: {thumbnail_url[:50]}...")
                test_results.append(("썸네일 기능", True))
            else:
                print("❌ 썸네일 URL 추출 실패")
                test_results.append(("썸네일 기능", False))
        else:
            print("⚠️ 테스트할 데이터가 없어 썸네일 테스트 건너뛰기")
            test_results.append(("썸네일 기능", "N/A"))
    except Exception as e:
        print(f"❌ 썸네일 기능 테스트 실패: {e}")
        test_results.append(("썸네일 기능", False))
    
    # 8. 채널 분석 기능 테스트
    print("\n8️⃣ 채널 분석 기능 테스트")
    try:
        if 'results' in locals() and results:
            test_video = results[0]
            channel_id = test_video['snippet']['channelId']
            
            channel_videos = api_client.get_channel_videos(channel_id, max_results=5)
            
            if channel_videos:
                print(f"✅ 채널 영상 목록 가져오기 성공: {len(channel_videos)}개")
                test_results.append(("채널 분석", True))
            else:
                print("❌ 채널 영상 목록 가져오기 실패")
                test_results.append(("채널 분석", False))
        else:
            print("⚠️ 테스트할 데이터가 없어 채널 분석 테스트 건너뛰기")
            test_results.append(("채널 분석", "N/A"))
    except Exception as e:
        print(f"❌ 채널 분석 테스트 실패: {e}")
        test_results.append(("채널 분석", False))
    
    # 테스트 결과 요약
    print("\n" + "=" * 60)
    print("📊 테스트 결과 요약")
    print("=" * 60)
    
    passed = sum(1 for _, result in test_results if result is True)
    failed = sum(1 for _, result in test_results if result is False)
    na = sum(1 for _, result in test_results if result == "N/A")
    
    for test_name, result in test_results:
        if result is True:
            status = "✅ 통과"
        elif result is False:
            status = "❌ 실패"
        else:
            status = "⚠️ 해당없음"
        
        print(f"{test_name:15} : {status}")
    
    print(f"\n총 테스트: {len(test_results)}개")
    print(f"통과: {passed}개")
    print(f"실패: {failed}개")
    print(f"해당없음: {na}개")
    
    # 성공률 계산
    total_applicable = passed + failed
    if total_applicable > 0:
        success_rate = (passed / total_applicable) * 100
        print(f"성공률: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("\n🎉 대부분의 기능이 정상 작동합니다!")
        elif success_rate >= 60:
            print("\n⚠️ 일부 기능에 문제가 있습니다. 실패한 테스트를 확인해주세요.")
        else:
            print("\n❌ 심각한 문제가 있습니다. 설정을 다시 확인해주세요.")
    
    return test_results

def print_troubleshooting_guide():
    """문제 해결 가이드 출력"""
    print("\n" + "=" * 60)
    print("🔧 문제 해결 가이드")
    print("=" * 60)
    
    print("\n❌ API 연결 실패시:")
    print("   1. config.py에서 YouTube API 키 확인")
    print("   2. Google Cloud Console에서 YouTube Data API v3 활성화 확인")
    print("   3. API 키 할당량 확인 (일일 10,000 단위)")
    
    print("\n❌ 필터링 실패시:")
    print("   1. 검색 조건을 완화해보세요 (필터 해제)")
    print("   2. 다른 키워드로 테스트")
    print("   3. 검색 기간을 늘려보세요 (90일)")
    
    print("\n❌ 엑셀/썸네일 기능 실패시:")
    print("   1. 필요한 라이브러리 설치: pip install openpyxl xlsxwriter pillow")
    print("   2. 파일 쓰기 권한 확인")
    print("   3. 충분한 디스크 공간 확인")
    
    print("\n💡 성능 최적화:")
    print("   1. 경량 모드 사용으로 API 사용량 90% 절약")
    print("   2. 첫 실행시에는 적은 수의 영상으로 테스트")
    print("   3. 필터 조건을 점진적으로 적용")

def main():
    """메인 실행 함수"""
    try:
        test_results = test_all_functions()
        print_troubleshooting_guide()
        
        # 결과 파일 저장
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        result_file = f"test_results_{timestamp}.txt"
        
        with open(result_file, 'w', encoding='utf-8') as f:
            f.write(f"YouTube 트렌드 분석기 테스트 결과\n")
            f.write(f"테스트 일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write("=" * 50 + "\n\n")
            
            for test_name, result in test_results:
                status = "통과" if result is True else "실패" if result is False else "해당없음"
                f.write(f"{test_name}: {status}\n")
        
        print(f"\n📄 테스트 결과가 {result_file}에 저장되었습니다.")
        
    except Exception as e:
        print(f"\n❌ 테스트 실행 중 전체 오류: {e}")
        print("\n상세 오류 정보:")
        print(traceback.format_exc())

if __name__ == "__main__":
    main()