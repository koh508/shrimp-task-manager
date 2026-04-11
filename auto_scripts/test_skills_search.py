"""
스킬 검색 기능 테스트 — 11개 optional 스킬 각각 1개 쿼리로 검증
search_skills()가 올바른 스킬을 score >= 1.0으로 반환하는지 확인
"""

import os
import sys
import math

# skills_server의 _score 함수 직접 재현 (MCP 서버 임포트 없이 독립 실행)
SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OPTIONAL_DIR = os.path.join(SYSTEM_DIR, "skills", "optional")


def _score(query: str, fname: str, content: str) -> float:
    q = query.lower()
    c = content.lower()
    score = 3.0 if q in os.path.basename(fname).lower() else 0.0
    score += len(set(q.split()) & set(c.split())) * 1.5
    score += c.count(q) * 0.5
    score -= math.log(len(content) + 1) * 0.03
    return round(score, 2)


def load_skills() -> dict:
    skills = {}
    for fname in sorted(os.listdir(OPTIONAL_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(OPTIONAL_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                skills[fpath] = f.read().strip()
        except OSError:
            pass
    return skills


def search(query: str, skills: dict, top_k: int = 2) -> list:
    results = []
    for fp, content in skills.items():
        s = _score(query, fp, content)
        if s >= 1.0:
            results.append((s, os.path.basename(fp), content[:60]))
    results.sort(reverse=True)
    return results[:top_k]


# ── 테스트 케이스: (쿼리, 기대 파일명 일부) ──────────────────────────────────
TEST_CASES = [
    ("python async await coroutine",          "python_async"),
    ("type hint annotation TypedDict",        "python_typing"),
    ("pytest fixture mock 테스트",             "python_testing"),
    ("lancedb sqlalchemy async session",      "python_db"),
    ("review checklist CRITICAL WARN NIT severity",  "dev_code_review"),
    ("git commit conventional branch",        "dev_git_workflow"),
    ("dockerfile container compose",          "dev_docker"),
    ("clean code 명명 조기 반환 매직 넘버",       "dev_clean_code"),
    ("security 시크릿 환경변수 인젝션",           "security_best_practices"),
    ("prompt engineering few-shot CoT",       "ai_prompt_engineering"),
    ("productivity ICE 우선순위 ADHD",          "productivity_planning"),
]

# ── 실행 ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    skills = load_skills()
    print(f"로드된 스킬: {len(skills)}개\n")
    print(f"{'#':<3} {'쿼리':<38} {'결과':<6} {'매칭 파일':<30} {'score'}")
    print("-" * 90)

    passed = 0
    for i, (query, expected) in enumerate(TEST_CASES, 1):
        results = search(query, skills)
        if results:
            score, fname, _ = results[0]
            ok = expected in fname
            status = "PASS" if ok else "FAIL"
            if ok:
                passed += 1
            print(f"{i:<3} {query[:37]:<38} {status:<6} {fname:<30} {score}")
        else:
            print(f"{i:<3} {query[:37]:<38} {'MISS':<6} {'(매칭 없음)':<30} -")

    print("-" * 90)
    print(f"\n결과: {passed}/{len(TEST_CASES)} 통과")
    sys.exit(0 if passed == len(TEST_CASES) else 1)
