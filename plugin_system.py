#!/usr/bin/env python3
"""
플러그인 시스템 (수정 버전)
"""
import json
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional

# 로깅 설정
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """플러그인 기본 클래스"""

    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.enabled = True
        self.last_run = None
        self.run_count = 0

    @abstractmethod
    def execute(self, action: str, *args, **kwargs) -> Dict[str, Any]:
        """플러그인 실행 (추상 메서드)"""
        pass

    def get_info(self) -> Dict[str, Any]:
        """플러그인 정보 조회"""
        return {
            "name": self.name,
            "version": self.version,
            "enabled": self.enabled,
            "last_run": self.last_run,
            "run_count": self.run_count,
        }

    def enable(self):
        """플러그인 활성화"""
        self.enabled = True
        logger.info(f"플러그인 활성화: {self.name}")

    def disable(self):
        """플러그인 비활성화"""
        self.enabled = False
        logger.info(f"플러그인 비활성화: {self.name}")


class GitHubPlugin(BasePlugin):
    """GitHub 플러그인"""

    def __init__(self):
        super().__init__("GitHub", "1.0.0")
        self.repo_name = "demo/repository"
        self.issues_count = 0
        self.api_calls = 0

    def execute(self, action: str, *args, **kwargs) -> Dict[str, Any]:
        """GitHub 작업 실행"""
        self.last_run = datetime.now().isoformat()
        self.run_count += 1
        self.api_calls += 1

        try:
            if action == "create_issue":
                return self._create_issue(kwargs.get("title", "새 이슈"), kwargs.get("body", ""))
            elif action == "get_status":
                return self._get_status()
            elif action == "get_rate_limit":
                return self._get_rate_limit()
            else:
                return self._error_response(f"지원하지 않는 작업: {action}")

        except Exception as e:
            logger.error(f"GitHub 플러그인 오류: {e}")
            return self._error_response(str(e))

    def _create_issue(self, title: str, body: str) -> Dict[str, Any]:
        """이슈 생성 (시뮬레이션)"""
        self.issues_count += 1
        issue_data = {
            "number": self.issues_count,
            "title": title,
            "body": body,
            "state": "open",
            "created_at": datetime.now().isoformat(),
        }
        return {
            "plugin": self.name,
            "action": "create_issue",
            "result": "success",
            "data": issue_data,
            "timestamp": self.last_run,
            "message": f"이슈 #{self.issues_count} 생성 완료: {title}",
        }

    def _get_status(self) -> Dict[str, Any]:
        """저장소 상태 조회"""
        return {
            "plugin": self.name,
            "action": "get_status",
            "result": "success",
            "data": {
                "repo": self.repo_name,
                "issues_count": self.issues_count,
                "api_calls": self.api_calls,
                "last_activity": self.last_run,
            },
            "timestamp": self.last_run,
            "message": f"저장소 상태 조회 완료: {self.repo_name}",
        }

    def _get_rate_limit(self) -> Dict[str, Any]:
        """API 사용량 조회 (시뮬레이션)"""
        remaining = max(0, 5000 - self.api_calls)
        return {
            "plugin": self.name,
            "action": "get_rate_limit",
            "result": "success",
            "data": {
                "remaining": remaining,
                "limit": 5000,
                "reset": datetime.now().isoformat(),
                "used": self.api_calls,
            },
            "timestamp": self.last_run,
            "message": f"API 사용량: {remaining}/5000 남음",
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        """오류 응답 생성"""
        return {
            "plugin": self.name,
            "result": "error",
            "error": message,
            "timestamp": self.last_run,
        }


class NotificationPlugin(BasePlugin):
    """알림 플러그인"""

    def __init__(self):
        super().__init__("Notification", "1.0.0")
        self.notifications = []
        self.notification_id = 0

    def execute(self, action: str, *args, **kwargs) -> Dict[str, Any]:
        """알림 작업 실행"""
        self.last_run = datetime.now().isoformat()
        self.run_count += 1

        try:
            if action == "send_notification":
                return self._send_notification(
                    kwargs.get("title", "알림"),
                    kwargs.get("message", "메시지"),
                    kwargs.get("priority", "normal"),
                )
            elif action == "get_notifications":
                return self._get_notifications()
            else:
                return self._error_response(f"지원하지 않는 작업: {action}")
        except Exception as e:
            return self._error_response(str(e))

    def _send_notification(self, title: str, message: str, priority: str) -> Dict[str, Any]:
        self.notification_id += 1
        notification = {
            "id": self.notification_id,
            "title": title,
            "message": message,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
        }
        self.notifications.append(notification)
        return {
            "plugin": self.name,
            "action": "send_notification",
            "result": "success",
            "data": {"id": self.notification_id},
            "timestamp": self.last_run,
            "message": f"알림 전송 완료: {title}",
        }

    def _get_notifications(self) -> Dict[str, Any]:
        return {
            "plugin": self.name,
            "action": "get_notifications",
            "result": "success",
            "data": self.notifications,
            "timestamp": self.last_run,
            "message": f"{len(self.notifications)}개 알림 조회",
        }

    def _error_response(self, message: str) -> Dict[str, Any]:
        return {
            "plugin": self.name,
            "result": "error",
            "error": message,
            "timestamp": self.last_run,
        }


class PluginManager:
    """플러그인 관리자"""

    def __init__(self):
        self.plugins: Dict[str, BasePlugin] = {}
        self.load_default_plugins()

    def load_default_plugins(self):
        """기본 플러그인 로드"""
        self.register_plugin(GitHubPlugin())
        self.register_plugin(NotificationPlugin())

    def register_plugin(self, plugin: BasePlugin):
        """플러그인 등록"""
        self.plugins[plugin.name.lower()] = plugin
        logger.info(f"플러그인 등록: {plugin.name}")

    def execute_plugin(
        self, plugin_name: str, action: str, *args, **kwargs
    ) -> Optional[Dict[str, Any]]:
        """플러그인 실행"""
        plugin = self.plugins.get(plugin_name.lower())
        if plugin and plugin.enabled:
            return plugin.execute(action, *args, **kwargs)
        elif not plugin:
            logger.warning(f"플러그인을 찾을 수 없음: {plugin_name}")
            return {"error": f"플러그인을 찾을 수 없음: {plugin_name}"}
        else:
            logger.warning(f"비활성화된 플러그인: {plugin_name}")
            return {"error": f"비활성화된 플러그인: {plugin_name}"}

    def list_plugins(self) -> List[Dict[str, Any]]:
        """플러그인 목록 조회"""
        return [p.get_info() for p in self.plugins.values()]


def main():
    """메인 실행 함수"""
    manager = PluginManager()

    print("🔌 플러그인 시스템")
    print("=" * 40)

    while True:
        print("\n📋 메뉴:")
        print("1. 플러그인 목록 조회")
        print("2. GitHub 플러그인 실행")
        print("3. 알림 플러그인 실행")
        print("0. 종료")

        choice = input("\n선택하세요 (0-3): ").strip()

        if choice == "0":
            print("👋 플러그인 시스템 종료")
            break
        elif choice == "1":
            plugins = manager.list_plugins()
            print("\n🧩 설치된 플러그인:")
            for p in plugins:
                print(f"  - {p['name']} (v{p['version']}) - {'활성' if p['enabled'] else '비활성'}")
        elif choice == "2":
            print("\n🔧 GitHub 작업:")
            print("   a. 이슈 생성")
            print("   b. 상태 조회")
            print("   c. API 사용량 조회")
            action_choice = input("   선택: ").strip().lower()

            if action_choice == "a":
                title = input("   이슈 제목: ")
                result = manager.execute_plugin("github", "create_issue", title=title)
            elif action_choice == "b":
                result = manager.execute_plugin("github", "get_status")
            elif action_choice == "c":
                result = manager.execute_plugin("github", "get_rate_limit")
            else:
                result = {"error": "잘못된 선택"}

            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif choice == "3":
            print("\n🔧 알림 작업:")
            print("   a. 알림 보내기")
            print("   b. 알림 목록 보기")
            action_choice = input("   선택: ").strip().lower()

            if action_choice == "a":
                title = input("   알림 제목: ")
                message = input("   알림 내용: ")
                result = manager.execute_plugin(
                    "notification", "send_notification", title=title, message=message
                )
            elif action_choice == "b":
                result = manager.execute_plugin("notification", "get_notifications")
            else:
                result = {"error": "잘못된 선택"}

            print(json.dumps(result, indent=2, ensure_ascii=False))

        else:
            print("❌ 잘못된 선택입니다.")


if __name__ == "__main__":
    main()
