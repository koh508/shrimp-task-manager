"""
onew_shared.py — 온유 공유 상태
- 대화 중 백그라운드 출력 억제 (quiet period)
- 배경 모듈 오류 텔레그램 알림 (30분 중복 방지)
"""
import time, os, urllib.request, urllib.parse

_last_activity: float = 0.0
QUIET_WINDOW: int = 120  # 대화 후 이 시간(초) 동안 백그라운드 출력 억제

_is_syncing: bool = False  # 동기화 중 플래그


def set_syncing(value: bool):
    """동기화 시작/종료 시 호출"""
    global _is_syncing
    _is_syncing = value


def is_syncing() -> bool:
    """True면 동기화 중 → 배경 학습 대기"""
    return _is_syncing

_last_error_alert: dict = {}   # {module_name: last_alert_timestamp}
ERROR_ALERT_INTERVAL = 1800    # 같은 모듈 오류는 30분에 한 번만 알림


def touch():
    """사용자 입력 발생 시 호출 — 활동 시각 갱신"""
    global _last_activity
    _last_activity = time.time()


def is_quiet_period() -> bool:
    """True면 대화 중 → 백그라운드 스레드는 출력/작업 스킵"""
    return (time.time() - _last_activity) < QUIET_WINDOW


def report_error(module: str, error: str):
    """
    배경 모듈 오류 발생 시 호출.
    30분 내 같은 모듈 오류가 이미 알림됐으면 무시.
    """
    now = time.time()
    last = _last_error_alert.get(module, 0)
    if now - last < ERROR_ALERT_INTERVAL:
        return
    _last_error_alert[module] = now

    try:
        sys_dir = os.path.dirname(os.path.abspath(__file__))

        def _get_env(name):
            val = os.environ.get(name, '')
            if not val:
                try:
                    import winreg
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 'Environment')
                    val, _ = winreg.QueryValueEx(key, name)
                    winreg.CloseKey(key)
                except:
                    pass
            return val or ''

        token = _get_env('TELEGRAM_BOT_TOKEN')
        if not token:
            return
        ids_file = os.path.join(sys_dir, 'telegram_allowed_ids.json')
        import json
        with open(ids_file, 'r') as f:
            ids = json.load(f)
        if not ids:
            return

        msg = f"⚠️ *온유 배경 오류* — `{module}`\n\n`{str(error)[:300]}`\n\n다음 루프에서 자동 재시도합니다."
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode(
            {'chat_id': ids[0], 'text': msg, 'parse_mode': 'Markdown'}
        ).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
    except:
        pass
