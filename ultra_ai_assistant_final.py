import os
import logging
import asyncio
import shutil
import traceback
import time
from pathlib import Path
from datetime import datetime
from typing import List

try:
    from github import Github
except ImportError:
    Github = None

# 로깅 설정 (단일 호출)
def setup_logging(log_dir: Path = Path("D:/my workspace/OneDrive NEW/GNY/logs"), level: int = logging.INFO):
    logger = logging.getLogger(__name__) # Use a named logger
    if logger.hasHandlers():
        # This check is now more for preventing re-configuration in the same run
        return logger

    log_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"ultra_ai_{ts}.log"

    logger.setLevel(level)
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s - %(message)s")

    # Prevent adding handlers multiple times
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    logger.info(f"로깅 설정 완료: {log_file}")
    return logger

logger = setup_logging()

# 에러 notifier
class ErrorNotifier:
    def __init__(self, error_dir: Path):
        self.error_dir = error_dir
        self.error_dir.mkdir(exist_ok=True)

    def notify_error(self, msg: str):
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        err_file = self.error_dir / f"error_{ts}.md"
        try:
            with open(err_file, 'w', encoding='utf-8') as f:
                f.write(f"# AI Agent Error Report\n\n**Timestamp:** {datetime.now()}\n\n**Error Message:**\n```\n{msg}\n```\n\n**Traceback:**\n```\n{traceback.format_exc()}\n```")
            logger.info(f"Error noted: {err_file}")
        except Exception as e:
            logger.error(f"Failed to write error notification file: {e}")

# 목표 관리 (검색 결과 [1] 기반)
class GoalHierarchy:
    def __init__(self):
        self.long_term_goals = []
        logger.info("GoalHierarchy initialized.")

    def align_goals(self, user_input: str):
        if user_input not in self.long_term_goals:
            self.long_term_goals.append(user_input)
            logger.info(f"New long-term goal aligned: {user_input}")
        else:
            logger.warning(f"Goal already exists: {user_input}")

# GitHub 통합 (브랜치/커밋/PR)
class GitHubManager:
    def __init__(self, token, repo_name):
        self.repo = None
        if not Github:
            logger.warning("PyGithub 라이브러리가 설치되지 않았습니다. GitHub 통합 기능을 건너뜁니다.")
            return
        if not token or not repo_name or 'your_username' in repo_name:
            logger.warning("GitHub 토큰 또는 리포지토리 이름이 설정되지 않았습니다. GitHub 통합 기능을 건너뜁니다.")
            return
        try:
            self.github = Github(token)
            self.repo = self.github.get_repo(repo_name)
            logger.info(f"GitHub 리포지토리에 성공적으로 연결되었습니다: {repo_name}")
        except Exception as e:
            logger.error(f"GitHub 연결 실패: {e}")
            self.repo = None

    def create_branch(self, branch_name):
        if not self.repo:
            return
        try:
            main_branch = self.repo.get_branch("main")
            self.repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=main_branch.commit.sha)
            logger.info(f"성공적으로 브랜치를 생성했습니다: {branch_name}")
            return True
        except Exception as e: # GithubException
            if 'Reference already exists' in str(e):
                logger.warning(f"브랜치가 이미 존재합니다: {branch_name}")
                return True
            logger.error(f"브랜치 생성 실패: {e}")
            return False

    def commit_changes(self, message, files: List[Path], branch="main"):
        if not self.repo:
            return
        try:
            contents = []
            for file_path in files:
                if file_path.exists():
                    content = file_path.read_text(encoding='utf-8')
                    # This is a simplified example. Real implementation needs more robust logic 
                    # for creating/updating files, handling blobs and trees for multiple files.
                    # For a single file commit for now:
                    try:
                        # Check if file exists to update, otherwise create
                        existing_file = self.repo.get_contents(file_path.name, ref=branch)
                        self.repo.update_file(existing_file.path, message, content, existing_file.sha, branch=branch)
                        logger.info(f"파일 업데이트 및 커밋: {file_path.name} in {branch}")
                    except Exception: # GithubException - Not Found
                        self.repo.create_file(file_path.name, message, content, branch=branch)
                        logger.info(f"파일 생성 및 커밋: {file_path.name} in {branch}")
            logger.info(f"커밋 완료: {message}")
        except Exception as e:
            logger.error(f"커밋 실패: {e}")

    def create_pr(self, title, body, head_branch, base_branch="main"):
        if not self.repo:
            return
        try:
            self.repo.create_pull(title=title, body=body, head=head_branch, base=base_branch)
            logger.info(f"PR 생성 성공: '{title}' ({head_branch} -> {base_branch})")
        except Exception as e:
            logger.error(f"PR 생성 실패: {e}")

# 클리핑 에이전트 (디버깅 강화)
class StableClipAgent:
    def __init__(self, vault_root='D:/my workspace/OneDrive NEW/GNY'):
        self.vault_path = Path(vault_root)
        self.clip_dir = self.vault_path / 'Clippings'
        self.processed_dir = self.vault_path / 'Processed'
        self.error_notifier = ErrorNotifier(self.vault_path / 'AI_Agent_Error')
        
        # GitHub 설정은 사용자가 직접 교체해야 합니다.
        repo_name = "koko8829/Ultra_AI_Assistant_ver2" # <--- 실제 리포지토리 이름으로 변경하세요
        self.github_manager = GitHubManager(os.environ.get("GITH_TOKEN"), repo_name)
        
        self.goal_hierarchy = GoalHierarchy()

    async def resilient_loop(self, interval=10):
        fail_count = 0
        max_fails = 5
        while True:
            try:
                files = list(self.clip_dir.glob('*.md'))
                if not files:
                    # logger.info("감시 중... 새로운 클리핑 파일 없음.")
                    pass
                else:
                    logger.info(f"총 {len(files)}개의 클리핑 파일을 찾았습니다.")
                    processed_files = []
                    for file in files:
                        if self.wait_for_file_ready(file):
                            logger.info(f"처리 시작: {file.name}")
                            # content = file.read_text(encoding='utf-8') # 필요한 경우 내용 처리
                            shutil.move(str(file), str(self.processed_dir / file.name))
                            logger.info(f"파일 이동 완료: {file.name} -> {self.processed_dir.name}")
                            processed_files.append(self.processed_dir / file.name)
                    
                    if processed_files:
                        commit_message = f"Automated commit for {len(processed_files)} processed files"
                        self.github_manager.commit_changes(commit_message, processed_files)
                
                fail_count = 0  # 성공 시 실패 카운트 리셋
            except Exception as e:
                fail_count += 1
                logger.error(f"프로세스 루프에서 에러 발생 (시도 {fail_count}/{max_fails}): {e}")
                self.error_notifier.notify_error(f"An error occurred in the processing loop (Attempt {fail_count}).")
                if fail_count >= max_fails:
                    logger.critical(f"{max_fails}회 연속 에러 발생. 시스템을 중단합니다.")
                    break
                sleep_time = min(fail_count * 5, 60) # Exponential backoff
                logger.info(f"{sleep_time}초 후 재시도합니다.")
                await asyncio.sleep(sleep_time)
                continue

            await asyncio.sleep(interval)

    def wait_for_file_ready(self, path: Path, timeout=10):
        start_time = time.time()
        while time.time() - start_time < timeout:
            try:
                with path.open('r'):
                    return True
            except (IOError, PermissionError) as e:
                # logger.debug(f"파일이 아직 준비되지 않았습니다: {path.name}, 오류: {e}. 잠시 후 재시도합니다.")
                time.sleep(0.5)
        logger.warning(f"파일 준비 대기 시간 초과: {path.name}")
        return False

# 추가 발전: GitHub Actions YAML 예시 (자동 백업)
def generate_github_actions_yaml():
    ga_dir = Path('.github/workflows')
    ga_dir.mkdir(parents=True, exist_ok=True)
    yaml_file = ga_dir / 'ci.yml'
    
    if yaml_file.exists():
        logger.info("GitHub Actions YAML 파일이 이미 존재합니다.")
        return

    yaml_content = """
name: AI Agent CI/CD
on:
  push:
    branches:
      - main
  schedule:
    - cron: '0 0 * * *' # 매일 자정에 실행

jobs:
  backup_and_test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Run tests (if any)
        run: python -m unittest discover tests/

      - name: Backup important directories
        run: |
          # 이 부분은 실제 백업 전략에 맞게 수정해야 합니다.
          echo "Backing up data..."
          # 예: zip -r backup.zip /path/to/data
"""
    try:
        with open(yaml_file, 'w', encoding='utf-8') as f:
            f.write(yaml_content)
        logger.info(f"성공적으로 GitHub Actions YAML 파일을 생성했습니다: {yaml_file}")
    except Exception as e:
        logger.error(f"GitHub Actions YAML 파일 생성 실패: {e}")

# 메인 실행
async def main():
    logger.info("===== Ultra AI Assistant v2 시작 =====")
    # 사용자가 GITHUB_TOKEN과 리포지토리 이름을 설정했는지 확인하는 것이 중요합니다.
    # 이 예제에서는 StableClipAgent 생성자에서 확인합니다.
    
    agent = StableClipAgent()
    agent.goal_hierarchy.align_goals("System Stability and Autonomous Operation")
    
    # GitHub Actions 파일 생성 (필요 시)
    generate_github_actions_yaml()
    
    logger.info("에이전트가 클리핑 파일 감시를 시작합니다...")
    try:
        await agent.resilient_loop()
    except KeyboardInterrupt:
        logger.info("사용자에 의해 시스템이 중단되었습니다.")
    except Exception as e:
        logger.critical(f"메인 루프에서 처리되지 않은 심각한 오류 발생: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    finally:
        logger.info("===== Ultra AI Assistant v2 종료 =====")

