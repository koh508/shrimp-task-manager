---
title: "월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-tracker-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%8a%b5%ea%b4%80/"
author:
  - "[[북트레싱]]"
published: 2024-01-13
created: 2025-07-01
description: "옵시디언의 먼슬리 노트에 Tracker 플러그인을 이용해서 습관을 유지하는데 도움이 되는 방법에 대해 알아보세요"
tags:
  - "clippings"
---
[![옵시디언 Tracker 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-Tracker-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8.webp)](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-Tracker-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8.webp)

일간, [주간 노트](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a3%bc%ea%b0%84-%ea%b3%84%ed%9a%8d-%ec%9c%84%ed%81%b4%eb%a6%ac-%eb%85%b8%ed%8a%b8/) 에 이은 월간, 연간 노트에 관한 내용입니다.

대부분 디지털 노트를 작성하는데 하루하루 [데일리 노트](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/) 에만 기록을 남기곤 합니다. 하지만 삶이라는 전체적인 관점에서 하루하루를 연결시키는 부분이 정말 중요합니다.

## 습관 기르기

이번 먼슬리 노트에는 ‘습관’ 이라는 키워드를 넣어봤습니다. 습관을 만들고 싶을 때 막연한 생각만 하고 노력하는 것보다는 시각적으로 직접 진행 상황을 보면서 하게 되면, 성취감을 느낄 수도 있고 연속되는 기록을 깨트리고 싶지 않아서 도전 정신도 생기게 됩니다.

옵시디언의 [Tracker 플러그인](https://github.com/pyrochlore/obsidian-tracker/blob/master/docs/Examples.md) 은 캘린더, 그래프 등의 형식으로 습관의 진행 상황을 직관적으로 볼 수 있게 만들어주는 도구입니다.

## Tracker 플러그인

![월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인](https://booktracing.com/wp-content/uploads/2024/01/Tracker-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-%EC%8A%B5%EA%B4%80.webp)

월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인

옵시디언 Tracker 플러그인은 개인적인 습관과 목표를 추적하고 관리할 수 있도록 도와주는 도구입니다. 이 플러그인은 특히 습관 형성과 유지에 유용하고, 일상적인 활동이나 공부, 운동 등과 같은 다양한 개인 목표에 대한 진행 상황을 기록하고 추적할 수 있게 해줍니다. 사용자는 특정 습관이나 목표에 대한 진행 상태를 시각적으로 볼 수 있으며, 이를 통해 동기부여를 받고 자신의 진행 상황을 정확하게 파악할 수 있습니다.

트래커 플러그인은 옵시디언의 유연한 노트 작성 환경과 잘 통합되어, 사용자가 자신만의 맞춤형 트래킹 시스템을 구축할 수 있도록 지원합니다. 예를 들어, 하루에 물을 충분히 마시거나, 정기적인 운동을 하는 것과 같은 습관을 기록하고, 이를 통해 장기적인 건강 목표를 달성할 수 있도록 돕습니다. 또한, 이 플러그인은 습관 형성 과정에서 발생할 수 있는 장애물을 극복하고, 일관성을 유지할 수 있도록 도와줍니다.

## 월간, 연간 노트 템플릿 만들기

![](https://www.youtube.com/watch?v=mcPAaVrA6b0)

## 월간 계획 (Monthly note) 소스 코드

### 운동 습관 기르기

※ 이 코드는 tracker 플러그인의 설치 및 활성화가 필요합니다.

사용과 수정하는 방법은 영상을 시청해주세요

```js
\`\`\`tracker
searchType: frontmatter
searchTarget: exercise
folder: 10. Planner/11. Daily
datasetName: 운동 습관 기르기
month:
    startWeekOn: 'mon'
    headerMonthColor: orange
    initMonth: <% tp.file.title %>
    mode: annotation
    annotation: 💪
\`\`\`
```

### 독서 습관 기르기

※ 이 코드는 tracker 플러그인의 설치 및 활성화가 필요합니다.

사용과 수정하는 방법은 영상을 시청해주세요

```js
\`\`\`tracker
searchType: frontmatter
searchTarget: reading_page
datasetName: 읽은 페이지
folder: 10. Planner/11. Daily

line:
    title: 책 읽는 습관
    xAxisLabel: 날짜
    yAxisLabel: 읽은 페이지
    yAxisUnit: 페이지
    lineColor: red
    pointColor: red
    pointBorderWidth: 2
    pointBorderColor: red
    showLegend: True
\`\`\`
```

#### 요약

```js
\`\`\`tracker
searchType: frontmatter
searchTarget: reading_page
datasetName: 읽은 페이지
folder: 10. Planner/11. Daily
startDate: <%* const title = tp.file.title; const firstDay = moment(title + "-01").format('YYYY-MM-DD(ddd)'); tR += firstDay; %>
endDate: <%* const year = tp.file.title.split("-")[0]; const month = tp.file.title.split("-")[1]; const lastDay = moment(title).endOf('month').format('YYYY-MM-DD(ddd)'); tR += lastDay; %>

summary:
    template: "적게 읽은 날: {{min()::i}}페이지\n많이 읽은 날: {{max()::i}}페이지\n독서한 날: {{numDaysHavingData()::i}}일"

\`\`\`
```

## 연간 계획 (Yearly Note) 소스 코드

### achievement 및 체크박스

```js
\`\`\`dataview
TABLE without id
    file.link as 날짜,
    achievement as 성과
FROM "10. Planner/11. Daily"
WHERE important_date = true AND contains(file.name, "<% tp.file.title %>")
\`\`\`
```

### 읽은 책 리스트

```js
\`\`\`dataview
TABLE without id
    rows.reading_book as "책 제목",
    rows.date_daily as "읽은 날짜"
FROM "10. Planner/11. Daily"
WHERE contains(file.name, "<% tp.file.title %>") AND reading_book != null
FLATTEN reading_book
GROUP BY reading_book
\`\`\`
```

### 월간 리뷰

편안하게 사용하시고, 재배포 시에는 출처를 표기해주세요

```js
|요일| 내용 |
|---|---|
|<% tp.file.title %>-1월|<%* const year01 = tp.file.title; const month01 = "01"; const monthlyNoteTitle01 = \`${year01}-${month01}\`; const reviewSection01 = \`![[${monthlyNoteTitle01}#^review]]\`; tR += reviewSection01; %>|   
|<% tp.file.title %>-2월|<%* const year02 = tp.file.title; const month02 = "02"; const monthlyNoteTitle02 = \`${year02}-${month02}\`; const reviewSection02 = \`![[${monthlyNoteTitle02}#^review]]\`; tR += reviewSection02; %>|
|<% tp.file.title %>-3월|<%* const year03 = tp.file.title; const month03 = "03"; const monthlyNoteTitle03 = \`${year03}-${month03}\`; const reviewSection03 = \`![[${monthlyNoteTitle03}#^review]]\`; tR += reviewSection03; %>|
|<% tp.file.title %>-4월|<%* const year04 = tp.file.title; const month04 = "04"; const monthlyNoteTitle04 = \`${year04}-${month04}\`; const reviewSection04 = \`![[${monthlyNoteTitle04}#^review]]\`; tR += reviewSection04; %>|
|<% tp.file.title %>-5월|<%* const year05 = tp.file.title; const month05 = "05"; const monthlyNoteTitle05 = \`${year05}-${month05}\`; const reviewSection05 = \`![[${monthlyNoteTitle05}#^review]]\`; tR += reviewSection05; %>|
|<% tp.file.title %>-6월|<%* const year06 = tp.file.title; const month06 = "06"; const monthlyNoteTitle06 = \`${year06}-${month06}\`; const reviewSection06 = \`![[${monthlyNoteTitle06}#^review]]\`; tR += reviewSection06; %>|
|<% tp.file.title %>-7월|<%* const year07 = tp.file.title; const month07 = "07"; const monthlyNoteTitle07 = \`${year07}-${month07}\`; const reviewSection07 = \`![[${monthlyNoteTitle07}#^review]]\`; tR += reviewSection07; %>|
|<% tp.file.title %>-8월|<%* const year08 = tp.file.title; const month08 = "08"; const monthlyNoteTitle08 = \`${year08}-${month08}\`; const reviewSection08 = \`![[${monthlyNoteTitle08}#^review]]\`; tR += reviewSection08; %>|
|<% tp.file.title %>-9월|<%* const year09 = tp.file.title; const month09 = "09"; const monthlyNoteTitle09 = \`${year09}-${month09}\`; const reviewSection09 = \`![[${monthlyNoteTitle09}#^review]]\`; tR += reviewSection09; %>|
|<% tp.file.title %>-10월|<%* const year10 = tp.file.title; const month10 = "10"; const monthlyNoteTitle10 = \`${year10}-${month10}\`; const reviewSection10 = \`![[${monthlyNoteTitle10}#^review]]\`; tR += reviewSection10; %>|
|<% tp.file.title %>-11월|<%* const year11 = tp.file.title; const month11 = "11"; const monthlyNoteTitle11 = \`${year11}-${month11}\`; const reviewSection11 = \`![[${monthlyNoteTitle11}#^review]]\`; tR += reviewSection11; %>|
|<% tp.file.title %>-12월|<%* const year12 = tp.file.title; const month12 = "12"; const monthlyNoteTitle12 = \`${year12}-${month12}\`; const reviewSection12 = \`![[${monthlyNoteTitle12}#^review]]\`; tR += reviewSection12; %>|
```

Next Post

[![옵시디언-todoist-투두이스트](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-todoist-%ED%88%AC%EB%91%90%EC%9D%B4%EC%8A%A4%ED%8A%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-todoist-%ed%88%ac%eb%91%90%ec%9d%b4%ec%8a%a4%ed%8a%b8-%ec%97%b0%eb%8f%99/)

[![옵시디언 미니멀 테마](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%AF%B8%EB%8B%88%EB%A9%80-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%af%b8%eb%8b%88%eb%a9%80-%ed%85%8c%eb%a7%88-%ec%b9%b4%eb%93%9c%eb%b7%b0-%ea%b0%a4%eb%9f%ac%eb%a6%ac%eb%b7%b0/)

[![책 정보 수집 플러그인](https://booktracing.com/wp-content/uploads/2024/02/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-8-75x75.webp)](https://booktracing.com/%ec%b1%85-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-korean-book-info/)

[![옵시디언 콜아웃 멀티 칼럼](https://booktracing.com/wp-content/uploads/2024/02/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%BD%9C%EC%95%84%EC%9B%83-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%bd%9c%ec%95%84%ec%9b%83-%eb%a9%80%ed%8b%b0-%ec%b9%bc%eb%9f%bc/)

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png)