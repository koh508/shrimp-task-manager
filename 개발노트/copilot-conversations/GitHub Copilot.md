---
title: "GitHub Copilot"
source: "https://github.com/copilot/c/d2bc2229-1558-46b2-8e2f-4d3a1af81bd0"
author:
  - "[[GitHub]]"
published:
created: 2025-05-20
description: "GitHub is where people build software. More than 150 million people use GitHub to discover, fork, and contribute to over 420 million projects."
tags:
  - "clippings"
---
옵시디언으로 네이버블로그에 있는 글을 다 가져오고 싶어 관련해서 만들어진 거 있을까?

옵시디언(Obsidian)에서 네이버 블로그의 글을 한 번에 가져오는(크롤링/마이그레이션) 플러그인이나 스크립트가 있는지 궁금하신 거죠?  
현재 공식적인 옵시디언 플러그인 마켓플레이스에는 "네이버 블로그"를 직접 지원하는 플러그인은 없습니다. 다만, 몇 가지 우회 방법이나 커뮤니티에서 공유된 스크립트, 워크플로우가 있을 수 있습니다.

### 일반적인 방법

1. **네이버 블로그 글 백업/내보내기 → 마크다운 변환 → 옵시디언 가져오기**
	- 네이버 블로그에서 글을 백업(내보내기)하면 XML 파일로 받을 수 있습니다.
	- 이 XML을 마크다운(.md) 파일로 변환해주는 스크립트(파이썬 등)가 깃허브 등지에 공개되어 있습니다.
	- 변환된 .md 파일을 옵시디언 vault 폴더에 넣으면 바로 사용할 수 있습니다.
2. **웹 크롤링/스크래핑**
	- 파이썬의 BeautifulSoup, Selenium 등으로 네이버 블로그에서 글을 직접 크롤링해 마크다운으로 저장하는 스크립트를 사용할 수 있습니다.
	- 이미 만들어진 오픈소스 프로젝트나 깃허브 저장소가 있을 수 있습니다.

### 관련 프로젝트/스크립트 예시

- GitHub에서 "네이버 블로그 마크다운 변환", "naver blog to markdown" 등으로 검색하면 여러 파이썬 스크립트, 노코드 워크플로우 등이 나옵니다.
	- 예) [github.com/jungwinter/naver-blog-backup](https://github.com/jungwinter/naver-blog-backup)
	- 예) [github.com/kybin/naver-blog2markdown](https://github.com/kybin/naver-blog2markdown)

### 옵시디언 플러그인 마켓 내 직접 지원 플러그인

- "네이버 블로그"를 키워드로 한 공식 플러그인은 없습니다.
- 하지만 **Web Clipper** 플러그인(Obsidian Web Clipper, MarkDownload 등)을 사용하면 브라우저에서 네이버 블로그 글을 열고, 마크다운으로 바로 옵시디언에 저장할 수 있습니다.  
	(단, 이 방법은 글 하나씩 저장하는 방식입니다.)

---

#### 요약

- 대량 자동화는 "네이버 블로그 백업 → 마크다운 변환 → 옵시디언"이 가장 효율적입니다.
- 이미 공개된 변환 스크립트를 활용하면 됩니다.
- 옵시디언 플러그인 마켓에는 공식 플러그인은 없으나 Web Clipper류 플러그인과 외부 스크립트 활용이 가능합니다.

원하시면 변환 스크립트 예시나, 사용법, 또는 직접 쓸 수 있는 파이썬 코드 샘플을 안내해드릴 수 있습니다!  
필요한 정보나 예시가 있다면 말씀해주세요.