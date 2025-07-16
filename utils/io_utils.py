from pathlib import Path
import logging

def safe_read_file(path: Path) -> str | None:
    try:
        return path.read_text(encoding='utf-8')
    except FileNotFoundError:
        logging.warning(f"❗ 파일 없음 (이미 이동됨/삭제됨): {path}")
        return None
    except Exception as e:
        logging.error(f"❌ 파일 읽기 실패: {path} → {e}")
        return None

def safe_move_file(src: Path, dest: Path) -> bool:
    try:
        if not src.exists():
            logging.warning(f"⚠️ 이동 실패: 소스 파일 없음: {src}")
            return False
        dest.parent.mkdir(parents=True, exist_ok=True)
        src.rename(dest)
        return True
    except Exception as e:
        logging.error(f"❌ 파일 이동 오류: {src} → {dest} | {e}")
        return False
