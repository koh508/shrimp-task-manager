# [OPTIONAL SKILL] System Self-Optimization

keywords: optimizer system optimize cache hit-rate skill usage proactive suggest recommendation

## 언제 사용하는가
- 온유 대화 중 "시스템 점검", "최적화", "안 쓰는 스킬" 언급 시
- 매일 첫 대화 시작 시 자동 점검 (daily reflection)

## 점검 항목
| 항목 | 측정 방법 | 임계치 |
|------|-----------|--------|
| 스킬 파일 크기 | 파일 바이트 | >10KB → 분리 권장 |
| experimental 누적 | 파일 수 | >5개 → 정리 권장 |
| 로그 파일 크기 | 바이트 | >5MB → 로테이션 권장 |
| Vault 고아 파일 | 링크 없는 md | 보고만 |

## 제안 생성 원칙
1. 수치 기반 — 주관적 판단 금지
2. 행동 가능 — "~하면 어떨까요?" 형식
3. 동의 후 실행 — 사용자 확인 없이 삭제/변경 금지

## 스크립트 연동
```bash
# 온유 내부에서 호출
execute_script("auto_scripts/system_optimizer.py")
```

## 출력 형식 (온유 리포트)
```
[SYSTEM REPORT] 2026-03-25
- experimental/: 2개 파일 (정상)
- skills 최대 파일: dev_code_review.md (3.1KB)
- 30일 미사용 스킬: dev_docker.md

제안:
1. dev_docker.md 를 experimental/ 로 이동할까요?
2. 다음 최적화: 없음
```
