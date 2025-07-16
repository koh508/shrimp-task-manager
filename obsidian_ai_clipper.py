#!/usr/bin/env python3
"""
AI 기반 옵시디언 자동 클리핑 시스템 (간단 버전)
"""
import json
import os
import time
from pathlib import Path


def analyze_content(content):
    # 간단한 중요도 분석 (예시)
    return 1.0 if len(content) > 100 else 0.1


def main():
    print("📎 옵시디언 AI 클리퍼 실행")
    print("=" * 30)
    # 설정 파일 로드
    if not Path("clipper_config.json").exists():
        print("❌ 설정 파일(clipper_config.json)이 없습니다. 먼저 clipper_setup.py를 실행하세요.")
        return
    with open("clipper_config.json", "r") as f:
        config = json.load(f)
    vault_path = Path(config["obsidian_vault_path"])
    temp_path = Path(config["temp_storage_path"])
    temp_path.mkdir(exist_ok=True)
    print(f"📁 감시 경로: {vault_path}")
    print(f"📁 임시 저장소: {temp_path}")
    # 예시: vault 내 모든 md파일을 스캔
    if not vault_path.exists():
        print(f"❌ 옵시디언 볼트 경로가 존재하지 않습니다: {vault_path}")
        return
    for md_file in vault_path.glob("*.md"):
        with open(md_file, "r", encoding="utf-8") as f:
            content = f.read()
        score = analyze_content(content)
        if score >= config["importance_threshold"]:
            temp_file = temp_path / md_file.name
            with open(temp_file, "w", encoding="utf-8") as f:
                f.write(content)
            print(f"✅ 중요 파일 클립: {md_file.name} (score={score}) → {temp_file}")
    print("🎉 클리핑 완료!")


if __name__ == "__main__":
    main()
