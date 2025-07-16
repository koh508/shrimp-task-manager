---
title: "One-way sync between Telegram, Notion, Google Drive, and Google Sheets | n8n workflow template"
source: "https://n8n.io/workflows/4404-one-way-sync-between-telegram-notion-google-drive-and-google-sheets/"
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
description: "One-way sync between Telegram, Notion, Google Drive, and Google SheetsWho is this for?This workflow is perfect for productivity-focused teams, remote workers, v"
tags:
  - "clippings"
---
---

## Telegram, Notion, Google Drive 및 Google Sheets 간의 일원 동기화

## 이게 누구야?

이 워크 플로는 전보를 통해 문서, 이미지 또는 메모를 받고 수동 작업없이 개념, Google 드라이브 및 Google 시트에 자동으로 구성하고 저장하려는 생산성 중심 팀, 원격 작업자, 가상 어시스턴트 및 디지털 지식 관리자에게 적합합니다.

## 이 워크 플로우 해결은 어떤 문제입니까?

개념, 드라이브 및 시트와 같은 다양한 도구에서 전보 메시지 및 미디어를 수동으로 관리하는 것은 지루할 수 있습니다. 이 워크 플로우는 텍스트 노트, 이미지 또는 문서 등 수신 전보 콘텐츠의 분류 및 저장을 자동화합니다. 시간을 절약하고 인적 오류를 줄이며 미디어가 메타 데이터 추적으로 올바른 위치에 저장되도록합니다.

## 이 워크 플로가하는 일

- **새로운 전보 메시지를 트리거합니다** Telegram 트리거 노드 사용.
- **메시지 유형을 분류합니다** 스위치 노드 사용:
	- 문자 메시지는 개념 블록에 추가됩니다.
	- 이미지는 Base64로 변환되어 IMGBB에 업로드 한 다음 토글 이미지 블록으로 개념에 추가됩니다.
	- 문서는 다운로드되고 Google 드라이브에 업로드되며 메타 데이터는 Google 시트에 로그인됩니다.
- **완료 확인을 보냅니다** 원래 전보 채팅으로 돌아갑니다.

## 설정

1. **Telegram Bot** : 봇을 설치하고 API 토큰을 얻습니다.
2. **개념 통합** :
	- 대상 개념 페이지/블록에 대한 액세스를 공유하십시오.
	- 개념 API 자격 증명과 컨텐츠를 추가 해야하는 블록 ID를 사용하십시오.
3. **Google 드라이브 및 시트** :
	- 관련 계정을 연결하십시오.
	- 대상 폴더 및 스프레드 시트를 선택하십시오.
4. **IMGBB 화재** : 무료 API 키를 얻으십시오 [IMGBB](https://api.imgbb.com/) .

수입 워크 플로에서 필요에 따라 자리 표시 자 신용 ID 및 자산 URL을 교체하십시오.

## 이 워크 플로우를 필요에 맞게 사용자 정의하는 방법

- **스토리지 위치를 변경하십시오** :
	- 개념 블록 ID 또는 Google 드라이브 폴더 ID를 업데이트하십시오.
	- Google 시트를 전환하여 다른 파일이나 시트에 로그인하십시오.
- **더 많은 필터를 추가하십시오** :
	- 추가 스위치 규칙을 사용하여 다른 Telegram 메시지 유형 (동영상 또는 음성 메시지 등)을 처리하십시오.
- **응답 메시지를 수정하십시오** :
	- 파일 유형 또는 발신자에 따라 Telegram 확인 텍스트를 개인화하십시오.
- **다른 이미지 호스팅 서비스를 사용하십시오** IMGBB를 사용하고 싶지 않은 경우.

;