# link_safe_writer.py - 수식/코드블록/YAML 회피 안전 링크 삽입 엔진

import hashlib
import re
from pathlib import Path

# ── 보호 구간 패턴 (순서 중요: 넓은 범위가 먼저) ──────────────────────────
# 각 항목: (정규식 패턴, 레이블, re 플래그)
PROTECTED_PATTERNS = [
    # 1. YAML frontmatter (파일 맨 앞 --- ~ --- 사이)
    (r'^---\s*\n[\s\S]*?\n---\s*\n', "YAML", re.MULTILINE),
    # 2. 코드 펜스 블록 (``` ... ```)
    (r'```[\s\S]*?```', "CODE_FENCE", 0),
    # 3. 블록 수식 $$ ... $$ (여러 줄 포함)
    (r'\$\$[\s\S]*?\$\$', "MATH_BLOCK", 0),
    # 4. 인라인 수식 $ ... $ (같은 줄 내)
    (r'\$[^\n$]+\$', "MATH_INLINE", 0),
    # 5. LaTeX 환경 \begin{...} ... \end{...}
    (r'\\begin\{[^}]+\}[\s\S]*?\\end\{[^}]+\}', "LATEX_ENV", 0),
    # 6. 인라인 코드 ` ... `
    (r'`[^`\n]+`', "CODE_INLINE", 0),
    # 7. 이미 존재하는 위키링크 [[ ... ]]
    (r'\[\[.*?\]\]', "EXISTING_LINK", 0),
    # 8. 마크다운 이미지/링크 ![]() or []()
    (r'!?\[.*?\]\([^)]*\)', "MD_LINK", 0),
    # 9. HTML 태그
    (r'<[^>\n]+>', "HTML_TAG", 0),
    # 10. URL
    (r'https?://\S+', "URL", 0),
    # 11. Anki 블록 구분자 (TARGET DECK, 숫자:숫자 패턴 등) — 나중에 활성화
    # (r'^TARGET DECK[\s\S]*?(?=\n---|\Z)', "ANKI_BLOCK", re.MULTILINE),
]


def mask_protected(text: str) -> tuple[str, list[str]]:
    """
    보호 구간을 널바이트 플레이스홀더로 치환.
    반환: (마스킹된 텍스트, 원본 문자열 목록)
    """
    placeholders: list[str] = []
    result = text

    for pattern, label, flags in PROTECTED_PATTERNS:
        def replacer(m, _label=label):
            idx   = len(placeholders)
            token = f"\x00PROTECTED_{idx}\x00"
            placeholders.append(m.group(0))
            return token

        result = re.sub(pattern, replacer, result, flags=flags)

    return result, placeholders


def unmask(text: str, placeholders: list[str]) -> str:
    """
    플레이스홀더를 원본으로 복원.
    역순 복원: 나중에 마스킹된 것(번호 큰 것)부터 복원해야
    중첩 토큰(placeholders 안에 또 다른 토큰이 있는 경우)이 올바르게 처리됨.
    """
    for i in reversed(range(len(placeholders))):
        text = text.replace(f"\x00PROTECTED_{i}\x00", placeholders[i])
    return text


def insert_links(content: str, approved_links: list[dict]) -> tuple[str, int]:
    """
    approved_links 형식:
      [{"keyword": "압축기", "insert_as": "[[압축기]]", "line_hint": "원심 압축기는"}, ...]

    규칙:
    - 보호 구간(수식/코드/YAML/기존링크 등) 안에는 절대 삽입 안 함
    - 같은 키워드는 파일당 최초 1회만 링크
    - 반환: (수정된 내용, 실제 삽입된 링크 수)
    """
    masked, placeholders = mask_protected(content)
    inserted      = 0
    used_keywords: set[str] = set()

    for link in approved_links:
        keyword   = link.get("keyword", "")
        insert_as = link.get("insert_as", f"[[{keyword}]]")

        if not keyword or keyword in used_keywords:
            continue

        # 키워드에 널바이트가 있으면 플레이스홀더 토큰과 충돌 → 스킵
        if "\x00" in keyword:
            continue

        pattern = r'(?<!\[)' + re.escape(keyword) + r'(?!\])'

        # insert_as를 lambda로 감싸 re가 replacement 패턴으로 해석하지 못하게 함
        # (직접 전달 시 \1, \g<0> 등 backreference로 오해할 수 있음)
        _literal = insert_as
        new_masked, count = re.subn(pattern, lambda m: _literal, masked, count=1)

        if count > 0:
            masked = new_masked
            used_keywords.add(keyword)
            inserted += 1

    result = unmask(masked, placeholders)

    # ── 무결성 검사 1: 보호 구간 복원 확인 ──────────────────────────────────
    # 언마스킹 후 플레이스홀더가 하나라도 남아 있으면 복원 실패
    if "\x00PROTECTED_" in result:
        raise ValueError("보호 구간 복원 실패: 플레이스홀더가 결과에 남아 있음 (수식/코드 오염 위험)")

    return result, inserted


def update_yaml_flag(
    content: str,
    key:   str = "링크처리",
    value: str = "true"
) -> str:
    """YAML frontmatter에 처리 완료 플래그를 추가하거나 덮어씀."""
    yaml_match = re.match(r'^(---\s*\n)([\s\S]*?)(\n---\s*\n)', content)

    if not yaml_match:
        # YAML 없음 → 앞에 최소 YAML 추가
        return f"---\n{key}: {value}\n---\n\n" + content

    open_tag  = yaml_match.group(1)
    yaml_body = yaml_match.group(2)
    close_tag = yaml_match.group(3)
    rest      = content[yaml_match.end():]

    key_pattern = re.compile(rf'^({re.escape(key)}:).*$', re.MULTILINE)
    if key_pattern.search(yaml_body):
        yaml_body = key_pattern.sub(rf'\1 {value}', yaml_body)
    else:
        yaml_body = yaml_body.rstrip("\n") + f"\n{key}: {value}"

    modified = open_tag + yaml_body + close_tag + rest

    # ── 무결성 검사 2: YAML 파싱 검증 ────────────────────────────────────────
    # 수정 후 --- 블록이 정상적으로 열리고 닫히는지 확인
    yaml_check = re.match(r'^---\s*\n[\s\S]*?\n---\s*\n', modified)
    if not yaml_check:
        raise ValueError("YAML 파싱 검증 실패: 수정 후 frontmatter 구조가 깨짐")

    return modified


# ── 50KB 분할 ──────────────────────────────────────────────────────────────

def split_by_headings(content: str, max_chars: int = 8000) -> list[str]:
    """
    ## 헤딩 기준으로 청크 분할.
    YAML frontmatter는 항상 첫 청크에 포함.
    각 청크 크기가 max_chars 초과 시 추가 분할.
    """
    # YAML 분리
    yaml_match = re.match(r'^---\s*\n[\s\S]*?\n---\s*\n', content)
    if yaml_match:
        yaml_part = content[:yaml_match.end()]
        body      = content[yaml_match.end():]
    else:
        yaml_part = ""
        body      = content

    # ## 헤딩 위치 찾기
    heading_positions = [m.start() for m in re.finditer(r'^##+ ', body, re.MULTILINE)]

    if not heading_positions:
        return [content]  # 헤딩 없으면 분할 불가 → 원본 그대로

    chunks   = []
    sections = []

    for i, pos in enumerate(heading_positions):
        end = heading_positions[i + 1] if i + 1 < len(heading_positions) else len(body)
        sections.append(body[pos:end])

    # 첫 청크에 YAML + 헤딩 이전 내용 포함
    pre_heading = body[:heading_positions[0]] if heading_positions else body
    current_chunk = yaml_part + pre_heading

    for section in sections:
        if len(current_chunk) + len(section) > max_chars and current_chunk.strip():
            chunks.append(current_chunk)
            current_chunk = section
        else:
            current_chunk += section

    if current_chunk.strip():
        chunks.append(current_chunk)

    return chunks if chunks else [content]


def verify_split_integrity(original: str, chunks: list[str]) -> tuple[bool, str]:
    """
    분할 무결성 검사 (해시 기반으로 강화).
    YAML 제거 후 본문을 해시 비교 → 글자 수 + 내용 동시 검증.
    반환: (통과 여부, 오류 메시지)
    """
    def strip_yaml(text: str) -> str:
        m = re.match(r'^---\s*\n[\s\S]*?\n---\s*\n', text)
        return text[m.end():] if m else text

    def normalize(text: str) -> str:
        # 줄바꿈 방식 통일 후 앞뒤 공백 제거
        return text.replace("\r\n", "\n").replace("\r", "\n").strip()

    orig_body   = normalize(strip_yaml(original))
    joined_body = normalize("".join(strip_yaml(c) for c in chunks))

    # 1차: 글자 수 비교
    orig_len   = len(orig_body)
    joined_len = len(joined_body)
    diff       = abs(orig_len - joined_len)
    if diff > 5:
        return False, f"글자 수 불일치: 원본 {orig_len}자 vs 청크합산 {joined_len}자 (차이 {diff}자)"

    # 2차: MD5 해시 비교 (내용 동일성)
    orig_hash   = hashlib.md5(orig_body.encode("utf-8")).hexdigest()
    joined_hash = hashlib.md5(joined_body.encode("utf-8")).hexdigest()
    if orig_hash != joined_hash:
        return False, f"해시 불일치: 글자 수는 같지만 내용이 다름 (원본 {orig_hash[:8]}… vs 합산 {joined_hash[:8]}…)"

    return True, "OK"


def verify_write_integrity(path: Path, expected_content: str) -> tuple[bool, str]:
    """
    무결성 검사 3: 파일 저장 후 읽기 확인.
    저장한 내용을 다시 읽어 MD5 해시 비교.
    반환: (통과 여부, 오류 메시지)
    """
    def md5(text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    try:
        written = path.read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return False, f"저장 후 읽기 실패: {e}"

    expected_hash = md5(expected_content)
    written_hash  = md5(written)

    if expected_hash != written_hash:
        return False, f"저장 후 해시 불일치: 기대 {expected_hash[:8]}… vs 실제 {written_hash[:8]}…"

    return True, "OK"
