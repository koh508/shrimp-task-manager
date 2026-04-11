# plan/improvement_plan_generator.py

"""
온유 시스템 개선 계획 초기 설계 문서 생성 모듈.

이 모듈은 현재 온유 시스템에서 발생하는 'str' object has no attribute 'get' 오류 개선을 위한
초기 설계 문서를 Markdown 형식으로 생성합니다.
생성된 내용은 'plan/improvement_plan_initial_design.md' 파일에 저장될 수 있습니다.

요구사항:
- 개선할 기능의 개요
- 예상되는 변경 사항
- 변경 사항을 검증하기 위한 테스트 계획 (성공 지표 포함)

선행 태스크 결과 참고:
- 시스템 파일 구조 요약 로드 실패 원인 분석: analysis/system_interface_summary_failure_analysis.md
- 오류 원인: 'str' object has no attribute 'get'
"""

# 모듈 상수는 대문자로 정의하여 전역 변수 사용 금지 원칙을 준수합니다.
MARKDOWN_HEADER_LEVEL_1 = "#"
MARKDOWN_HEADER_LEVEL_2 = "##"
MARKDOWN_HEADER_LEVEL_3 = "###"
MARKDOWN_LIST_ITEM = "- "

def _generate_overview_section() -> str:
    """
    개선할 기능의 개요 섹션을 생성합니다.
    단일 책임 원칙에 따라 특정 섹션의 내용을 생성하는 순수 함수입니다.
    """
    overview_title = f"{MARKDOWN_HEADER_LEVEL_2} 1. 개선 기능 개요\n"
    overview_content = (
        f"{MARKDOWN_LIST_ITEM} **문제 정의**: 현재 시스템에서 파일 구조 요약을 로드하는 과정에서 "
        "'str' object has no attribute 'get' 오류가 발생하여 시스템 인터페이스 요약 로드가 실패합니다.\n"
        f"{MARKDOWN_LIST_ITEM} **원인 분석**: `analysis/system_interface_summary_failure_analysis.md` 문서에 따르면, "
        "이는 시스템이 딕셔너리 형태의 데이터를 기대하는 곳에 문자열 타입의 데이터가 전달되어, "
        "딕셔너리 메서드인 `get()`을 문자열 객체에서 호출하려 할 때 발생하는 `AttributeError`입니다.\n"
        f"{MARKDOWN_LIST_ITEM} **개선 목표**: 시스템 인터페이스 요약 로드 로직의 견고성을 강화하여, "
        "예상치 못한 데이터 타입이 입력될 경우에도 안정적으로 처리하고, "
        "정상적인 딕셔너리 형태의 데이터를 올바르게 파싱하여 사용하도록 합니다.\n"
        f"{MARKDOWN_LIST_ITEM} **주요 개선 방향**: 입력 데이터의 유효성 검사 및 타입 변환 로직 강화.\n"
    )
    return overview_title + overview_content

def _generate_expected_changes_section() -> str:
    """
    예상되는 변경 사항 섹션을 생성합니다.
    단일 책임 원칙에 따라 특정 섹션의 내용을 생성하는 순수 함수입니다.
    """
    changes_title = f"{MARKDOWN_HEADER_LEVEL_2} 2. 예상되는 변경 사항\n"
    changes_content = (
        f"{MARKDOWN_HEADER_LEVEL_3} 2.1. 데이터 로드 및 파싱 로직 수정\n"
        f"{MARKDOWN_LIST_ITEM} **현재**: 파일에서 읽어온 내용을 직접 사용하거나, 불충분한 타입 검사로 인해 문자열이 그대로 전달될 가능성.\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: 파일에서 읽어온 데이터가 JSON 문자열인 경우, `json.loads()`를 사용하여 딕셔너리 객체로 변환하는 로직을 추가합니다.\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: `json.JSONDecodeError` 등 파싱 실패 예외를 명시적으로 처리하여, 실패 시 기본값 반환 또는 적절한 오류 로깅 및 상위 전파를 수행합니다.\n"
        f"{MARKDOWN_HEADER_LEVEL_3} 2.2. 입력 데이터 유효성 검사 강화\n"
        f"{MARKDOWN_LIST_ITEM} **현재**: 데이터 타입에 대한 명시적인 검사 부족.\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: 로드된 데이터가 예상하는 딕셔너리 타입이 아닐 경우, 경고 로깅 후 기본값을 반환하거나, "
        "예외를 발생시켜 상위 호출자가 처리하도록 합니다.\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: 특정 키(`get()`으로 접근하려는 키)의 존재 여부 및 해당 값의 타입 유효성 검사를 추가합니다.\n"
        f"{MARKDOWN_HEADER_LEVEL_3} 2.3. 오류 처리 및 로깅 개선\n"
        f"{MARKDOWN_LIST_ITEM} **현재**: `AttributeError` 발생 시 시스템이 비정상 종료되거나 예상치 못한 동작을 할 수 있음.\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: 데이터 로드 및 파싱 실패 시, 상세한 오류 메시지와 함께 `logging` 모듈을 사용하여 오류를 기록합니다.\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: 오류 발생 시 시스템 전체에 영향을 주지 않도록, 해당 모듈에서 복구 가능한 수준의 오류는 처리하고, "
        "복구 불가능한 오류는 명시적으로 예외를 발생시켜 상위 호출자가 처리하도록 합니다.\n"
        f"{MARKDOWN_HEADER_LEVEL_3} 2.4. 의존성 관리 (선택 사항)\n"
        f"{MARKDOWN_LIST_ITEM} **변경**: 만약 해당 데이터가 다른 모듈에서 생성되는 경우, 데이터 생성 모듈과 소비 모듈 간의 "
        "데이터 계약(Data Contract)을 명확히 정의하고, 이를 준수하도록 리팩토링을 고려합니다.\n"
    )
    return changes_title + changes_content

def _generate_test_plan_section() -> str:
    """
    변경 사항을 검증하기 위한 테스트 계획 섹션을 생성합니다.
    단일 책임 원칙에 따라 특정 섹션의 내용을 생성하는 순수 함수입니다.
    """
    test_plan_title = f"{MARKDOWN_HEADER_LEVEL_2} 3. 테스트 계획\n"
    test_plan_content = (
        f"{MARKDOWN_HEADER_LEVEL_3} 3.1. 단위 테스트 (Unit Tests)\n"
        f"{MARKDOWN_LIST_ITEM} **테스트 대상**: 데이터 로드 및 파싱을 담당하는 함수 (예: `load_system_summary`, `parse_summary_data`).\n"
        f"{MARKDOWN_LIST_ITEM} **테스트 시나리오**:\n"
        f"    {MARKDOWN_LIST_ITEM} 유효한 JSON 문자열 입력: 올바른 딕셔너리 객체로 파싱되는지 확인.\n"
        f"    {MARKDOWN_LIST_ITEM} 유효하지 않은 JSON 문자열 입력: `JSONDecodeError`가 적절히 처리되고, 예상된 실패 값(예: `None` 또는 빈 딕셔너리)이 반환되는지 확인.\n"
        f"    {MARKDOWN_LIST_ITEM} 일반 문자열 입력 (JSON 형식이 아님): `AttributeError`가 발생하지 않고, 적절히 처리되는지 확인.\n"
        f"    {MARKDOWN_LIST_ITEM} 빈 문자열 또는 `None` 입력: 예외 없이 처리되고, 예상된 실패 값이 반환되는지 확인.\n"
        f"    {MARKDOWN_LIST_ITEM} 예상되는 키가 없는 딕셔너리 입력: `get()` 호출 시 기본값이 반환되거나, 적절히 처리되는지 확인.\n"
        f"{MARKDOWN_HEADER_LEVEL_3} 3.2. 통합 테스트 (Integration Tests)\n"
        f"{MARKDOWN_LIST_ITEM} **테스트 대상**: 시스템 인터페이스 요약 로드부터 이를 사용하는 상위 모듈까지의 전체 흐름.\n"
        f"{MARKDOWN_LIST_ITEM} **테스트 시나리오**:\n"
        f"    {MARKDOWN_LIST_ITEM} 실제 시스템 환경에서 유효한 요약 파일 로드: 요약 정보가 성공적으로 로드되고, 시스템이 정상적으로 동작하는지 확인.\n"
        f"    {MARKDOWN_LIST_ITEM} 실제 시스템 환경에서 손상되거나 잘못된 형식의 요약 파일 로드: `AttributeError` 없이 오류가 적절히 로깅되고, 시스템이 비정상 종료되지 않는지 확인.\n"
        f"    {MARKDOWN_LIST_ITEM} 요약 파일이 없는 경우: 파일 없음 오류가 적절히 처리되는지 확인.\n"
        f"{MARKDOWN_HEADER_LEVEL_3} 3.3. 성공 판단 지표\n"
        f"{MARKDOWN_LIST_ITEM} **오류 감소**: 프로덕션 환경에서 'str' object has no attribute 'get' 오류 로그가 0건으로 수렴.\n"
        f"{MARKDOWN_LIST_ITEM} **성공적인 로드율**: 유효한 시스템 인터페이스 요약 파일에 대한 로드 성공률이 100% 달성.\n"
        f"{MARKDOWN_LIST_ITEM} **시스템 안정성**: 잘못된 입력에도 불구하고 시스템이 비정상 종료되지 않고, 예상된 오류 처리 로직이 동작.\n"
        f"{MARKDOWN_LIST_ITEM} **데이터 무결성**: 로드된 요약 데이터가 원본 파일의 내용과 일치하며, 올바른 구조를 유지.\n"
        f"{MARKDOWN_LIST_ITEM} **성능**: 데이터 로드 및 파싱 로직 변경으로 인한 성능 저하가 발생하지 않음 (측정 시 5% 이내의 변화 허용).\n"
    )
    return test_plan_title + test_plan_content

def generate_improvement_plan_markdown() -> str:
    """
    전체 개선 계획 초기 설계 문서를 Markdown 형식으로 생성합니다.
    이 함수는 다른 섹션 생성 함수들을 호출하여 전체 문서를 구성합니다.
    """
    title = f"{MARKDOWN_HEADER_LEVEL_1} 온유 시스템 개선 계획: 시스템 인터페이스 요약 로드 오류 해결\n"
    introduction = (
        "이 문서는 현재 온유 시스템에서 발생하는 'str' object has no attribute 'get' 오류를 해결하기 위한 "
        "초기 설계 계획을 담고 있습니다. 해당 오류는 시스템 파일 구조 요약을 로드하는 과정에서 발생하며, "
        "데이터 타입 불일치로 인해 발생합니다. 본 개선 계획은 이 문제를 해결하고 시스템의 안정성을 높이는 것을 목표로 합니다.\n\n"
    )

    overview = _generate_overview_section()
    expected_changes = _generate_expected_changes_section()
    test_plan = _generate_test_plan_section()

    full_markdown = (
        title +
        introduction +
        overview + "\n" + # 각 섹션 사이에 줄 바꿈 추가
        expected_changes + "\n" +
        test_plan + "\n"
    )
    return full_markdown

if __name__ == "__main__":
    # 이 스크립트를 직접 실행하여 마크다운 내용을 콘솔에 출력하거나 파일로 저장할 수 있습니다.
    markdown_content = generate_improvement_plan_markdown()
    print(markdown_content)

    # 실제 파일로 저장하려면 다음 주석을 해제하고 사용하세요.
    # output_filename = "plan/improvement_plan_initial_design.md"
    # try:
    #     with open(output_filename, "w", encoding="utf-8") as f:
    #         f.write(markdown_content)
    #     print(f"\n개선 계획 문서가 '{output_filename}' 파일로 성공적으로 생성되었습니다.")
    # except IOError as e:
    #     # 예외는 로깅 후 상위로 전파하거나 명시적 실패값 반환 원칙에 따라,
    #     # 여기서는 간단히 출력하지만 실제 시스템에서는 logging 모듈을 사용합니다.
    #     print(f"\n파일 저장 중 오류 발생: {e}")