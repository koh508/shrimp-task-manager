---
title: "필요한 건 오직 교과서 수준의 데이터뿐!! 📖 - phi-1: Textbooks Are All You Need 논문 리뷰"
source: "https://cartinoe5930.tistory.com/entry/%ED%95%84%EC%9A%94%ED%95%9C-%EA%B1%B4-%EC%98%A4%EC%A7%81-%EA%B5%90%EA%B3%BC%EC%84%9C-%EC%88%98%EC%A4%80%EC%9D%98-%EB%8D%B0%EC%9D%B4%ED%84%B0%EB%BF%90-%F0%9F%93%96-phi-1-Textbooks-Are-All-You-Need-%EB%85%BC%EB%AC%B8-%EB%A6%AC%EB%B7%B0"
author:
  - "[[Cartinoe]]"
published: 2023-06-25
created: 2025-06-01
description: "The overview of this paper 논문에서는 다른 모델보다 훨씬 작고 code를 위한 LLM인 phi-1을 소개하였다. phi-1은 1.3B Transformer model이고, 웹으로부터 textbook 퀄리티 데이터의 선택적 모음과 종합적으로 생성된 textbook을 사용하고, GPT-3.5로 훈련되었다. phi-1은 작은 규모에도 불구하고 높은 pass@1 accuracy를 달성하였다. Table of Contents 1. Introduction 2. Training details and the importance of high-quality data 3. Spikes of model capability after finetuning on CodeExercises 4. Evaluati.."
tags:
  - "clippings"
---
#### The overview of this paper

논문에서는 다른 모델보다 훨씬 작고 code를 위한 LLM인 **phi-1** 을 소개하였다. phi-1은 1.3B Transformer model이고, 웹으로부터 textbook 퀄리티 데이터의 선택적 모음과 종합적으로 생성된 textbook을 사용하고, GPT-3.5로 훈련되었다. phi-1은 작은 규모에도 불구하고 높은 pass@1 accuracy를 달성하였다.

#### Table of Contents

1\. Introduction

2\. Training details and the importance of high-quality data

3\. Spikes of model capability after finetuning on CodeExercises

4\. Evaluation on unconventional problems with LLM grading

5\. Data pruning for unbiased performance evaluation

#### 1\. Introduction

이 논문에서는 이전의 연구를 따라서 다른 축(데이터 퀄리티)과 함께 성능 개선이 얻어질 수 있다는 것을 탐구하였다. 높은 퀄리티의 데이터는 더 나은 결과를 이끈다는 것은 오랫동안 잘 알려진 사실이고, 이는 어느 정도 작은 데이터셋으로 이점을 얻거나 데이터에서 더 많은 패스를 허락해준다. 최근의 연구에 따르면 데이터의 품질을 개선하는 것은 scaling law의 형태도 바꿀 뿐만 아니라 잠재적으로 대규모 모델의 성능과 맞먹는 성능을 보여줄 수 있다고 밝혔다.

이 논문은 high-quality 데이터가 LLM의 SoTA를 개선시킬 뿐만 아니라 데이터셋 사이즈와 학습 비용을 상당히 줄일 수 있다는 주장과 함꼐 진행된다. 중요한 점은 smaller model은 적은 학습을 필요로 해서 LLM의 환경적 비용을 상당히 줄일 수 있다는 것이다. 논문에서는 LLM이 code에 대해 학습하는 것에 초점을 두었고, 평가 벤치마크로는 널리 사용되는 HumanEval을 사용하였다.

논문에서는 high-quality 데이터의 효과를 phi-1이라 부르는 1.3B 모델을 학습시킴으로써 설명하였다. phi-1은 웹 소스로부터 수집되고 필터링된 'textbook quality' 데이터에서 pre-train 시키고, 'textbook-exercise-like' 데이터에서 학습시켰다. phi-1은 다른 모델에 비해 상당히 작은 사이즈임에도 불구하고, HumanEval, MBAPP에서 최고의 pass@1 accuracy를 달성하였다. 또한 다른 모델에 비해 더욱 적은 토큰에서 학습되었음에도 불구하고, phi-1은 좋은 성능을 보여줬다. 그리고 phi-1와 phi-1-small을 비교함으로써 파라미터의 수가 중요한 역할을 한다는 가설을 입증하였다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fb2e1P2%2FbtsldPjCVaz%2F0j5n5FcKr3l2PhMt2chAP1%2Fimg.png)

표 1. 가능한 많은 모델 간의 비교. phi-1은 다른 모델에 비해 굉장히 작은 규모에서 학습했음에도 불구하고 유망한 성능을 보여줌.

#### 2\. Training details and the importance of high-quality data

논문의 제목에서 언급되어 있는 것처럼, phi-1의 주성분은 textbook quality의 training data에 의존한다. 이전에는 TheStack 같은 text data를 사용하고 다른 웹 시반 데이터를 사용하였지만, 이러한 소스는 모델에게 어떻게 계획을 세우고 추론을 하게 할 지를 가르치는 데 최적이 아니다. phi-1의 모델 아키텍처와 training method는 똑같으나, 데이터를 어떻게 curate하는지만 다르다.

기존의 code dataset은 광범위한 토픽과 사용 케이스를 커버하는 크고 다양한 corpus를 형성한다. 하지만, 이 데이터들은 코딩의 기본을 학습시키는데 not instructive 하고, 다음의 여러 결점을 겪는다:

- 많은 샘플들이 독립적이지 않음 → 데이터의 외부에 있는 다른 모듈 또는 파일에 의존함
- 전형적인 example은 의미있는 computation을 포함하지 않고 사소한 code로 구성되어 있음
- 알고리즘 논리를 포함하는 샘플은 복잡하거나 좋지 않는 문서화된함수 안에 숨겨져 있음 → 이것으로부터의 학습을 어렵게 함
- example 특정 토픽 또는 사용 케이스에 편향돼서 코딩 개념과 스킬의 unbalance한 분포를 내놓게 됌

논문에서는 LM도 사람이 좋은 textbook이라 여길 정도의 퀄리티를 가지는 training set로부터 이점을 얻어야 한다고 추측하였다: 투명하고, 독립적이고, instructive하고 밸런스 잡힌 데이터. 논문에서는 이 문제를 해결하고자 의도적으로 high-quality 데이터를 수집하고 생성하였다. 이렇게 해서 더욱 작은 모델과 적은 compute로도 code-generation task에서 SoTA를 달성할 수 있었다. phi-1의 training은 다음의 3개의 주된 데이터셋에 의존한다:

- LM 기반 분류기를 사용해서 얻어진 *filtered code-language dataset* (TheStack & StackOverflow) - 6B tokens
- GPT-3.5가 생성한 Python 교과서의 <1B token으로 구성된 *synthetic textbook dataset*
- Python exercise와 솔루션의 ~180M token으로 구성된 적은 *synthetic exercise dataset*

위의 데이터셋은 7B보다 적은 토큰으로 이루어져 있다. 논문에서는 *filtered code-language* & *synthetic textbook dataset* 의 조합을 'CodeTextbook'으로 부르고, 이것을 pre-training 페이즈에 사용해서 base model  **phi-1-base** 을 얻었다. 그 다음에 'CodeExercise' 라고 불리는 180M token을 포함하고 있는 *synthetic exercise* 데이터셋을 사용해서 **phi-1-base** 를 fine-tune 해서  **phi-1** 을 얻을 수 있었다. 'CodeExercise'의 작은 사이즈에도 불구하고 이 데이터셋에서의 fine-tuning은 상당한 개선을 보여줄 뿐만 아니라 많은 흥미로운 능력을 unlock 하였다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fby8iyu%2Fbtsk9Rwvpyi%2FB0mvRwJAXGmKmxI2D2JUG0%2Fimg.png)

그림 1. HumanEval에서 pass@1 accuracy

**2-1. FIltering of existing code datasets using a transformer-based clssifier**

논문에서는 publicly available한 TheStack과 StackOverflow의 서브셋인 Python code dataset을 사용해서 실험을 시작하였다. TheStack과 StackOverflow의 퀄리티는 GPT-4를 사용해서 annotate 하였다.

논문에서는 output embedding을 사용해서 file/sample의 퀄리티를 예측하는 Random Forest Classifier를 학습시키기 위해 annotated dataset를 사용하였다. 그리고 GPT-4를 TheStack & StackOverflow의 작은 서브셋의 퀄리티에서 annotation을 하기 위해 최소한으로 사용하였다. 이는 human effort를 피하기 위한 방법으로만 사용되었다.

**2-2. Creation of synthetic textbook-quality datasets**

code generation을 위한 high-quality 데이터셋을 생성하는데 주된 어려운 점은 example이 다양하고 비반복적이라는 것을 보장하는 것이다. 다양성은 다으므이 몇 가지 이유로 인해서 중요하다: LM이 문제 해결을 위한 서로 다른 다양한 방법에 노출되게 해주고 overfitting의 위험과 특정 패턴 또는 솔루션을 기억하는 것을 줄여주고, 모델의 일반화와 robustness를 증가시켜준다. 그래서 LM이 더욱 창의적이고 다양해지도록 유도하고, example의 퀄리티와 일관성은 유지하는 올바른 트릭을 찾을 필요가 있어졌다. 이전 연구에 영감을 받아서 다양한 데이터셋 생성을 일으키는 prompt에 무작위성을 주입하기 위한 방법을 찾고자 하였다.

**The synthetic textbook dataset.** 이 데이터셋은 관련 코드 snippet이 삽입된 high-quality의 자연어 텍스트 소스를 제공해준다. 논문에서는 추가적으로 이러한 textbook의 컨텐츠를 추론과 기본적인 알고리즘 스킬을 촉진하는 토픽을 커버하는 것으로 목표를 두었다. 여기서는 토픽과 알고리즘 스킬의 타깃 청중에게 제약을 제공함으로써 다양성을 제공해준다. 다음의 예시는 종합적으로 생성된 textbook text를 설명한다:

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fcxcrv9%2FbtslmTrYa4R%2FT5L7RS7rwjUWBD6dhFQbfk%2Fimg.png)

synthetic textbook dataset

**The CodeExercise dataset.** 각 Exercise는 완성되어야 하는 함수의 docstring이다. 이 데이터셋의 목표는 자연어 instruction에 기반해서 함수오나성 task를 수행하기 위해 모델을 align하고자 하는 것이다. 이 데이터셋은 GPT-3.5에 의해 생성되었고, 다양성을 끌어내기 위해 함수 이름에 제약을 걸었다. 이 데이터셋에 대해서는 특별하게 decontamination과 alternative 벤치마크도 수행하였다. 다음의 snippet은 종합적으로 생성된 exercise를 묘사한다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FXgeSG%2FbtslffvPnwO%2FNMiUjd8cAsV6jNAhwNm3E1%2Fimg.png)

CodeExercise dataset

**2-3. Model architecture & training**

논문에서는 MHA의 FlashAttention을 사용한 decoder-only Transformer를 사용하였다. 또한 다른 CodeGen 모델과 같이 MHA & MLP의 병렬적 레이어를 사용하였다. 또한 rotary position embedding(RoPE)를 사용하였다. tokenizer는 codegen-350M-mono와 똑같은 tokenizer를 사용하였다.

pre-training과 fine-tuning에 대해 각각의 데이터셋을 <|endofext|>를 사용해서 연결하였다. 그리고 2,048의 sequence length에서 next-token prediction loss를 사용해서 학습하였다. **phi-1-base** 는 8개의 A100 GPU에서 4일 동안 학습되었고, **phi-1** 은 똑같은 세팅에서 7시간 동안 fine-tuning 되었다.

**Pretraining.** **phi-1-base** 는 CodeTextbook 데이터셋에서 학습되었다. 작은 사이즈와 computation에도 불구하고 HumanEval에서 29%의 정확도를 달성하였다.

**Finetuning. phi-1** 은 phi-1-base를 CodeExercise dataset에 fine-tune 함으로써 얻어졌다. fine-tuning과 pre-training은 똑같은 셋업에서 진행되었다.

#### 3\. Spikes of model capability after finetuning on CodeExercises

작은 CodeExercise 데이터셋에서의 fine-tuning으로부터 HumanEval에서 큰 성능 개선을 내놓았다. 이 섹션에서는 fine-tuning을 거친 모델은 fine-tuning 데이터셋에서 feature 되지 않은 task를 수행하는데 상당한 성능 개선을 보여준다는 것을 설명한다. 이것은 phi-1의 fine-tuning 프로세스가 모델이 pre-training 중에 얻은 지식을 재조직하고 강화하는데 도움을 준다는 것을 제안한다.

**3-1. Fine-tuning improves the model's understanding**

논문에서 만들어낸 간단한 Python 함수를 사용해서 모델이 fine-tuning을 거친 instruction과 함께 더 높은 레벨의 이해와 준수를 보여준다는 것을 관찰하였다. **phi-1-base** 는 prompt에서 논리적 관계에 대해 어려움을 겪었는데, **phi-1** 은 question을 해석하고, answer를 올바르게 생성하였다. 아래의 예시에서 350M **phi-1-small** 도 솔루션이 틀리긴 했지만, 어느 정도의 문제 이해를 보여줬다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FSzrQI%2Fbtsk9Rce5dW%2F8CYzVnKJPkpk174bk0ypR1%2Fimg.png)

**3-2. Finetuning improves the model's ability to use external libraries**

논문에서는 CodeExercise에서의 fine-tuning은 예측치 못하게 모델의 외부 라이브러리 사용 능력을 개선시켰다. exercise에 이 데이터를 포함시키지 않았음에도 말이다! 이것은 phi-1의 fine-tuning이 타깃으로 삼는 task를 개선시킬 뿐만 아니라 pre-training으로부터 distill하기 위한 비관련 task도 가능하게 만들었다.

**PyGame Examples.** 논문에서는 PyGame으로 공을 움직이는 코드를 생성하도록 모델에게 물어봤다. 아래의 코드를 살펴보면 phi-1은 PyGame 함수를 올바르게 적용하였다. phi-1-base & phi-1-small은 구문적으로는 맞으나, 의미상으로는 관련이 없었다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FD6YhJ%2FbtslatoCqKj%2FmpPol3TJ9vbVOI7WD0n2a0%2Fimg.png)

PyGame example

**TKinter Example.** 두 번째 예시로는 TKinter이다. 사용자가 버튼을 클릭함에 따라 textfield를 업데이트하도록 물어봤다. 결과를 살펴보면 3개의 모델의 코드는 prompt 이해의 큰 갭을 보여준다. **phi-1-base** 와  **phi-1-small** 은 알맞은 TKinter API를 사용하는데 실패하고, 의미없은 함수 호출을 만들어냈다. 반대로  **phi-1** 은 GUI와 모든 함수를 알맞게 구현하였다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FCIm8S%2FbtslcCSnafQ%2FkwWwbUilEsSe0jmUxqtVD0%2Fimg.png)

TKinter example

**Chat model Example.** **phi-1** 은  **phi-1-base** 보다 더 나은 chat 능력을 보여줬다. chat data는 전적으로 pre-training에 있고, fine-tuning에는 없었음에도 불구하고 말이다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FSoigP%2Fbtslhcr5Ly5%2FVWcPuKKQllhbsSDMFRu061%2Fimg.png)

chat mode example

#### 4\. Evaluation on unconventional problems with LLM grading

HumanEval에서 phi-1의 놀라울 정도로 좋은 성능에 대한 잠재적인 걱정은 CodeExercise dataset의 contamination에 기인하는 memorization이 있을 수도 있다. 논문에서는 전통적이지 않은 방식으로 고안된 새로운 평가와 함께 이러한 걱정을 해결하였다.

real-world code base 또는 coding exercise에 잘 나타나지 않는 문제를 디자인하기 위한 instruction과 함께 HumanEval과 똑같은 포맷의 50개의 새로운 문제를 생성하였다.

LM을 coding task에서 평가하는데 한 가지 어려운 점은 모델의 output이 종종 binary 하다는 것이다. 하지만 코드가 test를 통과하는지 그렇지 않은지는 모델 성능의 뉘앙스를 캡처하지 못한다. 거의 알맞은 코드이지만, 사소한 에러를 가지는 코드를 생성하거나, 코드는 완전히 틀렸지만, 우연히도 몇 개의 테스트를 통과하기도 하기 때문이다. 그래서 모델의 코딩 스킬을 더욱 정보적 방식으로 평가하는 것은 coding 인터뷰에서 output과 알맞은 솔루션을 비교하고 예측 논리와 얼마나 잘 매치하는지에 기반해서 평가하는 것이다.

논문에서는 후보 솔루션의 평가를 위해 GPT-4를 사용해서 솔루션에 등급을 매기는 방식을 채택하였다. 여기에는 다음의 2가지 장점이 있다.

1. GPT-4를 grader로 사용해서 student model의 코딩 능력의 더욱 fine-grained & meaningul signal을 얻을 수 있었음
2. test에 대한 필요를 제거

prompt는 LLM이 student의 솔루션을 short verbal evaluation에서 평가하도록 instruct 하였다.

표 2는 phi-1과 다른 모델의 결과를 보여준다. 논문의 새로운 grading method도 HumanEval과 똑같은 랭킹을 보여주는 것을 알 수 있다(표 1 참고). 이러한 결과는 phi-1 성능의 유효성의 신뢰를 크게 증가시킨다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FbjdiGk%2Fbtslb6lFdcT%2FuPO4wAplfuz7V2KzLLfUKK%2Fimg.png)

표 2. 50개의 새로운 비전통적 코딩 문제에서 LLM에 의해 매겨진 understanding score

#### 5\. Data pruning for unbiased performance evaluation

CodeExercise에서의 학습은 HumanEval 벤치마크에서 모델의 성능에 상당한 향상을 이끈다. 이러한 성능 향상을 조사하기 위해 HumanEval의 파일과 유사한 파일을 제거함으로써 CodeExercise를 prune하는 것을 제안하였다. 그 다음에 pruned data에서 모델을 재학습시켰음에도 HumanEval에서 강력한 성능을 보여줬다.

논문에서는 이러한 data pruning 실험은 성능을 평가하기 위한 올바른 방법으로 믿는다. 또한 기존 contamination 실험을 통해 CodeExercise가 HumanEval에 의해 contaminate되지 않는다는 것을 보여준다.

**5-1. N-gram overlap**

N-gram은 공유된 n-word sequence에 기반해서 text segment의 유사도를 측정한다. 논문에서는 각 humaneval question과 각 exercise의 docstring 간에 n-gram overlap을 계산하였다. 그 결과 최소 하나의 데이터셋 entry에서 4개의 humaneval question에서 13-gram overlap을 발견하였다. 논문의 n-gram ovelap 분석은 phi-1 데이터셋이 HumanEval과 최소한의 letter-by-letter overlap을 가진다는 것을 보여준다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2FdeBDj2%2FbtslaeecuxE%2F75zmCCuK0iKG8u1aMHCFs1%2Fimg.png)

n-gram overlap analysis

**5-2. Embedding and syntax-based similarity analysis**

앞서 봤던 것처럼 n-gram 분석은 HumanEval과 CodeExercise 간의 유사 code snipper을 찾는데 충분히 개선되지 않았다. 그래서 그 대신에 임베딩과 syntax-based distance의 조합을 사용하였다. embedding distance 계산을 위해 논문에서는 code snippet 간에 **L2 distance** 를 계산하였다. embedding distance는 code 쌍을 갭처하는데 성공적이었다. syntac-based distance를 위해서 논문에서는 주어진 두 code snippet의 **Abstract syntax trees(AST)** 간의 edit distance를 계산하였다. AST distance는 코드 쌍 간의 오버랩을 성공적으로 판별해냈다. CodeExercise의 pruning을 위해 embedding distance를 위한 기준점을 고정하고, AST distance에 대해 여러 match rate를 테스트 하였다.

표 3은 pruned dataset에서 재학습된 phi-1의 성능과 full CodeExercise에서 학습된 기존의 phi-1, StarCoder-prompted를 비교해서 요약하였다. 논문에서는 HumanEval problem을 기존 CodeExercise 데이터셋 내부의 최소 하나의 close match를 가지는지 그렇지 않은지에 기반해서 2개의 서브셋(similar & non-similar)으로 나눴다. 그 다음에 HumanEval의 각 서브셋에서 모델의 정확도를 기록하였다. 데이터셋을 크게 prune 한 후에도, phi-1은 아직 StarCoder-Prompted를 큰 마진으로 능가하였다. 이것은 phi-1의 성능 향상이 data contamination 때문이 아니라는 것을 입증한다.

![](https://img1.daumcdn.net/thumb/R1280x0/?scode=mtistory2&fname=https%3A%2F%2Fblog.kakaocdn.net%2Fdn%2Fctu2Yq%2FbtslbwZcALe%2FkQnH88ZkLDUp8AKDW7ddKk%2Fimg.png)

표 3. 서로 다른 모델에 의해 올바르게 해결된 similar vs non-similar HumanEval problems의 퍼센테이지

출처

[https://arxiv.org/abs/2306.11644](https://arxiv.org/abs/2306.11644)

[

Textbooks Are All You Need

We introduce phi-1, a new large language model for code, with significantly smaller size than competing models: phi-1 is a Transformer-based model with 1.3B parameters, trained for 4 days on 8 A100s, using a selection of \`\`textbook quality" data from the w

arxiv.org

](https://arxiv.org/abs/2306.11644)

#### ' > ' 카테고리의 다른 글

| [GPT-4도 잘 못한 API 호출을 한다고?!? - Gorilla🦍: Large Language Model Connected with Massive APIs 논문 리뷰](https://cartinoe5930.tistory.com/entry/GPT-4%EB%8F%84-%EC%9E%98-%EB%AA%BB%ED%95%9C-API-%ED%98%B8%EC%B6%9C%EC%9D%84-%ED%95%9C%EB%8B%A4%EA%B3%A0-Gorilla%F0%9F%A6%8D-Large-Language-Model-Connected-with-Massive-APIs-%EB%85%BC%EB%AC%B8-%EB%A6%AC%EB%B7%B0) (0) | 2023.06.27 |
| --- | --- |
| [Open-domain instruction의 효과 🪄 - WizardLM: Empowering Large Language Models to Follow Complex Instructions 논문 리뷰](https://cartinoe5930.tistory.com/entry/Open-domain-instruction%EC%9D%98-%ED%9A%A8%EA%B3%BC-%F0%9F%AA%84-WizardLM-Empowering-Large-Language-Models-to-Follow-Complex-Instructions-%EB%85%BC%EB%AC%B8-%EB%A6%AC%EB%B7%B0) (2) | 2023.06.26 |
| [LM이 도구를 사용하게 된다면? 🔬: Large Language Models as Tool Makers 논문 리뷰](https://cartinoe5930.tistory.com/entry/LM%EC%9D%B4-%EB%8F%84%EA%B5%AC%EB%A5%BC-%EC%82%AC%EC%9A%A9%ED%95%98%EA%B2%8C-%EB%90%9C%EB%8B%A4%EB%A9%B4-%F0%9F%94%AC-Large-Language-Models-as-Tool-Makers-%EB%85%BC%EB%AC%B8-%EB%A6%AC%EB%B7%B0) (0) | 2023.06.24 |
| [🐬Orca: Progressive Learning from Complex Explanation Traces of GPT-4 논문 리뷰](https://cartinoe5930.tistory.com/entry/%F0%9F%90%ACOrca-Progressive-Learning-from-Complex-Explanation-Traces-of-GPT-4-%EB%85%BC%EB%AC%B8-%EB%A6%AC%EB%B7%B0) (0) | 2023.06.23 |
| [KD에 살짝의 변화를 줘보자!! 😜 - Knowledge Distillation of Large Language Models 논문 리뷰](https://cartinoe5930.tistory.com/entry/KD%EC%97%90-%EC%82%B4%EC%A7%9D%EC%9D%98-%EB%B3%80%ED%99%94%EB%A5%BC-%EC%A4%98%EB%B3%B4%EC%9E%90-%F0%9F%98%9C-Knowledge-Distillation-of-Large-Language-Models-%EB%85%BC%EB%AC%B8-%EB%A6%AC%EB%B7%B0) (0) | 2023.06.22 |

[Cartinoe's paper review](https://cartinoe5930.tistory.com/) [Welcome! I'm a student studying about deep learning(NLP) 😉 The goal of my study is to develop a competent LLM helping people!](https://cartinoe5930.tistory.com/)

필요한 건 오직 교과서 수준의 데이터뿐!! 📖 - phi-1: Textbooks Are All You Need 논문 리뷰

[상단으로](https://cartinoe5930.tistory.com/entry/#hELLO)