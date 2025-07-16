#!/usr/bin/env python3
"""
옵시디언 화면 모니터링 및 변화 감지 시스템
"""
import hashlib
import json
import logging
import os
import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np
import pyautogui

# 로깅 설정
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class ObsidianScreenMonitor:
    """옵시디언 화면 모니터링 시스템"""

    def __init__(self, obsidian_window_title: str = "Obsidian"):
        self.obsidian_window_title = obsidian_window_title
        self.last_screenshot = None
        self.last_screenshot_hash = None
        self.change_threshold = 0.05  # 5% 변화 감지
        self.monitor_interval = 2.0  # 2초 간격 모니터링
        self.clipping_cooldown = 5.0  # 5초 쿨다운
        self.last_clipping_time = 0

        # 변화 감지 관련
        self.change_history = []
        self.max_history_size = 100

        # 클리핑 데이터 저장
        self.clipping_data = []
        self.clipping_counter = 0

        # 모니터링 상태
        self.monitoring = False
        self.monitor_thread = None

        # 저장 경로
        self.screenshots_dir = Path("screenshots")
        self.screenshots_dir.mkdir(exist_ok=True)

        # 변화 감지 알고리즘 설정
        self.detection_method = "histogram"  # histogram, ssim, mse

    def find_obsidian_window(self) -> Optional[Tuple[int, int, int, int]]:
        """옵시디언 윈도우 찾기"""
        try:
            import pygetwindow as gw

            # 옵시디언 윈도우 찾기
            windows = gw.getWindowsWithTitle(self.obsidian_window_title)

            if not windows:
                logger.warning(f"옵시디언 윈도우를 찾을 수 없음: {self.obsidian_window_title}")
                return None

            window = windows[0]

            # 윈도우가 최소화되어 있으면 복원
            if window.isMinimized:
                window.restore()

            # 윈도우 정보 반환 (x, y, width, height)
            return (window.left, window.top, window.width, window.height)

        except ImportError:
            logger.warning("pygetwindow가 설치되지 않음. 전체 화면 캡처를 사용합니다.")
            return None
        except Exception as e:
            logger.error(f"윈도우 찾기 실패: {e}")
            return None

    def capture_obsidian_screen(self) -> Optional[np.ndarray]:
        """옵시디언 화면 캡처"""
        try:
            # 옵시디언 윈도우 찾기
            window_info = self.find_obsidian_window()

            if window_info:
                # 특정 윈도우 영역 캡처
                x, y, width, height = window_info
                screenshot = pyautogui.screenshot(region=(x, y, width, height))
            else:
                # 전체 화면 캡처
                screenshot = pyautogui.screenshot()

            # PIL Image를 OpenCV 형식으로 변환
            screenshot_np = np.array(screenshot)
            screenshot_cv = cv2.cvtColor(screenshot_np, cv2.COLOR_RGB2BGR)

            return screenshot_cv

        except Exception as e:
            logger.error(f"화면 캡처 실패: {e}")
            return None

    def calculate_image_hash(self, image: np.ndarray) -> str:
        """이미지 해시 계산"""
        try:
            # 이미지를 작은 크기로 리사이즈
            small_image = cv2.resize(image, (16, 16))

            # 그레이스케일 변환
            gray = cv2.cvtColor(small_image, cv2.COLOR_BGR2GRAY)

            # 해시 계산
            image_hash = hashlib.md5(gray.tobytes()).hexdigest()

            return image_hash

        except Exception as e:
            logger.error(f"이미지 해시 계산 실패: {e}")
            return ""

    def detect_changes_histogram(self, current_image: np.ndarray) -> float:
        """히스토그램 기반 변화 감지"""
        try:
            if self.last_screenshot is None:
                return 1.0

            # 히스토그램 계산
            hist1 = cv2.calcHist(
                [self.last_screenshot], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
            )
            hist2 = cv2.calcHist(
                [current_image], [0, 1, 2], None, [8, 8, 8], [0, 256, 0, 256, 0, 256]
            )

            # 히스토그램 비교
            correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

            # 변화량 계산 (0에 가까울수록 변화가 큼)
            change_amount = 1.0 - correlation

            return max(0.0, min(1.0, change_amount))

        except Exception as e:
            logger.error(f"히스토그램 변화 감지 실패: {e}")
            return 0.0

    def detect_changes_ssim(self, current_image: np.ndarray) -> float:
        """SSIM 기반 변화 감지"""
        try:
            if self.last_screenshot is None:
                return 1.0

            # 이미지 크기 맞추기
            height, width, _ = self.last_screenshot.shape

            img1 = cv2.resize(self.last_screenshot, (width, height))
            img2 = cv2.resize(current_image, (width, height))

            # 그레이스케일 변환
            gray1 = cv2.cvtColor(img1, cv2.COLOR_BGR2GRAY)
            gray2 = cv2.cvtColor(img2, cv2.COLOR_BGR2GRAY)

            # SSIM 계산 (간단한 구현)
            mean1 = np.mean(gray1)
            mean2 = np.mean(gray2)

            var1 = np.var(gray1)
            var2 = np.var(gray2)

            cov = np.mean((gray1 - mean1) * (gray2 - mean2))

            ssim = (
                (2 * mean1 * mean2 + 0.01)
                * (2 * cov + 0.03)
                / ((mean1**2 + mean2**2 + 0.01) * (var1 + var2 + 0.03))
            )

            # 변화량 계산
            change_amount = 1.0 - ssim

            return max(0.0, min(1.0, change_amount))

        except Exception as e:
            logger.error(f"SSIM 변화 감지 실패: {e}")
            return 0.0

    def detect_changes_mse(self, current_image: np.ndarray) -> float:
        """MSE 기반 변화 감지"""
        try:
            if self.last_screenshot is None:
                return 1.0

            # 이미지 크기 맞추기
            height, width, _ = self.last_screenshot.shape

            img1 = cv2.resize(self.last_screenshot, (width, height))
            img2 = cv2.resize(current_image, (width, height))

            # MSE 계산
            mse = np.mean((img1.astype(float) - img2.astype(float)) ** 2)

            # 정규화 (0-1 범위)
            normalized_mse = min(1.0, mse / 10000.0)

            return normalized_mse

        except Exception as e:
            logger.error(f"MSE 변화 감지 실패: {e}")
            return 0.0

    def detect_changes(self, current_image: np.ndarray) -> float:
        """변화 감지"""
        try:
            if self.detection_method == "histogram":
                return self.detect_changes_histogram(current_image)
            elif self.detection_method == "ssim":
                return self.detect_changes_ssim(current_image)
            elif self.detection_method == "mse":
                return self.detect_changes_mse(current_image)
            else:
                return self.detect_changes_histogram(current_image)

        except Exception as e:
            logger.error(f"변화 감지 실패: {e}")
            return 0.0

    def save_screenshot(self, image: np.ndarray, change_amount: float) -> str:
        """스크린샷 저장"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"obsidian_screenshot_{timestamp}_{change_amount:.3f}.png"
            filepath = self.screenshots_dir / filename

            cv2.imwrite(str(filepath), image)

            return str(filepath)

        except Exception as e:
            logger.error(f"스크린샷 저장 실패: {e}")
            return ""

    def extract_text_from_image(self, image: np.ndarray) -> str:
        """이미지에서 텍스트 추출 (OCR)"""
        try:
            import pytesseract

            # 그레이스케일 변환
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # 텍스트 추출
            text = pytesseract.image_to_string(gray, lang="eng+kor")

            return text.strip()

        except ImportError:
            logger.warning("pytesseract가 설치되지 않음. 텍스트 추출을 건너뜁니다.")
            return ""
        except Exception as e:
            logger.error(f"텍스트 추출 실패: {e}")
            return ""

    def create_clipping_data(self, image: np.ndarray, change_amount: float) -> Dict:
        """클리핑 데이터 생성"""
        try:
            self.clipping_counter += 1

            # 스크린샷 저장
            screenshot_path = self.save_screenshot(image, change_amount)

            # 텍스트 추출
            extracted_text = self.extract_text_from_image(image)

            # 클리핑 데이터 생성
            clipping_data = {
                "id": self.clipping_counter,
                "timestamp": datetime.now().isoformat(),
                "screenshot_path": screenshot_path,
                "change_amount": change_amount,
                "extracted_text": extracted_text,
                "image_hash": self.calculate_image_hash(image),
                "detection_method": self.detection_method,
                "window_info": self.find_obsidian_window(),
            }

            return clipping_data

        except Exception as e:
            logger.error(f"클리핑 데이터 생성 실패: {e}")
            return {}

    def should_trigger_clipping(self, change_amount: float) -> bool:
        """클리핑 트리거 조건 확인"""
        try:
            current_time = time.time()

            # 쿨다운 확인
            if current_time - self.last_clipping_time < self.clipping_cooldown:
                return False

            # 지속적인 작은 변화 감지
            if len(self.change_history) >= 3:
                recent_changes = self.change_history[-3:]
                if all(change >= self.change_threshold for change in recent_changes):
                    return True

            return change_amount >= self.change_threshold * 2  # 큰 변화는 즉시 트리거

        except Exception as e:
            logger.error(f"클리핑 트리거 확인 실패: {e}")
            return False

    def monitor_loop(self):
        """모니터링 루프"""
        logger.info("옵시디언 화면 모니터링 시작")

        while self.monitoring:
            try:
                # 화면 캡처
                current_image = self.capture_obsidian_screen()

                if current_image is None:
                    logger.warning("화면 캡처 실패")
                    time.sleep(self.monitor_interval)
                    continue

                # 변화 감지
                change_amount = self.detect_changes(current_image)

                # 변화 히스토리 업데이트
                self.change_history.append(change_amount)
                if len(self.change_history) > self.max_history_size:
                    self.change_history.pop(0)

                # 클리핑 트리거 확인
                if self.should_trigger_clipping(change_amount):
                    logger.info(f"변화 감지됨: {change_amount:.3f} - 클리핑 트리거")

                    # 클리핑 데이터 생성
                    clipping_data = self.create_clipping_data(current_image, change_amount)

                    if clipping_data:
                        self.clipping_data.append(clipping_data)
                        self.last_clipping_time = time.time()

                        # 클리핑 이벤트 발생 알림
                        self.on_clipping_triggered(clipping_data)

                # 이전 스크린샷 업데이트
                self.last_screenshot = current_image.copy()
                self.last_screenshot_hash = self.calculate_image_hash(current_image)

                # 대기
                time.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"모니터링 루프 오류: {e}")
                time.sleep(self.monitor_interval)

        logger.info("옵시디언 화면 모니터링 종료")

    def on_clipping_triggered(self, clipping_data: Dict):
        """클리핑 트리거 이벤트 핸들러"""
        try:
            logger.info(f"클리핑 트리거됨: ID {clipping_data['id']}")

            # 클리핑 데이터 저장
            self.save_clipping_data(clipping_data)

            # WindSurf 연동 트리거 (다른 모듈에서 처리)
            # 여기서는 이벤트만 발생시키고 실제 처리는 다른 모듈에서

        except Exception as e:
            logger.error(f"클리핑 트리거 이벤트 처리 실패: {e}")

    def save_clipping_data(self, clipping_data: Dict):
        """클리핑 데이터 저장"""
        try:
            # JSON 파일로 저장
            clipping_file = Path(f"clipping_data_{clipping_data['id']}.json")

            with open(clipping_file, "w", encoding="utf-8") as f:
                json.dump(clipping_data, f, ensure_ascii=False, indent=2)

            logger.info(f"클리핑 데이터 저장됨: {clipping_file}")

        except Exception as e:
            logger.error(f"클리핑 데이터 저장 실패: {e}")

    def start_monitoring(self):
        """모니터링 시작"""
        if self.monitoring:
            logger.warning("이미 모니터링 중입니다.")
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self.monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

        logger.info("옵시디언 모니터링 시작됨")

    def stop_monitoring(self):
        """모니터링 중지"""
        if not self.monitoring:
            logger.warning("모니터링이 실행되지 않고 있습니다.")
            return

        self.monitoring = False

        if self.monitor_thread:
            self.monitor_thread.join(timeout=5.0)

        logger.info("옵시디언 모니터링 중지됨")

    def get_latest_clipping_data(self) -> Optional[Dict]:
        """최신 클리핑 데이터 조회"""
        if not self.clipping_data:
            return None

        return self.clipping_data[-1]

    def get_clipping_statistics(self) -> Dict:
        """클리핑 통계 조회"""
        if not self.clipping_data:
            return {"total_clippings": 0, "average_change_amount": 0.0, "last_clipping_time": None}

        change_amounts = [data["change_amount"] for data in self.clipping_data]

        return {
            "total_clippings": len(self.clipping_data),
            "average_change_amount": sum(change_amounts) / len(change_amounts),
            "last_clipping_time": self.clipping_data[-1]["timestamp"],
            "detection_method": self.detection_method,
            "change_threshold": self.change_threshold,
        }


def main():
    """메인 실행 함수"""
    print("옵시디언 화면 모니터링 시스템")
    print("=" * 50)

    # 모니터 인스턴스 생성
    monitor = ObsidianScreenMonitor()

    try:
        # 모니터링 시작
        monitor.start_monitoring()

        print("모니터링 시작됨")
        print("실시간 통계:")

        # 상태 모니터링
        while True:
            time.sleep(10)  # 10초마다 통계 출력

            stats = monitor.get_clipping_statistics()
            print(f"\n클리핑 통계:")
            print(f"   총 클리핑: {stats['total_clippings']}개")
            print(f"   평균 변화량: {stats['average_change_amount']:.3f}")
            print(f"   마지막 클리핑: {stats['last_clipping_time']}")

            latest_clipping = monitor.get_latest_clipping_data()
            if latest_clipping:
                print(f"   최신 클리핑 ID: {latest_clipping['id']}")
                print(f"   변화량: {latest_clipping['change_amount']:.3f}")

    except KeyboardInterrupt:
        print("\n모니터링 중지 중...")
        monitor.stop_monitoring()
        print("모니터링 중지됨")

    except Exception as e:
        print(f"오류 발생: {e}")
        monitor.stop_monitoring()


if __name__ == "__main__":
    main()
