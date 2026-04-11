"""
onew_make_work_index.py — 온유/Claude Code 최근 작업 인덱스 자동 생성

출력: SYSTEM/onew_work_index.md
- API 호출 없음 (순수 파일 읽기)
- Claude Code가 단일 파일 Read로 최근 작업 전체 파악 가능
- 온유의 작업(코드변경이력)과 Claude Code 작업(작업일지) 모두 포함
"""
import json, os, re
from datetime import datetime, timedelta
from pathlib import Path

SCRIPT_DIR    = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH    = str(Path(SCRIPT_DIR).parent)
OUTPUT_FILE   = os.path.join(SCRIPT_DIR, "onew_work_index.md")
WORK_LOG_DIR  = os.path.join(VAULT_PATH, "작업일지")
CODE_HIST_DIR = os.path.join(SCRIPT_DIR, "코드변경이력")
SUMMARY_FILE  = os.path.join(SCRIPT_DIR, "interface_summary.json")
DAYS_BACK     = 14  # 최근 N일치 포함


def _read_head(path: str, max_chars: int = 600) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read(max_chars + 200)
        # YAML 프론트매터 제거
        body = re.sub(r'^---[\s\S]*?---\n?', '', raw).strip()
        return body[:max_chars]
    except:
        return ""


def _extract_title(path: str) -> str:
    """파일명에서 날짜 제거 후 제목 추출."""
    name = Path(path).stem
    name = re.sub(r'^\d{4}-\d{2}-\d{2}_?', '', name)   # 날짜 제거
    name = re.sub(r'_\d{4}$', '', name)                  # 시간 제거 (1427 등)
    return name.replace('_', ' ')


def _get_date_from_name(path: str):
    m = re.search(r'(\d{4}-\d{2}-\d{2})', Path(path).name)
    if m:
        try: return datetime.strptime(m.group(1), "%Y-%m-%d")
        except: pass
    return datetime.fromtimestamp(os.path.getmtime(path))


def build_index() -> str:
    cutoff = datetime.now() - timedelta(days=DAYS_BACK)
    lines  = []
    today  = datetime.now().strftime("%Y-%m-%d %H:%M")

    lines.append(f"# 온유 ↔ Claude Code 최근 작업 인덱스")
    lines.append(f"> 자동 생성: {today} | 최근 {DAYS_BACK}일 | API 비용: 0원\n")
    lines.append("> Claude Code에서 이 파일 Read 1회로 전체 맥락 파악 가능.\n")

    # ── 1. Claude Code 작업일지 ──────────────────────────────────────────────
    lines.append("## Claude Code 작업일지\n")
    work_logs = []
    if os.path.isdir(WORK_LOG_DIR):
        for f in sorted(Path(WORK_LOG_DIR).glob("*.md"), reverse=True):
            if _get_date_from_name(str(f)) >= cutoff:
                work_logs.append(f)

    if not work_logs:
        lines.append("*(최근 작업 없음)*\n")
    else:
        current_date = ""
        for f in work_logs:
            fdate = _get_date_from_name(str(f)).strftime("%Y-%m-%d")
            if fdate != current_date:
                lines.append(f"\n### {fdate}")
                current_date = fdate
            title   = _extract_title(str(f))
            preview = _read_head(str(f), 300)
            # 변경 파일 목록 추출
            changed = re.findall(r'[`\*]([^\s`\*]+\.(?:py|md|json|bat))[`\*]?', preview)
            changed_str = " → " + ", ".join(list(dict.fromkeys(changed))[:4]) if changed else ""
            lines.append(f"- **{title}**{changed_str}")
            # 핵심 내용 1줄 추출 (## 다음 첫 번째 비어있지 않은 줄)
            m = re.search(r'##[^\n]*\n+([^\n#\-\*]{10,})', preview)
            if m:
                lines.append(f"  _{m.group(1).strip()[:120]}_")
        lines.append("")

    # ── 2. 온유 자율코딩 변경이력 ────────────────────────────────────────────
    lines.append("## 온유 자율코딩 변경이력\n")
    code_hists = []
    if os.path.isdir(CODE_HIST_DIR):
        for f in sorted(Path(CODE_HIST_DIR).glob("*.md"), reverse=True):
            if _get_date_from_name(str(f)) >= cutoff:
                code_hists.append(f)

    if not code_hists:
        lines.append("*(최근 자율코딩 없음)*\n")
    else:
        for f in code_hists:
            fdate = _get_date_from_name(str(f)).strftime("%Y-%m-%d %H:%M")
            title = _extract_title(str(f))
            preview = _read_head(str(f), 200)
            lines.append(f"- **{fdate}** {title}")
            m = re.search(r'##[^\n]*\n+([^\n#]{10,})', preview)
            if m:
                lines.append(f"  _{m.group(1).strip()[:100]}_")
        lines.append("")

    # ── 3. 현재 코드 상태 (interface_summary) ───────────────────────────────
    lines.append("## 현재 코드 상태 (interface_summary.json)\n")
    try:
        with open(SUMMARY_FILE, "r", encoding="utf-8") as f:
            summary = json.load(f)
        for fname, desc in summary.items():
            lines.append(f"- `{fname}`: {desc}")
    except:
        lines.append("*(interface_summary.json 읽기 실패)*")
    lines.append("")

    # ── 4. API 사용량 요약 ───────────────────────────────────────────────────
    lines.append("## 최근 API 사용량\n")
    usage_file = os.path.join(SCRIPT_DIR, "api_usage_log.json")
    try:
        with open(usage_file, "r", encoding="utf-8") as f:
            usage = json.load(f)
        recent_dates = sorted(
            {k.split("_")[-1] for k in usage if re.match(r'.*\d{4}-\d{2}-\d{2}$', k)},
            reverse=True)[:5]
        for d in recent_dates:
            total = usage.get(d, 0)
            chat  = usage.get(f"chat_{d}", 0)
            rag   = usage.get(f"rag_{d}", 0)
            ns    = usage.get(f"night_study_{d}", 0)
            lines.append(f"- {d}: 총 {total} | chat {chat} | rag {rag} | 야간학습 {ns}")
    except:
        lines.append("*(사용량 로그 읽기 실패)*")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys
    sys.stdout.reconfigure(encoding="utf-8")
    result = build_index()
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(result)
    line_count = result.count("\n")
    print(f"[작업인덱스] 생성 완료 → onew_work_index.md ({line_count}줄)")
