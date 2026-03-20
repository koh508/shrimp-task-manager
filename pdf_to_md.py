"""
pdf_to_md.py - OCU 강의 PDF → 옵시디언 마크다운 변환기 (Gemini Vision 버전)
사용법: python pdf_to_md.py
"""
import os, re, sys, math, subprocess
from datetime import datetime
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# [설정]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
OUTPUT_FOLDER     = os.path.join(OBSIDIAN_VAULT_PATH, "OCU")
WORK_PDF_FOLDER   = os.path.join(OBSIDIAN_VAULT_PATH, "Work Folder")
WORK_OUT_FOLDER   = os.path.join(OBSIDIAN_VAULT_PATH, "업무자료")
DAILY_ATTACH_DIR  = os.path.join(OBSIDIAN_VAULT_PATH, "DAILY", "attachments")
CHUNK_PAGES = 5
IMAGE_DPI = 150
MIN_FIG_SIZE = 150          # px 이하 아이콘/장식 제외
MAX_FILE_SIZE_KB = 50       # 이 용량 초과 시 자동 파일 분할 (온유 200KB 제한 대응)

# ==============================================================================
# [초기화]
# ==============================================================================
def get_api_key():
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        result = subprocess.run(
            ['powershell', '-Command', "[System.Environment]::GetEnvironmentVariable('GEMINI_API_KEY', 'User')"],
            capture_output=True, text=True)
        key = result.stdout.strip()
    return key

def get_client():
    from google import genai
    from google.genai import types
    key = get_api_key()
    if not key:
        print("오류: GEMINI_API_KEY 없음")
        sys.exit(1)
    return genai.Client(api_key=key), types

# ==============================================================================
# [PDF 처리]
# ==============================================================================
def get_total_pages(pdf_path):
    return len(fitz.open(pdf_path))

def pages_to_images(pdf_path, start_page, end_page):
    """페이지 렌더링 이미지 (Gemini Vision용 + 벡터 폴백용)"""
    doc = fitz.open(pdf_path)
    total = len(doc)
    end_page = min(end_page, total)
    images = []
    for i in range(start_page - 1, end_page):
        pixmap = doc[i].get_pixmap(dpi=IMAGE_DPI)
        images.append(pixmap.tobytes("png"))
    return images, total

def extract_figures(pdf_path, start_page, end_page):
    """
    페이지별 내장 래스터 이미지 추출 (실제 사진/이미지만, 1MB 이상).
    대부분의 공학 도면은 벡터라 페이지 렌더링으로 폴백됨.
    반환: {청크내순서: [{'bytes':..., 'ext':...}, ...]}
    """
    doc = fitz.open(pdf_path)
    end_page = min(end_page, len(doc))
    figures = {}

    for chunk_idx, page_num in enumerate(range(start_page - 1, end_page), start=1):
        page = doc[page_num]
        seen = set()
        page_figs = []
        for img_info in page.get_images(full=True):
            xref = img_info[0]
            if xref in seen:
                continue
            seen.add(xref)
            img_data = doc.extract_image(xref)
            # 실제 사진/이미지만 (파일 크기 100KB 이상인 것만)
            if len(img_data.get('image', b'')) >= 100_000:
                page_figs.append({
                    'bytes': img_data['image'],
                    'ext': img_data.get('ext', 'png')
                })
        if page_figs:
            figures[chunk_idx] = page_figs

    return figures

# ==============================================================================
# [Gemini Vision → 마크다운 변환]
# ==============================================================================
def convert_to_md(client, types, page_images, figures, subject, chapter, page_range,
                  first_chunk=False, page_start=1, img_dir=None, name_prefix="p",
                  doc_context="OCU 강의 PDF", extra_tags=None):
    today = datetime.now().strftime("%Y-%m-%d")
    tags = (extra_tags or ["OCU", subject])
    tag_lines = "\n".join(f"  - {t}" for t in tags)

    frontmatter = f"""---
tags:
{tag_lines}
상태: 완료
날짜: {today}
페이지: {page_range}
분류: {subject}
---

# {chapter}
""" if first_chunk else ""

    prompt = f"""다음은 {doc_context} {page_range} 페이지 이미지다 (P1~P{len(page_images)}).
분류: {subject} / 문서: {chapter}

[변환 규칙]
1. YAML 프론트매터 {"포함" if first_chunk else "생략"}
2. 모든 텍스트 → 마크다운
3. 수식/공식: 반드시 LaTeX 문법 사용
   - 인라인: $수식$  예) $Q = mc\\Delta T$
   - 블록: $$수식$$  예) $$COP = \\frac{{Q_L}}{{W}}$$
   - 단위: $\\text{{kW}}$, $\\text{{kJ/kg}}$, $^\\circ\\text{{C}}$, $\\text{{m}}^2$ 등
4. 표: 헤더/구분선/정렬 완비한 마크다운 표로 변환 (표는 인용블록 밖에 독립적으로)
   | 항목 | 값 | 단위 |
   |:---|---:|:---:|
5. 페이지 번호, 반복 머리글/꼬리글 제거
6. 중요 개념 **볼드** (표와 수식은 인용블록 안에 넣지 말 것)
7. 그림/도표/그래프/배관도/선도 자리에는 다음 형식을 빈 줄 포함해 단독 삽입:

IMAGE_P{{청크내페이지번호}}_{{해당페이지내그림순번}}

   예) P2의 첫 번째 그림 → IMAGE_P2_1
   규칙: 한 줄에 이 텍스트만, 앞뒤 빈 줄, 괄호/느낌표/마크다운 문법 절대 금지

{frontmatter}(변환 결과)"""

    contents = []
    for img_bytes in page_images:
        contents.append(types.Part(
            inline_data=types.Blob(data=img_bytes, mime_type="image/png")
        ))
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
            if '503' in str(e) or 'UNAVAILABLE' in str(e) or '500' in str(e) or 'INTERNAL' in str(e):
                wait = 15 * (attempt + 1)
                print(f"\n  서버 오류, {wait}초 후 재시도 ({attempt+1}/5)...", end=" ")
                time.sleep(wait)
            else:
                raise

    text = response.text.strip()
    # ```yaml, ```markdown, ``` 등 모든 코드블록 래퍼 제거
    text = re.sub(r'^```\w*\n', '', text)
    text = re.sub(r'\n```$', '', text)

    # 마커 → 이미지 파일로 교체
    # 충분히 큰 래스터 이미지가 있으면 사용, 없으면 해당 페이지 렌더링으로 폴백
    saved_pages = set()  # 페이지 렌더링 중복 저장 방지

    def replace_marker(match):
        ci, fi = int(match.group(1)), int(match.group(2))
        actual_page = page_start + ci - 1
        page_figs = figures.get(ci, [])

        if fi <= len(page_figs):
            # 내장 래스터 이미지 사용
            fig = page_figs[fi - 1]
            filename = f"{name_prefix}_p{actual_page:03d}_fig{fi:02d}.{fig['ext']}"
            img_bytes = fig['bytes']
        else:
            # 벡터/기타: 해당 페이지 전체 렌더링
            filename = f"{name_prefix}_p{actual_page:03d}_render.png"
            img_bytes = page_images[ci - 1] if (ci - 1) < len(page_images) else None

        if img_dir and img_bytes:
            os.makedirs(img_dir, exist_ok=True)
            filepath = os.path.join(img_dir, filename)
            if filepath not in saved_pages:
                with open(filepath, 'wb') as f:
                    f.write(img_bytes)
                saved_pages.add(filepath)

        return f"\n![[{filename}]]\n"

    # 모든 마커 형식 처리
    text = re.sub(r'!\[.*?\]\(IMAGE_P(\d+)_(\d+)[^)]*\)', replace_marker, text)
    text = re.sub(r'!\[\[IMAGE_P(\d+)_(\d+)\]\]', replace_marker, text)
    text = re.sub(r'\[\[IMAGE_P(\d+)_(\d+)\]\]', replace_marker, text)
    text = re.sub(r'\bIMAGE_P(\d+)_(\d+)\b', replace_marker, text)
    return text

# ==============================================================================
# [메인]
# ==============================================================================
def _scan_pdfs(folder):
    pdfs = []
    if os.path.exists(folder):
        for root, _, files in os.walk(folder):
            for f in sorted(files):
                if f.lower().endswith('.pdf'):
                    pdfs.append(os.path.join(root, f))
    return pdfs

def _print_pdf_list(pdfs, base_dir):
    if not pdfs:
        print("  (PDF 없음)")
        return
    for i, f in enumerate(pdfs, 1):
        size = os.path.getsize(f) / (1024 * 1024)
        rel  = os.path.relpath(f, base_dir)
        print(f"  {i:2}. {rel}  ({size:.1f}MB)")

def _run_conversion(client, types, pdf_path, start, end,
                    subject, chapter, out_dir, doc_context, extra_tags,
                    img_dir=None):
    safe_chapter = re.sub(r'[\\/:*?"<>|]', '_', chapter)
    os.makedirs(out_dir, exist_ok=True)
    # 이미지 저장 폴더: 별도 지정 없으면 md와 같은 폴더
    if img_dir is None:
        img_dir = out_dir
    os.makedirs(img_dir, exist_ok=True)
    total_pages = end - start + 1

    print(f"\n변환 중... ({start}~{end}p, {total_pages}페이지)")
    print(f"예상 비용: ~{total_pages * 0.4:.0f}원")
    print(f"용량 초과 시 자동 분할 ({MAX_FILE_SIZE_KB}KB 기준)\n")

    saved_files   = []
    cur_chunks    = []   # 현재 파일에 누적된 청크
    cur_size      = 0    # 현재 파일 누적 용량 (bytes)
    file_idx      = 0
    file_first    = True # 현재 파일의 첫 번째 청크 여부

    def _flush(last_page):
        nonlocal cur_chunks, cur_size, file_idx, file_first
        if not cur_chunks:
            return
        file_idx += 1
        content  = "\n\n---\n\n".join(cur_chunks)
        fname    = f"{safe_chapter}_part{file_idx}.md"
        out_path = os.path.join(out_dir, fname)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write(content)
        kb = len(content.encode('utf-8')) / 1024
        saved_files.append((out_path, fname))
        print(f"  → 저장: {fname}  ({kb:.0f}KB)\n")
        cur_chunks = []
        cur_size   = 0
        file_first = True  # 다음 파일의 첫 청크

    for ps in range(start, end + 1, CHUNK_PAGES):
        pe = min(ps + CHUNK_PAGES - 1, end)
        print(f"  [{ps}/{end}] {ps}-{pe}p ...", end=" ", flush=True)

        page_images, _ = pages_to_images(pdf_path, ps, pe)
        figures        = extract_figures(pdf_path, ps, pe)
        total_figs     = sum(len(v) for v in figures.values())
        if total_figs:
            print(f"(이미지 {total_figs}개) ", end="")

        md = convert_to_md(
            client, types, page_images, figures, subject, chapter,
            page_range  = f"{ps}-{pe}",
            first_chunk = file_first,
            page_start  = ps,
            img_dir     = img_dir,
            name_prefix = safe_chapter,
            doc_context = doc_context,
            extra_tags  = extra_tags,
        )
        chunk_size = len(md.encode('utf-8'))

        # 현재 청크 추가 전에 용량 초과 여부 확인
        if cur_chunks and (cur_size + chunk_size) > MAX_FILE_SIZE_KB * 1024:
            _flush(ps - 1)

        cur_chunks.append(md)
        cur_size   += chunk_size
        file_first  = False
        print(f"완료  (누적 {cur_size//1024}KB)")

    _flush(end)  # 마지막 파일 저장

    # 파일이 1개뿐이면 _part1 접미사 제거
    if len(saved_files) == 1:
        old_path, old_name = saved_files[0]
        new_name = f"{safe_chapter}.md"
        new_path = os.path.join(out_dir, new_name)
        os.rename(old_path, new_path)
        saved_files[0] = (new_path, new_name)

    return saved_files, out_dir


def main():
    print("=" * 54)
    print("  PDF → 마크다운 변환기 (Gemini Vision)")
    print("=" * 54)
    print("\n[카테고리 선택]")
    print("  1. OCU 강의자료   → OCU/과목명/")
    print("  2. 업무/현장자료  → 업무자료/분류/")
    print("  3. 직접 경로 입력")
    cat = input("\n번호: ").strip()

    # ── 카테고리별 설정 ──────────────────────────────
    if cat == '1':
        pdf_dir     = os.path.join(OBSIDIAN_VAULT_PATH, "Study PDF")
        out_base    = OUTPUT_FOLDER
        doc_context = "OCU 강의 PDF"
        subj_label  = "과목명 (예: 공조냉동기계기사)"
        chap_label  = "단원명 (예: 1장 냉동사이클)"
        tag_prefix  = "OCU"

    elif cat == '2':
        os.makedirs(WORK_PDF_FOLDER, exist_ok=True)
        pdf_dir     = WORK_PDF_FOLDER
        out_base    = WORK_OUT_FOLDER
        doc_context = "업무/현장 PDF 문서"
        subj_label  = "분류 (예: 안전관리, 설비도면, 공정자료)"
        chap_label  = "문서명 (예: 소각로 운전매뉴얼)"
        tag_prefix  = "업무자료"

    else:
        pdf_dir     = None
        out_base    = os.path.join(OBSIDIAN_VAULT_PATH, "변환문서",
                                   datetime.now().strftime("%Y-%m-%d"))
        doc_context = "PDF 문서"
        subj_label  = "분류"
        chap_label  = "문서명"
        tag_prefix  = "변환문서"

    # ── PDF 선택 ────────────────────────────────────
    if pdf_dir:
        pdfs = _scan_pdfs(pdf_dir)
        if not pdfs:
            print(f"\n  PDF 없음: {pdf_dir}")
            print("  해당 폴더에 PDF를 넣고 재실행하세요.")
            return
        print(f"\n[PDF 목록]  ({pdf_dir})")
        _print_pdf_list(pdfs, pdf_dir)
        idx      = int(input("\n번호 선택: ")) - 1
        pdf_path = pdfs[idx]
    else:
        pdf_path = input("\nPDF 경로 (드래그 앤 드롭): ").strip().strip('"')
        if not os.path.exists(pdf_path):
            print("파일 없음"); return

    # ── 페이지 범위 ──────────────────────────────────
    total = get_total_pages(pdf_path)
    print(f"\n총 페이지: {total}")
    start_inp = input(f"시작 페이지 (엔터=1): ").strip()
    end_inp   = input(f"끝 페이지   (엔터={total}): ").strip()
    start = int(start_inp) if start_inp else 1
    end   = int(end_inp)   if end_inp   else total

    # ── 메타데이터 ───────────────────────────────────
    subject = input(f"{subj_label}: ").strip()
    chapter = input(f"{chap_label}: ").strip()
    if not subject: subject = "미분류"
    if not chapter: chapter = os.path.splitext(os.path.basename(pdf_path))[0]

    extra_tags = [tag_prefix, subject]
    out_dir    = os.path.join(out_base, subject)

    client, types = get_client()

    # ── 변환 실행 ────────────────────────────────────
    saved_files, out_dir = _run_conversion(
        client, types, pdf_path, start, end,
        subject, chapter, out_dir, doc_context, extra_tags,
        img_dir=DAILY_ATTACH_DIR)

    # ── 최종 요약 ────────────────────────────────────
    saved_imgs = sum(
        1 for f in os.listdir(DAILY_ATTACH_DIR)
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ) if os.path.exists(DAILY_ATTACH_DIR) else 0

    rel_base   = os.path.relpath(out_dir, OBSIDIAN_VAULT_PATH)
    rel_attach = os.path.relpath(DAILY_ATTACH_DIR, OBSIDIAN_VAULT_PATH)
    print("=" * 54)
    print(f"✅ 변환 완료")
    for _, fname in saved_files:
        print(f"   {rel_base}/{fname}")
    print(f"   이미지: {saved_imgs}개 → {rel_attach}/")
    print("=" * 54)

if __name__ == "__main__":
    main()
