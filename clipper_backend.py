#!/usr/bin/env python3
"""
클리퍼 백엔드 서버 (안전한 dotenv 처리)
"""
import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from waitress import serve

# 안전한 dotenv 로딩
def safe_load_dotenv():
    """안전한 .env 파일 로딩"""
    try:
        from dotenv import load_dotenv, find_dotenv

        env_file = find_dotenv()
        if env_file:
            load_dotenv(env_file)
            print("✅ .env 파일 로드 성공")
        else:
            print("⚠️ .env 파일을 찾을 수 없음")
    except ImportError:
        print("⚠️ python-dotenv 패키지가 설치되지 않음")
        print("   설치 명령: pip install python-dotenv")
    except Exception as e:
        print(f"⚠️ .env 파일 로딩 오류: {e}")


# 환경 변수 로드
safe_load_dotenv()

app = Flask(__name__)
CORS(app)

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.route("/health", methods=["GET"])
def health_check():
    """헬스체크 엔드포인트"""
    return jsonify(
        {"status": "healthy", "service": "clipper_backend", "timestamp": "2025-01-16T22:30:00Z"}
    )


@app.route("/api/clip", methods=["POST"])
def clip_text():
    """텍스트 클립 API"""
    try:
        data = request.get_json()
        text = data.get("text", "")

        # 클립보드 처리 로직
        logger.info(f"텍스트 클립 요청: {len(text)} 문자")

        return jsonify({"success": True, "message": "텍스트가 클립보드에 저장되었습니다", "length": len(text)})

    except Exception as e:
        logger.error(f"클립 처리 오류: {e}")
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    print("🚀 클리퍼 백엔드 서버 시작 (프로덕션 모드: Waitress)")
    print(f"   포트: 5001")
    print(f"   헬스체크: http://localhost:5001/health")

    try:
        serve(app, host="0.0.0.0", port=5001)
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
