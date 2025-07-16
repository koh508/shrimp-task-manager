import asyncio
import logging

from clipper.batch_processor import batch_process_clippings
from clipper.connection_manager import MCPConnectionManager
from clipper.dashboard import create_realtime_dashboard


class UltraAdvancedAIAssistant:
    def __init__(self, name, obsidian_vault, mcp_server_url=None):
        self.name = name
        self.obsidian_vault = obsidian_vault
        self.mcp_server_url = mcp_server_url or "wss://shrimp-mcp-production.up.railway.app"
        self.connection_manager = MCPConnectionManager(
            primary_url=self.mcp_server_url, backup_urls=["ws://localhost:8765"]
        )
        self.logger = logging.getLogger("UltraAdvancedAIAssistant")

    async def process_batch_clippings(self, batch_size=10):
        await batch_process_clippings(batch_size=batch_size)

    async def show_dashboard(self):
        status = await create_realtime_dashboard()
        self.logger.info(
            f"MCP 상태: {status['mcp_status']}, 오늘 처리: {status['processed_today']}건, LLM 성공률: {status['llm_summary_success_rate']}, 평균 처리: {status['average_processing_time']}"
        )
        return status

    async def run(self):
        # 예시: 대시보드/배치처리 반복
        while True:
            await self.process_batch_clippings(batch_size=10)
            await self.show_dashboard()
            await asyncio.sleep(10)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(message)s")
    assistant = UltraAdvancedAIAssistant(
        name="UltraAssistant",
        obsidian_vault="D:/my workspace/OneDrive NEW/GNY",
        mcp_server_url="wss://shrimp-mcp-production.up.railway.app",
    )
    asyncio.run(assistant.run())
