"""
온유-Claude Code 브릿지 (claude_bridge.py)
- Telegram에서 "클로드: <요청>" → claude --print subprocess → 결과 스트리밍

API 비용: Gemini 0회 (정적 템플릿 사용)
확장: allowed_tools, workdir, permission_mode 파라미터로 제어
"""
import asyncio
import json
import os

# ── 상수 ────────────────────────────────────────────────────────────────────
SYSTEM_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CLAUDE_CMD   = "claude"
CLAUDE_TIMEOUT_SEC = 300   # 5분

# 허용 도구 프리셋
TOOL_PRESETS = {
    "readonly":  "Read,Glob,Grep",
    "standard":  "Read,Write,Edit,Bash,Glob,Grep",
    "full":      "Read,Write,Edit,Bash,Glob,Grep,WebSearch,WebFetch",
}

# 프롬프트 래퍼 (Gemini API 0회)
_PROMPT_TEMPLATE = """\
[온유 → Claude Code 작업 지시]
작업 디렉터리: {workdir}

{request}

--- 완료 후 반드시 아래 형식으로 보고 ---
변경 파일: (없으면 '없음')
요약: (1-3줄)
"""

# ── 상태 ────────────────────────────────────────────────────────────────────
_proc: asyncio.subprocess.Process | None = None


def build_prompt(request: str, workdir: str = SYSTEM_DIR) -> str:
    """정적 템플릿으로 프롬프트 래핑 (API 비용 없음)."""
    return _PROMPT_TEMPLATE.format(request=request.strip(), workdir=workdir)


async def run_async(
    prompt: str,
    workdir: str = SYSTEM_DIR,
    tool_preset: str = "standard",
    on_chunk=None,      # async callable(text: str) — 스트리밍 델타 콜백
) -> tuple[bool, str]:
    """
    claude --print 비동기 실행.

    Returns:
        (success: bool, output: str)
    """
    global _proc

    if _proc is not None:
        return False, "이미 실행 중입니다. /claude_cancel 로 취소하세요."

    allowed = TOOL_PRESETS.get(tool_preset, TOOL_PRESETS["standard"])
    cmd = [
        CLAUDE_CMD, "--print",
        "--output-format", "stream-json",
        "--include-partial-messages",
        "--allowedTools", allowed,
        prompt,
    ]

    try:
        _proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=workdir,
        )

        text_so_far = ""      # 누적 텍스트 (partial message 비교용)
        final_result = ""
        is_error = False

        async def _read_with_timeout():
            nonlocal text_so_far, final_result, is_error
            async for raw_line in _proc.stdout:
                line = raw_line.decode("utf-8", errors="replace").strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue

                msg_type = obj.get("type", "")

                # 스트리밍 텍스트 (partial 포함)
                if msg_type == "assistant":
                    for block in obj.get("message", {}).get("content", []):
                        if block.get("type") == "text":
                            full = block.get("text", "")
                            delta = full[len(text_so_far):]
                            if delta and on_chunk:
                                await on_chunk(delta)
                            text_so_far = full

                # 최종 결과
                elif msg_type == "result":
                    final_result = obj.get("result", text_so_far)
                    is_error = obj.get("is_error", False)

        await asyncio.wait_for(_read_with_timeout(), timeout=CLAUDE_TIMEOUT_SEC)
        await _proc.wait()
        rc = _proc.returncode
        output = final_result or text_so_far
        return (rc == 0 and not is_error), output

    except asyncio.TimeoutError:
        if _proc:
            try:
                _proc.terminate()
            except Exception:
                pass
        return False, f"⏱ 타임아웃 ({CLAUDE_TIMEOUT_SEC}초 초과). /claude_cancel 로 정리하세요."

    except FileNotFoundError:
        return False, "`claude` CLI를 찾을 수 없습니다. PATH를 확인하세요."

    except Exception as e:
        return False, f"실행 오류: {e}"

    finally:
        _proc = None


async def cancel() -> bool:
    """실행 중인 프로세스 강제 종료. 종료했으면 True."""
    global _proc
    if _proc is None:
        return False
    try:
        _proc.terminate()
    except Exception:
        pass
    _proc = None
    return True


def is_running() -> bool:
    return _proc is not None
