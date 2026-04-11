"""스킬: python_typing — TypedDict, Protocol, Literal, overload, Optional"""
from typing import TypedDict, Protocol, Literal, Optional, overload, Union
from typing import runtime_checkable

# ── 1. TypedDict annotation ───────────────────────────────────────────────────
class ServerConfig(TypedDict):
    host: str
    port: int
    debug: bool

def start_server(cfg: ServerConfig) -> str:
    return f"{cfg['host']}:{cfg['port']} (debug={cfg['debug']})"

# ── 2. Protocol — 구조적 서브타이핑 ──────────────────────────────────────────
@runtime_checkable
class Readable(Protocol):
    def read(self) -> str: ...

class FileReader:
    def read(self) -> str:
        return "file content"

class SocketReader:
    def read(self) -> str:
        return "socket content"

def consume(reader: Readable) -> str:
    return reader.read()

# ── 3. Literal — 상수 타입 annotation ────────────────────────────────────────
Mode = Literal["home", "work", "mobile"]

def get_timeout(mode: Mode) -> int:
    timeouts: dict[str, int] = {"home": 30, "work": 10, "mobile": 60}
    return timeouts[mode]

# ── 4. overload — 다중 시그니처 ───────────────────────────────────────────────
@overload
def process(x: int) -> int: ...
@overload
def process(x: str) -> str: ...
def process(x: Union[int, str]) -> Union[int, str]:
    if isinstance(x, int):
        return x * 2
    return x.upper()

# ── 5. Optional annotation ────────────────────────────────────────────────────
def find_user(user_id: int) -> Optional[str]:
    db = {1: "고용준", 2: "온유"}
    return db.get(user_id)  # str | None

# ── 검증 ─────────────────────────────────────────────────────────────────────
cfg: ServerConfig = {"host": "localhost", "port": 8000, "debug": True}
assert start_server(cfg) == "localhost:8000 (debug=True)"
print(f"  [1] TypedDict : {start_server(cfg)}")

assert isinstance(FileReader(), Readable)
assert isinstance(SocketReader(), Readable)
assert consume(FileReader()) == "file content"
print(f"  [2] Protocol  : isinstance 체크 통과")

assert get_timeout("home") == 30
assert get_timeout("mobile") == 60
print(f"  [3] Literal   : timeout home={get_timeout('home')}, mobile={get_timeout('mobile')}")

assert process(21) == 42
assert process("hello") == "HELLO"
print(f"  [4] overload  : process(21)={process(21)}, process('hello')={process('hello')}")

assert find_user(1) == "고용준"
assert find_user(99) is None
print(f"  [5] Optional  : find_user(1)={find_user(1)}, find_user(99)={find_user(99)}")

print("PASS")
