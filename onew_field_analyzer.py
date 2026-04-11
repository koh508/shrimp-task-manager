"""
onew_field_analyzer.py
산업현장 사진 안전 분석 모듈
- 단일: Vision + Vault RAG + KOSHA + 웹검색 + Claude 합성
- 다중: 개별분석 → 종합분석 → 재분석 → 최종보고서 4단계
"""
import os
import sys
import tempfile

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)

from onew_safety_apis import search_all_kosha, search_perplexity, synthesize_with_claude

SAFETY_RULES = """
[분석 규칙 - 반드시 준수]
- 불확실한 항목: ❓ 불확실 표시, 추측임을 명시
- 즉각 조치 필요: 🚨 즉시조치 표시
- 주의 필요: ⚠️ 주의 표시
- 정상 확인: ✅ 정상 표시
- 단정 금지: 확실하지 않은 내용은 반드시 "추정" "가능성" 등으로 표현
- 최종판단은 반드시 현장 전문가가 직접 확인하도록 명시
"""

SINGLE_PROMPT = """
당신은 산업현장 안전 분석 전문가입니다.
{rules}

[사용자 질문]: {question}
[사진 시각 분석]: {vision}
[Vault 개인자료]: {vault}
[KOSHA 법령/재해사례/판례]: {kosha}
[웹 검색 결과 (Perplexity)]: {web}

아래 형식으로 현장 작업기록지를 작성하세요. 빈칸(미확인 항목)은 반드시 표시하고 확인 방법을 제시하세요.

## 📷 사진 분석 요약
- **식별 설비:** (설비명)
- **식별 부품:** (부품명)
- **계기값:** (수치 또는 없음)
- **육안 상태:** (이상징후 포함 전반 상태)

## 🚨 위험요소 (우선순위순)
| 등급 | 항목 | 내용 |
|------|------|------|
| 🚨/⚠️/✅/❓ | (항목) | (설명) |

## 📋 작업 절차
(이 작업에 특화된 단계별 안전 절차. 번호 목록으로 작성. LOTO → 분해 → 교체 → 재조립 → 시운전 순서)

## ❓ 부족한 정보 — 현장 확인 후 기입
| 항목 | 상태 | 조치 |
|------|------|------|
| (미확인 항목) | ❌ 미확인 | (확인 방법) |

## 📚 관련 자료 참조
(Vault 자료 인용 + 출처 파일명)

## 📜 관련 법령
(KOSHA 법령/재해사례/판례에서 관련 항목 요약. API 오류 시 일반 법령 조항 명시)

## 🔍 종합 판단
(5개 정보원 종합, 핵심 주의사항 1~4개 번호 목록)

## ✅ 작업 완료 확인
- [ ] 시운전 정상 확인
- [ ] LOTO 해제 완료
- [ ] 작업 구역 정리 완료
- [ ] 작업 완료 시각: `____________`
- [ ] 작업자 서명: `____________`
- [ ] 차기 점검 일정: `____________`

## 📝 특이사항 / 메모
_(작업 중 발견된 추가 이상 또는 메모)_

---
⚠️ 본 분석은 AI 보조 도구입니다. 최종 안전 판단은 반드시 현장 전문가가 직접 확인하십시오.
"""

HOLISTIC_PROMPT = """
당신은 산업현장 안전 분석 전문가입니다.
{rules}

아래는 동일 현장에서 촬영한 {n}장의 사진에 대한 개별 분석 결과입니다.
이 사진들을 하나의 현장으로 보고 전체적인 맥락을 파악하세요.

{individual_analyses}

[Vault 통합 참고자료]: {vault}
[KOSHA 법령/재해사례/판례]: {kosha}
[웹 검색 결과 (Perplexity)]: {web}
[사용자 질문]: {question}

아래 형식으로 현장 전체 종합 분석을 작성하세요:

## 🏭 현장 전체 파악
(N장 사진을 종합한 현장 상황 전체 그림)

## 🔗 사진 간 연관성
(각 사진이 어떻게 연결되는지, 같은 설비의 다른 부위인지 등)

## 🚨 현장 전체 위험요소 (우선순위순)
(전체 맥락에서 파악된 위험, 개별 분석에서 놓쳤을 수 있는 것 포함)

## 💡 재분석 시 주목할 포인트
(각 사진별로 전체 맥락을 고려해 다시 봐야 할 핵심 포인트)
사진1: ...
사진2: ...
(N장까지)

## ❓ 불확실 / 추가 촬영 필요
(더 확인이 필요한 부위나 각도)

---
⚠️ 최종 안전 판단은 반드시 현장 전문가가 직접 확인하십시오.
"""

REANALYSIS_PROMPT = """
당신은 산업현장 안전 분석 전문가입니다.
{rules}

[현장 전체 맥락 (N장 종합 분석)]:
{holistic}

위 전체 맥락을 바탕으로 아래 사진 {idx}번을 재분석하세요.
첫 번째 분석에서 놓쳤거나, 전체 맥락을 알고 나서 새롭게 보이는 것에 집중하세요.

[사진 {idx}번 1차 분석 결과]:
{first_analysis}

재분석 형식:

## 📷 사진 {idx} 재분석
### 1차와 달라진 판단
(맥락을 알고 나서 수정되거나 추가된 내용)

### 이 사진에서 전체 맥락상 주목할 점
(전체 현장에서 이 사진의 역할/중요성)

### 위험요소 재평가
(🚨/⚠️/✅/❓ 재평가, 변경 이유 명시)
"""

FINAL_PROMPT = """
당신은 산업현장 안전 분석 전문가입니다.
{rules}

아래는 {n}장 사진에 대한 완전한 분석 결과입니다.
(개별분석 → 종합분석 → 재분석 3단계 완료)

[현장 종합 분석]:
{holistic}

[각 사진 재분석 결과]:
{reanalyses}

위 모든 분석을 바탕으로 최종 현장 안전 보고서를 작성하세요:

## 🏭 현장 최종 안전 보고서

### 현장 상황 요약

### 🚨 즉시 조치 필요 사항 (우선순위순)

### ⚠️ 단기 조치 필요 사항

### ✅ 정상 확인 항목

### ❓ 추가 확인 / 전문가 점검 필요

### 📋 권장 조치 순서

---
⚠️ 본 보고서는 AI 보조 분석이며 법적 효력이 없습니다.
최종 안전 판단 및 조치는 반드시 자격을 갖춘 현장 전문가가 수행하십시오.
"""


# ==============================================================================
# 단일 사진 분석
# ==============================================================================
def analyze_field_image(img_path: str, question: str = "", agent=None) -> dict:
    import obsidian_agent as _oa
    from google.genai import types

    print("[현장분석] ① 사진 시각 분석 중...")
    vision_q = (
        f"이 산업현장 사진을 안전 점검 관점에서 상세히 분석하라. "
        f"설비명, 부품명, 계기판 수치, 이상징후, 위험요소를 구체적으로 열거하라. "
        f"텍스트/라벨이 있으면 전부 읽어라."
        + (f" 사용자 질문: {question}" if question else "")
    )
    vision = _oa.analyze_image(img_path, vision_q)

    print("[현장분석] ② Vault 자료 검색 중...")
    vault, vault_sources = _search_vault(vision[:300], agent)

    print("[현장분석] ③ KOSHA 법령/재해사례/판례 검색 중...")
    kosha_query = f"{question} {vision[:150]}"[:200]
    kosha = search_all_kosha(kosha_query)

    print("[현장분석] ④ Perplexity 웹 검색 중...")
    web_query = f"산업현장 안전기준 {question} {vision[:100]} 안전점검"[:300]
    web = search_perplexity(web_query)
    if "[Perplexity] API 키 없음" in web or "[Perplexity 오류]" in web:
        # fallback: Gemini 웹검색
        web = _oa.analyze_trend(web_query)

    print("[현장분석] ⑤ 종합 보고서 생성 중 (Claude 우선)...")
    prompt = SINGLE_PROMPT.format(
        rules=SAFETY_RULES, question=question or "(없음)",
        vision=vision, vault=vault, kosha=kosha, web=web
    )
    report = synthesize_with_claude(prompt) or _generate(prompt)

    return {'report': report, 'vision': vision,
            'vault': vault, 'vault_sources': vault_sources,
            'kosha': kosha, 'web': web}


# ==============================================================================
# 다중 사진 4단계 분석
# ==============================================================================
def analyze_multiple_field_images(img_paths: list, question: str = "",
                                   agent=None) -> str:
    """
    4단계 다중 사진 분석:
    1단계: 각 사진 개별 Vision 분석
    2단계: 전체 종합 분석 (Vault + 웹 + 교차분석)
    3단계: 종합 맥락 기반 각 사진 재분석
    4단계: 최종 통합 보고서
    """
    import obsidian_agent as _oa
    n = len(img_paths)

    # ── 1단계: 개별 Vision 분석 ─────────────────────────────────────────
    print(f"[다중분석] 1단계: {n}장 개별 사진 분석 중...")
    vision_q = (
        "이 산업현장 사진을 안전 점검 관점에서 상세히 분석하라. "
        "설비명, 부품명, 계기판 수치, 이상징후, 위험요소를 구체적으로 열거하라. "
        "텍스트/라벨이 있으면 전부 읽어라."
        + (f" 사용자 질문: {question}" if question else "")
    )
    individual_visions = []
    for i, path in enumerate(img_paths):
        print(f"  사진 {i+1}/{n} Vision 분석 중...")
        vision = _oa.analyze_image(path, vision_q)
        individual_visions.append(vision)

    # ── 2단계: Vault + KOSHA + 웹 검색 (전체 맥락으로 통합 검색) ─────────
    print("[다중분석] 2단계: Vault + KOSHA + 웹 검색 중...")
    combined_text = " ".join([v[:150] for v in individual_visions])
    vault, vault_sources = _search_vault(combined_text[:400], agent, k=8)

    kosha_query = f"{question} {combined_text[:150]}"[:200]
    kosha = search_all_kosha(kosha_query)

    web_query = f"산업현장 안전기준 {question} {combined_text[:100]} 안전점검"[:300]
    web = search_perplexity(web_query)
    if "[Perplexity] API 키 없음" in web or "[Perplexity 오류]" in web:
        web = _oa.analyze_trend(web_query)

    # 종합 맥락 분석
    individual_section = "\n\n".join(
        [f"[사진 {i+1}번 분석]\n{v}" for i, v in enumerate(individual_visions)]
    )
    holistic_prompt = HOLISTIC_PROMPT.format(
        rules=SAFETY_RULES, n=n,
        individual_analyses=individual_section,
        vault=vault, kosha=kosha, web=web,
        question=question or "(없음)"
    )
    print("[다중분석] 2단계: 현장 전체 종합 분석 중 (Claude 우선)...")
    holistic = synthesize_with_claude(holistic_prompt) or _generate(holistic_prompt)

    # ── 3단계: 각 사진 재분석 ────────────────────────────────────────────
    print("[다중분석] 3단계: 종합 맥락 기반 재분석 중...")
    reanalyses = []
    for i, (path, first_vision) in enumerate(zip(img_paths, individual_visions)):
        print(f"  사진 {i+1}/{n} 재분석 중...")
        re_prompt = REANALYSIS_PROMPT.format(
            rules=SAFETY_RULES, holistic=holistic,
            idx=i+1, first_analysis=first_vision
        )
        reanalysis = _generate(re_prompt)
        reanalyses.append(reanalysis)

    # ── 4단계: 최종 통합 보고서 ──────────────────────────────────────────
    print("[다중분석] 4단계: 최종 보고서 생성 중 (Claude 우선)...")
    reanalyses_section = "\n\n".join(
        [f"[사진 {i+1}번 재분석]\n{r}" for i, r in enumerate(reanalyses)]
    )
    final_prompt = FINAL_PROMPT.format(
        rules=SAFETY_RULES, n=n,
        holistic=holistic,
        reanalyses=reanalyses_section
    )
    final_report = synthesize_with_claude(final_prompt) or _generate(final_prompt)

    # 전체 구조 조합
    result = (
        f"{'='*50}\n"
        f"📊 {n}장 현장 사진 다중 분석 결과\n"
        f"{'='*50}\n\n"
    )
    for i, (vision, reanalysis) in enumerate(zip(individual_visions, reanalyses)):
        result += f"{'─'*40}\n📷 사진 {i+1}번\n{'─'*40}\n"
        result += f"[1차 분석]\n{vision}\n\n"
        result += f"{reanalysis}\n\n"

    result += f"{'='*50}\n🔍 현장 전체 종합 분석\n{'='*50}\n{holistic}\n\n"
    result += f"{'='*50}\n🏭 최종 안전 보고서\n{'='*50}\n{final_report}"

    return result


# ==============================================================================
# 내부 헬퍼
# ==============================================================================
def _search_vault(query: str, agent=None, k: int = 5):
    import obsidian_agent as _oa
    vault_result = "관련 자료를 찾지 못했습니다."
    vault_sources = []
    try:
        mem = agent.mem if agent else _oa.OnewPureMemory()
        results = mem.search(query, k=k)
        if results:
            lines = []
            for r in results:
                src = r.get('source', '알 수 없음')
                vault_sources.append(src)
                lines.append(f"[출처: {src}]\n{r['text'][:500]}")
            vault_result = "\n\n".join(lines)
    except Exception as e:
        vault_result = f"Vault 검색 오류: {e}"
    return vault_result, list(set(vault_sources))


def _generate(prompt: str) -> str:
    import obsidian_agent as _oa
    from google.genai import types
    try:
        res = _oa.client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            )
        )
        return res.text.strip()
    except Exception as e:
        return f"[생성 오류: {e}]"


# ──────────────────────────────────────────────────────────────────────────────
# 시험 문제 풀이 파이프라인 (공조냉동기계기사 / OCU 등)
# ──────────────────────────────────────────────────────────────────────────────

# caption에 이 키워드가 있으면 exam 모드로 라우팅
EXAM_KEYWORDS = (
    "문제", "퀴즈", "풀어", "공조", "냉동", "냉매", "압축기", "응축기",
    "증발기", "p-h", "몰리에르", "소방", "ocu", "실기", "필기",
    "계산", "공식", "열역학", "냉동사이클", "과열도", "과냉각",
)


def is_exam_photo(caption: str) -> bool:
    """caption 기반으로 시험 문제 사진인지 판단."""
    c = caption.lower()
    return any(kw in c for kw in EXAM_KEYWORDS)


def _exam_vision_prompt(question: str = "") -> str:
    base = (
        "이 이미지에서 시험 문제나 문제지 내용을 빠짐없이 읽어라. "
        "텍스트, 수식, 선도(p-h선도/냉동사이클), 도표, 그림의 레이블을 모두 읽어라. "
        "읽은 내용을 그대로 출력한 뒤, 문제가 있으면 그 문제를 명확히 한 줄로 요약하라."
    )
    return base + (f" 사용자 추가 질문: {question}" if question else "")

_EXAM_SOLVE_PROMPT = """당신은 공조냉동기계기사·소방설비·열역학 전문 강사입니다.

[사진에서 읽은 내용]
{vision}

[Vault 관련 자료]
{vault}

{user_q}

아래 형식으로 간결하게 답하라:

**정답:** (한 줄)
**핵심 공식/원리:** (한 줄)
**풀이:** (2~3줄, 계산 과정 포함)

"자세히"라고 요청하지 않는 한 위 형식을 절대 벗어나지 마라.
"""


def analyze_exam_image(img_path: str, question: str = "", agent=None) -> dict:
    """
    시험 문제 사진 → 핵심 풀이 반환.
    Returns: {'answer': str, 'vision': str, 'vault': str}
    """
    import obsidian_agent as _oa

    # ① Vision: 문제 텍스트/선도 읽기
    vision_q = (
        "이 이미지에서 시험 문제나 문제지 내용을 빠짐없이 읽어라. "
        "텍스트, 수식, 선도(p-h선도/냉동사이클), 도표, 그림의 레이블을 모두 읽어라. "
        "읽은 내용 그대로 출력하고, 문제가 있으면 한 줄로 요약하라."
        + (f" 사용자 질문: {question}" if question else "")
    )
    vision = _oa.analyze_image(img_path, vision_q)

    # ② Vault RAG: 관련 학습 자료 검색 (API 절감: 짧은 쿼리)
    vault_q = (question or vision[:150]).strip()
    vault, _ = _search_vault(vault_q[:200], agent, k=3)

    # ③ LLM 풀이 생성
    user_q_line = f"[사용자 질문]: {question}" if question else ""
    prompt = _EXAM_SOLVE_PROMPT.format(
        vision=vision, vault=vault or "없음", user_q=user_q_line
    )
    answer = _generate(prompt)

    return {'answer': answer, 'vision': vision, 'vault': vault}


def analyze_field_image_bytes(img_bytes: bytes, ext: str,
                               question: str = "", agent=None) -> dict:
    with tempfile.NamedTemporaryFile(suffix=f'.{ext}', delete=False) as tmp:
        tmp.write(img_bytes)
        tmp_path = tmp.name
    try:
        return analyze_field_image(tmp_path, question, agent)
    finally:
        try:
            os.unlink(tmp_path)
        except:
            pass
