---
tags: [incident, 온유, LanceDB, 과금, 임베딩]
날짜: 2026-03-19
상태: 해결완료
---

# 🚨 2026-03-19 온유 과금 사고 보고서

## 1. 피해 요약

| 항목 | 내용 |
|------|------|
| 발생일 | 2026-03-18 ~ 03-19 |
| 피해 금액 | **24,000원** (2026-03-18 하루치) |
| 임베딩 호출 수 | **64,181회** (정상 일일 사용: 수백 회 수준) |
| 데이터 피해 | LanceDB 임베딩 데이터 전체 소실 |
| 복구 가능 여부 | **불가** (백업과 현재 모델 차원 불일치) |

---

## 2. 사고 타임라인

### 2026-03-18 (사고 당일)

```
11:18  onew_pure_db.json (구 JSON DB, 1.4GB, 3072d 임베딩) 수동 백업
         → db_backup/onew_pure_db_MANUAL_20260318_113155.json

11:18  obsidian_agent.py 대규모 업데이트
         - JSON DB → LanceDB 마이그레이션 코드 추가
         - 임베딩 모델: 구 모델(3072d) → gemini-embedding-001(768d)
         - CHUNK_VERSION: "v2" → "v3"
         - EMBED_DIM: 3072 → 768

20:21  마이그레이션 실행
         - DB_FILE(onew_pure_db.json)이 이미 70바이트(빈 파일)
         - 마이그레이션 조건: count_rows()==0 AND DB_FILE 존재 → 실행
         - 결과: 0개 청크 로드 (빈 파일이라 데이터 없음)

20:25  sync_vault() 실행
         ① chunk_version 체크: "v2"(백업) ≠ "v3"(현재)
         ② _init_tables(mode="overwrite") 호출 → chunks 테이블 전체 초기화
         ③ 이미 0개였으므로 실질적 피해는 이미 발생 전

         ↓ 여기서 문제 발생

         ④ 4,962개 파일 전체가 to_update에 포함
            (DB가 비어있어 모든 파일 mtime 미등록)
         ⑤ 64,181회 임베딩 API 호출 → 24,000원 과금
         ⑥ 완료 후 LanceDB에 데이터 저장

03-19  08:47  재부팅 또는 재실행
         → chunk_version 체크 재발생
         → 또다시 _init_tables() 호출
         → LanceDB 데이터 전체 삭제 (어제 저장한 64,181회치)
         → 오늘 다시 30,000회 호출 후 서킷 브레이커 작동
```

---

## 3. 근본 원인 분석

### 원인 1: `CHUNK_VERSION` 변경 시 즉시 전체 삭제 (핵심 버그)

```python
# 문제 코드 (obsidian_agent.py sync_vault)
stored_version = self._meta.get("chunk_version")
if stored_version != CHUNK_VERSION:
    self._init_tables()   # ← mode="overwrite" 로 전체 삭제
    self._meta = {}
```

- `CHUNK_VERSION`이 코드 업데이트로 바뀌면 **경고 없이 즉시 전체 삭제**
- 삭제 후 바로 전체 재임베딩 시작 → 수만 건 API 호출
- 이 패턴이 **매 실행마다 반복** 가능 (meta가 초기화되므로)

### 원인 2: 마이그레이션 소스 파일이 비어있었음

```
onew_pure_db.json = 70바이트 (빈 파일)
→ 마이그레이션 실행되지만 0개 청크 로드
→ DB는 여전히 비어 있음
→ 모든 파일이 "신규" 로 인식 → 전체 재임베딩
```

구 JSON DB(1.4GB)가 이미 비워진 상태에서 LanceDB로 전환하여 복구 불가.

### 원인 3: `MAX_DAILY_EMBED_CALLS = 30,000` 이 사실상 무의미

- 하루 한도 30,000회이지만 **전날 0시 기준 리셋**
- 3/18에 64,181회 발생했는데 한도가 작동하지 않은 것은
  `daily_calls`가 당일 사용량만 카운트하는 구조였고,
  당일 첫 실행이라 카운터가 0에서 시작했기 때문
- 즉, 한도가 맞지 않게 설정되어 있었음 (30,000 < 실제 필요량)

### 원인 4: `max_chunk=800` 이 너무 작음

```python
def _semantic_chunks(content: str, max_chunk: int = 800):
```

- 800자 단위 청크 → 파일당 평균 13개 청크
- 4,962개 파일 × 13청크 = **64,506회** 임베딩 필요
- 청크 크기를 키우면 동일 내용을 더 적은 호출로 처리 가능

### 원인 5: 백업이 실제로 생성되지 않음

- `_save_db()`가 성공/실패를 로그로 남기지 않았음
- LanceDB 데이터가 삭제된 후 백업이 없어서 복구 불가
- `db_backup/` 폴더에 `onew_lance_db_*` 백업 없음 확인됨

---

## 4. 구 백업으로 복구가 불가능한 이유

| 항목 | 백업 (구) | 현재 코드 |
|------|----------|----------|
| chunk_version | v2 | v3 |
| 임베딩 차원 | **3072d** | **768d** |
| 임베딩 모델 | 구 모델 | gemini-embedding-001 |

- 백업(`onew_pure_db_MANUAL_20260318_113155.json`)의 임베딩은 3072차원
- 현재 LanceDB 스키마는 768차원으로 고정
- 차원이 다르면 벡터 검색 불가 → 마이그레이션 불가
- **결론: 전체 재임베딩 외 방법 없음**

---

## 5. 적용된 수정 사항

### Fix 1: `CHUNK_VERSION` 변경 시 즉시 삭제 금지

```python
# 수정 전
if stored_version != CHUNK_VERSION:
    self._init_tables()   # 전체 삭제
    self._meta = {}

# 수정 후
force_reindex = stored_version is not None and stored_version != CHUNK_VERSION
if force_reindex and not silent:
    print(f"청크 전략 변경 감지. 순차 재학습 시작 (기존 데이터 유지)...")
# → 기존 데이터 유지하면서 파일마다 순차 교체
```

### Fix 2: `max_chunk` 크기 증가

```python
# 수정 전
def _semantic_chunks(content: str, max_chunk: int = 800):

# 수정 후
def _semantic_chunks(content: str, max_chunk: int = 2000):
```

→ 파일당 청크 수 약 2.5배 감소 → API 호출 수 감소

### Fix 3: 배치 쓰기로 LanceDB 파일 폭발 방지

```python
# 수정 전: 파일마다 add() 호출 → 4,962개 .lance 파일 생성
self._table.add(new_rows)  # 파일마다 호출

# 수정 후: 100개 파일마다 한 번에 add()
BATCH_SIZE = 100
batch_rows = []
# ... 파일 처리 후 batch_rows.extend(new_rows)
if updated % BATCH_SIZE == 0:
    self._table.add(batch_rows); batch_rows.clear()
```

### Fix 4: `MAX_DAILY_EMBED_CALLS` 재인덱싱 후 하향 예정

```python
# 현재 (재인덱싱 중)
MAX_DAILY_EMBED_CALLS = 200000

# 재인덱싱 완료 후 낮출 예정
MAX_DAILY_EMBED_CALLS = 10000
```

### Fix 5: 백업 성공 여부 로그 추가

```python
if os.path.exists(dst):
    print(f"💾 DB 백업 완료: onew_lance_db_{ts}")
else:
    print(f"⚠️ 백업 폴더가 생성되지 않았습니다: {dst}")
```

---

## 6. 향후 재발 방지 체크리스트

- [ ] `CHUNK_VERSION` 변경 전 반드시 LanceDB 백업 확인
- [ ] 코드 업데이트 후 첫 실행 시 sync 자동 실행 여부 확인
- [ ] 재인덱싱 완료 후 `MAX_DAILY_EMBED_CALLS = 10000` 으로 낮추기
- [ ] `_save_db()` 백업 로그 확인 습관화
- [ ] 임베딩 모델 변경 시 기존 DB와 차원 호환 여부 반드시 확인

---

## 7. 교훈

> **"데이터를 삭제하는 코드는 절대로 암묵적으로 실행되어서는 안 된다."**

`CHUNK_VERSION` 하나 바뀌었다고 수십만 원짜리 데이터가 경고도 없이 삭제된 것이 이번 사고의 본질이다. 앞으로 DB를 초기화하는 작업은 반드시 **명시적 사용자 확인** 또는 **백업 후 실행** 원칙을 지켜야 한다.
