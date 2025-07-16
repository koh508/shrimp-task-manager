from flask import Flask, jsonify
from waitress import serve # waitress 임포트

app = Flask(__name__)


@app.route("/")
def dashboard():
    return "<h1>System Dashboard</h1><p>Monitoring service status...</p>"


@app.route("/health")
def health_check():
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("🚀 단순 대시보드 서버 시작 (프로덕션 모드: Waitress)")
    print(f"   포트: 5000")
    print(f"   헬스체크: http://localhost:5000/health")
    serve(app, host="0.0.0.0", port=5000)
