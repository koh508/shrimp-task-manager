# [OPTIONAL SKILL] Python Type System

keywords: type hint annotation mypy typing TypedDict Protocol Literal TypeVar Generic overload

## 타입 힌트(Type Hint) / 어노테이션(Annotation) 적용 범위
- 모든 함수 시그니처와 클래스 속성에 annotation 필수
- 공개 API는 완전한 type hint 주석
- mypy strict 모드 통과 목표: `mypy --strict src/`

## 핵심 패턴
```python
from typing import TypeVar, ParamSpec, Protocol, Literal, TypedDict, overload
from collections.abc import Generator, AsyncGenerator

T = TypeVar("T")

# TypedDict — 구조화된 dict type annotation
class Config(TypedDict):
    host: str
    port: int
    debug: bool

# Protocol — 구조적 서브타이핑 (덕타이핑 type hint)
class Readable(Protocol):
    def read(self) -> str: ...

# Literal — 상수 타입 annotation
Mode = Literal["home", "work", "mobile"]
```

## Optional / Union type hint 처리
```python
# Python 3.10+ annotation 방식 (권장)
def get(key: str) -> str | None: ...
def process(val: int | str | None) -> None: ...

# 구버전 호환 annotation
from typing import Optional, Union
def get(key: str) -> Optional[str]: ...
def process(val: Union[int, str, None]) -> None: ...
```

## Generic + ParamSpec type hint
```python
from typing import Callable, ParamSpec
P = ParamSpec("P")

def retry(func: Callable[P, T]) -> Callable[P, T]:
    def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
        return func(*args, **kwargs)
    return wrapper
```

## overload — 다중 시그니처 annotation
```python
from typing import overload

@overload
def process(x: int) -> int: ...
@overload
def process(x: str) -> str: ...
def process(x):
    return x
```

## mypy 설정 (pyproject.toml)
```toml
[tool.mypy]
strict = true
ignore_missing_imports = true
```

## 자주 실수하는 annotation
```python
# BAD — 런타임에만 hint, mypy 무시
from __future__ import annotations  # 전체 파일 annotation 지연

# BAD — 뮤터블 기본값에 type hint만 붙임
def f(lst: list = []) -> None: ...  # hint 있어도 버그

# GOOD
def f(lst: list | None = None) -> None:
    if lst is None:
        lst = []
```
