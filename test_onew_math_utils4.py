"""
onew_math_utils4.py 모듈의 square_number 함수를 테스트하는 모듈입니다.
양수, 음수, 0에 대한 테스트 케이스를 포함합니다.

이 파일은 onew_math_utils4.py 파일이 동일한 디렉토리에 존재한다고 가정하고 작성되었습니다.
"""

import onew_math_utils4

def test_square_number():
    """
    onew_math_utils4.square_number 함수를 테스트합니다.
    양수, 음수, 0에 대한 테스트 케이스를 검증합니다.
    """
    print("\n--- square_number 함수 테스트 시작 ---")

    # 1. 양수 테스트 케이스
    positive_number = 5
    expected_positive_result = 25
    actual_positive_result = onew_math_utils4.square_number(positive_number)
    assert actual_positive_result == expected_positive_result, \
        f"양수 테스트 실패: {positive_number}의 제곱은 {expected_positive_result}여야 하지만, {actual_positive_result}가 반환되었습니다."
    print(f"양수 테스트 성공: {positive_number}의 제곱은 {actual_positive_result}입니다.")

    # 2. 음수 테스트 케이스
    negative_number = -3
    expected_negative_result = 9
    actual_negative_result = onew_math_utils4.square_number(negative_number)
    assert actual_negative_result == expected_negative_result, \
        f"음수 테스트 실패: {negative_number}의 제곱은 {expected_negative_result}여야 하지만, {actual_negative_result}가 반환되었습니다."
    print(f"음수 테스트 성공: {negative_number}의 제곱은 {actual_negative_result}입니다.")

    # 3. 0 테스트 케이스
    zero_number = 0
    expected_zero_result = 0
    actual_zero_result = onew_math_utils4.square_number(zero_number)
    assert actual_zero_result == expected_zero_result, \
        f"0 테스트 실패: {zero_number}의 제곱은 {expected_zero_result}여야 하지만, {actual_zero_result}가 반환되었습니다."
    print(f"0 테스트 성공: {zero_number}의 제곱은 {actual_zero_result}입니다.")

    # 추가 테스트 케이스 (실수)
    float_number = 2.5
    expected_float_result = 6.25
    actual_float_result = onew_math_utils4.square_number(float_number)
    assert actual_float_result == expected_float_result, \
        f"실수 테스트 실패: {float_number}의 제곱은 {expected_float_result}여야 하지만, {actual_float_result}가 반환되었습니다."
    print(f"실수 테스트 성공: {float_number}의 제곱은 {actual_float_result}입니다.")

    print("--- square_number 함수 테스트 완료 (모든 테스트 통과) ---")

# 이 모듈이 직접 실행될 때 테스트 함수를 호출합니다.
if __name__ == "__main__":
    test_square_number()