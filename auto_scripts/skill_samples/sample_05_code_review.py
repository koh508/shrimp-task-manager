"""스킬: dev_code_review — BAD 패턴 탐지 + GOOD 패턴 검증"""
import ast
import re

# ── BAD 패턴 정적 탐지기 ─────────────────────────────────────────────────────
def detect_bad_patterns(source: str) -> list[dict]:
    """코드에서 리뷰 포인트(CRITICAL/WARN/NIT)를 탐지"""
    issues = []

    # [CRITICAL] bare except
    if re.search(r'except\s*:', source):
        issues.append({"severity": "CRITICAL", "pattern": "bare except", "rule": "구체적 예외 타입 명시 필요"})

    # [WARN] 뮤터블 기본 인수
    if re.search(r'def\s+\w+\([^)]*=\s*[\[\{]', source):
        issues.append({"severity": "WARN", "pattern": "mutable default arg", "rule": "def f(x=None) 사용"})

    # [NIT] == None 비교
    if re.search(r'==\s*None', source):
        issues.append({"severity": "NIT", "pattern": "== None", "rule": "is None 사용"})

    # [NIT] == True 비교
    if re.search(r'==\s*True', source):
        issues.append({"severity": "NIT", "pattern": "== True", "rule": "truthy 비교 사용"})

    return issues

# ── 테스트 소스 ───────────────────────────────────────────────────────────────
BAD_CODE = """
def append_item(item, lst=[]):
    try:
        lst.append(item)
    except:
        pass
    if lst == None:
        return []
    if item == True:
        return lst
    return lst
"""

GOOD_CODE = """
def append_item(item, lst=None):
    if lst is None:
        lst = []
    try:
        lst.append(item)
    except TypeError as e:
        raise ValueError(f"item 추가 실패: {e}")
    return lst
"""

# ── Code Smell 카운터 ─────────────────────────────────────────────────────────
def count_smells(source: str) -> dict[str, int]:
    tree = ast.parse(source)
    smells = {"long_functions": 0, "nested_depth": 0}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            lines = node.end_lineno - node.lineno
            if lines > 50:
                smells["long_functions"] += 1
    return smells

# ── 검증 ─────────────────────────────────────────────────────────────────────
bad_issues = detect_bad_patterns(BAD_CODE)
severities = [i["severity"] for i in bad_issues]
patterns   = [i["pattern"] for i in bad_issues]

assert "CRITICAL" in severities, "bare except 탐지 실패"
assert "WARN" in severities,     "mutable default arg 탐지 실패"
assert "NIT" in severities,      "== None 탐지 실패"
print(f"  [1] BAD 패턴 탐지 ({len(bad_issues)}개):")
for i in bad_issues:
    print(f"      [{i['severity']}] {i['pattern']} → {i['rule']}")

good_issues = detect_bad_patterns(GOOD_CODE)
assert len(good_issues) == 0, f"GOOD 코드에서 패턴 탐지됨: {good_issues}"
print(f"  [2] GOOD 코드 검증 통과 (이슈 0개)")

smells = count_smells(GOOD_CODE)
print(f"  [3] Code Smell 카운터: {smells}")

print("PASS")
