# [OPTIONAL SKILL] Git Workflow Patterns

keywords: git commit branch conventional workflow rebase stash cherry-pick squash amend merge pull-request

## 커밋 메시지 규칙 — Conventional Commits
형식: `<type>(<scope>): <요약>`

```
feat(auth): 소셜 로그인 추가
fix(session): 세션 타임아웃 버그 수정
refactor(agent): MCP 연결 로직 분리
docs(readme): 설치 가이드 업데이트
chore(deps): requirements.txt 업데이트
```

conventional commit type 목록:
- `feat`     — 새 기능
- `fix`      — 버그 수정
- `refactor` — 기능 변경 없는 개선
- `docs`     — 문서만 변경
- `chore`    — 빌드/설정 변경
- `test`     — 테스트만 추가/수정

## 브랜치 전략 (Branch Strategy)
```
main           ← 배포 가능 상태 (branch 보호 필수)
  └─ develop   ← 통합 branch
       ├─ feature/login     ← 기능 개발 branch
       ├─ feature/mcp-skill ← 기능 개발 branch
       └─ hotfix/critical-bug ← 긴급 수정 branch
```

branch 명명: `feature/기능명`, `fix/버그명`, `hotfix/긴급명`

## 유용한 명령어
```bash
# branch 생성 + 이동
git checkout -b feature/new-skill

# 직전 commit 수정 (push 전에만) — amend
git commit --amend --no-edit

# 특정 commit만 가져오기 — cherry-pick
git cherry-pick <commit-hash>

# branch 병합 이력 정리 — squash
git merge --squash feature/xxx

# 변경 임시 저장 — stash
git stash push -m "작업 내용 설명"
git stash pop

# branch 이력 재정렬 — rebase
git rebase develop

# 파일별 변경 이력
git log --follow -p -- 파일경로

# 원격 branch 동기화
git fetch --prune
```

## rebase vs merge
| 상황 | 권장 |
|------|------|
| feature branch → develop | rebase (이력 선형화) |
| hotfix → main | merge (이력 보존) |
| 공개 branch | merge만 (rebase 금지) |

## PR 체크리스트 (Pull Request)
- [ ] 단일 목적 (한 PR = 한 이슈)
- [ ] conventional commit 메시지 준수
- [ ] 자기 리뷰 완료 (→ `dev_code_review` 스킬 참조)
- [ ] 테스트 추가/업데이트
- [ ] 시크릿 하드코딩 없음
- [ ] CHANGELOG 업데이트 (배포 관련 시)
