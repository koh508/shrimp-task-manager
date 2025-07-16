---
title: "옵시디언 책 정보 수집 플러그인, korean book info 커스텀"
source: "https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/"
author:
  - "[[북트레싱]]"
published: 2024-02-10
created: 2025-07-01
description: "안녕하세요 북트레싱입니다.웹에서 책 정보를 불러오는 플러그인인 korean book info를 커스텀하여 사용할 수 있는 방법입니다.이 책 정보 수집 플러그인은 YES24 홈페이지에서 추출하여, 한 번의 클릭만으로 나만의 서재를 만들 수 있게 도와줍니다."
tags:
  - "clippings"
---
![북트레싱](https://secure.gravatar.com/avatar/11941127f7b84c939019207d4f24b5d316232341844f140465343801c8cbf3cc?s=80&d=mm&r=g) by

[2월 10, 2024](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/), [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/#comments)

[![책 정보 수집 플러그인](https://booktracing.com/wp-content/uploads/2024/02/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-8.webp)](https://booktracing.com/wp-content/uploads/2024/02/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-8.webp)

## 1 책 정보 수집 플러그인 커스텀하기

안녕하세요 북트레싱입니다.  
웹에서 책 정보를 불러오는 플러그인인 korean book info를 커스텀하여 사용할 수 있는 방법입니다.  
이 책 정보 수집 플러그인은 YES24 홈페이지에서 추출하여, 한 번의 클릭만으로 나만의 서재를 만들 수 있게 도와줍니다.

플러그인의 제한적인 부분을 내 입맛에 맞춰 변경할 수 있는 방법을 살펴보겠습니다.

## 2 main.js 파일 찾기

### 맥OS

Finder를 열고 Valut가 설치되어 있는 폴더로 이동하여 단축키 `Shift + Cmd + .`를 입력하게 되면 숨겨져 있던 파일들이 보이게 됩니다.

![맥 숨김 파일 표시](https://booktracing.com/wp-content/uploads/2024/02/02-10-2024-15.19.22.webp)

맥 숨김 파일 표시

`.obsidian → plugins → kr-book-info-plugin → main.js`

경로로 이동하여 파일을 열어 줍니다. 이때 텍스트 편집기를 이용해서도 편집이 가능하고, 코드를 좀 더 보기 쉽게 [VS CODE 프로그램](https://code.visualstudio.com/download) 을 설치하여 사용하면 더욱 좋습니다.

### 윈도우

윈도우는 `보기 → 표시 → 숨긴 항목` 버튼을 눌러 숨겨진 파일을 볼 수 있습니다.

![옵시디언 책 정보 수집 플러그인, korean book info 커스텀](https://booktracing.com/wp-content/uploads/2024/02/02-10-2024-15.25.13-1.webp)

옵시디언 책 정보 수집 플러그인, korean book info 커스텀

맥OS와 동일한 폴더에 main.js 파일이 저장되어 있고, 메모장 또는 vs code를 이용하여 편집이 가능합니다.

## 3 코드 수정하기

main.js 파일을 열어보면 수많은 코드가 있는데, 맥은 `Cmd + F`, 윈도우는 `Ctrl + F` 를 눌러서 검색 창에 frontmatter를 입력하여 해당 부분으로 이동합니다.

![옵시디언 프론트매터 정보](https://booktracing.com/wp-content/uploads/2024/02/02-10-2024-15.31.03.webp)

옵시디언 프론트매터 정보

`:`을 기준으로 좌측은 Key, 우측은 Value를 넣어줍니다.

처음에 바로 main.js 파일을 수정하는 것보다 옵시디언에서 먼저 정리를 한 다음에 그것을 참고하여 작성하면 더욱 편리합니다.  
코드의 작성 순서대로 프론트매터에 적용이 되기 때문에 위에서부터 차근차근 입력해줍니다.

![책 정보 수집 플러그인](https://booktracing.com/wp-content/uploads/2024/02/02-10-2024-15.38.03.webp)

책 정보 수집 플러그인

`콜론(:)` 을 기준으로 좌측은 마음대로 수정이 가능하지만 우측은 주의하여 수정해야만 코드가 정상적으로 작동하게 됩니다.

공백으로 남기고 싶은 경우에는 백틱 `` ` `` 2개를 입력해주고, 체크박스를 만들려면 `false` 를 입력해줘야 합니다.  
그리고 property 사이에는 `,`를 사용하여 구분시켜 줍니다.

## 4 korean book info 플러그인 설명 영상

![](https://www.youtube.com/watch?v=r-DL7-egGgo)

## 5 main.js 파일 공유

영상에서 소개해드리는 파일을 다운 받아서 적용한 후에 수정을 하시는 것을 추천드립니다.  
특히 Yes24에서 책 정보를 불러오는 부분에서 author를 리스트 형식으로 불러올 수 있도록 코드를 적용했습니다.

main.js 파일을 다운 받으신 다음에 위에서 말씀드린 것 처럼,

`.obsidian → plugins → kr-book-info-plugin` 폴더에 붙여넣기 하신 다음에 대치 또는 덮어쓰기로 파일을 변경해줍니다.

그리고 코드를 수정하신 다음에는 반드시 옵시디언을 종료했다가 다시 시작하셔야 정상 작동을 하게 됩니다.

## 6 main.js 파일 다운로드

파일은 소스 공유를 쉽게할 수 있는 깃허브를 통해서 공유하고 있습니다.

[main.js 파일 다운로드](https://github.com/BookTracing/kr-book-info/blob/master/main.js)

위의 링크를 눌러 이동을 하신 다음에 아래 그림에서 설명드리는 것처럼 다운로드 아이콘(Download raw file)을 누르면 다운이 완료됩니다.

![깃허브 파일 공유](https://booktracing.com/wp-content/uploads/2024/02/02-10-2024-15.48.50.webp)

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%af%b8%eb%8b%88%eb%a9%80-%ed%85%8c%eb%a7%88-%ec%b9%b4%eb%93%9c%eb%b7%b0-%ea%b0%a4%eb%9f%ac%eb%a6%ac%eb%b7%b0/)

### [옵시디언 미니멀 테마 추천, 카드뷰, 갤러리뷰](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%af%b8%eb%8b%88%eb%a9%80-%ed%85%8c%eb%a7%88-%ec%b9%b4%eb%93%9c%eb%b7%b0-%ea%b0%a4%eb%9f%ac%eb%a6%ac%eb%b7%b0/)

옵시디언 대시보드, MOC 만들기

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8c%80%ec%8b%9c%eb%b3%b4%eb%93%9c-moc-%ec%9d%b8%eb%8d%b1%ec%8a%a4-%eb%85%b8%ed%8a%b8/)

Next Post

### 옵시디언 대시보드, MOC 만들기

[![옵시디언 콜아웃 멀티 칼럼](https://booktracing.com/wp-content/uploads/2024/02/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%BD%9C%EC%95%84%EC%9B%83-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

### 옵시디언 콜아웃 사용법 멀티 칼럼 모듈러 CSS 적용

[![옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/wp-content/uploads/2024/03/tasks-%EC%BA%98%EB%A6%B0%EB%8D%94-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/)

### 옵시디언 할 일 관리를 캘린더 tasks 플러그인

[![옵시디언 지도 위치 표시](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%A7%80%EB%8F%84-%EC%9C%84%EC%B9%98-%ED%91%9C%EC%8B%9C-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/)

### 옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

[![옵시디언 파일 복구 스냅샷](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%ED%8C%8C%EC%9D%BC-%EB%B3%B5%EA%B5%AC-%EC%8A%A4%EB%83%85%EC%83%B7-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

### 옵시디언 파일 복구하기 스냅샷 기능

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result