---
title: "옵시디언 대시보드, MOC 만들기"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-moc-%ec%9d%b8%eb%8d%b1%ec%8a%a4-%eb%85%b8%ed%8a%b8/"
author:
  - "[[북트레싱]]"
published: 2024-02-14
created: 2025-07-01
description: "옵시디언 대시보드를 만들고 홈페이지로 지정하는 방법에 대해서 다루겠습니다.대시보드는 MOC 즉 Map of content 라고 부르기도 하고, 인덱스 페이지, 홈페이지 등으로 불리기도 합니다."
tags:
  - "clippings"
---
![북트레싱](https://secure.gravatar.com/avatar/11941127f7b84c939019207d4f24b5d316232341844f140465343801c8cbf3cc?s=80&d=mm&r=g) by

[2월 15, 2024](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-moc-%ec%9d%b8%eb%8d%b1%ec%8a%a4-%eb%85%b8%ed%8a%b8/)

in [책 리뷰](https://booktracing.com/book-reviews/)

A A

[0](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-moc-%ec%9d%b8%eb%8d%b1%ec%8a%a4-%eb%85%b8%ed%8a%b8/#comments)

## 1 홈페이지를 만드는 방법 Dashboard

옵시디언 대시보드를 만들고 홈페이지로 지정하는 방법에 대해서 다루겠습니다.  
대시보드는 MOC 즉 Map of content 라고 부르기도 하고, 인덱스 페이지, 홈페이지 등으로 불리기도 합니다.

대시보드를 만들어서 홈페이지로 지정하거나 대시보드의 노트 링크 안에 대시보드를 추가로 작성하여 입체적인 지식 관리가 가능합니다.

우리가 꼭 기억해야 할 중요한 일이 있을 때 “염두에 둔다” 라는 표현을 자주 사용하듯이 옵시디언에서도 현재 진행중인 프로젝트의 노트 또는, 단기간에 완성하지 못하는 노트가 있다면 그것을 홈페이지에 두고, 단축키 또는 간단히 아이콘을 클릭하는 것 만으로도 접근이 가능하도록 만들 수 있습니다.

![옵시디언 대시보드 MOC](https://booktracing.com/wp-content/uploads/2024/02/02-14-2024-20.30.48-1024x800.webp)

옵시디언 대시보드 MOC

## 2 대시보드 만드는 방법

![](https://www.youtube.com/watch?v=JknCCe1k9UY)

## 3 옵시디언 대시보드(MOC) 만들기

대시보드를 작성하고 적용하기 위해서는 CSS 스니펫을 적용시켜줘야 합니다.  
이는 커뮤니티 플러그인을 설치했던 방법과 차이가 있습니다.

![옵시디언 CSS 적용](https://booktracing.com/wp-content/uploads/2024/02/02-14-2024-20.17.47-1024x317.webp)

옵시디언 CSS 적용

먼저 사용하는 볼트가 저장된 폴더 내의 `.obsidian → snippets` 에.css 파일을 저장을 먼저 해주신 다음에, 옵시디언 \[설정\] – \[테마\]에서 CSS 스니펫에서 활성화를 시켜줘야 합니다.

## 4 대시보드 노트 만들기

가장 새 노트를 만들어주고, 노트의 제목은 자유롭게 만들어 주면 되고, 예시에서는 Home 이라고 만들었습니다.  
대시보드 CSS의 원활한 작동을 위해서 반드시 카테고리의 제목은 heading 2로 입력을 해주셔야 합니다.

그리고 그 아래에 리스트를 만들어 섹션 이름을 지정하고, 하위 항목으로 노트들의 링크를 삽입할 수 있습니다.

![옵시디언 대시보드, MOC 만들기](https://booktracing.com/wp-content/uploads/2024/02/02-14-2024-20.33.15.webp)

옵시디언 대시보드, MOC 만들기

## 5 데이터뷰 인라인 쿼리 사용

대시보드의 아래 부분은 특정한 노트의 리스트를 볼 수 있는 카테고리를 만들었습니다.  
여기에서는 [데이터뷰 플러그인](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/) 의 인라인 쿼리를 사용하여 작성을 하였습니다.

하나를 살펴보면 최근 수정한 노트 5개를 가져오는 쿼리인데, 기본적으로 아래를 응용하여 바꿀 수 있습니다.

\`$=dv.list(dv.pages(”).sort(f=>f.file.mtime.ts,”desc”).limit(5).file.link)\`

폴더를 지정하기 위해서는 pages(“)에 넣어주시면 되고, desc(내림차순)은 ase(오름차순)으로 변경하실 수 있습니다.  
그리고 limit뒤의 괄호 안의 숫자는 대시보드에 보여줄 노트의 개수를 의미합니다.

## 6 대시보드 페이지 작성 예시

```js
---
cssclasses: dashboard
---

## 독서
- 📗 현재 읽고 있는 책
 - [[노트1]]
 - [[노트2]]
- 📕 앞으로 읽을 책
 - [[노트3]]
 - [[노트4]]
- 📘 독서 노트
 - [[독서 노트 작성]]

## 학습
- 💻 코딩 공부
 - [[자바스크립트 기초]]
 - [[파이썬 기초]]
- 💜 옵시디언
 - [[Dataview 플러그인]]
 - [[Templater 플러그인]]

## 유튜브
- 🗒 기획
 - [[03_옵시디언 꾸미기]]
- 🎥 촬영
 - [[02_CSS 적용하기]]
- 🖥 편집
 - [[01_플러그인 활용]]

## 노트 리스트
- 🗃 최근 수정한 노트
  \`$=dv.list(dv.pages('').sort(f=>f.file.mtime.ts,"desc").limit(5).file.link)\`
- 📝 최근 작성한 노트
  \`$=dv.list(dv.pages('').sort(f=>f.file.ctime.ts,"desc").limit(5).file.link)\`
- 📁 폴더: 폴더명
  \`$=dv.list(dv.pages('"폴더명"').sort(f=>f.file.ctime.ts,"desc").limit(5).file.link)\`
- 🔖 태그: 태그명
  \`$=dv.list(dv.pages('#태그명').sort(f=>f.file.name,"desc").limit(5).file.link)\`
- ✅ 완료: 프로젝트
  \`$=dv.list(dv.pages('').where(p => p.source === "값").sort(f=>f.file.name, "asc").limit(5).file.link)\`
```

## 7 dashboard.css 파일

[Dashboard.css 파일 다운로드](https://github.com/BookTracing/dashboard/blob/main/dashboard.css)

위 링크에 접속하여 아래 그림에서 표시된 버튼을 눌러서 다운로드 받을 수 있습니다.

![옵시디언 대시보드, MOC 만들기](https://booktracing.com/wp-content/uploads/2024/02/02-14-2024-21.05.52-1024x378.png)

옵시디언 대시보드, MOC 만들기

## 8 homepage 플러그인

대시보드로 지정할 노트의 작성을 완성한 다음은 ‘homepage’라는 커뮤니티 플러그인을 사용하여 옵시디언의 Home 화면으로 사용할 수 있습니다.이렇게 완성을 해봤는데요.  
이제 작성한 노트를 홈페이지로 지정을 해 주어야 합니다.  

\[옵션\]에서 open when empty를 활성화시켜 주게 되면 옵시디언의 모든 탭을 닫아도 홈 화면이 유지가 됩니다.  
그리고 ‘Opened view’는 기본으로 Default view로 설정이 되어 있지만 dashboard.css 파일을 사용하려면 reading view로 변경하고 사용해야 합니다.

Tags:

[Previous Post](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/)

### [옵시디언 책 정보 수집 플러그인, korean book info 커스텀](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/)

옵시디언 콜아웃 사용법 멀티 칼럼 모듈러 CSS 적용

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

Next Post

[![옵시디언 콜아웃 멀티 칼럼](https://booktracing.com/wp-content/uploads/2024/02/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%BD%9C%EC%95%84%EC%9B%83-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

### 옵시디언 콜아웃 사용법 멀티 칼럼 모듈러 CSS 적용

[![옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/wp-content/uploads/2024/03/tasks-%EC%BA%98%EB%A6%B0%EB%8D%94-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/)

### 옵시디언 할 일 관리를 캘린더 tasks 플러그인

[![옵시디언 지도 위치 표시](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%A7%80%EB%8F%84-%EC%9C%84%EC%B9%98-%ED%91%9C%EC%8B%9C-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/)

### 옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

[![옵시디언 파일 복구 스냅샷](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%ED%8C%8C%EC%9D%BC-%EB%B3%B5%EA%B5%AC-%EC%8A%A4%EB%83%85%EC%83%B7-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

### 옵시디언 파일 복구하기 스냅샷 기능

[![Mac homebrew 홈브류 설치](https://booktracing.com/wp-content/uploads/2024/05/Mac-homebrew-%ED%99%88%EB%B8%8C%EB%A5%98-%EC%84%A4%EC%B9%98-75x75.webp)](https://booktracing.com/mac-homebrew-nodejs-python-terminal/)

### 맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result