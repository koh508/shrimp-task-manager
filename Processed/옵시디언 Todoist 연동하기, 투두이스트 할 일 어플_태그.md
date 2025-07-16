---
title: "옵시디언 Todoist 연동하기, 투두이스트 할 일 어플"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-todoist-%ed%88%ac%eb%91%90%ec%9d%b4%ec%8a%a4%ed%8a%b8-%ec%97%b0%eb%8f%99/"
author:
  - "[[북트레싱]]"
published: 2024-01-17
created: 2025-07-01
description: "옵시디언 todoist 와의 연동을 통해서 더욱 생산성을 높이고 스마트폰에서도 옵시디언의 할 일 관리를 가능하도록 도와줍니다."
tags:
  - "clippings"
---
by

[1월 17, 2024](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-todoist-%ed%88%ac%eb%91%90%ec%9d%b4%ec%8a%a4%ed%8a%b8-%ec%97%b0%eb%8f%99/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/), [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-todoist-%ed%88%ac%eb%91%90%ec%9d%b4%ec%8a%a4%ed%8a%b8-%ec%97%b0%eb%8f%99/#comments)

[![옵시디언-todoist-투두이스트](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-todoist-%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8.webp)](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-todoist-%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8.webp)

## 1 옵시디언 Todoist 연동

Todoist는 전세계적으로 3천만 명 이상의 사용자가 있는 할 일 어플입니다.

앱 스토어와 플레이 스토어에서도 많은 사용자들에 의해 좋은 평가를 받고 있으며, 무료/유료 서비스를 제공합니다.

![옵시디언 Todoist 연동하기, 투두이스트 할 일 어플](https://booktracing.com/wp-content/uploads/2024/01/%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8-%EC%95%84%EC%9D%B4%ED%8F%B0.webp)

옵시디언 Todoist 연동하기, 투두이스트 할 일 어플

![옵시디언 Todoist 연동하기, 투두이스트 할 일 어플](https://booktracing.com/wp-content/uploads/2024/01/%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8-%EB%AC%B4%EB%A3%8C-%EC%9C%A0%EB%A3%8C.webp)

옵시디언 Todoist 연동하기, 투두이스트 할 일 어플

### 옵시디언에서 투두이스트 사용

옵시디언에서 Todoist를 사용하기 위해서는 두 개의 어플을 사용하여 상호보완을 할 수 있습니다.

Ultimate Todoist Sync어플은 옵시디언에 할 일을 등록하고 등록한 할 일을 Todoist로 보내주는 역할을 하고, Todoist Sync Plugin은 Todoiost에 등록된 할 일을 실시간으로 불러오는 기능을 합니다.

옵시디언과 Todoist를 연동하기 위해서는 API가 필요하며, API 토큰을 받는 방법은 영상에서 소개하고 있습니다.

## 2 옵시디언과 Todoist 연동

![](https://www.youtube.com/watch?v=iEWXK22L6gA)

## 3 Ultimate Todoist Sync

예전에 언급했던 Tasks 플러그인의 사용법과 유사한 점이 많아서, Tasks 플러그인을 설치하지 않았다면 설치를 하고 사용하는 것을 권장합니다.

아래와 같이 작성하는데 체크박스를 입력하려면 단축키 cmd+L로도 가능합니다.  

### 프로젝트

투두이스트 내의 프로젝트 이름 앞에 `#` 을 붙여주게 되면 할 일이 자동으로 프로젝트로 이동을 하고,  
`#todoist` 를 넣어주면 자동으로 할 일의 뒤에 todoist id 가 생성되어야 정상적인 등록이 된 것입니다.

프로젝트는 무료 계정의 경우 최대 5개 까지 생성이 가능합니다.

![옵시디언 Todoist 연동하기, 투두이스트 할 일 어플](https://booktracing.com/wp-content/uploads/2024/01/%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8-%ED%94%84%EB%A1%9C%EC%A0%9D%ED%8A%B8.webp)

옵시디언 Todoist 연동하기, 투두이스트 할 일 어플

### 우선 순위

우선 순위는 `!!2` 로 입력하게 되면 중요도가 P2가 아닌 P3인 일로 입력이 됩니다.  
참고로 중요도는 P1~P4 까지 4단계가 있는데 입력을 할 때는 P1=!!4, P4=!!1로 입력을 해야하는 오류가 있습니다.

### 작성 예시

```js
- [ ] 할 일 📅날짜 !!2 #프로젝트이름 #todoist
```

기본적으로 할 일이 자동으로 투두이스트로 이동하게 되고, 체크박스를 눌러 완료를 시키거나, 할 일 또는 날짜 등의 변경도 가능합니다.

## 4 Todoist Sync Plugin

```js
\`\`\`todoist 로 시작하는 블록 코드를 만들어서 입력 가능
```

### 기본적인 사용법의 예시

```js
\`\`\`todoist
name: Todoist 할 일 ({task_count})
filter: "(today | tomorrow) & P1 "
group: true
sorting:
- priority
- date
\`\`\`
```

### 필터 (filter) 예시

- `#project이름`: 프로젝트 이름 앞에 `#` 을 추가하면 프로젝트 내의 할 일을 필터링
- `today`,`tomorrow`,`yesterday` 등의 자연어의 입력이 가능
- `overdue`: due date가 지난 일들
- `P1`,`P2`,`P3`,`P4`: 중요도 (P1이 가장 중요도가 높음)
- `group`: 프로젝트를 그룹별도 묶여서 표시해 줌
- `sorting`: 정렬을 하는 기준을 입력

#### 기호 설명

`&`, `|`, `(`, `)`, `,` 등의 기호를 필터 사이에 넣을 수 있음

![옵시디언 Todoist 연동하기, 투두이스트 할 일 어플](https://booktracing.com/wp-content/uploads/2024/01/%ED%95%84%ED%84%B0-%EA%B8%B0%ED%98%B8.webp)

옵시디언 Todoist 연동하기, 투두이스트 할 일 어플

[todoist 필터](https://todoist.com/ko/help/articles/introduction-to-filters-V98wIH) 참고

### 날짜 기간 입력하는 방법

- `due after: 날짜` 에서 날짜 부분의 날은 포함하지 않고 그 이후의 날을 계산합니다.
- `due before:날짜` 역시 날짜 부분을 날을 제외하고 그 이전의 날까지만 계산합니다.

### 데일리 노트 기간 적용 예시

```js
filter: "due after:<% tp.file.title.slice(0,10) %> & due before:<%* const extractedDate = tp.file.title.slice(0, 10); const currentDate = new Date(extractedDate); currentDate.setDate(currentDate.getDate() + 5); const formattedDate = currentDate.toISOString().split('T')[0]; tR += formattedDate; %>"
```

위의 코드에서 `currentDate.getDate() + 숫자` 부분에서 숫자를 바꿔서 사용 가능합니다.

반드시 Templater 플러그인이 설치가 되어 있어야 실행이 가능하고, 사용법은 [데일리 노트](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/) 를 참고하세요

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-tracker-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%8a%b5%ea%b4%80/)

### [월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-tracker-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%8a%b5%ea%b4%80/)

옵시디언 미니멀 테마 추천, 카드뷰, 갤러리뷰

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%af%b8%eb%8b%88%eb%a9%80-%ed%85%8c%eb%a7%88-%ec%b9%b4%eb%93%9c%eb%b7%b0-%ea%b0%a4%eb%9f%ac%eb%a6%ac%eb%b7%b0/)

Next Post

[![옵시디언 미니멀 테마](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%AF%B8%EB%8B%88%EB%A9%80-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%af%b8%eb%8b%88%eb%a9%80-%ed%85%8c%eb%a7%88-%ec%b9%b4%eb%93%9c%eb%b7%b0-%ea%b0%a4%eb%9f%ac%eb%a6%ac%eb%b7%b0/)

### 옵시디언 미니멀 테마 추천, 카드뷰, 갤러리뷰

[![책 정보 수집 플러그인](https://booktracing.com/wp-content/uploads/2024/02/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-8-75x75.webp)](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/)

### 옵시디언 책 정보 수집 플러그인, korean book info 커스텀

### 옵시디언 대시보드, MOC 만들기

[![옵시디언 콜아웃 멀티 칼럼](https://booktracing.com/wp-content/uploads/2024/02/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%BD%9C%EC%95%84%EC%9B%83-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

### 옵시디언 콜아웃 사용법 멀티 칼럼 모듈러 CSS 적용

[![옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/wp-content/uploads/2024/03/tasks-%EC%BA%98%EB%A6%B0%EB%8D%94-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/)

### 옵시디언 할 일 관리를 캘린더 tasks 플러그인

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result