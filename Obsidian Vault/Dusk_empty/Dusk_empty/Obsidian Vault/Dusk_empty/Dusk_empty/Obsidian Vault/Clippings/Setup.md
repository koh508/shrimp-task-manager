---
title: "Setup"
source: "https://yukigasai.github.io/obsidian-google-calendar/Setup"
author:
published:
created: 2025-05-14
description: "The installation of this plugin is a little cumbersome. But after the initial setup you should never have to touch it again. The creation of a public OAUTH client to skip this setup is WIP."
tags:
  - "clippings"
---
The installation of this plugin is a little cumbersome. But after the initial setup you should never have to touch it again. The creation of a public OAUTH client to skip this setup is WIP.

## Install Plugin

- One click install from [community plugin store](https://yukigasai.github.io/obsidian-google-calendar/)
- Go to settings and activate plugin

## Setup Google Calendar plugin

The required URLS for the google cloud project are:

- Authorized JavaScript origins:
	- `http://127.0.0.1:42813`
	- `https://google-auth-obsidian-redirect.vercel.app`
- Authorized redirect URIs:
	- `http://127.0.0.1:42813/callback`
	- `https://google-auth-obsidian-redirect.vercel.app/callback`

This browser does not support PDFs. Please download the PDF to view it: [Download PDF](https://yukigasai.github.io/obsidian-google-calendar/Install.pdf).

A video showing the creation of the google cloud project can be found [here](https://youtu.be/TMQ8HZjeauo)

## Login

- Go into the plugin settings알겠습니다. 다음은 제공된 텍스트의 한국어 번역입니다.

---
title: "설정"
source: "https://yukigasai.github.io/obsidian-google-calendar/Setup"
author:
published:
created: 2025-05-14
description: "이 플러그인의 설치는 약간 번거롭습니다. 하지만 초기 설정 후에는 다시 손댈 필요가 없을 것입니다. 이 설정을 건너뛸 수 있는 공개 OAUTH 클라이언트 생성은 진행 중입니다."
tags:
  - "clippings"
---
이 플러그인의 설치는 약간 번거롭습니다. 하지만 초기 설정 후에는 다시 손댈 필요가 없을 것입니다. 이 설정을 건너뛸 수 있는 공개 OAUTH 클라이언트 생성은 진행 중입니다.

## 플러그인 설치

- [커뮤니티 플러그인 스토어](https://yukigasai.github.io/obsidian-google-calendar/)에서 원클릭 설치
- 설정으로 이동하여 플러그인 활성화

## Google Calendar 플러그인 설정

Google Cloud 프로젝트에 필요한 URL은 다음과 같습니다.

- 허용된 JavaScript 원본:
	- `http://127.0.0.1:42813`
	- `https://google-auth-obsidian-redirect.vercel.app`
- 허용된 리디렉션 URI:
	- `http://127.0.0.1:42813/callback`
	- `https://google-auth-obsidian-redirect.vercel.app/callback`

이 브라우저는 PDF를 지원하지 않습니다. 보려면 PDF를 다운로드하십시오: [PDF 다운로드](https://yukigasai.github.io/obsidian-google-calendar/Install.pdf).

Google Cloud 프로젝트 생성 방법을 보여주는 비디오는 [여기](https://youtu.be/TMQ8HZjeauo)에서 찾을 수 있습니다.

## 로그인

- 플러그인 설정으로 이동
- [UseCustomClient](https://yukigasai.github.io/obsidian-google-calendar/Settings/UseCustomClient) 설정을 활성화합니다.
- [GoogleClientId](https://yukigasai.github.io/obsidian-google-calendar/Settings/GoogleClientId) 및 [GoogleClientSecret](https://yukigasai.github.io/obsidian-google-calendar/Settings/GoogleClientSecret)을 입력 필드에 삽입합니다.
- 로그인을 누릅니다.
	- 브라우저 창이 열립니다.
- 로그인 / Google 계정 선택
- Google에서 앱이 확인되지 않았다는 경고를 표시합니다.
	1. 고급을 클릭합니다.
	2. {프로젝트 이름}(안전하지 않음)으로 이동을 클릭합니다.
	- 브라우저가 동의 화면으로 리디렉션됩니다.
- 허용을 클릭합니다(모든 범위를 허용해야 합니다).

![Google 경고 예시](https://yukigasai.github.io/obsidian-google-calendar/exampleGoogleWarning.png)

> Google은 내부 사용에 대한 확인을 요구하지 않습니다. 즉, 다른 사람과 공유하지 않는 한 확인되지 않은 앱을 Google 계정으로 사용할 수 있습니다.

---
title: "설정"
source: "https://yukigasai.github.io/obsidian-google-calendar/Setup"
author:
published:
created: 2025-05-14
description: "이 플러그인의 설치는 약간 번거롭습니다. 하지만 초기 설정 후에는 다시 손댈 필요가 없을 것입니다. 이 설정을 건너뛸 수 있는 공개 OAUTH 클라이언트 생성은 진행 중입니다."
tags:
  - "clippings"
---
이 플러그인의 설치는 약간 번거롭습니다. 하지만 초기 설정 후에는 다시 손댈 필요가 없을 것입니다. 이 설정을 건너뛸 수 있는 공개 OAUTH 클라이언트 생성은 진행 중입니다.

## 플러그인 설치

- [커뮤니티 플러그인 스토어](https://yukigasai.github.io/obsidian-google-calendar/)에서 원클릭 설치
- 설정으로 이동하여 플러그인 활성화

## Google Calendar 플러그인 설정

Google Cloud 프로젝트에 필요한 URL은 다음과 같습니다.

- 허용된 JavaScript 원본:
	- `http://127.0.0.1:42813`
	- `https://google-auth
- Enable the [UseCustomClient](https://yukigasai.github.io/obsidian-google-calendar/Settings/UseCustomClient) setting
- Insert your [GoogleClientId](https://yukigasai.github.io/obsidian-google-calendar/Settings/GoogleClientId) and [GoogleClientSecret](https://yukigasai.github.io/obsidian-google-calendar/Settings/GoogleClientSecret) in the input fields
- Press Login
	- A browser window will open
- Login / Select your google account
- Google will display a warning that the app is not verified
	1. Click on advanced
	2. Click on go to {project name} (unsafe)
	- The browser will redirect to the consent screen
- Click on allow (Make sure to allow all scopes)

![Example Google Warning](https://yukigasai.github.io/obsidian-google-calendar/exampleGoogleWarning.png)

> Google does not require verification for internal use. This means you can use your unverified app with your google account, as long as you don’t share it with others.