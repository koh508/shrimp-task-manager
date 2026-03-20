# vault_backup.py - Obsidian Vault 파이썬 백업 도구 (마크다운 + 이미지 + 설정)
# 저장 위치: C:\Users\User\Documents\VaultBackups\
# 보관 개수: 최대 MAX_BACKUPS개 (초과 시 오래된 것 자동 삭제)
#
# [포함] .md, 이미지(.png/.jpg 등), .canvas, .obsidian 설정, 중요 JSON 설정
# [제외] 원본 PDF(Study PDF/), 벡터DB(onew_pure_db.json), .py 스크립트, __pycache__

import zipfile
import time
from pathlib import Path
from datetime import datetime

# ── 설정 ────────────────────────────────────────────────────
VAULT_DIR   = Path(r"C:\Users\User\Documents\Obsidian Vault")
BACKUP_DIR  = Path(r"C:\Users\User\Documents\VaultBackups")
MAX_BACKUPS = 10  # 최대 보관 개수

# ── 화이트리스트: 포함할 확장자 ─────────────────────────────
INCLUDE_EXTS = {
    # 마크다운
    ".md", ".markdown",
    # Obsidian 전용
    ".canvas",
    # 이미지 (pdf_to_md 변환 이미지 + 붙여넣기 이미지 포함)
    ".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".bmp",
    # Excalidraw
    ".excalidraw",
    # 설정
    ".json", ".yaml", ".yml", ".css",
}

# ── 제외 폴더 (어느 경로에 있든 제외) ───────────────────────
EXCLUDE_DIRS = {
    "Study PDF",       # 원본 PDF (1.8GB) — OCR 재변환으로 복구 가능
    "__pycache__",
    ".git",
    ".trash",
    "db_backup",       # SYSTEM/db_backup — 구형 DB 백업본
    "code_backup",     # SYSTEM/code_backup — 구형 코드 백업본
    "Onew_Core_Backup_절대건드리지말것",  # 별도 보호 폴더
}

# ── 제외 특정 파일 (파일명 일치) ────────────────────────────
EXCLUDE_FILES = {
    "onew_pure_db.json",        # 벡터 DB 431MB — 재임베딩으로 복구 가능
    "api_usage_log.json",       # API 사용 로그 — 불필요
    "clipping_인덱스.json",      # 재생성 가능
    "클리핑_인덱스.json",         # 재생성 가능
    "test_out.txt",
    "voice_profile.npy",        # 음성 프로필 (바이너리, .npy)
}

# ── 제외 확장자 ─────────────────────────────────────────────
EXCLUDE_EXTS = {
    ".py",    # 파이썬 스크립트 — code_backup에 있음, 필요 시 이 대화에서 재생성
    ".pyc",
    ".pdf",   # 원본 PDF — Study PDF 폴더 외 간혹 있는 것도 제외
    ".npy",   # numpy 바이너리
    ".tmp",
    ".log",
}
# ──────────────────────────────────────────────────────────────


def should_include(rel: Path) -> bool:
    """포함 여부 결정. True = 백업 대상."""
    parts = rel.parts

    # 제외 폴더 검사
    for part in parts:
        if part in EXCLUDE_DIRS:
            return False

    # 제외 파일명 검사
    if rel.name in EXCLUDE_FILES:
        return False

    # 제외 확장자 검사
    ext = rel.suffix.lower()
    if ext in EXCLUDE_EXTS:
        return False

    # 화이트리스트 확장자만 포함
    if ext not in INCLUDE_EXTS:
        return False

    return True


def format_size(bytes_val: int) -> str:
    if bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.1f} KB"
    return f"{bytes_val / (1024 * 1024):.1f} MB"


def cleanup_old_backups():
    """오래된 백업 파일 삭제 (MAX_BACKUPS 초과분)"""
    backups = sorted(
        BACKUP_DIR.glob("VaultBackup_*.zip"),
        key=lambda p: p.stat().st_mtime,
        reverse=True
    )
    deleted = []
    for old in backups[MAX_BACKUPS:]:
        old.unlink()
        deleted.append(old.name)
    return deleted


def backup_vault():
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    backup_path = BACKUP_DIR / f"VaultBackup_{timestamp}.zip"

    print("=" * 55)
    print(f"  Obsidian Vault 백업 (마크다운 + 이미지)")
    print(f"  시각  : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"  대상  : {VAULT_DIR}")
    print(f"  저장  : {backup_path}")
    print("=" * 55)

    start_time = time.time()
    file_count = 0
    skip_count = 0

    try:
        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED, compresslevel=6) as zf:
            for file_path in sorted(VAULT_DIR.rglob("*")):
                if not file_path.is_file():
                    continue

                rel = file_path.relative_to(VAULT_DIR)

                if not should_include(rel):
                    skip_count += 1
                    continue

                try:
                    zf.write(file_path, arcname=rel)
                    file_count += 1
                    if file_count % 100 == 0:
                        print(f"  처리 중... {file_count}개", end='\r')
                except PermissionError:
                    print(f"\n  [건너뜀] 접근 거부: {rel}")
                    skip_count += 1
                except Exception as e:
                    print(f"\n  [오류] {rel}: {e}")
                    skip_count += 1

    except Exception as e:
        print(f"\n[치명적 오류] 백업 중단: {e}")
        if backup_path.exists():
            backup_path.unlink()
        return False

    elapsed = time.time() - start_time
    size = backup_path.stat().st_size

    print(f"\n{'=' * 55}")
    print(f"  백업 완료")
    print(f"  파일 수 : {file_count:,}개 (건너뜀: {skip_count}개)")
    print(f"  크기    : {format_size(size)}")
    print(f"  소요    : {elapsed:.1f}초")
    print(f"  파일명  : {backup_path.name}")

    # 무결성 검사 (직접 읽기로 CRC 검증 — 한글/특수문자 파일명 안전)
    print(f"\n  CRC 무결성 검사 중...")
    errors = []
    checked = 0
    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            for info in zf.infolist():
                try:
                    zf.read(info)  # ZipInfo 객체 직접 전달 → 파일명 인코딩 우회
                    checked += 1
                except Exception as e:
                    errors.append((info.filename, str(e)))
        if not errors:
            print(f"  무결성 OK - {checked:,}개 전체 이상 없음")
        else:
            print(f"  [경고] 손상 파일 {len(errors)}개 발견:")
            for fname, err in errors:
                print(f"    - {fname}: {err}")
    except Exception as e:
        print(f"  [경고] 무결성 검사 실패: {e}")

    deleted = cleanup_old_backups()
    if deleted:
        print(f"\n  오래된 백업 {len(deleted)}개 삭제:")
        for d in deleted:
            print(f"    - {d}")

    backups = sorted(BACKUP_DIR.glob("VaultBackup_*.zip"),
                     key=lambda p: p.stat().st_mtime, reverse=True)
    print(f"\n  현재 보관 중: {len(backups)}개")
    for i, b in enumerate(backups, 1):
        sz = format_size(b.stat().st_size)
        print(f"    {i}. {b.name}  ({sz})")

    print("=" * 55)
    return True


if __name__ == "__main__":
    success = backup_vault()
    if not success:
        input("\n[실패] 엔터를 눌러 종료...")
    else:
        input("\n완료. 엔터를 눌러 종료...")
