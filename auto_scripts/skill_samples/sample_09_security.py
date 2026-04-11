"""스킬: security_best_practices — 입력 검증 + 경로 보호 + 시크릿 마스킹"""
import os
import re
from pathlib import Path

# ── 1. 파일명 검증 (경로 탐색 공격 방지) ─────────────────────────────────────
def validate_filename(fname: str) -> str:
    fname = os.path.basename(fname)
    if not re.match(r'^[\w\-. ]+$', fname):
        raise ValueError(f"허용되지 않는 파일명: {fname}")
    return fname

# ── 2. 쿼리 검증 (인젝션 방지) ────────────────────────────────────────────────
def validate_query(query: str, max_len: int = 500) -> str:
    if len(query) > max_len:
        raise ValueError(f"쿼리가 너무 깁니다 ({len(query)} > {max_len})")
    return query.strip()

# ── 3. 경로 탈출 방지 ─────────────────────────────────────────────────────────
VAULT_ROOT = Path("C:/Users/User/Documents/Obsidian Vault")
PROTECTED_DIRS = {"SYSTEM/skills/core", "SYSTEM/skills/domain", "SYSTEM/skills/optional"}

def is_safe_path(target: Path) -> bool:
    try:
        target.resolve().relative_to(VAULT_ROOT.resolve())
        return True
    except ValueError:
        return False

def is_protected(target: Path) -> bool:
    rel = str(target).replace("\\", "/")
    return any(protected in rel for protected in PROTECTED_DIRS)

# ── 4. 시크릿 마스킹 ──────────────────────────────────────────────────────────
def mask_secret(secret: str, visible: int = 4) -> str:
    if len(secret) <= visible * 2:
        return "*" * len(secret)
    return secret[:visible] + "..." + secret[-visible:]

# ── 검증 ─────────────────────────────────────────────────────────────────────
# 파일명 검증
assert validate_filename("python_async.md") == "python_async.md"
assert validate_filename("../../../etc/passwd") == "passwd"   # basename으로 공격 차단
try:
    validate_filename("file<script>.md")
    assert False
except ValueError:
    pass
print("  [1] validate_filename: OK")

# 쿼리 검증
assert validate_query("  python async  ") == "python async"
try:
    validate_query("A" * 501)
    assert False
except ValueError:
    pass
print("  [2] validate_query: OK")

# 경로 보호
safe   = Path("C:/Users/User/Documents/Obsidian Vault/DAILY/2026-03-25.md")
unsafe = Path("C:/Users/User/Desktop/secret.txt")
protected = Path("C:/Users/User/Documents/Obsidian Vault/SYSTEM/skills/core/01_identity.md")

assert is_safe_path(safe)
assert not is_safe_path(unsafe)
assert is_protected(protected)
assert not is_protected(safe)
print("  [3] path protection: OK")

# 시크릿 마스킹
api_key = "sk-abc123xyz456def789"
masked = mask_secret(api_key)
assert api_key not in masked
assert masked.startswith("sk-a")
assert masked.endswith("f789")
print(f"  [4] mask: '{api_key}' -> '{masked}'")

print("PASS")
