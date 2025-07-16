---
title: "[GitHub] 깃허브에 프로젝트 올리기"
source: "https://soda-dev.tistory.com/12"
author:
  - "[[yujch]]"
published: 2021-08-24
created: 2025-06-12
description: "보통은 저장소를 생성한뒤 'Upload files'를 하면 업로드되지만파일 갯수가 너무 많을 경우 안되므로큰 프로젝트를 업로드할때는 이 방법으로 하자    1. Git을 설치한다.https://git-scm.com/downloads Git - DownloadsDownloads macOS Windows Linux/Unix Older releases are available and the Git source repository is on GitHub. GUI Clients Git comes with built-in GUI tools (git-gui, gitk), but there are several third-party tools for users looking for a platform-specific .."
tags:
  - "clippings"
---
보통은 저장소를 생성한뒤 'Upload files'를 하면 업로드되지만

![](https://blog.kakaocdn.net/dn/3O8yJ/btrc1TWMZb5/EeDuaaiKcq8nrOh9YFn01K/img.png)

파일 갯수가 너무 많을 경우 안되므로

![](https://blog.kakaocdn.net/dn/CUHKw/btrc8h2UZRg/7OyIxyG2BsAkscj8xtMxC1/img.png)

큰 프로젝트를 업로드할때는 이 방법으로 하자

## 1\. Git을 설치한다.

[https://git-scm.com/downloads](https://git-scm.com/downloads)

[

Git - Downloads

Downloads macOS Windows Linux/Unix Older releases are available and the Git source repository is on GitHub. GUI Clients Git comes with built-in GUI tools (git-gui, gitk), but there are several third-party tools for users looking for a platform-specific exp

git-scm.com

](https://git-scm.com/downloads)

## 2\. GitHub에 새 저장소를 생성한다.

![](https://blog.kakaocdn.net/dn/qyUGD/btrc1flv7tu/HrZk2mzKAHNByi4pQncL61/img.png)

왼쪽 상단에서 클릭

![](https://blog.kakaocdn.net/dn/WzxHF/btrc2oCdm3T/qVqhZ7f1Uvp6ZA1VIvH6yk/img.png)

저장소 이름을 정하고 생성한다.

## 3\. 생성된 저장소의 주소를 기억해두자.

![](https://blog.kakaocdn.net/dn/wK0vm/btrc1d2eqyA/7QcEraZzSoQNokAekUM4W0/img.png)

.git으로 끝나는 주소이다.

## 4\. 업로드하고 싶은 프로젝트의 폴더를 마우스 우클릭 > Git Bash Here

![](https://blog.kakaocdn.net/dn/bToRXB/btrc8hBOBpk/UX2WMv4CzfEeyPcFrG5eok/img.png)

## 5\. 초기 설정을 해준다.

```shell
git config --global user.name "유저이름"

git config --global user.email "유저 이메일"
```

\- 이 창에서는 Ctrl+v로 붙여넣기 안됨 => Shift + Ins 사용하자

![](https://blog.kakaocdn.net/dn/bi4ZJP/btrc4EEA5iB/k9gr0f9TUZ5UpTAcj11Xf0/img.png)

## 6\. 파일 준비

```shell
git init      #.git 파일 생성

git add .     #선택한 프로젝트 폴더 내의 모든 파일 관리
        -> 특정파일만 하고 싶다면  git add 파일이름.파일형식  ex) git add a.txt

git status    #상태확인

git commit -m "주석"     #커밋
```
![](https://blog.kakaocdn.net/dn/cdUqtY/btrcUj9pQaH/NACK88NMkt34Kmc67WjRDk/img.png)

## 7\. 업로드하기

```shell
git remote add origin {위 3번에서 저장한 깃허브 저장소 주소}

git push -u origin master
```
![](https://blog.kakaocdn.net/dn/q6acr/btrdaEQQaEj/VwKCWn39bGKgqGtUf5c7G0/img.png)

## 8\. 프로젝트 업로드 완료

![](https://blog.kakaocdn.net/dn/dOMoNV/btrc3ZIx46P/lnQV0rDkR37rE98qghOxk0/img.png)

## 9\. 프로젝트 설명 적기

![](https://blog.kakaocdn.net/dn/vV694/btrc4DsbdzG/tLkRr3fh4kEhTwtOeRON70/img.png)

설정(톱니바퀴) 클릭

![](https://blog.kakaocdn.net/dn/diZJoo/btrc2o3jB04/IOKsth5Qh9EpC6uwmnuAl0/img.png)

Description에 적고 저장

[https://creatorlink.net](https://ader.naver.com/v1/DE9VUbMC6qxX3FCBXcXy08OKymZq8Jwo9CZh3PX0PoUrvgHVR8VfOwRIZ7bkN92YPEXHTJKbXCpGrJAdCYM4r4Lp_vdSvlXITog0Yl1JisMOiw9pMjNclPbyScoXU0r5XtvtnntvTWyCPyYzZ76PQ0aCbnwhdgFmWzKS-BPFBJahXFcXLNl94yobxzEmwaS7UIzNWapIYXXvInJrffNtZfaoUp_TDBIU0f50C_v-MxkCQDLaUMeDyOEDCdayBcr79qcDwnhCxhdFug2s9aj_RGf18_zQG62SqpKboWPCRhFB_Vp5Zi1iFsD6qjJOgBwWRruPrx7bRL78KQPuZgC9CnR1IPWvOKKl5XI7GqSrHslpedkD4kqHkQjsN_kkNNkClUMxwZRJs96QbfYRccOOmHeWuIWrKKJdisSc3z4nPO8=?c=tistory.ch1&t=0) 광고

[크리에이터링크 GITHUB](https://ader.naver.com/v1/DE9VUbMC6qxX3FCBXcXy08OKymZq8Jwo9CZh3PX0PoUrvgHVR8VfOwRIZ7bkN92YPEXHTJKbXCpGrJAdCYM4r4Lp_vdSvlXITog0Yl1JisMOiw9pMjNclPbyScoXU0r5XtvtnntvTWyCPyYzZ76PQ0aCbnwhdgFmWzKS-BPFBJahXFcXLNl94yobxzEmwaS7UIzNWapIYXXvInJrffNtZfaoUp_TDBIU0f50C_v-MxkCQDLaUMeDyOEDCdayBcr79qcDwnhCxhdFug2s9aj_RGf18_zQG62SqpKboWPCRhFB_Vp5Zi1iFsD6qjJOgBwWRruPrx7bRL78KQPuZgC9CnR1IPWvOKKl5XI7GqSrHslpedkD4kqHkQjsN_kkNNkClUMxwZRJs96QbfYRccOOmHeWuIWrKKJdisSc3z4nPO8=?c=tistory.ch1&t=0) [100%무료! 무료 도메인/호스팅! 누구나 쉽게 코딩없이 직접 만드는 홈페이지!](https://ader.naver.com/v1/DE9VUbMC6qxX3FCBXcXy08OKymZq8Jwo9CZh3PX0PoUrvgHVR8VfOwRIZ7bkN92YPEXHTJKbXCpGrJAdCYM4r4Lp_vdSvlXITog0Yl1JisMOiw9pMjNclPbyScoXU0r5XtvtnntvTWyCPyYzZ76PQ0aCbnwhdgFmWzKS-BPFBJahXFcXLNl94yobxzEmwaS7UIzNWapIYXXvInJrffNtZfaoUp_TDBIU0f50C_v-MxkCQDLaUMeDyOEDCdayBcr79qcDwnhCxhdFug2s9aj_RGf18_zQG62SqpKboWPCRhFB_Vp5Zi1iFsD6qjJOgBwWRruPrx7bRL78KQPuZgC9CnR1IPWvOKKl5XI7GqSrHslpedkD4kqHkQjsN_kkNNkClUMxwZRJs96QbfYRccOOmHeWuIWrKKJdisSc3z4nPO8=?c=tistory.ch1&t=0)

[![](https://searchad-phinf.pstatic.net/MjAyMTAzMTJfMjA1/MDAxNjE1NTIyNjgxOTAz.qg_LHLyCsoiQiBdyFJgaoFp2gqZ-AzpXl4gDU1p87kEg.v3uCphnkFAxYpikX5ciJnHqxBYhV9Y5AnT3QVrOf3Ogg.JPEG/1100445-a6abf670-3172-4ed6-94c3-7f18f85f4832.jpg)](https://ader.naver.com/v1/R5gLPU41Bs90M0ROOcQPMQX9sINQDvZMRdncCW7sEf9J2Mrk7vx_t0E7mJ4On8Xqt2RdEzqJnbFV6YgAOqRMC-oPHG3pBT7hF3U4-mAWKBAhqGmfp6ao7d6o7s6yRa4SsuHmhW1J15YcFJdAYFewTWirfOPNaq1dRgTqYYiiTZeudhBl3-88bZXZdo7_fyRxaIHg_uuqnSks8XxHyiiX2Dg2iRSMWfYfjhXCInDWqyNX8t--YUDlqwvEQcPmm8IlfpmaMt4lRf1ohLC1TimSle5FsNA-u3fYGbjZoYggKbr_kF99Uvv73-ffTUKp9MPoD1SMAQabdbsKdn4UZqbtNBoW80KQIQT989k30I16-bvWvm-Vx08M3-upBTXuLjFMtJPXsXzZA2oSBPbhw1hCzZVkSCg8f7iu4rGLfXQcTtFlVnRqNBf5YJ5MXfxhtZAo?c=tistory.ch1&t=0)

[http://hutess.com](https://ader.naver.com/v1/AOawzKnMOPZ-OKfyIjAIPDzahsBbnUwnM2lEOMiIw4uX8lY5eS80NlPVQnNaLTHBbjoYNADMD3-3FRkdmgT6qb_WoV0uwq4Gjj5yHUrio9DZqQZq0GuCX6aviSyHv2-431NWLTL_XjtIXf4AeRKLKgjMkJCZLYTqvyQYIjTBd_6GbiKPYE1Rde-VTdM-MTnTWMMiQvR0uoIsVscl1ZObJg==?c=tistory.ch1&t=0) 광고

[공작물 자동워크셋팅 프로브](https://ader.naver.com/v1/AOawzKnMOPZ-OKfyIjAIPDzahsBbnUwnM2lEOMiIw4uX8lY5eS80NlPVQnNaLTHBbjoYNADMD3-3FRkdmgT6qb_WoV0uwq4Gjj5yHUrio9DZqQZq0GuCX6aviSyHv2-431NWLTL_XjtIXf4AeRKLKgjMkJCZLYTqvyQYIjTBd_6GbiKPYE1Rde-VTdM-MTnTWMMiQvR0uoIsVscl1ZObJg==?c=tistory.ch1&t=0) [공작기계에서 워크좌표계 자동셋팅과가공후 검사로 불량및생산성향상은물론 정밀가공탁월함](https://ader.naver.com/v1/AOawzKnMOPZ-OKfyIjAIPDzahsBbnUwnM2lEOMiIw4uX8lY5eS80NlPVQnNaLTHBbjoYNADMD3-3FRkdmgT6qb_WoV0uwq4Gjj5yHUrio9DZqQZq0GuCX6aviSyHv2-431NWLTL_XjtIXf4AeRKLKgjMkJCZLYTqvyQYIjTBd_6GbiKPYE1Rde-VTdM-MTnTWMMiQvR0uoIsVscl1ZObJg==?c=tistory.ch1&t=0)

#### ' > ' 카테고리의 다른 글

| [\[Eclipse\] TODO Auto-generated method stub 주석 제거](https://soda-dev.tistory.com/20) (0) | 2021.09.27 |
| --- | --- |
| [\[Eclipse\] 테마 변경하기](https://soda-dev.tistory.com/19) (0) | 2021.09.27 |
| [\[Eclipse\] 소스파일 export, import](https://soda-dev.tistory.com/13) (0) | 2021.09.04 |
| [\[Eclipse\] 겪었던 에러들 해결방법](https://soda-dev.tistory.com/11) (0) | 2021.08.24 |
| [\[Eclipse\] 코드 자동완성 Emmet 설치하기](https://soda-dev.tistory.com/9) (2) | 2021.08.24 |