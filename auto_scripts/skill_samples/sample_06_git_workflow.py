"""스킬: dev_git_workflow — Conventional Commit 생성기 + 브랜치명 검증"""
import re

# ── Conventional Commit 생성기 ────────────────────────────────────────────────
VALID_TYPES = {"feat", "fix", "refactor", "docs", "chore", "test", "style", "perf"}

def make_commit_message(type_: str, scope: str, summary: str, body: str = "") -> str:
    if type_ not in VALID_TYPES:
        raise ValueError(f"잘못된 type: '{type_}'. 허용: {VALID_TYPES}")
    if not summary.strip():
        raise ValueError("summary는 비어 있을 수 없습니다")
    if len(summary) > 72:
        raise ValueError(f"summary가 너무 깁니다 ({len(summary)}자 > 72자)")
    header = f"{type_}({scope}): {summary}" if scope else f"{type_}: {summary}"
    return f"{header}\n\n{body}".strip() if body else header

def parse_commit_message(msg: str) -> dict:
    pattern = r'^(\w+)(?:\(([^)]+)\))?: (.+)$'
    m = re.match(pattern, msg.split("\n")[0])
    if not m:
        raise ValueError(f"Conventional Commit 형식 불일치: {msg}")
    return {"type": m.group(1), "scope": m.group(2), "summary": m.group(3)}

# ── 브랜치명 검증 ─────────────────────────────────────────────────────────────
BRANCH_PREFIXES = {"feature", "fix", "hotfix", "release", "chore"}

def validate_branch_name(branch: str) -> bool:
    """branch 명명 규칙: prefix/kebab-case-description"""
    pattern = r'^(feature|fix|hotfix|release|chore)/[\w\-]+$'
    return bool(re.match(pattern, branch))

# ── 검증 ─────────────────────────────────────────────────────────────────────
# 커밋 메시지 생성
msg1 = make_commit_message("fix", "session", "LanceDB deadlock preload 시점 변경")
assert msg1 == "fix(session): LanceDB deadlock preload 시점 변경"
print(f"  [1] commit: {msg1}")

msg2 = make_commit_message("feat", "", "skills MCP 서버 추가")
assert msg2 == "feat: skills MCP 서버 추가"
print(f"  [2] no-scope: {msg2}")

# 커밋 파싱
parsed = parse_commit_message("refactor(agent): MCP 연결 로직 분리")
assert parsed == {"type": "refactor", "scope": "agent", "summary": "MCP 연결 로직 분리"}
print(f"  [3] 파싱: {parsed}")

# 잘못된 type
try:
    make_commit_message("update", "core", "뭔가 수정")
    assert False, "예외 미발생"
except ValueError as e:
    print(f"  [4] 잘못된 type 차단: {e}")

# 브랜치명 검증
valid_branches = ["feature/mcp-skills", "fix/lancedb-deadlock", "hotfix/session-crash"]
invalid_branches = ["main", "Feature/test", "fix_lancedb", "feature/"]

for b in valid_branches:
    assert validate_branch_name(b), f"유효한 branch 거부됨: {b}"
for b in invalid_branches:
    assert not validate_branch_name(b), f"무효한 branch 통과됨: {b}"

print(f"  [5] branch 검증: 유효 {len(valid_branches)}개, 무효 {len(invalid_branches)}개 정확히 분류")
print("PASS")
