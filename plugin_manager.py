#!/usr/bin/env python3
"""
플러그인을 동적으로 로드하고 관리하는 시스템.
"""
import os
import importlib.util
import inspect
import logging
from typing import List, Dict, Any


class PluginInterface:
    """
    모든 플러그인이 상속해야 하는 기본 인터페이스입니다.
    플러그인은 `name`과 `description` 속성을 가질 수 있으며,
    `initialize`와 `run` 메소드를 구현해야 합니다.
    """

    def __init__(self):
        self.name = self.__class__.__name__
        self.description = "플러그인에 대한 설명이 없습니다."

    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        플러그인을 초기화합니다. 설정(config)을 받아 필요한 준비를 합니다.
        성공 시 True, 실패 시 False를 반환합니다.
        """
        logging.info(f"플러그인 초기화 중: {self.name}")
        return True

    def run(self):
        """
        플러그인의 주요 로직을 실행합니다.
        이 메소드는 각 플러그인에서 반드시 재정의해야 합니다.
        """
        raise NotImplementedError(f"'{self.name}' 플러그인의 run 메소드가 구현되지 않았습니다.")


class PluginManager:
    """
    지정된 폴더에서 플러그인을 찾아 로드하고, 실행을 관리합니다.
    """

    def __init__(self, plugin_folder: str = "plugins", config: Dict[str, Any] = None):
        self.plugin_folder = plugin_folder
        self.config = config or {}
        self.plugins: List[PluginInterface] = []
        self._load_plugins()

    def _load_plugins(self):
        """
        플러그인 폴더를 스캔하여 유효한 플러그인을 로드합니다.
        `config` 파일의 `enabled_plugins` 목록에 따라 선택적으로 로드할 수 있습니다.
        """
        if not os.path.isdir(self.plugin_folder):
            logging.warning(f"플러그인 폴더를 찾을 수 없습니다: {self.plugin_folder}")
            return

        enabled_plugins = self.config.get("enabled_plugins", ["*"])
        is_all_enabled = "*" in enabled_plugins

        for filename in os.listdir(self.plugin_folder):
            if not filename.endswith(".py") or filename.startswith("__"):
                continue

            module_name = filename[:-3]
            if not is_all_enabled and module_name not in enabled_plugins:
                logging.debug(f"비활성화된 플러그인 건너뛰기: {module_name}")
                continue

            try:
                module_path = os.path.join(self.plugin_folder, filename)
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                if spec is None:
                    continue

                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                for name, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, PluginInterface) and obj is not PluginInterface:
                        plugin_instance = obj()
                        plugin_config = self.config.get("plugin_settings", {}).get(
                            plugin_instance.name, {}
                        )
                        if plugin_instance.initialize(plugin_config):
                            self.plugins.append(plugin_instance)
                            logging.info(f"플러그인 로드 성공: {plugin_instance.name}")
                        else:
                            logging.error(f"플러그인 초기화 실패: {plugin_instance.name}")

            except Exception as e:
                logging.error(f"플러그인 로드 실패 {module_name}: {e}", exc_info=True)

    def run_all(self):
        """
        로드된 모든 플러그인의 `run` 메소드를 순차적으로 실행합니다.
        """
        if not self.plugins:
            logging.info("실행할 플러그인이 없습니다.")
            return

        logging.info(f"{len(self.plugins)}개의 플러그인을 실행합니다.")
        for plugin in self.plugins:
            try:
                logging.info(f"플러그인 실행: {plugin.name}")
                plugin.run()
            except Exception as e:
                logging.error(f"플러그인 '{plugin.name}' 실행 중 오류 발생: {e}", exc_info=True)
