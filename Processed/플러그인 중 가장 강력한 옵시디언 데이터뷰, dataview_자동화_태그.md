---
title: "플러그인 중 가장 강력한 옵시디언 데이터뷰, dataview"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/"
author:
  - "[[북트레싱]]"
published: 2024-01-10
created: 2025-07-01
description: "옵시디언 데이터뷰 플러그인은 옵시디언에 저장된 데이터를 효과적으로 관리하는 데 많은 도움이 됩니다.이 플러그인으로 데이터베이스 내의 정보를 정돈하고 필요한 데이터를 필터링하여 테이블, 리스트, 캘린더 등으로 시각적으로 표현할 수 있습니다."
tags:
  - "clippings"
---
by

[1월 10, 2024](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/)

in [세컨드 브레인](https://booktracing.com/second-brain/), [옵시디언](https://booktracing.com/second-brain/obsidian/)

A A

[0](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/#comments)

[![옵시디언 데이터뷰 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B7%B0-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-750x750.webp)](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B7%B0-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8.webp)

이번은 ‘옵시디언의 꽃’ 이라 불릴만 한 Dataview 플러그인에 대한 기본적인 사용법과 활용 방법에 대해서 간단히 살펴보려고 하는데요.

옵시디언 데이터뷰 플러그인은 옵시디언에 저장된 데이터를 효과적으로 관리하는 데 많은 도움이 됩니다.,  
이 플러그인으로 데이터베이스 내의 정보를 정돈하고 필요한 데이터를 필터링하여 테이블, 리스트, 캘린더 등으로 시각적으로 표현할 수 있습니다.

지난 영상에서 우리가 제작했던 데일리 노트를 DB로 활용하여 위클리, 먼슬리, 이얼리 노트에 데이터를 모아서 볼 수 있도록 만들 수 있고  
또 동적으로 작동하기 때문에, 사용자가 입력한 데이터에 따라 바로바로 정보가 업데이트되어 작성한 노트들의 정보를 실시간으로 볼 수 있는 장점도 가지고 있습니다.

옵시디언을 사용하면서 가장 중요한 플러그인 중 하나인 데이터뷰에 대해 알아보겠습니다.

![](https://www.youtube.com/watch?v=Iv7wCJArqPI)

## 1 Dataview 플러그인 언어

플러그인을 사용하는 언어는 두 가지가 있는데 일반적으로 DQL을 사용합니다.  
Dataview Query Language의 약자로, SQL 언어와 유사한 하지만 Dataview를 위한 언어라고 보시면 되겠습니다.  
그리고 dataviewjs는 자바스크립트를 이용하여 쿼리를 만들 수 있는데, 이 내용은 너무 복잡하고 어렵기 때문에 옵시디언을 라이트하게 쓰시는 분들은 DQL block 만 사용하셔도 충분히 사용이 가능합니다.  
dataview 플러그인에서 자바스크립트로 블록을 만들어 사용이 가능하다는 사실만 확인하고 넘어가시면 되겠습니다.

[데이터뷰 깃허브](https://blacksmithgu.github.io/obsidian-dataview/) 에서 자세한 내용을 참조하세요

## 2 옵시디언 데이터뷰 쿼리 구조

데이터뷰 쿼리 작성을 하기 전에 데이터뷰에 어떤 식으로 명령을 내려야 하는지 전반적으로 살펴본 다음에 세부 내용을 하나씩 보도록 하겠습니다.

데이터뷰 플러그인의 쿼리 작성에 대한 설명을 드릴 텐데요. 우선 그 쿼리의 구조에 대해 알아보겠습니다.  
쿼리의 구조를 보게 되면, 먼저 어떤 형태로 데이터를 볼 것인지 결정을 할 수 있고,  
구성 요소를 추가하여 세부적인 설정을 할 수 있습니다.

### 형식

형식은 총 네 가지로 작성을 할 수 있는데 TABLE, LIST, TASK, CALENDAR가 있습니다.

### 키워드

그리고 키워드를 사용하여 데이터링 필터링 하거나 정렬을 할 수 있습니다.  
여기 사용 가능한 키워드를 보면  
그리고 그 구문에 세부 정보를 넣어서 쿼리를 완성합니다. 세부 정보를 작성하는 방식은 여러 가지가 있습니다.

먼저 키워드로 들어갈 수 있는 옵션을 보면 FROM, WHERE, SORT, GROUP BY, LIMIT, FLATTEN 등이 있습니다.  
이 6가지

1. **FROM**: 특정 태그, 폴더, 또는 링크와 같은 소스에서 페이지를 선택합니다.
2. **WHERE**: 노트 내부의 정보나 메타데이터 필드를 기반으로 노트를 필터링합니다.
3. **SORT**: 결과를 특정 필드 및 방향에 따라 정렬합니다.
4. **LIMIT**: 쿼리 결과의 수를 지정된 숫자로 제한합니다.
5. **GROUP BY**: 여러 결과를 하나의 결과 행당 한 그룹으로 묶습니다.
6. **FLATTEN**: 하나의 결과를 특정 필드나 계산에 따라 여러 결과로 분할합니다.

---

예를 들어, `TABLE date, task FROM "Daily Notes"` 쿼리를 사용하면 “Daily Notes” 폴더에 있는 노트들에서 날짜와 할 일 목록을 테이블 형태로 보여줄 수 있습니다. 또한, `WHERE` 구문을 추가하여 특정 조건을 만족하는 데이터만을 선택할 수 있으며, `SORT` 를 통해 원하는 기준으로 데이터를 정렬할 수 있습니다.

이 외에도 Dataview 플러그인은 노트의 메타데이터를 활용하여 더 복잡한 데이터 구조를 만들 수 있게 해줍니다. 예를 들어, 태그, 카테고리, 작성자 등의 메타데이터를 기반으로 노트들을 그룹화하고 분석할 수 있습니다.

#### FROM (파일 선택)

어떤 파일로 부터 가져올지를 작성하는 곳입니다.

1. 첫 번째로 어떤 태그가 있는 노트를 가져올 것인지, 어떤 폴더에 있는 노트들에서 가져올 것인지, 혹은 특정한 파일로부터 가져올 것인지
2. 특정한 노트를 기준으로 나가거나, 들어오는 노트들을 가져올 것인지 마지막으로 위의 것들을 조합해서 가져오는 방법도 있습니다.

#### #태그

#### 폴더

FROM “폴더A/폴더AA”

#### 특정 파일

FROM “폴더A/파일A.md”

#### 링크

- `[[note]]` 로 연결되는 모든 링크
- outgoing `[[note]]`

#### 모두를 조합

`and` 또는 `or` 을 사용해서 복잡한 연산자를  
예를 들어보면 폴더A와 폴더B에 있는 것들 중에서 태그가 #태그 인 것만  
#태그 and (“폴더A” or “폴더B”)

#### WHERE

1. **조건 지정**:
- 특정 필드나 값에 대한 조건을 지정합니다. 예를 들어, 특정 태그가 있는 노트를 찾거나, 특정 날짜 범위에 작성된 노트를 필터링할 수 있습니다.
1. **비교 연산자 사용**:
```js
\`=\`, \`!=\`, \`>\`, \`<\`, \`>=\`, \`<=\`
```
1. **논리 연산자 사용**:
```js
- \`AND\`, \`OR\`, \`NOT\`
```

**예시**

```js
TABLE
WHERE contains(file.tags, "#습관")
```
```js
TABLE
WHERE contains(file.path, "templater")
```
```js
TABLE
WHERE contains(author, "전중환")
```
```js
TABLE
WHERE book_page >100
LIMIT 3
```
```js
TABLE
WHERE contains(file.folder, "000. Inbox")
LIMIT 3
```

**날짜와 시간 기반 필터링**:

- **특정 날짜 이후**: `WHERE date > "2022-01-01"`
- **날짜 범위**: `WHERE date >= "2022-01-01" AND date <= "2022-12-31"`
- **오늘 날짜 기준**: `WHERE date = today`

#### 논리적 조건

- **AND 연산자**: `WHERE 조건1 AND 조건2`
- **OR 연산자**: `WHERE 조건1 OR 조건2`
- **NOT 연산자**: `WHERE NOT 조건`

#### 복합 조건:

- **복합 조건의 사용**: `WHERE (조건1 OR 조건2) AND 조건3`

#### 숫자 및 범위 기반 필터링:

- **숫자 비교**: `WHERE 숫자필드 > 10`
- **범위 지정**: `WHERE 숫자필드 BETWEEN 10 AND 20`

Obsidian의 Dataview 플러그인은 노트의 메타데이터와 내용을 다양한 방식으로 필터링하고 조회할 수 있도록 해줍니다. 하지만 정확한 사용법과 가능성은 Dataview의 버전과 Obsidian의 데이터 구조에 따라 다를 수 있으므로, 구체적인 사용을 위해서는 해당 플러그인의 문서를 참고하는 것이 좋습니다.

### SORT

SORT 다음은 위의 TABLE 다음에 작성한 방식과 같습니다.  
SORT 뒤에 어떤 기준으로 정렬을 할지 하나 골라서 입력하고, 그 뒤에 오름차순은 asc, 또는 내림차순 desc를 입력해주면 되고, 어떤 방식으로 정렬할지 정하지 않는다면 자동으로 오름차순이 적용됩니다.

```js
TABLE
    file.ctime
SORT file.ctime DESC
LIMIT 3
```

### 사용 가능한 키워드

프론트매터 내의 Key값, `file.link`, `file.cday`, `file.mday`, `file.name` 등

## 3 데이터뷰 테이블 예시

![플러그인 중 가장 강력한 옵시디언 데이터뷰, dataview](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B7%B0-%ED%85%8C%EC%9D%B4%EB%B8%94.webp)

플러그인 중 가장 강력한 옵시디언 데이터뷰, dataview

### dataview 소스 코드

```js
\`\`\`dataview
TABLE without id
    ("![|100](" + cover_url + ")") as "책 표지",
    file.link as "책 제목",
    author[0] as "저자",
    tags[1] as "태그",
    total_page as "페이지",
    finish_read_date as "읽은 날짜",
    book_note as "독서 노트"

FROM "50. Book/51. 도서 목록" OR "리뷰"

SORT author[0], finish_read_date

\`\`\`
```

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/)

### [옵시디언 데일리 노트를 만들어 2024년, 새롭게 시작해보자](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/)

옵시디언 주간 계획을 자동화해서 더욱 강력한 생산성 향상

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a3%bc%ea%b0%84-%ea%b3%84%ed%9a%8d-%ec%9c%84%ed%81%b4%eb%a6%ac-%eb%85%b8%ed%8a%b8/)

Next Post

[![옵시디언 주간 계획 위클리 노트](https://booktracing.com/wp-content/uploads/2024/01/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-4-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a3%bc%ea%b0%84-%ea%b3%84%ed%9a%8d-%ec%9c%84%ed%81%b4%eb%a6%ac-%eb%85%b8%ed%8a%b8/)

### 옵시디언 주간 계획을 자동화해서 더욱 강력한 생산성 향상

[![옵시디언 Tracker 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-Tracker-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-tracker-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%8a%b5%ea%b4%80/)

### 월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인

[![옵시디언-todoist-투두이스트](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-todoist-%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-todoist-%ed%88%ac%eb%91%90%ec%9d%b4%ec%8a%a4%ed%8a%b8-%ec%97%b0%eb%8f%99/)

### 옵시디언 Todoist 연동하기, 투두이스트 할 일 어플

[![옵시디언 미니멀 테마](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%AF%B8%EB%8B%88%EB%A9%80-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%af%b8%eb%8b%88%eb%a9%80-%ed%85%8c%eb%a7%88-%ec%b9%b4%eb%93%9c%eb%b7%b0-%ea%b0%a4%eb%9f%ac%eb%a6%ac%eb%b7%b0/)

### 옵시디언 미니멀 테마 추천, 카드뷰, 갤러리뷰

[![책 정보 수집 플러그인](https://booktracing.com/wp-content/uploads/2024/02/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-8-75x75.webp)](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/)

### 옵시디언 책 정보 수집 플러그인, korean book info 커스텀

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result