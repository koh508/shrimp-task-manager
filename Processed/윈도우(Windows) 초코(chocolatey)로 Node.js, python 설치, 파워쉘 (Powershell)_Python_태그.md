---
title: "윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)"
source: "https://booktracing.com/chocolatey-nodejs-powershell/"
author:
  - "[[북트레싱]]"
published: 2024-05-03
created: 2025-07-01
description: "윈도우의 Powershell을 이용하여 chocolatey, node.js, python을 설치 및 경로 확인 방법입니다"
tags:
  - "clippings"
---
![북트레싱](https://secure.gravatar.com/avatar/11941127f7b84c939019207d4f24b5d316232341844f140465343801c8cbf3cc?s=80&d=mm&r=g) by

[5월 3, 2024](https://booktracing.com/chocolatey-nodejs-powershell/)

in [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/chocolatey-nodejs-powershell/#comments)

[![윈도우 chocolatey 초코 설치](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-chocolatey-%EC%B4%88%EC%BD%94-%EC%84%A4%EC%B9%98.webp)](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-chocolatey-%EC%B4%88%EC%BD%94-%EC%84%A4%EC%B9%98.webp)

## 1 윈도우 Powershell 실행

![윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-%ED%8C%8C%EC%9B%8C%EC%89%98-1024x560.webp)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

검색에 `cmd` 또는 `명령 프롬프트` 를 검색하고 우측에 있는 **==관리자 권한으로 실행==**

## 2 chocolatey (choco:초코)설치

아래를 복사하여 PowerShell에 붙여넣고 choco 설치

`[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))`

## 3 Node.js 설치

Node.js를 설치하는 방법은 여러가지가 있지만 바로 Node.js를 설치하는 방법과 NVM의 설치를 먼저 진행한 다음 Node.js를 설치하는 방법 등이 있습니다.

### Nodejs 바로 설치

PowerShell에서 `choco install nodejs` 를 입력해주면 설치가 진행됩니다.

![윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)](https://booktracing.com/wp-content/uploads/2024/05/choco-nodejs-1024x402.webp)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

(위의 이미지는 이미 설치가 되었기 때문에 추가로 설치가 진행되지 않았고 이미 설치가 되었다는 메시지를 출력합니다.)

`node -v` 를 입력해서 설치가 제대로 되었는지 버전을 확인할 수 있습니다.

![윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)](https://booktracing.com/wp-content/uploads/2024/05/nodejs-%EB%B2%84%EC%A0%84-%ED%99%95%EC%9D%B8.webp)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

### 설치 경로 확인

`(Get-Command node).Path` 을 실행시켜 설치 경로를 확인할 수 있습니다.

### NVM(Node Version Manager) 설치

두 번째 방법으로는 NVM (Node Version Manager)은 Node.js의 여러 버전을 관리할 수 있게 해주는 도구입니다.

이를 사용하면 여러 Node.js 버전을 쉽게 설치, 전환 및 사용을 할 수 있습니다.

위에서 설치한 초코(chocolatey)를 이용하여 쉽게 설치가 가능합니다. 아래의 명령을 복사해서 PowerShell에 붙여넣기 실행시키면 설치가 진행됩니다.

`choco install nvm` 로 먼저 nvm의 설치를 진행해주시고, `nvm install node` 을 입력하시면 최신 버전이 자동으로 설치됩니다.

그리고 마찬가지로 `node -v` 를 입력하시면 설치된 버전을 확인할 수 있습니다.

## 4 파이썬(Python) 설치

파이썬의 설치도 nodejs와 마찬가지로 chocolatey를 이용하여 진행할 수 있습니다.

똑같이 PowerShell을 관리자 권한으로 실행을 시켜주시고 입력창에 `choco install python` 을 입력하고 엔터를 눌러줍니다.

![윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)](https://booktracing.com/wp-content/uploads/2024/05/%EC%B4%88%EC%BD%94-%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EC%84%A4%EC%B9%98-1024x397.webp)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

설치 진행 중에 **==Do you want to run the script?==** 메시지가 출력되면 **==A==** 를 입력하면 설치가 계속 진행됩니다.

![윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)](https://booktracing.com/wp-content/uploads/2024/05/%EC%B4%88%EC%BD%94-%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EC%84%A4%EC%B9%98-%EC%99%84%EB%A3%8C-1024x603.webp)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

설치가 완료되면 설치된 내용이 출력됩니다.

그리고 설치된 파이썬 버전을 확인하려면 `python -V` 를 입력해야 합니다. 여기서 중요한 점은 V가 소문자가 아닌 대문자라는 점입니다.

![윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%B2%84%EC%A0%84-%ED%99%95%EC%9D%B8.webp)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

### 파이썬 설치 경로 확인

Powershell에 `(Get-Command python).Path` 을 입력하여 파이썬의 설치 경로를 확인할 수 있습니다.

Tags:

[Previous Post](https://booktracing.com/mac-homebrew-nodejs-python-terminal/)

### [맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/mac-homebrew-nodejs-python-terminal/)

옵시디언 CSS 테마 텍스트 편집기 설정

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

Next Post

[![옵시디언 CSS 테마](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-CSS-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

### 옵시디언 CSS 테마 텍스트 편집기 설정

[![메타데이터 메뉴 플러그인](https://booktracing.com/wp-content/uploads/2024/07/%EB%A9%94%ED%83%80%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%A9%94%EB%89%B4-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/)

### 메타데이터 메뉴 (metadata menu) 플러그인, (데이터뷰 테이블)

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result