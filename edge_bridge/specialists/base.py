"""Base class — specialists are text plugins. They never call an LLM or a tool."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, List


class Specialist(ABC):
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
