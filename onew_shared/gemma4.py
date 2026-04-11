"""
onew_shared/gemma4.py
Gemma4(Ollama) 호출 — PC/태블릿 공통 인터페이스

PC obsidian_agent.py의 _ask_ollama()/_needs_gemini()를 여기서 관리.
heart_mobile도 이걸 import해서 사용 가능.

사용 예:
    from onew_shared.gemma4 import ask, needs_tool_call, is_available

    if not needs_tool_call(query) and is_available():
        answer = ask(system_prompt, query, context)
"""
import json
import logging
import urllib.request

from .config import get_ollama_url, get_ollama_model

log = logging.getLogger(__name__)

# 도구 호출이 필요한 키워드 — 이 키워드가 있으면 Gemma4로 처리 불가
# (파일 조작, 웹 검색 등은 Gemini/Claude가 필요)
_TOOL_KEYWORDS = [
    "파일", "저장", "수정", "생성", "실행", "검색", "찾아", "노트", "스크립트",
    "코드 수정", "코드수정", "웹", "이미지", "사진", "음성", "백업", "동기화",
    "폴더", "열어", "만들어", "써줘", "작성", "삭제", "이동", "복사", "캡처",
    "ocr", "pdf", "요약해줘", "정리해줘", "계획 세워", "알림", "텔레그램",
    "인덱스", "임베딩", "싱크", "클리핑", "다운로드",
]


def needs_tool_call(query: str) -> bool:
    """
    도구 호출이 필요한 쿼리인지 판단.
    True → Gemini/Claude 필요
    False → Gemma4 로컬 처리 가능
    """
    q = query.lower()
    return any(kw in q for kw in _TOOL_KEYWORDS)


def is_available() -> bool:
    """Ollama 서버가 실행 중이고 모델이 로드됐는지 확인."""
    try:
        url = f"{get_ollama_url()}/api/tags"
        with urllib.request.urlopen(url, timeout=3) as resp:
            data = json.loads(resp.read())
            models = [m["name"] for m in data.get("models", [])]
            return get_ollama_model() in models
    except Exception:
        return False


def ask(
    system_prompt: str,
    query: str,
    context: str = "",
    timeout: int = 90,
    temperature: float = 0.3,
    max_tokens: int = 2048,
) -> str | None:
    """
    Gemma4(Ollama) 호출. 실패 시 None 반환 → 호출부에서 Gemini fallback 처리.

    Args:
        system_prompt: 시스템 프롬프트 (온유 페르소나 등)
        query: 사용자 질문
        context: RAG 검색 결과 컨텍스트 (선택)
        timeout: 응답 대기 시간 초
        temperature: 생성 온도 (낮을수록 일관성 높음)
        max_tokens: 최대 생성 토큰 수

    Returns:
        응답 문자열, 실패 시 None
    """
    try:
        url = f"{get_ollama_url()}/api/chat"
        content = f"Context:\n{context}\n\n명령: {query}" if context.strip() else query
        payload = json.dumps({
            "model": get_ollama_model(),
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content},
            ],
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens,
            },
        }).encode("utf-8")

        req = urllib.request.Request(
            url, data=payload,
            headers={"Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read())
            return data["message"]["content"].strip()

    except Exception as e:
        log.warning("[Gemma4] 호출 실패: %s", e)
        return None


def ask_simple(query: str, timeout: int = 60) -> str | None:
    """
    시스템 프롬프트 없이 단순 질문. 빠른 테스트용.
    """
    return ask(
        system_prompt="한국어로 짧고 정확하게 답해.",
        query=query,
        timeout=timeout,
    )
