"""
onew_budget.py — 일일 API 호출 예산 관리
- 배경 작업 호출만 카운트 (대화는 항상 허용)
- 80% 도달 시 텔레그램 경고
- 100% 도달 시 배경 작업 중단 + 텔레그램 알림
- /예산 명령으로 현황 확인
"""
import os, json, urllib.request, urllib.parse
from datetime import date
from pathlib import Path

SYSTEM_DIR  = os.path.dirname(os.path.abspath(__file__))
BUDGET_FILE = os.path.join(SYSTEM_DIR, 'api_budget.json')

# ── 기본 설정 (onew_config.json 있으면 오버라이드)
DEFAULT_DAILY_LIMIT = 1000  # 배경 작업 일일 호출 한도 (학습 파이프라인 보장)


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


def _load() -> dict:
    today = date.today().isoformat()
    if os.path.exists(BUDGET_FILE):
        try:
            with open(BUDGET_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data.get('date') == today:
                return data
        except:
            pass
    # 날짜 바뀌었거나 파일 없음 → 초기화
    return {'date': today, 'count': 0, 'limit': DEFAULT_DAILY_LIMIT,
            'alerted_80': False, 'alerted_100': False}


def _save(data: dict):
    with open(BUDGET_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def _send_telegram(msg: str):
    try:
        token = _get_env('TELEGRAM_BOT_TOKEN')
        if not token:
            return
        ids_file = os.path.join(SYSTEM_DIR, 'telegram_allowed_ids.json')
        with open(ids_file, 'r') as f:
            ids = json.load(f)
        if not ids:
            return
        url  = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode(
            {'chat_id': ids[0], 'text': msg, 'parse_mode': 'Markdown'}
        ).encode()
        urllib.request.urlopen(url, data=data, timeout=10)
    except:
        pass


def check_budget() -> bool:
    """
    배경 작업 실행 전 호출.
    True = 허용, False = 예산 초과 (작업 건너뜀)
    """
    data = _load()
    limit = data['limit']
    count = data['count']

    if count >= limit:
        if not data['alerted_100']:
            data['alerted_100'] = True
            _save(data)
            _send_telegram(
                f"🔴 *온유 API 예산 초과*\n\n"
                f"오늘 배경 작업 호출 {count}/{limit}회 도달.\n"
                f"배경 작업(클리핑·야간학습·현장연결 등)을 *일시 중단*합니다.\n"
                f"대화는 정상 이용 가능합니다.\n\n"
                f"한도 조정: `SYSTEM/api_budget.json` → limit 값 변경"
            )
        return False

    # 카운트 증가
    data['count'] = count + 1

    # 80% 경고
    if not data['alerted_80'] and data['count'] >= int(limit * 0.8):
        data['alerted_80'] = True
        _send_telegram(
            f"🟡 *온유 API 예산 80% 도달*\n\n"
            f"오늘 배경 작업 호출 {data['count']}/{limit}회.\n"
            f"계속 사용 시 {limit - data['count']}회 남았습니다."
        )

    _save(data)
    return True


def get_status() -> str:
    """현재 예산 현황 문자열 반환 (비용 추정 포함)"""
    data  = _load()
    count = data['count']
    limit = data['limit']
    pct   = int(count / limit * 100) if limit else 0
    bar   = '█' * (pct // 10) + '░' * (10 - pct // 10)
    status = "정상" if count < limit * 0.8 else ("주의" if count < limit else "초과")

    # 비용 추정 (Gemini 2.5 Flash 기준)
    # 배경 호출: 호출당 평균 2000 input + 1000 output 토큰 가정
    # 입력 $0.075/1M, 출력 $0.30/1M
    bg_cost   = count * (2000 * 0.075 + 1000 * 0.30) / 1_000_000
    # 월간 추정 (오늘 배경 호출 기준 × 30일)
    monthly   = bg_cost * 30

    return (
        f"📊 *API 예산 현황* ({data['date']})\n\n"
        f"`{bar}` {pct}%\n"
        f"배경 호출: {count} / {limit}회\n"
        f"상태: {status}\n\n"
        f"💰 오늘 배경 비용 추정: ${bg_cost:.4f}\n"
        f"📅 월간 추정 (배경만): ${monthly:.2f}\n"
        f"※ 대화 비용: 호출당 ~$0.0003 (500회/일 상한)"
    )


def set_limit(new_limit: int):
    """한도 변경"""
    data = _load()
    data['limit'] = new_limit
    _save(data)
