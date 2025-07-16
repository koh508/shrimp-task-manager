---
title: "옵시디언 할 일 관리를 캘린더 tasks 플러그인"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/"
author:
  - "[[북트레싱]]"
published: 2024-03-27
created: 2025-07-01
description: "한 눈에 볼 수 있는 캘린더 tasks 플러그인을 활용할 수 있습니다."
tags:
  - "clippings"
---
by

[4월 5, 2024](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/), [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/#comments)

[![옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/wp-content/uploads/2024/03/tasks-%EC%BA%98%EB%A6%B0%EB%8D%94.webp)](https://booktracing.com/wp-content/uploads/2024/03/tasks-%EC%BA%98%EB%A6%B0%EB%8D%94.webp)

## 1 캘린더 tasks

옵시디언을 사용하면서 tasks 플러그인을 활용하여 할 일을 관리할 수 있습니다.

하지만 아래와 같이 입력을 하게 되면 결괏값은 리스트 형식으로만 출력이 되기 때문에 한 눈에 여러 할 일을 파악하는 것이 쉽지 않습니다.

```js
\`\`\`tasks
\`\`\`
```

이번에 소개해드릴 tasksCalendar 플러그인을 활용하면 리스트뷰, 캘린더뷰, 위클리뷰 등으로 할 일을 볼 수 있습니다.

한 눈에 볼 수 있는 캘린더 tasks 플러그인을 활용할 수 있습니다.

tasksCalendar 플러그인은 옵시디언 내에서 설치가 가능하지 않으며, 깃허브를 통해서 다운로드 받을 수 있습니다.

그리고 이 플러그인을 사용하기 위해서는 우선 [Tasks 플러그인](https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/) 과 [Dataview 플러그인](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/) 이 필수적으로 설치가 되어있어야 합니다.

![옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/wp-content/uploads/2024/03/%EC%BA%98%EB%A6%B0%EB%8D%94-%EB%B7%B0-1024x644.webp)

옵시디언 할 일 관리를 캘린더 tasks 플러그인

![옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/wp-content/uploads/2024/03/%EC%9C%84%ED%81%B4%EB%A6%AC-%EB%B7%B0-1024x643.webp)

옵시디언 할 일 관리를 캘린더 tasks 플러그인

## 2 tasksCalendar 설명 영상

![](https://www.youtube.com/watch?v=fl_ExilH9to)

## 3 tasks-calendar 플러그인 다운로드

아래 버튼을 클릭, 링크로 이동하여 플러그인을 다운로드 받으실 수 있고, 다운로드 받은 파일에서 \`tasksCalendar\`를 그대로 옵시디언 볼트의 최상단에 복사하여 사용할 수 있습니다.

[Tasks-Calendar 플러그인](https://vo.la/xDwoW)

폴더 내에는 view.css, view.js, demo\_file.md 파일이 포함되어 있습니다.

## 4 사용

옵시디언에서 demo\_file.md 파일을 열어보면 아래와 같은 코드가 기본으로 작성되어 있습니다.

이 코드는 따로 노트를 만들어서 사용하실 수도 있고, 기존의 노트에 추가하여 사용을 할 수도 있기 때문에 필요에 따라 활용하시면 되겠습니다.

```js
\`\`\`dataviewjs

await dv.view("tasksCalendar", {

pages: "",
view: "month",
firstDayOfWeek: "1",
options: "style1"

})

\`\`\`
```

dataviewjs 코드로 작성이 되어 있고, pages, view, firstDayOfWeek, options 이 네 가지는 기본적으로 작성이 되어야 정상적으로 작동을 합니다.

그리고 쿼리를 작성하실 때 **==대소문자 구분==** 은 반드시 해줘야 합니다.

### pages

할 일을 가져오는 방법을 설정할 수 있습니다. 기본적으로 폴더나 태그 등에서 가져올 수 있고, 예시로 폴더를 설정하는 방법과 태그를 설정하는 방식으로 설명하겠습니다.

#### 폴더

아래 ‘폴더 이름’ 이라고 작성된 부분에 각자의 폴더 경로를 적어주면 됩니다. 폴더에 상위 폴더가 있는 경우에는 상위 폴더를 포함한 경로를 입력할 수 있습니다.

```js
pages:"dv.pages().file.where(f=>f.folder === '폴더 이름').tasks"
```

#### 태그

```js
pages: "dv.pages().file.tasks.where(t => t.tags.includes('#태그'))"
```

### view

view는 3가지로 설정이 가능하고, `view: "list"`, `view: "month"`, `view: "week"` 로 작성이 가능합니다.

처음 노트를 열었을 때 기본 화면을 설정하는 것으로 캘린더 뷰인 “month”가 가장 활용도가 좋을 것이라 생각합니다.

### firstDayOfWeek

숫자 ‘0’과 ‘1’ 로 설정이 가능하며, `firstDayOfWeek: "0"` 형식으로 입력할 수 있습니다.

‘0’은 한 주의 시작을 일요일로 설정하는 것이고, ‘1’은 월요일로 설정합니다.

### options

기본적으로 ‘style’이 입력되어 있습니다. style뒤에 숫자 1부터 11까지 입력하여 변경이 가능한데, 노트를 열게 되면 초기에 표시되는 형식을 지정해주는 것입니다.

`week` 아이콘을 눌러서 확인을 해보실 수 있습니다.

그 외에도 옵션에는 많은 것들을 추가로 입력하실 수 있습니다. 옵션을 입력하는 방식은 `options: "옵션1 옵션2 옵션3"` 형식으로 **==옵션 사이에는 스페이스바를 눌러서 한 칸의 띄워야 합니다.==**

#### noProcess

`options: "noProcess"` 형식으로 입력이 가능하고, 할 일의 시작일과 마감일 사이의 날짜들에 할 일을 표시하지 않습니다. 이는 due date만 입력했을 때는 나타나지 않고, 시작 날짜를 입력해야 나타나게 됩니다.

#### noCellNameEvent

`options: "noCellNameEvent` 형식으로 입력 가능하고, 날짜를 눌러서 데일리 노트로 이동하는 동작을 비활성화 시켜줍니다.

#### mini

`options: "mini"` 로 입력할 수 있고, 노트에 표시되는 플러그인의 크기를 줄여줍니다.

#### noWeekNr

`options: "noWeekNr"` 로 입력하고 캘린더의 좌측에서 주차 번호를 숨길 수 있습니다.

#### noFilename

`options: "noFilename"` 을 입력하게 되면 캘린더에서 노트의 제목을 숨길 수 있습니다. 할 일이 많이 등록된 경우 불필요한 노트 제목을 제거함으로써 더욱 많은 할 일을 캘린더에 나타낼 수 있습니다.

#### lineClamp

```js
options: "lineClamp1"
options: "lineClamp2"
options: "lineClamp3"
options: "noLineClamp"
```

위와 같은 형식으로 입력이 가능하고, 캘린더에 표시되는 할 일의 행의 개수를 조절할 수 있습니다. 기본적으로 한 줄로 표시가 됩니다.

#### noLayer

`options: "noLayer"` 를 입력하게 되면 캘린더에 표시되는 해당 월의 글자를 숨길 수 있습니다.

## 5 데일리 노트 경로와 제목 설정

### 데일리 노트의 경로

캘린더에서 날짜를 클릭했을 때 데일리 노트로 이동하게 되는데, 설정을 따로 해주지 않은 경우에는 옵시디언에 기본으로 설정된 폴더에 새로운 데일리 노트가 생성되기 때문에 반드시 설정을 하시는 걸 추천드립니다.

`dailyNoteFolder: "데일리노트 폴더명"` 데일리 노트가 저장된 폴더의 경로를 지정할 수 있습니다. 데일리 노트가 하위 폴더인 경우에는 상위폴더를 포함한 경로를 작성해주어야 합니다.

### 데일리 노트 제목 포맷 설정

플러그인의 설명에서는 아래와 같이 입력하여 설정이 가능하다고 설명하고 있지만 실제로는 작동하지 않습니다.

```js
dailyNoteFormat: "YYYY, MMMM DD - dddd"
dailyNoteFormat: "YYYY-[W]ww"
```

그렇기 때문에 view.js 파일을 직접 변경해주어야 하는데, 우선.js 파일을 열어서 `YYYY-MM-DD` 로 검색을 해서 본인의 데일리 노트 포맷으로 변경해주어야 합니다.

검색을 진행하게 되면 결과는 총 12개가 나오게 되고, `YYYY-MM-DD(ddd)` 형식으로 변경하게 되면, `2024-03-27(화)` 형식으로 데일리 노트가 생성 및 이동하게 됩니다.

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

### [옵시디언 콜아웃 사용법 멀티 칼럼 모듈러 CSS 적용](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/)

Next Post

[![옵시디언 지도 위치 표시](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%A7%80%EB%8F%84-%EC%9C%84%EC%B9%98-%ED%91%9C%EC%8B%9C-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/)

### 옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

[![옵시디언 파일 복구 스냅샷](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%ED%8C%8C%EC%9D%BC-%EB%B3%B5%EA%B5%AC-%EC%8A%A4%EB%83%85%EC%83%B7-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

### 옵시디언 파일 복구하기 스냅샷 기능

[![Mac homebrew 홈브류 설치](https://booktracing.com/wp-content/uploads/2024/05/Mac-homebrew-%ED%99%88%EB%B8%8C%EB%A5%98-%EC%84%A4%EC%B9%98-75x75.webp)](https://booktracing.com/mac-homebrew-nodejs-python-terminal/)

### 맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

[![윈도우 chocolatey 초코 설치](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-chocolatey-%EC%B4%88%EC%BD%94-%EC%84%A4%EC%B9%98-75x75.webp)](https://booktracing.com/chocolatey-nodejs-powershell/)

### 윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

[![옵시디언 CSS 테마](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-CSS-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

### 옵시디언 CSS 테마 텍스트 편집기 설정

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result