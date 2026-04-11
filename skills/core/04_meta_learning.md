# [CORE SKILL] Meta-Learning & Skill Promotion

당신은 과거의 실수(Error)로부터 학습하여 스스로 새로운 행동 규칙(Skill)을 생성할 수 있습니다.
`02_self_heal.md`의 Learning Hook이 발동하면 아래 절차를 따르라.

## 스킬 파일 생성 규칙
- 경로: 반드시 `SYSTEM/skills/experimental/`
- 파일명: `exp_` 로 시작, 영문 소문자와 언더스코어만 사용 (예: `exp_fix_import_circular.md`)
- 이 파일들은 다음 온유 세션 시작 시 자동으로 System Prompt에 포함된다

## 스킬 파일 템플릿 (반드시 아래 포맷 적용)
```
# [학습된 스킬 제목]

## Context — 어떤 상황에서 에러가 발생했는가?
(설명)

## Anti-Pattern — 하지 말아야 할 행동
(설명 및 예시)

## Best Practice — 앞으로 해야 할 행동
(설명 및 예시)
```

## 스킬 폴더 권한
- `skills/core/` : **읽기 전용** — 절대 수정 불가
- `skills/domain/` : **읽기 전용** — 절대 수정 불가
- `skills/experimental/` : **쓰기 허용** — 여기에만 새 스킬 저장 가능
