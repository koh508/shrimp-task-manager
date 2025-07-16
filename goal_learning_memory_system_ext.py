# 목표 지향적 AI 자율 학습 시스템 - 확장 및 통합 구현
# 핵심: 목표 관리 + 옵시디언 동기화 + 에러 로깅 통합
from datetime import datetime

from goal_learning_memory_system import GoalHierarchy, IntegratedLearningMemorySystem


class EnhancedGoalHierarchy(GoalHierarchy):
    """강화된 목표 관리 시스템 (옵시디언 연동)"""

    def __init__(self, obsidian_vault_path):
        super().__init__()
        self.obsidian_path = obsidian_vault_path
        self.goal_tracking_file = f"{obsidian_vault_path}/AI_Goal_Tracking.md"

    def sync_with_obsidian(self):
        self.save_goals_to_obsidian()
        self.update_progress_in_obsidian()

    def save_goals_to_obsidian(self):
        with open(self.goal_tracking_file, "w", encoding="utf-8") as f:
            f.write("# AI 목표 추적\n\n")
            f.write("## 장기 목표\n")
            for g in self.long_term_goals:
                f.write(f"- [ ] {g}\n")
            f.write("## 중기 목표\n")
            for g in self.medium_term_goals:
                f.write(f"- [ ] {g}\n")
            f.write("## 단기 목표\n")
            for g in self.short_term_goals:
                f.write(f"- [ ] {g}\n")
            f.write("## 즉시 작업\n")
            for g in self.immediate_tasks:
                f.write(f"- [ ] {g}\n")

    def update_progress_in_obsidian(self):
        # 실제 진행 상황 업데이트 로직 필요 (예시)
        pass


class LearningErrorHandler:
    """학습 과정 에러 처리 및 로깅"""

    def __init__(self, error_folder):
        self.error_folder = error_folder

    def log_learning_error(self, learning_phase, error_details):
        error_file = (
            f"{self.error_folder}/learning_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        )
        with open(error_file, "w", encoding="utf-8") as f:
            f.write(f"# 학습 시스템 에러 보고\n\n")
            f.write(f"**단계**: {learning_phase}\n")
            f.write(f"**에러 내용**: {error_details}\n")
            f.write(f"**시간**: {datetime.now().isoformat()}\n")


# 메인 에이전트 통합 예시
from ultra_ai_assistant import UltraAdvancedAIAssistant


class GoalOrientedUltraAI(UltraAdvancedAIAssistant):
    """목표 지향 Ultra AI Assistant (목표/학습/기억 통합)"""

    def __init__(self, name, obsidian_vault, mcp_server_url):
        super().__init__(name, obsidian_vault, mcp_server_url)
        self.goal_system = EnhancedGoalHierarchy(obsidian_vault)
        self.learning_system = IntegratedLearningMemorySystem()
        self.error_handler = LearningErrorHandler(f"{obsidian_vault}/AI_Errors")

    async def process_with_goal_awareness(self, user_input):
        try:
            self.goal_system.sync_with_obsidian()
            response = await self.learning_system.process_user_interaction(user_input, context={})
            return response
        except Exception as e:
            self.error_handler.log_learning_error("process_with_goal_awareness", str(e))
            return f"⚠️ 처리 중 오류 발생: {e}"
