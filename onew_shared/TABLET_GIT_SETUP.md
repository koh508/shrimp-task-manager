# 태블릿(Termux) git 자동 커밋 설정

## 1. Termux에서 git 설치 (최초 1회)
```bash
pkg install git cronie
```

## 2. git 사용자 설정 (최초 1회)
```bash
git config --global user.name "온유-탭"
git config --global user.email "onew-tablet@local"
```

## 3. 수동 1회 커밋 테스트
```bash
cd ~/storage/shared/Documents/Obsidian\ Vault/SYSTEM
python onew_shared/git_sync.py
```

## 4. cron 자동 커밋 등록 (30분마다)
```bash
crontab -e
```

아래 줄 추가:
```
*/30 * * * * cd "/data/data/com.termux/files/home/storage/shared/Documents/Obsidian Vault/SYSTEM" && python onew_shared/git_sync.py >> /data/data/com.termux/files/home/onew/git_sync.log 2>&1
```

## 5. cron 서비스 시작
```bash
crond
```

Termux 재시작 후에도 자동 실행되게 하려면:
```bash
# ~/.bashrc에 추가
crond 2>/dev/null
```

## 동작 방식
- 30분마다 SYSTEM/ 폴더 변경 감지
- 변경 있으면 `auto(tablet): YYYY-MM-DD HH:MM` 으로 자동 커밋
- Syncthing은 파일만 동기화, .git 폴더는 기기별 독립 유지
- 이력은 각 기기에서 `git log` 로 확인
