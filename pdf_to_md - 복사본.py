"""
pdf_to_md.py - OCU 강의 PDF → 옵시디언 마크다운 변환기 (Gemini Vision 버전)
사용법: python pdf_to_md.py
"""
import os
import re
import sys
import math
import subprocess
from datetime import datetime
import fitz  # PyMuPDF

sys.stdout.reconfigure(encoding='utf-8')

# ==============================================================================
# [설정]
# ==============================================================================
OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
OUTPUT_FOLDER = os.path.join(OBSIDIAN_VAULT_PATH, "OCU")
CHUNK_PAGES = 5
IMAGE_DPI = 150
MIN_FIG_SIZE = 150          # px 이하 아이콘/장식 제외
MAX_PAGES_PER_FILE = 60     # 이 페이지 수 초과 시 자동 파일 분할 (온유 200KB 제한 대응)

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
                  first_chunk=False, page_start=1, img_dir=None, name_prefix="p"):
    today = datetime.now().strftime("%Y-%m-%d")

    frontmatter = f"""---
tags:
  - OCU
  - {subject}
상태: 완료
날짜: {today}
페이지: {page_range}
---

# {chapter}
""" if first_chunk else ""

    prompt = f"""다음은 OCU 강의 PDF {page_range} 페이지 이미지다 (P1~P{len(page_images)}).
과목: {subject} / 챕터: {chapter}

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
            if '503' in str(e) or 'UNAVAILABLE' in str(e):
                wait = 10 * (attempt + 1)
                print(f"\n  서버 과부하, {wait}초 후 재시도 ({attempt+1}/5)...", end=" ")
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
def main():
    print("=" * 52)
    print("  OCU PDF → 마크다운 변환기 (Gemini Vision)")
    print("=" * 52)

    pdf_dir = os.path.join(OBSIDIAN_VAULT_PATH, "Study PDF")
    pdfs = []
    for root, dirs, files in os.walk(pdf_dir):
        for f in files:
            if f.endswith('.pdf'):
                pdfs.append(os.path.join(root, f))

    print("\n[PDF 목록]")
    for i, f in enumerate(pdfs, 1):
        size = os.path.getsize(f) / (1024*1024)
        print(f"  {i}. {os.path.relpath(f, pdf_dir)} ({size:.1f}MB)")

    idx = int(input("\n번호 선택: ")) - 1
    pdf_path = pdfs[idx]

    total = get_total_pages(pdf_path)
    print(f"총 페이지: {total}")
    start = int(input("시작 페이지: "))
    end   = int(input("끝 페이지: "))

    subject = input("과목명 (예: 공조냉동기계기사): ")
    chapter = input("단원명 (예: 1장 냉동사이클): ")

    safe_chapter = chapter.replace("/", "_").replace("\\", "_")
    out_dir = os.path.join(OUTPUT_FOLDER, subject)
    img_dir = out_dir  # Obsidian attachmentFolderPath='./' 설정에 맞게 MD와 같은 폴더에 저장
    os.makedirs(out_dir, exist_ok=True)

    client, types = get_client()
    total_pages = end - start + 1

    # ── 파일 분할 계산 ──────────────────────────────
    num_parts = max(1, math.ceil(total_pages / MAX_PAGES_PER_FILE))
    print(f"\n변환 중... ({start}~{end}p, {total_pages}페이지)")
    print(f"예상 비용: ~{total_pages * 0.4:.0f}원")
    if num_parts > 1:
        print(f"📂 {total_pages}p → {num_parts}개 파일로 자동 분할 (파트당 최대 {MAX_PAGES_PER_FILE}p)\n")
    else:
        print()

    saved_files = []

    for part_idx in range(num_parts):
        part_start = start + part_idx * MAX_PAGES_PER_FILE
        part_end   = min(part_start + MAX_PAGES_PER_FILE - 1, end)
        part_pages = part_end - part_start + 1

        if num_parts > 1:
            print(f"── Part {part_idx + 1}/{num_parts}  ({part_start}~{part_end}p, {part_pages}페이지) ──")

        part_md = []

        for ps in range(part_start, part_end + 1, CHUNK_PAGES):
            pe = min(ps + CHUNK_PAGES - 1, part_end)
            page_range = f"{ps}-{pe}"

            print(f"  [{ps}/{part_end}] {page_range}p ...", end=" ", flush=True)
            page_images, _ = pages_to_images(pdf_path, ps, pe)
            figures = extract_figures(pdf_path, ps, pe)
            total_figs = sum(len(v) for v in figures.values())
            if total_figs:
                print(f"(래스터 {total_figs}개) ", end="")

            md = convert_to_md(
                client, types, page_images, figures, subject, chapter,
                page_range=f"{part_start}-{part_end}" if (ps == part_start) else page_range,
                first_chunk=(ps == part_start),
                page_start=ps,
                img_dir=img_dir,
                name_prefix=safe_chapter
            )
            part_md.append(md)
            print("완료")

        # 파일명: 단일 파일이면 기존 방식, 분할이면 _part1, _part2, ...
        if num_parts == 1:
            out_filename = f"{safe_chapter}.md"
        else:
            out_filename = f"{safe_chapter}_part{part_idx + 1}.md"

        out_path = os.path.join(out_dir, out_filename)
        with open(out_path, 'w', encoding='utf-8') as f:
            f.write("\n\n---\n\n".join(part_md))

        saved_files.append(out_filename)
        print(f"  → 저장: OCU/{subject}/{out_filename}\n")

    # ── 최종 요약 ───────────────────────────────────
    saved_imgs = sum(
        1 for f in os.listdir(img_dir)
        if f.endswith(('.png', '.jpg', '.jpeg', '.webp'))
    ) if os.path.exists(img_dir) else 0

    print("=" * 52)
    print(f"✅ 변환 완료")
    for fname in saved_files:
        print(f"   OCU/{subject}/{fname}")
    print(f"   저장된 그림: {saved_imgs}개")
    print("=" * 52)

if __name__ == "__main__":
    main()
