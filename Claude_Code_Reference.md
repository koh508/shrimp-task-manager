---
tags:
  - Claude_Code
  - 참조문서
상태: 유지관리중
날짜: 2026-03-15
관리: Claude Code가 직접 작성/업데이트
---

# Claude Code 공식 기능 참조문서

> ⚠️ 이 문서에 없는 기능/명령어는 존재하지 않을 수 있음.
> 불확실하면 "Claude Code에게 직접 물어보세요"로 답변 종료.

---

## 1. 슬래시 명령어 (Slash Commands)

| 명령어 | 설명 |
|--------|------|
| `/help` | 사용 가능한 명령어 목록 표시 |
| `/compact` | 대화 컨텍스트 압축 (플래그 없음) |
| `/clear` | 대화 내용 초기화 |
| `/cost` | 현재 세션 토큰 사용량 및 비용 표시 |
| `/model` | 사용 모델 변경 |
| `/exit` / `/quit` | Claude Code 종료 |
| `/review` | 변경 사항 검토 |
| `/commit` | git 커밋 생성 (스킬) |

> ❌ 존재하지 않는 것: `/compact --by-module`, `/compact --incremental`, `/compact --max-tokens`

---

## 2. 설정 파일

| 파일 | 위치 | 용도 |
|------|------|------|
| `CLAUDE.md` | 프로젝트 루트 또는 `~/.claude/` | Claude에게 프로젝트 지침 제공 |
| `.claudeignore` | 프로젝트 루트 | 스캔 제외 파일/폴더 지정 (gitignore 문법) |
| `settings.json` | `~/.claude/` | 전역 설정 |

---

## 3. 컨텍스트 관리

- 컨텍스트가 일정 용량 초과 시 **자동 압축** 발생
- 수동 압축: `/compact` (옵션 없음)
- 컨텍스트 완전 초기화: `/clear`

---

## 4. 실행 모드

| 모드 | 방법 |
|------|------|
| 대화형 (기본) | `claude` |
| 비대화형 (스크립트용) | `claude --print "질문"` |
| 권한 자동승인 | `claude --dangerously-skip-permissions` |

---

## 5. Hooks

파일: `~/.claude/settings.json`
- 도구 실행 전/후에 셸 명령어를 자동 실행하는 기능
- 예: 파일 저장 후 자동 포맷팅, 커밋 전 린트 실행

---

## 6. MCP (Model Context Protocol)

- 외부 도구/서버를 Claude Code에 연결하는 프로토콜
- 설정: `~/.claude/settings.json`의 `mcpServers` 항목

---

## 7. 주요 단축키

| 단축키 | 동작 |
|--------|------|
| `Ctrl+C` | 현재 작업 중단 |
| `Ctrl+L` | 화면 지우기 |
| 위/아래 방향키 | 이전 입력 탐색 |

---

## 업데이트 이력
- 2026-03-15: 최초 작성 (Claude Code 직접 작성)
