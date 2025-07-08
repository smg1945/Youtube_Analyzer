"""
통계 계산 전용 모듈
기술통계, 상관관계, 분포 분석, 시계열 분석 담당
"""

import math
from collections import Counter, defaultdict
from datetime import datetime, timedelta
import re

class StatisticsCalculator:
    """통계 계산 클래스"""
    
    def __init__(self):
        """통계 계산기 초기화"""
        pass
    
    def calculate_descriptive_stats(self, values):
        """
        기술통계 계산
        
        Args:
            values (list): 숫자 값 목록
            
        Returns:
            dict: 기술통계 결과
        """
        if not values:
            return self._empty_stats()
        
        try:
            # 정렬된 값
            sorted_values = sorted(values)
            n = len(sorted_values)
            
            # 기본 통계
            total = sum(values)
            mean = total / n
            
            # 중간값
            if n % 2 == 0:
                median = (sorted_values[n//2 - 1] + sorted_values[n//2]) / 2
            else:
                median = sorted_values[n//2]
            
            # 최빈값
            mode_data = Counter(values)
            mode = mode_data.most_common(1)[0][0] if mode_data else None
            
            # 분산과 표준편차
            variance = sum((x - mean) ** 2 for x in values) / n
            std_dev = math.sqrt(variance)
            
            # 사분위수
            q1 = self._calculate_percentile(sorted_values, 25)
            q3 = self._calculate_percentile(sorted_values, 75)
            iqr = q3 - q1
            
            # 왜도와 첨도 (간단한 버전)
            skewness = self._calculate_skewness(values, mean, std_dev)
            kurtosis = self._calculate_kurtosis(values, mean, std_dev)
            
            # 범위
            data_range = max(values) - min(values)
            
            return {
                'count': n,
                'sum': total,
                'mean': round(mean, 4),
                'median': round(median, 4),
                'mode': mode,
                'std_dev': round(std_dev, 4),
                'variance': round(variance, 4),
                'min': min(values),
                'max': max(values),
                'range': data_range,
                'q1': round(q1, 4),
                'q3': round(q3, 4),
                'iqr': round(iqr, 4),
                'skewness': round(skewness, 4),
                'kurtosis': round(kurtosis, 4),
                'cv': round(std_dev / mean * 100, 2) if mean != 0 else 0  # 변동계수
            }
            
        except Exception as e:
            print(f"기술통계 계산 오류: {e}")
            return self._empty_stats()
    
    def calculate_correlation_matrix(self, data_dict):
        """
        상관관계 매트릭스 계산
        
        Args:
            data_dict (dict): {'metric1': [values], 'metric2': [values], ...}
            
        Returns:
            dict: 상관관계 매트릭스
        """
        if not data_dict or len(data_dict) < 2:
            return {}
        
        try:
            metrics = list(data_dict.keys())
            correlation_matrix = {}
            
            for metric1 in metrics:
                correlation_matrix[metric1] = {}
                for metric2 in metrics:
                    if metric1 == metric2:
                        correlation_matrix[metric1][metric2] = 1.0
                    else:
                        correlation = self._calculate_pearson_correlation(
                            data_dict[metric1], data_dict[metric2]
                        )
                        correlation_matrix[metric1][metric2] = round(correlation, 4)
            
            # 강한 상관관계 찾기
            strong_correlations = []
            for metric1 in metrics:
                for metric2 in metrics:
                    if metric1 < metric2:  # 중복 방지
                        corr = correlation_matrix[metric1][metric2]
                        if abs(corr) >= 0.7:  # 강한 상관관계 기준
                            strong_correlations.append({
                                'metric1': metric1,
                                'metric2': metric2,
                                'correlation': corr,
                                'strength': self._classify_correlation_strength(corr)
                            })
            
            return {
                'matrix': correlation_matrix,
                'strong_correlations': strong_correlations,
                'metrics_analyzed': metrics
            }
            
        except Exception as e:
            print(f"상관관계 계산 오류: {e}")
            return {}
    
    def analyze_distribution(self, values, bins=10):
        """
        분포 분석
        
        Args:
            values (list): 분석할 값들
            bins (int): 히스토그램 구간 수
            
        Returns:
            dict: 분포 분석 결과
        """
        if not values:
            return {}
        
        try:
            sorted_values = sorted(values)
            n = len(values)
            
            # 히스토그램 생성
            min_val = min(values)
            max_val = max(values)
            bin_width = (max_val - min_val) / bins if max_val != min_val else 1
            
            histogram = {}
            for i in range(bins):
                bin_start = min_val + i * bin_width
                bin_end = min_val + (i + 1) * bin_width
                bin_label = f"{bin_start:.1f}-{bin_end:.1f}"
                
                count = sum(1 for v in values if bin_start <= v < bin_end)
                if i == bins - 1:  # 마지막 구간은 끝값 포함
                    count = sum(1 for v in values if bin_start <= v <= bin_end)
                
                histogram[bin_label] = count
            
            # 백분위수 계산
            percentiles = {}
            for p in [5, 10, 25, 50, 75, 90, 95]:
                percentiles[f'p{p}'] = self._calculate_percentile(sorted_values, p)
            
            # 이상치 탐지 (IQR 방법)
            q1 = percentiles['p25']
            q3 = percentiles['p75']
            iqr = q3 - q1
            lower_bound = q1 - 1.5 * iqr
            upper_bound = q3 + 1.5 * iqr
            
            outliers = [v for v in values if v < lower_bound or v > upper_bound]
            
            # 정규성 검정 (간단한 방법)
            skewness = abs(self._calculate_skewness(values, sum(values)/n, self._calculate_std_dev(values)))
            kurtosis = abs(self._calculate_kurtosis(values, sum(values)/n, self._calculate_std_dev(values)))
            
            normality_score = max(0, 100 - (skewness * 10 + abs(kurtosis - 3) * 5))
            
            return {
                'histogram': histogram,
                'percentiles': percentiles,
                'outliers': {
                    'values': outliers,
                    'count': len(outliers),
                    'percentage': round(len(outliers) / n * 100, 2),
                    'lower_bound': round(lower_bound, 4),
                    'upper_bound': round(upper_bound, 4)
                },
                'normality_assessment': {
                    'score': round(normality_score, 2),
                    'skewness': round(skewness, 4),
                    'kurtosis': round(kurtosis, 4),
                    'likely_normal': normality_score > 70
                },
                'distribution_type': self._classify_distribution(values)
            }
            
        except Exception as e:
            print(f"분포 분석 오류: {e}")
            return {}
    
    def analyze_time_series(self, time_data):
        """
        시계열 분석
        
        Args:
            time_data (list): [{'date': '2024-01-01', 'value': 100}, ...]
            
        Returns:
            dict: 시계열 분석 결과
        """
        if not time_data or len(time_data) < 2:
            return {}
        
        try:
            # 날짜 순으로 정렬
            sorted_data = sorted(time_data, key=lambda x: x['date'])
            values = [item['value'] for item in sorted_data]
            dates = [item['date'] for item in sorted_data]
            
            # 기본 통계
            basic_stats = self.calculate_descriptive_stats(values)
            
            # 트렌드 분석
            trend_analysis = self._analyze_trend(values)
            
            # 계절성 분석 (주간 패턴)
            seasonality = self._analyze_seasonality(sorted_data)
            
            # 변화율 분석
            change_rates = []
            for i in range(1, len(values)):
                if values[i-1] != 0:
                    change_rate = (values[i] - values[i-1]) / values[i-1] * 100
                    change_rates.append(change_rate)
            
            change_stats = self.calculate_descriptive_stats(change_rates) if change_rates else {}
            
            # 이동평균 계산
            moving_averages = self._calculate_moving_averages(values)
            
            # 변동성 분석
            volatility = self._calculate_volatility(values)
            
            return {
                'period': {
                    'start_date': dates[0],
                    'end_date': dates[-1],
                    'total_periods': len(sorted_data)
                },
                'basic_statistics': basic_stats,
                'trend_analysis': trend_analysis,
                'seasonality': seasonality,
                'change_analysis': {
                    'change_rates_stats': change_stats,
                    'total_change': round((values[-1] - values[0]) / values[0] * 100, 2) if values[0] != 0 else 0,
                    'avg_period_change': round(sum(change_rates) / len(change_rates), 2) if change_rates else 0
                },
                'moving_averages': moving_averages,
                'volatility': volatility,
                'forecasting': self._simple_forecast(values, periods=3)
            }
            
        except Exception as e:
            print(f"시계열 분석 오류: {e}")
            return {}
    
    def calculate_video_metrics_correlation(self, videos_data):
        """
        영상 지표 간 상관관계 분석
        
        Args:
            videos_data (list): 영상 데이터 목록
            
        Returns:
            dict: 영상 지표 상관관계 분석
        """
        if not videos_data:
            return {}
        
        try:
            # 지표 추출
            metrics_data = {
                'views': [],
                'likes': [],
                'comments': [],
                'duration': [],
                'title_length': [],
                'days_since_upload': []
            }
            
            for video in videos_data:
                try:
                    stats = video.get('statistics', {})
                    snippet = video.get('snippet', {})
                    content_details = video.get('contentDetails', {})
                    
                    # 기본 지표
                    metrics_data['views'].append(int(stats.get('viewCount', 0)))
                    metrics_data['likes'].append(int(stats.get('likeCount', 0)))
                    metrics_data['comments'].append(int(stats.get('commentCount', 0)))
                    
                    # 영상 길이 (초 단위)
                    duration_str = content_details.get('duration', 'PT0S')
                    duration_seconds = self._parse_duration(duration_str)
                    metrics_data['duration'].append(duration_seconds)
                    
                    # 제목 길이
                    title_length = len(snippet.get('title', ''))
                    metrics_data['title_length'].append(title_length)
                    
                    # 업로드 후 경과일
                    published_at = snippet.get('publishedAt', '')
                    if published_at:
                        upload_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                        days_elapsed = (datetime.now(upload_date.tzinfo) - upload_date).days
                        metrics_data['days_since_upload'].append(days_elapsed)
                    else:
                        metrics_data['days_since_upload'].append(0)
                        
                except Exception as e:
                    continue
            
            # 상관관계 계산
            correlation_results = self.calculate_correlation_matrix(metrics_data)
            
            # 추가 분석
            additional_analysis = {
                'sample_size': len(videos_data),
                'metrics_summary': {
                    metric: self.calculate_descriptive_stats(values)
                    for metric, values in metrics_data.items()
                },
                'interesting_findings': self._identify_interesting_correlations(correlation_results)
            }
            
            return {
                **correlation_results,
                **additional_analysis
            }
            
        except Exception as e:
            print(f"영상 지표 상관관계 분석 오류: {e}")
            return {}
    
    def analyze_performance_distribution(self, videos_data, metric='viewCount'):
        """
        성과 분포 분석
        
        Args:
            videos_data (list): 영상 데이터 목록
            metric (str): 분석할 지표
            
        Returns:
            dict: 성과 분포 분석 결과
        """
        if not videos_data:
            return {}
        
        try:
            # 지표 값 추출
            values = []
            for video in videos_data:
                try:
                    if metric in ['viewCount', 'likeCount', 'commentCount']:
                        value = int(video.get('statistics', {}).get(metric, 0))
                    elif metric == 'engagement_rate':
                        views = int(video.get('statistics', {}).get('viewCount', 0))
                        likes = int(video.get('statistics', {}).get('likeCount', 0))
                        comments = int(video.get('statistics', {}).get('commentCount', 0))
                        value = ((likes + comments) / views * 100) if views > 0 else 0
                    else:
                        continue
                    
                    values.append(value)
                except Exception as e:
                    continue
            
            if not values:
                return {}
            
            # 분포 분석
            distribution_analysis = self.analyze_distribution(values)
            
            # 성과 계층 분석
            performance_tiers = self._analyze_performance_tiers(values, videos_data, metric)
            
            # 파레토 분석 (80-20 법칙)
            pareto_analysis = self._perform_pareto_analysis(values)
            
            return {
                'metric_analyzed': metric,
                'distribution_analysis': distribution_analysis,
                'performance_tiers': performance_tiers,
                'pareto_analysis': pareto_analysis,
                'summary': {
                    'total_videos': len(values),
                    'high_performers_count': performance_tiers.get('top_tier', {}).get('count', 0),
                    'concentration_ratio': pareto_analysis.get('concentration_ratio', 0)
                }
            }
            
        except Exception as e:
            print(f"성과 분포 분석 오류: {e}")
            return {}
    
    # Private methods
    def _empty_stats(self):
        """빈 통계 객체 반환"""
        return {
            'count': 0, 'sum': 0, 'mean': 0, 'median': 0, 'mode': None,
            'std_dev': 0, 'variance': 0, 'min': 0, 'max': 0, 'range': 0,
            'q1': 0, 'q3': 0, 'iqr': 0, 'skewness': 0, 'kurtosis': 0, 'cv': 0
        }
    
    def _calculate_percentile(self, sorted_values, percentile):
        """백분위수 계산"""
        if not sorted_values:
            return 0
        
        n = len(sorted_values)
        k = (percentile / 100) * (n - 1)
        
        if k.is_integer():
            return sorted_values[int(k)]
        else:
            k_floor = int(k)
            k_ceil = k_floor + 1
            if k_ceil >= n:
                return sorted_values[-1]
            
            weight = k - k_floor
            return sorted_values[k_floor] * (1 - weight) + sorted_values[k_ceil] * weight
    
    def _calculate_skewness(self, values, mean, std_dev):
        """왜도 계산"""
        if std_dev == 0 or len(values) < 3:
            return 0
        
        n = len(values)
        skewness = sum(((x - mean) / std_dev) ** 3 for x in values) / n
        return skewness
    
    def _calculate_kurtosis(self, values, mean, std_dev):
        """첨도 계산"""
        if std_dev == 0 or len(values) < 4:
            return 3  # 정규분포의 첨도
        
        n = len(values)
        kurtosis = sum(((x - mean) / std_dev) ** 4 for x in values) / n
        return kurtosis
    
    def _calculate_std_dev(self, values):
        """표준편차 계산"""
        if not values:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return math.sqrt(variance)
    
    def _calculate_pearson_correlation(self, x_values, y_values):
        """피어슨 상관계수 계산"""
        if len(x_values) != len(y_values) or len(x_values) < 2:
            return 0
        
        n = len(x_values)
        sum_x = sum(x_values)
        sum_y = sum(y_values)
        sum_x_sq = sum(x * x for x in x_values)
        sum_y_sq = sum(y * y for y in y_values)
        sum_xy = sum(x * y for x, y in zip(x_values, y_values))
        
        # 피어슨 상관계수 공식
        numerator = n * sum_xy - sum_x * sum_y
        denominator_x = n * sum_x_sq - sum_x * sum_x
        denominator_y = n * sum_y_sq - sum_y * sum_y
        
        if denominator_x <= 0 or denominator_y <= 0:
            return 0
        
        denominator = math.sqrt(denominator_x * denominator_y)
        
        if denominator == 0:
            return 0
        
        correlation = numerator / denominator
        
        # -1과 1 사이로 제한 (부동소수점 오차 방지)
        correlation = max(-1, min(1, correlation))
        
        return round(correlation, 4)

    def calculate_correlation_matrix(self, data_dict):
        """여러 변수 간의 상관관계 매트릭스 계산"""
        try:
            variables = list(data_dict.keys())
            n_vars = len(variables)
            
            if n_vars < 2:
                return {}
            
            # 상관관계 매트릭스 초기화
            correlation_matrix = {}
            
            for i, var1 in enumerate(variables):
                correlation_matrix[var1] = {}
                
                for j, var2 in enumerate(variables):
                    if i == j:
                        # 자기 자신과의 상관관계는 1
                        correlation_matrix[var1][var2] = 1.0
                    elif j > i:
                        # 상관계수 계산
                        values1 = data_dict[var1]
                        values2 = data_dict[var2]
                        
                        # 데이터 길이 맞추기
                        min_length = min(len(values1), len(values2))
                        values1 = values1[:min_length]
                        values2 = values2[:min_length]
                        
                        correlation = self._calculate_pearson_correlation(values1, values2)
                        correlation_matrix[var1][var2] = correlation
                        
                        # 대칭 매트릭스이므로 반대편도 설정
                        if var2 not in correlation_matrix:
                            correlation_matrix[var2] = {}
                        correlation_matrix[var2][var1] = correlation
                    else:
                        # 이미 계산된 값 사용 (대칭성)
                        if var2 in correlation_matrix and var1 in correlation_matrix[var2]:
                            correlation_matrix[var1][var2] = correlation_matrix[var2][var1]
            
            return correlation_matrix
            
        except Exception as e:
            print(f"상관관계 매트릭스 계산 오류: {e}")
            return {}

    def interpret_correlation(self, correlation_value):
        """상관계수 해석"""
        abs_corr = abs(correlation_value)
        
        if abs_corr >= 0.9:
            strength = "매우 강한"
        elif abs_corr >= 0.7:
            strength = "강한"
        elif abs_corr >= 0.5:
            strength = "보통"
        elif abs_corr >= 0.3:
            strength = "약한"
        else:
            strength = "매우 약한"
        
        direction = "양의" if correlation_value > 0 else "음의"
        
        return {
            'strength': strength,
            'direction': direction,
            'interpretation': f"{direction} {strength} 상관관계"
        }

    def calculate_regression_analysis(self, x_values, y_values):
        """단순 선형 회귀 분석"""
        try:
            if len(x_values) != len(y_values) or len(x_values) < 2:
                return {}
            
            n = len(x_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_x_sq = sum(x * x for x in x_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            
            # 기울기 (slope) 계산
            denominator = n * sum_x_sq - sum_x * sum_x
            if denominator == 0:
                return {}
            
            slope = (n * sum_xy - sum_x * sum_y) / denominator
            
            # 절편 (intercept) 계산
            intercept = (sum_y - slope * sum_x) / n
            
            # R-squared 계산
            correlation = self._calculate_pearson_correlation(x_values, y_values)
            r_squared = correlation ** 2
            
            # 예측값 계산
            predicted_values = [slope * x + intercept for x in x_values]
            
            # 잔차 계산
            residuals = [y - pred for y, pred in zip(y_values, predicted_values)]
            
            # 평균 제곱 오차 (MSE) 계산
            mse = sum(r ** 2 for r in residuals) / n
            rmse = math.sqrt(mse)
            
            return {
                'slope': round(slope, 4),
                'intercept': round(intercept, 4),
                'correlation': round(correlation, 4),
                'r_squared': round(r_squared, 4),
                'mse': round(mse, 4),
                'rmse': round(rmse, 4),
                'equation': f"y = {slope:.4f}x + {intercept:.4f}",
                'predicted_values': predicted_values,
                'residuals': residuals
            }
            
        except Exception as e:
            print(f"회귀 분석 오류: {e}")
            return {}

    def calculate_outlier_detection(self, values, method='iqr'):
        """이상치 탐지"""
        try:
            if not values or len(values) < 4:
                return {'outliers': [], 'outlier_indices': []}
            
            outliers = []
            outlier_indices = []
            
            if method == 'iqr':
                # IQR 방법
                sorted_values = sorted(values)
                q1 = self._calculate_percentile(sorted_values, 25)
                q3 = self._calculate_percentile(sorted_values, 75)
                iqr = q3 - q1
                
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                
                for i, value in enumerate(values):
                    if value < lower_bound or value > upper_bound:
                        outliers.append(value)
                        outlier_indices.append(i)
            
            elif method == 'zscore':
                # Z-score 방법
                mean_val = sum(values) / len(values)
                std_dev = self._calculate_std_dev(values)
                
                if std_dev > 0:
                    for i, value in enumerate(values):
                        z_score = abs((value - mean_val) / std_dev)
                        if z_score > 2.5:  # 2.5 표준편차 이상
                            outliers.append(value)
                            outlier_indices.append(i)
            
            return {
                'outliers': outliers,
                'outlier_indices': outlier_indices,
                'outlier_count': len(outliers),
                'outlier_percentage': round((len(outliers) / len(values)) * 100, 2),
                'method': method
            }
            
        except Exception as e:
            print(f"이상치 탐지 오류: {e}")
            return {'outliers': [], 'outlier_indices': []}

    def calculate_trend_analysis(self, time_series_data):
        """시계열 트렌드 분석"""
        try:
            if not time_series_data or len(time_series_data) < 3:
                return {}
            
            values = [point['value'] for point in time_series_data]
            x_values = list(range(len(values)))
            
            # 선형 트렌드 계산
            regression = self.calculate_regression_analysis(x_values, values)
            
            # 트렌드 방향 판단
            slope = regression.get('slope', 0)
            if slope > 0.1:
                trend_direction = 'increasing'
                trend_strength = 'strong' if slope > 1 else 'moderate'
            elif slope < -0.1:
                trend_direction = 'decreasing'
                trend_strength = 'strong' if slope < -1 else 'moderate'
            else:
                trend_direction = 'stable'
                trend_strength = 'none'
            
            # 변화율 계산
            if len(values) >= 2:
                first_value = values[0]
                last_value = values[-1]
                total_change = ((last_value - first_value) / first_value * 100) if first_value != 0 else 0
                period_count = len(values) - 1
                avg_period_change = total_change / period_count if period_count > 0 else 0
            else:
                total_change = 0
                avg_period_change = 0
            
            return {
                'trend_direction': trend_direction,
                'trend_strength': trend_strength,
                'slope': slope,
                'r_squared': regression.get('r_squared', 0),
                'total_change_percent': round(total_change, 2),
                'avg_period_change_percent': round(avg_period_change, 2),
                'regression_equation': regression.get('equation', ''),
                'data_points': len(values)
            }
            
        except Exception as e:
            print(f"트렌드 분석 오류: {e}")
            return {}
    
    def _classify_correlation_strength(self, correlation):
        """상관관계 강도 분류"""
        abs_corr = abs(correlation)
        
        if abs_corr >= 0.9:
            return "매우 강함"
        elif abs_corr >= 0.7:
            return "강함"
        elif abs_corr >= 0.5:
            return "보통"
        elif abs_corr >= 0.3:
            return "약함"
        else:
            return "매우 약함"
    
    def _classify_distribution(self, values):
        """분포 유형 분류"""
        if not values:
            return "알 수 없음"
        
        mean = sum(values) / len(values)
        std_dev = self._calculate_std_dev(values)
        skewness = abs(self._calculate_skewness(values, mean, std_dev))
        
        if skewness < 0.5:
            return "정규분포에 가까움"
        elif skewness < 1.0:
            return "약간 편향됨"
        else:
            return "강하게 편향됨"
    
    def _analyze_trend(self, values):
        """트렌드 분석"""
        if len(values) < 2:
            return {}
        
        # 선형 회귀를 위한 간단한 계산
        n = len(values)
        x_values = list(range(n))
        
        # 기울기 계산
        sum_x = sum(x_values)
        sum_y = sum(values)
        sum_xy = sum(x * y for x, y in zip(x_values, values))
        sum_x2 = sum(x ** 2 for x in x_values)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
        
        # 트렌드 방향 결정
        if slope > 0.1:
            direction = "상승"
        elif slope < -0.1:
            direction = "하락"
        else:
            direction = "안정"
        
        return {
            'slope': round(slope, 4),
            'direction': direction,
            'strength': abs(slope),
            'r_squared': self._calculate_r_squared(values, x_values)
        }
    
    def _analyze_seasonality(self, time_data):
        """계절성 분석 (주간 패턴)"""
        if len(time_data) < 7:
            return {}
        
        try:
            # 요일별 평균 계산
            weekday_values = defaultdict(list)
            
            for item in time_data:
                date_str = item['date']
                value = item['value']
                
                # 날짜 파싱
                if isinstance(date_str, str):
                    date_obj = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date_obj = date_str
                
                weekday = date_obj.strftime('%A')
                weekday_values[weekday].append(value)
            
            # 요일별 평균
            weekday_averages = {}
            for weekday, values in weekday_values.items():
                weekday_averages[weekday] = sum(values) / len(values)
            
            # 최고/최저 요일
            best_day = max(weekday_averages, key=weekday_averages.get)
            worst_day = min(weekday_averages, key=weekday_averages.get)
            
            return {
                'weekday_averages': weekday_averages,
                'best_performing_day': best_day,
                'worst_performing_day': worst_day,
                'seasonality_strength': max(weekday_averages.values()) / min(weekday_averages.values()) if min(weekday_averages.values()) > 0 else 1
            }
            
        except Exception as e:
            return {}
    
    def _calculate_moving_averages(self, values, windows=[3, 7, 14]):
        """이동평균 계산"""
        moving_averages = {}
        
        for window in windows:
            if len(values) >= window:
                ma_values = []
                for i in range(len(values) - window + 1):
                    window_avg = sum(values[i:i+window]) / window
                    ma_values.append(round(window_avg, 2))
                
                moving_averages[f'ma_{window}'] = ma_values
        
        return moving_averages
    
    def _calculate_volatility(self, values):
        """변동성 계산"""
        if len(values) < 2:
            return {}
        
        # 변화율 계산
        changes = []
        for i in range(1, len(values)):
            if values[i-1] != 0:
                change = (values[i] - values[i-1]) / values[i-1]
                changes.append(change)
        
        if not changes:
            return {}
        
        # 변동성 (표준편차)
        volatility = self._calculate_std_dev(changes)
        
        return {
            'volatility': round(volatility, 4),
            'volatility_percentage': round(volatility * 100, 2),
            'classification': self._classify_volatility(volatility)
        }
    
    def _classify_volatility(self, volatility):
        """변동성 분류"""
        if volatility < 0.1:
            return "낮음"
        elif volatility < 0.3:
            return "보통"
        elif volatility < 0.5:
            return "높음"
        else:
            return "매우 높음"
    
    def _simple_forecast(self, values, periods=3):
        """간단한 예측 (선형 트렌드)"""
        if len(values) < 3:
            return {}
        
        try:
            # 최근 추세 계산
            recent_values = values[-min(5, len(values)):]
            trend = self._analyze_trend(recent_values)
            
            # 예측값 계산
            last_value = values[-1]
            forecasts = []
            
            for i in range(1, periods + 1):
                forecast = last_value + (trend['slope'] * i)
                forecasts.append(round(forecast, 2))
            
            return {
                'forecasts': forecasts,
                'trend_based': True,
                'confidence': 'low' if abs(trend['slope']) < 0.1 else 'medium'
            }
            
        except Exception as e:
            return {}
    
    def _calculate_r_squared(self, y_values, x_values):
        """결정계수 계산"""
        if len(y_values) != len(x_values) or len(y_values) < 2:
            return 0
        
        try:
            # 회귀선의 기울기와 절편 계산
            n = len(y_values)
            sum_x = sum(x_values)
            sum_y = sum(y_values)
            sum_xy = sum(x * y for x, y in zip(x_values, y_values))
            sum_x2 = sum(x ** 2 for x in x_values)
            
            slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2)
            intercept = (sum_y - slope * sum_x) / n
            
            # 예측값 계산
            y_pred = [slope * x + intercept for x in x_values]
            
            # 총 제곱합과 잔차 제곱합
            y_mean = sum(y_values) / len(y_values)
            ss_tot = sum((y - y_mean) ** 2 for y in y_values)
            ss_res = sum((y - y_p) ** 2 for y, y_p in zip(y_values, y_pred))
            
            # R-squared 계산
            r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
            return round(r_squared, 4)
            
        except Exception as e:
            return 0
    
    def _parse_duration(self, duration_str):
        """YouTube duration 파싱"""
        try:
            # PT15M33S 형태 파싱
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            
            if not match:
                return 0
            
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            
            return hours * 3600 + minutes * 60 + seconds
        except:
            return 0
    
    def _identify_interesting_correlations(self, correlation_results):
        """흥미로운 상관관계 식별"""
        findings = []
        
        if 'strong_correlations' in correlation_results:
            for corr in correlation_results['strong_correlations']:
                metric1 = corr['metric1']
                metric2 = corr['metric2']
                value = corr['correlation']
                
                if metric1 == 'views' and metric2 == 'title_length':
                    if value > 0.5:
                        findings.append("제목이 길수록 조회수가 높은 경향")
                    elif value < -0.5:
                        findings.append("제목이 짧을수록 조회수가 높은 경향")
                
                elif metric1 == 'duration' and metric2 == 'views':
                    if value > 0.5:
                        findings.append("영상이 길수록 조회수가 높은 경향")
                    elif value < -0.5:
                        findings.append("영상이 짧을수록 조회수가 높은 경향")
        
        return findings
    
    def _analyze_performance_tiers(self, values, videos_data, metric):
        """성과 계층 분석"""
        if not values:
            return {}
        
        # 상위 10%, 25%, 50% 계층 분석
        sorted_indices = sorted(range(len(values)), key=lambda i: values[i], reverse=True)
        
        total_count = len(values)
        top_10_count = max(1, total_count // 10)
        top_25_count = max(1, total_count // 4)
        top_50_count = max(1, total_count // 2)
        
        tiers = {
            'top_tier': {
                'percentage': 10,
                'count': top_10_count,
                'min_value': values[sorted_indices[top_10_count - 1]] if top_10_count <= len(values) else 0,
                'avg_value': sum(values[i] for i in sorted_indices[:top_10_count]) / top_10_count
            },
            'high_tier': {
                'percentage': 25,
                'count': top_25_count - top_10_count,
                'min_value': values[sorted_indices[top_25_count - 1]] if top_25_count <= len(values) else 0,
                'avg_value': sum(values[i] for i in sorted_indices[top_10_count:top_25_count]) / (top_25_count - top_10_count) if top_25_count > top_10_count else 0
            }
        }
        
        return tiers
    
    def _perform_pareto_analysis(self, values):
        """파레토 분석 (80-20 법칙)"""
        if not values:
            return {}
        
        sorted_values = sorted(values, reverse=True)
        total_sum = sum(values)
        
        # 상위 20%가 전체의 몇 %를 차지하는지
        top_20_percent_count = max(1, len(values) // 5)
        top_20_percent_sum = sum(sorted_values[:top_20_percent_count])
        
        concentration_ratio = (top_20_percent_sum / total_sum * 100) if total_sum > 0 else 0
        
        return {
            'top_20_percent_count': top_20_percent_count,
            'top_20_percent_value': top_20_percent_sum,
            'concentration_ratio': round(concentration_ratio, 2),
            'pareto_efficiency': concentration_ratio >= 80,
            'inequality_level': "높음" if concentration_ratio >= 80 else "보통" if concentration_ratio >= 60 else "낮음"
        }