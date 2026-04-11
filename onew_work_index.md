# 온유 ↔ Claude Code 최근 작업 인덱스
> 자동 생성: 2026-03-29 18:22 | 최근 14일 | API 비용: 0원

> Claude Code에서 이 파일 Read 1회로 전체 맥락 파악 가능.

## Claude Code 작업일지


### 2026-03-29
- **준공도서 오탐 수정**
  _온유에게 "로그 알람기능 어떻게 생각해?" 질문 시 `[준공도서] 라우터 발화` 출력 확인._
- **메모리시스템 안정화**
  _3/28 메모리 구조 개편 이후 5가지 안정화 작업 완료._
- **로그시스템 구축**
  _온유 시스템 "완전 무로그 상태"에서 "스스로 문제를 알리는 시스템"으로 전환._
- **RAG 파이프라인 개선** → onew_core/query_pipeline.py, memory/entities.md
  _메모리시스템 안정화(9개 항목) 이후 RAG 파이프라인 3개 항목 추가 개선._

### 2026-03-28
- **준공도서RAG 장비추론 고장힌트구현**
- **준공도서RAG 앵커기반추출 구현** → work_extract_pdf_structured.py
- **준공도서RAG 보일러급수펌프 P0-0301 추출**
  _온유가 "보일러급수펌프 압력이 몇이야", "모터 부하측 베어링 넘버는?" 쿼리에 정확한 데이터를 반환하지 못함._
- **준공도서RAG Company34 펌프 JSON 수동추출**
  _자동 추출(work_extract_pdf_structured.py_
- **온유 자동보고 체인구현**
- **온유 메모리시스템 구조개편**
  _온유가 "보완사항 저장 완료"라고 말만 하고 실제 저장 안 하는 문제 + User_Profile 무한 팽창 + 클리핑 방향성 없음 진단 → 4가지 구조 개편_
- **온유 라우팅개선 APM 회차변환** → SYSTEM/onew_apm.py
- **온유 APM lite 구현** → query_log.json
  _로그 수집(비침습 4종) 완료 후 해석 레이어 추가 — 규칙 기반 진단_
- **보완사항생성불가버그수정** → obsidian_agent.py, onew_system_prompt.md

### 2026-03-27
- **준공도서 RAG Phase7 라우터 pdf structured 연동**
  _| 이전 | 이후 |_
- **준공도서 RAG Phase6 TagFirst PDF추출기 완료**
  _| 문제 | 심각도 | 내용 |_
- **준공도서 RAG Phase5 라우터버그수정 완료** → work_query_router.py
- **준공도서 RAG Phase4 라우터 도면인덱서 완료** → work_query_router.py, work_index_dwg.py, obsidian_agent.py
  _| 스크립트 | 역할 | 상태 |_
- **준공도서 RAG Phase1 2 3 완료** → work_make_manifest.py, work_extract_xlsx.py, work_extract_pdf.py
  _| 스크립트 | 역할 | 상태 |_
- **준공도서 Phase2 XLSX추출기 생성** → work_make_manifest.py, file_manifest.json
  _`work_make_manifest.py` (Phase 1) 완료 후, Phase 2 첫 번째 스크립트 작성._
- **온유시스템 보완사항 전체** → SYSTEM/onew_night_study.py
- **온유시스템 보완사항3종 수정** → onew_night_study.py
- **온유 정서위기지원모드 추가** → onew_system_prompt.md
  _용준 님이 자살 관련 내용을 언급했을 때 온유가 "전문가 상담 받으세요"로 응답함._

### 2026-03-26
- **텔레그램 인박스 승인시스템 구축**
  _| 원제안 | 온유 시스템 적용 결과 |_
- **온유실전테스트**
  _20:20 ~ 20:25 (테스트 실행 약 5분)_
- **온유 약점보완 W1~W5**
  _| 항목 | 내용 | 결과 |_
- **온유-35문항-실전테스트** → SYSTEM/onew_core/query_pipeline.py
  _| 카테고리 | PASS | PARTIAL | FAIL | ACTION | 합계 |_
- **스킬시스템 검증 및 오탐버그수정**
  _| 테스트 | 결과 |_
- **sync embed limit guard** → obsidian_agent.py
  _`obsidian_agent.py`의 `OnewPureMemory.sync()` 메서드 초반부에 임베딩 API 일일 한도 체크 로직 추가._
- **quiz me 파일경로 검색 개선** → quiz_me(file_path='2026-03-18_공조냉동_01.md
- **Phase16B-SRE대시보드-Drift감지** → shadow_rl_engine.py
  _제안된 Phase 16_
- **Phase13B Shadow RL 구현**
  _| 파일 | 작업 |_
- **Phase12.5 메트릭수집기 구현** → SYSTEM/action_taxonomy.json, SYSTEM/tools/metrics_collector.py, SYSTEM/tools/baseline_calculator.py
  _| 파일 | 설명 |_
- **option b llm microrouter**
  _"뭐 먹었어" vs "뭘 먹었어" — 단어 한 글자 차이로 같은 날짜 쿼리 실패._
- **morning briefing wrong tracker**
  _PTB JobQueue `run_daily` 사용 (apscheduler 기존 설치 확인됨)._
- **exam vision 3line rule**
  _`STATIC_BLOCK_v1` [응답 원칙] 최상단에 추가:_
- **eojeogje temporal fix**
  _"엊그제 내가 뭐 먹었지?" → "쌈을 먹었습니다" (hallucination)_
- **code planner approval fix**
  _"실행해" 입력 → 승인 미인식 → smolagents 루프 진입 → 7단계 × 20k 토큰 = 130k 토큰 소모 + "Reached max steps"_
- **claude relay**
  _텔레그램에서 온유에게 "클로드: 요청"을 보내면 Claude Code subprocess가 실행되고 결과를 실시간 스트리밍으로 받는 시스템 구현._
- **bg task notification**
  _Claude Code처럼 온유도 비동기 백그라운드 작업 실행 후 완료 알림을 보내는 기능 추가._

### 2026-03-25
- **온유 시작시 Claude작업 자동인식** → SYSTEM/onew_core/session_manager.py
  _온유가 Claude Code의 최근 작업을 스스로 알아서 환각 방지 + 맥락 파악._
- **온유 스킬시스템 구축** → SYSTEM/skills/core/01_identity.md, SYSTEM/skills/core/02_self_heal.md, SYSTEM/skills/core/03_code_rules.md, SYSTEM/skills/core/04_meta_learning.md
  _온유의 system_prompt 하드코딩 구조를 마크다운 기반 플러그인 스킬 구조로 전환._
- **오류로그 파이프라인 검증** → SYSTEM/obsidian_agent.py, SYSTEM/온유_오류.md, SYSTEM/mcp_servers/system_server.py
  _"오류를 실제로 발생시켜서 로그가 쌓이고 확인할 수 있는지 확인해봐"_
- **시간순 정렬 버그 수정** → SYSTEM/onew_core/query_pipeline.py
  _Vault 청크가 날짜 레이블 없이 LLM에 전달됨 → LLM이 시간순 정렬 불가._
- **빠른시작 최근동기화 추가** → 온유_빠른실행.bat, SYSTEM/obsidian_agent.py, C:\Users\User\Desktop\온유_빠른실행.bat
  _1. 최근 7일 내 수정된 .md 파일 스캔_
- **능동형 스킬 3종 구현**
  _기존 온유 시스템의 반응형(Reactive) 한계를 극복하기 위해 3가지 능동형 스킬 구조 설계._
- **Temporal RAG 어제오늘 날짜범위 추가** → SYSTEM/onew_core/query_pipeline.py
  _이전 세션에서 _TEMPORAL_KW 정규식에 "어제|그저께|오늘|내일"을 추가했으나,_
- **Temporal RAG query pipeline 추가**
  _과거 사건 디테일 질문 시 시간 정보 취약 문제 해결._
- **skills server MCP 구현** → SYSTEM/mcp_servers/skills_server.py, SYSTEM/skills/optional/python_async.md, SYSTEM/skills/optional/python_typing.md
  _Behavior RAG (스킬) ↔ Knowledge RAG (LanceDB) 완전 분리 구조 구현._
- **Pattern RAG 및 Safety Guards 구현**
  _Decision Layer 통합 전 필수 선행 작업._
- **Pattern RAG Context 주입 및 Delta 완성**
  _| 제안 | 문제점 | 조치 |_
- **api사용량쿼리 action라우팅 수정**
  _"오늘 api 호출 횟수는 몇 회니?" → `tools.get_api_usage()` 텍스트 출력_

### 2026-03-22
- **학습설계엔진 구축** → onew_review_scheduler.py
  _자율학습이 임의로 실행되는 문제 → 설계 계획 기반 학습 시스템 구축 요청_
- **코드인덱스 자동갱신** → SYSTEM/onew_code_indexer.py
  _obsidian_agent.py 수정 시 온유_코드구조.md가 자동 업데이트되지 않는 문제_
- **온유시스템 검색파이프라인 대규모패치**
- **온유 퀴즈모드 파일경로 버그수정**
  _사용자가 '공조냉동기계기사 실기 합본' 파일 위치를 알려줘도 온유가 Vault 실제 파일을 읽지 않고 AI 생성 문제를 보여주는 문제._
- **온유 코드플래너 확인단계 추가**
- **온유 코드플래너 자율개선 수정** → interface_summary.json, src/onew_system/core/interface.py, onew_contract.py
  _코드플래너가 `interface_summary.json` 없이 실행 → Gemini가 존재하지 않는 `src/onew_system/core/interface.py` 경로를 생성 → 계속 실패/중단_
- **온유 장기기억 사용자프로필 개선** → User_Profile.md
  _1. `User_Profile.md`가 존재하지만 온유 시스템 프롬프트에_
- **온유 성장로드맵 설계** → SYSTEM/onew_growth_roadmap.md
  _코드플래너가 자동 실행되며 Kafka, Kubernetes, ELK Stack 등 과도한 개선안 생성 → 시스템 수준에 맞는 현실적 로드맵 필요_
- **실시간 임베딩 훅 및 작업인덱스**
  _1. Claude Code가 .md 파일 수정 시 즉시 LanceDB에 반영 (sync 12시간 대기 제거)_
- **방어기제 텔레그램 알림**
  _온유가 코드 생성 중 Gemini Safety 필터에 막혔을 때 어떤 오류인지 알 수 없었던 문제_
- **v2마이그레이션 5단계 병렬운영준비**
- **v2마이그레이션 4단계 진입점교체**
  _`_auto_backup()` 직후에 v2/legacy 분기 블록 삽입._
- **v2마이그레이션 3단계 OnewSessionManager**
  _obsidian_agent.py의 고유 기능을 OnewAgentV2 래퍼로 이식._
- **v2마이그레이션 2단계 system prompt강화**
- **v2마이그레이션 1단계 MCP서버보완**
- **Phase0 Step1~4 용어DB BM25업그레이드**
- **Phase0 Step0 Step1 초안작성** → SYSTEM/onew_core/prompt_builder.py, system_prompt.py
- **Phase0 SingleShot파이프라인** → SYSTEM/onew_core/query_pipeline.py
- **Phase0 ContactMigrator**
  _| 항목 | 수치 |_
- **Phase05 AsyncLearner**
  _온유가 모르는 용어(검색 미달)를 자동 수집 → 배치 LLM → 신뢰도 기반 자동 등록_
- **onew search LanceDB 마이그레이션** → onew_search.py, onew_pure_db.json
  _`onew_search.py`가 구버전 `onew_pure_db.json` (빈 파일, 메타데이터만 존재)을 참조해 검색 결과 항상 없음._
- **MCP 등록 및 v2 마이그레이션 계획**
  _| 서버 | 도구 수 | 상태 |_
- **interface summary 갱신** → interface_summary.json, obsidian_agent.py

### 2026-03-20
- **학습목표 포착기 구현**
  _ADHD 특성: 순간 떠오른 궁금증을 즉시 포착 → 망각 방지 → 야간학습 자동 투입._
- **최종검증 설명원칙 추가**
  _| 파일 | 문법 | 동작 |_
- **자율코딩 기반설계**
- **자율코딩 v4 안전망강화**
- **자율코딩 v4 문제점6개 해결**
- **자율코딩 v4 pytest TDD**
  _검사 순서 (4단계 게이트):_
- **자율코딩 v4 aider 연동**
- **자율코딩 v3 완성**
- **자율코딩 v2 완성**
  _| 액션 | 설명 |_
- **자율코딩 Lv5 핵심4가지**
- **인터페이스계약 onew contract** → SYSTEM/onew_contract.py, SYSTEM/interface_contract.json, SYSTEM/interface_summary.json
- **온유 코드플래너 v3 완성**
- **온유 ADHD 보조 프로토콜 추가** → onew_system_prompt.md
  _`onew_system_prompt.md` 섹션 9 "ADHD 보조 프로토콜" 추가 및 심층 개선._
- **야간학습 문제생성 제거**
  _야간자율학습에서 예상 시험 문제 5개 생성 기능 완전 제거._
- **세션연계성 체크리스트감지 개선**
- **세션연계성 Lv3 Lv4 적용** → 대화요약/YYYY-MM-DD_대화요약.md
- **세션연계성 Lv1 Lv2 적용**
- **검증강화 Ruff 테스트품질 계약개선**
- **개념정리 지연로직 추가**
  _대화 중 또는 동기화 중에 `[개념정리]`가 실행되어 지연이 발생하는 문제 수정._
- **SafePoint 테스트 완료**
- **quiz me 파일지정 기능추가** → 2026-03-20_21-07_보완사항_점검.md
  _보완사항 `2026_
- **onew adhd 엔진 구현**
- **Obsidian 최적화 및 백업 외부이전** → test_canary.py, test_hidden_dependency.py
- **Lv5 Masterplan 완료** → test_canary.py
- **API 제한 정비**
  _| 항목 | 이전 | 이후 | 이유 |_

### 2026-03-19
- **온유 에이전틱 아키텍처 구축**
- **온유 서킷브레이커 NSSM 정리** → api_usage_log.json
- **보완사항B유형3가지수정**
- **search vault deadlock 수정**
  _20:45 ~ 20:55 (약 10분, 원인 파악 포함 약 30분)_
- **LanceDB버그수정및검색복구**
- **DAILY폴더 정리 및 동기화 점검**

### 2026-03-18
- **텔레그램파일명 DAILY규칙 수정** → 2026-03-18.md, DAILY/2026-03-18.md, telegram_export_to_md.py, {day_str}.md
- **캘린더 중복검사 추가** → obsidian_agent.py
- **출처명시규칙추가**
  _온유가 생성하는 파일과 정보에 출처를 명확히 표기하도록 규칙 추가._
- **종합작업일지** → onew_night_study.py
- **전체작업일지** → SYSTEM/onew_to_claude.md
- **재부팅 순서 안전장치** → obsidian_agent.py
  _| 시나리오 | 증상 |_
- **자율에이전트 아키텍처 검토**
  _| 제안 | 판정 | 이유 |_
- **자가치유 루프 구현** → SYSTEM/obsidian_agent.py
  _| 문제 | 해결 |_
- **일기PDF변환기 개선** → diary_pdf_to_md.py
  _`diary_pdf_to_md.py` 초기 버전에서 발생한 오류 4건 수정 + [[oylbinobsidian_
- **일기PDF변환기**
  _블로그 일기 PDF 20개 → [[옵시디언]] DAILY [[마크다운, Markdown 코드 블록]] 자동 변환 [[Python File Scanner Diagnostic Analysis|스크립트]] 제작._
- **온유시스템개선 전체적용** → SYSTEM/onew_antipatterns.md, obsidian_agent.py
- **온유 빠른시작 백그라운드sync** → SYSTEM/obsidian_agent.py
- **오답노트시스템적용**
  _1. `C:\Users\User\Documents\Obsidian Vault\SYSTEM\onew_antipatterns.md` — 신규 생성 (오답 노트_
- **야간학습 성장루프 구현** → embed_queue.json
  _| 충돌 | 해결 |_
- **시크릿모드오탐 topics오류 수정**
- **스킬파일6개추가** → daily_briefing.md, hvac_solver.md, ocu_pass.md, vault_cleanup.md
  _| 파일 | 트리거 키워드 |_
- **미완료작업자동재개** → _Checklist.md, _Plan.md
  _[[Onew_Background_Log|온유]] 부팅 시 이전 세션의 미완료 working_memory를 자동 감지하여 사용자에게 재개 여부를 안내하는 기능 추가._
- **마크다운표준화**
  _온유의 마크다운 출력 품질 향상 — Callout/[[Shrimp MCP|Mermaid]]/Wikilinks/[[공조부하|YAML]]/템플릿/자가개선 6가지 구현._
- **내일 작업예정**
- **공조냉동 과년도 문제생성 강제** → SYSTEM/onew_night_study.py, OCU/공조냉동기계기사/실기기출_25년1-3회.md
- **Wikilinks규칙수정**
  _[[마크다운, Markdown 코드 블록]] 표준화 작업에서 추가된 Wikilinks 자동 삽입 규칙의 링크 충돌 위험 3가지 수정._
- **RAG검색 품질개선**
- **list files Vault경로 수정**
  _온유가 `list_files` 도구 사용 시 Vault 경로를 찾지 못하는 문제 수정._
- **LanceDB 마이그레이션** → SYSTEM/obsidian_agent.py
- **Google Devblog 학습 추가** → obsidian_agent.py
- **DB지연로딩적용** → SYSTEM/db_backup/onew_pure_db_MANUAL_20260318_113202.json
  _onew_pure_db.json (1.34GB, 1081문서)의 메모리 부하를 두 단계로 최적화._
- **DAILY 이미지 attachments 분리**
- **APScheduler browseWeb 구현** → onew_scheduler.py
  _| 항목 | 전 | 후 |_
- **API 과금 안전장치**
  _| 카테고리 | 3/18 | 3/17 | 3/16 | 비고 |_
- **Anthropic 공홈 학습 추가** → obsidian_agent.py, 클리핑/Anthropic/YYYY-MM-DD_제목.md, onew_night_study.py

### 2026-03-17
- **파일충돌방지 원자적쓰기 적용**
- **중복파일명해소**
  _[[How to Sync [[옵시디언]] Notes Across Devices for Free Using GitHub|Obsidian Vault]] 내 중복 파일명 25개 일괄 리네임 완료._
- **온유재부팅자동실행 텔레그램봇 클리핑수정** → onew_telegram_bot.py
- **온유시스템 전체업데이트** → onew_telegram_bot.py
- **온유시스템 안정성 태스크관리**
- **온유 태스크 일괄처리**
- **온유 퀴즈기능 실패학습 구현**
- **온유 자율에이전트 안전성강화**
- **온유 안정화 자율화 완성**
- **온유 대화연속성 맥락강화** → obsidian_agent.py
  _사용자가 "구체적으로 얘기해달라"는 말을 자주 해야 하는 문제 → [[2026_
- **온유 대규모 개선작업**
- **온유 다음단계 구현** → SYSTEM/작업_진행계획.md
- **오후작업 예정사항** → obsidian_agent.py

### 2026-03-16
- **텔레그램봇 현장분석 구현** → onew_telegram_bot.py, onew_field_analyzer.py
  _1. 온유 텔레그램 봇 구현 (`onew_telegram_bot.py`)_
- **텔레그램 수집 문서변환 개선** → SYSTEM/telegram_export_to_md.py, result.json, 텔레그램/그룹명/YYYY-MM-DD.md
- **전체작업정리** → onew_safety_apis.py, SYSTEM/onew_safety_apis.py
- **자율형 에이전트 1차 구현** → SYSTEM/onew_weakness_tracker.py, 약점노트/개념명.md
  _[[Clippings/오픈클로 설치하고 느낀 솔직 사용기 – 이게 진짜 AI 비서구나]] 수준을 넘어 진정한 자율형 에이전트로 발전._
- **온유 자율형 완성 및 대화** → telegram_collector.py, telegram_state.json
  _어제 만들다 멈춘 `telegram_collector.py` 중복 방지를 완성했다._
- **온유 자율형 Level2 완성 및 소각장전문화** → onew_shared.py, onew_weakness_tracker.py
  _총 6개의 자율 모듈을 새로 만들었다._
- **온유 모바일 연동** → SYSTEM/onew_mobile_server.py, Desktop/온유_모바일_실행.bat
- **안전분석 KOSHA Claude 통합**

## 온유 자율코딩 변경이력

- **2026-03-22 00:00** 1427 onew budget.py

## 현재 코드 상태 (interface_summary.json)

- `obsidian_agent.py`: 클래스: _MetaCompat, OnewPureMemory, AutoClipper, OnewAgent, WakeWordListener | 함수 84개 | 5782줄
- `onew_self_improve.py`: 클래스: CircuitBreaker, NeedAnalyzer, ASTChecker, SafetyGate, SandboxTester | 함수 11개 | 1379줄
- `onew_contract.py`: 함수 6개 | 350줄
- `onew_code_planner.py`: 함수 30개 | 1006줄
- `onew_watcher.py`: 클래스: VaultEventHandler, SystemFolderHandler | 함수 11개 | 552줄
- `onew_meta.py`: 클래스: MetaEngine | 함수 11개 | 375줄
- `onew_night_study.py`: 클래스: _LastInputInfo, _Extractor, _Extractor | 함수 30개 | 914줄
- `onew_adhd.py`: 클래스: FeatureTracker, HyperfocusGuard, StudyStreak, LearningGoalCatcher, ADHDEngine | 함수 12개 | 484줄
- `onew_adhd_coach.py`: 클래스: ADHDCoach | 함수 8개 | 517줄
- `onew_task_manager.py`: 함수 9개 | 175줄
- `onew_budget.py`: 함수 7개 | 140줄
- `onew_review_scheduler.py`: 클래스: ReviewScheduler | 함수 5개 | 200줄
- `onew_weakness_tracker.py`: 클래스: WeaknessTracker | 함수 6개 | 172줄
- `onew_planner.py`: 클래스: DailyPlanner | 함수 21개 | 478줄
- `onew_shared.py`: 함수 5개 | 82줄
- `onew_tools.py`: 함수 5개 | 113줄
- `onew_locks.py`: 함수 4개 | 133줄
- `onew_scheduler.py`: 함수 11개 | 315줄
- `onew_field_linker.py`: 함수 11개 | 275줄
- `onew_field_analyzer.py`: 함수 8개 | 443줄
- `pdf_to_md.py`: 함수 10개 | 401줄

## 최근 API 사용량

- 2026-03-29: 총 {'chat': 69, 'profile_update': 3, 'entity': 13} | chat 0 | rag 0 | 야간학습 0
- 2026-03-28: 총 {'chat': 116, 'entity': 30, 'profile_update': 13} | chat 0 | rag 0 | 야간학습 0
- 2026-03-27: 총 {'chat': 29, 'entity': 8, 'profile_update': 2} | chat 0 | rag 0 | 야간학습 0
- 2026-03-26: 총 {'chat': 91, 'entity': 22, 'profile_update': 12} | chat 0 | rag 0 | 야간학습 0
- 2026-03-25: 총 {'chat': 120, 'entity': 30, 'profile_update': 18} | chat 0 | rag 0 | 야간학습 0