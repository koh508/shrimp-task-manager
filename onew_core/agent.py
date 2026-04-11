"""
온유 에이전트 v2 (agent.py) — smolagents + MCP 서버 기반
사용법:
    from onew_core.agent import OnewAgentV2
    agent = OnewAgentV2()
    reply = agent.run("공조냉동 냉동효과 설명해줘")
"""
import os, sys, contextlib, atexit
import mcp

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MCP_DIR    = os.path.join(SYSTEM_DIR, "mcp_servers")

sys.path.insert(0, SYSTEM_DIR)

from smolagents import ToolCallingAgent, LiteLLMModel, ToolCollection, Tool
from onew_core.system_prompt import build as build_prompt


class CodePlannerTool(Tool):
    """온유 코드 플래너 — 복잡한 코딩 작업을 TDD 단계별 계획으로 실행."""
    name        = "create_code_plan"
    description = (
        "여러 파일을 생성/수정하거나 TDD 순서가 필요한 복잡한 코딩 작업에 사용합니다. "
        "목표를 입력하면 계획을 세우고 30초마다 한 단계씩 자동 실행합니다. "
        "단순한 파일 1개 작업은 write_file을 사용하세요."
    )
    inputs      = {
        "goal": {
            "type":        "string",
            "description": "달성할 코딩 목표 (구체적으로 작성할수록 좋음)",
        }
    }
    output_type = "string"

    def forward(self, goal: str) -> str:
        import onew_code_planner as _ocp
        from google import genai as _genai
        _client = _genai.Client(api_key=os.environ.get("GEMINI_API_KEY", ""))
        return _ocp.receive_direction(goal, client=_client)


def _mcp_params(server_file: str) -> mcp.StdioServerParameters:
    """MCP 서버를 stdio 서브프로세스로 실행하는 파라미터 반환."""
    return mcp.StdioServerParameters(
        command=sys.executable,
        args=[os.path.join(MCP_DIR, server_file)],
        env={**os.environ},
    )


class OnewAgentV2:
    """smolagents 기반 온유 에이전트."""

    def __init__(self, location_mode: str = "home"):
        self.location_mode = location_mode
        self._stack: contextlib.ExitStack | None = None
        self._agent = self._build()
        atexit.register(self.close)  # 인터프리터 종료 전 MCP 스레드 정리

    def _build(self, extra_context: str = "") -> ToolCallingAgent:
        # 기존 스택 정리
        if self._stack:
            self._stack.close()

        self._stack = contextlib.ExitStack()

        # ── LLM: Gemini 2.5 Flash via LiteLLM ────────────────────────────────
        model = LiteLLMModel(
            model_id="gemini/gemini-2.5-flash",
            api_key=os.environ.get("GEMINI_API_KEY", ""),
            max_tokens=8192,  # 폭주 방지 하드캡 (thinking 누출 시 66k 토큰 방지)
        )

        # ── MCP 서버 연결 (from_mcp은 contextmanager — ExitStack으로 생명주기 관리) ──
        tools = []

        for server_file, label in [
            ("vault_server.py",  "Vault"),
            ("study_server.py",  "Study"),
            ("system_server.py", "System"),
            ("skills_server.py", "Skills"),
        ]:
            server_path = os.path.join(MCP_DIR, server_file)
            if not os.path.exists(server_path):
                print(f"[OnewAgentV2] {label} 서버 없음 — 건너뜀 ({server_file})")
                continue
            try:
                collection = self._stack.enter_context(
                    ToolCollection.from_mcp(
                        _mcp_params(server_file),
                        trust_remote_code=True,
                    )
                )
                tools.extend(collection.tools)
                print(f"[OnewAgentV2] {label} 서버 연결 ({len(collection.tools)}개 도구)")
            except Exception as e:
                print(f"[OnewAgentV2] {label} 서버 연결 실패: {e}")

        if not tools:
            self._stack.close()
            raise RuntimeError("연결된 MCP 서버가 없습니다. mcp_servers/ 폴더를 확인하세요.")

        # 코드 플래너 도구 추가
        tools.append(CodePlannerTool())

        # ── 시스템 프롬프트 조립 (+ 세션 복원 컨텍스트) ──────────────────────
        instructions = build_prompt(self.location_mode)
        if extra_context:
            instructions += f"\n\n{extra_context}"

        # ── 에이전트 생성 ──────────────────────────────────────────────────────
        agent = ToolCallingAgent(
            tools=tools,
            model=model,
            instructions=instructions,
            max_steps=6,
        )
        return agent

    def run(self, query: str, reset: bool = True) -> str:
        """쿼리를 실행하고 최종 응답 문자열을 반환.

        reset=False: 이전 대화 메모리를 유지한 채 이어서 실행 (멀티턴 대화용).
        reset=True : 매번 새로 시작 (기본값, 독립 실행 시 사용).
        """
        try:
            result = self._agent.run(query, reset=reset)
            return str(result)
        except Exception as e:
            return f"[에이전트 오류] {e}"

    def reload(self, location_mode: str = None, extra_context: str = ""):
        """에이전트 재빌드 (세션 리셋 또는 location_mode 변경 시 사용)."""
        if location_mode:
            self.location_mode = location_mode
        self._agent = self._build(extra_context=extra_context)
        print("[OnewAgentV2] 에이전트 재빌드 완료")

    def close(self):
        """MCP 서버 연결 종료."""
        if self._stack:
            try:
                self._stack.close()
            except Exception:
                pass
            self._stack = None


# ── 직접 실행 테스트 ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys, io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

    print("OnewAgentV2 초기화 중...")
    agent = OnewAgentV2()
    print("완료. 쿼리를 입력하세요 (종료: Ctrl+C)\n")

    while True:
        try:
            q = input("질문 > ").strip()
            if not q:
                continue
            print(agent.run(q))
            print()
        except KeyboardInterrupt:
            print("\n종료")
            break
