# [OPTIONAL SKILL] Security Best Practices

## 시크릿 관리
```python
# BAD — 절대 금지
API_KEY = "sk-abc123..."

# GOOD — 환경변수
import os
api_key = os.environ["GEMINI_API_KEY"]  # 없으면 KeyError → 명시적 실패
```

## 입력 검증
```python
import re

def validate_filename(fname: str) -> str:
    """경로 탐색 공격 방지"""
    # 경로 구분자, 상위 디렉토리 참조 제거
    fname = os.path.basename(fname)
    if not re.match(r'^[\w\-. ]+$', fname):
        raise ValueError(f"허용되지 않는 파일명: {fname}")
    return fname

def validate_query(query: str, max_len: int = 500) -> str:
    """SQL/명령어 인젝션 방지"""
    if len(query) > max_len:
        raise ValueError("쿼리가 너무 깁니다")
    return query.strip()
```

## 커맨드 인젝션 방지
```python
import subprocess

# BAD — shell=True + 사용자 입력 직접 삽입
subprocess.run(f"ls {user_input}", shell=True)

# GOOD — 리스트 형태, shell=False
subprocess.run(["ls", user_input], shell=False, capture_output=True)
```

## 파일 접근 보호 (온유 시스템 패턴)
```python
VAULT_ROOT = Path("C:/Users/User/Documents/Obsidian Vault")
PROTECTED_DIRS = {"SYSTEM/skills/core", "SYSTEM/skills/domain"}

def is_safe_path(target: Path) -> bool:
    """경로 탈출 방지"""
    try:
        target.resolve().relative_to(VAULT_ROOT.resolve())
        return True
    except ValueError:
        return False
```

## 로깅 보안
```python
# BAD — 시크릿 노출
logger.info("API 호출: key=%s", api_key)

# GOOD — 마스킹
logger.info("API 호출: key=%s...%s", api_key[:4], api_key[-4:])
```
