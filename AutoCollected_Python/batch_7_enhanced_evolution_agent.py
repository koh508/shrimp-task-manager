#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
강화된 진화 에이전트 - MCP 연동 및 고급 기능
Enhanced Evolution Agent with MCP Integration
"""

import json
import time
import sqlite3
import subprocess
import asyncio
import os
from datetime import datetime
from pathlib import Path

class EnhancedEvolutionAgent:
    def __init__(self):
        self.db_file = "evolution_agent.db"
        self.state_file = "evolving_super_agent_evolution_state.json"
        self.mcp_available = False
        self.shrimp_port = 8080
        
        # 진화 전략 설정
        self.evolution_strategies = [
            "learning_optimization",    # 학습 최적화
            "code_refactoring",        # 코드 리팩토링
            "feature_enhancement",     # 기능 향상
            "performance_tuning",      # 성능 튜닝
            "intelligence_boost"       # 지능 증강
        ]
        
    def check_mcp_server(self):
        """MCP 서버 상태 확인"""
        try:
            import requests
            response = requests.get(f"http://localhost:{self.shrimp_port}", timeout=3)
            self.mcp_available = response.status_code == 200
            return self.mcp_available
        except:
            self.mcp_available = False
            return False
    
    def get_current_evolution_state(self):
        """현재 진화 상태 조회"""
        try:
            if Path(self.state_file).exists():
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
            else:
                state = {
                    "generation": 1,
                    "intelligence_level": 1.0,
                    "evolution_count": 0,
                    "learned_patterns": [],
                    "new_abilities": []
                }
            
            # 데이터베이스 통계 추가
            try:
                conn = sqlite3.connect(self.db_file)
                cursor = conn.cursor()
                
                cursor.execute("SELECT COUNT(*) FROM learning_history")
                learning_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM code_evolution")
                evolution_count = cursor.fetchone()[0]
                
                cursor.execute("SELECT COUNT(*) FROM feature_expansion")
                feature_count = cursor.fetchone()[0]
                
                conn.close()
                
                state["db_stats"] = {
                    "learning_records": learning_count,
                    "code_evolutions": evolution_count,
                    "feature_expansions": feature_count
                }
                
            except Exception as e:
                state["db_stats"] = {"error": str(e)}
            
            return state
            
        except Exception as e:
            print(f"❌ 상태 조회 실패: {e}")
            return {}
    
    def analyze_evolution_potential(self, state):
        """진화 잠재력 분석"""
        analysis = {
            "readiness_score": 0,
            "bottlenecks": [],
            "opportunities": [],
            "recommendations": []
        }
        
        # 학습 경험치 분석
        experience = state.get("learning_experience", 0)
        if experience >= 4.0:
            analysis["readiness_score"] += 30
            analysis["opportunities"].append("진화 임계값 근접")
        elif experience >= 2.0:
            analysis["readiness_score"] += 15
        else:
            analysis["bottlenecks"].append("학습 경험 부족")
        
        # 지능 레벨 분석
        intelligence = state.get("intelligence_level", 1.0)
        if intelligence >= 2.0:
            analysis["readiness_score"] += 25
            analysis["opportunities"].append("고급 지능 달성")
        elif intelligence >= 1.5:
            analysis["readiness_score"] += 15
        else:
            analysis["bottlenecks"].append("지능 레벨 낮음")
        
        # 학습 패턴 분석
        patterns = len(state.get("learned_patterns", []))
        if patterns >= 50:
            analysis["readiness_score"] += 25
            analysis["opportunities"].append("풍부한 학습 패턴")
        elif patterns >= 20:
            analysis["readiness_score"] += 15
        else:
            analysis["bottlenecks"].append("학습 패턴 부족")
        
        # 기능 확장 분석
        abilities = len(state.get("new_abilities", []))
        if abilities >= 5:
            analysis["readiness_score"] += 20
            analysis["opportunities"].append("다양한 기능 보유")
        elif abilities >= 2:
            analysis["readiness_score"] += 10
        
        # 권장사항 생성
        if analysis["readiness_score"] >= 80:
            analysis["recommendations"].append("🚀 고급 진화 모드 권장")
        elif analysis["readiness_score"] >= 60:
            analysis["recommendations"].append("⚡ 표준 진화 권장")
        elif analysis["readiness_score"] >= 40:
            analysis["recommendations"].append("🔧 기초 진화 권장")
        else:
            analysis["recommendations"].append("📚 추가 학습 필요")
        
        return analysis
    
    def execute_targeted_evolution(self, strategy="auto"):
        """목표 지향 진화 실행"""
        print(f"🎯 목표 지향 진화 시작: {strategy}")
        
        # 현재 상태 분석
        current_state = self.get_current_evolution_state()
        analysis = self.analyze_evolution_potential(current_state)
        
        print(f"📊 진화 준비도: {analysis['readiness_score']}/100")
        
        if analysis["opportunities"]:
            print("✨ 기회 요소:")
            for opp in analysis["opportunities"]:
                print(f"   • {opp}")
        
        if analysis["bottlenecks"]:
            print("⚠️ 병목 요소:")
            for bottleneck in analysis["bottlenecks"]:
                print(f"   • {bottleneck}")
        
        # 진화 전략 선택
        if strategy == "auto":
            if analysis["readiness_score"] >= 70:
                strategy = "intelligence_boost"
            elif analysis["readiness_score"] >= 50:
                strategy = "feature_enhancement"
            else:
                strategy = "learning_optimization"
        
        print(f"🧬 선택된 전략: {strategy}")
        
        # 전략별 진화 파라미터 조정
        evolution_params = self.get_strategy_parameters(strategy)
        
        # 진화 실행
        result = self.run_evolution_with_params(evolution_params)
        
        # 결과 분석
        new_state = self.get_current_evolution_state()
        evolution_impact = self.analyze_evolution_impact(current_state, new_state)
        
        return {
            "strategy": strategy,
            "before": current_state,
            "after": new_state,
            "impact": evolution_impact,
            "success": result
        }
    
    def get_strategy_parameters(self, strategy):
        """전략별 진화 파라미터"""
        strategies = {
            "learning_optimization": {
                "focus": "학습 효율성",
                "target_improvement": 0.2,
                "evolution_cycles": 1
            },
            "code_refactoring": {
                "focus": "코드 품질",
                "target_improvement": 0.15,
                "evolution_cycles": 2
            },
            "feature_enhancement": {
                "focus": "기능 확장",
                "target_improvement": 0.25,
                "evolution_cycles": 1
            },
            "performance_tuning": {
                "focus": "성능 최적화",
                "target_improvement": 0.3,
                "evolution_cycles": 2
            },
            "intelligence_boost": {
                "focus": "지능 증강",
                "target_improvement": 0.4,
                "evolution_cycles": 3
            }
        }
        
        return strategies.get(strategy, strategies["learning_optimization"])
    
    def run_evolution_with_params(self, params):
        """파라미터를 적용한 진화 실행"""
        try:
            print(f"🔧 진화 파라미터: {params['focus']}")
            print(f"🎯 목표 개선: {params['target_improvement']*100}%")
            print(f"🔄 진화 사이클: {params['evolution_cycles']}회")
            
            success_count = 0
            
            for cycle in range(params['evolution_cycles']):
                print(f"\n🧬 진화 사이클 {cycle + 1}/{params['evolution_cycles']}")
                
                # 진화 에이전트 실행
                process = subprocess.run(
                    ["D:/.venv/Scripts/python.exe", "self_evolving_agent.py"],
                    cwd="d:/",
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if process.returncode == 0:
                    success_count += 1
                    print(f"✅ 사이클 {cycle + 1} 성공")
                else:
                    print(f"❌ 사이클 {cycle + 1} 실패")
                
                # 사이클 간 대기
                if cycle < params['evolution_cycles'] - 1:
                    time.sleep(2)
            
            success_rate = success_count / params['evolution_cycles']
            print(f"\n📊 전체 성공률: {success_rate*100:.1f}%")
            
            return success_rate >= 0.5
            
        except Exception as e:
            print(f"❌ 진화 실행 실패: {e}")
            return False
    
    def analyze_evolution_impact(self, before, after):
        """진화 영향 분석"""
        impact = {}
        
        # 세대 변화
        gen_before = before.get("generation", 1)
        gen_after = after.get("generation", 1)
        impact["generation_change"] = gen_after - gen_before
        
        # 지능 레벨 변화
        intel_before = before.get("intelligence_level", 1.0)
        intel_after = after.get("intelligence_level", 1.0)
        impact["intelligence_improvement"] = intel_after - intel_before
        impact["intelligence_percent"] = ((intel_after - intel_before) / intel_before * 100) if intel_before > 0 else 0
        
        # 능력 추가
        abilities_before = len(before.get("new_abilities", []))
        abilities_after = len(after.get("new_abilities", []))
        impact["new_abilities"] = abilities_after - abilities_before
        
        # 학습 패턴 증가
        patterns_before = len(before.get("learned_patterns", []))
        patterns_after = len(after.get("learned_patterns", []))
        impact["pattern_growth"] = patterns_after - patterns_before
        
        # 데이터베이스 변화
        db_before = before.get("db_stats", {})
        db_after = after.get("db_stats", {})
        
        if isinstance(db_before, dict) and isinstance(db_after, dict):
            impact["db_evolution"] = db_after.get("code_evolutions", 0) - db_before.get("code_evolutions", 0)
            impact["db_features"] = db_after.get("feature_expansions", 0) - db_before.get("feature_expansions", 0)
        
        return impact
    
    def continuous_adaptive_evolution(self, target_generations=5):
        """연속 적응형 진화"""
        print(f"🚀 연속 적응형 진화 시작 - 목표: {target_generations}세대")
        
        results = []
        
        for gen in range(target_generations):
            print(f"\n{'='*50}")
            print(f"🧬 진화 라운드 {gen + 1}/{target_generations}")
            print('='*50)
            
            # 현재 상태 기반 전략 선택
            current_state = self.get_current_evolution_state()
            analysis = self.analyze_evolution_potential(current_state)
            
            # 적응형 전략 선택
            if analysis["readiness_score"] >= 80:
                strategy = "intelligence_boost"
            elif analysis["readiness_score"] >= 60:
                strategy = "feature_enhancement"
            elif analysis["readiness_score"] >= 40:
                strategy = "performance_tuning"
            else:
                strategy = "learning_optimization"
            
            # 진화 실행
            result = self.execute_targeted_evolution(strategy)
            results.append(result)
            
            # 결과 요약
            impact = result["impact"]
            print(f"\n📊 라운드 {gen + 1} 결과:")
            print(f"   세대: +{impact.get('generation_change', 0)}")
            print(f"   지능: +{impact.get('intelligence_improvement', 0):.3f} ({impact.get('intelligence_percent', 0):+.1f}%)")
            print(f"   새 능력: +{impact.get('new_abilities', 0)}개")
            print(f"   학습 패턴: +{impact.get('pattern_growth', 0)}개")
            
            # 다음 라운드 준비
            if gen < target_generations - 1:
                print("⏰ 다음 라운드까지 3초 대기...")
                time.sleep(3)
        
        # 전체 결과 요약
        self.print_final_evolution_summary(results)
        
        return results
    
    def print_final_evolution_summary(self, results):
        """최종 진화 요약"""
        print(f"\n🎉 연속 진화 완료!")
        print("="*60)
        
        total_gen_change = sum(r["impact"].get("generation_change", 0) for r in results)
        total_intel_improvement = sum(r["impact"].get("intelligence_improvement", 0) for r in results)
        total_abilities = sum(r["impact"].get("new_abilities", 0) for r in results)
        total_patterns = sum(r["impact"].get("pattern_growth", 0) for r in results)
        
        print(f"📈 전체 성과:")
        print(f"   세대 발전: +{total_gen_change}")
        print(f"   지능 향상: +{total_intel_improvement:.3f}")
        print(f"   새 능력: +{total_abilities}개")
        print(f"   학습 패턴: +{total_patterns}개")
        
        success_count = sum(1 for r in results if r["success"])
        print(f"   성공률: {success_count}/{len(results)} ({success_count/len(results)*100:.1f}%)")
        
        # 사용된 전략 분석
        strategies = [r["strategy"] for r in results]
        strategy_counts = {}
        for strategy in strategies:
            strategy_counts[strategy] = strategy_counts.get(strategy, 0) + 1
        
        print(f"\n🎯 사용된 전략:")
        for strategy, count in strategy_counts.items():
            print(f"   {strategy}: {count}회")

def main():
    print("🧬 강화된 진화 에이전트 시스템")
    print("="*50)
    print("1. 목표 지향 진화 (자동 전략)")
    print("2. 연속 적응형 진화 (3세대)")
    print("3. 연속 적응형 진화 (5세대)")
    print("4. 진화 상태 분석")
    print("5. 수동 전략 선택")
    
    choice = input("\n선택하세요 (1-5): ").strip()
    
    agent = EnhancedEvolutionAgent()
    
    if choice == "1":
        agent.execute_targeted_evolution("auto")
    
    elif choice == "2":
        agent.continuous_adaptive_evolution(3)
    
    elif choice == "3":
        agent.continuous_adaptive_evolution(5)
    
    elif choice == "4":
        state = agent.get_current_evolution_state()
        analysis = agent.analyze_evolution_potential(state)
        
        print("\n📊 현재 진화 상태:")
        print(f"   세대: {state.get('generation', 'N/A')}")
        print(f"   지능 레벨: {state.get('intelligence_level', 'N/A'):.3f}")
        print(f"   진화 횟수: {state.get('evolution_count', 'N/A')}")
        print(f"   학습 패턴: {len(state.get('learned_patterns', []))}개")
        print(f"   새 능력: {len(state.get('new_abilities', []))}개")
        
        print(f"\n🎯 진화 준비도: {analysis['readiness_score']}/100")
        
        if analysis["opportunities"]:
            print("\n✨ 기회 요소:")
            for opp in analysis["opportunities"]:
                print(f"   • {opp}")
        
        if analysis["recommendations"]:
            print("\n💡 권장사항:")
            for rec in analysis["recommendations"]:
                print(f"   • {rec}")
    
    elif choice == "5":
        print("\n🎯 전략 선택:")
        strategies = [
            "learning_optimization", "code_refactoring", 
            "feature_enhancement", "performance_tuning", "intelligence_boost"
        ]
        
        for i, strategy in enumerate(strategies, 1):
            print(f"   {i}. {strategy}")
        
        strategy_choice = input("전략 번호 선택: ").strip()
        
        try:
            strategy_index = int(strategy_choice) - 1
            if 0 <= strategy_index < len(strategies):
                selected_strategy = strategies[strategy_index]
                agent.execute_targeted_evolution(selected_strategy)
            else:
                print("❌ 잘못된 선택입니다.")
        except ValueError:
            print("❌ 숫자를 입력해주세요.")
    
    else:
        print("❌ 잘못된 선택입니다.")

if __name__ == "__main__":
    main()
