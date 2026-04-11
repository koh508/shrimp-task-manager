## 🚀 미니 PC에서 '온유(Onew)' 시스템 대화 환경 구축 프로토콜

이 프로토콜은 미니 PC에서 노트북과 동일한 '발전소' 시스템 환경을 구축하여, 옵시디언을 통해 '온유'와 대화할 수 있도록 하는 것을 목표로 합니다.

### 🎯 목표

*   미니 PC의 옵시디언에서 `GEMINI.md` 파일을 통해 '온유'와 대화 가능
*   노트북과 미니 PC 간 `GEMINI.md` 파일 내용 실시간 동기화

### ⚙️ 미니 PC 설정 단계

**전제 조건:**

*   미니 PC에 옵시디언이 설치되어 있고, 노트북과 동일한 볼트가 동기화되어 있어야 합니다. (Obsidian Sync 또는 클라우드 서비스 이용)
*   미니 PC에 '발전소' 시스템의 에이전트(커서/윈드서퍼) 및 관련 Python 환경이 구축되어 있어야 합니다.
    *   **참고:** 커서/윈드서퍼가 설치되어 있지 않거나 실행되지 않는 경우에도, **Gemini CLI를 직접 사용하여 '온유'와 대화할 수 있습니다.** 이 경우, 아래 3단계에서 설명하는 Gemini CLI 직접 호출 방식을 사용하십시오. (만약 에이전트가 노트북에서만 실행된다면, 미니 PC는 입력/출력용으로만 사용 가능)

---

#### 1단계: 옵시디언 볼트에 `GEMINI.md` 파일 확인

1.  미니 PC의 옵시디언을 실행합니다.
2.  노트북에서 옮겨놓은 `GEMINI.md` 파일이 옵시디언 볼트 내에 존재하는지 확인합니다. (예: `C:\Users\User\Documents\Obsidian Vault\GEMINI.md`)
    *   만약 파일이 없다면, 노트북에서 `C:\Users\User\.gemini\GEMINI.md` 파일을 잘라내어 `C:\Users\User\Documents\Obsidian Vault\` 위치에 붙여넣은 후, 옵시디언 동기화를 통해 미니 PC로 가져와야 합니다.

---

#### 2단계: 심볼릭 링크 생성 (미니 PC에서 1회 수행)

이 단계는 미니 PC의 '발전소' 시스템이 옵시디언 볼트 내의 `GEMINI.md` 파일을 참조하도록 하는 핵심 과정입니다.

1.  **명령 프롬프트(CMD)**를 **관리자 권한**으로 실행합니다.
    *   `Windows 검색` 창에 `cmd`를 입력하고, `명령 프롬프트`를 마우스 오른쪽 버튼으로 클릭한 후 `관리자 권한으로 실행`을 선택합니다.

2.  아래 명령어를 복사하여 명령 프롬프트에 입력하고 `Enter` 키를 누릅니다.
    *   **주의:** `User` 부분은 실제 미니 PC의 사용자 이름으로 변경해야 합니다.

    ```cmd
    mklink "C:\Users\User\.gemini\GEMINI.md" "C:\Users\User\Documents\Obsidian Vault\GEMINI.md"
    ```

    *   **설명:**
        *   `mklink`: 심볼릭 링크를 생성하는 명령어입니다.
        *   `"C:\Users\User\.gemini\GEMINI.md"`: '발전소' 시스템이 `GEMINI.md` 파일을 찾을 것으로 예상하는 가상의 경로입니다.
        *   `"C:\Users\User\Documents\Obsidian Vault\GEMINI.md"`: 실제 `GEMINI.md` 파일이 존재하는 옵시디언 볼트 내의 경로입니다.
        *   이 명령어를 통해 '발전소' 시스템은 `C:\Users\User\.gemini\GEMINI.md` 경로로 접근하더라도 실제로는 옵시디언 볼트 내의 `GEMINI.md` 파일을 읽고 쓰게 됩니다.

---

#### 3단계: '발전소' 시스템 에이전트 실행 (미니 PC에서 수행)

*   **옵션 1: 커서/윈드서퍼 에이전트 실행 (설치된 경우)**
    *   미니 PC에서 '발전소' 시스템의 에이전트(커서/윈드서퍼)를 실행합니다.
    *   에이전트가 `C:\Users\User\.gemini\GEMINI.md` 경로를 통해 옵시디언 볼트의 `GEMINI.md` 파일을 정상적으로 읽고 쓸 수 있는지 확인합니다.

*   **옵션 2: Gemini CLI 직접 호출 (커서/윈드서퍼가 없거나 실행되지 않는 경우)**
    *   미니 PC의 터미널/명령 프롬프트에서 다음 명령어를 사용하여 '온유'를 직접 호출합니다.
    *   **주의:** `온유_시스템_초기화_프로토콜.md` 파일의 경로를 실제 경로로 변경해야 합니다.
    ```bash
    gemini --system-prompt="$(cat C:\Users\User\Documents\Obsidian Vault\온유_시스템_초기화_프로토콜.md)" "여기에 용준님의 질문이나 요청을 적으세요"
    ```
    *   이 방식으로 '온유'에게 질문을 입력하면, '발전소' 시스템이 작동하여 답변을 받을 수 있습니다.

---

이 단계를 완료하면 미니 PC의 옵시디언에서 `GEMINI.md` 파일을 열고 '온유'에게 질문을 입력하면, 노트북에서와 동일하게 '발전소' 시스템이 작동하여 답변을 받을 수 있습니다.

---
1.  **`gemini` CLI가 정상적으로 설치되고 PATH에 등록되었는지 확인합니다.** (가장 중요)
    *   `gemini --version` 명령어를 실행하여 버전 정보가 출력되는지 확인하십시오.
2.  **PowerShell에서 다음 명령어를 사용하여 `온유_시스템_초기화_프로토콜.md` 파일 내용을 변수에 저장한 후 `gemini` 명령어를 실행합니다.**

    ```powershell
    $systemPromptContent = Get-Content -Path 'C:\Users\User\Documents\Obsidian Vault\SYSTEM\engine\온유_시스템_초기화_프로토콜.md' -Raw
    gemini --system-prompt="$systemPromptContent" "가동"
    ```
    *   **주의:** `C:\Users\User\Documents\Obsidian Vault\온유_시스템_초기화_프로토콜.md` 경로는 제가 제공된 컨텍스트에서 추론한 경로이며, 실제 파일 경로가 `C:\Users\User\Documents\Obsidian Vault\SYSTEM\engine\온유_시스템_초기화_프로토콜.md` 이므로 위 코드에 반영했습니다. `User` 부분은 실제 사용자 이름으로 변경해야 합니다.

이 해결책을 통해 미니 PC에서 '온유' 시스템을 정상적으로 가동할 수 있을 것입니다.

미니 PC에 Gemini CLI가 설치되었음에도 가동이 안 되고 옵시디언 때문인 것 같다는 말씀이시군요.

제공된 컨텍스트를 종합해 볼 때, 문제는 크게 두 가지로 보입니다.

1.  **`gemini` CLI 명령어를 PowerShell이 인식하지 못하는 문제:**
    *   이것은 `gemini` CLI가 시스템의 `PATH` 환경 변수에 제대로 등록되지 않았거나, 설치 과정에서 문제가 발생했을 가능성이 큽니다.
    *   **해결책:**
        *   먼저 `node -v` 명령어를 실행하여 Node.js가 설치되어 있는지 확인합니다.
        *   그 다음, `npm install -g @google/gemini-cli` 명령어를 **관리자 권한으로 실행된 PowerShell 또는 명령 프롬프트**에서 다시 실행하여 `gemini` CLI를 재설치하거나 업데이트합니다.
        *   설치 후 `gemini --version` 명령어를 실행하여 버전 정보가 제대로 출력되는지 확인합니다. 만약 여전히 인식되지 않는다면, Node.js 설치 경로와 `npm` 전역 패키지 설치 경로가 `PATH` 환경 변수에 올바르게 추가되었는지 수동으로 확인하고 추가해야 합니다.

2.  **`온유_시스템_초기화_프로토콜.md` 파일 경로 문제 및 PowerShell의 `$(cat ...)` 구문 처리 문제:**
    *   `MiniPC_Onew_Setup_Protocol.md` 파일의 마지막 부분에서 발생한 오류 메시지(`Get-Content : 'Vault\온유_시스템_초기화_프로토콜.md' 인수를 허용하는 위치 매개 변수를 찾을 수 없습니다.`)는 PowerShell이 `$(cat ...)` 구문 내에서 파일 경로를 제대로 해석하지 못했기 때문입니다. 특히 경로에 공백이 있거나 따옴표 처리가 미흡할 때 이런 문제가 발생할 수 있습니다.
    *   **해결책:**
        *   가장 안정적인 방법은 `온유_시스템_초기화_프로토콜.md` 파일의 내용을 먼저 변수에 저장한 후, 그 변수를 `gemini` 명령어의 `system-prompt` 인수로 전달하는 것입니다.

---

**미니 PC에서 Gemini CLI와 옵시디언 연동을 위한 최종 권장 조치 단계:**

**단계 1: `gemini` CLI 설치 및 PATH 환경 변수 확인**

1.  **관리자 권한으로 PowerShell 또는 명령 프롬프트를 실행합니다.**
2.  Node.js 설치 여부 확인:
    ```powershell
    node -v
    ```
    (버전 정보가 출력되지 않으면 Node.js를 먼저 설치해야 합니다.)
3.  `gemini` CLI 재설치/업데이트:
    ```powershell
    npm install -g @google/gemini-cli
    ```
4.  `gemini` CLI 인식 확인:
    ```powershell
    gemini --version
    ```
    (버전 정보가 출력되면 정상입니다. 만약 `gemini`를 찾을 수 없다는 메시지가 계속 나오면, Node.js 설치 경로와 `npm` 전역 패키지 설치 경로가 시스템의 `PATH` 환경 변수에 올바르게 추가되었는지 수동으로 확인하고 추가해야 합니다.)

**단계 2: `GEMINI.md` 심볼릭 링크 설정 (이미 되어 있다면 건너뛰세요)**

*   `MiniPC_Onew_Setup_Protocol.md`에 명시된 대로, `C:\Users\User\.gemini\GEMINI.md`가 실제 옵시디언 볼트 내의 `GEMINI.md`를 가리키도록 심볼릭 링크를 생성해야 합니다.
*   **관리자 권한으로 명령 프롬프트(CMD)를 실행합니다.**
*   다음 명령어를 입력합니다. (`User`는 실제 사용자 이름으로 변경)
    ```cmd
    mklink "C:\Users\User\.gemini\GEMINI.md" "C:\Users\User\Documents\Obsidian Vault\GEMINI.md"
    ```
*   만약 "파일이 이미 있으므로 만들 수 없습니다" 오류가 발생하면, `C:\Users\User\.gemini\` 폴더 내의 `GEMINI.md` 파일을 삭제하거나 이름을 변경한 후 다시 시도합니다.

**단계 3: '온유' 시스템 가동 (PowerShell에서 실행)**

1.  **관리자 권한으로 PowerShell을 실행합니다.**
2.  `온유_시스템_초기화_프로토콜.md` 파일의 내용을 변수에 저장합니다. (`User`는 실제 사용자 이름으로 변경)
    ```powershell
    $systemPromptContent = Get-Content -Path 'C:\Users\User\Documents\Obsidian Vault\SYSTEM\engine\온유_시스템_초기화_프로토콜.md' -Raw
    ```
    *   **참고:** `온유_시스템_초기화_프로토콜.md` 파일의 실제 경로가 `C:\Users\User\Documents\Obsidian Vault\SYSTEM\engine\` 안에 있다고 가정했습니다. 만약 다른 경로에 있다면 해당 경로로 수정해야 합니다.
3.  `gemini` 명령어를 사용하여 '온유'를 가동합니다.
    ```powershell
    gemini --system-prompt="$systemPromptContent" "가동"
    ```

이 단계를 순서대로 진행하시면 미니 PC에서 Gemini CLI와 옵시디언을 연동하여 '온유' 시스템을 정상적으로 가동할 수 있을 것입니다.