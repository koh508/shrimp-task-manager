---
title: "빌드(Build)와 컴파일(Compile)의 차이점과 이해하기 쉬운 예시 코드"
source: "https://statuscode.tistory.com/4"
author:
  - "[[Status Code]]"
published: 2023-03-08
created: 2025-06-09
description: "프로그래밍에서 빌드와 컴파일은 중요한 개념 중 하나입니다. 이 두 용어는 비슷한 기능을 수행하지만 다른 의미를 갖고 있습니다. 머리글 빌드(Build)와 컴파일(Compile)의 차이 목차 빌드(Build)란? 컴파일(Compile)이란? 빌드와 컴파일의 차이 예시를 통한 이해 1. 빌드(Build)란? 빌드(Build)란 소스 코드 파일을 실행 가능한 소프트웨어 산출물로 변환하는 과정입니다. 이 과정에서는 소스 코드 파일을 컴파일하고, 링크를 거쳐 실행 파일이나 라이브러리 파일 등을 생성합니다. 즉, 빌드는 소스 코드 파일을 실행 가능한 형태로 변환하는 과정으로, 컴파일 이후 링크 과정을 포함합니다. 2. 컴파일(Compile)이란? 컴파일(Compile)은 소스 코드를 바이너리 코드로 변환하는 과정입.."
tags:
  - "clippings"
---
knowledge

[http://plckorea.kr](https://adcr.naver.com/adcr?x=s/haGgAyT+QdvDyy22GNa////w==kRvPQLbkAqzUMQ+//ZHx8S0UHbTLpimCUqtlWnyDPYdxC/TAojlhLllmswC2C0ggvSow4xiP8dVUM8XeHxewB+rLhO8C4yMXLiasOhB06CC/TlaUgDTJNkqe9Ki74hItgX727n4SOdAwpmenFDj7R1+AJtXiFM5jdtF2RfxwHGuwKucDRyvM+A8TvBzvq3BrgjqFLDynfrmlSoWSwFaH8pAMXNKOM2kEgSW6zxTytpFLx2gIvNNC0kNFxggtus7XZeN7Do1pphzbP3cB1+BRTfRLrSyphrmhPD6rmAis8HdqL/vLQLS4tc6qkx9Op8rs0peJpebb2fwQ0sGPQGMQw7/uOOaqkh8WfC/Fa1WzaC2yZKi3EcyKAZoF2MPB5HebJab3KL7KYF5hSsnwbaaNG4+1KfJLO9gqIQevpGxSJs0Cy8Rp+Hq6J9StNxzx/hyIhs/6ID6R6dlyZoXniSJd4E0gRYVRfZrcELjVUMdYupydK9BoJ8qEUEaEELZWdnO1hjFZAjzod14DK+AZlE2C1lyDRE/eCX1m6mlgjft02j8t/jrZAuJS7/3c3HALsSBaXRvT9ICPwSLn/5FjlP5U788jIQm6SqEIkkU7f/IQbL/zQBJROtQVTJA+CIfEKTx0UoDPXsOHd4C0HCFiWjCpGgzaVgRcWd4gWgnhHneNr+eGmCs2PRQZPKdhV68mllRqhJ22kQ5irQ0/6QbRRC1vwAd4HdUdS7UAngbZOQGD6vePgfOOtTBYv938rqHr6X0Q+r9pfvGtd/Q6dlliAY0ornVI5H3gPhxZj3OuxvLma+4GKWN0QyB9EmdVneX2tFBOC) 광고

[월정액유지보수 1초견적MET 산업자동화 장비판매수리보수](https://adcr.naver.com/adcr?x=s/haGgAyT+QdvDyy22GNa////w==kRvPQLbkAqzUMQ+//ZHx8S0UHbTLpimCUqtlWnyDPYdxC/TAojlhLllmswC2C0ggvSow4xiP8dVUM8XeHxewB+rLhO8C4yMXLiasOhB06CC/TlaUgDTJNkqe9Ki74hItgX727n4SOdAwpmenFDj7R1+AJtXiFM5jdtF2RfxwHGuwKucDRyvM+A8TvBzvq3BrgjqFLDynfrmlSoWSwFaH8pAMXNKOM2kEgSW6zxTytpFLx2gIvNNC0kNFxggtus7XZeN7Do1pphzbP3cB1+BRTfRLrSyphrmhPD6rmAis8HdqL/vLQLS4tc6qkx9Op8rs0peJpebb2fwQ0sGPQGMQw7/uOOaqkh8WfC/Fa1WzaC2yZKi3EcyKAZoF2MPB5HebJab3KL7KYF5hSsnwbaaNG4+1KfJLO9gqIQevpGxSJs0Cy8Rp+Hq6J9StNxzx/hyIhs/6ID6R6dlyZoXniSJd4E0gRYVRfZrcELjVUMdYupydK9BoJ8qEUEaEELZWdnO1hjFZAjzod14DK+AZlE2C1lyDRE/eCX1m6mlgjft02j8t/jrZAuJS7/3c3HALsSBaXRvT9ICPwSLn/5FjlP5U788jIQm6SqEIkkU7f/IQbL/zQBJROtQVTJA+CIfEKTx0UoDPXsOHd4C0HCFiWjCpGgzaVgRcWd4gWgnhHneNr+eGmCs2PRQZPKdhV68mllRqhJ22kQ5irQ0/6QbRRC1vwAd4HdUdS7UAngbZOQGD6vePgfOOtTBYv938rqHr6X0Q+r9pfvGtd/Q6dlliAY0ornVI5H3gPhxZj3OuxvLma+4GKWN0QyB9EmdVneX2tFBOC) [산업장비 월정액유지보수 긴급대응 월정액종합점검 단종품구매 눈깜짝1초견적조회](https://adcr.naver.com/adcr?x=s/haGgAyT+QdvDyy22GNa////w==kRvPQLbkAqzUMQ+//ZHx8S0UHbTLpimCUqtlWnyDPYdxC/TAojlhLllmswC2C0ggvSow4xiP8dVUM8XeHxewB+rLhO8C4yMXLiasOhB06CC/TlaUgDTJNkqe9Ki74hItgX727n4SOdAwpmenFDj7R1+AJtXiFM5jdtF2RfxwHGuwKucDRyvM+A8TvBzvq3BrgjqFLDynfrmlSoWSwFaH8pAMXNKOM2kEgSW6zxTytpFLx2gIvNNC0kNFxggtus7XZeN7Do1pphzbP3cB1+BRTfRLrSyphrmhPD6rmAis8HdqL/vLQLS4tc6qkx9Op8rs0peJpebb2fwQ0sGPQGMQw7/uOOaqkh8WfC/Fa1WzaC2yZKi3EcyKAZoF2MPB5HebJab3KL7KYF5hSsnwbaaNG4+1KfJLO9gqIQevpGxSJs0Cy8Rp+Hq6J9StNxzx/hyIhs/6ID6R6dlyZoXniSJd4E0gRYVRfZrcELjVUMdYupydK9BoJ8qEUEaEELZWdnO1hjFZAjzod14DK+AZlE2C1lyDRE/eCX1m6mlgjft02j8t/jrZAuJS7/3c3HALsSBaXRvT9ICPwSLn/5FjlP5U788jIQm6SqEIkkU7f/IQbL/zQBJROtQVTJA+CIfEKTx0UoDPXsOHd4C0HCFiWjCpGgzaVgRcWd4gWgnhHneNr+eGmCs2PRQZPKdhV68mllRqhJ22kQ5irQ0/6QbRRC1vwAd4HdUdS7UAngbZOQGD6vePgfOOtTBYv938rqHr6X0Q+r9pfvGtd/Q6dlliAY0ornVI5H3gPhxZj3OuxvLma+4GKWN0QyB9EmdVneX2tFBOC)

[![](https://searchad-phinf.pstatic.net/MjAxOTAyMTVfNjkg/MDAxNTUwMTg4NjExMzM4.wAhrqNfHeBVG-yzg6QHqH-07O6IqBjHn8v8AXqHAUo4g.Er3NrAsBCBBrSKnt3XiIH10Eo2INWjrSdw7qxQIGdEkg.JPEG/913430-6fc0d5c5-c21d-489d-aa57-562ac4cec1c1.jpg)](https://adcr.naver.com/adcr?x=X+V5iRGKHVbtZDlDcr8Ws////w==kRvPQLbkAqzUMQ+//ZHx8S0UHbTLpimCUqtlWnyDPYdxC/TAojlhLllmswC2C0ggvSow4xiP8dVUM8XeHxewB+rLhO8C4yMXLiasOhB06CC/TlaUgDTJNkqe9Ki74hItgX727n4SOdAwpmenFDj7R1+AJtXiFM5jdtF2RfxwHGuwKucDRyvM+A8TvBzvq3BrgjqFLDynfrmlSoWSwFaH8pAMXNKOM2kEgSW6zxTytpFLx2gIvNNC0kNFxggtus7XZeN7Do1pphzbP3cB1+BRTfRLrSyphrmhPD6rmAis8HdqL/vLQLS4tc6qkx9Op8rs0peJpebb2fwQ0sGPQGMQw7/uOOaqkh8WfC/Fa1WzaC2yZKi3EcyKAZoF2MPB5HebJab3KL7KYF5hSsnwbaaNG4+1KfJLO9gqIQevpGxSJs0Cy8Rp+Hq6J9StNxzx/hyIhs/6ID6R6dlyZoXniSJd4E0gRYVRfZrcELjVUMdYupydK9BoJ8qEUEaEELZWdnO1hjFZAjzod14DK+AZlE2C1lyDRE/eCX1m6mlgjft02j8t/jrZAuJS7/3c3HALsSBaXRvT9ICPwSLn/5FjlP5U788jIQm6SqEIkkU7f/IQbL/zQBJROtQVTJA+CIfEKTx0UoDPXsOHd4C0HCFiWjCpGgzaVgRcWd4gWgnhHneNr+eG2C3MV6tsEw/iGISvpAqCOTY1mpq5gx3pFZ2WLZa9DFLfJvnWpRoWhv6JlE3Tp30RkW798laWKGzSgztVQ9zwXUDsG5wWiv+ZB0eMGc/8IDIrwJRC8OyYgwyzhztjemvlRz9nx1dvNh1pyNizewiVK)

[http://www.anydoor.kr](https://adcr.naver.com/adcr?x=giEJVTDnjOOOqYEzTKUHXP///w==kSrZ0dzgJTbqErpomw+CLPl+wSRMCpqDDk7O3xHtmCdCOjRdHWCHfTmQ6mW0kIV0sBkL36Yn9h/270PVvi2JoZCSvLAgpYYuTD3oSb/8Dewz7jmbHhvsmpboJUJhHwku5cWumH52020VRlge2j7x7NNvnnaW0pueOYMHkdbdp10wnTWf2rXHEtk6s+qaCT0CaOLzZcZ4O+j2CwzwrkYRhi8LtrGS4lR6YU8xb5NNjSpJOfrbGLKvoKEARdpfOmVyaCZQ+VmLpc7DHxVa4fhYu8ovsP1FdhpplSVat5PfpLTlMBp8oiUKQKGGA5+2FuzkgBQwBHFkdhgjj6A2GiOvmgmYMBivfhVH8dpGfWcCfoOpCRPCSDjXtO2psYmPeLKnz5TMXCF5Cg+nQ/zoteTdBuml/NCB9P58ZAJYGEvMbT3UfoHpZnbMAmpC73/gg2d+mJ9FFVK9WXVVttjhfBXLhR8FOHE3rmuYJD66vDjPRwWIvgLYvIXt2rp6u1kwGpzYcqKC/T/maN3a5r7xpgTvudMF1BTNqMDr6DAdDOCOG0ur8inIah8gZZ1fw26rQCf8DSYxf9dTYFLkvKnt8YJfeCEW4G0wJR7Jk6vA6ZC85OcdFHCs0mI6acuYPSZBj4QcsCKh39JhF1K/R0FYdtDIDT79aemISD12Y6Aq83AjrNsxPnwxQmdwtEyBQUNmp9OoLWKdkEiIOHCUZxavKfnXL8jFtL7ho3fXNinOYI33odvuid5v1bOzhbcwAip60Jyo477ma1IG9lUjhfkiOtzmdxpEreZzyzRMCjZ5rChZ8JoALXDaS3F4IIe4KyBf1YqDD0IOv+VOAVXCcvSXnS0LOfw==) 광고

[60년 기술력 한일자동도어 자동대문 차고자동문의 모든것](https://adcr.naver.com/adcr?x=giEJVTDnjOOOqYEzTKUHXP///w==kSrZ0dzgJTbqErpomw+CLPl+wSRMCpqDDk7O3xHtmCdCOjRdHWCHfTmQ6mW0kIV0sBkL36Yn9h/270PVvi2JoZCSvLAgpYYuTD3oSb/8Dewz7jmbHhvsmpboJUJhHwku5cWumH52020VRlge2j7x7NNvnnaW0pueOYMHkdbdp10wnTWf2rXHEtk6s+qaCT0CaOLzZcZ4O+j2CwzwrkYRhi8LtrGS4lR6YU8xb5NNjSpJOfrbGLKvoKEARdpfOmVyaCZQ+VmLpc7DHxVa4fhYu8ovsP1FdhpplSVat5PfpLTlMBp8oiUKQKGGA5+2FuzkgBQwBHFkdhgjj6A2GiOvmgmYMBivfhVH8dpGfWcCfoOpCRPCSDjXtO2psYmPeLKnz5TMXCF5Cg+nQ/zoteTdBuml/NCB9P58ZAJYGEvMbT3UfoHpZnbMAmpC73/gg2d+mJ9FFVK9WXVVttjhfBXLhR8FOHE3rmuYJD66vDjPRwWIvgLYvIXt2rp6u1kwGpzYcqKC/T/maN3a5r7xpgTvudMF1BTNqMDr6DAdDOCOG0ur8inIah8gZZ1fw26rQCf8DSYxf9dTYFLkvKnt8YJfeCEW4G0wJR7Jk6vA6ZC85OcdFHCs0mI6acuYPSZBj4QcsCKh39JhF1K/R0FYdtDIDT79aemISD12Y6Aq83AjrNsxPnwxQmdwtEyBQUNmp9OoLWKdkEiIOHCUZxavKfnXL8jFtL7ho3fXNinOYI33odvuid5v1bOzhbcwAip60Jyo477ma1IG9lUjhfkiOtzmdxpEreZzyzRMCjZ5rChZ8JoALXDaS3F4IIe4KyBf1YqDD0IOv+VOAVXCcvSXnS0LOfw==) [한일자동도어의 새로운 브랜드 Vild 자동대문 차고자동문 전문 KC인증 모터 시공](https://adcr.naver.com/adcr?x=giEJVTDnjOOOqYEzTKUHXP///w==kSrZ0dzgJTbqErpomw+CLPl+wSRMCpqDDk7O3xHtmCdCOjRdHWCHfTmQ6mW0kIV0sBkL36Yn9h/270PVvi2JoZCSvLAgpYYuTD3oSb/8Dewz7jmbHhvsmpboJUJhHwku5cWumH52020VRlge2j7x7NNvnnaW0pueOYMHkdbdp10wnTWf2rXHEtk6s+qaCT0CaOLzZcZ4O+j2CwzwrkYRhi8LtrGS4lR6YU8xb5NNjSpJOfrbGLKvoKEARdpfOmVyaCZQ+VmLpc7DHxVa4fhYu8ovsP1FdhpplSVat5PfpLTlMBp8oiUKQKGGA5+2FuzkgBQwBHFkdhgjj6A2GiOvmgmYMBivfhVH8dpGfWcCfoOpCRPCSDjXtO2psYmPeLKnz5TMXCF5Cg+nQ/zoteTdBuml/NCB9P58ZAJYGEvMbT3UfoHpZnbMAmpC73/gg2d+mJ9FFVK9WXVVttjhfBXLhR8FOHE3rmuYJD66vDjPRwWIvgLYvIXt2rp6u1kwGpzYcqKC/T/maN3a5r7xpgTvudMF1BTNqMDr6DAdDOCOG0ur8inIah8gZZ1fw26rQCf8DSYxf9dTYFLkvKnt8YJfeCEW4G0wJR7Jk6vA6ZC85OcdFHCs0mI6acuYPSZBj4QcsCKh39JhF1K/R0FYdtDIDT79aemISD12Y6Aq83AjrNsxPnwxQmdwtEyBQUNmp9OoLWKdkEiIOHCUZxavKfnXL8jFtL7ho3fXNinOYI33odvuid5v1bOzhbcwAip60Jyo477ma1IG9lUjhfkiOtzmdxpEreZzyzRMCjZ5rChZ8JoALXDaS3F4IIe4KyBf1YqDD0IOv+VOAVXCcvSXnS0LOfw==)

[![](https://searchad-phinf.pstatic.net/MjAyNTAyMDdfMzIg/MDAxNzM4OTExMjQ3MDI4.GaHGS6cevngrok2s7i6IhgZHHiBqQuGkEmYBLAH5c-Mg.dPQlovp9stsr9Ez1Yc_uuZDq-fvTkdoo3QPqi53qFPYg.JPEG/250246-2b7ecf72-0a70-41f4-994a-a510ef9e44d2.jpg)](https://adcr.naver.com/adcr?x=O8sPLqS8R9UNYwl79xU1Zf///w==kSrZ0dzgJTbqErpomw+CLPl+wSRMCpqDDk7O3xHtmCdCOjRdHWCHfTmQ6mW0kIV0sBkL36Yn9h/270PVvi2JoZCSvLAgpYYuTD3oSb/8Dewz7jmbHhvsmpboJUJhHwku5cWumH52020VRlge2j7x7NNvnnaW0pueOYMHkdbdp10wnTWf2rXHEtk6s+qaCT0CaOLzZcZ4O+j2CwzwrkYRhi8LtrGS4lR6YU8xb5NNjSpJOfrbGLKvoKEARdpfOmVyaCZQ+VmLpc7DHxVa4fhYu8ovsP1FdhpplSVat5PfpLTlMBp8oiUKQKGGA5+2FuzkgBQwBHFkdhgjj6A2GiOvmgmYMBivfhVH8dpGfWcCfoOpCRPCSDjXtO2psYmPeLKnz5TMXCF5Cg+nQ/zoteTdBuml/NCB9P58ZAJYGEvMbT3UfoHpZnbMAmpC73/gg2d+mJ9FFVK9WXVVttjhfBXLhR8FOHE3rmuYJD66vDjPRwWIvgLYvIXt2rp6u1kwGpzYcqKC/T/maN3a5r7xpgTvudMF1BTNqMDr6DAdDOCOG0ur8inIah8gZZ1fw26rQCf8DSYxf9dTYFLkvKnt8YJfeCEW4G0wJR7Jk6vA6ZC85OcdFHCs0mI6acuYPSZBj4QcsCKh39JhF1K/R0FYdtDIDT79aemISD12Y6Aq83AjrNsxPnwxQmdwtEyBQUNmp9OoLPPo6KJBZN5rycsJ2Gkn57oYtHRGXI5yuUXLe/YDZcjwdDRSavmymyAgxWX0dVfuyQpBDGU8sJB5QjKg4u9UUYU/nx8AYmJfev7UW+V/ZUdUlYS4azXcNqjuyr8pwpBualE68ZtIl2ck/qrLAO9W1Cw==)

프로그래밍에서 빌드와 컴파일은 중요한 개념 중 하나입니다. 이 두 용어는 비슷한 기능을 수행하지만 다른 의미를 갖고 있습니다.

## 머리글

### 빌드(Build)와 컴파일(Compile)의 차이

## 목차

1. 빌드(Build)란?
2. 컴파일(Compile)이란?
3. 빌드와 컴파일의 차이
4. 예시를 통한 이해

## 1\. 빌드(Build)란?

빌드(Build)란 소스 코드 파일을 실행 가능한 소프트웨어 산출물로 변환하는 과정입니다. 이 과정에서는 소스 코드 파일을 컴파일하고, 링크를 거쳐 실행 파일이나 라이브러리 파일 등을 생성합니다. 즉, 빌드는 소스 코드 파일을 실행 가능한 형태로 변환하는 과정으로, 컴파일 이후 링크 과정을 포함합니다.

## 2\. 컴파일(Compile)이란?

컴파일(Compile)은 소스 코드를 바이너리 코드로 변환하는 과정입니다. 이 과정에서는 프로그래밍 언어로 작성된 소스 코드를 컴퓨터가 이해할 수 있는 기계어로 번역합니다. 즉, 컴파일은 소스 코드를 실행 가능한 바이너리 코드로 변환하는 과정입니다.

## 3\. 빌드와 컴파일의 차이

빌드와 컴파일은 비슷한 기능을 수행하지만 다른 의미를 갖고 있습니다. 빌드는 소스 코드 파일을 실행 가능한 소프트웨어 산출물로 변환하는 과정으로, 컴파일 이후 링크 과정을 포함합니다. 반면, 컴파일은 소스 코드를 바이너리 코드로 변환하는 과정입니다.  
  
따라서, 빌드는 컴파일 이후에 발생하는 과정으로, 컴파일 과정과 함께 빌드 과정을 수행하게 됩니다.

## 4\. 예시를 통한 이해

예를 들어, 자바 언어로 작성된 코드를 빌드하고 실행해보면 다음과 같습니다.

```java
// Hello.java
public class Hello {
  public static void main(String[] args) {
    System.out.println("Hello, World!");
  }
}
```

위 코드를 빌드하고 실행하는 과정은 다음과 같습니다.

1\. 소스 코드를 컴파일러에 의해 컴파일합니다.  
2\. 컴파일러가 생성한 바이트코드(.class 파일)를 실행 파일로 패키징합니다.  
3\. 실행 파일을 실행하여 결과를 출력합니다.

아래는 자바로 작성된 코드를 빌드하고 실행하는 과정을 명령어로 수행하는 예시입니다.

```bash
# 소스 코드 컴파일
$ javac Hello.java

# 패키징
$ jar cvfe Hello.jar Hello Hello.class

# 실행
$ java -jar Hello.jar
Hello, World!
```

컴파일과 빌드는 보통 개발 프로세스에서 자주 사용되는 단계입니다. 이러한 단계를 거치지 않고 소스 코드를 직접 실행하는 경우에는 컴파일러나 빌드 툴 등을 사용하지 않기 때문에 컴파일과 빌드의 차이점을 명확히 이해하는 것이 중요합니다.

#### '' 카테고리의 다른 글

| [빌드와 컴파일의 차이점과 개념 이해하기](https://statuscode.tistory.com/27) (0) | 2023.04.20 |
| --- | --- |
| [프로그래밍을 잘하는 방법: 문제 해결 능력부터 디버깅 능력까지](https://statuscode.tistory.com/10) (0) | 2023.03.21 |
| [IT 기술에서 중요한 역할을 하는 트러블슈팅 - 개념부터 해결과정까지](https://statuscode.tistory.com/7) (0) | 2023.03.08 |
| [HTTP 상태 코드에 대해](https://statuscode.tistory.com/6) (0) | 2023.03.08 |
| [CSS에서 Margin과 Padding의 차이점과 예시 코드](https://statuscode.tistory.com/5) (0) | 2023.03.08 |

---

이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.