"""
onew_safety_apis.py
산업안전 외부 API 통합 모듈

- KOSHA 안전보건법령 스마트검색
- KOSHA 국내재해사례
- KOSHA 안전보건자료 링크
- 근로복지공단 산재보험 판례
- Perplexity 웹검색
- Claude 최종 합성
"""
import os
import sys
import json
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

SYSTEM_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SYSTEM_DIR)


def _get_env(name: str) -> str:
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


DATA_KEY = _get_env('DATA_GO_KR_KEY')
ANTHROPIC_KEY = _get_env('ANTHROPIC_API_KEY')
PPLX_KEY = _get_env('PPLX_API_KEY')


# ==============================================================================
# KOSHA 안전보건법령 스마트검색
# ==============================================================================
def search_kosha_law(query: str, num: int = 3) -> str:
    """안전보건 법령/KOSHA Guide 검색"""
    if not DATA_KEY:
        return "[KOSHA법령] API 키 없음"
    try:
        params = urllib.parse.urlencode({
            'serviceKey': DATA_KEY,
            'searchValue': query[:50],
            'pageNo': 1,
            'numOfRows': num,
        })
        url = f"https://apis.data.go.kr/B552468/srch/smartSearch?{params}"
        req = urllib.request.Request(url, headers={'Accept': 'application/json'})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode('utf-8'))

        items = (data.get('response', {})
                     .get('body', {})
                     .get('items', {})
                     .get('item', []))
        if isinstance(items, dict):
            items = [items]
        if not items:
            return "[KOSHA법령] 관련 법령을 찾지 못했습니다."

        lines = ["[KOSHA 안전보건법령]"]
        for it in items[:num]:
            title = it.get('title', '')
            content = it.get('content', '')[:300]
            lines.append(f"· {title}\n  {content}")
        return "\n".join(lines)
    except Exception as e:
        return f"[KOSHA법령 오류] {e}"


# ==============================================================================
# KOSHA 국내재해사례
# ==============================================================================
def search_kosha_accident(query: str, num: int = 3) -> str:
    """국내 산업재해 사례 검색 (재해사례 게시판 → 첨부파일 목록)"""
    if not DATA_KEY:
        return "[재해사례] API 키 없음"
    try:
        # 첨부파일 목록에서 제목 기반 검색 (키워드 필터)
        params = urllib.parse.urlencode({
            'serviceKey': DATA_KEY,
            'pageNo': 1,
            'numOfRows': 20,
            'callApiId': '',
        })
        url = (f"http://apis.data.go.kr/B552468/disaster_attach_api02"
               f"/Disaster_attach_api02?{params}")
        with urllib.request.urlopen(url, timeout=10) as r:
            root = ET.fromstring(r.read())

        items = root.findall('.//item')
        if not items:
            return "[재해사례] 관련 사례를 찾지 못했습니다."

        q_lower = query.lower()
        lines = ["[KOSHA 국내재해사례]"]
        count = 0
        for item in items:
            filenm = item.findtext('filenm', '')
            if any(kw in filenm for kw in query.split()[:3]):
                lines.append(f"· {filenm}")
                count += 1
                if count >= num:
                    break

        if count == 0:
            # 키워드 매칭 없으면 최신 N건 반환
            for item in items[:num]:
                lines.append(f"· {item.findtext('filenm', '')}")

        return "\n".join(lines)
    except Exception as e:
        return f"[재해사례 오류] {e}"


# ==============================================================================
# KOSHA 안전보건자료 링크
# ==============================================================================
def search_kosha_media(query: str, num: int = 3) -> str:
    """안전보건 교육자료/영상/가이드 링크 검색"""
    if not DATA_KEY:
        return "[안전보건자료] API 키 없음"
    try:
        params = urllib.parse.urlencode({
            'serviceKey': DATA_KEY,
            'pageNo': 1,
            'numOfRows': num,
            'callApiId': '1030',
        })
        url = (f"http://apis.data.go.kr/B552468/selectMediaList01"
               f"/getselectMediaList01?{params}")
        with urllib.request.urlopen(url, timeout=10) as r:
            root = ET.fromstring(r.read())

        items = root.findall('.//item')
        if not items:
            return "[안전보건자료] 관련 자료를 찾지 못했습니다."

        lines = ["[KOSHA 안전보건자료]"]
        for item in items[:num]:
            title = item.findtext('MED_SJ_NM', '')
            url_link = item.findtext('MED_URL', '')
            lines.append(f"· {title}\n  링크: {url_link}")
        return "\n".join(lines)
    except Exception as e:
        return f"[안전보건자료 오류] {e}"


# ==============================================================================
# 근로복지공단 산재보험 판례
# ==============================================================================
def search_accident_precedent(query: str, num: int = 2) -> str:
    """산재보험 판례/판결문 검색"""
    if not DATA_KEY:
        return "[산재판례] API 키 없음"
    try:
        params = urllib.parse.urlencode({
            'serviceKey': DATA_KEY,
            'pageNo': 1,
            'numOfRows': num,
        })
        url = (f"http://apis.data.go.kr/B490001/sjbPrecedentInfoService"
               f"/getSjbPrecedentNaeyongPstate?{params}")
        with urllib.request.urlopen(url, timeout=10) as r:
            root = ET.fromstring(r.read())

        items = root.findall('.//item')
        if not items:
            return "[산재판례] 관련 판례를 찾지 못했습니다."

        lines = ["[근로복지공단 산재판례]"]
        for item in items[:num]:
            title = item.findtext('caseNm', '') or item.findtext('sjbNm', '')
            result = item.findtext('jdgRslt', '')
            summary = item.findtext('jdgCn', '')[:200] if item.findtext('jdgCn') else ''
            lines.append(f"· {title} [{result}]\n  {summary}")
        return "\n".join(lines)
    except Exception as e:
        return f"[산재판례 오류] {e}"


# ==============================================================================
# Perplexity 웹검색 (Google Search 대체)
# ==============================================================================
def search_perplexity(query: str) -> str:
    """Perplexity sonar로 최신 안전기준/사례 검색 (출처 포함)"""
    if not PPLX_KEY:
        return "[Perplexity] API 키 없음"
    try:
        from openai import OpenAI
        client = OpenAI(api_key=PPLX_KEY, base_url="https://api.perplexity.ai")
        resp = client.chat.completions.create(
            model="sonar",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "한국 산업현장 안전 전문가로서 답변하라. "
                        "관련 법령, 안전기준, 사고사례를 근거로 제시하라. "
                        "출처를 명시하라. 불확실한 내용은 명시적으로 표시하라."
                    )
                },
                {"role": "user", "content": query}
            ],
            max_tokens=1000,
        )
        answer = resp.choices[0].message.content
        return f"[Perplexity 웹검색]\n{answer}"
    except Exception as e:
        return f"[Perplexity 오류] {e}"


# ==============================================================================
# Claude 최종 안전 합성 (할루시네이션 교차검증)
# ==============================================================================
def synthesize_with_claude(prompt: str) -> str:
    """Claude Opus로 최종 안전 판단 합성 - Gemini와 교차검증"""
    if not ANTHROPIC_KEY:
        return None  # 키 없으면 None 반환 → Gemini fallback
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
        msg = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=4096,
            messages=[{"role": "user", "content": prompt}]
        )
        return msg.content[0].text.strip()
    except Exception as e:
        print(f"[Claude 오류 → Gemini fallback] {e}")
        return None


# ==============================================================================
# 통합 KOSHA 검색 (3개 API 병렬 실행)
# ==============================================================================
def search_all_kosha(query: str) -> str:
    """KOSHA 3개 API + 산재판례 통합 검색"""
    import concurrent.futures
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as ex:
        futures = {
            ex.submit(search_kosha_law, query): 'law',
            ex.submit(search_kosha_accident, query): 'accident',
            ex.submit(search_kosha_media, query): 'media',
            ex.submit(search_accident_precedent, query): 'precedent',
        }
        for f in concurrent.futures.as_completed(futures):
            key = futures[f]
            try:
                results[key] = f.result()
            except Exception as e:
                results[key] = f"[{key} 오류] {e}"

    return "\n\n".join([
        results.get('law', ''),
        results.get('accident', ''),
        results.get('media', ''),
        results.get('precedent', ''),
    ])
