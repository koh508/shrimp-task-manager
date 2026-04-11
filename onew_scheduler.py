"""
onew_scheduler.py — 온유 내장 스케줄러 (APScheduler)
작업 스케줄러 없이 Python 프로세스 내에서 시간 기반 작업 실행
- 매주 일요일 03:00 Vault 백업
- 매일 00:05 API 예산 리셋 알림
- 매일 09:00 미복습 항목 알림
"""
import os, sys, threading, time, urllib.request, urllib.parse
from datetime import datetime
from pathlib import Path

# 에이전트 준비 완료 플래그 — start_background() 호출 후 READY_DELAY_SEC 뒤에 True
_agent_ready = False
READY_DELAY_SEC = 45  # 재부팅 직후 초기화·sync 완료 대기 시간

def _mark_ready():
    global _agent_ready
    time.sleep(READY_DELAY_SEC)
    _agent_ready = True

def _is_safe_to_run() -> bool:
    """sync 중이거나 에이전트 초기화 미완료면 False 반환."""
    if not _agent_ready:
        return False
    try:
        sys.path.insert(0, SYSTEM_DIR)
        import onew_shared
        return not onew_shared.is_syncing()
    except Exception:
        return True  # onew_shared 없으면 허용

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
VAULT_DIR  = Path(r"C:\Users\User\Documents\Obsidian Vault")


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


def _send_telegram(msg: str):
    try:
        token = _get_env('TELEGRAM_BOT_TOKEN')
        if not token:
            return
        import json
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


# ==============================================================================
# 스케줄 작업
# ==============================================================================
def job_weekly_backup():
    """매주 일요일 03:00 — Vault 백업"""
    if not _is_safe_to_run(): return
    try:
        import sys
        sys.path.insert(0, SYSTEM_DIR)
        from vault_backup import backup_vault
        print("\n📦 [스케줄러] 주간 Vault 백업 시작...")
        success = backup_vault()
        if success:
            _send_telegram("📦 *주간 Vault 백업 완료*\n`VaultBackups/` 폴더에 저장됐습니다.")
        else:
            _send_telegram("⚠️ *주간 Vault 백업 실패*\n`vault_backup.py` 확인 필요")
    except Exception as e:
        print(f"  ⚠️ [스케줄러] 백업 오류: {e}")
        _send_telegram(f"⚠️ 백업 오류: `{str(e)[:200]}`")


def job_budget_reset_notify():
    """매일 00:05 — 예산 초기화 알림 (어제 초과했을 경우)"""
    if not _is_safe_to_run(): return
    try:
        import json
        budget_file = os.path.join(SYSTEM_DIR, 'api_budget.json')
        if not os.path.exists(budget_file):
            return
        with open(budget_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        yesterday_count = data.get('count', 0)
        yesterday_limit = data.get('limit', 300)
        if yesterday_count >= int(yesterday_limit * 0.8):
            _send_telegram(
                f"📊 *어제 API 예산 현황*\n"
                f"배경 호출 {yesterday_count}/{yesterday_limit}회\n\n"
                f"오늘 예산이 초기화되었습니다."
            )
    except:
        pass


def job_evening_nudge():
    """평일 20:00 — 퇴근 후 저녁 학습 제안"""
    if not _is_safe_to_run(): return
    try:
        import json
        from datetime import date
        state_file = os.path.join(SYSTEM_DIR, 'adhd_coach_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                s = json.load(f)
            # 오늘 이미 충분히 했으면 패스
            if s.get('date') == date.today().isoformat() and s.get('questions_today', 0) >= 3:
                return
        _send_telegram(
            "🌙 *퇴근했어요?*\n\n"
            "오늘 하루 수고했어요.\n"
            "자기 전에 문제 3개만 풀어볼까요?\n\n"
            "*'공부 시작'* 이라고 말해주세요."
        )
    except Exception as e:
        print(f"  ⚠️ [스케줄러] 저녁 넛지 오류: {e}")


def job_study_nudge():
    """매일 09:00 — 공부 안 했으면 넛지"""
    if not _is_safe_to_run(): return
    try:
        import json
        from datetime import date, timedelta

        # 야간학습 마지막 세션 확인
        state_file = os.path.join(SYSTEM_DIR, 'night_study_state.json')
        last_session = ''
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                ns = json.load(f)
            last_session = ns.get('last_session', '')

        today = date.today().isoformat()
        yesterday = (date.today() - timedelta(days=1)).isoformat()

        if last_session and (today in last_session or yesterday in last_session):
            return  # 최근 학습했으면 패스

        # 복습 대상 확인
        db_file = os.path.join(SYSTEM_DIR, 'review_db.json')
        due_count = 0
        if os.path.exists(db_file):
            with open(db_file, 'r', encoding='utf-8') as f:
                db = json.load(f)
            due_count = sum(1 for e in db.values() if e.get('next_review', '9999') <= today)

        msg = f"☀️ *좋은 아침이에요, 용준씨*\n\n"
        if due_count > 0:
            msg += f"📚 오늘 복습할 항목 *{due_count}개* 있어요.\n"
        msg += "온유에게 '오늘 계획' 또는 '뭐 공부할까' 물어보세요."
        _send_telegram(msg)
    except Exception as e:
        print(f"  ⚠️ [스케줄러] 넛지 오류: {e}")


def job_health_check():
    """매일 12:00 — 시스템 상태 점검 후 이상 시 텔레그램 알림"""
    if not _is_safe_to_run(): return
    try:
        import json
        from datetime import datetime, timedelta, date
        issues = []
        today = date.today().isoformat()

        # 1. 야간학습 3일 이상 미실행
        state_file = os.path.join(SYSTEM_DIR, 'night_study_state.json')
        if os.path.exists(state_file):
            with open(state_file, 'r', encoding='utf-8') as f:
                ns = json.load(f)
            last = ns.get('last_session', '')
            if last:
                try:
                    last_dt = datetime.strptime(last[:10], '%Y-%m-%d')
                    days = (datetime.now() - last_dt).days
                    if days >= 3:
                        issues.append(f"🌙 야간학습 {days}일째 미실행")
                except: pass
            else:
                issues.append("🌙 야간학습 기록 없음")

        # 2. 오늘 클리핑 0건 (오후 12시 기준)
        usage_file = os.path.join(SYSTEM_DIR, 'api_usage_log.json')
        if os.path.exists(usage_file):
            with open(usage_file, 'r', encoding='utf-8') as f:
                usage = json.load(f)
            if usage.get(f'clip_{today}', 0) == 0:
                issues.append("📎 오늘 클리핑 0건")

        # 3. 최근 1시간 내 오류 로그
        error_file = os.path.join(SYSTEM_DIR, '온유_오류.md')
        if os.path.exists(error_file) and os.path.getsize(error_file) > 0:
            mtime = datetime.fromtimestamp(os.path.getmtime(error_file))
            if (datetime.now() - mtime).total_seconds() < 3600:
                issues.append("🔴 최근 1시간 내 오류 발생 (`SYSTEM/온유_오류.md` 확인)")

        # 4. 코드 백업 3일 이상 없음
        backup_base = r"C:\Users\User\AppData\Local\onew\code_backup"
        if os.path.exists(backup_base):
            dirs = sorted(os.listdir(backup_base), reverse=True)
            if dirs:
                try:
                    latest = datetime.strptime(dirs[0], '%Y-%m-%d')
                    if (datetime.now() - latest).days >= 3:
                        issues.append(f"💾 코드 백업 {(datetime.now()-latest).days}일째 없음")
                except: pass

        if issues:
            msg = "🔧 *온유 헬스체크 이상 감지*\n\n" + "\n".join(f"• {i}" for i in issues)
            _send_telegram(msg)
            print(f"  ⚠️ [헬스체크] 이상 {len(issues)}건 텔레그램 전송")
        else:
            print(f"  ✅ [헬스체크] 정상 ({today})")

    except Exception as e:
        print(f"  ⚠️ [헬스체크] 오류: {e}")


# ==============================================================================
# 시험 D-day 기반 집중 학습 잡
# ==============================================================================
EXAM_DATES = {
    "공조냉동": "2026-04-18",   # 공조냉동기계기사 실기
}

def job_exam_intensive():
    """시험 D-30 ~ D-1 기간 자동 감지 — 집중 학습 넛지 전송"""
    if not _is_safe_to_run(): return
    try:
        from datetime import date
        today = date.today()
        for exam_name, exam_date_str in EXAM_DATES.items():
            exam_date = date.fromisoformat(exam_date_str)
            days_left  = (exam_date - today).days
            if 0 < days_left <= 30:
                _send_telegram(
                    f"📅 *{exam_name} D-{days_left}*\n\n"
                    f"오늘도 실기 문제 3개 풀어봐요!\n"
                    f"온유에게 *'공조냉동 문제 내줘'* 라고 말해주세요."
                )
    except Exception as e:
        print(f"  ⚠️ [시험 넛지] 오류: {e}")


# ==============================================================================
# 스케줄러 시작
# ==============================================================================
def start_background():
    """APScheduler 백그라운드 스레드로 시작
    - SQLite persistent job store: PC가 꺼져 있다 켜져도 미실행 잡 자동 복구
    - misfire_grace_time=3600: 최대 1시간 내 미실행 잡 재실행
    - coalesce=True: 여러 번 밀린 같은 잡은 1회만 실행
    """
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore

        db_path = os.path.join(SYSTEM_DIR, 'onew_scheduler_jobs.db')
        scheduler = BackgroundScheduler(
            jobstores={'default': SQLAlchemyJobStore(url=f'sqlite:///{db_path}')},
            timezone='Asia/Seoul',
        )

        def _add(fn, trigger, job_id=None):
            scheduler.add_job(fn, trigger,
                              id=job_id or fn.__name__,
                              coalesce=True,
                              misfire_grace_time=3600,
                              max_instances=1,
                              replace_existing=True)

        # 매주 일요일 03:00 백업
        _add(job_weekly_backup,       CronTrigger(day_of_week='sun', hour=3, minute=0))
        # 매일 00:05 예산 리셋 알림
        _add(job_budget_reset_notify, CronTrigger(hour=0, minute=5))
        # 평일 06:00 공부 넛지
        _add(job_study_nudge,         CronTrigger(day_of_week='mon-fri', hour=6,  minute=0),
             job_id='job_study_nudge_weekday')
        # 주말 09:00 공부 넛지
        _add(job_study_nudge,         CronTrigger(day_of_week='sat,sun', hour=9,  minute=0),
             job_id='job_study_nudge_weekend')
        # 평일 저녁 20:00 퇴근 넛지
        _add(job_evening_nudge,       CronTrigger(day_of_week='mon-fri', hour=20, minute=0))
        # 매일 12:00 헬스체크
        _add(job_health_check,        CronTrigger(hour=12, minute=0))
        # 매일 08:00 시험 D-day 넛지 (D-30~D-1 구간만 실제 발송)
        _add(job_exam_intensive,      CronTrigger(hour=8, minute=0))

        scheduler.start()
        active = len(scheduler.get_jobs())
        print(f"⏰ [스케줄러] 시작 — {active}개 잡 등록 (misfire복구·coalesce·중복방지 활성)")
        # 초기화 완료 대기 후 잡 허용 (재부팅 직후 misfire 충돌 방지)
        threading.Thread(target=_mark_ready, daemon=True).start()
        return scheduler

    except Exception as e:
        print(f"  ⚠️ [스케줄러] 시작 실패: {e}")
        return None
