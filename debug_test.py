"""
키워드 검색 문제 디버깅 테스트 스크립트
GUI 실행 전에 이 스크립트를 실행해서 문제를 진단하세요.
"""

import sys
import os

def test_imports():
    """필수 라이브러리 import 테스트"""
    print("📦 라이브러리 import 테스트...")
    
    missing_libraries = []
    
    try:
        import config
        print("✅ config.py 로드 성공")
    except ImportError:
        missing_libraries.append("config.py 파일이 없습니다")
    
    try:
        from googleapiclient.discovery import build
        print("✅ google-api-python-client 로드 성공")
    except ImportError:
        missing_libraries.append("google-api-python-client")
    
    try:
        import pandas
        print("✅ pandas 로드 성공")
    except ImportError:
        missing_libraries.append("pandas")
    
    try:
        import requests
        print("✅ requests 로드 성공")
    except ImportError:
        missing_libraries.append("requests")
    
    if missing_libraries:
        print(f"❌ 누락된 라이브러리: {missing_libraries}")
        print("설치 명령어: pip install " + " ".join(missing_libraries))
        return False
    
    print("✅ 모든 필수 라이브러리 로드 성공!")
    return True

def test_api_key():
    """API 키 설정 테스트"""
    print("\n🔑 API 키 설정 테스트...")
    
    try:
        import config
        
        if not hasattr(config, 'DEVELOPER_KEY'):
            print("❌ config.py에 DEVELOPER_KEY가 설정되지 않았습니다")
            return False
        
        api_key = config.DEVELOPER_KEY
        
        if not api_key or api_key == "YOUR_YOUTUBE_API_KEY_HERE":
            print("❌ API 키가 설정되지 않았습니다")
            print("💡 해결방법: config.py에서 DEVELOPER_KEY를 실제 YouTube API 키로 변경하세요")
            return False
        
        print(f"✅ API 키 설정됨: {api_key[:10]}...")
        return True
        
    except Exception as e:
        print(f"❌ API 키 확인 오류: {e}")
        return False

def test_youtube_api_connection():
    """YouTube API 연결 테스트"""
    print("\n🌐 YouTube API 연결 테스트...")
    
    try:
        import config
        from googleapiclient.discovery import build
        
        youtube = build('youtube', 'v3', developerKey=config.DEVELOPER_KEY)
        
        # 간단한 API 호출
        request = youtube.videos().list(
            part='snippet',
            chart='mostPopular',
            regionCode='KR',
            maxResults=1
        )
        response = request.execute()
        
        items = response.get('items', [])
        if items:
            print(f"✅ YouTube API 연결 성공! 테스트 영상: {items[0]['snippet']['title']}")
            return True
        else:
            print("⚠️ API 연결은 되지만 결과가 없습니다")
            return False
            
    except Exception as e:
        print(f"❌ YouTube API 연결 실패: {e}")
        
        error_str = str(e)
        if "keyInvalid" in error_str:
            print("💡 원인: 잘못된 API 키")
            print("💡 해결방법: Google Cloud Console에서 새 API 키를 발급받으세요")
        elif "quotaExceeded" in error_str:
            print("💡 원인: API 할당량 초과")
            print("💡 해결방법: 내일 다시 시도하거나 새 Google Cloud 프로젝트를 만드세요")
        elif "blocked" in error_str:
            print("💡 원인: API 키가 차단됨")
            print("💡 해결방법: Google Cloud Console에서 API 키 제한사항을 확인하세요")
        
        return False

def test_keyword_search():
    """키워드 검색 테스트"""
    print("\n🔍 키워드 검색 테스트...")
    
    try:
        from youtube_api import YouTubeAPIClient
        
        # API 클라이언트 초기화
        api_client = YouTubeAPIClient()
        
        # 간단한 키워드로 검색 테스트
        test_keyword = "BTS"
        print(f"테스트 키워드: '{test_keyword}'")
        
        # 검색 실행
        results = api_client.search_videos_by_keyword(
            keyword=test_keyword,
            region_code="KR",
            max_results=5,  # 소량 테스트
            period_days=30
        )
        
        if results:
            print(f"✅ 키워드 검색 성공! {len(results)}개 영상 발견")
            for i, video in enumerate(results[:3], 1):
                title = video['snippet']['title'][:50]
                views = video['statistics'].get('viewCount', 0)
                print(f"   {i}. {title} | {views:,} 조회수")
            return True
        else:
            print("❌ 키워드 검색 결과가 없습니다")
            print("💡 해결방법:")
            print("   1. 다른 키워드를 시도해보세요")
            print("   2. 검색 기간을 늘려보세요")
            print("   3. 필터 조건을 완화해보세요")
            return False
            
    except Exception as e:
        print(f"❌ 키워드 검색 테스트 실패: {e}")
        import traceback
        print("상세 오류:")
        print(traceback.format_exc())
        return False

def test_network_connection():
    """네트워크 연결 테스트"""
    print("\n🌍 네트워크 연결 테스트...")
    
    try:
        import requests
        
        # Google API 서버 연결 테스트
        response = requests.get("https://www.googleapis.com", timeout=10)
        if response.status_code == 200:
            print("✅ Google API 서버 연결 성공")
        else:
            print(f"⚠️ Google API 서버 응답 이상: {response.status_code}")
        
        # YouTube 연결 테스트
        response = requests.get("https://www.youtube.com", timeout=10)
        if response.status_code == 200:
            print("✅ YouTube 서버 연결 성공")
            return True
        else:
            print(f"⚠️ YouTube 서버 응답 이상: {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        print("❌ 네트워크 연결 시간초과")
        print("💡 해결방법: 인터넷 연결을 확인하세요")
        return False
    except Exception as e:
        print(f"❌ 네트워크 연결 오류: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("🔧 YouTube 트렌드 분석기 문제 진단 시작")
    print("=" * 60)
    
    tests = [
        ("라이브러리 import", test_imports),
        ("API 키 설정", test_api_key),
        ("네트워크 연결", test_network_connection),
        ("YouTube API 연결", test_youtube_api_connection),
        ("키워드 검색", test_keyword_search)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 테스트 중 오류: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 60)
    print("🏁 테스트 결과 요약")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ 통과" if result else "❌ 실패"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n총 테스트: {len(results)}개 | 통과: {passed}개 | 실패: {failed}개")
    
    if failed == 0:
        print("\n🎉 모든 테스트가 통과했습니다! GUI를 실행해보세요.")
    else:
        print(f"\n⚠️ {failed}개 테스트가 실패했습니다. 위의 해결방법을 참고하세요.")
        
        print("\n📋 일반적인 해결방법:")
        print("1. config.py에서 YouTube API 키 확인")
        print("2. 필수 라이브러리 설치: pip install -r requirements.txt")
        print("3. 인터넷 연결 상태 확인")
        print("4. Google Cloud Console에서 YouTube Data API v3 활성화 확인")
        print("5. API 할당량 확인 (일일 10,000 단위)")

if __name__ == "__main__":
    main()