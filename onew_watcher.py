import os
import re
import json
import time
import logging
from datetime import datetime
from google import genai
from google.genai import types
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from onew_tools import generate_project_map

# ==============================================================================
# [설정]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_PATH    = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM")
SUMMARY_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, "Processed")
DB_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_pure_db.json")
LOG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "onew_error.log")
USAGE_LOG_FILE = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "api_usage_log.json")

# 로그 설정
logging.basicConfig(
    filename=LOG_FILE,
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    encoding="utf-8"
)
def log_error(msg, exc=None):
    logging.error(msg, exc_info=exc is not None)
    print(f"   오류: {msg}")

def _increment_usage(category: str):
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

# 감시 제외 폴더
IGNORE_FOLDERS = ["SYSTEM", ".obsidian", "Processed", "첨부파일", "Excalidraw", "Study PDF", "Quotation", "DD"]

# 요약 생성 최소 글자 수
MIN_CONTENT_LENGTH = 80

# 같은 파일 중복 처리 방지 쿨다운 (초)
COOLDOWN_SECONDS = 10

# ==============================================================================
# [초기화]
# ==============================================================================
API_KEY = os.environ.get("GEMINI_API_KEY")
if not API_KEY:
    print("❌ 오류: GEMINI_API_KEY 환경변수가 설정되지 않았습니다.")
    print("💡 PowerShell에서 다음 명령어를 실행하세요:")
    print('   [System.Environment]::SetEnvironmentVariable("GEMINI_API_KEY", "your_api_key", "User")')
    exit(1)

client = genai.Client(api_key=API_KEY)

# ==============================================================================
# [유틸]
# ==============================================================================
def should_ignore(path):
    for folder in IGNORE_FOLDERS:
        if os.sep + folder + os.sep in path or path.endswith(os.sep + folder):
            return True
    # 요약 파일 자체는 무시
    if path.endswith("_요약.md"):
        return True
    # 파일 크기 100KB 초과 시 무시
    try:
        if os.path.getsize(path) > 100 * 1024:
            return True
    except:
        pass
    # YAML 프론트매터에 '요약제외: true' 있으면 무시
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read(500)
        if '요약제외: true' in content:
            return True
    except:
        pass
    return False

def detect_note_type(filename, content):
    """노트 유형 자동 감지"""
    import re
    if re.match(r'\d{4}-\d{2}-\d{2}', filename):
        return "daily"
    if any(kw in content for kw in ["냉동", "공조", "압축기", "응축기", "증발기", "냉매", "성적계수"]):
        return "study_refrigeration"
    if any(kw in content for kw in ["OCU", "소방", "강의", "과제", "시험"]):
        return "study_ocu"
    return "general"

def build_prompt(note_type, filename, content, today):
    base_name = os.path.splitext(filename)[0]

    if note_type == "daily":
        return f"""다음은 고용준의 일일 노트다. 핵심만 추출하여 아래 형식으로 출력하라. 감정적 위로 없이 팩트만.

노트 내용:
{content[:3000]}

출력 형식:
---
tags:
  - 자동요약
  - 일일리포트
상태: 완료
날짜: {today}
원본: [[{base_name}]]
---

## 오늘의 팩트
(완료한 일, 진척도 수치 위주)

## 문제점
(막혔던 것, 실패한 것)

## 내일 액션 플랜
(If-Then 형식, 최대 3개)

## 연결 노트
([[관련키워드1]], [[관련키워드2]])
"""

    if note_type == "study_refrigeration":
        return f"""다음은 공조냉동 공부 노트다. 시험에 바로 쓸 수 있는 형태로 요약하라.

노트 내용:
{content[:3000]}

출력 형식:
---
tags:
  - 자동요약
  - 공조냉동
상태: 완료
날짜: {today}
원본: [[{base_name}]]
---

## 핵심 키워드
([[키워드1]], [[키워드2]])

## 공식/순서도
(계산 문제용 알고리즘, 1~3단계)

## 시험 포인트
(자주 나오는 패턴, 조건반사용)
"""

    if note_type == "study_ocu":
        return f"""다음은 OCU 강의 관련 노트다. 오픈북 시험에서 빠르게 찾을 수 있게 정리하라.

노트 내용:
{content[:3000]}

출력 형식:
---
tags:
  - 자동요약
  - OCU
상태: 완료
날짜: {today}
원본: [[{base_name}]]
---

## 핵심 키워드 → 정의
(키워드: 정의, 1:1 매칭 리스트)

## 객관식 함정 포인트
(헷갈리기 쉬운 개념)
"""

    # 일반 노트
    return f"""다음 옵시디언 노트를 분석하고 간결하게 요약하라.

노트 파일명: {filename}
노트 내용:
{content[:3000]}

출력 형식:
---
tags:
  - 자동요약
상태: 완료
날짜: {today}
원본: [[{base_name}]]
---

## 핵심 요약
(2~3문장, 팩트만)

## 키워드
([[키워드1]], [[키워드2]])

## 액션 플랜
(필요 시만, If-Then 형식)
"""

def generate_flowchart(filename, content):
    """공조냉동 문제 → Mermaid 순서도 자동 생성"""
    today = datetime.now().strftime("%Y-%m-%d")
    base_name = os.path.splitext(filename)[0]

    prompt = f"""다음은 공조냉동기계기사 실기 문제 노트다.
문제를 분석하여 풀이 순서도를 Mermaid flowchart 형식으로 만들어라.

규칙:
1. 풀이 단계를 3~6단계로 압축
2. 각 단계: [조건 파악] → [공식 선택] → [수치 대입] → [계산] → [답]
3. 조건문(분기)이 있으면 菱형({{{{조건}}}})으로 표현
4. 공식은 노드 안에 직접 표기 (예: Q = m × Cp × ΔT)
5. Mermaid 코드만 출력, 설명 없음

노트 내용:
{content[:2000]}

출력 형식:
---
tags:
  - 순서도
  - 공조냉동
상태: 완료
날짜: {today}
원본: [[{base_name}]]
---

## 풀이 순서도

```mermaid
flowchart TD
    (여기에 Mermaid 코드)
```

## 핵심 공식
(이 문제에서 사용된 공식만 1줄씩)
"""

    last_err = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt)
            if response.text:
                _increment_usage("flowchart")
                return response.text
        except Exception as e:
            last_err = e
            wait = (attempt + 1) * 2
            time.sleep(wait)
    if last_err:
        log_error(f"순서도 생성 최종 실패: {filename} / {last_err}", last_err)
    return None

def _semantic_chunks(content: str, max_chunk: int = 800) -> list:
    """obsidian_agent.py와 동일한 헤더 기반 청크 전략."""
    body = re.sub(r'^---[\s\S]*?---\n?', '', content.strip())
    sections = re.split(r'(?=\n#{1,3} )', body)
    chunks = []
    for sec in sections:
        sec = sec.strip()
        if not sec:
            continue
        if len(sec) <= max_chunk:
            chunks.append(sec)
        else:
            paras = [p.strip() for p in re.split(r'\n{2,}', sec) if p.strip()]
            buf = ""
            for p in paras:
                if len(buf) + len(p) + 1 <= max_chunk:
                    buf = (buf + "\n\n" + p).strip()
                else:
                    if buf:
                        chunks.append(buf)
                    if len(p) > max_chunk:
                        for i in range(0, len(p), max_chunk):
                            chunks.append(p[i:i+max_chunk])
                    else:
                        buf = p
            if buf:
                chunks.append(buf)
    return [c for c in chunks if len(c.strip()) > 20]


def _score_importance(content: str, filename: str) -> str:
    """obsidian_agent.py와 동일한 중요도 판별."""
    score = 0
    study_kw = ["공조냉동", "냉매", "압축기", "응축기", "증발기", "성적계수", "COP",
                "소방", "방재", "OCU", "시험", "오답", "공식", "계산"]
    event_kw = ["산재", "양악", "병원", "면담", "복직", "마감", "제출", "D-"]
    if re.match(r'\d{4}-\d{2}-\d{2}', filename):
        score += 1
    for kw in study_kw:
        if kw in content:
            score += 1
    for kw in event_kw:
        if kw in content:
            score += 2
    score += min(len(re.findall(r'\[\[.*?\]\]', content)) // 3, 3)
    if score >= 5:   return "HIGH"
    elif score >= 2: return "MEDIUM"
    else:            return "LOW"


def embed_file_to_db(file_path):
    """단일 파일을 임베딩해서 DB에 즉시 반영 (헤더 기반 청크 + 중요도)"""
    try:
        db = {}
        if os.path.exists(DB_FILE):
            with open(DB_FILE, 'r', encoding='utf-8') as f:
                db = json.load(f)

        mtime = os.path.getmtime(file_path)
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        if not content.strip():
            return False

        links = list(set([l.split('|')[0] for l in re.findall(r'\[\[(.*?)\]\]', content)]))
        tags = list(set(re.findall(r'(?<!\S)#([a-zA-Z0-9_가-힣]+)', content)))
        chunks = _semantic_chunks(content)
        importance = _score_importance(content, os.path.basename(file_path))

        if len(chunks) > 150:
            return False

        file_data = {"mtime": mtime, "importance": importance, "chunks": []}
        for c in chunks:
            for attempt in range(2):
                try:
                    res = client.models.embed_content(
                        model="gemini-embedding-001",
                        contents=c,
                        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"))
                    file_data["chunks"].append({
                        "text": c,
                        "embedding": res.embeddings[0].values,
                        "links": links,
                        "tags": tags
                    })
                    break
                except Exception as e:
                    if attempt == 0:
                        time.sleep(0.5)
                    else:
                        log_error(f"임베딩 실패: {os.path.basename(file_path)} / {e}", e)

        db[file_path] = file_data
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(db, f, ensure_ascii=False)
        return True

    except Exception as e:
        log_error(f"DB 업데이트 실패: {file_path} / {e}", e)
        return False

def generate_summary(filename, content):
    today = datetime.now().strftime("%Y-%m-%d")
    note_type = detect_note_type(filename, content)
    prompt = build_prompt(note_type, filename, content, today)

    last_err = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt)
            if response.text:
                _increment_usage("summary")
                return response.text
        except Exception as e:
            last_err = e
            wait = (attempt + 1) * 2
            time.sleep(wait)
    if last_err:
        log_error(f"요약 생성 최종 실패: {filename} / {last_err}", last_err)
    return None

# ==============================================================================
# [파일 감시 핸들러]
# ==============================================================================
class VaultEventHandler(FileSystemEventHandler):
    def __init__(self):
        self.cooldown = {}

    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            self._handle(event.src_path, "새 파일")

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.md'):
            now = time.time()
            last = self.cooldown.get(event.src_path, 0)
            if now - last < COOLDOWN_SECONDS:
                return
            self.cooldown[event.src_path] = now
            self._handle(event.src_path, "수정됨")

    def _handle(self, path, event_type):
        if should_ignore(path):
            return

        filename = os.path.basename(path)
        print(f"\n📄 [{event_type}] {filename}")

        # 파일이 완전히 저장될 때까지 대기
        time.sleep(1.5)

        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()

            if len(content.strip()) < MIN_CONTENT_LENGTH:
                print(f"   ⏭️ 내용 부족 ({len(content.strip())}자), 건너뜀")
                return

            print(f"   🤖 Gemini 요약 생성 중...")
            summary = generate_summary(filename, content)

            if not summary:
                print(f"   ❌ 요약 생성 실패")
                return

            base_name = os.path.splitext(filename)[0]
            summary_path = os.path.join(SUMMARY_FOLDER, f"{base_name}_요약.md")

            with open(summary_path, 'w', encoding='utf-8') as f:
                f.write(summary)

            print(f"   ✅ 요약 저장 완료 → Processed/{base_name}_요약.md")

            # 공조냉동 노트이면 순서도도 생성
            if detect_note_type(filename, content) == "study_refrigeration":
                print(f"   순서도 생성 중...")
                flowchart = generate_flowchart(filename, content)
                if flowchart:
                    flowchart_path = os.path.join(SUMMARY_FOLDER, f"{base_name}_순서도.md")
                    with open(flowchart_path, 'w', encoding='utf-8') as f:
                        f.write(flowchart)
                    print(f"   ✅ 순서도 저장 완료 → Processed/{base_name}_순서도.md")
                    embed_file_to_db(flowchart_path)

            # 원본 + 요약 파일 둘 다 DB에 즉시 반영
            print(f"   DB 업데이트 중...")
            ok1 = embed_file_to_db(path)
            ok2 = embed_file_to_db(summary_path)
            if ok1 and ok2:
                print(f"   DB 업데이트 완료 (온유가 바로 검색 가능)")
            else:
                print(f"   DB 업데이트 부분 실패 (다음 sync 시 반영됨)")

        except Exception as e:
            log_error(f"파일 처리 실패: {filename} / {e}", e)

# ==============================================================================
# [SYSTEM 폴더 감시 핸들러]
# ==============================================================================
class SystemFolderHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory:
            print(f"\n📁 [SYSTEM 변경] {os.path.basename(event.src_path)} 추가 → 맵 갱신 중...")
            generate_project_map()

    def on_deleted(self, event):
        if not event.is_directory:
            print(f"\n📁 [SYSTEM 변경] {os.path.basename(event.src_path)} 삭제 → 맵 갱신 중...")
            generate_project_map()

# ==============================================================================
# [메인]
# ==============================================================================
AUTO_SYNC_HOURS = 12  # 자동 sync 주기 (시간) — 증분 sync는 빠르나 여유있게 설정
SYNC_LOCK_FILE  = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", ".sync_lock")

def _auto_sync_loop():
    """백그라운드에서 주기적으로 obsidian_agent sync 실행. 중복 실행 방지."""
    import subprocess, sys
    agent_path = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM", "obsidian_agent.py")
    while True:
        time.sleep(AUTO_SYNC_HOURS * 3600)

        # 이미 sync 중이면 건너뜀
        if os.path.exists(SYNC_LOCK_FILE):
            print("⏭️  [자동 학습] 이전 동기화 진행 중 → 건너뜀")
            continue

        print(f"\n🧠 [자동 학습] {AUTO_SYNC_HOURS}시간 경과 → 백그라운드 동기화 시작...")
        try:
            # 락 파일 생성
            with open(SYNC_LOCK_FILE, 'w') as f:
                f.write(str(time.time()))

            subprocess.run([sys.executable, agent_path, "--sync"],
                           capture_output=True, timeout=7200)  # 최대 2시간
            print("✅ [자동 학습] 백그라운드 동기화 완료")
        except Exception as e:
            print(f"❌ [자동 학습] 실패: {e}")
        finally:
            # 락 파일 제거
            try: os.remove(SYNC_LOCK_FILE)
            except: pass

if __name__ == "__main__":
    os.makedirs(SUMMARY_FOLDER, exist_ok=True)

    print("=" * 52)
    print("  🌟 온유 자동 요약 모드 가동")
    print("=" * 52)
    print(f"📂 감시 경로: {OBSIDIAN_VAULT_PATH}")
    print(f"📝 요약 저장: Processed/")
    print(f"🚫 제외 폴더: {', '.join(IGNORE_FOLDERS)}")
    print(f"🧠 자동 학습: {AUTO_SYNC_HOURS}시간마다 백그라운드 동기화")
    print(f"\n💡 새 노트를 저장하면 자동으로 요약이 생성됩니다.")
    print("   종료하려면 Ctrl+C 를 누르세요.\n")

    # 백그라운드 자동 sync 스레드 시작
    import threading
    sync_thread = threading.Thread(target=_auto_sync_loop, daemon=True)
    sync_thread.start()

    handler = VaultEventHandler()
    system_handler = SystemFolderHandler()
    observer = Observer()
    observer.schedule(handler, OBSIDIAN_VAULT_PATH, recursive=True)
    observer.schedule(system_handler, SYSTEM_PATH, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n온유 자동 요약 모드 종료.")

    observer.join()