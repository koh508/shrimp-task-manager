---
title: "템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%85%9c%ed%94%8c%eb%a6%bf-templater-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8/"
author:
  - "[[북트레싱]]"
published: 2023-12-27
created: 2025-07-01
description: "옵시디언에는 이미 기본적으로 코어 플러그인으로 템플릿을 사용할 수도 있지만, Templater 플러그인을 사용하게 되면, 기본 기능에서 제공하지 않는, 많은 기능들이 추가 되어있기 때문에 옵시디언의 필수 플러그인 중 하나라고 생각합니다."
tags:
  - "clippings"
---
by

[1월 21, 2024](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%85%9c%ed%94%8c%eb%a6%bf-templater-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/), [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%85%9c%ed%94%8c%eb%a6%bf-templater-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8/#comments)

[![Templater 플러그인 사용법](https://booktracing.com/wp-content/uploads/2023/12/Templater-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-%EC%82%AC%EC%9A%A9%EB%B2%95-750x750.webp)](https://booktracing.com/wp-content/uploads/2023/12/Templater-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-%EC%82%AC%EC%9A%A9%EB%B2%95.webp)

## 1 Templater 플러그인 사용 방법

옵시디언에는 이미 기본적으로 코어 플러그인으로 템플릿을 사용할 수도 있지만, Templater 플러그인을 사용하게 되면, 기본 기능에서 제공하지 않는, 많은 기능들이 추가 되어있기 때문에 옵시디언의 필수 플러그인 중 하나라고 생각합니다.

특히 데일리나 위클리 노트 작성에 [Tasks 플러그인](https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/) 과 함께 활용한다면 더욱 생산성을 올릴 수 있습니다.

이번 글에서는 Templater를 어떻게 활용하는지와 사의 사용법에 대해 알아보겠습니다.

### 영상

영상은 총 2 편으로 제작이 되었으며,

1편 – 설치 및 Templater 명령어 설명

![](https://www.youtube.com/watch?v=17tThWhNNGw)

2편 – 템플릿 제작 및 설정

![](https://www.youtube.com/watch?v=Q2-aHQKEOHs)

## 2 템플릿 개념 설명

먼저 가볍게 템플릿의 개념에 대해 간단히 설명을 드리면, 템플릿은 우리 주변에서 자주 볼 수 있는 화이트 보드에 있는 월간 계획표와 같은 개념이라고 생각하시면 되겠습니다.

![템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인](https://booktracing.com/wp-content/uploads/2023/12/%EC%9B%94%EA%B0%84-%EA%B3%84%ED%9A%8D%ED%91%9C.webp)

템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인

월간 계획표에 매월 새로운 정보를 기입하지만 기본적으로 변하지 않는 구조가 있습니다.

이 구조를 옵시디언에서 템플릿으로 만들어서 사용하게 되면 반복되는 작업에서 아주 유용하게 활용이 가능합니다.

우리가 새 노트를 생성하고 문서 작성을 시작하기 전에 넣어야 할 반복적인 것들, 예를 들어서 프론트매터에 들어갈 내용이나, 글의 구조 등을 미리 분류해서 템플릿으로 작성하고, 필요에 따라서 불러오기만 하면 되니까 일관적인 형식의 글을 작성하거나 시간 단축에도 도움이 됩니다.

그리고 옵시디언에서 Templater를 사용하면 코어 플러그인으로 설치된 기본 템플릿의 기능과는 다르게 동적인 데이터를 넣을 수 있기 때문에 좀 더 디지털의 장점을 느끼실 수 있습니다.

## 3 Templater 기본 활용 방법

Templater 플러그인의 명령어의 시작은 `<%` 로 합니다.

그리고 templater의 약자인 `tp` 를 입력하고 `.`을 입력하면, 아래와 같은 메뉴가 나타나게 됩니다.

![템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인](https://booktracing.com/wp-content/uploads/2023/12/%ED%85%9C%ED%94%8C%EB%A0%88%EC%9D%B4%ED%84%B0-%EB%AA%85%EB%A0%B9%EC%96%B4-%EC%9E%85%EB%A0%A5.webp)

템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인

첫 단계에서 주로 많이 쓰이는 명령어는 date, file, system입니다.

하나를 선택해서 입력하고 다시 `.`를 입력하면 2단계로 선택할 수 있는 메뉴가 나옵니다.

![템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인](https://booktracing.com/wp-content/uploads/2023/12/12-25-2023-21.32.53.webp)

템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인

이런식으로 단계별로 입력해 나갈 수 있고, 입력 방법은 기본적으로 설명을 해주고 있으니 천천히 읽어보시고, 필요한 명령어를 선택하시면 되겠습니다.

## 4 날짜 및 시간 입력 포멧

### 날짜 입력

날짜를 입력하는 형식은 templater의 명령어 뿐만 아니라, 웹 기반의 모든 프로그램에서 똑같이 활용이 가능합니다.

예를 들어 2023-12-25를 출력하고 싶으면 ` YYYY-MM-DD` 형식으로 입력할 수 있습니다.

- 2024년 1월 2일 월요일
- YYYY: 2024
- YY: 24
- MM: 01
- M: 1
- DD: 02
- D: 2

dddd: 월요일

### 시간 입력

예를 들어 오전 3시 12분을 출력하고 싶으면 `a h시 mm분` 형식으로 입력할 수 있습니다.

오후 1시 8분

- a: 오전 또는 오후
- H: 13
- h: 1
- mm: 08
- m: 8

## 5 Templater 명령어 입력 예시

아래를 복사해서 옵시디언 노트에 그대로 붙여넣고 필요한 부분을 골라 사용하실 수 있습니다.

명령어 사용에 관한 자세한 내용과 활용 방법은 영상에서 확인바랍니다.

참고로 Templater 플러그인 영상은 총 2부로 나눠서 제작이 되었습니다.

```js
## tp.title
<% tp.file.title %>
### 노트 제목
<% tp.file.title.slice(9) %> 
<% tp.file.title.slice(0, 3) %>
<% tp.file.title.split("+")[1] %>
### 노트 생성 날짜
<% tp.file.creation_date("YYYY-MM-DD") %>
<% tp.file.creation_date("YYYY년 M월 D일 dddd") %>
### 노트 저장 폴더
<% tp.file.folder() %>
### 노트의 최근 수정 날짜
<% tp.file.last_modified_date("YYYY-MM-DD") %>
### 노트의 PC 경로
<% tp.file.path() %>
## tp date
<% tp.date.now("YYYY-MM-DD"%>
<% tp.date.tomorrow("YYYY-MM-DD"%>
<% tp.date.yesterday("YYYY-MM-DD"%>
### 주간 날짜
한 주의 시작 - 설정 
일요일 <% tp.date.weekday("YYYY-MM-DD", 0) %>
월요일 <% tp.date.weekday("YYYY-MM-DD", 1) %>
화요일 <% tp.date.weekday("YYYY-MM-DD", 2) %>
## tp.system
### 클립 보드
<% tp.system.clipboard() %>
### 드롭다운 메뉴
<% tp.system.suggester(
["별5개", "별4개", "별3개", "별2개", "별1개"],
["★★★★★", "★★★★☆", "★★★☆☆", "★★☆☆☆", "★☆☆☆☆"]
) %>
### 텍스트 필드
<% tp.system.prompt("하나의 키워드로 정리하면?", "") %>
```

Tags:

[Previous Post](https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/)

### [옵시디언 플러그인 Tasks 필터링 구문 할 일 목록](https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/)

옵시디언 데일리 노트를 만들어 2024년, 새롭게 시작해보자

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/)

Next Post

[![옵시디언 데일리 노트 템플릿](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%BC%EB%A6%AC-%EB%85%B8%ED%8A%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/)

### 옵시디언 데일리 노트를 만들어 2024년, 새롭게 시작해보자

[![옵시디언 데이터뷰 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B7%B0-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/)

### 플러그인 중 가장 강력한 옵시디언 데이터뷰, dataview

[![옵시디언 주간 계획 위클리 노트](https://booktracing.com/wp-content/uploads/2024/01/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-4-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a3%bc%ea%b0%84-%ea%b3%84%ed%9a%8d-%ec%9c%84%ed%81%b4%eb%a6%ac-%eb%85%b8%ed%8a%b8/)

### 옵시디언 주간 계획을 자동화해서 더욱 강력한 생산성 향상

[![옵시디언 Tracker 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-Tracker-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-tracker-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%8a%b5%ea%b4%80/)

### 월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인

[![옵시디언-todoist-투두이스트](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-todoist-%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-todoist-%ed%88%ac%eb%91%90%ec%9d%b4%ec%8a%a4%ed%8a%b8-%ec%97%b0%eb%8f%99/)

### 옵시디언 Todoist 연동하기, 투두이스트 할 일 어플

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result