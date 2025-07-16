#!/usr/bin/env python3
"""
코딩 도구 통합 시스템
"""
import subprocess
import ast
import os
from typing import Dict, List, Any
import json
from datetime import datetime


class CodingToolsIntegration:
    """코딩 도구 통합 매니저"""

    def __init__(self):
        self.tools = {
            "linting": ["flake8", "pylint", "mypy"],
            "formatting": ["black", "autopep8"],
            "testing": ["pytest", "coverage"],
            "security": ["bandit", "safety"],
            "complexity": ["radon", "mccabe"],
        }
        self.install_missing_tools()

    def install_missing_tools(self):
        """필요한 도구 자동 설치"""
        required_tools = ["flake8", "black", "pytest", "coverage", "bandit", "flake8-json"]

        for tool in required_tools:
            try:
                # Use python -m to check for module existence
                subprocess.run(
                    ["python", "-m", tool, "--version"], capture_output=True, check=True, text=True
                )
                print(f"✅ {tool} 설치됨")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print(f"📦 {tool} 설치 중...")
                subprocess.run(["pip", "install", tool], capture_output=True)

    def run_linting(self, file_path: str) -> Dict[str, Any]:
        """코드 린팅 실행"""
        results = {}

        # Flake8 실행
        try:
            result = subprocess.run(
                ["python", "-m", "flake8", file_path, "--format=json"],
                capture_output=True,
                text=True,
            )
            results["flake8"] = {
                "success": result.returncode == 0,
                "output": json.loads(result.stdout) if result.stdout else {},
                "errors": result.stderr,
            }
        except Exception as e:
            results["flake8"] = {"success": False, "error": str(e)}

        return results

    def run_formatting(self, file_path: str) -> Dict[str, Any]:
        """코드 포맷팅 실행"""
        results = {}

        # Black 포맷터 실행
        try:
            result = subprocess.run(
                ["python", "-m", "black", "--check", file_path], capture_output=True, text=True
            )
            results["black"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "needs_formatting": result.returncode != 0,
            }

            # 자동 포맷팅 적용
            if result.returncode != 0:
                format_result = subprocess.run(
                    ["python", "-m", "black", file_path], capture_output=True, text=True
                )
                results["black"]["formatted"] = format_result.returncode == 0

        except Exception as e:
            results["black"] = {"success": False, "error": str(e)}

        return results

    def run_testing(self, test_path: str = "tests/") -> Dict[str, Any]:
        """테스트 실행"""
        results = {}

        # pytest 실행
        try:
            result = subprocess.run(
                ["python", "-m", "pytest", test_path, "-v", "--tb=short"],
                capture_output=True,
                text=True,
            )
            results["pytest"] = {
                "success": result.returncode == 0,
                "output": result.stdout,
                "errors": result.stderr,
            }
        except Exception as e:
            results["pytest"] = {"success": False, "error": str(e)}

        # Coverage 실행
        try:
            result = subprocess.run(
                ["python", "-m", "coverage", "run", "-m", "pytest", test_path],
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                coverage_result = subprocess.run(
                    ["python", "-m", "coverage", "report", "--format=json"],
                    capture_output=True,
                    text=True,
                )
                results["coverage"] = {
                    "success": True,
                    "report": json.loads(coverage_result.stdout) if coverage_result.stdout else {},
                }
            else:
                results["coverage"] = {"success": False, "error": result.stderr}

        except Exception as e:
            results["coverage"] = {"success": False, "error": str(e)}

        return results

    def run_security_scan(self, path: str) -> Dict[str, Any]:
        """보안 스캔 실행"""
        results = {}

        # Bandit 보안 스캔
        try:
            result = subprocess.run(
                ["python", "-m", "bandit", "-r", path, "-f", "json"],
                capture_output=True,
                text=True,
            )
            results["bandit"] = {
                "success": result.returncode == 0,
                "output": json.loads(result.stdout) if result.stdout else {},
                "errors": result.stderr,
            }
        except Exception as e:
            results["bandit"] = {"success": False, "error": str(e)}

        return results

    def analyze_complexity(self, file_path: str) -> Dict[str, Any]:
        """코드 복잡도 분석"""
        results = {}

        try:
            # 기본 복잡도 분석
            with open(file_path, "r", encoding="utf-8") as f:
                code = f.read()

            tree = ast.parse(code)

            # 함수 수 계산
            functions = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            classes = [node for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]

            results["basic_analysis"] = {
                "functions": len(functions),
                "classes": len(classes),
                "lines": len(code.splitlines()),
                "complexity_score": len(functions) + len(classes) * 2,
            }

        except Exception as e:
            results["basic_analysis"] = {"success": False, "error": str(e)}

        return results

    def generate_report(self, file_path: str) -> Dict[str, Any]:
        """종합 코드 품질 리포트 생성"""
        report = {"timestamp": datetime.now().isoformat(), "file_path": file_path, "results": {}}

        # 모든 분석 실행
        report["results"]["linting"] = self.run_linting(file_path)
        report["results"]["formatting"] = self.run_formatting(file_path)
        report["results"]["security"] = self.run_security_scan(file_path)
        report["results"]["complexity"] = self.analyze_complexity(file_path)

        # 전체 점수 계산
        score = self.calculate_overall_score(report["results"])
        report["overall_score"] = score

        return report

    def calculate_overall_score(self, results: Dict[str, Any]) -> int:
        """전체 품질 점수 계산"""
        score = 100

        # 린팅 오류 차감
        if "linting" in results and not results["linting"].get("flake8", {}).get("success", True):
            score -= 20

        # 포맷팅 이슈 차감
        if "formatting" in results and results["formatting"].get("black", {}).get(
            "needs_formatting", False
        ):
            score -= 10

        # 보안 이슈 차감
        if "security" in results and not results["security"].get("bandit", {}).get(
            "success", True
        ):
            score -= 30

        # 복잡도 차감
        complexity = (
            results.get("complexity", {}).get("basic_analysis", {}).get("complexity_score", 0)
        )
        if complexity > 50:
            score -= 20

        return max(0, score)
