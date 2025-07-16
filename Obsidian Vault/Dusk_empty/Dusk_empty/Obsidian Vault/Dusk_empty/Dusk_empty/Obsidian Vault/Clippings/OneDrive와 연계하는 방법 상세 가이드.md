---
title: "OneDrive와 연계하는 방법: 상세 가이드"
source: "https://subinto.tistory.com/244"
author:
  - "[[subinto의 개발노트]]"
published: 2025-01-18
created: 2025-05-18
description: "OneDrive는 Microsoft에서 제공하는 클라우드 스토리지 서비스로, 파일 저장, 공유, 동기화 등을 제공합니다. 다양한 애플리케이션이나 시스템에서 OneDrive와 연계하면 클라우드 스토리지를 활용하여 데이터를 관리할 수 있습니다. 이 글에서는 OneDrive와의 연계를 구현하는 방법을 자세히 설명합니다. 주요 주제는 OneDrive API 활용, 인증 설정, 파일 업로드/다운로드, 파일 관리 등입니다.1. OneDrive 연동의 필요성OneDrive와의 연동은 다음과 같은 이유로 유용합니다:클라우드 데이터 관리:데이터를 안전하게 클라우드에 저장하고 관리.여러 플랫폼에서 접근 가능:Windows, Mac, iOS, Android에서 파일 접근 가능.공유 및 협업:파일을 실시간으로 공유하고 협업 .."
tags:
  - "clippings"
---
OneDrive는 Microsoft에서 제공하는 클라우드 스토리지 서비스로, 파일 저장, 공유, 동기화 등을 제공합니다. 다양한 애플리케이션이나 시스템에서 OneDrive와 연계하면 클라우드 스토리지를 활용하여 데이터를 관리할 수 있습니다. 이 글에서는 OneDrive와의 연계를 구현하는 방법을 자세히 설명합니다. 주요 주제는 OneDrive API 활용, 인증 설정, 파일 업로드/다운로드, 파일 관리 등입니다.

---

## 1\. OneDrive 연동의 필요성

OneDrive와의 연동은 다음과 같은 이유로 유용합니다:

1. **클라우드 데이터 관리**:
	- 데이터를 안전하게 클라우드에 저장하고 관리.
2. **여러 플랫폼에서 접근 가능**:
	- Windows, Mac, iOS, Android에서 파일 접근 가능.
3. **공유 및 협업**:
	- 파일을 실시간으로 공유하고 협업 가능.
4. **백업 및 복구**:
	- 데이터 유실 시 복구를 간단히 처리.

---

## 2\. OneDrive 연계 구성 요소

OneDrive와의 연계는 Microsoft Graph API를 활용하여 이루어집니다. 구성 요소는 다음과 같습니다.

### 2.1 Microsoft Graph API

Microsoft Graph API는 OneDrive를 비롯한 Microsoft 365 서비스에 접근할 수 있는 RESTful API입니다.

- **주요 기능**:
	- 파일 업로드, 다운로드.
	- 파일 및 폴더 생성.
	- 권한 관리 및 공유.

### 2.2 OAuth 2.0 인증

OneDrive와 연동하려면 OAuth 2.0 인증을 통해 사용자 또는 애플리케이션이 Microsoft 계정에 접근할 권한을 가져야 합니다.

---

## 3\. OneDrive 연동 단계

### 3.1 Microsoft Azure Portal 설정

1. **애플리케이션 등록**:
	- [Azure Portal](https://portal.azure.com/) 에 로그인.
	- **Azure Active Directory** > **앱 등록** > **새 등록** 선택.
	- 애플리케이션 이름을 입력하고, 지원 계정 유형을 선택합니다.
		- 조직 계정만 사용하거나, 모든 계정을 허용할 수 있습니다.
	- 리디렉션 URI를 설정합니다. (예: `http://localhost`)
2. **클라이언트 ID와 비밀 키 생성**:
	- 앱 등록 완료 후, **앱 등록 세부 정보** 에서 **애플리케이션(클라이언트) ID** 를 복사합니다.
	- **인증서 및 비밀** 탭에서 새로운 클라이언트 비밀 키를 생성하고 저장합니다.
3. **API 권한 추가**:
	- **API 권한** 탭에서 **Microsoft Graph** 를 선택.
	- 다음 권한을 추가:
		- `Files.ReadWrite` (파일 읽기 및 쓰기).
		- `offline_access` (오프라인 접근).

---

### 3.2 OAuth 2.0 인증 구현

OneDrive와 통신하려면 OAuth 2.0을 통해 액세스 토큰을 받아야 합니다.

#### 1) 인증 URL 생성

다음과 같이 인증 URL을 생성합니다:

```
https://login.microsoftonline.com/common/oauth2/v2.0/authorize?
client_id={클라이언트_ID}&
response_type=code&
redirect_uri={리디렉션_URI}&
scope=Files.ReadWrite offline_access
```
- **client\_id**: Azure에서 생성한 클라이언트 ID.
- **redirect\_uri**: 애플리케이션에 설정한 URI.
- **scope**: API 요청 범위.

#### 2) 인증 코드 교환

인증 코드(`code`)를 받은 후, 이를 액세스 토큰으로 교환합니다.

**POST 요청**:

```
POST https://login.microsoftonline.com/common/oauth2/v2.0/token
Content-Type: application/x-www-form-urlencoded

client_id={클라이언트_ID}
&client_secret={클라이언트_비밀}
&grant_type=authorization_code
&code={인증_코드}
&redirect_uri={리디렉션_URI}
```

**응답 예시**:

```json
{
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "Files.ReadWrite",
  "access_token": "{액세스_토큰}",
  "refresh_token": "{리프레시_토큰}"
}
```

---

### 3.3 파일 업로드 및 다운로드

#### 1) 파일 업로드

Microsoft Graph API를 사용하여 파일을 업로드합니다.

**API 호출**:

```
PUT https://graph.microsoft.com/v1.0/me/drive/root:/folder/filename.txt:/content
Authorization: Bearer {액세스_토큰}
Content-Type: text/plain

파일 내용
```
- **Authorization 헤더**: Bearer {액세스 토큰}.
- **URL 경로**: `folder/filename.txt` 경로로 파일 업로드.

**응답 예시**:

```json
{
  "id": "A12345",
  "name": "filename.txt",
  "size": 1024,
  "webUrl": "https://onedrive.live.com/?cid=..."
}
```

#### 2) 파일 다운로드

**API 호출**:

```
GET https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/content
Authorization: Bearer {액세스_토큰}
```
- **item\_id**: 다운로드할 파일의 ID.

---

### 3.4 폴더 관리

#### 폴더 생성

**API 호출**:

```
POST https://graph.microsoft.com/v1.0/me/drive/root/children
Authorization: Bearer {액세스_토큰}
Content-Type: application/json

{
  "name": "NewFolder",
  "folder": {},
  "@microsoft.graph.conflictBehavior": "rename"
}
```
- **`@microsoft.graph.conflictBehavior`**: 같은 이름의 폴더가 있을 때 처리 방식.

---

### 3.5 파일 공유

OneDrive 파일을 공유하려면 링크를 생성합니다.

**API 호출**:

```
POST https://graph.microsoft.com/v1.0/me/drive/items/{item_id}/createLink
Authorization: Bearer {액세스_토큰}
Content-Type: application/json

{
  "type": "view"
}
```

**응답 예시**:

```json
{
  "link": {
    "type": "view",
    "webUrl": "https://onedrive.live.com/..."
  }
}
```

---

## 4\. OneDrive 연계 예제: Java로 구현

#### Maven 종속성 추가

```xml
<dependency>
    <groupId>com.microsoft.graph</groupId>
    <artifactId>microsoft-graph</artifactId>
    <version>5.0.0</version>
</dependency>
```

#### 코드 예제

```java
import com.microsoft.graph.models.DriveItem;
import com.microsoft.graph.requests.GraphServiceClient;

import okhttp3.Request;

public class OneDriveExample {
    public static void main(String[] args) {
        String accessToken = "{액세스_토큰}";

        GraphServiceClient<Request> graphClient = GraphServiceClient.builder()
            .authenticationProvider(request -> request.addHeader("Authorization", "Bearer " + accessToken))
            .buildClient();

        // 파일 업로드
        DriveItem driveItem = graphClient.me().drive().root().itemWithPath("example.txt").content()
            .buildRequest()
            .put("파일 내용".getBytes());

        System.out.println("Uploaded File: " + driveItem.name);
    }
}
```

---

## 5\. 결론

OneDrive와 연계하면 클라우드 스토리지를 효율적으로 활용할 수 있습니다. OAuth 2.0을 통한 인증, Microsoft Graph API 호출, 파일 관리 등을 적절히 구성하면 파일 업로드, 다운로드, 공유, 폴더 관리와 같은 다양한 작업을 자동화할 수 있습니다. 이 글을 기반으로 OneDrive와의 연계를 성공적으로 구현해 보세요!

[https://www.raidrive.com/ko](https://adcr.naver.com/adcr?x=JS8RMDiHxa9z8XB7mwOOmf///w==kM30IDaaELwOoJ2TLe4JM/+BMMrE8nGNg/7BGXYqvGXNocORjI+N2TTXuyVyWjdNTzExJSejuTsvuDdsMnXQMAdV5Makw1XEGkgZ76k6tmj0sF9p1YfX0cn8u9FZJAj/diFap16k/TEfpAp4RwsE61MgczuGtk7/wMpUQMYv5aV+oRETmntANHIas/+kJ5V3I7cFTheWuCedzmvOnocg/5sdiFGQc61Xhm5GQdtOscyHOP3r2OAdwYJ/tFyI38V/GpommEtQVwrgKxaMJ2RGgO2puVS6DwV4PrPNzjob0XsvKDypvquV+oMBhPe3sOcYMgCpI/tdnDok/otAm2Qbtjck5L7/FIzvH0231fqLqLc2KoJFPWC4vtmPQDp6gRS1Lwhuz4qjenfJdh5yg3DnRIoZUxPsJCOgQXhB91MfnwwFiTwySU+Wk+WWzSFmfUxfA3ln1ndAUI+VaIvMPSfNel7QJcVhTdhVSmkTaDtZtrJ3Jf6xz778b+yiD1DLj6T6mJEoyVbHYwyq6O9YOr40CYSG/kJRg4oMYdwAdNaor2+NStOG2Q9rV6kX6x3+tJYAWhN9/PvJUQ+k4Ro6dsUcHCjYi1X/GYTpNqM2jaBv0rjGxGu9qwiL9sL9upJ/p1ltt4U8yLCzDIhzrF2B1tyEmXzTSEw+77NVJ9DeU5epASlo=) 광고

[레이드라이브, NO브라우저 학교용 무료제공](https://adcr.naver.com/adcr?x=JS8RMDiHxa9z8XB7mwOOmf///w==kM30IDaaELwOoJ2TLe4JM/+BMMrE8nGNg/7BGXYqvGXNocORjI+N2TTXuyVyWjdNTzExJSejuTsvuDdsMnXQMAdV5Makw1XEGkgZ76k6tmj0sF9p1YfX0cn8u9FZJAj/diFap16k/TEfpAp4RwsE61MgczuGtk7/wMpUQMYv5aV+oRETmntANHIas/+kJ5V3I7cFTheWuCedzmvOnocg/5sdiFGQc61Xhm5GQdtOscyHOP3r2OAdwYJ/tFyI38V/GpommEtQVwrgKxaMJ2RGgO2puVS6DwV4PrPNzjob0XsvKDypvquV+oMBhPe3sOcYMgCpI/tdnDok/otAm2Qbtjck5L7/FIzvH0231fqLqLc2KoJFPWC4vtmPQDp6gRS1Lwhuz4qjenfJdh5yg3DnRIoZUxPsJCOgQXhB91MfnwwFiTwySU+Wk+WWzSFmfUxfA3ln1ndAUI+VaIvMPSfNel7QJcVhTdhVSmkTaDtZtrJ3Jf6xz778b+yiD1DLj6T6mJEoyVbHYwyq6O9YOr40CYSG/kJRg4oMYdwAdNaor2+NStOG2Q9rV6kX6x3+tJYAWhN9/PvJUQ+k4Ro6dsUcHCjYi1X/GYTpNqM2jaBv0rjGxGu9qwiL9sL9upJ/p1ltt4U8yLCzDIhzrF2B1tyEmXzTSEw+77NVJ9DeU5epASlo=) [원드라이브, 이제 동기화 없이 탐색기의 네트워크 드라이브로 직접 연결해보세요.](https://adcr.naver.com/adcr?x=JS8RMDiHxa9z8XB7mwOOmf///w==kM30IDaaELwOoJ2TLe4JM/+BMMrE8nGNg/7BGXYqvGXNocORjI+N2TTXuyVyWjdNTzExJSejuTsvuDdsMnXQMAdV5Makw1XEGkgZ76k6tmj0sF9p1YfX0cn8u9FZJAj/diFap16k/TEfpAp4RwsE61MgczuGtk7/wMpUQMYv5aV+oRETmntANHIas/+kJ5V3I7cFTheWuCedzmvOnocg/5sdiFGQc61Xhm5GQdtOscyHOP3r2OAdwYJ/tFyI38V/GpommEtQVwrgKxaMJ2RGgO2puVS6DwV4PrPNzjob0XsvKDypvquV+oMBhPe3sOcYMgCpI/tdnDok/otAm2Qbtjck5L7/FIzvH0231fqLqLc2KoJFPWC4vtmPQDp6gRS1Lwhuz4qjenfJdh5yg3DnRIoZUxPsJCOgQXhB91MfnwwFiTwySU+Wk+WWzSFmfUxfA3ln1ndAUI+VaIvMPSfNel7QJcVhTdhVSmkTaDtZtrJ3Jf6xz778b+yiD1DLj6T6mJEoyVbHYwyq6O9YOr40CYSG/kJRg4oMYdwAdNaor2+NStOG2Q9rV6kX6x3+tJYAWhN9/PvJUQ+k4Ro6dsUcHCjYi1X/GYTpNqM2jaBv0rjGxGu9qwiL9sL9upJ/p1ltt4U8yLCzDIhzrF2B1tyEmXzTSEw+77NVJ9DeU5epASlo=)

[![](https://searchad-phinf.pstatic.net/MjAyMjA2MTNfMjc5/MDAxNjU1MTMwMDM2ODEw.fN9i_c0HUsleVwrDgZvch4gyVmhsu17QhCQxeBDmRhEg.tw2vDZ7g-j_3UCvJSTNjQX6lmpW9XRZpfba0yFGAtl4g.JPEG/1203809-5ff3ae74-9e53-472d-815d-78f895d07f80.jpg)](https://adcr.naver.com/adcr?x=UjevqF4TnXWhcjAvD3L1b////w==kM30IDaaELwOoJ2TLe4JM/+BMMrE8nGNg/7BGXYqvGXNocORjI+N2TTXuyVyWjdNTdJw50EGov9u/OGlNdeesNtV5Makw1XEGkgZ76k6tmj0sF9p1YfX0cn8u9FZJAj/diFap16k/TEfpAp4RwsE61MgczuGtk7/wMpUQMYv5aV+oRETmntANHIas/+kJ5V3I7cFTheWuCedzmvOnocg/5sdiFGQc61Xhm5GQdtOscyHOP3r2OAdwYJ/tFyI38V/GpommEtQVwrgKxaMJ2RGgO2puVS6DwV4PrPNzjob0XsvKDypvquV+oMBhPe3sOcYMgCpI/tdnDok/otAm2Qbtjck5L7/FIzvH0231fqLqLc2KoJFPWC4vtmPQDp6gRS1Lwhuz4qjenfJdh5yg3DnRIi1f6t7t9bGNGv9+rSklQuFXmS3Cib2IITbGRuUpVWx0jaHT/tGikeIM4fuAc7rxsXaclhbsASGBCCL9zUapVPT7GYmLDvLhPGb+YkrJklLz2MKxVLMft7GNEzrqOhL3Ny8PrIFdBCieclET+nkUL4kpYEefrCeMFu4/Z1i6BTcSjnkOzvBQg24lykDSYVIYG1AmSqMuJBlOa5a8VqL3NCWuKBGcVDpR0pHKuESENZ62w6WNe9wAVaArs820DYoRatGA17hx2HXp36D8Yf3a4NQ=)

[http://www.douzone.biz](https://adcr.naver.com/adcr?x=mdU9SqZjhkV/y8cIjFvH5P///w==kWO4JQlbBx13BqCCOeqVr/+IhdbXOnmS1ZAjzA95ymQZ0gjE+HtUD9GbQhvar+jpW4yITbQO5wFwTsSZnRiPEfBD8QOOMU/hqBYiQGICCb2CKetf2BsaK3TeiPYmJLNiFz+FVRnXv6NkQsLzAysngE7yLum/Zk2lNHDNLkKQqHq2Cl2SP/xSffTVNy75+dTV6XpKxF/j1tlauQ9yYICdvsKq0X6fxO2Ah7fGA7JAeCdKq1NGjMKfNS4F/7fXrWWvmQ68uGRKlu1KhzXKd/iZRptsLE+LloyxBfmFuWwxtt8yzOxJSklwr4op6+/qpRxODHCF5HpAMxqK6KkEZjnSZ9lOp3hgeSXG8QMhjdiQrvfc0ygAtgUaN26KCvRwG6bbx1vM3Za8MtMuL8oyfJlWjzyHEtwW0BqQVZNjewVrjJ/iaZYZuFkhRx0avvvTGYShcfH+btRY6fgYE+11syUVfiZUfIkOS6kZhVKQMmiNWDUpf8i6DNZbnKZ9M9lYbqMVg1EUPtv4sq/K+KlLxERT0DhBffSef6piVCwHKcfavs1eTuJl0/cLxOkg+3m9kf5t/WsFXYZXbLstyOc1mG0I7NvK5X2zz0mSztyj7NLw27ZY24iq6jhdGGAzT2Eod2CW1G06t6iLYgWuhMAxI3koACr+Zm7J+eawiqf9lZKqqMXjFWelOIDYusR6OV1/MeGgVl44rCq0h4d0HGogUoFCox25FBZ8PnwjIORG6XVl0PFjHg3b1wvFiH55oYbrvSp92wIWD5Wv6GE+hYT9boU3GyUqjVRKT14l1R2KEGpm28Qs=) 광고

[더존 공식사이트](https://adcr.naver.com/adcr?x=mdU9SqZjhkV/y8cIjFvH5P///w==kWO4JQlbBx13BqCCOeqVr/+IhdbXOnmS1ZAjzA95ymQZ0gjE+HtUD9GbQhvar+jpW4yITbQO5wFwTsSZnRiPEfBD8QOOMU/hqBYiQGICCb2CKetf2BsaK3TeiPYmJLNiFz+FVRnXv6NkQsLzAysngE7yLum/Zk2lNHDNLkKQqHq2Cl2SP/xSffTVNy75+dTV6XpKxF/j1tlauQ9yYICdvsKq0X6fxO2Ah7fGA7JAeCdKq1NGjMKfNS4F/7fXrWWvmQ68uGRKlu1KhzXKd/iZRptsLE+LloyxBfmFuWwxtt8yzOxJSklwr4op6+/qpRxODHCF5HpAMxqK6KkEZjnSZ9lOp3hgeSXG8QMhjdiQrvfc0ygAtgUaN26KCvRwG6bbx1vM3Za8MtMuL8oyfJlWjzyHEtwW0BqQVZNjewVrjJ/iaZYZuFkhRx0avvvTGYShcfH+btRY6fgYE+11syUVfiZUfIkOS6kZhVKQMmiNWDUpf8i6DNZbnKZ9M9lYbqMVg1EUPtv4sq/K+KlLxERT0DhBffSef6piVCwHKcfavs1eTuJl0/cLxOkg+3m9kf5t/WsFXYZXbLstyOc1mG0I7NvK5X2zz0mSztyj7NLw27ZY24iq6jhdGGAzT2Eod2CW1G06t6iLYgWuhMAxI3koACr+Zm7J+eawiqf9lZKqqMXjFWelOIDYusR6OV1/MeGgVl44rCq0h4d0HGogUoFCox25FBZ8PnwjIORG6XVl0PFjHg3b1wvFiH55oYbrvSp92wIWD5Wv6GE+hYT9boU3GyUqjVRKT14l1R2KEGpm28Qs=) [최소비용으로 효율을 극대화한 비즈니스 클라우드, 더존과 상의하세요](https://adcr.naver.com/adcr?x=mdU9SqZjhkV/y8cIjFvH5P///w==kWO4JQlbBx13BqCCOeqVr/+IhdbXOnmS1ZAjzA95ymQZ0gjE+HtUD9GbQhvar+jpW4yITbQO5wFwTsSZnRiPEfBD8QOOMU/hqBYiQGICCb2CKetf2BsaK3TeiPYmJLNiFz+FVRnXv6NkQsLzAysngE7yLum/Zk2lNHDNLkKQqHq2Cl2SP/xSffTVNy75+dTV6XpKxF/j1tlauQ9yYICdvsKq0X6fxO2Ah7fGA7JAeCdKq1NGjMKfNS4F/7fXrWWvmQ68uGRKlu1KhzXKd/iZRptsLE+LloyxBfmFuWwxtt8yzOxJSklwr4op6+/qpRxODHCF5HpAMxqK6KkEZjnSZ9lOp3hgeSXG8QMhjdiQrvfc0ygAtgUaN26KCvRwG6bbx1vM3Za8MtMuL8oyfJlWjzyHEtwW0BqQVZNjewVrjJ/iaZYZuFkhRx0avvvTGYShcfH+btRY6fgYE+11syUVfiZUfIkOS6kZhVKQMmiNWDUpf8i6DNZbnKZ9M9lYbqMVg1EUPtv4sq/K+KlLxERT0DhBffSef6piVCwHKcfavs1eTuJl0/cLxOkg+3m9kf5t/WsFXYZXbLstyOc1mG0I7NvK5X2zz0mSztyj7NLw27ZY24iq6jhdGGAzT2Eod2CW1G06t6iLYgWuhMAxI3koACr+Zm7J+eawiqf9lZKqqMXjFWelOIDYusR6OV1/MeGgVl44rCq0h4d0HGogUoFCox25FBZ8PnwjIORG6XVl0PFjHg3b1wvFiH55oYbrvSp92wIWD5Wv6GE+hYT9boU3GyUqjVRKT14l1R2KEGpm28Qs=)

[저작자표시 (새창열림)](https://creativecommons.org/licenses/by/4.0/deed.ko)

#### ' > ' 카테고리의 다른 글

| [변수명 작성 규칙 및 사례 분석](https://subinto.tistory.com/251) (0) | 2025.01.21 |
| --- | --- |
| [구글 드라이브와 연계하는 방법: 상세 가이드](https://subinto.tistory.com/245) (1) | 2025.01.19 |
| [Java 비즈니스 아키텍처의 파일명 및 변수명 명명 규칙: 효율적이고 유지보수 가능한 코드를 위한 가이드](https://subinto.tistory.com/231) (0) | 2025.01.16 |
| [Spring 태그 라이브러리(Spring Tag Library)란?](https://subinto.tistory.com/227)(0) | 2025.01.15 |
| [EL(Expression Language) 태그의 종류와 사용법](https://subinto.tistory.com/226) (0) | 2025.01.15 |

Powered by [Tistory](http://www.tistory.com/), Designed by [wallel](http://wallel.com/)