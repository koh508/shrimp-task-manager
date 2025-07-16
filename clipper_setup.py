#!/usr/bin/env python3
"""
AI 클리퍼 설정 도구 (간단 버전)
"""
import json
import os
from pathlib import Path


def main():
    print("🤖 AI 클리퍼 설정")
    print("=" * 30)

    # 기본 설정
    config = {
        "obsidian_vault_path": str(Path.home() / "Documents" / "Obsidian" / "MyVault"),
        "temp_storage_path": str(Path.cwd() / "temp_clips"),
        "onedrive_path": str(Path.home() / "OneDrive" / "ObsidianClips"),
        "importance_threshold": 0.3,
        "max_temp_files": 500,
    }

    # 설정 저장
    with open("clipper_config.json", "w") as f:
        json.dump(config, f, indent=2)

    print("✅ 기본 설정 완료!")
    print(f"📄 설정 파일: clipper_config.json")
    print(f"📁 옵시디언 경로: {config['obsidian_vault_path']}")
    print(f"📁 원드라이브 경로: {config['onedrive_path']}")


if __name__ == "__main__":
    main()
