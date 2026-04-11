---
tags: [로드맵, 온유, MCP, semantic-router, APM]
작성: 2026-03-28
시작예정: 2026-04-19
목표완료: 2026-06-30
---

# 온유(Onew) 시험 후 개발 전략 로드맵 v1.0

> 공조냉동기계기사 실기 시험(2026-04-18) 종료 후 진행.
> 감이 아니라 데이터로 진화한다.

---

## 전체 타임라인

### 의존관계

```
작업1: Router Interface 추상화 (4/19 ~ 4/25)
  └─→ 작업2: Semantic Router shadow mode (4/26 ~ 5/10)
        └─→ [100건 누적 관찰: 5/10 ~ 6/07]
              └─→ Semantic Router 전환 결정 (6/08)

작업3: APM precision/recall 추가 (4/19 ~ 4/23, 작업1과 병렬)
  └─→ [데이터 누적: 4/23 이후 상시 측정]

작업4: MCP 분할 (5/11 ~ 6/30, 작업1·2·3 완료 후)
  ├─ 4-A: memory_server + search_server (5/11 ~ 5/24)
  ├─ 4-B: file_server 분리 (5/25 ~ 6/01)
  ├─ 4-C: clip_server 분리 (6/02 ~ 6/08)
  └─ 4-D: agent_core 재배치 (6/09 ~ 6/30)
```

### 주차별 일정

| 기간 | 작업 | 병렬 여부 |
|------|------|---------|
| 4/19 ~ 4/23 | 작업1 (Router Interface) + 작업3-A (schema 필드 추가) | 병렬 가능 |
| 4/24 ~ 4/25 | 작업1 완료 검증 + 작업3-B (APM precision/recall 로직) | 순차 |
| 4/26 ~ 5/10 | 작업2 (Semantic Router shadow mode + utterance 설계) | 순차 (작업1 필수) |
| 5/11 ~ 5/24 | 작업4-A (memory_server + search_server) | 순차 (작업1 필수) |
| 5/25 ~ 6/01 | 작업4-B (file_server) | 순차 |
| 6/02 ~ 6/08 | 작업4-C (clip_server) + Semantic Router 100건 도달 | 병렬 가능 |
| 6/09 ~ 6/30 | 작업4-D (agent_core 재배치) + Semantic Router 전환 결정 | 순차 |

---

## 작업 1: Router Interface 추상화

### 신규 파일
`SYSTEM/onew_core/router_interface.py`

### 클래스 계층
```
BaseRouter (ABC)
  └── is_action(query: str) -> bool
  └── name() -> str

RegexIntentRouter(BaseRouter)
  └── 현행 _ACTION_RE + _PATH_RE 그대로 이전

SemanticIntentRouter(BaseRouter)      # 작업2에서 구현
  └── is_action() -> bool
  └── shadow_result(query) -> dict
```

RouteResult 도입 시점: 작업4 MCP 분할 완료 후. 지금은 bool만.

### session_manager 연동
- `query_pipeline.py` 모듈 레벨에 `_router: BaseRouter = RegexIntentRouter()` 싱글톤
- 외부에서 `query_pipeline.set_router(router)` 로 교체 가능
- session_manager.py import 경로 변경 없음 — 하위호환 완전 유지

### 성공 기준
- RegexIntentRouter.is_action(q) == 기존 is_action_command(q) 테스트셋 100건 전량 일치
- query_pipeline.py에서 is_action_command() 직접 호출 0건
- 세션 응답시간 변화 ±0.3초 이내

### 롤백 기준
- 분류 결과 기존 대비 1건이라도 다를 경우
- ImportError 발생 시
- query_pipeline.py에서 is_action_command() 직접 호출로 복원. 파일은 삭제하지 않음.

---

## 작업 2: Semantic Router shadow mode

### 패키지
`aurelio-ai/semantic-router` + gemini-embedding-001

설치 전 확인: `pip install semantic-router --dry-run` — 불필요 의존성 강제 설치 여부 확인.
충돌 시 대안: 직접 cosine similarity 구현 (~200줄 경량 버전)

### ACTION utterances (39개)

파일/쓰기 (10개):
파일 만들어줘 / 이거 파일로 저장해줘 / 메모 파일에 추가해줘 / 오늘 일기 써줘 / 내용 수정해줘 /
이 파일 고쳐줘 / 코드 작성해줘 / 설정 파일 업데이트해줘 / 새 노트 만들어줘 / 이 내용 덮어써줘

일정/캘린더 (8개):
내일 일정 추가해줘 / 캘린더에 등록해줘 / 미팅 일정 잡아줘 / 오늘 스케줄 확인해줘 /
이번 주 일정 삭제해줘 / 알람 설정해줘 / 회의 일정 변경해줘 / 할 일 목록에 추가해줘

검색/조사 (8개):
인터넷에서 찾아줘 / 웹 검색해줘 / 구글에서 조사해봐 / 최신 정보 찾아줘 /
뉴스 검색해봐 / 이거 온라인으로 찾아봐 / 요즘 이슈 검색해줘 / 공식 홈페이지 찾아줘

실행/작동 (8개):
클리핑해줘 / 퀴즈 내줘 / 문제 내줘 / 보고서 실행해줘 /
API 사용량 보여줘 / 상태 보고해줘 / 오늘 일기 읽어줘 / APM 리포트 돌려줘

경계선 케이스 (5개):
어제 일기 보여줘 / 그 파일 열어줘 / 이사님 연락처 저장해줘 / 오늘 먹은 거 기록해줘 / 이번 달 사용량 알려줘

### QA utterances (24개)

지식/개념 (8개):
냉동효과가 뭐야 / 과냉각이 왜 필요해 / 엔탈피 차이 설명해줘 / 압축기 원리 알려줘 /
몰리에르 선도 읽는 법 가르쳐줘 / 소방법 스프링클러 간격 규정 어떻게 돼 / 공조냉동 4대 요소가 뭐야 / COP 계산 공식이 뭐야

기억/과거 기반 (6개):
저번에 배운 냉동 사이클 뭐였어 / 양악수술 관련 메모한 거 있어 / 지난달 공부 어떻게 했어 /
내가 자주 틀리는 유형이 뭐야 / 산재 신청 절차 정리한 거 어디 있어 / 이이사 언제 만났어

분석/평가 (6개):
냉동효과와 성적계수 차이 분석해줘 / 내 공부 패턴이 어때 / 요즘 오답이 왜 많아 /
이 두 방식 비교해줘 / 최근 컨디션 어떤 것 같아 / 공조냉동 어떤 단원이 약해

대화/상태 (4개):
지금 몇 시야 / 오늘 뭐 했어 / 내 ADHD 현황 어때 / 스트릭 며칠이야

### shadow mode 구현 방식
1. 매 쿼리 → gemini-embedding-001 호출 (쿼리 임베딩)
2. utterance 벡터와 cosine 유사도 계산
3. query_log.jsonl에 shadow_router 필드 추가 기록
4. 실제 라우팅은 RegexIntentRouter 유지

utterance 임베딩: 최초 1회 계산 후 `SYSTEM/onew_core/router_utterances_cache.json` 저장.

LRU 캐시 분리 필수:
- `_embed_cached()`: 쿼리용, maxsize=128 (기존 유지)
- `_embed_utterance_cached()`: utterance용, maxsize=64 (신규 분리)
공유하면 utterance 39개가 쿼리 캐시 슬롯을 점유하므로 반드시 분리.

### 전환 기준 (100건 누적 후 `onew_apm.py --shadow-review`)

| mismatch rate | 조치 |
|--------------|------|
| < 5% | Semantic으로 전환 고려 |
| 5 ~ 15% | utterance 보완 후 재관찰 |
| > 15% | Regex 유지, utterance 전면 재설계 |

mismatch 케이스: `SYSTEM/onew_core/shadow_mismatch_log.jsonl`에 기록 → 수동 레이블링 후 원인 분석.

### 롤백 기준
- 응답시간 2초 이상 증가
- embedding 호출 횟수 예상 대비 2배 이상 (캐시 미스 폭발)
- query_log 레코드 1건이 500자 초과

---

## 작업 3: APM precision/recall 추가

### query_log.jsonl 스키마 변경

현재 (6필드):
```json
{"date":"...","q":"...","summary":"...","reused":false,"elapsed":3.2,"profile_len":4200}
```

변경 후 (9필드, 하위호환 유지):
```json
{
  "date": "2026-04-19",
  "q": "질문",
  "summary": "...",
  "reused": false,
  "elapsed": 3.2,
  "profile_len": 4200,
  "routed_as": "ACTION",
  "tool_error": false,
  "shadow_router": {"semantic_is_action": true, "confidence": 0.91}
}
```

| 필드 | 기본값 | 설명 |
|------|-------|------|
| `routed_as` | `"QA"` | 실제 라우팅 결과 |
| `tool_error` | `false` | 도구 실행 중 오류 여부 |
| `shadow_router` | `null` | 작업2 이전에는 null |

하위호환: APM 코드 전체 `.get("tool_error", False)`, `.get("routed_as", "QA")` 필수 사용.

### 기록 위치
- `routed_as`: query_pipeline.handle_query() 반환 직전
- `tool_error`: session_manager.agent.run() try/except 블록

### APM 진단 규칙 추가 (5개 → 8개)
- 규칙 6: action_error_rate > 0.20 → "도구 오류 빈발 — ACTION 라우팅 또는 MCP 서버 점검"
- 규칙 7: action_error_rate > 0.40 → "심각한 도구 오류 — 롤백 고려"
- 규칙 8 (shadow mode 한정): avg(confidence) < 0.60 → "utterance 추가 필요"

---

## 작업 4: MCP 분할

### 5개 서버 구조

| 서버 | 파일 | 주요 도구 |
|------|------|---------|
| memory_server | mcp_servers/memory_server.py | read_memory, write_memory, append_query_log, read_query_log |
| search_server | mcp_servers/search_server.py | search_vault, reuse_query, embed |
| file_server | mcp_servers/file_server.py | read_file, write_file, edit_file, list_files |
| clip_server | mcp_servers/clip_server.py | clip_url, clip_text, list_clips |
| 기존 유지 | study_server, system_server, skills_server | 변경 없음 |

### 공유 상태 처리

| 공유 자원 | 처리 방법 |
|-----------|---------|
| query_log.jsonl | memory_server 독점 쓰기, 타 서버는 경유 |
| LanceDB | search_server 독점 접근 (vault_server에서 완전 제거) |
| onew_locks.py | 각 서버 직접 import 가능 (독립 subprocess) |
| GEMINI_API_KEY | 각 서버 os.environ.get() 독립 참조 |

### LanceDB deadlock 방지 (search_server 필수 패턴)
```python
# search_server.py 모듈 최상단 (FastMCP 루프 시작 전)
try:
    import lancedb as _lancedb_preload
    _db_conn = _lancedb_preload.connect(LANCE_DB_DIR)
    _chunks_table = _db_conn.open_table("chunks")
except Exception:
    _lancedb_preload = None
    _chunks_table = None
```

### Single-Shot 경로와의 공존
- query_pipeline.py의 search_direct() — Single-Shot 경로 전용, 삭제 금지
- search_server.search_vault() — agent.run() (ACTION) 경로 전용
- 의도된 이원화, 충돌 아님

query_pipeline.py 상단 주석 추가 필수:
```python
# search_direct() — Single-Shot 경로 전용 (MCP search_server와 중복 아님)
# MCP 분할 후에도 이 함수는 유지되어야 함
```

### 작업4-D 시작 전 필수
obsidian_agent.py + onew_core/ 전체를 Onew_Core_Backup_절대건드리지말것/ 에 백업.

### 성공 기준

| 단계 | 기준 |
|------|------|
| 4-A | memory_server + search_server 독립 기동, agent.run() 정상 |
| 4-B | vault_server에서 파일 I/O 도구 제거 후 동작 동일 |
| 4-C | 클리핑 명령 정상 처리 |
| 4-D | MCP 서버 8개 전부 연결, Single-Shot 경로 비율 65% 이상 유지 |

---

## 충돌 분석

### 충돌 1: Router Interface ↔ MCP 분할
router_interface.py는 onew_core/ 안에 그대로 유지.
작업4-D는 "이동"이 아닌 "정리" — 위치 변경 없음.
작업4-D 시작 전: grep -r "from onew_core.router_interface" SYSTEM/ 으로 의존성 맵 확인.

### 충돌 2: Semantic Router ↔ LRU 캐시 경합
_embed_cached()(쿼리용)와 _embed_utterance_cached()(utterance용) 분리 필수.

### 충돌 3: LanceDB 동시 접근 (분할 중간 단계)
vault_server + search_server 동시 LanceDB 접근 기간 최대 1일 이내.
해당 기간 write 금지. 완료 후 vault_server에서 lancedb 코드 완전 제거.

### 충돌 4: query_log 스키마 ↔ APM 하위호환
모든 APM 코드 .get() 기본값 처리 필수. 기존 레코드 수정 불필요.

### 충돌 5: Single-Shot ↔ MCP 분할 후 search 이원화
의도된 설계. search_direct() 삭제 금지. query_pipeline.py 상단 주석으로 명문화.

---

## 절대 금지 신호 (전체 공통)

- Precision 2% 이상 급락
- action_error_rate 급증
- "왜 이렇게 라우팅됐지?" 디버깅이 반복됨
- APM slow_request 비율 전주 대비 10%p 이상 증가

→ 즉시 해당 단계 롤백.

---

## 핵심 파일 참조

- SYSTEM/onew_core/router_interface.py — 신규 (작업1 핵심, 모든 후속 작업 의존)
- SYSTEM/onew_core/query_pipeline.py — 작업1·2·3 수정 대상
- SYSTEM/onew_core/session_manager.py — 작업3 tool_error 기록 위치
- SYSTEM/onew_apm.py — 작업3 APM 확장
- SYSTEM/mcp_servers/vault_server.py — 작업4 레퍼런스 (lancedb preload 패턴)
