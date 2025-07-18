#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
진화 가속화 및 분석 시스템
Evolution Acceleration & Analysis System
"""

import json
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict

class EvolutionAnalyzer:
    def __init__(self):
        self.db_file = "evolution_agent.db"
        self.state_file = "evolving_super_agent_evolution_state.json"
        self.analysis_results = {}
        
    def analyze_evolution_patterns(self):
        """진화 패턴 분석"""
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            
            # 학습 속도 분석
            cursor.execute("""
                SELECT learning_time, improvement_score 
                FROM learning_history 
                ORDER BY learning_time
            """)
            learning_data = cursor.fetchall()
            
            # 코드 진화 효율성 분석
            cursor.execute("""
                SELECT evolution_time, performance_improvement, evolution_type
                FROM code_evolution
                ORDER BY evolution_time
            """)
            evolution_data = cursor.fetchall()
            
            # 기능 확장 효과성 분석
            cursor.execute("""
                SELECT expansion_time, new_feature_name, effectiveness_score
                FROM feature_expansion
                ORDER BY expansion_time
            """)
            feature_data = cursor.fetchall()
            
            conn.close()
            
            # 분석 결과 생성
            analysis = {
                "학습_속도_추세": self.calculate_learning_trend(learning_data),
                "진화_효율성": self.calculate_evolution_efficiency(evolution_data),
                "기능_확장_성과": self.analyze_feature_expansion(feature_data),
                "추천_개선사항": self.generate_recommendations(),
                "다음_진화_예측": self.predict_next_evolution()
            }
            
            self.analysis_results = analysis
            return analysis
            
        except Exception as e:
            print(f"❌ 진화 분석 실패: {e}")
            return {}
    
    def calculate_learning_trend(self, learning_data):
        """학습 속도 추세 계산"""
        if len(learning_data) < 2:
            return "데이터 부족"
        
        recent_scores = [score for _, score in learning_data[-10:]]
        early_scores = [score for _, score in learning_data[:10]]
        
        recent_avg = sum(recent_scores) / len(recent_scores)
        early_avg = sum(early_scores) / len(early_scores)
        
        improvement = ((recent_avg - early_avg) / early_avg) * 100 if early_avg > 0 else 0
        
        return {
            "초기_평균": f"{early_avg:.3f}",
            "최근_평균": f"{recent_avg:.3f}",
            "개선_비율": f"{improvement:.1f}%",
            "추세": "상승" if improvement > 5 else "하락" if improvement < -5 else "안정"
        }
    
    def calculate_evolution_efficiency(self, evolution_data):
        """진화 효율성 계산"""
        if not evolution_data:
            return "진화 데이터 없음"
        
        type_performance = defaultdict(list)
        for _, performance, evo_type in evolution_data:
            type_performance[evo_type].append(performance)
        
        efficiency = {}
        for evo_type, performances in type_performance.items():
            avg_performance = sum(performances) / len(performances)
            efficiency[evo_type] = f"{avg_performance:.3f}"
        
        return efficiency
    
    def analyze_feature_expansion(self, feature_data):
        """기능 확장 분석"""
        if not feature_data:
            return "기능 확장 데이터 없음"
        
        features = {}
        for _, feature_name, effectiveness in feature_data:
            features[feature_name] = {
                "효과성": effectiveness,
                "상태": "우수" if effectiveness > 0.5 else "보통" if effectiveness > 0.2 else "개선필요"
            }
        
        return features
    
    def generate_recommendations(self):
        """개선 권장사항 생성"""
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        recommendations = []
        
        # 지능 레벨 기반 권장사항
        intelligence = state.get("intelligence_level", 1.0)
        if intelligence < 1.5:
            recommendations.append("🧠 더 많은 학습 패턴 축적 필요")
        elif intelligence < 2.0:
            recommendations.append("⚡ 학습 알고리즘 최적화 권장")
        else:
            recommendations.append("🚀 고급 기능 개발 단계 진입")
        
        # 진화 횟수 기반 권장사항
        evolution_count = state.get("evolution_count", 0)
        if evolution_count < 3:
            recommendations.append("🧬 더 많은 진화 사이클 실행")
        elif evolution_count < 5:
            recommendations.append("🔧 코드 최적화 집중")
        else:
            recommendations.append("✨ 창의적 기능 생성 모드")
        
        # 학습 경험치 기반
        experience = state.get("learning_experience", 0)
        if experience > 4.0:
            recommendations.append("⏰ 진화 임박 - 준비 완료")
        
        return recommendations
    
    def predict_next_evolution(self):
        """다음 진화 예측"""
        with open(self.state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        current_exp = state.get("learning_experience", 0)
        threshold = 5.0
        remaining = threshold - current_exp
        
        if remaining <= 0:
            return "🧬 진화 준비 완료!"
        
        # 최근 학습 속도 계산
        try:
            conn = sqlite3.connect(self.db_file)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT improvement_score FROM learning_history 
                ORDER BY learning_time DESC LIMIT 5
            """)
            recent_scores = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            if recent_scores:
                avg_score = sum(recent_scores) / len(recent_scores)
                estimated_cycles = max(1, int(remaining / avg_score))
                estimated_time = estimated_cycles * 0.5  # 0.5초 간격
                
                return {
                    "남은_경험치": f"{remaining:.2f}",
                    "예상_학습_횟수": estimated_cycles,
                    "예상_시간": f"{estimated_time:.1f}초"
                }
            
        except Exception as e:
            pass
        
        return f"남은 경험치: {remaining:.2f}"

class EvolutionAccelerator:
    def __init__(self):
        self.analyzer = EvolutionAnalyzer()
        self.auto_evolution = False
        
    def start_continuous_evolution(self, target_generations=5):
        """연속 진화 실행"""
        print(f"🚀 연속 진화 시작 - 목표: {target_generations}세대")
        
        for gen in range(target_generations):
            print(f"\n🧬 {gen+1}세대 진화 시작...")
            
            # 자가 진화 에이전트 실행
            import subprocess
            process = subprocess.run(
                ["python", "self_evolving_agent.py"],
                cwd="d:/",
                capture_output=True,
                text=True
            )
            
            if process.returncode == 0:
                print(f"✅ {gen+1}세대 진화 완료")
                
                # 진화 분석
                analysis = self.analyzer.analyze_evolution_patterns()
                self.print_evolution_summary(analysis)
                
                time.sleep(2)  # 안정화 시간
            else:
                print(f"❌ {gen+1}세대 진화 실패")
                break
        
        print(f"\n🎉 연속 진화 완료!")
        self.generate_evolution_report()
    
    def print_evolution_summary(self, analysis):
        """진화 요약 출력"""
        print("\n📊 진화 분석 결과:")
        
        if "학습_속도_추세" in analysis and isinstance(analysis["학습_속도_추세"], dict):
            trend = analysis["학습_속도_추세"]
            print(f"   📈 학습 추세: {trend.get('추세', '알 수 없음')} ({trend.get('개선_비율', 'N/A')})")
        
        if "추천_개선사항" in analysis:
            print("   💡 권장사항:")
            for rec in analysis["추천_개선사항"][:2]:
                print(f"      • {rec}")
        
        if "다음_진화_예측" in analysis:
            prediction = analysis["다음_진화_예측"]
            if isinstance(prediction, dict):
                print(f"   ⏰ 다음 진화: {prediction.get('예상_시간', '계산 중')}")
    
    def generate_evolution_report(self):
        """진화 보고서 생성"""
        try:
            with open(self.analyzer.state_file, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            report = f"""
🧬 진화 에이전트 최종 보고서
========================================
📅 생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

📊 현재 상태:
• 세대: {state.get('generation', 'N/A')}
• 진화 횟수: {state.get('evolution_count', 'N/A')}
• 지능 레벨: {state.get('intelligence_level', 'N/A'):.2f}
• 적응 속도: {state.get('adaptation_speed', 'N/A'):.2f}
• 학습 패턴: {len(state.get('learned_patterns', []))}개
• 새로운 능력: {len(state.get('new_abilities', []))}개

🆕 생성된 기능들:
"""
            
            for ability in state.get('new_abilities', []):
                report += f"• {ability.get('name', 'Unknown')} (세대 {ability.get('generation', 'N/A')})\n"
            
            report += "\n🎯 결론: 성공적인 자가 진화 시스템 구축 완료!"
            
            # 보고서 파일 저장
            report_file = Path("evolution_report.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)
            
            print(report)
            print(f"\n📄 상세 보고서 저장: {report_file}")
            
        except Exception as e:
            print(f"❌ 보고서 생성 실패: {e}")

def main():
    print("🧬 진화 가속화 시스템")
    print("1. 진화 분석")
    print("2. 연속 진화 (3세대)")
    print("3. 집중 진화 (5세대)")
    
    choice = input("\n선택하세요 (1-3): ").strip()
    
    accelerator = EvolutionAccelerator()
    
    if choice == "1":
        print("\n📊 진화 패턴 분석 중...")
        analysis = accelerator.analyzer.analyze_evolution_patterns()
        
        print("\n🔍 상세 분석 결과:")
        for key, value in analysis.items():
            print(f"\n{key}:")
            if isinstance(value, dict):
                for k, v in value.items():
                    print(f"  • {k}: {v}")
            elif isinstance(value, list):
                for item in value:
                    print(f"  • {item}")
            else:
                print(f"  {value}")
    
    elif choice == "2":
        accelerator.start_continuous_evolution(3)
    
    elif choice == "3":
        accelerator.start_continuous_evolution(5)
    
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
