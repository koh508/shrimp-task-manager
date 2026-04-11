import os
from pathlib import Path
from datetime import datetime
from threading import Lock

io_lock = Lock()

OBSIDIAN_VAULT_PATH = r"C:\Users\User\Documents\Obsidian Vault"
SYSTEM_PATH = os.path.join(OBSIDIAN_VAULT_PATH, "SYSTEM")


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


# 도구 맵 (온유가 함수명으로 호출할 때 사용)
tool_map = {
    "generate_project_map": generate_project_map,
}


if __name__ == "__main__":
    print(generate_project_map())
