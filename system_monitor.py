#!/usr/bin/env python3
"""
실시간 모니터링 및 헬스체크 시스템
"""
import asyncio
import logging
import time
from datetime import datetime
import json

class SystemMonitor:
    def __init__(self):
        self.health_status = {}
        self.alert_thresholds = {
            'github_api_rate_limit': 100,
            'response_time': 5.0,
            'error_rate': 0.05
        }
        self.monitoring_interval = 60  # 1분 간격
        logging.basicConfig(level=logging.INFO,
                            format='%(asctime)s - %(levelname)s - %(message)s')

    async def monitor_github_health(self):
        try:
            from github import Github
            from config_manager import ConfigManager
            config = ConfigManager()
            github_config = config.get_github_config()
            g = Github(github_config['token'])
            rate_limit = g.get_rate_limit()
            remaining = rate_limit.core.remaining
            self.health_status['github'] = {
                'status': 'healthy' if remaining > self.alert_thresholds['github_api_rate_limit'] else 'warning',
                'rate_limit_remaining': remaining,
                'rate_limit_reset': rate_limit.core.reset.isoformat(),
                'last_check': datetime.now().isoformat()
            }
            return True
        except Exception as e:
            self.health_status['github'] = {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }
            return False

    async def monitor_system_performance(self):
        try:
            import psutil
            cpu_percent = psutil.cpu_percent()
            memory_percent = psutil.virtual_memory().percent
            disk_percent = psutil.disk_usage('/').percent
            self.health_status['system'] = {
                'status': 'healthy',
                'cpu_percent': cpu_percent,
                'memory_percent': memory_percent,
                'disk_percent': disk_percent,
                'last_check': datetime.now().isoformat()
            }
            if cpu_percent > 80 or memory_percent > 80 or disk_percent > 80:
                self.health_status['system']['status'] = 'warning'
                await self.send_alert('System performance warning',
                                     f'CPU: {cpu_percent}%, Memory: {memory_percent}%, Disk: {disk_percent}%')
        except Exception as e:
            self.health_status['system'] = {
                'status': 'error',
                'error': str(e),
                'last_check': datetime.now().isoformat()
            }

    async def send_alert(self, subject: str, message: str):
        alert_data = {
            'timestamp': datetime.now().isoformat(),
            'subject': subject,
            'message': message,
            'system_status': self.health_status
        }
        logging.warning(f"ALERT: {subject} - {message}")
        with open('alerts.json', 'a', encoding='utf-8') as f:
            f.write(json.dumps(alert_data, ensure_ascii=False) + '\n')

    async def run_monitoring(self):
        while True:
            try:
                await self.monitor_github_health()
                await self.monitor_system_performance()
                report = {
                    'timestamp': datetime.now().isoformat(),
                    'overall_status': self.get_overall_status(),
                    'components': self.health_status
                }
                with open('monitoring_report.json', 'w', encoding='utf-8') as f:
                    json.dump(report, f, ensure_ascii=False, indent=2)
                print(f"📊 모니터링 리포트 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                await asyncio.sleep(self.monitoring_interval)
            except Exception as e:
                logging.error(f"모니터링 오류: {e}")
                await asyncio.sleep(10)

    def get_overall_status(self) -> str:
        statuses = [component.get('status', 'unknown') for component in self.health_status.values()]
        if 'error' in statuses:
            return 'error'
        elif 'warning' in statuses:
            return 'warning'
        else:
            return 'healthy'
