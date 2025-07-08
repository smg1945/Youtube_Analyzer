"""
참여도 계산 전용 모듈
좋아요율, 댓글율, 참여도 점수, Outlier Score 계산 담당
"""

import math
from datetime import datetime, timedelta
from collections import defaultdict

class EngagementCalculator:
    """참여도 계산 클래스"""
    
    def __init__(self):
        """참여도 계산기 초기화"""
        self.engagement_weights = {
            'like_weight': 0.7,      # 좋아요 가중치
            'comment_weight': 0.3,   # 댓글 가중치
            'view_weight': 0.1       # 조회수 가중치 (선택적)
        }
    
    def calculate_engagement_score(self, video_data):
        """
        참여도 점수 계산
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            float: 참여도 점수 (0-100)
        """
        try:
            stats = video_data.get('statistics', {})
            
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            comment_count = int(stats.get('commentCount', 0))
            
            if view_count == 0:
                return 0.0
            
            # 참여도 비율 계산
            like_rate = (like_count / view_count) * 100
            comment_rate = (comment_count / view_count) * 100
            
            # 가중 평균으로 참여도 점수 계산
            engagement_score = (
                like_rate * self.engagement_weights['like_weight'] + 
                comment_rate * self.engagement_weights['comment_weight']
            ) * 1000  # 0-100 범위로 스케일링
            
            # 0-100 범위로 제한
            return min(round(engagement_score, 2), 100.0)
            
        except Exception as e:
            print(f"참여도 점수 계산 오류: {e}")
            return 0.0
    
    def calculate_like_rate(self, video_data):
        """
        좋아요율 계산
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            float: 좋아요율 (%)
        """
        try:
            stats = video_data.get('statistics', {})
            view_count = int(stats.get('viewCount', 0))
            like_count = int(stats.get('likeCount', 0))
            
            if view_count == 0:
                return 0.0
            
            return round((like_count / view_count) * 100, 4)
            
        except Exception as e:
            print(f"좋아요율 계산 오류: {e}")
            return 0.0
    
    def calculate_comment_rate(self, video_data):
        """
        댓글율 계산
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            float: 댓글율 (%)
        """
        try:
            stats = video_data.get('statistics', {})
            view_count = int(stats.get('viewCount', 0))
            comment_count = int(stats.get('commentCount', 0))
            
            if view_count == 0:
                return 0.0
            
            return round((comment_count / view_count) * 100, 4)
            
        except Exception as e:
            print(f"댓글율 계산 오류: {e}")
            return 0.0
    
    def calculate_outlier_score(self, current_video_stats, channel_avg_stats):
        """
        vidIQ의 Outlier Score와 유사한 지표 계산
        
        Args:
            current_video_stats (dict): 현재 영상 통계
            channel_avg_stats (dict): 채널 평균 통계
            
        Returns:
            float: outlier score (1.0 = 평균, 2.0 = 평균의 2배 등)
        """
        if not channel_avg_stats or not current_video_stats:
            return 1.0
        
        try:
            current_views = int(current_video_stats.get('viewCount', 0))
            current_likes = int(current_video_stats.get('likeCount', 0))
            current_comments = int(current_video_stats.get('commentCount', 0))
            
            avg_views = max(channel_avg_stats.get('avg_views', 1), 1)
            avg_likes = max(channel_avg_stats.get('avg_likes', 1), 1)
            avg_comments = max(channel_avg_stats.get('avg_comments', 1), 1)
            
            # 각 지표별 배수 계산
            views_ratio = current_views / avg_views
            likes_ratio = current_likes / avg_likes
            comments_ratio = current_comments / avg_comments
            
            # 가중 평균으로 outlier score 계산
            # 조회수 50%, 좋아요 30%, 댓글 20% 가중치
            outlier_score = (
                views_ratio * 0.5 + 
                likes_ratio * 0.3 + 
                comments_ratio * 0.2
            )
            
            return round(outlier_score, 2)
            
        except Exception as e:
            print(f"Outlier score 계산 오류: {e}")
            return 1.0
    
    def categorize_outlier_score(self, outlier_score):
        """
        Outlier Score를 카테고리로 분류
        
        Args:
            outlier_score (float): outlier score
            
        Returns:
            str: 카테고리
        """
        if outlier_score >= 5.0:
            return "🔥 바이럴"
        elif outlier_score >= 3.0:
            return "⭐ 히트"
        elif outlier_score >= 1.5:
            return "📈 양호"
        elif outlier_score >= 0.7:
            return "😐 평균"
        else:
            return "📉 저조"
    
    def calculate_views_per_day(self, video_data):
        """
        일일 평균 조회수 계산
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            float: 일일 평균 조회수
        """
        try:
            published_at = video_data['snippet']['publishedAt']
            view_count = int(video_data['statistics'].get('viewCount', 0))
            
            # 업로드 날짜 파싱
            upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_date = datetime.now(upload_date.tzinfo)
            
            # 경과 일수 계산
            days_elapsed = (current_date - upload_date).days
            if days_elapsed == 0:
                days_elapsed = 1  # 최소 1일로 처리
            
            return round(view_count / days_elapsed, 2)
            
        except Exception as e:
            print(f"일일 평균 조회수 계산 오류: {e}")
            return 0.0
    
    def calculate_growth_velocity(self, video_data):
        """
        성장 속도 계산 (시간당 조회수 증가율)
        
        Args:
            video_data (dict): 영상 데이터
            
        Returns:
            dict: 성장 속도 정보
        """
        try:
            published_at = video_data['snippet']['publishedAt']
            view_count = int(video_data['statistics'].get('viewCount', 0))
            
            upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_date = datetime.now(upload_date.tzinfo)
            
            hours_elapsed = (current_date - upload_date).total_seconds() / 3600
            if hours_elapsed == 0:
                hours_elapsed = 1
            
            views_per_hour = view_count / hours_elapsed
            
            # 성장 속도 카테고리화
            if hours_elapsed <= 24:  # 24시간 이내
                category = "신규"
                if views_per_hour > 1000:
                    velocity_rating = "매우 빠름"
                elif views_per_hour > 100:
                    velocity_rating = "빠름"
                elif views_per_hour > 10:
                    velocity_rating = "보통"
                else:
                    velocity_rating = "느림"
            else:  # 24시간 이후
                category = "기존"
                if views_per_hour > 100:
                    velocity_rating = "매우 빠름"
                elif views_per_hour > 10:
                    velocity_rating = "빠름"
                elif views_per_hour > 1:
                    velocity_rating = "보통"
                else:
                    velocity_rating = "느림"
            
            return {
                'views_per_hour': round(views_per_hour, 2),
                'hours_since_upload': round(hours_elapsed, 1),
                'velocity_category': category,
                'velocity_rating': velocity_rating
            }
            
        except Exception as e:
            print(f"성장 속도 계산 오류: {e}")
            return {
                'views_per_hour': 0.0,
                'hours_since_upload': 0.0,
                'velocity_category': "알수없음",
                'velocity_rating': "알수없음"
            }
    
    def calculate_engagement_trends(self, videos_list):
        """
        영상 목록의 참여도 트렌드 분석
        
        Args:
            videos_list (list): 영상 데이터 목록 (시간순 정렬 권장)
            
        Returns:
            dict: 참여도 트렌드 분석 결과
        """
        if not videos_list:
            return {}
        
        try:
            engagement_data = []
            
            for video in videos_list:
                engagement_score = self.calculate_engagement_score(video)
                like_rate = self.calculate_like_rate(video)
                comment_rate = self.calculate_comment_rate(video)
                
                published_at = video['snippet']['publishedAt']
                upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                
                engagement_data.append({
                    'date': upload_date.date(),
                    'engagement_score': engagement_score,
                    'like_rate': like_rate,
                    'comment_rate': comment_rate,
                    'views': int(video['statistics'].get('viewCount', 0))
                })
            
            # 시간순으로 정렬
            engagement_data.sort(key=lambda x: x['date'])
            
            # 트렌드 계산
            if len(engagement_data) >= 2:
                recent_avg = sum(d['engagement_score'] for d in engagement_data[-5:]) / min(5, len(engagement_data))
                older_avg = sum(d['engagement_score'] for d in engagement_data[:5]) / min(5, len(engagement_data))
                
                trend_direction = "상승" if recent_avg > older_avg else "하락" if recent_avg < older_avg else "안정"
                trend_strength = abs(recent_avg - older_avg)
            else:
                trend_direction = "안정"
                trend_strength = 0
            
            return {
                'engagement_timeline': engagement_data,
                'trend_analysis': {
                    'direction': trend_direction,
                    'strength': round(trend_strength, 2),
                    'recent_avg_engagement': round(recent_avg, 2) if len(engagement_data) >= 2 else 0,
                    'overall_avg_engagement': round(sum(d['engagement_score'] for d in engagement_data) / len(engagement_data), 2)
                },
                'peak_performance': max(engagement_data, key=lambda x: x['engagement_score']) if engagement_data else None,
                'total_videos_analyzed': len(engagement_data)
            }
            
        except Exception as e:
            print(f"참여도 트렌드 계산 오류: {e}")
            return {}
    
    def compare_video_performance(self, video1, video2):
        """
        두 영상의 성과 비교
        
        Args:
            video1 (dict): 첫 번째 영상 데이터
            video2 (dict): 두 번째 영상 데이터
            
        Returns:
            dict: 비교 결과
        """
        try:
            # 각 영상의 지표 계산
            metrics1 = self._calculate_all_metrics(video1)
            metrics2 = self._calculate_all_metrics(video2)
            
            # 비교 결과 계산
            comparison = {}
            for metric in metrics1.keys():
                value1 = metrics1[metric]
                value2 = metrics2[metric]
                
                if value2 != 0:
                    ratio = value1 / value2
                    if ratio > 1.1:
                        winner = "video1"
                        difference = f"{(ratio - 1) * 100:.1f}% 높음"
                    elif ratio < 0.9:
                        winner = "video2"
                        difference = f"{(1 - ratio) * 100:.1f}% 낮음"
                    else:
                        winner = "similar"
                        difference = "비슷함"
                else:
                    winner = "video1" if value1 > 0 else "similar"
                    difference = "비교 불가"
                
                comparison[metric] = {
                    'video1_value': value1,
                    'video2_value': value2,
                    'winner': winner,
                    'difference': difference
                }
            
            return {
                'video1_title': video1['snippet']['title'][:50],
                'video2_title': video2['snippet']['title'][:50],
                'comparison': comparison,
                'overall_winner': self._determine_overall_winner(comparison)
            }
            
        except Exception as e:
            print(f"영상 성과 비교 오류: {e}")
            return {}
    
    def calculate_channel_engagement_benchmark(self, channel_videos):
        """
        채널의 참여도 벤치마크 계산
        
        Args:
            channel_videos (list): 채널의 영상 목록
            
        Returns:
            dict: 채널 참여도 벤치마크
        """
        if not channel_videos:
            return {}
        
        try:
            engagement_scores = []
            like_rates = []
            comment_rates = []
            view_counts = []
            
            for video in channel_videos:
                engagement_scores.append(self.calculate_engagement_score(video))
                like_rates.append(self.calculate_like_rate(video))
                comment_rates.append(self.calculate_comment_rate(video))
                view_counts.append(int(video['statistics'].get('viewCount', 0)))
            
            return {
                'total_videos': len(channel_videos),
                'engagement_benchmark': {
                    'avg_engagement_score': round(sum(engagement_scores) / len(engagement_scores), 2),
                    'median_engagement_score': self._calculate_median(engagement_scores),
                    'top_10_percent_avg': round(sum(sorted(engagement_scores, reverse=True)[:max(1, len(engagement_scores)//10)]) / max(1, len(engagement_scores)//10), 2),
                    'std_dev': round(self._calculate_std_dev(engagement_scores), 2)
                },
                'like_rate_benchmark': {
                    'avg_like_rate': round(sum(like_rates) / len(like_rates), 4),
                    'median_like_rate': self._calculate_median(like_rates),
                    'max_like_rate': max(like_rates),
                    'min_like_rate': min(like_rates)
                },
                'comment_rate_benchmark': {
                    'avg_comment_rate': round(sum(comment_rates) / len(comment_rates), 4),
                    'median_comment_rate': self._calculate_median(comment_rates),
                    'max_comment_rate': max(comment_rates),
                    'min_comment_rate': min(comment_rates)
                },
                'view_distribution': {
                    'avg_views': round(sum(view_counts) / len(view_counts), 0),
                    'median_views': self._calculate_median(view_counts),
                    'max_views': max(view_counts),
                    'min_views': min(view_counts)
                }
            }
            
        except Exception as e:
            print(f"채널 참여도 벤치마크 계산 오류: {e}")
            return {}
    
    def _calculate_all_metrics(self, video_data):
        """영상의 모든 지표 계산"""
        return {
            'engagement_score': self.calculate_engagement_score(video_data),
            'like_rate': self.calculate_like_rate(video_data),
            'comment_rate': self.calculate_comment_rate(video_data),
            'views_per_day': self.calculate_views_per_day(video_data),
            'view_count': int(video_data['statistics'].get('viewCount', 0)),
            'like_count': int(video_data['statistics'].get('likeCount', 0)),
            'comment_count': int(video_data['statistics'].get('commentCount', 0))
        }
    
    def _determine_overall_winner(self, comparison):
        """전체적인 승자 결정"""
        video1_wins = sum(1 for metrics in comparison.values() if metrics['winner'] == 'video1')
        video2_wins = sum(1 for metrics in comparison.values() if metrics['winner'] == 'video2')
        
        if video1_wins > video2_wins:
            return "video1"
        elif video2_wins > video1_wins:
            return "video2"
        else:
            return "similar"
    
    def _calculate_median(self, values):
        """중간값 계산"""
        if not values:
            return 0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
        else:
            return sorted_values[n//2]
    
    def _calculate_std_dev(self, values):
        """표준편차 계산"""
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5


class PerformanceAnalyzer:
    """성과 분석 전문 클래스"""
    
    def __init__(self, engagement_calculator):
        """
        성과 분석기 초기화
        
        Args:
            engagement_calculator: EngagementCalculator 인스턴스
        """
        self.calc = engagement_calculator
    
    def analyze_video_lifecycle(self, video_data, time_series_data=None):
        """
        영상 생명주기 분석
        
        Args:
            video_data (dict): 영상 기본 데이터
            time_series_data (list): 시간별 조회수 데이터 (선택적)
            
        Returns:
            dict: 생명주기 분석 결과
        """
        try:
            # 기본 생명주기 정보
            published_at = video_data['snippet']['publishedAt']
            upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            current_date = datetime.now(upload_date.tzinfo)
            
            age_days = (current_date - upload_date).days
            age_hours = (current_date - upload_date).total_seconds() / 3600
            
            # 생명주기 단계 결정
            if age_hours <= 24:
                lifecycle_stage = "론칭"
            elif age_days <= 7:
                lifecycle_stage = "초기 성장"
            elif age_days <= 30:
                lifecycle_stage = "성장"
            elif age_days <= 180:
                lifecycle_stage = "성숙"
            else:
                lifecycle_stage = "쇠퇴"
            
            # 성장 속도 정보
            growth_info = self.calc.calculate_growth_velocity(video_data)
            
            result = {
                'upload_date': upload_date.isoformat(),
                'age_days': age_days,
                'age_hours': round(age_hours, 1),
                'lifecycle_stage': lifecycle_stage,
                'growth_velocity': growth_info,
                'performance_prediction': self._predict_performance(video_data, age_hours)
            }
            
            # 시간별 데이터가 있으면 더 상세한 분석
            if time_series_data:
                result['detailed_analysis'] = self._analyze_detailed_lifecycle(time_series_data)
            
            return result
            
        except Exception as e:
            print(f"영상 생명주기 분석 오류: {e}")
            return {}
    
    def identify_high_performers(self, videos_list, criteria='engagement'):
        """
        고성과 영상 식별
        
        Args:
            videos_list (list): 영상 목록
            criteria (str): 평가 기준 ('engagement', 'views', 'growth')
            
        Returns:
            dict: 고성과 영상 분석 결과
        """
        if not videos_list:
            return {}
        
        try:
            # 각 영상의 성과 지표 계산
            performance_data = []
            
            for video in videos_list:
                if criteria == 'engagement':
                    score = self.calc.calculate_engagement_score(video)
                elif criteria == 'views':
                    score = int(video['statistics'].get('viewCount', 0))
                elif criteria == 'growth':
                    growth_info = self.calc.calculate_growth_velocity(video)
                    score = growth_info['views_per_hour']
                else:
                    score = self.calc.calculate_engagement_score(video)
                
                performance_data.append({
                    'video': video,
                    'score': score,
                    'title': video['snippet']['title'],
                    'views': int(video['statistics'].get('viewCount', 0)),
                    'engagement_score': self.calc.calculate_engagement_score(video)
                })
            
            # 점수 기준으로 정렬
            performance_data.sort(key=lambda x: x['score'], reverse=True)
            
            # 성과 구간 분석
            total_videos = len(performance_data)
            top_10_percent = max(1, total_videos // 10)
            top_25_percent = max(1, total_videos // 4)
            
            high_performers = performance_data[:top_10_percent]
            good_performers = performance_data[top_10_percent:top_25_percent]
            
            # 고성과 영상의 공통 특성 분석
            common_traits = self._analyze_high_performer_traits(high_performers)
            
            return {
                'criteria': criteria,
                'total_videos_analyzed': total_videos,
                'high_performers': {
                    'count': len(high_performers),
                    'videos': high_performers,
                    'avg_score': round(sum(v['score'] for v in high_performers) / len(high_performers), 2) if high_performers else 0
                },
                'good_performers': {
                    'count': len(good_performers),
                    'videos': good_performers[:5],  # 상위 5개만
                    'avg_score': round(sum(v['score'] for v in good_performers) / len(good_performers), 2) if good_performers else 0
                },
                'common_traits': common_traits,
                'performance_distribution': self._calculate_performance_distribution(performance_data)
            }
            
        except Exception as e:
            print(f"고성과 영상 식별 오류: {e}")
            return {}
    
    def _predict_performance(self, video_data, age_hours):
        """성과 예측 (간단한 모델)"""
        try:
            current_views = int(video_data['statistics'].get('viewCount', 0))
            views_per_hour = current_views / max(age_hours, 1)
            
            # 24시간, 7일, 30일 예측
            if age_hours < 24:
                predicted_24h = views_per_hour * 24
                predicted_7d = views_per_hour * 24 * 7 * 0.3  # 감소 계수 적용
                predicted_30d = views_per_hour * 24 * 30 * 0.1
            else:
                # 이미 24시간이 지난 경우 현재 추세 기반
                daily_views = views_per_hour * 24
                predicted_24h = current_views  # 이미 지남
                predicted_7d = current_views + daily_views * (7 - age_hours/24) * 0.5 if age_hours < 168 else current_views
                predicted_30d = current_views + daily_views * (30 - age_hours/24) * 0.2 if age_hours < 720 else current_views
            
            return {
                'predicted_24h_views': max(current_views, int(predicted_24h)),
                'predicted_7d_views': max(current_views, int(predicted_7d)),
                'predicted_30d_views': max(current_views, int(predicted_30d)),
                'confidence': 'low' if age_hours < 6 else 'medium' if age_hours < 48 else 'high'
            }
            
        except Exception as e:
            print(f"성과 예측 오류: {e}")
            return {}
    
    def _analyze_detailed_lifecycle(self, time_series_data):
        """상세 생명주기 분석"""
        # 시간별 조회수 변화 패턴 분석
        if len(time_series_data) < 2:
            return {}
        
        # 성장률 계산
        growth_rates = []
        for i in range(1, len(time_series_data)):
            prev_views = time_series_data[i-1]['views']
            curr_views = time_series_data[i]['views']
            
            if prev_views > 0:
                growth_rate = (curr_views - prev_views) / prev_views * 100
                growth_rates.append(growth_rate)
        
        # 피크 시점 찾기
        max_growth_idx = growth_rates.index(max(growth_rates)) if growth_rates else 0
        
        return {
            'peak_growth_period': max_growth_idx,
            'max_growth_rate': max(growth_rates) if growth_rates else 0,
            'avg_growth_rate': sum(growth_rates) / len(growth_rates) if growth_rates else 0,
            'growth_consistency': self.calc._calculate_std_dev(growth_rates) if growth_rates else 0
        }
    
    def _analyze_high_performer_traits(self, high_performers):
        """고성과 영상의 공통 특성 분석"""
        if not high_performers:
            return {}
        
        # 제목 길이 분석
        title_lengths = [len(video['video']['snippet']['title']) for video in high_performers]
        
        # 업로드 시간 분석
        upload_hours = []
        for video in high_performers:
            published_at = video['video']['snippet']['publishedAt']
            dt = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
            upload_hours.append(dt.hour)
        
        # 카테고리 분석
        categories = [video['video']['snippet'].get('categoryId', 'Unknown') for video in high_performers]
        category_counts = Counter(categories)
        
        return {
            'avg_title_length': round(sum(title_lengths) / len(title_lengths), 1),
            'title_length_range': f"{min(title_lengths)}-{max(title_lengths)}",
            'popular_upload_hours': [hour for hour, count in Counter(upload_hours).most_common(3)],
            'most_common_categories': dict(category_counts.most_common(3)),
            'sample_size': len(high_performers)
        }
    
    def _calculate_performance_distribution(self, performance_data):
        """성과 분포 계산"""
        scores = [data['score'] for data in performance_data]
        
        return {
            'min_score': min(scores),
            'max_score': max(scores),
            'avg_score': round(sum(scores) / len(scores), 2),
            'median_score': self.calc._calculate_median(scores),
            'std_dev': round(self.calc._calculate_std_dev(scores), 2),
            'quartiles': {
                'q1': self.calc._calculate_median(scores[:len(scores)//2]),
                'q3': self.calc._calculate_median(scores[len(scores)//2:])
            }
        }