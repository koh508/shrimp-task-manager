"""
onew_tools.py — 온유 Tool 공통 유틸리티

Strangler Fig Step 1:
  obsidian_agent.py 내 Tool 함수들의 공통 로직 모음.
  obsidian_agent.py와 독립적으로 임포트 가능.

제공:
  generate_project_map()   → Vault 구조 스캔 → project_map.md 생성
  is_in_vault(path)        → Vault 내부 경로 검사 (경로 탈출 방어)
  resolve_vault_path(name) → 파일명/상대경로 → 절대 Path
  safe_read(path)          → 안전한 파일 읽기
  tool_error(fn, e)        → 통일된 에러 문자열 포맷
"""
import os
from pathlib import Path
from datetime import datetime
from threading import Lock

io_lock = Lock()

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM")
_VAULT_PATH = Path(OBSIDIAN_VAULT_PATH)


def generate_project_map() -> str:
    """Vault 전체 폴더 구조를 스캔하여 SYSTEM/project_map.md를 자동 생성/갱신."""
    try:
        with io_lock:
            map_path = os.path.join(SYSTEM_PATH, "project_map.md")
            ignore_dirs = {"venv", ".git", "__pycache__", "db_backup", "code_backup",
                           ".obsidian", "Onew_Core_Backup"}

            # Vault 루트 직속 폴더 목록 (교차검증용)
            root_folders = sorted([
                d for d in os.listdir(OBSIDIAN_VAULT_PATH)
                if os.path.isdir(os.path.join(OBSIDIAN_VAULT_PATH, d))
                and d not in ignore_dirs
            ])

            lines = [
                "# Obsidian Vault 구조 (자동 생성됨)",
                f"**마지막 갱신:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                "## 📁 Vault 폴더 목록 (교차검증용 정확한 폴더명)",
                "",
            ]
            for folder in root_folders:
                lines.append(f"- {folder}")
            lines.append("")

            # SYSTEM 폴더는 파일 목록까지 상세 표시
            lines.append("## ⚙️ SYSTEM 파일 목록")
            lines.append("")
            for f in sorted(os.listdir(SYSTEM_PATH)):
                if f.endswith((".py", ".json", ".md", ".bat")):
                    lines.append(f"- {f}")
            lines.append("")

            Path(map_path).write_text("\n".join(lines), encoding="utf-8")
            return f"맵 갱신 완료 ({len(root_folders)}개 폴더) -> {map_path}"
    except Exception as e:
        return f"Error: 맵 생성 실패 ({e})"


# ==============================================================================
# [경로 유틸리티]
# ==============================================================================
def is_in_vault(path: str | Path) -> bool:
    """경로가 Vault 내부인지 확인. 경로 탈출(../ 등) 방어."""
    try:
        Path(path).resolve().relative_to(_VAULT_PATH.resolve())
        return True
    except ValueError:
        return False


def resolve_vault_path(name: str) -> Path | None:
    """파일명 또는 Vault 기준 상대경로 → 절대 Path.
    절대경로이면 그대로 반환. 파일을 못 찾으면 None."""
    p = Path(name)
    if p.is_absolute():
        return p if p.exists() else None
    candidates = list(_VAULT_PATH.rglob(p.name))
    if candidates:
        return candidates[0]
    direct = _VAULT_PATH / p
    return direct if direct.exists() else None


def safe_read(path: str | Path, encoding: str = "utf-8") -> str:
    """파일 읽기. 실패 시 에러 문자열 반환 (예외 전파 없음)."""
    try:
        with open(path, "r", encoding=encoding) as f:
            return f.read()
    except Exception as e:
        return f"Error reading {path}: {e}"


def tool_error(fn_name: str, exc: Exception) -> str:
    """Tool 함수 에러 통일 포맷."""
    return f"Error [{fn_name}]: {exc}"


# 도구 맵 (온유가 함수명으로 호출할 때 사용)
tool_map = {
    "generate_project_map": generate_project_map,
}


if __name__ == "__main__":
    print(generate_project_map())
