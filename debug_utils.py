#!/usr/bin/env python3
"""
고급 디버깅 및 로깅 시스템
"""
import asyncio
import json
import logging
import os
import sys
import traceback
from datetime import datetime, timedelta
from functools import wraps
from pathlib import Path
from typing import Any, Dict, List, Optional


class AdvancedDebugger:
    """고급 디버깅 시스템"""

    def __init__(self):
        self.debug_logs = []
        self.performance_data = {}
        self.error_patterns = {}
        self.setup_logging()

    def setup_logging(self):
        """향상된 로깅 설정"""
        log_dir = Path("debug_logs")
        log_dir.mkdir(exist_ok=True)

        # 다중 레벨 로깅 핸들러
        formatters = {
            "detailed": logging.Formatter(
                "%(asctime)s | %(name)s | %(levelname)s | %(filename)s:%(lineno)d | %(message)s"
            ),
            "simple": logging.Formatter("%(levelname)s: %(message)s"),
        }

        handlers = {
            "console": logging.StreamHandler(sys.stdout),
            "file": logging.FileHandler(
                log_dir / f'debug_{datetime.now().strftime("%Y%m%d")}.log'
            ),
            "error": logging.FileHandler(
                log_dir / f'errors_{datetime.now().strftime("%Y%m%d")}.log'
            ),
        }

        handlers["console"].setFormatter(formatters["simple"])
        handlers["file"].setFormatter(formatters["detailed"])
        handlers["error"].setFormatter(formatters["detailed"])
        handlers["error"].setLevel(logging.ERROR)

        self.logger = logging.getLogger("AdvancedDebugger")
        self.logger.setLevel(logging.DEBUG)

        for handler in handlers.values():
            self.logger.addHandler(handler)

    def debug_wrapper(self, func_name: str = None):
        """디버깅 래퍼 데코레이터"""

        def decorator(func):
            @wraps(func)
            async def async_wrapper(*args, **kwargs):
                name = func_name or func.__name__
                start_time = datetime.now()

                try:
                    self.logger.debug(
                        f"🔍 {name} 시작 | args: {args[:2]} | kwargs: {list(kwargs.keys())}"
                    )
                    result = await func(*args, **kwargs)
                    execution_time = (datetime.now() - start_time).total_seconds()

                    self.logger.debug(f"✅ {name} 완료 | 실행시간: {execution_time:.3f}초")

                    # 성능 데이터 수집
                    if name not in self.performance_data:
                        self.performance_data[name] = []
                    self.performance_data[name].append(execution_time)

                    return result

                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self.logger.error(f"❌ {name} 실패 | 실행시간: {execution_time:.3f}초 | 에러: {str(e)}")
                    self.logger.error(f"📍 스택트레이스: {traceback.format_exc()}")

                    # 에러 패턴 분석
                    error_type = type(e).__name__
                    if error_type not in self.error_patterns:
                        self.error_patterns[error_type] = []
                    self.error_patterns[error_type].append(
                        {
                            "function": name,
                            "error": str(e),
                            "timestamp": datetime.now().isoformat(),
                        }
                    )

                    raise

            @wraps(func)
            def sync_wrapper(*args, **kwargs):
                name = func_name or func.__name__
                start_time = datetime.now()

                try:
                    self.logger.debug(f"🔍 {name} 시작")
                    result = func(*args, **kwargs)
                    execution_time = (datetime.now() - start_time).total_seconds()

                    self.logger.debug(f"✅ {name} 완료 | 실행시간: {execution_time:.3f}초")
                    return result

                except Exception as e:
                    execution_time = (datetime.now() - start_time).total_seconds()
                    self.logger.error(f"❌ {name} 실패 | 에러: {str(e)}")
                    self.logger.error(f"📍 스택트레이스: {traceback.format_exc()}")
                    raise

            return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

        return decorator

    def get_debug_report(self) -> Dict[str, Any]:
        """디버깅 리포트 생성"""
        return {
            "timestamp": datetime.now().isoformat(),
            "performance_summary": {
                func: {
                    "avg_time": sum(times) / len(times),
                    "max_time": max(times),
                    "min_time": min(times),
                    "call_count": len(times),
                }
                for func, times in self.performance_data.items()
            },
            "error_patterns": self.error_patterns,
            "system_info": {
                "python_version": sys.version,
                "platform": sys.platform,
                "current_directory": os.getcwd(),
            },
        }


class ErrorMonitor:
    """실시간 에러 모니터링"""

    def __init__(self):
        self.error_history = []
        self.alert_thresholds = {
            "error_rate": 0.1,  # 10% 이상
            "critical_errors": 5,  # 5개 이상
            "response_time": 10.0,  # 10초 이상
        }

    def monitor_errors(self, error_data: Dict):
        """에러 모니터링 및 자동 대응"""
        self.error_history.append(error_data)

        # 최근 1시간 에러만 유지
        cutoff_time = datetime.now() - timedelta(hours=1)
        self.error_history = [
            err
            for err in self.error_history
            if datetime.fromisoformat(err["timestamp"]) > cutoff_time
        ]

        # 임계값 확인
        if len(self.error_history) > self.alert_thresholds["critical_errors"]:
            self.trigger_alert("high_error_rate", len(self.error_history))

    def trigger_alert(self, alert_type: str, data: Any):
        """알림 발송"""
        alert = {
            "type": alert_type,
            "data": data,
            "timestamp": datetime.now().isoformat(),
            "severity": "high" if alert_type == "high_error_rate" else "medium",
        }

        # 알림 파일 저장
        with open("alerts.json", "a") as f:
            f.write(json.dumps(alert) + "\n")

        print(f"🚨 ALERT: {alert_type} - {data}")
