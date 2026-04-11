"""스킬: ai_prompt_engineering — RTRE 빌더 + Few-Shot 템플릿 + 출력 형식 검증"""
import json
import re

# ── 1. RTRE 프롬프트 빌더 ─────────────────────────────────────────────────────
def build_rtre_prompt(
    role: str,
    task: str,
    rules: list[str],
    examples: list[dict] | None = None,
) -> str:
    lines = [
        f"Role: {role}",
        f"Task: {task}",
        "Rules:",
    ]
    for r in rules:
        lines.append(f"  - {r}")
    if examples:
        lines.append("Examples:")
        for ex in examples:
            lines.append(f"  입력: {ex['input']}")
            lines.append(f"  출력: {ex['output']}")
    return "\n".join(lines)

# ── 2. Few-Shot 템플릿 생성 ───────────────────────────────────────────────────
def build_fewshot(examples: list[dict], query: str, label: str = "출력") -> str:
    blocks = []
    for ex in examples:
        blocks.append(f"입력: {ex['input']}\n{label}: {ex['output']}")
    blocks.append(f"입력: {query}\n{label}:")
    return "\n\n".join(blocks)

# ── 3. JSON 출력 형식 파서 ────────────────────────────────────────────────────
def parse_json_response(response: str) -> dict:
    """LLM이 JSON으로 응답했는지 검증 + 파싱"""
    # 코드블록 제거
    cleaned = re.sub(r'```json\s*|\s*```', '', response).strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 파싱 실패: {e}\n응답: {cleaned[:100]}")
    required = {"result", "confidence", "reason"}
    missing = required - data.keys()
    if missing:
        raise ValueError(f"필수 필드 누락: {missing}")
    if not (0 <= data["confidence"] <= 1):
        raise ValueError(f"confidence 범위 오류: {data['confidence']}")
    return data

# ── 검증 ─────────────────────────────────────────────────────────────────────
# RTRE 빌더
prompt = build_rtre_prompt(
    role="Python 코드 리뷰어",
    task="다음 코드의 CRITICAL/WARN/NIT 이슈를 찾아라",
    rules=["bare except 금지", "타입 힌트 필수", "함수 50줄 이하"],
    examples=[
        {"input": "except: pass", "output": "[CRITICAL] bare except → 구체적 예외 명시"},
    ]
)
assert "Role:" in prompt
assert "Task:" in prompt
assert "Rules:" in prompt
assert "Examples:" in prompt
print(f"  [1] RTRE 프롬프트 빌드 완료 ({len(prompt.splitlines())}줄)")

# Few-Shot
examples = [
    {"input": "오늘 날씨가 좋아요", "output": "긍정"},
    {"input": "배달이 너무 늦었어요", "output": "부정"},
]
fewshot = build_fewshot(examples, "서비스가 빨라졌네요")
assert "긍정" in fewshot
assert "부정" in fewshot
assert "서비스가 빨라졌네요" in fewshot
assert fewshot.endswith("출력:")
print(f"  [2] Few-Shot 템플릿 생성 ({len(fewshot.splitlines())}줄)")

# JSON 파서
valid_response = '{"result": "긍정", "confidence": 0.95, "reason": "긍정적 표현 감지"}'
parsed = parse_json_response(valid_response)
assert parsed["confidence"] == 0.95
print(f"  [3] JSON 파싱: {parsed}")

invalid_response = '{"result": "긍정"}'  # 필드 누락
try:
    parse_json_response(invalid_response)
    assert False
except ValueError as e:
    print(f"  [4] 필드 누락 차단: {e}")

print("PASS")
