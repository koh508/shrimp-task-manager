"""스킬: dev_clean_code — 리팩토링 전후 비교 + Guard Clause + 매직 넘버"""
import ast

# ── 1. Guard Clause 리팩토링 ──────────────────────────────────────────────────
class User:
    def __init__(self, name: str, is_active: bool, has_permission: bool):
        self.name = name
        self.is_active = is_active
        self.has_permission = has_permission

def process_bad(user: User | None) -> str:
    """BAD: 깊은 중첩"""
    if user:
        if user.is_active:
            if user.has_permission:
                return f"작업 완료: {user.name}"
    return "실패"

def process_good(user: User | None) -> str:
    """GOOD: Guard Clause — 조기 반환"""
    if not user:
        return "실패"
    if not user.is_active:
        return "실패"
    if not user.has_permission:
        return "실패"
    return f"작업 완료: {user.name}"

# ── 2. 매직 넘버 제거 ─────────────────────────────────────────────────────────
SKILL_SCORE_CUTOFF   = 1.0    # 노이즈 컷오프
SKILL_TOKEN_WEIGHT   = 1.5    # 토큰 overlap 가중치
SKILL_LOG_PENALTY    = 0.03   # 길이 패널티 계수
MAX_SKILL_RESULTS    = 2      # 최대 반환 수

def score_bad(overlap: int, content_len: int) -> float:
    import math
    return round(overlap * 1.5 - math.log(content_len + 1) * 0.03, 2)  # 매직 넘버

def score_good(overlap: int, content_len: int) -> float:
    import math
    return round(
        overlap * SKILL_TOKEN_WEIGHT - math.log(content_len + 1) * SKILL_LOG_PENALTY,
        2
    )

# ── 3. 함수명 명명 규칙 ───────────────────────────────────────────────────────
def validate_function_names(source: str) -> list[str]:
    """함수명이 동사+목적어 패턴인지 검사 (단순 길이 기반)"""
    tree = ast.parse(source)
    bad_names = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            name = node.name
            if not name.startswith("_") and name == name.lower() and "_" not in name and len(name) < 4:
                bad_names.append(name)
    return bad_names

# ── 검증 ─────────────────────────────────────────────────────────────────────
u_ok  = User("고용준", is_active=True,  has_permission=True)
u_no  = User("온유",   is_active=False, has_permission=True)
u_none = None

# BAD와 GOOD이 같은 결과를 내는지
for u, expected in [(u_ok, "작업 완료: 고용준"), (u_no, "실패"), (u_none, "실패")]:
    assert process_bad(u) == process_good(u) == expected
print("  [1] Guard Clause: BAD/GOOD 동일 결과 확인")

# 매직 넘버 제거 후 결과 동일
assert score_bad(3, 500) == score_good(3, 500)
print(f"  [2] 매직 넘버 제거: score={score_good(3, 500)} (동일)")

# 상수 범위 검증
assert 0 < SKILL_SCORE_CUTOFF < 2.0
assert 0 < SKILL_TOKEN_WEIGHT < 3.0
assert 0 < SKILL_LOG_PENALTY  < 0.1
assert 1 <= MAX_SKILL_RESULTS <= 10
print(f"  [3] 상수 범위 유효: cutoff={SKILL_SCORE_CUTOFF}, weight={SKILL_TOKEN_WEIGHT}")

# 함수명 검사
bad_source = "def f(x):\n    pass\ndef proc(d):\n    pass\n"
bad_names = validate_function_names(bad_source)
assert "f" in bad_names
print(f"  [4] 짧은 함수명 탐지: {bad_names}")

print("PASS")
