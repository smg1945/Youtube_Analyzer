"""
YouTube 트렌드 키워드 분석기 - 현실적 구현
실제로 구현 가능한 방법으로 YouTube 트렌드를 분석합니다.
"""

import os
import re
from datetime import datetime, timedelta
from collections import Counter, defaultdict
import pandas as pd
from googleapiclient.discovery import build
import matplotlib.pyplot as plt
import seaborn as sns
from konlpy.tag import Okt  # 한국어 키워드 추출용

class YouTubeTrendKeywordAnalyzer:
    def __init__(self, api_key):
        self.youtube = build('youtube', 'v3', developerKey=api_key)
        self.okt = Okt()  # 한국어 형태소 분석기
        
    def get_trending_videos(self, region_code='KR', max_results=200):
        """인기 급상승 동영상 수집"""
        videos = []
        
        # 1. 인기 동영상 (mostPopular)
        request = self.youtube.videos().list(
            part='snippet,statistics,contentDetails',
            chart='mostPopular',
            regionCode=region_code,
            maxResults=50
        )
        response = request.execute()
        videos.extend(response.get('items', []))
        
        # 2. 카테고리별 인기 동영상
        categories = ['10', '20', '22', '23', '24']  # 음악, 게임, 사람/블로그, 코미디, 엔터
        for category_id in categories:
            try:
                request = self.youtube.videos().list(
                    part='snippet,statistics',
                    chart='mostPopular',
                    regionCode=region_code,
                    videoCategoryId=category_id,
                    maxResults=20
                )
                response = request.execute()
                videos.extend(response.get('items', []))
            except:
                continue
        
        # 3. 최근 24시간 내 업로드된 인기 영상
        published_after = (datetime.now() - timedelta(days=1)).isoformat() + 'Z'
        search_request = self.youtube.search().list(
            part='snippet',
            type='video',
            order='viewCount',
            publishedAfter=published_after,
            regionCode=region_code,
            maxResults=50
        )
        search_response = search_request.execute()
        
        # 검색 결과의 상세 정보 가져오기
        video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]
        if video_ids:
            details_request = self.youtube.videos().list(
                part='snippet,statistics',
                id=','.join(video_ids)
            )
            details_response = details_request.execute()
            videos.extend(details_response.get('items', []))
        
        return videos
    
    def extract_keywords_from_videos(self, videos):
        """동영상 메타데이터에서 키워드 추출"""
        all_keywords = []
        keyword_stats = defaultdict(lambda: {
            'count': 0,
            'total_views': 0,
            'avg_views': 0,
            'videos': []
        })
        
        for video in videos:
            # 제목, 태그, 설명에서 키워드 추출
            title = video['snippet']['title']
            tags = video['snippet'].get('tags', [])
            description = video['snippet'].get('description', '')[:200]
            views = int(video['statistics'].get('viewCount', 0))
            
            # 1. 제목에서 키워드 추출
            title_keywords = self._extract_keywords_from_text(title)
            
            # 2. 태그 정제
            clean_tags = [self._clean_keyword(tag) for tag in tags[:10]]
            
            # 3. 설명에서 해시태그 추출
            hashtags = re.findall(r'#(\w+)', description)
            
            # 모든 키워드 통합
            video_keywords = set(title_keywords + clean_tags + hashtags)
            
            # 통계 업데이트
            for keyword in video_keywords:
                if len(keyword) >= 2:  # 2글자 이상만
                    keyword_stats[keyword]['count'] += 1
                    keyword_stats[keyword]['total_views'] += views
                    keyword_stats[keyword]['videos'].append({
                        'title': title,
                        'views': views,
                        'channel': video['snippet']['channelTitle']
                    })
        
        # 평균 조회수 계산
        for keyword, stats in keyword_stats.items():
            stats['avg_views'] = stats['total_views'] // stats['count']
        
        return keyword_stats
    
    def _extract_keywords_from_text(self, text):
        """텍스트에서 핵심 키워드 추출"""
        # 특수문자 제거
        clean_text = re.sub(r'[^\w\s]', ' ', text)
        
        # 한국어 키워드 추출
        if any(ord('가') <= ord(char) <= ord('힣') for char in text):
            nouns = self.okt.nouns(clean_text)
            keywords = [word for word in nouns if len(word) >= 2]
        else:
            # 영어 키워드 추출
            words = clean_text.lower().split()
            stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for'}
            keywords = [word for word in words if len(word) > 3 and word not in stopwords]
        
        return keywords[:5]  # 상위 5개만
    
    def _clean_keyword(self, keyword):
        """키워드 정제"""
        # 소문자 변환, 특수문자 제거
        keyword = re.sub(r'[^\w\s가-힣]', '', keyword.lower())
        return keyword.strip()
    
    def analyze_trend_velocity(self, keyword_stats):
        """트렌드 속도 분석 (급상승 지표)"""
        trend_scores = {}
        
        for keyword, stats in keyword_stats.items():
            # 트렌드 점수 = (등장 빈도 × 평균 조회수) / 1000000
            trend_score = (stats['count'] * stats['avg_views']) / 1000000
            trend_scores[keyword] = {
                'score': trend_score,
                'frequency': stats['count'],
                'avg_views': stats['avg_views'],
                'total_views': stats['total_views']
            }
        
        # 점수 기준 정렬
        sorted_trends = sorted(trend_scores.items(), 
                              key=lambda x: x[1]['score'], 
                              reverse=True)
        
        return sorted_trends
    
    def get_related_keywords(self, main_keyword, keyword_stats):
        """연관 키워드 찾기"""
        related = {}
        main_videos = keyword_stats.get(main_keyword, {}).get('videos', [])
        
        if not main_videos:
            return []
        
        # 같은 동영상에 등장한 다른 키워드 찾기
        for keyword, stats in keyword_stats.items():
            if keyword != main_keyword:
                common_videos = 0
                for video in stats['videos']:
                    if any(v['title'] == video['title'] for v in main_videos):
                        common_videos += 1
                
                if common_videos > 0:
                    related[keyword] = {
                        'common_videos': common_videos,
                        'relevance_score': common_videos / len(main_videos)
                    }
        
        # 관련도 순 정렬
        sorted_related = sorted(related.items(), 
                               key=lambda x: x[1]['relevance_score'], 
                               reverse=True)
        
        return sorted_related[:10]
    
    def generate_trend_report(self, region_code='KR', save_to_file=True):
        """트렌드 리포트 생성"""
        print("🔍 YouTube 트렌드 분석 시작...")
        
        # 1. 인기 동영상 수집
        print("📊 인기 동영상 수집 중...")
        videos = self.get_trending_videos(region_code)
        print(f"✅ {len(videos)}개 동영상 수집 완료")
        
        # 2. 키워드 추출
        print("🔤 키워드 추출 중...")
        keyword_stats = self.extract_keywords_from_videos(videos)
        print(f"✅ {len(keyword_stats)}개 고유 키워드 추출")
        
        # 3. 트렌드 분석
        print("📈 트렌드 속도 분석 중...")
        trend_results = self.analyze_trend_velocity(keyword_stats)
        
        # 4. 리포트 생성
        report = {
            'analysis_time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'region': region_code,
            'total_videos_analyzed': len(videos),
            'total_keywords_found': len(keyword_stats),
            'top_trending_keywords': []
        }
        
        # 상위 50개 트렌드 키워드
        for keyword, trend_data in trend_results[:50]:
            stats = keyword_stats[keyword]
            
            # 연관 키워드 찾기
            related = self.get_related_keywords(keyword, keyword_stats)
            
            keyword_info = {
                'rank': len(report['top_trending_keywords']) + 1,
                'keyword': keyword,
                'trend_score': round(trend_data['score'], 2),
                'frequency': trend_data['frequency'],
                'avg_views': f"{trend_data['avg_views']:,}",
                'total_views': f"{trend_data['total_views']:,}",
                'related_keywords': [k[0] for k in related[:5]],
                'top_videos': [
                    {
                        'title': v['title'][:50] + '...' if len(v['title']) > 50 else v['title'],
                        'views': f"{v['views']:,}",
                        'channel': v['channel']
                    } for v in sorted(stats['videos'], 
                                     key=lambda x: x['views'], 
                                     reverse=True)[:3]
                ]
            }
            report['top_trending_keywords'].append(keyword_info)
        
        # 5. 시각화
        if save_to_file:
            self._save_visualization(report)
            self._save_report_to_excel(report)
        
        return report
    
    def _save_visualization(self, report):
        """트렌드 시각화"""
        # 상위 20개 키워드 차트
        top_20 = report['top_trending_keywords'][:20]
        keywords = [item['keyword'] for item in top_20]
        scores = [item['trend_score'] for item in top_20]
        
        plt.figure(figsize=(12, 8))
        plt.barh(keywords[::-1], scores[::-1])
        plt.xlabel('트렌드 점수')
        plt.title(f'YouTube 트렌드 키워드 TOP 20 ({report["region"]})')
        plt.tight_layout()
        
        filename = f'youtube_trends_{report["region"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"📊 차트 저장: {filename}")
    
    def _save_report_to_excel(self, report):
        """엑셀 리포트 저장"""
        # 데이터프레임 생성
        df_data = []
        for item in report['top_trending_keywords']:
            df_data.append({
                '순위': item['rank'],
                '키워드': item['keyword'],
                '트렌드점수': item['trend_score'],
                '출현빈도': item['frequency'],
                '평균조회수': item['avg_views'],
                '총조회수': item['total_views'],
                '연관키워드': ', '.join(item['related_keywords'][:3]),
                '대표영상': item['top_videos'][0]['title'] if item['top_videos'] else ''
            })
        
        df = pd.DataFrame(df_data)
        
        filename = f'youtube_trend_keywords_{report["region"]}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        df.to_excel(filename, index=False)
        
        print(f"📑 엑셀 리포트 저장: {filename}")


# 사용 예시
if __name__ == "__main__":
    # API 키 설정
    API_KEY = "YOUR_API_KEY_HERE"
    
    # 분석기 생성
    analyzer = YouTubeTrendKeywordAnalyzer(API_KEY)
    
    # 트렌드 리포트 생성
    report = analyzer.generate_trend_report(region_code='KR')
    
    # 상위 10개 출력
    print("\n🔥 YouTube 트렌드 키워드 TOP 10:")
    print("=" * 60)
    for item in report['top_trending_keywords'][:10]:
        print(f"{item['rank']}. {item['keyword']}")
        print(f"   트렌드 점수: {item['trend_score']}")
        print(f"   출현 빈도: {item['frequency']}회")
        print(f"   평균 조회수: {item['avg_views']}")
        print(f"   연관 키워드: {', '.join(item['related_keywords'][:3])}")
        print()