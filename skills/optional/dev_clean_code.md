# [OPTIONAL SKILL] Clean Code Principles

## 명명 규칙
```python
# BAD
def proc(d, f=True):
    ...

# GOOD
def process_user_data(data: dict, validate: bool = True) -> dict:
    ...
```
- 함수명: 동사+목적어 (`get_user`, `send_notification`)
- 불리언: `is_`, `has_`, `can_` 접두어
- 상수: `MAX_RETRY_COUNT = 3` (대문자+언더스코어)

## 함수 설계 원칙
```python
# 단일 책임 원칙 — 하나의 함수는 하나의 일만
def validate_email(email: str) -> bool:
    return "@" in email and "." in email.split("@")[-1]

def send_welcome_email(user_email: str) -> None:
    if not validate_email(user_email):
        raise ValueError(f"유효하지 않은 이메일: {user_email}")
    # 전송 로직...
```

## 조기 반환 (Guard Clause)
```python
# BAD: 깊은 중첩
def process(user):
    if user:
        if user.is_active:
            if user.has_permission:
                do_work(user)

# GOOD: 조기 반환
def process(user):
    if not user:
        return
    if not user.is_active:
        return
    if not user.has_permission:
        return
    do_work(user)
```

## 매직 넘버 제거
```python
# BAD
if score > 85:
    ...

# GOOD
PASSING_SCORE = 85
if score > PASSING_SCORE:
    ...
```

## 주석 원칙
- 코드가 **무엇을** 하는지 → 코드 자체로 표현
- 주석은 **왜** 그렇게 했는지 설명
```python
# BAD: 코드 복사
# i를 1 증가
i += 1

# GOOD: 의도 설명
# LanceDB는 동시 write 시 deadlock 발생 → preload로 우회
lancedb.preload()
```
