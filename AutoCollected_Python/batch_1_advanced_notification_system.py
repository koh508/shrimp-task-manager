#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔔 Advanced Notification and Alert System
==========================================
에이전트 진화 시스템을 위한 고급 알림 및 경고 시스템
"""

import asyncio
import json
import logging
import smtplib
from datetime import datetime, timedelta
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
from typing import Dict, List, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
import threading
from pathlib import Path

# 알림 레벨 정의
class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class NotificationChannel(Enum):
    CONSOLE = "console"
    EMAIL = "email"
    WEBHOOK = "webhook"
    DASHBOARD = "dashboard"
    SMS = "sms"

@dataclass
class AlertRule:
    """알림 규칙 정의"""
    rule_id: str
    name: str
    condition: str  # Python 표현식
    level: AlertLevel
    channels: List[NotificationChannel]
    cooldown_minutes: int = 30
    enabled: bool = True
    description: str = ""

@dataclass
class Alert:
    """알림 객체"""
    alert_id: str
    rule_id: str
    level: AlertLevel
    title: str
    message: str
    agent_id: Optional[str] = None
    timestamp: datetime = None
    data: Dict = None
    action_required: str = ""
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
        if self.data is None:
            self.data = {}

class NotificationSystem:
    """고급 알림 시스템"""
    
    def __init__(self, db_path: str = "d:/notifications.db"):
        self.db_path = db_path
        self.alert_rules: Dict[str, AlertRule] = {}
        self.subscribers: Dict[NotificationChannel, List[Callable]] = {}
        self.alert_history: List[Alert] = []
        self.cooldown_tracker: Dict[str, datetime] = {}
        self.logger = logging.getLogger(__name__)
        
        # 데이터베이스 초기화
        self._init_database()
        
        # 기본 알림 규칙 설정
        self._setup_default_rules()
        
        # 백그라운드 모니터링 시작
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._background_monitor, daemon=True)
        self.monitor_thread.start()
    
    def _init_database(self):
        """데이터베이스 초기화"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # 알림 기록 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alert_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        alert_id TEXT UNIQUE,
                        rule_id TEXT,
                        level TEXT,
                        title TEXT,
                        message TEXT,
                        agent_id TEXT,
                        timestamp DATETIME,
                        data TEXT,
                        action_required TEXT,
                        resolved BOOLEAN DEFAULT FALSE,
                        resolved_at DATETIME,
                        resolved_by TEXT
                    )
                """)
                
                # 알림 규칙 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS alert_rules (
                        rule_id TEXT PRIMARY KEY,
                        name TEXT,
                        condition_expr TEXT,
                        level TEXT,
                        channels TEXT,
                        cooldown_minutes INTEGER,
                        enabled BOOLEAN,
                        description TEXT,
                        created_at DATETIME,
                        updated_at DATETIME
                    )
                """)
                
                # 구독자 설정 테이블
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS notification_settings (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        channel TEXT,
                        config TEXT,
                        enabled BOOLEAN DEFAULT TRUE,
                        created_at DATETIME
                    )
                """)
                
                conn.commit()
                self.logger.info("✅ 알림 시스템 데이터베이스 초기화 완료")
        except Exception as e:
            self.logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
    
    def _setup_default_rules(self):
        """기본 알림 규칙 설정"""
        default_rules = [
            AlertRule(
                rule_id="performance_critical",
                name="성능 임계점 도달",
                condition="performance < 0.3",
                level=AlertLevel.CRITICAL,
                channels=[NotificationChannel.DASHBOARD, NotificationChannel.CONSOLE],
                cooldown_minutes=15,
                description="에이전트 성능이 위험 수준으로 떨어짐"
            ),
            AlertRule(
                rule_id="performance_declining",
                name="성능 하락 추세",
                condition="trend < -0.05 and performance < 0.7",
                level=AlertLevel.WARNING,
                channels=[NotificationChannel.DASHBOARD],
                cooldown_minutes=60,
                description="에이전트 성능이 지속적으로 하락하는 추세"
            ),
            AlertRule(
                rule_id="evolution_failure",
                name="진화 실패",
                condition="evolution_failed == True",
                level=AlertLevel.CRITICAL,
                channels=[NotificationChannel.DASHBOARD, NotificationChannel.CONSOLE],
                cooldown_minutes=30,
                description="에이전트 진화 프로세스 실패"
            ),
            AlertRule(
                rule_id="resource_usage_high",
                name="리소스 사용량 과다",
                condition="cpu_usage > 90 or memory_usage > 85",
                level=AlertLevel.WARNING,
                channels=[NotificationChannel.DASHBOARD],
                cooldown_minutes=45,
                description="시스템 리소스 사용량이 임계치 초과"
            ),
            AlertRule(
                rule_id="agent_unresponsive",
                name="에이전트 응답 없음",
                condition="last_response_time > 300",  # 5분
                level=AlertLevel.EMERGENCY,
                channels=[NotificationChannel.DASHBOARD, NotificationChannel.CONSOLE],
                cooldown_minutes=10,
                description="에이전트가 5분 이상 응답하지 않음"
            ),
            AlertRule(
                rule_id="excellent_performance",
                name="우수한 성능 달성",
                condition="performance > 0.95 and trend > 0.01",
                level=AlertLevel.INFO,
                channels=[NotificationChannel.DASHBOARD],
                cooldown_minutes=120,
                description="에이전트가 우수한 성능을 달성함"
            )
        ]
        
        for rule in default_rules:
            self.add_alert_rule(rule)
    
    def add_alert_rule(self, rule: AlertRule):
        """알림 규칙 추가"""
        try:
            self.alert_rules[rule.rule_id] = rule
            
            # 데이터베이스에 저장
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT OR REPLACE INTO alert_rules 
                    (rule_id, name, condition_expr, level, channels, cooldown_minutes, 
                     enabled, description, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rule.rule_id, rule.name, rule.condition, rule.level.value,
                    json.dumps([ch.value for ch in rule.channels]),
                    rule.cooldown_minutes, rule.enabled, rule.description,
                    datetime.now(), datetime.now()
                ))
                conn.commit()
            
            self.logger.info(f"✅ 알림 규칙 추가: {rule.name}")
        except Exception as e:
            self.logger.error(f"❌ 알림 규칙 추가 실패: {e}")
    
    def subscribe(self, channel: NotificationChannel, callback: Callable):
        """알림 채널 구독"""
        if channel not in self.subscribers:
            self.subscribers[channel] = []
        self.subscribers[channel].append(callback)
        self.logger.info(f"📡 {channel.value} 채널 구독 추가")
    
    async def check_conditions(self, agent_id: str, metrics: Dict):
        """조건 확인 및 알림 생성"""
        try:
            for rule_id, rule in self.alert_rules.items():
                if not rule.enabled:
                    continue
                
                # 쿨다운 확인
                if self._is_in_cooldown(rule_id):
                    continue
                
                # 조건 평가
                if self._evaluate_condition(rule.condition, agent_id, metrics):
                    await self._trigger_alert(rule, agent_id, metrics)
                    
        except Exception as e:
            self.logger.error(f"❌ 조건 확인 실패: {e}")
    
    def _evaluate_condition(self, condition: str, agent_id: str, metrics: Dict) -> bool:
        """조건 평가"""
        try:
            # 안전한 컨텍스트 생성
            context = {
                'agent_id': agent_id,
                'performance': metrics.get('performance', 0),
                'trend': metrics.get('trend', 0),
                'cpu_usage': metrics.get('cpu_usage', 0),
                'memory_usage': metrics.get('memory_usage', 0),
                'last_response_time': metrics.get('last_response_time', 0),
                'evolution_failed': metrics.get('evolution_failed', False),
                # 수학 함수들
                'abs': abs,
                'min': min,
                'max': max,
                'round': round
            }
            
            # 조건 평가
            return bool(eval(condition, {"__builtins__": {}}, context))
        except Exception as e:
            self.logger.error(f"❌ 조건 평가 실패 ({condition}): {e}")
            return False
    
    async def _trigger_alert(self, rule: AlertRule, agent_id: str, metrics: Dict):
        """알림 발생"""
        try:
            alert_id = f"{rule.rule_id}_{agent_id}_{int(datetime.now().timestamp())}"
            
            # 상세 메시지 생성
            message = self._generate_alert_message(rule, agent_id, metrics)
            action_required = self._suggest_action(rule, metrics)
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule.rule_id,
                level=rule.level,
                title=f"[{agent_id}] {rule.name}",
                message=message,
                agent_id=agent_id,
                data=metrics,
                action_required=action_required
            )
            
            # 알림 전송
            await self._send_alert(alert, rule.channels)
            
            # 히스토리에 추가
            self.alert_history.append(alert)
            
            # 데이터베이스에 저장
            self._save_alert_to_db(alert)
            
            # 쿨다운 설정
            self.cooldown_tracker[rule.rule_id] = datetime.now()
            
            self.logger.info(f"🚨 알림 발생: {alert.title}")
            
        except Exception as e:
            self.logger.error(f"❌ 알림 발생 실패: {e}")
    
    def _generate_alert_message(self, rule: AlertRule, agent_id: str, metrics: Dict) -> str:
        """알림 메시지 생성"""
        base_message = rule.description
        
        if rule.level == AlertLevel.CRITICAL:
            performance = metrics.get('performance', 0)
            trend = metrics.get('trend', 0)
            base_message += f"\n\n📊 현재 성능: {performance:.3f}"
            base_message += f"\n📈 성능 추세: {trend:+.3f}"
            
            if performance < 0.3:
                base_message += "\n⚠️ 즉시 조치가 필요합니다!"
        
        elif rule.level == AlertLevel.WARNING:
            base_message += f"\n\n📊 성능: {metrics.get('performance', 0):.3f}"
            base_message += f"\n📉 추세: {metrics.get('trend', 0):+.3f}"
        
        elif rule.level == AlertLevel.INFO:
            base_message += f"\n\n🎉 성능: {metrics.get('performance', 0):.3f}"
        
        base_message += f"\n\n🕒 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        return base_message
    
    def _suggest_action(self, rule: AlertRule, metrics: Dict) -> str:
        """권장 조치 제안"""
        if rule.rule_id == "performance_critical":
            return "1. 에이전트 재시작 고려 2. 학습률 조정 3. 메모리 최적화"
        elif rule.rule_id == "performance_declining":
            return "1. 진화 전략 변경 2. 하이퍼파라미터 조정 3. 데이터 품질 확인"
        elif rule.rule_id == "evolution_failure":
            return "1. 로그 확인 2. 리소스 사용량 점검 3. 진화 알고리즘 재설정"
        elif rule.rule_id == "resource_usage_high":
            return "1. 불필요한 프로세스 종료 2. 메모리 정리 3. 부하 분산"
        elif rule.rule_id == "agent_unresponsive":
            return "1. 즉시 에이전트 재시작 2. 네트워크 연결 확인 3. 로그 분석"
        elif rule.rule_id == "excellent_performance":
            return "1. 현재 설정 백업 2. 성능 분석 3. 다른 에이전트에 적용 고려"
        else:
            return "상황에 따른 적절한 조치 필요"
    
    async def _send_alert(self, alert: Alert, channels: List[NotificationChannel]):
        """알림 전송"""
        for channel in channels:
            try:
                if channel in self.subscribers:
                    for callback in self.subscribers[channel]:
                        await self._safe_callback(callback, alert)
                else:
                    # 기본 채널 처리
                    if channel == NotificationChannel.CONSOLE:
                        self._send_console_alert(alert)
                    elif channel == NotificationChannel.DASHBOARD:
                        await self._send_dashboard_alert(alert)
                        
            except Exception as e:
                self.logger.error(f"❌ {channel.value} 채널 알림 전송 실패: {e}")
    
    async def _safe_callback(self, callback: Callable, alert: Alert):
        """안전한 콜백 실행"""
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(alert)
            else:
                callback(alert)
        except Exception as e:
            self.logger.error(f"❌ 콜백 실행 실패: {e}")
    
    def _send_console_alert(self, alert: Alert):
        """콘솔 알림 전송"""
        icon = {
            AlertLevel.INFO: "ℹ️",
            AlertLevel.WARNING: "⚠️",
            AlertLevel.CRITICAL: "🚨",
            AlertLevel.EMERGENCY: "🆘"
        }.get(alert.level, "📢")
        
        print(f"\n{icon} {alert.level.value.upper()}: {alert.title}")
        print(f"📝 {alert.message}")
        if alert.action_required:
            print(f"💡 권장 조치: {alert.action_required}")
        print("-" * 50)
    
    async def _send_dashboard_alert(self, alert: Alert):
        """대시보드 알림 전송"""
        # 대시보드 브로드캐스트를 위한 메시지 형식
        dashboard_message = {
            "type": "alert",
            "data": {
                "level": alert.level.value.upper(),
                "message": alert.message,
                "agent_id": alert.agent_id or "system",
                "action": alert.action_required,
                "timestamp": alert.timestamp.isoformat()
            }
        }
        
        # 대시보드가 있다면 전송 (import 시도)
        try:
            from agent_evolution_dashboard import broadcast_to_clients
            await broadcast_to_clients(dashboard_message)
        except ImportError:
            self.logger.debug("대시보드 모듈 없음 - 대시보드 알림 건너뛰기")
    
    def _is_in_cooldown(self, rule_id: str) -> bool:
        """쿨다운 확인"""
        if rule_id not in self.cooldown_tracker:
            return False
        
        rule = self.alert_rules[rule_id]
        last_alert = self.cooldown_tracker[rule_id]
        cooldown_end = last_alert + timedelta(minutes=rule.cooldown_minutes)
        
        return datetime.now() < cooldown_end
    
    def _save_alert_to_db(self, alert: Alert):
        """알림을 데이터베이스에 저장"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO alert_history 
                    (alert_id, rule_id, level, title, message, agent_id, 
                     timestamp, data, action_required)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    alert.alert_id, alert.rule_id, alert.level.value,
                    alert.title, alert.message, alert.agent_id,
                    alert.timestamp, json.dumps(alert.data), alert.action_required
                ))
                conn.commit()
        except Exception as e:
            self.logger.error(f"❌ 알림 저장 실패: {e}")
    
    def _background_monitor(self):
        """백그라운드 모니터링"""
        self.logger.info("🔄 백그라운드 알림 모니터링 시작")
        
        while self.monitoring_active:
            try:
                # 시스템 상태 체크
                self._check_system_health()
                
                # 오래된 알림 정리
                self._cleanup_old_alerts()
                
                # 30초 대기
                threading.Event().wait(30)
                
            except Exception as e:
                self.logger.error(f"❌ 백그라운드 모니터링 오류: {e}")
                threading.Event().wait(60)
    
    def _check_system_health(self):
        """시스템 건강 상태 확인"""
        try:
            import psutil
            
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            memory_usage = memory.percent
            
            # 시스템 리소스 알림 확인
            system_metrics = {
                'cpu_usage': cpu_usage,
                'memory_usage': memory_usage,
                'performance': 0.5,  # 기본값
                'trend': 0
            }
            
            # 비동기 함수를 동기적으로 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            loop.run_until_complete(self.check_conditions("system", system_metrics))
            loop.close()
            
        except ImportError:
            # psutil이 없으면 건너뛰기
            pass
        except Exception as e:
            self.logger.error(f"❌ 시스템 상태 확인 실패: {e}")
    
    def _cleanup_old_alerts(self):
        """오래된 알림 정리"""
        try:
            # 7일 이상 된 알림 정리
            cutoff_date = datetime.now() - timedelta(days=7)
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    DELETE FROM alert_history 
                    WHERE timestamp < ? AND resolved = TRUE
                """, (cutoff_date,))
                
                deleted_count = cursor.rowcount
                conn.commit()
                
                if deleted_count > 0:
                    self.logger.info(f"🧹 오래된 알림 {deleted_count}개 정리 완료")
                    
        except Exception as e:
            self.logger.error(f"❌ 알림 정리 실패: {e}")
    
    def get_alert_history(self, limit: int = 100) -> List[Dict]:
        """알림 히스토리 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM alert_history 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                """, (limit,))
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    alert_dict = dict(zip(columns, row))
                    alert_dict['data'] = json.loads(alert_dict['data'] or '{}')
                    results.append(alert_dict)
                
                return results
                
        except Exception as e:
            self.logger.error(f"❌ 알림 히스토리 조회 실패: {e}")
            return []
    
    def resolve_alert(self, alert_id: str, resolved_by: str = "system"):
        """알림 해결 처리"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE alert_history 
                    SET resolved = TRUE, resolved_at = ?, resolved_by = ?
                    WHERE alert_id = ?
                """, (datetime.now(), resolved_by, alert_id))
                conn.commit()
                
                if cursor.rowcount > 0:
                    self.logger.info(f"✅ 알림 해결: {alert_id}")
                    
        except Exception as e:
            self.logger.error(f"❌ 알림 해결 처리 실패: {e}")
    
    def get_active_alerts(self) -> List[Dict]:
        """활성 알림 조회"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM alert_history 
                    WHERE resolved = FALSE 
                    ORDER BY timestamp DESC
                """)
                
                columns = [desc[0] for desc in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    alert_dict = dict(zip(columns, row))
                    alert_dict['data'] = json.loads(alert_dict['data'] or '{}')
                    results.append(alert_dict)
                
                return results
                
        except Exception as e:
            self.logger.error(f"❌ 활성 알림 조회 실패: {e}")
            return []
    
    def stop_monitoring(self):
        """모니터링 중단"""
        self.monitoring_active = False
        self.logger.info("🛑 백그라운드 알림 모니터링 중단")

# 전역 알림 시스템 인스턴스
_notification_system = None

def get_notification_system() -> NotificationSystem:
    """전역 알림 시스템 인스턴스 반환"""
    global _notification_system
    if _notification_system is None:
        _notification_system = NotificationSystem()
    return _notification_system

# 편의 함수들
async def send_agent_alert(agent_id: str, metrics: Dict):
    """에이전트 알림 전송"""
    notification_system = get_notification_system()
    await notification_system.check_conditions(agent_id, metrics)

async def send_custom_alert(title: str, message: str, level: AlertLevel = AlertLevel.INFO, 
                          agent_id: str = None, action_required: str = ""):
    """커스텀 알림 전송"""
    notification_system = get_notification_system()
    
    alert_id = f"custom_{int(datetime.now().timestamp())}"
    alert = Alert(
        alert_id=alert_id,
        rule_id="custom",
        level=level,
        title=title,
        message=message,
        agent_id=agent_id,
        action_required=action_required
    )
    
    channels = [NotificationChannel.DASHBOARD, NotificationChannel.CONSOLE]
    await notification_system._send_alert(alert, channels)
    notification_system._save_alert_to_db(alert)

if __name__ == "__main__":
    # 테스트 코드
    async def test_notification_system():
        notification_system = get_notification_system()
        
        # 테스트 메트릭
        test_metrics = {
            'performance': 0.25,  # 임계점 아래
            'trend': -0.1,
            'cpu_usage': 95,
            'memory_usage': 90
        }
        
        print("🧪 알림 시스템 테스트 시작...")
        await notification_system.check_conditions("test_agent", test_metrics)
        
        # 커스텀 알림 테스트
        await send_custom_alert(
            "테스트 알림",
            "알림 시스템이 정상적으로 작동합니다",
            AlertLevel.INFO,
            "test_agent"
        )
        
        print("✅ 테스트 완료")
    
    asyncio.run(test_notification_system())
