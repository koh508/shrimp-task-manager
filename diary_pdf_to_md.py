"""
diary_pdf_to_md.py - 블로그 일기 PDF → Obsidian DAILY 마크다운 변환기
사용법: python diary_pdf_to_md.py
"""
import os, re, sys, json
from datetime import datetime
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# [설정]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
DAILY_DIR        = os.path.join(OBSIDIAN_VAULT_PATH, "DAILY")
DAILY_ATTACH_DIR = os.path.join(OBSIDIAN_VAULT_PATH, "DAILY", "attachments")
PDF_DIR          = os.path.join(OBSIDIAN_VAULT_PATH, "Study PDF", "일기")
CHUNK_PAGES = 2    # 일기는 페이지당 여러 날짜 가능 → 작게 끊기
IMAGE_DPI   = 150

# ==============================================================================
# [초기화]
# ==============================================================================
def get_api_key():
    import subprocess
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        result = subprocess.run(
            ['powershell', '-Command',
             "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')"],
            capture_output=True, text=True)
        key = result.stdout.strip()
    return key

def get_client():
    from google import genai
    from google.genai import types
    key = get_api_key()
    if not key:
        print("오류: GEMINI_API_KEY 환경변수 없음")
        sys.exit(1)
    return genai.Client(api_key=key), types

# ==============================================================================
# [PDF → 이미지]
# ==============================================================================
def pages_to_images(pdf_path, start, end):
    doc = fitz.open(pdf_path)
    end = min(end, len(doc))
    images = []
    for i in range(start - 1, end):
        images.append(doc[i].get_pixmap(dpi=IMAGE_DPI).tobytes("png"))
    return images, len(doc)

def extract_figures(pdf_path, start_page, end_page):
    """페이지별 내장 래스터 이미지 추출 (100KB 이상만).
    반환: {청크내순서(1-based): [{'bytes':..., 'ext':...}, ...]}"""
    doc = fitz.open(pdf_path)
    end_page = min(end_page, len(doc))
    figures = {}
    for chunk_idx, page_num in enumerate(range(start_page - 1, end_page), start=1):
        page = doc[page_num]
        seen, page_figs = set(), []
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen:
                continue
            seen.add(xref)
            img_data = doc.extract_image(xref)
            if len(img_data.get('image', b'')) >= 100_000:
                page_figs.append({'bytes': img_data['image'],
                                  'ext':   img_data.get('ext', 'png')})
        if page_figs:
            figures[chunk_idx] = page_figs
    return figures

def replace_image_markers(content, figures, page_images, page_start, img_dir, name_prefix):
    """content 안의 IMAGE_P{N}_{N} 마커를 ![[파일명]] 으로 교체하고 이미지 파일 저장."""
    saved = set()
    def replace(match):
        ci, fi = int(match.group(1)), int(match.group(2))
        actual_page = page_start + ci - 1
        page_figs   = figures.get(ci, [])
        if fi <= len(page_figs):
            fig      = page_figs[fi - 1]
            filename = f"{name_prefix}_p{actual_page:03d}_fig{fi:02d}.{fig['ext']}"
            img_bytes = fig['bytes']
        else:
            filename  = f"{name_prefix}_p{actual_page:03d}_render.png"
            img_bytes = page_images[ci - 1] if (ci - 1) < len(page_images) else None
        if img_dir and img_bytes:
            os.makedirs(img_dir, exist_ok=True)
            fpath = os.path.join(img_dir, filename)
            if fpath not in saved:
                with open(fpath, 'wb') as f:
                    f.write(img_bytes)
                saved.add(fpath)
        return f"\n![[{filename}]]\n"
    # 모든 마커 형식 처리 (pdf_to_md.py 동일)
    for pat in [r'!\[.*?\]\(IMAGE_P(\d+)_(\d+)[^)]*\)',
                r'!\[\[IMAGE_P(\d+)_(\d+)\]\]',
                r'\[\[IMAGE_P(\d+)_(\d+)\]\]',
                r'\bIMAGE_P(\d+)_(\d+)\b']:
        content = re.sub(pat, replace, content)
    return content

# ==============================================================================
# [파일명에서 연도 힌트 추출]
# ==============================================================================
def infer_year_from_filename(filename):
    """
    파일명 패턴으로 연도 범위 추출.
    예) "17년 10월 ~ 12월.pdf" → 2017
        "26년~25년 4월까지 일기.pdf" → (2025, 2026) 중 시작 연도
    """
    name = os.path.basename(filename)
    # "XX년" 패턴 전부 추출
    years_raw = re.findall(r'(\d{2,4})년', name)
    years = []
    for y in years_raw:
        y = int(y)
        if y < 100:
            y = 2000 + y if y <= 30 else 1900 + y
        years.append(y)
    if years:
        return min(years)  # 가장 이른 연도를 기준
    return datetime.now().year

# ==============================================================================
# [Gemini Vision → 일기 항목 JSON 추출]
# ==============================================================================
def extract_entries(client, types, page_images, page_label, year_hint,
                    figures=None, page_start=1, img_dir=None, name_prefix="diary"):
    """
    일기 페이지에서 날짜별 항목을 JSON으로 추출.
    반환: [{"date": "YYYY-MM-DD" or null, "title": str or null, "content": str}]
    """
    if figures is None:
        figures = {}
    prompt = f"""다음은 개인 블로그에서 내보낸 일기 PDF의 {page_label} 페이지다.
기준 연도 힌트: {year_hint}년

모든 일기 항목을 아래 JSON 배열로 추출하라. 설명 없이 JSON만 출력하라.

[
  {{
    "date": "YYYY-MM-DD",
    "title": null,
    "content": "마크다운 본문"
  }}
]

추출 규칙:
1. 날짜 변환:
   - "17년 10월 3일", "10월 3일", "10.03", "2017-10-03" 등 → "2017-10-03" (ISO 형식)
   - 연도 없으면 힌트({year_hint}년) 사용
   - 날짜를 확정할 수 없으면 "date": null, "title": 글제목이나 첫 문장 15자
2. 한 페이지에 여러 날짜가 있으면 각각 별도 항목으로 분리
3. 본문은 원문 그대로 보존 (감정, 줄바꿈, 구어체 유지)
4. 마크다운 정리: 소제목 ##, 목록 -, 강조 **굵게**
5. 이미지/사진/그림 자리에는 반드시 아래 형식을 빈 줄 포함해 단독으로 삽입:

IMAGE_P{{청크내페이지번호}}_{{해당페이지내그림순번}}

   예) 첫 번째 페이지의 첫 번째 이미지 → IMAGE_P1_1
   규칙: 한 줄에 이 텍스트만, 앞뒤 빈 줄, 괄호/느낌표/마크다운 문법 절대 금지
6. 블로그 메뉴, 광고, 헤더/푸터 텍스트는 제외"""

    contents = []
    for img in page_images:
        contents.append(types.Part(
            inline_data=types.Blob(data=img, mime_type="image/png")))
    contents.append(prompt)

    import time
    for attempt in range(5):
        try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=contents,
                config=types.GenerateContentConfig(
                    thinking_config=types.ThinkingConfig(thinking_budget=0)))
            break
        except Exception as e:
            if any(x in str(e) for x in ['503', '500', 'UNAVAILABLE', 'INTERNAL']):
                wait = 15 * (attempt + 1)
                print(f"\n  서버 오류 {wait}초 후 재시도 ({attempt+1}/5)...", end=" ")
                time.sleep(wait)
            else:
                raise

    # response.text가 None이면 (안전필터 차단 또는 빈 응답) 빈 항목 반환
    if not response.text:
        print(f"\n  ⚠ 빈 응답 ({page_label}), 건너뜀 (안전필터 차단 가능성)")
        return []

    text = response.text.strip()

    # 1차: 코드블록 래퍼 제거
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'^```\s*',     '', text)
    text = re.sub(r'\s*```$',     '', text).strip()

    # 2차: 텍스트 안에서 JSON 배열 부분만 추출 (Gemini가 설명을 앞뒤에 붙이는 경우 대응)
    def extract_json(raw):
        # strict=False: JSON 문자열 내 실제 줄바꿈/탭 허용 (Gemini 비이스케이프 대응)
        for candidate in [raw,
                          re.search(r'(\[.*\])', raw, re.DOTALL),
                          re.search(r'(\{.*\})', raw, re.DOTALL)]:
            s = candidate.group(1) if hasattr(candidate, 'group') else candidate
            if not s:
                continue
            for strict in (False, True):
                try:
                    result = json.loads(s, strict=strict)
                    return [result] if isinstance(result, dict) else result
                except (json.JSONDecodeError, TypeError):
                    pass
        return None

    result = extract_json(text)
    if result is not None:
        if isinstance(result, dict):
            result = [result]
        # 이미지 마커 → ![[파일명]] 교체
        if img_dir:
            for e in result:
                if e.get("content"):
                    e["content"] = replace_image_markers(
                        e["content"], figures, page_images,
                        page_start, img_dir, name_prefix)
        return result

    # 모든 파싱 실패 → 원문 출력 후 보존
    print(f"\n  ⚠ JSON 파싱 실패 ({page_label}), 원문 보존")
    print(f"  [DEBUG 전체길이: {len(text)}자]")
    print(f"  [앞 300자]\n{text[:300]}")
    print(f"  [뒤 200자]\n{text[-200:]}\n  [/DEBUG]")
    return [{"date": None,
             "title": f"파싱오류_{page_label}",
             "content": text}]

# ==============================================================================
# [마크다운 파일 포맷]
# ==============================================================================
def format_diary_md(date, contents_list, source_pdf):
    """날짜 기반 파일 포맷 (여러 항목 병합)"""
    today = datetime.now().strftime("%Y-%m-%d")
    body = "\n\n---\n\n".join(contents_list) if len(contents_list) > 1 else contents_list[0]

    return f"""---
tags:
  - 일기
  - PDF변환
날짜: {date}
출처: 사용자 제공
원본: {os.path.basename(source_pdf)}
변환일: {today}
---

# {date} 일기

{body}
"""

def format_untitled_md(title, content, source_pdf):
    """날짜 없는 항목 포맷"""
    today = datetime.now().strftime("%Y-%m-%d")
    safe_title = re.sub(r'[\\/:*?"<>|\n\r\t]', '_', (title or "제목없음"))
    safe_title = re.sub(r'_+', '_', safe_title).strip('_ ')[:50]

    md = f"""---
tags:
  - 일기
  - PDF변환
날짜: {today}
출처: 사용자 제공
원본: {os.path.basename(source_pdf)}
변환일: {today}
---

# {title or "제목없음"}

{content}
"""
    return safe_title, md

# ==============================================================================
# [파일 저장 — 기존 파일 있으면 병합]
# ==============================================================================
def save_file(fpath, content, is_new, source_marker=""):
    """
    신규: 전체 내용 저장
    기존 파일 존재: 동일 출처 마커가 없을 때만 본문 추가 (중복 방지)
    """
    if is_new:
        with open(fpath, 'w', encoding='utf-8') as f:
            f.write(content)
    else:
        # 동일 출처 이미 존재하면 건너뜀
        with open(fpath, 'r', encoding='utf-8') as f:
            existing = f.read()
        if source_marker and source_marker in existing:
            return "중복"
        body_only = re.sub(r'^---.*?---\n+', '', content, flags=re.DOTALL)
        with open(fpath, 'a', encoding='utf-8') as f:
            f.write(f"\n\n---\n{source_marker}\n\n{body_only}")
    return "완료"

# ==============================================================================
# [PDF 1개 처리]
# ==============================================================================
def process_pdf(client, types, pdf_path):
    year_hint   = infer_year_from_filename(pdf_path)
    doc         = fitz.open(pdf_path)
    total       = len(doc)
    basename    = os.path.basename(pdf_path)
    # 이미지 저장 폴더 = DAILY/attachments/ (MD 파일과 분리)
    img_dir     = DAILY_ATTACH_DIR
    name_prefix = re.sub(r'[\\/:*?"<>|\s]', '_', os.path.splitext(basename)[0])[:30]

    print(f"\n📄 {basename}  ({total}페이지, 기준연도: {year_hint})")

    # 날짜별 항목 수집 dict
    date_entries  = {}   # {"YYYY-MM-DD": ["본문1", "본문2", ...]}
    untitled_list = []   # [{"title": ..., "content": ...}]

    for ps in range(1, total + 1, CHUNK_PAGES):
        pe = min(ps + CHUNK_PAGES - 1, total)
        label   = f"p{ps}-{pe}"
        print(f"  [{ps}/{total}] {label} ...", end=" ", flush=True)

        images, _  = pages_to_images(pdf_path, ps, pe)
        figures    = extract_figures(pdf_path, ps, pe)
        total_figs = sum(len(v) for v in figures.values())
        if total_figs:
            print(f"(이미지 {total_figs}개) ", end="", flush=True)

        entries = extract_entries(client, types, images, label, year_hint,
                                  figures=figures, page_start=ps,
                                  img_dir=img_dir, name_prefix=name_prefix)

        for e in entries:
            date    = e.get("date")
            title   = e.get("title")
            content = (e.get("content") or "").strip()
            if not content:
                continue

            if date and re.match(r'\d{4}-\d{2}-\d{2}', date):
                date_entries.setdefault(date, []).append(content)
            else:
                fallback_title = re.sub(r'[\n\r\t\\/:*?"<>|]+', ' ', title or content[:30]).strip()[:40]
                untitled_list.append({
                    "title":   fallback_title or "제목없음",
                    "content": content
                })

        found = len(entries)
        print(f"{found}항목 추출")

    # ── 저장 ──────────────────────────────────────────
    saved = []
    os.makedirs(DAILY_DIR, exist_ok=True)
    # 출처 마커: 같은 PDF를 두 번 실행해도 중복 삽입 방지
    source_marker = f"<!-- PDF출처: {basename} -->"

    # 날짜 기반 파일
    for date in sorted(date_entries.keys()):
        fpath  = os.path.join(DAILY_DIR, f"{date}.md")
        is_new = not os.path.exists(fpath)
        md     = format_diary_md(date, date_entries[date], pdf_path)
        result = save_file(fpath, md, is_new, source_marker)
        if result == "중복":
            status = "중복(건너뜀)"
        else:
            status = "신규" if is_new else "병합"
        saved.append((f"{date}.md", status))

    # 날짜 없는 항목
    for u in untitled_list:
        safe_title, md = format_untitled_md(u["title"], u["content"], pdf_path)
        fpath  = os.path.join(DAILY_DIR, f"{safe_title}.md")
        is_new = not os.path.exists(fpath)
        result = save_file(fpath, md, is_new, source_marker)
        if result == "중복":
            status = "중복(건너뜀)"
        else:
            status = "신규" if is_new else "병합"
        saved.append((f"{safe_title}.md", status))

    return saved

# ==============================================================================
# [메인]
# ==============================================================================
def main():
    print("=" * 56)
    print("  일기 PDF → Obsidian DAILY 변환기")
    print("=" * 56)

    # PDF 목록
    pdfs = sorted([
        os.path.join(PDF_DIR, f)
        for f in os.listdir(PDF_DIR)
        if f.lower().endswith('.pdf')
    ])

    if not pdfs:
        print(f"\nPDF 없음: {PDF_DIR}")
        return

    print(f"\n[PDF 목록]  {PDF_DIR}")
    for i, p in enumerate(pdfs, 1):
        size = os.path.getsize(p) / (1024 * 1024)
        print(f"  {i:2}. {os.path.basename(p)}  ({size:.1f}MB)")

    print("\n변환할 번호 입력 (예: 1,3,5 / 전체=all / 범위=1-5)")
    sel = input("선택: ").strip().lower()

    selected = []
    if sel == "all":
        selected = pdfs
    elif '-' in sel and ',' not in sel:
        a, b = sel.split('-')
        selected = pdfs[int(a)-1 : int(b)]
    else:
        for s in sel.split(','):
            s = s.strip()
            if s.isdigit():
                idx = int(s) - 1
                if 0 <= idx < len(pdfs):
                    selected.append(pdfs[idx])

    if not selected:
        print("선택 없음. 종료.")
        return

    print(f"\n선택된 파일 {len(selected)}개")
    print(f"저장 경로: {DAILY_DIR}")
    confirm = input("시작할까요? (y/n): ").strip().lower()
    if confirm != 'y':
        return

    client, types = get_client()

    total_saved = []
    for pdf in selected:
        try:
            saved = process_pdf(client, types, pdf)
            total_saved.extend(saved)
        except Exception as e:
            print(f"\n  ❌ 오류: {os.path.basename(pdf)} — {e}")
            continue

    # ── 최종 요약 ──
    print("\n" + "=" * 56)
    print(f"✅ 변환 완료 — 총 {len(total_saved)}개 파일")
    new_count   = sum(1 for _, s in total_saved if s == "신규")
    merge_count = sum(1 for _, s in total_saved if s == "병합")
    print(f"   신규: {new_count}개 / 기존 파일 병합: {merge_count}개")
    print(f"   저장 위치: {DAILY_DIR}")
    print("=" * 56)


if __name__ == "__main__":
    main()
