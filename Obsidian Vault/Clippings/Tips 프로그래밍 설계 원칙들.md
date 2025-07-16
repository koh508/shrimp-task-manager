---
title: "[Tips] 프로그래밍 설계 원칙들"
source: "https://devartrio.tistory.com/entry/Tips-%ED%94%84%EB%A1%9C%EA%B7%B8%EB%9E%98%EB%B0%8D-%EC%84%A4%EA%B3%84-%EC%9B%90%EC%B9%99%EB%93%A4"
author:
  - "[[Rio's Insight]]"
published: 2024-07-05
created: 2025-05-14
description: "KISSKeep It Simple, Supid간결함은 미덕이다.오컴의 면도날DRYDon’t Repeat YourselfOnce And Only OnceRule of ThreeHCLCHigh Cohesion Louse Coupling높은 응집도, 낮은 결합도비슷한 것들은 뭉쳐 있어야 한다서로의 의존도는 낮아야 한다.SOLIDSRP - 단일 책임 원칙 - 하나의 객체는 하나의 책임을 가진다그 하나의 책임에 의해서만 변경된다GRASP(General Responsibility Assignment Software Pattern)OCP - 개방 폐쇄 원칙 - 확장에는 열려있고 변경에는 닫혀있다.모듈의 수정 없이 기능 확장 가능인터페이스는 임의로 변경할 수 없다변경은 오류를 수정할 때만 확장은 새 클래스로 구현한다L.."
tags:
  - "clippings"
---
### KISS

Keep It Simple, Supid

- 간결함은 미덕이다.
- 오컴의 면도날

### DRY

Don’t Repeat Yourself

- Once And Only Once
- Rule of Three

### HCLC

High Cohesion Louse Coupling

- 높은 응집도, 낮은 결합도
- 비슷한 것들은 뭉쳐 있어야 한다
- 서로의 의존도는 낮아야 한다.

### SOLID

SRP - 단일 책임 원칙 - 하나의 객체는 하나의 책임을 가진다

- 그 하나의 책임에 의해서만 변경된다
- GRASP(General Responsibility Assignment Software Pattern)

OCP - 개방 폐쇄 원칙 - 확장에는 열려있고 변경에는 닫혀있다.

- 모듈의 수정 없이 기능 확장 가능
- 인터페이스는 임의로 변경할 수 없다
- 변경은 오류를 수정할 때만 확장은 새 클래스로 구현한다

LSP - 리스코프 치환 원칙 - 객체는 부모 객체를 대체 가능해야 한다.

ISP - 인터페이스 격리 원칙 - 인터페이스는 서로 격리되어야 한다

- 객체는 사용하지 않는 인터페이스의 영향을 받아서는 안된다
- 필요 인터페이스만 사용 가능해야 한다

DIP - 의존성 역전 원칙 - 상위 객체는 하위 객체를 몰라야 한다

- 의존성 순환이 벌어지면 안된다
- 추상화 인터페이스를 이용한다

내용 출처: [https://www.slideshare.net/slideshow/ndc2012-12695564/12695564](https://www.slideshare.net/slideshow/ndc2012-12695564/12695564)

#### '' 카테고리의 다른 글

| [모르면 손해인 윈도우 단축키 모음집](https://devartrio.tistory.com/entry/%EB%AA%A8%EB%A5%B4%EB%A9%B4-%EC%86%90%ED%95%B4%EC%9D%B8-%EC%9C%88%EB%8F%84%EC%9A%B0-%EB%8B%A8%EC%B6%95%ED%82%A4-%EB%AA%A8%EC%9D%8C%EC%A7%91) (0) | 2025.03.12 |
| --- | --- |
| [옵시디언 카테고리별 단축키 정리](https://devartrio.tistory.com/entry/%EC%98%B5%EC%8B%9C%EB%94%94%EC%96%B8-%EC%B9%B4%ED%85%8C%EA%B3%A0%EB%A6%AC%EB%B3%84-%EB%8B%A8%EC%B6%95%ED%82%A4-%EC%A0%95%EB%A6%AC) (0) | 2025.03.11 |
| [\[Rider\] 북마크 기능](https://devartrio.tistory.com/entry/Rider-%EB%B6%81%EB%A7%88%ED%81%AC-%EA%B8%B0%EB%8A%A5) (0) | 2024.05.09 |