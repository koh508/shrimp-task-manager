import os
import glob
import json
import re
import math
import time
import sys
import shutil
import threading
import numpy as np
import subprocess
import urllib.request
import warnings
warnings.filterwarnings("ignore", message=".*non-text parts.*")
warnings.filterwarnings("ignore", message=".*function_call.*")

# ==============================================================================
# [파일 충돌 방지] — onew_locks.py로 분리됨 (WinError 5 재시도 포함)
# ==============================================================================
from onew_locks import _get_file_lock, _atomic_json_write, _atomic_md_append

from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional
from google import genai
from google.genai import types

# ==============================================================================
# [설정 영역]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
_PID_FILE    = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew.pid")

def _check_single_instance():
    """중복 실행 방지 — 이미 실행 중인 프로세스가 있으면 경고 후 종료."""
    if os.path.exists(_PID_FILE):
        try:
            with open(_PID_FILE) as _f:
                _old_pid = int(_f.read().strip())
            import psutil as _ps
            if _ps.pid_exists(_old_pid):
                proc = _ps.Process(_old_pid)
                if 'python' in proc.name().lower():
                    print(f"⚠️ [중복 실행 방지] 온유가 이미 실행 중입니다 (PID {_old_pid}).")
                    print("   종료하려면 기존 창에서 '끄기' 입력 또는 Ctrl+C 를 누르세요.")
                    sys.exit(1)
        except (ValueError, ImportError, Exception):
            pass  # psutil 없거나 PID 파싱 실패 → 그냥 진행
    try:
        with open(_PID_FILE, 'w') as _f:
            _f.write(str(os.getpid()))
        import atexit
        atexit.register(lambda: os.path.exists(_PID_FILE) and os.remove(_PID_FILE))
    except Exception:
        pass

DB_FILE      = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_pure_db.json")  # 마이그레이션 참조용
LANCE_DB_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", ".onew_lance_db")
EMBED_DIM    = 3072  # gemini-embedding-001 실제 출력 차원
SYSTEM_PROMPT_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_system_prompt.md")
ANTIPATTERNS_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_antipatterns.md")
SKILLS_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "skills")
WORKING_MEMORY_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "working_memory")
USAGE_LOG_FILE   = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "api_usage_log.json")
HASH_CACHE_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_content_hashes.json")

# ==============================================================================
# [테두리 설정 - 여기만 수정하면 됩니다]
# ==============================================================================

# ── 학습 테두리 ──────────────────────────────────────────────────────────────
# 이 이름이 경로에 포함된 폴더는 임베딩 학습에서 제외
SYNC_EXCLUDE_DIRS  = ["대화기록", "venv", ".obsidian", ".git",
                       "code_backup", ".db_backup", "__pycache__", "Onew_Core_Backup"]

# 이 이름이 포함된 파일은 학습 제외
SYNC_EXCLUDE_FILES = ["onew_pure_db", "api_usage_log", "onew_content_hashes"]

MAX_FILE_SIZE_KB   = 200        # 이 크기(KB) 초과 파일은 학습 스킵
MAX_CHUNKS_PER_FILE = 150       # 파일 당 청크 최대 수 (초과 시 스킵)
MAX_DAILY_EMBED_CALLS = 10000   # 하루 임베딩 API 호출 한도
MAX_DAILY_CHAT_WARN  = 500     # 하루 chat API 경고 기준 (초과 시 텔레그램 알림)
AUTO_SYNC_HOURS    = 12         # 자동 학습 주기 (시간 단위)
CHUNK_VERSION      = "v3"       # 청크 전략 버전 (바뀌면 전체 재학습)

# ── 자율학습 설정 ─────────────────────────────────────────────────────────────
CORRECTION_KEYWORDS = ["틀렸어", "아니야", "아니잖아", "다시 해줘", "잘못됐어",
                        "틀린 것 같아", "그게 아니라", "잘못 알고 있어", "오답이야"]
MISTAKE_LOG_FILE    = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "오답_패턴.md")
# 온유 성장 기록 폴더 (야간학습 학습 대상)
GROWTH_DIR          = os.path.join(OBSIDIAN_VAULT_PATH, "온유_성장기록")
FAILURE_DIR         = os.path.join(GROWTH_DIR, "실패사례")
CODE_LESSON_DIR     = os.path.join(GROWTH_DIR, "코드교훈")
SELF_EVAL_MIN_LEN   = 20        # 자기 평가 최소 질문 길이 (이하 스킵)
SELF_EVAL_MIN_SCORE = 3         # 이 점수 미만 시 보완 검색 실행
IMPORTANCE_RECALC_DAYS = 7      # 중요도 재계산 주기 (일)
HIT_WINDOW_DAYS     = 30        # 중요도 반영 최근 히트 기간 (일)

# ── 웹 검색 테두리 ───────────────────────────────────────────────────────────
MAX_DAILY_SEARCHES = 30         # 하루 웹 검색 최대 횟수
EXAM_DATE          = datetime(2026, 4, 26)  # 공조냉동 실기 시험일
# 허용 주제 키워드 (비어있으면 무제한)
SEARCH_ALLOW_TOPICS = []  # 비어있으면 무제한 (일일 30회 한도만 적용)

# ── 핵심 시스템 파일 보호 목록 (온유 직접 수정 불가) ────────────────────────
PROTECTED_FILES = {
    'obsidian_agent.py',   # 온유 메인 에이전트
    'onew_shared.py',      # 공유 상태 모듈
    'onew_tools.py',       # 도구 정의
    'onew_scheduler.py',   # 스케줄러
    'onew_telegram_bot.py', # 텔레그램 봇
}
CODE_REVIEW_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "코드리뷰")

# ── 읽기전용(보호) 폴더 목록 ─────────────────────────────────────────────────
# 이 폴더 내 파일은 온유가 write/edit/delete/move 할 수 없음
PROTECTED_FOLDERS = {
    'OCU',           # OCU 강의자료 — 원본 보존
    '03_OCU',        # OCU 강의자료 (구 폴더명)
    '04_Reference',  # 참고자료 — 원본 보존
}

# ── 자동 클리핑 설정 ──────────────────────────────────────────────────────────
CLIP_CONFIG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "clip_config.json")
CLIP_INDEX_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "클리핑_인덱스.json")
CLIP_FOLDER      = os.path.join(OBSIDIAN_VAULT_PATH, "클리핑")
MAX_CLIP_FILE_KB = 200   # 클리핑 파일 최대 크기
CLIP_DEDUP_DAYS  = 1     # 동일 주제 재클리핑 방지 기간 (일)
CLIP_DEFAULTS = {
    "topics": [
        # ── AI 도구 / 개발 (5개) ── 공신력 있는 소스 우선
        "Anthropic Claude 최신 연구 및 업데이트 anthropic.com",
        "Google DeepMind Gemini 연구 동향 deepmind.google",
        "Hugging Face 오픈소스 AI 모델 신규 출시 huggingface.co",
        "LLM 에이전트 MCP 프로토콜 개발 최신 기법",
        "AI 개발자 도구 실전 활용 사례 2026",
        # ── AI 윤리 / 안전성 (5개) ── Anthropic 방향성
        "Anthropic Constitutional AI 정렬 연구 AI safety",
        "Responsible Scaling Policy AI 안전성 거버넌스",
        "AI 해석가능성 Interpretability 연구 mechanistic",
        "AI 윤리 정책 규범 국제 거버넌스 2026",
        "AI 복지 의식 연구 AI welfare consciousness",
    ],
    "delay_seconds": 30,
    "max_clips": 10,
    "enabled": True
}

# Gemini API 키 (환경변수에서 로드)
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ 오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    print("💡 PowerShell에서 다음 명령어를 실행하세요:")
    print('   [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_api_key", "User")')
    sys.exit(1)
client = genai.Client(api_key=API_KEY)

# ==============================================================================
# [위치 감지 모듈 - 집/회사 모드]
# ==============================================================================
LOCATION_CONFIG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_location.json")

# 회사 모드에서 차단할 민감 주제 키워드
SENSITIVE_KEYWORDS = [
    "양악", "수술", "산재", "요양", "우울", "힘들어", "외로워", "불안",
    "상처", "아파", "속상", "고민", "스트레스", "감정", "마음이", "외롭",
    "죽고", "포기", "무기력", "치료", "병원", "정신", "심리",
]

# 시간 관련 질문 키워드 — 감지 시 RAG 결과를 최신순으로 가중치 부여
TIME_QUERY_KEYWORDS = [
    "어제", "오늘", "최근", "요즘", "이번 주", "지난주", "이번달", "지난달",
    "방금", "아까", "최신", "며칠 전", "얼마 전", "요 며칠",
    "뭐 했", "뭐했", "무엇을 했", "어떻게 했", "했었나", "했었어", "했지",
    "뭐 하고", "뭐하고", "어떻게 지냈", "어떻게 보냈",
]

# 모호한 지시어 — 감지 시 이전 대화로 RAG 쿼리 보강
VAGUE_REFS = [
    "그거", "그것", "그게", "그걸", "그거랑", "그거를",
    "아까", "저번에", "그때", "이전에", "방금",
    "그 방법", "그 파일", "그 코드", "그 문제", "그 내용",
    "거기", "거기서", "그 사람", "그분", "그 설비", "그 장치",
    "이거", "이것", "저거", "저것",
]

# 엔티티 워킹메모리 파일
ENTITY_MEMORY_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_entities.json")

def _get_public_ip() -> str:
    """현재 공인 IP를 반환. 실패 시 빈 문자열."""
    try:
        with urllib.request.urlopen("https://api.ipify.org", timeout=5) as r:
            return r.read().decode().strip()
    except:
        return ""

_wifi_security_cache: dict = {}  # {"result": str, "time": float}

def _get_wifi_security() -> str:
    """현재 연결된 WiFi 보안 방식을 반환. 'open'(비밀번호없음), 'secured'(비밀번호있음), 'unknown' 중 하나.
    PowerShell + UTF-8 강제 출력으로 한글 Windows 인코딩 문제 우회.
    결과를 60초간 캐시하여 중복 호출 방지.
    """
    if _wifi_security_cache and time.time() - _wifi_security_cache.get("time", 0) < 60:
        return _wifi_security_cache["result"]
    try:
        _PS = ["powershell", "-NoProfile", "-Command"]

        # 1. 현재 연결된 SSID 가져오기
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

        # 2. 해당 프로필의 인증 방식 확인 (영문 출력 강제)
        r2 = subprocess.run(
            _PS + [f"[Console]::OutputEncoding=[System.Text.Encoding]::UTF8; netsh wlan show profiles name='{ssid}' key=clear"],
            capture_output=True, timeout=7
        )
        output2 = r2.stdout.decode("utf-8", errors="ignore")
        result = "unknown"
        for line in output2.splitlines():
            # 영문 Windows: "Authentication", 한글 Windows: "인증"
            if "Authentication" in line or "인증" in line:
                auth = line.split(":", 1)[-1].strip().lower()
                # 영문: "open", "none" / 한글: "없음"(none), "개방"(open)
                open_values = ("open", "none", "없음", "개방")
                result = "open" if any(auth == v or auth.startswith(v) for v in open_values) else "secured"
                break
        _wifi_security_cache.update({"result": result, "ssid": ssid, "time": time.time()})
        return result
    except:
        _wifi_security_cache.update({"result": "unknown", "time": time.time()})
        return "unknown"

def detect_location_mode() -> str:
    """WiFi 보안 방식 기반으로 시크릿 모드 결정.
    - 개방형 WiFi(비밀번호 없음) → 'work' (시크릿 ON)
    - 보안 WiFi(비밀번호 있음)  → 'home' (시크릿 OFF)
    - 수동 오버라이드 설정 있으면 그걸 우선 적용.
    """
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass

    # 수동 오버라이드 우선 적용
    if config.get("manual_override") is not None:
        return "work" if config["manual_override"] else "home"

    # WiFi 보안 방식 자동 감지
    wifi_sec = _get_wifi_security()
    ssid = _wifi_security_cache.get("ssid", "")

    # 신뢰 SSID 목록: 개방형으로 감지되더라도 집으로 처리
    trusted_ssids = config.get("trusted_ssids", [])
    if ssid and ssid in trusted_ssids:
        return "home"   # 신뢰 네트워크 → 시크릿 OFF

    if wifi_sec == "open":
        return "work"   # 개방형 → 시크릿 ON
    elif wifi_sec == "secured":
        return "home"   # 보안됨 → 시크릿 OFF

    # 폴백: 공인 IP 기반 (onew_location.json의 work_ips 목록)
    work_ips = config.get("work_ips", [])
    if work_ips:
        current_ip = _get_public_ip()
        if current_ip and current_ip in work_ips:
            return "work"
    return "home"

# ==============================================================================
# [1. 스마트 기억 모듈 (마크다운 전용 순정 코어)]
# ==============================================================================
def cosine_similarity(v1, v2):
    dot_product = sum(a * b for a, b in zip(v1, v2))
    mag1 = math.sqrt(sum(a * a for a in v1))
    mag2 = math.sqrt(sum(b * b for b in v2))
    return dot_product / (mag1 * mag2) if mag1 * mag2 != 0 else 0.0

# ==============================================================================
# [자율학습 모듈]
# ==============================================================================
def _save_mistake(question: str, wrong_answer: str, correction: str):
    """오답을 두 곳에 저장.
    1. 기존 SYSTEM/오답_패턴.md (하위 호환 유지)
    2. 온유_성장기록/실패사례/YYYY-MM_실패사례.md (야간학습 대상)
    """
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        today     = datetime.now().strftime("%Y-%m-%d")

        # 실패 유형 자동 분류
        combined = question + " " + correction
        if any(k in combined for k in ["코드", "파일", "write_file", "edit_file", "오류", "버그", "실패"]):
            fail_type = "코드/파일 작업 실패"
        elif any(k in combined for k in ["시크릿", "위치", "모드", "설정"]):
            fail_type = "설정/모드 오인식"
        elif any(k in combined for k in ["기억", "기억못", "잊", "언급"]):
            fail_type = "문맥/기억 오류"
        else:
            fail_type = "응답 오류"

        entry = (f"\n## [{timestamp}] {fail_type}\n"
                 f"**질문:** {question[:200]}\n"
                 f"**온유 오답:** {wrong_answer[:300]}\n"
                 f"**교정:** {correction[:200]}\n"
                 f"**교훈:** 이 유형의 실수를 반복하지 않으려면 → {fail_type} 패턴 주의\n\n---")

        # 1. 기존 평탄 파일 유지
        _atomic_md_append(MISTAKE_LOG_FILE, entry)

        # 2. 성장기록 폴더 (월별 파일)
        os.makedirs(FAILURE_DIR, exist_ok=True)
        month_file = os.path.join(FAILURE_DIR, f"{today[:7]}_실패사례.md")
        if not os.path.exists(month_file):
            header = (f"---\ntags: [온유성장, 실패사례, {today[:7]}]\n"
                      f"날짜: {today}\nauthor: Onew\n---\n\n"
                      f"# 온유 실패 사례 — {today[:7]}\n"
                      f"> 이 파일은 온유가 틀린 답변·실수 패턴을 자동 기록합니다.\n"
                      f"> 야간학습 시 반복 학습하여 동일 실수 방지에 활용됩니다.\n")
            with open(month_file, 'w', encoding='utf-8') as f:
                f.write(header)
        _atomic_md_append(month_file, entry)
    except: pass


def _save_code_lesson(func_name: str, error: str, context: str = ""):
    """에러 반복 감지 시 코드 교훈으로 저장 (야간학습 대상)."""
    try:
        today = datetime.now().strftime("%Y-%m-%d")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        os.makedirs(CODE_LESSON_DIR, exist_ok=True)
        month_file = os.path.join(CODE_LESSON_DIR, f"{today[:7]}_코드교훈.md")
        if not os.path.exists(month_file):
            header = (f"---\ntags: [온유성장, 코드교훈, {today[:7]}]\n"
                      f"날짜: {today}\nauthor: Onew\n---\n\n"
                      f"# 온유 코드 교훈 — {today[:7]}\n"
                      f"> tool_loop 에러 반복·코드 수정 실패 패턴 자동 기록.\n")
            with open(month_file, 'w', encoding='utf-8') as f:
                f.write(header)
        entry = (f"\n## [{timestamp}] {func_name} 반복 실패\n"
                 f"**에러:** {error[:200]}\n"
                 f"**맥락:** {context[:200]}\n"
                 f"**교훈:** `{func_name}` 호출 시 이 오류 패턴을 사전 확인하라.\n\n---")
        _atomic_md_append(month_file, entry)
    except: pass


def _self_evaluate(query: str, answer: str) -> int:
    """답변 자기 채점. 1~5점 반환. 단순 질문은 5점(스킵)으로 반환."""
    if len(query) < SELF_EVAL_MIN_LEN:
        return 5
    simple_triggers = ["안녕", "고마워", "고맙", "맞아", "응", "좋아", "ㅇㅇ", "알겠어", "오케이"]
    if any(t in query for t in simple_triggers):
        return 5
    try:
        eval_prompt = (f"다음 질문과 답변을 보고, 답변이 질문에 얼마나 충분했는지 1~5점으로만 출력하라. "
                       f"숫자 하나만 출력. 설명 없음.\n"
                       f"질문: {query}\n답변: {answer[:500]}")
        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=eval_prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)))
        score_str = res.text.strip()
        return int(score_str[0]) if score_str and score_str[0].isdigit() else 5
    except:
        return 5


def _semantic_chunks(content: str, max_chunk: int = 2000) -> list[str]:
    """마크다운 헤더(#) 단위로 의미 있게 분할. 섹션이 너무 길면 재분할."""
    # YAML 프론트매터 제거
    body = re.sub(r'^---[\s\S]*?---\n?', '', content.strip())

    # 헤더 기준 분할 (# ## ### 모두)
    sections = re.split(r'(?=\n#{1,3} )', body)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= max_chunk:
            chunks.append(sec)
        else:
            # 긴 섹션은 문단(빈 줄) 단위로 재분할
            paras = [p.strip() for p in re.split(r'\n{2,}', sec) if p.strip()]
            buf = ""
            for p in paras:
                if len(buf) + len(p) + 1 <= max_chunk:
                    buf = (buf + "\n\n" + p).strip()
                else:
                    if buf:
                        chunks.append(buf)
                    # 문단 자체가 max_chunk 초과면 고정 크기로 자름
                    if len(p) > max_chunk:
                        for i in range(0, len(p), max_chunk):
                            chunks.append(p[i:i+max_chunk])
                    else:
                        buf = p
            if buf:
                chunks.append(buf)

    # 빈 청크 제거
    return [c for c in chunks if len(c.strip()) > 20]


def _compress_content(content: str, filename: str) -> str:
    """대용량 파일을 섹션별로 나눠 Gemini로 압축 요약한다."""
    try:
        # 3000자 단위로 섹션 분할 후 각각 요약
        sections = [content[i:i+3000] for i in range(0, len(content), 3000)]
        summaries = []
        for i, sec in enumerate(sections[:10]):  # 최대 10섹션
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    f"다음 마크다운 내용을 핵심만 남겨 500자 이내로 압축하라. "
                    f"파일명: {filename}\n\n{sec}"
                ),
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0))
            )
            summaries.append(res.text.strip())
            time.sleep(0.3)
        return f"[압축 요약 - {filename}]\n\n" + "\n\n".join(summaries)
    except Exception as e:
        return ""

def _score_importance(content: str, filename: str) -> str:
    """노트 중요도를 HIGH / MEDIUM / LOW 로 자동 판별."""
    score = 0
    # 시험/공부 관련 키워드
    study_kw = ["공조냉동", "냉매", "압축기", "응축기", "증발기", "성적계수", "COP",
                "소방", "방재", "OCU", "시험", "오답", "공식", "계산"]
    # 일정/중요 이벤트 키워드
    event_kw = ["산재", "양악", "병원", "면담", "복직", "마감", "제출", "D-"]
    # 일기 (날짜 파일명)
    import re as _re
    if _re.match(r'\d{4}-\d{2}-\d{2}', filename):
        score += 1
    for kw in study_kw:
        if kw in content:
            score += 1
    for kw in event_kw:
        if kw in content:
            score += 2
    # 링크/태그 많을수록 중요
    link_count = len(_re.findall(r'\[\[.*?\]\]', content))
    score += min(link_count // 3, 3)

    if score >= 5:   return "HIGH"
    elif score >= 2: return "MEDIUM"
    else:            return "LOW"


# ==============================================================================
# LanceDB 하위호환 래퍼 — onew.mem.db.get("__meta__", {}).get(key) 패턴 지원
# ==============================================================================
class _MetaCompat:
    def __init__(self, meta_dict, mem_obj):
        self._meta = meta_dict
        self._mem  = mem_obj

    def get(self, key, default=None):
        if key == "__meta__":
            return self._meta
        return default

    def setdefault(self, key, default=None):
        if key == "__meta__":
            return self._meta
        return default if default is not None else {}

    def __len__(self):
        try:
            self._mem._ensure_loaded()
            rows = self._mem._table.search().select(["path"]).limit(10_000_000).to_list()
            return len(set(r["path"] for r in rows))
        except:
            return 0

    def __contains__(self, key):
        return key == "__meta__"


class OnewPureMemory:
    def __init__(self):
        self._lance_db  = None
        self._table     = None
        self._db_loaded = False
        self._load_lock  = threading.Lock()
        self._hit_counts    = {}   # {파일경로: ["2026-03-14", ...]} 인메모리 히트 로그
        self._meta          = {}   # {chunk_version, last_sync, last_importance_recalc}
        self._fts_available = False  # tantivy FTS 인덱스 사용 가능 여부

    # ── 하위호환 프로퍼티 ──────────────────────────────────────────────────────
    @property
    def db(self):
        """외부 코드 하위호환: onew.mem.db.get('__meta__', {}).get(key) 패턴 지원"""
        return _MetaCompat(self._meta, self)

    # ── 내부 초기화 ───────────────────────────────────────────────────────────
    def _init_tables(self):
        import pyarrow as pa
        schema = pa.schema([
            pa.field("path",         pa.string()),
            pa.field("chunk_idx",    pa.int32()),
            pa.field("text",         pa.string()),
            pa.field("vector",       pa.list_(pa.float32(), EMBED_DIM)),
            pa.field("mtime",        pa.float64()),
            pa.field("links",        pa.string()),   # JSON list
            pa.field("tags",         pa.string()),   # JSON list
            pa.field("importance",   pa.string()),
            pa.field("user_written", pa.bool_()),
            pa.field("hit_log",      pa.string()),   # JSON list of date strings
        ])
        self._table = self._lance_db.create_table("chunks", schema=schema, mode="overwrite")
        meta_schema = pa.schema([pa.field("key", pa.string()), pa.field("value", pa.string())])
        self._lance_db.create_table("meta", schema=meta_schema, mode="overwrite")

    def _load_db(self):
        import lancedb
        os.makedirs(LANCE_DB_DIR, exist_ok=True)
        try:
            self._lance_db = lancedb.connect(LANCE_DB_DIR)
            if "chunks" in (self._lance_db.table_names() if hasattr(self._lance_db, "table_names") else [str(t) for t in self._lance_db.list_tables()]):
                self._table = self._lance_db.open_table("chunks")
            else:
                self._init_tables()
            # 메타 로드
            if "meta" in (self._lance_db.table_names() if hasattr(self._lance_db, "table_names") else [str(t) for t in self._lance_db.list_tables()]):
                for row in self._lance_db.open_table("meta").to_arrow().to_pylist():
                    self._meta[row["key"]] = row["value"]
            # JSON → LanceDB 최초 마이그레이션
            if self._table.count_rows() == 0 and os.path.exists(DB_FILE):
                self._migrate_from_json()
            # FTS 인덱스 초기화 (tantivy 미설치 시 비활성)
            try:
                self._table.create_fts_index("text", replace=False)
                self._fts_available = True
            except Exception as _fts_e:
                _s = str(_fts_e).lower()
                if any(k in _s for k in ("already", "exists", "index")):
                    self._fts_available = True
            self._db_loaded = True
        except Exception as e:
            print(f"❌ LanceDB 로드 오류: {e}")
            self._db_loaded = True   # 재시도 방지

    def _migrate_from_json(self):
        """기존 onew_pure_db.json → LanceDB 1회 마이그레이션"""
        print("🔄 [마이그레이션] JSON → LanceDB 변환 중...")
        try:
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                old_db = json.load(f)
        except Exception as e:
            print(f"❌ 마이그레이션 실패: {e}"); return

        rows = []
        for path, data in old_db.items():
            if path == "__meta__":
                self._meta.update(data); continue
            hit_json = json.dumps(data.get("hit_log", []), ensure_ascii=False)
            for i, chunk in enumerate(data.get("chunks", [])):
                if "embedding" not in chunk: continue
                emb = chunk["embedding"]
                vec = emb.astype(np.float32).tolist() if isinstance(emb, np.ndarray) else [float(x) for x in emb]
                if len(vec) != EMBED_DIM: continue
                rows.append({
                    "path": path, "chunk_idx": i,
                    "text": chunk.get("text", ""),
                    "vector": vec, "mtime": float(data.get("mtime", 0.0)),
                    "links": json.dumps(chunk.get("links", []), ensure_ascii=False),
                    "tags":  json.dumps(chunk.get("tags",  []), ensure_ascii=False),
                    "importance": data.get("importance", "LOW"),
                    "user_written": bool(data.get("user_written", True)),
                    "hit_log": hit_json,
                })
        if rows:
            self._table.add(rows)
            print(f"✅ [마이그레이션] {len(rows)}개 청크 ({len(set(r['path'] for r in rows))}개 파일) 완료")
        self._save_meta()
        import shutil
        shutil.copy2(DB_FILE, DB_FILE + ".pre_lance_backup")
        print(f"📦 기존 JSON 백업: {DB_FILE}.pre_lance_backup")

    def _save_meta(self):
        try:
            if "meta" not in (self._lance_db.table_names() if hasattr(self._lance_db, "table_names") else [str(t) for t in self._lance_db.list_tables()]):
                import pyarrow as pa
                self._lance_db.create_table("meta",
                    schema=pa.schema([pa.field("key", pa.string()), pa.field("value", pa.string())]),
                    mode="overwrite")
            rows = [{"key": k, "value": str(v)} for k, v in self._meta.items()]
            self._lance_db.open_table("meta").add(rows, mode="overwrite")
        except Exception as e:
            print(f"⚠️ 메타 저장 오류: {e}")

    def _save_db(self):
        """LanceDB는 자동 저장. 백업 폴더에 스냅샷만 남김."""
        try:
            import shutil
            backup_dir = r"C:\Users\User\AppData\Local\onew\db_backup"
            os.makedirs(backup_dir, exist_ok=True)
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            dst = os.path.join(backup_dir, f"onew_lance_db_{ts}")
            if os.path.exists(LANCE_DB_DIR):
                shutil.copytree(LANCE_DB_DIR, dst, dirs_exist_ok=True)
                # 백업 성공 확인
                if os.path.exists(dst):
                    print(f"💾 DB 백업 완료: onew_lance_db_{ts}")
                else:
                    print(f"⚠️ 백업 폴더가 생성되지 않았습니다: {dst}")
            else:
                print(f"⚠️ 백업 대상 없음: {LANCE_DB_DIR}")
            for old in sorted(glob.glob(os.path.join(backup_dir, "onew_lance_db_*")))[:-3]:
                shutil.rmtree(old, ignore_errors=True)
        except Exception as e:
            print(f"⚠️ 백업 오류: {e}")

    # ── 로드 제어 ─────────────────────────────────────────────────────────────
    def _ensure_loaded(self):
        if self._db_loaded: return
        with self._load_lock:
            if not self._db_loaded:
                self._load_db()

    def _reload_if_updated(self):
        """LanceDB는 항상 최신 상태이므로 ensure_loaded만 호출."""
        self._ensure_loaded()

    # ── 동기화 ────────────────────────────────────────────────────────────────
    def sync(self, silent=False):
        self._ensure_loaded()

        # embed_queue 처리 (야간학습 C 기능)
        _embed_queue_file = os.path.join(os.path.dirname(DB_FILE), 'embed_queue.json')
        _embed_priority   = set()
        if os.path.exists(_embed_queue_file):
            try:
                with open(_embed_queue_file, 'r', encoding='utf-8') as _f:
                    _queued = json.load(_f)
                _embed_priority = set(p for p in _queued if os.path.exists(p))
                if _embed_priority and not silent:
                    print(f"📥 [임베딩 큐] 야간학습 신규 {len(_embed_priority)}개 파일 우선 처리")
                os.remove(_embed_queue_file)
            except: pass

        if not silent:
            print("🧠 온유(MD 전용 안전 모드)가 지식 네트워크를 스캔 중입니다...")

        # 청크 버전 체크 — 버전 다르면 순차 재학습 (즉시 삭제 금지, 기존 데이터 유지)
        stored_version = self._meta.get("chunk_version")
        force_reindex = stored_version is not None and stored_version != CHUNK_VERSION
        if force_reindex and not silent:
            print(f"🔄 청크 전략 변경 감지 ({stored_version} → {CHUNK_VERSION}). 순차 재학습 시작 (기존 데이터 유지)...")

        # 메타 선점: 중간에 꺼져도 chunk_version 유지 (재시작 시 force_reindex 방지)
        self._meta["chunk_version"] = CHUNK_VERSION
        self._save_meta()

        last_sync = self._meta.get("last_sync")
        if not silent and last_sync:
            print(f"⏱️  마지막 동기화: {last_sync}")

        # 콘텐츠 해시 캐시 로드 (내용 무변경 파일 API 호출 완전 스킵)
        # DB가 비어있으면 해시 캐시 무시 (DB 소실 후 재실행 시 모든 파일 스킵되는 버그 방지)
        import hashlib as _hashlib
        try:
            _db_empty = self._table.count_rows() == 0
        except:
            _db_empty = True
        hash_cache = {}
        if not _db_empty and os.path.exists(HASH_CACHE_FILE):
            try:
                with open(HASH_CACHE_FILE, 'r', encoding='utf-8') as f: hash_cache = json.load(f)
            except: pass

        # 일일 사용량 로드
        today = datetime.now().strftime("%Y-%m-%d")
        usage_data = {}
        if os.path.exists(USAGE_LOG_FILE):
            try:
                with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: usage_data = json.load(f)
            except: pass
        daily_calls = usage_data.get(today, 0)

        md_files = glob.glob(os.path.join(OBSIDIAN_VAULT_PATH, "**/*.md"), recursive=True)

        def _is_excluded(path):
            p = path.replace("\\", "/")
            if any(f"/{d}/" in p or p.endswith(f"/{d}") for d in SYNC_EXCLUDE_DIRS): return True
            if any(excl in os.path.basename(path) for excl in SYNC_EXCLUDE_FILES): return True
            return False

        md_files     = [f for f in md_files if not _is_excluded(f)]
        md_files_set = set(md_files)
        updated      = 0

        if not silent:
            print(f"📂 학습 대상: {len(md_files)}개 파일 (제외 폴더: {', '.join(SYNC_EXCLUDE_DIRS)})")

        # DB 파일별 최신 mtime 조회
        db_mtimes = {}
        try:
            for row in self._table.search().select(["path", "mtime"]).limit(10_000_000).to_list():
                p = row["path"]
                if p not in db_mtimes or row["mtime"] > db_mtimes[p]:
                    db_mtimes[p] = row["mtime"]
        except: pass

        # 삭제된 파일 정리
        orphan_paths = [p for p in db_mtimes if p not in md_files_set]
        for op in orphan_paths:
            try: self._table.delete(f"path = '{op.replace(chr(39), chr(39)*2)}'")
            except: pass
            hash_cache.pop(op, None)  # hash_cache 고아 항목도 제거
        if orphan_paths and not silent:
            print(f"🗑️  DB 정리: {len(orphan_paths)}개 제거")

        # 신규/변경 파일 탐색 (force_reindex면 전체 대상)
        to_update = [
            f for f in md_files
            if os.path.exists(f) and (force_reindex or f not in db_mtimes or db_mtimes[f] < os.path.getmtime(f))
        ]
        if _embed_priority:
            prio   = [f for f in to_update if f in _embed_priority]
            rest   = [f for f in to_update if f not in _embed_priority]
            extra  = [f for f in _embed_priority if f not in set(to_update) and os.path.exists(f)]
            to_update = prio + extra + rest
        total = len(to_update)
        BATCH_SIZE = 100  # 파일 100개마다 한 번에 DB에 씀 (LanceDB 파일 폭발 방지)
        batch_rows = []   # 누적 행 버퍼
        global_hit_limit = False

        def _flush_batch():
            if batch_rows:
                self._table.add(batch_rows)
                batch_rows.clear()

        for idx, f_path in enumerate(to_update, 1):
            if global_hit_limit: break
            if not os.path.exists(f_path): continue
            mtime = os.path.getmtime(f_path)
            try:
                with open(f_path, 'r', encoding='utf-8') as f: content = f.read()
                if not content.strip(): continue

                # 해시 철벽: 내용이 한 글자도 안 바뀌었으면 0원으로 스킵
                content_hash = _hashlib.md5(content.encode('utf-8', errors='ignore')).hexdigest()
                if hash_cache.get(f_path) == content_hash:
                    continue

                links        = list(set([l.split('|')[0] for l in re.findall(r'\[\[(.*?)\]\]', content)]))
                tags         = list(set(re.findall(r'(?<!\S)#([a-zA-Z0-9_가-힣]+)', content)))
                importance   = _score_importance(content, os.path.basename(f_path))
                user_written = 'author: Onew' not in content[:500]

                is_large = (os.path.getsize(f_path) > MAX_FILE_SIZE_KB * 1024)
                chunks   = _semantic_chunks(content)
                if not chunks: continue
                if is_large:
                    if not silent: print(f"\n📦 압축 중: {os.path.basename(f_path)}")
                    compressed = _compress_content(content, os.path.basename(f_path))
                    if not compressed:
                        if not silent: print(f"\n⚠️  압축 실패, 건너뜀: {os.path.basename(f_path)}")
                        continue
                    chunks = _semantic_chunks(compressed)
                if len(chunks) > MAX_CHUNKS_PER_FILE:
                    if not silent: print(f"\n⚠️  청크 초과({len(chunks)}개 > {MAX_CHUNKS_PER_FILE}): {os.path.basename(f_path)}")

                if not silent:
                    print(f"🔄 [{idx}/{total}] {os.path.basename(f_path)}", end="\r")

                new_rows   = []
                skip_file  = False
                hit_limit  = False
                for i, c in enumerate(chunks):
                    if daily_calls >= MAX_DAILY_EMBED_CALLS:
                        if not silent: print(f"\n🚨 [서킷 브레이커] 금일 리미트({MAX_DAILY_EMBED_CALLS:,}회) 도달. 중단.")
                        hit_limit = True; global_hit_limit = True
                        # 비정상 종료 대비 즉시 저장
                        try:
                            usage_data[today] = daily_calls
                            with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as _f:
                                json.dump(usage_data, _f)
                        except: pass
                        break
                    res = None
                    for attempt in range(2):
                        try:
                            res = client.models.embed_content(
                                model="gemini-embedding-001", contents=c,
                                config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
                            break
                        except: time.sleep(0.5)
                    if not res or not res.embeddings: skip_file = True; break
                    daily_calls += 1
                    vec = list(res.embeddings[0].values)
                    if len(vec) != EMBED_DIM: continue
                    new_rows.append({
                        "path": f_path, "chunk_idx": i,
                        "text": f"[문서명: {os.path.basename(f_path)}]\n{c}",
                        "vector": vec, "mtime": mtime,
                        "links": json.dumps(links, ensure_ascii=False),
                        "tags":  json.dumps(tags,  ensure_ascii=False),
                        "importance": importance, "user_written": user_written,
                        "hit_log": json.dumps([]),
                    })
                    time.sleep(0.1)

                if skip_file:
                    if not silent: print(f"\n❌ API 응답 지연 건너뜀: {os.path.basename(f_path)}")
                    continue
                if hit_limit:
                    _flush_batch()  # 이전 파일들 누적분 flush 후 중단
                    continue

                if new_rows:
                    escaped = f_path.replace("'", "''")
                    try: self._table.delete(f"path = '{escaped}'")
                    except: pass
                    batch_rows.extend(new_rows)
                    hash_cache[f_path] = content_hash  # 해시 캐시 업데이트
                    updated += 1

                # 100개마다 배치 flush + 해시 캐시 저장
                if updated % BATCH_SIZE == 0 and updated > 0:
                    _flush_batch()
                    try:
                        with open(HASH_CACHE_FILE, 'w', encoding='utf-8') as f:
                            json.dump(hash_cache, f, ensure_ascii=False)
                    except: pass

            except: continue

        # 남은 배치 flush
        _flush_batch()

        # 해시 캐시 최종 저장
        try:
            with open(HASH_CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(hash_cache, f, ensure_ascii=False)
        except: pass

        # 메타 업데이트
        self._meta["last_sync"]     = datetime.now().strftime("%Y-%m-%d %H:%M")
        self._meta["chunk_version"] = CHUNK_VERSION
        self._save_meta()

        usage_data[today] = daily_calls
        try:
            with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f: json.dump(usage_data, f)
        except: pass

        if updated > 0 or orphan_paths:
            # LanceDB 단편화 파일 병합 (배치 add() 반복으로 누적된 fragment 정리)
            # compact_files/optimize 호출 제거 (Python 3.14 + LanceDB 버그로 DB 초기화됨)
            self._save_db()
            # FTS 인덱스 갱신 (데이터 변경 시)
            try:
                self._table.create_fts_index("text", replace=True)
                self._fts_available = True
            except: pass
            if not silent: print(f"\n💾 완료: {updated}개 업데이트, {len(orphan_paths)}개 정리")
        else:
            if not silent: print("\n✨ 모든 자료가 최신 상태입니다.")

    # ── 단일 파일 즉시 임베딩 (Lv.4: 세션 요약 저장 직후 호출) ────────────────
    def embed_single_file(self, file_path: str, silent: bool = True):
        """단일 파일을 즉시 임베딩하여 LanceDB에 추가/갱신한다."""
        import hashlib as _hashlib
        if not os.path.exists(file_path):
            return
        try:
            mtime = os.path.getmtime(file_path)
            content = Path(file_path).read_text(encoding="utf-8")
            if not content.strip():
                return
            links = list(set([l.split('|')[0] for l in re.findall(r'\[\[(.*?)\]\]', content)]))
            tags  = list(set(re.findall(r'(?<!\S)#([a-zA-Z0-9_가-힣]+)', content)))
            importance = _score_importance(content, os.path.basename(file_path))
            chunks = _semantic_chunks(content)
            if not chunks:
                return
            # 기존 청크 삭제 후 재삽입
            try:
                safe_path = file_path.replace("'", "''")
                self._table.delete(f"path = '{safe_path}'")
            except:
                pass
            new_rows = []
            for i, c in enumerate(chunks[:20]):  # 요약 파일은 최대 20청크
                try:
                    res = client.models.embed_content(
                        model="gemini-embedding-001", contents=c,
                        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
                    vec = list(res.embeddings[0].values)
                    if len(vec) != EMBED_DIM:
                        continue
                    new_rows.append({
                        "path": file_path, "chunk_idx": i,
                        "text": f"[문서명: {os.path.basename(file_path)}]\n{c}",
                        "vector": vec, "mtime": mtime,
                        "links": json.dumps(links, ensure_ascii=False),
                        "tags":  json.dumps(tags,  ensure_ascii=False),
                        "importance": importance, "user_written": True,
                        "hit_log": json.dumps([]),
                    })
                    _increment_usage("rag")
                    time.sleep(0.1)
                except:
                    pass
            if new_rows:
                self._table.add(new_rows)
                if not silent:
                    print(f"🔗 [Lv.4] 세션 요약 즉시 임베딩 완료: {os.path.basename(file_path)} ({len(new_rows)}청크)")
        except Exception as e:
            if not silent:
                print(f"  (임베딩 실패: {e})")

    # ── 검색 ──────────────────────────────────────────────────────────────────
    def search(self, query, k=5):
        self._reload_if_updated()

        # 쿼리 임베딩
        try:
            res = client.models.embed_content(
                model="gemini-embedding-001", contents=query,
                config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"))
            q_emb = list(res.embeddings[0].values)
            _increment_usage("rag")
        except:
            return []

        # LanceDB 벡터 검색 — 후보 k*5개
        try:
            candidates_raw = (self._table.search(q_emb)
                              .metric("cosine").limit(k * 5).to_list())
        except:
            return []
        if not candidates_raw:
            return []

        # FTS 검색 후 union (키워드 정확 매칭 문서 사각지대 해소)
        if self._fts_available:
            try:
                fts_raw = self._table.search(query, query_type="fts").limit(k * 5).to_list()
                seen = {(r["path"], r["chunk_idx"]) for r in candidates_raw}
                for row in fts_raw:
                    key = (row["path"], row["chunk_idx"])
                    if key not in seen:
                        row["_distance"] = 1.0  # 벡터 거리 미측정 → 기본값
                        candidates_raw.append(row)
                        seen.add(key)
            except: pass

        all_chunks = [{
            "text":         row["text"],
            "links":        json.loads(row.get("links", "[]")),
            "source":       os.path.basename(row["path"]),
            "path":         row["path"],
            "importance":   row.get("importance", "LOW"),
            "user_written": bool(row.get("user_written", True)),
            "_dist":        row.get("_distance", 1.0),
        } for row in candidates_raw]

        # 벡터 점수 (distance → similarity)
        vec_scores = [max(0.0, 1.0 - c["_dist"]) for c in all_chunks]

        # BM25 점수
        try:
            from rank_bm25 import BM25Okapi
            tokenized  = [c["text"].split() for c in all_chunks]
            bm25       = BM25Okapi(tokenized)
            bm25_raw   = bm25.get_scores(query.split())
            bm25_max   = max(bm25_raw) or 1
            bm25_scores = [s / bm25_max for s in bm25_raw]
        except:
            bm25_scores = [0.0] * len(all_chunks)

        # 최신순 가중치
        import re as _re
        from datetime import date as _date
        _date_pat = _re.compile(r'(\d{4}-\d{2}-\d{2})')
        _today    = _date.today()
        is_time_query = any(kw in query for kw in TIME_QUERY_KEYWORDS)

        def _recency_bonus(chunk):
            if not is_time_query: return 0.0
            m = _date_pat.search(chunk.get("source", ""))
            if m:
                try:
                    days_ago = (_today - _date.fromisoformat(m.group(1))).days
                    return max(0.0, 0.5 - days_ago * 0.02)
                except: pass
            try:
                days_ago = (_today - _date.fromtimestamp(os.path.getmtime(chunk.get("path", "")))).days
                return max(0.0, 0.2 - days_ago * 0.01)
            except: return 0.0

        # 하이브리드 점수 (벡터 70% + BM25 30% + 보정들)
        importance_bonus = {"HIGH": 0.05, "MEDIUM": 0.02, "LOW": 0.0}
        query_tokens     = query.split()
        for i, c in enumerate(all_chunks):
            c["score"] = (
                vec_scores[i] * 0.7 + bm25_scores[i] * 0.3
                + importance_bonus.get(c.get("importance", "LOW"), 0.0)
                + (0.3 if any(tok in c["text"] for tok in query_tokens) else 0.0)
                + (0.08 if c.get("user_written", True) else 0.0)
                + _recency_bonus(c)
            )

        all_chunks.sort(key=lambda x: x["score"], reverse=True)
        results = [r for r in all_chunks[:k] if r["score"] >= 0.15]

        # 히트 기록 (인메모리)
        today = datetime.now().strftime("%Y-%m-%d")
        for r in results:
            self._hit_counts.setdefault(r["path"], []).append(today)
        return results

    # ── 중요도 재계산 ─────────────────────────────────────────────────────────
    def recalculate_importance(self):
        from datetime import timedelta
        cutoff  = (datetime.now() - timedelta(days=HIT_WINDOW_DAYS)).strftime("%Y-%m-%d")
        changed = 0
        try:
            rows = self._table.search().select(["path", "hit_log", "importance"]).limit(10_000_000).to_list()
        except: return

        path_info = {}
        for row in rows:
            p = row["path"]
            if p not in path_info:
                path_info[p] = {
                    "importance": row.get("importance", "LOW"),
                    "hit_log":    json.loads(row.get("hit_log") or "[]"),
                }

        for path, info in path_info.items():
            recent = [d for d in info["hit_log"] + self._hit_counts.get(path, []) if d >= cutoff]
            new_imp = "HIGH" if len(recent) >= 10 else "MEDIUM" if len(recent) >= 3 else info["importance"]
            if info["importance"] != new_imp or recent != info["hit_log"]:
                escaped  = path.replace("'", "''")
                hit_json = json.dumps(recent, ensure_ascii=False)
                try:
                    self._table.update(where=f"path = '{escaped}'",
                                       values={"importance": new_imp, "hit_log": hit_json})
                    changed += 1
                except: pass

        if changed > 0:
            self._save_db()
            print(f"📈 [중요도 재계산] {changed}개 파일 업데이트 완료")
        self._meta["last_importance_recalc"] = datetime.now().strftime("%Y-%m-%d")
        self._save_meta()

# ==============================================================================
# [2. Vibe Coding Tools (파일 제어 권한 도구)]
# ==============================================================================
def read_file(filepath: str) -> str:
    """지정된 경로의 파일 내용을 읽어옵니다. 코드를 수정하기 전에 먼저 읽어보세요.
    파일명만 입력 시(예: '2025-10-17.md') Vault 전체에서 자동으로 파일을 찾습니다."""
    try:
        p = Path(filepath)
        # 절대경로이거나 파일이 바로 존재하면 그대로 읽기
        if p.is_absolute() and p.exists():
            with open(p, 'r', encoding='utf-8') as f:
                return f.read()
        # 상대경로 또는 파일명만 입력된 경우 → Vault 전체에서 탐색
        if not p.is_absolute():
            candidates = list(Path(OBSIDIAN_VAULT_PATH).rglob(p.name))
            if candidates:
                with open(candidates[0], 'r', encoding='utf-8') as f:
                    return f.read()
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def create_folder(folderpath: str) -> str:
    """Vault 내에 폴더를 생성합니다. 폴더 경로는 절대경로 또는 Vault 기준 상대경로 모두 가능합니다."""
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

def _backup_file(p: Path):
    """수정 전 원본을 code_backup/YYYY-MM-DD/ 에 보존."""
    try:
        import shutil
        backup_dir = Path(r"C:\Users\User\AppData\Local\onew\code_backup") / datetime.now().strftime('%Y-%m-%d')
        backup_dir.mkdir(parents=True, exist_ok=True)
        dest = backup_dir / p.name
        # 같은 날 이미 백업 있으면 덮어쓰지 않음 (첫 수정본 보존)
        if not dest.exists():
            shutil.copy2(str(p), str(dest))
    except Exception as e:
        print(f"  ⚠️ [백업] 실패: {e}")


def _send_telegram_notify(msg: str):
    """옵시디언 에이전트 → 텔레그램 단방향 알림."""
    try:
        import urllib.request, urllib.parse, json as _json
        token = os.environ.get('TELEGRAM_BOT_TOKEN', '')
        if not token:
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment')
                token, _ = winreg.QueryValueEx(k, 'TELEGRAM_BOT_TOKEN')
                winreg.CloseKey(k)
            except: pass
        if not token:
            return
        ids_file = os.path.join(OBSIDIAN_VAULT_PATH, 'SYSTEM', 'telegram_allowed_ids.json')
        if not os.path.exists(ids_file):
            return
        with open(ids_file, 'r') as f:
            ids = _json.load(f)
        if not ids:
            return
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode(
            {'chat_id': ids[0], 'text': msg, 'parse_mode': 'Markdown'}
        ).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
    except Exception as e:
        print(f"  ⚠️ [텔레그램 알림] 실패: {e}")


def _review_with_claude_bg(filepath: str, content: str):
    """백그라운드: Claude API로 코드 리뷰 후 SYSTEM/코드리뷰/에 저장."""
    try:
        import anthropic as _ant
        # API 키: 환경변수 → 레지스트리 순
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        if not api_key:
            try:
                import winreg
                k = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment')
                api_key, _ = winreg.QueryValueEx(k, 'ANTHROPIC_API_KEY')
                winreg.CloseKey(k)
            except: pass
        if not api_key:
            print("  ⚠️ [Claude 리뷰] ANTHROPIC_API_KEY 없음. 리뷰 생략.")
            return

        filename = Path(filepath).name
        client = _ant.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": (
                    f"Python 코드를 검토해주세요. 버그, 논리 오류, 개선점을 한국어로 간결하게 알려주세요.\n"
                    f"문제 없으면 '✅ 이상 없음'만 출력하세요.\n\n"
                    f"파일: {filename}\n\n```python\n{content[:4000]}\n```"
                )
            }]
        )
        review = msg.content[0].text

        os.makedirs(CODE_REVIEW_DIR, exist_ok=True)
        review_file = os.path.join(CODE_REVIEW_DIR, f"{datetime.now().strftime('%Y-%m-%d')}_코드리뷰.md")
        entry = f"\n## {datetime.now().strftime('%H:%M')} — {filename}\n\n{review}\n\n---\n"
        with open(review_file, 'a', encoding='utf-8') as f:
            f.write(entry)

        # 결과 터미널 출력 + 텔레그램 알림
        if '✅' not in review:
            print(f"⚠️ [Claude 리뷰] {filename} — 검토 결과 있음 → SYSTEM/코드리뷰/ 확인하세요.")
            _send_telegram_notify(
                f"⚠️ *Claude 코드 리뷰 — {filename}*\n\n"
                f"{review[:600]}\n\n"
                f"📁 `SYSTEM/코드리뷰/{datetime.now().strftime('%Y-%m-%d')}_코드리뷰.md`"
            )
        else:
            print(f"✅ [Claude 리뷰] {filename} — 이상 없음.")
            _send_telegram_notify(f"✅ *Claude 코드 리뷰 — {filename}*\n이상 없음.")
    except Exception as e:
        print(f"  ⚠️ [Claude 리뷰] 실패: {e}")


def write_file(filepath: str, content: str) -> str:
    """지정된 경로에 파일을 생성하거나 내용을 덮어씁니다. 코드를 작성하거나 수정할 때 사용하세요."""
    try:
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        p = Path(filepath)
        # 상대경로면 Vault 기준으로 처리
        if not p.is_absolute():
            p = vault_path / p
        p = p.resolve()
        # .md 파일이 Vault 외부에 저장되려 하면 Vault 루트로 리다이렉트 (폴더 구조 보존)
        if p.suffix == '.md':
            try:
                p.relative_to(vault_path)  # Vault 내부면 통과
            except ValueError:
                p = vault_path / Path(filepath).name   # Vault 외부면 루트로
            filepath = str(p)
        # YYYY-MM-DD.md 형식 파일은 DAILY 폴더에만 허용
        import re as _re
        if p.suffix == '.md' and _re.fullmatch(r'\d{4}-\d{2}-\d{2}', p.stem):
            daily_dir = (vault_path / 'DAILY').resolve()
            if p.resolve().parent != daily_dir:
                return (
                    f"🚫 [경로 규칙] '{p.name}'은 날짜 형식 파일입니다. "
                    f"반드시 DAILY 폴더에만 생성하세요.\n"
                    f"올바른 경로: DAILY/{p.name}"
                )

        # .md 파일: Vault 전체 중복 파일명 방지
        if p.suffix == '.md' and not p.exists():
            target_name = p.name
            conflicts = []
            for root, dirs, files in os.walk(str(vault_path)):
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['__pycache__', 'code_backup', 'db_backup']]
                for f in files:
                    if f == target_name:
                        rel = os.path.relpath(os.path.join(root, f), str(vault_path))
                        conflicts.append(rel)
            if conflicts:
                return (
                    f"⚠️ [중복 파일명 방지] '{target_name}'은 이미 Vault 내 다른 위치에 존재합니다:\n"
                    + "\n".join(f"  - {c}" for c in conflicts)
                    + f"\n파일명을 고유하게 변경 후 다시 시도하세요. (예: {p.stem}_구분자.md)"
                )

        # 보호 폴더 체크
        try:
            rel_parts = p.relative_to(vault_path).parts
            if any(part in PROTECTED_FOLDERS for part in rel_parts):
                folder = next(part for part in rel_parts if part in PROTECTED_FOLDERS)
                return f"🔒 [보호 폴더] '{folder}' 폴더는 읽기전용입니다. 온유가 직접 수정할 수 없습니다."
        except ValueError:
            pass

        if p.suffix == '.py':
            # 핵심 파일 보호
            if p.name in PROTECTED_FILES:
                return (
                    f"🔒 [보호] '{p.name}'은 핵심 시스템 파일입니다. 온유가 직접 수정할 수 없습니다.\n"
                    f"수정이 필요하면 Claude Code에게 요청하세요."
                )
            # 문법 검사
            import ast
            try: ast.parse(content)
            except SyntaxError as se: return f"문법 오류로 저장 실패: {se}"
            # 수정 전 백업
            if p.exists():
                _backup_file(p)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding='utf-8')
        # .py 파일이면 백그라운드에서 Claude 리뷰
        if p.suffix == '.py':
            t = threading.Thread(target=_review_with_claude_bg, args=(str(p), content), daemon=True)
            t.start()
        # 저장 후 실제 내용을 읽어서 반환 → 온유가 직접 검증 가능
        saved = p.read_text(encoding='utf-8')
        preview = saved[:800] + ('\n...(이하 생략)' if len(saved) > 800 else '')
        review_note = "\n🔍 Claude 코드 리뷰 백그라운드 실행 중..." if p.suffix == '.py' else ""
        return (
            f"Success: {filepath} 저장 완료.{review_note}\n"
            f"[저장된 실제 내용 — 직접 확인하세요]\n"
            f"---\n{preview}\n---"
        )
    except Exception as e:
        return f"Error writing file: {e}"

def edit_file(filepath: str, old_str: str, new_str: str) -> str:
    """파일의 특정 부분만 교체합니다. 전체 재작성 대신 반드시 이 도구를 사용하세요.
    old_str: 교체할 기존 텍스트 (파일 내에서 유일해야 함)
    new_str: 교체할 새 텍스트"""
    try:
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        p = Path(filepath)
        if not p.is_absolute():
            p = vault_path / p
        p = p.resolve()

        # 보호 폴더 체크 (존재 여부보다 먼저)
        try:
            rel_parts = p.relative_to(vault_path).parts
            if any(part in PROTECTED_FOLDERS for part in rel_parts):
                folder = next(part for part in rel_parts if part in PROTECTED_FOLDERS)
                return f"🔒 [보호 폴더] '{folder}' 폴더는 읽기전용입니다. 온유가 직접 수정할 수 없습니다."
        except ValueError:
            pass

        # 핵심 파일 보호
        if p.name in PROTECTED_FILES:
            return (
                f"🔒 [보호] '{p.name}'은 핵심 시스템 파일입니다. 온유가 직접 수정할 수 없습니다.\n"
                f"수정이 필요하면 Claude Code에게 요청하세요."
            )

        if not p.exists():
            return f"Error: 파일이 존재하지 않습니다 → {filepath}"

        original = p.read_text(encoding='utf-8')

        # old_str 존재 확인
        count = original.count(old_str)
        if count == 0:
            return f"Error: 찾을 수 없습니다. old_str가 파일 내용과 정확히 일치하는지 확인하세요."
        if count > 1:
            return f"Error: old_str가 파일에서 {count}번 발견됩니다. 더 많은 주변 코드를 포함해서 유일하게 만들어주세요."

        # .py 파일이면 결과물 문법 검사 먼저
        new_content = original.replace(old_str, new_str, 1)
        if p.suffix == '.py':
            import ast
            try:
                ast.parse(new_content)
            except SyntaxError as se:
                return f"문법 오류로 수정 실패: {se}"

        # 백업 (하루 첫 수정본 보존)
        if p.suffix == '.py':
            _backup_file(p)

        p.write_text(new_content, encoding='utf-8')

        # .py이면 백그라운드 Claude 리뷰
        if p.suffix == '.py':
            t = threading.Thread(target=_review_with_claude_bg, args=(str(p), new_content), daemon=True)
            t.start()

        # 변경된 부분 전후 3줄 미리보기
        lines = new_content.splitlines()
        new_lines = new_str.splitlines()
        # 변경 위치 찾기
        changed_start = new_content.find(new_str)
        before = new_content[:changed_start].count('\n')
        start = max(0, before - 2)
        end   = min(len(lines), before + len(new_lines) + 3)
        preview = '\n'.join(lines[start:end])

        review_note = "\n🔍 Claude 코드 리뷰 백그라운드 실행 중..." if p.suffix == '.py' else ""
        return (
            f"Success: {p.name} 수정 완료.{review_note}\n"
            f"[변경된 부분 미리보기 (줄 {start+1}~{end})]\n"
            f"---\n{preview}\n---"
        )
    except Exception as e:
        return f"Error editing file: {e}"


def list_files(directory: str) -> str:
    """지정된 디렉토리 내의 파일 및 폴더 목록을 반환합니다. 구조를 파악할 때 사용하세요.
    경로는 절대경로 또는 Vault 기준 상대경로 모두 가능합니다. 경로 생략 시 Vault 루트를 반환합니다."""
    try:
        p = Path(directory) if directory else Path(OBSIDIAN_VAULT_PATH)
        if not p.is_absolute():
            p = Path(OBSIDIAN_VAULT_PATH) / p
        p = p.resolve()
        entries = sorted(p.iterdir(), key=lambda x: (x.is_file(), x.name))
        lines = []
        for entry in entries:
            prefix = "📄 " if entry.is_file() else "📁 "
            lines.append(f"{prefix}{entry.name}")
        return f"[{p}]\n" + "\n".join(lines) if lines else f"[{p}] (비어 있음)"
    except Exception as e:
        return f"Error listing directory: {e}"

def move_file(src: str, dst: str) -> str:
    """파일을 src에서 dst로 이동합니다. 바탕화면 → Vault 정리 등에 사용하세요."""
    try:
        s = Path(src).resolve()
        d = Path(dst).resolve()
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(s).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] 출발 경로가 허용 범위 밖입니다 → {src}"
        if not any(str(d).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] 목적지 경로가 허용 범위 밖입니다 → {dst}"
        # 보호 폴더 체크 (출발/목적지 모두, 존재 여부보다 먼저)
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        for check_path, label in [(s, '출발'), (d, '목적지')]:
            try:
                rel_parts = check_path.relative_to(vault_path).parts
                if any(part in PROTECTED_FOLDERS for part in rel_parts):
                    folder = next(part for part in rel_parts if part in PROTECTED_FOLDERS)
                    return f"🔒 [보호 폴더] '{folder}' 폴더는 읽기전용입니다 ({label}). 온유가 직접 이동할 수 없습니다."
            except ValueError:
                pass
        if not s.exists():
            return f"Error: 파일이 존재하지 않습니다 → {src}"
        # 확인 프롬프트
        if sys.stdin.isatty():
            try:
                answer = input(f"⚠️ '{s.name}' 파일을 이동해도 될까요? ({src} → {dst}) (y/n): ").strip().lower()
                if answer != 'y':
                    return "취소: 사용자가 파일 이동을 취소했습니다."
            except EOFError:
                pass
        else:
            _send_telegram_notify(
                f"🚫 [이동 요청 차단]\n온유가 파일 이동을 시도했습니다.\n"
                f"출발: `{src}`\n목적지: `{dst}`\n직접 확인 후 처리하세요."
            )
            return "🚫 [텔레그램 모드] 파일 이동은 자동 실행이 차단됩니다. 사용자에게 알림을 전송했습니다."
        d.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(s), str(d))
        return f"Success: 이동 완료 → {src}  →  {dst}"
    except Exception as e:
        return f"Error moving file: {e}"

def delete_file(filepath: str) -> str:
    """지정된 파일을 삭제합니다. 파일 이동 후 원본 제거, 불필요한 파일 정리에 사용하세요."""
    try:
        p = Path(filepath)
        # 파일명만 넘긴 경우 Vault 전체에서 검색
        if not p.is_absolute() and not p.exists():
            import glob as _glob
            matches = _glob.glob(str(Path(OBSIDIAN_VAULT_PATH) / '**' / p.name), recursive=True)
            if matches:
                p = Path(matches[0])
        p = p.resolve()
        # Vault 내부 또는 바탕화면만 허용
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(p).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] Vault/바탕화면 외부 경로는 삭제할 수 없습니다 → {filepath}"
        # 보호 폴더 체크 (존재 여부보다 먼저)
        vault_path = Path(OBSIDIAN_VAULT_PATH).resolve()
        try:
            rel_parts = p.relative_to(vault_path).parts
            if any(part in PROTECTED_FOLDERS for part in rel_parts):
                folder = next(part for part in rel_parts if part in PROTECTED_FOLDERS)
                return f"🔒 [보호 폴더] '{folder}' 폴더는 읽기전용입니다. 온유가 직접 삭제할 수 없습니다."
        except ValueError:
            pass
        if not p.exists():
            return f"Error: 파일이 존재하지 않습니다 → {filepath}"
        if p.is_dir():
            return f"Error: 디렉토리는 삭제할 수 없습니다 (파일만 가능) → {filepath}"
        # 확인 프롬프트
        if sys.stdin.isatty():
            try:
                answer = input(f"⚠️ '{p.name}' 파일을 삭제해도 될까요? (y/n): ").strip().lower()
                if answer != 'y':
                    return "취소: 사용자가 삭제를 취소했습니다."
            except EOFError:
                pass
        else:
            _send_telegram_notify(
                f"🚫 [삭제 요청 차단]\n온유가 파일 삭제를 시도했습니다.\n"
                f"파일: `{filepath}`\n직접 확인 후 처리하세요."
            )
            return "🚫 [텔레그램 모드] 파일 삭제는 자동 실행이 차단됩니다. 사용자에게 알림을 전송했습니다."
        p.unlink()
        return f"Success: 삭제 완료 → {filepath}"
    except Exception as e:
        return f"Error deleting file: {e}"

AUTO_SCRIPTS_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "auto_scripts")

def execute_script(filepath: str) -> str:
    """작성된 파이썬 스크립트를 즉시 실행하고 결과를 반환한다.
    ⚠️ 온유가 생성한 자동화 스크립트는 반드시 SYSTEM/auto_scripts/ 폴더에 저장 후 이 도구로 실행하세요.
    SYSTEM/auto_scripts/ 외부 .py 파일은 터미널 확인 없이 실행 불가."""
    try:
        p = Path(filepath).resolve()
        sandbox = Path(AUTO_SCRIPTS_DIR).resolve()
        allowed_roots = [
            Path(OBSIDIAN_VAULT_PATH).resolve(),
            Path(r"C:\Users\User\Desktop").resolve(),
        ]
        if not any(str(p).startswith(str(root)) for root in allowed_roots):
            return f"🚫 [보안] Vault/바탕화면 외부 경로의 스크립트는 실행할 수 없습니다 → {filepath}"
        if p.suffix != '.py':
            return f"🚫 [보안] .py 파일만 실행 가능합니다 → {filepath}"

        # 샌드박스 외부 스크립트는 터미널 확인 필요
        try:
            p.relative_to(sandbox)
            is_sandboxed = True
        except ValueError:
            is_sandboxed = False
        if not is_sandboxed:
            if sys.stdin.isatty():
                try:
                    answer = input(
                        f"⚠️ 샌드박스(auto_scripts/) 외부 스크립트 실행 요청:\n  {p}\n실행해도 될까요? (y/n): "
                    ).strip().lower()
                    if answer != 'y':
                        return "취소: 사용자가 스크립트 실행을 취소했습니다."
                except EOFError:
                    pass
            else:
                _send_telegram_notify(
                    f"🚫 [스크립트 실행 요청 차단]\n샌드박스 외부 스크립트: `{filepath}`\n직접 확인 후 처리하세요."
                )
                return "🚫 [텔레그램 모드] 샌드박스 외부 스크립트 실행은 차단됩니다. 사용자에게 알림을 전송했습니다."

        # 샌드박스 폴더가 없으면 생성
        sandbox.mkdir(parents=True, exist_ok=True)
        res = subprocess.run(
            [sys.executable, str(p)],
            capture_output=True, text=True, timeout=30,
            cwd=str(sandbox)   # 작업 디렉토리를 샌드박스로 고정
        )
        sandbox_tag = "✅ [샌드박스]" if is_sandboxed else "⚠️ [비샌드박스]"
        return f"{sandbox_tag}\n--- Output ---\n{res.stdout}\n--- Error ---\n{res.stderr}"
    except Exception as e:
        return f"Execution Failed: {e}"

_SHELL_SAFELIST = [
    "pip install", "pip uninstall", "pip list", "pip show", "pip freeze",
    "python -c", "python -m",
]

def run_shell_command(cmd: str) -> str:
    """안전한 쉘 명령어를 실행한다. 주로 패키지 설치 확인, python 모듈 실행에 사용.
    허용: pip install/uninstall/list/show/freeze, python -m, python -c
    ⚠️ 위 목록 외 명령어는 보안상 차단됩니다."""
    cmd_stripped = cmd.strip()
    cmd_lower = cmd_stripped.lower()
    if not any(cmd_lower.startswith(s) for s in _SHELL_SAFELIST):
        return (f"🚫 [보안] 허용되지 않는 명령어입니다.\n"
                f"허용 목록: {', '.join(_SHELL_SAFELIST)}")
    try:
        res = subprocess.run(
            cmd_stripped, shell=True, capture_output=True, text=True, timeout=60
        )
        out = res.stdout.strip()
        err = res.stderr.strip()
        parts = []
        if out: parts.append(f"[stdout]\n{out}")
        if err: parts.append(f"[stderr]\n{err}")
        parts.append(f"종료 코드: {res.returncode}")
        return "\n".join(parts)
    except subprocess.TimeoutExpired:
        return "Error: 명령어 실행 타임아웃 (60초)"
    except Exception as e:
        return f"Error: {e}"


def browse_web(url: str, extract: str = "") -> str:
    """Playwright 헤드리스 브라우저로 URL을 열어 마크다운 본문을 반환한다.
    JavaScript 렌더링이 필요한 페이지(SPA, 동적 사이트)도 처리 가능.
    Jina/urllib로 접근 불가한 페이지에 사용하라.

    url: 크롤링할 웹 페이지 주소
    extract: 특정 키워드나 섹션을 지정하면 해당 내용 위주로 필터링 (선택)"""
    if not url.startswith(('http://', 'https://')):
        return f"Error: 유효하지 않은 URL: {url}"
    try:
        from playwright.sync_api import sync_playwright
        import re as _re

        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page    = browser.new_page(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            )
            page.goto(url, wait_until="domcontentloaded", timeout=20000)
            page.wait_for_timeout(1500)   # JS 렌더링 대기

            # 제목
            title = page.title() or url.split('/')[-1]

            # 불필요한 태그 제거 후 본문 추출
            body = page.evaluate("""() => {
                ['script','style','nav','footer','header','aside','noscript']
                  .forEach(t => document.querySelectorAll(t).forEach(e => e.remove()));
                return document.body ? document.body.innerText : '';
            }""")
            browser.close()

        # 정리
        body = _re.sub(r'\n{3,}', '\n\n', body.strip())[:8000]

        # 키워드 필터 (extract 지정 시)
        if extract:
            lines   = body.split('\n')
            kw_low  = extract.lower()
            matched = [l for l in lines if kw_low in l.lower()]
            if matched:
                body = '\n'.join(matched[:100])

        return f"[{title}]\n{url}\n\n{body}"

    except Exception as e:
        return f"Error: browse_web 실패: {e}"


def rollback_file(filepath: str) -> str:
    """파일을 가장 최근 백업본으로 복원합니다. 코드 수정 후 문제가 생겼을 때 사용하세요."""
    try:
        p = Path(filepath)
        if not p.is_absolute():
            p = Path(OBSIDIAN_VAULT_PATH) / filepath
        p = p.resolve()

        backup_base = Path(r"C:\Users\User\AppData\Local\onew\code_backup")
        if not backup_base.exists():
            return "Error: 백업 폴더가 없습니다."

        # 날짜 폴더 역순 검색 → 가장 최근 백업 찾기
        date_dirs = sorted(
            [d for d in backup_base.iterdir() if d.is_dir()],
            reverse=True
        )
        for date_dir in date_dirs:
            backup_file = date_dir / p.name
            if backup_file.exists():
                shutil.copy2(str(backup_file), str(p))
                _send_telegram_notify(
                    f"🔄 *롤백 완료*\n`{p.name}` → {date_dir.name} 백업본으로 복원됨"
                )
                return f"✅ 롤백 완료: {p.name} → {date_dir.name} 백업본으로 복원"

        return f"Error: '{p.name}'의 백업본이 없습니다."
    except Exception as e:
        return f"Error: {e}"


def backup_system() -> str:
    """SYSTEM 폴더 전체를 ZIP으로 압축 백업한다."""
    try:
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_dir = r"C:\Users\User\AppData\Local\onew\db_backup"
        os.makedirs(backup_dir, exist_ok=True)
        target = os.path.join(backup_dir, f"Onew_Backup_{ts}")
        shutil.make_archive(target, 'zip', os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM"))
        return f"Success: 백업 완료 → {target}.zip"
    except Exception as e:
        return f"Backup Failed: {e}"

def code_safety_check() -> str:
    """핵심 코드 파일의 MD5 체크섬을 검증하고 안전 점검 보고서를 반환한다."""
    try:
        import path_cleanup
        return path_cleanup.run_all_checks()
    except Exception as e:
        return f"Error: path_cleanup 실행 실패 → {e}"

def save_code_checksums() -> str:
    """현재 핵심 코드 파일들의 MD5 체크섬을 베이스라인으로 저장한다."""
    try:
        import path_cleanup
        return path_cleanup.save_checksums()
    except Exception as e:
        return f"Error: {e}"

def _get_search_count() -> tuple[dict, str, int]:
    """오늘의 웹 검색 횟수를 반환한다."""
    today = datetime.now().strftime("%Y-%m-%d")
    usage_data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: usage_data = json.load(f)
        except: pass
    return usage_data, today, usage_data.get(f"search_{today}", 0)

def _get_today_usage(category: str) -> int:
    """오늘 특정 카테고리의 API 호출 횟수를 반환한다."""
    today = datetime.now().strftime("%Y-%m-%d")
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f).get(f"{category}_{today}", 0)
        except: pass
    return 0

def _increment_usage(category: str):
    """카테고리별 API 호출 횟수를 기록한다. category: 'chat', 'rag', 'summary', 'flowchart'"""
    today = datetime.now().strftime("%Y-%m-%d")
    key = f"{category}_{today}"
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except: pass
    data[key] = data.get(key, 0) + 1
    try:
        with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f: json.dump(data, f)
    except: pass

# ==============================================================================
# [자동 클리핑 시스템]
# ==============================================================================
def _load_clip_config() -> dict:
    cfg = dict(CLIP_DEFAULTS)
    if os.path.exists(CLIP_CONFIG_FILE):
        try:
            with open(CLIP_CONFIG_FILE, 'r', encoding='utf-8') as f:
                cfg.update(json.load(f))
        except: pass
    return cfg

def _save_clip_config(cfg: dict):
    try:
        with open(CLIP_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except: pass

def _load_clip_index() -> dict:
    if os.path.exists(CLIP_INDEX_FILE):
        try:
            with open(CLIP_INDEX_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except: pass
    return {}

def _save_clip_index(index: dict):
    try:
        with open(CLIP_INDEX_FILE, 'w', encoding='utf-8') as f:
            json.dump(index, f, ensure_ascii=False, indent=2)
    except: pass

def _is_recently_clipped(topic: str) -> bool:
    index = _load_clip_index()
    if topic not in index: return False
    try:
        last = datetime.strptime(index[topic]["date"], "%Y-%m-%d")
        # 주간 주제면 7일, 일반 주제면 CLIP_DEDUP_DAYS
        cfg = _load_clip_config()
        weekly = cfg.get("weekly_topics", [])
        dedup = 7 if topic in weekly else CLIP_DEDUP_DAYS
        return (datetime.now() - last).days < dedup
    except: return False

def _today_clip_count() -> int:
    today = datetime.now().strftime("%Y-%m-%d")
    if not os.path.exists(USAGE_LOG_FILE): return 0
    try:
        with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f).get(f"clip_{today}", 0)
    except: return 0

class AutoClipper:
    def __init__(self):
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
        self.today_clips = []  # {"topic", "file", "status"}

    def start(self):
        if self._running: return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True

    def stop(self):
        self._stop_event.set()
        self._running = False

    def _run(self):
        cfg = _load_clip_config()
        if not cfg.get("enabled", True):
            self._running = False
            return

        today = datetime.now().strftime("%Y-%m-%d")
        done = _today_clip_count()
        max_clips = cfg.get("max_clips", 10)
        delay = cfg.get("delay_seconds", 30)

        if done >= max_clips:
            self._running = False
            return

        os.makedirs(CLIP_FOLDER, exist_ok=True)
        topics = cfg.get("topics", [])

        # 이전 세션에서 오늘 완료된 항목 복원 (목록 MD 연속성 유지)
        index = _load_clip_index()
        for topic in topics:
            entry = index.get(topic, {})
            if entry.get("date") == today:
                self.today_clips.append({
                    "topic": topic,
                    "file": entry.get("file", ""),
                    "status": "✅ (이전 세션)"
                })
        if self.today_clips:
            self._update_list_md(today)

        for topic in topics:
            if self._stop_event.is_set(): break

            done = _today_clip_count()
            cfg = _load_clip_config()  # 실행 중 설정 변경 반영
            max_clips = cfg.get("max_clips", 10)
            delay = cfg.get("delay_seconds", 30)

            if done >= max_clips: break
            if _is_recently_clipped(topic): continue
            if self._stop_event.is_set(): break

            # 동기화 중이거나 대화 중이면 클리핑 중단
            try:
                import onew_shared as _os
                if _os.is_syncing() or _os.is_quiet_period():
                    time.sleep(delay)
                    continue
            except ImportError:
                pass

            try:
                import onew_budget as _ob
                if not _ob.check_budget():
                    break
            except ImportError:
                pass

            try:
                search_tool = types.Tool(google_search=types.GoogleSearch())
                ans = client.models.generate_content(
                    model="gemini-2.5-flash",
                    contents=(
                        f"다음 주제를 Anthropic, Google DeepMind, Hugging Face, MIT Technology Review, "
                        f"arXiv 등 공신력 있는 출처 기반으로 최신 동향을 상세히 정리해줘. "
                        f"출처 URL도 함께 명시할 것.\n\n주제: {topic}"
                    ),
                    config=types.GenerateContentConfig(tools=[search_tool])
                )
                result_text = ans.text or ""

                # 200KB 제한
                max_bytes = MAX_CLIP_FILE_KB * 1024
                encoded = result_text.encode('utf-8')
                if len(encoded) > max_bytes:
                    result_text = encoded[:max_bytes].decode('utf-8', errors='ignore')
                    result_text += "\n\n*(200KB 제한으로 잘림)*"

                # 주간 주제: 이전 클리핑과 내용 비교 (hash)
                import hashlib
                new_hash = hashlib.md5(result_text[:2000].encode('utf-8')).hexdigest()
                cfg_now = _load_clip_config()
                weekly_topics = cfg_now.get("weekly_topics", [])
                prev_index = _load_clip_index()
                prev_hash = prev_index.get(topic, {}).get("content_hash", "")

                if topic in weekly_topics and prev_hash and prev_hash == new_hash:
                    # 내용 동일 → "변동 없음" 기록만
                    safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)
                    filename = f"{today}_{safe_topic}.md"
                    filepath = os.path.join(CLIP_FOLDER, filename)
                    content = (
                        f"---\ntags:\n  - 클리핑\n  - 주간추적\n  - 변동없음\n"
                        f"날짜: {today}\n주제: {topic}\n---\n\n"
                        f"# {topic}\n\n> ⏸️ 변동 없음 — {today} (지난 주와 동일한 내용)\n"
                    )
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    index = _load_clip_index()
                    index[topic] = {"date": today, "file": filename, "content_hash": new_hash}
                    _save_clip_index(index)
                    self.today_clips.append({"topic": topic, "file": filename, "status": "⏸️ 변동없음"})
                    self._update_list_md(today)
                    print(f"\n⏸️  [클리핑] {topic} → 변동 없음 (저장 생략)")
                else:
                    # 신규 또는 내용 변경 → 전체 저장
                    safe_topic = re.sub(r'[\\/:*?"<>|]', '_', topic)
                    filename = f"{today}_{safe_topic}.md"
                    filepath = os.path.join(CLIP_FOLDER, filename)
                    weekly_tag = "  - 주간추적\n" if topic in weekly_topics else ""
                    content = (
                        f"---\ntags:\n  - 클리핑\n  - AI\n  - 자동수집\n{weekly_tag}"
                        f"날짜: {today}\n주제: {topic}\n---\n\n"
                        f"# {topic}\n\n> 자동 클리핑 ({today})\n\n{result_text}"
                    )
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)

                    # 인덱스 + 카운터 업데이트 (hash 포함)
                    index = _load_clip_index()
                    index[topic] = {"date": today, "file": filename, "content_hash": new_hash}
                    _save_clip_index(index)
                    _increment_usage("clip")

                    self.today_clips.append({"topic": topic, "file": filename, "status": "✅"})
                    self._update_list_md(today)
                    print(f"\n📎 [클리핑] {topic} → {filename}")

            except Exception as e:
                self.today_clips.append({"topic": topic, "file": "", "status": f"❌ {e}"})
                self._update_list_md(today)
                print(f"\n⚠️  [클리핑 오류] {topic}: {e}")
                log_error_to_vault(f"클리핑: {topic}", str(e))

            self._stop_event.wait(delay)

        self._running = False

    def _update_list_md(self, today: str):
        cfg = _load_clip_config()
        list_path = os.path.join(CLIP_FOLDER, f"{today}_클리핑목록.md")
        lines = [
            "---", "tags:", "  - 클리핑목록", f"날짜: {today}", "---", "",
            f"# {today} 자동 클리핑 목록", "",
            "| # | 주제 | 파일 | 상태 |",
            "|---|------|------|------|",
        ]
        for i, item in enumerate(self.today_clips, 1):
            flink = f"[[{item['file']}]]" if item['file'] else "-"
            lines.append(f"| {i} | {item['topic']} | {flink} | {item['status']} |")
        lines += [
            "", "---",
            f"설정 | 딜레이: {cfg.get('delay_seconds',30)}초 "
            f"| 최대: {cfg.get('max_clips',10)}개 "
            f"| 중복방지: {CLIP_DEDUP_DAYS}일",
        ]
        try:
            with open(list_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
        except: pass

    def status(self) -> str:
        cfg = _load_clip_config()
        today = datetime.now().strftime("%Y-%m-%d")
        done = _today_clip_count()
        state = "🔄 실행 중" if self._running else "⏸ 대기/완료"
        index = _load_clip_index()
        lines = [
            f"📎 [자동 클리핑 현황] {state}",
            f"- 오늘: {done}/{cfg.get('max_clips',10)}개 완료",
            f"- 딜레이: {cfg.get('delay_seconds',30)}초",
            f"- 자동클리핑: {'ON' if cfg.get('enabled',True) else 'OFF'}",
            f"- 중복방지: {CLIP_DEDUP_DAYS}일",
            "", "[주제 목록]",
        ]
        for i, t in enumerate(cfg.get("topics", []), 1):
            last = index.get(t, {}).get("date", "미수집")
            lines.append(f"  {i}. {t}  (최근: {last})")
        return "\n".join(lines)


def _clip_command(q: str, clipper: "AutoClipper") -> bool:
    """자연어 클리핑 명령 처리. 처리됐으면 True 반환."""
    t = q.strip()

    # ── 시작 ─────────────────────────────────────────
    if re.search(r'클리핑.*(시작|켜|on|열어|돌려|실행)', t, re.I):
        clipper.start(); print("📎 클리핑 시작됨."); return True

    # ── 정지 ─────────────────────────────────────────
    if re.search(r'클리핑.*(정지|꺼|off|멈춰|중지|그만|끄)', t, re.I):
        clipper.stop(); print("📎 클리핑 정지됨."); return True

    # ── 상태 ─────────────────────────────────────────
    if re.search(r'클리핑.*(상태|현황|어때|확인|보여|알려|몇)', t, re.I):
        print(clipper.status()); return True

    # ── 딜레이 변경: "딜레이 60", "간격 30초", "30초마다" ───
    m = re.search(r'(딜레이|간격|주기).*?(\d+)\s*초?', t)
    if not m: m = re.search(r'(\d+)\s*초\s*(마다|간격|딜레이)', t)
    if m and re.search(r'클리핑', t, re.I):
        sec = int(m.group(2) if m.lastindex >= 2 else m.group(1))
        print(set_clip_config(delay_seconds=sec)); return True

    # ── 횟수 변경: "횟수 5", "5개로", "10개로 늘려" ──────
    m = re.search(r'(\d+)\s*개', t)
    if m and re.search(r'클리핑.*(횟수|개수|수|늘|줄|변경|바꿔|설정)', t, re.I):
        print(set_clip_config(max_clips=int(m.group(1)))); return True

    # ── 주제 변경 ────────────────────────────────────────────
    is_topic_cmd = bool(re.search(r'클리핑.*(주제|topic)', t, re.I) or
                        re.search(r'주제.*(바꿔|변경|교체|설정)', t, re.I))
    if is_topic_cmd:
        new_topics = []

        # 명령어 노이즈 제거 헬퍼
        def _clean(s):
            # 앞쪽: "변경해줘", "바꿔줘", "클리핑", "주제" 등 제거
            s = re.sub(r'^(클리핑|주제|topic)\s*', '', s, flags=re.I).strip()
            s = re.sub(r'^(변경해줘?|바꿔줘?|교체해줘?|해줘?|변경|바꿔|교체)\s*', '', s, flags=re.I).strip()
            # 뒤쪽: "으로 바꿔줘", "주제" 잔여 제거
            s = re.sub(r'\s*(으?로\s*)?(바꿔|변경|교체|해)줘?\.?$', '', s).strip()
            s = re.sub(r'\s*(주제|topic)\s*$', '', s, flags=re.I).strip(' .,')
            return s

        # 패턴1: "주제: A, B" / "주제 A, B" 쉼표 목록
        m = re.search(r'주제\s*[:\s]\s*(.+)', t)
        if m:
            candidates = [_clean(s) for s in re.split(r'[,，/]', m.group(1)) if s.strip()]
            new_topics = [c for c in candidates if c]

        # 패턴2: "X로 바꿔줘" → X 추출
        if not new_topics:
            m = re.search(r'([가-힣a-zA-Z0-9\s]+?)(?:으?로)\s*(?:바꿔|변경|교체)', t)
            if m:
                c = _clean(m.group(1))
                if c: new_topics = [c]

        # 패턴3: "주제바꿔줘. X로" — 문장 끝 "X로" 형태
        if not new_topics:
            m = re.search(r'([가-힣a-zA-Z0-9]+)(?:으?로)[.\s]*$', t)
            if m:
                c = m.group(1).strip()
                if c: new_topics = [c]

        # 패턴4: "주제 X" 직접 지정 (fallback)
        if not new_topics:
            m = re.search(r'(?:주제|topic)\s+([가-힣a-zA-Z0-9\s,]+)', t, re.I)
            if m:
                parts = [_clean(s) for s in re.split(r'[,，]', m.group(1)) if s.strip()]
                new_topics = [p for p in parts if p]

        if new_topics:
            print(set_clip_config(topics=new_topics)); return True

    return False


def clip_status() -> str:
    """자동 클리핑 현황, 주제 목록, 설정을 보여준다."""
    if 'clipper' in globals(): return globals()['clipper'].status()
    return "클리핑 시스템이 초기화되지 않았습니다."

def get_clip_topics() -> str:
    """현재 클리핑 주제 목록을 번호와 함께 반환한다. 주제 추가/삭제 전 반드시 호출하라."""
    cfg = _load_clip_config()
    topics = cfg.get("topics", [])
    if not topics:
        return "현재 등록된 클리핑 주제가 없습니다."
    lines = [f"{i+1}. {t}" for i, t in enumerate(topics)]
    return f"📋 클리핑 주제 목록 ({len(topics)}개):\n" + "\n".join(lines)

def set_clip_config(topics: List[str] = None, delay_seconds: int = None,
                    max_clips: int = None, enabled: bool = None) -> str:
    """자동 클리핑 설정을 변경한다.
    topics: 새 주제 리스트 (예: ["AI 뉴스", "Python 팁"])
    delay_seconds: 클리핑 간격 (초)
    max_clips: 하루 최대 클리핑 수
    enabled: True=ON / False=OFF
    """
    cfg = _load_clip_config()
    if topics        is not None: cfg["topics"]         = topics
    if delay_seconds is not None: cfg["delay_seconds"] = delay_seconds
    if max_clips     is not None: cfg["max_clips"]     = max_clips
    if enabled       is not None: cfg["enabled"]       = enabled
    _save_clip_config(cfg)
    msgs = []
    if topics        is not None: msgs.append(f"주제 {len(topics)}개 업데이트")
    if delay_seconds is not None: msgs.append(f"딜레이 {delay_seconds}초")
    if max_clips     is not None: msgs.append(f"최대 {max_clips}개")
    if enabled       is not None: msgs.append(f"자동클리핑 {'ON' if enabled else 'OFF'}")
    return "✅ 클리핑 설정 변경: " + ", ".join(msgs)


def set_weekly_clip(topics: List[str], action: str = "add") -> str:
    """특정 주제를 주간(7일) 클리핑 추적 목록에 추가/제거한다.
    topics: 주제 리스트
    action: 'add'(추가) 또는 'remove'(제거)
    주간 주제는 일반 클리핑 주제와 별개로 7일마다 한 번씩 클리핑된다.
    """
    cfg = _load_clip_config()
    weekly = cfg.get("weekly_topics", [])
    if action == "add":
        added = [t for t in topics if t not in weekly]
        weekly.extend(added)
        # 일반 topics에도 추가 (클리퍼가 순회하도록)
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


def analyze_trend(query: str) -> str:
    """Google 검색으로 최신 금융/기술/학습 트렌드를 분석한다."""
    # 웹 검색 일일 횟수 체크
    usage_data, today, search_count = _get_search_count()
    if search_count >= MAX_DAILY_SEARCHES:
        return f"🚫 [검색 테두리] 오늘 검색 한도({MAX_DAILY_SEARCHES}회)를 초과했습니다. (현재: {search_count}회)"

    # 허용 주제 필터 (SEARCH_ALLOW_TOPICS 비어있으면 무제한)
    if SEARCH_ALLOW_TOPICS:
        allowed = any(keyword in query for keyword in SEARCH_ALLOW_TOPICS)
        if not allowed:
            return (f"🚫 [검색 테두리] 허용되지 않은 주제입니다.\n"
                    f"허용 주제: {', '.join(SEARCH_ALLOW_TOPICS[:8])} 등")

    try:
        search_tool = types.Tool(google_search=types.GoogleSearchRetrieval())
        ans = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=query,
            config=types.GenerateContentConfig(tools=[search_tool])
        )
        # 검색 횟수 기록
        usage_data[f"search_{today}"] = search_count + 1
        with open(USAGE_LOG_FILE, 'w', encoding='utf-8') as f: json.dump(usage_data, f)
        return f"🌐 [웹 검색 리포트] ({search_count+1}/{MAX_DAILY_SEARCHES}회)\n\n{ans.text}"
    except Exception as e:
        return f"Search Error: {e}"

# ==============================================================================
# [Google Calendar 연동]
# ==============================================================================
CALENDAR_CREDS_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "calendar_credentials.json")
CALENDAR_TOKEN_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "calendar_token.json")
CALENDAR_SCOPES      = ["https://www.googleapis.com/auth/calendar"]

def _get_calendar_service():
    """Google Calendar 서비스 객체를 반환한다. 최초 1회 브라우저 인증 필요."""
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
                    f"calendar_credentials.json 없음 → {CALENDAR_CREDS_FILE}\n"
                    "Google Cloud Console에서 OAuth2 자격증명을 다운로드 후 저장하세요.")
            flow = InstalledAppFlow.from_client_secrets_file(CALENDAR_CREDS_FILE, CALENDAR_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(CALENDAR_TOKEN_FILE, 'w') as f:
            f.write(creds.to_json())
    return build("calendar", "v3", credentials=creds)

def calendar_list(days: int = 7) -> str:
    """오늘부터 N일간의 구글 캘린더 일정을 조회한다. (기본 7일)"""
    try:
        service = _get_calendar_service()
        from datetime import timezone
        now = datetime.now(timezone.utc)
        end = now + timedelta(days=days)
        events_result = service.events().list(
            calendarId="primary",
            timeMin=now.isoformat(),
            timeMax=end.isoformat(),
            singleEvents=True,
            orderBy="startTime"
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

def _normalize_dt(dt: str) -> str:
    """날짜시간 문자열을 'YYYY-MM-DDTHH:MM:SS' 형식으로 정규화."""
    dt = dt.strip().replace(" ", "T")
    # 초 없으면 추가
    if len(dt) == 16:  # YYYY-MM-DDTHH:MM
        dt += ":00"
    # 날짜만 있으면 자정으로
    if len(dt) == 10:  # YYYY-MM-DD
        dt += "T00:00:00"
    return dt

def calendar_add(title: str, start: str, end: str, description: str = "") -> str:
    """구글 캘린더에 일정을 추가한다. 추가 전 같은 시간대 중복 일정을 자동 확인한다.
    start/end 형식: 'YYYY-MM-DDTHH:MM' (예: '2026-03-20T09:00')"""
    try:
        service = _get_calendar_service()
        from datetime import timezone
        import dateutil.parser

        start_norm = _normalize_dt(start)
        end_norm   = _normalize_dt(end)

        # ── 중복 검사: 같은 시간대에 겹치는 일정 조회 ──────────────────────
        existing = service.events().list(
            calendarId="primary",
            timeMin=start_norm + "+09:00",
            timeMax=end_norm   + "+09:00",
            singleEvents=True,
            orderBy="startTime"
        ).execute().get("items", [])

        if existing:
            lines = [f"⚠️ [{start}~{end}] 시간대에 이미 일정이 있습니다:"]
            for e in existing:
                e_start = e["start"].get("dateTime", e["start"].get("date", ""))[:16]
                lines.append(f"  - [{e_start}] {e.get('summary', '(제목없음)')}  (id: {e['id']})")
            lines.append(f"\n그래도 '{title}' 일정을 추가하려면 calendar_add_force를 사용하세요.")
            return "\n".join(lines)

        # ── 중복 없음 → 추가 ────────────────────────────────────────────────
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


def calendar_add_force(title: str, start: str, end: str, description: str = "") -> str:
    """중복 확인 없이 구글 캘린더에 일정을 강제 추가한다. 중복 경고 후 사용자가 명시적으로 요청한 경우에만 사용."""
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

def calendar_update(event_id: str, title: str = "", start: str = "", end: str = "", description: str = "") -> str:
    """기존 일정을 수정한다. event_id는 calendar_list로 확인. 변경할 항목만 입력."""
    try:
        service = _get_calendar_service()
        event = service.events().get(calendarId="primary", eventId=event_id).execute()
        if title:       event["summary"] = title
        if description: event["description"] = description
        if start:       event["start"] = {"dateTime": _normalize_dt(start), "timeZone": "Asia/Seoul"}
        if end:         event["end"]   = {"dateTime": _normalize_dt(end),   "timeZone": "Asia/Seoul"}
        updated = service.events().update(calendarId="primary", eventId=event_id, body=event).execute()
        return f"✅ 일정 수정 완료: {updated.get('summary')} (id: {event_id})"
    except Exception as e:
        return f"Calendar Error: {e}"

def calendar_delete(event_id: str) -> str:
    """구글 캘린더 일정을 삭제한다. event_id는 calendar_list로 확인."""
    try:
        service = _get_calendar_service()
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        return f"✅ 일정 삭제 완료 (id: {event_id})"
    except Exception as e:
        return f"Calendar Error: {e}"

def check_errors() -> str:
    """온유_오류.md에서 최근 오류를 읽어 분석하고 원인과 조치를 제안한다."""
    log_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_오류.md")
    if not os.path.exists(log_path):
        return "✅ 기록된 오류 없음."
    try:
        content = Path(log_path).read_text(encoding="utf-8").strip()
        if not content:
            return "✅ 기록된 오류 없음."

        # 최근 10개 항목만 추출
        entries = content.split("\n## ")
        recent = "\n## ".join(entries[-10:])

        res = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=(
                f"다음은 온유 시스템 오류 로그다. 각 오류의 원인을 짧게 분석하고 "
                f"조치 방법을 제안하라. 한국어로, 항목별로 간결하게.\n\n{recent}"
            ),
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        return f"🔍 [오류 분석 리포트]\n\n{res.text}"
    except Exception as e:
        return f"Error: {e}"

def log_error_to_vault(context: str, error: str):
    """오류를 Obsidian SYSTEM/온유_오류.md에 날짜별로 누적 기록. 최대 50개 유지."""
    try:
        log_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_오류.md")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        entry = f"\n## {timestamp}\n- 상황: {context}\n- 오류: {error}\n"
        existing = ""
        if os.path.exists(log_path):
            with open(log_path, 'r', encoding='utf-8') as f:
                existing = f.read()
        # 최대 50개 항목 유지 (오래된 것부터 제거)
        entries = existing.split("\n## ")
        if len(entries) > 50:
            entries = entries[-50:]
            existing = "\n## ".join(entries)
        with open(log_path, 'w', encoding='utf-8') as f:
            f.write(existing + entry)
    except: pass

def report_status() -> str:
    """오늘의 API 사용량, 비용, 저장된 지식 수를 보고한다."""
    _, today, search_count = _get_search_count()
    data = {}
    if os.path.exists(USAGE_LOG_FILE):
        try:
            with open(USAGE_LOG_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
        except: pass
    embed_count  = data.get(today, 0)
    chat_count   = data.get(f"chat_{today}", 0)
    rag_count    = data.get(f"rag_{today}", 0)
    sum_count    = data.get(f"summary_{today}", 0)
    flow_count   = data.get(f"flowchart_{today}", 0)
    doc_count    = len(onew.mem.db) if 'onew' in globals() else '?'
    return (f"📊 [온유 오늘 API 사용 내역]\n"
            f"  대화(chat):    {chat_count}회\n"
            f"  RAG 검색:      {rag_count}회\n"
            f"  임베딩(sync):  {embed_count:,} / {MAX_DAILY_EMBED_CALLS:,}회\n"
            f"  자동 요약:     {sum_count}회\n"
            f"  순서도 생성:   {flow_count}회\n"
            f"  웹 검색:       {search_count} / {MAX_DAILY_SEARCHES}회\n"
            f"─────────────────────────────\n"
            f"  보존 지식:     {doc_count}개 문서\n"
            f"  학습 제외:     {', '.join(SYNC_EXCLUDE_DIRS)}")

def search_vault(query: str) -> str:
    """옵시디언 Vault(개인 노트/일기/공부자료)에서 키워드를 검색한다.
    인물, 날짜, 대화 내용, 공부 기록 등 개인 기록을 찾을 때 사용하라.
    웹 검색(analyze_trend)과 다르며, 인터넷 연결 없이 로컬 DB에서 검색한다.
    """
    if 'onew' not in globals():
        return "Error: 온유 에이전트가 초기화되지 않았습니다."
    agent = globals()['onew']

    # 시크릿(회사) 모드: 민감 키워드 포함 결과 필터링
    if agent.location_mode == "work":
        if any(kw in query for kw in SENSITIVE_KEYWORDS):
            return "🔒 [시크릿 모드] 이 주제는 집에서 검색하세요."

    results = agent.mem.search(query, k=10)
    if not results:
        return f"Vault에서 '{query}'와 관련된 기록을 찾지 못했습니다."

    lines = [f"🔍 Vault 검색 결과: '{query}'"]
    for i, r in enumerate(results, 1):
        text = r['text']
        # 시크릿 모드: 결과 텍스트 내 민감 키워드 포함 시 해당 항목 제외
        if agent.location_mode == "work" and any(kw in text for kw in SENSITIVE_KEYWORDS):
            continue
        lines.append(f"\n[{i}] 출처: {r['source']}")
        lines.append(text[:400])

    if len(lines) == 1:  # 헤더만 남은 경우
        return "🔒 [시크릿 모드] 해당 검색 결과에 민감한 내용이 포함되어 있어 표시할 수 없습니다."
    return "\n".join(lines)

def set_secret_mode(on: bool) -> str:
    """시크릿 모드를 켜거나 끈다. on=True면 민감 주제 차단, on=False면 해제."""
    if 'onew' in globals():
        globals()['onew'].set_secret_mode(on)
    mode = "ON" if on else "OFF"
    return f"✅ 시크릿 모드 {mode} 완료."

def get_secret_mode() -> str:
    """현재 시크릿 모드 상태와 설정 방식을 확인한다. (WiFi 자동감지 or 수동 오버라이드)"""
    config = {}
    if os.path.exists(LOCATION_CONFIG_FILE):
        try:
            with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                config = json.load(f)
        except:
            pass
    manual = config.get("manual_override")
    wifi_sec = _get_wifi_security()
    if manual is not None:
        mode = "ON (시크릿)" if manual else "OFF (일반)"
        return (f"🔒 시크릿 모드: {mode}\n"
                f"- 설정 방식: 수동 오버라이드\n"
                f"- WiFi 보안: {wifi_sec}\n"
                f"- 해제: '시크릿 자동' 입력 시 WiFi 자동감지로 복귀")
    else:
        if wifi_sec == "open":
            mode = "ON (시크릿) - 개방형 WiFi 감지"
        elif wifi_sec == "secured":
            mode = "OFF (일반) - 보안 WiFi 감지"
        else:
            mode = "OFF (일반) - WiFi 미감지, 기본값"
        return (f"🔍 시크릿 모드: {mode}\n"
                f"- 설정 방식: WiFi 자동감지\n"
                f"- 현재 WiFi 보안: {wifi_sec}\n"
                f"- 수동 변경: '시크릿 on' / '시크릿 off'")

def fetch_url_as_md(url: str, title: str = "") -> str:
    """URL의 웹 페이지 내용을 가져와 마크다운으로 변환하고 클리핑/ 폴더에 저장한다.
    - Anthropic 공홈(docs.anthropic.com, anthropic.com) → 클리핑/Anthropic/
    - Google 개발자 블로그(developers.googleblog.com) → 클리핑/Google/
    - 그 외 URL → 클리핑/
    url: 가져올 웹 페이지 주소
    title: 저장할 제목 (비워두면 페이지 <title> 자동 추출)"""
    import re as _re
    from html.parser import HTMLParser

    class _Extractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self._skip = False
            self._skip_tags = {'script', 'style', 'nav', 'footer', 'head', 'aside'}
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

    if not url.startswith(('http://', 'https://')):
        return f"❌ 유효하지 않은 URL: {url}"

    # URL 기반 출처/폴더 자동 결정 (요청 전에 계산)
    _domain = url.split('/')[2] if url.count('/') >= 2 else url
    if 'anthropic.com' in _domain:
        _subfolder, _source_tag, _source_label = 'Anthropic', 'Anthropic', 'Anthropic 공홈'
    elif 'developers.googleblog.com' in _domain or 'googleblog.com' in _domain:
        _subfolder, _source_tag, _source_label = 'Google', 'Google', 'Google Developers Blog'
    else:
        _subfolder, _source_tag, _source_label = '', '', _domain

    text = None

    # ① Jina Reader API 시도 (구조화된 마크다운 반환)
    try:
        _jina_req = urllib.request.Request(
            f"https://r.jina.ai/{url}",
            headers={'User-Agent': 'Mozilla/5.0 (compatible)', 'X-Return-Format': 'markdown'})
        with urllib.request.urlopen(_jina_req, timeout=20) as _r:
            _jina_md = _r.read().decode('utf-8', errors='ignore')
        # Jina 응답 헤더에서 제목 추출
        if not title:
            _m_t = _re.search(r'^Title:\s*(.+)$', _jina_md, _re.MULTILINE)
            if _m_t:
                title = _m_t.group(1).strip()
                title = _re.sub(r'\s*[-|]\s*(Anthropic|Google Developers Blog|Google).*$',
                                '', title, flags=_re.IGNORECASE).strip()
        # 메타 헤더 제거 후 본문만 사용
        text = _re.sub(r'^(Title|URL Source|Markdown Content):[^\n]*\n?', '',
                       _jina_md, flags=_re.MULTILINE).strip()[:8000]
    except Exception:
        pass

    # ② Jina 실패 시 기존 HTMLParser fallback
    if not text:
        try:
            _req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (compatible)'})
            with urllib.request.urlopen(_req, timeout=15) as _r:
                _charset = _r.headers.get_content_charset('utf-8')
                _html_raw = _r.read().decode(_charset, errors='ignore')
        except Exception as e:
            return f"❌ URL 접근 실패: {e}"
        if not title:
            _m = _re.search(r'<title[^>]*>(.*?)</title>', _html_raw, _re.IGNORECASE | _re.DOTALL)
            title = _re.sub(r'\s+', ' ', _m.group(1).strip()) if _m else url.split('/')[-1] or "untitled"
            title = _re.sub(r'\s*[-|]\s*(Anthropic|Google Developers Blog|Google).*$',
                            '', title, flags=_re.IGNORECASE).strip()
        _ext = _Extractor()
        _ext.feed(_html_raw)
        text = _re.sub(r'\n{3,}', '\n\n', '\n'.join(_ext.parts))[:8000]

    if not title:
        title = url.split('/')[-1] or "untitled"

    # 저장
    today = datetime.now().strftime('%Y-%m-%d')
    save_dir = os.path.join(CLIP_FOLDER, _subfolder) if _subfolder else CLIP_FOLDER
    os.makedirs(save_dir, exist_ok=True)
    safe_title = _re.sub(r'[\\/:*?"<>|]', '_', title)[:60]
    fpath = os.path.join(save_dir, f"{today}_{safe_title}.md")

    extra_tag = f", {_source_tag}" if _source_tag else ""
    md = (
        f"---\ntags: [클리핑{extra_tag}, {today}]\n"
        f"날짜: {today}\n원본: {url}\n출처: {_source_label}\n---\n\n"
        f"# {title}\n\n"
        f"> [!NOTE] 원본\n> {url}\n\n"
        f"{text}"
    )
    with open(fpath, 'w', encoding='utf-8') as f:
        f.write(md)

    rel = os.path.relpath(fpath, OBSIDIAN_VAULT_PATH)
    return f"✅ 저장 완료: {rel}  ({len(text):,}자)"


def analyze_image(filepath: str, question: str = "") -> str:
    """이미지 파일을 Gemini Vision으로 분석한다. question이 없으면 전체 내용을 설명한다."""
    import mimetypes
    try:
        p = Path(filepath).resolve()
        if not p.exists():
            # Vault 전체에서 파일명으로 탐색
            candidates = list(Path(OBSIDIAN_VAULT_PATH).rglob(p.name))
            if not candidates:
                return f"Error: 파일을 찾을 수 없습니다 ({filepath})"
            p = candidates[0]

        mime_type, _ = mimetypes.guess_type(str(p))
        if not mime_type or not mime_type.startswith("image/"):
            return "Error: 이미지 파일만 분석 가능합니다 (jpg, png, webp 등)"

        with open(p, "rb") as f:
            image_bytes = f.read()

        prompt = question if question else (
            "이 이미지의 내용을 한국어로 상세히 설명하라. "
            "텍스트가 있으면 전부 추출하고, 도표/수식/순서도가 있으면 구조화하여 정리하라."
        )

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                types.Part.from_bytes(data=image_bytes, mime_type=mime_type),
                prompt
            ]
        )
        _increment_usage("vision")
        return response.text.strip()
    except Exception as e:
        return f"Error: 이미지 분석 실패 ({e})"


# ==============================================================================
# [퀴즈 모드] 야간학습 → 실시간 퀴즈 출제
# ==============================================================================
QUIZ_HISTORY_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "quiz_history.json")
NIGHT_STUDY_DIR   = os.path.join(OBSIDIAN_VAULT_PATH, "야간학습")
QUIZ_COOLDOWN_DAYS = 3   # 같은 문제를 n일 내 재출제 방지

def _load_quiz_history() -> dict:
    """최근 출제된 문제 해시 목록 로드."""
    try:
        if os.path.exists(QUIZ_HISTORY_FILE):
            with open(QUIZ_HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except:
        pass
    return {"asked": []}   # {"asked": [{"hash": ..., "date": "YYYY-MM-DD"}, ...]}

def _save_quiz_history(h: dict):
    try:
        _atomic_json_write(QUIZ_HISTORY_FILE, h)
    except:
        pass

def _clean_latex(text: str) -> str:
    """LaTeX 수식을 읽기 쉬운 텍스트로 변환."""
    import re as _re
    t = text
    # \frac{a}{b} → (a)/(b)
    for _ in range(5):
        t = _re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", t)
    # \text{...} → 내용만
    t = _re.sub(r"\\text\{([^{}]+)\}", r"\1", t)
    # \mathrm{...} → 내용만
    t = _re.sub(r"\\mathrm\{([^{}]+)\}", r"\1", t)
    # ^{...} → 위첨자
    t = _re.sub(r"\^\{([^{}]+)\}", r"^\1", t)
    # _{...} → 아래첨자
    t = _re.sub(r"_\{([^{}]+)\}", r"_\1", t)
    # 특수 기호 치환
    replacements = [
        (r"\\approx",   "≈"),
        (r"\\times",    "×"),
        (r"\\cdot",     "·"),
        (r"\\circ",     "°"),
        (r"\\degree",   "°"),
        (r"\\Delta",    "Δ"),
        (r"\\delta",    "δ"),
        (r"\\alpha",    "α"),
        (r"\\beta",     "β"),
        (r"\\gamma",    "γ"),
        (r"\\eta",      "η"),
        (r"\\rho",      "ρ"),
        (r"\\mu",       "μ"),
        (r"\\sum",      "Σ"),
        (r"\\sqrt\{([^{}]+)\}", r"√(\1)"),
        (r"\\sqrt",     "√"),
        (r"\\geq",      "≥"),
        (r"\\leq",      "≤"),
        (r"\\neq",      "≠"),
        (r"\\infty",    "∞"),
        (r"\\left",     ""),
        (r"\\right",    ""),
        (r"\\\[",       ""),
        (r"\\\]",       ""),
        (r"\\\\",       " "),
    ]
    for pattern, repl in replacements:
        t = _re.sub(pattern, repl, t)
    # ^2 ^3 등 위첨자 숫자
    superscripts = {"0":"⁰","1":"¹","2":"²","3":"³","4":"⁴","5":"⁵","6":"⁶","7":"⁷","8":"⁸","9":"⁹"}
    def _sup(m):
        return "".join(superscripts.get(c, c) for c in m.group(1))
    t = _re.sub(r"\^(\d+)", _sup, t)
    # 인라인 수식 $...$ 감싸개 제거 (내용만 남김)
    t = _re.sub(r"\$\$(.+?)\$\$", r"\1", t, flags=_re.DOTALL)
    t = _re.sub(r"\$(.+?)\$", r"\1", t)
    # 남은 {} 제거
    t = _re.sub(r"[{}]", "", t)
    # 위키링크 [[A|B]] → B, [[A]] → A
    t = _re.sub(r"\[\[.+?\|(.+?)\]\]", r"\1", t)
    t = _re.sub(r"\[\[(.+?)\]\]", r"\1", t)
    # 마크다운 볼드 **..** 제거
    t = _re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    # ^° 잔여 정리 (\\circ 이후 ^ 남은 것)
    t = _re.sub(r"\^°", "°", t)
    t = _re.sub(r"\^(\s)", r"\1", t)   # 고립된 ^ 제거
    # 연속 공백 정리
    t = _re.sub(r"  +", " ", t).strip()
    return t

def _is_calc_heavy(question: str, answer: str) -> bool:
    """계산기가 필요한 수치 계산 문제 여부 판별."""
    import re as _re
    combined = question + " " + answer
    # LaTeX 수식이 2개 이상 있으면 계산 문제
    math_blocks = _re.findall(r"\$[^$]+\$", combined)
    if len(math_blocks) >= 2:
        return True
    # 계산 요구 키워드
    calc_keywords = ["계산하시오", "계산하라", "구하시오", "구하라", "값을 구", "수치를",
                     "몇 kW", "몇 kJ", "몇 W", "몇 kg", "몇 m", "몇 Pa", "몇 bar",
                     "계산 과정", "풀이 과정"]
    if any(kw in combined for kw in calc_keywords):
        return True
    # 숫자+단위 패턴이 3개 이상
    num_units = _re.findall(r"\d+[\.,]?\d*\s*(?:kW|kJ|W|kg|m²|m³|Pa|bar|°C|RPM|%|kcal)", combined)
    if len(num_units) >= 3:
        return True
    return False

def _question_hash(q_text: str) -> str:
    import hashlib
    return hashlib.md5(q_text.strip().encode("utf-8")).hexdigest()[:12]

def _parse_questions_from_file(fpath: str) -> list[dict]:
    """야간학습 .md 파일에서 문제/정답/해설 파싱.
    형식:
      1.  (문제) 실제 문제 텍스트
          정답: 정답 텍스트 (멀티라인 가능)
          해설: 해설 텍스트
    """
    questions = []
    try:
        text = Path(fpath).read_text(encoding="utf-8")
        # 노트 섹션별로 분리 (## 📝 기준)
        sections = re.split(r"\n## 📝 (.+)", text)
        # sections: [before_first, title1, body1, title2, body2, ...]
        pairs = []
        if len(sections) >= 3:
            for i in range(1, len(sections), 2):
                title = sections[i].strip()
                body  = sections[i+1] if i+1 < len(sections) else ""
                pairs.append((title, body))
        else:
            # 섹션 없으면 파일 전체를 하나로
            pairs.append((Path(fpath).stem, text))

        for source, body in pairs:
            # 개별 문제 블록 분리: 숫자. 로 시작하는 라인
            blocks = re.split(r"\n(?=\s*\d+[\.\)]\s+)", body)
            for block in blocks:
                # 문제 텍스트 추출 (숫자. (문제) ... 또는 숫자. ...)
                q_match = re.match(r"\s*\d+[\.\)]\s+(?:\(문제\)\s*)?(.+?)(?:\n|$)", block)
                if not q_match:
                    continue
                q_text = q_match.group(1).strip()
                # "(문제)" / "**문제)**" 등 접두사 잔여 제거
                q_text = re.sub(r"^\*?\*?\(문제\)\*?\*?\s*", "", q_text).strip()
                q_text = re.sub(r"^\*\*문제\)\*\*\s*", "", q_text).strip()
                if not q_text or q_text in ("(문제)", "**문제)**", ""):
                    continue

                # 정답: 이후 다음 구분선까지 멀티라인 수집
                a_match = re.search(r"정답\s*[:：]\s*(.+?)(?:\n\s*해설|---|\Z)", block, re.DOTALL)
                answer = ""
                if a_match:
                    answer = re.sub(r"\s+", " ", a_match.group(1)).strip()
                    answer = answer[:200]  # 너무 길면 잘라냄

                e_match = re.search(r"해설\s*[:：]\s*(.+?)(?:\n\s*\d+[\.\)]|---|\Z)", block, re.DOTALL)
                explain = ""
                if e_match:
                    explain = re.sub(r"\s+", " ", e_match.group(1)).strip()[:150]

                if not answer:
                    continue  # 정답 없는 블록 제외

                questions.append({
                    "question": q_text,
                    "answer":   answer,
                    "explain":  explain,
                    "source":   source,
                    "file":     fpath,
                })
    except:
        pass
    return questions

def quiz_me(category: str = None, count: int = 3, exclude_calc: bool = True, file_path: str = None) -> str:
    """야간학습에서 예상 문제를 가져와 퀴즈 세트를 반환합니다.
    category: '공조냉동' / '소방' / 'OCU' / 'AI클리핑' / '현장' / None(전체)
    count: 출제 문제 수 (기본 3, 최대 5)
    exclude_calc: True(기본) → 계산기 필요한 수치 계산 문제 제외
    file_path: 특정 Vault 파일 경로 지정 시 해당 파일 내용에서 직접 문제 추출
               (야간학습 폴더 무관 — 상대경로: Vault 기준, 절대경로 모두 허용)

    ⚠️ 반환된 문제+정답 세트를 활용 방법:
    - 사용자에게는 문제만 하나씩 보여주세요
    - 답변 후 정답과 해설을 공개하세요
    - 전체 끝나면 점수와 격려 메시지로 마무리하세요
    """
    import random

    count = min(max(1, count), 5)
    history = _load_quiz_history()
    cutoff  = (datetime.now() - timedelta(days=QUIZ_COOLDOWN_DAYS)).strftime("%Y-%m-%d")
    recent_hashes = {
        e["hash"] for e in history.get("asked", [])
        if e.get("date", "0000-00-00") >= cutoff
    }

    # ── 특정 파일 지정 모드 ──────────────────────────────────────────────────
    if file_path:
        # 상대경로면 Vault 기준으로 변환
        if not os.path.isabs(file_path):
            file_path = os.path.join(OBSIDIAN_VAULT_PATH, file_path)
        if not os.path.exists(file_path):
            return f"파일을 찾을 수 없습니다: {file_path}"
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return f"파일 읽기 실패: {e}"

        # 파일 내용에서 문제 직접 추출 (파싱 시도 → 없으면 헤더 기반 분할)
        all_questions = _parse_questions_from_file(file_path)
        if not all_questions:
            # 파싱 실패 시 ## 헤더 단위로 분할해 문제 형식으로 변환
            sections = re.split(r'\n#{1,3} ', content)
            all_questions = []
            for sec in sections[1:]:
                lines = sec.strip().splitlines()
                if not lines:
                    continue
                title = lines[0].strip()
                body  = '\n'.join(lines[1:]).strip()
                if len(body) < 10:
                    continue
                all_questions.append({
                    "question": title,
                    "answer": body[:300],
                    "explain": "",
                    "source": os.path.basename(file_path)
                })
        if not all_questions:
            return f"'{os.path.basename(file_path)}'에서 문제를 추출할 수 없습니다. 파일 내용을 확인하세요."

        for q in all_questions:
            q["question"] = _clean_latex(q["question"])
            q["answer"]   = _clean_latex(q["answer"])
            q["explain"]  = _clean_latex(q.get("explain", ""))

        fresh = [q for q in all_questions if _question_hash(q["question"]) not in recent_hashes]
        pool = fresh if len(fresh) >= count else all_questions
        selected = random.sample(pool, min(count, len(pool)))

        today = datetime.now().strftime("%Y-%m-%d")
        asked_list = history.get("asked", [])
        for q in selected:
            asked_list.append({"hash": _question_hash(q["question"]), "date": today})
        history["asked"] = asked_list[-500:]
        _save_quiz_history(history)

        lines = [f"📚 퀴즈 {len(selected)}문제 준비됨 (파일: {os.path.basename(file_path)})\n"]
        for i, q in enumerate(selected, 1):
            lines.append(
                f"[Q{i}]\n"
                f"문제: {q['question']}\n"
                f"정답: {q['answer']}\n"
                f"해설: {q.get('explain','')}\n"
                f"출처: {q['source']}\n"
            )
        lines.append("--- 퀴즈 진행 방법 ---")
        lines.append("각 문제를 하나씩 제시하고, 사용자가 답한 뒤 정답+해설 공개. 마지막에 총점 알림.")
        return "\n".join(lines)

    # ── 야간학습 폴더 모드 (기존) ────────────────────────────────────────────
    if not os.path.exists(NIGHT_STUDY_DIR):
        return "야간학습 폴더가 없습니다. 자율학습이 아직 실행되지 않았을 수 있습니다."

    # 야간학습 파일 수집 (카테고리 필터)
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

    # 전체 문제 파싱 + LaTeX 클리닝
    all_questions = []
    for fp in all_files:
        for q in _parse_questions_from_file(fp):
            q["question"] = _clean_latex(q["question"])
            q["answer"]   = _clean_latex(q["answer"])
            q["explain"]  = _clean_latex(q["explain"])
            all_questions.append(q)

    if not all_questions:
        return "야간학습 파일은 있으나 파싱 가능한 문제가 없습니다. 형식을 확인하세요."

    # 계산 문제 제외 (기본값)
    if exclude_calc:
        filtered = [q for q in all_questions if not _is_calc_heavy(q["question"], q["answer"])]
        # 필터 후 문제가 너무 적으면 전체 사용
        if len(filtered) >= count:
            all_questions = filtered
        else:
            # 계산 문제가 포함될 수 있음을 알림
            all_questions = filtered if filtered else all_questions

    # 쿨다운 제외 → 셔플 → count개 선택
    fresh = [q for q in all_questions if _question_hash(q["question"]) not in recent_hashes]
    # fresh가 부족하면 전체에서 보충
    pool = fresh if len(fresh) >= count else all_questions
    selected = random.sample(pool, min(count, len(pool)))

    # 출제 이력 기록
    today = datetime.now().strftime("%Y-%m-%d")
    asked_list = history.get("asked", [])
    for q in selected:
        asked_list.append({"hash": _question_hash(q["question"]), "date": today})
    history["asked"] = asked_list[-500:]   # 최근 500개 유지
    _save_quiz_history(history)

    # 반환 형식 — Onew가 문제/정답을 구분해 사용
    lines = [f"📚 퀴즈 {len(selected)}문제 준비됨 (카테고리: {category or '전체'})\n"]
    for i, q in enumerate(selected, 1):
        lines.append(
            f"[Q{i}]\n"
            f"문제: {q['question']}\n"
            f"정답: {q['answer']}\n"
            f"해설: {q['explain']}\n"
            f"출처: {q['source']}\n"
        )
    lines.append("--- 퀴즈 진행 방법 ---")
    lines.append("각 문제를 하나씩 제시하고, 사용자가 답한 뒤 정답+해설 공개. 마지막에 총점 알림.")
    return "\n".join(lines)


def load_skills_metadata() -> str:
    """SYSTEM/skills/ 폴더의 스킬 파일들에서 name과 description만 추출해 반환."""
    if not os.path.isdir(SKILLS_DIR):
        return ""
    lines = ["[스킬 목록 — 요청이 description과 일치하면 read_file로 해당 스킬 파일을 로드하고 지침을 따르세요]"]
    for fname in sorted(os.listdir(SKILLS_DIR)):
        if not fname.endswith(".md"):
            continue
        fpath = os.path.join(SKILLS_DIR, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                name, description = "", ""
                for line in f:
                    line = line.strip()
                    if line.startswith("name:"):
                        name = line.split(":", 1)[1].strip()
                    elif line.startswith("description:"):
                        description = line.split(":", 1)[1].strip()
                    if name and description:
                        break
            if name and description:
                lines.append(f"- {name}: {description}  →  SYSTEM/skills/{fname}")
        except:
            pass
    return "\n".join(lines) if len(lines) > 1 else ""


def create_working_memory(task_name: str) -> str:
    """복잡한 작업 시작 전 Plan.md, Context.md, Checklist.md 3개 파일을 working_memory 폴더에 생성합니다.

    Args:
        task_name: 작업 이름 (예: "obsidian_agent 리팩토링")
    """
    os.makedirs(WORKING_MEMORY_DIR, exist_ok=True)
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    safe_name = task_name.replace("/", "_").replace("\\", "_")[:40]

    plan_content = f"""---
tags: [작업기억, 계획서]
날짜: {datetime.now().strftime("%Y-%m-%d")}
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
날짜: {datetime.now().strftime("%Y-%m-%d")}
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
날짜: {datetime.now().strftime("%Y-%m-%d")}
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
        (f"{safe_name}_Plan.md", plan_content),
        (f"{safe_name}_Context.md", context_content),
        (f"{safe_name}_Checklist.md", checklist_content),
    ]:
        fpath = os.path.join(WORKING_MEMORY_DIR, fname)
        try:
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(content)
            results.append(f"✅ {fname}")
        except Exception as e:
            results.append(f"❌ {fname}: {e}")

    return "📋 작업 기억 파일 생성 완료:\n" + "\n".join(results) + f"\n경로: SYSTEM/working_memory/"


# 온유가 사용할 수 있는 권한 목록
tool_map = {
    "read_file": read_file,
    "write_file": write_file,
    "edit_file": edit_file,
    "create_folder": create_folder,
    "list_files": list_files,
    "move_file": move_file,
    "delete_file": delete_file,
    "execute_script": execute_script,
    "run_shell_command": run_shell_command,
    "browse_web": browse_web,
    "rollback_file": rollback_file,
    "backup_system": backup_system,
    "code_safety_check": code_safety_check,
    "save_code_checksums": save_code_checksums,
    "analyze_trend": analyze_trend,
    "calendar_list": calendar_list,
    "calendar_add": calendar_add,
    "calendar_add_force": calendar_add_force,
    "calendar_update": calendar_update,
    "calendar_delete": calendar_delete,
    "check_errors": check_errors,
    "report_status": report_status,
    "get_secret_mode": get_secret_mode,
    "set_secret_mode": set_secret_mode,
    "search_vault": search_vault,
    "clip_status": clip_status,
    "get_clip_topics": get_clip_topics,
    "set_clip_config": set_clip_config,
    "set_weekly_clip": set_weekly_clip,
    "task_create":  __import__('onew_task_manager').task_create,
    "task_list":    __import__('onew_task_manager').task_list,
    "task_update":  __import__('onew_task_manager').task_update,
    "task_next":    __import__('onew_task_manager').task_next,
    "task_cancel":  __import__('onew_task_manager').task_cancel,
    "analyze_image": analyze_image,
    "fetch_url_as_md": fetch_url_as_md,
    "quiz_me": quiz_me,
    "create_working_memory": create_working_memory,
}
onew_tools = [
    read_file, write_file, edit_file, create_folder, list_files, move_file, delete_file,
    execute_script, run_shell_command, browse_web, rollback_file, backup_system, code_safety_check, save_code_checksums, analyze_trend,
    calendar_list, calendar_add, calendar_add_force, calendar_update, calendar_delete,
    check_errors, report_status, get_secret_mode, set_secret_mode,
    search_vault, clip_status, get_clip_topics, set_clip_config, set_weekly_clip,
    fetch_url_as_md, analyze_image,
    quiz_me, create_working_memory,
] + [
    __import__('onew_task_manager').task_create,
    __import__('onew_task_manager').task_list,
    __import__('onew_task_manager').task_update,
    __import__('onew_task_manager').task_next,
    __import__('onew_task_manager').task_cancel,
]

# ==============================================================================
# [3. 온유 본체]
# ==============================================================================
class OnewAgent:
    def __init__(self, location_mode: str = None):
        self.mem = OnewPureMemory()
        self.history_records = []

        # 위치 모드 감지 (외부에서 지정 시 그대로 사용 → 이중 세션 생성 방지)
        self.location_mode = location_mode if location_mode else detect_location_mode()

        # Lv.2+3: 재실행 시 직전 세션 + 최근 3일 요약 자동 주입
        print("📖 [맥락 복원] 직전 세션 및 최근 기록 로딩 중...")
        prev_summary = self._summarize_last_session()
        recent_summaries = self._load_recent_summaries(days=3)
        combined = ""
        if recent_summaries:
            combined += f"[최근 3일 요약]\n{recent_summaries}"
        if prev_summary:
            combined += f"\n\n[직전 세션 요약]\n{prev_summary}"
        if combined:
            print("✅ [맥락 복원] 다일 맥락 주입 완료")
        self._new_chat_session(prev_summary=combined)

    def _save_history_to_vault(self):
        try:
            # 월별 폴더로 정리 (삭제 없이 보존)
            month_dir = os.path.join(OBSIDIAN_VAULT_PATH, "대화기록",
                                     datetime.now().strftime("%Y-%m"))
            os.makedirs(month_dir, exist_ok=True)
            timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
            save_path = os.path.join(month_dir, f"{timestamp}_온유_대화.md")

            now = datetime.now()
            lines = [
                f"---",
                f"tags: [대화기록, 온유]",
                f"날짜: {now.strftime('%Y-%m-%d')}",
                f"시간: {now.strftime('%H:%M')}",
                f"---",
                f"",
                f"# {timestamp} 온유 대화 기록",
                f"",
                f"**저장 시각:** {now.strftime('%Y년 %m월 %d일 %H시 %M분')}\n"
            ]

            for msg in self.history_records:
                role = "💬 용준" if msg["role"] == "user" else "💡 온유"
                lines.append(f"## {role}")
                lines.append(msg["text"].strip())
                lines.append("")

            with open(save_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(lines))
            print(f"💾 대화 기록 자동 저장 → {save_path}")

            # 학습 요약본 생성 → RAG 인덱싱 대상 폴더에 저장
            self._save_session_summary(now)
        except Exception as e:
            print(f"❌ 대화 기록 저장 실패: {e}")

    def _save_session_summary(self, now: datetime):
        """대화에서 학습한 내용 요약 → 대화요약/ 에 저장 (RAG 인덱싱 대상)"""
        try:
            if len(self.history_records) < 2:
                return
            convo = "\n".join(
                f"{'Q' if m['role']=='user' else 'A'}: {m['text'][:500]}"
                for m in self.history_records
            )
            prompt = (
                "다음 대화에서 용준이 학습하거나 이해한 핵심 내용만 요약하라.\n"
                "형식:\n"
                "- 학습 개념: (개념명)\n"
                "- 핵심 내용: (2~3줄)\n"
                "학습 내용이 없으면 '없음'만 출력.\n\n"
                f"대화:\n{convo[:3000]}"
            )
            summary = client.models.generate_content(
                model='gemini-2.5-flash', contents=prompt
            ).text.strip()

            if '없음' in summary and len(summary) < 10:
                return

            summary_dir = os.path.join(OBSIDIAN_VAULT_PATH, "대화요약")
            os.makedirs(summary_dir, exist_ok=True)
            day_path = os.path.join(summary_dir, f"{now.strftime('%Y-%m-%d')}_대화요약.md")

            block = (
                f"\n\n---\n\n"
                f"## {now.strftime('%H:%M')} 세션\n\n"
                f"{summary}"
            )
            if not os.path.exists(day_path):
                header = (
                    f"---\n"
                    f"tags: [대화요약, 학습기록, {now.strftime('%Y-%m-%d')}]\n"
                    f"날짜: {now.strftime('%Y-%m-%d')}\n"
                    f"---\n\n"
                    f"# 📘 {now.strftime('%Y-%m-%d')} 학습 요약\n"
                )
                with open(day_path, 'w', encoding='utf-8') as f:
                    f.write(header + block)
            else:
                with open(day_path, 'a', encoding='utf-8') as f:
                    f.write(block)
            print(f"📘 학습 요약 저장 → 대화요약/{now.strftime('%Y-%m-%d')}_대화요약.md")
            # Lv.4: 저장된 요약 파일 즉시 RAG 임베딩 (백그라운드)
            def _bg_embed(p):
                try:
                    self.mem.embed_single_file(p, silent=False)
                except:
                    pass
            threading.Thread(target=_bg_embed, args=(day_path,), daemon=True).start()
        except Exception as e:
            print(f"  (학습 요약 저장 실패: {e})")

    def _build_system_prompt(self) -> str:
        """위치 모드에 따라 시스템 프롬프트를 다르게 구성."""
        now = datetime.now()
        base = (
            f"현재 날짜와 시간: {now.strftime('%Y년 %m월 %d일 %H시 %M분')} (로컬 시스템 시간)\n\n"
            "당신은 고용준님의 완벽한 외부 뇌이자 바이브 코딩(Vibe Coding) 에이전트 '온유(Onew)'입니다. "
            "이제 당신은 컴퓨터의 파일을 직접 읽고 쓸 수 있는 권한(Tools)을 가집니다. "
            "사용자가 파일 수정이나 생성을 요청하면 즉시 도구를 사용하여 파일을 제어하세요. "
            "철저히 팩트 기반으로 답변하며, 감정적 위로보다 확실한 행동(결과물)으로 증명하세요.\n\n"
            "[주간 추적 클리핑 규칙]\n"
            "사용자가 '일주일마다 추적', '매주 모니터링', '주간 추적', '주 1회 클리핑' 등을 요청하면:\n"
            "1. 해당 주제를 5~10개의 세부 검색어로 분해한다\n"
            "2. set_weekly_clip(topics=[세부 주제 목록], action='add')를 호출한다\n"
            "3. '✅ 주간 추적 등록 완료. 매주 1회 클리핑됩니다.' 라고 안내한다\n"
            "제거 요청 시: set_weekly_clip(topics=[제거할 주제], action='remove')\n\n"
            "[태스크 관리 규칙]\n"
            "여러 단계가 필요한 작업은 반드시 task_create로 태스크를 생성하고 단계별로 실행하라.\n"
            "각 단계 완료 시 task_update로 상태를 갱신하라. 세션이 리셋돼도 태스크는 유지된다.\n"
            "새 세션 시작 시 task_next()로 이전에 중단된 작업을 먼저 확인하라.\n"
            "한 번에 끝낼 수 없는 작업(코드 리팩토링, 대량 파일 처리 등)은 반드시 태스크로 관리하라.\n\n"
            "[코드 롤백 규칙]\n"
            "Claude 리뷰에서 심각한 버그가 발견되거나 코드 수정 후 동작이 이상하면 즉시 rollback_file(filepath)을 호출하라.\n\n"
            "[과거 실패 사례 선조회 규칙]\n"
            "코드를 작성하거나 수정하기 전에 반드시 아래 절차를 따르라:\n"
            "1. search_vault('실패사례 코드교훈 {작업 내용 키워드}') 를 호출하여 관련 과거 실패 패턴을 확인한다\n"
            "2. 검색 결과에 관련 실패/교훈이 있으면 해당 내용을 반영하여 코드를 작성한다\n"
            "3. 결과가 없거나 무관하면 바로 진행해도 된다\n"
            "예시: write_file로 .md 생성 전 → search_vault('실패사례 write_file 파일생성')\n"
            "     edit_file로 .py 수정 전 → search_vault('코드교훈 edit_file 코드수정')\n"
            "이 규칙은 동일한 실수 반복을 방지하기 위한 것이다. 검색 결과를 무시하지 말 것.\n\n"
            "[코드 수정 규칙 — 반드시 준수]\n"
            "기존 .py 파일을 수정할 때는 반드시 edit_file 도구를 사용하라. write_file로 전체를 덮어쓰는 것은 금지.\n"
            "edit_file(filepath, old_str, new_str): old_str는 파일에서 유일한 문자열이어야 하며, 충분한 주변 코드를 포함해야 한다.\n"
            "새 파일 생성 시에만 write_file을 사용하라.\n\n"
            "[복잡한 작업 계획표 강제 규칙]\n"
            "아래 조건 중 하나라도 해당하면 반드시 작업 시작 전에 create_working_memory(task_name) 도구를 호출하라:\n"
            "  - 수정/생성할 파일이 3개 이상인 작업\n"
            "  - 코드 여러 곳을 연속으로 수정해야 하는 작업\n"
            "  - 단계가 4단계 이상인 절차적 작업\n"
            "  - 태스크(task_create)로 관리해야 할 만큼 긴 작업\n"
            "도구 호출 후 '📋 작업 기억 파일 생성 완료. 계획을 확인해 주세요.' 라고 안내하고 승인 받은 뒤 실행하라.\n"
            "단순 질문·파일 1~2개 수정·메모 저장 등 소규모 작업은 계획표 없이 바로 진행한다.\n\n"
            "[즉시 클리핑 요청 규칙]\n"
            "사용자가 '~로 클리핑 N개', '~에 대해 클리핑해줘', '~관련 클리핑' 등 특정 주제로 즉시 클리핑을 요청하면:\n"
            "1. 해당 주제를 N개의 구체적인 세부 주제로 직접 생성한다 (N 미지정 시 기본 10개)\n"
            "   예: '최신 경제 근황' → ['한국 경제 성장률 동향', '물가·인플레이션 현황', '금리 정책 변화', ...]\n"
            "2. set_clip_config(topics=[생성한 세부 주제 목록])으로 저장한다\n"
            "3. '✅ 주제 N개 설정 완료. 클리핑을 시작하려면 \"클리핑 시작\"이라고 말해주세요.' 라고 안내한다\n\n"
            "[클리핑 주제 자연어 수정 규칙]\n"
            "사용자가 클리핑 주제를 추가/삭제/교체하려는 자연어 요청을 하면 다음 절차를 따르라:\n"
            "1. get_clip_topics 도구로 현재 주제 목록을 가져온다\n"
            "2. 요청에 따라 목록을 수정한다 (추가: 끝에 append / 삭제: 해당 항목 제거 / 교체: 해당 항목 변경)\n"
            "3. set_clip_config(topics=[수정된 전체 목록])으로 저장한다\n"
            "4. '✅ 클리핑 주제 업데이트 완료. 현재 N개' 형식으로 알린다\n"
            "예시: '요리 레시피 빼줘', '클리핑에 제주 날씨 추가해', '5번 주제 삭제해', '공조냉동으로 바꿔줘'\n\n"
            "[퀴즈 모드 규칙]\n"
            "사용자가 '퀴즈', '문제 풀어', '시험 준비', '약점 문제', '연습 문제', '공부하자', '테스트해줘', '문제 내줘', '퀴즈 내줘' 등을 말하면:\n"
            "⚠️ 예외: '계산', '공식', '풀이 순서', '어떻게 계산해' 등 계산 문제 풀이 요청은 퀴즈 모드 대신 hvac_solver 스킬을 우선 적용하라.\n"
            "1. quiz_me(category=관련_카테고리, count=3, exclude_calc=True) 를 즉시 호출하라\n"
            "   ⚠️ category 값은 아래 실제 폴더명과 정확히 일치해야 한다 (오타/부분명 금지):\n"
            "   - 공조냉동/냉동기사 관련 → category='공조냉동'\n"
            "   - OCU/소방/방재 관련 → category='소방'\n"
            "   - 현장/소각 관련 → category='현장'\n"
            "   - AI 뉴스/클리핑 관련 → category='AI클리핑'\n"
            "   - 언급 없으면 → category=None (전체)\n"
            "   - 사용자가 '계산 문제 포함해줘' 라고 하면 exclude_calc=False 로 호출\n"
            "2. 도구 반환값에서 문제를 하나씩 꺼내 사용자에게 제시한다. 정답은 절대 먼저 보여주지 않는다.\n"
            "   예시: '📝 1번 문제입니다!\n\n{문제 내용}\n\n답변해 보세요 💪'\n"
            "3. 사용자가 답하면:\n"
            "   - 맞으면: '✅ 정답! {정답}\\n💡 {해설}'\n"
            "   - 틀리면: '❌ 아쉽네요. 정답은 {정답}입니다.\\n💡 {해설}'\n"
            "   - 모르면(모르겠어/패스/다음): '💡 정답은 {정답}\\n{해설}'\n"
            "4. 다음 문제로 넘어갈 때 '다음 문제 준비됐나요? 😊' 한 마디 추가\n"
            "5. 전체 완료 시: '🎯 {맞힌수}/{전체수} 정답!\\n{격려 메시지}' 로 마무리\n"
            "6. 퀴즈 도중 사용자가 '그만', '종료', '스톱' 이라고 하면 즉시 중단하고 중간 점수 알림\n\n"
            "[AI 생성 파일 태그 규칙]\n"
            "write_file 도구로 .md 파일을 새로 생성할 때는 반드시 YAML 프론트매터에 'author: Onew'와 '출처' 필드를 포함해야 한다.\n"
            "예시:\n"
            "---\n"
            "tags: []\n"
            "날짜: YYYY-MM-DD\n"
            "author: Onew\n"
            "출처: Vault RAG\n"
            "---\n"
            "이 규칙은 예외 없이 온유가 생성하는 모든 .md 파일에 적용된다. (사용자가 직접 작성한 파일에는 적용하지 않는다)\n\n"
            "[정보 출처 명시 규칙]\n"
            "파일을 생성하거나 정보를 제공할 때 반드시 출처를 명시하라. 출처 유형은 4가지다:\n"
            "  - 'Vault RAG'    : search_vault() 검색 결과 기반\n"
            "  - '웹검색'       : analyze_trend() 검색 결과 기반\n"
            "  - 'AI 생성'      : Gemini 자체 지식 기반 (환각 가능성 있음 — 반드시 ⚠️ 표시)\n"
            "  - '사용자 제공'  : 사용자가 직접 입력/첨부한 내용 기반\n"
            "복합 출처(예: Vault + 웹검색 혼합)는 'Vault RAG + 웹검색'처럼 모두 표기한다.\n"
            "YAML 출처 필드: 파일 생성 시 위 4가지 중 해당하는 값을 'Vault RAG', '웹검색', 'AI 생성', '사용자 제공'으로 입력.\n"
            "본문 출처 표기: 정보를 서술할 때 문장 끝 또는 섹션 끝에 `[출처: 웹검색]` 형태로 인라인 표기.\n"
            "⚠️ 특히 'AI 생성' 출처는 반드시 본문에 '⚠️ AI 생성 내용 — 사실 확인 권장' 경고 문구를 포함하라.\n\n"
            "[모호한 질문 되묻기 규칙]\n"
            "사용자 메시지에 '그거', '그것', '아까', '저번에', '그때', '이전에', '그 방법', '그 파일', '거기', '그 사람' 등 "
            "지시어나 모호한 표현이 포함되어 있고, 대화 맥락만으로 무엇을 가리키는지 확실하지 않을 때:\n"
            "1. 추측으로 답하지 말고 먼저 한 줄로 되물어라. 예: '아까 말씀하신 냉동기 문제를 말씀하시는 건가요?'\n"
            "2. 되물을 때는 가장 가능성 높은 대상을 1~2개만 제시하고 짧게 끝낸다.\n"
            "3. 맥락에서 명확히 알 수 있으면 되묻지 않고 바로 답한다.\n\n"
            "[보완사항 자동 저장 및 실행 규칙]\n"
            "사용자가 '보완', '보완 메모', '보완 필요', '보완해줘', '보완 사항', '개선 필요', '개선 메모' 등 "
            "보완/개선을 기록해달라는 자연어 요청을 하면 다음 절차를 즉시 실행하라:\n\n"
            "0. 중복 확인 (필수): 새 파일 저장 전에 search_vault('보완사항')로 기존 보완사항 파일을 확인하라.\n"
            "   - 오늘 날짜 파일(YYYY-MM-DD_*)이 이미 존재하면: 새 파일 생성 대신 기존 파일에 항목을 append하라.\n"
            "   - 동일하거나 매우 유사한 항목이 이미 기록된 경우: 중복이라고 알리고 추가하지 않는다.\n"
            "   - 기존 파일이 없거나 오늘 날짜 파일이 없으면: 새 파일을 생성하라.\n\n"
            "1. 각 보완 항목을 두 유형으로 분류하라:\n"
            "   [A유형 - 온유 직접 처리] 지식 보완, Vault 파일 수정, 사실 기록, 정보 추가 등 대화/도구로 해결 가능한 것\n"
            "   [B유형 - 코드 수정 필요] obsidian_agent.py 등 시스템 코드 변경이 필요한 것 → Claude Code에게 위임\n\n"
            "2. write_file 도구로 아래 형식의 파일을 '보완사항/YYYY-MM-DD_HH-MM_보완사항_점검.md'로 저장\n"
            "   파일 형식:\n"
            "   ---\n"
            "   tags: [보완사항, 점검, <관련 키워드>]\n"
            "   날짜: YYYY-MM-DD\n"
            "   시간: HH:MM\n"
            "   ---\n"
            "   # YYYY-MM-DD HH:MM 보완사항\n\n"
            "   ## 요청 내용\n"
            "   (사용자가 말한 내용 그대로)\n\n"
            "   ## [A유형] 온유 직접 처리 항목\n"
            "   - 항목 (처리 방법: 어떤 도구/파일에 어떻게 반영할지)\n\n"
            "   ## [B유형] 코드 수정 필요 항목\n"
            "   - 항목 (수정 위치: 어느 파일 몇 번째 기능인지)\n\n"
            "   ## 우선순위\n"
            "   높음/보통/낮음 + 이유\n\n"
            "3. 저장 완료 후 대화창에 요약 보고:\n"
            "   💾 보완사항 저장 완료 → {경로}\n\n"
            "   **[A유형] 온유가 지금 바로 처리:**\n"
            "   - 항목1 → 처리 방법\n"
            "   **[B유형] Claude Code에게 요청 필요:**\n"
            "   - 항목1 → 수정 위치\n"
            "   **우선순위:** 높음/보통/낮음\n\n"
            "※ 파일 저장은 반드시 write_file 도구를 실제로 호출해야 한다. 내용을 출력만 하고 저장했다고 말하는 것은 절대 금지.\n"
            "   저장 성공 여부는 도구 호출 결과로만 판단하라. 실패 시 이유를 사용자에게 명확히 알려라.\n\n"
            "4. A유형 항목은 보고 직후 즉시 실행하라:\n"
            "   - Vault 파일에 사실 추가 → write_file 또는 edit_file 사용\n"
            "   - 정보 검색 필요 → search_vault 사용 후 결과를 파일에 반영\n"
            "   - 완료 후 '✅ A유형 처리 완료: {항목}' 형식으로 알려라\n"
            "   B유형은 처리하지 말고 사용자에게 'Claude Code에게 요청하세요'라고만 안내하라."
        )
        if self.location_mode == "work":
            base += (
                "\n\n[회사 모드 활성화] "
                "현재 회사 네트워크에서 접속 중입니다. "
                "공부(공조냉동, OCU), 업무, 코딩, 일정 관련 대화만 응답하세요. "
                "양악·수술·산재·우울·감정·심리 등 사적인 내면 주제가 명확히 포함된 경우에만 "
                "'이 주제는 집에서 이야기해요.' 한 문장으로만 안내하고 응답을 거절하세요. "
                "⚠️ 반복 금지: 같은 세션에서 이미 한 번 거절한 주제가 다시 나와도 "
                "'아까 말씀드렸듯 집에서 이야기해요.' 한 줄로만 끝내라. "
                "일반 대화·공부 질문 중에는 이 문구를 절대 삽입하지 마라. "
                "조금이라도 공부/업무 연관성이 있으면 거절하지 말고 그냥 답하라."
            )
        return base

    def _check_unfinished_tasks(self) -> str:
        """WORKING_MEMORY_DIR에서 미완료 체크리스트를 감지하여 재개 프롬프트 반환."""
        if not os.path.exists(WORKING_MEMORY_DIR):
            return ""
        try:
            files = os.listdir(WORKING_MEMORY_DIR)
        except:
            return ""

        unfinished = []
        for fname in sorted(files):
            if not fname.endswith("_Checklist.md"):
                continue
            fpath = os.path.join(WORKING_MEMORY_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read()
                # 미완료 항목 감지: "- [ ]" 또는 "N. [ ]" 또는 체크박스 없는 번호목록
                def _has_incomplete(text: str) -> bool:
                    for line in text.splitlines():
                        s = line.strip()
                        if s.startswith("- [ ]"):
                            return True
                        if re.match(r'^\d+\.\s+\[[ ]\]', s):  # "1. [ ]" 형식
                            return True
                        if re.match(r'^\d+\.\s+\*\*', s):  # "1. **항목**" 번호목록 (체크박스 없음)
                            return True
                    return False

                def _get_incomplete_lines(text: str) -> list:
                    result_lines = []
                    for line in text.splitlines():
                        s = line.strip()
                        if s.startswith("- [ ]"):
                            result_lines.append(s)
                        elif re.match(r'^\d+\.\s+\[[ ]\]', s):
                            result_lines.append(s)
                        elif re.match(r'^\d+\.\s+\*\*', s):
                            result_lines.append(s)
                    return result_lines

                if not _has_incomplete(content):
                    continue  # 미완료 항목 없음
                task_name = fname.replace("_Checklist.md", "")
                plan_path = os.path.join(WORKING_MEMORY_DIR, f"{task_name}_Plan.md")
                plan_content = ""
                if os.path.exists(plan_path):
                    with open(plan_path, "r", encoding="utf-8") as f:
                        plan_content = f.read()
                unfinished.append({
                    "task": task_name,
                    "checklist": content,
                    "plan": plan_content,
                    "incomplete_lines": _get_incomplete_lines(content),
                })
            except:
                continue

        if not unfinished:
            return ""

        result = "\n\n[⚠️ 미완료 작업 감지 — 세션 재개 필요]\n"
        result += "이전 세션에서 완료되지 않은 작업이 있다. 세션 시작 시 사용자에게 먼저 안내하고 재개 여부를 물어라.\n"
        for u in unfinished:
            result += f"\n### 미완료 작업: {u['task']}\n"
            incomplete = u["incomplete_lines"]
            result += f"남은 항목 ({len(incomplete)}개):\n"
            for item in incomplete[:5]:  # 토큰 절약: 최대 5개만
                result += f"  {item.strip()}\n"
            if u["plan"]:
                plan_preview = "\n".join(u["plan"].splitlines()[:15])
                result += f"\n계획서 미리보기:\n{plan_preview}\n"
        result += "\n재개 시: 해당 *_Plan.md 와 *_Checklist.md 를 read_file로 로드하여 남은 단계부터 진행하라."
        return result

    def _new_chat_session(self, prev_summary: str = ""):
        """채팅 세션만 초기화 (메모리 DB는 유지). 이전 맥락 요약 주입 가능."""
        prompt = self._build_system_prompt()
        if prev_summary:
            prompt += f"\n\n[이전 대화 맥락]: {prev_summary}"
        # 엔티티 워킹메모리 주입
        entities = self._load_entities()
        if entities:
            entity_lines = "\n".join(
                f"- [{e['type']}] {e['value']}" for e in entities[-15:]
            )
            prompt += f"\n\n[대화 중 언급된 핵심 항목 — 지시어 해석 시 우선 참조]\n{entity_lines}"
        if os.path.exists(SYSTEM_PROMPT_PATH):
            try:
                with open(SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
                    prompt += "\n\n" + f.read()
            except: pass
        if os.path.exists(ANTIPATTERNS_PATH):
            try:
                with open(ANTIPATTERNS_PATH, "r", encoding="utf-8") as f:
                    content = f.read()
                    # 최대 15개 항목만 유효 — 파일 크기 제한 (4KB 초과 시 경고)
                    if len(content) < 4096:
                        prompt += "\n\n" + content
            except: pass
        skills_meta = load_skills_metadata()
        if skills_meta:
            prompt += "\n\n" + skills_meta
        unfinished_prompt = self._check_unfinished_tasks()
        if unfinished_prompt:
            prompt += unfinished_prompt
        self.chat = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=prompt,
                tools=onew_tools,
                temperature=0.2,
                thinking_config=types.ThinkingConfig(thinking_budget=0),
                automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
            )
        )

    def set_secret_mode(self, on: bool):
        """시크릿 모드를 수동으로 설정하고 onew_location.json에 저장."""
        config = {}
        if os.path.exists(LOCATION_CONFIG_FILE):
            try:
                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        config["manual_override"] = on
        with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.location_mode = "work" if on else "home"
        self._new_chat_session()
        if on:
            print("🔒 [시크릿 모드 ON] 개인·민감 주제가 차단됩니다. '시크릿 off'로 해제 가능.")
        else:
            print("🔓 [시크릿 모드 OFF] 모든 대화 가능합니다. '시크릿 on'으로 재설정 가능.")

    def clear_secret_override(self):
        """수동 오버라이드를 제거 → 이후 WiFi 자동 감지로 복귀."""
        config = {}
        if os.path.exists(LOCATION_CONFIG_FILE):
            try:
                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
            except:
                pass
        config.pop("manual_override", None)
        with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        self.location_mode = detect_location_mode()
        self._new_chat_session()
        mode_str = "시크릿 ON (개방형 WiFi)" if self.location_mode == "work" else "시크릿 OFF (보안 WiFi)"
        print(f"🔄 [자동 감지 복귀] 현재 모드: {mode_str}")

    def _classify_session(self, content: str) -> str:
        """대화 내용을 '휘발성' 또는 '장기'로 분류.
        - 휘발성: 일상 잡담, 단순 질문, 검색 1회성 응답
        - 장기: 학습 내용, 결정 사항, 파일 수정, 태스크, 계획
        턴이 4개 미만이면 분류 생략 (API 절약).
        """
        try:
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=(
                    "아래 대화의 유형을 판단하라. 딱 한 단어만 답하라: 'volatile' 또는 'long'\n"
                    "volatile: 순수 일상 잡담, 단순 인사, 1회성 검색으로만 이루어진 대화\n"
                    "long: 학습 내용, 결정 사항, 파일 수정/생성, 태스크 관리, 계획, 코드 작업,\n"
                    "      날짜/일정/인물/장소 언급, 건강·수술·산재·복직 관련, 감정적으로 중요한 사안\n"
                    "판단이 애매하면 'long'으로 답하라.\n\n"
                    f"{content[:1500]}"
                ),
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0))
            )
            label = res.text.strip().lower()
            return 'long' if 'long' in label else 'volatile'
        except:
            return 'long'  # 오류 시 안전하게 장기로 분류

    def _summarize_last_session(self) -> str:
        """저장된 마지막 대화 파일을 읽어 요약 반환.
        휘발성 대화는 요약 생략 → 세션 리셋 시 맥락 주입 안 함 (API 절약).
        """
        try:
            month_dir = os.path.join(OBSIDIAN_VAULT_PATH, "대화기록",
                                     datetime.now().strftime("%Y-%m"))
            files = sorted(Path(month_dir).glob("*_온유_대화.md"))
            if not files:
                return ""
            content = files[-1].read_text(encoding="utf-8")[:3000]

            # 휘발성 분류 → 요약 생략
            session_type = self._classify_session(content)
            if session_type == 'volatile':
                print("💨 [대화 분류] 휘발성 세션 → 요약 생략")
                return ""

            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=f"다음 대화를 5문장 이내로 핵심 주제·결정·미완료 사항을 포함하여 요약하라. 한국어로.\n\n{content}",
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0))
            )
            return res.text.strip()
        except:
            return ""

    def _load_recent_summaries(self, days: int = 3) -> str:
        """최근 N일치 대화요약 파일을 읽어 다일 맥락 문자열 반환 (API 호출 없음)."""
        summary_dir = os.path.join(OBSIDIAN_VAULT_PATH, "대화요약")
        if not os.path.exists(summary_dir):
            return ""
        today = datetime.now().date()
        blocks = []
        for i in range(1, days + 1):  # 어제부터 N일 전까지 (오늘 제외)
            target = today - timedelta(days=i)
            fpath = os.path.join(summary_dir, f"{target}_대화요약.md")
            if not os.path.exists(fpath):
                continue
            try:
                text = Path(fpath).read_text(encoding="utf-8")
                # YAML 프론트매터 제거
                if text.startswith("---"):
                    end = text.find("---", 3)
                    if end != -1:
                        text = text[end + 3:].strip()
                # 너무 길면 앞부분만 (토큰 절약)
                blocks.append(f"[{target} 요약]\n{text[:800]}")
            except:
                continue
        if not blocks:
            return ""
        return "\n\n".join(blocks)

    def _load_entities(self) -> list:
        """저장된 엔티티 워킹메모리 로드."""
        try:
            if os.path.exists(ENTITY_MEMORY_FILE):
                with open(ENTITY_MEMORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return data.get("entities", [])
        except:
            pass
        return []

    def _save_entities(self, entities: list):
        """엔티티 워킹메모리 저장."""
        try:
            _atomic_json_write(ENTITY_MEMORY_FILE, {
                "entities": entities[-50:],  # 최대 50개 유지
                "updated": datetime.now().strftime("%Y-%m-%d %H:%M")
            })
        except:
            pass

    def _extract_entities(self, query: str, answer: str):
        """대화에서 핵심 엔티티 추출 후 워킹메모리에 저장 (3턴마다 실행)."""
        turn = len(self.history_records)
        if turn % 6 != 0:  # 3 Q&A(6 레코드)마다 한 번
            return
        try:
            existing = self._load_entities()
            existing_vals = {e["value"] for e in existing}
            prompt = (
                f"아래 대화에서 나중에 참조될 수 있는 핵심 항목을 추출하라.\n"
                f"형식: 각 줄에 '유형|값' (유형: 주제/파일/결정/인물/장소/설비)\n"
                f"최대 5개, 짧게, 한국어로.\n"
                f"제외: 일상적인 감정 표현, 단순 인사, 1회성 잡담, 수면/휴식 관련 일반 언급은 추출하지 말 것.\n\n"
                f"사용자: {query[:300]}\n온유: {answer[:300]}"
            )
            res = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0))
            )
            now = datetime.now().strftime("%Y-%m-%d %H:%M")
            new_entities = []
            for line in res.text.strip().splitlines():
                if "|" in line:
                    parts = line.strip().split("|", 1)
                    if len(parts) == 2:
                        etype, val = parts[0].strip(), parts[1].strip()
                        if val and val not in existing_vals:
                            new_entities.append({"type": etype, "value": val, "at": now})
                            existing_vals.add(val)
            if new_entities:
                self._save_entities(existing + new_entities)
        except:
            pass

    def _reset_chat_if_needed(self):
        turn = len(self.history_records)

        # 10턴 초과 시 저장 + 세션 리셋 (기존 5턴 → 10턴, 맥락 유지 강화)
        if turn > 10:
            self._save_history_to_vault()
            print("💾 [자동저장] 대화 기록 저장됨")
            summary = self._summarize_last_session()
            # 마지막 12개 레코드(6 Q&A) 직접 보존 → 새 세션 맥락 주입용
            recent_pairs = self.history_records[-12:] if len(self.history_records) >= 12 else self.history_records[:]
            self.history_records = []
            # 최근 교환을 요약에 직접 첨부
            if recent_pairs:
                recent_str = "\n".join(
                    f"{'사용자' if r['role']=='user' else '온유'}: {r['text'][:300]}"
                    for r in recent_pairs
                )
                combined = (summary + "\n\n[직전 교환]\n" + recent_str) if summary else ("[직전 교환]\n" + recent_str)
            else:
                combined = summary
            self._new_chat_session(prev_summary=combined)
            if summary:
                print(f"✅ 새 세션 시작\n📝 [이전 맥락]: {summary}")
            else:
                print("✅ 새 세션 시작 (이전 대화는 저장되었습니다)")
            # 미완료 태스크 알림
            try:
                from onew_task_manager import get_pending_summary
                pending = get_pending_summary()
                if pending:
                    print(f"\n{pending}")
            except: pass

    def ask(self, query, silent_search=False):
        self._reset_chat_if_needed()

        # 대화 활동 시각 갱신 → 유휴 감지 기준으로 사용
        try:
            import onew_shared; onew_shared.touch()
        except ImportError:
            pass

        # ADHD 엔진: 메시지 타이밍 기록 (과집중 감지용) + 학습 의도 포착
        try:
            import onew_adhd as _adhd
            _adhd.on_user_message()
            _goal_msg = _adhd.detect_learning_goal(query)
            if _goal_msg:
                print(f"\n{_goal_msg}\n")
        except Exception:
            pass

        # 공부 완료 키워드 감지 → 스트릭 기록 + 즉각 피드백
        _study_done_kw = ["공부 완료", "공부 끝", "오늘 공부 다 했어", "다 풀었어", "문제 다 풀었어"]
        if any(kw in query for kw in _study_done_kw):
            try:
                import onew_adhd as _adhd
                print(f"\n{_adhd.record_study_done()}\n")
            except Exception:
                pass

        # 도파민 메뉴 요청 감지
        if any(kw in query for kw in ["도파민 메뉴", "뭐 하지", "지루해", "보상 뭐야"]):
            try:
                import onew_adhd as _adhd
                print(f"\n{_adhd.dopamine_menu()}\n")
            except Exception:
                pass

        # ADHD 현황 보고 요청
        if any(kw in query for kw in ["adhd 현황", "스트릭", "반응률", "공부 기록"]):
            try:
                import onew_adhd as _adhd
                print(f"\n{_adhd.adhd_status()}\n")
            except Exception:
                pass

        # 회사 모드: 민감 주제 클라이언트 측 차단 (API 호출 전에 막음)
        if self.location_mode == "work":
            if any(kw in query for kw in SENSITIVE_KEYWORDS):
                print("==================================================")
                print("💡 온유: 이 주제는 집에서 이야기해요.")
                print("   지금은 공부·업무·코딩 관련 대화만 할게요.")
                print("==================================================")
                return

        # [자율학습 1] 교정 키워드 감지 → 이전 Q&A 오답으로 저장
        if any(kw in query for kw in CORRECTION_KEYWORDS) and len(self.history_records) >= 2:
            prev_q = self.history_records[-2].get("text", "")
            prev_a = self.history_records[-1].get("text", "")
            _save_mistake(prev_q, prev_a, query)
            print("📝 [자율학습] 오답 패턴 기록됨 → 오답_패턴.md")

        if not silent_search:
            print(f"\n온유(Onew) 🔍 지식 네트워크 탐색 중...")

        # 1. RAG 기반 지식 검색 (지시어 감지 시 이전 대화로 쿼리 보강)
        search_query = query
        if any(ref in query for ref in VAGUE_REFS) and self.history_records:
            recent_ctx = " ".join(
                r["text"][:150] for r in self.history_records[-6:]
            )
            search_query = f"{query} {recent_ctx}"
            if not silent_search:
                print("🔗 [지시어 감지] 이전 대화 맥락으로 검색 보강")
        res = self.mem.search(search_query)
        ctx = ""
        source_list = "없음"
        if not res:
            if not silent_search: print("💡 관련된 기억을 찾지 못했습니다. 일반 지식과 Vibe 권한으로 응답합니다.")
        else:
            ctx = "\n".join([f"[출처: {r['source']}] (연결: {r['links']})\n{r['text']}" for r in res])
            source_list = ", ".join(list(set([r['source'] for r in res])))

        # ── 코드 작업 감지 시 실패사례/교훈 자동 주입 ─────────────────
        CODE_WRITE_TRIGGERS = [
            "파일 만들어", "만들어줘", "생성해줘", "작성해줘", "코드 작성",
            "write_file", "edit_file", "수정해줘", "고쳐줘", ".py", ".md 만",
        ]
        try:
            if any(kw in query for kw in CODE_WRITE_TRIGGERS):
                failure_res = self.mem.search("실패사례 코드교훈 " + query[:60], k=3)
                failure_ctx_parts = [
                    r['text'][:250] for r in failure_res
                    if any(tag in r.get('source', '') for tag in ['실패사례', '코드교훈', '오답_패턴'])
                ]
                if failure_ctx_parts:
                    failure_block = "\n".join(f"[과거교훈] {t}" for t in failure_ctx_parts)
                    ctx = failure_block + ("\n\n" + ctx if ctx else "")
                    if not silent_search:
                        print(f"🧠 [실패사례 선조회] {len(failure_ctx_parts)}건 컨텍스트 주입됨")
        except Exception:
            pass  # 선조회 실패 시 조용히 건너뜀 — ask() 전체에 영향 없음

        # 2. 질문 전송
        # 대화 하드스톱: 하루 500회 초과 시 차단 (루프 과금 방지)
        _today_chat_pre = _get_today_usage("chat")
        if _today_chat_pre >= 500:
            print("🔴 [과금 보호] 오늘 대화 API 500회 초과. 온유를 재시작하거나 내일 다시 사용하세요.")
            _send_telegram_notify(
                f"🔴 *온유 대화 한도 초과*\n\n"
                f"오늘 대화 API {_today_chat_pre}회 도달.\n"
                f"비정상 루프 가능성. 온유를 재시작하세요."
            )
            return

        try:
            ans = self.chat.send_message(f"Context:\n{ctx}\n\n명령: {query}")
            _increment_usage("chat")
            # chat 일일 과금 경고 (소프트 한도)
            _today_chat = _get_today_usage("chat")
            if _today_chat == MAX_DAILY_CHAT_WARN:
                _send_telegram_notify(
                    f"⚠️ [과금 경고] chat API 오늘 {_today_chat}회 도달.\n"
                    f"비정상적으로 많으면 온유를 재시작하세요."
                )
        except Exception as e:
            print(f"❌ API 호출 오류: {e}")
            log_error_to_vault("API 호출", str(e))
            return

        # 3. 🌟 Vibe Coding: 도구(Tool) 자동 실행 루프 (최대 10회)
        tool_loop_count = 0
        _error_counter: dict = {}   # {func_name + error_key: 횟수} — 동일 에러 3회 반복 시 강제 중단
        _self_fix_counter: dict = {}  # {filepath: 횟수} — execute_script 자가치유 시도 횟수
        _force_break = False
        while getattr(ans, 'function_calls', None) and tool_loop_count < 10 and not _force_break:
            tool_loop_count += 1
            tool_responses = []
            for call in ans.function_calls:
                func_name = call.name

                # 인자(args) 파싱 방어 로직
                if isinstance(call.args, dict): args_dict = call.args
                elif hasattr(call.args, "model_dump"): args_dict = call.args.model_dump()
                else: args_dict = {k: getattr(call.args, k) for k in dir(call.args) if not k.startswith('_')}

                target = args_dict.get('filepath') or args_dict.get('directory') or str(args_dict)
                if not silent_search:
                    print(f"🛠️ [Vibe Coding] 온유가 시스템을 제어합니다: [{func_name}] -> {target}")

                # 실제 함수 실행
                try:
                    if func_name in tool_map:
                        result = tool_map[func_name](**args_dict)
                    else:
                        result = f"Error: 존재하지 않는 기능입니다 ({func_name})"
                except Exception as e:
                    result = f"Error 실행 실패: {e}"
                    log_error_to_vault(f"Tool 실행: {func_name}", str(e))

                # ── 에러 반복 패턴 감지 ──────────────────────────────────────
                if isinstance(result, str) and result.startswith("Error"):
                    err_key = f"{func_name}|{result[:80]}"
                    _error_counter[err_key] = _error_counter.get(err_key, 0) + 1
                    if _error_counter[err_key] >= 3:
                        warn_msg = (
                            f"⚠️ [반복 에러 감지] '{func_name}' 동일 오류가 3회 반복되어 강제 중단합니다.\n"
                            f"오류 내용: {result[:200]}\n개입이 필요합니다."
                        )
                        print(warn_msg)
                        _send_telegram_notify(warn_msg)
                        log_error_to_vault(f"반복 에러 강제 중단: {func_name}", result[:200])
                        _save_code_lesson(func_name, result[:200], str(args_dict)[:150])
                        _force_break = True
                        result = warn_msg

                    # ── execute_script 자가치유 루프 ──────────────────────────
                    elif func_name == "execute_script":
                        _fp = args_dict.get("filepath", "unknown")
                        _self_fix_counter[_fp] = _self_fix_counter.get(_fp, 0) + 1
                        _fix_attempt = _self_fix_counter[_fp]
                        if _fix_attempt <= 2:
                            if not silent_search:
                                print(f"🔧 [자가치유 {_fix_attempt}/2] 에러 분석 후 수정 시도 중: {os.path.basename(_fp)}")
                            result = (
                                f"{result}\n\n"
                                f"[자가치유 지시 — {_fix_attempt}/2회차]\n"
                                f"위 에러를 분석하라. 원인을 파악했으면:\n"
                                f"- 코드 버그라면 edit_file로 '{_fp}' 수정 후 execute_script 재실행\n"
                                f"- 패키지 미설치(ModuleNotFoundError)라면 run_shell_command('pip install 패키지명') 후 execute_script 재실행\n"
                                f"사용자에게 묻지 말고 스스로 해결하라."
                            )
                        else:
                            warn_msg = (
                                f"⚠️ [자가치유 실패] '{os.path.basename(_fp)}' 3회 수정 시도 후에도 에러 지속.\n"
                                f"마지막 오류: {result[:300]}\n사용자 개입이 필요합니다."
                            )
                            print(warn_msg)
                            _send_telegram_notify(warn_msg)
                            log_error_to_vault(f"자가치유 실패: {_fp}", result[:300])
                            _save_code_lesson(func_name, result[:300], str(args_dict)[:150])
                            _force_break = True
                            result = warn_msg
                # ─────────────────────────────────────────────────────────────
                
                # 결과를 모델이 이해할 수 있게 패키징
                tool_responses.append(types.Part.from_function_response(
                    name=func_name,
                    response={"result": result}
                ))
            
            # 도구 실행 결과를 다시 모델에게 던져서 최종 텍스트 답변을 받아냄
            try:
                ans = self.chat.send_message(tool_responses)
                _increment_usage("chat")
            except Exception as e:
                if "INVALID_ARGUMENT" in str(e):
                    self._new_chat_session()
                    ans = self.chat.send_message(query)
                    _increment_usage("chat")
                else:
                    raise
        
        # 4. 최종 결과 출력 및 히스토리 저장
        # ans.text 대신 parts에서 직접 추출 → function_call 경고 방지
        try:
            parts = ans.candidates[0].content.parts
            texts = [p.text for p in parts if hasattr(p, 'text') and p.text]
            final_text = ' '.join(texts) if texts else "(파일 제어 작업이 완료되었습니다.)"
        except:
            final_text = (ans.text or "") if not getattr(ans, 'function_calls', None) else "(파일 제어 작업이 완료되었습니다.)"
        self.history_records.append({"role": "user", "text": query})
        self.history_records.append({"role": "model", "text": final_text})

        # [엔티티 추출] 3 Q&A마다 핵심 항목 워킹메모리 저장
        self._extract_entities(query, final_text)

        print(f"==================================================")
        print(f"💡 온유:\n{final_text}\n")
        if source_list != "없음":
            print(f"📚 참고자료: {source_list}")

        # [자율학습 3] 자기 평가 → 점수 낮으면 보완 검색 후 추가 답변
        score = _self_evaluate(query, final_text)
        if score < SELF_EVAL_MIN_SCORE:
            print(f"🔄 [자기 평가] {score}점 → 보완 검색 중...")
            supplement = self.mem.search(query, k=3)
            if supplement:
                supp_ctx = "\n".join([f"[{r['source']}] {r['text']}" for r in supplement])
                try:
                    supp_ans = self.chat.send_message(
                        f"앞의 답변을 보완하라. 추가 자료:\n{supp_ctx}\n\n원래 질문: {query}")
                    _increment_usage("chat")
                    if supp_ans.text:
                        print(f"💡 [보완]:\n{supp_ans.text}\n")
                        self.history_records[-1]["text"] += "\n\n[보완]\n" + supp_ans.text
                except: pass

        print(f"==================================================")

# ==============================================================================
# [TTS 모듈]
# ==============================================================================
TTS_MAX_CHARS = 500  # 너무 긴 답변은 앞부분만 읽음

def speak(text: str):
    """텍스트를 edge-tts(Microsoft 한국어 여성 신경망 음성)로 출력."""
    import asyncio, tempfile, subprocess

    async def _speak_async(clean_text):
        import edge_tts
        tmp = tempfile.NamedTemporaryFile(suffix='.mp3', delete=False,
                                          dir=os.environ.get('TEMP', '.'))
        tmp.close()
        try:
            c = edge_tts.Communicate(clean_text, voice='ko-KR-SunHiNeural')
            await c.save(tmp.name)
            duration_ms = max(2000, int(len(clean_text) / 4 * 1000) + 1000)
            uri = tmp.name.replace('\\', '/')
            ps_cmd = (
                f"Add-Type -AssemblyName PresentationCore; "
                f"$m=[System.Windows.Media.MediaPlayer]::new(); "
                f"$m.Open([uri]'file:///{uri}'); "
                f"$m.Play(); "
                f"Start-Sleep -Milliseconds {duration_ms}; "
                f"$m.Stop()"
            )
            subprocess.run(['powershell', '-c', ps_cmd],
                           capture_output=True, timeout=duration_ms // 1000 + 5)
        finally:
            try: os.unlink(tmp.name)
            except: pass

    try:
        clean = re.sub(r'[*#`>_\[\](){}<>|\\]', '', text)
        clean = re.sub(r'\n+', ' ', clean).strip()
        if len(clean) > TTS_MAX_CHARS:
            clean = clean[:TTS_MAX_CHARS] + ". 이하 생략."
        if not clean:
            return
        asyncio.run(_speak_async(clean))
    except Exception as e:
        print(f"⚠️ TTS 오류: {e}")


# ==============================================================================
# [음성 입력 모듈]
# ==============================================================================
VOICE_SAMPLE_RATE      = 16000   # whisper 권장 샘플레이트
VOICE_SILENCE_THRESHOLD = 0.008  # 침묵 판단 RMS 임계값
VOICE_SILENCE_DURATION  = 1.5    # 이 초 이상 침묵이면 녹음 종료
VOICE_MAX_DURATION      = 30     # 최대 녹음 시간 (초)

_whisper_model = None  # 최초 사용 시 로드

def _get_whisper_model():
    global _whisper_model
    if _whisper_model is None:
        print("🎤 음성인식 모델 로딩 중... (최초 1회)")
        import whisper
        _whisper_model = whisper.load_model("small")
        print("✅ 음성인식 준비 완료")
    return _whisper_model

def _record_until_silence() -> "np.ndarray | None":
    """마이크 입력 녹음. 침묵 감지 시 자동 종료."""
    import sounddevice as sd
    import numpy as np
    chunk_sec  = 0.1
    chunk_size = int(VOICE_SAMPLE_RATE * chunk_sec)
    need_silent_chunks = int(VOICE_SILENCE_DURATION / chunk_sec)
    max_chunks = int(VOICE_MAX_DURATION / chunk_sec)

    chunks = []
    silent_count = 0
    started = False

    print("🎤 듣는 중... (말씀 후 잠시 기다리면 자동 종료)")
    with sd.InputStream(samplerate=VOICE_SAMPLE_RATE, channels=1, dtype="float32") as stream:
        for _ in range(max_chunks):
            chunk, _ = stream.read(chunk_size)
            import numpy as np
            rms = float(np.sqrt(np.mean(chunk ** 2)))
            if rms > VOICE_SILENCE_THRESHOLD:
                started = True
                silent_count = 0
                chunks.append(chunk)
            elif started:
                chunks.append(chunk)
                silent_count += 1
                if silent_count >= need_silent_chunks:
                    break

    if not chunks:
        return None
    import numpy as np
    return np.concatenate(chunks, axis=0).flatten()

def voice_input() -> str:
    """음성 녹음 → 텍스트 변환. 실패 시 빈 문자열 반환."""
    try:
        import numpy as np
        audio = _record_until_silence()
        if audio is None or len(audio) < VOICE_SAMPLE_RATE * 0.3:
            print("⚠️ 음성이 감지되지 않았습니다.")
            return ""
        print("🔄 변환 중...")
        model = _get_whisper_model()
        result = model.transcribe(audio, language="ko", fp16=False)
        text = result["text"].strip()
        if text:
            print(f"📝 인식: {text}")
        return text
    except Exception as e:
        print(f"⚠️ 음성인식 오류: {e}")
        return ""

# ==============================================================================
# [웨이크워드 모듈] "온유야" 호출 시 음성 입력 활성화
# ==============================================================================
VOICE_PROFILE_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "voice_profile.npy")

def _extract_mfcc(audio: "np.ndarray", sr: int = 16000) -> "np.ndarray":
    """librosa로 MFCC 40차 추출 → 평균 벡터 반환."""
    import librosa
    mfcc = librosa.feature.mfcc(y=audio.astype(float), sr=sr, n_mfcc=40)
    return mfcc.mean(axis=1)

def _cosine_similarity(a: "np.ndarray", b: "np.ndarray") -> float:
    import numpy as np
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    return float(np.dot(a, b) / denom) if denom > 0 else 0.0

def enroll_voice(seconds: int = 10) -> str:
    """용준님 목소리 등록 (10초 녹음 → MFCC 성문 저장)."""
    import sounddevice as sd
    import numpy as np
    print(f"🎤 목소리 등록 시작 — {seconds}초간 자연스럽게 말해주세요.")
    audio = sd.rec(int(seconds * 16000), samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    audio = audio.flatten()
    profile = _extract_mfcc(audio)
    np.save(VOICE_PROFILE_PATH, profile)
    print(f"✅ 목소리 등록 완료 → {VOICE_PROFILE_PATH}")
    return profile

def verify_voice(audio: "np.ndarray", threshold: float = 0.82) -> bool:
    """녹음된 음성이 등록된 성문과 유사한지 확인."""
    import numpy as np
    if not os.path.exists(VOICE_PROFILE_PATH):
        return True  # 미등록 시 항상 통과
    profile = np.load(VOICE_PROFILE_PATH)
    mfcc = _extract_mfcc(audio)
    sim = _cosine_similarity(profile, mfcc)
    return sim >= threshold


class WakeWordListener:
    WAKE_WORDS    = ["온유야", "온유", "오뉴야", "오뉴", "은유야", "은유",
                     "옹유야", "옹유", "오유야", "오유", "온우야", "안유야",
                     "운이야", "운유야", "운유", "우니야", "오니야"]
    RMS_THRESHOLD  = 0.02   # 기본값 (시작 시 자동 보정됨)
    MONITOR_SEC    = 0.1    # RMS 체크 간격 (초)
    SILENCE_CHUNKS = 15     # 침묵 15청크(1.5초) → 발화 종료 판단
    MAX_CHUNKS     = 300    # 최대 30초
    COOLDOWN_SEC   = 2.0    # 감지 후 재감지 방지 대기 (초)
    SAMPLE_RATE    = 16000

    def __init__(self):
        self._thread     = None
        self._stop_event = threading.Event()
        self._triggered  = threading.Event()
        self._running    = False
        self._wake_query = ""
        # 저장된 임계값 로드 (없으면 기본값)
        try:
            with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                _cfg = json.load(f)
            self._threshold = float(_cfg.get("wake_threshold", self.RMS_THRESHOLD))
        except:
            self._threshold = self.RMS_THRESHOLD

    def start(self):
        if self._running: return
        self._stop_event.clear()
        self._triggered.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._running = True
        print("👂 웨이크워드 ON — '온유야'라고 부르면 음성 입력이 시작됩니다.")

    def stop(self):
        self._stop_event.set()
        self._running = False
        print("👂 웨이크워드 OFF")

    def is_triggered(self) -> bool:
        if self._triggered.is_set():
            self._triggered.clear()
            return True
        return False

    def _run(self):
        try:
            import sounddevice as sd
            import numpy as np
            import whisper as _whisper

            SR         = self.SAMPLE_RATE
            monitor_sz = int(SR * self.MONITOR_SEC)

            model = _get_whisper_model()  # small 모델 공유 (tiny보다 정확)
            print("✅ 웨이크워드 모델 준비 완료")

            with sd.InputStream(samplerate=SR, channels=1, dtype='float32') as stream:
                # ── 스트림 안정화 대기 후 소음 측정 ─────────────────
                import time as _time
                print("🔇 마이크 초기화 중...")
                _time.sleep(1.0)  # 스트림 버퍼 안정화

                # 0이 아닌 데이터가 나올 때까지 대기 (최대 3초)
                for _ in range(30):
                    c, _ = stream.read(monitor_sz)
                    if float(np.sqrt(np.mean(c ** 2))) > 0:
                        break

                # 2초 소음 측정
                noise_samples = []
                for _ in range(int(2.0 / self.MONITOR_SEC)):
                    c, _ = stream.read(monitor_sz)
                    v = float(np.sqrt(np.mean(c ** 2)))
                    if v > 0:
                        noise_samples.append(v)

                if noise_samples:
                    ambient = float(np.mean(noise_samples))
                    self._threshold = max(self.RMS_THRESHOLD, ambient * 5)
                else:
                    ambient = 0.0
                    self._threshold = self.RMS_THRESHOLD
                print(f"🎚️  임계값: {self._threshold:.4f} (주변소음: {ambient:.4f})  — '웨이크워드 임계값 0.05' 로 수동 조정 가능")

                rms_history = []
                HISTORY_SIZE = 300   # 최근 30초 (0.1초 × 300)
                ADJUST_EVERY = 50    # 5초마다 재조정

                iter_count = 0
                while not self._stop_event.is_set():
                    # ── RMS 체크 (거의 0% CPU) ───────────────────────
                    chunk, _ = stream.read(monitor_sz)
                    rms = float(np.sqrt(np.mean(chunk ** 2)))

                    # ── 동적 임계값 자동조정 (5초마다) ──────────────
                    rms_history.append(rms)
                    if len(rms_history) > HISTORY_SIZE:
                        rms_history.pop(0)
                    iter_count += 1
                    if iter_count % ADJUST_EVERY == 0 and len(rms_history) >= ADJUST_EVERY:
                        p80 = sorted(rms_history)[int(len(rms_history) * 0.8)]
                        new_t = max(self.RMS_THRESHOLD, p80 * 2.0)
                        # 올라가는 방향만 자동조정 (내려가면 무시)
                        if new_t > self._threshold + 0.001:
                            self._threshold = new_t
                            print(f"\n🎚️  임계값 자동조정(상향): {self._threshold:.4f}")

                    if rms < self._threshold:
                        continue

                    # ── 소리 감지 → 침묵까지 전체 녹음 (Siri 방식) ──
                    frames        = [chunk]
                    peak_rms      = rms
                    silent_count  = 0
                    for _ in range(self.MAX_CHUNKS):
                        if self._stop_event.is_set(): break
                        data, _ = stream.read(monitor_sz)
                        frames.append(data)
                        r = float(np.sqrt(np.mean(data ** 2)))
                        if r > peak_rms: peak_rms = r
                        if r < self._threshold:
                            silent_count += 1
                            if silent_count >= self.SILENCE_CHUNKS:
                                break
                        else:
                            silent_count = 0

                    audio = np.concatenate(frames).flatten()

                    # ── Whisper tiny 변환 ────────────────────────────
                    try:
                        result = model.transcribe(
                            audio, language="ko", fp16=False,
                            no_speech_threshold=0.6,       # 음성 없으면 무시
                            logprob_threshold=-1.0,        # 불확실한 인식 무시
                            condition_on_previous_text=False
                        )
                        # 신뢰도 필터: no_speech_prob 높거나 avg_logprob 낮으면 스킵
                        seg = result.get("segments", [])
                        if seg:
                            no_speech = seg[0].get("no_speech_prob", 0)
                            avg_logprob = seg[0].get("avg_logprob", -1)
                            if no_speech > 0.5 or avg_logprob < -0.8:
                                continue
                        text = result["text"].strip()
                        if not text:
                            continue
                        # 웨이크워드가 문장 맨 앞 10자 안에 있어야 인식
                        text_front = text[:10]
                        if any(w in text_front for w in self.WAKE_WORDS):
                            # 화자 검증 (성문 등록된 경우만)
                            if not verify_voice(audio):
                                print(f"[웨이크워드] 타인 목소리 차단: '{text}'")
                                continue
                            print(f"\n👂 웨이크워드 감지: '{text}'")
                            # 웨이크워드 제거 후 남은 질문 추출
                            query = text
                            for w in sorted(self.WAKE_WORDS, key=len, reverse=True):
                                query = re.sub(re.escape(w), "", query).strip(" .,~!?")
                            self._wake_query = query
                            self._triggered.set()
                            self._stop_event.wait(self.COOLDOWN_SEC)  # 쿨다운
                    except:
                        pass

        except Exception as e:
            print(f"⚠️ 웨이크워드 오류: {e}")
            self._running = False


def _startup_briefing():
    """시작 시 학습 진도 알림 + 오늘 클리핑 뉴스 브리핑을 음성으로 출력."""
    try:
        lines = []

        # 1. 학습 진도 알림
        exam_dday = (EXAM_DATE - datetime.now()).days
        if exam_dday > 0:
            lines.append(f"공조냉동기계기사 실기 시험까지 {exam_dday}일 남았습니다.")
            if exam_dday <= 7:
                lines.append("시험이 코앞입니다. 오늘도 집중해봅시다.")
            elif exam_dday <= 30:
                lines.append("한 달 안에 시험입니다. 꾸준히 잘 하고 있습니다.")

        # 2. 오늘 클리핑 뉴스 브리핑
        today = datetime.now().strftime("%Y-%m-%d")
        today_clips = []
        if os.path.exists(CLIP_FOLDER):
            for f in sorted(os.listdir(CLIP_FOLDER)):
                fp = os.path.join(CLIP_FOLDER, f)
                if f.endswith('.md'):
                    mtime_str = datetime.fromtimestamp(os.path.getmtime(fp)).strftime("%Y-%m-%d")
                    if mtime_str == today:
                        today_clips.append(os.path.splitext(f)[0].replace('_', ' '))

        if today_clips:
            lines.append(f"오늘 클리핑된 뉴스 {len(today_clips)}건입니다.")
            for title in today_clips[:3]:
                lines.append(title + ".")

        if lines:
            briefing = " ".join(lines)
            print(f"🔊 [브리핑] {briefing}")
            speak(briefing)
    except Exception as e:
        pass


def _send_telegram_notify(msg: str):
    """봇으로 용준님에게 텔레그램 알림 전송"""
    import urllib.request, urllib.parse, json as _json
    try:
        token = _get_env('TELEGRAM_BOT_TOKEN')
        if not token:
            return
        ids_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'telegram_allowed_ids.json')
        if not os.path.exists(ids_file):
            return
        with open(ids_file, 'r') as f:
            ids = _json.load(f)
        if not ids:
            return
        chat_id = ids[0]
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({'chat_id': chat_id, 'text': msg}).encode()
        urllib.request.urlopen(url, data=data, timeout=5)
    except Exception:
        pass


def _auto_backup():
    """시작 시 SYSTEM 코드 파일(.py, .md)을 code_backup/YYYY-MM-DD/ 에 자동 백업."""
    try:
        system_dir = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM")
        today = datetime.now().strftime("%Y-%m-%d")
        backup_dir = os.path.join(r"C:\Users\User\AppData\Local\onew\code_backup", today)
        # 오늘 이미 백업했으면 건너뜀
        if os.path.exists(backup_dir):
            return
        os.makedirs(backup_dir, exist_ok=True)
        import shutil
        backed = 0
        for f in os.listdir(system_dir):
            if f.endswith((".py", ".md")) and "복사본" not in f:
                shutil.copy2(os.path.join(system_dir, f), os.path.join(backup_dir, f))
                backed += 1
        print(f"💾 [자동 백업] {backed}개 파일 → code_backup/{today}/")
    except Exception as e:
        print(f"⚠️ [자동 백업] 실패: {e}")

if __name__ == "__main__":
    _check_single_instance()
    _auto_backup()
    onew = OnewAgent()
    from onew_weakness_tracker import WeaknessTracker
    from onew_review_scheduler import ReviewScheduler
    _gen_fn     = lambda p: client.models.generate_content(model='gemini-2.5-flash', contents=p).text
    try:
        from onew_api_guard import make_bg_generate_fn
        _bg_gen_fn = make_bg_generate_fn(_gen_fn)   # 배경용 (속도 제한 적용)
    except Exception as _ge:
        print(f"  ⚠️ [API가드] 초기화 실패, 가드 없이 실행: {_ge}")
        _bg_gen_fn = _gen_fn

    _review   = ReviewScheduler(generate_fn=_bg_gen_fn)
    _weakness = WeaknessTracker(generate_fn=_bg_gen_fn, review_scheduler=_review)
    _review.run_daily_check()
    from onew_night_study import start_background as _night_start
    _night_start(_bg_gen_fn)
    from onew_field_linker import start_background as _field_start
    _field_start(_bg_gen_fn)
    from onew_meta import MetaEngine, start_background as _meta_start
    _meta = MetaEngine(generate_fn=_bg_gen_fn)
    _meta_start(_meta)
    from onew_planner import DailyPlanner, start_background as _planner_start
    _planner = DailyPlanner(generate_fn=_bg_gen_fn)
    _planner_start(_planner)

    try:
        from onew_scheduler import start_background as _scheduler_start
        _scheduler_start()
    except Exception as _e:
        print(f"  ⚠️ [스케줄러] 초기화 실패: {_e}")

    # 자율코딩 워처 시작 (5분마다 오류 로그 감시 + 야간 자기진단)
    try:
        import onew_self_improve as _si
        _si.start_watcher(check_interval=300)
        print("🔧 [자율코딩] 워처 시작 (5분 간격, 야간 자기진단 23:00)")
    except Exception as _e:
        print(f"  ⚠️ [자율코딩] 초기화 실패: {_e}")

    try:
        from onew_adhd_coach import ADHDCoach, start_background as _coach_start
        _coach = ADHDCoach(generate_fn=_gen_fn)
        _coach_start(_coach)
    except Exception as _e:
        print(f"  ⚠️ [ADHD코치] 초기화 실패: {_e}")

    # ADHD 엔진 초기화 (generate_fn 주입 — 학습목표 자료 검색용)
    try:
        import onew_adhd as _adhd_mod
        _adhd_mod.get_engine(generate_fn=_bg_gen_fn)
        print("🧠 [ADHD엔진] 초기화 완료 (학습목표 포착 + 과집중 보호 + 스트릭)")
    except Exception as _e:
        print(f"  ⚠️ [ADHD엔진] 초기화 실패: {_e}")

    clipper = AutoClipper()

    # [자율학습 2] 주 1회 중요도 재계산
    last_recalc = onew.mem.db.get("__meta__", {}).get("last_importance_recalc", "")
    recalc_needed = True
    if last_recalc:
        try:
            from datetime import timedelta
            if (datetime.now() - datetime.strptime(last_recalc, "%Y-%m-%d")).days < IMPORTANCE_RECALC_DAYS:
                recalc_needed = False
        except: pass
    if recalc_needed:
        print("📈 [자율학습] 중요도 재계산 중...")
        onew.mem.recalculate_importance()
    
    # 🌟 빠른 시작 플래그: python obsidian_agent.py --fast
    # sync 완전 건너뜀 — 기존 DB 그대로 사용. 급할 때 사용.
    FAST_MODE = len(sys.argv) > 1 and sys.argv[1] == "--fast"
    if FAST_MODE:
        sys.argv.pop(1)  # --fast 플래그 제거 후 대화형 모드로 진입

    # 🌟 [과금 방어 1단계] 수동 동기화 전용 명령어: gemini --sync
    if len(sys.argv) > 1 and sys.argv[1] == "--sync":
        print("⚠️ [수동 학습 모드] 새로 작성된 노트를 온유의 뇌(DB)에 각인시킵니다...")
        onew.mem.sync(silent=False)
        print("✅ 학습이 완료되었습니다. 이제 평소처럼 gemini 명령어를 사용하십시오.")
        sys.exit(0)

    # 🌟 백그라운드 서비스 전용 모드 (재부팅 자동시작용): python obsidian_agent.py --service
    elif len(sys.argv) > 1 and sys.argv[1] == "--service":
        # 자율 학습 sync (6시간 이상 지났으면)
        last_sync_str = onew.mem.db.get("__meta__", {}).get("last_sync")
        auto_sync_needed = True
        if last_sync_str:
            try:
                if (datetime.now() - datetime.strptime(last_sync_str, "%Y-%m-%d %H:%M")).total_seconds() < AUTO_SYNC_HOURS * 3600:
                    auto_sync_needed = False
            except: pass
        if auto_sync_needed:
            print(f"🧠 [자율 학습] 마지막 동기화: {last_sync_str or '없음'} → 자동 업데이트 시작...")
            try:
                import onew_shared as _os; _os.set_syncing(True)
            except: pass
            try:
                onew.mem.sync(silent=False)
            finally:
                try:
                    import onew_shared as _os; _os.set_syncing(False)
                except: pass
        else:
            print(f"✅ [자율 학습] 최신 상태 확인 완료 (마지막: {last_sync_str})")

        clip_cfg = _load_clip_config()
        if clip_cfg.get("enabled", True):
            done = _today_clip_count()
            max_c = clip_cfg.get("max_clips", 10)
            if done < max_c:
                clipper.start()
                print(f"📎 [자동 클리핑] 백그라운드 시작 ({done}/{max_c}개 완료)")
        print("🔧 [서비스 모드] 백그라운드 서비스 실행 중 (Ctrl+C로 종료)")
        try:
            while True:
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n🔧 [서비스 모드] 종료합니다.")
        sys.exit(0)

    # 🌟 [과금 방어 2단계] 단발성 CLI 모드 (스캔 절대 안 함)
    elif len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
        # onew.mem.sync() 로직을 완전히 삭제. 오직 기존에 저장된 로컬 DB만 읽습니다.
        onew.ask(query, silent_search=True)
    
    # 🌟 [과금 방어 3단계] 대화형 챗봇 모드
    else:
        print("🌟 온유(Onew) Vibe Coding 에이전트 가동 중...")
        wifi_sec = _wifi_security_cache.get("result", _get_wifi_security())  # 캐시 우선 사용
        config_data = {}
        if os.path.exists(LOCATION_CONFIG_FILE):
            try:
                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config_data = json.load(f)
            except: pass
        is_manual = config_data.get("manual_override") is not None
        detected_ssid = _wifi_security_cache.get("ssid", "")
        ssid_info = f", SSID: {detected_ssid}" if detected_ssid else ""
        if onew.location_mode == "work":
            reason = "수동 설정" if is_manual else f"개방형 WiFi 감지{ssid_info}"
            print(f"🔒 [시크릿 모드 ON] 개인 민감 주제 차단 중. ({reason})")
            print("   해제하려면: '시크릿 off' 또는 '시크릿 자동'(WiFi 재감지)")
            if not is_manual and detected_ssid:
                print(f"   집 WiFi인 경우 '신뢰 SSID 추가: {detected_ssid}' 입력 시 영구 해결")
        else:
            reason = "수동 설정" if is_manual else f"보안 WiFi{ssid_info}"
            print(f"🔓 [시크릿 모드 OFF] 모든 대화 가능. ({reason})")
            print("   활성화하려면: '시크릿 on'")

        # 🧠 [자율 학습] 마지막 sync로부터 6시간 이상 지났으면 자동 학습
        last_sync_str = onew.mem.db.get("__meta__", {}).get("last_sync")
        auto_sync_needed = True
        if last_sync_str:
            try:
                last_sync_dt = datetime.strptime(last_sync_str, "%Y-%m-%d %H:%M")
                if (datetime.now() - last_sync_dt).total_seconds() < AUTO_SYNC_HOURS * 3600:
                    auto_sync_needed = False
            except: pass

        if FAST_MODE:
            print(f"⚡ [빠른 시작] sync 건너뜀. 기존 DB 사용 (마지막 sync: {last_sync_str or '없음'})")
            print("   정상 시작: '온유_실행.bat' / 수동 sync: 'python obsidian_agent.py --sync'")
        elif auto_sync_needed:
            # 백그라운드 sync — 사용자는 즉시 대화 시작 가능
            print(f"🧠 [자율 학습] 백그라운드 동기화 시작 (마지막: {last_sync_str or '없음'})")
            print("   ※ sync 진행 중에도 바로 질문 가능. 새 내용은 sync 완료 후 검색됩니다.")
            def _bg_sync():
                try:
                    import onew_shared as _os; _os.set_syncing(True)
                except: pass
                try:
                    onew.mem.sync(silent=True)
                    print("\n✅ [자율 학습] 백그라운드 sync 완료. 새 내용 검색 가능.")
                except Exception as _e:
                    print(f"\n⚠️ [자율 학습] sync 오류: {_e}")
                finally:
                    try:
                        import onew_shared as _os; _os.set_syncing(False)
                    except: pass
            threading.Thread(target=_bg_sync, daemon=True).start()
        else:
            print(f"✅ [자율 학습] 최신 상태 확인 완료 (마지막: {last_sync_str})")

        print("🌐 [웹 검색] Google Search 직접 연결 완료.")

        # 📎 자동 클리핑 시작
        clip_cfg = _load_clip_config()
        if clip_cfg.get("enabled", True):
            done = _today_clip_count()
            max_c = clip_cfg.get("max_clips", 10)
            if done < max_c:
                clipper.start()
                print(f"📎 [자동 클리핑] 백그라운드 시작 ({done}/{max_c}개 완료, {clip_cfg.get('delay_seconds',30)}초 간격)")
            else:
                print(f"📎 [자동 클리핑] 오늘 {done}개 완료 (한도 도달)")
        else:
            print("📎 [자동 클리핑] OFF (켜려면: '클리핑 시작')")

        # 📅 오늘 일정 + D-day 자동 표시
        try:
            today_schedule = calendar_list(1)
            if "없음" not in today_schedule:
                print(f"\n{today_schedule}")
            exam_dday = (EXAM_DATE - datetime.now()).days
            print(f"⏳ 공조냉동 실기 D-{exam_dday}")
        except: pass

        # 🔊 시작 브리핑 (학습 진도 + 뉴스)
        try:
            with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                _cfg = json.load(f)
        except:
            _cfg = {}
        if _cfg.get("briefing_enabled", True):
            _startup_briefing()

        # 🔍 오류 로그 자동 점검 (1시간 이내 오류만 알림)
        try:
            log_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "온유_오류.md")
            if os.path.exists(log_path) and os.path.getsize(log_path) > 0:
                mtime = datetime.fromtimestamp(os.path.getmtime(log_path))
                if (datetime.now() - mtime).total_seconds() < 3600:
                    print(f"\n⚠️  최근 오류 기록 감지됨. '오류 확인해줘'라고 말하면 분석합니다.")
        except: pass

        print("\n💬 파일 수정, 코드 작성, 웹 검색 등 무엇이든 명령하십시오.")
        print("   💡 '음성 on' / 'tts on' 으로 음성 모드 전환 | '웨이크워드 on' 으로 '온유야' 호출 활성화")
        import queue as _queue
        voice_mode = False
        tts_mode = False
        voice_empty_count = 0
        wake_listener = WakeWordListener()

        # 키보드 입력을 별도 스레드로 분리 → 메인 루프가 웨이크워드도 체크 가능
        _input_queue = _queue.Queue()
        def _input_worker():
            while True:
                try:
                    line = input("\n💬 용준 님: ")
                    _input_queue.put(line)
                except EOFError:
                    break
        _input_thread = threading.Thread(target=_input_worker, daemon=True)
        _input_thread.start()

        while True:
            try:
                # 웨이크워드 감지 → 항상 별도 명령어 입력 대기 (2단계)
                if wake_listener.is_triggered():
                    wake_listener._wake_query = ""
                    print("🟢 온유야 감지! 명령을 말씀하세요...")
                    q = voice_input()
                    if q:
                        print(f"\n💬 용준 님 (음성): {q}")
                        cmd = q.strip().lower().lstrip('/')
                        if cmd not in ['끝', 'exit', 'quit']:
                            onew.ask(q)
                            if onew.history_records:
                                _last_ans = onew.history_records[-1].get("text", "")
                                _weakness.detect_and_log(q, _last_ans)
                                if tts_mode and _last_ans: speak(_last_ans)
                    continue

                if voice_mode:
                    q = voice_input()
                    if not q:
                        voice_empty_count += 1
                        if voice_empty_count >= 3:
                            voice_mode = False
                            voice_empty_count = 0
                            print("🔇 음성 무응답 3회 → 음성 입력 자동 종료")
                        continue
                    voice_empty_count = 0
                    import onew_shared; onew_shared.touch()  # 음성 입력도 touch
                    print(f"\n💬 용준 님 (음성): {q}")
                else:
                    try:
                        q = _input_queue.get(timeout=0.1)
                        import onew_shared; onew_shared.touch()
                    except _queue.Empty:
                        continue

                cmd = q.strip().lower().lstrip('/')
                if cmd in ['끝', 'exit', 'quit']: break
                elif cmd in ['음성 on', '음성on', 'voice on']:
                    voice_mode = True
                    _get_whisper_model()
                    print("🎤 음성 입력 ON (TTS 별도: 'tts on')")
                elif any(kw in cmd for kw in ['음성 off', '음성off', 'voice off',
                                              '음성 오프', '음성오프', '음성 꺼줘',
                                              '음성꺼줘', '영상 오프', '영상오프',
                                              '음성 인식 꺼', '음성인식 꺼', '음성인식꺼',
                                              '음성 인식 꺼져', '음성인식 꺼져',
                                              '음성 입력 꺼', '음성입력 꺼',
                                              '마이크 꺼', '마이크꺼', '마이크 off',
                                              '듣기 꺼', '듣기꺼', '그만 들어',
                                              '음성 그만', '음성모드 꺼']):
                    voice_mode = False
                    print("⌨️  텍스트 입력 모드로 전환 (TTS는 유지)")
                elif any(kw in cmd for kw in ['tts off', 'tts 꺼', 'tts꺼',
                                              'ts 꺼', 'ts꺼', 'cts 꺼', 'cts꺼',
                                              'ts 꺼져', 'cts 꺼져', 'tts 꺼져',
                                              '읽어줘 off', '소리 off', '소리꺼',
                                              '소리 꺼', '읽기 꺼', '음성출력 꺼',
                                              '티티에스 꺼', '읽어주기 꺼']):
                    tts_mode = False
                    print("🔇 TTS OFF (음성 입력은 유지)")
                elif cmd in ['tts on', '읽어줘 on', '소리 on']:
                    tts_mode = True
                    print("🔊 TTS ON (텍스트 입력 유지, 답변만 음성 출력)")
                elif cmd in ['웨이크워드 on', '웨이크워드on', 'wake on', '온유야 on', '호출 on']:
                    wake_listener.start()
                elif cmd in ['웨이크워드 off', '웨이크워드off', 'wake off', '온유야 off', '호출 off']:
                    wake_listener.stop()
                elif re.match(r'웨이크워드 임계값\s+(\d+\.?\d*)', cmd):
                    val = float(re.match(r'웨이크워드 임계값\s+(\d+\.?\d*)', cmd).group(1))
                    wake_listener.RMS_THRESHOLD = val
                    wake_listener._threshold = val
                    # 파일에 저장 (재시작 시 유지)
                    try:
                        with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                            _cfg = json.load(f)
                    except:
                        _cfg = {}
                    _cfg["wake_threshold"] = val
                    with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(_cfg, f, ensure_ascii=False, indent=2)
                    print(f"🎚️  웨이크워드 임계값 → {val} (즉시 적용 + 저장)")
                elif cmd in ['목소리 등록', '목소리등록', '성문 등록', '성문등록', 'voice enroll']:
                    enroll_voice(seconds=10)
                elif cmd in ['목소리 삭제', '목소리삭제', '성문 삭제', '성문삭제', 'voice reset']:
                    if os.path.exists(VOICE_PROFILE_PATH):
                        os.remove(VOICE_PROFILE_PATH)
                        print("🗑️  목소리 프로필 삭제됨 (웨이크워드 화자검증 비활성화)")
                    else:
                        print("등록된 목소리 프로필 없음.")
                elif cmd in ['브리핑 on', '브리핑on', 'briefing on']:
                    try:
                        with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                            _cfg = json.load(f)
                    except:
                        _cfg = {}
                    _cfg["briefing_enabled"] = True
                    with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(_cfg, f, ensure_ascii=False, indent=2)
                    print("🔊 브리핑 ON — 다음 재시작부터 적용됩니다.")
                elif cmd in ['브리핑 off', '브리핑off', 'briefing off']:
                    try:
                        with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                            _cfg = json.load(f)
                    except:
                        _cfg = {}
                    _cfg["briefing_enabled"] = False
                    with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                        json.dump(_cfg, f, ensure_ascii=False, indent=2)
                    print("🔇 브리핑 OFF — 다음 재시작부터 적용됩니다.")
                elif cmd in ['공부 시작', '공부시작', '문제 줘', '문제줘', '공부']:
                    try:
                        _coach.start_session()
                        print("  📚 텔레그램으로 첫 문제를 전송했습니다.")
                    except Exception as _ce:
                        print(f"  ⚠️ 코치 오류: {_ce}")
                elif cmd in ['끄기', '/끄기', '온유 끄기', '시스템 종료']:
                    import onew_budget as _budget_mod
                    flag = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'stop.flag')
                    with open(flag, 'w') as _f:
                        _f.write('stop')
                    _send_telegram_notify("🔴 온유 시스템을 종료합니다. (재시작하려면 BAT 실행)")
                    print("🔴 온유 종료 플래그 생성 — 잠시 후 종료됩니다.")
                    break
                elif cmd in ['예산', '/예산', 'api 예산', 'api예산', '요금']:
                    import onew_budget as _budget_mod
                    print(_budget_mod.get_status())
                elif cmd in ['약점', '약점 현황', '약점현황', '내 약점', '내약점']:
                    print(_weakness.get_summary())
                elif cmd in ['패턴', '학습 패턴', '학습패턴', '내 패턴']:
                    print(_meta.get_summary())
                elif cmd in ['오늘 공부', '오늘 추천', '뭐 공부할까', '공부 추천']:
                    print(_meta.recommend_today())
                elif cmd in ['오늘 계획', '오늘계획', '계획', '학습 계획']:
                    print(_planner.get_today_plan())
                elif cmd in ['계획 세워줘', '계획세워줘', '계획 다시']:
                    _planner.force_plan()
                elif cmd in ['복습 현황', '복습현황', '복습 일정', '복습일정']:
                    print(_review.get_summary())
                elif q.startswith('복습등록:') or q.startswith('복습 등록:'):
                    concept = q.split(':', 1)[-1].strip()
                    if concept:
                        _review.register(concept)
                        print(f"  📅 '{concept}' 복습 일정 등록 완료")
                elif q.startswith('복습완료:') or q.startswith('복습 완료:'):
                    concept = q.split(':', 1)[-1].strip()
                    if concept:
                        _review.mark_reviewed(concept)
                        print(f"  ✅ '{concept}' 복습 완료 처리")
                elif cmd in ['저장', '저장해줘', '저장해', '저장하기', '대화 저장', '대화저장']:
                    onew._save_history_to_vault()
                    print("💾 대화 기록 저장 완료")
                elif q.startswith('계획:') or q.startswith('계획 '):
                    # 온유 자율 코딩 계획 실행
                    goal = q.split(':', 1)[-1].strip() if ':' in q else q[3:].strip()
                    try:
                        import onew_code_planner as _ocp
                        result = _ocp.receive_direction(goal, client=client)
                        print(f"📋 {result}")
                    except Exception as _e:
                        print(f"⚠️ 계획 생성 실패: {_e}")
                elif q in ('계획상태', '계획 상태', 'plan status'):
                    try:
                        import onew_code_planner as _ocp
                        print(_ocp.get_status())
                    except Exception as _e:
                        print(f"⚠️ {_e}")
                elif q in ('플래너로그', '계획로그', 'plan log'):
                    try:
                        import onew_code_planner as _ocp
                        print(_ocp.get_log())
                    except Exception as _e:
                        print(f"⚠️ {_e}")
                elif q in ('승인', '플래너승인', 'plan approve'):
                    try:
                        import onew_code_planner as _ocp
                        print(_ocp.approve_plan())
                    except Exception as _e:
                        print(f"⚠️ {_e}")
                elif q.startswith('클로드한테 시킬 거야') or q.startswith('클로드에게 시킬 거야') or q.startswith('클로드한테 시켜'):
                    # 콜론 또는 공백 이후 내용 추출
                    task = q.split(':', 1)[-1].strip() if ':' in q else re.sub(r'^클로드(한테|에게)\s*시킬\s*거야|^클로드한테\s*시켜', '', q).strip()
                    if not task:
                        print("💬 어떤 작업을 시킬까요? 예: 클로드한테 시킬 거야: link_batch_scan.py 오류 분석해줘")
                    else:
                        print("✍️  프롬프트 작성 중...")
                        prompt_req = f"""너는 Claude Code 전문 프롬프트 엔지니어다.
아래 작업 요청을 Claude Code에게 전달할 최적화된 프롬프트로 변환하라.

[작업 요청]
{task}

[반드시 포함할 3가지]
1. 범위 지정: 어떤 파일/코드/범위를 다룰지 명확히
2. 원칙 제시: Claude Code가 지켜야 할 제약 조건
3. 출력 형태 강제: 결과물 형식 (코드/설명/파일 등)

[출력 형식]
마크다운 코드블록 없이 완성된 프롬프트 텍스트만 출력. 설명 없음."""
                        try:
                            resp = client.models.generate_content(
                                model="gemini-2.5-flash",
                                contents=prompt_req,
                                config=types.GenerateContentConfig(
                                    thinking_config=types.ThinkingConfig(thinking_budget=0)
                                )
                            )
                            refined = resp.text.strip()
                            out_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_to_claude.md")
                            with open(out_path, 'w', encoding='utf-8') as f:
                                f.write(f"---\n날짜: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n원본요청: {task}\n---\n\n{refined}\n")
                            print(f"✅ 프롬프트 저장 완료 → SYSTEM/onew_to_claude.md")
                            print(f"{'='*50}")
                            print(refined)
                            print(f"{'='*50}")
                            print("💡 위 내용을 Claude Code에 붙여넣기 하세요.")
                        except Exception as e:
                            print(f"❌ 프롬프트 생성 실패: {e}")
                elif cmd in ['동기화', 'sync', '싱크']:
                    onew.mem.sync(silent=False)
                elif cmd in ['시크릿 on', '시크릿on', '시크릿모드 on', '시크릿모드on', 'secret on', '보안모드 on']:
                    onew.set_secret_mode(True)
                elif cmd in ['시크릿 off', '시크릿off', '시크릿모드 off', '시크릿모드off', 'secret off', '보안모드 off']:
                    onew.set_secret_mode(False)
                elif cmd in ['시크릿 자동', '자동감지', '시크릿모드 자동', 'secret auto']:
                    onew.clear_secret_override()
                elif cmd.startswith('신뢰 ssid 추가:') or cmd.startswith('신뢰 ssid 추가 '):
                    ssid_to_trust = q.split(':', 1)[-1].strip() if ':' in q else q.split(' ', 3)[-1].strip()
                    if ssid_to_trust:
                        cfg = {}
                        if os.path.exists(LOCATION_CONFIG_FILE):
                            try:
                                with open(LOCATION_CONFIG_FILE, 'r', encoding='utf-8') as f:
                                    cfg = json.load(f)
                            except: pass
                        trusted = cfg.get("trusted_ssids", [])
                        if ssid_to_trust not in trusted:
                            trusted.append(ssid_to_trust)
                            cfg["trusted_ssids"] = trusted
                            with open(LOCATION_CONFIG_FILE, 'w', encoding='utf-8') as f:
                                json.dump(cfg, f, ensure_ascii=False, indent=2)
                            onew.location_mode = "home"
                            onew._new_chat_session()
                            print(f"✅ '{ssid_to_trust}' 신뢰 네트워크로 등록. 시크릿 모드 해제.")
                        else:
                            print(f"ℹ️ '{ssid_to_trust}'은 이미 신뢰 목록에 있습니다.")
                    else:
                        print("❌ SSID 이름이 필요합니다. 예: 신뢰 SSID 추가: MyHomeWifi")
                elif _clip_command(q, clipper):
                    pass
                elif q.strip():
                    # 이미지 파일 경로 자동 감지
                    img_exts = ('.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp')
                    tokens = q.strip().split()
                    img_path = next((t for t in tokens if t.lower().endswith(img_exts)), None)

                    # 자연어 이미지 요청 감지 (경로 없을 때)
                    img_nl_keywords = [
                        '사진', '이미지', '그림', '스크린샷', '캡처', '사진을', '이미지를',
                        '그림을', '사진은', '이미지는', '사진파일', '이미지파일',
                    ]
                    img_action_keywords = [
                        '변환', '변경', '바꿔', '분석', '마크다운', '정리', '읽어',
                        '텍스트로', '추출', '요약', '설명', '알려',
                    ]
                    is_img_nl = (not img_path
                                 and any(k in q for k in img_nl_keywords)
                                 and any(k in q for k in img_action_keywords))

                    if img_path:
                        question = q.replace(img_path, "").strip()
                        print(f"🖼️  이미지 분석 중: {os.path.basename(img_path)}")
                        result = analyze_image(img_path, question)
                        print(f"==================================================")
                        print(f"💡 온유:\n{result}\n")
                        print(f"==================================================")
                    elif is_img_nl:
                        print("💬 용준 님: 파일 경로를 입력해주세요 (예: C:\\Users\\User\\Desktop\\문제.jpg)")
                        path_input = input("📂 경로: ").strip()
                        if path_input:
                            print(f"🖼️  이미지 분석 중: {os.path.basename(path_input)}")
                            result = analyze_image(path_input, q)
                            print(f"==================================================")
                            print(f"💡 온유:\n{result}\n")
                            print(f"==================================================")
                    else:
                        onew.ask(q)
                        if onew.history_records:
                            _last_ans = onew.history_records[-1].get("text", "")
                            _weakness.detect_and_log(q, _last_ans)
                            _suggestion = _meta.observe(q, _last_ans)
                            if _suggestion:
                                print(_suggestion)
                            if tts_mode and _last_ans: speak(_last_ans)
                            # 자율코딩: 대화 키워드 감지
                            try:
                                _si.notify_conversation(q, _last_ans)
                            except: pass
            except KeyboardInterrupt: break
        print("온유 시스템 종료.")
        _send_telegram_notify("⚠️ 온유 시스템이 종료되었습니다.")