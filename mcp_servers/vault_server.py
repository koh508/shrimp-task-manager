"""
온유 Vault MCP 서버 (vault_server.py)
파일 읽기/쓰기/검색 등 Vault 관련 도구를 제공하는 독립 MCP 서버.

실행 (단독):  python vault_server.py
smolagents가 StdioServerParameters로 subprocess로 실행함.
"""
import os, sys, json, re, shutil, urllib.request
from datetime import datetime
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# lancedb를 모듈 레벨에서 미리 import (FastMCP asyncio 루프 시작 전 초기화)
# → 스레드 내부에서 최초 import 시 발생하는 asyncio deadlock 방지
try:
    import lancedb as _lancedb_preload
except Exception:
    _lancedb_preload = None

# ── kiwipiepy 형태소 분석기 (BM25 토크나이저) ──────────────────────────────────
try:
    from kiwipiepy import Kiwi as _Kiwi
    _kiwi = _Kiwi()
    def _tokenize(text: str) -> list[str]:
        """kiwipiepy: 한국어 명사(NNG/NNP) + 2글자 이상 순수 한글만 추출."""
        try:
            return [
                t.form for t in _kiwi.tokenize(text)
                if t.tag in ('NNG', 'NNP') and len(t.form) >= 2
                and re.fullmatch(r'[가-힣]+', t.form)
            ]
        except Exception:
            return text.split()
except Exception:
    _kiwi = None
    def _tokenize(text: str) -> list[str]:
        return text.split()

# ── 용어 정규화 인덱스 (TerminologyIndex) ─────────────────────────────────────
_term_index = None

def _get_term_index():
    """TerminologyIndex 싱글톤 — 최초 호출 시 로드, 실패 시 None."""
    global _term_index
    if _term_index is not None:
        return _term_index
    try:
        import sys as _sys
        _onew_core = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "onew_core")
        if _onew_core not in _sys.path:
            _sys.path.insert(0, _onew_core)
        from terminology_server import TerminologyIndex
        _term_index = TerminologyIndex()
    except Exception:
        _term_index = None
    return _term_index

# ── 경로 / 상수 ───────────────────────────────────────────────────────────────
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
LANCE_DB_DIR        = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", ".onew_lance_db")
USAGE_LOG_FILE      = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "api_usage_log.json")
CLIP_FOLDER         = os.path.join(OBSIDIAN_VAULT_PATH, "클리핑")

MAX_DAILY_SEARCHES  = 30
SEARCH_ALLOW_TOPICS = []   # 비어있으면 무제한

PROTECTED_FOLDERS = {"OCU", "03_OCU", "04_Reference"}
PROTECTED_FILES   = {
    "obsidian_agent.py", "onew_shared.py", "onew_tools.py",
    "onew_scheduler.py", "onew_telegram_bot.py",
}
# skills/core, skills/domain, skills/optional은 읽기 전용 — skills/experimental만 쓰기 허용
PROTECTED_SKILL_DIRS = {"core", "domain", "optional"}

TIME_QUERY_KEYWORDS = [
    "최근", "요즘", "오늘", "어제", "이번 주", "이번 달", "최신", "며칠",
    "언제", "날짜", "일정", "지난", "작년", "올해",
]

# ── Gemini API 키 조회 ─────────────────────────────────────────────────────────
def _get_api_key() -> str:
    """GEMINI_API_KEY를 환경변수 또는 winreg에서 반환."""
    key = os.environ.get("GEMINI_API_KEY", "")
    if not key:
        try:
            import winreg
            k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            key, _ = winreg.QueryValueEx(k, "GEMINI_API_KEY")
            winreg.CloseKey(k)
        except:
            pass
    return key


# ── Gemini 클라이언트 (analyze_image 등 다른 도구용) ──────────────────────────
_gemini_client = None

def _get_client():
    global _gemini_client
    if _gemini_client is None:
        from google import genai
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            try:
                import winreg
                key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
                api_key, _ = winreg.QueryValueEx(key, "GEMINI_API_KEY")
                winreg.CloseKey(key)
            except:
                pass
        _gemini_client = genai.Client(api_key=api_key)
    return _gemini_client

# ── 내부 헬퍼 ─────────────────────────────────────────────────────────────────
def _is_protected(p: Path) -> str | None:
    """보호 폴더/파일이면 에러 메시지 반환, 아니면 None."""
    vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
    if p.name in PROTECTED_FILES:
        return f"🔒 '{p.name}'은 핵심 시스템 파일입니다. Claude Code에게 요청하세요."
    try:
        rel_parts = p.resolve().relative_to(vault_path).parts
        # skills/core, skills/domain 쓰기 보호 (skills/experimental만 허용)
        if (len(rel_parts) >= 3
                and rel_parts[0] == "SYSTEM"
                and rel_parts[1] == "skills"
                and rel_parts[2] in PROTECTED_SKILL_DIRS):
            return (f"🔒 'skills/{rel_parts[2]}/' 폴더는 읽기전용입니다. "
                    f"새 스킬은 skills/experimental/ 에만 저장하세요.")
        for part in rel_parts:
            if part in PROTECTED_FOLDERS:
                return f"🔒 '{part}' 폴더는 읽기전용입니다."
    except ValueError:
        pass
    return None

def _get_search_count():
    today = datetime.now().strftime("%Y-%m-%d")
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
    return data, today, data.get(f"search_{today}", 0)

def _atomic_write(filepath: str, data):
    tmp = filepath + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, filepath)

# ── MCP 서버 인스턴스 ─────────────────────────────────────────────────────────
mcp = FastMCP("onew-vault")

# ==============================================================================
# 파일 I/O
# ==============================================================================

_FUZZY_YEAR = re.compile(r'(\d{5,})-(\d{2})-(\d{2})')


def _sanitize_fuzzy_date(fp: str) -> str:
    """
    연도 오타 자동 교정.
    '20250-01-11' → '2025-01-11' (5자리 연도의 앞 4자리만 사용)
    '20255-01-11' → '2025-01-11'
    """
    def _fix_year(m: re.Match) -> str:
        year = m.group(1)[:4]   # 앞 4자리만
        return f"{year}-{m.group(2)}-{m.group(3)}"
    return _FUZZY_YEAR.sub(_fix_year, fp)


def _resolve_path(filepath: str) -> Path:
    """
    파일 경로 방어적 정규화.
    - 앞뒤 따옴표/공백 제거
    - 이중 백슬래시(\\) → 단일(\\) 정규화
    - 연도 오타 자동 교정 (20250 → 2025)
    - 슬래시 혼용(/) → os.path.normpath
    """
    # 따옴표·공백 제거
    fp = filepath.strip().strip('"\'')
    # 이중 백슬래시 정규화
    fp = fp.replace('\\\\', '\\')
    # 연도 오타 교정 (20250-01-11 → 2025-01-11)
    fp_fixed = _sanitize_fuzzy_date(fp)
    if fp_fixed != fp:
        import logging as _lg
        _lg.getLogger(__name__).info("[read_file] 날짜 오타 교정: %s → %s", fp, fp_fixed)
        fp = fp_fixed
    # normpath: 슬래시 혼용 정리
    fp = os.path.normpath(fp)
    return Path(fp)


@mcp.tool()
def read_file(filepath: str) -> str:
    """지정된 경로의 파일 내용을 읽어옵니다.
    파일명만 입력 시(예: '2025-10-17.md') Vault 전체에서 자동으로 파일을 찾습니다.

    Args:
        filepath: 읽을 파일의 절대경로 또는 파일명
    """
    try:
        p = _resolve_path(filepath)

        def _try_read(path: Path) -> str | None:
            """존재하면 읽기, 없으면 None."""
            try:
                if path.exists():
                    return path.read_text(encoding="utf-8")
            except Exception:
                pass
            return None

        def _with_md(path: Path) -> Path:
            """확장자 없으면 .md 추가."""
            return path if path.suffix else path.with_suffix(".md")

        # ── 1. 절대경로 직접 접근 ─────────────────────────────────────────────
        if p.is_absolute():
            # 1a. 그대로 시도
            r = _try_read(p)
            if r is not None:
                return r
            # 1b. .md 추가 후 재시도
            r = _try_read(_with_md(p))
            if r is not None:
                return r
            return f"Error reading file: 파일을 찾을 수 없습니다 → {p}"

        # ── 2. 상대경로 / 파일명 → Vault 하위 탐색 ──────────────────────────
        vault = Path(OBSIDIAN_VAULT_PATH)

        # 2a. Vault root 기준 상대경로 직접 결합
        for candidate in [vault / p, vault / _with_md(p)]:
            r = _try_read(candidate)
            if r is not None:
                return r

        # 2b. 파일명으로 rglob (확장자 없으면 .md 가정)
        search_name = _with_md(p).name
        candidates = list(vault.rglob(search_name))
        if candidates:
            # DAILY 폴더 우선
            daily = [c for c in candidates if "DAILY" in c.parts]
            target = daily[0] if daily else candidates[0]
            return target.read_text(encoding="utf-8")

        return f"Error reading file: '{search_name}' 파일을 Vault에서 찾을 수 없습니다."

    except Exception as e:
        return f"Error reading file: {e}"


@mcp.tool()
def write_file(filepath: str, content: str) -> str:
    """지정된 경로에 파일을 생성하거나 내용을 덮어씁니다. 새 파일 생성 시에만 사용하세요.
    기존 파일 수정은 edit_file을 사용하세요.

    Args:
        filepath: 저장할 파일의 경로
        content: 기록할 내용
    """
    try:
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        p = Path(filepath)
        if not p.is_absolute():
            p = vault_path / p
        p = p.resolve()

        err = _is_protected(p)
        if err:
            return err

        allowed_roots = [vault_path, Path(r"C:\Users\User\Desktop").resolve()]
        if not any(str(p).startswith(str(r)) for r in allowed_roots):
            return f"🚫 Vault/바탕화면 외부 경로에는 쓸 수 없습니다 → {filepath}"

        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        rel = os.path.relpath(str(p), OBSIDIAN_VAULT_PATH)
        return f"Success: 저장 완료 → {rel} ({len(content):,}자)"
    except Exception as e:
        return f"Error writing file: {e}"


@mcp.tool()
def edit_file(filepath: str, old_str: str, new_str: str) -> str:
    """파일의 특정 부분만 교체합니다. 기존 파일 수정 시 write_file 대신 반드시 이 도구를 사용하세요.

    Args:
        filepath: 수정할 파일 경로
        old_str: 교체할 기존 텍스트 (파일 내에서 유일해야 함, 주변 코드를 충분히 포함)
        new_str: 교체할 새 텍스트
    """
    try:
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        p = Path(filepath)
        if not p.is_absolute():
            p = vault_path / p
        p = p.resolve()

        err = _is_protected(p)
        if err:
            return err

        if not p.exists():
            return f"Error: 파일이 존재하지 않습니다 → {filepath}"

        original = p.read_text(encoding="utf-8")
        count = original.count(old_str)
        if count == 0:
            return "Error: old_str를 찾을 수 없습니다. 파일 내용과 정확히 일치하는지 확인하세요."
        if count > 1:
            return f"Error: old_str가 {count}번 발견됩니다. 주변 코드를 더 포함해서 유일하게 만들어주세요."

        new_content = original.replace(old_str, new_str, 1)

        # .py 파일이면 문법 검사
        if p.suffix == ".py":
            import ast
            try:
                ast.parse(new_content)
            except SyntaxError as se:
                return f"문법 오류로 수정 취소: {se}"

        # 하루 첫 수정 시 백업
        if p.suffix == ".py":
            backup_dir = Path(r"C:\Users\User\AppData\Local\onew\code_backup") / datetime.now().strftime("%Y-%m-%d")
            backup_dir.mkdir(parents=True, exist_ok=True)
            backup_path = backup_dir / p.name
            if not backup_path.exists():
                shutil.copy2(str(p), str(backup_path))

        p.write_text(new_content, encoding="utf-8")

        # 변경된 부분 미리보기
        lines = new_content.splitlines()
        idx = next((i for i, l in enumerate(lines) if new_str.splitlines()[0] in l), None)
        preview = ""
        if idx is not None:
            start = max(0, idx - 2)
            end   = min(len(lines), idx + 4)
            preview = "\n".join(f"{start+i+1:4}: {l}" for i, l in enumerate(lines[start:end]))

        rel = os.path.relpath(str(p), OBSIDIAN_VAULT_PATH)
        return f"Success: 수정 완료 → {rel}\n---\n{preview}"
    except Exception as e:
        return f"Error editing file: {e}"


@mcp.tool()
def create_folder(folderpath: str) -> str:
    """Vault 내에 폴더를 생성합니다.

    Args:
        folderpath: 절대경로 또는 Vault 기준 상대경로
    """
    try:
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        p = Path(folderpath)
        if not p.is_absolute():
            p = vault_path / p
        p = p.resolve()
        try:
            p.relative_to(vault_path)
        except ValueError:
            return f"🚫 Vault 외부 폴더는 생성할 수 없습니다 → {folderpath}"
        p.mkdir(parents=True, exist_ok=True)
        return f"Success: 폴더 생성 완료 → {p}"
    except Exception as e:
        return f"Error creating folder: {e}"


@mcp.tool()
def list_files(directory: str = "") -> str:
    """지정된 디렉토리의 파일/폴더 목록을 반환합니다.

    Args:
        directory: 절대경로 또는 Vault 기준 상대경로. 생략 시 Vault 루트.
    """
    try:
        p = Path(directory) if directory else Path(OBSIDIAN_VAULT_PATH)
        if not p.is_absolute():
            p = Path(OBSIDIAN_VAULT_PATH) / p
        p = p.resolve()
        entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        lines = [("📄 " if e.is_file() else "📁 ") + e.name for e in entries]
        return f"[{p}]\n" + "\n".join(lines) if lines else f"[{p}] (비어 있음)"
    except Exception as e:
        return f"Error listing directory: {e}"


@mcp.tool()
def move_file(src: str, dst: str) -> str:
    """파일을 src에서 dst로 이동합니다.

    Args:
        src: 이동할 파일 경로
        dst: 목적지 경로
    """
    try:
        s = Path(src).resolve()
        d = Path(dst).resolve()
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(s).startswith(str(r)) for r in allowed_roots):
            return f"🚫 출발 경로가 허용 범위 밖입니다 → {src}"
        if not any(str(d).startswith(str(r)) for r in allowed_roots):
            return f"🚫 목적지 경로가 허용 범위 밖입니다 → {dst}"

        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        for check, label in [(s, "출발"), (d, "목적지")]:
            err = _is_protected(check)
            if err:
                return f"[{label}] {err}"

        if not s.exists():
            return f"Error: 파일이 존재하지 않습니다 → {src}"

        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return f"Success: 이동 완료 → {src}  →  {dst}"
    except Exception as e:
        return f"Error moving file: {e}"


@mcp.tool()
def delete_file(filepath: str) -> str:
    """지정된 파일을 삭제합니다.

    Args:
        filepath: 삭제할 파일 경로 또는 파일명
    """
    try:
        p = Path(filepath)
        if not p.is_absolute() and not p.exists():
            import glob as _glob
            matches = _glob.glob(str(Path(OBSIDIAN_VAULT_PATH) / "**" / p.name), recursive=True)
            if matches:
                p = Path(matches[0])
        p = p.resolve()

        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(p).startswith(str(r)) for r in allowed_roots):
            return f"🚫 Vault/바탕화면 외부 경로는 삭제할 수 없습니다 → {filepath}"

        err = _is_protected(p)
        if err:
            return err
        if not p.exists():
            return f"Error: 파일이 존재하지 않습니다 → {filepath}"
        if p.is_dir():
            return f"Error: 디렉토리는 삭제할 수 없습니다 (파일만 가능)"

        p.unlink()
        return f"Success: 삭제 완료 → {filepath}"
    except Exception as e:
        return f"Error deleting file: {e}"


@mcp.tool()
def rollback_file(filepath: str) -> str:
    """파일을 가장 최근 백업본으로 복원합니다. 코드 수정 후 문제가 생겼을 때 사용하세요.

    Args:
        filepath: 복원할 파일 경로 또는 파일명
    """
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = Path(OBSIDIAN_VAULT_PATH) / filepath
        p = p.resolve()

        backup_base = Path(r"C:\Users\User\AppData\Local\onew\code_backup")
        if not backup_base.exists():
            return "Error: 백업 폴더가 없습니다."

        date_dirs = sorted([d for d in backup_base.iterdir() if d.is_dir()], reverse=True)
        for date_dir in date_dirs:
            backup_file = date_dir / p.name
            if backup_file.exists():
                shutil.copy2(str(backup_file), str(p))
                return f"✅ 롤백 완료: {p.name} → {date_dir.name} 백업본으로 복원"

        return f"Error: '{p.name}'의 백업본이 없습니다."
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def backup_system() -> str:
    """SYSTEM 폴더 전체를 ZIP으로 압축 백업합니다."""
    try:
        ts         = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = r"C:\Users\User\AppData\Local\onew\db_backup"
        os.makedirs(backup_dir, exist_ok=True)
        target = os.path.join(backup_dir, f"Onew_Backup_{ts}")
        shutil.make_archive(target, "zip", os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM"))
        return f"Success: 백업 완료 → {target}.zip"
    except Exception as e:
        return f"Backup Failed: {e}"


# ==============================================================================
# 검색
# ==============================================================================

@mcp.tool()
async def search_vault(query: str) -> str:
    """옵시디언 Vault(개인 노트/일기/공부자료)에서 키워드를 검색합니다.
    인물, 날짜, 대화 내용, 공부 기록 등 개인 기록을 찾을 때 사용하세요.

    Args:
        query: 검색할 키워드 또는 문장
    """
    import asyncio

    def _do_search() -> str:
        try:
            import lancedb
            import urllib.request, json as _json

            # 쿼리 정규화 (용어 사전으로 변형어 → 정규 표현 치환)
            normalized_query = query
            idx = _get_term_index()
            if idx is not None:
                normalized_query = idx.normalize(query)

            # 임베딩: google-genai SDK 대신 urllib 직접 호출
            # (FastMCP asyncio 이벤트 루프와의 충돌 방지)
            api_key = _get_api_key()
            url = (f"https://generativelanguage.googleapis.com/v1beta/models/"
                   f"gemini-embedding-001:embedContent?key={api_key}")
            body = _json.dumps({
                "model": "models/gemini-embedding-001",
                "content": {"parts": [{"text": normalized_query}]},
                "taskType": "RETRIEVAL_QUERY",
            }).encode()
            req = urllib.request.Request(url, data=body,
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=15) as r:
                q_emb = _json.loads(r.read())["embedding"]["values"]

            # LanceDB 검색
            if not os.path.exists(LANCE_DB_DIR):
                return "Vault DB가 없습니다. 먼저 동기화를 실행하세요."
            db = lancedb.connect(LANCE_DB_DIR)
            existing = db.table_names() if hasattr(db, "table_names") else [str(t) for t in db.list_tables()]
            if "chunks" not in existing:
                return "chunks 테이블이 없습니다."

            tbl = db.open_table("chunks")
            candidates = tbl.search(q_emb).metric("cosine").limit(50).to_list()
            if not candidates:
                return f"Vault에서 '{query}'와 관련된 기록을 찾지 못했습니다."

            # 하이브리드 스코어 (벡터 70% + BM25 30%)
            try:
                from rank_bm25 import BM25Okapi
                texts       = [r["text"] for r in candidates]
                # kiwipiepy 형태소 분석 토크나이저 (공백 분리 폴백)
                bm25        = BM25Okapi([_tokenize(t) for t in texts])
                bm25_raw    = bm25.get_scores(_tokenize(normalized_query))
                bm25_max    = max(bm25_raw) or 1
                bm25_scores = [s / bm25_max for s in bm25_raw]
            except Exception:
                bm25_scores = [0.0] * len(candidates)

            results = []
            for i, r in enumerate(candidates):
                vec_score = max(0.0, 1.0 - r.get("_distance", 1.0))
                score     = vec_score * 0.7 + bm25_scores[i] * 0.3
                if score >= 0.15:
                    results.append((score, r))

            results.sort(key=lambda x: x[0], reverse=True)
            results = results[:10]

            if not results:
                return f"Vault에서 '{query}'와 관련된 기록을 찾지 못했습니다."

            header = f"🔍 Vault 검색 결과: '{query}'"
            if normalized_query != query:
                header += f" (정규화: '{normalized_query}')"
            lines = [header]
            for i, (score, r) in enumerate(results, 1):
                lines.append(f"\n[{i}] 출처: {os.path.basename(r['path'])}  (score={score:.3f})")
                lines.append(r["text"][:400])

            return "\n".join(lines)

        except Exception as e:
            return f"Error searching vault: {e}"

    # blocking 코드를 스레드 풀에서 실행 (FastMCP 이벤트 루프 차단 방지)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, _do_search)


# ==============================================================================
# 웹 / 이미지
# ==============================================================================

@mcp.tool()
def fetch_url_as_md(url: str, title: str = "") -> str:
    """URL의 웹 페이지 내용을 가져와 마크다운으로 변환하고 클리핑/ 폴더에 저장합니다.

    Args:
        url: 가져올 웹 페이지 주소
        title: 저장할 제목 (비워두면 페이지 제목 자동 추출)
    """
    from html.parser import HTMLParser

    class _Extractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._skip = False
            self._skip_tags = {"script", "style", "nav", "footer", "head", "aside"}
            self._depth = {}
            self.parts = []
        def handle_starttag(self, tag, attrs):
            self._depth[tag] = self._depth.get(tag, 0) + 1
            if tag in self._skip_tags:
                self._skip = True
        def handle_endtag(self, tag):
            self._depth[tag] = max(0, self._depth.get(tag, 1) - 1)
            if tag in self._skip_tags and self._depth.get(tag, 0) == 0:
                self._skip = False
        def handle_data(self, data):
            if not self._skip and data.strip():
                self.parts.append(data.strip())

    if not url.startswith(("http://", "https://")):
        return f"❌ 유효하지 않은 URL: {url}"

    _domain = url.split("/")[2] if url.count("/") >= 2 else url
    if "anthropic.com" in _domain:
        _subfolder, _source_tag = "Anthropic", "Anthropic"
    elif "googleblog.com" in _domain:
        _subfolder, _source_tag = "Google", "Google"
    else:
        _subfolder, _source_tag = "", _domain

    text = None
    try:
        req = urllib.request.Request(
            f"https://r.jina.ai/{url}",
            headers={"User-Agent": "Mozilla/5.0", "X-Return-Format": "markdown"})
        with urllib.request.urlopen(req, timeout=20) as r:
            jina_md = r.read().decode("utf-8", errors="ignore")
        if not title:
            m = re.search(r"^Title:\s*(.+)$", jina_md, re.MULTILINE)
            if m:
                title = re.sub(r"\s*[-|]\s*(Anthropic|Google).*$", "", m.group(1).strip(), flags=re.IGNORECASE).strip()
        text = re.sub(r"^(Title|URL Source|Markdown Content):[^\n]*\n?", "", jina_md, flags=re.MULTILINE).strip()[:8000]
    except:
        pass

    if not text:
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=15) as r:
                charset  = r.headers.get_content_charset("utf-8")
                html_raw = r.read().decode(charset, errors="ignore")
        except Exception as e:
            return f"❌ URL 접근 실패: {e}"
        if not title:
            m = re.search(r"<title[^>]*>(.*?)</title>", html_raw, re.IGNORECASE | re.DOTALL)
            title = re.sub(r"\s+", " ", m.group(1).strip()) if m else url.split("/")[-1] or "untitled"
        ext = _Extractor()
        ext.feed(html_raw)
        text = re.sub(r"\n{3,}", "\n\n", "\n".join(ext.parts))[:8000]

    if not title:
        title = url.split("/")[-1] or "untitled"

    today    = datetime.now().strftime("%Y-%m-%d")
    save_dir = os.path.join(CLIP_FOLDER, _subfolder) if _subfolder else CLIP_FOLDER
    os.makedirs(save_dir, exist_ok=True)
    safe_title = re.sub(r'[\\/:*?"<>|]', "_", title)[:60]
    fpath = os.path.join(save_dir, f"{today}_{safe_title}.md")

    extra_tag = f", {_source_tag}" if _source_tag else ""
    md = (
        f"---\ntags: [클리핑{extra_tag}, {today}]\n날짜: {today}\n원본: {url}\n---\n\n"
        f"# {title}\n\n> [!NOTE] 원본\n> {url}\n\n{text}"
    )
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(md)

    rel = os.path.relpath(fpath, OBSIDIAN_VAULT_PATH)
    return f"✅ 저장 완료: {rel}  ({len(text):,}자)"


@mcp.tool()
def browse_web(url: str, extract: str = "") -> str:
    """Playwright 헤드리스 브라우저로 URL을 열어 본문을 반환합니다.
    JavaScript 렌더링이 필요한 페이지에 사용하세요. fetch_url_as_md로 안 될 때 사용.

    Args:
        url: 크롤링할 웹 페이지 주소
        extract: 특정 키워드 지정 시 해당 내용 위주로 필터링 (선택)
    """
    if not url.startswith(("http://", "https://")):
        return f"Error: 유효하지 않은 URL: {url}"
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page    = browser.new_page(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64)")
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)
            title = page.title() or url.split("/")[-1]
            body  = page.evaluate("""() => {
                ['script','style','nav','footer','header','aside','noscript']
                  .forEach(t => document.querySelectorAll(t).forEach(e => e.remove()));
                return document.body ? document.body.innerText : '';
            }""")
            browser.close()

        body = re.sub(r"\n{3,}", "\n\n", body.strip())[:8000]
        if extract:
            kw_low  = extract.lower()
            matched = [l for l in body.split("\n") if kw_low in l.lower()]
            if matched:
                body = "\n".join(matched[:100])

        return f"[{title}]\n{url}\n\n{body}"
    except Exception as e:
        return f"Error: browse_web 실패: {e}"


@mcp.tool()
def analyze_image(filepath: str, question: str = "") -> str:
    """이미지 파일을 Gemini Vision으로 분석합니다.

    Args:
        filepath: 이미지 파일 경로 또는 파일명
        question: 분석 질문 (비워두면 전체 내용 설명)
    """
    import mimetypes
    from google.genai import types as gtypes
    try:
        p = Path(filepath).resolve()
        if not p.exists():
            candidates = list(Path(OBSIDIAN_VAULT_PATH).rglob(Path(filepath).name))
            if not candidates:
                return f"Error: 파일을 찾을 수 없습니다 ({filepath})"
            p = candidates[0]

        mime_type, _ = mimetypes.guess_type(str(p))
        if not mime_type or not mime_type.startswith("image/"):
            return "Error: 이미지 파일만 분석 가능합니다 (jpg, png, webp 등)"

        image_bytes = p.read_bytes()
        prompt = question or (
            "이 이미지의 내용을 한국어로 상세히 설명하라. "
            "텍스트가 있으면 전부 추출하고, 도표/수식/순서도가 있으면 구조화하여 정리하라."
        )

        client   = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[gtypes.Part.from_bytes(data=image_bytes, mime_type=mime_type), prompt]
        )
        return response.text.strip()
    except Exception as e:
        return f"Error: 이미지 분석 실패 ({e})"


@mcp.tool()
def analyze_trend(query: str) -> str:
    """Google 검색으로 최신 금융/기술/학습 트렌드를 분석합니다.

    Args:
        query: 검색할 질문 또는 주제
    """
    from google.genai import types as gtypes

    usage_data, today, search_count = _get_search_count()
    if search_count >= MAX_DAILY_SEARCHES:
        return f"🚫 오늘 검색 한도({MAX_DAILY_SEARCHES}회)를 초과했습니다. (현재: {search_count}회)"

    if SEARCH_ALLOW_TOPICS and not any(kw in query for kw in SEARCH_ALLOW_TOPICS):
        return f"🚫 허용되지 않은 주제입니다. 허용 주제: {', '.join(SEARCH_ALLOW_TOPICS[:8])}"

    try:
        client      = _get_client()
        search_tool = gtypes.Tool(google_search=gtypes.GoogleSearchRetrieval())
        ans = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=gtypes.GenerateContentConfig(tools=[search_tool])
        )
        usage_data[f"search_{today}"] = search_count + 1
        _atomic_write(USAGE_LOG_FILE, usage_data)
        return f"🌐 [웹 검색 리포트] ({search_count+1}/{MAX_DAILY_SEARCHES}회)\n\n{ans.text}"
    except Exception as e:
        return f"Search Error: {e}"


@mcp.tool()
def refresh_code_index() -> str:
    """obsidian_agent.py의 AST를 파싱해 온유_코드구조.md를 재생성합니다.
    코드 수정 후 온유가 변경 내용을 인식하게 하려면 이 도구를 호출하세요.
    Gemini API 토큰 소모 없음 (순수 AST 파싱).
    """
    try:
        import importlib.util, sys as _sys
        idx_path = os.path.join(os.path.dirname(OBSIDIAN_VAULT_PATH), "Obsidian Vault", "SYSTEM", "onew_code_indexer.py")
        # 경로 보정: OBSIDIAN_VAULT_PATH가 Vault 루트이므로 SYSTEM 하위
        idx_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_code_indexer.py")
        spec = importlib.util.spec_from_file_location("onew_code_indexer", idx_path)
        mod  = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod.build_index()
    except Exception as e:
        return f"Error: refresh_code_index 실패 → {e}"


def _part_num(path: Path) -> int:
    """'xxx_partN.md' 파일명에서 N을 추출. 없으면 0."""
    m = re.search(r'_part(\d+)\.md$', path.name, re.IGNORECASE)
    return int(m.group(1)) if m else 0


def _book_prefix(path: Path) -> str:
    """'xxx_partN.md' → 'xxx' (part 번호 앞 공통 접두어)."""
    return re.sub(r'_part\d+\.md$', '', path.name, flags=re.IGNORECASE)


def _build_combined_text(anchor_file: Path) -> tuple[str, list[Path]]:
    """anchor_file 이 속한 합본 시리즈 전체를 번호 순으로 이어붙인 텍스트와 파일 목록을 반환.
    anchor_file이 _partN 형식이 아니면 해당 파일 단독 반환.
    """
    part_n = _part_num(anchor_file)
    if part_n == 0:
        # 단일 파일 — 그대로 반환
        try:
            return anchor_file.read_text(encoding="utf-8", errors="ignore"), [anchor_file]
        except Exception:
            return "", [anchor_file]

    prefix = _book_prefix(anchor_file)
    folder = anchor_file.parent

    # 같은 폴더에서 동일 접두어를 가진 모든 part 파일 수집
    siblings: list[Path] = sorted(
        [f for f in folder.glob(f"{prefix}_part*.md")],
        key=_part_num
    )

    combined = ""
    used: list[Path] = []
    for f in siblings:
        try:
            combined += f.read_text(encoding="utf-8", errors="ignore") + "\n"
            used.append(f)
        except Exception:
            continue
    return combined, used


@mcp.tool()
def get_exam_problem(date_str: str, problem_num: int) -> str:
    """공조냉동기계기사 기출문제를 시행일자와 문제번호로 직접 조회합니다.
    RAG 임베딩이 아닌 파일 텍스트 직접 추출 — 파일이 여러 part로 분할되어 있어도
    전체 합본 시리즈를 이어붙여 검색하므로 cross-part 문제도 정확하게 반환합니다.
    원문을 그대로 반환하며 내용을 수정하지 않습니다.

    Args:
        date_str:    시행일 문자열. 예: "2020.11.29", "2021.7.10", "2025.4.20"
        problem_num: 문제 번호 (정수). 예: 3

    Returns:
        해당 문제 원문 전체 (문제 지문 + 풀이/해설 포함) + 출처 표기.
        없으면 오류 메시지.
    """
    vault = Path(OBSIDIAN_VAULT_PATH)

    # ── 1. 날짜 문자열을 포함하는 파일 탐색 (OCU 폴더 우선) ─────────────────────
    date_esc = re.escape(date_str)
    candidate_files: list[Path] = []
    for md_file in vault.rglob("*.md"):
        try:
            if re.search(date_esc, md_file.read_text(encoding="utf-8", errors="ignore")):
                candidate_files.append(md_file)
        except Exception:
            continue

    if not candidate_files:
        return f"'{date_str}' 시행 문제가 포함된 파일을 찾을 수 없습니다."

    # OCU 폴더 파일 우선, 그 외(system_prompt 등) 후순위
    candidate_files.sort(key=lambda f: (0 if "OCU" in str(f) else 1, f.name))

    # ── 2. 정규식 ────────────────────────────────────────────────────────────────
    # 날짜 섹션 경계: 헤더(#)형 또는 플레인텍스트형 모두 인식
    # - `## 2020 과년도 출제문제(2020.10.17 시행)` → # 있는 형태
    # - `2021 과년도 출제문제 (2021.7.10 시행)`   → # 없는 형태
    # TOC 항목(`* ...`, `| ... |`)은 제외
    next_date_re = re.compile(
        r'^(?![\*\|\-\s])(?:#{1,4}\s+)?.{0,25}(\d{4}\s*과년도|\d{4}\.\d{1,2}\.\d{1,2}\s*시행)',
        re.MULTILINE
    )
    # 문제 N번 헤더
    prob_re = re.compile(
        rf'^(#{{1,4}}\s+)?문제\s*{problem_num}(?!\d)\b',
        re.MULTILINE
    )
    # 다음 임의 문제 번호 헤더
    next_prob_re = re.compile(
        r'^(#{1,4}\s+)?문제\s*\d+(?!\d)\b',
        re.MULTILINE
    )

    # TOC·목차 라인 판별: `* ...`, `| ... |`, 페이지번호 테이블 등
    _toc_line_re = re.compile(r'^\s*[\*\-]\s+|^\s*\|')

    def _find_content_date(text: str, esc: str):
        """date_str의 첫 번째 실제 콘텐츠 위치 반환 (TOC/목차 라인 건너뜀)."""
        for m in re.finditer(esc, text):
            # 해당 매치가 포함된 줄 추출
            line_start = text.rfind('\n', 0, m.start()) + 1
            line_end   = text.find('\n', m.start())
            if line_end == -1:
                line_end = len(text)
            line = text[line_start:line_end]
            # TOC/목차 패턴이면 건너뜀
            if _toc_line_re.match(line):
                continue
            # 페이지 번호 테이블 패턴이면 건너뜀 (`| ... | 숫자 |`)
            if re.search(r'\|\s*\d+\s*\|?\s*$', line):
                continue
            return m
        return None

    # ── 3. 후보 파일마다 합본 전체 텍스트 구성 후 검색 ─────────────────────────
    seen_prefixes: set[str] = set()

    for anchor in candidate_files:
        book_key = str(anchor.parent) + "/" + _book_prefix(anchor)
        if book_key in seen_prefixes:
            continue
        seen_prefixes.add(book_key)

        combined, used_files = _build_combined_text(anchor)
        if not combined:
            continue

        # 날짜 위치: TOC 건너뛰고 실제 콘텐츠 위치 탐색
        dm = _find_content_date(combined, date_esc)
        if not dm:
            continue

        # 날짜가 포함된 줄의 시작부터 탐색 시작 (줄 전체를 섹션 시작으로)
        line_start = combined.rfind('\n', 0, dm.start()) + 1

        # 다음 날짜 섹션 시작 위치 탐색 (현재 날짜 줄 이후)
        next_date_m = next_date_re.search(combined, dm.end() + 1)
        section_end = next_date_m.start() if next_date_m else len(combined)

        search_region = combined[line_start:section_end]

        # 문제 N번 위치
        pm = prob_re.search(search_region)
        if not pm:
            continue

        # 문제 N번 ~ 다음 문제 번호 전까지 추출
        p_start = pm.start()
        next_pm = next_prob_re.search(search_region, pm.end())
        p_end   = next_pm.start() if next_pm else len(search_region)

        problem_text = search_region[p_start:p_end].strip()
        if not problem_text:
            continue

        # 출처: 사용된 파일 목록
        sources = [str(f.relative_to(vault)) for f in used_files
                   if re.search(date_esc, f.read_text(encoding="utf-8", errors="ignore"))]
        if not sources:
            sources = [str(f.relative_to(vault)) for f in used_files[:2]]

        source_str = "\n".join(f"  - {s}" for s in sources)
        return (
            f"📄 출처:\n{source_str}\n"
            f"📅 시행일: {date_str}  |  문제 {problem_num}\n"
            f"{'─' * 40}\n\n"
            f"{problem_text}"
        )

    # ── 4. Fallback: 연도만 있는 헤더 검색 (e.g., '# 2022' 단독 헤더) ─────────
    # 2022.10.16처럼 날짜 전체 문자열이 없고 '# 2022' 만 있는 경우 처리
    year_m = re.match(r'(\d{4})\.(\d{1,2})\.(\d{1,2})', date_str)
    if year_m:
        year = year_m.group(1)
        month = int(year_m.group(2))
        # year 단독 헤더 (# 2022) 패턴 — 과년도/날짜가 붙지 않은 것만
        year_only_re = re.compile(
            rf'^#{{1,4}}\s+{year}\b(?!\s*\d{{1,2}}\.\d{{1,2}}|\s*과년도)',
            re.MULTILINE
        )
        # 이미 탐색한 합본 시리즈 (OCU 폴더) 재사용
        seen_fb: set[str] = set()
        for md_file in vault.rglob("*.md"):
            if "OCU" not in str(md_file):
                continue
            try:
                text_fb = md_file.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            if not year_only_re.search(text_fb):
                continue
            book_key = str(md_file.parent) + "/" + _book_prefix(md_file)
            if book_key in seen_fb:
                continue
            seen_fb.add(book_key)
            combined_fb, used_fb = _build_combined_text(md_file)
            if not combined_fb:
                continue
            # year 단독 헤더 위치 탐색 — 완전한 날짜 헤더 이후에 등장하는 것만
            # (같은 연도의 이전 시행 섹션 이후에 오는 year-only 헤더 = 후반 회차)
            # 이전 시행 날짜 헤더들을 먼저 찾아 그 뒤에 오는 year-only 헤더 선택
            # 이전 회차 날짜 탐색: 헤더 중간에 있어도 되므로 ^ 없이 검색
            earlier_date_re = re.compile(
                rf'{year}\.(\d{{1,2}})\.\d{{1,2}}\s*시행',
                re.MULTILINE
            )
            # 이전 회차 중 month 보다 작은 것의 최후 위치
            last_earlier_end = 0
            for edm in earlier_date_re.finditer(combined_fb):
                em = int(edm.group(1))
                if em < month:
                    last_earlier_end = edm.end()
            # last_earlier_end 이후에 year_only_re 매치 탐색
            yh_m = year_only_re.search(combined_fb, last_earlier_end)
            if not yh_m:
                continue
            yh_line_start = combined_fb.rfind('\n', 0, yh_m.start()) + 1
            next_date_m_fb = next_date_re.search(combined_fb, yh_m.end() + 1)
            section_end_fb = next_date_m_fb.start() if next_date_m_fb else len(combined_fb)
            search_fb = combined_fb[yh_line_start:section_end_fb]
            pm_fb = prob_re.search(search_fb)
            if not pm_fb:
                continue
            next_pm_fb = next_prob_re.search(search_fb, pm_fb.end())
            p_end_fb = next_pm_fb.start() if next_pm_fb else len(search_fb)
            problem_text_fb = search_fb[pm_fb.start():p_end_fb].strip()
            if not problem_text_fb:
                continue
            sources_fb = [str(f.relative_to(vault)) for f in used_fb[:2]]
            source_str_fb = "\n".join(f"  - {s}" for s in sources_fb)
            return (
                f"📄 출처:\n{source_str_fb}\n"
                f"📅 시행일: {date_str} (헤더 부분 누락 — 연도 기반 추정)  |  문제 {problem_num}\n"
                f"{'─' * 40}\n\n"
                f"{problem_text_fb}"
            )

    return (
        f"'{date_str}' 시행 파일은 찾았으나 {problem_num}번 문제를 추출하지 못했습니다.\n"
        f"후보 파일: {', '.join(f.name for f in candidate_files[:5])}"
    )


@mcp.tool()
def list_exam_problems(date_str: str) -> str:
    """특정 시행일의 기출문제 목록(번호 + 제목)을 반환합니다.
    get_exam_problem 호출 전 "몇 번까지 있는지" 확인할 때 사용.

    Args:
        date_str: 시행일. 예: "2020.11.29", "2021.7.10"

    Returns:
        문제 번호별 첫 줄(제목/조건 요약) 목록.
    """
    vault = Path(OBSIDIAN_VAULT_PATH)
    date_esc = re.escape(date_str)
    candidate_files: list[Path] = []
    for md_file in vault.rglob("*.md"):
        try:
            if re.search(date_esc, md_file.read_text(encoding="utf-8", errors="ignore")):
                candidate_files.append(md_file)
        except Exception:
            continue

    if not candidate_files:
        return f"'{date_str}' 시행 문제가 포함된 파일을 찾을 수 없습니다."

    candidate_files.sort(key=lambda f: (0 if "OCU" in str(f) else 1, f.name))
    seen: set[str] = set()

    _list_next_date_re = re.compile(
        r'^(?![\*\|\-\s])(?:#{1,4}\s+)?.{0,25}(\d{4}\s*과년도|\d{4}\.\d{1,2}\.\d{1,2}\s*시행)',
        re.MULTILINE
    )
    _list_toc_re = re.compile(r'^\s*[\*\-]\s+|^\s*\|')
    prob_header_re = re.compile(
        r'^(#{1,4}\s+)?문제\s*(\d+)(?!\d)\b[ \t]*\n+(.*)',
        re.MULTILINE
    )

    def _find_content_date_list(text: str, esc: str):
        for m in re.finditer(esc, text):
            ls = text.rfind('\n', 0, m.start()) + 1
            le = text.find('\n', m.start())
            line = text[ls:(le if le != -1 else len(text))]
            if _list_toc_re.match(line):
                continue
            if re.search(r'\|\s*\d+\s*\|?\s*$', line):
                continue
            return m
        return None

    for anchor in candidate_files:
        book_key = str(anchor.parent) + "/" + _book_prefix(anchor)
        if book_key in seen:
            continue
        seen.add(book_key)

        combined, _ = _build_combined_text(anchor)
        dm = _find_content_date_list(combined, date_esc)
        if not dm:
            continue

        line_start = combined.rfind('\n', 0, dm.start()) + 1
        next_date_m = _list_next_date_re.search(combined, dm.end() + 1)
        section_end = next_date_m.start() if next_date_m else len(combined)
        search_region = combined[line_start:section_end]

        problems: list[tuple[int, str]] = []
        for m in prob_header_re.finditer(search_region):
            num = int(m.group(2))
            first_line = m.group(3).strip()[:80]
            if not any(p[0] == num for p in problems):
                problems.append((num, first_line))

        if problems:
            problems.sort(key=lambda x: x[0])
            lines = [f"📅 {date_str} 시행 — 총 {len(problems)}문제\n"]
            for num, title in problems:
                lines.append(f"  문제 {num:2d}. {title}")
            return "\n".join(lines)

    return f"'{date_str}' 시행 파일에서 문제 목록을 추출하지 못했습니다."


# ── 진입점 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
