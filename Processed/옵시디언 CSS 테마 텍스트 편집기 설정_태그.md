---
title: "옵시디언 CSS 테마 텍스트 편집기 설정"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/"
author:
  - "[[북트레싱]]"
published: 2024-06-16
created: 2025-07-01
description: "옵시디언 CSS 스니펫을 사용해 편집기를 더욱 업그레이드 시켜줄 수 있는 소스 코드를 모았습니다"
tags:
  - "clippings"
---
[![옵시디언 CSS 테마](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-CSS-%ED%85%8C%EB%A7%88.webp)](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-CSS-%ED%85%8C%EB%A7%88.webp)

옵시디언에서 불편함이나 부족함을 느낄만 한 내용을 모았습니다.

옵시디언 CSS 스니펫 기능을 활용해서 적용이 가능하며 자세한 내용은 영상에 담았습니다.

obsidian\_style.css 파일은 [링크](https://vo.la/gwDpk) 또는 하단의 버튼을 통해 다운로드 받으실 수 있습니다.

## 유튜브 참고 영상

아래의 내용 외에도 많은 내용들이 포함되어 있습니다.

![](https://www.youtube.com/watch?v=-jHkfKzbqHw)

## 헤딩 (제목) 스타일 변경하기

![옵시디언 CSS 테마 텍스트 편집기 설정](https://booktracing.com/wp-content/uploads/2024/06/%EC%A0%9C%EB%AA%A9-%ED%97%A4%EB%94%A9-%EC%8A%A4%ED%83%80%EC%9D%BC-1024x729.webp)

옵시디언 CSS 테마 텍스트 편집기 설정

Style setting를 통해서 제목의 크기나 색상 등의 변경이 가능하지만 CSS를 통해서도 가능합니다. 하지만 테마가 적용되는 경우에 우선 순위에서 밀려 CSS가 순간적으로 늦게 적용되는 현상이 발생하게 됩니다.

그렇기 때문에 테마에서 적용가능한 것은 style settings 플러그인을 통해서 변경을 하고, 그 외의 것들에 대해서만 CSS 스니펫을 사용하는 것을 추천드립니다.

아래는 Heading1 ~ 6 까지의 코드를 담았으며, 필요에 따라 추가, 수정해서 사용하시면 되겠습니다.

`.cm-s-obsidian span.cm-header-1`: 편집 모드 (라이브 미리보기)

`.markdown-preview-view h1`: 읽기 모드

그리고 아래의 코드에는 제목과 본문의 텍스트와의 간격을 조절할 수 있도록 margin 값을 수정할 수 있습니다.

편집 모드와 읽기 모드에서 간격의 차이가 발생하기 때문에 CSS를 통해 어느 정도 줄여줄 수도 있습니다.

```js
/* Heading 1 */

.cm-s-obsidian span.cm-header-1 { /* 편집 모드에서 적용 */
  margin-top: 15px !important;
  margin-bottom: 15px !important;
  display: inline-block;
  }
.markdown-preview-view h1 {  /* 읽기 모드에서 적용 */
    margin-bottom: -10px !important;
  }

/* Heading 2 */
.cm-s-obsidian span.cm-header-2 {
  margin-top: 10px !important;
  margin-bottom: 10px !important;
  display: inline-block !important;
}
.markdown-preview-view h2 {
  color: darkorange !important;
  font-size: 28px !important;
  margin-bottom: -5px !important;
}

/* Heading 3 */
.cm-s-obsidian span.cm-header-3 {
  margin-top: 8px !important;
  margin-bottom: 8px !important;
  display: inline-block;
}
.markdown-preview-view h3 {
  margin-bottom: -5px !important;
}

/* Heading 4 */
.cm-s-obsidian span.cm-header-4 {
  margin-top: 6px !important;
  margin-bottom: 6px !important;
  display: inline-block;
}
.markdown-preview-view h4 {
  margin-bottom: -10px !important;
}

/* Heading 5 */
.cm-s-obsidian span.cm-header-5 {
  margin-top: 0px !important;
  margin-bottom: 0px !important;
  display: inline-block;
}
.markdown-preview-view h5 {

  margin-bottom: -20px !important;
}

/* Heading 6 */
.cm-s-obsidian span.cm-header-6 {
  margin-top: 0px !important;
  margin-bottom: 0px !important;
  display: inline-block;
}
.markdown-preview-view h6 {

  margin-bottom: -20px !important;
```

## 텍스트 강조 스타일 변경

![옵시디언 CSS 테마 텍스트 편집기 설정](https://booktracing.com/wp-content/uploads/2024/06/%EB%A7%88%ED%81%AC%EB%8B%A4%EC%9A%B4-%ED%85%8D%EC%8A%A4%ED%8A%B8-%EA%B0%95%EC%A1%B0-%EC%98%88%EC%8B%9C.webp)

옵시디언 CSS 테마 텍스트 편집기 설정

아래 제공해드리는 소스 코드는 읽기 모드와 편집 모드 (라이브 미리보기)에 같은 스타일로 적용이 되도록 제작했습니다.  
만약 따로 사용하실 분들은 코드를 나눠서 작성하시면 되겠습니다.

예)

- `.markdown-source-view.mod-cm6 .cm-strong { } `
- `.markdown-preview-view strong { }`

### 볼드체 (두꺼운 글씨)

텍스트의 색상, 사이즈, 글꼴을 변경했고, 글꼴에 따라서 높이가 달라 보기 불편한 경우가 있기 때문에 위치를 조절할 수 있도록 작성했습니다.

```js
/* 텍스트 볼드 (굵은 글씨) */
.markdown-source-view.mod-cm6 .cm-strong, 
.markdown-preview-view strong {
    color: #dd8d31 !important;
  font-family: 'Courier New', Courier, monospace;
  vertical-align: bottom;
  position: relative;
  top: 2px;
    }
```

### 이탤릭 (기울임)

기본적으로 색상을 변경해서 사용하시면 되고, 마진은 우측에 3px을 두어 텍스트가 기울여질 때 다른 텍스트의 간섭을 최소화 시켰습니다.

글꼴에 따라서 변경해서 사용하시면 되겠습니다.

```js
/* 텍스트 이탤릭 */
.markdown-preview-view em,
.markdown-source-view.mod-cm6 .cm-em {
  color: #4BACC6 !important;
  margin-right: 3px;
}
```

### 두껍고 기울임 (볼드 + 이텔릭)

`***두껍고 기울임***` 으로 사용이 가능하며, 단축키로는 `Cmd + B` 를 누르시고 `Cmd + i` 를 한 번 더 눌러서 적용이 가능합니다.

볼드, 이탤릭과는 또 다른 강조할 수 있는 수단으로 HTML 사용을 최소화 시키면서 여러가지 방법으로 옵시디언에서 강조를 할 수 있도록 도와줍니다.

색상, 사이즈, 글꼴, 마진을 적용했습니다.

```js
/* 텍스트 볼드 & 이탤릭 (굵고 기울인 글씨) */
.markdown-source-view.mod-cm6 .cm-strong.cm-em, 
.markdown-preview-view strong em {
color: #7ce13d !important;
font-family: 'Courier New', Courier, monospace !important;
margin-right: 3px;
}
```

### 하이라이트

마크다운 적용이 가능하며 `==하이라이트==` 로 입력이 가능합니다. 단축키를 따로 지정하여 사용하면 손쉽게 텍스트를 강조할 수 있습니다.

현재 패딩이 상하좌우로 2px 들어가 있고, 텍스트의 글꼴에 따라서 조절해서 사용할 수 있습니다.

그리고 배경색과 텍스트 컬러도 변경해서 사용 가능합니다.

```js
/* 텍스트 하이라이트 */
.markdown-preview-view mark,
.markdown-source-view.mod-cm6 .cm-highlight {
background-color: #b35e09 !important;
color: #dddddd !important;
padding: 2px 2px !important; /* 상하, 좌우 너비 */
}
```

### 밑줄

기본적으로 밑줄은 마크다운에는 없지만 html을 이용해서 사용이 가능합니다. 옵시디언에서 **editing boolbar** 플러그인을 설치하면 더욱 손쉽게 사용이 가능합니다.

추가로 플러그인을 설치하고, 밑줄을 단축키로 지정하면 좋습니다.

코드는 색상과 밑줄 위치를 조절할 수 있는데, 현재 값은 4px로 입력이 되어있지만 사용하시는 텍스트에 따라 간섭이 생기는 경우에 조절하시면 됩니다.

```js
/* 밑줄 */
u {
  text-underline-offset: 4px; /* 밑줄의 위치 조정 */
  color: #dd578c
  }
```

## 노트 임베딩 타이틀

`![[노트제목]]` 형식으로 옵시디언의 노트에 임베딩된 노트의 타이틀의 스타일을 변경할 수 있습니다.

![옵시디언 CSS 테마 텍스트 편집기 설정](https://booktracing.com/wp-content/uploads/2024/06/%EC%9E%84%EB%B2%A0%EB%94%A9-%EB%85%B8%ED%8A%B8-%EC%A0%9C%EB%AA%A9-%EC%8A%A4%ED%83%80%EC%9D%BC.webp)

옵시디언 CSS 테마 텍스트 편집기 설정

```js
/* 노트 임베딩 타이틀 */
.markdown-embed-title {
    font-size: 1.2em;
    color: #2eded6; /* 폰트 색상 */

}
```

## 이미지 테두리 여백 넣기

화면과 이미지의 색상이 비슷하거나 같을 때 구분을 시켜주는데 도움이 됩니다. 현재는 화이트 색상의 테두리이기 때문에 밝은 배경화면을 사용하시는 분들은 색상을 변경하고 사용하시면 되겠습니다.

추가로 이미지의 상,하단에 여백을 추가하여 텍스트와 분리되어 보일 수 있도록 했습니다.

![옵시디언 CSS 테마 텍스트 편집기 설정](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%9D%B4%EB%AF%B8%EC%A7%80-%ED%85%8C%EB%91%90%EB%A6%AC-1024x456.webp)

옵시디언 CSS 테마 텍스트 편집기 설정

```js
/* 이미지 테두리 및 여백 */
img {
  border: 1px solid #eeeeee;
  margin-top: 15px; /* 이미지 위에 여백 추가 */
margin-bottom: 15px; /* 이미지 아래에 여백 추가 */
  }
```

## 태그 색상 변경

영상에서 불필요한 부분은 제거하였습니다.

`#데이터뷰`, `#일기`, `#플러그인` 세 가지 태그를 예시로 만들었습니다. 필요한 태그를 넣어주시고, 배경 색상과 텍스트 색상을 변경하여 사용할 수 있습니다.

![옵시디언 CSS 테마 텍스트 편집기 설정](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%ED%83%9C%EA%B7%B8-%EC%83%89%EC%83%81-%EB%B3%80%EA%B2%BD.webp)

옵시디언 CSS 테마 텍스트 편집기 설정

```js
/* 예: #데이터뷰 태그 */
.tag[href="#데이터뷰"] {
    color: #eeeeee;
    background-color: #0e74b9;
}

/* 예: #일기 태그 */
.tag[href="#일기"] {
    color: red;
    background-color: transparent;
}
/* 예: #플러그인 태그 */
.tag[href="#플러그인"] {
    color: #eeeeee;
    background-color: #21a058;

}
```

## 구분선

구분선의 스타일을 변경 가능합니다. 아래의 예시는 너비는 50%, 중앙 정렬과 마진 그리고 두께를 조절하였습니다.

```js
/* 구분선 스타일 */
.markdown-preview-view hr,
.markdown-source-view.mod-cm6 .cm-line hr {
  width: 50%;
  margin: 50px auto;
  border: none; 
  border-top: 2px solid #a5da49;
```

## 깃허브 다운로드

[**obsidian\_style.css 파일 다운로드**](https://vo.la/gwDpk)

Next Post

[![메타데이터 메뉴 플러그인](https://booktracing.com/wp-content/uploads/2024/07/%EB%A9%94%ED%83%80%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%A9%94%EB%89%B4-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/)

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png)