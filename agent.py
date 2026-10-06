import json
from typing import Any
from llm import LLM

class Agent:
    def __init__(self, name: str, llm: LLM, mcp_session, max_steps: int = 10):
        self.name = name
        self.llm = llm
        self.mcp = mcp_session
        self.max_steps = max_steps

    async def run(self, user_input: str) -> str:
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {"role": "user", "content": user_input},
        ]
        tools = await self._get_tools()

        for _ in range(self.max_steps):
            response = await self.llm.generate(messages=messages, tools=tools)
            choice = response.choices[0]
            message = choice.message

            # If no tool calls, return final response
            if not message.tool_calls:
                return message.content or ""

            # Append the assistant message with tool calls to conversation history
            messages.append(message.model_dump(exclude_unset=True))

            # Execute every tool call requested by the model
            for tool_call in message.tool_calls:
                tool_name = tool_call.function.name
                args = json.loads(tool_call.function.arguments)

                tool_result = await self._execute_tool(tool_name, args)

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": str(tool_result),
                })

        return "Reached maximum iteration limit without completing the task."

    async def _get_tools(self):
        mcp_tools = await self.mcp.list_tools()
        # Transform MCP tool format into OpenAI tool definitions
        return [
            {
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.inputSchema,
                },
            }
            for tool in mcp_tools.tools
        ]

    async def _execute_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        result = await self.mcp.call_tool(tool_name, arguments)
        return result.content

    def _system_prompt(self) -> str:
        return (
            "You are an AI knowledge assistant for an Obsidian vault.\n"
            "Answer questions using the user's Obsidian knowledge base.\n"
            "Search for relevant notes, read them, and explore links.\n"
            "Base answers strictly on vault information."
        )