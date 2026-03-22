#!/usr/bin/env python3
"""
onew_code_indexer.py
obsidian_agent.py → 온유_코드구조.md 자동 생성 (AST 파싱, 토큰 소모 없음)
생성 후 LanceDB 임베딩 갱신 (변경된 파일 1개만, embedding API 1회/청크)

사용:
  python onew_code_indexer.py           # 직접 실행 (강제 재생성 + 임베딩)
  python onew_code_indexer.py --hook    # Claude Code 훅 모드 (stdin JSON 확인 후 조건부 실행)
"""

import ast
import json
import os
import re
import sys
from datetime import datetime

SCRIPT_DIR  = os.path.dirname(os.path.abspath(__file__))
AGENT_PATH  = os.path.join(SCRIPT_DIR, "obsidian_agent.py")
OUTPUT_PATH = os.path.join(SCRIPT_DIR, "온유_코드구조.md")
LANCE_DB_DIR = os.path.join(SCRIPT_DIR, ".onew_lance_db")
EMBED_DIM   = 3072

_TOOL_LIST_PAT = re.compile(r'onew_tools\s*=\s*\[([^\]]+)\]', re.DOTALL)


# ── AST 추출 함수들 ────────────────────────────────────────────────────────────

def _extract_constants(tree, source: str) -> list:
    result = []
    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id.isupper():
                    val = ast.get_source_segment(source, node.value) or "..."
                    val = val.replace("\n", " ").strip()[:80]
                    result.append((target.id, val))
    return result


def _extract_classes(tree) -> list:
    classes = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            cls_doc = ast.get_docstring(node) or ""
            methods = []
            for item in node.body:
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    m_doc = ast.get_docstring(item) or ""
                    methods.append((item.lineno, item.name, m_doc[:100]))
            methods.sort(key=lambda x: x[0])
            classes.append((node.lineno, node.name, cls_doc[:120], methods))
    return classes


def _extract_functions(tree) -> list:
    result = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            doc = ast.get_docstring(node) or ""
            result.append((node.lineno, node.name, doc[:100]))
    return result


def _extract_tool_names(source: str) -> list:
    m = _TOOL_LIST_PAT.search(source)
    if not m:
        return []
    block = m.group(1)
    lines = [ln.strip() for ln in block.splitlines() if not ln.strip().startswith('#')]
    block_clean = " ".join(lines)
    import_names = re.findall(r"__import__\('[^']+'\)\.(\w+)", block_clean)
    simple = re.findall(r'\b([a-zA-Z_]\w*)\b', block_clean)
    skip = {'__import__', 'True', 'False', 'None', 'and', 'or', 'not', 'in', 'is'}
    names = [n for n in simple if n not in skip and not n.startswith('__')]
    return list(dict.fromkeys(names + import_names))


# ── 청크 분할 ─────────────────────────────────────────────────────────────────

def _split_chunks(content: str, max_chars: int = 1500) -> list:
    """## 헤더 기준으로 청크 분할. 짧은 청크는 병합."""
    parts = re.split(r'\n(?=## )', content)
    chunks = []
    buf = ""
    for part in parts:
        if len(buf) + len(part) < max_chars:
            buf += "\n" + part if buf else part
        else:
            if buf:
                chunks.append(buf.strip())
            buf = part
    if buf:
        chunks.append(buf.strip())
    return [c for c in chunks if len(c) > 30]


# ── LanceDB 임베딩 갱신 ───────────────────────────────────────────────────────

def embed_after_build() -> str:
    """온유_코드구조.md를 LanceDB에 즉시 임베딩 (변경 파일 1개만, 전체 sync 불필요)."""
    try:
        import lancedb
        from google import genai
        from google.genai import types
    except ImportError as e:
        return f"임베딩 스킵 (패키지 없음): {e}"

    api_key = os.environ.get("GEMINI_API_KEY", "")
    if not api_key:
        return "임베딩 스킵 (GEMINI_API_KEY 없음)"

    if not os.path.exists(LANCE_DB_DIR):
        return "임베딩 스킵 (LanceDB 없음 — 온유 첫 실행 후 자동 생성됨)"

    try:
        db = lancedb.connect(LANCE_DB_DIR)
        tbl_names = db.table_names() if hasattr(db, "table_names") else [str(t) for t in db.list_tables()]
        if "chunks" not in tbl_names:
            return "임베딩 스킵 (chunks 테이블 없음 — 온유 첫 실행 후 생성됨)"
        table = db.open_table("chunks")
    except Exception as e:
        return f"LanceDB 연결 실패: {e}"

    content = open(OUTPUT_PATH, encoding="utf-8").read()
    chunks  = _split_chunks(content)
    mtime   = os.path.getmtime(OUTPUT_PATH)
    fname   = os.path.basename(OUTPUT_PATH)
    tags_json  = json.dumps(["온유시스템", "코드구조"], ensure_ascii=False)
    links_json = json.dumps([], ensure_ascii=False)

    # 기존 청크 삭제
    try:
        safe = OUTPUT_PATH.replace("'", "''")
        table.delete(f"path = '{safe}'")
    except Exception:
        pass

    client = genai.Client(api_key=api_key)
    new_rows = []
    for i, chunk in enumerate(chunks[:20]):
        try:
            res = client.models.embed_content(
                model="gemini-embedding-001",
                contents=chunk,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
            )
            vec = list(res.embeddings[0].values)
            if len(vec) != EMBED_DIM:
                continue
            new_rows.append({
                "path":         OUTPUT_PATH,
                "chunk_idx":    i,
                "text":         f"[문서명: {fname}]\n{chunk}",
                "vector":       vec,
                "mtime":        mtime,
                "links":        links_json,
                "tags":         tags_json,
                "importance":   "HIGH",
                "user_written": True,
                "hit_log":      json.dumps([]),
            })
        except Exception:
            pass

    if new_rows:
        table.add(new_rows)
        return f"LanceDB 임베딩 완료 ({len(new_rows)}청크)"
    return "임베딩 실패 (청크 없음)"


# ── 메인 빌드 ─────────────────────────────────────────────────────────────────

def build_index() -> str:
    """온유_코드구조.md 재생성 + LanceDB 임베딩 갱신."""
    if not os.path.exists(AGENT_PATH):
        return f"오류: {AGENT_PATH} 없음"

    with open(AGENT_PATH, "r", encoding="utf-8") as f:
        source = f.read()

    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return f"AST 파싱 오류: {e}"

    file_size_kb = len(source.encode("utf-8")) // 1024
    line_count   = source.count("\n")
    now          = datetime.now().strftime("%Y-%m-%d %H:%M")

    constants  = _extract_constants(tree, source)
    classes    = _extract_classes(tree)
    functions  = _extract_functions(tree)
    tool_names = _extract_tool_names(source)

    lines = [
        "---",
        "tags: [온유시스템, 코드구조, obsidian_agent]",
        f"날짜: {now[:10]}",
        f"자동생성: {now}",
        "---",
        "",
        "# 온유 시스템 코드 구조 (obsidian_agent.py)",
        "",
        f"> 자동 생성됨 by `onew_code_indexer.py` — {now}",
        f"> 파일 크기: {file_size_kb}KB | 총 {line_count}줄 | 클래스 {len(classes)}개 | 함수 {len(functions)}개",
        "> **.py 파일은 임베딩 대상 아님** — 이 .md 파일이 RAG 검색 진입점",
        "> 코드 직접 조회: `read_file(\"SYSTEM/obsidian_agent.py\")`",
        "> 인덱스 갱신: `refresh_code_index()` 또는 Claude Code 자동 실행",
        "",
        "---",
        "",
        "## 1. 핵심 상수 (설정)",
        "",
        "| 상수 | 값 / 설명 |",
        "|------|-----------|",
    ]

    for name, val in constants:
        lines.append(f"| {name} | `{val}` |")

    lines += ["", "---", "", "## 2. 클래스 구조", ""]

    for cls_line, cls_name, cls_doc, methods in classes:
        lines.append(f"### {cls_name} (줄 {cls_line})")
        if cls_doc:
            lines.append(cls_doc)
        lines.append("")
        if methods:
            lines += ["| 줄 | 메서드 | 설명 |", "|----|--------|------|"]
            for m_line, m_name, m_doc in methods:
                lines.append(f"| {m_line} | {m_name}() | {m_doc} |")
        lines.append("")

    lines += [
        "---", "",
        "## 3. 주요 모듈 레벨 함수", "",
        "| 줄 | 함수 | 설명 |",
        "|----|------|------|",
    ]
    for fn_line, fn_name, fn_doc in functions:
        lines.append(f"| {fn_line} | {fn_name}() | {fn_doc} |")

    if tool_names:
        lines += [
            "", "---", "",
            "## 4. 온유 도구 함수 (onew_tools 등록됨)", "",
            "| 함수명 |", "|--------|",
        ]
        for name in tool_names:
            lines.append(f"| {name} |")

    lines += [
        "", "---", "",
        f"> 원본: `SYSTEM/obsidian_agent.py` ({file_size_kb}KB, {line_count}줄)",
        f"> 마지막 갱신: {now}",
    ]

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    # md 파일 생성 완료 → LanceDB 임베딩 갱신 (해당 파일 1개만)
    embed_result = embed_after_build()

    return (
        f"온유_코드구조.md 갱신 완료 "
        f"({file_size_kb}KB, {len(classes)}개 클래스, {len(functions)}개 함수) | "
        f"{embed_result}"
    )


# ── 훅 모드 ───────────────────────────────────────────────────────────────────

def _hook_mode():
    """Claude Code PostToolUse 훅 모드: stdin JSON에서 file_path 확인 후 조건부 실행"""
    try:
        raw = sys.stdin.read()
        data = json.loads(raw)
        tool_input = data.get("tool_input", {})
        file_path  = tool_input.get("file_path", "")
        if "obsidian_agent.py" not in file_path:
            sys.exit(0)
        result = build_index()
        print(f"[코드 인덱스] {result}", flush=True)
    except Exception:
        sys.exit(0)  # 훅 실패는 조용히 — 온유 실행 방해 금지


if __name__ == "__main__":
    if "--hook" in sys.argv:
        _hook_mode()
    else:
        print(build_index())
