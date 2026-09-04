"""Specialist registry — discovers and loads pure plugin specialists."""

from __future__ import annotations

import importlib
import logging
from typing import Dict, List

from specialists.base import Specialist

logger = logging.getLogger("multi_agent.registry")


class Registry:
    def __init__(self) -> None:
        self._specialists: Dict[str, Specialist] = {}

    def register(self, specialist: Specialist) -> None:
        name = specialist.name.lower()
        if name in self._specialists:
            logger.warning("Overwriting specialist %s", name)
        self._specialists[name] = specialist
        logger.info("Registered specialist: %s", name)

    def get(self, name: str) -> Specialist:
        key = name.lower()
        if key not in self._specialists:
            raise KeyError(f"Unknown specialist: {name}. Known: {list(self._specialists)}")
        return self._specialists[key]

    def list_names(self) -> List[str]:
        return sorted(self._specialists.keys())

    def describe(self) -> str:
        lines = []
        for name, sp in sorted(self._specialists.items()):
            lines.append(f"- {name}: {sp.description}")
        return "\n".join(lines)

    @classmethod
    def load_default(cls) -> "Registry":
        """Load core + domain specialists (Phase-0 + Domain Specialist Factory)."""
        reg = cls()
        modules = [
            "specialists.researcher",
            "specialists.experiment_critic",
            "specialists.coder",
            "specialists.architect",
            "specialists.residual_stream",
            "specialists.vibration",
            "specialists.quantum_sim",
            "specialists.rf",
        ]
        for mod_name in modules:
            mod = importlib.import_module(mod_name)
            if hasattr(mod, "specialist"):
                reg.register(mod.specialist)
            elif hasattr(mod, "SpecialistClass"):
                reg.register(mod.SpecialistClass())
            else:
                for attr in dir(mod):
                    obj = getattr(mod, attr)
                    if isinstance(obj, type) and issubclass(obj, Specialist) and obj is not Specialist:
                        reg.register(obj())
                        break
        return reg
