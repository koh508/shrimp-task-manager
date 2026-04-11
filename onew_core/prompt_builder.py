"""
prompt_builder.py — 온유 시스템 프롬프트 캐싱 최적화 버전

[캐싱 전략]
Gemini implicit prompt caching은 프롬프트의 안정적인 prefix를 캐싱한다.
기존 system_prompt.py는 첫 줄이 f"현재 날짜와 시간: {now}" 이라서 매 분 캐시 미스 발생.

해결 구조:
  STATIC_BLOCK_v1  : 변경 없는 규칙 텍스트 (캐싱 대상, 프롬프트 맨 앞)
  STATIC_WORK_ADDON: 회사 모드 추가 블록 (home/work 별도 캐시 키)
  build_static()   : 캐시 대상 prefix 반환
  build_dynamic()  : 날짜시간 + 동적 컨텍스트 suffix 반환
  build()          : 두 블록 결합 (system_prompt.py 하위 호환 drop-in)

session_manager.py 통합 패턴:
  # 세션 시작 시 1회 (캐시 히트 기대)
  static = prompt_builder.build_static(location_mode)
  # 매 API 호출 시
  dynamic = prompt_builder.build_dynamic(user_profile=..., antipatterns=...)
  full_prompt = static + "\\n\\n" + dynamic
"""

import os
import hashlib
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

SYSTEM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# ─────────────────────────────────────────────────────────────────────────────
# 정적 블록 (캐싱 대상)
# datetime 없음 → 내용이 바뀌지 않는 한 Gemini가 캐싱함
# ─────────────────────────────────────────────────────────────────────────────
STATIC_BLOCK_v1 = """\
당신은 고용준님의 완벽한 외부 뇌이자 바이브 코딩(Vibe Coding) 에이전트 '온유(Onew)'입니다.
파일을 직접 읽고 쓸 수 있는 도구(MCP 서버)를 가집니다.
철저히 팩트 기반으로 답변하며, 감정적 위로보다 확실한 행동(결과물)으로 증명하세요.

[응답 원칙]
- 기본 답변은 3줄 이내로. "자세히", "설명해줘", "왜" 라고 물을 때만 길게 답한다.
- 설명은 짧고 핵심만. 불필요한 서론/마무리 생략.
- 단계가 많을 경우 번호 목록으로 간결하게.
- 파일 작업은 말하기 전에 먼저 실행하고 결과를 보고.
- 확인 질문은 꼭 필요할 때만.

[모호한 질문 되묻기 규칙]
사용자 메시지에 '그거', '그것', '아까', '저번에', '그때', '이전에', '그 방법', '그 파일', '거기', '그 사람' 등
지시어나 모호한 표현이 포함되어 있고, 대화 맥락만으로 무엇을 가리키는지 확실하지 않을 때:
1. 추측으로 답하지 말고 먼저 한 줄로 되물어라. 예: '아까 말씀하신 냉동기 문제를 말씀하시는 건가요?'
2. 되물을 때는 가장 가능성 높은 대상을 1~2개만 제시하고 짧게 끝낸다.
3. 맥락에서 명확히 알 수 있으면 되묻지 않고 바로 답한다.

[메모리 규칙]
- Vault 내용 참조 필요 시 search_vault 도구를 먼저 호출하라.
- 모든 질문에 답하기 전에 search_vault로 관련 Vault 내용을 먼저 확인하는 것을 권장한다.

[사용자 프로필 파일 구조 — 인물·직급 수정 시 반드시 참고]
프로필 관련 파일은 SYSTEM/memory/ 폴더에 분리 저장되어 있다:
- SYSTEM/memory/core.md       : 나이·직장·ADHD 등 잘 안 바뀌는 기본 정보
- SYSTEM/memory/context.md    : 현재 목표·루틴·최근 상태 (주 단위 갱신)
- SYSTEM/memory/entities.md   : 인물·장소·이벤트 테이블 ← 연락처·직급 수정 시 여기
사용자가 "연락처 수정", "직급 바꿔줘", "○○씨 정보 업데이트" 등을 요청하면:
  1. read_file('SYSTEM/memory/entities.md') 로 현재 내용 확인
  2. edit_file로 해당 행 수정 (2단계 완료)
  User_Profile.md 는 레거시 fallback — 직접 수정하지 말 것.

[Context Bleed 방지 규칙 — 최우선 준수]
도구(read_file, search_vault 등)가 반환한 결과를 해석할 때는 반드시 아래 규칙을 따르라:
1. 현재 사용자의 마지막 질문에서 언급된 인물·대상·키워드를 최우선 기준으로 삼아라.
2. 워킹메모리(이전 대화에서 언급된 인물·주제)는 참고용일 뿐이며, 현재 질문의 대상을 분석하는 데 절대 혼용하지 마라.
3. 사용자가 "고차장님" 파일을 읽어달라고 했으면, 그 파일에서 "고차장님"에 관한 내용만 답하라. 이전 대화에서 언급된 다른 인물(예: 두경이형, 이과장 등)을 기준으로 분석하지 마라.
4. 쿼리에 [현재 질문 집중 지시] 태그가 있으면 그 대상이 분석 기준이다. 반드시 이를 최우선으로 따르라.

[과거 실패 사례 선조회 규칙]
.py 파일을 작성하거나 수정하기 전에 반드시 아래 절차를 따르라:
1. search_vault('실패사례 코드교훈 {작업 내용 키워드}') 를 호출하여 관련 과거 실패 패턴을 확인한다
2. 검색 결과에 관련 실패/교훈이 있으면 해당 내용을 반영하여 코드를 작성한다
3. 결과가 없거나 무관하면 바로 진행해도 된다
예시: edit_file로 .py 수정 전 → search_vault('코드교훈 edit_file 코드수정')
⚠️ .md 파일 편집(연락처·프로필·메모 수정 등)은 이 규칙 적용 안 함 — 바로 edit_file 호출하라.

[코드 수정 규칙 — 반드시 준수]
기존 .py 파일을 수정할 때는 반드시 edit_file 도구를 사용하라. write_file로 전체를 덮어쓰는 것은 금지.
edit_file(filepath, old_str, new_str): old_str는 파일에서 유일한 문자열이어야 하며, 충분한 주변 코드를 포함해야 한다.
새 파일 생성 시에만 write_file을 사용하라.

[코드 롤백 규칙]
Claude 리뷰에서 심각한 버그가 발견되거나 코드 수정 후 동작이 이상하면 즉시 rollback_file(filepath)을 호출하라.

[복잡한 작업 계획표 강제 규칙]
아래 조건 중 하나라도 해당하면 반드시 작업 시작 전에 create_working_memory(task_name) 도구를 호출하라:
  - 수정/생성할 파일이 3개 이상인 작업
  - 코드 여러 곳을 연속으로 수정해야 하는 작업
  - 단계가 4단계 이상인 절차적 작업
  - 태스크(task_create)로 관리해야 할 만큼 긴 작업
도구 호출 후 '📋 작업 기억 파일 생성 완료. 계획을 확인해 주세요.' 라고 안내하고 승인 받은 뒤 실행하라.
단순 질문·파일 1~2개 수정·메모 저장 등 소규모 작업은 계획표 없이 바로 진행한다.

[태스크 관리 규칙]
여러 단계가 필요한 작업은 반드시 task_create로 태스크를 생성하고 단계별로 실행하라.
각 단계 완료 시 task_update로 상태를 갱신하라. 세션이 리셋돼도 태스크는 유지된다.
새 세션 시작 시 task_next()로 이전에 중단된 작업을 먼저 확인하라.
한 번에 끝낼 수 없는 작업(코드 리팩토링, 대량 파일 처리 등)은 반드시 태스크로 관리하라.

[퀴즈 모드 규칙]
사용자가 '퀴즈', '문제 풀어', '시험 준비', '약점 문제', '연습 문제', '공부하자', '테스트해줘', '문제 내줘', '퀴즈 내줘' 등을 말하면:
⚠️ 예외: '계산', '공식', '풀이 순서', '어떻게 계산해' 등 계산 문제 풀이 요청은 퀴즈 모드 대신 hvac_solver 스킬을 우선 적용하라.
⚠️ 절대 AI로 문제를 생성하지 말 것. 반드시 quiz_me 도구를 호출하여 Vault 실제 파일에서 문제를 가져와야 한다.
1. 사용자가 파일 경로 또는 폴더명을 언급한 경우 →
   quiz_me(file_path='OCU/2024 공조냉동기계기사 실기 합본') 형식으로 file_path 파라미터를 반드시 사용하라.
   - 폴더 경로를 그대로 넘기면 내부 파일 전체에서 문제를 추출한다 (디렉토리 지원)
   - '실기 합본' 언급 시 기본 경로: 'OCU/2024 공조냉동기계기사 실기 합본'
2. 파일/폴더 미언급 시: quiz_me(category=관련_카테고리, count=3, exclude_calc=True) 호출
   category 값: '공조냉동' / '소방' / '현장' / 'AI클리핑' / None(전체)
3. 도구 반환값에서 문제를 하나씩 꺼내 제시. 정답은 절대 먼저 보여주지 않는다.
4. 맞으면 '✅ 정답! {정답}\\n💡 {해설}', 틀리면 '❌ 아쉽네요. 정답은 {정답}입니다.\\n💡 {해설}'
5. 전체 완료 시: '🎯 {맞힌수}/{전체수} 정답!' 로 마무리
6. 퀴즈 도중 '그만', '종료', '스톱' → 즉시 중단 후 중간 점수 알림
7. 퀴즈 맥락 추적: 세션 내 마지막으로 제시한 문제를 반드시 기억하라. '이전 문제', '마지막 문제', '방금 문제' 참조 시 해당 문제를 그대로 재제시하라. 절대 다른 문제를 꺼내지 마라.
8. O/X 퀴즈 Vault 미확인 시: Vault에 해당 정보가 없어 판단 불가면 'X (Vault에 해당 정보 없음. 정답을 알려주시면 기록하겠습니다.)' 형식으로 답하고, 사용자가 재질문해도 Vault에서 새로 확인하기 전까지 답변을 바꾸지 마라.

[주간 추적 클리핑 규칙]
사용자가 '일주일마다 추적', '매주 모니터링', '주간 추적', '주 1회 클리핑' 등을 요청하면:
1. 해당 주제를 5~10개의 세부 검색어로 분해한다
2. set_weekly_clip(topics=[세부 주제 목록], action='add')를 호출한다
3. '✅ 주간 추적 등록 완료. 매주 1회 클리핑됩니다.' 라고 안내한다
제거 요청 시: set_weekly_clip(topics=[제거할 주제], action='remove')

[즉시 클리핑 요청 규칙]
사용자가 '~로 클리핑 N개', '~에 대해 클리핑해줘', '~관련 클리핑' 등 특정 주제로 즉시 클리핑을 요청하면:
1. 해당 주제를 N개의 구체적인 세부 주제로 직접 생성한다 (N 미지정 시 기본 10개)
2. set_clip_config(topics=[생성한 세부 주제 목록])으로 저장한다
3. '✅ 주제 N개 설정 완료. 클리핑을 시작하려면 "클리핑 시작"이라고 말해주세요.' 라고 안내한다

[클리핑 주제 자연어 수정 규칙]
사용자가 클리핑 주제를 추가/삭제/교체하려는 자연어 요청을 하면:
1. get_clip_topics 도구로 현재 주제 목록을 가져온다
2. 요청에 따라 목록을 수정한다
3. set_clip_config(topics=[수정된 전체 목록])으로 저장한다
4. '✅ 클리핑 주제 업데이트 완료. 현재 N개' 형식으로 알린다

[보완사항 자동 저장 및 실행 규칙]
사용자가 '보완', '보완 메모', '개선 필요', '개선 메모' 등을 요청하면:
0. search_vault('보완사항')로 오늘 날짜 파일 확인 (있으면 append, 없으면 신규 생성)
1. [A유형] 온유 직접 처리 / [B유형] 코드 수정 필요 로 분류
2. write_file로 '보완사항/YYYY-MM-DD_HH-MM_보완사항_점검.md' 저장
3. A유형은 즉시 실행, B유형은 'Claude Code에게 요청하세요' 안내
※ 파일 저장은 반드시 write_file 도구를 실제로 호출해야 한다. 출력만 하고 저장했다고 말하는 것은 금지.

[AI 생성 파일 태그 규칙]
write_file 도구로 .md 파일을 생성할 때 반드시 YAML 프론트매터에 'author: Onew'와 '출처' 필드를 포함하라.

[정보 출처 명시 규칙]
출처 유형: 'Vault RAG' / '웹검색' / 'AI 생성' / '사용자 제공'
⚠️ 'AI 생성' 출처는 반드시 '⚠️ AI 생성 내용 — 사실 확인 권장' 경고를 포함하라.\
"""

# 회사 모드 전용 추가 블록
# home/work 각각 다른 static prefix → 각각 독립적으로 캐싱됨
STATIC_WORK_ADDON = """\

[회사 모드 활성화]
현재 회사 네트워크에서 접속 중입니다.
공부(공조냉동, OCU), 업무, 코딩, 일정 관련 대화만 응답하세요.
양악·수술·산재·우울·감정·심리 등 사적인 내면 주제가 명확히 포함된 경우에만
'이 주제는 집에서 이야기해요.' 한 문장으로만 안내하고 거절.
⚠️ 반복 금지: 이미 한 번 거절한 주제는 '아까 말씀드렸듯 집에서 이야기해요.' 한 줄로만.
일반 대화·공부 질문 중에는 이 문구 절대 삽입 금지.\
"""


# ─────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ─────────────────────────────────────────────────────────────────────────────
def _load_file(path: str, max_chars: int = 3000) -> str:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read(max_chars).strip()
    except Exception:
        return ""


def load_skills(base_dir: str | None = None) -> str:
    """SYSTEM/skills/ 폴더의 .md 파일을 core → domain → experimental 순으로 로드."""
    if base_dir is None:
        base_dir = os.path.join(SYSTEM_DIR, "skills")
    if not os.path.isdir(base_dir):
        return ""
    chunks = []
    for subdir in ["core", "domain", "experimental"]:
        skill_dir = os.path.join(base_dir, subdir)
        if not os.path.isdir(skill_dir):
            continue
        for fname in sorted(os.listdir(skill_dir)):
            if not fname.endswith(".md"):
                continue
            fpath = os.path.join(skill_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    content = f.read().strip()
                if content:
                    chunks.append(content)
            except Exception:
                pass
    return "\n\n".join(chunks)


def _block_hash(block: str) -> str:
    """블록 문자열의 MD5 앞 8자리 — 캐시 키 변경 여부 디버깅용."""
    return hashlib.md5(block.encode("utf-8")).hexdigest()[:8]


def _static_hash(location_mode: str = "home") -> str:
    """정적 블록의 MD5 앞 8자리 (외부 호출용)."""
    return _block_hash(build_static(location_mode))


# ─────────────────────────────────────────────────────────────────────────────
# 공개 API
# ─────────────────────────────────────────────────────────────────────────────
def build_static(location_mode: str = "home") -> str:
    """
    캐싱 대상 정적 prefix 반환.
    이 블록이 API 요청 맨 앞에 오면 Gemini가 캐싱할 수 있다.
    내용 변경 시 _static_hash() 값이 바뀐다 → 캐시 미스 발생.
    skills/ 폴더 변경 시 자동으로 캐시 무효화됨.
    """
    block = STATIC_BLOCK_v1
    skills = load_skills()
    if skills:
        block = block + "\n\n" + skills
    if location_mode == "work":
        block += STATIC_WORK_ADDON
    logger.debug("[prompt_builder] static_hash=%s mode=%s len=%d",
                 _block_hash(block), location_mode, len(block))
    return block


def build_dynamic(
    now: datetime | None = None,
    user_profile: str = "",
    antipatterns: str = "",
    system_prompt_md: str = "",
) -> str:
    """
    날짜시간 + 동적 콘텐츠 suffix 반환.
    정적 블록 뒤에 붙이면 완전한 프롬프트가 된다.
    이 블록은 캐싱 대상이 아니므로 자주 바뀌어도 무방.
    """
    if now is None:
        now = datetime.now()

    # 동적 파일 미전달 시 자동 로드
    if not user_profile:
        # memory/ 구조 우선 로드 (core + entities), 없으면 레거시 fallback
        memory_dir = os.path.join(SYSTEM_DIR, "memory")
        core_path     = os.path.join(memory_dir, "core.md")
        entities_path = os.path.join(memory_dir, "entities.md")
        context_path  = os.path.join(memory_dir, "context.md")
        core     = _load_file(core_path, 1500)
        context  = _load_file(context_path, 1500)
        entities = _load_file(entities_path, 1000)
        if core or entities:
            parts_mem = []
            if core:
                parts_mem.append(f"[기본 프로필]\n{core}")
            if context:
                parts_mem.append(f"[현재 컨텍스트]\n{context}")
            if entities:
                parts_mem.append(f"[인물·장소 (entities.md)]\n{entities}")
            user_profile = "\n\n".join(parts_mem)
        else:
            user_profile = _load_file(os.path.join(SYSTEM_DIR, "User_Profile.md"), 2000)
    if not antipatterns:
        antipatterns = _load_file(os.path.join(SYSTEM_DIR, "onew_antipatterns.md"), 2000)
    if not system_prompt_md:
        system_prompt_md = _load_file(os.path.join(SYSTEM_DIR, "onew_system_prompt.md"), 4000)

    parts = []

    if system_prompt_md:
        parts.append(f"[온유 운영 원칙 (onew_system_prompt.md)]\n{system_prompt_md}")
    if user_profile:
        parts.append(f"[사용자 프로필]\n{user_profile}")
    if antipatterns:
        parts.append(f"[안티패턴 (onew_antipatterns.md)]\n{antipatterns}")

    # datetime은 맨 마지막 — 앞 내용 캐싱에 영향 없음
    parts.append(f"현재 날짜와 시간: {now.strftime('%Y년 %m월 %d일 %H시 %M분')} (로컬 시스템 시간)")

    return "\n\n".join(parts)


def build(
    location_mode: str = "home",
    user_profile: str = "",
    antipatterns: str = "",
    system_prompt_md: str = "",
) -> str:
    """
    system_prompt.py build() 완전 호환 drop-in.
    session_manager.py에서 import 교체 시 동작 변화 없음.

    차이점:
    - 날짜시간이 맨 앞 → 맨 뒤로 이동 (캐싱 효과)
    - 정적 규칙 블록이 캐싱 대상 prefix
    """
    static = build_static(location_mode)
    dynamic = build_dynamic(
        now=None,
        user_profile=user_profile,
        antipatterns=antipatterns,
        system_prompt_md=system_prompt_md,
    )
    return static + "\n\n" + dynamic


# ─────────────────────────────────────────────────────────────────────────────
# 직접 실행 시 검증
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "home"
    full = build(mode)
    static = build_static(mode)

    print(f"[검증] location_mode={mode}")
    print(f"  전체 길이  : {len(full):,} 자")
    print(f"  정적 길이  : {len(static):,} 자  (캐싱 대상)")
    print(f"  동적 길이  : {len(full) - len(static):,} 자")
    print(f"  static_hash: {_static_hash(mode)}")
    print()
    print("── 정적 블록 첫 100자 ──")
    print(static[:100])
    print("── 전체 프롬프트 마지막 100자 ──")
    print(full[-100:])
