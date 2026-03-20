"""
onew_self_improve.py — 온유 자율 코딩 엔진 v4.0

[전체 루프]
트리거 감지
  → 서킷 브레이커 확인 (블랙리스트 차단)
    → AST 정적 분석 (무한루프/미정의 변수 감지)
      → subprocess Dry-run (timeout 3s, 런타임 에러 감지)
        → 샌드박스 문법 검사
          → 롤링 윈도우로 컨텍스트 절약
            → PASS: 라이브 적용 / FAIL: 블랙리스트 카운터 +1
              → 자기진단 보고서 → 다음 날 proactive 반영 → 반복 성장
"""

import os, sys, json, shutil, subprocess, threading, time, re, tempfile, ast, difflib, hashlib
from datetime import datetime, date
from pathlib import Path

# ── 경로 ─────────────────────────────────────────────────────────────────────
SYSTEM_DIR      = os.path.dirname(os.path.abspath(__file__))
VAULT_PATH      = os.path.dirname(SYSTEM_DIR)
ERROR_LOG       = os.path.join(SYSTEM_DIR, "온유_오류.md")
IMPROVE_LOG     = os.path.join(SYSTEM_DIR, "onew_improve_log.json")
ANALYSIS_LOG    = os.path.join(SYSTEM_DIR, "onew_fix_analysis.json")
REASONING_LOG   = os.path.join(SYSTEM_DIR, "onew_reasoning_log.json")
BACKUP_DIR      = r"C:\Users\User\AppData\Local\onew\code_backup"
SELF_REVIEW_DIR = os.path.join(SYSTEM_DIR, "self_review")

# ── 신뢰 점수 기준 ────────────────────────────────────────────────────────────
HUMAN_APPROVAL_THRESHOLD = 60  # 60점 미만 → Human-in-the-loop 대기

# ── 화이트리스트 ──────────────────────────────────────────────────────────────
ALLOWED_FILES = [
    os.path.join(SYSTEM_DIR, "obsidian_agent.py"),
    os.path.join(SYSTEM_DIR, "onew_system_prompt.md"),
    os.path.join(SYSTEM_DIR, "onew_antipatterns.md"),
]

# ── 한도 ─────────────────────────────────────────────────────────────────────
MAX_DAILY_MODIFICATIONS = 5
MAX_DAILY_ROLLBACKS     = 2

# ── 트리거 키워드 ─────────────────────────────────────────────────────────────
TRIGGER_KEYWORDS = [
    "이상해", "버그", "오류", "틀렸어", "왜이래", "왜 이래",
    "고장", "안돼", "안 돼", "작동 안", "제대로 안", "망가",
]

# ── aider Python 경로 (모듈 로드 시 1회 고정, 문제 ③ 해결) ───────────────────
def _resolve_aider_python() -> list[str]:
    """py -3.12 실행 커맨드를 초기화 시 탐지해 고정."""
    for cmd in [["py", "-3.12"], ["python3.12"]]:
        try:
            r = subprocess.run(cmd + ["--version"], capture_output=True, timeout=5)
            if r.returncode == 0:
                return cmd
        except Exception:
            pass
    return ["py", "-3.12"]  # 기본값 (실패 시 FileNotFoundError로 fallback 진입)

AIDER_PYTHON_CMD = _resolve_aider_python()


# ==============================================================================
# [① 서킷 브레이커] CircuitBreaker — 파일별 연속 실패 감지 + 24h 블랙리스트
# ==============================================================================
class CircuitBreaker:
    """파일 단위로 연속 실패를 추적. 3연속 실패 시 24시간 블랙리스트."""

    BLACKLIST_FILE = os.path.join(SYSTEM_DIR, "onew_blacklist.json")
    FAIL_THRESHOLD = 3
    BAN_SECONDS    = 86400  # 24시간

    def _load(self) -> dict:
        if os.path.exists(self.BLACKLIST_FILE):
            try:
                with open(self.BLACKLIST_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {"blacklist": {}, "failures": {}}

    def _save(self, data: dict):
        with open(self.BLACKLIST_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def is_blacklisted(self, filepath: str) -> tuple[bool, str]:
        """(차단여부, 사유) 반환."""
        data = self._load()
        key  = os.path.abspath(filepath)
        ban_until = data["blacklist"].get(key, 0)
        if time.time() < ban_until:
            remaining = int((ban_until - time.time()) / 3600)
            return True, f"블랙리스트 — {remaining}시간 남음"
        # 만료된 항목 정리
        if key in data["blacklist"]:
            del data["blacklist"][key]
            data["failures"].pop(key, None)
            self._save(data)
        return False, ""

    def record_failure(self, filepath: str, reason: str = ""):
        data = self._load()
        key  = os.path.abspath(filepath)
        data.setdefault("failures", {})[key] = data["failures"].get(key, 0) + 1
        count = data["failures"][key]
        if count >= self.FAIL_THRESHOLD:
            data["blacklist"][key] = time.time() + self.BAN_SECONDS
            data["failures"][key]  = 0
            self._save(data)
            return f"⛔ {os.path.basename(filepath)} 블랙리스트 등록 (24h) — {count}연속 실패"
        self._save(data)
        return f"⚠️ 연속 실패 {count}/{self.FAIL_THRESHOLD}"

    def record_success(self, filepath: str):
        data = self._load()
        key  = os.path.abspath(filepath)
        data.setdefault("failures", {}).pop(key, None)
        self._save(data)

    # ── 해시 기반 실패 캐시 (무한 재시도 차단) ─────────────────────────────
    def _fix_hash(self, fix: dict) -> str:
        return hashlib.md5(
            json.dumps(fix, sort_keys=True, default=str).encode()
        ).hexdigest()

    def is_fix_duplicate(self, fix: dict) -> bool:
        """동일 fix JSON이 이전에 실패했으면 True."""
        h    = self._fix_hash(fix)
        data = self._load()
        return h in data.get("failed_hashes", {})

    def record_failed_hash(self, fix: dict):
        """실패 fix 해시 기록 (최대 100개, 오래된 것 자동 삭제)."""
        h      = self._fix_hash(fix)
        data   = self._load()
        hashes = data.setdefault("failed_hashes", {})
        hashes[h] = datetime.now().isoformat()
        if len(hashes) > 100:
            for k in sorted(hashes, key=hashes.get)[:20]:
                del hashes[k]
        self._save(data)


# ==============================================================================
# [사전 분석] NeedAnalyzer — 수정 필요성 검토 (문제 ①②: API 호출 전 필터)
# ==============================================================================
class NeedAnalyzer:
    """
    수정이 실제로 필요한지 API 호출 없이 사전 분석.
    95% 이상 불필요한 호출을 차단 → Gemini/aider 이중 호출 방지.
    """

    @staticmethod
    def should_fix(issue: str, file_content: str, filepath: str) -> tuple[bool, str]:
        """
        True  = 수정 진행
        False = 스킵 (사유 반환)
        """
        # 1. 이슈가 너무 짧거나 모호 (30자 미만)
        if len(issue.strip()) < 30:
            return False, f"이슈 너무 짧음 ({len(issue.strip())}자) — 구체성 부족"

        # 2. 파일 최근 수정 (5분 이내) — 방금 수정됐을 가능성
        try:
            if time.time() - os.path.getmtime(filepath) < 300:
                return False, "파일 최근 수정 (5분 이내) — 안정화 대기"
        except Exception:
            pass

        # 3. 이슈 키워드와 파일 내용 매칭률 (30% 미만 → 무관한 이슈)
        keywords = re.findall(r'[a-zA-Z_가-힣]{3,}', issue)
        if keywords:
            file_lower = file_content.lower()
            matched = sum(1 for kw in keywords if kw.lower() in file_lower)
            ratio = matched / len(keywords)
            if ratio < 0.3:
                return False, f"키워드 매칭 낮음 ({matched}/{len(keywords)}, {ratio:.0%})"

        # 4. 동일 이슈 최근 성공 수정 이력 확인 (FixAnalyzer 연동)
        if os.path.exists(ANALYSIS_LOG):
            try:
                with open(ANALYSIS_LOG, "r", encoding="utf-8") as f:
                    records = json.load(f)
                recent = records[-10:]
                issue_short = issue[:80].lower()
                for rec in recent:
                    if (rec.get("live_applied") and
                            rec.get("issue", "")[:80].lower() == issue_short):
                        return False, "동일 이슈 최근 수정 완료 — 재수정 불필요"
            except Exception:
                pass

        return True, "수정 필요"


# ==============================================================================
# [② AST 정적 분석] ASTChecker — 런타임 위험 코드 사전 탐지
# ==============================================================================
class ASTChecker:
    """py_compile이 잡지 못하는 논리 위험을 AST로 사전 탐지."""

    @staticmethod
    def check(code: str) -> list[str]:
        """위험 목록 반환. 빈 리스트 = 이상 없음."""
        risks = []
        if not code.strip():
            return risks
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return ["SyntaxError: AST 파싱 실패"]

        for node in ast.walk(tree):
            # 무한 루프: while True / while 1 (break 없음)
            if isinstance(node, (ast.While,)):
                test = node.test
                is_true = (
                    (isinstance(test, ast.Constant) and test.value) or
                    (isinstance(test, ast.NameConstant) and test.value)  # py<3.8
                )
                if is_true:
                    has_break = any(isinstance(n, ast.Break) for n in ast.walk(node))
                    if not has_break:
                        risks.append("위험: while True 무한 루프 (break 없음)")

            # 미정의 위험 패턴: eval/exec/os.system 직접 호출
            if isinstance(node, ast.Call):
                func = node.func
                name = ""
                if isinstance(func, ast.Name):
                    name = func.id
                elif isinstance(func, ast.Attribute):
                    name = func.attr
                if name in ("eval", "exec", "system", "__import__"):
                    risks.append(f"위험: {name}() 호출 감지")

        return risks


# ==============================================================================
# [안전망] SafetyGate
# ==============================================================================
class SafetyGate:

    @staticmethod
    def backup(filepath: str) -> str:
        try:
            ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
            day_dir = os.path.join(BACKUP_DIR, datetime.now().strftime("%Y-%m-%d"))
            os.makedirs(day_dir, exist_ok=True)
            dst = os.path.join(day_dir, f"{ts}_{os.path.basename(filepath)}")
            shutil.copy2(filepath, dst)
            return dst
        except Exception as e:
            return f"ERROR:{e}"

    @staticmethod
    def verify_syntax(filepath: str) -> tuple[bool, str]:
        if not filepath.endswith(".py"):
            return True, ""
        try:
            r = subprocess.run(
                [sys.executable, "-m", "py_compile", filepath],
                capture_output=True, text=True, timeout=15
            )
            return (True, "") if r.returncode == 0 else (False, r.stderr.strip())
        except Exception as e:
            return False, str(e)

    @staticmethod
    def rollback(filepath: str) -> bool:
        try:
            fname = os.path.basename(filepath)
            for day_dir in sorted(Path(BACKUP_DIR).iterdir(), reverse=True):
                if not day_dir.is_dir():
                    continue
                candidates = sorted(day_dir.glob(f"*_{fname}"), reverse=True)
                if candidates:
                    shutil.copy2(str(candidates[0]), filepath)
                    return True
                plain = day_dir / fname
                if plain.exists():
                    shutil.copy2(str(plain), filepath)
                    return True
        except:
            pass
        return False

    @staticmethod
    def is_allowed(filepath: str) -> bool:
        abs_path = os.path.abspath(filepath)
        if abs_path in [os.path.abspath(f) for f in ALLOWED_FILES]:
            return True
        skills_dir = os.path.abspath(os.path.join(SYSTEM_DIR, "skills"))
        return abs_path.startswith(skills_dir) and abs_path.endswith(".md")


# ==============================================================================
# [샌드박스 테스터] — 라이브에 영향 없이 코드 생성/검증
# ==============================================================================
class SandboxTester:
    """임시 복사본에 수정 적용 → 테스트 → 결과 반환. 라이브 파일 불변."""

    def run(self, filepath: str, fix: dict) -> tuple[bool, str]:
        """
        반환: (통과여부, 상세결과)
        통과 시에만 라이브에 적용하도록 apply_fix()에서 판단.
        """
        details = []
        sandbox_path = None
        try:
            # 1. 샌드박스 생성 (임시 파일)
            suffix = Path(filepath).suffix
            tmp = tempfile.NamedTemporaryFile(
                suffix=suffix, delete=False,
                dir=os.path.dirname(filepath),
                prefix="_sandbox_"
            )
            sandbox_path = tmp.name
            tmp.close()
            shutil.copy2(filepath, sandbox_path)
            details.append(f"샌드박스 생성: {os.path.basename(sandbox_path)}")

            # 2. 수정 적용 (라이브 아님)
            content = Path(sandbox_path).read_text(encoding="utf-8")
            ok, new_content = _apply_action(content, fix)
            if not ok:
                details.append("FAIL: 수정 대상 코드를 찾지 못함")
                return False, "\n".join(details)
            with open(sandbox_path, "w", encoding="utf-8") as f:
                f.write(new_content)
            details.append(f"액션 적용: {fix.get('action','?')} — {fix.get('desc','')}")

            # 3. 문법 검사
            gate = SafetyGate()
            syntax_ok, err = gate.verify_syntax(sandbox_path)
            if not syntax_ok:
                details.append(f"FAIL 문법 오류: {err[:150]}")
                return False, "\n".join(details)
            details.append("PASS 문법 검사")

            # 3-b. AST 정적 분석 (무한루프·위험 호출 감지)
            ast_risks = ASTChecker.check(new_content)
            if ast_risks:
                details.append(f"FAIL AST 위험: {' / '.join(ast_risks)}")
                return False, "\n".join(details)
            details.append("PASS AST 정적 분석")

            # 3-b.5 Ruff 린트 (import 누락·미정의 변수 — False Negative 보완)
            if sandbox_path.endswith(".py"):
                try:
                    result = subprocess.run(
                        [sys.executable, "-m", "ruff", "check", sandbox_path,
                         "--select=F401,F821,E9",
                         "--output-format=concise"],
                        capture_output=True, text=True, timeout=10
                    )
                    if result.returncode != 0:
                        err_out = (result.stdout or result.stderr)[:200]
                        details.append(f"FAIL Ruff: {err_out}")
                        return False, "\n".join(details)
                    details.append("PASS Ruff (import/변수 검사)")
                except FileNotFoundError:
                    details.append("Ruff 스킵: 미설치 (pip install ruff)")
                except Exception as e:
                    details.append(f"Ruff 스킵 (예외): {e}")

            # 3-c. Dry-run: 새로 추가된 코드만 격리 실행 (timeout 3s)
            new_code = ""
            action = fix.get("action", "")
            if action in ("append", "insert_after"):
                new_code = fix.get("code", "")
            elif action == "replace":
                new_code = fix.get("new", "")
            if new_code.strip() and sandbox_path.endswith(".py"):
                try:
                    dry_script = (
                        "import sys\n"
                        "sys.path.insert(0, '.')\n"
                        f"{new_code}\n"
                        "print('DRYRUN_OK')\n"
                    )
                    dry_tmp = tempfile.NamedTemporaryFile(
                        suffix=".py", delete=False, dir=os.path.dirname(sandbox_path),
                        prefix="_dryrun_"
                    )
                    dry_tmp.write(dry_script.encode("utf-8"))
                    dry_tmp.close()
                    result = subprocess.run(
                        [sys.executable, dry_tmp.name],
                        capture_output=True, text=True, timeout=3
                    )
                    os.remove(dry_tmp.name)
                    if "DRYRUN_OK" in result.stdout:
                        details.append("PASS Dry-run (3s 실행)")
                    else:
                        err_out = (result.stderr or result.stdout)[:150]
                        details.append(f"FAIL Dry-run: {err_out}")
                        return False, "\n".join(details)
                except subprocess.TimeoutExpired:
                    try: os.remove(dry_tmp.name)
                    except: pass
                    details.append("FAIL Dry-run: 3s 초과 (무한루프 의심)")
                    return False, "\n".join(details)
                except Exception as e:
                    details.append(f"Dry-run 스킵 (예외): {e}")
            else:
                details.append("Dry-run 스킵 (코드 없거나 .md 파일)")

            # 3-d. Pytest TDD 검증 (test_code 있을 때만)
            # --- 미래 확장 포인트 ---
            # SANDBOX_BACKEND = "pytest"  # 추후 "aider" | "docker" 로 교체 가능
            test_code = fix.get("test_code", "").strip()
            if test_code and sandbox_path.endswith(".py"):
                # test_code 품질 검사 (MCP 기만 탐지)
                quality_ok, quality_msg = _validate_test_code(test_code)
                if not quality_ok:
                    details.append(f"FAIL test_code 품질: {quality_msg}")
                    return False, "\n".join(details)
                pytest_path = None
                try:
                    pytest_tmp = tempfile.NamedTemporaryFile(
                        suffix=".py", delete=False,
                        dir=os.path.dirname(sandbox_path),
                        prefix="_pytest_"
                    )
                    pytest_path = pytest_tmp.name
                    pytest_tmp.write(test_code.encode("utf-8"))
                    pytest_tmp.close()
                    result = subprocess.run(
                        [sys.executable, "-m", "pytest", pytest_path,
                         "-v", "--tb=short", "--timeout=5", "-q"],
                        capture_output=True, text=True, timeout=15,
                        cwd=os.path.dirname(sandbox_path)
                    )
                    if result.returncode == 0:
                        passed_lines = [l for l in result.stdout.splitlines() if "passed" in l]
                        details.append(f"PASS Pytest: {passed_lines[-1] if passed_lines else 'OK'}")
                    else:
                        err_out = (result.stdout + result.stderr)[:300]
                        details.append(f"FAIL Pytest:\n{err_out}")
                        return False, "\n".join(details)
                except subprocess.TimeoutExpired:
                    details.append("FAIL Pytest: 15s 초과")
                    return False, "\n".join(details)
                except FileNotFoundError:
                    details.append("Pytest 스킵: pytest 미설치 (pip install pytest)")
                except Exception as e:
                    details.append(f"Pytest 스킵 (예외): {e}")
                finally:
                    if pytest_path and os.path.exists(pytest_path):
                        try: os.remove(pytest_path)
                        except: pass
            else:
                details.append("Pytest 스킵 (test_code 없거나 .md)")

            # 4. 변경 diff 요약 (라인 수 비교)
            orig_lines = Path(filepath).read_text(encoding="utf-8").count("\n")
            new_lines  = new_content.count("\n")
            details.append(f"라인 수 변화: {orig_lines} → {new_lines} ({new_lines - orig_lines:+d})")

            # 5. 새로 추가된 코드 스니펫 기록
            action = fix.get("action", "")
            if action == "append":
                details.append(f"추가된 코드:\n{fix.get('code','')[:200]}")
            elif action == "insert_after":
                details.append(f"삽입된 코드:\n{fix.get('code','')[:200]}")
            elif action == "replace":
                details.append(f"교체 전: {fix.get('old','')[:100]}")
                details.append(f"교체 후: {fix.get('new','')[:100]}")

            return True, "\n".join(details)

        except Exception as e:
            return False, f"샌드박스 예외: {e}"
        finally:
            # 샌드박스 항상 정리
            if sandbox_path and os.path.exists(sandbox_path):
                try:
                    os.remove(sandbox_path)
                except:
                    pass


# ==============================================================================
# [분석 저장소] FixAnalyzer — 성공/실패 패턴 누적
# ==============================================================================
class FixAnalyzer:
    """각 수정 시도 결과를 저장하고, 실패 패턴을 다음 시도에 피드백."""

    def _load(self) -> list:
        if os.path.exists(ANALYSIS_LOG):
            try:
                with open(ANALYSIS_LOG, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return []

    def _save(self, data: list):
        with open(ANALYSIS_LOG, "w", encoding="utf-8") as f:
            json.dump(data[-200:], f, ensure_ascii=False, indent=2)  # 최근 200건

    def record(self, issue: str, fix: dict, sandbox_ok: bool,
               sandbox_detail: str, live_applied: bool):
        data = self._load()
        data.append({
            "time":          datetime.now().strftime("%Y-%m-%d %H:%M"),
            "issue":         issue[:200],
            "action":        fix.get("action", "?"),
            "desc":          fix.get("desc", ""),
            "sandbox_pass":  sandbox_ok,
            "sandbox_detail": sandbox_detail[:300],
            "live_applied":  live_applied,
        })
        self._save(data)

    def get_failure_patterns(self, n: int = 10) -> str:
        """최근 N건 실패 사례 요약 → Gemini 컨텍스트로 활용."""
        data = self._load()
        failures = [d for d in data if not d["sandbox_pass"]][-n:]
        if not failures:
            return "최근 실패 없음"
        lines = ["[최근 실패 패턴]"]
        for f in failures:
            lines.append(
                f"- [{f['time']}] {f['action']} / {f['desc']}\n"
                f"  원인: {f['sandbox_detail'][:100]}"
            )
        return "\n".join(lines)

    def get_success_rate(self) -> str:
        data = self._load()
        if not data:
            return "데이터 없음"
        total   = len(data)
        passed  = sum(1 for d in data if d["sandbox_pass"])
        applied = sum(1 for d in data if d["live_applied"])
        return (f"전체 {total}건 | 샌드박스 통과 {passed}건 ({passed*100//total}%)"
                f" | 실제 적용 {applied}건")

    def get_recent_summary(self, n: int = 5) -> str:
        data = self._load()[-n:]
        if not data:
            return "이력 없음"
        lines = []
        for d in data:
            icon = "✅" if d["live_applied"] else ("⚠️" if d["sandbox_pass"] else "❌")
            lines.append(f"{icon} [{d['time']}] {d['action']}: {d['desc']}")
        return "\n".join(lines)

    # ── Reasoning Log ─────────────────────────────────────────────────────────
    def record_reasoning(self, issue: str, fix: dict, confidence: int,
                         gates_passed: list, apply_method: str, result: str,
                         human_approved: bool = False):
        """
        추론 로그 저장 — 왜 이 수정을 했는가.
        result: "live_applied" | "rollback" | "pending_approval" | "fail"
        """
        try:
            data = []
            if os.path.exists(REASONING_LOG):
                with open(REASONING_LOG, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except Exception:
            data = []

        data.append({
            "time":           datetime.now().strftime("%Y-%m-%d %H:%M"),
            "issue":          issue[:200],
            "action":         fix.get("action", "?"),
            "desc":           fix.get("desc", ""),
            "confidence":     confidence,
            "gates_passed":   gates_passed,
            "apply_method":   apply_method,
            "human_approved": human_approved,
            "result":         result,
        })
        with open(REASONING_LOG, "w", encoding="utf-8") as f:
            json.dump(data[-200:], f, ensure_ascii=False, indent=2)


# ==============================================================================
# [개선 이력] ImprovementLog
# ==============================================================================
class ImprovementLog:

    def _load(self) -> dict:
        if os.path.exists(IMPROVE_LOG):
            try:
                with open(IMPROVE_LOG, "r", encoding="utf-8") as f:
                    return json.load(f)
            except:
                pass
        return {}

    def _save(self, data: dict):
        with open(IMPROVE_LOG, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def today_key(self) -> str:
        return date.today().isoformat()

    def get_today(self) -> dict:
        return self._load().get(self.today_key(),
                                {"modifications": 0, "rollbacks": 0, "history": []})

    def can_modify(self) -> bool:
        t = self.get_today()
        return (t["modifications"] < MAX_DAILY_MODIFICATIONS and
                t["rollbacks"] < MAX_DAILY_ROLLBACKS)

    def record_modification(self, filepath: str, description: str, success: bool):
        data = self._load()
        key = self.today_key()
        if key not in data:
            data[key] = {"modifications": 0, "rollbacks": 0, "history": []}
        data[key]["modifications"] += 1
        data[key]["history"].append({
            "time": datetime.now().strftime("%H:%M"),
            "file": os.path.basename(filepath),
            "desc": description, "success": success,
        })
        self._save(data)

    def record_rollback(self, filepath: str, reason: str):
        data = self._load()
        key = self.today_key()
        if key not in data:
            data[key] = {"modifications": 0, "rollbacks": 0, "history": []}
        data[key]["rollbacks"] += 1
        data[key]["history"].append({
            "time": datetime.now().strftime("%H:%M"),
            "file": os.path.basename(filepath),
            "desc": f"[롤백] {reason}", "success": False,
        })
        self._save(data)

    def today_summary(self) -> str:
        t = self.get_today()
        lines = [f"수정 {t['modifications']}/{MAX_DAILY_MODIFICATIONS}회, "
                 f"롤백 {t['rollbacks']}/{MAX_DAILY_ROLLBACKS}회"]
        for h in t.get("history", [])[-5:]:
            icon = "✅" if h["success"] else "❌"
            lines.append(f"  {icon} [{h['time']}] {h['file']}: {h['desc']}")
        return "\n".join(lines)

    def recent_history(self, days: int = 7) -> str:
        data = self._load()
        lines = []
        for key in sorted(data.keys())[-days:]:
            d = data[key]
            lines.append(f"[{key}] 수정 {d['modifications']}회, 롤백 {d['rollbacks']}회")
            for h in d.get("history", []):
                icon = "✅" if h["success"] else "❌"
                lines.append(f"  {icon} {h['file']}: {h['desc']}")
        return "\n".join(lines) if lines else "이력 없음"


# ==============================================================================
# [git 정리 에이전트] GitCleanupAgent — 문제 ⑥ 해결
# ==============================================================================
class GitCleanupAgent:
    """
    git working tree 상태를 정리.
    - 문법 OK 수정 파일 → 커밋
    - 문법 오류 파일 → backup 롤백 + git checkout
    - apply_fix 성공/실패 후 자동 호출
    """

    @staticmethod
    def run() -> str:
        try:
            r = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=SYSTEM_DIR, timeout=10
            )
            lines = r.stdout.strip().splitlines()
            if not lines:
                return "git clean"

            report = []
            for line in lines:
                status = line[:2].strip()
                fname  = line[3:].strip()
                fpath  = os.path.join(SYSTEM_DIR, fname)

                if not os.path.exists(fpath):
                    continue

                if status in ("M", "A", "AM", "MM"):
                    ok, err = SafetyGate.verify_syntax(fpath)
                    if ok:
                        subprocess.run(["git", "add", fname],
                                       capture_output=True, cwd=SYSTEM_DIR)
                        subprocess.run(
                            ["git", "commit", "-m", f"auto[onew]: {fname}"],
                            capture_output=True, cwd=SYSTEM_DIR
                        )
                        report.append(f"✅ 커밋: {fname}")
                    else:
                        SafetyGate.rollback(fpath)
                        subprocess.run(["git", "checkout", "--", fname],
                                       capture_output=True, cwd=SYSTEM_DIR)
                        report.append(f"🔄 롤백+복구: {fname} (문법 오류)")
                elif status == "??":
                    # untracked — 온유 시스템 파일이면 add만 (커밋은 보류)
                    if fname.endswith((".py", ".md", ".json")):
                        subprocess.run(["git", "add", fname],
                                       capture_output=True, cwd=SYSTEM_DIR)
                        report.append(f"📎 tracked 등록: {fname}")

            return "\n".join(report) if report else "정리 완료"
        except Exception as e:
            return f"git 정리 오류: {e}"


# ==============================================================================
# [Safe Point + Update Lock] — 핫 업데이트 크래시 방지
# ==============================================================================
# _UPDATE_LOCK: apply_fix() 동시 진입 차단 (단일 스레드만 라이브 적용 허용)
_UPDATE_LOCK = threading.Lock()
_PID_FILE    = os.path.join(SYSTEM_DIR, "onew.pid")


def _get_agent_pid() -> int | None:
    """obsidian_agent.py 프로세스 PID 반환. 없으면 None."""
    if not os.path.exists(_PID_FILE):
        return None
    try:
        with open(_PID_FILE, "r") as f:
            return int(f.read().strip())
    except Exception:
        return None


def _wait_for_safe_point(timeout: int = 30) -> bool:
    """
    obsidian_agent 프로세스가 유휴(CPU < 5%)가 될 때까지 대기.

    - psutil 없거나 PID 파일 없으면 즉시 통과 (하위 호환)
    - timeout 초 초과 시에도 통과 (무한 대기 방지)
    - 반환: True = 안전 시점 확인 / False = 타임아웃 후 강제 진행
    """
    try:
        import psutil
        pid = _get_agent_pid()
        if pid is None:
            return True
        proc = psutil.Process(pid)
        deadline = time.time() + timeout
        while time.time() < deadline:
            cpu = proc.cpu_percent(interval=1.0)
            if cpu < 5.0:
                return True
            time.sleep(0.5)
        return False  # 타임아웃 — 강제 진행
    except Exception:
        return True  # psutil 없거나 프로세스 종료 → 바로 진행


# ==============================================================================
# [공용 유틸]
# ==============================================================================
def _extract_file_structure(content: str, filepath: str) -> str:
    if not filepath.endswith(".py"):
        return content[:2000]
    lines = content.splitlines()
    structure = []
    for i, line in enumerate(lines, 1):
        s = line.strip()
        if s.startswith(("class ", "def ", "async def ")):
            indent = len(line) - len(line.lstrip())
            structure.append(f"L{i:04d} {'  '*(indent//4)}{s.split(':')[0]}")
    return f"[파일 구조]\n{chr(10).join(structure[:80])}\n\n[파일 앞부분]\n{content[:1500]}"


def _validate_test_code(test_code: str) -> tuple[bool, str]:
    """
    test_code 품질 검사 — MCP 기만(return True 하드코딩) 탐지.
    최소 조건: assert 1개 이상 + trivial assert 없음.
    """
    try:
        tree = ast.parse(test_code)
    except SyntaxError as e:
        return False, f"test_code 문법 오류: {e}"

    asserts = [n for n in ast.walk(tree) if isinstance(n, ast.Assert)]
    if not asserts:
        return False, "assert 없음 — 테스트 무효"

    for a in asserts:
        # assert True / assert 1 / assert "ok" 같은 trivial 탐지
        if isinstance(a.test, ast.Constant) and bool(a.test.value):
            return False, "assert True 하드코딩 탐지 — 의미 없는 테스트"
        # assert func() 만 있고 비교 없는 경우 경고 (FAIL 아님, 로그만)

    return True, "OK"


def _make_diff(original: str, modified: str, filename: str) -> str:
    """unified diff 생성 (aider --apply 에 전달용)."""
    return "".join(difflib.unified_diff(
        original.splitlines(keepends=True),
        modified.splitlines(keepends=True),
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))


def _apply_action(content: str, fix: dict) -> tuple[bool, str]:
    action = fix.get("action", "skip")
    if action == "replace":
        old, new = fix.get("old", ""), fix.get("new", "")
        if not old or old not in content:
            return False, content
        return True, content.replace(old, new, 1)
    elif action == "insert_after":
        anchor, code = fix.get("anchor", ""), fix.get("code", "")
        if not anchor or anchor not in content:
            return False, content
        idx = content.index(anchor) + len(anchor)
        nl = content.find("\n", idx)
        insert_at = nl + 1 if nl != -1 else len(content)
        return True, content[:insert_at] + "\n" + code + "\n" + content[insert_at:]
    elif action == "append":
        code = fix.get("code", "")
        if not code:
            return False, content
        return True, content.rstrip() + "\n\n" + code + "\n"
    return False, content


# ==============================================================================
# [자율 개선 엔진] SelfImproveEngine
# ==============================================================================
class SelfImproveEngine:

    def __init__(self):
        self.gate     = SafetyGate()
        self.log      = ImprovementLog()
        self.analyzer = FixAnalyzer()
        self.sandbox  = SandboxTester()
        self.breaker  = CircuitBreaker()
        self._lock    = threading.Lock()
        self._last_error_mtime = 0.0
        self._pending_issues: list[str] = []

    # ── Gemini 호출 ───────────────────────────────────────────────────────────
    def _call_gemini(self, prompt: str) -> str:
        from google import genai
        from google.genai import types
        api_key = os.environ.get("GEMINI_API_KEY", "")
        if not api_key:
            return ""
        client = genai.Client(api_key=api_key)
        res = client.models.generate_content(
            model="gemini-2.5-flash", contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0))
        )
        return res.text.strip()

    # ── 수정안 생성 (③ 롤링 윈도우 적용) ────────────────────────────────────
    def _generate_fix(self, issue: str, file_content: str, filepath: str) -> dict:
        context = _extract_file_structure(file_content, filepath)

        # 롤링 윈도우: 최근 5건만 (토큰 절약)
        failure_patterns = self.analyzer.get_failure_patterns(n=5)

        # 프롬프트 각 섹션 길이 제한
        issue_trimmed   = issue[:300]
        context_trimmed = context[:1500]
        failure_trimmed = failure_patterns[:500]

        try:
            prompt = (
                f"온유 코드 개선 요청:\n{issue_trimmed}\n\n"
                f"파일: {os.path.basename(filepath)}\n{context_trimmed}\n\n"
                f"최근 실패 패턴 (반드시 피할 것):\n{failure_trimmed}\n\n"
                "수정안을 JSON 1개만 출력하라 (설명 없이).\n"
                "반드시 test_code 필드를 포함하라 — 수정/추가한 코드가 올바르게 동작하는지\n"
                "검증하는 완전 독립적인 pytest 함수(def test_...():)를 작성하라.\n"
                "test_code는 import 없이 동작해야 하며, 테스트할 함수 정의도 함께 포함하라.\n\n"
                'replace: {"action":"replace","old":"기존코드","new":"새코드","desc":"설명",'
                '"test_code":"def test_fix():\\n    # 새코드 로직 직접 포함 후 assert"}\n'
                'append:  {"action":"append","code":"추가코드","desc":"설명",'
                '"test_code":"def test_new():\\n    # 추가코드 함수 정의 포함 후 assert"}\n'
                'insert_after: {"action":"insert_after","anchor":"기준줄","code":"삽입코드","desc":"설명",'
                '"test_code":"def test_inserted():\\n    assert ..."}\n'
                'skip: {"action":"skip","desc":"이유","test_code":""}'
            )
            text = self._call_gemini(prompt)
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if m:
                return json.loads(m.group())
        except:
            pass
        return {"action": "skip", "desc": "파싱 실패", "test_code": ""}

    # ── 신뢰 점수 계산 ───────────────────────────────────────────────────────
    def _score_fix(self, fix: dict, sandbox_detail: str, filepath: str) -> tuple[int, list]:
        """
        수정안 신뢰 점수 (0~100) + 통과 게이트 목록 반환.
        HUMAN_APPROVAL_THRESHOLD(60) 미만 → Human-in-the-loop.
        """
        score = 100
        gates = ["PASS 문법", "PASS AST", "PASS Ruff", "PASS Dry-run", "PASS Pytest"]
        passed_gates = [g for g in gates if g in sandbox_detail]

        # 연속 실패 이력 감점
        fail_count = self.breaker._load().get("failures", {}).get(
            os.path.abspath(filepath), 0)
        score -= fail_count * 15

        # critical 파일 감점
        cf_path = os.path.join(SYSTEM_DIR, "critical_functions.json")
        if os.path.exists(cf_path):
            try:
                with open(cf_path, encoding="utf-8") as f:
                    cf = json.load(f)
                # strict 함수가 정의된 파일이면 감점 (파일명 기준 rough 매칭)
                fname = os.path.basename(filepath).replace(".py", "")
                has_strict = any(
                    v.get("strict") for k, v in cf.items()
                    if isinstance(v, dict) and fname in k
                )
                if has_strict:
                    score -= 10
            except Exception:
                pass

        # 변경 규모 감점
        change_size = len(fix.get("old", "") + fix.get("code", "") + fix.get("new", ""))
        if change_size > 500:
            score -= 20
        elif change_size > 200:
            score -= 10

        # aider 실패 → 수동 폴백 사용 시 감점
        if "수동폴백" in sandbox_detail or "aider 오류" in sandbox_detail:
            score -= 10

        # 통과 게이트 수 반영 (5개 미만 시 감점)
        if len(passed_gates) < 3:
            score -= (3 - len(passed_gates)) * 10

        return max(0, min(100, score)), passed_gates

    # ── aider 라이브 적용 (--apply diff, LLM 호출 없음) ─────────────────────
    def _apply_via_aider(self, filepath: str, fix: dict,
                         original_content: str) -> tuple[bool, str]:
        """
        샌드박스에서 검증된 diff를 aider --apply 로 적용.
        LLM 2차 호출 없음 (문제 ② 해결).
        untracked 파일 자동 git add (문제 ⑤ 해결).
        AIDER_PYTHON_CMD 로 경로 고정 (문제 ③ 해결).
        """
        # 1. diff 생성 (sandbox와 동일한 _apply_action 결과)
        ok, new_content = _apply_action(original_content, fix)
        if not ok:
            return False, "diff 생성 실패: 대상 코드 없음"
        diff_text = _make_diff(original_content, new_content, os.path.basename(filepath))
        if not diff_text.strip():
            return False, "diff 없음 (변경 사항 없음)"

        # 2. untracked 파일 git add (문제 ⑤)
        try:
            tr = subprocess.run(
                ["git", "ls-files", "--error-unmatch", os.path.basename(filepath)],
                capture_output=True, cwd=SYSTEM_DIR, timeout=5
            )
            if tr.returncode != 0:
                subprocess.run(["git", "add", os.path.basename(filepath)],
                               capture_output=True, cwd=SYSTEM_DIR, timeout=5)
        except Exception:
            pass  # git 없어도 계속 진행

        # 3. diff 임시 파일 → aider --apply
        diff_tmp = None
        try:
            diff_tmp = tempfile.NamedTemporaryFile(
                suffix=".diff", delete=False, dir=SYSTEM_DIR, prefix="_aider_diff_"
            )
            diff_tmp.write(diff_text.encode("utf-8"))
            diff_tmp.close()

            result = subprocess.run(
                AIDER_PYTHON_CMD + ["-m", "aider",
                 "--apply", diff_tmp.name,
                 "--yes",
                 "--no-auto-commits",
                 os.path.basename(filepath)],
                capture_output=True, text=True, timeout=30,
                cwd=SYSTEM_DIR,
            )
            if result.returncode == 0:
                return True, "aider --apply 성공 (LLM 호출 없음)"
            else:
                err = (result.stderr or result.stdout)[:300]
                return False, f"aider 오류: {err}"
        except subprocess.TimeoutExpired:
            return False, "aider 30s 타임아웃"
        except FileNotFoundError:
            return False, f"aider 미설치 또는 {AIDER_PYTHON_CMD} 없음"
        except Exception as e:
            return False, f"aider 호출 예외: {e}"
        finally:
            if diff_tmp and os.path.exists(diff_tmp.name):
                try: os.remove(diff_tmp.name)
                except: pass

    # ── 핵심 루프: 서킷 브레이커 → 샌드박스 → 분석 → 라이브 ────────────────
    def apply_fix(self, filepath: str, issue: str) -> str:
        with self._lock:
            if not self.log.can_modify():
                return "⛔ 오늘 수정 한도 초과"
            if not self.gate.is_allowed(filepath):
                return f"⛔ 수정 불허: {os.path.basename(filepath)}"
            # ① 서킷 브레이커 확인
            banned, reason = self.breaker.is_blacklisted(filepath)
            if banned:
                return f"⛔ {reason}"
            try:
                content = Path(filepath).read_text(encoding="utf-8")
            except Exception as e:
                return f"❌ 읽기 실패: {e}"

            # 0. 수정 필요성 사전 분석 (문제 ①② — API 호출 전 필터)
            needed, reason = NeedAnalyzer.should_fix(issue, content, filepath)
            if not needed:
                return f"💡 분석 스킵: {reason}"

            # 1. 수정안 생성
            fix    = self._generate_fix(issue, content, filepath)
            action = fix.get("action", "skip")
            desc   = fix.get("desc", "")
            if action == "skip":
                return f"💡 스킵: {desc}"

            # 1-b. 해시 중복 차단 (동일 실패 fix 무한 재시도 방지)
            if self.breaker.is_fix_duplicate(fix):
                return "⛔ 동일 수정안 이전 실패 이력 — 재시도 차단 (해시 캐시)"

            # 2. 샌드박스 테스트 (라이브 불변)
            sandbox_ok, sandbox_detail = self.sandbox.run(filepath, fix)

            # 3. 분석 기록 (통과/실패 모두 저장)
            self.analyzer.record(issue, fix, sandbox_ok, sandbox_detail,
                                 live_applied=False)

            if not sandbox_ok:
                bl_msg = self.breaker.record_failure(filepath, sandbox_detail[:80])
                self.breaker.record_failed_hash(fix)  # 해시 캐시 등록
                self._notify(
                    f"⚠️ [자율코딩] 샌드박스 FAIL\n"
                    f"파일: {os.path.basename(filepath)}\n"
                    f"내용: {desc}\n상세: {sandbox_detail[:150]}\n{bl_msg}"
                )
                return f"❌ 샌드박스 FAIL\n{sandbox_detail}\n{bl_msg}"

            # 3-b. Confidence Score + Human-in-the-loop
            confidence, gates_passed = self._score_fix(fix, sandbox_detail, filepath)
            if confidence < HUMAN_APPROVAL_THRESHOLD:
                self.analyzer.record_reasoning(
                    issue, fix, confidence, gates_passed, "pending", "pending_approval")
                self._notify(
                    f"🤔 [Human-loop] 신뢰 점수 {confidence}/100\n"
                    f"파일: {os.path.basename(filepath)}\n"
                    f"수정: {desc}\n기준: {HUMAN_APPROVAL_THRESHOLD}점 미달"
                )
                return (f"⏸ 신뢰 점수 {confidence}/100 — Human 승인 대기\n"
                        f"(기준: {HUMAN_APPROVAL_THRESHOLD}, 게이트: {gates_passed})")

            # 4. Safe Point 대기 (메인 루프 유휴 상태 확인)
            safe = _wait_for_safe_point(timeout=30)
            if not safe:
                self._notify(f"⚠️ [Safe Point] 30s 대기 후 강제 진행: {os.path.basename(filepath)}")

            # 5. Update Lock — 동시 apply_fix() 충돌 방지 (단일 스레드만 진입)
            if not _UPDATE_LOCK.acquire(blocking=False):
                return "⏳ 다른 apply_fix() 실행 중 — 이번 수정 건너뜀"
            try:
                # 5a. 라이브 적용 (백업 → aider → 원자적 수동폴백)
                backup_path = self.gate.backup(filepath)
                if backup_path.startswith("ERROR"):
                    return f"❌ 백업 실패: {backup_path}"

                aider_ok, aider_detail = self._apply_via_aider(filepath, fix, content)
                apply_method = "aider"
                if not aider_ok:
                    # 원자적 수동 폴백 (os.replace — 중간 실패 시 파일 보호)
                    apply_ok, new_content = _apply_action(content, fix)
                    if not apply_ok:
                        return f"❌ 라이브 적용 실패 (aider: {aider_detail})"
                    tmp_path = filepath + ".tmp"
                    with open(tmp_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    os.replace(tmp_path, filepath)  # 원자적 교체
                    apply_method = f"수동폴백 (aider: {aider_detail[:60]})"

                syntax_ok, err = self.gate.verify_syntax(filepath)
                if not syntax_ok:
                    rolled = self.gate.rollback(filepath)
                    self.log.record_rollback(filepath, err[:80])
                    bl_msg = self.breaker.record_failure(filepath, err[:80])
                    self.breaker.record_failed_hash(fix)
                    self.analyzer.record_reasoning(
                        issue, fix, confidence, gates_passed, apply_method, "rollback")
                    self._notify(f"⚠️ [자율코딩] 라이브 문법 오류 → 롤백\n{err[:80]}\n{bl_msg}")
                    return f"❌ 라이브 문법 오류 → 롤백 {'성공' if rolled else '실패'}"

                # 5b. 인터페이스 계약 검증
                try:
                    from onew_contract import verify as _contract_verify
                    violations = _contract_verify(filepath)
                    if violations:
                        rolled = self.gate.rollback(filepath)
                        self.log.record_rollback(filepath, "인터페이스 계약 위반")
                        self.breaker.record_failed_hash(fix)
                        self.analyzer.record_reasoning(
                            issue, fix, confidence, gates_passed, apply_method, "rollback")
                        self._notify(f"⛔ [계약 위반] 롤백\n" + "\n".join(violations[:3]))
                        return f"⛔ 인터페이스 계약 위반 → 롤백\n" + "\n".join(violations)
                except ImportError:
                    pass

                # 6. 성공 — 모든 기록
                self.breaker.record_success(filepath)
                self.log.record_modification(filepath, f"[{action}] {desc}", success=True)
                self.analyzer.record(issue, fix, True, sandbox_detail, live_applied=True)
                self.analyzer.record_reasoning(
                    issue, fix, confidence, gates_passed, apply_method, "live_applied")
                self._notify(
                    f"✅ [자율코딩 Lv5] 적용 완료\n"
                    f"파일: {os.path.basename(filepath)}\n"
                    f"액션: {action} / {desc}\n"
                    f"신뢰: {confidence}/100 | 적용: {apply_method}\n"
                    f"누적: {self.analyzer.get_success_rate()}"
                )
                return f"✅ [{action}] {desc}\n적용: {apply_method}"
            finally:
                _UPDATE_LOCK.release()

    # ── 트리거 A: 오류 로그 감시 ──────────────────────────────────────────────
    def check_error_log(self) -> str:
        if not os.path.exists(ERROR_LOG):
            return ""
        mtime = os.path.getmtime(ERROR_LOG)
        if mtime <= self._last_error_mtime:
            return ""
        self._last_error_mtime = mtime
        try:
            content = Path(ERROR_LOG).read_text(encoding="utf-8")
            sections = content.split("##")
            return sections[-1].strip() if len(sections) > 1 else content[-1000:]
        except:
            return ""

    # ── 트리거 B: 대화 키워드 감지 ───────────────────────────────────────────
    def detect_from_conversation(self, user_query: str, agent_answer: str):
        if any(kw in user_query for kw in TRIGGER_KEYWORDS):
            self._pending_issues.append(f"사용자 피드백: '{user_query[:200]}'")

    def process_pending(self):
        if not self._pending_issues:
            return
        issue  = self._pending_issues.pop(0)
        target = os.path.join(SYSTEM_DIR, "obsidian_agent.py")
        result = self.apply_fix(target, issue)
        print(f"\n🔧 [자율코딩] {result}\n")

    # ── 트리거 C: 능동 개선 (자기진단 보고서 반영) ───────────────────────────
    def proactive_improve(self):
        if not self.log.can_modify():
            return
        try:
            # 오류 로그
            error_content = ""
            if os.path.exists(ERROR_LOG):
                error_content = Path(ERROR_LOG).read_text(encoding="utf-8")[-1000:]

            # 최신 자기진단 보고서 읽기 (야간 자기진단 → 다음 날 반영)
            review_content = ""
            if os.path.exists(SELF_REVIEW_DIR):
                review_files = sorted(Path(SELF_REVIEW_DIR).glob("*_자기진단.md"))
                if review_files:
                    review_content = review_files[-1].read_text(encoding="utf-8")[:1000]

            # 실패 패턴 + 성공률
            failure_patterns = self.analyzer.get_failure_patterns()
            success_rate     = self.analyzer.get_success_rate()
            history          = self.log.recent_history(days=3)

            prompt = (
                "온유 시스템을 개선할 수 있는 구체적인 항목 1개를 골라라.\n\n"
                f"[최근 오류]\n{error_content}\n\n"
                f"[자기진단 보고서 — 내일 우선 수정 제안 포함]\n{review_content}\n\n"
                f"[수정 이력]\n{history}\n\n"
                f"[실패 패턴]\n{failure_patterns}\n"
                f"[성공률]\n{success_rate}\n\n"
                "출력 (JSON만):\n"
                '{"target":"obsidian_agent.py 또는 skills/파일명",'
                '"issue":"구체적 문제",'
                '"type":"fix 또는 new_skill",'
                '"skill_purpose":"new_skill일 때 목적"}\n'
                '개선 없으면: {"type":"none"}'
            )
            text = self._call_gemini(prompt)
            m = re.search(r'\{.*\}', text, re.DOTALL)
            if not m:
                return
            plan = json.loads(m.group())

            if plan.get("type") == "none":
                return
            elif plan.get("type") == "fix":
                filepath = os.path.join(SYSTEM_DIR, plan.get("target", "obsidian_agent.py"))
                if os.path.exists(filepath):
                    result = self.apply_fix(filepath, f"[능동 개선] {plan.get('issue','')}")
                    print(f"\n🔧 [자율코딩 능동] {result}\n")
            elif plan.get("type") == "new_skill":
                result = self.create_skill(
                    plan.get("target", "새스킬"),
                    plan.get("skill_purpose", "")
                )
                print(f"\n🆕 [자율코딩 스킬] {result}\n")
        except:
            pass

    # ── 새 스킬 자동 생성 ────────────────────────────────────────────────────
    def create_skill(self, skill_name: str, purpose: str) -> str:
        skills_dir = os.path.join(SYSTEM_DIR, "skills")
        os.makedirs(skills_dir, exist_ok=True)
        safe  = re.sub(r'[^\w가-힣]', '_', skill_name)[:30]
        fpath = os.path.join(skills_dir, f"{safe}.md")
        if os.path.exists(fpath):
            return f"💡 스킬 이미 존재: {safe}.md"
        try:
            prompt = (
                f"온유 AI 에이전트의 새 스킬 파일.\n"
                f"스킬명: {skill_name}\n목적: {purpose}\n\n"
                "형식:\n# 스킬명\n## 트리거\n## 절차\n1.\n## 주의\n-\n"
                "한국어, 실용적으로."
            )
            content = self._call_gemini(prompt)
            header  = (
                f"---\ntags: [스킬, 자율생성]\n날짜: {date.today()}\n"
                f"author: Onew-SelfImprove\n---\n\n"
            )
            with open(fpath, "w", encoding="utf-8") as f:
                f.write(header + content)
            self._notify(f"🆕 [자율코딩] 새 스킬 생성: {safe}.md\n목적: {purpose}")
            return f"✅ 스킬 생성: {safe}.md"
        except Exception as e:
            return f"❌ 스킬 생성 실패: {e}"

    # ── 트리거 D: 야간 자기진단 ───────────────────────────────────────────────
    def nightly_self_review(self):
        try:
            error_content = ""
            if os.path.exists(ERROR_LOG):
                error_content = Path(ERROR_LOG).read_text(encoding="utf-8")[-2000:]

            analysis_summary = self.analyzer.get_recent_summary(10)
            success_rate     = self.analyzer.get_success_rate()
            history          = self.log.recent_history(days=7)

            prompt = (
                "온유 시스템 자기진단 보고서를 작성하라. 내일 proactive_improve()가 이 보고서를 읽고 개선한다.\n"
                "1. 반복 오류 패턴 (구체적)\n"
                "2. 샌드박스 실패 원인 분석\n"
                "3. 내일 우선 수정 제안 (파일명과 구체적 위치 포함)\n"
                "각 항목 3줄 이내, 한국어.\n\n"
                f"[오류 로그]\n{error_content}\n\n"
                f"[수정 이력]\n{history}\n\n"
                f"[수정 분석 최근 10건]\n{analysis_summary}\n"
                f"[성공률]\n{success_rate}"
            )
            report = self._call_gemini(prompt)

            os.makedirs(SELF_REVIEW_DIR, exist_ok=True)
            today       = date.today().isoformat()
            report_path = os.path.join(SELF_REVIEW_DIR, f"{today}_자기진단.md")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(
                    f"---\ntags: [자기진단, 자율코딩]\n날짜: {today}\n---\n\n"
                    f"# {today} 온유 자기진단\n\n{report}"
                )
            self._notify(f"📋 [자기진단] {today}\n{report[:300]}\n성공률: {success_rate}")
        except:
            pass

    # ── Telegram ──────────────────────────────────────────────────────────────
    def _notify(self, msg: str):
        try:
            import urllib.request, urllib.parse
            token   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
            chat_id = os.environ.get("TELEGRAM_CHAT_ID", "")
            if not token or not chat_id:
                return
            data = urllib.parse.urlencode({"chat_id": chat_id, "text": msg}).encode()
            urllib.request.urlopen(
                f"https://api.telegram.org/bot{token}/sendMessage",
                data=data, timeout=5
            )
        except:
            pass


# ==============================================================================
# [백그라운드 워처]
# ==============================================================================
_engine: SelfImproveEngine | None = None

def get_engine() -> SelfImproveEngine:
    global _engine
    if _engine is None:
        _engine = SelfImproveEngine()
    return _engine


def _get_gemini_client():
    """onew_code_planner에 주입할 Gemini 클라이언트 반환."""
    try:
        from google import genai
        return genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
    except Exception:
        return None


def start_watcher(check_interval: int = 300):
    engine = get_engine()

    def _watch():
        nightly_done = None
        last_proactive = 0.0
        while True:
            try:
                # A: 오류 로그
                err = engine.check_error_log()
                if err:
                    r = engine.apply_fix(
                        os.path.join(SYSTEM_DIR, "obsidian_agent.py"),
                        f"오류 로그:\n{err}"
                    )
                    if "✅" in r:
                        print(f"\n🔧 [자율코딩] {r}\n")
                # B: 대화 이슈
                engine.process_pending()
                # C: 능동 개선 (2시간)
                if time.time() - last_proactive >= 7200:
                    last_proactive = time.time()
                    threading.Thread(target=engine.proactive_improve, daemon=True).start()
                # D: 야간 자기진단 (23:00)
                now = datetime.now()
                if now.hour == 23 and nightly_done != date.today():
                    nightly_done = date.today()
                    threading.Thread(target=engine.nightly_self_review, daemon=True).start()
                # E: git 상태 정리 (매 사이클)
                threading.Thread(target=GitCleanupAgent.run, daemon=True).start()
                # F: 코드 계획 태스크 실행 (대기 중인 계획이 있으면 1개 처리)
                try:
                    import onew_code_planner as _cp
                    _cp.execute_next(engine=engine, client=_get_gemini_client())
                except Exception:
                    pass
            except Exception:
                pass
            time.sleep(check_interval)

    t = threading.Thread(target=_watch, daemon=True, name="onew-self-improve")
    t.start()
    return t


def notify_conversation(user_query: str, agent_answer: str):
    get_engine().detect_from_conversation(user_query, agent_answer)
