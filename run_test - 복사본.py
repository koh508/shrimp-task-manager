"""공조냉동 기출문제 테스트"""
import sys, os, shutil
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, r'C:\Users\User\Documents\Obsidian Vault\SYSTEM')
import pdf_to_md as p

pdf_path = r'C:\Users\User\Documents\Obsidian Vault\Study PDF\공조냉동기계 실기 기출문제(25년 1-3회).pdf'
subject = '공조냉동기계기사'
chapter = '실기기출_25년1-3회'
start, end = 1, 30

safe_chapter = chapter.replace('/', '_').replace('\\', '_')
out_dir = os.path.join(p.OUTPUT_FOLDER, subject)
img_dir = out_dir  # MD 파일과 같은 폴더

client, types = p.get_client()
all_md = []
print(f"전체 {end}페이지 변환 시작\n")

for ps in range(start, end + 1, p.CHUNK_PAGES):
    pe = min(ps + p.CHUNK_PAGES - 1, end)
    page_range = f"{ps}-{pe}"
    print(f"  [{ps}/{end}] {page_range}p ...", end=" ", flush=True)
    page_images, _ = p.pages_to_images(pdf_path, ps, pe)
    figures = p.extract_figures(pdf_path, ps, pe)
    if figures:
        print(f"(내장그림 {len(figures)}개) ", end="")
    md = p.convert_to_md(
        client, types, page_images, figures, subject, chapter, page_range,
        first_chunk=(ps == start), page_start=ps,
        img_dir=img_dir, name_prefix=safe_chapter
    )
    all_md.append(md)
    print("완료")

out_path = os.path.join(out_dir, f'{safe_chapter}.md')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write('\n\n---\n\n'.join(all_md))

saved = len(os.listdir(img_dir)) if os.path.exists(img_dir) else 0
print(f'\n완료: {out_path}')
print(f'저장된 그림: {saved}개 / 전체 {end}페이지')
