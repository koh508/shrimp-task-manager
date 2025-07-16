---
title: "Get Airtable data via AI and Obsidian Notes | n8n workflow template"
source: "https://n8n.io/workflows/2615-get-airtable-data-via-ai-and-obsidian-notes/"
author:
  - "[[Igor Fediczko @igordisco]]"
  - "[[로빈 틴달 @Robm]]"
  - "[[안드로 아 @Anderoav]]"
  - "[[Maxim Poulsen @maximpoulsen]]"
  - "[[펠릭스 르버 @felixleber]]"
  - "[[난 빙 @1ronben]]"
  - "[[Francois Laßl @francois-laßl]]"
  - "[[조디 m @jodime]]"
published:
created: 2025-05-28
description: "I am submitting this workflow for the Obsidian community to showcase the potential of integrating Obsidian with n8n. While straightforward, it serves as a compe"
tags:
  - "clippings"
---
---

Obsidian 커뮤니티를 위해이 워크 플로우를 제출하여 Obsidian을 N8N과 통합 할 수있는 잠재력을 보여줍니다. 간단하지만, 흑요석을 N8N과 통합하여 잠재적 잠금 해제에 대한 설득력있는 데모 역할을합니다.

**작동 방식**

이 워크 플로우를 사용하면 N8N을 사용하여 Obsidian 메모 내에서 직접 몇 초 안에 필요한 특정 공기 테이블 데이터를 검색 할 수 있습니다. Obsidian의 질문을 강조하고 [Webhook 플러그인을 게시하십시오](https://github.com/Masterb1234/obsidian-post-webhook/) , 당신은 에어테이블베이스에서 특정 데이터를 가져 와서 즉시 응답을 메모에 다시 삽입 할 수 있습니다. 워크 플로우는 OpenAI의 GPT 모델을 활용하여 쿼리를 해석하고 AirTable에서 관련 데이터를 추출하며 노트에 원활한 통합을위한 결과를 형식화합니다.

**단계를 설정하십시오**

- 설치 [Webhook 플러그인을 게시하십시오](https://github.com/Masterb1234/obsidian-post-webhook/) :이 플러그인을 플러그인 스토어 또는 Github에서 Obsidian Vault에 추가하십시오.
- N8N Webhook 설정:이 워크 플로에서 생성 된 Webhook URL을 복사하여 Obsidian의 Post Webhook 플러그인 설정에 삽입하십시오.
- Airtable Access 구성: Airtable 계정을 연결하고 원하는 기본 및 테이블을 지정하여 데이터를 가져옵니다.
- 워크 플로 테스트: Obsidian 메모에서 질문을 강조 표시하고 "Webhook로 선택"명령을 사용하고 데이터가 예상대로 반환되는지 확인하십시오.- [+2](https://n8n.io/workflows/1954-ai-agent-chat/)
[

### AI 고양이 요원

](https://n8n.io/workflows/1954-ai-agent-chat/)

[

N8N 팀

](https://n8n.io/workflows/1954-ai-agent-chat/)[

- +12

### 첫 WhatsApp 챗봇 구축

짐

](https://n8n.io/workflows/2465-building-your-first-whatsapp-chatbot/)[

- +9

### AI로 웹 페이지를 긁어 내고 요약하십시오

N8N 팀

](https://n8n.io/workflows/1951-scrape-and-summarize-webpages-with-ai/)[

- +7

### 웹 페이지를 긁을 수있는 AI 에이전트

에두아드

](https://n8n.io/workflows/2006-ai-agent-that-can-scrape-webpages/)[

- +4

### 전보 챗봇

에두아드

](https://n8n.io/workflows/1934-telegram-ai-chatbot/)[

- +17

### ai를 사용한 다중 플랫폼 소셜 미디어 컨텐츠 제작

조셉 루지

](https://n8n.io/workflows/3066-automate-multi-platform-social-media-content-creation-with-ai/)

;