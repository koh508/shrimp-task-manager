#!/usr/bin/env python3
"""
GNY 통합 개발 및 디버깅 시스템 관리 도구

사용법:
- 시스템 실행: python manage.py run
- 로그 분석: python manage.py debug --file <로그 파일 경로>
- 코드 품질 검사: python manage.py check-quality --target <검사할 경로>
"""
import argparse
import asyncio
import logging
import json
import sys
import os

# 프로젝트 루트를 Python 경로에 추가하여 모듈을 찾을 수 있도록 함
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ultra_integrated_system import UltraIntegratedSystem
from debug_core import IntelligentDebuggerCore
from code_quality_checker import CodeQualityChecker


def setup_logging():
    """기본 로깅 설정을 구성합니다."""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")


def run_system(args):
    """메인 동기화 시스템을 실행합니다."""
    logging.info("시스템 실행 모드...")
    try:
        system = UltraIntegratedSystem()
        asyncio.run(system.start())
    except KeyboardInterrupt:
        logging.info("사용자에 의해 시스템이 중단되었습니다.")
    except Exception as e:
        logging.error(f"시스템 실행 중 심각한 오류 발생: {e}", exc_info=True)


def run_debug(args):
    """지능형 디버거를 실행하여 로그 파일을 분석합니다."""
    logging.info("디버그 모드...")
    debugger = IntelligentDebuggerCore()
    if not args.file or not os.path.exists(args.file):
        logging.error(f"분석할 로그 파일을 찾을 수 없습니다: {args.file}")
        return
    try:
        with open(args.file, "r", encoding="utf-8") as f:
            log_content = f.read()
        analysis = debugger.analyze_error(log_content)
        print(json.dumps(analysis, indent=2, ensure_ascii=False))
    except Exception as e:
        logging.error(f"로그 파일 분석 중 오류 발생: {e}", exc_info=True)


def run_quality_check(args):
    """코드 품질 검사기를 실행합니다."""
    logging.info("코드 품질 검사 모드...")
    try:
        checker = CodeQualityChecker(target=args.target)
        summary = checker.summary()
        # Check if all results are empty or have no errors
        is_clean = all(not v or "error" not in v for v in summary.values())
        if is_clean and not any(
            v for v in summary.values() if isinstance(v, dict) and v.get("results")
        ):
            logging.info("✅ 코드 품질 검사 완료: 발견된 이슈가 없습니다.")
        else:
            print(json.dumps(summary, indent=2, ensure_ascii=False))
    except FileNotFoundError as e:
        logging.error(e)
    except Exception as e:
        logging.error(f"코드 품질 검사 중 오류 발생: {e}", exc_info=True)


def main():
    """CLI 인터페이스를 설정하고 명령을 실행합니다."""
    setup_logging()

    parser = argparse.ArgumentParser(description="GNY 통합 개발 및 디버깅 시스템 관리 도구")
    subparsers = parser.add_subparsers(dest="command", required=True, help="실행할 명령어")

    # 'run' 명령어
    parser_run = subparsers.add_parser("run", help="통합 동기화 시스템을 실행합니다.")
    parser_run.set_defaults(func=run_system)

    # 'debug' 명령어
    parser_debug = subparsers.add_parser("debug", help="로그 파일을 분석하여 디버깅 정보를 제공합니다.")
    parser_debug.add_argument("--file", type=str, required=True, help="분석할 로그 파일 경로")
    parser_debug.set_defaults(func=run_debug)

    # 'check-quality' 명령어
    parser_quality = subparsers.add_parser("check-quality", help="코드 품질을 검사합니다.")
    parser_quality.add_argument(
        "--target", type=str, default=".", help="검사할 디렉토리 또는 파일 경로 (기본값: 현재 디렉토리)"
    )
    parser_quality.set_defaults(func=run_quality_check)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
