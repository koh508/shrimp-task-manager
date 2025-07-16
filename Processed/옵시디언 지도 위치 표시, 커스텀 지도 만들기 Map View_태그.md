---
title: "옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View"
source: "https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/"
author:
  - "[[북트레싱]]"
published: 2024-04-03
created: 2025-07-01
description: "옵시디언 지도 위치 표시를 하여 나만의 지도를 만드는 방법에 대해 알아보겠습니다. 이를 활용하면 부동산 임장 지도를 만들거나, 여행 기록, 지역별 고객관리, 맛집 지도 등을 만드는 등 다양한 지도를 만들 수 있습니다."
tags:
  - "clippings"
---
![북트레싱](https://secure.gravatar.com/avatar/11941127f7b84c939019207d4f24b5d316232341844f140465343801c8cbf3cc?s=80&d=mm&r=g) by

[4월 9, 2024](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/)

in [옵시디언](https://booktracing.com/second-brain/obsidian/), [세컨드 브레인](https://booktracing.com/second-brain/)

A A

[0](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%a7%80%eb%8f%84-%ec%9c%84%ec%b9%98-%ed%91%9c%ec%8b%9c/#comments)

[![옵시디언 지도 위치 표시](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%A7%80%EB%8F%84-%EC%9C%84%EC%B9%98-%ED%91%9C%EC%8B%9C.webp)](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%A7%80%EB%8F%84-%EC%9C%84%EC%B9%98-%ED%91%9C%EC%8B%9C.webp)

옵시디언 지도 위치 표시를 하여 나만의 지도를 만드는 방법에 대해 알아보겠습니다.

이를 활용하면 부동산 임장 지도를 만들거나, 여행 기록, 지역별 고객관리, 맛집 지도 등을 만드는 등 다양한 지도를 만들 수 있습니다.

## 1 Map View 플러그인

위치를 지도 위에 기록하게 되면 시각적으로 볼 수 있게되어 더욱 직관적인 노트 접근이 가능합니다.  
예를 들어서 지역별로 고객을 나눠서 관리한다든지, 내가 갔던 여행지나 맛집을 지도에 기록한다든지 등으로 효율적인 관리가 가능합니다.

### 기본 사용법

마우스 좌측 버튼을 누르고 드래그를 하면 이동이 가능하고, 휠로 줌인, 줌아웃을 할 수 있습니다.

## 2 Map View 플러그인 사용법 영상 1편

![](https://www.youtube.com/watch?v=yLwZk86LoCk)

## 3 Map View 플러그인 사용법 영상 2편

![](https://www.youtube.com/watch?v=uzXQGvMmPtQ)

## 4 맵 타일 변경하기

기본으로 사용되고 있는 CartoDB는 소축적에서는 영어로 표기가 되기도 하고 자세한 정보를 보여주지 않고 있습니다.

설정에서 변경을 하실 수가 있는데 Map sources 부분을 보면 현재 CartoDB로 설정되어 있습니다.  
맵 타일을 추가하려면 New map source를 누르고 URL을 입력해주어야 합니다.

![옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View](https://booktracing.com/wp-content/uploads/2024/04/%EB%A7%B5-%ED%83%80%EC%9D%BC-%EB%B3%80%EA%B2%BD-1024x297.webp)

옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

[맵 타일](https://wiki.openstreetmap.org/wiki/Raster_tile_providers) 링크를 통해 여러 타일을 확인할 수 있습니다.  
그 중에서 가장 처음 있는 OpenStreetMap의 Standard tile을 적용해보겠습니다.

Name에는 `OpenStreet`

URL에는 `https://tile.openstreetmap.org/{z}/{x}/{y}.png`

을 입력해주고 지도를 확인을 해보면

![옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View](https://booktracing.com/wp-content/uploads/2024/04/CartoDB-1-1024x894.webp)

CartoDB

![옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View](https://booktracing.com/wp-content/uploads/2024/04/CartoDB-2-1024x890.webp)

CartoDB

메뉴에서 View – CartoDB 옆의 토글을 누르면 OpenStreet 적용이 가능합니다.  
OpenStreet로 변경하면 지도가 달라진 게 확연히 느껴집니다.  
소축적으로 바꿔서 보면 차이가 더욱 큰데, 전국의 도시들의 이름이 한글로 확인이 됩니다.

## 5 옵시디언 지도 위치 표시 방법

Map View 플러그인을 이용하여 위치를 기록하는 방법은 여러가지가 있습니다.

1. 마우스 우측 버튼을 누르고 으로 하실 수도 있지만 내가 원하는 위치를 지정하시려면 `Cmd + P` 를 누르셔서 지정할 수도 있습니다.

### 위치 수동 입력

이 부분을 수동으로도 입력이 가능한데요.  
구글맵에 접속해서 찾고자 하는 위치를 검색 후에 URL을 자세히 보면 위도와 경도가 포함되어 있습니다.

  
`https://www.google.co.kr/maps/place/국립현대미술관+서울/data=!4m10!1m2!2m1!1z6rWt66a97ZiE64yA66-47Iig6rSA!3m6!1s0x357ca2c6a9d32947:0xfb70e7c1c785a405!8m2!3d==37.5795117==!4d==126.9805862==!15sChXqta3rpr3tmITrjIDrr7jsiKDqtIAiA4gBAZIBEW1vZGVybl9hcnRfbXVzZXVt4AEA!16s%2Fm%2F0zg9hg7?hl=ko&entry=ttu`

URL의 3d 뒤에는 위도가, 4d 뒤에는 경도 정보가 있습니다.

위도와 경도 사이에 `,`를 넣어서 구분하실 수 있습니다.

`geo:` 뒤에 `==37.5795117,126.9805862==` 를 붙여넣어 주시면 위치를 기록할 수 있습니다.

### 명령어 팔레트 (Cmd + P)

![옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View](https://booktracing.com/wp-content/uploads/2024/04/%EB%AA%85%EB%A0%B9-%ED%94%84%EB%A1%AC%ED%94%84%ED%8A%B8.webp)

옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

`Cmd + P` 를 누르시고 map view를 입력해서 보면 open map view가 있고,  
그 아래에 지도에 위치를 추가할 수 있는 기능들이 있습니다.

`New geolocation note` 는 새로운 노트를 만들어 위치를 기록할 수 있고,  
`Add inline geolocation link` 는 인라인에 위치를 기록할 수 있고,  
`Add geolocation (front matter) to current note` 는 기존의 노트에 프론트 매터로 위치를 기록할 수 있습니다.

자주 사용하는 기능에는 단축키를 할당하여 손쉽게 사용할 수 있습니다.  

## 6 구글 map api

위치를 기록할 때 기본 설정을 사용하게 되면 검색이 잘 되지 않기도 하고, 구체적인 위치가 검색이 되지 않습니다.

그 이유는 Map View 설정에서 Geocoding search provider를 보면 기본으로 OpenStreetMap으로 선택이 되어 있습니다.

바로 옆의 토글을 눌러서 보면 Google을 선택해주고, 아래 API key를 입력해줍니다.

![구글-API-key](https://booktracing.com/wp-content/uploads/2024/04/%EA%B5%AC%EA%B8%80-API-key-1024x314.webp)

구글-API-key

[구글 API key 발급](https://developers.google.com/maps?hl=ko)

  
위 버튼을 눌러 Google API key를 발급 받을 수 있습니다.

개인 정보 및 결제 정보를 입력하신 다음 받을 수 있는데, 유료 결제를 따로 신청하지 않는 이상은 무료로 사용이 가능합니다.

![옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View](https://booktracing.com/wp-content/uploads/2024/04/%EA%B5%AC%EA%B8%80-API-key-%EB%B3%B5%EC%82%AC.webp)

옵시디언 지도 위치 표시, 커스텀 지도 만들기 Map View

### API 적용

API를 발급 받게 되면 우측에 복사 버튼이 있고, API key를 복사하여 옵시디언의 설정으로 다시 이동합니다.

`Gecoding API key` 에 API key를 붙여넣기 하고, 바로 아래에 있는  
`Use Google Place for Searches` 를 활성화 시켜줍니다.

Google API 적용 후 지도를 검색하면 전보다 훨씬 정확한 검색이 가능합니다.

Tags:

[Previous Post](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/)

### [옵시디언 할 일 관리를 캘린더 tasks 플러그인](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ec%ba%98%eb%a6%b0%eb%8d%94-tasks/)

옵시디언 파일 복구하기 스냅샷 기능

Next Post

[View original](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

Next Post

[![옵시디언 파일 복구 스냅샷](https://booktracing.com/wp-content/uploads/2024/04/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%ED%8C%8C%EC%9D%BC-%EB%B3%B5%EA%B5%AC-%EC%8A%A4%EB%83%85%EC%83%B7-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-%ed%8c%8c%ec%9d%bc-%eb%b3%b5%ea%b5%ac-%ec%8a%a4%eb%83%85%ec%83%b7/)

### 옵시디언 파일 복구하기 스냅샷 기능

[![Mac homebrew 홈브류 설치](https://booktracing.com/wp-content/uploads/2024/05/Mac-homebrew-%ED%99%88%EB%B8%8C%EB%A5%98-%EC%84%A4%EC%B9%98-75x75.webp)](https://booktracing.com/mac-homebrew-nodejs-python-terminal/)

### 맥(Mac OS) Homebrew(홈브류)를 통한 Node.js 및 파이썬 설치

[![윈도우 chocolatey 초코 설치](https://booktracing.com/wp-content/uploads/2024/05/%EC%9C%88%EB%8F%84%EC%9A%B0-chocolatey-%EC%B4%88%EC%BD%94-%EC%84%A4%EC%B9%98-75x75.webp)](https://booktracing.com/chocolatey-nodejs-powershell/)

### 윈도우(Windows) 초코(chocolatey)로 Node.js, python 설치, 파워쉘 (Powershell)

[![옵시디언 CSS 테마](https://booktracing.com/wp-content/uploads/2024/06/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-CSS-%ED%85%8C%EB%A7%88-75x75.webp)](https://booktracing.com/%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8-css-%ec%8a%a4%ed%83%80%ec%9d%bc-%ed%85%8c%eb%a7%88/)

### 옵시디언 CSS 테마 텍스트 편집기 설정

[![메타데이터 메뉴 플러그인](https://booktracing.com/wp-content/uploads/2024/07/%EB%A9%94%ED%83%80%EB%8D%B0%EC%9D%B4%ED%84%B0-%EB%A9%94%EB%89%B4-%ED%94%8C%EB%9F%AC%EA%B7%B8%EC%9D%B8-75x75.webp)](https://booktracing.com/%eb%a9%94%ed%83%80%eb%8d%b0%ec%9d%b4%ed%84%b0-%eb%a9%94%eb%89%b4-%ed%94%8c%eb%9f%ac%ea%b7%b8%ec%9d%b8-%ec%98%b5%ec%8b%9c%eb%94%94%ec%96%b8/)

### 메타데이터 메뉴 (metadata menu) 플러그인, (데이터뷰 테이블)

### 태그

![](https://booktracing.com/wp-content/uploads/2023/09/%EB%B6%81%ED%8A%B8%EB%9E%98%EC%8B%B1-%EC%95%BC%EA%B0%84%EB%AA%A8%EB%93%9C-%EC%A0%84%ED%99%98-1.png) 

No Result

View All Result