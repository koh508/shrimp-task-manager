---
tags: [설계문서, 마이그레이션, OnewAgentV2]
날짜: 2026-03-22
상태: 승인대기
---

# 온유 v2 마이그레이션 계획 (obsidian_agent → OnewAgentV2 + MCP)

> 목표: 현재 obsidian_agent.py의 monolith 구조를 OnewAgentV2(smolagents + MCP) 기반으로 전환
> 기존 고유 기능(ADHD 엔진, 세션 관리, 과금 보호 등)은 100% 보존

---

## 현황 요약

### 도구 중복 현황 (전부 MCP로 대체 가능)

| tool_map 항목 | MCP 서버 |
|---|---|
| read_file, write_file, edit_file, create_folder, list_files, move_file, delete_file, rollback_file, backup_system | vault_server.py |
| search_vault, fetch_url_as_md, browse_web, analyze_image, analyze_trend | vault_server.py |
| execute_script, run_shell_command | system_server.py |
| calendar_list/add/add_force/update/delete | system_server.py |
| get/set_secret_mode, clip_*, task_* | system_server.py |
| quiz_me | study_server.py |
| code_safety_check, save_code_checksums | ❌ MCP 미등록 (1단계에서 추가) |
| create_working_memory | ❌ @mcp.tool() 누락 (1단계에서 추가) |
| refresh_code_index | ❌ MCP 미존재 (1단계에서 추가) |

### obsidian_agent.py 고유 기능 (MCP로 대체 불가 → 래퍼 레이어 이식)

1. `ask()` — RAG 자동 주입 + tool_loop(10회) + 오류 자가치유
2. 세션 관리 — `_new_chat_session()`, 10턴 자동 리셋, 요약 저장
3. 맥락 복원 — `_summarize_last_session()`, 직전 세션 재주입
4. 엔티티 워킹메모리 — 3턴마다 `_extract_entities()`
5. 사용자 프로필 자동 업데이트 — 6턴마다 `_update_user_profile_facts()`
6. ADHD 엔진 통합 — `on_user_message()`, 과집중 감지, 스트릭, 도파민 메뉴
7. 오답 패턴 기록 — 교정 키워드 감지 → `_save_mistake()`
8. 실패사례 선조회 — 코드 작업 감지 시 자동 RAG 후 컨텍스트 주입
9. 텔레그램 알림 — 과금 경고, 반복 에러, Safety 방어기제
10. 과금 보호 — 500회 하드스톱, `_increment_usage()`
11. 회사 모드 차단 — SENSITIVE_KEYWORDS (API 호출 전 필터)
12. 동적 시스템 프롬프트 조립 — User_Profile.md + antipatterns + skills

---

## 단계별 계획

### 1단계: MCP 서버 보완 (준비)

**목표:** tool_map에 있으나 MCP에 없는 도구 3개 추가

수정 파일: `mcp_servers/system_server.py`
- `create_working_memory`에 `@mcp.tool()` 데코레이터 추가
- `code_safety_check` 도구 추가 (현재 obsidian_agent.py 내부 로직 이식)
- `save_code_checksums` 도구 추가

수정 파일: `mcp_servers/vault_server.py`
- `refresh_code_index` 도구 추가 (onew_code_indexer.py 호출 래퍼)

검증:
```bash
python mcp_servers/system_server.py  # 오류 없이 시작
python mcp_servers/vault_server.py   # 오류 없이 시작
```

완료 기준: `claude mcp list`에서 3개 서버 ✓ Connected 유지

---

### 2단계: system_prompt.py 강화 (준비)

**목표:** obsidian_agent.py의 `_build_system_prompt()` 내용을 `onew_core/system_prompt.py`에 반영

현재 `system_prompt.py` 누락 규칙:
- 퀴즈 모드 규칙 (file_path 파라미터, AI 생성 금지, 실기 합본 기본 경로)
- 즉시/주간 클리핑 규칙
- 복잡한 작업 시 계획표 강제 규칙
- 실패사례 선조회 규칙 (코드 작업 전 search_vault 필수)
- 보완사항 자동 저장 규칙
- User_Profile.md 동적 로딩 (현재 `build()` 함수가 정적 텍스트)

`build(location_mode)` → `build(location_mode, user_profile="", antipatterns="")` 로 확장

검증: `python -c "from onew_core.system_prompt import build; p=build('home'); print(len(p), '자')`
완료 기준: 프롬프트 길이 현재 obsidian_agent.py 수준과 근접

---

### 3단계: OnewSessionManager 작성 (핵심)

**목표:** obsidian_agent.py 고유 기능을 OnewAgentV2를 감싸는 얇은 계층으로 구현

새 파일: `onew_core/session_manager.py`

```python
class OnewSessionManager:
    def __init__(self, location_mode=None):
        # 1. 고유 모듈 초기화 (ADHD, 세션, 엔티티 등)
        # 2. OnewAgentV2 초기화 (MCP 서버 연결)
        # 3. 맥락 복원 (_load_recent_summaries → agent instructions에 주입)

    def ask(self, query: str) -> str:
        # === 호출 전 ===
        # 1. 과금 하드스톱 (500회)
        # 2. 회사 모드 클라이언트 차단 (SENSITIVE_KEYWORDS)
        # 3. ADHD 엔진 (on_user_message, detect_learning_goal)
        # 4. 오답 패턴 감지
        # 5. 코드 작업 시 실패사례 선조회 → query에 컨텍스트 주입
        # === OnewAgentV2 호출 ===
        # 6. self.agent.run(enriched_query)
        # === 호출 후 ===
        # 7. 엔티티 추출 (3턴마다)
        # 8. 프로필 업데이트 (6턴마다)
        # 9. turn_count 증가, 10턴 초과 시 세션 리셋 + 요약 저장
        # 10. 과금 카운터 증가 + 텔레그램 경고
```

검증:
- `OnewSessionManager` 단독 import 오류 없음
- 10턴 후 자동 세션 리셋 확인
- ADHD 엔진 `on_user_message()` 호출 확인

완료 기준: `OnewSessionManager().ask("테스트")` 정상 응답

---

### 4단계: obsidian_agent.py 진입점 교체 (연결)

**목표:** 메인 루프가 OnewSessionManager를 사용하도록 전환

변경 내용:
```python
# 기존 (유지, --legacy 플래그 시 사용)
onew = OnewAgent()  # 기존 클래스 유지

# 신규 (기본)
from onew_core.session_manager import OnewSessionManager
onew = OnewSessionManager(location_mode=...)
```

`--legacy` 플래그 추가:
```bash
python obsidian_agent.py          # OnewSessionManager (신규)
python obsidian_agent.py --legacy # OnewAgent (기존, 롤백용)
```

검증:
```bash
python obsidian_agent.py "테스트 질문"     # 신규 경로 응답
python obsidian_agent.py --legacy "테스트"  # 기존 경로 응답
```

완료 기준: 두 경로 모두 응답 정상, 기존 BAT 파일 수정 불필요

---

### 5단계: 병렬 운영 및 검증 (1주일 관찰)

**목표:** 신규/기존 경로 동시 운용, 실사용 검증

검증 항목 체크리스트:
- [ ] 퀴즈 모드: `quiz_me`가 실제 파일 읽어서 문제 출제
- [ ] 파일 편집: `edit_file` 정상 작동, 보호 파일 거부 확인
- [ ] 캘린더: `calendar_add` → 구글 캘린더 반영
- [ ] 검색: `search_vault` LanceDB 결과 동일
- [ ] ADHD 스트릭 기록 유지
- [ ] 10턴 후 세션 리셋 + 대화요약 저장
- [ ] Safety 차단 시 텔레그램 알림
- [ ] smolagents tool loop 안정성 (max_steps 초과 시 처리)
- [ ] MCP subprocess 종료 시 좀비 프로세스 없음

이상 발견 시: `--legacy` 플래그로 즉시 롤백

---

### 6단계: 정리 (안정화 확인 후)

obsidian_agent.py에서 제거:
- `tool_map` 딕셔너리
- `onew_tools` 리스트
- tool loop (while function_calls...)
- `OnewAgent` 클래스 본체

유지:
- 최상단 임포트 (utils, 상수 정의)
- `if __name__ == "__main__"` 메인 루프
- 과금/usage 카운터 함수들

---

## 위험 요소 & 대응

| 위험 | 대응 |
|------|------|
| smolagents + LiteLLM + Gemini function calling 불안정 | 5단계에서 1주일 병렬 운용 후 판단 |
| Windows MCP subprocess 좀비 프로세스 | `atexit.register(self.close)` + BAT에 taskkill 추가 |
| asyncio + smolagents 스레드 충돌 | vault_server.py lancedb 모듈 레벨 preload 유지 (이미 적용됨) |
| 시스템 프롬프트 토큰 비용 증가 | 2단계에서 동적 조립 유지, 세션 리셋마다 agent.reload() |
| RAG 컨텍스트 자동 주입 소실 | system_prompt에 "모든 질문 전 search_vault 먼저" 규칙 강화 |

---

## 파일 변경 목록 (예상)

```
신규:
  SYSTEM/onew_core/session_manager.py

수정:
  SYSTEM/mcp_servers/system_server.py   (도구 3개 추가)
  SYSTEM/mcp_servers/vault_server.py    (refresh_code_index 추가)
  SYSTEM/onew_core/system_prompt.py     (프롬프트 대폭 확장)
  SYSTEM/obsidian_agent.py              (진입점만 교체, --legacy 플래그)

삭제 (6단계, 안정화 후):
  SYSTEM/obsidian_agent.py 내 tool_map, onew_tools, tool_loop, OnewAgent 클래스
```

---

## 진행 상황

- [x] A단계: Claude Code MCP 등록 완료 (2026-03-22)
  - onew-vault ✓ Connected
  - onew-system ✓ Connected
  - onew-study ✓ Connected
- [x] 1단계: MCP 서버 보완 (2026-03-22)
- [x] 2단계: system_prompt.py 강화 (2026-03-22)
- [x] 3단계: OnewSessionManager 작성 (2026-03-22)
- [x] 4단계: obsidian_agent.py 진입점 교체 (2026-03-22)
- [ ] 5단계: 병렬 운영 1주일
- [ ] 6단계: 정리
