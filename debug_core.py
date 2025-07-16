#!/usr/bin/env python3
"""
지능형 디버깅 시스템의 핵심 로직
"""
import json
import logging
import os
import re
from collections import defaultdict, Counter
from datetime import datetime
from typing import Dict, List


class IntelligentDebuggerCore:
    """
    에러 패턴과 해결책을 외부 JSON 파일에서 로드하여
    에러를 분석하는 핵심 디버깅 클래스.
    """

    PATTERN_FILE = "error_patterns.json"
    SOLUTION_FILE = "solutions.json"

    def __init__(self, pattern_path: str = None, solution_path: str = None):
        self.pattern_file = pattern_path or self.PATTERN_FILE
        self.solution_file = solution_path or self.SOLUTION_FILE

        self.error_patterns = self._load_json(self.pattern_file)
        self.solutions = self._load_json(self.solution_file)

        if not self.error_patterns or not self.solutions:
            logging.error("디버거 초기화 실패: 패턴 또는 해결책 파일을 로드할 수 없습니다.")
            # Fallback to empty dicts to prevent crashes
            self.error_patterns = self.error_patterns or {}
            self.solutions = self.solutions or {}

        self.debug_history = []
        self.performance_metrics = defaultdict(list)

    def _load_json(self, file_path: str) -> Dict:
        """JSON 파일을 안전하게 로드합니다."""
        if not os.path.exists(file_path):
            logging.error(f"파일을 찾을 수 없습니다: {file_path}")
            return {}
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError as e:
            logging.error(f"JSON 파싱 오류 {file_path}: {e}")
            return {}
        except Exception as e:
            logging.error(f"파일 읽기 오류 {file_path}: {e}")
            return {}

    def analyze_error(self, error_text: str) -> Dict:
        """에러 분석 및 해결책 제시"""
        analysis = {
            "error_type": "unknown",
            "severity": "medium",
            "solutions": [],
            "patterns_found": [],
            "timestamp": datetime.now().isoformat(),
        }

        # 패턴 매칭
        for error_type, pattern in self.error_patterns.items():
            if re.search(pattern, error_text, re.IGNORECASE):
                analysis["error_type"] = error_type
                analysis["patterns_found"].append(pattern)
                analysis["solutions"] = self.solutions.get(error_type, [])
                break

        # 심각도 판단
        if "critical" in error_text.lower() or "fatal" in error_text.lower():
            analysis["severity"] = "critical"
        elif "warning" in error_text.lower():
            analysis["severity"] = "low"

        self.debug_history.append(analysis)
        return analysis

    def generate_debug_report(self) -> str:
        """디버그 리포트 생성"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "debug_sessions": len(self.debug_history),
            "common_errors": dict(
                Counter(
                    d["error_type"] for d in self.debug_history if d["error_type"] != "unknown"
                )
            ),
            "performance_summary": dict(self.performance_metrics),
        }

        return json.dumps(report, indent=2, ensure_ascii=False)
