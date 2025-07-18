#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
진화 에이전트 파일 분석 API 서버
Evolution Agent File Analysis API Server
"""

import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
import urllib.parse
import threading

class FileAnalysisAPI:
    def __init__(self):
        self.port = 8088
        self.analysis_db = "file_analysis.db"
        self.processed_files = {}
        
        self.init_analysis_db()
    
    def init_analysis_db(self):
        """파일 분석 데이터베이스 초기화"""
        try:
            conn = sqlite3.connect(self.analysis_db)
            cursor = conn.cursor()
            
            # 파일 분석 기록 테이블
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS file_analyses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    file_name TEXT,
                    file_path TEXT,
                    file_size INTEGER,
                    content_type TEXT,
                    source TEXT,
                    analysis_summary TEXT,
                    key_insights TEXT,
                    suggestions TEXT,
                    complexity_score REAL,
                    quality_score REAL
                )
            """)
            
            # 옵시디언 파일 캐시
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS obsidian_files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP,
                    file_name TEXT,
                    file_path TEXT,
                    content TEXT,
                    word_count INTEGER,
                    last_modified TIMESTAMP,
                    tags TEXT,
                    links TEXT
                )
            """)
            
            conn.commit()
            conn.close()
            
            print("📁 파일 분석 API DB 초기화 완료")
            
        except Exception as e:
            print(f"❌ 분석 DB 초기화 실패: {e}")
    
    def analyze_file_content(self, file_name, content, source="unknown"):
        """파일 내용 분석"""
        try:
            analysis = {
                "timestamp": datetime.now().isoformat(),
                "file_name": file_name,
                "content_size": len(content),
                "source": source
            }
            
            # 기본 분석
            word_count = len(content.split())
            line_count = len(content.splitlines())
            
            # 파일 타입 감지
            file_type = self.detect_file_type(file_name, content)
            
            # 복잡도 분석
            complexity_score = self.calculate_complexity(content, file_type)
            
            # 품질 점수
            quality_score = self.calculate_quality(content, file_type)
            
            # 키워드 추출
            keywords = self.extract_keywords(content)
            
            # 구조 분석
            structure = self.analyze_structure(content, file_type)
            
            # 제안사항 생성
            suggestions = self.generate_suggestions(content, file_type, complexity_score)
            
            analysis.update({
                "file_type": file_type,
                "word_count": word_count,
                "line_count": line_count,
                "complexity_score": complexity_score,
                "quality_score": quality_score,
                "keywords": keywords,
                "structure": structure,
                "suggestions": suggestions,
                "summary": self.generate_summary(content, file_type, word_count),
                "insights": self.generate_insights(content, file_type, keywords)
            })
            
            # 데이터베이스에 기록
            self.save_analysis(analysis)
            
            return analysis
            
        except Exception as e:
            return {
                "error": str(e),
                "status": "분석 실패",
                "timestamp": datetime.now().isoformat()
            }
    
    def detect_file_type(self, file_name, content):
        """파일 타입 감지"""
        extension = Path(file_name).suffix.lower()
        
        type_mapping = {
            '.py': 'python',
            '.js': 'javascript', 
            '.ts': 'typescript',
            '.md': 'markdown',
            '.txt': 'text',
            '.json': 'json',
            '.html': 'html',
            '.css': 'css',
            '.yaml': 'yaml',
            '.yml': 'yaml'
        }
        
        detected_type = type_mapping.get(extension, 'unknown')
        
        # 내용 기반 추가 감지
        if detected_type == 'unknown' or detected_type == 'text':
            if '```' in content and '#' in content:
                detected_type = 'markdown'
            elif 'function' in content and '{}' in content:
                detected_type = 'javascript'
            elif 'def ' in content and 'import ' in content:
                detected_type = 'python'
        
        return detected_type
    
    def calculate_complexity(self, content, file_type):
        """복잡도 계산"""
        try:
            base_score = 1.0
            
            # 길이 기반 복잡도
            length_factor = min(len(content) / 1000, 5.0)
            
            # 타입별 복잡도 지표
            if file_type == 'python':
                # 함수, 클래스, 임포트 개수
                functions = content.count('def ')
                classes = content.count('class ')
                imports = content.count('import ')
                complexity_indicators = functions * 0.5 + classes * 1.0 + imports * 0.2
                
            elif file_type == 'javascript':
                functions = content.count('function')
                classes = content.count('class ')
                complexity_indicators = functions * 0.5 + classes * 1.0
                
            elif file_type == 'markdown':
                headers = content.count('#')
                links = content.count('[')
                complexity_indicators = headers * 0.3 + links * 0.1
                
            else:
                complexity_indicators = len(content.split()) / 100
            
            total_complexity = base_score + length_factor + complexity_indicators
            return min(total_complexity, 10.0)
            
        except:
            return 2.0
    
    def calculate_quality(self, content, file_type):
        """품질 점수 계산"""
        try:
            quality_score = 5.0  # 기본 점수
            
            # 기본 품질 지표
            if len(content.strip()) == 0:
                return 0.0
            
            # 구조적 품질
            if file_type == 'python':
                if 'def ' in content:
                    quality_score += 1.0
                if 'class ' in content:
                    quality_score += 1.0
                if '"""' in content or "'''" in content:
                    quality_score += 0.5  # 문서화
                    
            elif file_type == 'markdown':
                if '#' in content:
                    quality_score += 0.5  # 구조화
                if '[' in content and '](' in content:
                    quality_score += 0.5  # 링크
                if '```' in content:
                    quality_score += 0.5  # 코드 블록
            
            # 가독성 점수
            avg_line_length = len(content) / max(len(content.splitlines()), 1)
            if 20 <= avg_line_length <= 80:
                quality_score += 0.5
            
            return min(quality_score, 10.0)
            
        except:
            return 5.0
    
    def extract_keywords(self, content):
        """키워드 추출"""
        try:
            # 간단한 키워드 추출
            words = content.lower().split()
            
            # 불용어 제거
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
            
            filtered_words = [w for w in words if len(w) > 3 and w not in stop_words]
            
            # 빈도 계산
            word_freq = {}
            for word in filtered_words:
                word_freq[word] = word_freq.get(word, 0) + 1
            
            # 상위 키워드 반환
            top_keywords = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            return [word for word, freq in top_keywords]
            
        except:
            return []
    
    def analyze_structure(self, content, file_type):
        """구조 분석"""
        structure = {
            "sections": [],
            "complexity_indicators": {},
            "organization_score": 0.0
        }
        
        try:
            if file_type == 'markdown':
                # 마크다운 구조 분석
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if line.strip().startswith('#'):
                        level = len(line) - len(line.lstrip('#'))
                        title = line.strip('#').strip()
                        structure["sections"].append({
                            "line": i + 1,
                            "level": level,
                            "title": title
                        })
                
                structure["organization_score"] = min(len(structure["sections"]) * 1.5, 10.0)
                
            elif file_type == 'python':
                # 파이썬 구조 분석
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    stripped = line.strip()
                    if stripped.startswith('class '):
                        class_name = stripped.split()[1].split('(')[0].rstrip(':')
                        structure["sections"].append({
                            "line": i + 1,
                            "type": "class",
                            "name": class_name
                        })
                    elif stripped.startswith('def '):
                        func_name = stripped.split()[1].split('(')[0]
                        structure["sections"].append({
                            "line": i + 1,
                            "type": "function", 
                            "name": func_name
                        })
                
                structure["complexity_indicators"] = {
                    "classes": len([s for s in structure["sections"] if s.get("type") == "class"]),
                    "functions": len([s for s in structure["sections"] if s.get("type") == "function"])
                }
            
        except Exception as e:
            structure["error"] = str(e)
        
        return structure
    
    def generate_suggestions(self, content, file_type, complexity_score):
        """개선 제안사항 생성"""
        suggestions = []
        
        try:
            # 길이 기반 제안
            if len(content) > 5000:
                suggestions.append("📄 파일이 길어 보입니다. 여러 파일로 분할을 고려해보세요.")
            
            # 복잡도 기반 제안
            if complexity_score > 7.0:
                suggestions.append("🔧 복잡도가 높습니다. 리팩토링을 고려해보세요.")
            elif complexity_score < 2.0:
                suggestions.append("📈 내용을 더 풍부하게 만들어보세요.")
            
            # 타입별 제안
            if file_type == 'python':
                if '"""' not in content and "'''" not in content:
                    suggestions.append("📚 함수와 클래스에 문서화를 추가해보세요.")
                if 'import ' not in content and len(content) > 100:
                    suggestions.append("📦 필요한 라이브러리 임포트를 확인해보세요.")
                    
            elif file_type == 'markdown':
                if '#' not in content:
                    suggestions.append("📋 헤더를 추가하여 구조를 개선해보세요.")
                if '```' not in content and len(content) > 500:
                    suggestions.append("💻 코드 예제를 추가해보세요.")
            
            # 일반적인 제안
            line_count = len(content.splitlines())
            if line_count > 0:
                avg_line_length = len(content) / line_count
                if avg_line_length > 100:
                    suggestions.append("📏 줄이 너무 길어 보입니다. 가독성을 위해 줄바꿈을 고려해보세요.")
            
        except Exception as e:
            suggestions.append(f"⚠️ 분석 중 오류 발생: {str(e)}")
        
        return suggestions
    
    def generate_summary(self, content, file_type, word_count):
        """요약 생성"""
        try:
            summary = f"{file_type.title()} 파일 ({word_count} 단어)"
            
            if file_type == 'python':
                functions = content.count('def ')
                classes = content.count('class ')
                if functions > 0 or classes > 0:
                    summary += f" - {classes}개 클래스, {functions}개 함수"
                    
            elif file_type == 'markdown':
                headers = content.count('#')
                if headers > 0:
                    summary += f" - {headers}개 섹션"
            
            return summary
            
        except:
            return f"{file_type.title()} 파일"
    
    def generate_insights(self, content, file_type, keywords):
        """인사이트 생성"""
        insights = []
        
        try:
            # 키워드 기반 인사이트
            if keywords:
                top_keyword = keywords[0]
                insights.append(f"주요 주제: {top_keyword}")
            
            # 타입별 인사이트
            if file_type == 'python':
                if 'class' in content.lower():
                    insights.append("객체지향 프로그래밍 구조 사용")
                if 'async' in content.lower():
                    insights.append("비동기 프로그래밍 패턴 발견")
                    
            elif file_type == 'markdown':
                if '[' in content and '](' in content:
                    insights.append("외부 링크 및 참조 포함")
                if '```' in content:
                    insights.append("코드 예제 포함")
            
            # 길이 기반 인사이트
            if len(content) > 2000:
                insights.append("상세한 내용을 포함한 문서")
            elif len(content) < 200:
                insights.append("간결한 내용")
            
        except Exception as e:
            insights.append(f"분석 중 오류: {str(e)}")
        
        return insights
    
    def save_analysis(self, analysis):
        """분석 결과 저장"""
        try:
            conn = sqlite3.connect(self.analysis_db)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO file_analyses 
                (timestamp, file_name, file_path, file_size, content_type, source, 
                 analysis_summary, key_insights, suggestions, complexity_score, quality_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                datetime.now(),
                analysis.get("file_name", ""),
                analysis.get("file_path", ""),
                analysis.get("content_size", 0),
                analysis.get("file_type", ""),
                analysis.get("source", ""),
                analysis.get("summary", ""),
                json.dumps(analysis.get("insights", [])),
                json.dumps(analysis.get("suggestions", [])),
                analysis.get("complexity_score", 0.0),
                analysis.get("quality_score", 0.0)
            ))
            
            conn.commit()
            conn.close()
            
        except Exception as e:
            print(f"❌ 분석 결과 저장 실패: {e}")
    
    class AnalysisHandler(BaseHTTPRequestHandler):
        def __init__(self, request, client_address, server, api_instance):
            self.api = api_instance
            super().__init__(request, client_address, server)
        
        def do_POST(self):
            if self.path == '/api/analyze':
                try:
                    content_length = int(self.headers['Content-Length'])
                    post_data = self.rfile.read(content_length)
                    request_data = json.loads(post_data.decode('utf-8'))
                    
                    file_name = request_data.get('fileName', 'unknown.txt')
                    file_content = request_data.get('content', '')
                    source = request_data.get('source', 'api')
                    
                    # 파일 분석 수행
                    analysis_result = self.api.analyze_file_content(file_name, file_content, source)
                    
                    # 응답 전송
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
                    
                    response = {
                        "status": "성공",
                        "summary": analysis_result.get("summary", "분석 완료"),
                        "details": f"""
**📊 분석 결과:**
- 파일 타입: {analysis_result.get('file_type', 'unknown')}
- 복잡도: {analysis_result.get('complexity_score', 0):.1f}/10
- 품질: {analysis_result.get('quality_score', 0):.1f}/10
- 단어 수: {analysis_result.get('word_count', 0)}
- 줄 수: {analysis_result.get('line_count', 0)}

**🔑 주요 키워드:**
{', '.join(analysis_result.get('keywords', [])[:5])}

**💡 제안사항:**
{chr(10).join(analysis_result.get('suggestions', []))}

**🎯 인사이트:**
{chr(10).join(analysis_result.get('insights', []))}
                        """.strip()
                    }
                    
                    self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                    
                except Exception as e:
                    self.send_response(500)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    
                    error_response = {
                        "status": "오류",
                        "summary": "분석 처리 실패",
                        "details": str(e)
                    }
                    
                    self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
            
            else:
                self.send_response(404)
                self.end_headers()
        
        def do_OPTIONS(self):
            self.send_response(200)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
            self.send_header('Access-Control-Allow-Headers', 'Content-Type')
            self.end_headers()
        
        def log_message(self, format, *args):
            # 로그 억제
            pass
    
    def create_handler(self):
        """핸들러 생성"""
        api = self
        
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                if self.path == '/api/analyze':
                    try:
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        request_data = json.loads(post_data.decode('utf-8'))
                        
                        file_name = request_data.get('fileName', 'unknown.txt')
                        file_content = request_data.get('content', '')
                        source = request_data.get('source', 'api')
                        
                        # 파일 분석 수행
                        analysis_result = api.analyze_file_content(file_name, file_content, source)
                        
                        # 응답 전송
                        self.send_response(200)
                        self.send_header('Content-type', 'application/json')
                        self.send_header('Access-Control-Allow-Origin', '*')
                        self.end_headers()
                        
                        response = {
                            "status": "성공",
                            "summary": analysis_result.get("summary", "분석 완료"),
                            "details": f"""
**📊 분석 결과:**
- 파일 타입: {analysis_result.get('file_type', 'unknown')}
- 복잡도: {analysis_result.get('complexity_score', 0):.1f}/10
- 품질: {analysis_result.get('quality_score', 0):.1f}/10
- 단어 수: {analysis_result.get('word_count', 0)}
- 줄 수: {analysis_result.get('line_count', 0)}

**🔑 주요 키워드:**
{', '.join(analysis_result.get('keywords', [])[:5])}

**💡 제안사항:**
{chr(10).join(analysis_result.get('suggestions', []))}

**🎯 인사이트:**
{chr(10).join(analysis_result.get('insights', []))}
                            """.strip()
                        }
                        
                        self.wfile.write(json.dumps(response, ensure_ascii=False).encode('utf-8'))
                        
                    except Exception as e:
                        self.send_response(500)
                        self.send_header('Content-type', 'application/json')
                        self.end_headers()
                        
                        error_response = {
                            "status": "오류",
                            "summary": "분석 처리 실패",
                            "details": str(e)
                        }
                        
                        self.wfile.write(json.dumps(error_response, ensure_ascii=False).encode('utf-8'))
                
                else:
                    self.send_response(404)
                    self.end_headers()
            
            def do_OPTIONS(self):
                self.send_response(200)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
                self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                self.end_headers()
            
            def log_message(self, format, *args):
                # 로그 억제
                pass
        
        return Handler
    
    def start_api_server(self):
        """API 서버 시작"""
        try:
            handler = self.create_handler()
            server = HTTPServer(('localhost', self.port), handler)
            
            print(f"📁 파일 분석 API 서버 시작")
            print(f"🔗 API URL: http://localhost:{self.port}/api/analyze")
            print(f"📊 옵시디언 파일 분석 준비 완료")
            
            # 백그라운드에서 서버 실행
            server_thread = threading.Thread(target=server.serve_forever, daemon=True)
            server_thread.start()
            
            return server
            
        except Exception as e:
            print(f"❌ API 서버 시작 실패: {e}")
            return None

def main():
    api = FileAnalysisAPI()
    server = api.start_api_server()
    
    if server:
        try:
            while True:
                time.sleep(10)
                # 서버 유지
        except KeyboardInterrupt:
            print("\n👋 파일 분석 API 서버 종료")
            server.shutdown()

if __name__ == "__main__":
    main()
