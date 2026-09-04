from specialists.base import Specialist


class Coder(Specialist):
    name = "coder"
    description = "Modular code. Small units. No side effects claimed."

    @property
    def system_prompt(self) -> str:
        return (
            "You are the coder specialist on Edge Bridge. "
            "Emit complete, small modules. Do not pretend you wrote files to disk. "
            "Do not emit INVOKE/CONSULT/HANDOFF."
        )


specialist = Coder()
