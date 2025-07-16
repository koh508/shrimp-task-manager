#!/usr/bin/env python3
"""
파일 관련 유틸리티 함수 모음
"""
import os
import logging
from typing import List


def safe_write(path: str, content_parts: List[str]) -> bool:
    """
    파일을 여러 부분으로 나누어 안전하게 씁니다.
    임시 파일에 먼저 내용을 쓴 뒤, 성공적으로 완료되면 원자적으로 교체합니다.
    이를 통해 쓰기 도중 발생하는 중단으로부터 파일을 보호합니다.

    Args:
        path (str): 최종 파일 경로.
        content_parts (List[str]): 파일에 쓸 내용 조각들의 리스트.

    Returns:
        bool: 성공 여부.
    """
    tmp_path = f"{path}.tmp"
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            for part in content_parts:
                f.write(part)

        os.replace(tmp_path, path)
        logging.info(f"파일이 성공적으로 저장되었습니다: {path}")
        return True
    except IOError as e:
        logging.error(f"파일 쓰기 오류 ({path}): {e}")
        # Clean up the temporary file if it exists
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False
    except Exception as e:
        logging.error(f"알 수 없는 오류 발생 ({path}): {e}")
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
        return False
