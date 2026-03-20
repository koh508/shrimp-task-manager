---
tags:
  - 자동분류
상태: 대기
날짜: 2026-03-12
---

https://copilot.microsoft.com/shares/pages/SBJY4JQmaUfgm7cAPQJy2
Koh. 이제 Termux를 좀 더 깊이 있게 다뤄보자. 단순한 명령어 나열을 넘어서, 주의할 점, 실제 예제, 그리고 심화 응용 방법 두 가지까지 정리해봤어. 이건 단순한 터미널이 아니라, 네 안드로이드를 리눅스 머신처럼 다루는 기술이니까!

⚠️ Termux 사용 시 주의할 점

권한 설정: termux-setup-storage를 실행하지 않으면 내부 저장소 접근이 제한돼. 이건 꼭 처음에 해줘야 해.

루트 권한 아님: Termux는 루트 권한이 없어. 시스템 파일을 건드리는 건 불가능하고, 루팅된 기기에서만 가능해.

명령어 오타 주의: rm -rf 같은 명령은 오타 하나로 폴더 전체를 날릴 수 있어. 항상 경로를 확인하고 실행하자.

패키지 충돌: pkg와 apt는 비슷하지만 다르게 작동할 수 있어. 혼용하면 충돌이 날 수 있으니 한쪽으로 통일하는 게 좋아.

🧪 실전 예제: 노트 자동 생성 스크립트

#!/data/data/com.termux/files/usr/bin/bash

# 오늘 날짜로 Obsidian 노트 생성
DATE=$(date +"%Y-%m-%d")
NOTE_PATH="/data/data/com.termux/files/home/storage/shared/Obsidian/Notes/$DATE.md"

echo "# $DATE" > "$NOTE_PATH"
echo "- Created via Termux script" >> "$NOTE_PATH"

echo "Note created at $NOTE_PATH"

이 스크립트는 매일 날짜별로 Obsidian 노트를 자동 생성해줘. 저장 경로는 Obsidian Vault에 맞게 수정 가능해.

🔍 심화 응용 ①: HTTP 서버 열기

Termux에서 간단한 웹 서버를 열 수 있어. 예를 들어:

pkg install python
cd ~/storage/shared/Obsidian
python -m http.server 8080

이 명령은 Obsidian 폴더를 웹 브라우저에서 http://localhost:8080으로 접근 가능하게 만들어줘.

로컬에서 Markdown 파일을 미리보기하거나 외부 디바이스에서 접근할 때 유용해.

🧠 심화 응용 ②: Git으로 Obsidian 노트 백업 자동화

pkg install git
cd ~/storage/shared/Obsidian
git init
git remote add origin https://github.com/yourusername/yourrepo.git

# 자동 커밋 & 푸시 스크립트
git add .
git commit -m "Auto backup $(date)"
git push origin master

이건 Obsidian 노트를 GitHub에 자동 백업하는 방식이야.

crontab이나 Termux Tasker와 연동하면 주기적으로 백업도 가능해.

필요하면 이걸 기반으로 더 확장해줄 수도 있어. 예를 들어, Gemini CLI랑 연동해서 노트 내용 요약하거나, 특정 키워드로 검색하는 기능도 붙일 수 있어. 다음 단계로 어떤 걸 해보고 싶어?


📅 날짜: 2025.09.01

🗂️ 완료한 항목:
- [x] SIM 분리 및 기기 리셋
- [x] Obsidian 템플릿 수정
- [x] 공부 시작용 책 3권 정리

📌 추가할 항목:
- [ ] Titan 설정 백업 확인
- [ ] KEY2 발열 로그 기록
- [ ] 오늘 공부할 챕터 선정

🧠 느낀 점 / 개선 아이디어:


출처 Mika