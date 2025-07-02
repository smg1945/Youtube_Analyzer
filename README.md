# 🎬 YouTube 트렌드 분석기 v3.0

YouTube 영상 트렌드를 분석하고 실시간 키워드를 모니터링하는 강력한 분석 도구입니다.

## ✨ 주요 기능

### 🔍 영상 검색 분석기
- **키워드 기반 검색**: 원하는 키워드로 YouTube 영상 검색
- **Outlier Score 분석**: 채널 평균 대비 성과 측정
- **병렬 처리**: 최대 10개 스레드로 빠른 분석
- **필터링 옵션**: 조회수, 업로드 기간, 영상 유형별 필터
- **엑셀 리포트**: 분석 결과를 엑셀로 저장
- **썸네일 다운로드**: 선택한 영상의 썸네일 일괄 다운로드

### 🔥 트렌드 키워드 대시보드
- **실시간 모니터링**: 5분마다 자동 업데이트
- **트렌드 추적**: 인기 급상승 키워드 감지
- **순위 변화**: 키워드 순위 변화 시각화
- **연관 키워드**: 함께 검색되는 키워드 분석
- **대표 영상**: 각 키워드의 인기 영상 확인

## 🚀 빠른 시작

### 1. 요구사항
- Python 3.8 이상
- YouTube Data API v3 키

### 2. 설치

```bash
# 저장소 클론
git clone https://github.com/yourusername/youtube-trend-analyzer.git
cd youtube-trend-analyzer

# 가상환경 생성 (권장)
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate

# 패키지 설치
pip install -r requirements.txt
```

### 3. API 키 설정

#### 방법 1: .env 파일 사용 (권장)
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일을 열어서 API 키 입력
YOUTUBE_API_KEY=your_actual_api_key_here
```

#### 방법 2: 프로그램에서 직접 입력
- 프로그램 실행 시 API 키 입력 창이 자동으로 표시됩니다.

### 4. 실행

```bash
python main.py
```

## 📖 사용 가이드

### 영상 검색 분석기

1. **검색 설정**
   - API 키 입력 (최초 1회)
   - 검색 키워드 입력 (예: "맛집", "여행", "게임")
   - 필터 설정:
     - 최소 조회수: 0, 1000, 10000, 50000, 100000
     - 업로드 기간: 오늘, 2일, 일주일, 한달, 3개월
     - 영상 유형: 전체, 쇼츠, 롱폼

2. **검색 실행**
   - "검색" 버튼 클릭
   - 최대 200개 영상 분석 (약 1-2분 소요)

3. **결과 활용**
   - 더블클릭: YouTube에서 영상 열기
   - 엑셀 추출: 분석 결과를 엑셀 파일로 저장
   - 썸네일 다운로드: 선택한 영상의 썸네일 저장

### 트렌드 키워드 대시보드

1. **초기 설정**
   - API 키 입력
   - 지역 선택 (KR, US, JP, GB)

2. **실시간 모니터링**
   - 자동 새로고침: 5분마다 업데이트
   - 순위 변화: ▲상승, ▼하락, 🆕신규
   - 키워드 클릭: 상세 정보 확인

3. **데이터 분석**
   - 트렌드 점수: 출현 빈도 × 평균 조회수
   - 연관 키워드: 함께 등장하는 키워드
   - 대표 영상: 해당 키워드의 인기 영상

## 📊 분석 지표 설명

### Outlier Score
- **의미**: 채널 평균 대비 영상 성과
- **계산**: (현재 조회수 / 채널 평균 조회수)
- **해석**:
  - 5.0x 이상: 🔥 바이럴
  - 3.0x 이상: ⭐ 히트
  - 1.5x 이상: 📈 양호
  - 0.7x 이상: 😐 평균
  - 0.7x 미만: 📉 저조

### 트렌드 점수
- **의미**: 키워드의 인기도
- **계산**: (출현 빈도 × 평균 조회수) / 1,000,000
- **활용**: 높을수록 현재 핫한 키워드

## 🔧 고급 설정

### config.py 수정
```python
# 최대 검색 결과 수
MAX_RESULTS = 200  # 기본값

# API 할당량
API_QUOTA_LIMIT = 10000  # 일일 한도

# 병렬 처리 워커 수
MAX_WORKERS = 10  # 동시 처리 스레드
```

## 🐛 문제 해결

### API 키 오류
```
❌ YouTube API 키가 설정되지 않았습니다
```
**해결**: .env 파일에 올바른 API 키 입력

### 할당량 초과
```
❌ API 할당량을 초과했습니다
```
**해결**: 
- 내일 다시 시도 (매일 자정 UTC 리셋)
- 경량 모드 사용 (이미 기본값)

### 검색 결과 없음
```
❌ 검색 결과가 없습니다
```
**해결**:
- 다른 키워드로 검색
- 필터 조건 완화
- 검색 기간 확대

## 📁 프로젝트 구조

```
youtube-trend-analyzer/
├── main.py                    # 메인 실행 파일
├── improved_gui.py            # 영상 검색 분석기 GUI
├── youtube_trend_dashboard.py # 트렌드 대시보드 GUI
├── youtube_trend_analyzer.py  # 트렌드 분석 엔진
├── youtube_api.py            # YouTube API 클라이언트
├── data_analyzer.py          # 데이터 분석 모듈
├── excel_generator.py        # 엑셀 생성 모듈
├── config.py                 # 설정 파일
├── requirements.txt          # 필수 패키지
├── .env.example             # 환경변수 예시
├── .gitignore              # Git 제외 목록
└── README.md               # 프로젝트 문서
```

## 🤝 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 라이선스

MIT License - 자유롭게 사용하세요!

## 🙏 감사의 말

- YouTube Data API v3
- Python 커뮤니티
- 오픈소스 기여자들

---

**문의사항이나 버그 리포트는 Issues에 남겨주세요!** 🎉