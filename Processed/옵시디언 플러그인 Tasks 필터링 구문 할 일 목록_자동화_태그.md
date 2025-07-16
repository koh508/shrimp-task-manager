---
title: "옵시디언 플러그인 Tasks 필터링 구문 할 일 목록"
source: "https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/"
author:
  - "[[북트레싱]]"
published: 2023-12-24
created: 2025-07-01
description: "옵시디언에서 할 일을 관리해주는 플러그인 Tasks 필터링 구문을 정리했습니다."
tags:
  - "clippings"
---
by

[12월 24, 2023](https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/)

A A

[0](https://booktracing.com/tasks-%ed%95%84%ed%84%b0%eb%a7%81-%ea%b5%ac%eb%ac%b8/#comments)

[![옵시디언_tasks_필터링_구문](https://booktracing.com/wp-content/uploads/2023/12/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8_tasks_%ED%95%84%ED%84%B0%EB%A7%81_%EA%B5%AC%EB%AC%B8-750x750.webp)](https://booktracing.com/wp-content/uploads/2023/12/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8_tasks_%ED%95%84%ED%84%B0%EB%A7%81_%EA%B5%AC%EB%AC%B8.webp)

옵시디언에서 할 일을 관리해주는 플러그인 Tasks 필터링 구문을 정리했습니다.

이 플러그인은 일상적인 작업이나 복잡한 업무 등에 사용이 되는데할 일을 명확하게 정리하고,  
우선순위를 설정하는 등 생산성과 효율성을 높일 수가 있습니다.

![](https://www.youtube.com/watch?v=Qok3EljgmbA)

## 1 자이가르닉 효과

우리가 할 일을 관리해야 하는 이유는 단순히 일을 잊어버리지 않고 수행하기 위한 것도 있겠지만 그 외에도 많은 이점들이 있습니다.  
보통 머릿속이 복잡할 때 노트에 간단히 적어보는 것만으로도 어느 정도 복잡함이 사라지고 개운한 느낌이 들기도 하는데,  
이건 미완성된 일에 대해 메모를 작성함으로써 뇌에게 나중에 처리할 것이라는 확신을 주는 겁니다.  
  
이 방법으로 인지적 긴장을 줄여주고 해야할 일을 나중에 완료할 것이라는 계획을 세우고 이를 기록함으로써 우리의 뇌는 그 과제에 대한 긴장을 해소하고 다른 일에 집중을 할 수 있게 되는 겁니다.

## 2 Tasks 필터링 구문

아래에 있는 구문들 외에 많은 구문들은 [Tasks User Guide](https://publish.obsidian.md/tasks/Introduction) 를 참고하시면 더욱 더 풍성한 옵시디언의 활용이 가능합니다.

아래 코드 블록의 글을 복사해서 옵시디언의 노트에 붙여넣고 사용하세요

```js
### 완료되지 않은 일
not done
### 완료된 일
- has done date
- no done date
- done (on|befor|after) \<date>|\<data range>
### 정렬
- sort by priority
- sort by due
- sort by start
- sort by scheduled
- sort by done
- sort by description
- sort by path
- sort by recurring
- sort by tag
### 숨김
- hide start date
- hide due date
- hide edit button
- hide backlink
### 마감 기한
- due 2023-12-25
- due before yesterday
- due today
- due after 3 days ago
- due in this week
- due after this month
- due or or before next year
- due in 2023-Www(ww에는 주, 2자리 숫자)
- due in 2023-10 (10월)
- due (before|after|in) \<data range>
### priority
- priority is (above|below|not) (lowest|low|none|medium|high|highest)
## Custom filter
### 비어있는 필드
#### 비어있는 작업 찾기
description regex matches /^$/
#### 비어있는 작업 제외하기
description regex does not match /^$/
### 폴더 필터링
#### 현재의 폴더에 들어있는 할 일
folder includes {{query.file.folder}}
#### 폴더를 포함
filter by function task.file.folder.includes("폴더 이름")
```

Tags:

[Previous Post](https://booktracing.com/%ec%84%b8%ec%bb%a8%eb%93%9c%eb%b8%8c%eb%a0%88%ec%9d%b8-%ea%b5%ac%ec%b6%95-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91/)

### [세컨드브레인 구축을 위한 지식 수집](https://booktracing.com/%ec%84%b8%ec%bb%a8%eb%93%9c%eb%b8%8c%eb%a0%88%ec%9d%b8-%ea%b5%ac%ec%b6%95-%ec%a0%95%eb%b3%b4-%ec%88%98%ec%a7%91/)

템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%85%9c%ed%94%8c%eb%a6%bf-templater-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8/)

Next Post

[![Templater 플러그인 사용법](https://booktracing.com/wp-content/uploads/2023/12/Templater-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-%EC%82%AC%EC%9A%A9%EB%B2%95-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%85%9c%ed%94%8c%eb%a6%bf-templater-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8/)

### 템플릿을 만들어 옵시디언에서 지식 관리하자, Templater 플러그인

[![옵시디언 데일리 노트 템플릿](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%BC%EB%A6%AC-%EB%85%B8%ED%8A%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%bc%eb%a6%ac-%eb%85%b8%ed%8a%b8-%ed%85%9c%ed%94%8c%eb%a6%bf/)

### 옵시디언 데일리 노트를 만들어 2024년, 새롭게 시작해보자

[![옵시디언 데이터뷰 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%B7%B0-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%eb%8d%b0%ec%9d%b4%ed%84%b0%eb%b7%b0-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-dataview/)

### 플러그인 중 가장 강력한 옵시디언 데이터뷰, dataview

[![옵시디언 주간 계획 위클리 노트](https://booktracing.com/wp-content/uploads/2024/01/%EC%A0%9C%EB%AA%A9%EC%9D%84-%EC%9E%85%EB%A0%A5%ED%95%B4%EC%A3%BC%EC%84%B8%EC%9A%94_-001-4-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a3%bc%ea%b0%84-%ea%b3%84%ed%9a%8d-%ec%9c%84%ed%81%b4%eb%a6%ac-%eb%85%b8%ed%8a%b8/)

### 옵시디언 주간 계획을 자동화해서 더욱 강력한 생산성 향상

[![옵시디언 Tracker 플러그인](https://booktracing.com/wp-content/uploads/2024/01/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-Tracker-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-tracker-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%8a%b5%ea%b4%80/)

### 월간, 연간 계획 꾸준한 습관 기르기, Tracker 플러그인

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result