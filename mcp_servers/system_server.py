"""
온유 시스템 MCP 서버 (system_server.py)
시스템 제어, 캘린더, 클리핑, 태스크 관리, 시크릿 모드 등 20개 도구 제공.
실행: python mcp_servers/system_server.py
"""
import os, sys, json, subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import List

SYSTEM_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VAULT_DIR    = os.path.dirname(SYSTEM_DIR)

sys.path.insert(0, SYSTEM_DIR)

# ── 경로 상수 ──────────────────────────────────────────────────────────────────
AUTO_SCRIPTS_DIR    = os.path.join(SYSTEM_DIR, "auto_scripts")
USAGE_LOG_FILE      = os.path.join(SYSTEM_DIR, "api_usage_log.json")
CLIP_CONFIG_FILE    = os.path.join(SYSTEM_DIR, "clip_config.json")
LOCATION_CONFIG_FILE= os.path.join(SYSTEM_DIR, "onew_location.json")
WORKING_MEMORY_DIR  = os.path.join(SYSTEM_DIR, "working_memory")
ERROR_LOG_FILE      = os.path.join(SYSTEM_DIR, "온유_오류.md")
CALENDAR_CREDS_FILE = os.path.join(SYSTEM_DIR, "calendar_credentials.json")
CALENDAR_TOKEN_FILE = os.path.join(SYSTEM_DIR, "calendar_token.json")
CALENDAR_SCOPES     = ["https://www.googleapis.com/auth/calendar"]

CLIP_DEFAULTS = {
    "topics": [
        "Anthropic Claude 최신 연구 및 업데이트 anthropic.com",
        "Google DeepMind Gemini 연구 동향 deepmind.google",
        "Hugging Face 오픈소스 AI 모델 신규 출시 huggingface.co",
        "LLM 에이전트 MCP 프로토콜 개발 최신 기법",
        "AI 개발자 도구 실전 활용 사례 2026",
    ],
    "delay_seconds": 30,
    "max_clips": 10,
    "enabled": True,
}

_SHELL_SAFELIST = [
    "pip install", "pip uninstall", "pip list", "pip show", "pip freeze",
    "python -m",
    # "python -c" 제거 — execute_script() 사용 강제 (에이전트 인라인 코드 실행 방지)
]

_wifi_security_cache: dict = {}

# ── FastMCP 인스턴스 ──────────────────────────────────────────────────────────
from mcp.server.fastmcp import FastMCP
mcp = FastMCP("onew-system")


# ── 헬퍼 함수 ─────────────────────────────────────────────────────────────────
def _atomic_write(path: str, data: dict):
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _load_clip_config() -> dict:
    cfg = dict(CLIP_DEFAULTS)
    if os.path.exists(CLIP_CONFIG_FILE):
        try:
            with open(CLIP_CONFIG_FILE, "r", encoding="utf-8") as f:
                cfg.update(json.load(f))
        except:
            pass
    return cfg


def _save_clip_config(cfg: dict):
    try:
        with open(CLIP_CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except:
        pass


def _get_search_count() -> tuple:
    today = datetime.now().strftime("%Y-%m-%d")
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
    return data, today, data.get(f"search_{today}", 0)


def _get_wifi_security() -> str:
    """현재 WiFi 보안 방식 반환 ('open' / 'secured' / 'unknown'). 60초 캐시."""
    import time
    if _wifi_security_cache and time.time() - _wifi_security_cache.get("time", 0) < 60:
        return _wifi_security_cache["result"]
    try:
        _PS = ["powershell", "-NoProfile", "-Command"]
        r1 = subprocess.run(
            _PS + ["[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; netsh wlan show interfaces"],
            capture_output=True, timeout=7
        )
        output1 = r1.stdout.decode("utf-8", errors="ignore")
        ssid = ""
        for line in output1.splitlines():
            if "SSID" in line and "BSSID" not in line:
                ssid = line.split(":", 1)[-1].strip()
                break
        if not ssid:
            _wifi_security_cache.update({"result": "unknown", "time": time.time()})
            return "unknown"
        r2 = subprocess.run(
            _PS + [f"[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; netsh wlan show profiles name='{ssid}' key=clear"],
            capture_output=True, timeout=7
        )
        output2 = r2.stdout.decode("utf-8", errors="ignore").lower()
        if "open" in output2 or "none" in output2:
            result = "open"
        elif "wpa" in output2 or "wep" in output2 or "psk" in output2:
            result = "secured"
        else:
            result = "unknown"
        _wifi_security_cache.update({"result": result, "time": time.time()})
        return result
    except:
        return "unknown"


def _get_calendar_service():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from google.auth.transport.requests import Request
    from googleapiclient.discovery import build
    creds = None
    if os.path.exists(CALENDAR_TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(CALENDAR_TOKEN_FILE, CALENDAR_SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists(CALENDAR_CREDS_FILE):
                raise FileNotFoundError(
                    f"calendar_credentials.json 없음 → {CALENDAR_CREDS_FILE}")
            flow = InstalledAppFlow.from_client_secrets_file(CALENDAR_CREDS_FILE, CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(CALENDAR_TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)


def _normalize_dt(dt: str) -> str:
    dt = dt.strip().replace(" ", "T")
    if len(dt) == 16:
        dt += ":00"
    if len(dt) == 10:
        dt += "T00:00:00"
    return dt


# ── 스크립트 실행 ──────────────────────────────────────────────────────────────
@mcp.tool()
def execute_script(filepath: str) -> str:
    """파이썬 스크립트를 실행하고 결과를 반환합니다.
    SYSTEM/auto_scripts/ 폴더 내 파일이 권장됩니다.

    Args:
        filepath: 실행할 .py 파일 경로
    """
    try:
        p = Path(filepath).resolve()
        sandbox = Path(AUTO_SCRIPTS_DIR).resolve()
        allowed_roots = [
            Path(VAULT_DIR).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(p).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] Vault/바탕화면 외부 경로 실행 불가 → {filepath}"
        if p.suffix != ".py":
            return f"🚫 [보안] .py 파일만 실행 가능 → {filepath}"
        try:
            p.relative_to(sandbox)
            is_sandboxed = True
        except ValueError:
            is_sandboxed = False
        sandbox.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            [sys.executable, str(p)],
            capture_output=True, text=True, timeout=30,
            cwd=str(sandbox),
        )
        tag = "✅ [샌드박스]" if is_sandboxed else "⚠️ [비샌드박스]"
        return f"{tag}\n--- Output ---\n{res.stdout}\n--- Error ---\n{res.stderr}"
    except Exception as e:
        return f"Execution Failed: {e}"


@mcp.tool()
def run_shell_command(cmd: str) -> str:
    """안전한 쉘 명령어를 실행합니다.
    허용: pip install/uninstall/list/show/freeze, python -m, python -c

    Args:
        cmd: 실행할 명령어
    """
    cmd_stripped = cmd.strip()
    if not any(cmd_stripped.lower().startswith(s) for s in _SHELL_SAFELIST):
        return f"🚫 [보안] 허용되지 않는 명령어.\n허용 목록: {', '.join(_SHELL_SAFELIST)}"
    try:
        res = subprocess.run(
            cmd_stripped, shell=True, capture_output=True, text=True, timeout=60
        )
        parts = []
        if res.stdout.strip(): parts.append(f"[stdout]\n{res.stdout.strip()}")
        if res.stderr.strip(): parts.append(f"[stderr]\n{res.stderr.strip()}")
        parts.append(f"종료 코드: {res.returncode}")
        return "\n".join(parts)
    except subprocess.TimeoutExpired:
        return "Error: 명령어 실행 타임아웃 (60초)"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def code_safety_check() -> str:
    """핵심 코드 파일의 MD5 체크섬을 검증하고 안전 점검 보고서를 반환합니다."""
    try:
        sys.path.insert(0, SYSTEM_DIR)
        import path_cleanup
        return path_cleanup.run_all_checks()
    except Exception as e:
        return f"Error: path_cleanup 실행 실패 → {e}"


@mcp.tool()
def save_code_checksums() -> str:
    """현재 핵심 코드 파일들의 MD5 체크섬을 베이스라인으로 저장합니다."""
    try:
        sys.path.insert(0, SYSTEM_DIR)
        import path_cleanup
        return path_cleanup.save_checksums()
    except Exception as e:
        return f"Error: {e}"


# ── Google 캘린더 ─────────────────────────────────────────────────────────────
@mcp.tool()
def calendar_list(days: int = 7) -> str:
    """오늘부터 N일간의 구글 캘린더 일정을 조회합니다.

    Args:
        days: 조회 기간 (기본 7일)
    """
    try:
        from datetime import timezone
        service = _get_calendar_service()
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        events = events_result.get("items", [])
        if not events:
            return f"📅 향후 {days}일간 일정 없음."
        lines = [f"📅 향후 {days}일 일정:"]
        for e in events:
            start = e["start"].get("dateTime", e["start"].get("date", ""))[:16]
            lines.append(f"- [{start}] {e.get('summary', '(제목없음)')}  (id: {e['id']})")
        return "\n".join(lines)
    except Exception as e:
        return f"Calendar Error: {e}"


@mcp.tool()
def calendar_add(title: str, start: str, end: str, description: str = "") -> str:
    """구글 캘린더에 일정을 추가합니다. 같은 시간대 중복 일정을 자동 확인합니다.

    Args:
        title: 일정 제목
        start: 시작 시간 (YYYY-MM-DDTHH:MM)
        end: 종료 시간 (YYYY-MM-DDTHH:MM)
        description: 메모 (선택)
    """
    try:
        service = _get_calendar_service()
        start_norm = _normalize_dt(start)
        end_norm   = _normalize_dt(end)
        existing = service.events().list(
            calendarId="primary",
            timeMin=start_norm + "+09:00",
            timeMax=end_norm   + "+09:00",
            singleEvents=True,
            orderBy="startTime",
        ).execute().get("items", [])
        if existing:
            lines = [f"⚠️ [{start}~{end}] 시간대에 이미 일정이 있습니다:"]
            for e in existing:
                e_start = e["start"].get("dateTime", e["start"].get("date", ""))[:16]
                lines.append(f"  - [{e_start}] {e.get('summary', '(제목없음)')}  (id: {e['id']})")
            lines.append(f"\n그래도 '{title}' 추가하려면 calendar_add_force를 사용하세요.")
            return "\n".join(lines)
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": start_norm, "timeZone": "Asia/Seoul"},
            "end":   {"dateTime": end_norm,   "timeZone": "Asia/Seoul"},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ 일정 추가 완료: [{start}] {title}  (id: {created['id']})"
    except Exception as e:
        return f"Calendar Error: {e}"


@mcp.tool()
def calendar_add_force(title: str, start: str, end: str, description: str = "") -> str:
    """중복 확인 없이 구글 캘린더에 일정을 강제 추가합니다.

    Args:
        title: 일정 제목
        start: 시작 시간 (YYYY-MM-DDTHH:MM)
        end: 종료 시간 (YYYY-MM-DDTHH:MM)
        description: 메모 (선택)
    """
    try:
        service = _get_calendar_service()
        event = {
            "summary": title,
            "description": description,
            "start": {"dateTime": _normalize_dt(start), "timeZone": "Asia/Seoul"},
            "end":   {"dateTime": _normalize_dt(end),   "timeZone": "Asia/Seoul"},
        }
        created = service.events().insert(calendarId="primary", body=event).execute()
        return f"✅ 일정 강제 추가 완료: [{start}] {title}  (id: {created['id']})"
    except Exception as e:
        return f"Calendar Error: {e}"


@mcp.tool()
def calendar_update(event_id: str, title: str = "", start: str = "",
                    end: str = "", description: str = "") -> str:
    """기존 구글 캘린더 일정을 수정합니다. 변경할 항목만 입력하면 됩니다.

    Args:
        event_id: 일정 ID (calendar_list로 확인)
        title: 새 제목 (선택)
        start: 새 시작 시간 (선택, YYYY-MM-DDTHH:MM)
        end: 새 종료 시간 (선택)
        description: 새 메모 (선택)
    """
    try:
        service = _get_calendar_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        if title:       event["summary"]     = title
        if description: event["description"] = description
        if start:       event["start"] = {"dateTime": _normalize_dt(start), "timeZone": "Asia/Seoul"}
        if end:         event["end"]   = {"dateTime": _normalize_dt(end),   "timeZone": "Asia/Seoul"}
        updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return f"✅ 일정 수정 완료: {updated.get('summary')} (id: {event_id})"
    except Exception as e:
        return f"Calendar Error: {e}"


@mcp.tool()
def calendar_delete(event_id: str) -> str:
    """구글 캘린더 일정을 삭제합니다.

    Args:
        event_id: 일정 ID (calendar_list로 확인)
    """
    try:
        service = _get_calendar_service()
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"✅ 일정 삭제 완료 (id: {event_id})"
    except Exception as e:
        return f"Calendar Error: {e}"


# ── 시스템 상태 ───────────────────────────────────────────────────────────────
@mcp.tool()
def check_errors() -> str:
    """온유_오류.md에서 최근 오류를 읽어 원인과 조치를 제안합니다."""
    if not os.path.exists(ERROR_LOG_FILE):
        return "✅ 기록된 오류 없음."
    try:
        content = Path(ERROR_LOG_FILE).read_text(encoding="utf-8").strip()
        if not content:
            return "✅ 기록된 오류 없음."
        entries = content.split("\n## ")
        recent = "\n## ".join(entries[-10:])
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return f"[오류 로그 원문 (Gemini 키 없음)]\n\n{recent}"
        try:
            from google import genai
            from google.genai import types
            client = genai.Client(api_key=api_key)
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    f"다음은 온유 시스템 오류 로그다. 각 오류 원인을 짧게 분석하고 "
                    f"조치 방법을 제안하라. 한국어로, 항목별 간결하게.\n\n{recent}"
                ),
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                ),
            )
            return f"🔍 [오류 분석 리포트]\n\n{res.text}"
        except Exception as e:
            return f"[오류 로그] (Gemini 분석 실패: {e})\n\n{recent}"
    except Exception as e:
        return f"Error: {e}"


@mcp.tool()
def report_status() -> str:
    """오늘의 API 사용량, 클리핑 설정, 시크릿 모드 상태를 보고합니다."""
    _, today, search_count = _get_search_count()
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        except:
            pass
    chat_count  = data.get(f"chat_{today}", 0)
    rag_count   = data.get(f"rag_{today}",  0)
    sum_count   = data.get(f"summary_{today}", 0)
    cfg = _load_clip_config()
    clip_on = "ON" if cfg.get("enabled", True) else "OFF"
    wifi_sec = _get_wifi_security()
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass
    manual = config.get("manual_override")
    if manual is not None:
        secret_mode = "ON (수동)" if manual else "OFF (수동)"
    elif wifi_sec == "open":
        secret_mode = "ON (WiFi 자동)"
    else:
        secret_mode = "OFF (WiFi 자동)"
    return (
        f"📊 [온유 오늘 현황 — {today}]\n"
        f"  대화(chat):    {chat_count}회\n"
        f"  RAG 검색:      {rag_count}회\n"
        f"  자동 요약:     {sum_count}회\n"
        f"  웹 검색:       {search_count}회\n"
        f"─────────────────────────────\n"
        f"  자동클리핑:    {clip_on} ({len(cfg.get('topics', []))}개 주제)\n"
        f"  시크릿 모드:   {secret_mode}\n"
        f"  WiFi 보안:     {wifi_sec}"
    )


# ── 시크릿 모드 ───────────────────────────────────────────────────────────────
@mcp.tool()
def get_secret_mode() -> str:
    """현재 시크릿 모드 상태를 확인합니다. (WiFi 자동감지 or 수동 오버라이드)"""
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass
    manual = config.get("manual_override")
    wifi_sec = _get_wifi_security()
    if manual is not None:
        mode = "ON (시크릿)" if manual else "OFF (일반)"
        return (
            f"🔒 시크릿 모드: {mode}\n"
            f"- 설정 방식: 수동 오버라이드\n"
            f"- WiFi 보안: {wifi_sec}\n"
            f"- 해제: set_secret_mode 호출 시 WiFi 자동감지로 복귀 가능"
        )
    else:
        if wifi_sec == "open":
            mode = "ON (시크릿) - 개방형 WiFi 감지"
        elif wifi_sec == "secured":
            mode = "OFF (일반) - 보안 WiFi 감지"
        else:
            mode = "OFF (일반) - WiFi 미감지, 기본값"
        return (
            f"🔍 시크릿 모드: {mode}\n"
            f"- 설정 방식: WiFi 자동감지\n"
            f"- 현재 WiFi 보안: {wifi_sec}"
        )


@mcp.tool()
def set_secret_mode(on: bool) -> str:
    """시크릿 모드를 수동으로 켜거나 끕니다.

    Args:
        on: True=시크릿 ON / False=시크릿 OFF
    """
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except:
            pass
    config["manual_override"] = on
    _atomic_write(LOCATION_CONFIG_FILE, config)
    mode = "ON" if on else "OFF"
    return f"✅ 시크릿 모드 {mode} 완료 (수동 오버라이드 저장됨)."


# ── 자동 클리핑 ───────────────────────────────────────────────────────────────
@mcp.tool()
def clip_status() -> str:
    """자동 클리핑 현황과 설정을 보여줍니다."""
    cfg = _load_clip_config()
    enabled = "ON" if cfg.get("enabled", True) else "OFF"
    topics = cfg.get("topics", [])
    weekly = cfg.get("weekly_topics", [])
    lines = [
        f"📋 자동클리핑: {enabled}",
        f"  딜레이: {cfg.get('delay_seconds', 30)}초",
        f"  하루 최대: {cfg.get('max_clips', 10)}개",
        f"  주제 수: {len(topics)}개",
    ]
    if weekly:
        lines.append(f"  주간 추적: {', '.join(weekly[:3])}{'...' if len(weekly)>3 else ''}")
    return "\n".join(lines)


@mcp.tool()
def get_clip_topics() -> str:
    """현재 클리핑 주제 목록을 번호와 함께 반환합니다. 주제 추가/삭제 전 반드시 호출하세요."""
    cfg = _load_clip_config()
    topics = cfg.get("topics", [])
    if not topics:
        return "현재 등록된 클리핑 주제가 없습니다."
    lines = [f"{i+1}. {t}" for i, t in enumerate(topics)]
    return f"📋 클리핑 주제 목록 ({len(topics)}개):\n" + "\n".join(lines)


@mcp.tool()
def set_clip_config(topics: List[str] = None, delay_seconds: int = None,
                    max_clips: int = None, enabled: bool = None) -> str:
    """자동 클리핑 설정을 변경합니다.

    Args:
        topics: 새 주제 리스트 (예: ["AI 뉴스", "Python 팁"])
        delay_seconds: 클리핑 간격 (초)
        max_clips: 하루 최대 클리핑 수
        enabled: True=ON / False=OFF
    """
    cfg = _load_clip_config()
    if topics        is not None: cfg["topics"]         = topics
    if delay_seconds is not None: cfg["delay_seconds"]  = delay_seconds
    if max_clips     is not None: cfg["max_clips"]      = max_clips
    if enabled       is not None: cfg["enabled"]        = enabled
    _save_clip_config(cfg)
    msgs = []
    if topics        is not None: msgs.append(f"주제 {len(topics)}개 업데이트")
    if delay_seconds is not None: msgs.append(f"딜레이 {delay_seconds}초")
    if max_clips     is not None: msgs.append(f"최대 {max_clips}개")
    if enabled       is not None: msgs.append(f"자동클리핑 {'ON' if enabled else 'OFF'}")
    return "✅ 클리핑 설정 변경: " + ", ".join(msgs)


@mcp.tool()
def set_weekly_clip(topics: List[str], action: str = "add") -> str:
    """특정 주제를 주간(7일) 클리핑 추적 목록에 추가/제거합니다.

    Args:
        topics: 주제 리스트
        action: 'add'(추가) 또는 'remove'(제거)
    """
    cfg = _load_clip_config()
    weekly = cfg.get("weekly_topics", [])
    if action == "add":
        added = [t for t in topics if t not in weekly]
        weekly.extend(added)
        all_topics = cfg.get("topics", [])
        for t in added:
            if t not in all_topics:
                all_topics.append(t)
        cfg["topics"] = all_topics
        msg = f"✅ 주간 추적 {len(added)}개 추가: {', '.join(added)}"
    else:
        removed = [t for t in topics if t in weekly]
        weekly = [t for t in weekly if t not in topics]
        msg = f"✅ 주간 추적 {len(removed)}개 제거: {', '.join(removed)}"
    cfg["weekly_topics"] = weekly
    _save_clip_config(cfg)
    return msg + f"\n현재 주간 추적 주제: {len(weekly)}개"


# ── 태스크 관리 ───────────────────────────────────────────────────────────────
def _get_tm():
    try:
        import onew_task_manager as tm
        return tm
    except ImportError:
        return None


@mcp.tool()
def task_create(title: str, steps: List[str], priority: str = "보통") -> str:
    """새 멀티스텝 태스크를 생성합니다.

    Args:
        title: 태스크 제목
        steps: 순서대로 실행할 단계 목록 (예: ["파일 읽기", "내용 수정", "검증"])
        priority: '높음' / '보통' / '낮음'
    """
    tm = _get_tm()
    if tm:
        return tm.task_create(title, steps, priority)
    return "Error: onew_task_manager 모듈을 찾을 수 없습니다."


@mcp.tool()
def task_list(status_filter: str = "") -> str:
    """현재 태스크 목록을 반환합니다.

    Args:
        status_filter: '' (전체) / '대기' / '진행중' / '완료' / '실패'
    """
    tm = _get_tm()
    if tm:
        return tm.task_list(status_filter)
    return "Error: onew_task_manager 모듈을 찾을 수 없습니다."


@mcp.tool()
def task_update(task_id: str, step_index: int, status: str, note: str = "") -> str:
    """태스크의 특정 단계 상태를 업데이트합니다.

    Args:
        task_id: 태스크 ID (예: 'T001')
        step_index: 단계 번호 (1부터 시작)
        status: '진행중' / '완료' / '실패'
        note: 메모 (선택)
    """
    tm = _get_tm()
    if tm:
        return tm.task_update(task_id, step_index, status, note)
    return "Error: onew_task_manager 모듈을 찾을 수 없습니다."


@mcp.tool()
def task_next(task_id: str = "") -> str:
    """다음 실행할 단계를 반환합니다. task_id 생략 시 우선순위 높은 태스크 자동 선택.

    Args:
        task_id: 태스크 ID (선택, 생략 시 자동 선택)
    """
    tm = _get_tm()
    if tm:
        return tm.task_next(task_id)
    return "Error: onew_task_manager 모듈을 찾을 수 없습니다."


@mcp.tool()
def task_cancel(task_id: str) -> str:
    """태스크를 취소합니다.

    Args:
        task_id: 취소할 태스크 ID (예: 'T001')
    """
    tm = _get_tm()
    if tm:
        return tm.task_cancel(task_id)
    return "Error: onew_task_manager 모듈을 찾을 수 없습니다."


# ── 작업 기억 ─────────────────────────────────────────────────────────────────
@mcp.tool()
def create_working_memory(task_name: str) -> str:
    """복잡한 작업 시작 전 Plan.md, Context.md, Checklist.md 3개 파일을 생성합니다.
    수정/생성 파일 3개 이상 또는 4단계 이상 작업에 반드시 사용하세요.

    Args:
        task_name: 작업 이름 (예: "obsidian_agent 리팩토링")
    """
    os.makedirs(WORKING_MEMORY_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    today = datetime.now().strftime("%Y-%m-%d")
    safe_name = task_name.replace("/", "_").replace("\\", "_")[:40]

    plan_content = f"""---
tags: [작업기억, 계획서]
날짜: {today}
author: Onew
---
# 작업 계획서: {task_name} ({now})

## 목표
(이 작업을 통해 달성할 최종 결과물)

## 단계별 계획
1. [ ] 단계1 — 대상 파일, 예상 변경 내용
2. [ ] 단계2 —
3. [ ] 단계3 —

## 롤백 방법
- rollback_file() 또는 code_backup에서 복원

## 예상 위험
-
"""

    context_content = f"""---
tags: [작업기억, 맥락노트]
날짜: {today}
author: Onew
---
# 맥락 노트: {task_name}

## 작업 배경 및 의도
(사용자가 이 작업을 지시한 이유)

## 주요 의사결정 내역
- [{now}] 작업 시작

## 참고 파일
-

## 제약 사항
- 절대 해서는 안 될 것:
- 과거 실수:
"""

    checklist_content = f"""---
tags: [작업기억, 체크리스트]
날짜: {today}
author: Onew
---
# 체크리스트: {task_name}

## 전체 진행 상태
- **현재 진행률:** 0%
- **현재 단계:** 시작 전

## 세부 체크리스트
### Phase 1
- [ ]

### Phase 2
- [ ]

### QA
- [ ] 지시한 포맷을 지켰는가?
- [ ] 오답 노트의 실수를 반복하지 않았는가?
- [ ] 사용자 승인을 받았는가?

## 이슈 사항
-
"""

    results = []
    for fname, content in [
        (f"{safe_name}_Plan.md",      plan_content),
        (f"{safe_name}_Context.md",   context_content),
        (f"{safe_name}_Checklist.md", checklist_content),
    ]:
        fpath = os.path.join(WORKING_MEMORY_DIR, fname)
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            results.append(f"✅ {fname}")
        except Exception as e:
            results.append(f"❌ {fname}: {e}")

    return "📋 작업 기억 파일 생성 완료:\n" + "\n".join(results) + "\n경로: SYSTEM/working_memory/"


# ── 진입점 ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
