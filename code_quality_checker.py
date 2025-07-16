#!/usr/bin/env python3
"""
자동 코드 품질 검사 시스템
flake8, radon, bandit을 사용하여 코드 품질을 분석합니다.
"""
import subprocess
import json
import pathlib
import logging


class CodeQualityChecker:
    """외부 도구를 사용하여 코드 품질을 검사하는 클래스"""

    def __init__(self, target: str = "."):
        self.target = pathlib.Path(target)
        if not self.target.exists():
            raise FileNotFoundError(f"타겟 경로를 찾을 수 없습니다: {self.target}")

    def _run_tool(self, command: list) -> dict:
        """품질 검사 도구를 실행하고 결과를 JSON으로 파싱합니다."""
        try:
            result = subprocess.run(
                command, capture_output=True, text=True, check=False, encoding="utf-8"
            )
            # Bandit can return non-zero exit code even with results, so we don't use check=True
            if result.returncode != 0 and not result.stdout:
                logging.error(f"도구 실행 오류 '{command[0]}': {result.stderr}")
                return {"error": result.stderr.strip()}

            # radon cc -j returns empty stdout on success with no issues
            if not result.stdout.strip():
                return {}

            return json.loads(result.stdout)

        except FileNotFoundError:
            msg = f"'{command[0]}'를 찾을 수 없습니다. 설치되었는지 확인하세요."
            logging.error(msg)
            return {"error": msg}
        except json.JSONDecodeError as e:
            msg = f"'{command[0]}'의 출력(JSON)을 파싱하는 데 실패했습니다: {e}"
            logging.error(msg)
            return {"error": msg, "output": result.stdout}
        except Exception as e:
            logging.error(f"알 수 없는 오류 발생: {e}")
            return {"error": str(e)}

    def run_flake8(self) -> dict:
        """flake8을 실행하여 PEP8 준수 여부를 검사합니다."""
        logging.info("Executing flake8...")
        command = [
            "python",
            "-m",
            "flake8",
            str(self.target),
            "--format=json",
            "--exclude=.git,__pycache__,.venv,node_modules,logs",
        ]
        result = self._run_tool(command)
        logging.info("flake8 check finished.")
        return result

    def run_radon(self) -> dict:
        """radon을 실행하여 순환 복잡도를 검사합니다."""
        logging.info("Executing radon...")
        command = [
            "python",
            "-m",
            "radon",
            "cc",
            "-s",
            "-j",
            str(self.target),
            "-e",
            "*.venv/*,*.git/*,*/__pycache__/*",
        ]
        result = self._run_tool(command)
        logging.info("radon check finished.")
        return result

    def run_bandit(self) -> dict:
        """bandit을 실행하여 보안 취약점을 검사합니다."""
        logging.info("Executing bandit...")
        command = [
            "python",
            "-m",
            "bandit",
            "-r",
            str(self.target),
            "-f",
            "json",
            "-x",
            ".git,__pycache__,.venv,node_modules,logs",
        ]
        result = self._run_tool(command)
        logging.info("bandit check finished.")
        return result

    def summary(self) -> dict:
        """모든 품질 검사를 실행하고 결과를 요약합니다."""
        logging.info(f"'{self.target}'에 대한 코드 품질 검사를 시작합니다...")
        return {
            "flake8": self.run_flake8(),
            "radon": self.run_radon(),
            "bandit": self.run_bandit(),
        }
