from specialists.base import Specialist


class Critic(Specialist):
    name = "critic"
    description = "Attack assumptions, find failure modes, demand tests"

    @property
    def system_prompt(self) -> str:
        return (
            "You are the critic specialist on Edge Bridge. "
            "Find holes, missing constraints, and unsafe generalizations. "
            "Do not emit INVOKE/CONSULT/HANDOFF. Return a structured critique."
        )


specialist = Critic()
