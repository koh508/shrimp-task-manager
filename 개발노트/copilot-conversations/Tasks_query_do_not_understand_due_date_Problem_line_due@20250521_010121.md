---
epoch: 1747756881245
modelKey: copilot-plus-flash|copilot-plus
tags:
  - copilot-conversation
---

**user**: Tasks query: do not understand due date
Problem line: "due template_contact" 뜻이 뭐야?
[Timestamp: 2025/05/21 01:01:21]

**ai**: "due template_contact"는 "template_contact"라는 이름의 템플릿 연락처에 대한 마감일을 의미합니다. 여기서 "template_contact"는 특정 연락처 템플릿을 나타내는 것으로 보입니다.
[Timestamp: 2025/05/21 01:01:25]

**user**: Tasks query: do not understand due date
Problem line: "due before template_contact"
[Timestamp: 2025/05/21 01:01:42]

**ai**: "due before template_contact"는 "template_contact"라는 이름의 템플릿 연락처 **전**에 마감일을 의미합니다. 즉, 해당 템플릿 연락처와 관련된 어떤 날짜보다 먼저 완료해야 함을 나타냅니다.

[Timestamp: 2025/05/21 01:01:46]

**user**: Tasks query: do not understand done date
Problem line: "done template_contact"
[Timestamp: 2025/05/21 01:01:51]

**ai**: "done template_contact"는 "template_contact"라는 이름의 템플릿 연락처가 완료된 날짜를 의미합니다. 즉, 해당 템플릿 연락처가 완료된 시점을 나타냅니다.

[Timestamp: 2025/05/21 01:01:55]

**user**: 번역해줘
[Timestamp: 2025/05/21 01:03:04]

**ai**: ## 번역: [[Getting Started]]

---
cssclasses:
  - no-inline
  - hide-properties_editing
  - hide-properties_reading
---
# **시작하기** 폴더의 지침을 따르세요.
**디렉토리: SYSTEM > GETTING STARTED**
# 다음 순서를 따르세요:
1. [[Vault Onboarding Part 1  - Very Important Setup]]
2. [[Vault Onboarding Part 2 - Structure Concept]]
3. [[Vault Onboarding Part 3 - Main Features]]
4. [[Vault Onboarding Part 4 - Setting up on Mobile]]
5. [[Vault Walkthrough - Concept Map]]
# 참조 파일:
1. [[Concept Inspiration and Reference]]
# 참고 사항:
- / 이 Vault는 **PARA**와 **ZETA**(Zettelkasten) 노트 작성 방법 사이에 강력한 구분을 만듭니다.
- / **프로젝트 컴포넌트**를 사용하여 **프로젝트**를 쉽게 모니터링할 수 있습니다.
- / **영역 컴포넌트**를 사용하면 탐색하려는 주제에 대한 **MOC(Map of Content)**를 만들 수 있습니다.
	- ? 저는 **PARA**와 관련 없는 입력/개념에 **ZETA** 컴포넌트를 사용하는 것을 좋아합니다 (제 경우에는 PARA가 기술 개발 또는 업무 관련 사항에 중점을 두기 때문입니다).
- / **홈페이지**의 일부 Dataview 테이블은 **수정된 날짜를 기준으로 나열/정렬**되며 표시되는 노트는 **15**개로 제한됩니다.
	- & 이것은 Vault 크기를 조정하여 가장 최근 파일로 쉽게 이동할 수 있도록 도와줍니다.
- @ CSS 스니펫은 대부분 변경되지 않았으므로 원하는 대로 **Vault의 모양을 개인화**할 수 있습니다.
#### **Vault의 잠재력을 최대한 활용하려면 설명서를 자세히 살펴보는 것이 좋습니다.**
# **샘플 보기**
````tabs
tab: HUB
**홈페이지**
![[Getting Started.png]]
**목차 지도**
![[Getting Started-1.png]]
**메일 박스**
![[Getting Started-2.png]]
tab: Area
**영역 패밀리**
![[Getting Started-3.png]]
**영역 노트**
![[Getting Started-4.png]]
tab: Project
**프로젝트 대시보드**
![[Getting Started-5.png]]
**프로젝트 노트**
![[Getting Started-6.png]]
tab: Daily
**데일리 노트**
![[Getting Started-7.png]]
**위클리 노트**
![[Getting Started-8.png]]
**먼슬리 노트**
![[Getting Started-9.png]]
- ? **데일리/위클리/먼슬리** 노트를 빠르게 생성하려면 **달력을 더블 클릭**하세요.
![[Getting Started-12.png]]
또는 여기를 클릭하세요.
![[Getting Started-13.png]]
tab: Meeting
**일반 회의**
![[Getting Started-10.png]]
- ? **세 가지 유형의 회의 노트**가 있습니다.
	- 일반 회의
	- 스탠드업 회의
	- 팀 회의
tab: Contacts
**연락처**
![[Getting Started-11.png]]
- ? **`#contact/{name}`**을 사용하여 연락처에 대한 작업 또는 회의를 추가할 수 있습니다. 자세한 내용은 [[Vault Walkthrough - Concept Map]]을 참조하십시오.
````

[Timestamp: 2025/05/21 01:03:19]

**user**: Getting Started
The vault is mainly divided into two parts:

/ PARA: Project, Area, Resources, Archive
/ ZETA: Fleeting Note, Permanent Note, Literature Note If you want your vault to scale well in the long run you must understand your use case for the vault and follow a separation rule for your note inputs.
? My use case example:
@ my PARA file inputs are things that are related to the development of a skill or things that might be doing that is work related.
@ my ZETA file inputs are concepts for the brain that is not PARA related.
Quick Overview
/ HUB
Homepage - This homepage can take you anywhere
Map of Content - Quick navigation and for searching checking related concepts
Mail Box - Monitor existing and completed page tasks (this is different from the tasks inside a note)
/ PARA
PROJECTS - Things you work on with a given deadline
AREAS - Things you work on without a deadline
RESOURCES
CONTACTS - You can store all your contacts here
DOCUMENTATIONS - Create documentations for your PARA files (The select connection only suggests notes inside the PARA category)
CONCEPT MAP - All Canvas and Excalidraw files goes here
MEETINGS - There are three types of meetings you can create
ARCHIVES - You can move Project and Area Family folders here when no longer in use
WORKSTATION - These are like Fleeting Notes but PARA related
/ ZETA (The select connection only suggests notes inside the ZETA category)
PERMANENT - Permanent Notes
LITERATURE - Literature Notes
FLEETING - Fleeting Notes
/ DAILY
DAILY - All daily notes goes here
WEEKLY - All weekly notes goes here
MONTHLY - All monthly notes goes here
QUARTERLY - All quarterly notes goes here (I have not prepared a template for this as I do not use it)
YEARLY - All yearly notes goes here (I have not prepared a template for this as I do not use it)
/ STICKY - These are quick disposable notes that does not belong to any category (things you will just delete soon).
/ SYSTEM - Mobile HUB, Media, Templates, Getting Started guide and all the system configurations goes here.번역
[Timestamp: 2025/05/21 01:18:28]

**ai**: ## 번역: 시작하기

Vault는 크게 두 부분으로 나뉩니다.

/ PARA: 프로젝트(Project), 영역(Area), 자료(Resources), 보관(Archive)
/ ZETA: 휘발성 노트(Fleeting Note), 영구 노트(Permanent Note), 문헌 노트(Literature Note)

Vault를 장기적으로 잘 확장하려면 Vault의 사용 사례를 이해하고 노트 입력에 대한 분리 규칙을 따라야 합니다.

? 제 사용 사례 예시:
@ 제 PARA 파일 입력은 기술 개발 또는 업무 관련 활동과 관련된 것입니다.
@ 제 ZETA 파일 입력은 PARA와 관련 없는 두뇌를 위한 개념입니다.

## 빠른 개요

/ HUB
홈페이지 - 이 홈페이지에서 어디든 갈 수 있습니다.
목차 지도 - 빠른 탐색 및 관련 개념 검색 및 확인
메일 박스 - 기존 및 완료된 페이지 작업 모니터링 (노트 내부의 작업과는 다름)

/ PARA
프로젝트 - 주어진 마감일이 있는 작업
영역 - 마감일이 없는 작업
자료
연락처 - 모든 연락처를 여기에 저장할 수 있습니다.
문서 - PARA 파일에 대한 문서 생성 (선택 연결은 PARA 범주 내의 노트만 제안)
개념 지도 - 모든 Canvas 및 Excalidraw 파일이 여기에 들어갑니다.
회의 - 세 가지 유형의 회의를 만들 수 있습니다.
보관 - 더 이상 사용하지 않는 프로젝트 및 영역 패밀리 폴더를 여기로 이동할 수 있습니다.
작업 공간 - 휘발성 노트와 같지만 PARA 관련

/ ZETA (선택 연결은 ZETA 범주 내의 노트만 제안)
영구 - 영구 노트
문헌 - 문헌 노트
휘발성 - 휘발성 노트

/ DAILY
데일리 - 모든 데일리 노트가 여기에 들어갑니다.
위클리 - 모든 위클리 노트가 여기에 들어갑니다.
먼슬리 - 모든 먼슬리 노트가 여기에 들어갑니다.
쿼터리 - 모든 쿼터리 노트가 여기에 들어갑니다 (저는 사용하지 않으므로 템플릿을 준비하지 않았습니다).
이어리 - 모든 이어리 노트가 여기에 들어갑니다 (저는 사용하지 않으므로 템플릿을 준비하지 않았습니다).

/ STICKY - 어떤 범주에도 속하지 않는 빠른 임시 노트 (곧 삭제할 것들).
/ SYSTEM - 모바일 HUB, 미디어, 템플릿, 시작하기 가이드 및 모든 시스템 구성이 여기에 들어갑니다.

[Timestamp: 2025/05/21 01:18:36]