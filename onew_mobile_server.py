"""
온유 모바일 서버 (onew_mobile_server.py)
- Flask 웹서버 + pyngrok 터널링
- 스마트폰/태블릿 브라우저에서 온유에게 질문 가능
- 실행: python onew_mobile_server.py
"""
import sys
import os
import threading
import json

# obsidian_agent.py 경로 추가
SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)

from flask import Flask, request, jsonify, render_template_string

# ==============================================================================
# 모바일 UI HTML
# ==============================================================================
MOBILE_HTML = """<!DOCTYPE html>
<html lang="ko">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0">
  <meta name="apple-mobile-web-app-capable" content="yes">
  <title>온유 현장 AI</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, 'Malgun Gothic', sans-serif;
      background: #1a1a2e; color: #e0e0e0;
      height: 100dvh; display: flex; flex-direction: column;
    }
    #header {
      background: #16213e; padding: 12px 16px;
      display: flex; align-items: center; gap: 10px;
      border-bottom: 1px solid #0f3460; flex-shrink: 0;
    }
    #header h1 { font-size: 18px; color: #e94560; }
    #status { font-size: 11px; color: #7f8c8d; margin-left: auto; }
    #chat-container {
      flex: 1; overflow-y: auto; padding: 12px;
      display: flex; flex-direction: column; gap: 10px;
      -webkit-overflow-scrolling: touch;
    }
    .msg {
      max-width: 90%; padding: 10px 14px; border-radius: 16px;
      font-size: 15px; line-height: 1.6; word-break: break-word;
    }
    .msg.user { background: #0f3460; color: #e0e0e0; align-self: flex-end; border-bottom-right-radius: 4px; }
    .msg.onew {
      background: #16213e; color: #e0e0e0;
      align-self: flex-start; border-bottom-left-radius: 4px;
      border-left: 3px solid #e94560;
    }
    .msg.onew pre { background: #0d1117; padding: 8px; border-radius: 6px; overflow-x: auto; font-size: 13px; margin: 6px 0; }
    .msg.onew code { font-family: 'Courier New', monospace; font-size: 13px; }
    .msg.system { background: #0d2436; color: #7f8c8d; align-self: center; font-size: 12px; padding: 6px 12px; border-radius: 8px; }
    .msg img { max-width: 100%; border-radius: 8px; margin-top: 6px; display: block; }
    .typing { display: flex; align-items: center; gap: 4px; padding: 10px 14px;
      background: #16213e; border-radius: 16px; border-bottom-left-radius: 4px;
      align-self: flex-start; border-left: 3px solid #e94560; }
    .typing span { width: 8px; height: 8px; background: #e94560; border-radius: 50%; animation: bounce 1.2s infinite; }
    .typing span:nth-child(2) { animation-delay: 0.2s; }
    .typing span:nth-child(3) { animation-delay: 0.4s; }
    @keyframes bounce { 0%,60%,100%{transform:translateY(0)} 30%{transform:translateY(-6px)} }
    #input-area {
      background: #16213e; padding: 8px 12px;
      display: flex; flex-direction: column; gap: 6px;
      border-top: 1px solid #0f3460; flex-shrink: 0;
    }
    #input-row { display: flex; gap: 8px; align-items: flex-end; }
    #msg-input {
      flex: 1; background: #0f3460; border: none; border-radius: 20px;
      padding: 10px 16px; color: #e0e0e0; font-size: 16px;
      resize: none; outline: none; max-height: 100px; min-height: 44px;
      line-height: 1.4; font-family: inherit;
    }
    #msg-input::placeholder { color: #5d6d7e; }
    .icon-btn {
      background: #0f3460; border: none; border-radius: 50%;
      width: 44px; height: 44px; cursor: pointer; font-size: 20px;
      display: flex; align-items: center; justify-content: center;
      flex-shrink: 0; color: #e0e0e0; transition: opacity 0.2s;
    }
    .icon-btn:active { opacity: 0.6; }
    #send-btn { background: #e94560; }
    #send-btn:disabled { opacity: 0.4; cursor: not-allowed; }
    #preview-bar {
      display: none; align-items: center; gap: 8px;
      background: #0f3460; border-radius: 10px; padding: 6px 10px;
    }
    #preview-bar img { width: 48px; height: 48px; object-fit: cover; border-radius: 6px; }
    #preview-bar span { flex: 1; font-size: 12px; color: #aaa; }
    #preview-bar button { background: none; border: none; color: #e94560; font-size: 18px; cursor: pointer; }
    /* 카메라 모달 */
    #cam-modal {
      display: none; position: fixed; inset: 0;
      background: #000; flex-direction: column; z-index: 100;
    }
    #cam-modal.open { display: flex; }
    #cam-video { flex: 1; width: 100%; object-fit: cover; }
    #cam-controls {
      background: #111; padding: 16px;
      display: flex; justify-content: space-around; align-items: center;
    }
    #cam-controls button {
      background: none; border: none; color: #fff;
      font-size: 32px; cursor: pointer; padding: 8px;
    }
    #capture-btn {
      width: 64px; height: 64px; border-radius: 50% !important;
      background: #fff !important; color: #000 !important;
      font-size: 24px !important;
    }
    #cam-hint { font-size: 11px; color: #aaa; text-align: center; padding: 4px 0; }
  </style>
</head>
<body>
  <div id="header">
    <h1>온유</h1>
    <span id="status">연결 중...</span>
  </div>
  <div id="chat-container">
    <div class="msg system">현장 AI 온유 — 텍스트·카메라·사진 분석 가능</div>
  </div>
  <div id="input-area">
    <div id="preview-bar">
      <img id="preview-img" src="" alt="">
      <span id="preview-label">이미지 첨부됨</span>
      <button id="save-toggle" onclick="toggleSave()" title="Vault 저장 ON/OFF" style="background:#1a4a2e;border:none;border-radius:6px;padding:4px 8px;color:#4caf50;font-size:12px;cursor:pointer;">저장 ON</button>
      <button onclick="clearImage()">✕</button>
    </div>
    <div id="input-row">
      <button class="icon-btn" onclick="openCamera()" title="카메라">📷</button>
      <button class="icon-btn" onclick="document.getElementById('file-input').click()" title="갤러리">🖼</button>
      <textarea id="msg-input" placeholder="질문 입력 (이미지 첨부 후 질문 가능)..." rows="1"></textarea>
      <button class="icon-btn" id="send-btn" onclick="sendMsg()">➤</button>
    </div>
  </div>
  <input type="file" id="file-input" accept="image/*" style="display:none">

  <!-- 카메라 모달 -->
  <div id="cam-modal">
    <video id="cam-video" autoplay playsinline muted></video>
    <div id="cam-hint">탭하여 촬영 / 전·후면 전환 가능</div>
    <div id="cam-controls">
      <button onclick="closeCamera()" title="닫기">✕</button>
      <button id="capture-btn" onclick="capturePhoto()" title="촬영">◎</button>
      <button onclick="flipCamera()" title="전·후면 전환">🔄</button>
    </div>
  </div>
  <canvas id="snap-canvas" style="display:none"></canvas>

  <script>
    const chat = document.getElementById('chat-container');
    const input = document.getElementById('msg-input');
    const sendBtn = document.getElementById('send-btn');
    const status = document.getElementById('status');
    const previewBar = document.getElementById('preview-bar');
    const previewImg = document.getElementById('preview-img');

    let pendingImageB64 = null;  // 첨부된 이미지 base64
    let saveToVault = true;       // Vault 저장 여부
    let camStream = null;
    let camFacing = 'environment';  // 기본: 후면

    function toggleSave() {
      saveToVault = !saveToVault;
      const btn = document.getElementById('save-toggle');
      btn.textContent = saveToVault ? '저장 ON' : '저장 OFF';
      btn.style.color = saveToVault ? '#4caf50' : '#888';
      btn.style.background = saveToVault ? '#1a4a2e' : '#222';
    }

    fetch('/api/ping').then(r => r.json()).then(d => {
      status.textContent = d.mode === 'work' ? '시크릿' : '일반';
    }).catch(() => { status.textContent = '오류'; });

    input.addEventListener('input', function() {
      this.style.height = 'auto';
      this.style.height = Math.min(this.scrollHeight, 100) + 'px';
    });
    input.addEventListener('keydown', function(e) {
      if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
    });

    // 갤러리 파일 선택
    document.getElementById('file-input').addEventListener('change', function(e) {
      const file = e.target.files[0];
      if (!file) return;
      const reader = new FileReader();
      reader.onload = ev => setImage(ev.target.result);
      reader.readAsDataURL(file);
      this.value = '';
    });

    function setImage(dataUrl) {
      pendingImageB64 = dataUrl;
      previewImg.src = dataUrl;
      previewBar.style.display = 'flex';
      document.getElementById('preview-label').textContent = '이미지 첨부됨 (전송 시 분석)';
    }

    function clearImage() {
      pendingImageB64 = null;
      previewBar.style.display = 'none';
      previewImg.src = '';
    }

    // 카메라
    async function openCamera() {
      try {
        camStream = await navigator.mediaDevices.getUserMedia({
          video: { facingMode: camFacing }, audio: false
        });
        document.getElementById('cam-video').srcObject = camStream;
        document.getElementById('cam-modal').classList.add('open');
      } catch(e) {
        addMsg('카메라 접근 권한이 필요합니다: ' + e.message, 'system');
      }
    }

    function closeCamera() {
      if (camStream) { camStream.getTracks().forEach(t => t.stop()); camStream = null; }
      document.getElementById('cam-modal').classList.remove('open');
    }

    async function flipCamera() {
      camFacing = camFacing === 'environment' ? 'user' : 'environment';
      if (camStream) { camStream.getTracks().forEach(t => t.stop()); }
      camStream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: camFacing }, audio: false
      });
      document.getElementById('cam-video').srcObject = camStream;
    }

    function capturePhoto() {
      const video = document.getElementById('cam-video');
      const canvas = document.getElementById('snap-canvas');
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      canvas.getContext('2d').drawImage(video, 0, 0);
      const dataUrl = canvas.toDataURL('image/jpeg', 0.85);
      closeCamera();
      setImage(dataUrl);
    }

    function addMsg(text, role, imgSrc) {
      const d = document.createElement('div');
      d.className = 'msg ' + role;
      if (imgSrc) {
        const img = document.createElement('img');
        img.src = imgSrc;
        d.appendChild(img);
      }
      if (role === 'onew') {
        const span = document.createElement('span');
        span.innerHTML = formatText(text);
        d.appendChild(span);
      } else {
        if (text) d.appendChild(document.createTextNode(text));
      }
      chat.appendChild(d);
      chat.scrollTop = chat.scrollHeight;
    }

    function formatText(text) {
      return text
        .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
        .replace(/```([\\s\\S]*?)```/g, (m,c) => '<pre><code>'+c+'</code></pre>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\\*\\*(.*?)\\*\\*/g, '<strong>$1</strong>')
        .replace(/\\n/g, '<br>');
    }

    function showTyping() {
      const d = document.createElement('div');
      d.className = 'typing'; d.id = 'typing-indicator';
      d.innerHTML = '<span></span><span></span><span></span>';
      chat.appendChild(d); chat.scrollTop = chat.scrollHeight;
    }
    function hideTyping() { const t = document.getElementById('typing-indicator'); if(t) t.remove(); }

    async function sendMsg() {
      const text = input.value.trim();
      if ((!text && !pendingImageB64) || sendBtn.disabled) return;

      const imgToSend = pendingImageB64;
      addMsg(text || '(이미지 분석 요청)', 'user', imgToSend);
      input.value = ''; input.style.height = '44px';
      clearImage();
      sendBtn.disabled = true;
      showTyping();

      try {
        let res, data;
        if (imgToSend) {
          res = await fetch('/api/image', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ image: imgToSend, question: text, save: saveToVault })
          });
        } else {
          res = await fetch('/api/chat', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ message: text })
          });
        }
        data = await res.json();
        hideTyping();
        let replyText = data.reply || '응답 없음';
        if (data.saved_path) replyText += '\\n\\n💾 저장됨: ' + data.saved_path;
        addMsg(replyText, 'onew');
      } catch(e) {
        hideTyping();
        addMsg('서버 연결 오류', 'system');
      } finally {
        sendBtn.disabled = false;
      }
    }
  </script>
</body>
</html>
"""

# ==============================================================================
# Flask 앱 초기화
# ==============================================================================
app = Flask(__name__)
_agent = None
_lock = threading.Lock()


def get_agent():
    global _agent
    if _agent is None:
        print("온유 에이전트 초기화 중... (DB 로딩)")
        import obsidian_agent as _oa
        _agent = _oa.OnewAgent()
        # 도구 함수들이 globals()['onew']로 에이전트를 찾으므로 등록
        _oa.onew = _agent
        # 모바일 서버는 Cloudflare HTTPS로 보안되므로 시크릿 모드 비활성화
        # (WiFi 자동감지가 서버 환경에서 오작동하는 것 방지)
        _agent.location_mode = "home"
        print("온유 에이전트 준비 완료 (시크릿 모드 OFF)")
    return _agent


@app.route('/')
def index():
    return render_template_string(MOBILE_HTML)


@app.route('/api/ping')
def ping():
    try:
        agent = get_agent()
        return jsonify({'ok': True, 'mode': agent.location_mode})
    except Exception as e:
        return jsonify({'ok': False, 'mode': 'unknown', 'error': str(e)})


@app.route('/api/image', methods=['POST'])
def image_analyze():
    import base64, tempfile
    from datetime import datetime
    data = request.get_json(force=True, silent=True) or {}
    image_data = data.get('image', '')  # data:image/jpeg;base64,xxxx
    question = str(data.get('question', '')).strip()
    do_save = data.get('save', True)

    if not image_data:
        return jsonify({'reply': '이미지가 없습니다.'})

    try:
        # base64 디코딩
        if ',' in image_data:
            header, b64 = image_data.split(',', 1)
            ext = 'jpg' if 'jpeg' in header else 'png'
        else:
            b64, ext = image_data, 'jpg'
        img_bytes = base64.b64decode(b64)

        # 임시파일에 저장 후 분석
        with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
            tmp.write(img_bytes)
            tmp_path = tmp.name

        from onew_field_analyzer import analyze_field_image
        result = analyze_field_image(tmp_path, question, get_agent())
        reply = result['report']

        saved_path = None
        if do_save:
            now = datetime.now()
            month_str = now.strftime('%Y-%m')
            ts = now.strftime('%Y-%m-%d_%H-%M')

            # 저장 폴더 생성
            save_dir = os.path.join(_oa.OBSIDIAN_VAULT_PATH, '현장사진', month_str)
            os.makedirs(save_dir, exist_ok=True)

            # 이미지 파일 저장
            img_filename = f'{ts}_현장.{ext}'
            img_save_path = os.path.join(save_dir, img_filename)
            with open(img_save_path, 'wb') as f:
                f.write(img_bytes)

            # 마크다운 저장
            md_filename = f'{ts}_현장분석.md'
            md_save_path = os.path.join(save_dir, md_filename)
            question_line = f'\n## 질문\n{question}\n' if question else ''
            md_content = (
                f'---\n'
                f'tags: [현장, 이미지분석]\n'
                f'날짜: {now.strftime("%Y-%m-%d")}\n'
                f'시간: {now.strftime("%H:%M")}\n'
                f'상태: 완료\n'
                f'---\n\n'
                f'# {ts} 현장 이미지 분석\n'
                f'{question_line}\n'
                f'## 분석 결과\n'
                f'{reply}\n\n'
                f'## 원본 이미지\n'
                f'![[{img_filename}]]\n'
            )
            with open(md_save_path, 'w', encoding='utf-8') as f:
                f.write(md_content)

            saved_path = f'현장사진/{month_str}/{md_filename}'

        try:
            os.unlink(tmp_path)
        except:
            pass

        return jsonify({'reply': reply, 'saved_path': saved_path})

    except Exception as e:
        return jsonify({'reply': f'이미지 분석 오류: {e}'}), 500


@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.get_json(force=True, silent=True) or {}
    query = str(data.get('message', '')).strip()

    if not query:
        return jsonify({'reply': '질문을 입력해주세요.'})

    try:
        agent = get_agent()
        with _lock:
            prev_len = len(agent.history_records)
            agent.ask(query, silent_search=True)
            # ask() 이후 history_records의 마지막 model 메시지 추출
            if len(agent.history_records) > prev_len:
                reply = agent.history_records[-1].get('text', '응답 없음')
            else:
                # 시크릿 모드 등으로 응답 없는 경우
                reply = '이 주제는 집에서 이야기해요. (시크릿 모드)'

        return jsonify({'reply': reply})

    except Exception as e:
        error_msg = f'서버 오류: {str(e)}'
        print(f"❌ {error_msg}")
        return jsonify({'reply': error_msg}), 500


# ==============================================================================
# 메인 실행
# ==============================================================================
if __name__ == '__main__':
    PORT = 5757

    print("=" * 55)
    print("  🌿 온유 모바일 서버 시작")
    print("=" * 55)

    # 온유 에이전트 미리 로딩
    get_agent()

    # 로컬 IP 표시
    import socket
    local_ip = socket.gethostbyname(socket.gethostname())

    # 터널 시도 순서: ngrok(토큰 있을 때) → serveo.net(SSH, 무료)
    tunnel_ok = False

    # 1) ngrok: NGROK_AUTHTOKEN 환경변수 있을 때만 시도
    authtoken = os.environ.get('NGROK_AUTHTOKEN', '')
    if authtoken and not tunnel_ok:
        try:
            from pyngrok import ngrok, conf
            conf.get_default().auth_token = authtoken
            tunnel = ngrok.connect(PORT, 'http')
            print(f"\n{'='*55}")
            print(f"  [ngrok] 모바일 접속 URL:")
            print(f"  {tunnel.public_url}")
            print(f"{'='*55}\n")
            tunnel_ok = True
        except Exception as e:
            print(f"ngrok 실패: {e}")

    # 2) serveo.net: SSH 내장 (회원가입 불필요)
    if not tunnel_ok:
        import subprocess, re as _re, threading as _th
        CLOUDFLARED = os.path.join(SYSTEM_DIR, 'cloudflared.exe')
        try:
            cf_proc = subprocess.Popen(
                [CLOUDFLARED, 'tunnel', '--url', f'http://localhost:{PORT}'],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True, encoding='utf-8', errors='ignore'
            )
            url_found = []
            def _read_url():
                for line in cf_proc.stdout:
                    # URL 패턴: https://xxxx.trycloudflare.com
                    m = _re.search(r'https://[\w-]+\.trycloudflare\.com', line)
                    if m:
                        url_found.append(m.group())
                        break
                    # 계속 읽어서 프로세스가 살아있게 유지
            t = _th.Thread(target=_read_url, daemon=True)
            t.start()
            t.join(timeout=30)
            url_found = url_found[0] if url_found else ''
            if url_found:
                print(f"\n{'='*55}")
                print(f"  [Cloudflare] 모바일 접속 URL:")
                print(f"  {url_found}")
                print(f"{'='*55}")
                print(f"  위 주소를 스마트폰/태블릿 브라우저에서 여세요")
                print(f"  종료: Ctrl+C")
                print(f"{'='*55}\n")
                tunnel_ok = True
            else:
                cf_proc.terminate()
                raise RuntimeError("Cloudflare URL을 받지 못했습니다")
        except Exception as e:
            print(f"Cloudflare 터널 실패: {e}")

    if not tunnel_ok:
        print(f"\n{'='*55}")
        print(f"  외부 터널 연결 실패")
        print(f"  같은 WiFi에서: http://{local_ip}:{PORT}")
        print(f"  (폰과 PC가 같은 WiFi에 있으면 위 주소 사용 가능)")
        print(f"{'='*55}\n")

    # Flask 서버 실행 (스레드 비활성 = OnewAgent 스레드 안전)
    app.run(host='0.0.0.0', port=PORT, threaded=False, use_reloader=False)
