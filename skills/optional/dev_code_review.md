# [OPTIONAL SKILL] Code Review Patterns

keywords: review checklist reviewer pull-request PR code-smell refactor lint static-analysis
severity: CRITICAL WARN NIT smell anti-pattern

## 리뷰 체크리스트 (Review Checklist)
1. **정확성** — 로직 버그, 엣지 케이스, 타입 오류
2. **가독성** — 변수명, 함수 길이, 주석 필요성 (→ `dev_clean_code` 스킬 참조)
3. **성능** — O(n²) 루프, 불필요한 DB 쿼리, 메모리 누수
4. **보안** — 입력 검증, SQL 인젝션, 하드코딩 시크릿 (→ `security_best_practices` 스킬 참조)
5. **테스트** — 커버리지 공백, 엣지 케이스 누락 (→ `python_testing` 스킬 참조)
6. **동시성** — race condition, deadlock, asyncio 블로킹 코드 (→ `python_async` 스킬 참조)

## 심각도 분류 (Severity)
```
[CRITICAL] 위치: 문제 설명
→ 권장 해결책 또는 예시
```
- `[CRITICAL]` — 버그/보안 취약점, 반드시 수정. PR 머지 차단.
- `[WARN]`     — 성능/유지보수 이슈, 수정 강력 권장
- `[NIT]`      — 스타일/명명, 선택사항 (블로킹 아님)

## Code Smell 카탈로그
| Smell | 증상 | 해결 |
|-------|------|------|
| Long Method | 함수 50줄+ | 단일 책임으로 분리 |
| God Class | 클래스가 너무 많은 일 | 역할별 분리 |
| Dead Code | 사용 안 하는 함수/변수 | 삭제 |
| Feature Envy | 다른 클래스 데이터를 과도하게 참조 | 메서드 이동 |
| Primitive Obsession | 원시 타입 과다 사용 | dataclass/TypedDict로 묶기 |
| Magic Number | 의미 없는 숫자 리터럴 | 상수로 추출 |
| Duplicate Code | 똑같은 블록 반복 | 함수로 추출 |

## Python 리뷰 anti-pattern (BAD/GOOD)
```python
# [CRITICAL] 예외 묵살 — 버그 숨김
try:
    result = risky_op()
except:          # bare except
    pass

# GOOD
try:
    result = risky_op()
except ValueError as e:
    logger.error("risky_op 실패: %s", e)
    raise

# [WARN] 뮤터블 기본 인수 — 호출 간 상태 공유
def append_item(item, lst=[]):   # BAD
    lst.append(item)
    return lst

def append_item(item, lst=None): # GOOD
    if lst is None:
        lst = []
    lst.append(item)
    return lst

# [NIT] 동일성 비교
if x == None:   # BAD
if x is None:   # GOOD
if x == True:   # BAD
if x:           # GOOD
```

## 비동기 코드 리뷰 포인트 (Async Review)
```python
# [CRITICAL] asyncio 루프 안에서 블로킹 호출 — 전체 루프 멈춤
async def handler():
    time.sleep(1)           # BAD — blocking
    data = open("f").read() # BAD — blocking I/O

    await asyncio.sleep(1)  # GOOD
    async with aiofiles.open("f") as f:  # GOOD
        data = await f.read()

# [CRITICAL] asyncio 루프 내 스레드에서 무거운 import
# → run_in_executor 또는 모듈 레벨 preload 사용
# (LanceDB deadlock 사례 — python_db 스킬 참조)

# [WARN] Task 생성 후 참조 안 하면 GC가 취소할 수 있음
asyncio.create_task(coro())         # BAD — 참조 없음
task = asyncio.create_task(coro())  # GOOD
```

## 리뷰 코멘트 템플릿
```
# 버그 발견
[CRITICAL] `process_user` L42: `user_id`가 None일 때 KeyError 발생
→ `if user_id is None: raise ValueError(...)` 추가 필요

# 성능 이슈
[WARN] `get_all_items` L18: 루프 안에서 DB 쿼리 — N+1 문제
→ 쿼리를 루프 밖으로 옮기거나 bulk fetch 사용

# 스타일
[NIT] `tmp` → `temp_buffer` 로 이름 변경 권장 (가독성)
```

## PR 머지 전 최종 체크 (Pre-merge Gate)
- [ ] `[CRITICAL]` 코멘트 전부 해결됨
- [ ] 새 코드에 테스트 추가됨
- [ ] 로컬 테스트 통과 (`pytest --cov`)
- [ ] 시크릿/API 키 하드코딩 없음 (`git diff` 확인)
- [ ] 불필요한 디버그 print/로그 제거됨
