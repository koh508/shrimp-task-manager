#!/usr/bin/env python3
"""
자체 진화 에이전트 시스템
"""
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class SelfEvolvingAgent:
    """자체 진화 에이전트 관리 및 개선 시스템"""

    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.agents_dir = self.vault_path / "agents"
        self.logs_dir = self.vault_path / "logs"
        self.evolution_history_file = self.vault_path / "evolution_history.json"

        # 디렉토리 생성
        self.agents_dir.mkdir(exist_ok=True)
        self.logs_dir.mkdir(exist_ok=True)

        # 진화 기록 로드
        self.evolution_history = self.load_evolution_history()

    def load_evolution_history(self) -> List[Dict[str, Any]]:
        """진화 기록 로드"""
        if not self.evolution_history_file.exists():
            return []

        try:
            with open(self.evolution_history_file, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.error(f"진화 기록 로드 실패: {e}")
            return []

    def save_evolution_history(self):
        """진화 기록 저장"""
        try:
            with open(self.evolution_history_file, "w", encoding="utf-8") as f:
                json.dump(self.evolution_history, f, ensure_ascii=False, indent=2)
        except IOError as e:
            logger.error(f"진화 기록 저장 실패: {e}")

    def save_generated_file(
        self, file_content: str, file_type: str, file_extension: str, clipping_id: int
    ) -> Optional[Path]:
        """생성된 파일 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            if file_type == "python_agent":
                filename = f"agent_{clipping_id}_{timestamp}{file_extension}"
                save_dir = self.agents_dir
            elif file_type == "markdown_log":
                filename = f"log_{clipping_id}_{timestamp}{file_extension}"
                save_dir = self.logs_dir
            else:
                return None

            filepath = save_dir / filename
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(file_content)

            logger.info(f"파일 저장됨: {filepath}")
            return filepath

        except IOError as e:
            logger.error(f"생성된 파일 저장 실패: {e}")
            return None

    def analyze_agent_code(self, agent_filepath: Path) -> Dict[str, Any]:
        """에이전트 코드 분석"""
        try:
            with open(agent_filepath, "r", encoding="utf-8") as f:
                code = f.read()

            analysis = {
                "filepath": str(agent_filepath),
                "line_count": len(code.splitlines()),
                "char_count": len(code),
                "function_count": len(re.findall(r"def\s+\w+", code)),
                "class_count": len(re.findall(r"class\s+\w+", code)),
                "imports": re.findall(
                    r"^import\s+([\w, ]+)|^from\s+([\w.]+)\s+import\s+([\w, ]+)",
                    code,
                    re.MULTILINE,
                ),
                "comments_count": len(re.findall(r"#.*", code)),
                "complexity_score": 0,  # 예시: 복잡도 점수
            }

            # 간단한 복잡도 계산
            analysis["complexity_score"] = (
                (analysis["function_count"] * 2)
                + (analysis["class_count"] * 3)
                + (analysis["line_count"] / 20)
            )

            return analysis

        except (IOError, FileNotFoundError) as e:
            logger.error(f"에이전트 코드 분석 실패: {e}")
            return {}

    def identify_improvements(self, analysis: Dict[str, Any]) -> List[str]:
        """개선점 식별"""
        improvements = []

        if analysis.get("complexity_score", 0) > 10:
            improvements.append("복잡도가 높습니다. 리팩토링을 고려하세요.")

        if analysis.get("function_count", 0) > 5:
            improvements.append("함수가 너무 많습니다. 클래스로 묶는 것을 고려하세요.")

        # TODO: 더 정교한 개선점 식별 로직 추가
        # 예: 비동기 처리, 에러 핸들링, 타입 힌트 등

        return improvements

    def evolve_agent(self, agent_filepath: Path):
        """에이전트 진화"""
        logger.info(f"에이전트 진화 시작: {agent_filepath}")

        analysis = self.analyze_agent_code(agent_filepath)
        if not analysis:
            return

        improvements = self.identify_improvements(analysis)

        if not improvements:
            logger.info("개선점이 발견되지 않았습니다.")
            return

        logger.info(f"개선점 발견: {', '.join(improvements)}")

        # TODO: WindSurf API를 호출하여 코드 개선
        # 이 예제에서는 개선점을 로그로만 남김

        evolution_record = {
            "timestamp": datetime.now().isoformat(),
            "agent_filepath": str(agent_filepath),
            "analysis": analysis,
            "suggested_improvements": improvements,
            "status": "pending_improvement",  # 'completed', 'failed'
        }

        self.evolution_history.append(evolution_record)
        self.save_evolution_history()

        logger.info(f"에이전트 진화 기록됨: {agent_filepath}")


def main():
    """메인 테스트 함수"""
    print("자체 진화 에이전트 시스템 테스트")
    print("=" * 50)

    # 테스트용 Vault 경로 설정
    vault_path = Path("./obsidian_vault_test")
    vault_path.mkdir(exist_ok=True)

    # 에이전트 인스턴스 생성
    evolving_agent = SelfEvolvingAgent(str(vault_path))

    # 테스트용 에이전트 파일 생성
    test_agent_code = """\
import os

class MyAgent:
    def run(self):
        print("Running agent")

def func1(): pass
def func2(): pass
def func3(): pass
def func4(): pass
def func5(): pass
def func6(): pass
"""
    agent_filepath = evolving_agent.save_generated_file(
        test_agent_code, "python_agent", ".py", 101
    )

    if agent_filepath:
        # 에이전트 분석
        analysis = evolving_agent.analyze_agent_code(agent_filepath)
        print("\n에이전트 분석 결과:")
        print(json.dumps(analysis, indent=2))

        # 에이전트 진화
        evolving_agent.evolve_agent(agent_filepath)

        # 진화 기록 확인
        print("\n진화 기록:")
        print(json.dumps(evolving_agent.load_evolution_history(), indent=2))


if __name__ == "__main__":
    main()
