#!/usr/bin/env python3
"""
플러그인 시스템을 테스트하기 위한 간단한 예제 플러그인.
"""
import logging
from plugin_manager import PluginInterface
from typing import Dict, Any


class HelloPlugin(PluginInterface):
    """
    실행 시 환영 메시지를 로그로 남기는 예제 플러그인.
    """

    def __init__(self):
        super().__init__()
        self.name = "HelloPlugin"
        self.description = "간단한 환영 메시지를 출력하는 테스트 플러그인입니다."
        self.message = "안녕하세요! 플러그인이 성공적으로 실행되었습니다."

    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        플러그인 설정에서 메시지를 커스터마이징할 수 있습니다.
        """
        super().initialize(config)
        # config 딕셔너리에서 'message' 키를 찾아 self.message를 업데이트합니다.
        # 키가 없으면 기본값을 사용합니다.
        self.message = config.get("message", self.message)
        logging.info(f"'{self.name}' 플러그인이 메시지와 함께 초기화되었습니다: '{self.message}'")
        return True

    def run(self):
        """
        설정된 메시지를 로그로 출력합니다.
        """
        logging.info(f"[{self.name}] {self.message}")
