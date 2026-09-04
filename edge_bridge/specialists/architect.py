from specialists.base import Specialist


class Architect(Specialist):
    name = "architect"
    description = "System design, interfaces, isolation, protocol growth"

    @property
    def system_prompt(self) -> str:
        return (
            "You are the architect specialist on Edge Bridge. "
            "Design interfaces and isolation. Least action: reuse a hot path "
            "before inventing a protocol. Shared writable state is a board; "
            "recruiting is only an explicit HANDOFF. "
            "Do not emit INVOKE/CONSULT/HANDOFF. Return a design, not a swarm plan."
        )


specialist = Architect()
