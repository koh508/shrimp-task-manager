"""
온유 세션 매니저 (session_manager.py)

OnewAgentV2를 감싸는 래퍼 레이어.
obsidian_agent.py의 고유 기능(ADHD 엔진, 세션 관리, 과금 보호, 오답 패턴 등)을 보존.

사용법:
    from onew_core.session_manager import OnewSessionManager
    onew = OnewSessionManager()
    onew.ask("공조냉동 냉동효과 설명해줘")
"""
import os, sys, json, re, time
from datetime import datetime, timedelta
from pathlib import Path

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_PATH = os.path.dirname(SYSTEM_DIR)

sys.path.insert(0, SYSTEM_DIR)

from onew_locks import _atomic_json_write, _atomic_md_append
from onew_core.agent import OnewAgentV2

# ── 경로 상수 ─────────────────────────────────────────────────────────────────
USAGE_LOG_FILE    = os.path.join(SYSTEM_DIR, "api_usage_log.json")
ENTITY_FILE       = os.path.join(SYSTEM_DIR, "onew_entities.json")
USER_PROFILE_PATH  = os.path.join(SYSTEM_DIR, "User_Profile.md")  # 레거시 fallback
_MEMORY_DIR        = os.path.join(SYSTEM_DIR, "memory")
USER_CONTEXT_PATH  = os.path.join(_MEMORY_DIR, "context.md")
MISTAKE_LOG_FILE  = os.path.join(SYSTEM_DIR, "오답_패턴.md")
LOCATION_FILE     = os.path.join(SYSTEM_DIR, "onew_location.json")
PID_FILE          = os.path.join(SYSTEM_DIR, "onew.pid")   # legacy와 공유 — 이중실행 방지
SUMMARY_DIR       = os.path.join(VAULT_PATH, "대화요약")
DIALOG_DIR        = os.path.join(VAULT_PATH, "대화기록")
WORK_LOG_DIR      = os.path.join(VAULT_PATH, "작업일지")
WORK_INDEX_FILE   = os.path.join(SYSTEM_DIR, "onew_work_index.md")

MAX_DAILY_CHAT = 500   # 하드스톱 (과금 보호)
MAX_TURNS      = 10    # 이 턴 수 초과 시 세션 리셋

# ── 필터 키워드 ───────────────────────────────────────────────────────────────
SENSITIVE_KEYWORDS = [
    "양악", "수술", "산재", "요양", "우울", "힘들어", "외로워", "불안",
    "상처", "아파", "속상", "고민", "스트레스", "감정", "마음이", "외롭",
    "죽고", "포기", "무기력", "치료", "병원", "정신", "심리",
]

CORRECTION_KEYWORDS = [
    "틀렸어", "아니야", "아니잖아", "다시 해줘", "잘못됐어",
    "틀린 것 같아", "그게 아니라", "잘못 알고 있어", "오답이야",
]

VAGUE_REFS = [
    "그거", "그것", "그게", "그걸", "아까", "저번에", "그때", "이전에", "방금",
    "그 방법", "그 파일", "그 코드", "그 문제", "그 내용",
    "거기", "거기서", "이거", "이것", "저거", "저것",
]

CODE_WRITE_TRIGGERS = [
    "파일 만들어", "만들어줘", "생성해줘", "작성해줘", "코드 작성",
    "write_file", "edit_file", "수정해줘", "고쳐줘", ".py", ".md 만",
]

STUDY_DONE_KW = ["공부 완료", "공부 끝", "오늘 공부 다 했어", "다 풀었어", "문제 다 풀었어"]
DOPAMINE_KW   = ["도파민 메뉴", "뭐 하지", "지루해", "보상 뭐야"]
ADHD_STATUS_KW = ["adhd 현황", "스트릭", "반응률", "공부 기록"]


# ══════════════════════════════════════════════════════════════════════════════
# 유틸리티 함수 (obsidian_agent.py의 side-effect 없이 독립 구현)
# ══════════════════════════════════════════════════════════════════════════════

def _get_today_usage(category: str) -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        if os.path.exists(USAGE_LOG_FILE):
            with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data.get(today, {}).get(category, 0)
    except:
        pass
    return 0


def _increment_usage(category: str):
    today = datetime.now().strftime("%Y-%m-%d")
    try:
        data = {}
        if os.path.exists(USAGE_LOG_FILE):
            with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        if today not in data:
            data[today] = {}
        data[today][category] = data[today].get(category, 0) + 1
        _atomic_json_write(USAGE_LOG_FILE, data)
    except:
        pass


def _send_telegram(msg: str):
    """텔레그램 알림 전송 (환경변수 TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 필요)."""
    token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
    if not token or not chat_id:
        return
    try:
        import urllib.request, urllib.parse
        data = urllib.parse.urlencode({
            "chat_id": chat_id, "text": msg, "parse_mode": "Markdown"
        }).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage", data=data
        )
        urllib.request.urlopen(req, timeout=5)
    except:
        pass


def _detect_location() -> str:
    """onew_location.json manual_override 우선, 없으면 'home'."""
    try:
        if os.path.exists(LOCATION_FILE):
            with open(LOCATION_FILE, "r", encoding="utf-8") as f:
                cfg = json.load(f)
            if "manual_override" in cfg:
                return "work" if cfg["manual_override"] else "home"
    except:
        pass
    return "home"


def _save_mistake(question: str, wrong_answer: str, correction: str):
    now  = datetime.now().strftime("%Y-%m-%d %H:%M")
    line = (
        f"\n---\n**날짜:** {now}\n"
        f"**질문:** {question[:200]}\n"
        f"**오답:** {wrong_answer[:200]}\n"
        f"**교정:** {correction[:200]}\n"
    )
    try:
        _atomic_md_append(MISTAKE_LOG_FILE, line)
    except:
        pass


def _load_recent_summaries(days: int = 3) -> str:
    """최근 N일치 대화요약 파일 로드 (API 0원)."""
    if not os.path.exists(SUMMARY_DIR):
        return ""
    today  = datetime.now().date()
    blocks = []
    for i in range(1, days + 1):
        target = today - timedelta(days=i)
        fpath  = os.path.join(SUMMARY_DIR, f"{target}_대화요약.md")
        if not os.path.exists(fpath):
            continue
        try:
            text = Path(fpath).read_text(encoding="utf-8")
            if text.startswith("---"):
                end = text.find("---", 3)
                if end != -1:
                    text = text[end + 3:].strip()
            blocks.append(f"[{target} 요약]\n{text[:800]}")
        except:
            continue
    return "\n\n".join(blocks)


def _refresh_work_index():
    """온유 시작 시 onew_work_index.md를 최신 상태로 갱신 (API 0원).
    실패해도 시작 흐름에 영향 없음.
    """
    try:
        sys.path.insert(0, SYSTEM_DIR)
        import onew_make_work_index as _idx
        result = _idx.build_index()
        with open(WORK_INDEX_FILE, "w", encoding="utf-8") as f:
            f.write(result)
        print("[OnewSessionManager] 작업 인덱스 갱신 완료")
    except Exception as e:
        print(f"[OnewSessionManager] 작업 인덱스 갱신 실패 (무시): {e}")


def _load_claude_work_context(today_detail_chars: int = 600) -> str:
    """Claude Code 작업 컨텍스트 로드 (온유 환각 방지용).

    반환 구성:
    1. 오늘 작업일지 파일들 — 상세 내용 (변경 파일·함수 포함)
    2. 최근 3일치 작업 요약 — onew_work_index.md 에서 추출

    API 0원, 파일 읽기만.
    """
    today_str = datetime.now().strftime("%Y-%m-%d")
    parts: list[str] = []

    # ── 1. 오늘 작업일지 상세 ────────────────────────────────────────────────
    today_logs: list[str] = []
    if os.path.isdir(WORK_LOG_DIR):
        for f in sorted(Path(WORK_LOG_DIR).glob(f"{today_str}_*.md"), reverse=True):
            try:
                raw = f.read_text(encoding="utf-8", errors="ignore")
                # YAML 프론트매터 제거
                body = re.sub(r'^---[\s\S]*?---\n?', '', raw).strip()
                title = f.stem.replace(f"{today_str}_", "").replace("_", " ")
                today_logs.append(f"### {title}\n{body[:today_detail_chars]}")
            except Exception:
                continue

    if today_logs:
        parts.append(
            f"[오늘({today_str}) Claude Code 작업 — 변경 파일·함수 포함]\n\n"
            + "\n\n".join(today_logs)
        )

    # ── 2. 최근 3일 작업 요약 (index에서 추출) ───────────────────────────────
    if os.path.exists(WORK_INDEX_FILE):
        try:
            index_text = Path(WORK_INDEX_FILE).read_text(encoding="utf-8")
            # "## Claude Code 작업일지" 섹션만 추출
            m = re.search(
                r'## Claude Code 작업일지\n([\s\S]*?)(?=\n## |\Z)', index_text
            )
            if m:
                section = m.group(1).strip()
                # 최근 3개 날짜 블록만 (### YYYY-MM-DD 기준)
                blocks = re.split(r'(?=\n### \d{4}-\d{2}-\d{2})', section)
                recent_blocks = [b.strip() for b in blocks if b.strip()][:3]
                if recent_blocks:
                    parts.append(
                        "[최근 3일 Claude Code 작업 요약]\n\n"
                        + "\n\n".join(recent_blocks)
                    )
        except Exception:
            pass

    return "\n\n".join(parts)


def _check_single_instance():
    """이미 실행 중인 온유(v2 또는 legacy)가 있으면 경고 후 종료.
    legacy의 onew.pid와 동일 파일을 공유 → v2+legacy 동시 실행 방지.
    cmdline으로 실제 온유인지 확인 (PID 재사용 오감지 방지)."""
    if os.path.exists(PID_FILE):
        try:
            with open(PID_FILE) as f:
                old_pid = int(f.read().strip())
            import psutil as _ps
            if _ps.pid_exists(old_pid):
                proc = _ps.Process(old_pid)
                cmdline = ' '.join(proc.cmdline()).lower()
                if "python" in proc.name().lower() and "obsidian_agent" in cmdline:
                    print(f"⚠️ [이중 실행 방지] 온유가 이미 실행 중입니다 (PID {old_pid}).")
                    print("   기존 창에서 '끄기'를 입력하거나 Ctrl+C로 종료하세요.")
                    sys.exit(1)
                # 온유가 아닌 다른 python → 좀비 PID 파일, 정리 후 계속
        except (ValueError, ImportError, Exception):
            pass
        # 좀비 PID 파일 정리
        try:
            os.remove(PID_FILE)
        except Exception:
            pass
    try:
        with open(PID_FILE, "w") as f:
            f.write(str(os.getpid()))
        import atexit
        atexit.register(lambda: os.path.exists(PID_FILE) and os.remove(PID_FILE))
    except Exception:
        pass


def _load_entities() -> list:
    try:
        if os.path.exists(ENTITY_FILE):
            with open(ENTITY_FILE, "r", encoding="utf-8") as f:
                return json.load(f).get("entities", [])
    except:
        pass
    return []


def _save_entities(new_entities: list):
    """파일의 기존 엔티티와 merge 후 저장.
    legacy ↔ v2 교차 사용 시 '마지막 쓴 쪽이 이김' 문제 방지."""
    try:
        existing = _load_entities()
        # value 기준 중복 제거, 새 항목 우선
        seen, merged = set(), []
        for e in (new_entities + existing):
            key = e.get("value", "")
            if key and key not in seen:
                seen.add(key)
                merged.append(e)
        _atomic_json_write(ENTITY_FILE, {
            "entities": merged[:50],
            "updated":  datetime.now().strftime("%Y-%m-%d %H:%M"),
        })
    except:
        pass


# ══════════════════════════════════════════════════════════════════════════════
# Context Bleed 방지 헬퍼
# ══════════════════════════════════════════════════════════════════════════════

_FOCUS_TITLE = re.compile(
    r'([가-힣]{1,4})(이사|대표|과장|차장|부장|팀장|계장|주임|대리|사원|기사|조장|소장)(님)?'
)
_FOCUS_DATE  = re.compile(r'\d{4}-\d{2}-\d{2}')


def _extract_query_focus(query: str) -> list[str]:
    """
    현재 쿼리에서 핵심 분석 대상(인물명+직함, 날짜) 추출.
    agent.run() 전 Context Bleed 방지 핀으로 사용.
    """
    focus = []
    # 직함 결합 인물: "고차장님", "양대리"
    for m in _FOCUS_TITLE.finditer(query):
        name_part  = m.group(1)
        title_part = m.group(2)
        honorific  = m.group(3) or ''
        if len(name_part) >= 1:
            focus.append(f"{name_part}{title_part}{honorific}")
    # 날짜: "2024-12-08"
    for m in _FOCUS_DATE.finditer(query):
        focus.append(m.group(0))
    return focus


# ══════════════════════════════════════════════════════════════════════════════
# OnewSessionManager
# ══════════════════════════════════════════════════════════════════════════════

class OnewSessionManager:
    """
    OnewAgentV2를 감싸는 세션 관리 레이어.

    obsidian_agent.py 고유 기능 보존:
      - 10턴 자동 세션 리셋 + 대화요약 주입
      - ADHD 엔진 (on_user_message, 스트릭, 도파민 메뉴)
      - 과금 하드스톱 500회
      - 회사 모드 민감 주제 차단
      - 오답 패턴 자동 기록
      - 코드 작업 전 실패사례 선조회 힌트
      - 3 Q&A마다 엔티티 워킹메모리 갱신
      - 3 Q&A마다 User_Profile.md 자동 업데이트
    """

    def __init__(self, location_mode: str = None):
        # 이중 실행 방지는 obsidian_agent.py __main__ 블록에서만 호출
        # 여기서 호출하면 자기 자신의 PID를 차단하는 버그 발생
        self.location_mode = location_mode or _detect_location()
        self.history: list  = []   # [{"role": "user"|"model", "text": str}]
        self._entities: list = _load_entities()

        # 작업 인덱스 최신화 (API 0원 — Claude Code 작업 내역 갱신)
        _refresh_work_index()

        # 세션 복원 컨텍스트 조립 (API 0원)
        extra_ctx = self._build_restore_context()

        # OnewAgentV2 초기화 — MCP 서버 연결 + 복원 컨텍스트 시스템 프롬프트 주입
        print("[OnewSessionManager] 에이전트 초기화 중...")
        self.agent = OnewAgentV2(location_mode=self.location_mode)
        if extra_ctx:
            self.agent.reload(self.location_mode, extra_context=extra_ctx)

    # ── 내부 헬퍼 ──────────────────────────────────────────────────────────────

    def _build_restore_context(self) -> str:
        """시스템 프롬프트에 주입할 세션 복원 블록 조립."""
        parts = []

        # Claude Code 작업 컨텍스트 (환각 방지 — 오늘 변경 파일·함수 명시)
        claude_ctx = _load_claude_work_context()
        if claude_ctx:
            parts.append(claude_ctx)

        # 최근 대화 요약
        recent = _load_recent_summaries(days=3)
        if recent:
            parts.append(f"[최근 대화 요약 — 참고용]\n{recent}")

        # 엔티티 워킹메모리
        entities = self._entities
        if entities:
            ent_lines = "\n".join(f"- [{e['type']}] {e['value']}" for e in entities[-15:])
            parts.append(f"[대화 중 언급된 핵심 항목 — 지시어 해석 시 우선 참조]\n{ent_lines}")

        return "\n\n".join(parts)

    def _reset_session(self):
        """10턴 초과 시 대화기록 저장 + 에이전트 재빌드."""
        self._save_history()
        print("💾 [자동저장] 대화 기록 저장됨")

        # 직전 6 Q&A(12 레코드) 보존 → 새 세션에 맥락으로 주입
        recent_recs = self.history[-12:] if len(self.history) >= 12 else self.history[:]
        recent_str  = "\n".join(
            f"{'사용자' if r['role'] == 'user' else '온유'}: {r['text'][:300]}"
            for r in recent_recs
        )
        self.history = []

        # 요약 파일 로드 (API 0원)
        extra_parts = []
        recent_ctx = _load_recent_summaries(days=3)
        if recent_ctx:
            extra_parts.append(f"[최근 대화 요약]\n{recent_ctx}")
        if recent_str:
            extra_parts.append(f"[직전 교환]\n{recent_str}")
        # 엔티티 워킹메모리
        self._entities = _load_entities()
        ent_ctx = self._build_restore_context()
        if ent_ctx:
            extra_parts.append(ent_ctx)

        # 에이전트 재빌드 (새 시스템 프롬프트 + 복원 컨텍스트)
        self.agent.reload(
            self.location_mode,
            extra_context="\n\n".join(extra_parts),
        )
        print("✅ 새 세션 시작")

        # 미완료 태스크 알림
        try:
            from onew_task_manager import get_pending_summary
            pending = get_pending_summary()
            if pending:
                print(f"\n{pending}")
        except:
            pass

    def _save_history(self):
        """대화기록 파일 저장 (대화기록/YYYY-MM/날짜_시각_온유_대화.md)."""
        if not self.history:
            return
        now       = datetime.now()
        month_dir = os.path.join(DIALOG_DIR, now.strftime("%Y-%m"))
        os.makedirs(month_dir, exist_ok=True)
        fname = os.path.join(
            month_dir,
            f"{now.strftime('%Y-%m-%d_%H-%M')}_온유_대화_v2.md"  # legacy 파일명과 구분
        )
        lines = [
            f"---\ntags: [대화기록]\n날짜: {now.strftime('%Y-%m-%d')}\n---\n",
            f"# {now.strftime('%Y-%m-%d %H:%M')} 온유 대화\n",
        ]
        for rec in self.history:
            role = "**사용자**" if rec["role"] == "user" else "**온유**"
            lines.append(f"\n{role}: {rec['text']}\n")
        try:
            with open(fname, "w", encoding="utf-8") as f:
                f.write("".join(lines))
        except:
            pass

    def _extract_entities(self, query: str, answer: str):
        """3 Q&A마다 엔티티 추출 → 워킹메모리 갱신."""
        turn = len(self.history) // 2
        if turn % 3 != 0:
            return
        try:
            from google import genai as _genai
            from google.genai import types as _types
            _client = _genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
            res = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    "다음 Q&A에서 핵심 엔티티를 JSON 배열로만 추출하라.\n"
                    "형식: [{\"type\": \"설비|인물|장소|날짜|파일|개념\", \"value\": \"값\"}]\n"
                    "없으면 빈 배열 []만 출력.\n\n"
                    f"Q: {query[:300]}\nA: {answer[:300]}"
                ),
                config=_types.GenerateContentConfig(
                    thinking_config=_types.ThinkingConfig(thinking_budget=0))
            )
            raw = re.sub(r"```json\n?|```", "", res.text).strip()
            new_entities = json.loads(raw)
            if new_entities:
                self._entities = (self._entities + new_entities)[-50:]
                _save_entities(self._entities)
                _increment_usage("entity")
        except:
            pass  # 엔티티 추출 실패해도 대화에 영향 없음

    def _update_profile(self, query: str, answer: str):
        """3 Q&A마다 memory/context.md '최근 상태' 섹션에 새 사실 추가.
        User_Profile.md(레거시)에는 쓰지 않음."""
        turn = len(self.history) // 2
        if turn % 3 != 0:
            return
        if not os.path.exists(USER_CONTEXT_PATH):
            return
        try:
            from google import genai as _genai
            from google.genai import types as _types
            _client = _genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
            res = _client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    "대화에서 '고용준'에 관한 새로운 사실/상태 변화를 추출하라.\n"
                    "추출 대상: 건강 상태, 목표 진척, 중요한 결정, 감정 변화, 일상 변화\n"
                    "형식: 각 줄에 한 문장. 없으면 '없음'만 출력.\n"
                    "⛔ 제외: 인물 이름 단순 언급, 날짜 단순 언급, 수면/일상 언급, AI 도구 관련\n\n"
                    f"Q: {query[:200]}\nA: {answer[:200]}"
                ),
                config=_types.GenerateContentConfig(
                    thinking_config=_types.ThinkingConfig(thinking_budget=0))
            )
            raw = res.text.strip()
            if not raw or raw == "없음":
                return
            facts = [l.strip() for l in raw.splitlines()
                     if l.strip() and l.strip() != "없음"]
            if not facts:
                return

            today = datetime.now().strftime("%Y-%m-%d")
            new_lines = "\n".join(f"- {today}: {f.lstrip('- ')}" for f in facts)

            content = Path(USER_CONTEXT_PATH).read_text(encoding="utf-8")
            SECTION = "## 최근 상태 (자동 업데이트"
            sec_idx = content.find(SECTION)
            if sec_idx != -1:
                insert_at = content.find("\n", sec_idx) + 1
                while content[insert_at:insert_at+4] == "<!--":
                    insert_at = content.find("\n", insert_at) + 1
                content = content[:insert_at] + new_lines + "\n" + content[insert_at:]
            else:
                content = content.rstrip() + f"\n\n{SECTION} — 온유 자동갱신)\n{new_lines}\n"

            # 최근 상태 최대 15개 유지
            lines = content.splitlines()
            state_start = next((i for i, l in enumerate(lines) if SECTION in l), None)
            if state_start is not None:
                next_section = next(
                    (i for i, l in enumerate(lines[state_start+1:], state_start+1)
                     if l.startswith("## ")), len(lines))
                section_body = lines[state_start+1:next_section]
                after_section = lines[next_section:]
                state_lines = [l for l in section_body if l.startswith("- ")]
                if len(state_lines) > 15:
                    excess = len(state_lines) - 15
                    removed = 0
                    new_body = []
                    for l in section_body:
                        if l.startswith("- ") and removed < excess:
                            removed += 1
                        else:
                            new_body.append(l)
                    content = (
                        "\n".join(lines[:state_start+1]) + "\n"
                        + "\n".join(new_body)
                        + ("\n" + "\n".join(after_section) if after_section else "")
                    )

            Path(USER_CONTEXT_PATH).write_text(content, encoding="utf-8")
            _increment_usage("profile_update")
        except:
            pass

    # ── 공개 API ──────────────────────────────────────────────────────────────

    def ask(self, query: str) -> str:
        """쿼리를 처리하고 최종 응답을 반환 (콘솔 출력 포함)."""

        # ── 1. 세션 리셋 확인 (10턴 초과) ────────────────────────────────────
        if len(self.history) >= MAX_TURNS * 2:
            self._reset_session()

        # ── 2. 대화 활동 시각 갱신 ────────────────────────────────────────────
        try:
            import onew_shared; onew_shared.touch()
        except:
            pass

        # ── 3. ADHD 엔진 ─────────────────────────────────────────────────────
        try:
            import onew_adhd as _adhd
            _adhd.on_user_message()
            goal_msg = _adhd.detect_learning_goal(query)
            if goal_msg:
                print(f"\n{goal_msg}\n")
        except:
            pass

        if any(kw in query for kw in STUDY_DONE_KW):
            try:
                import onew_adhd as _adhd
                print(f"\n{_adhd.record_study_done()}\n")
            except:
                pass

        if any(kw in query for kw in DOPAMINE_KW):
            try:
                import onew_adhd as _adhd
                print(f"\n{_adhd.dopamine_menu()}\n")
            except:
                pass

        if any(kw in query for kw in ADHD_STATUS_KW):
            try:
                import onew_adhd as _adhd
                print(f"\n{_adhd.adhd_status()}\n")
            except:
                pass

        # ── 4. 과금 하드스톱 (500회) ─────────────────────────────────────────
        today_count = _get_today_usage("chat")
        if today_count >= MAX_DAILY_CHAT:
            msg = f"🔴 [과금 보호] 오늘 대화 API {today_count}회 초과. 내일 다시 사용하세요."
            print(msg)
            _send_telegram(f"🔴 *온유 대화 한도 초과*\n\n오늘 {today_count}회 도달.\n비정상 루프 가능성.")
            return msg

        # ── 5. 회사 모드 민감 주제 차단 ──────────────────────────────────────
        if self.location_mode == "work":
            if any(kw in query for kw in SENSITIVE_KEYWORDS):
                print("=" * 50)
                print("💡 온유: 이 주제는 집에서 이야기해요.")
                print("=" * 50)
                return "이 주제는 집에서 이야기해요."

        # ── 6. 오답 패턴 감지 → 자동 저장 ────────────────────────────────────
        if any(kw in query for kw in CORRECTION_KEYWORDS) and len(self.history) >= 2:
            prev_q = self.history[-2].get("text", "")
            prev_a = self.history[-1].get("text", "")
            _save_mistake(prev_q, prev_a, query)
            print("📝 [자율학습] 오답 패턴 기록됨 → 오답_패턴.md")

        # ── 7. 쿼리 보강 ─────────────────────────────────────────────────────
        enriched = query

        # 지시어 감지: 이전 대화 맥락을 힌트로 첨부
        if any(ref in query for ref in VAGUE_REFS) and self.history:
            ctx = " ".join(r["text"][:150] for r in self.history[-6:])
            enriched = f"{query}\n[이전 대화 맥락 참고]: {ctx[:400]}"
            print("🔗 [지시어 감지] 이전 대화 맥락으로 쿼리 보강")

        # 코드 작업 감지: 실패사례 선조회 힌트 주입
        if any(kw in query for kw in CODE_WRITE_TRIGGERS):
            enriched += (
                f"\n\n⚠️ 코드 작업 전 반드시 search_vault('실패사례 코드교훈 {query[:40]}')"
                f" MCP 도구를 먼저 호출하라."
            )

        # ── 8. 에이전트 호출 ──────────────────────────────────────────────────
        print(f"\n온유(Onew) 🔍 처리 중...")
        try:
            # ── Single-Shot Q&A 파이프라인 먼저 시도 ──────────────────────────
            # ACTION 명령 → None 반환 → agent.run()으로 폴백
            # Q&A → str 반환 → 토큰 97% 절감
            from onew_core.query_pipeline import handle_query as _hq
            from onew_core.prompt_builder import build_static as _build_static
            from datetime import datetime as _dt
            _date_suffix = (
                f"\n\n현재 날짜와 시간: "
                f"{_dt.now().strftime('%Y년 %m월 %d일 %H시 %M분')} (로컬 시스템 시간)"
            )
            # build_static만 사용 (도구 호출 지시 없음) + 날짜만 추가
            # build() 전체 사용 시 onew_system_prompt.md의 tool_code 지시가
            # LiteLLM Single-Shot 경로에서 literal 텍스트로 출력되는 문제 방지
            _single_shot_guard = (
                "\n\n[★ Single-Shot 모드 — 도구 완전 비활성화 ★]\n"
                "이 응답에서는 search_vault, read_file, write_file, edit_file 등 "
                "모든 도구·함수가 존재하지 않는다. 위 지시 중 '도구를 호출하라', "
                "'search_vault로 확인하라' 등의 모든 도구 호출 지시는 이 모드에서 무효다.\n"
                "search_vault(...), tools.read_file(...) 등 함수 호출 형식의 텍스트를 "
                "출력하는 것은 절대 금지다. 출력하면 오답 처리된다.\n"
                "RAG 검색 결과는 이미 위 컨텍스트에 포함되어 있다. 그것만 참고하여 "
                "순수 자연어로만 답하라. 컨텍스트에 답이 없으면 '확인되지 않습니다'로 답하라."
            )
            _sys_prompt = _build_static(self.location_mode) + _date_suffix + _single_shot_guard

            # ── 짧은 확인 응답 감지 ───────────────────────────────────────────
            # 온유가 직전에 "할까요?/볼까요?/드릴까요?" 등으로 끝난 경우
            # 사용자의 짧은 긍정("응", "응 해줘", "생성해봐" 등)을 ACTION으로 처리
            _CONFIRM_RE = re.compile(r'(할까요|볼까요|드릴까요|생성할까요|만들까요|실행할까요|써드릴까요)\s*\??$')
            _AFFIRM_RE  = re.compile(r'^(응|어|ㅇ|네|예|그래|좋아|해줘|해봐|생성해봐|만들어봐|실행해봐|써봐)\s*[.,!]?\s*$')
            _last_assistant = ""
            if self.history:
                for _h in reversed(self.history):
                    if _h.get("role") == "assistant":
                        _last_assistant = _h.get("content", "")
                        break
            _is_confirm_followup = (
                bool(_CONFIRM_RE.search(_last_assistant)) and
                bool(_AFFIRM_RE.match(query.strip()))
            )
            if _is_confirm_followup:
                _pipeline_result = None  # ACTION 강제
            else:
                _pipeline_result = _hq(enriched, _sys_prompt, self.history)

            if _pipeline_result is not None:
                # Q&A 파이프라인 처리 완료
                response = _pipeline_result
                print("  [Single-Shot]")
            else:
                # ACTION 명령 → smolagents MCP 루프
                # Context Bleed 방지: 현재 쿼리의 핵심 대상을 enriched 끝에 핀으로 주입
                _focus = _extract_query_focus(query)
                if _focus:
                    enriched += (
                        f"\n\n[현재 질문 집중 지시] "
                        f"이 요청의 분석 대상은 {', '.join(_focus[:3])} 입니다. "
                        f"도구 결과를 해석할 때 반드시 이 대상을 기준으로 내용을 찾고 요약하라. "
                        f"워킹메모리의 다른 인물·주제와 혼동하지 마라."
                    )
                # [SKILL INTERCEPT] LanceDB 검색 이후 — Knowledge RAG 오염 없음
                # 에러/코드 작업 의도 감지 시 관련 스킬 힌트 주입
                _q_lower = query.lower()
                _has_error  = any(k in _q_lower for k in ("error", "traceback", "exception", "오류", "에러"))
                # "수정" 단독은 제외 — md 파일 편집도 걸리는 오탐 방지
                # 코드 맥락(".py", "함수", "클래스") 이 있을 때만 트리거
                _has_code_ctx = any(k in _q_lower for k in (".py", "함수", "클래스", "코드", "fix", "debug"))
                _has_intent = _has_code_ctx and any(k in _q_lower for k in ("수정", "작성", "실행", "고쳐"))
                if _has_error or _has_intent:
                    enriched += (
                        "\n\n[SKILL HINT] 코드/에러 관련 작업입니다. "
                        "search_skills()로 관련 스킬을 검색하세요. "
                        "결과가 있으면 사용자에게 '관련 스킬이 있습니다: [스킬명] — 적용할까요?' 라고 먼저 물어보고, "
                        "동의하면 해당 스킬을 참고해 작업하세요. 없으면 그냥 진행하세요."
                    )
                    print("  [INTERCEPT] 스킬 힌트 주입됨")
                response = self.agent.run(enriched, reset=False)
                print("  [Agent-Run]")

            _increment_usage("chat")
        except Exception as e:
            err_msg = f"[에이전트 오류] {e}"
            print(err_msg)
            _send_telegram(f"⚠️ *온유 에이전트 오류*\n\n{str(e)[:300]}")
            return err_msg

        # ── 9. 히스토리 기록 ──────────────────────────────────────────────────
        self.history.append({"role": "user", "text": query})

        # Phase 13-B: History Guard — 저품질 응답 히스토리 제외
        _LOW_CONF = ["잘 모르겠습니다", "확실하지 않습니다", "추정됩니다"]
        try:
            from onew_core.query_pipeline import _last_metrics as _qp_meta
            _skip = (
                _qp_meta.get("degraded")
                or _qp_meta.get("action") == "ANSWER_FALLBACK"
                or any(p in response for p in _LOW_CONF)
            )
            if _skip:
                logger.debug("[History Guard] 저품질 응답 제외 (action=%s)",
                             _qp_meta.get("action", "?"))
            else:
                self.history.append({"role": "model", "text": response})
        except Exception:
            self.history.append({"role": "model", "text": response})

        # ── 10. 사후 처리 ─────────────────────────────────────────────────────
        self._extract_entities(query, response)
        self._update_profile(query, response)

        # ── 11. 과금 경고 (소프트 한도) ──────────────────────────────────────
        new_count = _get_today_usage("chat")
        if new_count == 500:
            _send_telegram(f"⚠️ [과금 경고] chat API 오늘 {new_count}회 도달.")

        # ── 출력 ─────────────────────────────────────────────────────────────
        print("=" * 50)
        print(f"💡 온유:\n{response}\n")
        print("=" * 50)

        return response

    def set_location(self, mode: str):
        """위치 모드 변경 ('home' | 'work') + onew_location.json 저장 (재시작 후에도 유지)."""
        self.location_mode = mode
        # onew_location.json에 manual_override 저장 → legacy 경로와 공유
        try:
            cfg = {}
            if os.path.exists(LOCATION_FILE):
                with open(LOCATION_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
            cfg["manual_override"] = (mode == "work")
            with open(LOCATION_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, ensure_ascii=False, indent=2)
        except Exception:
            pass
        self.agent.reload(mode, extra_context=self._build_restore_context())
        status = "🔒 [회사 모드 ON]" if mode == "work" else "🔓 [홈 모드]"
        print(f"{status} 위치 모드 변경 + 저장됨: {mode}")

    def close(self):
        """종료 시 대화기록 저장 + MCP 연결 종료."""
        self._save_history()
        self.agent.close()


# ── 직접 실행 테스트 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("OnewSessionManager 초기화 중...")
    onew = OnewSessionManager()
    print("완료. 질문을 입력하세요 (종료: '끄기' 또는 Ctrl+C)\n")

    import atexit
    atexit.register(onew.close)

    while True:
        try:
            q = input("질문 > ").strip()
            if not q:
                continue
            if q in ["끄기", "종료", "exit", "quit"]:
                print("온유를 종료합니다.")
                break
            onew.ask(q)
            print()
        except KeyboardInterrupt:
            print("\n종료")
            break
