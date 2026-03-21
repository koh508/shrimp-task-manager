"""
온유 시스템의 전체 흐름을 통합하고 실행하는 메인 스크립트입니다.

이 스크립트는 외부 입력을 처리하고, 'onew_system_processor' 모듈을 호출하며,
최종 결과를 출력하는 역할을 합니다. 환경 변수 사용 원칙을 준수합니다.

설계 원칙 준수:
- 전역 변수 사용 금지 (모듈 상수는 대문자, 런타임 상태는 파일에 영속화)
- 순환 참조(Circular Import) 절대 금지 (의존 방향: tools → locks → core)
- 순수 함수(Pure Function) 우선 — 외부 상태 의존 없이 인수/반환값으로만 동작
- 함수 1개 = 책임 1개 (단일 책임 원칙)
- 예외는 로깅 후 상위로 전파하거나 명시적 실패값 반환
- API 키 하드코딩 금지 — 환경변수 사용
"""

import os
import argparse
import logging
import sys

# onew_system_processor 모듈 임포트
# onew_system_processor.py 파일이 이 스크립트와 동일한 디렉토리에 있거나
# PYTHONPATH에 포함되어 있어야 합니다.
try:
    import onew_system_processor
except ImportError:
    print("오류: 'onew_system_processor.py' 모듈을 찾을 수 없습니다.", file=sys.stderr)
    print("스크립트와 동일한 디렉토리에 있는지 확인하거나 PYTHONPATH를 설정하세요.", file=sys.stderr)
    sys.exit(1)

# --- 모듈 상수 정의 (전역 변수 아님) ---
# 메인 스크립트의 로깅 레벨을 제어하는 환경 변수 이름
LOG_LEVEL_ENV_VAR = "ONEW_MAIN_LOG_LEVEL"
# 기본 로깅 레벨
DEFAULT_LOG_LEVEL = "INFO"
# 성공적인 종료를 위한 시스템 종료 코드
SUCCESS_EXIT_CODE = 0
# 실패적인 종료를 위한 시스템 종료 코드
FAILURE_EXIT_CODE = 1

# --- 로거 설정 ---
def setup_logging() -> None:
    """
    환경 변수 'ONEW_MAIN_LOG_LEVEL'에 따라 로깅을 설정합니다.
    환경 변수가 설정되지 않은 경우 기본값은 INFO입니다.
    """
    # 환경 변수에서 로깅 레벨을 읽어오고, 없으면 기본값 사용
    log_level_str = os.getenv(LOG_LEVEL_ENV_VAR, DEFAULT_LOG_LEVEL).upper()
    # 문자열 로깅 레벨을 logging 모듈의 상수로 변환
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 기본 로깅 설정
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)  # 표준 출력으로 로그를 보냄
        ]
    )
    # onew_system_processor 모듈의 로거도 동일한 레벨로 설정하여 일관성을 유지합니다.
    # onew_system_processor 내부에서 별도의 로거 이름을 사용한다면 해당 이름을 지정해야 합니다.
    logging.getLogger('onew_system_processor').setLevel(log_level)

# --- 명령줄 인수 파싱 ---
def parse_arguments() -> argparse.Namespace:
    """
    명령줄 인수를 파싱합니다.

    -i, --input: 온유 시스템이 처리할 입력 데이터 (필수)
    -c, --config-path: 추가 설정 파일 경로 (선택 사항, 현재는 사용되지 않음)

    Returns:
        argparse.Namespace: 파싱된 인수 객체.
    """
    parser = argparse.ArgumentParser(
        description="온유 시스템 통합 및 실행 스크립트"
    )
    parser.add_argument(
        "-i", "--input",
        type=str,
        required=True,
        help="온유 시스템이 처리할 입력 데이터"
    )
    parser.add_argument(
        "-c", "--config-path",
        type=str,
        default=None,
        help="온유 시스템에 전달할 추가 설정 파일의 경로 (현재는 main.py에서 직접 사용되지 않음, 확장 가능성)"
    )
    return parser.parse_args()

# --- 시스템 흐름 실행 ---
def execute_onew_system_flow(input_data: str, config_path: str = None) -> str | None:
    """
    'onew_system_processor' 모듈을 사용하여 온유 시스템의 핵심 흐름을 실행합니다.
    예외 발생 시 로깅하고 None을 반환하여 실패를 알립니다.

    Args:
        input_data (str): 시스템에 전달할 입력 데이터.
        config_path (str, optional): 설정 파일 경로. 현재는 main.py에서 직접 사용되지 않지만,
                                     onew_system_processor에 전달될 수 있습니다.

    Returns:
        str | None: 처리 성공 시 결과 문자열, 실패 시 None.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"온유 시스템 흐름 시작. 입력 데이터: '{input_data[:70]}{'...' if len(input_data) > 70 else ''}'")

    # onew_system_processor에 전달할 설정 딕셔너리
    # main.py에서 onew_system_processor에 특정 설정을 전달해야 한다면 이 딕셔너리를 채웁니다.
    # 예: processor_config["mode"] = os.getenv("ONEW_PROCESSOR_MODE", "default")
    # onew_system_processor는 자체적으로 필요한 환경 변수(예: ONEW_API_KEY)를 읽는다고 가정합니다.
    processor_config = {}

    try:
        # onew_system_processor 모듈의 핵심 처리 함수 호출
        # onew_system_processor.process_system 함수가 input_data와 config 딕셔너리를
        # 인수로 받는다고 가정합니다.
        result = onew_system_processor.process_system(input_data=input_data, config=processor_config)
        logger.info("온유 시스템 처리 성공.")
        return result
    except ValueError as e:
        # 입력 데이터 관련 오류 처리
        logger.error(f"입력 데이터 오류 발생: {e}")
        return None
    except RuntimeError as e:
        # 시스템 내부 처리 중 발생한 런타임 오류 처리
        logger.error(f"시스템 처리 중 런타임 오류 발생: {e}")
        return None
    except Exception as e:
        # 예상치 못한 모든 종류의 오류 처리
        logger.exception(f"예기치 않은 오류 발생: {e}") # exception은 스택 트레이스를 포함하여 로깅
        return None

# --- 메인 실행 함수 ---
def main() -> None:
    """
    스크립트의 메인 진입점입니다.
    로깅 설정, 인수 파싱, 시스템 흐름 실행 및 결과 출력을 담당합니다.
    """
    setup_logging()  # 로깅 설정 초기화
    logger = logging.getLogger(__name__) # 메인 로거 인스턴스 가져오기

    args = parse_arguments()  # 명령줄 인수 파싱
    input_data = args.input
    config_path = args.config_path

    logger.info("메인 스크립트 실행 시작.")
    logger.debug(f"파싱된 입력 데이터: '{input_data[:70]}{'...' if len(input_data) > 70 else ''}'")
    if config_path:
        logger.debug(f"파싱된 설정 파일 경로: '{config_path}'")

    # 온유 시스템의 핵심 흐름 실행
    final_result = execute_onew_system_flow(input_data, config_path)

    if final_result is not None:
        # 처리 성공 시 결과 출력 및 성공 종료 코드 반환
        print("\n--- 온유 시스템 최종 결과 ---")
        print(final_result)
        sys.exit(SUCCESS_EXIT_CODE)
    else:
        # 처리 실패 시 오류 메시지 출력 및 실패 종료 코드 반환
        print("\n--- 온유 시스템 처리 실패 ---", file=sys.stderr)
        sys.exit(FAILURE_EXIT_CODE)

# --- 스크립트 직접 실행 시 ---
if __name__ == "__main__":
    main()