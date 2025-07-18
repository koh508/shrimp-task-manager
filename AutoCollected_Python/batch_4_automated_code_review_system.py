#!/usr/bin/env python3
"""
Automated Code Review and Improvement System
Based on Microsoft VS Code patterns
- 자동 코드 분석 및 품질 평가
- 리팩토링 제안 및 최적화 권장사항
- 코드 스타일 및 베스트 프랙티스 검증
- 실시간 개선사항 적용
"""

import os
import ast
import re
import json
import sqlite3
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path
import difflib

@dataclass
class CodeIssue:
    """코드 이슈 정보"""
    file_path: str
    line_number: int
    issue_type: str
    severity: str  # 'error', 'warning', 'info', 'suggestion'
    description: str
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class RefactoringSuggestion:
    """리팩토링 제안"""
    file_path: str
    start_line: int
    end_line: int
    refactor_type: str
    description: str
    original_code: str
    improved_code: str
    improvement_score: float

class CodeAnalyzer:
    """코드 분석기"""
    
    def __init__(self):
        self.issues = []
        self.refactoring_suggestions = []
        
    def analyze_python_file(self, file_path: str) -> List[CodeIssue]:
        """Python 파일 분석"""
        issues = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # AST 파싱
            try:
                tree = ast.parse(content)
                issues.extend(self._analyze_ast(tree, file_path, lines))
            except SyntaxError as e:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=e.lineno or 1,
                    issue_type="syntax_error",
                    severity="error",
                    description=f"Syntax error: {e.msg}",
                    code_snippet=lines[e.lineno - 1] if e.lineno and e.lineno <= len(lines) else ""
                ))
            
            # 추가 분석
            issues.extend(self._analyze_code_style(file_path, lines))
            issues.extend(self._analyze_complexity(file_path, lines))
            issues.extend(self._analyze_security(file_path, lines))
            
        except Exception as e:
            issues.append(CodeIssue(
                file_path=file_path,
                line_number=1,
                issue_type="analysis_error",
                severity="error",
                description=f"Failed to analyze file: {str(e)}"
            ))
        
        return issues
    
    def _analyze_ast(self, tree: ast.AST, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """AST 기반 분석"""
        issues = []
        
        for node in ast.walk(tree):
            # 함수 복잡도 검사
            if isinstance(node, ast.FunctionDef):
                complexity = self._calculate_complexity(node)
                if complexity > 10:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="high_complexity",
                        severity="warning",
                        description=f"Function '{node.name}' has high complexity ({complexity})",
                        suggestion="Consider breaking this function into smaller functions",
                        code_snippet=lines[node.lineno - 1] if node.lineno <= len(lines) else ""
                    ))
                
                # 긴 함수 검사
                func_length = (node.end_lineno or node.lineno) - node.lineno + 1
                if func_length > 50:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="long_function",
                        severity="info",
                        description=f"Function '{node.name}' is {func_length} lines long",
                        suggestion="Consider breaking this function into smaller functions"
                    ))
            
            # 클래스 분석
            if isinstance(node, ast.ClassDef):
                # 메서드 수 검사
                methods = [n for n in node.body if isinstance(n, ast.FunctionDef)]
                if len(methods) > 20:
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="large_class",
                        severity="warning",
                        description=f"Class '{node.name}' has {len(methods)} methods",
                        suggestion="Consider splitting this class or using composition"
                    ))
            
            # TODO 주석 검사
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str) and 'TODO' in node.value.value.upper():
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=node.lineno,
                        issue_type="todo_comment",
                        severity="info",
                        description="TODO comment found",
                        code_snippet=node.value.value
                    ))
        
        return issues
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """사이클로매틱 복잡도 계산"""
        complexity = 1  # 기본 복잡도
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.Try)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _analyze_code_style(self, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """코드 스타일 분석"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            # 긴 라인 검사
            if len(line) > 120:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="long_line",
                    severity="info",
                    description=f"Line too long ({len(line)} > 120 characters)",
                    suggestion="Break line into multiple lines",
                    code_snippet=line[:50] + "..." if len(line) > 50 else line
                ))
            
            # 트레일링 공백 검사
            if line.endswith(' ') or line.endswith('\t'):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="trailing_whitespace",
                    severity="info",
                    description="Trailing whitespace found",
                    suggestion="Remove trailing whitespace"
                ))
            
            # 하드코딩된 경로 검사
            if re.search(r'["\'](?:[A-Za-z]:)?[/\\][\w/\\.-]+["\']', line):
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="hardcoded_path",
                    severity="warning",
                    description="Hardcoded file path found",
                    suggestion="Use os.path.join() or pathlib.Path",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _analyze_complexity(self, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """복잡도 분석"""
        issues = []
        
        # 중첩 레벨 검사
        for i, line in enumerate(lines, 1):
            indent_level = (len(line) - len(line.lstrip())) // 4
            if indent_level > 4:
                issues.append(CodeIssue(
                    file_path=file_path,
                    line_number=i,
                    issue_type="deep_nesting",
                    severity="warning",
                    description=f"Deep nesting level ({indent_level})",
                    suggestion="Consider extracting nested logic into separate functions",
                    code_snippet=line.strip()
                ))
        
        return issues
    
    def _analyze_security(self, file_path: str, lines: List[str]) -> List[CodeIssue]:
        """보안 분석"""
        issues = []
        
        security_patterns = [
            (r'eval\s*\(', "Use of eval() is dangerous"),
            (r'exec\s*\(', "Use of exec() can be dangerous"),
            (r'shell=True', "shell=True in subprocess can be dangerous"),
            (r'password\s*=\s*["\'][^"\']+["\']', "Hardcoded password detected"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "Hardcoded API key detected"),
        ]
        
        for i, line in enumerate(lines, 1):
            for pattern, message in security_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issues.append(CodeIssue(
                        file_path=file_path,
                        line_number=i,
                        issue_type="security_issue",
                        severity="warning",
                        description=message,
                        suggestion="Use secure alternatives or environment variables",
                        code_snippet=line.strip()
                    ))
        
        return issues

class RefactoringEngine:
    """리팩토링 엔진"""
    
    def __init__(self):
        self.suggestions = []
    
    def suggest_refactoring(self, file_path: str) -> List[RefactoringSuggestion]:
        """리팩토링 제안 생성"""
        suggestions = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # 중복 코드 검사
            suggestions.extend(self._detect_duplicate_code(file_path, lines))
            
            # 함수 추출 제안
            suggestions.extend(self._suggest_function_extraction(file_path, lines))
            
            # 변수명 개선 제안
            suggestions.extend(self._suggest_variable_naming(file_path, lines))
            
        except Exception as e:
            logging.error(f"Error in refactoring analysis: {e}")
        
        return suggestions
    
    def _detect_duplicate_code(self, file_path: str, lines: List[str]) -> List[RefactoringSuggestion]:
        """중복 코드 검출"""
        suggestions = []
        
        # 간단한 중복 검출 (3줄 이상)
        for i in range(len(lines) - 2):
            block = lines[i:i+3]
            if all(line.strip() for line in block):  # 빈 줄 제외
                for j in range(i + 3, len(lines) - 2):
                    compare_block = lines[j:j+3]
                    if block == compare_block:
                        suggestions.append(RefactoringSuggestion(
                            file_path=file_path,
                            start_line=i + 1,
                            end_line=i + 3,
                            refactor_type="extract_function",
                            description=f"Duplicate code found (lines {i+1}-{i+3} and {j+1}-{j+3})",
                            original_code='\n'.join(block),
                            improved_code=f"# Extract to function:\n# def extracted_function():\n{chr(10).join(block)}",
                            improvement_score=0.7
                        ))
                        break
        
        return suggestions
    
    def _suggest_function_extraction(self, file_path: str, lines: List[str]) -> List[RefactoringSuggestion]:
        """함수 추출 제안"""
        suggestions = []
        
        # 긴 블록 검사
        current_indent = 0
        block_start = 0
        
        for i, line in enumerate(lines):
            if line.strip():
                indent = len(line) - len(line.lstrip())
                if indent > current_indent and i - block_start > 10:
                    block = lines[block_start:i]
                    suggestions.append(RefactoringSuggestion(
                        file_path=file_path,
                        start_line=block_start + 1,
                        end_line=i,
                        refactor_type="extract_function",
                        description=f"Large code block ({i - block_start} lines) can be extracted",
                        original_code='\n'.join(block),
                        improved_code=f"# Extract to function:\n# def extracted_logic():\n{chr(10).join(['    ' + l for l in block])}",
                        improvement_score=0.6
                    ))
                
                current_indent = indent
                block_start = i
        
        return suggestions
    
    def _suggest_variable_naming(self, file_path: str, lines: List[str]) -> List[RefactoringSuggestion]:
        """변수명 개선 제안"""
        suggestions = []
        
        # 짧은 변수명 검사
        short_var_pattern = r'\b([a-z])\s*='
        
        for i, line in enumerate(lines, 1):
            matches = re.finditer(short_var_pattern, line)
            for match in matches:
                var_name = match.group(1)
                if var_name in ['i', 'j', 'k']:  # 루프 변수는 제외
                    continue
                
                suggestions.append(RefactoringSuggestion(
                    file_path=file_path,
                    start_line=i,
                    end_line=i,
                    refactor_type="rename_variable",
                    description=f"Variable '{var_name}' has a non-descriptive name",
                    original_code=line.strip(),
                    improved_code=f"# Consider renaming '{var_name}' to a more descriptive name",
                    improvement_score=0.4
                ))
        
        return suggestions

class CodeReviewSystem:
    """코드 리뷰 시스템"""
    
    def __init__(self):
        self.db_path = "code_review_system.db"
        self.analyzer = CodeAnalyzer()
        self.refactoring_engine = RefactoringEngine()
        self._setup_database()
        self.logger = self._setup_logging()
    
    def _setup_database(self):
        """데이터베이스 설정"""
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        cursor = self.conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                file_path TEXT,
                review_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_issues INTEGER,
                critical_issues INTEGER,
                suggestions_count INTEGER,
                overall_score REAL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS code_issues (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER,
                file_path TEXT,
                line_number INTEGER,
                issue_type TEXT,
                severity TEXT,
                description TEXT,
                suggestion TEXT,
                code_snippet TEXT,
                fixed BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (review_id) REFERENCES code_reviews (id)
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS refactoring_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                review_id INTEGER,
                file_path TEXT,
                start_line INTEGER,
                end_line INTEGER,
                refactor_type TEXT,
                description TEXT,
                original_code TEXT,
                improved_code TEXT,
                improvement_score REAL,
                applied BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (review_id) REFERENCES code_reviews (id)
            )
        """)
        
        self.conn.commit()
    
    def _setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('code_review_system.log'),
                logging.StreamHandler()
            ]
        )
        return logging.getLogger('CodeReviewSystem')
    
    def review_file(self, file_path: str) -> Dict[str, Any]:
        """파일 리뷰 수행"""
        self.logger.info(f"Starting code review for: {file_path}")
        
        # 파일 존재 확인
        if not os.path.exists(file_path):
            return {"error": f"File not found: {file_path}"}
        
        # 코드 분석
        issues = self.analyzer.analyze_python_file(file_path)
        suggestions = self.refactoring_engine.suggest_refactoring(file_path)
        
        # 점수 계산
        overall_score = self._calculate_overall_score(issues, suggestions)
        
        # 데이터베이스에 저장
        review_id = self._save_review_results(file_path, issues, suggestions, overall_score)
        
        # 결과 생성
        result = {
            "review_id": review_id,
            "file_path": file_path,
            "timestamp": datetime.now().isoformat(),
            "overall_score": overall_score,
            "summary": {
                "total_issues": len(issues),
                "critical_issues": len([i for i in issues if i.severity == "error"]),
                "warnings": len([i for i in issues if i.severity == "warning"]),
                "suggestions": len(suggestions)
            },
            "issues": [self._issue_to_dict(issue) for issue in issues],
            "refactoring_suggestions": [self._suggestion_to_dict(suggestion) for suggestion in suggestions]
        }
        
        self.logger.info(f"Code review completed. Score: {overall_score:.2f}")
        return result
    
    def review_directory(self, directory_path: str) -> Dict[str, Any]:
        """디렉토리 내 모든 Python 파일 리뷰"""
        self.logger.info(f"Starting directory review: {directory_path}")
        
        results = {}
        python_files = []
        
        # Python 파일 찾기
        for root, dirs, files in os.walk(directory_path):
            for file in files:
                if file.endswith('.py'):
                    python_files.append(os.path.join(root, file))
        
        total_score = 0
        total_issues = 0
        total_suggestions = 0
        
        # 각 파일 리뷰
        for file_path in python_files:
            try:
                result = self.review_file(file_path)
                if "error" not in result:
                    results[file_path] = result
                    total_score += result["overall_score"]
                    total_issues += result["summary"]["total_issues"]
                    total_suggestions += result["summary"]["suggestions"]
            except Exception as e:
                self.logger.error(f"Error reviewing {file_path}: {e}")
                results[file_path] = {"error": str(e)}
        
        # 전체 결과
        directory_result = {
            "directory_path": directory_path,
            "timestamp": datetime.now().isoformat(),
            "files_reviewed": len(python_files),
            "average_score": total_score / len(python_files) if python_files else 0,
            "total_issues": total_issues,
            "total_suggestions": total_suggestions,
            "file_results": results
        }
        
        self.logger.info(f"Directory review completed. Average score: {directory_result['average_score']:.2f}")
        return directory_result
    
    def _calculate_overall_score(self, issues: List[CodeIssue], suggestions: List[RefactoringSuggestion]) -> float:
        """전체 점수 계산"""
        base_score = 100.0
        
        # 이슈에 따른 점수 차감
        for issue in issues:
            if issue.severity == "error":
                base_score -= 10
            elif issue.severity == "warning":
                base_score -= 5
            elif issue.severity == "info":
                base_score -= 2
        
        # 리팩토링 제안에 따른 추가 차감
        for suggestion in suggestions:
            base_score -= suggestion.improvement_score * 5
        
        return max(0.0, min(100.0, base_score))
    
    def _save_review_results(self, file_path: str, issues: List[CodeIssue], 
                           suggestions: List[RefactoringSuggestion], overall_score: float) -> int:
        """리뷰 결과 저장"""
        cursor = self.conn.cursor()
        
        # 리뷰 기본 정보 저장
        cursor.execute("""
            INSERT INTO code_reviews (file_path, total_issues, critical_issues, suggestions_count, overall_score)
            VALUES (?, ?, ?, ?, ?)
        """, (
            file_path,
            len(issues),
            len([i for i in issues if i.severity == "error"]),
            len(suggestions),
            overall_score
        ))
        
        review_id = cursor.lastrowid
        
        # 이슈 저장
        for issue in issues:
            cursor.execute("""
                INSERT INTO code_issues 
                (review_id, file_path, line_number, issue_type, severity, description, suggestion, code_snippet)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, issue.file_path, issue.line_number, issue.issue_type,
                issue.severity, issue.description, issue.suggestion, issue.code_snippet
            ))
        
        # 리팩토링 제안 저장
        for suggestion in suggestions:
            cursor.execute("""
                INSERT INTO refactoring_suggestions
                (review_id, file_path, start_line, end_line, refactor_type, description, 
                 original_code, improved_code, improvement_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                review_id, suggestion.file_path, suggestion.start_line, suggestion.end_line,
                suggestion.refactor_type, suggestion.description, suggestion.original_code,
                suggestion.improved_code, suggestion.improvement_score
            ))
        
        self.conn.commit()
        return review_id
    
    def _issue_to_dict(self, issue: CodeIssue) -> Dict[str, Any]:
        """CodeIssue를 딕셔너리로 변환"""
        return {
            "file_path": issue.file_path,
            "line_number": issue.line_number,
            "issue_type": issue.issue_type,
            "severity": issue.severity,
            "description": issue.description,
            "suggestion": issue.suggestion,
            "code_snippet": issue.code_snippet
        }
    
    def _suggestion_to_dict(self, suggestion: RefactoringSuggestion) -> Dict[str, Any]:
        """RefactoringSuggestion을 딕셔너리로 변환"""
        return {
            "file_path": suggestion.file_path,
            "start_line": suggestion.start_line,
            "end_line": suggestion.end_line,
            "refactor_type": suggestion.refactor_type,
            "description": suggestion.description,
            "original_code": suggestion.original_code,
            "improved_code": suggestion.improved_code,
            "improvement_score": suggestion.improvement_score
        }
    
    def generate_report(self, review_id: Optional[int] = None) -> Dict[str, Any]:
        """리뷰 보고서 생성"""
        cursor = self.conn.cursor()
        
        if review_id:
            # 특정 리뷰 보고서
            cursor.execute("SELECT * FROM code_reviews WHERE id = ?", (review_id,))
            review = cursor.fetchone()
            
            if not review:
                return {"error": "Review not found"}
            
            cursor.execute("SELECT * FROM code_issues WHERE review_id = ?", (review_id,))
            issues = cursor.fetchall()
            
            cursor.execute("SELECT * FROM refactoring_suggestions WHERE review_id = ?", (review_id,))
            suggestions = cursor.fetchall()
            
            return {
                "review_id": review_id,
                "file_path": review[1],
                "timestamp": review[2],
                "overall_score": review[5],
                "issues": len(issues),
                "suggestions": len(suggestions)
            }
        else:
            # 전체 통계 보고서
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_reviews,
                    AVG(overall_score) as avg_score,
                    SUM(total_issues) as total_issues,
                    SUM(critical_issues) as total_critical
                FROM code_reviews
            """)
            stats = cursor.fetchone()
            
            return {
                "total_reviews": stats[0],
                "average_score": round(stats[1] or 0, 2),
                "total_issues": stats[2] or 0,
                "total_critical_issues": stats[3] or 0,
                "timestamp": datetime.now().isoformat()
            }

def main():
    """메인 실행 함수"""
    print("🔍 Automated Code Review and Improvement System")
    print("=" * 60)
    
    # 코드 리뷰 시스템 초기화
    review_system = CodeReviewSystem()
    
    # 현재 디렉토리의 모든 Python 파일 리뷰
    current_dir = "."
    print(f"Starting comprehensive code review of directory: {current_dir}")
    
    # 디렉토리 리뷰 실행
    results = review_system.review_directory(current_dir)
    
    print("\n" + "=" * 60)
    print("📋 CODE REVIEW RESULTS")
    print("=" * 60)
    
    print(f"📁 Directory: {results['directory_path']}")
    print(f"📄 Files Reviewed: {results['files_reviewed']}")
    print(f"⭐ Average Score: {results['average_score']:.2f}/100")
    print(f"⚠️  Total Issues: {results['total_issues']}")
    print(f"💡 Total Suggestions: {results['total_suggestions']}")
    
    # 파일별 결과 요약
    print(f"\n📊 File-by-File Summary:")
    for file_path, result in results['file_results'].items():
        if "error" not in result:
            score = result['overall_score']
            issues = result['summary']['total_issues']
            critical = result['summary']['critical_issues']
            status = "🟢" if score >= 80 else "🟡" if score >= 60 else "🔴"
            print(f"  {status} {file_path}: {score:.1f}/100 ({issues} issues, {critical} critical)")
        else:
            print(f"  ❌ {file_path}: Error - {result['error']}")
    
    # 전체 보고서 저장
    report_file = f"code_review_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Detailed report saved to: {report_file}")
    
    # 전체 통계
    stats = review_system.generate_report()
    print(f"\n📈 System Statistics:")
    print(f"  Total Reviews: {stats['total_reviews']}")
    print(f"  Average Score: {stats['average_score']}/100")
    print(f"  Total Issues Found: {stats['total_issues']}")
    print(f"  Critical Issues: {stats['total_critical_issues']}")
    
    print("\n🎯 Code Review System demonstrates automated code quality analysis!")

if __name__ == "__main__":
    main()
