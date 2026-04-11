"""
온유 Study MCP 서버 (study_server.py)
학습 관련 도구를 제공하는 독립 MCP 서버.

실행 (단독):  python study_server.py
smolagents가 StdioServerParameters로 subprocess로 실행함.
"""
import os, sys, json, re, hashlib, random
from datetime import datetime, timedelta
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# ── 경로 설정 ──────────────────────────────────────────────────────────────────
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
QUIZ_HISTORY_FILE   = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "quiz_history.json")
NIGHT_STUDY_DIR     = os.path.join(OBSIDIAN_VAULT_PATH, "야간학습")
QUIZ_COOLDOWN_DAYS  = 3

mcp = FastMCP("onew-study")

# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────
def _atomic_write(filepath: str, data: dict):
    tmp = filepath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, filepath)

def _load_quiz_history() -> dict:
    try:
        if os.path.exists(QUIZ_HISTORY_FILE):
            with open(QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"asked": []}

def _save_quiz_history(h: dict):
    try:
        _atomic_write(QUIZ_HISTORY_FILE, h)
    except:
        pass

def _question_hash(q_text: str) -> str:
    return hashlib.md5(q_text.strip().encode("utf-8")).hexdigest()[:12]

def _clean_latex(text: str) -> str:
    t = text
    for _ in range(5):
        t = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", t)
    t = re.sub(r"\\text\{([^{}]+)\}", r"\1", t)
    t = re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", t)
    t = re.sub(r"\^\{([^{}]+)\}", r"^\1", t)
    t = re.sub(r"_\{([^{}]+)\}", r"_\1", t)
    replacements = [
        (r"\\approx", "≈"), (r"\\times", "×"), (r"\\cdot", "·"),
        (r"\\circ", "°"), (r"\\degree", "°"), (r"\\Delta", "Δ"),
        (r"\\delta", "δ"), (r"\\alpha", "α"), (r"\\beta", "β"),
        (r"\\gamma", "γ"), (r"\\eta", "η"), (r"\\rho", "ρ"),
        (r"\\mu", "μ"), (r"\\sum", "Σ"),
        (r"\\sqrt\{([^{}]+)\}", r"√(\1)"), (r"\\sqrt", "√"),
        (r"\\geq", "≥"), (r"\\leq", "≤"), (r"\\neq", "≠"),
        (r"\\infty", "∞"), (r"\\left", ""), (r"\\right", ""),
        (r"\\\[", ""), (r"\\\]", ""), (r"\\\\", " "),
    ]
    for pattern, repl in replacements:
        t = re.sub(pattern, repl, t)
    sup = {"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹"}
    t = re.sub(r"\^(\d+)", lambda m: "".join(sup.get(c, c) for c in m.group(1)), t)
    t = re.sub(r"\$\$(.+?)\$\$", r"\1", t, flags=re.DOTALL)
    t = re.sub(r"\$(.+?)\$", r"\1", t)
    t = re.sub(r"[{}]", "", t)
    t = re.sub(r"\[\[.+?\|(.+?)\]\]", r"\1", t)
    t = re.sub(r"\[\[(.+?)\]\]", r"\1", t)
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\^°", "°", t)
    t = re.sub(r"\^(\s)", r"\1", t)
    return re.sub(r"  +", " ", t).strip()

def _is_calc_heavy(question: str, answer: str) -> bool:
    combined = question + " " + answer
    if len(re.findall(r"\$[^$]+\$", combined)) >= 2:
        return True
    calc_kw = ["계산하시오", "계산하라", "구하시오", "구하라", "값을 구", "수치를",
               "몇 kW", "몇 kJ", "몇 W", "몇 kg", "몇 m", "몇 Pa", "몇 bar",
               "계산 과정", "풀이 과정"]
    if any(kw in combined for kw in calc_kw):
        return True
    if len(re.findall(r"\d+[\.,]?\d*\s*(?:kW|kJ|W|kg|m²|m³|Pa|bar|°C|RPM|%|kcal)", combined)) >= 3:
        return True
    return False

def _parse_questions_from_file(fpath: str) -> list:
    questions = []
    try:
        text = Path(fpath).read_text(encoding="utf-8")
        sections = re.split(r"\n## 📝 (.+)", text)
        pairs = []
        if len(sections) >= 3:
            for i in range(1, len(sections), 2):
                pairs.append((sections[i].strip(), sections[i+1] if i+1 < len(sections) else ""))
        else:
            pairs.append((Path(fpath).stem, text))

        for source, body in pairs:
            blocks = re.split(r"\n(?=\s*\d+[\.\)]\s+)", body)
            for block in blocks:
                q_match = re.match(r"\s*\d+[\.\)]\s+(?:\(문제\)\s*)?(.+?)(?:\n|$)", block)
                if not q_match:
                    continue
                q_text = q_match.group(1).strip()
                q_text = re.sub(r"^\*?\*?\(문제\)\*?\*?\s*", "", q_text).strip()
                q_text = re.sub(r"^\*\*문제\)\*\*\s*", "", q_text).strip()
                if not q_text or q_text in ("(문제)", "**문제)**", ""):
                    continue

                a_match = re.search(r"정답\s*[:：]\s*(.+?)(?:\n\s*해설|---|\Z)", block, re.DOTALL)
                answer = ""
                if a_match:
                    answer = re.sub(r"\s+", " ", a_match.group(1)).strip()[:200]

                e_match = re.search(r"해설\s*[:：]\s*(.+?)(?:\n\s*\d+[\.\)]|---|\Z)", block, re.DOTALL)
                explain = ""
                if e_match:
                    explain = re.sub(r"\s+", " ", e_match.group(1)).strip()[:150]

                if not answer:
                    continue

                questions.append({
                    "question": q_text, "answer": answer,
                    "explain": explain, "source": source, "file": fpath,
                })
    except:
        pass
    return questions

# ── MCP Tool ───────────────────────────────────────────────────────────────────
@mcp.tool()
def quiz_me(category: str = None, count: int = 3, exclude_calc: bool = True) -> str:
    """야간학습 폴더에서 예상 문제를 가져와 퀴즈 세트를 반환합니다.

    Args:
        category: 카테고리 필터. '공조냉동' / '소방' / '현장' / 'AI클리핑' / None(전체)
                  반드시 야간학습/ 폴더명과 정확히 일치해야 함.
        count: 출제 문제 수 (기본 3, 최대 5)
        exclude_calc: True(기본) → 수치 계산 문제 제외
    """
    if not os.path.exists(NIGHT_STUDY_DIR):
        return "야간학습 폴더가 없습니다. 자율학습이 아직 실행되지 않았을 수 있습니다."

    count = min(max(1, count), 5)
    history = _load_quiz_history()
    cutoff  = (datetime.now() - timedelta(days=QUIZ_COOLDOWN_DAYS)).strftime("%Y-%m-%d")
    recent_hashes = {
        e["hash"] for e in history.get("asked", [])
        if e.get("date", "0000-00-00") >= cutoff
    }

    # 카테고리 필터 (정확한 최상위 폴더명 매칭)
    all_files = []
    for root, dirs, files in os.walk(NIGHT_STUDY_DIR):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        if category:
            rel = os.path.relpath(root, NIGHT_STUDY_DIR)
            if rel != ".":
                top_folder = rel.split(os.sep)[0]
                if top_folder != category:
                    continue
        for f in files:
            if f.endswith(".md"):
                all_files.append(os.path.join(root, f))

    if not all_files:
        msg = f"'{category}' 카테고리의 야간학습 파일이 없습니다." if category else "야간학습 파일이 없습니다."
        return msg + " 자율학습이 실행된 후 다시 시도하세요."

    all_questions = []
    for fp in all_files:
        for q in _parse_questions_from_file(fp):
            q["question"] = _clean_latex(q["question"])
            q["answer"]   = _clean_latex(q["answer"])
            q["explain"]  = _clean_latex(q["explain"])
            all_questions.append(q)

    if not all_questions:
        return "야간학습 파일은 있으나 파싱 가능한 문제가 없습니다."

    if exclude_calc:
        filtered = [q for q in all_questions if not _is_calc_heavy(q["question"], q["answer"])]
        if len(filtered) >= count:
            all_questions = filtered

    fresh  = [q for q in all_questions if _question_hash(q["question"]) not in recent_hashes]
    pool   = fresh if len(fresh) >= count else all_questions
    selected = random.sample(pool, min(count, len(pool)))

    today = datetime.now().strftime("%Y-%m-%d")
    asked_list = history.get("asked", [])
    for q in selected:
        asked_list.append({"hash": _question_hash(q["question"]), "date": today})
    history["asked"] = asked_list[-500:]
    _save_quiz_history(history)

    lines = [f"퀴즈 {len(selected)}문제 준비됨 (카테고리: {category or '전체'})\n"]
    for i, q in enumerate(selected, 1):
        lines.append(
            f"[Q{i}]\n"
            f"문제: {q['question']}\n"
            f"정답: {q['answer']}\n"
            f"해설: {q['explain']}\n"
            f"출처: {q['source']}\n"
        )
    lines.append("--- 진행 방법: 문제 하나씩 제시 → 답변 후 정답+해설 공개 → 마지막에 총점 ---")
    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run()
