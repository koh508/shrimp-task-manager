#!/usr/bin/env python3
"""
개인 AI 비서 대화형 인터페이스
사용자와의 자연스러운 대화를 통해 비서 기능 활용
"""

import os
import json
import time
from datetime import datetime
from personal_ai_assistant import PersonalAIAssistant

class ConversationalAssistant:
    def __init__(self):
        print("🤖 개인 AI 비서 대화형 모드 시작")
        print("="*50)
        
        # 기본 비서 시스템 초기화
        self.assistant = PersonalAIAssistant()
        self.assistant.start_monitoring()
        
        # 대화 히스토리
        self.conversation_history = []
        
        # 사용자 선호도 로드
        self.user_preferences = self.load_user_preferences()
        
        print("💬 안녕하세요! 저는 당신의 개인 AI 비서입니다.")
        print("🖥️ AMD Ryzen 7 5800H 최적화 및 옵시디언 통합 완료")
        print("📚 현재 2,965개의 노트가 지식베이스에 로드되어 있습니다.")
        print("\n💡 도움말: 'help'를 입력하면 사용 가능한 명령어를 확인할 수 있습니다.")
    
    def load_user_preferences(self):
        """사용자 선호도 로드"""
        try:
            if os.path.exists("user_preferences.json"):
                with open("user_preferences.json", "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception:
            pass
        
        # 기본 선호도
        return {
            "greeting_style": "친근한",
            "response_length": "보통",
            "technical_level": "고급",
            "preferred_features": ["지식검색", "시스템모니터링", "파일관리"]
        }
    
    def save_user_preferences(self):
        """사용자 선호도 저장"""
        try:
            with open("user_preferences.json", "w", encoding="utf-8") as f:
                json.dump(self.user_preferences, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"❌ 선호도 저장 실패: {e}")
    
    def process_natural_language(self, user_input: str) -> dict:
        """자연어 입력 처리 및 의도 분석"""
        user_input = user_input.lower().strip()
        
        # 명령어 매핑
        intent_mapping = {
            # 검색 관련
            "search": ["검색", "찾아", "찾기", "search", "find"],
            "knowledge": ["지식", "노트", "옵시디언", "obsidian", "note"],
            
            # 시스템 관리
            "status": ["상태", "현황", "status", "health", "어떻게"],
            "performance": ["성능", "퍼포먼스", "performance", "속도"],
            "cleanup": ["정리", "청소", "cleanup", "clean"],
            "monitor": ["모니터링", "monitoring", "감시"],
            
            # 파일 관리
            "files": ["파일", "file", "분석", "analyze"],
            "backup": ["백업", "backup", "저장"],
            
            # 도움말
            "help": ["도움", "help", "명령어", "기능"],
            "settings": ["설정", "preferences", "환경설정"]
        }
        
        # 의도 분석
        detected_intent = "unknown"
        for intent, keywords in intent_mapping.items():
            if any(keyword in user_input for keyword in keywords):
                detected_intent = intent
                break
        
        # 매개변수 추출
        parameters = self.extract_parameters(user_input, detected_intent)
        
        return {
            "intent": detected_intent,
            "parameters": parameters,
            "original_input": user_input
        }
    
    def extract_parameters(self, user_input: str, intent: str) -> dict:
        """입력에서 매개변수 추출"""
        parameters = {}
        
        if intent == "search" or intent == "knowledge":
            # 검색어 추출 (따옴표 또는 키워드 뒤 내용)
            import re
            
            # "검색해줘 AI" -> AI 추출
            search_patterns = [
                r'검색.*?([가-힣\w\s]+)',
                r'찾아.*?([가-힣\w\s]+)',
                r'search.*?(\w+)',
                r'"([^"]+)"',
                r"'([^']+)'"
            ]
            
            for pattern in search_patterns:
                match = re.search(pattern, user_input)
                if match:
                    parameters["query"] = match.group(1).strip()
                    break
            
            # 기본값
            if "query" not in parameters:
                words = user_input.split()
                if len(words) > 1:
                    parameters["query"] = " ".join(words[1:])
        
        elif intent == "files":
            # 경로 추출
            if "경로" in user_input or "path" in user_input:
                import re
                path_match = re.search(r'([a-zA-Z]:[\\\/][\w\\\/\s]+)', user_input)
                if path_match:
                    parameters["path"] = path_match.group(1)
            
            # 기본값은 현재 디렉토리
            if "path" not in parameters:
                parameters["path"] = "."
        
        return parameters
    
    def execute_intent(self, parsed_input: dict) -> str:
        """의도에 따른 작업 실행"""
        intent = parsed_input["intent"]
        parameters = parsed_input["parameters"]
        
        try:
            if intent == "help":
                return self.show_help()
            
            elif intent == "status":
                return self.show_status()
            
            elif intent == "search" or intent == "knowledge":
                query = parameters.get("query", "")
                if not query:
                    return "🔍 검색어를 입력해주세요. 예: '검색해줘 AI 기술'"
                return self.search_knowledge(query)
            
            elif intent == "performance":
                return self.show_performance()
            
            elif intent == "files":
                path = parameters.get("path", ".")
                return self.analyze_files(path)
            
            elif intent == "cleanup":
                return self.cleanup_system()
            
            elif intent == "backup":
                return self.backup_obsidian()
            
            elif intent == "monitor":
                return self.show_monitoring()
            
            elif intent == "settings":
                return self.show_settings()
            
            else:
                return self.handle_unknown_intent(parsed_input["original_input"])
        
        except Exception as e:
            return f"❌ 작업 처리 중 오류가 발생했습니다: {e}"
    
    def search_knowledge(self, query: str) -> str:
        """지식베이스 검색"""
        results = self.assistant.search_knowledge_base(query, limit=5)
        
        if not results:
            return f"🔍 '{query}'에 대한 검색 결과가 없습니다."
        
        response = f"🔍 '{query}' 검색 결과 ({len(results)}개):\n\n"
        
        for i, result in enumerate(results, 1):
            response += f"📄 {i}. {result['title']}\n"
            response += f"   📁 {os.path.basename(result['file_path'])}\n"
            response += f"   📝 {result['content_preview']}\n"
            if result['tags']:
                response += f"   🏷️ 태그: {', '.join(result['tags'])}\n"
            response += f"   📅 수정일: {result['modified_date']}\n\n"
        
        return response
    
    def show_status(self) -> str:
        """시스템 상태 표시"""
        status = self.assistant.get_assistant_status()
        
        response = "🖥️ 시스템 현재 상태:\n\n"
        response += f"⚡ CPU 사용량: {status['system_health']['cpu_usage']:.1f}%\n"
        response += f"🧠 메모리 사용량: {status['system_health']['memory_usage']:.1f}%\n"
        response += f"💾 사용 가능 메모리: {status['system_health']['memory_available_gb']:.1f}GB\n"
        response += f"📊 모니터링 상태: {'활성' if status['system_health']['monitoring_active'] else '비활성'}\n\n"
        
        response += f"📚 지식베이스:\n"
        response += f"   📄 옵시디언 노트: {status['knowledge_base']['obsidian_notes']:,}개\n"
        response += f"   📁 연결된 볼트: {status['knowledge_base']['vaults_connected']}개\n\n"
        
        response += f"🎯 성능:\n"
        response += f"   ✅ 성공한 작업: {status['performance']['successful_tasks']}개\n"
        response += f"   📊 최근 1시간 모니터링: {status['performance']['monitoring_points_1h']}회\n"
        response += f"   🚀 PC 최적화: {status['performance']['pc_optimization']}\n"
        
        return response
    
    def show_performance(self) -> str:
        """성능 분석 표시"""
        task_result = self.assistant.execute_pc_optimized_task("performance_report", {})
        
        if not task_result["success"]:
            return "❌ 성능 보고서 생성에 실패했습니다."
        
        perf = task_result["result"]
        
        response = "📊 시스템 성능 분석 (최근 24시간):\n\n"
        response += f"🖥️ CPU 통계:\n"
        response += f"   평균: {perf['cpu_stats']['average']:.1f}%\n"
        response += f"   최대: {perf['cpu_stats']['max']:.1f}%\n"
        response += f"   최소: {perf['cpu_stats']['min']:.1f}%\n\n"
        
        response += f"🧠 메모리 통계:\n"
        response += f"   평균: {perf['memory_stats']['average']:.1f}%\n"
        response += f"   최대: {perf['memory_stats']['max']:.1f}%\n"
        response += f"   최소: {perf['memory_stats']['min']:.1f}%\n\n"
        
        response += f"🎯 종합 성능 점수: {perf['performance_stats']['average']:.1f}/100\n\n"
        
        response += "💡 권장사항:\n"
        for recommendation in perf['recommendations']:
            response += f"   • {recommendation}\n"
        
        return response
    
    def analyze_files(self, path: str) -> str:
        """파일 분석"""
        task_result = self.assistant.execute_pc_optimized_task("file_analysis", {"path": path})
        
        if not task_result["success"]:
            return f"❌ '{path}' 경로 분석에 실패했습니다."
        
        analysis = task_result["result"]
        
        response = f"📁 '{path}' 디렉토리 분석:\n\n"
        response += f"📊 통계:\n"
        response += f"   📄 총 파일 수: {analysis['total_files']:,}개\n"
        response += f"   💾 총 크기: {analysis['total_size_mb']:,.1f}MB\n\n"
        
        if analysis['file_types']:
            response += "📋 파일 형태별 분포:\n"
            sorted_types = sorted(analysis['file_types'].items(), key=lambda x: x[1], reverse=True)
            for ext, count in sorted_types[:10]:  # 상위 10개만
                ext_name = ext if ext else "확장자 없음"
                response += f"   {ext_name}: {count:,}개\n"
            response += "\n"
        
        if analysis['large_files']:
            response += f"📦 큰 파일들 (상위 {len(analysis['large_files'])}개):\n"
            for large_file in analysis['large_files']:
                filename = os.path.basename(large_file['path'])
                response += f"   📄 {filename}: {large_file['size_mb']:.1f}MB\n"
            response += "\n"
        
        if analysis['recent_files']:
            response += f"🆕 최근 파일들 (상위 {len(analysis['recent_files'])}개):\n"
            for recent_file in analysis['recent_files'][:5]:  # 상위 5개만
                filename = os.path.basename(recent_file['path'])
                mod_date = recent_file['modified'][:10]  # 날짜만
                response += f"   📄 {filename} ({mod_date})\n"
        
        return response
    
    def cleanup_system(self) -> str:
        """시스템 정리"""
        task_result = self.assistant.execute_pc_optimized_task("system_cleanup", {})
        
        if not task_result["success"]:
            return "❌ 시스템 정리에 실패했습니다."
        
        cleanup = task_result["result"]
        
        response = "🧹 시스템 정리 완료:\n\n"
        response += f"🗑️ 삭제된 임시 파일: {cleanup['temp_files_deleted']}개\n"
        response += f"💾 메모리 최적화: {'완료' if cleanup['memory_optimized'] else '실패'}\n"
        response += f"🧹 캐시 정리: {'완료' if cleanup['cache_cleared'] else '실패'}\n"
        
        if "error" in cleanup:
            response += f"\n⚠️ 일부 작업 실패: {cleanup['error']}"
        
        return response
    
    def backup_obsidian(self) -> str:
        """옵시디언 백업"""
        task_result = self.assistant.execute_pc_optimized_task("obsidian_backup", {})
        
        if not task_result["success"]:
            return "❌ 옵시디언 백업에 실패했습니다."
        
        backup = task_result["result"]
        
        response = "💾 옵시디언 백업 완료:\n\n"
        response += f"📁 백업된 볼트: {backup['vaults_backed_up']}개\n"
        response += f"💾 총 백업 크기: {backup['total_size_mb']:.1f}MB\n"
        response += f"📂 백업 위치: {backup['backup_path']}\n"
        
        if "error" in backup:
            response += f"\n⚠️ 백업 오류: {backup['error']}"
        
        return response
    
    def show_monitoring(self) -> str:
        """모니터링 정보"""
        status = self.assistant.get_assistant_status()
        
        response = "📊 실시간 모니터링 현황:\n\n"
        response += f"🔄 모니터링 상태: {'활성' if status['system_health']['monitoring_active'] else '비활성'}\n"
        response += f"📈 최근 1시간 데이터: {status['performance']['monitoring_points_1h']}개\n"
        response += f"⚡ 현재 CPU: {status['system_health']['cpu_usage']:.1f}%\n"
        response += f"🧠 현재 메모리: {status['system_health']['memory_usage']:.1f}%\n\n"
        
        # 메모리 상태에 따른 조언
        memory_usage = status['system_health']['memory_usage']
        if memory_usage > 90:
            response += "⚠️ 메모리 사용량이 매우 높습니다. 정리를 권장합니다.\n"
        elif memory_usage > 80:
            response += "💡 메모리 사용량이 높습니다. 모니터링 중입니다.\n"
        else:
            response += "✅ 메모리 상태가 양호합니다.\n"
        
        return response
    
    def show_settings(self) -> str:
        """설정 표시"""
        response = "⚙️ 현재 설정:\n\n"
        response += f"🎭 인사 스타일: {self.user_preferences['greeting_style']}\n"
        response += f"📏 응답 길이: {self.user_preferences['response_length']}\n"
        response += f"🎓 기술 수준: {self.user_preferences['technical_level']}\n"
        response += f"⭐ 선호 기능: {', '.join(self.user_preferences['preferred_features'])}\n\n"
        
        response += "💡 설정 변경은 추후 업데이트 예정입니다.\n"
        
        return response
    
    def show_help(self) -> str:
        """도움말 표시"""
        help_text = """
🤖 개인 AI 비서 사용법:

📚 지식 검색:
   • "AI 검색해줘" - 옵시디언 노트에서 AI 관련 내용 검색
   • "파이썬 찾아줘" - 파이썬 관련 노트 찾기
   • "검색 머신러닝" - 머신러닝 관련 내용 검색

🖥️ 시스템 관리:
   • "상태 보여줘" - 현재 시스템 상태 확인
   • "성능 분석해줘" - 시스템 성능 보고서
   • "시스템 정리해줘" - 임시 파일 정리 및 최적화
   • "모니터링 현황" - 실시간 모니터링 정보

📁 파일 관리:
   • "파일 분석해줘" - 현재 디렉토리 분석
   • "백업해줘" - 옵시디언 볼트 백업
   • "파일 분석 d:\\" - 특정 경로 분석

⚙️ 기타:
   • "설정" - 현재 설정 확인
   • "도움말" 또는 "help" - 이 도움말 표시
   • "종료" 또는 "exit" - 비서 종료

💡 자연스러운 대화로 명령하세요!
   예: "옵시디언에서 AI 노트 찾아줘", "메모리 상태 어때?"
"""
        return help_text
    
    def handle_unknown_intent(self, user_input: str) -> str:
        """알 수 없는 의도 처리"""
        responses = [
            f"🤔 '{user_input}'에 대해 잘 이해하지 못했습니다.",
            "💭 다시 한 번 명확하게 말씀해 주시겠어요?",
            "🔍 혹시 검색, 상태 확인, 파일 분석 중 하나를 원하시나요?",
            "💡 'help'를 입력하면 사용 가능한 명령어를 확인할 수 있습니다."
        ]
        
        import random
        return random.choice(responses)
    
    def save_conversation(self, user_input: str, ai_response: str):
        """대화 히스토리 저장"""
        conversation_entry = {
            "timestamp": datetime.now().isoformat(),
            "user_input": user_input,
            "ai_response": ai_response
        }
        
        self.conversation_history.append(conversation_entry)
        
        # 최근 100개 대화만 유지
        if len(self.conversation_history) > 100:
            self.conversation_history = self.conversation_history[-100:]
    
    def run_conversation(self):
        """대화형 인터페이스 실행"""
        print("\n💬 대화를 시작합니다. '종료' 또는 'exit'를 입력하면 종료됩니다.\n")
        
        while True:
            try:
                # 사용자 입력 받기
                user_input = input("👤 You: ").strip()
                
                # 종료 명령 확인
                if user_input.lower() in ['종료', 'exit', 'quit', '나가기']:
                    print("\n🤖 Assistant: 안녕히 가세요! 언제든지 다시 호출해 주세요. 👋")
                    break
                
                if not user_input:
                    continue
                
                # 입력 처리
                print("🤖 Assistant: ", end="", flush=True)
                
                # 자연어 처리
                parsed_input = self.process_natural_language(user_input)
                
                # 의도 실행
                response = self.execute_intent(parsed_input)
                
                # 응답 출력
                print(response)
                
                # 대화 히스토리 저장
                self.save_conversation(user_input, response)
                
                print()  # 빈 줄 추가
                
            except KeyboardInterrupt:
                print("\n\n🤖 Assistant: 인터럽트 신호를 받았습니다. 안녕히 가세요! 👋")
                break
            except EOFError:
                print("\n\n🤖 Assistant: 입력이 종료되었습니다. 안녕히 가세요! 👋")
                break
            except Exception as e:
                print(f"\n❌ 오류가 발생했습니다: {e}")
                print("💡 'help'를 입력하여 도움말을 확인하세요.\n")

def main():
    """대화형 비서 메인 실행"""
    try:
        assistant = ConversationalAssistant()
        assistant.run_conversation()
    except KeyboardInterrupt:
        print("\n👋 프로그램이 종료되었습니다.")
    except Exception as e:
        print(f"\n❌ 시스템 오류: {e}")

if __name__ == "__main__":
    main()
