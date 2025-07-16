---
title: "맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치"
source: "https://booktracing.com/mac-homebrew-nodejs-python-terminal/"
author:
  - "[[북트레싱]]"
published: 2024-05-03
created: 2025-07-01
description: "MacOS에서 터미널을 이용해 Homebrew를 설치하고 Node.js와 python을 설치하는 방법입니다."
tags:
  - "clippings"
---
by

[5월 3, 2024](https://booktracing.com/mac-homebrew-nodejs-python-terminal/)

in [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/mac-homebrew-nodejs-python-terminal/#comments)

[![Mac homebrew 홈브류 설치](https://booktracing.com/wp-content/uploads/2024/05/Mac-homebrew-%ED%99%88%EB%B8%8C%EB%A5%98-%EC%84%A4%EC%B9%98.webp)](https://booktracing.com/wp-content/uploads/2024/05/Mac-homebrew-%ED%99%88%EB%B8%8C%EB%A5%98-%EC%84%A4%EC%B9%98.webp)

## 1 Homebrew(홈브류) 설치

`Cmd + Spacebar` 를 입력하여 Spotlight 검색창에서 `터미널` 검색하여 실행

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/spotlight-1-1024x110.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/terminal-1024x576.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

### Homebrew 설치

Node.js와 python을 설치하기 전에 우선 **==Homebrew를 설치하면 더욱 쉬운 설치가 가능==** 합니다.

Homebrew는 macOS(또는 Linux) 사용자들이 소프트웨어를 쉽게 설치하고 관리할 수 있도록 도와주는 무료 소프트웨어 도구입니다. 일반적으로 소프트웨어를 설치하기 위해서는 복잡한 설치 과정을 거쳐야 하지만, Homebrew를 사용하면 명령어 한 줄로 소프트웨어를 설치하고 업데이트할 수 있습니다.

Homebrew를 사용하면 `brew install 패키지명` 명령어로 필요한 프로그램을 쉽게 설치할 수 있습니다.

터미널 창에 아래를 복사하여 붙여넣기 후 Enter

`/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"`

\*\* ====만약 설치 중에== **==password==** ==를 입력하라는 메시지가 나오는 경우에는 맥OS 로그인 비밀번호를 입력하시면 됩니다.====

Homebrew가 설치가 완료되면 `brew doctor` 를 입력하여 확인

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/brew-doctor.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

==**Your system is ready to brew**== 메시지를 확인하고 다음을 진행

## 2 node.js 설치

`brew install node` 를 터미널에 입력하여 **==설치를 진행==** 합니다.

참고로 Node.js를 설치하면 **==npm도 자동으로 설치==** 됩니다.

설치가 완료되면,

`node -v` 와 `npm -v` 를 각각 입력하여 **==설치된 버전을 확인==**

`which node` 를 입력해서 ==**설치된 경로를 확인**== 할 수 있습니다.

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/node-%EA%B2%BD%EB%A1%9C-%ED%99%95%EC%9D%B8.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

## 3 Python 설치

파이썬을 설치할 때도 node.js와 마찬가지로 아래를 입력하여 진행할 수 있습니다.

`brew install python` 또는 `brew install --cask anaconda`

비밀번호 입력을 요구 하는 경우에 마찬가지로 **==로그인 비밀번호를 입력==** 하면 되는데 입력할 때 창에 나타나지 않으므로 그냥 입력하시고 엔터를 누르시면 됩니다.

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/%EB%B9%84%EB%B0%80%EB%B2%88%ED%98%B8-%EC%9E%85%EB%A0%A5-1024x57.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

이렇게 설치가 완료되면,

`python -V` 으로 설치된 파이썬 버전을 확인할 수 있습니다. (여기서 중요한 점은 **==V==** 가 소문자가 아니라 **==대문자==** 라는 것입니다.

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/%ED%84%B0%EB%AF%B8%EB%84%90-%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%B2%84%EC%A0%84-%ED%99%95%EC%9D%B8.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

만약 `python -v` 로 입력하여 확인한 경우에는 인터렉티브 모드로 진입이 되는데

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EB%B2%84%EC%A0%84-%ED%99%95%EC%9D%B8-1-1024x153.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

`>>>` (인터렉티브 모드)에서 나오려면 `quit()` 를 입력해서 기본 셸 모드로 돌아갈 수 있습니다.

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/%EA%B8%B0%EB%B3%B8-%EC%85%B8-1024x88.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

### 파이썬 경로 확인

![맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치](https://booktracing.com/wp-content/uploads/2024/05/%ED%8C%8C%EC%9D%B4%EC%8D%AC-%EA%B2%BD%EB%A1%9C-%ED%99%95%EC%9D%B8.webp)

맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

### [옵시디언 파일 복구하기 스냅샷 기능](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

Next Post

[View original](https://booktracing.com/chocolatey-nodejs-powershell/)

Next Post

[![윈도우 chocolatey 초코 설치](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-chocolatey-%EC%B4%88%EC%BD%94-%EC%84%A4%EC%B9%98-75x75.webp)](https://booktracing.com/chocolatey-nodejs-powershell/)

### 윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

[![옵시디언 CSS 테마](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-CSS-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

### 옵시디언 CSS 테마 텍스트 편집기 설정

[![메타데이터 메뉴 플러그인](https://booktracing.com/wp-content/uploads/2024/07/%EB%A9%94%ED%83%80%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%A9%94%EB%89%B4-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/)

### 메타데이터 메뉴 (metadata menu) 플러그인, (데이터뷰 테이블)

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result