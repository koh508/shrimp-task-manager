"""
contact_migrator.py — 안드로이드 CSV 연락처 → contacts.db 마이그레이터

[역할]
- 안드로이드 내보내기 CSV(.md 확장자)를 SQLite contacts.db로 이전
- 전화번호 정규화 / 중복 감지 / 신뢰도 기반 병합
- 인명 aliases → onew_terminology.db에도 자동 등록

[DB 스키마]  contacts.db
  contacts:       id, name, phones(JSON), aliases(JSON), title, org,
                  last_seen, source, confidence
  pending_review: id, name, phones(JSON), reason, confidence,
                  existing_id (→contacts)
  file_hashes:    path, mtime, sha256  ← 증분 처리용

[신뢰도 병합 기준]
  ≥ 0.80  → contacts 테이블 자동 병합
  0.50~0.79 → pending_review (수동 확인)
  < 0.50  → 무시

[실행]
  python contact_migrator.py              # 전체 마이그레이션
  python contact_migrator.py --stats      # 통계 출력
  python contact_migrator.py --sync       # terminology DB 재동기화
  python contact_migrator.py --pending    # pending_review 목록 출력
"""

import csv
import io
import sys
import os
import re
import json
import sqlite3
import hashlib
import logging
from datetime import datetime
from pathlib import Path

# Windows 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

SYSTEM_DIR   = Path(__file__).parent.parent
VAULT_DIR    = SYSTEM_DIR.parent
CONTACTS_CSV = VAULT_DIR / "연락처" / "안드로이드 내 2025 연락처.md"
DB_PATH      = SYSTEM_DIR / "contacts.db"
TERM_DB_PATH = SYSTEM_DIR / "onew_terminology.db"
DAILY_DIR    = VAULT_DIR / "DAILY"


# ══════════════════════════════════════════════════════════════════════════════
# 전화번호 정규화
# ══════════════════════════════════════════════════════════════════════════════

_NON_DIGIT = re.compile(r'[^\d]')
_PHONE_SEP  = re.compile(r'\s*:::\s*')


def normalize_phone(raw: str) -> str | None:
    """
    전화번호 → '010-1234-5678' 형식.
    국제 번호 '+82 10-...' → 0으로 치환.
    반환 None = 번호 없음/불명확.
    """
    raw = raw.strip()
    if not raw:
        return None

    # +82 10- → 010
    raw = re.sub(r'^\+82\s*', '0', raw)

    digits = _NON_DIGIT.sub('', raw)
    if not digits:
        return None

    # 11자리: 01012345678 → 010-1234-5678
    if len(digits) == 11 and digits.startswith('0'):
        return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"

    # 10자리: 0101234567 → 010-123-4567 (구형)
    if len(digits) == 10 and digits.startswith('0'):
        return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"

    # 02-XXXX-XXXX (서울 지역번호)
    if len(digits) == 9 and digits.startswith('02'):
        return f"02-{digits[2:6]}-{digits[6:]}"
    if len(digits) == 10 and digits.startswith('02'):
        return f"02-{digits[2:6]}-{digits[6:]}"

    # 기타: 7자리 이상이면 그대로
    if len(digits) >= 7:
        return digits

    return None


def split_phones(raw: str) -> list[str]:
    """' ::: ' 로 구분된 복수 번호를 정규화된 목록으로 반환."""
    phones = []
    for part in _PHONE_SEP.split(raw):
        n = normalize_phone(part.strip())
        if n:
            phones.append(n)
    return list(dict.fromkeys(phones))   # 중복 제거, 순서 유지


# ══════════════════════════════════════════════════════════════════════════════
# 이름 파싱 (직함/소속 분리)
# ══════════════════════════════════════════════════════════════════════════════

# 긴 것 먼저 (부장님이 부장보다 먼저 매칭되어야 함)
_TITLES = [
    '이사님', '대표님', '과장님', '차장님', '부장님', '팀장님', '계장님',
    '주임님', '대리님', '사원님', '기사님', '직원님', '선생님', '교수님',
    '이사', '대표', '과장', '차장', '부장', '팀장', '계장',
    '주임', '대리', '사원', '기사', '직원', '조장', '반장',
]
_TITLE_PATTERN = re.compile(
    '(' + '|'.join(re.escape(t) for t in _TITLES) + r')(님)?$'
)
# 조 prefix: "a조", "A조", "D조", "c조"
_TEAM_PREFIX = re.compile(r'^([a-zA-Z가-힣]{1,3}조)\s+')
# 영문/대문자 조직 prefix: "MIT 손동원" → org="MIT", name="손동원"
_ORG_PREFIX  = re.compile(r'^([A-Z가-힣]{2,6})\s+([가-힣]{2,5})$')
# 괄호 소속: "(LSS)", "(자원순환센터)"
_PAREN_ORG   = re.compile(r'\(([^)]+)\)')
# 선배/형님/씨 등 비직함 접미어
_HONORIFICS  = re.compile(r'(선배|형님|형|씨|오빠)$')


def parse_name_field(raw: str) -> dict:
    """
    이름 필드에서 이름(name), 직함(title), 소속(org) 분리.

    예:
      "a조 강지훈사원"              → name="강지훈", title="사원",  org="a조"
      "MIT 손동원 과장님"           → name="손동원", title="과장",  org="MIT"
      "배근계장님(LSS)"             → name="배근",   title="계장",  org="LSS"
      "관리팀 팀장 강문석 부장"       → name="강문석", title="부장",  org="관리팀"
      "강원국 선배(포유류)"          → name="강원국", title="",      org="포유류"
    """
    s = raw.strip()
    org   = ''
    title = ''

    # 1. 괄호 소속 추출
    paren = _PAREN_ORG.search(s)
    if paren:
        org = paren.group(1).strip()
        s = (s[:paren.start()] + s[paren.end():]).strip()

    # 2. 직함 추출 (끝부분)
    tm = _TITLE_PATTERN.search(s)
    if tm:
        title = re.sub(r'님$', '', tm.group(0))  # "과장님" → "과장"
        s = s[:tm.start()].strip()

    # 3. 비직함 접미어 제거
    hm = _HONORIFICS.search(s)
    if hm:
        s = s[:hm.start()].strip()

    # 4. 조 prefix
    team = _TEAM_PREFIX.match(s)
    if team:
        if not org:
            org = team.group(1)
        s = s[team.end():].strip()

    # 5. 영문 org prefix: "MIT 손동원" 형태
    om = _ORG_PREFIX.match(s)
    if om:
        if not org:
            org = om.group(1)
        s = om.group(2).strip()

    # 6. 공백 포함 이름에서 앞부분이 조직명인 경우
    # 예: "관리팀 팀장 강문석 부장" → title 추출 후 s="관리팀 강문석"
    # 또는 "계량대 김예진"
    parts = s.split()
    if len(parts) >= 2:
        # 마지막 토큰이 한글 2-5자면 이름, 앞부분은 org
        last = parts[-1]
        rest = ' '.join(parts[:-1])
        if re.fullmatch(r'[가-힣]{2,5}', last) and not re.fullmatch(r'[가-힣]{2,5}', rest):
            if not org:
                org = rest
            s = last

    name = s.strip()
    return {'name': name, 'title': title, 'org': org}


# ══════════════════════════════════════════════════════════════════════════════
# CSV 파싱
# ══════════════════════════════════════════════════════════════════════════════

PHONE_COL = 18   # "Phone 1 - Value"


def read_csv_contacts(path: Path) -> list[dict]:
    """
    CSV(.md) → [{raw_name, phones, first_name, last_name, org_name, org_title}]
    """
    text = path.read_text(encoding='utf-8-sig')
    reader = csv.reader(io.StringIO(text))
    header = next(reader)

    contacts = []
    for row in reader:
        if not row:
            continue

        # 이름 우선순위: First Name(0) > Last Name(2) > Nickname(8) > Org Name(10)
        first = row[0].strip() if len(row) > 0 else ''
        last  = row[2].strip() if len(row) > 2 else ''
        nick  = row[8].strip() if len(row) > 8 else ''
        org_n = row[10].strip() if len(row) > 10 else ''
        org_t = row[11].strip() if len(row) > 11 else ''

        raw_name = first or last or nick or org_n
        if not raw_name:
            continue

        phone_raw = row[PHONE_COL].strip() if len(row) > PHONE_COL else ''
        phones    = split_phones(phone_raw) if phone_raw else []

        contacts.append({
            'raw_name': raw_name,
            'phones':   phones,
            'last':     last,
            'org_name': org_n,
            'org_title': org_t,
        })

    return contacts


# ══════════════════════════════════════════════════════════════════════════════
# DB 초기화
# ══════════════════════════════════════════════════════════════════════════════

def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS contacts (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            phones     TEXT DEFAULT '[]',   -- JSON list
            aliases    TEXT DEFAULT '[]',   -- JSON list (대체 이름)
            title      TEXT DEFAULT '',
            org        TEXT DEFAULT '',
            last_seen  TEXT,
            source     TEXT DEFAULT 'android_csv',
            confidence REAL DEFAULT 1.0
        );
        CREATE INDEX IF NOT EXISTS idx_contacts_name ON contacts(name);

        CREATE TABLE IF NOT EXISTS pending_review (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT,
            phones      TEXT DEFAULT '[]',
            aliases     TEXT DEFAULT '[]',
            title       TEXT DEFAULT '',
            org         TEXT DEFAULT '',
            reason      TEXT,
            confidence  REAL,
            existing_id INTEGER REFERENCES contacts(id)
        );

        CREATE TABLE IF NOT EXISTS file_hashes (
            path   TEXT PRIMARY KEY,
            mtime  REAL,
            sha256 TEXT
        );
    """)
    conn.commit()
    return conn


# ══════════════════════════════════════════════════════════════════════════════
# 증분 처리 (파일 변경 감지)
# ══════════════════════════════════════════════════════════════════════════════

def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    h.update(path.read_bytes())
    return h.hexdigest()


def needs_processing(conn: sqlite3.Connection, path: Path) -> bool:
    """파일이 이전과 동일하면 False (스킵)."""
    mtime  = path.stat().st_mtime
    sha256 = _file_sha256(path)
    row = conn.execute(
        "SELECT mtime, sha256 FROM file_hashes WHERE path=?", (str(path),)
    ).fetchone()
    if row and row[0] == mtime and row[1] == sha256:
        return False
    return True


def mark_processed(conn: sqlite3.Connection, path: Path):
    mtime  = path.stat().st_mtime
    sha256 = _file_sha256(path)
    conn.execute("""
        INSERT OR REPLACE INTO file_hashes (path, mtime, sha256)
        VALUES (?, ?, ?)
    """, (str(path), mtime, sha256))
    conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# 중복 감지 및 신뢰도 계산
# ══════════════════════════════════════════════════════════════════════════════

def _phones_overlap(phones_a: list, phones_b: list) -> bool:
    return bool(set(phones_a) & set(phones_b))


def _name_similarity(a: str, b: str) -> float:
    """단순 이름 유사도: 공통 한글 2-gram 비율."""
    def bigrams(s):
        s = re.sub(r'[^가-힣]', '', s)
        return {s[i:i+2] for i in range(len(s) - 1)} if len(s) >= 2 else set()

    bg_a, bg_b = bigrams(a), bigrams(b)
    if not bg_a or not bg_b:
        # 완전 일치 여부만 확인
        return 1.0 if a == b else 0.0
    inter = len(bg_a & bg_b)
    union = len(bg_a | bg_b)
    return inter / union if union else 0.0


def compute_confidence(new_contact: dict, existing: dict) -> tuple[float, str]:
    """
    (신뢰도 0~1, 이유 str) 반환.
    existing: contacts 테이블 row dict
    """
    new_phones = new_contact['phones']
    ex_phones  = json.loads(existing['phones'])
    new_name   = new_contact['parsed']['name'] or new_contact['raw_name']
    ex_name    = existing['name']

    # 전화번호 완전 일치
    if new_phones and ex_phones and _phones_overlap(new_phones, ex_phones):
        name_sim = _name_similarity(new_name, ex_name)
        if name_sim >= 0.5:
            return 0.95, f"전화 일치+이름 유사({name_sim:.2f})"
        else:
            return 0.80, f"전화 일치(이름 다름: {new_name!r} vs {ex_name!r})"

    # 이름 완전 일치 (전화 없거나 다름)
    if new_name == ex_name:
        return 0.75, "이름 완전 일치(전화 상이)"

    # 이름 유사도 ≥ 0.7
    name_sim = _name_similarity(new_name, ex_name)
    if name_sim >= 0.7:
        return 0.55 + name_sim * 0.1, f"이름 유사({name_sim:.2f})"

    return 0.0, ""


def find_existing(conn: sqlite3.Connection,
                  contact: dict) -> list[dict]:
    """
    contacts 테이블에서 잠재 중복 검색.
    전화 일치 또는 이름 유사 row 목록 반환.
    """
    candidates = []
    new_phones = contact['phones']
    new_name   = contact['parsed']['name'] or contact['raw_name']

    # 1. 전화번호 JSON에서 교집합 검색 (LIKE)
    for phone in new_phones:
        rows = conn.execute(
            "SELECT id, name, phones, aliases, title, org FROM contacts "
            "WHERE phones LIKE ?",
            (f'%{phone}%',)
        ).fetchall()
        for r in rows:
            d = {
                'id': r[0], 'name': r[1],
                'phones': r[2], 'aliases': r[3],
                'title': r[4], 'org': r[5],
            }
            if d not in candidates:
                candidates.append(d)

    # 2. 이름 부분 일치
    if new_name and len(new_name) >= 2:
        rows = conn.execute(
            "SELECT id, name, phones, aliases, title, org FROM contacts "
            "WHERE name LIKE ? OR aliases LIKE ?",
            (f'%{new_name}%', f'%{new_name}%')
        ).fetchall()
        for r in rows:
            d = {
                'id': r[0], 'name': r[1],
                'phones': r[2], 'aliases': r[3],
                'title': r[4], 'org': r[5],
            }
            if d not in candidates:
                candidates.append(d)

    return candidates


# ══════════════════════════════════════════════════════════════════════════════
# contacts 테이블 병합
# ══════════════════════════════════════════════════════════════════════════════

def _merge_phones(existing_json: str, new_phones: list) -> str:
    ex = json.loads(existing_json)
    merged = list(dict.fromkeys(ex + new_phones))
    return json.dumps(merged, ensure_ascii=False)


def _merge_aliases(existing_json: str, new_aliases: list) -> str:
    ex = json.loads(existing_json)
    merged = list(dict.fromkeys(ex + new_aliases))
    return json.dumps(merged, ensure_ascii=False)


def insert_contact(conn: sqlite3.Connection, contact: dict) -> int:
    """새 연락처 삽입. 삽입된 id 반환."""
    parsed  = contact['parsed']
    name    = parsed['name'] or contact['raw_name']
    aliases = [contact['raw_name']] if contact['raw_name'] != name else []

    conn.execute("""
        INSERT INTO contacts (name, phones, aliases, title, org, source)
        VALUES (?, ?, ?, ?, ?, 'android_csv')
    """, (
        name,
        json.dumps(contact['phones'], ensure_ascii=False),
        json.dumps(aliases, ensure_ascii=False),
        parsed['title'],
        parsed['org'],
    ))
    conn.commit()
    row = conn.execute(
        "SELECT id FROM contacts ORDER BY id DESC LIMIT 1"
    ).fetchone()
    return row[0]


def merge_into(conn: sqlite3.Connection,
               contact: dict, existing_id: int):
    """기존 연락처에 전화번호·aliases 병합."""
    ex = conn.execute(
        "SELECT phones, aliases FROM contacts WHERE id=?", (existing_id,)
    ).fetchone()
    if not ex:
        return

    new_aliases = [contact['raw_name']]
    if contact['parsed']['name'] and contact['parsed']['name'] != contact['raw_name']:
        new_aliases.append(contact['parsed']['name'])

    conn.execute("""
        UPDATE contacts
        SET phones  = ?,
            aliases = ?
        WHERE id = ?
    """, (
        _merge_phones(ex[0], contact['phones']),
        _merge_aliases(ex[1], new_aliases),
        existing_id,
    ))
    conn.commit()


def insert_pending(conn: sqlite3.Connection,
                   contact: dict, existing_id: int,
                   confidence: float, reason: str):
    parsed = contact['parsed']
    name   = parsed['name'] or contact['raw_name']
    aliases = [contact['raw_name']] if contact['raw_name'] != name else []
    conn.execute("""
        INSERT INTO pending_review
          (name, phones, aliases, title, org, reason, confidence, existing_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        name,
        json.dumps(contact['phones'], ensure_ascii=False),
        json.dumps(aliases, ensure_ascii=False),
        parsed['title'],
        parsed['org'],
        f"{reason} (기존 id={existing_id})",
        confidence,
        existing_id,
    ))
    conn.commit()


# ══════════════════════════════════════════════════════════════════════════════
# DAILY 일기에서 last_seen 날짜 추출
# ══════════════════════════════════════════════════════════════════════════════

def update_last_seen(conn: sqlite3.Connection):
    """
    DAILY/*.md 파일을 스캔하여 이름이 언급된 마지막 날짜를 contacts.last_seen에 기록.
    대용량 스캔이므로 이미 처리한 날짜는 file_hashes로 건너뜀.
    """
    if not DAILY_DIR.exists():
        return

    # contacts.name 목록 로드
    rows = conn.execute("SELECT id, name, aliases FROM contacts").fetchall()
    name_map: dict[str, int] = {}   # name/alias → id
    for row in rows:
        cid, name, aliases_json = row
        name_map[name] = cid
        try:
            for a in json.loads(aliases_json):
                if a and len(a) >= 2:
                    name_map[a] = cid
        except Exception:
            pass

    if not name_map:
        return

    # 날짜 역순 스캔
    daily_files = sorted(DAILY_DIR.glob("????-??-??.md"), reverse=True)
    seen: dict[int, str] = {}   # contact_id → date str

    for fp in daily_files:
        date_str = fp.stem   # "2026-03-22"
        if not needs_processing(conn, fp):
            continue
        try:
            text = fp.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue

        for name, cid in name_map.items():
            if cid not in seen and name in text:
                seen[cid] = date_str

        mark_processed(conn, fp)

    for cid, date in seen.items():
        conn.execute(
            "UPDATE contacts SET last_seen=? WHERE id=? AND (last_seen IS NULL OR last_seen < ?)",
            (date, cid, date)
        )
    conn.commit()
    if seen:
        print(f"  last_seen 업데이트: {len(seen)}명")


# ══════════════════════════════════════════════════════════════════════════════
# terminology DB 동기화
# ══════════════════════════════════════════════════════════════════════════════

def sync_to_terminology(conn: sqlite3.Connection):
    """
    contacts 테이블의 aliases → onew_terminology.db에 등록.
    variant(별칭/약칭) → primary_term(정식 이름)
    """
    if not TERM_DB_PATH.exists():
        print("  [sync] onew_terminology.db 없음, 건너뜀")
        return

    try:
        sys.path.insert(0, str(SYSTEM_DIR / "onew_core"))
        from terminology_server import TerminologyIndex
        idx = TerminologyIndex(TERM_DB_PATH)
    except Exception as e:
        print(f"  [sync] terminology_server 로드 실패: {e}")
        return

    rows = conn.execute("SELECT name, aliases, title FROM contacts").fetchall()
    added = 0
    for row in rows:
        name, aliases_json, title = row
        try:
            aliases = json.loads(aliases_json)
        except Exception:
            aliases = []

        for alias in aliases:
            if alias and alias != name and len(alias) >= 2:
                ok = idx.add_synonym(
                    primary_term=name,
                    variant=alias,
                    source='contact_migrator',
                    confidence=0.9,
                )
                if ok:
                    added += 1

        # "홍길동 차장" → primary: "홍길동"
        if title and name:
            combined = f"{name} {title}" if f"{name} {title}" != name else None
            if combined:
                ok = idx.add_synonym(
                    primary_term=name,
                    variant=combined,
                    source='contact_migrator',
                    confidence=0.9,
                )
                if ok:
                    added += 1

    print(f"  [sync] terminology 등록: {added}개")


# ══════════════════════════════════════════════════════════════════════════════
# 메인 마이그레이션
# ══════════════════════════════════════════════════════════════════════════════

def migrate(csv_path: Path = CONTACTS_CSV,
            db_path:  Path = DB_PATH) -> dict:
    """
    메인 함수. contacts.db로 마이그레이션.
    Returns: {inserted, merged, pending, skipped}
    """
    if not csv_path.exists():
        print(f"[ERROR] 연락처 파일 없음: {csv_path}")
        return {}

    conn = init_db(db_path)

    if not needs_processing(conn, csv_path):
        print("[migrate] 파일 변경 없음 — 건너뜀")
        return {}

    raw_contacts = read_csv_contacts(csv_path)
    print(f"[migrate] CSV 읽기 완료: {len(raw_contacts)}개 행")

    stats = {'inserted': 0, 'merged': 0, 'pending': 0, 'skipped': 0}

    for raw in raw_contacts:
        raw['parsed'] = parse_name_field(raw['raw_name'])

    for contact in raw_contacts:
        candidates = find_existing(conn, contact)

        if not candidates:
            # 신규 삽입
            insert_contact(conn, contact)
            stats['inserted'] += 1
            continue

        # 최고 신뢰도 후보 선택
        best_conf   = 0.0
        best_reason = ''
        best_ex     = None
        for ex in candidates:
            conf, reason = compute_confidence(contact, ex)
            if conf > best_conf:
                best_conf, best_reason, best_ex = conf, reason, ex

        if best_conf >= 0.80:
            merge_into(conn, contact, best_ex['id'])
            stats['merged'] += 1
        elif best_conf >= 0.50:
            insert_pending(conn, contact, best_ex['id'], best_conf, best_reason)
            stats['pending'] += 1
        else:
            # 신규 삽입
            insert_contact(conn, contact)
            stats['inserted'] += 1

    mark_processed(conn, csv_path)

    # last_seen 업데이트
    update_last_seen(conn)

    # terminology 동기화
    sync_to_terminology(conn)

    conn.close()
    return stats


# ══════════════════════════════════════════════════════════════════════════════
# CLI
# ══════════════════════════════════════════════════════════════════════════════

def _cmd_stats():
    conn = init_db()
    total    = conn.execute("SELECT COUNT(*) FROM contacts").fetchone()[0]
    with_ph  = conn.execute(
        "SELECT COUNT(*) FROM contacts WHERE phones != '[]'"
    ).fetchone()[0]
    pending  = conn.execute("SELECT COUNT(*) FROM pending_review").fetchone()[0]
    conn.close()
    print(f"contacts      : {total:,}명")
    print(f"전화번호 보유  : {with_ph:,}명")
    print(f"pending_review: {pending:,}건")


def _cmd_pending():
    conn = init_db()
    rows = conn.execute(
        "SELECT id, name, phones, confidence, reason FROM pending_review ORDER BY confidence DESC"
    ).fetchall()
    conn.close()
    if not rows:
        print("pending_review 없음")
        return
    print(f"{'id':>4}  {'이름':<20}  {'신뢰도':>6}  이유")
    print("-" * 70)
    for r in rows:
        phones = json.loads(r[2]) if r[2] else []
        ph_str = phones[0] if phones else '-'
        print(f"{r[0]:>4}  {r[1]:<20}  {r[3]:>6.2f}  {r[4]}")


def _cmd_sync():
    conn = init_db()
    sync_to_terminology(conn)
    conn.close()


if __name__ == "__main__":
    logging.basicConfig(level=logging.WARNING)

    if '--stats' in sys.argv:
        _cmd_stats()
    elif '--pending' in sys.argv:
        _cmd_pending()
    elif '--sync' in sys.argv:
        conn = init_db()
        sync_to_terminology(conn)
        conn.close()
    else:
        result = migrate()
        if result:
            print(f"\n[결과]")
            print(f"  신규 등록  : {result.get('inserted', 0):,}명")
            print(f"  기존 병합  : {result.get('merged',   0):,}명")
            print(f"  검토 대기  : {result.get('pending',  0):,}건")
            print(f"  DB: {DB_PATH}")
