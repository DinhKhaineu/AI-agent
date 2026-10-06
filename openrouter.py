import os

from dotenv import load_dotenv
from openai import AsyncOpenAI

from llm import LLM

load_dotenv()


class OpenRouterLLM(LLM):

    def __init__(self, model: str):

        self.client = AsyncOpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
        )

        self.model = model

    async def generate(self, messages, tools):

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=tools,
        )

        return response