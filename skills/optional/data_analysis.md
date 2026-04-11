# [OPTIONAL SKILL] Vault Data Analysis & Trend Prediction

keywords: data analysis trend predict analytics vault keyword frequency insight report pandas statistics

## 언제 사용하는가
- "최근 공부 패턴 어때?", "오답 많은 파트가 어디야?" 질문 시
- 주간/월간 리뷰 리포트 요청 시
- 키워드 트렌드나 감정 변화 분석 요청 시

## 분석 가능한 데이터 소스
| 소스 | 경로 | 분석 내용 |
|------|------|-----------|
| 일일 노트 | DAILY/*.md | 감정·피로·학습 키워드 빈도 |
| OCU 강의 | OCU/*.md | 과목별 진도, 약점 파트 |
| 작업일지 | 작업일지/*.md | 개발 활동 패턴 |
| Processed | Processed/*.md | 자동요약 빈도 |

## 분석 패턴 (순수 Python)
```python
from pathlib import Path
import re
from collections import Counter
from datetime import datetime, timedelta

def analyze_keyword_trend(vault_dir: str, keyword: str, days: int = 30) -> dict:
    """최근 N일간 키워드 등장 날짜별 빈도"""
    cutoff = datetime.now() - timedelta(days=days)
    daily_dir = Path(vault_dir) / "DAILY"
    trend = {}
    for f in sorted(daily_dir.glob("*.md")):
        try:
            date = datetime.strptime(f.stem, "%Y-%m-%d")
        except ValueError:
            continue
        if date < cutoff:
            continue
        count = f.read_text(encoding="utf-8", errors="ignore").lower().count(keyword.lower())
        if count:
            trend[f.stem] = count
    return trend

def find_weak_topics(ocu_dir: str) -> list[tuple[str, int]]:
    """OCU 노트에서 '오답', '틀림', '모름' 키워드가 많은 파트"""
    weakness_keywords = ["오답", "틀", "모름", "헷갈", "다시"]
    scores = {}
    for f in Path(ocu_dir).rglob("*.md"):
        text = f.read_text(encoding="utf-8", errors="ignore")
        score = sum(text.count(kw) for kw in weakness_keywords)
        if score:
            scores[f.stem] = score
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)
```

## 리포트 출력 형식
```
[VAULT ANALYSIS] 2026-03-25 (최근 30일)
키워드 트렌드 '피로':
  피크: 2026-03-10 (5회), 2026-03-18 (4회)
  평균: 1.2회/일

취약 파트 TOP3:
  1. 냉동사이클_계산 (오답 12회)
  2. 압축기_종류 (오답 8회)
  3. 증발기_설계 (오답 6회)

권장 액션:
  → 냉동사이클 계산 집중 복습 (시험 전 우선순위)
```

## execute_script 연동
```python
execute_script("auto_scripts/vault_analyzer.py --days 30 --report")
```
