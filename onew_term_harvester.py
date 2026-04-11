"""
onew_term_harvester.py — Vault 용어 수확 스크립트 (1회성)

[목적]
Vault .md 파일 전체에서 복합 명사(N-gram)와 장비 코드를 추출하여
온유 용어 사전 초안(proposed_synonyms.md)을 생성한다.

[실행 방법]
  pip install kiwipiepy        # 최초 1회 (kiwipiepy 없으면 공백 분리 폴백)
  cd "C:\\Users\\User\\Documents\\Obsidian Vault\\SYSTEM"
  python onew_term_harvester.py

[출력]
  SYSTEM/docs/proposed_synonyms.md
    - Tier 1: 장비 코드 + 자동 검증 (is_verified=True, - [x])
    - Tier 2: 복합 명사 + 수동 검토 필요 (- [ ])

[이후 작업]
  1. proposed_synonyms.md 열어서 Tier 2 항목 검토 (불필요한 것 삭제)
  2. 확정 항목을 onew_terminology.db에 등록 (Step 2: terminology_server.py)
"""

import os
import re
import sys
import io
import json
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

# Windows 터미널 인코딩 강제 UTF-8
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ── kiwipiepy 선택적 임포트 ──────────────────────────────────────────────────
try:
    from kiwipiepy import Kiwi
    _kiwi = Kiwi()
    KIWI_AVAILABLE = True
    print("✅ kiwipiepy 로드 완료")
except ImportError:
    _kiwi = None
    KIWI_AVAILABLE = False
    print("⚠️  kiwipiepy 미설치 → 공백 분리 폴백 모드")
    print("   (형태소 분석 없이 실행하면 품질이 낮습니다)")
    print("   설치: pip install kiwipiepy")
    print()

# ── 경로 설정 ────────────────────────────────────────────────────────────────
SYSTEM_DIR  = Path(__file__).parent
VAULT_PATH  = SYSTEM_DIR.parent
OUTPUT_FILE = SYSTEM_DIR / "docs" / "proposed_synonyms.md"

# ── 상수 ─────────────────────────────────────────────────────────────────────
# 장비 코드 패턴: TO-1011A, FCV-201, P-101, LIC-2030B, TRC101 등
EQUIP_CODE_RE = re.compile(r'\b[A-Z]{1,4}-?\d{2,6}[A-Z]?\b')

# 단독 단어로 동의어 등록 금지 (너무 일반적 — 복합어 구성원으로만 허용)
BLACKLIST = {'펌프', '밸브', '모터', '팬', '게이트', '장비', '기기', '설비', '시스템',
             '유닛', '배관', '라인', '포트', '탱크', '드럼', '타워', '칸', '층', '실'}

# 건너뛸 폴더
SKIP_DIRS = {'.git', 'SYSTEM', '.obsidian', 'Processed', 'node_modules'}

# 수확 대상 폴더 (None = 전체 Vault, 리스트 지정 시 해당 폴더만)
# 기술 용어 집중: OCU(강의자료) + DAILY(사용자 메모) 폴더 우선
FOCUS_DIRS: list[str] | None = ['OCU']

# 빈도 임계값
MIN_FREQ_NORMAL = 10  # 일반 복합어: 10회 이상
MIN_FREQ_EQUIP  = 1   # 장비 코드: 1회 이상

# N-gram 범위 (토큰 단위)
NGRAM_MIN = 2
NGRAM_MAX = 3

# 변형 생성 시 토큰 길이 범위 (너무 짧거나 길면 제외)
VARIANT_MIN_LEN = 2   # 글자 수
VARIANT_MAX_LEN = 12  # 글자 수


# ─────────────────────────────────────────────────────────────────────────────
# 파일 수집
# ─────────────────────────────────────────────────────────────────────────────
def collect_md_files(vault_path: Path) -> list[Path]:
    """Vault에서 .md 파일 목록 수집.
    FOCUS_DIRS 지정 시 해당 폴더만, None이면 SKIP_DIRS 제외 전체.
    """
    files = []

    if FOCUS_DIRS:
        # 지정 폴더만 수집
        for folder in FOCUS_DIRS:
            target = vault_path / folder
            if target.exists():
                for p in target.rglob("*.md"):
                    files.append(p)
            else:
                print(f"  ⚠️  폴더 없음: {target}")
        return files

    # 전체 Vault 수집 (스킵 폴더 제외)
    for p in vault_path.rglob("*.md"):
        try:
            rel = p.relative_to(vault_path)
            if rel.parts and rel.parts[0] in SKIP_DIRS:
                continue
        except ValueError:
            pass
        files.append(p)
    return files


# ─────────────────────────────────────────────────────────────────────────────
# 텍스트 전처리
# ─────────────────────────────────────────────────────────────────────────────
def clean_text(raw: str) -> str:
    """마크다운 메타데이터·코드 블록·링크 등 제거."""
    # YAML frontmatter 제거
    if raw.startswith("---"):
        end = raw.find("---", 3)
        if end != -1:
            raw = raw[end + 3:]

    # 코드 블록 제거
    raw = re.sub(r'```[\s\S]*?```', ' ', raw)
    raw = re.sub(r'`[^`]+`', ' ', raw)

    # 마크다운 링크/이미지 제거
    raw = re.sub(r'!\[.*?\]\(.*?\)', ' ', raw)
    raw = re.sub(r'\[\[.*?\]\]', lambda m: m.group()[2:-2], raw)  # 내부 링크는 텍스트만
    raw = re.sub(r'\[.*?\]\(.*?\)', lambda m: re.search(r'\[(.*?)\]', m.group()).group(1), raw)

    # HTML 태그 제거
    raw = re.sub(r'<[^>]+>', ' ', raw)

    # 특수문자 단순화
    raw = re.sub(r'[#*_~>|]', ' ', raw)

    return raw


# ─────────────────────────────────────────────────────────────────────────────
# 토크나이저
# ─────────────────────────────────────────────────────────────────────────────
def tokenize_nouns(text: str) -> list[str]:
    """
    kiwipiepy 사용 가능 시: 한국어 명사(NNG, NNP)만 추출
      - SL(외국어) 제외: 이미지 파일명(fig, jpeg, text, circ 등) 노이즈 방지
    불가 시: 공백 분리 + 한글 2글자 이상 필터
    """
    if KIWI_AVAILABLE:
        try:
            tokens = []
            result = _kiwi.tokenize(text)
            for token in result:
                # NNG=일반명사, NNP=고유명사만 (SL 외국어 제외)
                if token.tag in ('NNG', 'NNP') and len(token.form) >= 2:
                    # 순수 한글만 (숫자/영문 혼재 제외)
                    if re.fullmatch(r'[가-힣]+', token.form):
                        tokens.append(token.form)
            return tokens
        except Exception:
            pass

    # 폴백: 공백 분리 + 순수 한글 2글자 이상
    tokens = []
    for word in text.split():
        word = re.sub(r'[^가-힣]', '', word)
        if len(word) >= 2:
            tokens.append(word)
    return tokens


# ─────────────────────────────────────────────────────────────────────────────
# 장비 코드 추출
# ─────────────────────────────────────────────────────────────────────────────
def extract_equip_codes(text: str) -> list[str]:
    """장비 코드 패턴 추출."""
    return EQUIP_CODE_RE.findall(text)


# ─────────────────────────────────────────────────────────────────────────────
# N-gram 생성
# ─────────────────────────────────────────────────────────────────────────────
def make_ngrams(tokens: list[str], n_min: int = NGRAM_MIN, n_max: int = NGRAM_MAX) -> list[str]:
    """연속 토큰으로 N-gram 복합어 생성."""
    ngrams = []
    for n in range(n_min, n_max + 1):
        for i in range(len(tokens) - n + 1):
            gram = " ".join(tokens[i:i + n])
            ngrams.append(gram)
    return ngrams


# ─────────────────────────────────────────────────────────────────────────────
# 변형(동의어) 후보 생성
# ─────────────────────────────────────────────────────────────────────────────
def generate_variants(term: str) -> list[str]:
    """
    주어진 복합어에서 변형 후보를 생성한다.
    전략: 단축 (포함 관계) — 부분 토큰 조합 + 띄어쓰기 변형
    확장은 하지 않음 (노이즈 증가 우려).
    """
    parts = term.split()
    variants = set()

    # 1. 공백 제거 버전 (붙여쓰기)
    no_space = "".join(parts)
    if VARIANT_MIN_LEN <= len(no_space) <= VARIANT_MAX_LEN and no_space != term:
        variants.add(no_space)

    # 2. 앞부분 생략 (뒤 n-1 토큰)
    if len(parts) >= 3:
        for start in range(1, len(parts)):
            sub = " ".join(parts[start:])
            sub_ns = "".join(parts[start:])
            for v in (sub, sub_ns):
                if (VARIANT_MIN_LEN <= len(v) <= VARIANT_MAX_LEN
                        and v != term
                        # 블랙리스트 단독 단어 차단
                        and v not in BLACKLIST):
                    variants.add(v)

    # 3. 뒷부분 생략 (앞 n-1 토큰)
    if len(parts) >= 3:
        for end in range(1, len(parts)):
            sub = " ".join(parts[:end])
            sub_ns = "".join(parts[:end])
            for v in (sub, sub_ns):
                if (VARIANT_MIN_LEN <= len(v) <= VARIANT_MAX_LEN
                        and v != term
                        and v not in BLACKLIST):
                    variants.add(v)

    # 블랙리스트 최종 필터
    variants = {v for v in variants if v not in BLACKLIST}

    return sorted(variants)


# ─────────────────────────────────────────────────────────────────────────────
# 메인 수확 로직
# ─────────────────────────────────────────────────────────────────────────────
def harvest(vault_path: Path) -> tuple[dict, dict]:
    """
    Returns:
        equip_codes : {code: count}
        ngram_counts: {ngram: count}
    """
    files = collect_md_files(vault_path)
    print(f"  수집 파일: {len(files)}개")

    equip_counter: Counter = Counter()
    ngram_counter: Counter = Counter()
    processed = 0

    for fpath in files:
        try:
            raw = fpath.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue

        # 장비 코드 추출 (원본 텍스트에서)
        for code in extract_equip_codes(raw):
            equip_counter[code] += 1

        # 복합 명사 N-gram 추출
        cleaned = clean_text(raw)
        nouns = tokenize_nouns(cleaned)
        for gram in make_ngrams(nouns):
            ngram_counter[gram] += 1

        processed += 1
        if processed % 100 == 0:
            print(f"  처리 중... {processed}/{len(files)}")

    print(f"  완료: {processed}개 파일 처리")
    return dict(equip_counter), dict(ngram_counter)


# ─────────────────────────────────────────────────────────────────────────────
# 출력 파일 생성
# ─────────────────────────────────────────────────────────────────────────────
def write_output(
    equip_codes: dict,
    ngram_counts: dict,
    output_path: Path,
) -> None:
    """proposed_synonyms.md 생성."""

    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Tier 1: 장비 코드 (자동 검증, is_verified=True)
    tier1 = sorted(
        [(k, v) for k, v in equip_codes.items() if v >= MIN_FREQ_EQUIP],
        key=lambda x: -x[1]
    )

    # Tier 2: 빈도 충족 복합 명사 (수동 검토)
    tier2_raw = sorted(
        [(k, v) for k, v in ngram_counts.items() if v >= MIN_FREQ_NORMAL],
        key=lambda x: -x[1]
    )
    # 블랙리스트 단어만으로 구성된 항목 필터
    tier2 = [
        (k, v) for k, v in tier2_raw
        if not all(p in BLACKLIST for p in k.split())
    ]

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M")
    kiwi_str = f"kiwipiepy {KIWI_AVAILABLE}" if KIWI_AVAILABLE else "공백분리 폴백"

    lines = [
        "---",
        "tags: [용어사전, 동의어, Phase0]",
        f"날짜: {now_str}",
        "상태: 검토대기",
        "---",
        "",
        "# 온유 용어 사전 초안 (proposed_synonyms.md)",
        "",
        f"> 생성: {now_str}  |  형태소: {kiwi_str}",
        f"> Tier 1 (장비코드, 자동검증): {len(tier1)}개",
        f"> Tier 2 (복합명사, 수동검토): {len(tier2)}개",
        "",
        "**검토 방법:**",
        "- `- [x]` : 등록 확정 (onew_terminology.db에 추가)",
        "- `- [ ]` : 검토 필요 (불필요하면 줄 삭제)",
        "",
        "---",
        "",
        "## Tier 1 — 장비 코드 (자동 검증, is_verified=True)",
        "",
        "| # | 코드 | 빈도 | 변형 후보 | 등록 |",
        "|---|------|------|-----------|------|",
    ]

    for i, (code, cnt) in enumerate(tier1, 1):
        variants = generate_variants(code)
        var_str = ", ".join(variants) if variants else "-"
        lines.append(f"| {i} | `{code}` | {cnt} | {var_str} | `- [x]` |")

    lines += [
        "",
        "---",
        "",
        "## Tier 2 — 복합 명사 (수동 검토 필요)",
        "",
        "아래 항목을 검토하여 필요 없는 것은 삭제하세요.",
        "변형 후보가 실제로 사용자가 잘못 말할 법한 표현인지 확인하세요.",
        "",
    ]

    for term, cnt in tier2:
        variants = generate_variants(term)
        var_list = "\n".join(f"    - `{v}`" for v in variants) if variants else "    (변형 없음)"
        lines.append(f"- [ ] **{term}** (빈도: {cnt})")
        if variants:
            lines.append(f"  변형: {', '.join(f'`{v}`' for v in variants)}")
        lines.append("")

    lines += [
        "---",
        "",
        "## 통계",
        "",
        f"- 처리 기준: 빈도 ≥ {MIN_FREQ_NORMAL} (복합명사) / ≥ {MIN_FREQ_EQUIP} (장비코드)",
        f"- 형태소 분석기: {kiwi_str}",
        f"- 블랙리스트: {sorted(BLACKLIST)}",
        "",
    ]

    output_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"\n✅ 출력 완료: {output_path}")
    print(f"   Tier 1: {len(tier1)}개  |  Tier 2: {len(tier2)}개")


# ─────────────────────────────────────────────────────────────────────────────
# 실행
# ─────────────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print("온유 용어 수확기 (onew_term_harvester)")
    print("=" * 60)
    print(f"Vault 경로: {VAULT_PATH}")
    print(f"출력 경로: {OUTPUT_FILE}")
    print()

    if not VAULT_PATH.exists():
        print(f"❌ Vault 경로가 존재하지 않습니다: {VAULT_PATH}")
        sys.exit(1)

    print("[1/2] Vault 파일 수확 중...")
    equip_codes, ngram_counts = harvest(VAULT_PATH)

    raw_equip = sum(1 for v in equip_codes.values() if v >= MIN_FREQ_EQUIP)
    raw_ngram = sum(1 for v in ngram_counts.values() if v >= MIN_FREQ_NORMAL)
    print(f"  장비코드 후보: {raw_equip}개 / 복합명사 후보: {raw_ngram}개")

    print("\n[2/2] 출력 파일 생성 중...")
    write_output(equip_codes, ngram_counts, OUTPUT_FILE)

    print()
    print("다음 단계:")
    print(f"  1. {OUTPUT_FILE} 열어서 Tier 2 검토")
    print("  2. 불필요한 항목 삭제 후 저장")
    print("  3. terminology_server.py로 DB 등록 (Step 2)")


if __name__ == "__main__":
    main()
