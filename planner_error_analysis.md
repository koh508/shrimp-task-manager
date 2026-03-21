"""
온유 시스템 플래너 오류 분석 및 해결 방안 모듈

이 모듈은 온유 시스템의 플래너에서 발생할 수 있는 잠재적인 오류를 식별하고,
각 오류에 대한 구체적인 해결 방안을 제시합니다. 특히 '실행 불가 (engine/client 미주입)'와 같은
반복적인 문제에 초점을 맞춰 안정적인 플래너 운영을 위한 가이드라인을 제공합니다.

--- 1. 현재 플래너 분석 ---
플래너는 주어진 목표를 달성하기 위해 일련의 단계를 계획하고 실행하는 핵심 구성 요소입니다.
일반적으로 다음과 같은 흐름으로 작동합니다:
1.  **초기화**: 플래너가 시작될 때, 작업을 수행하는 데 필요한 핵심 의존성(예: `engine`, `client`)을 주입받고 설정을 로드합니다.
2.  **목표 수신**: 사용자 또는 상위 시스템으로부터 처리할 목표(Goal)를 받습니다.
3.  **계획 생성**: 수신된 목표를 분석하여, 목표 달성을 위한 구체적이고 실행 가능한 작업 목록(Plan)을 생성합니다. 이 과정에서 AI 모델 또는 복잡한 로직이 사용될 수 있습니다.
4.  **계획 실행**: 생성된 계획의 각 작업을 순차적으로 또는 병렬로 실행합니다. 각 작업은 `engine`을 통해 실제 시스템 동작으로 변환되거나 `client`를 통해 외부 서비스와 상호작용할 수 있습니다.
5.  **결과 반환/보고**: 모든 계획이 성공적으로 실행되면 최종 결과를 반환하거나, 관련 시스템에 진행 상황 및 완료를 보고합니다.

이 과정에서 다양한 외부 시스템(데이터베이스, 외부 API, 파일 시스템 등)과의 상호작용 및 플래너 내부 상태 관리가 이루어집니다.
플래너의 안정성은 이러한 의존성 관리, 계획의 유효성, 실행의 견고성, 그리고 상태의 일관성에 크게 좌우됩니다.
"""

import logging
import os
import threading
import time
from typing import Any, Dict, List, Optional, Tuple, Callable

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- 2. 오류 식별 ---
# 플래너에서 발생할 수 있는 잠재적인 오류 시나리오를 정의합니다.
# 특히 과거 실패 기록에서 나타난 '실행 불가 (engine/client 미주입)'와 같은 반복적인 문제에 초점을 맞춥니다.

class PlannerErrorType:
    """플래너에서 발생할 수 있는 잠재적인 오류 유형을 정의하는 상수."""
    # 반복적인 문제: '실행 불가 (engine/client 미주입)'
    # 이 문제는 플래너가 작업을 수행하는 데 필수적인 핵심 의존성인 'engine' 또는 'client'가
    # 올바르게 초기화되거나 주입되지 않았을 때 발생합니다. 이는 주로 설정 오류,
    # 초기화 로직의 결함, 또는 테스트 환경 구성 문제에서 기인합니다.
    MISSING_DEPENDENCY = "MISSING_DEPENDENCY"

    # 기타 잠재적 오류 시나리오
    INVALID_PLAN_GENERATION = "INVALID_PLAN_GENERATION"  # 유효하지 않거나 비실용적인 계획 생성
    EXECUTION_FAILURE = "EXECUTION_FAILURE"              # 계획 실행 중 개별 작업 실패
    EXTERNAL_SERVICE_UNAVAILABLE = "EXTERNAL_SERVICE_UNAVAILABLE" # 외부 서비스 (DB, API 등) 연결 실패
    STATE_CORRUPTION = "STATE_CORRUPTION"                # 플래너 내부 상태 불일치 또는 손상
    TIMEOUT = "TIMEOUT"                                  # 작업 또는 전체 계획 실행 시간 초과
    PERMISSION_DENIED = "PERMISSION_DENIED"              # 필요한 리소스 접근 권한 부족
    RESOURCE_EXHAUSTION = "RESOURCE_EXHAUSTION"          # 메모리, CPU, 디스크 공간 등 시스템 리소스 부족

# --- 3. 오류 방안 제시 ---
# 식별된 각 오류에 대한 구체적인 해결 방안을 제시하는 함수들입니다.

class MockEngine:
    """테스트 환경에서 사용될 Mock Engine 객체."""
    def __init__(self):
        logger.info("MockEngine: 초기화됨.")
    def execute(self, task: str, **kwargs) -> Any:
        logger.info(f"MockEngine: 작업 '{task}' 실행 중. kwargs: {kwargs}")
        return {"status": "mock_success", "task": task, "result": f"Mocked result for {task}"}

class MockClient:
    """테스트 환경에서 사용될 Mock Client 객체."""
    def __init__(self):
        logger.info("MockClient: 초기화됨.")
    def get_data(self, query: str, **kwargs) -> Dict[str, Any]:
        logger.info(f"MockClient: 데이터 '{query}' 요청 중. kwargs: {kwargs}")
        return {"mock_data": query, "source": "mock_client"}
    def send_notification(self, message: str) -> bool:
        logger.info(f"MockClient: 알림 '{message}' 전송 시도.")
        return True

def _validate_dependency_interface(dependency: Any, name: str, required_methods: List[str]) -> bool:
    """
    주어진 의존성 객체가 필요한 메서드를 가지고 있는지 확인합니다.
    """
    if dependency is None:
        return False
    for method in required_methods:
        if not hasattr(dependency, method) or not callable(getattr(dependency, method)):
            logger.error(f"의존성 '{name}'에 필수 메서드 '{method}'가 누락되었거나 호출 가능하지 않습니다.")
            return False
    return True

def check_and_resolve_missing_dependency(
    engine: Optional[Any],
    client: Optional[Any],
    use_mock_if_missing: bool = False
) -> Tuple[Any, Any]:
    """
    '실행 불가 (engine/client 미주입)' 문제를 확인하고 해결 방안을 제시합니다.
    engine/client가 올바르게 주입되고 초기화되는지 확인하며,
    필요한 경우 mock 객체를 사용하여 테스트 환경을 구성하는 방법을 포함합니다.

    Args:
        engine: 플래너에 주입될 엔진 객체 (예: 작업을 실행하는 핵심 로직).
        client: 플래너에 주입될 클라이언트 객체 (예: 외부 서비스와 통신).
        use_mock_if_missing: 의존성이 없을 경우 mock 객체를 생성하여 반환할지 여부.
                             주로 테스트 또는 개발 환경에서 사용됩니다.

    Returns:
        (validated_engine, validated_client) 튜플.
        모든 의존성이 유효하거나 mock 객체로 대체된 경우 해당 객체를 반환합니다.

    Raises:
        ValueError: `use_mock_if_missing`이 False이고 필수 의존성이 누락된 경우.
    """
    validated_engine = engine
    validated_client = client
    all_dependencies_ok = True

    # Engine 유효성 검사
    if not _validate_dependency_interface(validated_engine, "engine", ["execute"]):
        all_dependencies_ok = False
        if use_mock_if_missing:
            logger.warning("Engine이 누락되었거나 유효하지 않습니다. MockEngine을 주입합니다.")
            validated_engine = MockEngine()
        else:
            logger.error("Engine이 누락되었거나 유효하지 않으며, mock 주입이 비활성화되어 있습니다. 플래너를 실행할 수 없습니다.")

    # Client 유효성 검사 (예시: get_data, send_notification 메서드 필요)
    if not _validate_dependency_interface(validated_client, "client", ["get_data", "send_notification"]):
        all_dependencies_ok = False
        if use_mock_if_missing:
            logger.warning("Client가 누락되었거나 유효하지 않습니다. MockClient를 주입합니다.")
            validated_client = MockClient()
        else:
            logger.error("Client가 누락되었거나 유효하지 않으며, mock 주입이 비활성화되어 있습니다. 플래너를 실행할 수 없습니다.")

    if not all_dependencies_ok and not use_mock_if_missing:
        raise ValueError(
            f"{PlannerErrorType.MISSING_DEPENDENCY}: 필수 의존성(engine/client)이 누락되었거나 유효하지 않습니다. "
            "mock 객체 사용이 비활성화되어 플래너를 실행할 수 없습니다."
        )
    
    if all_dependencies_ok:
        logger.info("모든 필수 의존성(engine, client)이 성공적으로 검증되었습니다.")
    elif use_mock_if_missing:
        logger.info("일부 필수 의존성이 mock 객체로 대체되어 플래너가 테스트/개발 모드로 실행됩니다.")

    return validated_engine, validated_client

def analyze_invalid_plan_generation(plan_data: Dict[str, Any]) -> List[str]:
    """
    생성된 계획(Plan)의 유효성을 분석하고 잠재적인 문제를 식별합니다.
    계획이 올바른 구조를 가지고 있는지, 실행 가능한 단계를 포함하는지 등을 검사합니다.

    Args:
        plan_data: 플래너가 생성한 계획 데이터 (딕셔너리 형태).

    Returns:
        발견된 문제점 목록. 문제가 없으면 빈 리스트를 반환합니다.
    """
    issues = []
    if not plan_data or not isinstance(plan_data, dict):
        issues.append("계획 데이터가 비어있거나 딕셔너리 형태가 아닙니다.")
        return issues

    if "steps" not in plan_data or not isinstance(plan_data["steps"], list):
        issues.append("계획 데이터에 'steps' 키가 없거나 'steps'가 리스트 형태가 아닙니다.")
    elif not plan_data["steps"]:
        issues.append("계획에 실행할 단계(steps)가 전혀 없습니다.")
    else:
        for i, step in enumerate(plan_data["steps"]):
            if not isinstance(step, dict):
                issues.append(f"단계 {i}가 딕셔너리 형태가 아닙니다: {step}")
            elif "action" not in step:
                issues.append(f"단계 {i}에 필수 'action' 키가 누락되었습니다: {step}")
            # 추가적인 유효성 검사 예시:
            # if step.get("action") == "call_api" and "endpoint" not in step:
            #     issues.append(f"단계 {i} (call_api)에 필수 'endpoint' 키가 누락되었습니다.")
            # if step.get("action") == "execute_code" and "code" not in step:
            #     issues.append(f"단계 {i} (execute_code)에 필수 'code' 키가 누락되었습니다.")

    if issues:
        logger.warning(f"{PlannerErrorType.INVALID_PLAN_GENERATION}: 유효하지 않은 계획이 감지되었습니다. 문제점: {issues}")
    else:
        logger.info("계획 생성이 유효한 것으로 보입니다.")
    return issues

def handle_execution_failure(
    task_name: str,
    exception: Exception,
    retry_strategy: Optional[Callable[[], bool]] = None,
    max_retries: int = 3,
    backoff_factor: float = 0.5
) -> bool:
    """
    개별 작업 실행 실패를 처리합니다. 재시도 로직을 포함할 수 있습니다.

    Args:
        task_name: 실패한 작업의 이름.
        exception: 발생한 예외 객체.
        retry_strategy: 재시도 로직을 수행하는 콜백 함수. 성공 시 True 반환.
        max_retries: 최대 재시도 횟수.
        backoff_factor: 재시도 간 지연 시간 계산을 위한 백오프 팩터 (지수 백오프).

    Returns:
        작업이 최종적으로 성공했는지 (재시도 포함) 여부.
    """
    logger.error(f"{PlannerErrorType.EXECUTION_FAILURE}: 작업 '{task_name}' 실행 실패: {type(exception).__name__} - {exception}")

    if retry_strategy:
        for attempt in range(max_retries):
            delay = backoff_factor * (2 ** attempt)
            logger.info(f"작업 '{task_name}' 재시도 ({attempt + 1}/{max_retries} 시도), {delay:.2f}초 후 재시도...")
            time.sleep(delay)
            try:
                if retry_strategy():
                    logger.info(f"작업 '{task_name}' 재시도 성공.")
                    return True
            except Exception as retry_ex:
                logger.warning(f"작업 '{task_name}' 재시도 중 예외 발생: {type(retry_ex).__name__} - {retry_ex}")
        logger.error(f"작업 '{task_name}'가 {max_retries}번의 재시도 후에도 최종 실패했습니다.")
    return False

def check_external_service_availability(service_name: str, health_check_func: Callable[[], bool]) -> bool:
    """
    외부 서비스의 가용성을 확인합니다.

    Args:
        service_name: 확인할 서비스의 이름.
        health_check_func: 서비스의 상태를 확인하는 함수 (성공 시 True 반환).

    Returns:
        서비스가 사용 가능한지 여부.
    """
    try:
        if health_check_func():
            logger.info(f"외부 서비스 '{service_name}'가 사용 가능합니다.")
            return True
        else:
            logger.error(f"{PlannerErrorType.EXTERNAL_SERVICE_UNAVAILABLE}: 외부 서비스 '{service_name}'가 헬스 체크에 실패했습니다.")
            return False
    except Exception as e:
        logger.error(f"{PlannerErrorType.EXTERNAL_SERVICE_UNAVAILABLE}: 외부 서비스 '{service_name}' 가용성 확인 중 예외 발생: {e}")
        return False

def detect_and_recover_state_corruption(current_state: Dict[str, Any], expected_schema: Dict[str, Any]) -> bool:
    """
    플래너 내부 상태의 불일치 또는 손상을 감지하고 복구 시도를 제안합니다.
    (이 함수는 실제 복구 로직보다는 감지 및 경고에 중점을 둡니다. 실제 복구는 더 복잡할 수 있습니다.)

    Args:
        current_state: 플래너의 현재 상태 딕셔너리.
        expected_schema: 예상되는 상태 스키마 (예: 필수 키와 그 값의 타입).

    Returns:
        상태가 유효하다고 판단되면 True, 그렇지 않으면 False.
    """
    is_valid = True
    for key, expected_type in expected_schema.items():
        if key not in current_state:
            logger.error(f"{PlannerErrorType.STATE_CORRUPTION}: 상태 손상 감지 - 필수 키 '{key}'가 누락되었습니다.")
            is_valid = False
        elif not isinstance(current_state[key], expected_type):
            logger.error(f"{PlannerErrorType.STATE_CORRUPTION}: 상태 손상 감지 - 키 '{key}'의 타입이 예상과 다릅니다. "
                         f"현재 타입: {type(current_state[key]).__name__}, 예상 타입: {expected_type.__name__}.")
            is_valid = False
    
    if not is_valid:
        logger.warning("플래너 상태 손상이 감지되었습니다. 수동 개입 또는 상태 재설정(예: 기본값 로드, 이전 유효 상태로 롤백)이 필요할 수 있습니다.")
        # 복구 로직 예시 (실제 구현은 플래너의 상태 영속화 방식에 따라 달라짐):
        # - `current_state`를 기본값으로 재설정하거나,
        # - 영속화된 이전 유효 상태를 로드하는 로직을 호출하거나,
        # - 사용자/관리자에게 알림을 보내는 등의 조치를 취할 수 있습니다.
    else:
        logger.info("플래너 상태가 예상 스키마와 일관적입니다.")
    return is_valid

def enforce_timeout(func: Callable[..., Any], timeout_seconds: int, *args, **kwargs) -> Any:
    """
    주어진 함수에 시간 제한을 적용합니다. 함수 실행이 지정된 시간을 초과하면 `TimeoutError`를 발생시킵니다.

    Args:
        func: 시간 제한을 적용할 함수.
        timeout_seconds: 시간 제한 (초).
        *args, **kwargs: func에 전달될 인자.

    Returns:
        func의 반환 값.

    Raises:
        TimeoutError: 함수 실행이 시간 제한을 초과했을 때.
        Exception: func 실행 중 발생한 다른 예외.
    """
    result_container = [None]
    exception_container = [None]

    def target():
        try:
            result_container[0] = func(*args, **kwargs)
        except Exception as e:
            exception_container[0] = e

    thread = threading.Thread(target=target)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        logger.error(f"{PlannerErrorType.TIMEOUT}: 함수 '{func.__name__}'가 {timeout_seconds}초 내에 완료되지 않아 타임아웃되었습니다.")
        raise TimeoutError(f"Function '{func.__name__}' timed out after {timeout_seconds} seconds.")
    
    if exception_container[0]:
        logger.error(f"함수 '{func.__name__}' 실행 중 예외 발생: {exception_container[0]}")
        raise exception_container[0] # 원본 예외 다시 발생
    
    return result_container[0]

def check_permissions(resource_path: str, required_permissions: List[str]) -> bool:
    """
    특정 리소스(예: 파일, 디렉토리)에 대한 필요한 권한이 있는지 확인합니다.
    (이것은 OS 파일 시스템 권한의 예시이며, 실제 시스템에서는 데이터베이스 권한, API 접근 권한 등
    더 복잡한 권한 검사 로직이 필요할 수 있습니다.)

    Args:
        resource_path: 확인할 리소스의 경로.
        required_permissions: 필요한 권한 목록 (예: "read", "write", "execute").

    Returns:
        모든 필요한 권한이 있으면 True, 그렇지 않으면 False.
    """
    if not os.path.exists(resource_path):
        logger.error(f"{PlannerErrorType.PERMISSION_DENIED}: 리소스 '{resource_path}'가 존재하지 않습니다.")
        return False

    missing_permissions = []
    for perm in required_permissions:
        if perm == "read":
            if not os.access(resource_path, os.R_OK):
                missing_permissions.append("read")
        elif perm == "write":
            if not os.access(resource_path, os.W_OK):
                missing_permissions.append("write")
        elif perm == "execute":
            if not os.access(resource_path, os.X_OK):
                missing_permissions.append("execute")
        else:
            logger.warning(f"알 수 없는 권한 유형 '{perm}'이 리소스 '{resource_path}'에 대해 요청되었습니다.")

    if missing_permissions:
        logger.error(f"{PlannerErrorType.PERMISSION_DENIED}: 리소스 '{resource_path}'에 대한 권한이 부족합니다. 누락된 권한: {', '.join(missing_permissions)}")
        return False
    logger.info(f"리소스 '{resource_path}'에 대한 모든 필수 권한이 부여되었습니다.")
    return True

def check_resource_availability(resource_name: str, threshold_percent: float = 80.0) -> bool:
    """
    시스템 리소스(예: 디스크 공간)의 가용성을 확인합니다.
    (이것은 디스크 공간의 예시이며, 실제 시스템에서는 메모리, CPU 사용량 등 다양한 리소스를 확인할 수 있습니다.)

    Args:
        resource_name: 확인할 리소스의 이름 (예: 디스크 경로).
        threshold_percent: 사용률이 이 임계값을 초과하면 경고를 발생시킵니다.

    Returns:
        리소스가 임계값 미만으로 사용 중이면 True, 그렇지 않으면 False.
    """
    try:
        if os.path.isdir(resource_name):
            statvfs = os.statvfs(resource_name)
            total_bytes = statvfs.f_blocks * statvfs.f_frsize
            free_bytes = statvfs.f_bfree * statvfs.f_frsize
            used_percent = (total_bytes - free_bytes) / total_bytes * 100 if total_bytes > 0 else 0

            if used_percent >= threshold_percent:
                logger.error(f"{PlannerErrorType.RESOURCE_EXHAUSTION}: 리소스 '{resource_name}' 사용률이 임계값({threshold_percent:.2f}%)을 초과했습니다. "
                             f"현재 사용률: {used_percent:.2f}%")
                return False
            else:
                logger.info(f"리소스 '{resource_name}' 사용률: {used_percent:.2f}% (정상).")
                return True
        else:
            logger.warning(f"리소스 '{resource_name}'는 디렉토리가 아닙니다. 디스크 공간 확인을 건너뜀.")
            return True # 디렉토리가 아니면 일단 통과
    except Exception as e:
        logger.error(f"{PlannerErrorType.RESOURCE_EXHAUSTION}: 리소스 '{resource_name}' 가용성 확인 중 예외 발생: {e}")
        return False


# --- 4. 개선 제안 ---
# 플래너의 전반적인 안정성과 신뢰성을 높이기 위한 추가적인 개선 사항을 제안합니다.

class PlannerImprovements:
    """플래너의 안정성 및 신뢰성 향상을 위한 개선 제안."""

    RECOMMEND_DI_PATTERN = (
        "1. 강력한 의존성 주입 (DI) 패턴 적용: "
        "플래너 초기화 시 모든 필수 의존성을 명시적으로 주입하도록 강제하고, "
        "DI 컨테이너(예: `injector`, `dependency_injector`)를 사용하여 의존성 관리 및 테스트 용이성을 확보합니다. "
        "주입 시점에 의존성 유효성 검사 로직을 추가하여 초기 오류를 방지합니다."
    )

    RECOMMEND_STATE_MANAGEMENT = (
        "2. 강화된 상태 관리 및 영속화: "
        "플래너의 중요 상태(예: 현재 진행 단계, 작업 결과)를 주기적으로 영속화(파일, DB, 캐시 등)하여 "
        "장애 발생 시 복구 지점을 제공합니다. 상태 스키마 유효성 검사 로직을 추가하여 상태 손상을 방지하고, "
        "롤백 또는 재시작 시 이전 유효 상태로 복원하는 기능을 구현합니다."
    )

    RECOMMEND_RETRY_CIRCUIT_BREAKER = (
        "3. 견고한 재시도 및 회복 로직 구현: "
        "외부 서비스 호출 및 불안정한 작업에 대해 지수 백오프를 포함한 자동 재시도 메커니즘을 적용합니다. "
        "연속적인 실패로부터 시스템을 보호하기 위해 서킷 브레이커 패턴(예: `pybreaker`)을 적용하고, "
        "처리 실패한 메시지를 격리하고 사후 분석할 수 있도록 데드 레터 큐(DLQ)를 활용합니다."
    )

    RECOMMEND_LOGGING_MONITORING = (
        "4. 상세 로깅 및 모니터링 시스템 구축: "
        "플래너의 모든 주요 단계(초기화, 계획 생성, 작업 실행, 결과 보고)마다 상세하고 구조화된 로그를 기록합니다. "
        "Prometheus, Grafana와 같은 모니터링 도구와 연동하여 실시간으로 플래너의 상태를 감시하고, "
        "오류 발생 시 즉각적인 알림을 받을 수 있도록 합니다."
    )

    RECOMMEND_TESTING_SIMULATION = (
        "5. 통합 테스트 및 시뮬레이션 환경 강화: "
        "실제 운영 환경과 유사한 통합 테스트 환경을 구축하고, "
        "네트워크 지연, 서비스 중단, 리소스 고갈 등 다양한 실패 시나리오를 시뮬레이션하여 플래너의 복원력을 테스트합니다. "
        "카오스 엔지니어링 기법 도입을 고려하여 시스템의 취약점을 사전에 발견하고 개선합니다."
    )

    RECOMMEND_CODE_QUALITY = (
        "6. 정기적인 코드 리뷰 및 정적 분석 도입: "
        "정기적인 코드 리뷰를 통해 잠재적 버그 및 설계 결함을 조기에 발견합니다. "
        "Pylint, MyPy, Bandit 등 정적 분석 도구를 활용하여 코드 품질, 타입 안정성, 보안 취약점을 강화합니다."
    )


# --- 예시 사용법 ---
if __name__ == "__main__":
    logger.info("--- 플래너 오류 분석 모듈 예시 실행 시작 ---")

    # 1. '실행 불가 (engine/client 미주입)' 문제 시뮬레이션
    logger.info("\n--- 1. 의존성 미주입 시뮬레이션 ---")
    # Case 1: 의존성 누락 (mock 사용 안 함)
    try:
        logger.info("Case 1: Engine/Client 누락 (mock 사용 안 함) - 예상된 오류 발생")
        checked_engine, checked_client = check_and_resolve_missing_dependency(None, None, use_mock_if_missing=False)
    except ValueError as e:
        logger.error(f"예상된 오류 발생: {e}")

    # Case 2: 의존성 누락 (mock 사용)
    logger.info("\nCase 2: Engine/Client 누락 (mock 사용) - Mock 객체 주입")
    mock_engine_obj, mock_client_obj = check_and_resolve_missing_dependency(None, None, use_mock_if_missing=True)
    if mock_engine_obj and mock_client_obj:
        logger.info("MockEngine 및 MockClient가 성공적으로 주입되었습니다.")
        mock_engine_obj.execute("test_task_with_mock")
        mock_client_obj.get_data("test_query_with_mock")
        mock_client_obj.send_notification("Mock notification")

    # Case 3: 의존성 정상 주입
    logger.info("\nCase 3: Engine/Client 정상 주입")
    class RealEngine:
        def execute(self, task: str, **kwargs) -> str: return f"RealEngine: '{task}' 실행 완료. {kwargs}"
    class RealClient:
        def get_data(self, query: str, **kwargs) -> Dict[str, str]: return {"real_data": query, "kwargs": kwargs}
        def send_notification(self, message: str) -> bool: return True

    real_engine_obj = RealEngine()
    real_client_obj = RealClient()
    checked_engine, checked_client = check_and_resolve_missing_dependency(real_engine_obj, real_client_obj)
    if checked_engine and checked_client:
        logger.info("Real Engine 및 Client가 성공적으로 검증되었습니다.")
        logger.info(checked_engine.execute("real_task", param="value"))
        logger.info(checked_client.get_data("real_query", filter="active"))

    # 2. 유효하지 않은 계획 생성 분석 시뮬레이션
    logger.info("\n--- 2. 유효하지 않은 계획 생성 분석 시뮬레이션 ---")
    invalid_plan_1 = {}
    invalid_plan_2 = {"steps": []}
    invalid_plan_3 = {"steps": [{"action": "step1"}, "malformed_step", {"action": "step3"}]}
    valid_plan = {"steps": [{"action": "step1", "params": {"id": 1}}, {"action": "step2", "params": {"data": "abc"}}]}

    logger.info("invalid_plan_1 분석:")
    analyze_invalid_plan_generation(invalid_plan_1)
    logger.info("invalid_plan_2 분석:")
    analyze_invalid_plan_generation(invalid_plan_2)
    logger.info("invalid_plan_3 분석:")
    analyze_invalid_plan_generation(invalid_plan_3)
    logger.info("valid_plan 분석:")
    analyze_invalid_plan_generation(valid_plan)

    # 3. 실행 실패 처리 시뮬레이션
    logger.info("\n--- 3. 실행 실패 처리 시뮬레이션 ---")
    def failing_task_logic():
        # 50% 확률로 성공하는 재시도 로직
        if not hasattr(failing_task_logic, "attempt"):
            failing_task_logic.attempt = 0
        failing_task_logic.attempt += 1
        if failing_task_logic.attempt < 2: # 첫 번째 시도는 실패, 두 번째 시도는 성공
            raise RuntimeError(f"Simulated task failure! (Attempt {failing_task_logic.attempt})")
        logger.info(f"Simulating successful retry on attempt {failing_task_logic.attempt}...")
        return True

    def always_failing_task_logic():
        raise ConnectionError("Simulated persistent connection error!")

    logger.info("성공적인 재시도를 포함한 작업 실패 처리:")
    failing_task_logic.attempt = 0 # reset attempt counter
    handle_execution_failure("Task A", RuntimeError("Initial failure"), failing_task_logic, max_retries=2)

    logger.info("실패하는 재시도를 포함한 작업 실패 처리:")
    handle_execution_failure("Task B", ConnectionError("Initial connection error"), always_failing_task_logic, max_retries=2)

    logger.info("재시도 없이 작업 실패 처리:")
    handle_execution_failure("Task C", ValueError("Another failure"))

    # 4. 외부 서비스 가용성 확인 시뮬레이션
    logger.info("\n--- 4. 외부 서비스 가용성 확인 시뮬레이션 ---")
    def mock_db_health_check():
        # 50% 확률로 DB가 다운된 상황 시뮬레이션
        return os.urandom(1)[0] % 2 == 0

    check_external_service_availability("Database", mock_db_health_check)
    check_external_service_availability("API Gateway", lambda: True) # 항상 사용 가능
    check_external_service_availability("Broken Service", lambda: 1/0) # 예외 발생 시뮬레이션

    # 5. 상태 손상 감지 시뮬레이션
    logger.info("\n--- 5. 상태 손상 감지 시뮬레이션 ---")
    expected_state_schema = {
        "current_step": int,
        "plan_id": str,
        "is_active": bool
    }
    valid_state = {"current_step": 1, "plan_id": "plan-123", "is_active": True}
    missing_key_state = {"current_step": 1, "is_active": True} # plan_id 누락
    wrong_type_state = {"current_step": "one", "plan_id": "plan-123", "is_active": True} # current_step 타입 오류

    logger.info("valid_state에 대한 상태 손상 감지:")
    detect_and_recover_state_corruption(valid_state, expected_state_schema)
    logger.info("missing_key_state에 대한 상태 손상 감지:")
    detect_and_recover_state_corruption(missing_key_state, expected_state_schema)
    logger.info("wrong_type_state에 대한 상태 손상 감지:")
    detect_and_recover_state_corruption(wrong_type_state, expected_state_schema)

    # 6. 타임아웃 적용 시뮬레이션
    logger.info("\n--- 6. 타임아웃 적용 시뮬레이션 ---")
    def long_running_task(duration: int):
        logger.info(f"작업 시작: {duration}초 동안 실행...")
        time.sleep(duration)
        logger.info(f"작업 완료: {duration}초 후.")
        return "Task completed"

    try:
        logger.info("충분한 타임아웃으로 작업 실행 (2초 작업, 3초 타임아웃):")
        result = enforce_timeout(long_running_task, 3, duration=2)
        logger.info(f"결과: {result}")
    except TimeoutError as e:
        logger.error(f"타임아웃 오류 발생: {e}")

    try:
        logger.info("불충분한 타임아웃으로 작업 실행 (2초 작업, 1초 타임아웃):")
        result = enforce_timeout(long_running_task, 1, duration=2)
        logger.info(f"결과: {result}")
    except TimeoutError as e:
        logger.error(f"예상된 타임아웃 오류 발생: {e}")
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}")

    # 7. 권한 확인 시뮬레이션
    logger.info("\n--- 7. 권한 확인 시뮬레이션 ---")
    # 임시 파일 생성
    temp_file_path = "temp_planner_resource.txt"
    try:
        with open(temp_file_path, "w") as f:
            f.write("test content")
        os.chmod(temp_file_path, 0o400) # 소유자에게 읽기 권한만 부여

        logger.info(f"'{temp_file_path}' (읽기 전용)에 대한 권한 확인:")
        check_permissions(temp_file_path, ["read"])
        check_permissions(temp_file_path, ["read", "write"]) # 쓰기 권한 부족으로 실패 예상

        # 존재하지 않는 파일
        logger.info(f"존재하지 않는 파일 'non_existent.txt'에 대한 권한 확인:")
        check_permissions("non_existent.txt", ["read"])
    finally:
        if os.path.exists(temp_file_path):
            os.remove(temp_file_path)

    # 8. 리소스 고갈 확인 시뮬레이션 (디스크 공간)
    logger.info("\n--- 8. 리소스 고갈 확인 시뮬레이션 (디스크 공간) ---")
    # 현재 디렉토리의 디스크 공간 확인 (임계값 80%)
    check_resource_availability(os.getcwd(), threshold_percent=80.0)
    # 매우 낮은 임계값으로 설정하여 실패 시뮬레이션 (현재 디렉토리 사용률이 1%만 넘어도 실패)
    logger.info("매우 낮은 임계값(1%)으로 설정하여 실패 시뮬레이션:")
    check_resource_availability(os.getcwd(), threshold_percent=1.0)


    logger.info("\n--- 4. 개선 제안 ---")
    for attr_name in dir(PlannerImprovements):
        if attr_name.startswith("RECOMMEND_"):
            logger.info(f"{getattr(PlannerImprovements, attr_name)}")

    logger.info("--- 플래너 오류 분석 모듈 예시 실행 완료 ---")