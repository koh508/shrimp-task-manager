# [OPTIONAL SKILL] Proactive Monitoring & Alerting

keywords: monitoring alert daemon watcher polling threshold notify proactive background schedule

## 현재 아키텍처 제약 (중요)
온유는 CLI 세션 기반 — 대화 중에만 프로세스 존재.
알림은 **파일 기반 큐** 방식으로 구현 (온유 시작 시 읽음).

```
외부 트리거 → watcher_daemon.py (Task Scheduler) → alerts.json → 온유 시작 시 읽기
```

## 모니터링 항목
| 항목 | 방법 | 임계치 |
|------|------|--------|
| 디스크 잔여량 | shutil.disk_usage | <10GB 경고 |
| 로그 파일 크기 | os.path.getsize | >5MB |
| Vault 크기 증가율 | 이전 기록 비교 | +100MB/일 |
| 스크립트 실패 이력 | auto_scripts/*.log | 최근 오류 |
| 시스템 메모리 | psutil.virtual_memory | >85% |

## 알림 파일 형식 (SYSTEM/alerts.json)
```json
[
  {
    "level": "WARN",
    "time": "2026-03-25T09:00:00",
    "message": "C: 드라이브 잔여량 8.2GB — 정리 권장",
    "action": "disk_cleanup"
  }
]
```

## 온유 시작 시 알림 읽기 (session_manager 연동)
```python
# session_manager.py 시작 시
alerts = load_alerts("SYSTEM/alerts.json")
if alerts:
    print("[알림] 새로운 시스템 알림이 있습니다:")
    for a in alerts:
        print(f"  [{a['level']}] {a['message']}")
```

## Windows Task Scheduler 설정
```
작업 이름: OnewMonitor
트리거: 매일 09:00, 18:00
동작: python SYSTEM/auto_scripts/monitor_daemon.py
조건: 인터넷 연결 불필요
```

## 구현 우선순위
현재 아키텍처에서 즉시 구현 가능:
1. 디스크 용량 체크 (shutil — 표준 라이브러리)
2. 로그 파일 크기 체크
3. 스크립트 실패 이력 감지

psutil 필요 (선택):
4. 메모리/CPU 모니터링
