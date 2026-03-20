# link_index.py - Vault 노트 인덱스 빌더
# 동일 파일명 → 파일 크기 내림차순으로 우선순위 번호 부여 (1 = 최우선)

import json
from pathlib import Path
from collections import defaultdict

VAULT_DIR  = Path(r"C:\Users\User\Documents\Obsidian Vault")
INDEX_PATH = VAULT_DIR / "SYSTEM" / "link_index.json"

EXCLUDE_DIRS = {
    "SYSTEM", "Processed", ".obsidian", "__pycache__", ".trash", ".git",
    "Onew_Core_Backup_절대건드리지말것", "db_backup", "code_backup",
    "대화기록", "01_Daily",
}


def _is_excalidraw(path: Path) -> bool:
    try:
        header = path.read_bytes()[:500].decode("utf-8", errors="replace")
        return "excalidraw-plugin" in header
    except Exception:
        return False


def build_index() -> dict:
    """
    반환 형식:
    {
      "파일명(확장자 없음)": [
        {"path": "폴더/파일명.md", "size": 12345, "priority": 1},
        ...  # priority 1이 최우선 (크기 큰 순)
      ]
    }
    """
    name_map = defaultdict(list)

    for md_file in VAULT_DIR.rglob("*.md"):
        rel = md_file.relative_to(VAULT_DIR)

        # 제외 폴더
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue

        # Excalidraw 파일 제외
        if _is_excalidraw(md_file):
            continue

        try:
            size = md_file.stat().st_size
        except Exception:
            continue

        stem    = md_file.stem
        rel_str = str(rel).replace("\\", "/")
        name_map[stem].append({"path": rel_str, "size": size, "priority": None})

    # 동일 파일명 그룹: 크기 내림차순 → 우선순위 1, 2, 3 ...
    index      = {}
    duplicates = {}

    for stem, entries in name_map.items():
        sorted_entries = sorted(entries, key=lambda x: x["size"], reverse=True)
        for i, entry in enumerate(sorted_entries, 1):
            entry["priority"] = i
        index[stem] = sorted_entries
        if len(sorted_entries) > 1:
            duplicates[stem] = sorted_entries

    with INDEX_PATH.open("w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)

    total = sum(len(v) for v in index.values())
    print(f"인덱스 완료 : {total}개 파일 / {len(index)}개 고유 이름 / 동일파일명 {len(duplicates)}개 그룹")

    if duplicates:
        print("\n[동일 파일명 우선순위 목록]")
        for stem, entries in list(duplicates.items())[:15]:
            print(f"  '{stem}'")
            for e in entries:
                print(f"    [{e['priority']}순위] {e['path']}  ({e['size']/1024:.1f}KB)")

    return index


def load_index() -> dict:
    if INDEX_PATH.exists():
        with INDEX_PATH.open(encoding="utf-8") as f:
            return json.load(f)
    print("인덱스 없음 → 새로 빌드합니다.")
    return build_index()


def resolve_link(stem: str, index: dict) -> str | None:
    """
    파일명(확장자 없음)으로 링크 대상 경로 반환.
    동일 파일명이 여럿이면 priority=1(가장 큰 파일)을 반환.
    존재하지 않으면 None.
    """
    entries = index.get(stem)
    if not entries:
        return None
    return min(entries, key=lambda x: x["priority"])["path"]


def index_as_list(index: dict) -> list[str]:
    """API 프롬프트용 평탄화된 경로 목록 반환."""
    paths = []
    for entries in index.values():
        for e in entries:
            paths.append(e["path"])
    return sorted(paths)


if __name__ == "__main__":
    build_index()
