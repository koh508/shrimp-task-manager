#!/usr/bin/env python3
"""
🌟 Ultra AI Assistant - 확장 가능한 모듈러 시스템 예시
Perplexity 4.md 분석 기반, 실전 적용/확장/디버깅 최적화 구조
"""

import asyncio
import logging
import os
import shutil
import sys
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

############################
# 1. 환경 및 경로 설정
############################

STORAGE_ROOT = Path("D:/UltraAIStorage")
VAULT_PATH = Path("D:/my workspace/OneDrive NEW/GNY")
CLIP_FOLDER = VAULT_PATH / "Clippings"
PROCESSED_FOLDER = VAULT_PATH / "Processed"
REPORT_FOLDER = VAULT_PATH / "AI_WS_Reports"
ERROR_FOLDER = VAULT_PATH / "AI_Agent_Error"
PLUGIN_FOLDER = STORAGE_ROOT / "plugins"
LOG_FOLDER = STORAGE_ROOT / "logs"

for folder in [
    CLIP_FOLDER,
    PROCESSED_FOLDER,
    REPORT_FOLDER,
    ERROR_FOLDER,
    PLUGIN_FOLDER,
    LOG_FOLDER,
]:
    folder.mkdir(parents=True, exist_ok=True)

log_file = LOG_FOLDER / f"ultra_ai_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] %(levelname)s %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ],
)

############################
# 2. 플러그인/작업 처리 추상화
############################


class PluginBase(ABC):
    @abstractmethod
    def run(self, data):
        pass


class TaggingPlugin(PluginBase):
    def run(self, data):
        # 간단 태깅 예시
        tags = []
        if "AI" in data:
            tags.append("AI")
        if "Python" in data:
            tags.append("Python")
        if not tags:
            tags.append("General")
        return tags


def load_plugins():
    # 실제 확장 시: PLUGIN_FOLDER에서 동적으로 import
    return [TaggingPlugin()]


############################
# 3. 클리핑 유틸리티
############################


class WebClipper:
    def __init__(self, clip_folder=CLIP_FOLDER):
        self.clip_folder = Path(clip_folder)

    def generate_clip_filename(self, title):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_title = "".join(c if c.isalnum() or c == "_" else "_" for c in title[:40])
        return f"{timestamp}_{safe_title}.md"

    def clip(self, content, title="WebClip", source_url="", tags=None):
        if tags is None:
            tags = ["webclip"]
        filename = self.generate_clip_filename(title)
        filepath = self.clip_folder / filename
        body = f"""---
title: {title}
created: {datetime.now().isoformat()}
source: {source_url}
tags: {tags}
type: webclip
---
{content}

---

*Clipped by Ultra AI Assistant*
"""
        filepath.write_text(body, encoding="utf-8")
        logging.info(f"Clipped: {filepath}")
        return filepath


############################
# 4. 파일 감시 및 처리 에이전트 (확장형)
############################

from collections import defaultdict

from utils.io_utils import safe_move_file, safe_read_file


class ClipAgent:
    def __init__(
        self,
        clip_folder=CLIP_FOLDER,
        processed_folder=PROCESSED_FOLDER,
        report_folder=REPORT_FOLDER,
        error_folder=ERROR_FOLDER,
        plugins=None,
    ):
        self.clip_folder = Path(clip_folder)
        self.processed_folder = Path(processed_folder)
        self.report_folder = Path(report_folder)
        self.error_folder = Path(error_folder)
        self.plugins = plugins or load_plugins()
        self.loop_count = 0
        self.retry_errors = defaultdict(int)
        self.MAX_RETRY = 3
        self.warned_files = set()

    async def start(self, interval=10):
        logging.info("🛰️ 클리핑 감시 에이전트 시작")
        while True:
            try:
                await self.process_clips()
            except Exception as e:
                self.log_error(f"Loop error: {e}")
            await asyncio.sleep(interval)
            self.loop_count += 1

    async def process_clips(self):
        processed_files = []
        for file in self.clip_folder.glob("*.md"):
            if not file.exists():
                logging.warning(f"🔄 건너뜀: 파일 없음 (이미 처리됨): {file}")
                continue
            if self.retry_errors[file.name] > self.MAX_RETRY:
                logging.warning(f"⛔ 재시도 초과: {file.name}")
                continue
            content = safe_read_file(file)
            if content is None:
                self.retry_errors[file.name] += 1
                continue
            tags = []
            for plugin in self.plugins:
                tags += plugin.run(content)
            tag_str = "_".join(set(tags))
            target = self.processed_folder / f"{file.stem}_{tag_str}.md"
            if not safe_move_file(file, target):
                self.retry_errors[file.name] += 1
                self.log_error(f"파일 이동 실패: {file} → {target}")
                continue
            processed_files.append(target.name)
            logging.info(f"✅ 클립 처리 성공: {target.name}")
            # 최초 1회만 안내
            if file.name not in self.warned_files:
                logging.info(
                    """📢 클리핑 파일이 이미 이동/삭제된 경우, 대시보드에서 자동 회피 처리합니다. 콘솔 로그 또는 AI_Agent_Error 폴더를 참조해 실패 원인을 확인하세요."""
                )
                self.warned_files.add(file.name)
        if processed_files:
            self.write_report(processed_files)

    def write_report(self, processed_files):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.report_folder / f"report_{now}.md"
        summary = f"# 보고서 {now}\n\n## 처리 파일 목록\n" + "\n".join(f"- {f}" for f in processed_files)
        report_path.write_text(summary, encoding="utf-8")
        logging.info(f"Report written: {report_path}")

    def log_error(self, msg):
        now = datetime.now().strftime("%Y%m%d_%H%M%S")
        err_path = self.error_folder / f"error_{now}.md"
        err_path.write_text(f"에러: {msg}\n", encoding="utf-8")
        logging.error(f"에러 기록됨: {msg}")


############################
# 5. 확장 예시: 새로운 플러그인 추가
############################


class LengthPlugin(PluginBase):
    def run(self, data):
        return ["long"] if len(data) > 500 else ["short"]


############################
# 6. Entry Point (직접 실행/테스트)
############################


def test_all():
    clipper = WebClipper()
    f1 = clipper.clip(
        "테스트 콘텐츠", title="테스트1", source_url="https://test/a", tags=["test", "webclip"]
    )
    logging.info(f"테스트 클립 완료: {f1}")

    # 플러그인 확장: 태깅 + 길이
    plugins = [TaggingPlugin(), LengthPlugin()]
    agent = ClipAgent(plugins=plugins)
    asyncio.run(agent.process_clips())


if __name__ == "__main__":
    test_all()
    # 실전 감시 루프 사용 시
    # agent = ClipAgent(plugins=[TaggingPlugin(), LengthPlugin()])
    # asyncio.run(agent.start(interval=10))
