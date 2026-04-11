"""
background_learner.py
웹 검색 → 2단계 Gemini 평가 → inbox_filtered/ 저장

실행: python background_learner.py
주의: GEMINI_API_KEY 환경변수 필요
"""
import os, sys, json, re, time, random, logging
from datetime import datetime
from pathlib import Path

SYSTEM_DIR          = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH          = os.path.dirname(SYSTEM_DIR)
INBOX_DIR           = os.path.join(VAULT_PATH, "inbox_filtered")
LOG_FILE            = os.path.join(SYSTEM_DIR, "background_learner.log")
SEARCH_STATE_FILE   = os.path.join(SYSTEM_DIR, "background_learner_state.json")

os.makedirs(INBOX_DIR, exist_ok=True)

logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8",
)
logger = logging.getLogger(__name__)

# ── 검색 주제 (수정 가능) ──────────────────────────────────────────────────────
SEARCH_TOPICS = [
    "공조냉동기계기사 실기 핵심 정리",
    "소방설비기사 핵심 개념",
    "냉동사이클 계산 방법",
    "python 비동기 프로그래밍",
    "AI LLM 최신 연구",
    "소각로 설비 유지보수",
]

MAX_RESULTS_PER_TOPIC = 3   # 주제당 최대 검색 결과
SCORE_THRESHOLD       = 3   # 2단계 요약 진입 최소 점수
DAILY_TOPIC_LIMIT     = 4   # 하루 처리 주제 수 제한


# ══════════════════════════════════════════════════════════════════════════════
# 유틸
# ══════════════════════════════════════════════════════════════════════════════

def _get_env(name: str) -> str:
    val = os.environ.get(name, "")
    if not val:
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment")
            val, _ = winreg.QueryValueEx(key, name)
            winreg.CloseKey(key)
        except:
            pass
    return val or ""


def _load_state() -> dict:
    if os.path.exists(SEARCH_STATE_FILE):
        try:
            with open(SEARCH_STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {"seen_urls": [], "last_run": ""}


def _save_state(s: dict):
    with open(SEARCH_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(s, f, ensure_ascii=False, indent=2)


def _safe_filename(title: str) -> str:
    s = re.sub(r'[\\/:*?"<>|\s]+', "_", title)
    return s.strip("_")[:60] or "untitled"


# ══════════════════════════════════════════════════════════════════════════════
# 웹 검색 (DuckDuckGo HTML)
# ══════════════════════════════════════════════════════════════════════════════

def _ddg_search(query: str, max_results: int = 3) -> list[dict]:
    """DuckDuckGo HTML 검색 → [{"title": str, "url": str, "snippet": str}]"""
    try:
        import requests
        from html.parser import HTMLParser

        class _DDGParser(HTMLParser):
            def __init__(self):
                super().__init__()
                self.results = []
                self._in_result = False
                self._cur = {}
                self._tag_stack = []

            def handle_starttag(self, tag, attrs):
                attrs = dict(attrs)
                self._tag_stack.append(tag)
                if tag == "a" and "result__a" in attrs.get("class", ""):
                    self._in_result = True
                    self._cur = {"title": "", "url": attrs.get("href", ""), "snippet": ""}
                elif tag == "a" and "result__snippet" in attrs.get("class", ""):
                    self._in_snippet = True

            def handle_endtag(self, tag):
                if self._tag_stack:
                    self._tag_stack.pop()
                if tag == "a" and self._in_result and self._cur.get("title"):
                    self.results.append(self._cur)
                    self._cur = {}
                    self._in_result = False

            def handle_data(self, data):
                if self._in_result and self._cur is not None and not self._cur.get("title"):
                    self._cur["title"] = data.strip()

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }
        url = f"https://html.duckduckgo.com/html/?q={requests.utils.quote(query)}&kl=kr-kr"
        resp = requests.get(url, headers=headers, timeout=10)
        resp.raise_for_status()

        # 간단한 정규식 파싱 (HTMLParser 대신)
        results = []
        pattern = re.compile(
            r'class="result__a"[^>]*href="([^"]+)"[^>]*>([^<]+)<',
            re.DOTALL,
        )
        snip_pattern = re.compile(
            r'class="result__snippet">([^<]+)<',
            re.DOTALL,
        )
        urls   = pattern.findall(resp.text)
        snippets = snip_pattern.findall(resp.text)

        for i, (href, title) in enumerate(urls[:max_results]):
            snippet = snippets[i].strip() if i < len(snippets) else ""
            results.append({
                "title":   title.strip(),
                "url":     href,
                "snippet": snippet,
            })
        return results

    except Exception as e:
        logger.warning("DDG 검색 실패 (%s): %s", query[:30], e)
        return []


def _fetch_text(url: str, max_chars: int = 3000) -> str:
    """URL → 본문 텍스트 (HTML 태그 제거)"""
    try:
        import requests
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        resp = requests.get(url, headers=headers, timeout=12)
        resp.raise_for_status()
        text = re.sub(r"<[^>]+>", " ", resp.text)
        text = re.sub(r"\s+", " ", text).strip()
        return text[:max_chars]
    except Exception as e:
        logger.warning("URL 페치 실패 (%s): %s", url[:50], e)
        return ""


# ══════════════════════════════════════════════════════════════════════════════
# 2단계 Gemini 평가
# ══════════════════════════════════════════════════════════════════════════════

def _gemini_call(client, prompt: str) -> str:
    """단일 Gemini 호출 (thinking 비활성화)"""
    try:
        import google.genai.types as _types
        resp = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=_types.GenerateContentConfig(
                thinking_config=_types.ThinkingConfig(thinking_budget=0),
                max_output_tokens=512,
            ),
        )
        return resp.text.strip()
    except Exception as e:
        logger.error("Gemini 호출 실패: %s", e)
        return ""


def _evaluate_and_summarize(client, title: str, content: str) -> tuple[int, str]:
    """
    1단계: 0~5 점수만 반환
    2단계: 점수 >= SCORE_THRESHOLD 시 요약 생성
    Returns: (score, summary)
    """
    # 1단계: 점수
    score_prompt = (
        f"다음 문서의 실용성을 0~5로만 평가하라. 숫자만 출력.\n\n"
        f"제목: {title}\n내용: {content[:1500]}"
    )
    raw_score = _gemini_call(client, score_prompt)
    try:
        score = int(re.search(r"\d", raw_score).group())
        score = max(0, min(5, score))
    except:
        score = 0
    logger.info("1단계 평가 — '%s': score=%d", title[:40], score)

    if score < SCORE_THRESHOLD:
        return score, ""

    # 2단계: 요약
    summary_prompt = (
        f"다음 문서의 핵심적이고 실용적인 내용만 3~5줄로 요약하라.\n\n"
        f"제목: {title}\n내용: {content[:2000]}"
    )
    summary = _gemini_call(client, summary_prompt)
    logger.info("2단계 요약 완료 — '%s'", title[:40])
    return score, summary


# ══════════════════════════════════════════════════════════════════════════════
# inbox 저장
# ══════════════════════════════════════════════════════════════════════════════

def _save_to_inbox(title: str, url: str, score: int, summary: str, topic: str):
    today = datetime.now().strftime("%Y-%m-%d")
    ts    = datetime.now().strftime("%H%M%S")
    fname = f"{today}_{ts}_{_safe_filename(title)}.md"
    fpath = os.path.join(INBOX_DIR, fname)

    content = (
        f"---\n"
        f"tags: [inbox, 학습대기, {today}]\n"
        f"날짜: {today}\n"
        f"주제: {topic}\n"
        f"출처: {url}\n"
        f"점수: {score}/5\n"
        f"상태: 대기중\n"
        f"author: background_learner\n"
        f"---\n\n"
        f"# {title}\n\n"
        f"**출처:** {url}\n"
        f"**평가 점수:** {score}/5\n\n"
        f"## 핵심 요약\n\n"
        f"{summary}\n"
    )
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(content)
    logger.info("inbox 저장: %s", fname)
    return fname


# ══════════════════════════════════════════════════════════════════════════════
# 메인 실행
# ══════════════════════════════════════════════════════════════════════════════

def run():
    api_key = _get_env("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY 없음. 종료.")
        print("오류: GEMINI_API_KEY 환경변수가 없습니다.")
        return

    from google import genai
    client = genai.Client(api_key=api_key)

    state = _load_state()
    seen_urls: set = set(state.get("seen_urls", []))

    today = datetime.now().strftime("%Y-%m-%d")
    topics_today = random.sample(SEARCH_TOPICS, min(DAILY_TOPIC_LIMIT, len(SEARCH_TOPICS)))

    saved_count = 0
    skipped_count = 0

    logger.info("=== background_learner 시작 (주제 %d개) ===", len(topics_today))
    print(f"[{today}] 학습 시작 — {len(topics_today)}개 주제")

    for topic in topics_today:
        print(f"  검색: {topic}")
        time.sleep(random.uniform(1.0, 2.5))  # 안티봇 jitter

        results = _ddg_search(topic, max_results=MAX_RESULTS_PER_TOPIC)
        if not results:
            logger.warning("검색 결과 없음: %s", topic)
            continue

        for item in results:
            url = item["url"]
            if url in seen_urls:
                skipped_count += 1
                continue

            time.sleep(random.uniform(1.0, 2.5))  # URL 페치 전 jitter
            text = _fetch_text(url)
            if not text:
                seen_urls.add(url)
                continue

            score, summary = _evaluate_and_summarize(client, item["title"], text)

            if score >= SCORE_THRESHOLD:
                fname = _save_to_inbox(item["title"], url, score, summary, topic)
                print(f"    ✅ 저장 (score={score}): {fname[:50]}")
                saved_count += 1
            else:
                print(f"    ⏭ 스킵 (score={score}): {item['title'][:40]}")

            seen_urls.add(url)

    # 상태 저장 (seen_urls 최근 500개 유지)
    state["seen_urls"] = list(seen_urls)[-500:]
    state["last_run"] = today
    _save_state(state)

    summary_msg = f"완료: {saved_count}건 저장, {skipped_count}건 중복 스킵"
    logger.info("=== %s ===", summary_msg)
    print(summary_msg)
    return saved_count


if __name__ == "__main__":
    run()
