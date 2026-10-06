from typing import Any

from llm import LLM


class Agent:
    def __init__(self, name:str, llm: LLM, mcp):
        self.name = name
        self.llm = llm
        self.mcp = mcp

    async def run(self, user_input: str) -> str:
        message = [
            {
                "role": "system",
                "content": self._system_prompt(),

            },
            {
                "role": "user",
                "content": user_input,
            },
        ]

        while True:
            response = await self.llm.generate(
                messages=message,
                tools=await self._get_tools(),
            )

            if response["type"] == "final":
                return response["content"]

            if response["type"] == "tool_call":
                tool_name = response["tool_name"]
                arguments = response["arguments"]

                result = await self._execute_tool(
                    tool_name,
                    arguments,
                )

                message.append({
                    "role": "assistant",
                    "content": response,
                })

                message.append({
                    "role": "tool",
                    "name": tool_name,
                    "content": result,
                })

    async def _get_tools(self):
        # available tools from server.py
        tools = await self.mcp.list_tools()
        return tools

    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any],) -> Any:
        return await self.mcp.call_tool(tool_name, arguments)

    def _system_prompt(self) -> str:
        return """
You are an AI knowledge assistant for an Obsidian vault.

Your job is to answer questions using the user's Obsidian knowledge base.

Available capabilities include:
- searching notes
- reading note content
- inspecting note metadata and links
- exploring relationships between concepts

When answering a question about the vault:
1. Search for relevant notes.
2. Read useful notes.
3. Explore relationships when useful.
4. Base your answer on information found in the vault.
5. If the vault does not contain enough information, say so.

Do not invent information that is not supported by the vault.
"""
