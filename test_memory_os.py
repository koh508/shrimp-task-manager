# test_memory_os.py (Vector Search Edition)

import unittest

import numpy as np

from goal_learning_memory_system import MemoryOS


class TestVectorMemoryOS(unittest.TestCase):
    def setUp(self):
        """각 테스트 전에 MemoryOS 인스턴스를 생성합니다."""
        self.memory_os = MemoryOS()

    def test_initialization(self):
        """MemoryOS가 모델과 FAISS 인덱스를 올바르게 초기화하는지 테스트합니다."""
        self.assertIsNotNone(self.memory_os.model)
        self.assertIsNotNone(self.memory_os.vector_index)
        self.assertEqual(self.memory_os.vector_index.ntotal, 0)

    def test_store_and_consolidation(self):
        """기억이 저장되고 벡터 인덱스로 올바르게 고착화되는지 테스트합니다."""
        # 의미가 다른 두 개의 기억
        memory1 = {"user_input": "오늘 점심은 김치찌개를 먹었다", "importance": 0.9}
        memory2 = {"user_input": "파이썬으로 웹 스크래핑하는 법을 배웠다", "importance": 0.9}

        self.memory_os.store(memory1)
        self.memory_os.store(memory2)

        self.assertEqual(len(self.memory_os.working_memory), 2)

        # 고착화 실행
        self.memory_os.consolidate()

        # working_memory는 비워져야 함
        self.assertEqual(len(self.memory_os.working_memory), 0)

        # 벡터 인덱스에 두 개의 아이템이 추가되어야 함
        self.assertEqual(self.memory_os.vector_index.ntotal, 2)
        self.assertEqual(len(self.memory_os.long_term_memory_metadata), 2)

    def test_semantic_retrieval(self):
        """의미론적으로 유사한 기억을 올바르게 검색하는지 테스트합니다."""
        # 테스트 데이터 준비
        memory1 = {"user_input": "오늘 점심은 김치찌개를 먹었다", "importance": 0.9}
        memory2 = {"user_input": "파이썬으로 웹 스크래핑하는 법을 배웠다", "importance": 0.9}
        memory3 = {"user_input": "어젯밤에는 잠을 잘 잤다", "importance": 0.9}

        self.memory_os.store(memory1)
        self.memory_os.store(memory2)
        self.memory_os.store(memory3)
        self.memory_os.consolidate()

        # '식사'와 관련된 쿼리 (김치찌개와 의미적으로 유사)
        query = "오늘 뭐 먹었어?"
        retrieved_memories = self.memory_os.retrieve(query, k=1)

        self.assertEqual(len(retrieved_memories), 1)
        # 가장 유사한 기억이 '김치찌개'에 대한 것이어야 함
        self.assertEqual(retrieved_memories[0]["user_input"], "오늘 점심은 김치찌개를 먹었다")

        # '코딩'과 관련된 쿼리 (웹 스크래핑과 의미적으로 유사)
        query_coding = "프로그래밍에 대해 뭘 배웠니?"
        retrieved_coding_memories = self.memory_os.retrieve(query_coding, k=1)

        self.assertEqual(len(retrieved_coding_memories), 1)
        self.assertEqual(retrieved_coding_memories[0]["user_input"], "파이썬으로 웹 스크래핑하는 법을 배웠다")


if __name__ == "__main__":
    unittest.main()
