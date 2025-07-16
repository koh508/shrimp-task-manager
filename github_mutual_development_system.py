#!/usr/bin/env python3
"""
GitHub 기반 개인-에이전트 상호 발전 시스템
"""
import asyncio
import json
import logging
import os
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from github import Github

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class LearningGoal:
    id: str
    title: str
    description: str
    category: str
    priority: str
    target_date: datetime
    current_progress: float
    github_issue_number: Optional[int] = None
    skills_gained: List[str] = None
    agent_impact: str = ""


@dataclass
class AgentEvolution:
    generation: int
    timestamp: datetime
    capabilities_added: List[str]
    performance_improvements: Dict[str, float]
    learning_source: str
    github_branch: str
    commit_hash: str


class GitHubIntegrationManager:
    def __init__(self, token: str, repo_name: str):
        self.github = Github(token)
        self.repo = self.github.get_repo(repo_name)
        self.token = token
        self.repo_name = repo_name

    def create_learning_goal_issue(self, goal: LearningGoal):
        try:
            issue_body = f"""
## 📚 학습 목표

**설명**: {goal.description}
**카테고리**: {goal.category}
**우선순위**: {goal.priority}
**목표 날짜**: {goal.target_date.strftime('%Y-%m-%d')}

## 🎯 진행 상황
- [ ] 계획 수립
- [ ] 자료 수집
- [ ] 학습 시작
- [ ] 실습 진행
- [ ] 프로젝트 적용
- [ ] 완료 및 정리

## 🤖 AI 에이전트 연동
**예상 에이전트 영향**: {goal.agent_impact}

## 📊 성과 지표
- 진행률: {goal.current_progress * 100:.1f}%
- 습득 기술: {', '.join(goal.skills_gained or [])}

---
*이 이슈는 GitHub 통합 발전 시스템에 의해 자동 생성되었습니다.*
"""
            issue = self.repo.create_issue(
                title=f"[학습목표] {goal.title}",
                body=issue_body,
                labels=["학습목표", goal.category, goal.priority],
            )
            goal.github_issue_number = issue.number
            logger.info(f"학습 목표 이슈 생성: #{issue.number}")
            return issue
        except Exception as e:
            logger.error(f"이슈 생성 실패: {e}")
            return None

    def update_learning_progress(self, goal: LearningGoal, progress_note: str):
        try:
            if not goal.github_issue_number:
                return
            issue = self.repo.get_issue(goal.github_issue_number)
            comment_body = f"""
## 📈 진행 상황 업데이트

**날짜**: {datetime.now().strftime('%Y-%m-%d %H:%M')}
**진행률**: {goal.current_progress * 100:.1f}%

**내용**:
{progress_note}

**새로 습득한 기술**:
{', '.join(goal.skills_gained or [])}
"""
            issue.create_comment(comment_body)
            if goal.current_progress >= 1.0:
                issue.edit(state="closed")
        except Exception as e:
            logger.error(f"진행 상황 업데이트 실패: {e}")


class PersonalGrowthTracker:
    def __init__(self, github_manager: GitHubIntegrationManager):
        self.github_manager = github_manager
        self.learning_goals: List[LearningGoal] = []

    def set_learning_goal(
        self,
        title: str,
        description: str,
        category: str,
        priority: str,
        days_to_complete: int = 30,
        agent_impact: str = "",
    ) -> LearningGoal:
        goal = LearningGoal(
            id=f"goal_{len(self.learning_goals) + 1}",
            title=title,
            description=description,
            category=category,
            priority=priority,
            target_date=datetime.now() + timedelta(days=days_to_complete),
            current_progress=0.0,
            skills_gained=[],
            agent_impact=agent_impact,
        )
        self.github_manager.create_learning_goal_issue(goal)
        self.learning_goals.append(goal)
        logger.info(f"새로운 학습 목표 설정: {title}")
        return goal

    def update_learning_progress(
        self, goal_id: str, progress: float, skills_gained: List[str], note: str = ""
    ):
        goal = next((g for g in self.learning_goals if g.id == goal_id), None)
        if not goal:
            logger.error(f"학습 목표를 찾을 수 없습니다: {goal_id}")
            return
        goal.current_progress = progress
        goal.skills_gained = skills_gained
        self.github_manager.update_learning_progress(goal, note)
        logger.info(f"학습 진행 상황 업데이트: {goal.title} ({progress*100:.1f}%)")


class MutualDevelopmentSystem:
    def __init__(self, github_token: str, repo_name: str):
        self.github_manager = GitHubIntegrationManager(github_token, repo_name)
        self.growth_tracker = PersonalGrowthTracker(self.github_manager)

    async def run_daily_sync(self):
        logger.info("일일 동기화 시작")
        self.github_manager.update_learning_progress
        logger.info("일일 동기화 완료")

    def create_sample_learning_goals(self):
        sample_goals = [
            {
                "title": "Python 비동기 프로그래밍 마스터",
                "description": "asyncio, aiohttp 등을 활용한 비동기 프로그래밍 완전 정복",
                "category": "technical",
                "priority": "high",
                "days_to_complete": 21,
                "agent_impact": "에이전트의 동시 처리 능력 향상, 네트워크 요청 최적화",
            },
            {
                "title": "GitHub Actions CI/CD 구축",
                "description": "자동 테스트, 배포 파이프라인 구축으로 개발 워크플로우 개선",
                "category": "technical",
                "priority": "medium",
                "days_to_complete": 14,
                "agent_impact": "에이전트 코드 품질 자동 검증, 배포 자동화",
            },
            {
                "title": "효율적인 학습 방법론 연구",
                "description": "스페이스 리피티션, 포모도로 등 과학적 학습 방법 적용",
                "category": "personal",
                "priority": "medium",
                "days_to_complete": 30,
                "agent_impact": "에이전트의 학습 알고리즘 개선, 개인화 학습 패턴 인식",
            },
        ]
        for goal_data in sample_goals:
            self.growth_tracker.set_learning_goal(**goal_data)
        logger.info(f"{len(sample_goals)}개의 샘플 학습 목표 생성 완료")


# 실행 예시
def main():
    GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "your_github_token_here")
    REPO_NAME = os.environ.get("REPO_NAME", "your_username/your_repo")
    system = MutualDevelopmentSystem(GITHUB_TOKEN, REPO_NAME)
    # 샘플 학습 목표 생성 (처음 실행 시에만)
    # system.create_sample_learning_goals()
    print("GitHub 기반 상호 발전 시스템이 준비되었습니다.")


if __name__ == "__main__":
    main()
