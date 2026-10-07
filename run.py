import asyncio
import os
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from pathlib import Path

from agent import Agent
from openrouter import OpenRouterLLM

async def main():
    # Lấy đường dẫn thư mục hiện tại của project
    project_dir = Path(__file__).parent.resolve()
    server_script = project_dir / "server.py"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(server_script)],
        cwd=str(project_dir),  # Đảm bảo server chạy đúng thư mục chứa code
        env=os.environ.copy(),
    )

    # Connect via stdio client session
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Initialize LLM and Agent
            llm = OpenRouterLLM(model="anthropic/claude-3.5-sonnet")  # or your preferred model
            agent = Agent(name="VaultAgent", llm=llm, mcp_session=session)

            print("Obsidian AI Agent Ready! (type 'exit' to quit)\n")
            while True:
                user_query = input("You: ").strip()
                if not user_query or user_query.lower() in ("exit", "quit"):
                    break

                response = await agent.run(user_query)
                print(f"\nAgent:\n{response}\n")

if __name__ == "__main__":
    asyncio.run(main())