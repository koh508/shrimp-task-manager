#!/usr/bin/env python3
"""
AI 생성 코드 품질 평가 시스템
"""

import os
import ast
import re
import json
import sqlite3
from datetime import datetime
from pathlib import Path
import hashlib

class AICodeEvaluator:
    """AI가 생성한 코드의 품질을 평가"""
    
    def __init__(self):
        self.evaluation_db = "code_evaluation.db"
        self.setup_database()
    
    def setup_database(self):
        """평가 데이터베이스 설정"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS code_evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                filename TEXT,
                generation INTEGER,
                syntax_score INTEGER,
                complexity_score INTEGER,
                duplication_score INTEGER,
                functionality_score INTEGER,
                total_score INTEGER,
                issues TEXT,
                recommendations TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def evaluate_all_generated_code(self):
        """모든 AI 생성 코드 평가"""
        print("🔍 AI 생성 코드 품질 평가 시작")
        print("=" * 60)
        
        # AI 생성 파일들 찾기
        ai_files = [f for f in os.listdir('.') 
                   if f.startswith('self_evolved_ai_gen_') and f.endswith('.py')]
        
        if not ai_files:
            print("❌ AI 생성 파일을 찾을 수 없습니다.")
            return
        
        # 최근 10개 파일만 평가
        ai_files.sort(reverse=True)
        recent_files = ai_files[:10]
        
        evaluations = []
        
        for filename in recent_files:
            try:
                evaluation = self.evaluate_single_file(filename)
                evaluations.append(evaluation)
                
                print(f"📄 파일: {filename}")
                print(f"   세대: {evaluation['generation']}")
                print(f"   문법: {evaluation['syntax_score']}/100")
                print(f"   복잡도: {evaluation['complexity_score']}/100") 
                print(f"   중복도: {evaluation['duplication_score']}/100")
                print(f"   기능성: {evaluation['functionality_score']}/100")
                print(f"   📊 총점: {evaluation['total_score']}/100")
                
                if evaluation['issues']:
                    print(f"   ⚠️ 문제점: {len(evaluation['issues'])}개")
                    for issue in evaluation['issues'][:3]:  # 상위 3개만
                        print(f"      • {issue}")
                print()
                
            except Exception as e:
                print(f"❌ {filename} 평가 실패: {e}")
        
        # 종합 분석
        self.generate_summary_report(evaluations)
        
        return evaluations
    
    def evaluate_single_file(self, filename):
        """단일 파일 평가"""
        with open(filename, 'r', encoding='utf-8') as f:
            code = f.read()
        
        # 세대 번호 추출
        generation = self.extract_generation(filename)
        
        # 각 항목별 평가
        syntax_score = self.evaluate_syntax(code)
        complexity_score = self.evaluate_complexity(code)
        duplication_score = self.evaluate_duplication(filename, code)
        functionality_score = self.evaluate_functionality(code)
        
        # 총점 계산
        total_score = (syntax_score + complexity_score + duplication_score + functionality_score) // 4
        
        # 문제점 및 권장사항
        issues = self.find_issues(code)
        recommendations = self.generate_recommendations(code, issues)
        
        evaluation = {
            'filename': filename,
            'generation': generation,
            'syntax_score': syntax_score,
            'complexity_score': complexity_score,
            'duplication_score': duplication_score,
            'functionality_score': functionality_score,
            'total_score': total_score,
            'issues': issues,
            'recommendations': recommendations
        }
        
        # DB 저장
        self.save_evaluation(evaluation)
        
        return evaluation
    
    def extract_generation(self, filename):
        """파일명에서 세대 번호 추출"""
        try:
            parts = filename.split('_')
            if len(parts) >= 4:
                return int(parts[3])
        except:
            pass
        return 0
    
    def evaluate_syntax(self, code):
        """문법 평가"""
        try:
            ast.parse(code)
            return 100  # 문법 오류 없음
        except SyntaxError as e:
            # 문법 오류의 심각도에 따라 점수 차감
            if 'unexpected EOF' in str(e):
                return 30  # 심각한 오류
            elif 'invalid syntax' in str(e):
                return 50  # 중간 오류
            else:
                return 70  # 경미한 오류
        except Exception:
            return 0
    
    def evaluate_complexity(self, code):
        """복잡도 평가"""
        try:
            lines = code.splitlines()
            non_empty_lines = [line for line in lines if line.strip()]
            
            # 코드 구조 분석
            classes = len([line for line in non_empty_lines if line.strip().startswith('class ')])
            functions = len([line for line in non_empty_lines if line.strip().startswith('def ')])
            imports = len([line for line in non_empty_lines if 'import' in line])
            comments = len([line for line in non_empty_lines if line.strip().startswith('#')])
            docstrings = len(re.findall(r'""".*?"""', code, re.DOTALL))
            
            # 복잡도 점수 계산 (적당한 복잡도가 좋음)
            structure_score = min(100, (classes * 20) + (functions * 10) + (imports * 5))
            documentation_score = min(100, (comments * 5) + (docstrings * 20))
            
            # 라인 수 기반 평가
            if len(non_empty_lines) < 10:
                size_score = 30  # 너무 단순
            elif len(non_empty_lines) < 50:
                size_score = 80  # 적당함
            elif len(non_empty_lines) < 200:
                size_score = 100  # 좋음
            else:
                size_score = 60  # 너무 복잡
            
            return (structure_score + documentation_score + size_score) // 3
            
        except Exception:
            return 50
    
    def evaluate_duplication(self, filename, code):
        """중복도 평가"""
        try:
            # 다른 AI 생성 파일들과 비교
            ai_files = [f for f in os.listdir('.') 
                       if f.startswith('self_evolved_ai_gen_') and f.endswith('.py') and f != filename]
            
            code_hash = hashlib.md5(code.encode()).hexdigest()
            
            for other_file in ai_files[:10]:  # 최근 10개와만 비교
                try:
                    with open(other_file, 'r', encoding='utf-8') as f:
                        other_code = f.read()
                    
                    other_hash = hashlib.md5(other_code.encode()).hexdigest()
                    
                    if code_hash == other_hash:
                        return 0  # 완전 동일
                    
                    # 라인별 유사도 계산
                    import difflib
                    lines1 = code.splitlines()
                    lines2 = other_code.splitlines()
                    similarity = difflib.SequenceMatcher(None, lines1, lines2).ratio()
                    
                    if similarity > 0.95:
                        return 10  # 거의 동일
                    elif similarity > 0.8:
                        return 30  # 매우 유사
                    elif similarity > 0.6:
                        return 60  # 유사
                    
                except:
                    continue
            
            return 100  # 독창적
            
        except Exception:
            return 50
    
    def evaluate_functionality(self, code):
        """기능성 평가"""
        try:
            score = 50  # 기본 점수
            
            # 고급 기능 검사
            if 'async' in code and 'await' in code:
                score += 15  # 비동기 처리
            
            if 'ThreadPoolExecutor' in code or 'multiprocessing' in code:
                score += 15  # 병렬 처리
            
            if 'try:' in code and 'except' in code:
                score += 10  # 예외 처리
            
            if 'typing' in code:
                score += 10  # 타입 힌트
            
            if 'dataclass' in code:
                score += 10  # 데이터 클래스
            
            if 'logging' in code or 'logger' in code:
                score += 5  # 로깅
            
            # 실제 실행 가능성 테스트
            try:
                compile(code, '<string>', 'exec')
                score += 10  # 컴파일 가능
            except:
                score -= 20  # 컴파일 불가
            
            return min(100, score)
            
        except Exception:
            return 30
    
    def find_issues(self, code):
        """코드 문제점 찾기"""
        issues = []
        
        lines = code.splitlines()
        
        for i, line in enumerate(lines, 1):
            # 긴 라인
            if len(line) > 120:
                issues.append(f"라인 {i}: 너무 긴 라인 ({len(line)}자)")
            
            # 하드코딩
            if re.search(r'["\'].*[0-9]{3,}.*["\']', line):
                issues.append(f"라인 {i}: 하드코딩된 값")
            
            # TODO/FIXME
            if re.search(r'#.*\b(TODO|FIXME|HACK)\b', line, re.IGNORECASE):
                issues.append(f"라인 {i}: 미완성 코드")
        
        # 전체 코드 분석
        if 'import *' in code:
            issues.append("와일드카드 import 사용")
        
        if code.count('print(') > 5:
            issues.append("과도한 print 문 사용")
        
        if not re.search(r'""".*?"""', code, re.DOTALL) and 'def ' in code:
            issues.append("docstring 부족")
        
        return issues
    
    def generate_recommendations(self, code, issues):
        """개선 권장사항 생성"""
        recommendations = []
        
        if "긴 라인" in str(issues):
            recommendations.append("라인 길이를 120자 이내로 제한")
        
        if "하드코딩" in str(issues):
            recommendations.append("상수를 별도 변수로 분리")
        
        if "와일드카드 import" in str(issues):
            recommendations.append("명시적 import 사용")
        
        if "docstring 부족" in str(issues):
            recommendations.append("함수/클래스에 docstring 추가")
        
        if "print 문" in str(issues):
            recommendations.append("print 대신 logging 사용")
        
        # 추가 권장사항
        if 'async' not in code:
            recommendations.append("비동기 처리 도입 고려")
        
        if 'typing' not in code:
            recommendations.append("타입 힌트 추가")
        
        return recommendations
    
    def save_evaluation(self, evaluation):
        """평가 결과 저장"""
        conn = sqlite3.connect(self.evaluation_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO code_evaluations 
            (timestamp, filename, generation, syntax_score, complexity_score, 
             duplication_score, functionality_score, total_score, issues, recommendations)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            evaluation['filename'],
            evaluation['generation'],
            evaluation['syntax_score'],
            evaluation['complexity_score'],
            evaluation['duplication_score'],
            evaluation['functionality_score'],
            evaluation['total_score'],
            json.dumps(evaluation['issues']),
            json.dumps(evaluation['recommendations'])
        ))
        
        conn.commit()
        conn.close()
    
    def generate_summary_report(self, evaluations):
        """종합 리포트 생성"""
        if not evaluations:
            return
        
        print("=" * 60)
        print("📊 AI 코드 생성 품질 종합 분석")
        print("=" * 60)
        
        # 평균 점수
        avg_syntax = sum(e['syntax_score'] for e in evaluations) / len(evaluations)
        avg_complexity = sum(e['complexity_score'] for e in evaluations) / len(evaluations)
        avg_duplication = sum(e['duplication_score'] for e in evaluations) / len(evaluations)
        avg_functionality = sum(e['functionality_score'] for e in evaluations) / len(evaluations)
        avg_total = sum(e['total_score'] for e in evaluations) / len(evaluations)
        
        print(f"📈 평균 점수:")
        print(f"   문법: {avg_syntax:.1f}/100")
        print(f"   복잡도: {avg_complexity:.1f}/100")
        print(f"   중복도: {avg_duplication:.1f}/100")
        print(f"   기능성: {avg_functionality:.1f}/100")
        print(f"   📊 전체: {avg_total:.1f}/100")
        print()
        
        # 문제점 분석
        all_issues = []
        for e in evaluations:
            all_issues.extend(e['issues'])
        
        issue_counts = {}
        for issue in all_issues:
            key = issue.split(':')[1].strip() if ':' in issue else issue
            issue_counts[key] = issue_counts.get(key, 0) + 1
        
        if issue_counts:
            print("⚠️ 주요 문제점:")
            sorted_issues = sorted(issue_counts.items(), key=lambda x: x[1], reverse=True)
            for issue, count in sorted_issues[:5]:
                print(f"   • {issue}: {count}회")
            print()
        
        # 품질 등급
        if avg_total >= 80:
            grade = "🥇 우수"
        elif avg_total >= 60:
            grade = "🥈 양호"
        elif avg_total >= 40:
            grade = "🥉 보통"
        else:
            grade = "❌ 개선필요"
        
        print(f"🏆 전체 품질 등급: {grade} ({avg_total:.1f}점)")
        
        # 진화 트렌드
        if len(evaluations) > 1:
            recent_scores = [e['total_score'] for e in evaluations[:3]]
            older_scores = [e['total_score'] for e in evaluations[-3:]]
            
            recent_avg = sum(recent_scores) / len(recent_scores)
            older_avg = sum(older_scores) / len(older_scores)
            
            trend = recent_avg - older_avg
            
            if trend > 5:
                print(f"📈 진화 트렌드: 향상 중 (+{trend:.1f}점)")
            elif trend < -5:
                print(f"📉 진화 트렌드: 저하 중 ({trend:.1f}점)")
            else:
                print(f"📊 진화 트렌드: 안정적 ({trend:+.1f}점)")

def main():
    evaluator = AICodeEvaluator()
    evaluator.evaluate_all_generated_code()

if __name__ == "__main__":
    main()
