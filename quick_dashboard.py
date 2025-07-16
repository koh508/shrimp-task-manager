
import json
from datetime import datetime
from flask import Flask, jsonify

app = Flask(__name__)

@app.route('/')
def dashboard():
    return """
    🚀 통합 시스템 대시보드
    시스템 상태: 정상
    현재 시간: {}
    
        setInterval(() => {
            document.getElementById('time').textContent = new Date().toLocaleString();
        }, 1000);
    
    """.format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

@app.route('/api/status')
def status():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'uptime': '테스트 모드'
    })

if __name__ == '__main__':
    print("🌐 대시보드 시작: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
