"""
온유 Skills MCP 서버 (skills_server.py)
SYSTEM/skills/optional/ 및 experimental/ 폴더의 스킬을 온디맨드로 제공.

[설계 원칙]
- LanceDB 완전 배제 (deadlock 방지)
- 순수 Python 파일 스캔 + Token Overlap Scoring
- 로그 기반 길이 패널티 + score < 1.0 노이즈 컷오프
- mtime 기반 캐시 (추가/수정/삭제 모두 감지)
- Windows 파일 잠금 안전 처리

[로그 포맷]
  [SKILL_HIT]  query → fname | score=N.NN    (검색 결과 있음)
  [SKILL_MISS] query → 매칭 없음 (fallback)   (결과 없음)
  [SKILL_SKIP] fname — 파일 잠금 건너뜀        (Windows lock)
  [SKILL_LOAD] fname — 캐시 로드/갱신          (캐시 갱신)
  [SKILL_DROP] fname — 캐시에서 제거           (파일 삭제)
"""

import os
import math
import logging

import mcp.server.fastmcp as _fastmcp

logger = logging.getLogger(__name__)

# ── 경로 상수 ──────────────────────────────────────────────────────────────────
_THIS_DIR   = os.path.dirname(os.path.abspath(__file__))
_SYSTEM_DIR = os.path.dirname(_THIS_DIR)
_SKILLS_DIR = os.path.join(_SYSTEM_DIR, "skills")
_OPTIONAL_DIR     = os.path.join(_SKILLS_DIR, "optional")
_EXPERIMENTAL_DIR = os.path.join(_SKILLS_DIR, "experimental")

# ── 캐시 ──────────────────────────────────────────────────────────────────────
# { filepath: {"content": str, "mtime": float} }
_CACHE: dict[str, dict] = {}

mcp = _fastmcp.FastMCP("skills_server")


# ══════════════════════════════════════════════════════════════════════════════
# 내부 캐시 관리
# ══════════════════════════════════════════════════════════════════════════════

def _read_safe(fpath: str) -> str | None:
    """파일 읽기. Windows 잠금 시 None 반환."""
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            return f.read()
    except OSError as e:
        logger.debug("[SKILL_SKIP] %s — %s", os.path.basename(fpath), e)
        return None


def _scan_dir(dirpath: str) -> list[str]:
    """디렉토리의 .md 파일 경로 목록 (알파벳 순)."""
    if not os.path.isdir(dirpath):
        return []
    return sorted(
        os.path.join(dirpath, f)
        for f in os.listdir(dirpath)
        if f.endswith(".md") and not f.startswith(".")
    )


def _refresh_cache() -> None:
    """
    optional/ + experimental/ 스캔 → 캐시 동기화.
    - 새 파일: 로드
    - 수정된 파일: 재로드
    - 삭제된 파일: 제거
    """
    current_files = set(
        _scan_dir(_OPTIONAL_DIR) + _scan_dir(_EXPERIMENTAL_DIR)
    )
    cached_files = set(_CACHE.keys())

    # 삭제된 파일 제거
    for fp in cached_files - current_files:
        _CACHE.pop(fp, None)
        logger.debug("[SKILL_DROP] %s", os.path.basename(fp))

    # 추가 / 수정 파일 로드
    for fp in current_files:
        try:
            mtime = os.path.getmtime(fp)
        except OSError:
            continue
        cached = _CACHE.get(fp)
        if cached is None or cached["mtime"] != mtime:
            content = _read_safe(fp)
            if content:
                _CACHE[fp] = {"content": content.strip(), "mtime": mtime}
                logger.debug("[SKILL_LOAD] %s", os.path.basename(fp))


# ══════════════════════════════════════════════════════════════════════════════
# 스코어링 엔진
# ══════════════════════════════════════════════════════════════════════════════

def _score(query: str, fname: str, content: str) -> float:
    """Token Overlap + 파일명 매칭 - Log 길이 패널티."""
    q_lower = query.lower()
    c_lower = content.lower()

    # [+3] 파일명 키워드 매칭
    score = 3.0 if q_lower in os.path.basename(fname).lower() else 0.0

    # [+1.5 per token] 토큰 overlap
    q_tokens = set(q_lower.split())
    c_tokens = set(c_lower.split())
    overlap  = len(q_tokens & c_tokens)
    score   += overlap * 1.5

    # [+0.5 per freq] 본문 빈도
    score += c_lower.count(q_lower) * 0.5

    # [-log penalty] 긴 스킬 패널티 완화 (log 기반, 계수 0.03 — 과도한 패널티 방지)
    score -= math.log(len(content) + 1) * 0.03

    return round(score, 2)


# ══════════════════════════════════════════════════════════════════════════════
# MCP 도구
# ══════════════════════════════════════════════════════════════════════════════

@mcp.tool()
def list_skills() -> str:
    """사용 가능한 선택적 스킬 목록을 반환합니다.
    코딩/전문 작업 시작 전 이 도구로 관련 스킬을 확인하세요.
    """
    _refresh_cache()
    if not _CACHE:
        return "현재 로드된 스킬이 없습니다. (skills/optional/, skills/experimental/ 확인)"

    lines = []
    for fp in sorted(_CACHE.keys()):
        rel = os.path.relpath(fp, _SKILLS_DIR)
        first_line = _CACHE[fp]["content"].split("\n")[0].lstrip("# ").strip()
        lines.append(f"- {rel}  →  {first_line}")

    return "## 사용 가능한 스킬\n" + "\n".join(lines)


@mcp.tool()
def get_skill(name: str) -> str:
    """특정 스킬 파일의 전체 내용을 반환합니다.

    Args:
        name: 파일명 또는 경로 일부 (예: 'python_typing', 'exp_fix_import')
    """
    _refresh_cache()
    name_lower = name.lower().replace(".md", "")

    for fp, data in _CACHE.items():
        if name_lower in os.path.basename(fp).lower():
            logger.info("[SKILL_HIT] get_skill(%s) → %s", name, os.path.basename(fp))
            return data["content"]

    return f"스킬 '{name}'을 찾을 수 없습니다. list_skills()로 목록을 확인하세요."


@mcp.tool()
def search_skills(query: str, top_k: int = 2) -> str:
    """키워드로 관련 스킬을 검색하여 상위 결과를 반환합니다.
    에러 수정, 코드 패턴 참조, 특정 기술 스택 작업 시 활용하세요.

    Args:
        query: 검색 키워드 또는 문장
        top_k: 반환할 최대 스킬 수 (기본 2)
    """
    _refresh_cache()

    if not _CACHE:
        logger.info("[SKILL_MISS] query='%s' — 캐시 비어있음", query[:40])
        return "검색 가능한 스킬이 없습니다."

    results = []
    for fp, data in _CACHE.items():
        s = _score(query, fp, data["content"])
        if s >= 1.0:  # 노이즈 컷오프
            results.append((s, fp, data["content"]))

    if not results:
        logger.info("[SKILL_MISS] query='%s' — score < 1.0 전부 컷", query[:40])
        return f"'{query}'에 매칭되는 스킬이 없습니다."

    results.sort(key=lambda x: x[0], reverse=True)

    for score, fp, _ in results[:top_k]:
        logger.info("[SKILL_HIT] query='%s' → %s | score=%.2f",
                    query[:40], os.path.basename(fp), score)

    return "\n\n---\n\n".join(r[2] for r in results[:top_k])


@mcp.tool()
def reload_skills() -> str:
    """스킬 캐시를 강제 갱신합니다.
    skills/experimental/ 에 새 스킬을 저장한 직후 호출하여 즉시 반영하세요.
    """
    before = set(_CACHE.keys())
    _refresh_cache()
    after = set(_CACHE.keys())

    added   = after - before
    removed = before - after
    updated = after & before

    parts = [f"✅ 스킬 캐시 갱신 완료 ({len(after)}개)"]
    if added:
        parts.append(f"  추가: {', '.join(os.path.basename(f) for f in added)}")
    if removed:
        parts.append(f"  제거: {', '.join(os.path.basename(f) for f in removed)}")
    parts.append(f"  유지: {len(updated)}개")
    return "\n".join(parts)


# ── 서버 시작 시 캐시 초기화 ──────────────────────────────────────────────────
_refresh_cache()
logger.info("[SKILL_LOAD] skills_server 초기화 완료 (%d개 로드)", len(_CACHE))

if __name__ == "__main__":
    mcp.run()
