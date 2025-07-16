---
title: "메타데이터 메뉴 (metadata menu) 플러그인, (데이터뷰 테이블)"
source: "https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/"
author:
  - "[[북트레싱]]"
published: 2024-07-16
created: 2025-07-01
description: "메타데이터 메뉴 플러그인을 이용해 프론트매터를 관리할 수 있고, 데이터뷰과 연동해서 더욱 강력한 테이블을 만들 수 있습니다."
tags:
  - "clippings"
---
![북트레싱](https://secure.gravatar.com/avatar/11941127f7b84c939019207d4f24b5d316232341844f140465343801c8cbf3cc?s=80&d=mm&r=g) by

[7월 16, 2024](https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/), [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/#comments)

[![메타데이터 메뉴 플러그인](https://booktracing.com/wp-content/uploads/2024/07/%EB%A9%94%ED%83%80%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%A9%94%EB%89%B4-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8.webp)](https://booktracing.com/wp-content/uploads/2024/07/%EB%A9%94%ED%83%80%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%A9%94%EB%89%B4-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8.webp)

## 1 메타데이터 메뉴 플러그인

메타데이터 메뉴에 대한 기본적인 사용법에 대해 다뤘습니다.

이 플러그인은 여러 방법으로 활용이 가능하지만 다른 플러그인에 비해서 사용법이 조금 복잡한 편입니다.

아래 임베딩된 영상에서 메타데이터 메뉴 플러그인의 사용에 도움이 될만한 기본적인 개념과 사용 방법에 대해서 자세히 다뤘으니 시청부탁드립니다.

그리고 영상에서 사용된 소스 코드는 아래에 첨부하고 자세한 설명을 추가해뒀습니다.

## 2 Metadata Menu 플러그인 설명 영상

![](https://www.youtube.com/watch?v=rcgXLPgm4xk)

## 3 노트에 테이블 삽입

metadata menu 플러그인을 사용해 만든 field를 적용한 테이블을 기존의 노트에 테이블을 삽입하실 수 있습니다.

테이블을 노트에 추가하는 방법은 기본적으로 두 가지가 있습니다.

하나는 metadata menu 플러그인에서 제공하는 방법이고, 두 번째는 우리가 기존에 사용해왔던 dataview 플러그인을 통해 만든 테이블에서 metadata menu 플러그인의 기능을 사용할 수 있도록 만들어 주는 방법입니다.

### mdm 테이블

```js
\`\`\`mdm
fileClass: bookclass
view: default
files per page: 30
showAddField: true
\`\`\`
```

1\. 기본적으로 백틱 (\`) 3개를 입력한 후에 metadata menu의 약자인 **mdm** 을 입력해줍니다.

2\. `fileClass: bookclass` – 여기서 앞의 fileClass는 고정값이며, `:`을 추가한 후에 반드시 **한 칸의 띄워주신 다음** 에 클래스의 이름을 적으시면 됩니다. 여기서 **bookclass** 는 사용자가 설정한 클래스의 이름입니다. (fileClass는 필수로 입력해야 하며, 아래의 옵션들은 입력하지 않아도 테이블은 동작합니다.)

3\. `view: default` – 테이블의 필터를 적용한 후 저장한 이름이며, fileClass view에서 지정한 이름을 콜론(`:`)뒤에 한 칸을 띄워주시고 입력하시면 됩니다.

4\. `files per page: 30` – 한 페이지에 얼마나 많은 개수의 노트를 적을지를 입력하시면 됩니다.

5\. `showAddField: true` – 대소문자 구분을 해주시고, true를 입력하시면 노트에 property가 입력되지 않은 경우에 추가할 수 있도록 테이블에 버튼을 생성시켜줍니다.

### dataview 테이블

기본적으로 [데이터뷰](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/) 테이블에서는 체크박스에 체크를 하거나 프론트매터에 입력된 내용을 테이블에서 수정한 기능을 지원하지 않습니다. 하지만 metadata menu 플러그인과 연동하여 이러한 기능을 사용할 수 있게 됩니다.

코드는 기본적으로 **==dataviewjs==** 가 사용되기 때문에 작성 방법이 조금 복잡합니다. 모든 내용을 자세히 설명드릴 수는 없지만 변경하여 활용하실 수 있도록 설명드리겠습니다.

```js
\`\`\`dataviewjs
const {fieldModifier: f} = MetadataMenu.api

dv.table(["표지", "책 이름", "등록일", "읽기 시작 날짜", "독서 여부", "평점"],
    dv.pages('"50. Book/51. 도서 목록"')
        .map(p => [
            "![|90](" + p.cover_url + ")",  // 이미지 URL을 사용해 표지 이미지를 추가
            p.file.link,
            f(dv, p, "registered_date"),
            f(dv, p, "start_date", {options: {alwaysOn: true}}),
            f(dv, p, "reading"),
            f(dv, p, "score", {options: {showAddField: true}}),
        ])
);
\`\`\`
```

1\. `const {fieldModifier: f} = MetadataMenu.api` – 이 부분은 데이터뷰에서 메타데이터 메뉴 플러그인의 api를 가져오는 부분입니다.

2\. `dv.table(["표지", "책 이름","저자", "등록일", "읽기 시작 날짜", "독서 여부", "평점"],`

이 부분에 테이블 헤더의 이름을 나열해주시면 됩니다. 아래에 들어갈 `.map` 이하에 입력하는 항목의 개수와 반드시 일치해야 합니다.

쌍따옴표 안에 각 헤더를 적어주시고, 입력한 순서대로 테이블에 좌측부터 나타나게 됩니다. 각 항목 간에는 `,`를 이용하여 구분지어 줍니다.

3\. `   dv.pages('"50. book/051. 도서 목록"')` – 쌍따옴표 `"` 사이에 폴더를 입력해줍니다. 폴더의 경로의 이름을 정확히 작성해주셔야 하고, 특히 띄어쓰기 구분에 신경써서 작성을 해주셔야 오류가 발생하지 않습니다.

4\. `.map(p => [` – 이 부분 아래에 테이블 헤더를 작성한 순서에 따라서 불러올 값을 정확히 입력해주셔야 합니다. 각 항목의 사이에는 `,`로 구분을 해주셔야 하고 위에 작성한 `dv.table` 의 개수와 정확히 일치해야 합니다. 현재 예시에서는 7개의 항목이 작성되었습니다.

5\. `  "![|90](" + p.cover_url + ")",` – 이 부분은 url의 이미지를 미리보기 할 수 있는 부분입니다. `cover_url` 이라고 작성된 부분을 현재 사용하고 계시는 property의 key로 수정하여 사용하실 수 있습니다. 그리고 `[|90]` 은 미리보기 되는 이미지의 크기를 조절할 수 있습니다.

6\. `p.file.link,`– 이 부분은 파일의 링크를 추가하는 부분이며, 자동으로 파일의 이름에 링크가 생성됩니다. `file.`뒤에 link 뿐만 아니라, path, name, size, cday, mday, ctime, mtime 등을 사용하실 수 있습니다.

참고로 day와 타임 앞에 붙은 c,m 은 c는 creation(생성), m은 modification(수정)을 의미합니다.

7\. `f(dv, p, "start_date", {options: {alwaysOn: true}}),`

기본적으로 `"` 사이에는 프로퍼티의 key값을 입력하는 부분입니다.

그리고 뒤에 \` `{options: {alwaysOn: true}}` 이 부분은 이미 노트의 프론프매터에 해당하는 field가 있는 경우에 마우스를 올리면 버튼이 생기게 되지만, 이 옵션을 사용하면 마우스를 올리지 않아도 항상 버튼을 볼 수 있도록 설정해줍니다.

8\. `f(dv, p, "score", {options: {showAddField: true}}),`

여기서 score 부분을 변경해서 사용할 수 있고, `{showAddField: true}` 부분은 현재 노트의 프론트매터에 class field로 지정한 프로퍼티가 존재하지 않은 경우에, 테이블에서 바로 생성을 할 수 있도록 버튼을 만들어 주는 부분입니다.

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

### [옵시디언 CSS 테마 텍스트 편집기 설정](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result