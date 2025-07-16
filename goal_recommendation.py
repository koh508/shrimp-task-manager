#!/usr/bin/env python3
"""
AI 기반 학습 목표 추천 시스템
"""
from typing import Dict, List
from datetime import datetime
import numpy as np

class GoalRecommendationSystem:
    def __init__(self):
        self.skill_categories = {
            'programming': ['python', 'javascript', 'java', 'go', 'rust'],
            'ai_ml': ['machine_learning', 'deep_learning', 'nlp', 'computer_vision'],
            'devops': ['docker', 'kubernetes', 'aws', 'ci_cd', 'monitoring'],
            'web_development': ['react', 'vue', 'angular', 'node_js', 'django']
        }
        self.difficulty_levels = {
            'beginner': 1,
            'intermediate': 2,
            'advanced': 3,
            'expert': 4
        }
    def analyze_user_profile(self, completed_goals: List[Dict]) -> Dict:
        profile = {
            'skill_levels': {},
            'preferred_categories': {},
            'learning_velocity': 0,
            'strengths': [],
            'growth_areas': []
        }
        if not completed_goals:
            return profile
        for goal in completed_goals:
            category = goal.get('category', 'unknown')
            profile['preferred_categories'][category] = profile['preferred_categories'].get(category, 0) + 1
        total_days = sum(goal.get('completion_days', 30) for goal in completed_goals)
        profile['learning_velocity'] = len(completed_goals) / (total_days / 30) if total_days > 0 else 0
        for category, skills in self.skill_categories.items():
            completed_skills = [goal.get('skills_gained', []) for goal in completed_goals if goal.get('category') == category]
            completed_skills = [skill for sublist in completed_skills for skill in sublist]
            profile['skill_levels'][category] = len(set(completed_skills))
        return profile
    def generate_recommendations(self, user_profile: Dict, current_goals: List[Dict]) -> List[Dict]:
        recommendations = []
        for category, count in user_profile['preferred_categories'].items():
            if count > 0:
                recommendations.extend(self.get_category_recommendations(category, user_profile))
        recommendations.extend(self.get_skill_gap_recommendations(user_profile))
        recommendations.extend(self.get_trending_recommendations())
        recommendations = self.adjust_difficulty(recommendations, user_profile)
        recommendations = self.rank_recommendations(recommendations, user_profile)
        return recommendations[:5]
    def get_category_recommendations(self, category: str, user_profile: Dict) -> List[Dict]:
        current_level = user_profile['skill_levels'].get(category, 0)
        recommendations = []
        if category == 'programming':
            if current_level < 3:
                recommendations.append({'title': '파이썬 심화', 'category': 'programming', 'priority': 'high', 'estimated_days': 20, 'skills': ['python'], 'difficulty': 'intermediate'})
        return recommendations
    def get_skill_gap_recommendations(self, user_profile: Dict) -> List[Dict]:
        recommendations = []
        skill_levels = user_profile['skill_levels']
        min_level = min(skill_levels.values()) if skill_levels else 0
        for category, level in skill_levels.items():
            if level == min_level:
                recommendations.append({
                    'title': f'{category.title()} 기초 강화',
                    'description': f'{category} 영역 기초 실력 향상',
                    'category': category,
                    'priority': 'medium',
                    'estimated_days': 20,
                    'skills': self.skill_categories.get(category, [])[:3],
                    'difficulty': 'beginner'
                })
        return recommendations
    def get_trending_recommendations(self) -> List[Dict]:
        trending_topics = [
            {'title': 'AI 에이전트 워크플로우 구축', 'description': '자율적인 AI 에이전트 시스템 개발', 'category': 'ai_ml', 'priority': 'high', 'estimated_days': 60, 'skills': ['agent_frameworks', 'workflow_automation', 'llm_integration'], 'difficulty': 'advanced'},
            {'title': '클라우드 네이티브 애플리케이션', 'description': 'Kubernetes와 마이크로서비스 아키텍처', 'category': 'devops', 'priority': 'medium', 'estimated_days': 40, 'skills': ['kubernetes', 'microservices', 'service_mesh'], 'difficulty': 'intermediate'}
        ]
        return trending_topics
    def adjust_difficulty(self, recommendations: List[Dict], user_profile: Dict) -> List[Dict]:
        learning_velocity = user_profile.get('learning_velocity', 1)
        for rec in recommendations:
            if learning_velocity > 1.5:
                rec['estimated_days'] = int(rec['estimated_days'] * 0.8)
            elif learning_velocity < 0.7:
                rec['estimated_days'] = int(rec['estimated_days'] * 1.2)
        return recommendations
    def rank_recommendations(self, recommendations: List[Dict], user_profile: Dict) -> List[Dict]:
        def calculate_score(rec):
            score = 0
            category_preference = user_profile['preferred_categories'].get(rec['category'], 0)
            score += category_preference * 0.3
            priority_weights = {'high': 0.3, 'medium': 0.2, 'low': 0.1}
            score += priority_weights.get(rec['priority'], 0)
            velocity = user_profile.get('learning_velocity', 1)
            if velocity > 1:
                score += 0.2 if rec['difficulty'] == 'advanced' else 0.1
            return score
        recommendations.sort(key=calculate_score, reverse=True)
        return recommendations
