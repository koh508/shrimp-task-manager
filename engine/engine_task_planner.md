---
tags:
  - 자동분류
상태: 대기
날짜: 2026-03-14
---
# engine/task_planner.py

```python
from enum import Enum
from typing import List, Dict, Any, Optional
from datetime import datetime
from engine.strategy import LLMStrategy # LLMStrategy 임포트

class TaskStatus(Enum):
    PLANNING = "PLANNING"
    EXECUTING = "EXECUTING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"

class Task:
    def __init__(
        self, 
        task_id: str, 
        description: str, 
        plan_a: str,
        plan_b: Optional[str] = None,
        status: TaskStatus = TaskStatus.PLANNING,
        logs: Optional[List[str]] = None
    ):
        self.task_id = task_id
        self.description = description
        self.plan_a = plan_a
        self.plan_b = plan_b
        self.status = status
        self.logs = logs if logs is not None else []
        self.created_at = datetime.now()
        self.updated_at = datetime.now()

    def add_log(self, log_entry: str):
        self.logs.append(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {log_entry}")
        self.updated_at = datetime.now()

    def update_status(self, new_status: TaskStatus):
        self.status = new_status
        self.updated_at = datetime.now()
        self.add_log(f"상태 변경: {new_status.value}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "task_id": self.task_id,
            "description": self.description,
            "plan_a": self.plan_a,
            "plan_b": self.plan_b,
            "status": self.status.value,
            "logs": self.logs,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

class TaskPlanner:
    def __init__(self, llm_strategy: LLMStrategy):
        self.tasks: Dict[str, Task] = {}
        self.llm_strategy = llm_strategy
        self.logger = print # 간단한 로깅을 위해 print 사용

    def create_task(self, task_id: str, description: str, plan_a: str, plan_b: Optional[str] = None) -> Task:
        if task_id in self.tasks:
            self.logger(f"⚠️ 경고: Task ID '{task_id}'가 이미 존재합니다. 기존 작업을 반환합니다.")
            return self.tasks[task_id]
        
        new_task = Task(task_id, description, plan_a, plan_b)
        self.tasks[task_id] = new_task
        self.logger(f"✅ 새로운 작업 생성: {task_id} - {description}")
        return new_task

    def get_task(self, task_id: str) -> Optional[Task]:
        return self.tasks.get(task_id)

    def update_task_status(self, task_id: str, new_status: TaskStatus):
        task = self.get_task(task_id)
        if task:
            task.update_status(new_status)
            self.logger(f"🔄 작업 '{task_id}' 상태 업데이트: {new_status.value}")
        else:
            self.logger(f"❌ 오류: Task ID '{task_id}'를 찾을 수 없습니다.")

    async def execute_task_step(self, task_id: str, step_description: str) -> Dict[str, Any]:
        task = self.get_task(task_id)
        if not task:
            self.logger(f"❌ 오류: Task ID '{task_id}'를 찾을 수 없습니다.")
            return {"status": "error", "message": f"Task '{task_id}' not found."}

        task.add_log(f"단계 실행 시작: {step_description}")
        self.logger(f"▶️ 작업 '{task_id}' - 단계 실행: {step_description}")

        # LLM 전략을 사용하여 실제 작업 수행 시뮬레이션
        llm_response = await self.llm_strategy.execute_llm_call(step_description)
        task.add_log(f"LLM 응답: {llm_response}")

        if llm_response["status"] == "success":
            self.logger(f"✔️ 작업 '{task_id}' - 단계 성공: {step_description}")
            return {"status": "success", "response": llm_response["response"]}
        elif llm_response["status"] == "final_failed":
            task.update_status(TaskStatus.FAILED)
            self.logger(f"❌ 작업 '{task_id}' - 최종 실패: {llm_response['message']}")
            return {"status": "failed", "message": llm_response["message"]}
        else: # 저비용 LLM 실패 후 고비용 LLM 시도 중일 수 있음
            self.logger(f"⚠️ 작업 '{task_id}' - 단계 진행 중: {llm_response['message']}")
            return {"status": "in_progress", "message": llm_response["message"]}

    def get_task_status_report(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.get_task(task_id)
        if task:
            return task.to_dict()
        return None

```
