"""Base class for all specialist plugins."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class Specialist(ABC):
    """Pure plugin. Provides system prompt + message builder. Never calls an LLM itself."""

    name: str = "base"
    description: str = "Abstract specialist"

    @property
    @abstractmethod
    def system_prompt(self) -> str:
        ...

    def build_messages(self, task: str, extra_context: str = "") -> List[Dict[str, str]]:
        content = task
        if extra_context:
            content = f"{task}\n\nAdditional context:\n{extra_context}"
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": content},
        ]
