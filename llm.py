from abc import ABC, abstractmethod
from typing import Any


class LLM(ABC):

    @abstractmethod
    async def generate(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
    ) -> Any:
        pass