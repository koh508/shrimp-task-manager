"""
terminology_server.py — 온유 용어 정규화 서버

[역할]
- SQLite DB(onew_terminology.db)에서 동의어/변형어를 로드
- 쿼리의 표현 변형을 정규 표현(primary_term)으로 정규화
- MCP 도구로 노출: normalize_query, add_synonym, lookup_term

[캐싱 전략]
- 서버 시작 시 전체 DB를 메모리 alias_dict에 로드 → O(1) 조회
- DB 변경(add_synonym) 후 자동 갱신

[DB 스키마]  onew_terminology.db
  CREATE TABLE terms (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    primary_term TEXT NOT NULL,           -- 정규 표현 (Vault 실제 저장된 형태)
    variant      TEXT NOT NULL UNIQUE,    -- 변형 표현 (사용자가 잘못 말할 수 있는 것)
    confidence   REAL DEFAULT 1.0,        -- 0~1, 낮을수록 불확실
    source       TEXT DEFAULT 'harvester', -- 출처: harvester / user / correction
    created_at   TEXT,
    usage_count  INTEGER DEFAULT 0,
    last_used    TEXT,
    is_verified  INTEGER DEFAULT 0        -- 0=미검증, 1=검증완료
  );
  CREATE TABLE blacklist (
    term TEXT PRIMARY KEY
  );

[실행 방법]
  python terminology_server.py              # MCP 서버로 실행
  python terminology_server.py --init       # DB 초기화 + proposed_synonyms.md 가져오기
  python terminology_server.py --stats      # 통계 출력
"""

import os
import re
import sys
import io
import sqlite3
import logging
from datetime import datetime
from pathlib import Path

# Windows 인코딩
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding and sys.stderr.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

logger = logging.getLogger(__name__)

SYSTEM_DIR    = Path(__file__).parent.parent
DB_PATH       = SYSTEM_DIR / "onew_terminology.db"
SYNONYMS_FILE = SYSTEM_DIR / "docs" / "proposed_synonyms.md"

# 단독 등록 금지 블랙리스트 (harvester와 동일)
DEFAULT_BLACKLIST = {
    '펌프', '밸브', '모터', '팬', '게이트', '장비', '기기', '설비', '시스템',
    '유닛', '배관', '라인', '포트', '탱크', '드럼', '타워', '칸', '층', '실'
}


# ─────────────────────────────────────────────────────────────────────────────
# DB 초기화
# ─────────────────────────────────────────────────────────────────────────────
def init_db(db_path: Path = DB_PATH) -> sqlite3.Connection:
    """DB가 없으면 생성, 있으면 연결."""
    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS terms (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            primary_term TEXT NOT NULL,
            variant      TEXT NOT NULL,
            confidence   REAL DEFAULT 1.0,
            source       TEXT DEFAULT 'harvester',
            created_at   TEXT,
            usage_count  INTEGER DEFAULT 0,
            last_used    TEXT,
            is_verified  INTEGER DEFAULT 0
        );
        CREATE UNIQUE INDEX IF NOT EXISTS idx_variant ON terms(variant);
        CREATE INDEX IF NOT EXISTS idx_primary ON terms(primary_term);

        CREATE TABLE IF NOT EXISTS blacklist (
            term TEXT PRIMARY KEY
        );
    """)
    conn.commit()
    return conn


# ─────────────────────────────────────────────────────────────────────────────
# proposed_synonyms.md 가져오기
# ─────────────────────────────────────────────────────────────────────────────
def _parse_synonyms_md(path: Path) -> tuple[list[dict], list[dict]]:
    """
    proposed_synonyms.md 파싱.
    Returns:
        tier1: [{primary, variant, is_verified=1, source='harvester_equip'}]
        tier2: [{primary, variant, is_verified=0, source='harvester'}]
    """
    if not path.exists():
        print(f"  파일 없음: {path}")
        return [], []

    content = path.read_text(encoding='utf-8')
    tier1, tier2 = [], []
    now = datetime.now().isoformat()

    # ── Tier 1: 장비 코드 ───────────────────────────────────────────────────
    # | 1 | `VP-008` | 1980 | ... | `- [x]` |
    tier1_re = re.compile(r'\|\s*\d+\s*\|\s*`([^`]+)`\s*\|.*?\|\s*`- \[x\]`\s*\|')
    for m in tier1_re.finditer(content):
        code = m.group(1).strip()
        # 코드 자체를 variant로 (primary = 동일, 자기 자신)
        tier1.append({
            'primary_term': code,
            'variant':      code,
            'confidence':   1.0,
            'source':       'harvester_equip',
            'is_verified':  1,
            'created_at':   now,
        })

    # ── Tier 2: 복합 명사 ───────────────────────────────────────────────────
    # - [ ] **냉동 장치** (빈도: 426)
    #   변형: `냉동장치`
    tier2_block_re = re.compile(
        r'- \[ \] \*\*(.+?)\*\* \(빈도: \d+\)\n(?:  변형: (.+))?',
        re.MULTILINE
    )
    backtick_re = re.compile(r'`([^`]+)`')

    for m in tier2_block_re.finditer(content):
        primary = m.group(1).strip()
        variants_str = m.group(2) or ''
        variants = backtick_re.findall(variants_str)

        # primary 자체도 등록 (정규형)
        tier2.append({
            'primary_term': primary,
            'variant':      primary,
            'confidence':   0.9,
            'source':       'harvester',
            'is_verified':  0,
            'created_at':   now,
        })
        for v in variants:
            if v != primary:
                tier2.append({
                    'primary_term': primary,
                    'variant':      v,
                    'confidence':   0.8,
                    'source':       'harvester',
                    'is_verified':  0,
                    'created_at':   now,
                })

    return tier1, tier2


def import_synonyms(conn: sqlite3.Connection, path: Path = SYNONYMS_FILE) -> dict:
    """proposed_synonyms.md → DB 일괄 등록."""
    print(f"[import] {path.name} 파싱 중...")
    tier1, tier2 = _parse_synonyms_md(path)
    all_rows = tier1 + tier2

    inserted = 0
    skipped  = 0
    blacklisted = 0

    for row in all_rows:
        variant = row['variant']

        # 블랙리스트 확인
        cur = conn.execute("SELECT 1 FROM blacklist WHERE term=?", (variant,))
        if cur.fetchone():
            blacklisted += 1
            continue

        try:
            conn.execute("""
                INSERT OR IGNORE INTO terms
                  (primary_term, variant, confidence, source, is_verified, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                row['primary_term'], variant,
                row['confidence'], row['source'],
                row['is_verified'], row['created_at'],
            ))
            inserted += 1
        except sqlite3.IntegrityError:
            skipped += 1

    conn.commit()

    # 기본 블랙리스트 등록
    for term in DEFAULT_BLACKLIST:
        conn.execute("INSERT OR IGNORE INTO blacklist (term) VALUES (?)", (term,))
    conn.commit()

    stats = {
        'tier1': len(tier1),
        'tier2': len(tier2),
        'inserted': inserted,
        'skipped':  skipped,
        'blacklisted': blacklisted,
    }
    print(f"  Tier1={stats['tier1']} Tier2={stats['tier2']} "
          f"→ 등록={stats['inserted']} 중복스킵={stats['skipped']} 블랙={stats['blacklisted']}")
    return stats


# ─────────────────────────────────────────────────────────────────────────────
# In-memory alias_dict (O(1) 조회)
# ─────────────────────────────────────────────────────────────────────────────
class TerminologyIndex:
    """
    DB → 메모리 alias_dict 로드.
    {variant: primary_term} 형태로 저장.
    """

    def __init__(self, db_path: Path = DB_PATH):
        self.db_path   = db_path
        self.alias_dict: dict[str, str] = {}
        self._conn: sqlite3.Connection | None = None
        self._reload()

    def _reload(self):
        """DB 전체를 메모리로 로드."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            rows = conn.execute(
                "SELECT variant, primary_term FROM terms"
            ).fetchall()
            conn.close()
            self.alias_dict = {row[0]: row[1] for row in rows}
            logger.debug("[TermIndex] %d entries loaded", len(self.alias_dict))
        except Exception as e:
            logger.warning("[TermIndex] reload failed: %s", e)
            self.alias_dict = {}

    def _build_pattern(self):
        """alias_dict → 단일 통합 regex (캐싱)."""
        if not hasattr(self, '_pattern') or self._pattern_key != len(self.alias_dict):
            variants = sorted(self.alias_dict.keys(), key=len, reverse=True)
            if variants:
                self._pattern = re.compile(
                    '|'.join(re.escape(v) for v in variants)
                )
            else:
                self._pattern = None
            self._pattern_key = len(self.alias_dict)

    def normalize(self, text: str) -> str:
        """
        텍스트에서 알려진 변형어를 primary_term으로 교체.
        - 단일 좌→우 패스 (re.sub) → 연쇄 치환 없음
        - 가장 긴 변형어 우선 (alternation 순서로 보장)
        """
        if not self.alias_dict:
            return text

        self._build_pattern()
        if self._pattern is None:
            return text

        alias = self.alias_dict

        def _replace(m: re.Match) -> str:
            variant = m.group(0)
            return alias.get(variant, variant)

        return self._pattern.sub(_replace, text)

    def lookup(self, term: str) -> dict:
        """
        primary_term 또는 variant로 검색.
        Returns: {primary_term, variants: [...]}
        """
        # variant로 검색
        primary = self.alias_dict.get(term)
        if primary:
            variants = [v for v, p in self.alias_dict.items() if p == primary]
            return {'primary_term': primary, 'variants': sorted(variants)}

        # primary_term으로 검색 (역방향)
        variants = [v for v, p in self.alias_dict.items() if p == term]
        if variants:
            return {'primary_term': term, 'variants': sorted(variants)}

        return {'primary_term': None, 'variants': []}

    def add_synonym(self, primary_term: str, variant: str,
                    source: str = 'user', confidence: float = 1.0) -> bool:
        """
        새 동의어 등록 + alias_dict 즉시 갱신.
        Returns: True(신규) / False(이미 존재)
        """
        if variant in self.alias_dict:
            return False

        conn = sqlite3.connect(str(self.db_path))
        try:
            conn.execute("""
                INSERT OR IGNORE INTO terms
                  (primary_term, variant, confidence, source, is_verified, created_at)
                VALUES (?, ?, ?, ?, 1, ?)
            """, (primary_term, variant, confidence, source,
                  datetime.now().isoformat()))
            conn.commit()
            self.alias_dict[variant] = primary_term
            return True
        except Exception as e:
            logger.error("[add_synonym] %s", e)
            return False
        finally:
            conn.close()

    def record_usage(self, variant: str):
        """검색에 사용된 variant의 usage_count 증가."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.execute("""
                UPDATE terms SET usage_count=usage_count+1, last_used=?
                WHERE variant=?
            """, (datetime.now().isoformat(), variant))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def stats(self) -> dict:
        """DB 통계."""
        try:
            conn = sqlite3.connect(str(self.db_path))
            total    = conn.execute("SELECT COUNT(*) FROM terms").fetchone()[0]
            verified = conn.execute("SELECT COUNT(*) FROM terms WHERE is_verified=1").fetchone()[0]
            primaries = conn.execute(
                "SELECT COUNT(DISTINCT primary_term) FROM terms"
            ).fetchone()[0]
            conn.close()
            return {
                'total_variants': total,
                'verified': verified,
                'unique_primary_terms': primaries,
                'memory_entries': len(self.alias_dict),
            }
        except Exception as e:
            return {'error': str(e)}


# ─────────────────────────────────────────────────────────────────────────────
# MCP 서버 노출
# ─────────────────────────────────────────────────────────────────────────────
# TerminologyIndex 싱글톤
_index: TerminologyIndex | None = None


def get_index() -> TerminologyIndex:
    global _index
    if _index is None:
        _index = TerminologyIndex()
    return _index


try:
    from mcp.server.fastmcp import FastMCP
    _mcp_available = True
except ImportError:
    _mcp_available = False

if _mcp_available:
    mcp = FastMCP("onew-terminology")

    @mcp.tool()
    def normalize_query(query: str) -> str:
        """
        사용자 쿼리의 변형 표현을 정규 표현으로 정규화한다.
        예: '냉동장치' → '냉동 장치', '팽창밸브' → '팽창 밸브'
        """
        idx = get_index()
        normalized = idx.normalize(query)
        if normalized != query:
            logger.info("[normalize] '%s' → '%s'", query, normalized)
        return normalized

    @mcp.tool()
    def lookup_term(term: str) -> dict:
        """
        용어의 정규 표현과 모든 변형을 조회한다.
        Returns: {primary_term, variants: [...]}
        """
        return get_index().lookup(term)

    @mcp.tool()
    def add_synonym(primary_term: str, variant: str,
                    source: str = 'user') -> dict:
        """
        새 동의어를 등록한다. (사용자가 잘못 말한 표현 → 정규 표현 매핑)
        primary_term: Vault에 실제 저장된 정규 표현
        variant:      사용자가 사용한 변형 표현
        """
        ok = get_index().add_synonym(primary_term, variant, source=source)
        return {
            'success': ok,
            'message': f"{'등록 완료' if ok else '이미 존재'}: {variant!r} → {primary_term!r}"
        }

    @mcp.tool()
    def terminology_stats() -> dict:
        """용어 DB 통계를 반환한다."""
        return get_index().stats()


# ─────────────────────────────────────────────────────────────────────────────
# CLI 진입점
# ─────────────────────────────────────────────────────────────────────────────
def _cmd_init():
    """DB 초기화 + proposed_synonyms.md 가져오기."""
    print(f"DB 경로: {DB_PATH}")
    conn = init_db()
    import_synonyms(conn, SYNONYMS_FILE)
    conn.close()

    # 로드 확인
    idx = TerminologyIndex()
    s = idx.stats()
    print(f"\n로드 완료: {s['memory_entries']}개 in-memory")
    print(f"  고유 primary_term: {s['unique_primary_terms']}개")
    print(f"  검증 완료: {s['verified']}개")

    # 샘플 normalize 테스트
    tests = [
        '냉동장치',
        '팽창밸브',
        '마찰손실',
        '보일러급수펌프',  # 없을 경우 그대로 반환
        '압력스위치',
    ]
    print("\n[정규화 테스트]")
    for t in tests:
        result = idx.normalize(t)
        mark = '→' if result != t else '≡'
        print(f"  {t!r} {mark} {result!r}")


def _cmd_stats():
    """DB 통계 출력."""
    idx = TerminologyIndex()
    s = idx.stats()
    if 'error' in s:
        print(f"오류: {s['error']}")
        return
    print(f"전체 변형어 : {s['total_variants']:,}개")
    print(f"검증 완료   : {s['verified']:,}개")
    print(f"고유 정규표현: {s['unique_primary_terms']:,}개")
    print(f"메모리 로드  : {s['memory_entries']:,}개")


if __name__ == "__main__":
    if '--init' in sys.argv:
        _cmd_init()
    elif '--stats' in sys.argv:
        _cmd_stats()
    elif _mcp_available:
        mcp.run()
    else:
        print("mcp 패키지 없음. --init 또는 --stats 옵션 사용:")
        print("  python terminology_server.py --init")
        print("  python terminology_server.py --stats")
