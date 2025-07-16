#!/usr/bin/env python3
"""
지능형 학습 목표 추천 시스템
"""
import json
from datetime import datetime
from typing import Any, Dict, List

from llm_agent import LLMAgent


class IntelligentGoalRecommendation:
    """지능형 학습 목표 추천 시스템"""

    def __init__(self, llm_agent: LLMAgent):
        self.llm_agent = llm_agent
        self.user_history = []
        self.skill_tree = self.build_skill_tree()

    def build_skill_tree(self) -> Dict[str, Any]:
        """스킬 트리 구축"""
        return {
            "programming": {
                "python": {
                    "beginner": ["basic_syntax", "data_types", "control_flow"],
                    "intermediate": ["oop", "file_handling", "error_handling"],
                    "advanced": ["decorators", "metaclasses", "async_programming"],
                },
                "web_development": {
                    "frontend": ["html", "css", "javascript", "react"],
                    "backend": ["flask", "django", "fastapi", "databases"],
                },
            },
            "ai_ml": {
                "machine_learning": ["sklearn", "pandas", "numpy", "matplotlib"],
                "deep_learning": ["tensorflow", "pytorch", "keras", "transformers"],
                "nlp": ["spacy", "nltk", "transformers", "bert"],
            },
            "devops": {
                "containerization": ["docker", "kubernetes", "docker_compose"],
                "ci_cd": ["github_actions", "jenkins", "gitlab_ci"],
                "monitoring": ["prometheus", "grafana", "elk_stack"],
            },
        }

    async def recommend_goals(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """개인화된 학습 목표 추천"""
        current_skills = user_profile.get("skills", [])
        interests = user_profile.get("interests", [])

        recommendations = []

        # 1. 스킬 갭 기반 추천
        gap_recommendations = self.analyze_skill_gaps(current_skills)
        recommendations.extend(gap_recommendations)

        # 2. 트렌드 기반 추천
        trend_recommendations = await self.get_trending_skills()
        recommendations.extend(trend_recommendations)

        # 3. 커리어 패스 기반 추천
        career_recommendations = self.get_career_path_recommendations(user_profile)
        recommendations.extend(career_recommendations)

        # 4. LLM 기반 개인화 추천
        if self.llm_agent.llm_available:
            llm_recommendations = await self.get_llm_recommendations(user_profile)
            recommendations.extend(llm_recommendations)

        # 중복 제거 및 순위 매기기
        unique_recommendations = self.deduplicate_and_rank(recommendations, user_profile)

        return unique_recommendations[:5]  # 상위 5개 추천

    def analyze_skill_gaps(self, current_skills: List[str]) -> List[Dict[str, Any]]:
        """스킬 갭 분석"""
        recommendations = []

        for category, subcategories in self.skill_tree.items():
            for subcategory, levels in subcategories.items():
                for level, skills in levels.items():
                    missing_skills = [skill for skill in skills if skill not in current_skills]

                    if missing_skills:
                        recommendations.append(
                            {
                                "title": f"{subcategory.title()} {level.title()} 스킬 습득",
                                "description": f'{", ".join(missing_skills)} 기술 학습',
                                "category": category,
                                "subcategory": subcategory,
                                "level": level,
                                "skills": missing_skills,
                                "priority": "high" if level == "beginner" else "medium",
                                "estimated_days": 30 if level == "beginner" else 45,
                                "source": "skill_gap_analysis",
                            }
                        )

        return recommendations

    async def get_trending_skills(self) -> List[Dict[str, Any]]:
        """트렌드 기반 스킬 추천"""
        trending_skills = [
            {
                "title": "AI 에이전트 개발",
                "description": "LangChain, OpenAI API를 활용한 AI 에이전트 구축",
                "category": "ai_ml",
                "skills": ["langchain", "openai_api", "vector_databases"],
                "priority": "high",
                "estimated_days": 60,
                "source": "trending",
            },
            {
                "title": "클라우드 네이티브 개발",
                "description": "Kubernetes, Serverless 기반 애플리케이션 개발",
                "category": "devops",
                "skills": ["kubernetes", "serverless", "microservices"],
                "priority": "medium",
                "estimated_days": 45,
                "source": "trending",
            },
        ]

        return trending_skills

    def get_career_path_recommendations(
        self, user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """커리어 패스 기반 추천"""
        career_goal = user_profile.get("career_goal", "full_stack_developer")

        career_paths = {
            "full_stack_developer": [
                "React/Vue.js 프론트엔드",
                "Node.js/Python 백엔드",
                "Docker/Kubernetes 배포",
                "SQL/NoSQL 데이터베이스",
            ],
            "ai_engineer": ["Machine Learning 기초", "Deep Learning 심화", "MLOps 파이프라인", "AI 모델 배포"],
            "devops_engineer": ["인프라 자동화", "CI/CD 파이프라인", "모니터링 시스템", "클라우드 보안"],
        }

        recommendations = []
        skills = career_paths.get(career_goal, [])

        for skill in skills:
            recommendations.append(
                {
                    "title": f"{skill} 마스터",
                    "description": f"{career_goal} 커리어를 위한 {skill} 전문성 개발",
                    "category": "career_development",
                    "skills": [skill.lower().replace(" ", "_")],
                    "priority": "high",
                    "estimated_days": 30,
                    "source": "career_path",
                }
            )

        return recommendations

    async def get_llm_recommendations(self, user_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
        """LLM 기반 개인화 추천"""
        if not self.llm_agent.llm_available:
            return []

        try:
            prompt = f"""
            사용자 프로필을 기반으로 개인화된 학습 목표를 추천해주세요:

            현재 스킬: {user_profile.get('skills', [])}
            관심 분야: {user_profile.get('interests', [])}
            커리어 목표: {user_profile.get('career_goal', 'not_specified')}
            선호 난이도: {user_profile.get('difficulty', 'intermediate')}

            JSON 형식으로 5개의 학습 목표를 추천해주세요.
            각 목표는 다음 형식을 따라주세요:
            {{
                "title": "목표 제목",
                "description": "상세 설명",
                "category": "카테고리",
                "skills": ["스킬1", "스킬2"],
                "priority": "high/medium/low",
                "estimated_days": 30
            }}
            """

            response = await self.llm_agent.llm.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "당신은 개인화된 학습 경로 전문가입니다."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=1000,
                temperature=0.7,
            )

            llm_recommendations = json.loads(response.choices[0].message.content)
            for rec in llm_recommendations:
                rec["source"] = "llm_personalized"

            return llm_recommendations

        except Exception as e:
            print(f"LLM 추천 실패: {e}")
            return []

    def deduplicate_and_rank(
        self, recommendations: List[Dict[str, Any]], user_profile: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """중복 제거 및 순위 매기기"""
        unique_recs = {rec["title"]: rec for rec in recommendations}

        ranked_recs = list(unique_recs.values())
        ranked_recs.sort(
            key=lambda x: self.calculate_recommendation_score(x, user_profile), reverse=True
        )

        return ranked_recs

    def calculate_recommendation_score(
        self, recommendation: Dict[str, Any], user_profile: Dict[str, Any]
    ) -> float:
        """추천 점수 계산"""
        score = 0
        priority_weights = {"high": 0.3, "medium": 0.2, "low": 0.1}
        score += priority_weights.get(recommendation.get("priority", "medium"), 0.2)

        if recommendation.get("category") in user_profile.get("interests", []):
            score += 0.3

        overlap = len(set(user_profile.get("skills", [])) & set(recommendation.get("skills", [])))
        score += overlap * 0.1

        source_weights = {
            "llm_personalized": 0.4,
            "skill_gap_analysis": 0.3,
            "trending": 0.2,
            "career_path": 0.25,
        }
        score += source_weights.get(recommendation.get("source", "default"), 0.1)

        return score
